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

import hashlib
import hmac
import json
import os
import re
import time
from datetime import UTC, datetime, timedelta
from html import escape
from urllib.parse import quote

import httpx

from . import config, filters, grouping, h1b, paths, sponsorship

_MIN_HOURS_BETWEEN = 24          # a real rolling day; never double-spend quota
# Backstop only — NOT the definition of "new". `sent_role_ids` decides that.
# This bound exists for one situation: if mail state is ever lost or reset, the
# next digest must not mail the entire back catalogue. Under normal operation
# every role is sent within a day, so this never binds.
_MAX_LOOKBACK_DAYS = 14
# A first-ever digest (no send history at all) stays tight, so standing up the
# mailer doesn't blast every open role at the whole list.
_COLD_START_HOURS = 48
_MAX_ROLES = 30                  # cap the digest body
_MAX_SENDS = 250                 # stay under Brevo's free 300/day
_MAX_CONFIRMATIONS = 25          # reserve most daily capacity for the digest
_BREVO_URL = "https://api.brevo.com/v3/smtp/email"
_NOTIFY_DEADLINE_SECONDS = 8 * 60
_REQUEST_TIMEOUT = httpx.Timeout(8.0, connect=4.0)


# --- state (committed, so CI runs share it) -----------------------------------


class MailStateCorrupt(RuntimeError):
    """The durable delivery ledger exists but cannot be trusted."""

