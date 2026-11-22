"""Request policy tests for net.Net (no real network — httpx.MockTransport).

The retry rules are the difference between "one provider had a bad hour" and
"the publish gate blocked the site", so they get their own tests.
"""

import asyncio

import httpx
import pytest

from intern_engine import net as net_module
from intern_engine.net import HostLimiter, Net, NonJSONResponse, _Brake


def _net(handler) -> tuple[Net, httpx.AsyncClient]:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return Net(client, HostLimiter(per_host=4)), client


def _run(handler, *, retries: int = 3):
    async def go():
        net, client = _net(handler)
        try:
            return await net.get_json("https://boards.example/api", retries=retries)
        finally:
            await client.aclose()

    return asyncio.run(go())


@pytest.fixture(autouse=True)
def _no_sleeping(monkeypatch):
    """Backoff is policy, not something the suite should wait through."""
    async def instant(_seconds):
        return None

    monkeypatch.setattr(asyncio, "sleep", instant)


class TestNonJSONBody:
    """A 200 carrying HTML is a bot wall, and bot walls are per-request.

    On 2026-08-15 Workday served an unparseable body to roughly a third of its
    tenants for two hours. Parse failures skipped the retry path entirely, so
    563 boards failed on their first attempt and the registry fetch rate fell
    under the publish floor twice.
    """

    def test_a_wall_that_lifts_is_retried_into_a_success(self):
        attempts = []

        def handler(request):
            attempts.append(request.url)
            if len(attempts) < 3:
                return httpx.Response(
                    200, text="<html>Access Denied</html>",
                    headers={"Content-Type": "text/html"},
                )
            return httpx.Response(200, json={"jobPostings": [{"title": "Intern"}]})

        assert _run(handler) == {"jobPostings": [{"title": "Intern"}]}
        assert len(attempts) == 3

    def test_a_wall_that_never_lifts_fails_after_the_full_budget(self):
        attempts = []

        def handler(request):
            attempts.append(request.url)
            return httpx.Response(
                200, text="<html>Access Denied</html>",
                headers={"Content-Type": "text/html"},
            )

        with pytest.raises(NonJSONResponse) as caught:
            _run(handler)
        assert len(attempts) == 4  # the first try plus retries=3
        # The message is the whole point: health.json has to say what broke.
        assert "200 text/html" in str(caught.value)
        assert "boards.example" in str(caught.value)

    def test_it_stays_a_valueerror_for_existing_handlers(self):
        def handler(_request):
            return httpx.Response(200, text="not json")

        with pytest.raises(ValueError):
            _run(handler, retries=0)

    def test_no_retries_means_no_retries(self):
        attempts = []

        def handler(request):
            attempts.append(request.url)
            return httpx.Response(200, text="not json")

        with pytest.raises(NonJSONResponse):
            _run(handler, retries=0)
        assert len(attempts) == 1


class TestUnchangedPolicy:
    """The paths this change had to leave exactly as they were."""

    def test_a_clean_json_response_makes_one_request(self):
        attempts = []

        def handler(request):
            attempts.append(request.url)
            return httpx.Response(200, json={"ok": True})

        assert _run(handler) == {"ok": True}
        assert len(attempts) == 1

    def test_retryable_statuses_still_retry(self):
        codes = iter([503, 429, 200])

        def handler(_request):
            code = next(codes)
            if code == 200:
                return httpx.Response(200, json={"ok": True})
            return httpx.Response(code, json={"error": "slow down"})

        assert _run(handler) == {"ok": True}

    def test_a_404_is_still_fatal_on_the_first_attempt(self):
        attempts = []

        def handler(request):
            attempts.append(request.url)
            return httpx.Response(404, text="gone")

        with pytest.raises(httpx.HTTPStatusError):
            _run(handler)
        assert len(attempts) == 1


async def _tick(times: int = 3) -> None:
    """Let other tasks run. asyncio.sleep is patched to return without yielding."""
    loop = asyncio.get_running_loop()
    for _ in range(times):
        step = loop.create_future()
        loop.call_soon(step.set_result, None)
        await step


