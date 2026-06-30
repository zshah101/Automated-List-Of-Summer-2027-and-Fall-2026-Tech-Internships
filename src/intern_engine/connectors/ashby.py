"""Ashby job board API: public, no auth."""

from __future__ import annotations

from ..models import Job
from ..net import Net

URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


async def fetch(company: dict, net: Net) -> list[Job]:
    slug = company["slug"]
    data = await net.get_json(URL.format(slug=slug))

    jobs = []
    for posting in data.get("jobs", []):
        if posting.get("isListed") is False:
            continue
        job_url = posting.get("jobUrl") or posting.get("applyUrl") or ""
        external = job_url.rstrip("/").rsplit("/", 1)[-1] if job_url else posting.get("title")
        jobs.append(
            Job(
                id=f"ashby:{slug}:{external}",
                source="ashby",
                company=company["name"],
                company_slug=slug,
                title=(posting.get("title") or "").strip(),
                location=(posting.get("location") or "—").strip() or "—",
                url=job_url,
                posted_at=posting.get("publishedAt"),
            )
        )
    return jobs
