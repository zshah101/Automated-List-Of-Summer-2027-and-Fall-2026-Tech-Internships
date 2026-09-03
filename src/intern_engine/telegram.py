"""Telegram push alerts for newly spotted roles (optional, best-effort).

Why Telegram and not SMS: real SMS costs money per message, and the free
workaround — carrier email-to-SMS gateways like number@vtext.com — is actively
being switched off (AT&T ended theirs in 2025). Telegram's Bot API is free,
unlimited, delivers a real lock-screen push, and is not going to be
deprecated out from under us.

Setup is two minutes:
  1. Message @BotFather on Telegram, send /newbot, follow the prompts.
  2. Put the token it gives you in the TELEGRAM_BOT_TOKEN secret.
  3. Put the destination chat id in TELEGRAM_CHAT_ID (your own user id for a
     private feed, or a channel id like -1001234567890 to broadcast).

Unset = silent no-op, exactly like the Discord and email integrations.
Failures never break the pipeline: alerting is a side channel.
"""

from __future__ import annotations

import os
from html import escape

import httpx

from . import config, filters, grouping, h1b, sponsorship

_API = "https://api.telegram.org/bot{token}/sendMessage"
# Telegram rejects a message above 4096 Unicode characters. This is a hard
# output invariant, including header/footer and HTML markup.
_MAX_CHARS = 4096
_MAX_ROLES = 40      # beyond this a run is a backfill, not an announcement
_TIMEOUT = 10


def configured() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def _role_line(record: dict, us_context: bool = True) -> str:
    """One role, as Telegram-flavoured HTML.

    Telegram's HTML parse mode supports a small tag set (<b>, <i>, <a>, <code>)
    and nothing else — no tables, no styling. So the shape carries the meaning:
    bold employer, linked title, dim detail line.
    """
    company = escape((record.get("company") or "")[:180])
    # The H-1B badge and the visa flag are US immigration records; on a digest
    # of roles from a region that data doesn't cover they claim nothing.
    if us_context and h1b.badge(h1b.approvals_for(record.get("company") or "")):
        company += " ✓"
    if filters.is_remote(record.get("location") or "", record.get("title") or ""):
        company += " 🆁"

    title = escape((record.get("title") or "")[:500])
    url = (record.get("url") or "")[:1000]
    head = f'<b>{company}</b>\n<a href="{escape(url)}">{title}</a>' if url \
        else f"<b>{company}</b>\n{title}"

    bits = []
    openings = record.get("openings") or 1
    if openings > 1:
        bits.append(f"{openings} openings")
    season = record.get("season")
    if season and season != "Not stated":
        bits.append(season[:80])
    if record.get("location"):
        bits.append(record["location"][:80])
    if record.get("salary"):
        bits.append(record["salary"][:80])
    flag = sponsorship.flag(record.get("sponsorship")) if us_context else ""
    if flag:
        bits.append(flag)
    detail = escape(" · ".join(b for b in bits if b))

    skills = record.get("skills") or []
    if skills:
        detail += "\n" + escape(" · ".join(str(s)[:60] for s in skills[:4]))
    return f"{head}\n<i>{detail}</i>" if detail else head


