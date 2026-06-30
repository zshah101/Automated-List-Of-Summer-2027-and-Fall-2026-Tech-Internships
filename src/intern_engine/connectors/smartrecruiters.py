"""SmartRecruiters connector.

Public, no-auth JSON at:
  https://api.smartrecruiters.com/v1/companies/{company}/postings
We pass ?q=intern so the server only returns internship-ish postings.
SmartRecruiters exposes a real `releasedDate` — an accurate posting date.

Note: SmartRecruiters company identifiers are CASE-SENSITIVE (e.g. "ExpediaGroup"),
so unlike the other ATS we never lowercase these slugs.
"""

from __future__ import annotations

import requests

from ..models import Job

URL = "https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&q=intern"

_COUNTRY = {
    "us": "United States", "ca": "Canada", "gb": "United Kingdom",
    "in": "India", "de": "Germany", "ie": "Ireland", "au": "Australia",
}


def _location(loc) -> str:
    if not isinstance(loc, dict):
        return "—"
    country_code = (loc.get("country") or "").lower()
    country = _COUNTRY.get(country_code, (loc.get("country") or "").upper())
    parts = [loc.get("city"), loc.get("region"), country]
    text = ", ".join(p for p in parts if p)
    if loc.get("remote"):
        text = f"{text} (Remote)" if text else "Remote"
    return text or "—"


def fetch(company: dict, session: requests.Session) -> list[Job]:
    slug = company["slug"]
    resp = session.get(URL.format(slug=slug), timeout=15)
    resp.raise_for_status()
    data = resp.json()

    jobs: list[Job] = []
    for p in data.get("content", []):
        pid = p.get("id")
        jobs.append(
            Job(
                id=f"smartrecruiters:{slug}:{pid}",
                source="smartrecruiters",
                company=company["name"],
                company_slug=slug,
                title=(p.get("name") or "").strip(),
                location=_location(p.get("location")),
                url=f"https://jobs.smartrecruiters.com/{slug}/{pid}",
                posted_at=p.get("releasedDate"),  # real published date
            )
        )
    return jobs
