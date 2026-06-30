"""Greenhouse connector.

Public, no-auth JSON at:
  https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
"""

from __future__ import annotations

import requests

from ..models import Job

URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"


def fetch(company: dict, session: requests.Session) -> list[Job]:
    slug = company["slug"]
    resp = session.get(URL.format(slug=slug), timeout=15)
    resp.raise_for_status()
    data = resp.json()

    jobs: list[Job] = []
    for j in data.get("jobs", []):
        location = ""
        if isinstance(j.get("location"), dict):
            location = j["location"].get("name") or ""
        jobs.append(
            Job(
                id=f"greenhouse:{slug}:{j.get('id')}",
                source="greenhouse",
                company=company["name"],
                company_slug=slug,
                title=(j.get("title") or "").strip(),
                location=location.strip() or "—",
                url=j.get("absolute_url") or "",
                posted_at=j.get("updated_at"),
            )
        )
    return jobs
