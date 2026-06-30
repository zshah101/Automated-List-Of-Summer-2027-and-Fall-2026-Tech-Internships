"""Greenhouse board API: public, no auth."""

from __future__ import annotations

from ..models import Job
from ..net import Net

URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"


async def fetch(company: dict, net: Net) -> list[Job]:
    slug = company["slug"]
    data = await net.get_json(URL.format(slug=slug))

    jobs = []
    for posting in data.get("jobs", []):
        location = posting.get("location") or {}
        name = location.get("name") if isinstance(location, dict) else None
        jobs.append(
            Job(
                id=f"greenhouse:{slug}:{posting.get('id')}",
                source="greenhouse",
                company=company["name"],
                company_slug=slug,
                title=(posting.get("title") or "").strip(),
                location=(name or "").strip() or "—",
                url=posting.get("absolute_url") or "",
                # The board API exposes only `updated_at` (last edit), not a true
                # publish date, so we leave it blank rather than mislead.
                posted_at=None,
            )
        )
    return jobs
