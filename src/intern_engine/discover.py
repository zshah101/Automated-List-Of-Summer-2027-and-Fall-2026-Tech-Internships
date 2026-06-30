"""Discover companies at scale from public internship datasets.

We do NOT republish other people's listings. Instead we read their data files
purely to learn *which companies exist and on which ATS*, by pulling the ATS
token out of each apply URL. Those (ats, slug) pairs are merged into
data/companies.json, and from then on we poll each company's feed DIRECTLY —
our own live data, just a much bigger company list.

Run with:  python run.py discover
"""

from __future__ import annotations

import json
import re

import requests

from . import paths

# Public, maintained datasets we mine for company tokens (not for listings).
PUBLIC_SOURCES = [
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json",
    "https://raw.githubusercontent.com/vanshb03/Summer2026-Internships/dev/.github/scripts/listings.json",
]

# Pull the company token out of an ATS apply URL.
_PATTERNS = {
    "greenhouse": [
        re.compile(r"(?:job-boards|boards)\.greenhouse\.io/([a-z0-9][a-z0-9_\-]*)", re.I),
        re.compile(r"//([a-z0-9][a-z0-9_\-]*)\.greenhouse\.io", re.I),
    ],
    "lever": [re.compile(r"jobs\.lever\.co/([a-z0-9][a-z0-9_\-]*)", re.I)],
    "ashby": [re.compile(r"jobs\.ashbyhq\.com/([a-z0-9][a-z0-9_\-]*)", re.I)],
}

# Tokens that are URL noise, not real company slugs.
_BLOCKLIST = {"jobs", "www", "careers", "job", "embed", "search"}

HEADERS = {"User-Agent": "intern-engine/1.0 (+github.com/intern-engine)"}


def _extract(listings: list) -> dict:
    """Return {(ats, slug): company_name} from a list of listing dicts."""
    found: dict[tuple[str, str], str] = {}
    for item in listings:
        if not isinstance(item, dict):
            continue
        name = (item.get("company_name") or "").strip()
        blob = " ".join(str(item.get(k, "")) for k in ("url", "company_url"))
        for ats, patterns in _PATTERNS.items():
            for pattern in patterns:
                for slug in pattern.findall(blob):
                    slug = slug.lower()
                    if slug in _BLOCKLIST:
                        continue
                    key = (ats, slug)
                    if key not in found:
                        found[key] = name or slug
    return found


def discover() -> tuple[list[dict], int]:
    session = requests.Session()
    session.headers.update(HEADERS)

    discovered: dict[tuple[str, str], str] = {}
    for url in PUBLIC_SOURCES:
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                data = data.get("listings") or list(data.values())
            discovered.update(_extract(data))
        except (requests.RequestException, ValueError) as exc:
            print(f"  source failed: {url} ({exc})")

    # Merge with whatever companies we already have (keep existing names).
    merged: dict[tuple[str, str], str] = {}
    try:
        with open(paths.COMPANIES_PATH, encoding="utf-8") as f:
            for c in json.load(f):
                merged[(c["ats"], c["slug"])] = c["name"]
    except (OSError, json.JSONDecodeError, KeyError):
        pass

    for key, name in discovered.items():
        merged.setdefault(key, name)

    companies = [
        {"name": name, "slug": slug, "ats": ats}
        for (ats, slug), name in merged.items()
    ]
    companies.sort(key=lambda c: c["name"].lower())

    with open(paths.COMPANIES_PATH, "w", encoding="utf-8") as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)

    return companies, len(discovered)
