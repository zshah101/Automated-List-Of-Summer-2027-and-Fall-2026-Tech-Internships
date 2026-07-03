"""The Drop Radar: when each company is EXPECTED to post this cycle.

Every list shows what is open now. The radar answers the question applicants
actually plan around — "when does Stripe usually drop?" — by projecting each
company's first-post date from last cycle (data/seasons.json, built by
tools/build_seasons.py) one year forward, then checking it against what the
engine can already see live this cycle.

Honesty rules:
  - Dates inside the source's known backfill window (the reference dataset
    started mid-season) are shown as "by <date>" — the company had posted by
    then; we don't know how much earlier.
  - Status is "posted" only when OUR live feeds see a matching role this
    cycle; otherwise "waiting" — which means "not seen in tracked feeds",
    never a promise the company hasn't posted somewhere we don't watch.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

from . import h1b, paths, priority

# The big reference dataset began mid-November 2025; first-post dates in its
# opening days mean "already up by then", not "dropped that day".
_BACKFILL_START = "2025-11-01"
_BACKFILL_END = "2025-11-14"

_seasons_cache: dict | None = None


def load() -> dict:
    global _seasons_cache
    if _seasons_cache is None:
        try:
            with open(paths.SEASONS_PATH, encoding="utf-8") as f:
                _seasons_cache = json.load(f)
        except (OSError, ValueError):
            _seasons_cache = {}
    return _seasons_cache


def _plus_one_year(iso_day: str) -> date:
    d = datetime.strptime(iso_day, "%Y-%m-%d").date()
    try:
        return d.replace(year=d.year + 1)
    except ValueError:  # Feb 29
        return d.replace(year=d.year + 1, day=28)


def _open_this_cycle(store_data: dict, cycle: str) -> dict[str, str]:
    """{normalized company: apply url} for roles open in the target cycle."""
    seen: dict[str, str] = {}
    for r in store_data.values():
        if not r.get("is_open") or r.get("season") != cycle:
            continue
        key = h1b.normalize(r.get("company") or "")
        if key and key not in seen:
            seen[key] = r.get("url") or ""
    return seen


def rows(store_data: dict, cycle: str, today: date | None = None) -> list[dict]:
    """Radar rows for notable companies, soonest expected drop first."""
    seasons = load()
    companies = seasons.get("companies") or {}
    if not companies:
        return []
    today = today or datetime.now(UTC).date()
    live = _open_this_cycle(store_data, cycle)

    out = []
    for key, info in companies.items():
        count = info.get("count", 0)
        notable = priority.rank(info.get("name") or key) < priority.UNRANKED or count >= 3
        if not notable:
            continue
        first = info.get("first_posted") or ""
        if not first:
            continue
        expected = _plus_one_year(first)
        approx = _BACKFILL_START <= first <= _BACKFILL_END
        posted_url = live.get(key)
        out.append({
            "company": info.get("name") or key,
            "last_cycle_posted": first,
            "approx": approx,                       # "by <date>", not "on <date>"
            "expected": expected.strftime("%Y-%m-%d"),
            "days_until": (expected - today).days,
            "status": "posted" if posted_url is not None else "waiting",
            "url": posted_url or "",
            "roles_last_cycle": count,
        })

    out.sort(key=lambda r: (r["expected"], -r["roles_last_cycle"]))
    return out


# --- display helpers (shared by README + dashboard) -----------------------------

def pretty_last(row: dict) -> str:
    d = datetime.strptime(row["last_cycle_posted"], "%Y-%m-%d").strftime("%b %d")
    return f"by {d}" if row["approx"] else d


def pretty_expected(row: dict) -> str:
    d = datetime.strptime(row["expected"], "%Y-%m-%d")
    label = f"~{d.strftime('%b %d')}"
    if row["approx"]:
        label += " or earlier"
    days = row["days_until"]
    if row["status"] == "posted":
        return label
    if days <= 0:
        return f"{label} · any day now"
    if days <= 45:
        return f"{label} · in ~{days}d"
    return label
