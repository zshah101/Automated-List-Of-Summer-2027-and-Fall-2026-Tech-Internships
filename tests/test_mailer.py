"""Digest mailer: gating, composition, and the no-op-without-config contract."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from intern_engine import mailer, paths


def _record(hours_ago: float, **extra) -> dict:
    ts = (datetime.now(UTC) - timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec = {
        "id": f"x:{hours_ago}", "company": "Acme", "title": "SWE Intern",
        "season": "Summer 2027", "location": "NYC", "url": "https://x/1",
        "is_open": True, "first_seen_at": ts, "sponsorship": "unknown",
    }
    rec.update(extra)
    return rec


# --- what counts as news -------------------------------------------------------

def test_new_roles_window():
    store = {
        "a": _record(2),
        "b": _record(80),               # too old
        "c": _record(1, is_open=False),  # closed
    }
    fresh = mailer.new_roles(store)
    assert [r["id"] for r in fresh] == ["x:2"]


def test_already_sent_roles_are_never_repeated():
    # The duplicate-digest bug: the news window (48h) is wider than the send
    # interval (22h), so a role sits in two consecutive windows. Membership in
    # a previous digest — not the clock — is what keeps it out the second time.
    store = {"a": _record(2), "b": _record(20)}
    assert len(mailer.new_roles(store)) == 2
    fresh = mailer.new_roles(store, already_sent={"x:20"})
    assert [r["id"] for r in fresh] == ["x:2"]
    assert mailer.new_roles(store, already_sent={"x:2", "x:20"}) == []


def test_sent_alias_settles_the_canonical_survivor():
    record = _record(
        2, id="greenhouse:new-board:2",
        aliases=["greenhouse:old-board:1"],
    )
    store = {record["id"]: record}
    assert mailer.new_roles(
        store, already_sent={"greenhouse:old-board:1"}, has_history=True,
    ) == []

    state = {"sent_role_ids": ["greenhouse:old-board:1"]}
    assert mailer._migrate_sent_role_ids(state, store)
    assert set(state["sent_role_ids"]) == {
        "greenhouse:new-board:2", "greenhouse:old-board:1",
    }


def test_corrupt_mail_state_is_fatal_and_preserved(tmp_path, monkeypatch):
    target = tmp_path / "mail_state.json"
    target.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(paths, "MAIL_STATE_PATH", str(target))

    with pytest.raises(mailer.MailStateCorrupt):
        mailer._load_state()
    assert target.read_text(encoding="utf-8") == "{not json"


def test_subscriber_fallback_requires_the_specific_missing_column(monkeypatch):
    request = httpx.Request("GET", "https://db.example/rest/v1/email_subscribers")
    bad = httpx.Response(
        400, request=request,
        json={"code": "PGRST100", "message": "bad filter syntax"},
    )
    calls = []
    monkeypatch.setattr(
        mailer.httpx, "get", lambda *_args, **_kwargs: calls.append(1) or bad,
    )

    with pytest.raises(httpx.HTTPStatusError):
        mailer._subscribers("https://db.example", "secret")
    assert len(calls) == 1


def test_subscriber_fallback_allows_only_legacy_missing_confirmed_column(monkeypatch):
    request = httpx.Request("GET", "https://db.example/rest/v1/email_subscribers")
    missing = httpx.Response(
        400, request=request,
        json={"code": "42703", "message": "column confirmed_at does not exist"},
    )
    legacy = httpx.Response(
        200, request=request,
        json=[{"email": "student@example.com", "unsub_token": "token"}],
    )
    responses = iter((missing, legacy))
    monkeypatch.setattr(
        mailer.httpx, "get", lambda *_args, **_kwargs: next(responses),
    )

    assert mailer._subscribers("https://db.example", "secret") == [
        {"email": "student@example.com", "unsub_token": "token"},
    ]


class TestRecipientRotation:
    """Everyone gets served in turn once the list outgrows the daily quota."""

    def _subs(self, n):
        return [{"email": f"u{i}@x.com", "unsub_token": f"t{i}"} for i in range(n)]

    def test_small_list_is_sent_whole(self):
        subs = self._subs(10)
        got, cursor = mailer._recipients(subs, cursor=0)
        assert got == subs
        assert cursor == 0

    def test_oversized_list_rotates_instead_of_starving_the_tail(self):
        total = mailer._MAX_SENDS + 40
        subs = self._subs(total)
        first, cursor = mailer._recipients(subs, cursor=0)
        assert len(first) == mailer._MAX_SENDS
        second, _ = mailer._recipients(subs, cursor)
        # The 40 who were cut off last time lead the next digest.
        assert second[0]["email"] == f"u{mailer._MAX_SENDS}@x.com"
        # Two rounds cover everyone.
        assert {s["email"] for s in first} | {s["email"] for s in second} == {
            s["email"] for s in subs
        }


def test_new_roles_newest_first_and_uncapped():
    # new_roles reports the TRUE count (for the subject line); the HTML body
    # is what caps at _MAX_ROLES.
    store = {str(i): _record(i / 2, id=str(i)) for i in range(1, 45)}
    fresh = mailer.new_roles(store)
    assert len(fresh) == 44
    seen = [r["first_seen_at"] for r in fresh]
    assert seen == sorted(seen, reverse=True)


def test_digest_html_caps_rows_and_says_plus_n_more():
    fresh = [_record(i / 4, id=str(i), company=f"Co{i}") for i in range(40)]
    html = mailer.build_digest_html(fresh)
    listed = html.count("border-bottom:1px solid #e6e8eb")
    assert listed == mailer._MAX_ROLES
    assert f"plus {40 - mailer._MAX_ROLES} more new roles" in html


# --- daily gate ----------------------------------------------------------------

def test_should_send_requires_news():
    assert mailer.should_send({}, fresh_count=0) is False
    assert mailer.should_send({}, fresh_count=3) is True


def test_should_send_at_most_daily():
    now = datetime.now(UTC)
    recent = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    old = (now - timedelta(hours=25)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert mailer.should_send({"last_digest_at": recent}, 5) is False
    assert mailer.should_send({"last_digest_at": old}, 5) is True


def test_should_send_does_not_allow_two_digests_inside_24_hours():
    now = datetime(2026, 8, 6, 23, tzinfo=UTC)
    same_day = (now - timedelta(hours=22)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert mailer.should_send({"last_digest_at": same_day}, 1, now=now) is False


# --- composition ---------------------------------------------------------------

def test_digest_html_lists_roles_and_unsub_slot():
    fresh = [
        _record(1, company="Stripe", title="Backend Intern", salary="$55/hr"),
        _record(2, company="Acme", sponsorship="no-sponsorship"),
    ]
    html = mailer.build_digest_html(fresh)
    assert "Stripe" in html and "Backend Intern" in html
    assert "$55/hr" in html
    assert "\U0001f6c2" in html            # 🛂 flag carried into the email
    assert "{{UNSUB_URL}}" in html          # per-recipient link slot survives


def test_sender_parsing(monkeypatch):
    monkeypatch.setenv("MAIL_FROM", "Intern Engine <alerts@example.com>")
    assert mailer._sender() == {"name": "Intern Engine", "email": "alerts@example.com"}
    monkeypatch.setenv("MAIL_FROM", "alerts@example.com")
    assert mailer._sender() == {"name": "Intern Engine", "email": "alerts@example.com"}
    monkeypatch.setenv("MAIL_FROM", "not-an-email")
    assert mailer._sender() is None


# --- the contract: unset env = silent no-op ------------------------------------

def test_send_digest_noop_without_env(monkeypatch):
    for var in ("BREVO_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "MAIL_FROM"):
        monkeypatch.delenv(var, raising=False)
    assert mailer.send_digest({"a": _record(1)}) == 0


class TestNewMeansUnsent:
    """"New" is decided by what we've sent, never by a clock window."""

    NOW = datetime(2026, 8, 2, 12, tzinfo=UTC)

    def _store(self, **ages_hours):
        return {
            jid: {"id": jid, "is_open": True,
                  "first_seen_at": (self.NOW - timedelta(hours=h))
                  .strftime("%Y-%m-%dT%H:%M:%SZ")}
            for jid, h in ages_hours.items()
        }

    def test_an_unsent_role_older_than_the_old_window_still_goes_out(self):
        # Regression: the fixed 48h window meant a role missed during a failed
        # run aged out and could NEVER be mailed. Nothing should be skipped.
        store = self._store(stale=100)
        fresh = mailer.new_roles(store, now=self.NOW, already_sent={"other"})
        assert [r["id"] for r in fresh] == ["stale"]

    def test_already_sent_roles_never_repeat(self):
        store = self._store(a=1, b=2)
        fresh = mailer.new_roles(store, now=self.NOW, already_sent={"a"})
        assert [r["id"] for r in fresh] == ["b"]

    def test_lost_state_does_not_mail_the_back_catalogue(self):
        # sent_role_ids empty but a digest HAS gone out before: the 14-day
        # backstop applies, so an ancient role stays out.
        store = self._store(recent=24, ancient=24 * 30)
        fresh = mailer.new_roles(store, now=self.NOW, already_sent=set(),
                                 has_history=True)
        assert [r["id"] for r in fresh] == ["recent"]

    def test_first_ever_digest_stays_tight(self):
        # No history at all: only the last 48h, so standing up the mailer
        # doesn't blast every open role at the whole list.
        store = self._store(new=6, older=72)
        fresh = mailer.new_roles(store, now=self.NOW, already_sent=set(),
                                 has_history=False)
        assert [r["id"] for r in fresh] == ["new"]

    def test_closed_roles_are_never_news(self):
        store = self._store(a=1)
        store["a"]["is_open"] = False
        assert mailer.new_roles(store, now=self.NOW, already_sent=set()) == []


