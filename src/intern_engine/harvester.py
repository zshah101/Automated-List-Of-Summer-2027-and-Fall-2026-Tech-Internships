"""Discovery: turn a list of candidate company slugs into a validated registry.

There is no master directory of ATS boards, so we DISCOVER by probing: try each
slug against all three ATS and keep the ones that actually return jobs, recording
which ATS each lives on. Output -> data/companies.json (used by the pipeline).

This is how coverage grows: add slugs to data/candidates.json and re-harvest.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import requests

from . import paths

PROBES = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=1",
}

HEADERS = {"User-Agent": "intern-engine/1.0 (+github.com/intern-engine)"}


def _count(ats: str, payload) -> int:
    if ats == "lever":
        return len(payload) if isinstance(payload, list) else 0
    if ats == "smartrecruiters":
        if isinstance(payload, dict):
            return payload.get("totalFound", len(payload.get("content", [])))
        return 0
    return len(payload.get("jobs", [])) if isinstance(payload, dict) else 0


def detect(candidate: dict, session: requests.Session) -> dict | None:
    slug = candidate["slug"]
    for ats, template in PROBES.items():
        try:
            resp = session.get(template.format(slug=slug), timeout=12)
            if resp.status_code == 200 and _count(ats, resp.json()) > 0:
                return {"name": candidate["name"], "slug": slug, "ats": ats}
        except (requests.RequestException, ValueError):
            continue
    return None


def harvest() -> tuple[list[dict], list[dict]]:
    with open(paths.CANDIDATES_PATH, encoding="utf-8") as f:
        candidates = json.load(f)

    session = requests.Session()
    session.headers.update(HEADERS)

    found: list[dict] = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for result in pool.map(lambda c: detect(c, session), candidates):
            if result:
                found.append(result)

    found.sort(key=lambda c: c["name"].lower())
    with open(paths.COMPANIES_PATH, "w", encoding="utf-8") as f:
        json.dump(found, f, indent=2, ensure_ascii=False)

    return found, candidates