def _grouped(records: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
    """Identical openings in this batch become one line, carrying every id.

    Grouping is per-batch on purpose. Cross-run grouping would need its own
    durable state to answer "did we already announce this group?", and the
    outbox already answers that per requisition — a sibling opened tomorrow is
    genuinely new and should be announced then.
    """
    merged = grouping.group([{**record, "id": jid} for jid, record in records])
    return [(row.get("id") or "", row) for row in merged]


def build_chunks(records: list[tuple[str, dict]]) -> list[tuple[str, list[str]]]:
    """Split roles into (message text, ids in that message) pairs.

    Carrying the ids alongside each message is what makes partial delivery
    safe. An earlier version returned bare strings and only marked ids
    delivered once EVERY message had landed — so a run where message 1
    succeeded and message 2 timed out reported nothing delivered, left all of
    it queued, and re-sent message 1's roles on the next run. Each chunk now
    settles on its own POST.
    """
    if not records:
        return []
    # Count openings, not lines: three grouped requisitions are still three
    # new internships, and the header must not shrink to "1" because they
    # share a line.
    total = sum(len(r.get("opening_ids") or [1]) for _jid, r in records)
    header = (f"<b>{total} new internship"
              f"{'s' if total != 1 else ''}</b>")
    footer = f'\n<a href="{config.pages_base()}/">Open the dashboard</a>'

    us_context = config.want_us(config.load_config())
    chunks: list[tuple[list[str], list[str]]] = []   # (lines, ids)
    lines: list[str] = []
    ids: list[str] = []
    first = True
    for jid, record in records:
        line = _role_line(record, us_context)
        # One line can stand for several requisitions. All of them settle
        # together on that line's delivery, or none of them do.
        line_ids = [i for i in (record.get("opening_ids") or [jid]) if i]
        prefix = header + "\n\n" if first else ""
        candidate = prefix + "\n\n".join([*lines, line])
        # Reserve footer space on every chunk. Only the final one uses it, but
        # this keeps finalization from pushing a valid body past 4096.
        if lines and len(candidate + footer) > _MAX_CHARS:
            chunks.append((lines, ids))
            lines, ids, first = [line], list(line_ids), False
        else:
            lines.append(line)
            ids.extend(line_ids)
    if lines:
        chunks.append((lines, ids))

    out = []
    for i, (body, chunk_ids) in enumerate(chunks):
        text = (header + "\n\n" if i == 0 else "") + "\n\n".join(body)
        if i == len(chunks) - 1:
            text += footer
        if len(text) > _MAX_CHARS:
            # Field caps above make this unreachable for normal records. Keep
            # the invariant explicit instead of asking Telegram to reject it.
            raise ValueError("Telegram message exceeds 4096 characters")
        out.append((text, chunk_ids))
    return out


def build_messages(records: list[dict]) -> list[str]:
    """Just the message text — used by tests and previews."""
    return [text for text, _ids in build_chunks([("", r) for r in records])]


def send_new_roles(store_data: dict, new_ids: list[str]) -> list[str]:
    """Push new roles to Telegram. Returns the ids that no longer need announcing.

    Same contract as notify.send_new_roles, because the outbox drains on it:
    the return value must be exact. Ids that can never be announced (gone from
    the store, or since closed) count as settled so the queue doesn't grow
    forever; roles we meant to send but didn't stay queued for the next run.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return list(new_ids)  # nothing to deliver to; don't accumulate
    if not new_ids:
        return []

    live = [(jid, store_data[jid]) for jid in new_ids if jid in store_data]
    settled = [jid for jid in new_ids if jid not in store_data]
    settled += [jid for jid, r in live if not r.get("is_open")]
    records = [(jid, r) for jid, r in live if r.get("is_open")]
    if not records:
        return settled

    # GDIT opened RQ225450, RQ225456 and RQ225469 in the same hour: three real
    # requisitions, one job. Ungrouped, that was one push notification with the
    # same line printed three times. Group them into a single line that says
    # "3 openings" — and settle all three ids on that one line's delivery, so
    # nothing stays queued waiting for a message that will never be sent.
    records = _grouped(records)
    shown = records[:_MAX_ROLES]
    announced: list[str] = []
    url = _API.format(token=token)
    # Settle each chunk on its OWN successful POST. Waiting for every message
    # meant one failed chunk re-sent the ones that had already arrived.
    for text, chunk_ids in build_chunks(shown):
        try:
            httpx.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    # Link previews would turn a 10-role message into a wall of
                    # thumbnails for the same careers page.
                    "disable_web_page_preview": True,
                },
                timeout=_TIMEOUT,
            ).raise_for_status()
        except Exception:  # noqa: BLE001 — alerting is a side channel, never fatal
            break  # stop here; unsent chunks stay queued for the next run
        announced += chunk_ids
    return settled + announced