class TestDigestSubject:
    """The subject is the only thing seen on a lock screen — it must say who."""

    def test_names_the_employers(self):
        fresh = [_record(0, id="1", company="Stripe"),
                 _record(1, id="2", company="Anduril")]
        assert mailer.digest_subject(fresh) == "2 new internships · Stripe, Anduril"

    def test_singular_reads_naturally(self):
        assert mailer.digest_subject([_record(0, id="1", company="Ramp")]) == \
            "1 new internship · Ramp"

    def test_long_lists_are_truncated_with_a_count(self):
        fresh = [_record(i, id=str(i), company=f"Co{i}") for i in range(7)]
        assert mailer.digest_subject(fresh) == "7 new internships · Co0, Co1, Co2 +4"

    def test_repeat_employers_are_named_once(self):
        fresh = [_record(0, id="1", company="Akuna"), _record(1, id="2", company="Akuna")]
        assert mailer.digest_subject(fresh) == "2 new internships · Akuna"

    def test_missing_company_names_do_not_break_it(self):
        assert mailer.digest_subject([_record(0, id="1", company="")]) == "1 new internship"


class TestDigestBody:
    def test_marks_remote_roles_and_h1b(self):
        html = mailer.build_digest_html([_record(0, id="1", location="Remote - US")])
        assert ">R<" in html

    def test_unstated_cycle_says_so_rather_than_guessing(self):
        html = mailer.build_digest_html([_record(0, id="1", season="Not stated")])
        assert "cycle not stated" in html

    def test_skills_render_as_pills(self):
        html = mailer.build_digest_html([_record(0, id="1", skills=["Python", "Go"])])
        assert ">Python<" in html and ">Go<" in html

    def test_titles_are_escaped(self):
        html = mailer.build_digest_html([_record(0, id="1", title="C++ <b>Dev</b> Intern")])
        assert "&lt;b&gt;" in html

    def test_summary_line_reports_the_split(self):
        fresh = [_record(0, id="1", season="Summer 2027"),
                 _record(1, id="2", season="Not stated")]
        html = mailer.build_digest_html(fresh)
        assert "1 with a stated cycle" in html


