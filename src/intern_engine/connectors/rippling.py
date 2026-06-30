"""Rippling ATS board API: public JSON list, no auth."""

from __future__ import annotations

from ..models import Job
from ..net import Net

URL = "https://api.rippling.com/platform/api/ats/v1/board/{slug}/jobs"


async def fetch(company: dict, net: Net) -> list[Job]:
    slug = company["slug"]
    postings = await net.get_json(URL.format(slug=slug))

    jobs = []
    for p in postings:
        location = p.get("workLocation") or {}
        label = location.get("label") if isinstance(location, dict) else None
        jobs.append(
            Job(
                id=f"rippling:{slug}:{p.get('uuid')}",
                source="rippling",
                company=company["name"],
                company_slug=slug,
                title=(p.get("name") or "").strip(),
                location=(label or "—").strip() or "—",
                url=p.get("url") or "",
                posted_at=None,  # board API exposes no posting date
            )
        )
    return jobs
