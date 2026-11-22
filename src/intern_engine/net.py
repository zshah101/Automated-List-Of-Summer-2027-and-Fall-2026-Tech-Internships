"""Async HTTP with retry/backoff and per-host concurrency limits.

Connectors talk to the network only through `Net`, which keeps request policy
(retries, backoff, politeness) in one place instead of scattered across every
ATS module.
"""

from __future__ import annotations

import asyncio
import contextlib
import random
import time
from collections import deque
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

# Status codes worth retrying — transient server/rate-limit conditions.
_RETRYABLE = {429, 500, 502, 503, 504}
# The subset that means "slow down" rather than "something broke". Besides
# retrying the one request, these tighten the provider-wide brake. A bot wall
# (a 2xx that isn't JSON) is the same signal; it is caught where bodies parse.
_THROTTLED = {429, 503}
# Requests already in flight answer a burst of pushback together. That is one
# congestion event, not thirty-two, so the brake cuts at most once per window.
_CUT_SPACING_SECONDS = 2.0


class NonJSONResponse(ValueError):
    """A 2xx whose body did not parse as JSON — a bot wall, not an answer.

    Still a ValueError, so every existing handler catches it unchanged. It
    exists for the message: `JSONDecodeError: Expecting value: line 1 column 1
    (char 0)` is what 563 Workday boards wrote into health.json on 2026-08-15
    and it says nothing about what went wrong. "non-JSON body (200 text/html)"
    says all of it.
    """


class BotChallenge(httpx.HTTPStatusError):
    """The provider's CDN wants a real browser to solve a JavaScript challenge.

    Cloudflare marks these `cf-mitigated: challenge` whatever the status code;
    Workday's have arrived as 429s since 2026-11-13. A runner gets flagged for
    minutes at a time, so a retry seconds later meets the same wall, and each
    one is another automated-looking request against the score that triggered
    it. The request fails at once and the provider is slowed down. We never try
    to solve one.
    """


def _challenged(response: httpx.Response) -> bool:
    return response.headers.get("cf-mitigated", "").strip().casefold() == "challenge"


def _non_json(response: httpx.Response, url: str) -> NonJSONResponse:
    kind = response.headers.get("Content-Type", "").split(";")[0].strip()
    return NonJSONResponse(
        f"non-JSON body ({response.status_code} {kind or 'unknown type'}) from {url}"
    )


def _provider(host: str) -> str:
    lowered = host.casefold()
    families = {
        "myworkdayjobs.com": "workday",
        "myworkdaysite.com": "workday",
        "oraclecloud.com": "oracle",
        "greenhouse.io": "greenhouse",
        "smartrecruiters.com": "smartrecruiters",
        "ashbyhq.com": "ashby",
        "lever.co": "lever",
    }
    return next((name for suffix, name in families.items() if lowered.endswith(suffix)), lowered)


