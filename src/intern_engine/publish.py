"""Machine-readable outputs served from GitHub Pages (docs/).

Two artifacts, regenerated every run:
  docs/feed.xml       — Atom feed of roles ordered by when WE first saw them,
                        so any RSS reader / Slack / Discord RSS bot becomes a
                        free alerting channel with zero infrastructure.
  docs/api/jobs.json  — every open role, plus stats.json — for anyone who wants
                        to build on the data without scraping our README.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from xml.sax.saxutils import escape

from . import config, h1b, paths, radar, sponsorship

_FEED_LIMIT = 50


def _first_seen(record: dict) -> str:
    return record.get("first_seen_at") or ""


def _entry(record: dict, base: str) -> str:
    flag = sponsorship.flag(record.get("sponsorship"))
    title = f"{record.get('company', '')}: {record.get('title', '')}"
    if flag:
        title += f" {flag}"
    summary_bits = [
        record.get("season") or "",
        record.get("category") or "",
        record.get("location") or "",
    ]
    if record.get("salary"):
        summary_bits.append(record["salary"])
    if record.get("skills"):
        summary_bits.append(", ".join(record["skills"][:5]))
    sponsor = record.get("sponsorship", "unknown")
    if sponsor != "unknown":
        summary_bits.append(f"sponsorship: {sponsor}")
    approvals = h1b.approvals_for(record.get("company") or "")
    if h1b.badge(approvals):
        summary_bits.append(
            f"H-1B track record: ~{h1b.pretty_count(approvals)} approvals "
            f"({h1b.window_label()})"
        )
    summary = " · ".join(b for b in summary_bits if b)
    updated = _first_seen(record) or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        "  <entry>\n"
        f"    <id>urn:intern-engine:{escape(record.get('id', ''))}</id>\n"
        f"    <title>{escape(title)}</title>\n"
        f"    <link href=\"{escape(record.get('url') or base)}\"/>\n"
        f"    <updated>{escape(updated)}</updated>\n"
        f"    <category term=\"{escape(record.get('season') or 'Internship')}\"/>\n"
        f"    <summary>{escape(summary)}</summary>\n"
        "  </entry>\n"
    )


def write_feed(store_data: dict) -> int:
    """Atom feed of the most recently spotted open roles."""
    base = config.pages_base()
    cycles_phrase = " & ".join(config.cycles(config.load_config()))
    open_jobs = [r for r in store_data.values() if r.get("is_open")]
    open_jobs.sort(key=_first_seen, reverse=True)
    entries = open_jobs[:_FEED_LIMIT]
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    xml = [
        '<?xml version="1.0" encoding="utf-8"?>\n',
        '<feed xmlns="http://www.w3.org/2005/Atom">\n',
        f"  <id>{escape(base)}/feed.xml</id>\n",
        f"  <title>{escape(cycles_phrase)} Tech Internships — new roles</title>\n",
        "  <subtitle>Auto-detected internships, newest finds first.</subtitle>\n",
        f'  <link href="{escape(base)}/feed.xml" rel="self"/>\n',
        f'  <link href="https://github.com/{escape(config.repo_slug())}"/>\n',
        f"  <updated>{now}</updated>\n",
    ]
    xml.extend(_entry(r, base) for r in entries)
    xml.append("</feed>\n")

    os.makedirs(paths.DOCS_DIR, exist_ok=True)
    with open(paths.FEED_PATH, "w", encoding="utf-8") as f:
        f.write("".join(xml))
    return len(entries)


def _ics_escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;")
                .replace(",", "\\,").replace("\n", "\\n"))


def _ics_fold(line: str) -> str:
    """Fold a content line at 75 octets per RFC 5545 (UTF-8 aware)."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    out, chunk = [], b""
    for ch in line:
        enc = ch.encode("utf-8")
        # 74 leaves room; continuation lines start with a single space.
        limit = 75 if not out else 74
        if len(chunk) + len(enc) > limit:
            out.append(chunk.decode("utf-8"))
            chunk = b""
        chunk += enc
    out.append(chunk.decode("utf-8"))
    return "\r\n ".join(out)