class TestDurableRecipientSettlement:
    def _setup(self, monkeypatch, tmp_path, fail_addresses):
        from intern_engine import paths

        monkeypatch.setattr(paths, "MAIL_STATE_PATH", str(tmp_path / "mail_state.json"))
        for key, value in {
            "BREVO_API_KEY": "brevo", "SUPABASE_URL": "https://db.example",
            "SUPABASE_SERVICE_KEY": "private-ledger-key",
            "MAIL_FROM": "alerts@example.com",
        }.items():
            monkeypatch.setenv(key, value)
        subscribers = [
            {"email": "ok@example.com", "unsub_token": "ok-token"},
            {"email": "failed@example.com", "unsub_token": "fail-token"},
        ]
        monkeypatch.setattr(mailer, "_subscribers", lambda *_: subscribers)
        monkeypatch.setattr(mailer, "_confirmation_requests", lambda *_: [])
        monkeypatch.setattr(mailer.time, "sleep", lambda *_: None)

        calls = []

        class Resp:
            def raise_for_status(self):
                return None

        class Client:
            def __init__(self, **_kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def post(self, _url, **kwargs):
                address = kwargs["json"]["to"][0]["email"]
                calls.append(address)
                if address in fail_addresses:
                    raise RuntimeError("provider failure")
                return Resp()

        monkeypatch.setattr(mailer.httpx, "Client", Client)
        return calls

    def test_partial_delivery_retries_only_failed_recipient(self, monkeypatch, tmp_path):
        failures = {"failed@example.com"}
        calls = self._setup(monkeypatch, tmp_path, failures)
        data = {"r": _record(1, id="role-1")}

        assert mailer.send_digest(data) == 1
        state = mailer._load_state()
        assert state["last_digest_failed"] == 1
        assert "pending_digest" in state
        assert "role-1" not in state.get("sent_role_ids", [])
        assert "failed@example.com" not in str(state)

        failures.clear()
        calls.clear()
        assert mailer.send_digest(data) == 1
        assert calls == ["failed@example.com"]
        state = mailer._load_state()
        assert "pending_digest" not in state
        assert state["sent_role_ids"] == ["role-1"]

    def test_wall_clock_deadline_persists_partial_settlement(self, monkeypatch, tmp_path):
        calls = self._setup(monkeypatch, tmp_path, set())
        # confirmation preflight, post-confirmation gate, first digest call,
        # then the deadline stops the second recipient.
        verdicts = iter((False, False, False, True))
        monkeypatch.setattr(
            mailer, "_deadline_reached", lambda _deadline: next(verdicts, True),
        )

        assert mailer.send_digest({"r": _record(1, id="role-1")}) == 1
        assert calls == ["ok@example.com"]
        state = mailer._load_state()
        assert state["last_digest_failed"] == 1
        assert len(state["pending_digest"]["delivered_keys"]) == 1

    def test_zero_success_still_persists_exact_pending_digest(self, monkeypatch, tmp_path):
        self._setup(monkeypatch, tmp_path, {"ok@example.com", "failed@example.com"})
        data = {"r": _record(1, id="role-1")}
        assert mailer.send_digest(data) == 0
        state = mailer._load_state()
        assert state["pending_digest"]["role_ids"] == ["role-1"]
        assert state["pending_digest"]["html"]
        assert state["last_digest_failed"] == 2
        assert len(state["retry_recipient_keys"]) == 2

    def test_empty_subscriber_snapshot_cannot_settle_pending_audience(
        self, monkeypatch, tmp_path,
    ):
        failures = {"ok@example.com", "failed@example.com"}
        self._setup(monkeypatch, tmp_path, failures)
        data = {"r": _record(1, id="role-1")}
        assert mailer.send_digest(data) == 0
        before = mailer._load_state()["pending_digest"]

        monkeypatch.setattr(mailer, "_subscribers", lambda *_args: [])
        failures.clear()
        assert mailer.send_digest(data) == 0

        state = mailer._load_state()
        assert state["pending_digest"] == before
        assert "role-1" not in state.get("sent_role_ids", [])

    def test_recipient_ledger_uses_secret_keyed_hmac(self):
        import hashlib

        address = "student@example.com"
        plain = hashlib.sha256(address.encode()).hexdigest()[:32]
        assert mailer._recipient_key(address, "secret") != plain


# --- identical openings --------------------------------------------------------

def _same_job(jid):
    return _record(1, id=jid, url=f"https://x/{jid}",
                   first_seen_at="2026-08-07T10:45:44Z")


def test_digest_prints_identical_requisitions_as_one_card():
    html = mailer.build_digest_html([_same_job(r) for r in ("a", "b", "c")])
    assert html.count("border-bottom:1px solid #e6e8eb") == 1
    assert "3 openings" in html


def test_a_folded_card_marks_every_id_as_sent():
    # sent_role_ids is what stops a role being mailed twice. If the two ids the
    # card absorbed were left unmarked, tomorrow's digest would mail them again
    # — which is exactly the duplicate-digest bug this list exists to prevent.
    fresh = [_same_job(r) for r in ("a", "b", "c")]
    assert sorted(mailer.listed_role_ids(fresh)) == ["a", "b", "c"]


def test_plus_n_more_counts_roles_not_cards():
    # 30 cards' worth of distinct roles, plus one job filed three times.
    fresh = [_record(i / 4, id=f"u{i}", company=f"Co{i}") for i in range(mailer._MAX_ROLES)]
    fresh += [_same_job(r) for r in ("a", "b", "c")]
    html = mailer.build_digest_html(fresh)
    assert "plus 3 more new role" in html


# --- cadence derived from the email budget --------------------------------------

def test_min_gap_is_daily_on_the_free_tier(monkeypatch):
    """224 addresses against Brevo's free 300/day affords exactly one send."""
    monkeypatch.delenv("MAIL_DAILY_QUOTA", raising=False)
    assert mailer.min_gap(224) == timedelta(hours=24)


def test_min_gap_shortens_as_the_budget_grows(monkeypatch):
    """The point of the whole change: a bigger plan buys instant alerts.

    Nothing about the code changes — raising the quota is the only dial.
    """
    monkeypatch.setenv("MAIL_DAILY_QUOTA", "20000")
    gap = mailer.min_gap(224)
    assert gap < timedelta(minutes=30)
    # ...and it stays inside the budget: one send per subscriber per gap must
    # not exceed what the plan allows in a day.
    sends_per_day = timedelta(hours=24) / gap
    assert sends_per_day * 224 <= mailer.send_budget()


def test_min_gap_never_goes_faster_than_the_budget_allows(monkeypatch):
    """A list too big for even one daily send must not be mailed twice a day."""
    monkeypatch.setenv("MAIL_DAILY_QUOTA", "100")
    assert mailer.min_gap(5000) == timedelta(hours=24)


def test_min_gap_falls_back_to_daily_when_the_list_size_is_unknown(monkeypatch):
    monkeypatch.setenv("MAIL_DAILY_QUOTA", "20000")
    assert mailer.min_gap(0) == timedelta(hours=24)


def test_should_send_uses_the_budget_cadence_not_a_flat_day(monkeypatch):
    monkeypatch.setenv("MAIL_DAILY_QUOTA", "20000")
    now = datetime(2026, 9, 15, 12, tzinfo=UTC)
    an_hour_ago = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Under the old flat 24-hour gate this was False no matter what you paid.
    assert mailer.should_send(
        {"last_digest_at": an_hour_ago}, 5, now=now, list_size=224
    ) is True


def test_should_send_still_refuses_an_empty_digest(monkeypatch):
    monkeypatch.setenv("MAIL_DAILY_QUOTA", "20000")
    now = datetime(2026, 9, 15, 12, tzinfo=UTC)
    old = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert mailer.should_send(
        {"last_digest_at": old}, 0, now=now, list_size=224
    ) is False


# --- delivery health ------------------------------------------------------------

def test_health_flags_the_supabase_pause_that_went_unnoticed():
    """The exact 2026-08-24 shape: roles waiting, ledger frozen, runs green."""
    now = datetime(2026, 9, 15, 7, tzinfo=UTC)
    state = {"last_digest_at": "2026-08-22T10:52:11Z"}
    ok, reason = mailer.health(state, pending_count=428, now=now)
    assert ok is False
    assert "no digest has gone out" in reason


def test_health_reports_a_recorded_failure_with_its_cause():
    now = datetime(2026, 9, 15, 7, tzinfo=UTC)
    state = {"last_error": {
        "at": "2026-09-15T06:00:00Z", "stage": "subscriber lookup",
        "detail": "ConnectError('project is paused')",
    }}
    ok, reason = mailer.health(state, pending_count=0, now=now)
    assert ok is False
    assert "subscriber lookup" in reason and "paused" in reason


def test_health_is_quiet_when_there_is_simply_nothing_to_send():
    now = datetime(2026, 9, 15, 7, tzinfo=UTC)
    state = {"last_digest_at": "2026-08-22T10:52:11Z"}
    ok, _ = mailer.health(state, pending_count=0, now=now)
    assert ok is True


def test_health_tolerates_a_recent_digest_with_roles_still_queued():
    now = datetime(2026, 9, 15, 7, tzinfo=UTC)
    recent = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ok, _ = mailer.health({"last_digest_at": recent}, pending_count=12, now=now)
    assert ok is True


class TestAnOutageIsNeverSilent:
    """The 2026-08-24 regression: Supabase paused, and nothing said so.

    Every exit from `send_digest` returned 0, which the runner printed as
    "not due" — identical to a healthy run with no news. The subscriber list
    was unreachable for 24 days and every Actions run stayed green.
    """

    def _configure(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            paths, "MAIL_STATE_PATH", str(tmp_path / "mail_state.json")
        )
        for key, value in {
            "BREVO_API_KEY": "brevo", "SUPABASE_URL": "https://db.example",
            "SUPABASE_SERVICE_KEY": "private-ledger-key",
            "MAIL_FROM": "alerts@example.com",
        }.items():
            monkeypatch.setenv(key, value)
        monkeypatch.setattr(mailer, "_confirmation_requests", lambda *_: [])

    def test_unreachable_subscriber_list_is_recorded_not_swallowed(
        self, monkeypatch, tmp_path
    ):
        self._configure(monkeypatch, tmp_path)

        def paused(*_args, **_kwargs):
            raise httpx.ConnectError("project is paused")

        monkeypatch.setattr(mailer, "_subscribers", paused)
        store = {"a": _record(1, id="a")}

        assert mailer.send_digest(store) == 0      # still never fatal...
        state = mailer.load_state()
        assert state["last_error"]["stage"] == "subscriber lookup"
        assert "paused" in state["last_error"]["detail"]

        # ...and the run now has something to shout about.
        ok, reason = mailer.health(state, pending_count=1)
        assert ok is False
        assert "subscriber lookup" in reason

    def test_an_empty_list_holds_the_digest_and_says_so(
        self, monkeypatch, tmp_path
    ):
        self._configure(monkeypatch, tmp_path)
        monkeypatch.setattr(mailer, "_subscribers", lambda *_: [])
        store = {"a": _record(1, id="a")}

        assert mailer.send_digest(store) == 0
        state = mailer.load_state()
        assert state["last_error"]["stage"] == "subscriber lookup"
        assert mailer.health(state, pending_count=1)[0] is False

    def test_half_configured_mailer_reports_the_missing_secret(
        self, monkeypatch, tmp_path
    ):
        """A rotated-away key must not look like "email isn't set up here"."""
        self._configure(monkeypatch, tmp_path)
        monkeypatch.delenv("BREVO_API_KEY")

        assert mailer.send_digest({"a": _record(1, id="a")}) == 0
        state = mailer.load_state()
        assert state["last_error"]["stage"] == "configuration"
        assert "BREVO_API_KEY" in state["last_error"]["detail"]

    def test_a_mailer_that_was_never_configured_stays_quiet(
        self, monkeypatch, tmp_path
    ):
        """No secrets at all is a deliberate opt-out, not a broken install."""
        monkeypatch.setattr(
            paths, "MAIL_STATE_PATH", str(tmp_path / "mail_state.json")
        )
        for key in ("BREVO_API_KEY", "SUPABASE_URL",
                    "SUPABASE_SERVICE_KEY", "MAIL_FROM"):
            monkeypatch.delenv(key, raising=False)

        assert mailer.send_digest({"a": _record(1, id="a")}) == 0
        assert mailer.load_state() == {}

    def test_a_clean_send_clears_a_previous_failure(self, monkeypatch, tmp_path):
        self._configure(monkeypatch, tmp_path)
        monkeypatch.setattr(mailer, "_subscribers", lambda *_: [
            {"email": "ok@example.com", "unsub_token": "tok"},
        ])
        monkeypatch.setattr(mailer.time, "sleep", lambda *_: None)

        class Resp:
            def raise_for_status(self):
                return None

        class Client:
            def __init__(self, *a, **k):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def post(self, *a, **k):
                return Resp()

        monkeypatch.setattr(mailer.httpx, "Client", Client)
        mailer._save_state({"last_error": {
            "at": "2026-09-01T00:00:00Z", "stage": "subscriber lookup",
            "detail": "boom",
        }})

        assert mailer.send_digest({"a": _record(1, id="a")}) == 1
        assert "last_error" not in mailer.load_state()


# --- coming back from an outage -------------------------------------------------

def _backlog(n: int) -> list[dict]:
    # Distinct employers on purpose: identical postings are deliberately folded
    # into one card, which would make the cap look like it wasn't applied.
    return [
        _record(float(i), id=f"r{i}", company=f"Acme{i}", url=f"https://x/{i}")
        for i in range(n)
    ]


def test_catch_up_digest_settles_the_whole_backlog():
    """A 428-role backlog must not drip 30 stale roles a day for a fortnight."""
    now = datetime(2026, 9, 15, 7, tzinfo=UTC)
    fresh = _backlog(60)
    state = {"last_digest_at": "2026-08-22T10:52:11Z"}  # 24 days stale
    settled = mailer.settling_role_ids(fresh, state, now=now)
    assert len(settled) == 60


def test_a_normal_busy_day_still_holds_the_overflow_back():
    """Unchanged where the old behaviour was right: nothing is dropped."""
    now = datetime(2026, 9, 15, 7, tzinfo=UTC)
    fresh = _backlog(60)
    recent = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    settled = mailer.settling_role_ids(fresh, {"last_digest_at": recent}, now=now)
    assert len(settled) == mailer._MAX_ROLES


def test_a_digest_that_fits_settles_exactly_what_it_printed():
    now = datetime(2026, 9, 15, 7, tzinfo=UTC)
    fresh = _backlog(5)
    state = {"last_digest_at": "2026-08-22T10:52:11Z"}
    assert len(mailer.settling_role_ids(fresh, state, now=now)) == 5