class _Brake:
    """A provider's concurrency cap that tightens only when the provider pushes back.

    Additive increase, multiplicative decrease, the TCP congestion rule. With no
    pushback the limit sits at its ceiling and this is a plain semaphore, so a
    healthy run behaves exactly as before. Each 429/503/bot wall halves the
    limit (never below the floor); every `limit` clean answers in a row win one
    slot back.

    It exists because the alternative was measured in production: from
    2026-11-13 Workday's CDN pushed back on 200-400 boards a run while we kept
    32 requests in flight, every worker retrying into it on its own. Those
    boards failed, the breaker quarantined them, and the registry rate fell
    under the publish floor for five days straight. Fewer requests in flight
    is the one lever we have that is also the polite one.
    """

    def __init__(self, ceiling: int, floor: int) -> None:
        self.ceiling = ceiling
        self.floor = max(1, min(floor, ceiling))
        self.limit = ceiling
        self.signals = 0
        self.cuts = 0
        self.lowest = ceiling
        self._in_flight = 0
        self._clean = 0
        self._last_cut = float("-inf")
        self._waiters: deque[asyncio.Future] = deque()

    async def acquire(self) -> None:
        if self._in_flight < self.limit and not self._waiters:
            self._in_flight += 1
            return
        waiter = asyncio.get_running_loop().create_future()
        self._waiters.append(waiter)
        try:
            await waiter  # `_wake` counts us in before resolving it
        except BaseException:
            if waiter.done() and not waiter.cancelled():
                self.release()  # granted, then cancelled before we could use it
            else:
                with contextlib.suppress(ValueError):
                    self._waiters.remove(waiter)
            raise

    def release(self) -> None:
        self._in_flight -= 1
        self._wake()

    def throttled(self) -> None:
        self.signals += 1
        self._clean = 0
        now = time.monotonic()
        if now - self._last_cut < _CUT_SPACING_SECONDS:
            return
        self._last_cut = now
        if self.limit > self.floor:
            self.limit = max(self.floor, self.limit // 2)
            self.cuts += 1
            self.lowest = min(self.lowest, self.limit)

    def succeeded(self) -> None:
        if self.limit >= self.ceiling:
            return
        self._clean += 1
        if self._clean >= self.limit:
            self._clean = 0
            self.limit += 1
            self._wake()

    def _wake(self) -> None:
        while self._waiters and self._in_flight < self.limit:
            waiter = self._waiters.popleft()
            if not waiter.done():
                self._in_flight += 1
                waiter.set_result(None)


class _Permit:
    def __init__(self, brake: _Brake, host: asyncio.Semaphore) -> None:
        self.brake = brake
        self._host = host

    async def __aenter__(self):
        await self.brake.acquire()
        try:
            await self._host.acquire()
        except BaseException:
            # A board deadline can cancel us while we queue for the host. The
            # provider slot we already hold has to go back, or every timeout
            # quietly shrinks the provider for the rest of the run.
            self.brake.release()
            raise
        return self

    async def __aexit__(self, *_exc):
        self._host.release()
        self.brake.release()


class HostLimiter:
    """Caps how many requests run concurrently against any single host.

    All Greenhouse boards share one host, so a global limit alone would still
    let us hammer it. A per-host semaphore keeps us polite to each provider
    while different hosts still run in parallel. Above that, each provider
    family (Workday's thousands of tenant hosts count as one) shares a `_Brake`
    that backs off when the provider says so. Pushback can squeeze a provider
    down to `per_host` and no further: at worst it is treated like one host.
    """

    def __init__(self, per_host: int = 8, per_provider: int | None = None) -> None:
        self._per_host = per_host
        self._per_provider = per_provider or per_host
        self._sems: dict[str, asyncio.Semaphore] = {}
        self._brakes: dict[str, _Brake] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, host: str) -> _Permit:
        async with self._lock:
            sem = self._sems.get(host)
            if sem is None:
                sem = asyncio.Semaphore(self._per_host)
                self._sems[host] = sem
            provider = _provider(host)
            brake = self._brakes.get(provider)
            if brake is None:
                brake = _Brake(self._per_provider, floor=self._per_host)
                self._brakes[provider] = brake
            return _Permit(brake, sem)

    def pushback(self) -> dict[str, dict[str, int]]:
        """Providers that pushed back this run: {provider: {signals, cuts, lowest}}."""
        return {
            provider: {"signals": brake.signals, "cuts": brake.cuts,
                       "lowest": brake.lowest}
            for provider, brake in sorted(self._brakes.items())
            if brake.signals
        }


def _backoff(attempt: int, response: httpx.Response | None = None) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After", "").strip()
        if retry_after.isdigit():
            return min(float(retry_after), 120.0)
        if retry_after:
            try:
                when = parsedate_to_datetime(retry_after)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=UTC)
                return min(max((when - datetime.now(UTC)).total_seconds(), 0.0), 120.0)
            except (TypeError, ValueError):
                pass
    return min(2**attempt + random.random(), 20.0)


class Net:
    """A thin client wrapper bound to one httpx session + host limiter."""

    def __init__(self, client: httpx.AsyncClient, limiter: HostLimiter) -> None:
        self._client = client
        self._limiter = limiter

    async def get_json(self, url: str, **kwargs):
        return await self._request("GET", url, **kwargs)

    async def post_json(self, url: str, **kwargs):
        return await self._request("POST", url, **kwargs)

    async def _request(self, method: str, url: str, *, retries: int = 3, **kwargs):
        host = httpx.URL(url).host
        permit = await self._limiter.acquire(host)
        last_error: Exception | None = None

        for attempt in range(retries + 1):
            try:
                async with permit:
                    response = await self._client.request(method, url, **kwargs)
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt == retries:
                    raise
                await asyncio.sleep(_backoff(attempt))
                continue

            if _challenged(response):
                permit.brake.throttled()
                raise BotChallenge(
                    f"bot challenge ({response.status_code}, cf-mitigated) from {host}",
                    request=response.request, response=response,
                )
            if response.status_code in _THROTTLED:
                permit.brake.throttled()
            if response.status_code in _RETRYABLE and attempt < retries:
                await asyncio.sleep(_backoff(attempt, response))
                continue

            response.raise_for_status()
            try:
                data = response.json()
            except ValueError as exc:
                permit.brake.throttled()
                # A 200 carrying HTML is a bot wall or CDN interstitial — the
                # same transient condition as a 429, just wearing a different
                # status code. It used to skip the retry path entirely and fail
                # the board on the first attempt: on 2026-08-15, Workday served
                # an unparseable body to about a third of its tenants at random
                # between 06:00 and 08:00 UTC, 563 boards died instantly, and
                # the registry fetch rate fell under the publish floor twice.
                # A third of tenants failing means two thirds ANSWERED, so the
                # wall is per-request — which is exactly what retries are for.
                last_error = _non_json(response, url)
                if attempt == retries:
                    raise last_error from exc
                # Deliberately not honoring Retry-After here: an interstitial
                # can name a delay longer than the whole board deadline, which
                # would turn a retryable board into a timed-out one.
                await asyncio.sleep(_backoff(attempt))
                continue
            permit.brake.succeeded()
            return data

        # Only reached if every attempt hit a retryable status without resolving.
        raise last_error or httpx.HTTPError(f"request to {url} failed after retries")