def write_radar_ics(store_data: dict, cycle: str | None = None) -> int:
    """A subscribable calendar of expected internship drop dates.

    Point Google/Apple Calendar at docs/radar.ics and every company's expected
    opening becomes an all-day event with a reminder a week before. Only rows
    with a real date (verified projections + hand-verified month windows) get an
    event; rolling / already-open companies are skipped. This turns the radar
    from something you check into something that pings you — on brand for a
    real-time engine, and no infrastructure since Pages serves the static file.
    """
    cycle = cycle or config.cycles(config.load_config())[0]
    base = config.pages_base()
    now = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    rows = [r for r in radar.rows(store_data, cycle)
            if r["status"] == "waiting" and not r["rolling"] and r["expected"]]

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//intern-engine//Drop Radar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:Internship Drop Radar ({_ics_escape(cycle)})",
        "X-WR-CALDESC:Expected opening dates for tech internships. "
        "Verified from live career-page data + hand-checked windows.",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
    ]
    for r in rows:
        start = r["expected"].replace("-", "")
        end = (datetime.strptime(r["expected"], "%Y-%m-%d").date()
               + timedelta(days=1)).strftime("%Y%m%d")
        uid = f"radar-{h1b.normalize(r['company']) or r['company']}-{start}@intern-engine"
        verified = r["source"] == "engine"
        precise = r["precision"] == "day"
        mark = "🎯 " if verified else ""
        when = "expected to open" if precise else "typically opens"
        summary = f"{mark}{r['company']} — {when} ({cycle})"
        trust = ("date verified from our own live career-page observations"
                 if verified else "hand-verified typical opening month (month-level)")
        desc_bits = [f"{r['company']} {when} around this date.", trust]
        if r.get("note"):
            desc_bits.append(r["note"])
        desc_bits.append(f"Radar: {base}/#radar")
        lines += [
            "BEGIN:VEVENT",
            f"UID:{_ics_escape(uid)}",
            f"DTSTAMP:{now}",
            f"DTSTART;VALUE=DATE:{start}",
            f"DTEND;VALUE=DATE:{end}",
            f"SUMMARY:{_ics_escape(summary)}",
            f"DESCRIPTION:{_ics_escape('  '.join(desc_bits))}",
            "TRANSP:TRANSPARENT",
            "BEGIN:VALARM",
            "TRIGGER:-P7D",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{_ics_escape(r['company'] + ' internships open soon')}",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")

    os.makedirs(paths.DOCS_DIR, exist_ok=True)
    with open(paths.RADAR_ICS_PATH, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(_ics_fold(ln) for ln in lines) + "\r\n")
    return len(rows)


_API_FIELDS = (
    "id", "company", "title", "season", "season_inferred", "category",
    "location", "url", "posted_at", "first_seen_at", "sponsorship", "salary",
    "skills", "source",
)


def write_api(store_data: dict, stats: dict) -> int:
    """Static JSON API: every open role + the latest run metrics."""
    open_jobs = [r for r in store_data.values() if r.get("is_open")]
    open_jobs.sort(
        key=lambda r: ((r.get("posted_at") or "")[:10], _first_seen(r)), reverse=True
    )
    def _job(r: dict) -> dict:
        row = {k: r.get(k) for k in _API_FIELDS}
        row["h1b_approvals"] = h1b.approvals_for(r.get("company") or "")
        return row

    payload = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": f"https://github.com/{config.repo_slug()}",
        "h1b_window": h1b.window_label() or None,
        "count": len(open_jobs),
        "jobs": [_job(r) for r in open_jobs],
    }
    os.makedirs(paths.API_DIR, exist_ok=True)
    with open(os.path.join(paths.API_DIR, "jobs.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    with open(os.path.join(paths.API_DIR, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1, ensure_ascii=False)

    cycle = config.cycles(config.load_config())[0]
    radar_payload = {
        "generated_at": payload["generated_at"],
        "cycle": cycle,
        "source": payload["source"],
        "companies": radar.rows(store_data, cycle),
    }
    radar_payload["count"] = len(radar_payload["companies"])
    with open(os.path.join(paths.API_DIR, "radar.json"), "w", encoding="utf-8") as f:
        json.dump(radar_payload, f, indent=1, ensure_ascii=False)
    return len(open_jobs)
