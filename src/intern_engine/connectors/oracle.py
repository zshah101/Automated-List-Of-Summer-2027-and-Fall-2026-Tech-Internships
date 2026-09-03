"""Oracle Recruiting Cloud (enterprise + bank tenants).

Per-tenant like Workday: each company has its own oraclecloud.com host and a
site number (CX_1, CX_2001, ... — captured by discovery, not assumed). Public
REST endpoint, browser-like headers, paginated by offset.
"""

from __future__ import annotations

from ..models import (
    INCOMPLETE_CAPPED,
    INCOMPLETE_MALFORMED,
    INCOMPLETE_STALLED,
    Fetch,
    Job,
    clean_listing,
    source_board_key,
)
from ..net import Net

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
}

_PAGE_SIZE = 50
_MAX_JOBS = 200  # per keyword
# Like Workday, the keyword search is literal — "intern" alone drops co-ops.
_KEYWORDS = ("internship", "co-op", "student", "intern")

_COUNTRIES = {
    "US": "United States", "USA": "United States", "CA": "Canada",
    "GB": "United Kingdom", "IN": "India", "IL": "Israel",
    "AR": "Argentina", "CO": "Colombia", "ID": "Indonesia",
    # Southeast Asia - the tracked region. An unmapped code degrades to
    # "International (SG)", which the region filter cannot read.
    "SG": "Singapore", "MY": "Malaysia", "TH": "Thailand",
    "VN": "Vietnam", "PH": "Philippines",
}


def _posted(value) -> str | None:
    # Keep only real ISO-ish dates (YYYY-MM-...), ignore anything else.
    if isinstance(value, str) and len(value) >= 7 and value[:4].isdigit() and value[4] == "-":
        return value
    return None


def _positive_int(value) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _nonnegative_int(value) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _location(requisition: dict) -> str:
    """Preserve secondary locations, including advertised US options."""
    values: list[str] = []
    primary = str(requisition.get("PrimaryLocation") or "").strip()
    if primary:
        values.append(primary)
    secondary = requisition.get("secondaryLocations")
    if isinstance(secondary, list):
        for item in secondary:
            if not isinstance(item, dict):
                continue
            name = str(item.get("Name") or item.get("name") or "").strip()
            country = str(item.get("CountryCode") or "").strip().upper()
            if name and country:
                label = _COUNTRIES.get(country, f"International ({country})")
                if label.lower() not in name.lower():
                    name = f"{name}, {label}"
            if name and name not in values:
                values.append(name)
    return "; ".join(values) or "—"


async def fetch(company: dict, net: Net) -> Fetch:
    host = company["host"]
    site = company.get("site", "CX_1")
    tenant = company["slug"]
    url = f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
    base = f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job"

    jobs: dict[str, Job] = {}  # keyed by job id: the keyword searches overlap
    incomplete_reason: str | None = None
    for keyword in _KEYWORDS:
        exhausted = False
        offset = 0
        trusted_total: int | None = None
        seen_pages: set[tuple[str, ...]] = set()
        while offset < _MAX_JOBS:
            params = {
                "onlyData": "true",
                "expand": "requisitionList.secondaryLocations",
                "finder": f"findReqs;siteNumber={site},keyword={keyword},"
                          f"sortBy=POSTING_DATES_DESC,offset={offset}",
                "limit": str(_PAGE_SIZE),
            }
            data = await net.get_json(url, params=params, headers=HEADERS)
            items = clean_listing(data, "items")
            if items is None:
                incomplete_reason = INCOMPLETE_MALFORMED
                break  # malformed 200 / error envelope: not an empty board
            page = items[0] if items else {}
            requisitions = clean_listing(page, "requisitionList") if items else []
            if requisitions is None:
                incomplete_reason = INCOMPLETE_MALFORMED
                break
            for r in requisitions:
                rid = r.get("Id")
                job = Job(
                    id=f"oracle:{tenant}:{rid}",
                    source="oracle",
                    company=company["name"],
                    company_slug=tenant,
                    title=(r.get("Title") or "").strip(),
                    location=_location(r),
                    url=f"{base}/{rid}",
                    posted_at=_posted(r.get("PostedDate")),
                    board_key=source_board_key(company, "oracle", tenant),
                )
                jobs.setdefault(job.id, job)

            actual_offset = _nonnegative_int(page.get("Offset"))
            if actual_offset is None:
                actual_offset = offset
            total = _positive_int(page.get("TotalJobsCount"))
            if (
                trusted_total is None
                and total is not None
                and total >= actual_offset + len(requisitions)
            ):
                trusted_total = total
            actual_limit = _positive_int(page.get("Limit"))
            if actual_limit is None:
                actual_limit = len(requisitions) or _PAGE_SIZE
            end = actual_offset + len(requisitions)

            if trusted_total is not None and end >= trusted_total:
                exhausted = True
                break
            if not requisitions:
                if trusted_total is None or actual_offset >= trusted_total:
                    exhausted = True
                else:
                    incomplete_reason = incomplete_reason or INCOMPLETE_STALLED
                break
            if len(requisitions) < actual_limit and trusted_total is None:
                exhausted = True
                break
            signature = tuple(str(r.get("Id")) for r in requisitions)
            if signature in seen_pages:
                incomplete_reason = incomplete_reason or INCOMPLETE_STALLED
                break
            seen_pages.add(signature)

            # The API silently clamps requested limits (commonly 50 -> 25).
            # Its returned Offset/Limit define the only safe next page.
            next_offset = actual_offset + actual_limit
            if next_offset <= offset:
                incomplete_reason = incomplete_reason or INCOMPLETE_STALLED
                break
            offset = next_offset
        if not exhausted:
            incomplete_reason = incomplete_reason or INCOMPLETE_CAPPED
    return Fetch(
        list(jobs.values()),
        complete=incomplete_reason is None,
        incomplete_reason=incomplete_reason,
    )
