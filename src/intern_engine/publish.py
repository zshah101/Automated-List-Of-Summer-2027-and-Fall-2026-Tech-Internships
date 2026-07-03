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
from datetime import UTC, datetime
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
    open_jobs = [r for r in store_data.values() if r.get("is_open")]
    open_jobs.sort(key=_first_seen, reverse=True)
    entries = open_jobs[:_FEED_LIMIT]
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    xml = [
        '<?xml version="1.0" encoding="utf-8"?>\n',
        '<feed xmlns="http://www.w3.org/2005/Atom">\n',
        f"  <id>{escape(base)}/feed.xml</id>\n",
        "  <title>Summer 2027 Tech Internships — new roles</title>\n",
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


_API_FIELDS = (
    "id", "company", "title", "season", "category", "location", "url",
    "posted_at", "first_seen_at", "sponsorship", "salary", "source",
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
