"""Eightfold AI career sites (Netflix, American Express, Micron, ...).

One public JSON endpoint per tenant: /api/apply/v2/jobs on the company's own
careers host. The search payload carries each job's description and a real
creation timestamp, so sponsorship classification and posted dates are free —
no per-job detail requests.

Company entry shape:
    {"name": "Netflix", "slug": "netflix", "ats": "eightfold",
     "host": "explore.jobs.netflix.net", "domain": "netflix.com"}
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..models import Job
from ..net import Net

_PAGE = 100
_MAX = 300  # safety cap; "intern" on one tenant never legitimately needs more

_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "application/json",
}


def _posted(unix_ts) -> str | None:
    try:
        ts = int(unix_ts)
    except (TypeError, ValueError):
        return None
    if ts <= 0:
        return None
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _location(position: dict) -> str:
    locations = position.get("locations")
    if isinstance(locations, list) and locations:
        return "; ".join(str(x).replace(",", ", ") for x in locations[:4])
    return str(position.get("location") or "—").replace(",", ", ") or "—"


async def fetch(company: dict, net: Net) -> list[Job]:
    slug = company["slug"]
    host = company["host"]
    url = f"https://{host}/api/apply/v2/jobs"

    jobs: list[Job] = []
    start = 0
    while start < _MAX:
        params = {
            "domain": company.get("domain", ""),
            "query": "intern",
            "num": _PAGE,
            "start": start,
            "sort_by": "timestamp",
        }
        data = await net.get_json(url, params=params, headers=_BROWSER_HEADERS)
        positions = data.get("positions") or []
        for p in positions:
            external = p.get("id") or p.get("ats_job_id") or p.get("display_job_id")
            job_url = p.get("canonicalPositionUrl") or f"https://{host}/careers"
            jobs.append(
                Job(
                    id=f"eightfold:{slug}:{external}",
                    source="eightfold",
                    company=company["name"],
                    company_slug=slug,
                    title=(p.get("name") or "").strip(),
                    location=_location(p),
                    url=job_url,
                    posted_at=_posted(p.get("t_create")),
                    description=p.get("job_description") or None,
                )
            )
        start += _PAGE
        if len(positions) < _PAGE or start >= int(data.get("count") or 0):
            break
    return jobs
