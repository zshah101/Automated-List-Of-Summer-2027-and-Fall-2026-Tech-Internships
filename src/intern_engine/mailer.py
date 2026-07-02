"""Daily email digests to our own subscriber list (optional, best-effort).

The dashboard signup form inserts emails into Supabase (`email_subscribers`,
RLS: the public can sign up but never read the list). Each engine run calls
`send_digest`; it actually sends at most once a day, and only when there is
something new to say. Every email carries that subscriber's one-click
unsubscribe link (a per-subscriber secret token).

Sending goes through Brevo's transactional API (free tier: 300 emails/day,
no domain required — a verified sender address is enough). Like every
integration here: missing env vars = silent no-op, failures never break a run.

Env: BREVO_API_KEY, MAIL_FROM (verified sender, "Name <addr>" or bare),
     SUPABASE_URL, SUPABASE_SERVICE_KEY.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import UTC, datetime, timedelta
from html import escape

import httpx

from . import config, h1b, paths, sponsorship

_MIN_HOURS_BETWEEN = 22          # "daily", tolerant of cron jitter
_NEW_WINDOW_HOURS = 26           # a role counts as news if first seen in this window
_MAX_ROLES = 30                  # cap the digest body
_MAX_SENDS = 250                 # stay under Brevo's free 300/day
_BREVO_URL = "https://api.brevo.com/v3/smtp/email"


# --- state (committed, so CI runs share it) -----------------------------------

def _load_state() -> dict:
    try:
        with open(paths.MAIL_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    with open(paths.MAIL_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _parse_ts(value: str | None) -> datetime | None:
    try:
        return datetime.strptime((value or "")[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
    except ValueError:
        return None


def new_roles(store_data: dict, now: datetime | None = None) -> list[dict]:
    """Open roles first seen within the news window, newest first."""
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(hours=_NEW_WINDOW_HOURS)
    fresh = [
        r for r in store_data.values()
        if r.get("is_open") and (_parse_ts(r.get("first_seen_at")) or cutoff) > cutoff
    ]
    fresh.sort(key=lambda r: r.get("first_seen_at") or "", reverse=True)
    return fresh[:_MAX_ROLES]


def should_send(state: dict, fresh_count: int, now: datetime | None = None) -> bool:
    """At most one digest a day, and never an empty one."""
    if fresh_count == 0:
        return False
    now = now or datetime.now(UTC)
    last = _parse_ts(state.get("last_digest_at"))
    return last is None or (now - last) >= timedelta(hours=_MIN_HOURS_BETWEEN)


# --- composition ---------------------------------------------------------------

def _role_row(r: dict) -> str:
    flag = sponsorship.flag(r.get("sponsorship"))
    approvals = h1b.approvals_for(r.get("company") or "")
    check = " ✓" if h1b.badge(approvals) else ""
    bits = [b for b in (r.get("season"), r.get("location"), r.get("salary")) if b]
    return (
        '<tr><td style="padding:10px 0;border-bottom:1px solid #eee">'
        f'<strong>{escape(r.get("company") or "")}{check}</strong> — '
        f'<a href="{escape(r.get("url") or "")}">{escape(r.get("title") or "")}</a> {flag}'
        f'<br><span style="color:#666;font-size:13px">{escape(" · ".join(bits))}</span>'
        "</td></tr>"
    )


def build_digest_html(fresh: list[dict]) -> str:
    """The digest body; {{UNSUB_URL}} is replaced per recipient at send time."""
    repo = config.repo_slug()
    rows = "".join(_role_row(r) for r in fresh)
    return (
        '<div style="font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;'
        'max-width:640px;margin:0 auto;color:#1a1a1a">'
        f"<h2 style=\"font-size:18px\">{len(fresh)} new internship"
        f"{'s' if len(fresh) != 1 else ''} spotted</h2>"
        '<p style="color:#666;font-size:13px">✓ = the employer has a real H-1B '
        "track record (USCIS data) · 🇺🇸 = citizens only · 🛂 = no visa "
        "sponsorship — auto-detected, verify on the posting.</p>"
        f'<table style="width:100%;border-collapse:collapse">{rows}</table>'
        f'<p style="margin-top:18px"><a href="https://github.com/{escape(repo)}">'
        "Full list & tracker on GitHub</a> · "
        f'<a href="{config.pages_base()}/">live dashboard</a></p>'
        '<p style="color:#999;font-size:12px;margin-top:24px">You get this because '
        "you subscribed to new-internship alerts. "
        '<a href="{{UNSUB_URL}}" style="color:#999">Unsubscribe</a> anytime.</p>'
        "</div>"
    )


def _sender() -> dict | None:
    raw = (os.environ.get("MAIL_FROM") or "").strip()
    if not raw:
        return None
    m = re.match(r"^(.*?)\s*<([^<>@\s]+@[^<>\s]+)>$", raw)
    if m:
        return {"name": m.group(1).strip() or "Intern Engine", "email": m.group(2)}
    if "@" in raw:
        return {"name": "Intern Engine", "email": raw}
    return None


def _subscribers(base_url: str, service_key: str) -> list[dict]:
    resp = httpx.get(
        f"{base_url}/rest/v1/email_subscribers",
        params={"select": "email,unsub_token"},
        headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


# --- sending -------------------------------------------------------------------

def send_digest(store_data: dict) -> int:
    """Send today's digest if due. Returns how many emails went out."""
    api_key = os.environ.get("BREVO_API_KEY")
    base_url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    sender = _sender()
    if not api_key or not base_url or not service_key or not sender:
        return 0

    state = _load_state()
    fresh = new_roles(store_data)
    if not should_send(state, len(fresh)):
        return 0

    try:
        subscribers = _subscribers(base_url, service_key)
    except Exception:  # noqa: BLE001 — alerting is a side channel, never fatal
        return 0
    if not subscribers:
        return 0

    today = datetime.now(UTC).strftime("%b %d")
    subject = f"{len(fresh)} new internship{'s' if len(fresh) != 1 else ''} · {today}"
    body = build_digest_html(fresh)
    unsub_base = f"{config.pages_base()}/unsubscribe.html"

    sent = 0
    with httpx.Client(timeout=20) as client:
        for sub in subscribers[:_MAX_SENDS]:
            html = body.replace("{{UNSUB_URL}}", f"{unsub_base}?t={sub['unsub_token']}")
            try:
                client.post(
                    _BREVO_URL,
                    headers={"api-key": api_key, "Content-Type": "application/json"},
                    json={
                        "sender": sender,
                        "to": [{"email": sub["email"]}],
                        "subject": subject,
                        "htmlContent": html,
                    },
                ).raise_for_status()
                sent += 1
            except Exception:  # noqa: BLE001 — skip the bad address, keep going
                continue
            time.sleep(0.12)  # stay well under Brevo's request rate

    if sent:
        state["last_digest_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        state["last_digest_roles"] = len(fresh)
        state["last_digest_sent"] = sent
        _save_state(state)
    return sent
