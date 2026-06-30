"""Lever connector.

Public, no-auth JSON at:
  https://api.lever.co/v0/postings/{slug}?mode=json
Returns a bare JSON list of postings.
"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from ..models import Job

URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


def _ms_to_iso(ms) -> str | None:
    """Lever gives createdAt as milliseconds since epoch."""
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except (ValueError, OSError, TypeError):
        return None


def fetch(company: dict, session: requests.Session) -> list[Job]:
    slug = company["slug"]
    resp = session.get(URL.format(slug=slug), timeout=15)
    resp.raise_for_status()
    data = resp.json()

    jobs: list[Job] = []
    for p in data:  # Lever returns a list
        categories = p.get("categories") or {}
        jobs.append(
            Job(
                id=f"lever:{slug}:{p.get('id')}",
                source="lever",
                company=company["name"],
                company_slug=slug,
                title=(p.get("text") or "").strip(),
                location=(categories.get("location") or "—").strip() or "—",
                url=p.get("hostedUrl") or p.get("applyUrl") or "",
                posted_at=_ms_to_iso(p.get("createdAt")),
            )
        )
    return jobs