def _load_state() -> dict:
    if not os.path.exists(paths.MAIL_STATE_PATH):
        return {}
    try:
        with open(paths.MAIL_STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise MailStateCorrupt(
            f"{paths.MAIL_STATE_PATH} is unreadable: {exc}"
        ) from exc
    try:
        return _validate_state(state)
    except MailStateCorrupt as exc:
        raise MailStateCorrupt(f"{paths.MAIL_STATE_PATH}: {exc}") from exc


def _save_state(state: dict) -> None:
    _validate_state(state)
    os.makedirs(os.path.dirname(paths.MAIL_STATE_PATH), exist_ok=True)
    tmp = f"{paths.MAIL_STATE_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, paths.MAIL_STATE_PATH)


def _parse_ts(value: str | None) -> datetime | None:
    try:
        return datetime.strptime((value or "")[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
    except (TypeError, ValueError):
        return None


def _validate_state(state: object) -> dict:
    """Validate every delivery-critical field while accepting legacy keys."""
    if not isinstance(state, dict):
        raise MailStateCorrupt("mail state must be an object")

    list_fields = ("sent_role_ids", "retry_emails", "retry_recipient_keys")
    for field in list_fields:
        value = state.get(field)
        if value is not None and (
            not isinstance(value, list)
            or not all(isinstance(item, str) and item for item in value)
        ):
            raise MailStateCorrupt(f"{field} must be a list of identifiers")

    int_fields = (
        "last_digest_roles", "last_digest_sent", "last_digest_failed",
        "subscribers_total", "send_cursor",
    )
    for field in int_fields:
        value = state.get(field)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise MailStateCorrupt(f"{field} must be a non-negative integer")
    if state.get("last_digest_at") is not None and _parse_ts(
        state.get("last_digest_at")
    ) is None:
        raise MailStateCorrupt("last_digest_at must be a timestamp")

    attempts = state.get("send_attempts")
    if attempts is not None:
        if not isinstance(attempts, list):
            raise MailStateCorrupt("send_attempts must be a list")
        for attempt in attempts:
            if (
                not isinstance(attempt, dict)
                or _parse_ts(attempt.get("at")) is None
                or isinstance(attempt.get("count"), bool)
                or not isinstance(attempt.get("count"), int)
                or attempt["count"] <= 0
            ):
                raise MailStateCorrupt("send_attempts contains an invalid entry")

    pending = state.get("pending_digest")
    if pending is not None:
        if not isinstance(pending, dict):
            raise MailStateCorrupt("pending_digest must be an object")
        for field in (
            "role_ids", "listed_role_ids", "recipient_keys", "delivered_keys",
        ):
            value = pending.get(field)
            if not isinstance(value, list) or not all(
                isinstance(item, str) and item for item in value
            ):
                raise MailStateCorrupt(
                    f"pending_digest.{field} must be a list of identifiers"
                )
        for field in ("subject", "html"):
            if not isinstance(pending.get(field), str) or not pending[field]:
                raise MailStateCorrupt(f"pending_digest.{field} must be text")
        count = pending.get("role_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise MailStateCorrupt("pending_digest.role_count must be an integer")
        if not set(pending["delivered_keys"]).issubset(pending["recipient_keys"]):
            raise MailStateCorrupt("pending delivered recipients were not intended")
        created = pending.get("created_at")
        if created is not None and _parse_ts(created) is None:
            raise MailStateCorrupt("pending_digest.created_at must be a timestamp")
    return state


_SENT_MEMORY = 2000  # ids we remember; ~2 months of digests at current volume


def _role_identity_ids(record: dict, fallback: str | None = None) -> set[str]:
    ids = {
        str(value) for value in (record.get("id"), fallback)
        if isinstance(value, str) and value
    }
    ids.update(
        str(value) for value in (record.get("aliases") or ())
        if isinstance(value, str) and value
    )
    return ids


def _identity_index(store_data: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for key, record in store_data.items():
        for identity in _role_identity_ids(record, str(key)):
            index[identity] = record
    return index


def _migrate_sent_role_ids(state: dict, store_data: dict) -> bool:
    """Expand legacy presentation IDs to the current canonical identity set."""
    sent = list(state.get("sent_role_ids") or ())
    if not sent:
        return False
    index = _identity_index(store_data)
    migrated: list[str] = []
    for identity in sent:
        record = index.get(identity)
        values = _role_identity_ids(record) if record is not None else {identity}
        for value in sorted(values):
            if value not in migrated:
                migrated.append(value)
    migrated = migrated[-_SENT_MEMORY:]
    if migrated == sent:
        return False
    state["sent_role_ids"] = migrated
    return True


def new_roles(store_data: dict, now: datetime | None = None,
              already_sent: set[str] | None = None,
              has_history: bool | None = None) -> list[dict]:
    """Every open role the list hasn't been told about yet, newest first.

    "New" means *not yet sent* — full stop. It used to mean "first seen in the
    last N hours", which was wrong in both directions: a role could sit inside
    two consecutive windows and go out twice (2026-07-17: 26 of 30 roles were
    repeats), and a role that missed its window during a failed run could never
    be sent at all. `sent_role_ids` is now the only thing that decides, so
    nothing repeats and nothing is skipped.

    The clock survives only as a backstop. If mail state is lost,
    `_MAX_LOOKBACK_DAYS` stops the next digest mailing the back catalogue; on a
    first-ever digest `_COLD_START_HOURS` keeps it tighter still. Neither
    bound binds during normal operation.

    No cap here — the subject line reports the true count; the HTML body caps
    what it lists (and says "+N more") at composition time.
    """
    now = now or datetime.now(UTC)
    already_sent = already_sent or set()
    if has_history is None:
        has_history = bool(already_sent)
    span = timedelta(days=_MAX_LOOKBACK_DAYS) if has_history \
        else timedelta(hours=_COLD_START_HOURS)
    cutoff = now - span
    fresh = [
        r for r in store_data.values()
        if r.get("is_open")
        and (_parse_ts(r.get("first_seen_at")) or cutoff) > cutoff
        and not _role_identity_ids(r).intersection(already_sent)
    ]
    fresh.sort(key=lambda r: r.get("first_seen_at") or "", reverse=True)
    return fresh


def should_send(state: dict, fresh_count: int, now: datetime | None = None) -> bool:
    """At most one digest a day, and never an empty one."""
    if fresh_count == 0:
        return False
    now = now or datetime.now(UTC)
    last = _parse_ts(state.get("last_digest_at"))
    return last is None or (now - last) >= timedelta(hours=_MIN_HOURS_BETWEEN)


# --- composition ---------------------------------------------------------------

def _pill(text: str, bg: str, fg: str) -> str:
    return (f'<span style="display:inline-block;background:{bg};color:{fg};'
            f'border-radius:5px;padding:2px 7px;font-size:11px;font-weight:700;'
            f'line-height:1.5;white-space:nowrap">{escape(text)}</span>')


def _role_row(r: dict, us_context: bool = True) -> str:
    """One role as a card: employer line, linked title, facts, skills.

    Written for email clients, which means tables and inline styles only — no
    flexbox, no <style> block, no external CSS. Colours are chosen to stay
    legible on both white and dark backgrounds, since Gmail/Outlook dark mode
    inverts backgrounds but not inline text colours.
    """
    company = escape(r.get("company") or "")
    marks = ""
    # The H-1B badge and the visa flag are US immigration records; on a digest
    # of roles from a region that data doesn't cover they claim nothing.
    if us_context and h1b.badge(h1b.approvals_for(r.get("company") or "")):
        marks += ' <span style="color:#1a7f37" title="proven H-1B sponsor">✓</span>'
    if filters.is_remote(r.get("location") or "", r.get("title") or ""):
        marks += " " + _pill("R", "#dafbe1", "#1a7f37")

    cycle = r.get("season")
    cycle_pill = (_pill(cycle, "#ddf4ff", "#0550ae")
                  if cycle and cycle != "Not stated"
                  else _pill("cycle not stated", "#f6f8fa", "#57606a"))

    facts = [b for b in (r.get("location"), r.get("salary")) if b]
    openings = r.get("openings") or 1
    if openings > 1:
        facts.append(f"{openings} openings")
    flag = sponsorship.flag(r.get("sponsorship")) if us_context else ""
    if flag:
        facts.append(flag)
    skills = " ".join(_pill(s, "#f6f8fa", "#57606a") for s in (r.get("skills") or [])[:4])

    return (
        '<tr><td style="padding:14px 0;border-bottom:1px solid #e6e8eb">'
        f'<div style="font-size:15px;font-weight:700;color:#1a1a1a">{company}{marks}'
        f'&nbsp;&nbsp;{cycle_pill}</div>'
        f'<div style="margin:3px 0 5px"><a href="{escape(r.get("url") or "")}" '
        'style="font-size:15px;color:#0969da;text-decoration:none">'
        f'{escape(r.get("title") or "")}</a></div>'
        f'<div style="color:#57606a;font-size:13px">{escape(" · ".join(facts))}</div>'
        + (f'<div style="margin-top:6px">{skills}</div>' if skills else "")
        + "</td></tr>"
    )


def _digest_rows(fresh: list[dict]) -> list[dict]:
    """The cards this digest actually prints, identical openings folded once.

    An employer filing three copies of one requisition used to spend three of
    the thirty card slots saying the same thing. One card that says "3
    openings" is both shorter and more informative.
    """
    return grouping.group(fresh)[:_MAX_ROLES]


def listed_role_ids(fresh: list[dict]) -> list[str]:
    """Every requisition id a printed card stands for.

    `sent_role_ids` is what stops a role being mailed twice, so a card that
    folded three ids has to mark all three as sent — otherwise the two it
    absorbed look unsent and come back in tomorrow's digest.
    """
    return [
        rid
        for row in _digest_rows(fresh)
        for rid in (row.get("opening_ids") or [row.get("id")])
        if rid
    ]


def build_digest_html(fresh: list[dict]) -> str:
    """The digest body; {{UNSUB_URL}} is replaced per recipient at send time.

    Lists the newest _MAX_ROLES; a bigger day gets a "+N more" pointer instead
    of a 60-row email.
    """
    repo = config.repo_slug()
    shown = _digest_rows(fresh)
    us_context = config.want_us(config.load_config())
    rows = "".join(_role_row(r, us_context) for r in shown)
    # "…plus N more" counts ROLES the reader can't see here, so it has to
    # subtract the requisitions the printed cards already account for, not the
    # number of cards.
    extra = len(fresh) - sum(r.get("openings") or 1 for r in shown)
    if extra > 0:
        rows += (
            '<tr><td style="padding:10px 0;color:#666">'
            f'…plus {extra} more new role{"s" if extra != 1 else ""} on '
            f'<a href="{config.pages_base()}/">the live dashboard</a>.'
            "</td></tr>"
        )
    stated = sum(1 for r in fresh if (r.get("season") or "Not stated") != "Not stated")
    remote = sum(1 for r in fresh
                 if filters.is_remote(r.get("location") or "", r.get("title") or ""))
    summary = [f"{len(fresh)} new"]
    if stated:
        summary.append(f"{stated} with a stated cycle")
    if remote:
        summary.append(f"{remote} remote")

    return (
        '<div style="font:15px/1.55 -apple-system,BlinkMacSystemFont,Segoe UI,'
        'Roboto,Helvetica,Arial,sans-serif;max-width:640px;margin:0 auto;'
        'color:#1a1a1a;padding:0 4px">'
        f'<div style="font-size:22px;font-weight:800;letter-spacing:-.02em">'
        f"{len(fresh)} new internship{'s' if len(fresh) != 1 else ''}</div>"
        f'<div style="color:#57606a;font-size:13px;margin:4px 0 2px">'
        f'{escape(" · ".join(summary))}</div>'
        f'<table style="width:100%;border-collapse:collapse">{rows}</table>'
        f'<div style="margin:22px 0 6px">'
        f'<a href="{config.pages_base()}/" style="display:inline-block;'
        'background:#0969da;color:#fff;text-decoration:none;font-weight:700;'
        'font-size:14px;padding:10px 18px;border-radius:7px">'
        "Open the dashboard</a></div>"
        '<div style="color:#57606a;font-size:12px;margin-top:14px;line-height:1.6">'
        + ("<b>✓</b> the employer has a real H-1B track record (USCIS data) · "
           "<b>R</b> this role is remote · 🇺🇸 citizens only · 🛂 no visa "
           "sponsorship.<br>Sponsorship flags are auto-detected from the "
           "posting text — treat them as a strong hint and confirm on the "
           "posting itself." if us_context else
           "<b>R</b> this role is remote.")
        + "</div>"
        f'<div style="color:#8c959f;font-size:12px;margin-top:18px;'
        'border-top:1px solid #e6e8eb;padding-top:12px">'
        f'<a href="https://github.com/{escape(repo)}" style="color:#8c959f">'
        "GitHub</a> · You subscribed to new-internship alerts. "
        '<a href="{{UNSUB_URL}}" style="color:#8c959f">Unsubscribe</a>.</div>'
        "</div>"
    )


def digest_subject(fresh: list[dict], now: datetime | None = None) -> str:
    """Subject line that names employers instead of just counting.

    "3 new internships · Aug 06" told you nothing you could act on from the
    lock screen. Leading with the companies is what makes it worth opening.
    """
    n = len(fresh)
    names: list[str] = []
    for r in fresh:
        name = (r.get("company") or "").strip()
        if name and name not in names:
            names.append(name)
    lead = ", ".join(names[:3])
    if len(names) > 3:
        lead += f" +{len(names) - 3}"
    head = f"{n} new internship{'s' if n != 1 else ''}"
    return f"{head} · {lead}" if lead else head


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
    url = f"{base_url}/rest/v1/email_subscribers"
    headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}
    resp = httpx.get(url, params={
        "select": "email,unsub_token", "confirmed_at": "not.is.null",
        "order": "email.asc",
    }, headers=headers, timeout=_REQUEST_TIMEOUT)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError:
        # Deployment-safe migration: an installation that has not applied the
        # double-opt-in columns yet keeps its existing confirmed list working.
        # Never treat an arbitrary bad query as that migration state: doing so
        # would bypass the confirmation filter and mail unconfirmed addresses.
        try:
            error = resp.json()
        except ValueError:
            error = {}
        detail = " ".join(
            str(error.get(field) or "")
            for field in ("message", "details", "hint")
        ).casefold() if isinstance(error, dict) else ""
        if not (
            resp.status_code == 400
            and isinstance(error, dict)
            and str(error.get("code") or "") == "42703"
            and "confirmed_at" in detail
        ):
            raise
        resp = httpx.get(
            url, params={"select": "email,unsub_token", "order": "email.asc"},
            headers=headers, timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    return sorted(
        resp.json(), key=lambda s: (s.get("email") or "").strip().casefold()
    )


def _confirmation_requests(base_url: str, service_key: str) -> list[dict]:
    """Pending double-opt-in requests; absent migration means no-op."""
    resp = httpx.get(
        f"{base_url}/rest/v1/email_subscribers",
        params={
            "select": "email,confirmation_token", "confirmed_at": "is.null",
            "confirmation_sent_at": "is.null", "order": "created_at.asc",
            "limit": str(_MAX_CONFIRMATIONS),
        },
        headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
        timeout=_REQUEST_TIMEOUT,
    )
    if resp.status_code == 400:  # schema migration not deployed yet
        return []
    resp.raise_for_status()
    return resp.json()


def _recipients(subscribers: list[dict], cursor: int) -> tuple[list[dict], int]:
    """Today's slice of the list, and where the next digest should resume.

    The daily quota (_MAX_SENDS) is smaller than the list will eventually be.
    Always mailing `subscribers[:250]` meant everyone past that point silently
    never received a digest — and they'd have no way to tell. Rotating the
    start point instead means a list of any size gets served in turn, so the
    failure mode degrades from "starved forever" to "hears from us less often".
    """
    total = len(subscribers)
    if total <= _MAX_SENDS:
        return subscribers, 0
    start = cursor % total
    ordered = subscribers[start:] + subscribers[:start]
    return ordered[:_MAX_SENDS], (start + _MAX_SENDS) % total


def _recipient_key(address: str, secret: str) -> str:
    """Opaque delivery-ledger key for an address.

    `mail_state.json` is public. A plain email hash is dictionary-reversible;
    this HMAC is keyed by the private Supabase service key and reveals no
    subscriber address.
    """
    return hmac.new(
        secret.encode(), address.strip().casefold().encode(), hashlib.sha256
    ).hexdigest()[:32]


def _subscriber_key(subscriber: dict, secret: str) -> str:
    """Stable opaque id based on a subscriber's random unsubscribe secret.

    Hashing a 192-bit random token is safe to publish and, unlike an HMAC tied
    to the Supabase service key, survives routine service-key rotation.
    """
    token = str(subscriber.get("unsub_token") or "")
    if token:
        return hashlib.sha256(f"unsubscribe:{token}".encode()).hexdigest()[:32]
    return _recipient_key(subscriber.get("email") or "", secret)


def _order_with_retries(recipients: list[dict], retry: set[str],
                        secret: str = "") -> list[dict]:
    """Yesterday's failed recipients go first, so a transient provider error
    costs them one day, not their place in line."""
    if not retry:
        return recipients
    # The fallback understands legacy public SHA fingerprints during migration;
    # new state always uses the HMAC path.
    if secret:
        key = lambda s: _recipient_key(s.get("email") or "", secret)  # noqa: E731
    else:
        key = lambda s: hashlib.sha256(  # noqa: E731
            (s.get("email") or "").strip().casefold().encode()
        ).hexdigest()[:16]
    front = [s for s in recipients if key(s) in retry]
    rest = [s for s in recipients if key(s) not in retry]
    return front + rest


def _attempt_capacity(state: dict, now: datetime) -> int:
    """Provider calls still available in the rolling 24-hour safety window."""
    cutoff = now - timedelta(hours=24)
    kept: list[dict] = []
    used = 0
    for item in state.get("send_attempts") or ():
        if not isinstance(item, dict):
            continue
        at = _parse_ts(item.get("at"))
        count = int(item.get("count") or 0)
        if at and at > cutoff and count > 0:
            kept.append({"at": item["at"], "count": count})
            used += count
    state["send_attempts"] = kept
    return max(0, _MAX_SENDS - used)


def _record_attempt(state: dict, now: datetime) -> None:
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    attempts = state.setdefault("send_attempts", [])
    if attempts and attempts[-1].get("at") == stamp:
        attempts[-1]["count"] = int(attempts[-1].get("count") or 0) + 1
    else:
        attempts.append({"at": stamp, "count": 1})


def _deadline_reached(deadline: float) -> bool:
    return time.monotonic() >= deadline


def _send_confirmations(api_key: str, base_url: str, service_key: str,
                        sender: dict, state: dict, now: datetime,
                        deadline: float = float("inf")) -> int:
    """Send mailbox-ownership links without exposing pending addresses."""
    if _deadline_reached(deadline):
        return 0
    capacity = min(_MAX_CONFIRMATIONS, _attempt_capacity(state, now))
    if capacity <= 0:
        return 0
    try:
        requests = _confirmation_requests(base_url, service_key)
    except Exception:  # noqa: BLE001 — confirmation is also a side channel
        return 0
    sent = 0
    headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}",
               "Content-Type": "application/json", "Prefer": "return=minimal"}
    with httpx.Client(timeout=_REQUEST_TIMEOUT) as client:
        for request in requests[:capacity]:
            if _deadline_reached(deadline):
                break
            address = (request.get("email") or "").strip()
            token = request.get("confirmation_token") or ""
            if not address or not token:
                continue
            link = f"{config.pages_base()}/confirm.html?t={quote(token, safe='')}"
            _record_attempt(state, now)
            try:
                client.post(
                    _BREVO_URL,
                    headers={"api-key": api_key, "Content-Type": "application/json"},
                    json={
                        "sender": sender, "to": [{"email": address}],
                        "subject": "Confirm Internship Engine email alerts",
                        "htmlContent": (
                            '<div style="font:15px/1.55 -apple-system,Segoe UI,sans-serif">'
                            "<h2>Confirm your internship alerts</h2>"
                            "<p>Someone requested daily Internship Engine alerts for this "
                            "address. Confirm only if that was you.</p>"
                            f'<p><a href="{escape(link)}">Confirm email alerts</a></p>'
                            "<p>If you did not request this, ignore this email; no digest "
                            "will be sent.</p></div>"
                        ),
                    },
                ).raise_for_status()
                client.patch(
                    f"{base_url}/rest/v1/email_subscribers",
                    params={"confirmation_token": f"eq.{token}"}, headers=headers,
                    json={"confirmation_sent_at": now.strftime("%Y-%m-%dT%H:%M:%SZ")},
                ).raise_for_status()
                sent += 1
            except Exception:  # noqa: BLE001 — leave request eligible for retry
                pass
            _save_state(state)  # attempt quota survives zero-success runs
            time.sleep(0.12)
    return sent


def pending_roles(store_data: dict, state: dict | None = None,
                  now: datetime | None = None) -> list[dict]:
    """The exact role set production would put in a pending/new digest."""
    state = state if state is not None else _load_state()
    pending = state.get("pending_digest") or {}
    if pending:
        index = _identity_index(store_data)
        roles: list[dict] = []
        seen: set[str] = set()
        for identity in pending.get("role_ids") or ():
            record = index.get(identity)
            if record is None:
                continue
            owner = str(record.get("id") or identity)
            if owner not in seen:
                seen.add(owner)
                roles.append(record)
        return roles
    already_sent = set(state.get("sent_role_ids") or ())
    has_history = bool(already_sent or state.get("last_digest_at"))
    return new_roles(
        store_data, now=now, already_sent=already_sent, has_history=has_history
    )


def compose_pending_digest(store_data: dict, state: dict | None = None,
                           now: datetime | None = None) -> tuple[list[dict], str, str]:
    """Production/preview parity: roles, subject, and exact HTML template."""
    state = state if state is not None else _load_state()
    roles = pending_roles(store_data, state, now=now)
    pending = state.get("pending_digest") or {}
    if pending:
        return (
            roles,
            str(pending.get("subject") or digest_subject(roles)),
            str(pending.get("html") or build_digest_html(roles)),
        )
    return roles, digest_subject(roles), build_digest_html(roles) if roles else ""


# --- sending -------------------------------------------------------------------

def send_digest(store_data: dict) -> int:
    """Send/resume a digest, settling every intended recipient independently.

    A pending digest is written *before* the first provider call and contains
    the exact public body/subject plus opaque recipient keys. Successful keys
    settle individually; failures remain pending and are the first work on the
    next run. Roles become globally sent only after the whole intended audience
    has settled, so one successful address can never erase another's email.
    """
    api_key = os.environ.get("BREVO_API_KEY")
    base_url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    sender = _sender()
    if not api_key or not base_url or not service_key or not sender:
        return 0

    deadline = time.monotonic() + _NOTIFY_DEADLINE_SECONDS
    state = _load_state()
    if _migrate_sent_role_ids(state, store_data):
        _save_state(state)
    now = datetime.now(UTC)
    _send_confirmations(
        api_key, base_url, service_key, sender, state, now, deadline,
    )
    if _deadline_reached(deadline):
        return 0
    pending = state.get("pending_digest") or None
    fresh = pending_roles(store_data, state, now=now) if pending is None else []
    if pending is None and not should_send(state, len(fresh), now=now):
        return 0
    try:
        subscribers = _subscribers(base_url, service_key)
    except Exception:  # noqa: BLE001 — alerting is a side channel, never fatal
        return 0
    subscribers = [s for s in subscribers
                   if (s.get("email") or "").strip() and s.get("unsub_token")]
    if not subscribers:
        # An existing pending digest has a durable intended audience. A
        # transient successful-but-empty subscriber snapshot is not evidence
        # that every one of them unsubscribed; settling them all would silently
        # drop the digest and mark its roles sent. Keep it pending for retry.
        return 0

    # Map the private subscriber rows to public-safe opaque keys. Case variants
    # intentionally collapse to one delivery even on an older database whose
    # unique constraint was case-sensitive.
    by_email: dict[str, dict] = {}
    for sub in subscribers:
        by_email.setdefault(sub["email"].strip().casefold(), sub)
    subscribers = list(by_email.values())
    by_key = {_subscriber_key(sub, service_key): sub for sub in subscribers}

    if pending is None:
        # Legacy failures are promoted ahead of the regular stable order for
        # the one migration digest, then removed in favour of HMAC ledger keys.
        subscribers = _order_with_retries(
            subscribers, {str(v) for v in state.get("retry_emails") or ()}
        )
        recipient_keys = list(dict.fromkeys(
            _subscriber_key(s, service_key) for s in subscribers
        ))
        if not recipient_keys:
            return 0
        listed_ids = listed_role_ids(fresh)
        pending = {
            "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "role_ids": [r["id"] for r in fresh if r.get("id")],
            "listed_role_ids": listed_ids,
            "role_count": len(fresh),
            "subject": digest_subject(fresh),
            "html": build_digest_html(fresh),
            "recipient_keys": recipient_keys,
            "delivered_keys": [],
        }
        state["pending_digest"] = pending
        state.pop("retry_emails", None)
        state.pop("send_cursor", None)
        _save_state(state)  # durable even if every provider call fails

    subject = str(pending.get("subject") or "Internship digest")
    body = str(pending.get("html") or "")
    unsub_base = f"{config.pages_base()}/unsubscribe.html"
    intended = list(dict.fromkeys(str(k) for k in pending.get("recipient_keys") or ()))
    delivered = set(str(k) for k in pending.get("delivered_keys") or ())
    # A subscriber who has since unsubscribed is settled without sending.
    delivered.update(k for k in intended if k not in by_key)
    pending["delivered_keys"] = [k for k in intended if k in delivered]
    capacity = _attempt_capacity(state, now)
    outstanding = [k for k in intended if k not in delivered and k in by_key]
    sent = 0
    with httpx.Client(timeout=_REQUEST_TIMEOUT) as client:
        for recipient_key in outstanding[:capacity]:
            if _deadline_reached(deadline):
                break
            sub = by_key[recipient_key]
            address = (sub.get("email") or "").strip()
            token = sub.get("unsub_token") or ""
            unsub_url = f"{unsub_base}?t={token}"
            html = body.replace("{{UNSUB_URL}}", unsub_url)
            _record_attempt(state, now)
            try:
                client.post(
                    _BREVO_URL,
                    headers={"api-key": api_key, "Content-Type": "application/json"},
                    json={
                        "sender": sender,
                        "to": [{"email": address}],
                        "subject": subject,
                        "htmlContent": html,
                        # List-Unsubscribe gives every mail client its native
                        # "unsubscribe" button, pointing at our confirmation
                        # page. List-Unsubscribe-Post is deliberately NOT sent:
                        # RFC 8058 one-click requires an endpoint that handles
                        # a POST, and a static Pages file can't. Advertising it
                        # would make providers POST into a 405 and count the
                        # unsubscribe as failed.
                        "headers": {
                            "List-Unsubscribe": f"<{unsub_url}>",
                        },
                    },
                ).raise_for_status()
                sent += 1
                delivered.add(recipient_key)
            except Exception:  # noqa: BLE001 — skip the bad address, keep going
                pass
            pending["delivered_keys"] = [k for k in intended if k in delivered]
            # Persist each response. A later provider failure cannot erase the
            # successes that preceded it, and zero-success runs retain pending.
            _save_state(state)
            time.sleep(0.12)  # stay well under Brevo's request rate

    remaining = [k for k in intended if k not in delivered and k in by_key]
    state["last_digest_roles"] = int(pending.get("role_count") or 0)
    state["last_digest_sent"] = len(delivered)
    state["last_digest_failed"] = len(remaining)
    state["retry_recipient_keys"] = remaining
    state["subscribers_total"] = len(subscribers)
    if not remaining:
        state["last_digest_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        index = _identity_index(store_data)
        settled: list[str] = []
        for identity in pending.get("listed_role_ids") or ():
            record = index.get(identity)
            settled.extend(sorted(
                _role_identity_ids(record) if record is not None else {identity}
            ))
        remembered = list(state.get("sent_role_ids") or ()) + settled
        state["sent_role_ids"] = remembered[-_SENT_MEMORY:]  # oldest drop off
        state.pop("pending_digest", None)
        state.pop("retry_recipient_keys", None)
    _save_state(state)
    return sent
