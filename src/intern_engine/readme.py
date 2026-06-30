"""Render the public-facing README.md (the product) + a CSV tracker.

Plain, professional, human voice. No decorative emojis. Sections are exactly the
configured cycles, in order. Roles are sorted by their PUBLISHED date (newest on
top), and that date is frozen per role so the page behaves like a ladder.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone

from . import config, paths, priority


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%b %d, %Y at %H:%M UTC")


def _md_cell(text: str) -> str:
    return (text or "—").replace("|", "/").replace("\n", " ").strip() or "—"


def _short_location(loc: str, limit: int = 40) -> str:
    loc = _md_cell(loc)
    if len(loc) <= limit:
        return loc
    parts = [p.strip() for p in loc.replace(";", ",").split(",") if p.strip()]
    if len(parts) > 1:
        return f"{parts[0]} +{len(parts) - 1} more"
    return loc[: limit - 1].rstrip() + "…"


def _date_str(record: dict) -> str:
    """The published date string we sort/display by (frozen per role)."""
    return (record.get("posted_at") or record.get("first_seen_at") or "")


def _pretty_date(record: dict) -> str:
    iso = _date_str(record)
    if not iso:
        return "—"
    try:
        return datetime.strptime(iso[:10], "%Y-%m-%d").strftime("%b %d, %Y")
    except ValueError:
        return iso[:10]


def _row(record: dict) -> str:
    company = _md_cell(record.get("company"))
    title = _md_cell(record.get("title"))
    location = _short_location(record.get("location"))
    category = _md_cell(record.get("category"))
    posted = _pretty_date(record)
    url = record.get("url") or ""
    apply = f"[Apply]({url})" if url else "—"
    return f"| {company} | {title} | {category} | {location} | {posted} | {apply} |"


def _region_label(cfg: dict) -> str:
    if not config.restrict_region(cfg):
        return "Worldwide"
    parts = []
    if config.want_us(cfg):
        parts.append("United States")
    if config.want_canada(cfg):
        parts.append("Canada")
    return " & ".join(parts) if parts else "United States"


def _company_count() -> int:
    import json
    try:
        with open(paths.COMPANIES_PATH, encoding="utf-8") as f:
            return len(json.load(f))
    except (OSError, ValueError):
        return 0


def _header(cfg: dict, total_open: int, companies: int) -> list[str]:
    region = _region_label(cfg)
    cycles = config.cycles(cfg)
    cycles_phrase = " and ".join(cycles)

    return [
        "# Summer 2027 Tech Internships",
        "",
        "A self-updating engine that tracks tech internships so you don't have to. "
        "Instead of refreshing a dozen career pages by hand, it reads company hiring "
        "feeds directly and keeps one live list — newest roles on top, refreshed "
        "automatically throughout the day.",
        "",
        f"**{total_open} open roles · {companies} companies tracked · "
        f"updated {_now_str()}**",
        "",
        "## What this is",
        "",
        "This is an engine, not a hand-kept list. It polls company career feeds "
        "(Greenhouse, Lever, Ashby) several times a day, finds the internships, "
        "removes duplicates, and rebuilds this page on its own. Every link comes "
        "straight from the source, so it's real and current — not a stale list "
        "someone forgot to update.",
        "",
        "## Scope",
        "",
        "- **Roles:** Software Engineering, Data Science & Machine Learning "
        "(and closely related technical internships)",
        f"- **Region:** {region} only (for now)",
        f"- **Cycles:** {cycles_phrase}",
        "",
        "## About",
        "",
        "I'm a US-based international student studying in the United States, so I "
        "built this for the search I'm doing myself. It's US-only for now. Use it to "
        "spot roles early and apply before they fill up — being first genuinely helps.",
        "",
        "## Where this is going",
        "",
        "I'm building this in the open and adding to it as it grows. Coming soon: "
        "**SMS/email alerts** the moment a role opens, and **filtering** by role, "
        "location, and visa-sponsorship (a real one for fellow international "
        "students). If it helps you, a star means a lot and tells me to keep going.",
        "",
        "## How to use",
        "",
        "- Roles are grouped by cycle below — **newest posting on top, oldest at the bottom.**",
        "- The **Posted** column is the date the company published the role.",
        "- Track your applications with [`data/internships.csv`](data/internships.csv) "
        "(opens in Excel / Google Sheets).",
        "- Missing a company? Adding one takes a single line — see "
        "[CONTRIBUTING.md](CONTRIBUTING.md).",
        "",
        "---",
        "",
    ]


def _footer() -> list[str]:
    return [
        "---",
        "",
        "## How it stays current",
        "",
        "A small Python engine reads public company hiring feeds directly, keeps the "
        "roles that match the scope above, removes duplicates, records each role's "
        "published date once (so it never shifts), and regenerates this page through "
        "GitHub Actions. The full source is in this repo.",
        "",
        "## Contributing",
        "",
        "Adding a company takes one line — see [CONTRIBUTING.md](CONTRIBUTING.md). "
        "Suggestions and pull requests are welcome.",
        "",
        "## Note on dates",
        "",
        "The **Posted** date is when the company published the role, newest first. "
        "Most boards expose this directly; where a board doesn't, we show the earliest "
        "date we could confirm and keep it fixed afterward. Roles can close at any "
        "time — always confirm on the company's own site before applying.",
        "",
    ]


def _select(rows: list[dict], limit) -> list[dict]:
    """Pick which rows to show, then order them newest-first for display.

    If a section is over its cap, keep roles from the most sought-after
    companies first (ties broken by recency), then display newest on top.
    """
    if limit and len(rows) > limit:
        rows = sorted(rows, key=lambda r: _date_str(r)[:10], reverse=True)
        rows = sorted(rows, key=lambda r: priority.rank(r.get("company")))[:limit]
    return sorted(rows, key=lambda r: _date_str(r)[:10], reverse=True)


def generate(store_data: dict) -> dict:
    cfg = config.load_config()
    cycles = config.cycles(cfg)

    open_jobs = [r for r in store_data.values() if r.get("is_open")]
    groups: dict[str, list[dict]] = {}
    for r in open_jobs:
        groups.setdefault(r.get("season", ""), []).append(r)

    ordered_labels = cycles + [lbl for lbl in groups if lbl not in cycles]

    sections: list[tuple[str, list[dict]]] = []
    displayed: list[dict] = []
    for label in ordered_labels:
        rows = _select(groups.get(label) or [], config.section_limit(cfg, label))
        if rows:
            sections.append((label, rows))
            displayed.extend(rows)

    lines = _header(cfg, len(displayed), _company_count())
    for label, rows in sections:
        lines.append(f"## {label}  ({len(rows)} open)")
        lines.append("")
        lines.append("| Company | Role | Category | Location | Posted | Apply |")
        lines.append("|---|---|---|---|---|---|")
        lines.extend(_row(r) for r in rows)
        lines.append("")

    if not displayed:
        lines.append(
            "_No matching roles right now — the list fills as companies post. "
            "Star it and check back._"
        )
        lines.append("")

    lines.extend(_footer())

    with open(paths.README_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    _write_csv(displayed)

    return {"open": len(displayed), "companies": _company_count()}


def _write_csv(open_jobs: list[dict]) -> None:
    fields = [
        "company", "title", "season", "category", "location",
        "posted_at", "first_seen_at", "url",
    ]
    with open(paths.CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in open_jobs:
            writer.writerow({k: r.get(k, "") for k in fields})
