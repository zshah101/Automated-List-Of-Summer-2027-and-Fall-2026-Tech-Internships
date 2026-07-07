"""The Drop Radar: when each company is EXPECTED to post this cycle.

Every list shows what is open now. The radar answers the question applicants
actually plan around — "when does Stripe usually drop?" — by combining three
sources, most-trusted first:

  1. LIVE      — the company is already open this cycle. We show the real drop
                 date the engine saw, not a guess. Confidence: verified.
  2. OBSERVED  — the engine itself recorded this company's real posted date in
                 the SAME cycle a year ago (`data/observed.json`). We project it
                 forward. Confidence: verified. This layer grows every cycle, so
                 the radar becomes self-reliant and stops needing outside repos.
  3. REFERENCE — last cycle's first-post date from the public listing dataset
                 (`data/seasons.json`). Confidence: estimated — or "floor" when
                 the date sits at the dataset's start, meaning the role was
                 already up by then and we can only give a latest bound.

Honesty rules:
  - A "floor" date is rendered "by <date>" — the company had posted by then; we
    do not know how much earlier, so treat it as the latest point to start
    watching, never the drop day.
  - Status is "posted" only when OUR live feeds see a matching role this cycle;
    otherwise "waiting" — "not seen in tracked feeds", never a promise the
    company hasn't posted somewhere we don't watch.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

from . import h1b, observe, paths, priority

# A reference date within this many days of the dataset's floor is treated as
# "already up by then" rather than an exact drop date.
_FLOOR_BAND_DAYS = 6
# Fallback floor if the seasons file predates dynamic-floor detection.
_DEFAULT_FLOOR = "2025-11-10"

_seasons_cache: dict | None = None
_observed_cache: dict | None = None


def load() -> dict:
    global _seasons_cache
    if _seasons_cache is None:
        try:
            with open(paths.SEASONS_PATH, encoding="utf-8") as f:
                _seasons_cache = json.load(f)
        except (OSError, ValueError):
            _seasons_cache = {}
    return _seasons_cache


def _load_observed() -> dict:
    global _observed_cache
    if _observed_cache is None:
        _observed_cache = observe.load()
    return _observed_cache


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


def _within_floor(iso_day: str, floor: str) -> bool:
    if iso_day < floor:
        return False
    delta = (datetime.strptime(iso_day, "%Y-%m-%d").date()
             - datetime.strptime(floor, "%Y-%m-%d").date()).days
    return 0 <= delta <= _FLOOR_BAND_DAYS


def _resolve(key: str, name: str, seasons_info: dict | None,
             observed_companies: dict, cycle: str, floor: str) -> dict | None:
    """Pick the best available last-cycle signal for one company.

    Returns {last, expected(date), confidence, source} or None if we have
    nothing to project from.
    """
    obs = (observed_companies.get(key) or {}).get("cycles") or {}

    # OBSERVED: the engine's own real date for the same cycle a year ago.
    prior = obs.get(prev_cycle(cycle))
    if prior and prior.get("first_posted"):
        last = prior["first_posted"]
        return {"last": last, "expected": _plus_one_year(last),
                "confidence": "verified", "source": "engine"}

    # REFERENCE: outside dataset's first-post date last cycle.
    if seasons_info and seasons_info.get("first_posted"):
        last = seasons_info["first_posted"]
        confidence = "floor" if _within_floor(last, floor) else "estimated"
        return {"last": last, "expected": _plus_one_year(last),
                "confidence": confidence, "source": "reference"}
    return None


def rows(store_data: dict, cycle: str, today: date | None = None) -> list[dict]:
    """Radar rows for notable companies, soonest expected drop first."""
    seasons = load()
    seasons_companies = seasons.get("companies") or {}
    observed = _load_observed()
    observed_companies = observed.get("companies") or {}
    if not seasons_companies and not observed_companies:
        return []
    floor = seasons.get("floor") or _DEFAULT_FLOOR
    today = today or datetime.now(UTC).date()
    live = _open_this_cycle(store_data, cycle)

    # Union of every company either source knows about.
    keys = set(seasons_companies) | set(observed_companies)
    out = []
    for key in keys:
        s_info = seasons_companies.get(key)
        o_info = observed_companies.get(key)
        name = (s_info or {}).get("name") or (o_info or {}).get("name") or key
        count = (s_info or {}).get("count", 0)
        obs_this = ((o_info or {}).get("cycles") or {}).get(cycle) if o_info else None

        posted_url = live.get(key)
        is_posted = posted_url is not None

        # Notable = well-known company, OR posted enough roles last cycle, OR we
        # can already see it live this cycle (real signal beats any threshold).
        notable = (priority.rank(name) < priority.UNRANKED
                   or count >= 3 or is_posted)
        if not notable:
            continue

        resolved = _resolve(key, name, s_info, observed_companies, cycle, floor)

        # If it is already open this cycle and we caught the real drop date,
        # that verified date is the strongest thing we can show — it is our own
        # observation, so it always counts as engine-verified.
        if obs_this and obs_this.get("first_posted"):
            last = obs_this["first_posted"]
            # It already dropped this cycle — the real date IS the answer, so
            # "expected" is that date, not a projection from last year.
            expected = datetime.strptime(last, "%Y-%m-%d").date()
            row_last = resolved["last"] if resolved else ""
            confidence = "verified"
            source = "engine"
            observed_on = last
        elif resolved is None:
            continue
        else:
            row_last = resolved["last"]
            expected = resolved["expected"]
            confidence = resolved["confidence"]
            source = resolved["source"]
            observed_on = ""

        out.append({
            "company": name,
            "last_cycle_posted": row_last,
            "approx": confidence == "floor",   # "by <date>", not "on <date>"
            "confidence": confidence,          # verified | estimated | floor
            "source": source,                  # engine | reference
            "expected": expected.strftime("%Y-%m-%d"),
            "days_until": (expected - today).days,
            "status": "posted" if is_posted else "waiting",
            "posted_on": observed_on,          # real drop date, when we caught it
            "url": posted_url or "",
            "roles_last_cycle": count,
        })

    # Posted-this-cycle first (they're the live signal), then soonest expected.
    out.sort(key=lambda r: (r["status"] != "posted", r["expected"], -r["roles_last_cycle"]))
    return out


# --- display helpers (shared by README + dashboard) -----------------------------

def pretty_last(row: dict) -> str:
    if row["status"] == "posted" and row.get("posted_on"):
        return datetime.strptime(row["posted_on"], "%Y-%m-%d").strftime("%b %d")
    if not row.get("last_cycle_posted"):
        return "—"
    d = datetime.strptime(row["last_cycle_posted"], "%Y-%m-%d").strftime("%b %d")
    return f"by {d}" if row["approx"] else d


def pretty_expected(row: dict) -> str:
    if row["status"] == "posted":
        if row.get("posted_on"):
            d = datetime.strptime(row["posted_on"], "%Y-%m-%d").strftime("%b %d")
            return f"dropped {d}"
        return "live now"
    d = datetime.strptime(row["expected"], "%Y-%m-%d")
    label = f"~{d.strftime('%b %d')}"
    if row["approx"]:
        label += " or earlier"
    days = row["days_until"]
    if days <= 0:
        return f"{label} · any day now"
    if days <= 45:
        return f"{label} · in ~{days}d"
    return label


def confidence_note(row: dict) -> str:
    """Short trust label for the UI."""
    return {
        "verified": "verified",
        "estimated": "estimated",
        "floor": "latest bound",
    }.get(row.get("confidence", "estimated"), "estimated")