class TestProviderBrake:
    """Pushback slows a whole provider down, and nothing else does.

    From 2026-11-13 Workday answered 429 to 200-400 boards a run while 32
    requests stayed in flight, each worker retrying into the wall on its own.
    The boards failed, got quarantined, and the publish gate held the site for
    five days. A healthy provider must still run exactly as it did before.
    """

    @pytest.fixture(autouse=True)
    def _every_signal_is_its_own_event(self, monkeypatch):
        monkeypatch.setattr(net_module, "_CUT_SPACING_SECONDS", 0.0)

    def test_a_healthy_provider_is_never_slowed(self):
        brake = _Brake(32, floor=8)
        for _ in range(500):
            brake.succeeded()
        assert (brake.limit, brake.cuts, brake.signals) == (32, 0, 0)

    def test_pushback_halves_down_to_the_floor_and_no_further(self):
        brake = _Brake(32, floor=8)
        brake.throttled()
        assert brake.limit == 16
        brake.throttled()
        assert brake.limit == 8
        brake.throttled()
        assert brake.limit == 8
        assert (brake.signals, brake.cuts, brake.lowest) == (3, 2, 8)

    def test_one_burst_from_requests_in_flight_is_one_cut(self, monkeypatch):
        monkeypatch.setattr(net_module, "_CUT_SPACING_SECONDS", 2.0)
        brake = _Brake(32, floor=8)
        for _ in range(32):  # every request in flight answered 429 together
            brake.throttled()
        assert (brake.limit, brake.cuts, brake.signals) == (16, 1, 32)

    def test_clean_answers_win_slots_back_one_at_a_time(self):
        brake = _Brake(32, floor=8)
        brake.throttled()
        brake.throttled()
        for _ in range(8):
            brake.succeeded()
        assert brake.limit == 9
        for _ in range(1000):
            brake.succeeded()
        assert brake.limit == 32  # all the way back, never past the ceiling

    def test_pushback_breaks_the_clean_streak(self):
        brake = _Brake(32, floor=8)
        brake.throttled()
        brake.throttled()
        for _ in range(7):
            brake.succeeded()
        brake.throttled()  # already at the floor: no cut, but no credit either
        brake.succeeded()
        assert brake.limit == 8

    def test_the_limit_is_what_actually_runs(self):
        async def go():
            brake = _Brake(4, floor=1)
            brake.throttled()  # 4 -> 2
            running = peak = 0
            release = asyncio.Event()

            async def request():
                nonlocal running, peak
                await brake.acquire()
                running += 1
                peak = max(peak, running)
                await release.wait()
                running -= 1
                brake.release()

            tasks = [asyncio.create_task(request()) for _ in range(6)]
            await _tick()
            queued_peak = peak
            release.set()
            await asyncio.gather(*tasks)
            return queued_peak, peak, brake._in_flight

        queued_peak, peak, left = asyncio.run(go())
        assert queued_peak == 2 and peak == 2
        assert left == 0

    def test_a_cancelled_waiter_gives_nothing_away(self):
        async def go():
            brake = _Brake(1, floor=1)
            await brake.acquire()
            waiter = asyncio.create_task(brake.acquire())
            await _tick()
            waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await waiter
            brake.release()
            await brake.acquire()  # would hang if the cancelled waiter kept a slot
            brake.release()
            return brake._in_flight, len(brake._waiters)

        assert asyncio.run(go()) == (0, 0)

    def test_a_deadline_while_queued_for_the_host_returns_the_provider_slot(self):
        """The board deadline cancels mid-acquire; the provider slot must survive it."""
        async def go():
            limiter = HostLimiter(per_host=1, per_provider=4)
            holder = await limiter.acquire("acme.wd1.myworkdayjobs.com")
            await holder.__aenter__()
            queued = await limiter.acquire("acme.wd1.myworkdayjobs.com")
            task = asyncio.create_task(queued.__aenter__())
            await _tick()  # holds a provider slot, waiting on the busy host
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            await holder.__aexit__(None, None, None)
            return holder.brake._in_flight

        assert asyncio.run(go()) == 0

    def test_one_tenant_429_slows_all_of_workday_and_nothing_else(self):
        async def go():
            limiter = HostLimiter(per_host=8, per_provider=32)

            def handler(request):
                if request.url.host.startswith("busy."):
                    return httpx.Response(429)
                return httpx.Response(200, json={"ok": True})

            client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            net = Net(client, limiter)
            try:
                with pytest.raises(httpx.HTTPStatusError):
                    await net.get_json("https://busy.wd1.myworkdayjobs.com/x", retries=0)
                await net.get_json("https://boards-api.greenhouse.io/v1/boards/a/jobs")
                workday = await limiter.acquire("calm.wd5.myworkdayjobs.com")
                greenhouse = await limiter.acquire("boards-api.greenhouse.io")
                return workday.brake.limit, greenhouse.brake.limit, limiter.pushback()
            finally:
                await client.aclose()

        workday, greenhouse, report = asyncio.run(go())
        assert workday == 16
        assert greenhouse == 32
        assert report == {"workday": {"signals": 1, "cuts": 1, "lowest": 16}}

    def test_a_bot_wall_is_pushback_and_a_404_is_not(self):
        async def go():
            limiter = HostLimiter(per_host=8, per_provider=32)

            def handler(request):
                if request.url.path == "/wall":
                    return httpx.Response(200, text="<html>Access Denied</html>",
                                          headers={"Content-Type": "text/html"})
                return httpx.Response(404, text="gone")

            client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            net = Net(client, limiter)
            try:
                with pytest.raises(httpx.HTTPStatusError):
                    await net.get_json("https://acme.wd1.myworkdayjobs.com/gone", retries=0)
                after_404 = limiter.pushback()
                with pytest.raises(NonJSONResponse):
                    await net.get_json("https://acme.wd1.myworkdayjobs.com/wall", retries=0)
                return after_404, limiter.pushback()
            finally:
                await client.aclose()

        after_404, after_wall = asyncio.run(go())
        assert after_404 == {}
        assert after_wall["workday"]["cuts"] == 1


