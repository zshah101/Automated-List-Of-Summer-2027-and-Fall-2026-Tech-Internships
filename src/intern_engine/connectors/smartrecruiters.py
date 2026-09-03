"""SmartRecruiters postings API: public, no auth.

We union several targeted queries (internship, co-op, student, then the broad
intern fallback) and read `releasedDate` for an accurate posting date. Company
identifiers are case-sensitive, so discovery preserves their case. Each query
is paginated by offset and advertises incompleteness if its safety cap is hit.
"""

from __future__ import annotations

from ..models import (
    INCOMPLETE_CAPPED,
    INCOMPLETE_MALFORMED,
    Fetch,
    Job,
    clean_listing,
    source_board_key,
)
from ..net import Net

URL = "https://api.smartrecruiters.com/v1/companies/{slug}/postings"

_PAGE_SIZE = 100
_MAX_JOBS = 300
_QUERIES = ("internship", "co-op", "student", "intern")

_COUNTRY = {
    "us": "United States", "ca": "Canada", "gb": "United Kingdom",
    "in": "India", "de": "Germany", "ie": "Ireland", "au": "Australia",
    "il": "Israel", "ar": "Argentina", "co": "Colombia",
    "id": "Indonesia", "me": "Montenegro",
    # Southeast Asia - the tracked region. Without these an SG posting comes
    # back as "International (SG)", which the region filter cannot read.
    "sg": "Singapore", "my": "Malaysia", "th": "Thailand",
    "vn": "Vietnam", "ph": "Philippines",
}

_COUNTRY_ALIASES = {
    "usa": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
}


def _meaningful(value) -> str:
    text = str(value or "").strip(" ,;|-\t\r\n")
    return text if any(ch.isalnum() for ch in text) else ""


def _country_name(value) -> str:
    raw = _meaningful(value)
    if not raw:
        return ""
    lowered = raw.lower()
    if lowered in _COUNTRY:
        return _COUNTRY[lowered]
    if lowered in _COUNTRY_ALIASES:
        return _COUNTRY_ALIASES[lowered]
    if len(raw) == 2 and raw.isalpha():
        # Unknown ISO codes must not escape as a US-state-looking token.
        return f"International ({raw.upper()})"
    return raw


def _location(loc, posting: dict | None = None) -> str:
    if not isinstance(loc, dict):
        loc = {}
    posting = posting or {}
    country = _country_name(loc.get("country"))
    city = _meaningful(loc.get("city"))
    region = _meaningful(loc.get("region"))
    full = _meaningful(loc.get("fullLocation"))

    # A fullLocation is authoritative only when it spells out a country. The
    # common "Tel Aviv, IL" shape is not safe: IL looks exactly like Illinois.
    components = [part.strip().lower() for part in full.split(",") if part.strip()]
    country_names = {
        name.lower() for name in {*_COUNTRY.values(), *_COUNTRY_ALIASES.values()}
    }
    country_names.update({"us", "usa", "u.s.", "u.s.a.", "uk"})
    explicit_country = bool(components and components[-1] in country_names)
    if full and explicit_country:
        text = full
    else:
        # With no country, a two-letter region is ambiguous: `IL` can mean
        # Illinois or Israel. Keep the city, but do not manufacture US evidence.
        safe_region = region if country or len(region) != 2 else ""
        text = ", ".join(p for p in (city, safe_region, country) if p)

    remote = bool(loc.get("remote") or posting.get("remote"))
    hybrid = bool(loc.get("hybrid") or posting.get("hybrid"))
    workplace = str(posting.get("workplace") or loc.get("workplace") or "").lower()
    remote = remote or workplace == "remote"
    hybrid = hybrid or workplace == "hybrid"
    if hybrid:
        text = f"{text} (Hybrid)" if text else "Hybrid"
    elif remote:
        text = f"{text} (Remote)" if text else "Remote"
    return text or "—"


async def fetch(company: dict, net: Net) -> Fetch:
    slug = company["slug"]

    jobs: dict[str, Job] = {}
    incomplete_reason: str | None = None
    for query in _QUERIES:
        exhausted = False
        trusted_total: int | None = None
        for offset in range(0, _MAX_JOBS, _PAGE_SIZE):
            params = {"limit": _PAGE_SIZE, "offset": offset, "q": query}
            data = await net.get_json(URL.format(slug=slug), params=params)
            postings = clean_listing(data, "content")
            if postings is None:
                incomplete_reason = INCOMPLETE_MALFORMED
                break  # malformed 200 / error envelope: not an empty board
            total = data.get("totalFound") if isinstance(data, dict) else None
            if (
                trusted_total is None
                and isinstance(total, int)
                and not isinstance(total, bool)
                and total > 0
                and total >= offset + len(postings)
            ):
                trusted_total = total
            for posting in postings:
                pid = posting.get("id")
                canonical = posting.get("uuid") or posting.get("jobId")
                requisition = posting.get("refNumber")
                job = Job(
                    id=f"smartrecruiters:{slug}:{pid}",
                    source="smartrecruiters",
                    company=company["name"],
                    company_slug=slug,
                    title=(posting.get("name") or "").strip(),
                    location=_location(posting.get("location"), posting),
                    url=f"https://jobs.smartrecruiters.com/{slug}/{pid}",
                    posted_at=posting.get("releasedDate"),
                    board_key=source_board_key(company, "smartrecruiters", slug),
                    canonical_id=str(canonical) if canonical not in (None, "") else None,
                    requisition_id=str(requisition) if requisition not in (None, "") else None,
                )
                jobs.setdefault(job.id, job)
            if len(postings) < _PAGE_SIZE:
                exhausted = True
                break
            if trusted_total is not None and offset + len(postings) >= trusted_total:
                exhausted = True
                break
        if not exhausted:
            incomplete_reason = incomplete_reason or INCOMPLETE_CAPPED
    return Fetch(
        list(jobs.values()),
        complete=incomplete_reason is None,
        incomplete_reason=incomplete_reason,
    )
