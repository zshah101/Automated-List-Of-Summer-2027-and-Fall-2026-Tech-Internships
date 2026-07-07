"""The Drop Radar: when each company is EXPECTED to post this cycle.

Every list shows what is open now. The radar answers the question applicants
actually plan around — "when does Stripe usually drop?" — using only sources we
own or can verify. No third-party listing repo is involved. Most-trusted first:

  1. LIVE      — the company is open this cycle right now. We show the real drop
                 date the engine saw from the ATS. Confidence: verified.
  2. OBSERVED  — the engine itself recorded this company's real posted date in
                 the SAME cycle a year ago (`data/observed.json`), pulled straight
                 from the ATS. We project it forward. Confidence: verified. This
                 layer grows every cycle, so the radar becomes fully self-reliant.
  3. WINDOW    — a hand-verified typical opening month for a marquee name
                 (`data/known_windows.json`, checked against the company's own
                 careers page). Month-level only — never a fake day. Some
                 companies post year-round; those are shown as "rolling", not a
                 date. Confidence: window / rolling. This is only a seed until
                 the engine has observed the company itself.

Honesty rules:
  - A window is a month, not a day: rendered "~Aug", and "rolling" companies are
    rendered "year-round". We never invent a precise date we didn't observe.
  - Status is "posted" only when OUR live feeds see a matching role this cycle;
    otherwise "waiting".
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

from . import h1b, observe, paths

_known_cache: dict | None = None
_observed_cache: dict | None = None


def _load_observed() -> dict:
    global _observed_cache
    if _observed_cache is None:
        _observed_cache = observe.load()
    return _observed_cache


def _load_known() -> dict:
    """{normalized name: {name, opens, precision, note}} from known_windows.json."""
    global _known_cache
    if _known_cache is None:
        try:
            with open(paths.KNOWN_WINDOWS_PATH, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError):
            raw = {}
        out: dict[str, dict] = {}
        for entry in raw.get("companies") or []:
            key = h1b.normalize(entry.get("name") or "")
            if key:
                out[key] = entry
        _known_cache = out
    return _known_cache


def _plus_one_year(iso_day: str) -> date:
    d = datetime.strptime(iso_day, "%Y-%m-%d").date()
    try:
        return d.replace(year=d.year + 1)
    except ValueError:  # Feb 29
        return d.replace(year=d.year + 1, day=28)


def prev_cycle(cycle: str) -> str:
    """'Summer 2027' -> 'Summer 2026'. The same term one year earlier."""
    term, _, year = cycle.rpartition(" ")
    if term and year.isdigit():
        return f"{term} {int(year) - 1}"
    return cycle


def _window_expected(cycle: str, month: str) -> date | None:
    """A summer cycle opens the calendar year before it (Summer 2027 -> 2026)."""
    term, _, year = cycle.rpartition(" ")
    if not year.isdigit() or not month:
        return None
    open_year = int(year) - 1 if term == "Summer" else int(year)
    try:
        return date(open_year, int(month), 1)
    except ValueError:
        return None


def _open_this_cycle(store_data: dict, cycle: str) -> dict[str, dict]:
    """{normalized company: {url, name}} for roles open in the target cycle."""
    seen: dict[str, dict] = {}
    for r in store_data.values():
        if not r.get("is_open") or r.get("season") != cycle:
            continue
        name = r.get("company") or ""
        key = h1b.normalize(name)
        if key and key not in seen:
            seen[key] = {"url": r.get("url") or "", "name": name}
    return seen


def rows(store_data: dict, cycle: str, today: date | None = None) -> list[dict]:
    """Radar rows for every company we can say something real about."""
    observed = _load_observed().get("companies") or {}
    known = _load_known()
    live = _open_this_cycle(store_data, cycle)
    if not observed and not known and not live:
        return []
    today = today or datetime.now(UTC).date()

    keys = set(observed) | set(known) | set(live)
    out: list[dict] = []
    for key in keys:
        o_info = observed.get(key)
        k_info = known.get(key)
        l_info = live.get(key)
        cycles = (o_info or {}).get("cycles") or {}
        obs_this = cycles.get(cycle)
        obs_prev = cycles.get(prev_cycle(cycle))
        name = ((k_info or {}).get("name") or (o_info or {}).get("name")
                or (l_info or {}).get("name") or key)
        is_posted = l_info is not None
        url = (l_info or {}).get("url", "")

        # Defaults
        last = ""            # last cycle's date/month we project from (display)
        posted_on = ""       # the real date it dropped this cycle, if we caught it
        precision = "day"
        confidence = "window"
        source = "known"
        rolling = False
        expected: date | None = None

        if obs_this and obs_this.get("first_posted"):
            posted_on = obs_this["first_posted"]
            expected = datetime.strptime(posted_on, "%Y-%m-%d").date()
            confidence, source, precision = "verified", "engine", "day"
        elif obs_prev and obs_prev.get("first_posted"):
            last = obs_prev["first_posted"]
            expected = _plus_one_year(last)
            confidence, source, precision = "verified", "engine", "day"
        elif k_info and k_info.get("precision") == "month" and k_info.get("opens"):
            expected = _window_expected(cycle, k_info["opens"])
            confidence, source, precision = "window", "known", "month"
        elif k_info and k_info.get("precision") == "rolling":
            confidence, source, rolling = "rolling", "known", True
        elif is_posted:
            # Open now but we have no date on record — still a real live signal.
            confidence, source = "verified", "engine"
        else:
            continue  # nothing real to say

        # open = live now; dropped = we saw it post this cycle but it's since
        # closed; waiting = not seen this cycle yet.
        if is_posted:
            status = "open"
        elif posted_on:
            status = "dropped"
        else:
            status = "waiting"

        out.append({
            "company": name,
            "last_cycle_posted": last,
            "posted_on": posted_on,
            "precision": precision,             # day | month
            "rolling": rolling,
            "confidence": confidence,           # verified | window | rolling
            "source": source,                   # engine | known
            "expected": expected.strftime("%Y-%m-%d") if expected else "",
            "days_until": (expected - today).days if expected else None,
            "status": status,                   # open | dropped | waiting
            "url": url,
            "note": (k_info or {}).get("note", ""),
        })

    _rank = {"open": 0, "dropped": 1, "waiting": 2}

    def _sortkey(r: dict) -> tuple:
        return (
            _rank[r["status"]],                 # open, then dropped, then waiting
            r["rolling"],                       # dated before rolling
            r["expected"] or "9999-99-99",      # soonest expected next
            r["company"].lower(),
        )

    out.sort(key=_sortkey)
    return out


# --- display helpers (shared by README + dashboard) -----------------------------

def _fmt(iso_day: str, month_only: bool = False) -> str:
    d = datetime.strptime(iso_day, "%Y-%m-%d")
    return d.strftime("%b") if month_only else d.strftime("%b %d")


def pretty_last(row: dict) -> str:
    """The 'typical opening' cell."""
    if row.get("posted_on"):
        return _fmt(row["posted_on"])
    if row.get("rolling"):
        return "rolling"
    if row.get("last_cycle_posted"):
        return _fmt(row["last_cycle_posted"])
    if row.get("expected"):
        return f"~{_fmt(row['expected'], month_only=True)}"
    return "—"


def pretty_expected(row: dict) -> str:
    """The 'expected this cycle' cell."""
    if row["status"] == "open":
        return f"dropped {_fmt(row['posted_on'])}" if row.get("posted_on") else "live now"
    if row["status"] == "dropped":
        return f"dropped {_fmt(row['posted_on'])} · closed"
    if row.get("rolling"):
        return "year-round"
    if not row.get("expected"):
        return "—"
    month_only = row.get("precision") == "month"
    label = f"~{_fmt(row['expected'], month_only=month_only)}"
    days = row.get("days_until")
    if days is None:
        return label
    if days <= 0:
        return f"{label} · any day now"
    if days <= 45:
        return f"{label} · in ~{days}d"
    return label


def confidence_note(row: dict) -> str:
    """Short trust label for the UI."""
    return {
        "verified": "verified",
        "window": "typical window",
        "rolling": "rolling",
    }.get(row.get("confidence", "window"), "typical window")