class TestBotChallenge:
    """Workday's CDN since 2026-11-13: a JavaScript 'Security Check' sent as a 429.

    Captured live: status 429, `server: cloudflare`, `cf-mitigated: challenge`,
    body "Security Check - Enable JavaScript and cookies to continue". Waiting
    does not lift it, and every retry spends more of the reputation that
    triggered it, so it must fail on the first answer.
    """

    @staticmethod
    def _challenge(status: int = 429):
        return httpx.Response(
            status, text="<html>Security Check</html>",
            headers={"Content-Type": "text/html", "Server": "cloudflare",
                     "cf-mitigated": "challenge"},
        )

    def test_a_challenge_is_never_retried(self):
        attempts = []

        def handler(request):
            attempts.append(request.url)
            return self._challenge()

        with pytest.raises(net_module.BotChallenge) as caught:
            _run(handler, retries=3)
        assert len(attempts) == 1
        assert "bot challenge (429, cf-mitigated) from boards.example" in str(caught.value)

    def test_it_is_still_an_http_status_error(self):
        with pytest.raises(httpx.HTTPStatusError):
            _run(lambda _request: self._challenge(), retries=0)

    def test_a_challenge_dressed_as_a_200_is_not_retried_as_a_bot_wall(self):
        attempts = []

        def handler(request):
            attempts.append(request.url)
            return self._challenge(200)

        with pytest.raises(net_module.BotChallenge):
            _run(handler, retries=3)
        assert len(attempts) == 1

    def test_a_challenge_slows_the_provider_down(self, monkeypatch):
        monkeypatch.setattr(net_module, "_CUT_SPACING_SECONDS", 0.0)

        async def go():
            limiter = HostLimiter(per_host=8, per_provider=32)
            client = httpx.AsyncClient(
                transport=httpx.MockTransport(lambda _request: self._challenge()))
            try:
                with pytest.raises(net_module.BotChallenge):
                    await Net(client, limiter).post_json(
                        "https://acme.wd12.myworkdayjobs.com/wday/cxs/acme/Site/jobs")
                return limiter.pushback()
            finally:
                await client.aclose()

        assert asyncio.run(go()) == {"workday": {"signals": 1, "cuts": 1, "lowest": 16}}
