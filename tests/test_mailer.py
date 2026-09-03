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
    assert "{{UNSUB_URL}}" in html          # per-recipient link slot survives


def test_visa_flags_follow_the_tracked_region(monkeypatch):
    """🛂 is a US visa verdict, so it ships only on a digest of US roles.

    On the Southeast Asia list the classifier still runs (its text is shared
    with skills and cycle extraction), but its US-immigration reading is not
    something to put in front of a reader it does not apply to.
    """
    fresh = [_record(1, company="Acme", sponsorship="no-sponsorship")]

    monkeypatch.setattr(mailer.config, "load_config", lambda: {"regions": ["US"]})
    assert "🛂" in mailer.build_digest_html(fresh)

    monkeypatch.setattr(mailer.config, "load_config", lambda: {"regions": ["SEA"]})
    assert "🛂" not in mailer.build_digest_html(fresh)


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
