"""Digest mailer: gating, composition, and the no-op-without-config contract."""

from datetime import UTC, datetime, timedelta

from intern_engine import mailer


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
        "b": _record(30),               # too old
        "c": _record(1, is_open=False),  # closed
    }
    fresh = mailer.new_roles(store)
    assert [r["id"] for r in fresh] == ["a:2"] or len(fresh) == 1


def test_new_roles_newest_first_and_capped():
    store = {str(i): _record(i, id=str(i)) for i in range(1, 40)}
    fresh = mailer.new_roles(store)
    assert len(fresh) <= mailer._MAX_ROLES
    seen = [r["first_seen_at"] for r in fresh]
    assert seen == sorted(seen, reverse=True)


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
