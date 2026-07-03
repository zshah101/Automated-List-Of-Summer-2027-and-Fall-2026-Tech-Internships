"""Build data/seasons.json: when each company FIRST posted last cycle.

Answers the question every applicant asks and no list answers: "when does
[company] usually drop its internships?" We mine last cycle's public listing
datasets for the earliest SWE/DS/Quant intern posting date per company, and the
engine projects that date one year forward as this cycle's expected window.

Run once per cycle (or whenever):    python tools/build_seasons.py

Sources are the public Simplify-format listing files (same ones discovery
mines for company tokens; we read date_posted, we do not republish listings).
"""

import json
import os
import re
import sys
from datetime import UTC, datetime

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from intern_engine import h1b, paths  # noqa: E402  (shared name normalizer)

CYCLE = "Summer 2026"          # the completed cycle we learn timing from
SOURCES = [
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json",
    "https://raw.githubusercontent.com/vanshb03/Summer2026-Internships/dev/.github/scripts/listings.json",
]

# Simplify's category values worth tracking for a tech list.
_CATEGORIES = {"Software", "Data Science, AI & Machine Learning", "Quantitative Finance"}
_TECH_TITLE_RE = re.compile(
    r"software|swe|developer|data|machine learning|\bml\b|\bai\b|quant|research",
    re.IGNORECASE,
)


def _wanted(item: dict) -> bool:
    if item.get("category") in _CATEGORIES:
        return True
    return bool(_TECH_TITLE_RE.search(item.get("title") or ""))


def build() -> dict:
    best: dict[str, dict] = {}
    for url in SOURCES:
        try:
            listings = httpx.get(url, timeout=90, follow_redirects=True).json()
        except Exception as exc:  # noqa: BLE001 — a dead source shouldn't kill the build
            print(f"  source failed: {url} ({type(exc).__name__})")
            continue
        for item in listings:
            if not isinstance(item, dict) or not item.get("date_posted"):
                continue
            name = (item.get("company_name") or "").strip()
            if not name or not _wanted(item):
                continue
            key = h1b.normalize(name)
            if not key:
                continue
            posted = datetime.fromtimestamp(item["date_posted"], tz=UTC).strftime("%Y-%m-%d")
            entry = best.setdefault(key, {"name": name, "first_posted": posted, "count": 0})
            entry["count"] += 1
            if posted < entry["first_posted"]:
                entry["first_posted"] = posted
                entry["name"] = name

    return {
        "cycle": CYCLE,
        "built_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "companies": dict(sorted(best.items())),
    }


def main() -> None:
    data = build()
    with open(paths.SEASONS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    size_kb = os.path.getsize(paths.SEASONS_PATH) // 1024
    print(f"{len(data['companies']):,} companies with a {CYCLE} first-post date "
          f"-> {paths.SEASONS_PATH} ({size_kb} KB)")


if __name__ == "__main__":
    main()
