"""Workday (enterprise tier).

Per-tenant POST API behind bot management. We send browser-like headers and
isolate failures per company. Dates are relative text ("Posted 6 Days Ago");
we resolve the precise ones and blank the vague ones ("30+ Days Ago").

Cloud IPs are blocked more than home IPs, so the pipeline routes this connector
through an optional proxy (WORKDAY_PROXY) when one is configured.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from ..models import Job
from ..net import Net

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
}

_DAYS_AGO = re.compile(r"(\d+)\s*\+?\s*days?\s+ago", re.IGNORECASE)


def _resolve_posted(text: str | None) -> str | None:
    if not text:
        return None
    lowered = text.lower()
    if "today" in lowered:
        days = 0
    elif "yesterday" in lowered:
        days = 1
    elif "30+" in lowered:
        return None  # too vague to be a real date
    else:
        match = _DAYS_AGO.search(lowered)
        if not match or int(match.group(1)) >= 30:
            return None
        days = int(match.group(1))
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")


async def fetch(company: dict, net: Net) -> list[Job]:
    tenant, wd, site = company["slug"], company["wd"], company["site"]
    url = f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    body = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "intern"}

    data = await net.post_json(url, json=body, headers=HEADERS)

    base = f"https://{tenant}.{wd}.myworkdayjobs.com/{site}"
    jobs = []
    for posting in data.get("jobPostings", []):
        path = posting.get("externalPath") or ""
        jobs.append(
            Job(
                id=f"workday:{tenant}:{path or posting.get('title')}",
                source="workday",
                company=company["name"],
                company_slug=tenant,
                title=(posting.get("title") or "").strip(),
                location=(posting.get("locationsText") or "—").strip() or "—",
                url=(base + path) if path else base,
                posted_at=_resolve_posted(posting.get("postedOn")),
            )
        )
    return jobs
