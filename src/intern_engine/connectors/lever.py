"""Lever postings API: public, no auth. Returns a bare JSON list."""

from __future__ import annotations

from datetime import datetime, timezone

from ..models import Job
from ..net import Net

URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


def _epoch_ms_to_iso(ms) -> str | None:
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except (ValueError, OSError, TypeError):
        return None


async def fetch(company: dict, net: Net) -> list[Job]:
    slug = company["slug"]
    postings = await net.get_json(URL.format(slug=slug))

    jobs = []
    for posting in postings:
        categories = posting.get("categories") or {}
        jobs.append(
            Job(
                id=f"lever:{slug}:{posting.get('id')}",
                source="lever",
                company=company["name"],
                company_slug=slug,
                title=(posting.get("text") or "").strip(),
                location=(categories.get("location") or "—").strip() or "—",
                url=posting.get("hostedUrl") or posting.get("applyUrl") or "",
                posted_at=_epoch_ms_to_iso(posting.get("createdAt")),
            )
        )
    return jobs
