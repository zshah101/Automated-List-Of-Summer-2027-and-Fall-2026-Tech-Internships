"""Ashby connector.

Public, no-auth JSON at:
  https://api.ashbyhq.com/posting-api/job-board/{slug}
Filter to isListed == true to skip drafts/unlisted roles.
"""

from __future__ import annotations

import requests

from ..models import Job

URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


def fetch(company: dict, session: requests.Session) -> list[Job]:
    slug = company["slug"]
    resp = session.get(URL.format(slug=slug), timeout=15)
    resp.raise_for_status()
    data = resp.json()

    jobs: list[Job] = []
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        job_url = j.get("jobUrl") or j.get("applyUrl") or ""
        # Ashby has no plain numeric id in this API; derive one from the URL.
        external = job_url.rstrip("/").split("/")[-1] if job_url else (j.get("title") or "")
        jobs.append(
            Job(
                id=f"ashby:{slug}:{external}",
                source="ashby",
                company=company["name"],
                company_slug=slug,
                title=(j.get("title") or "").strip(),
                location=(j.get("location") or "—").strip() or "—",
                url=job_url,
                posted_at=j.get("publishedAt"),
            )
        )
    return jobs
