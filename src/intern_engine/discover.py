"""Discover companies at scale from public internship datasets.

We do NOT republish other people's listings. We read their data files only to
learn *which companies exist and on which ATS*, by pulling the ATS token (and,
for Workday/Oracle, the tenant + site) out of each apply URL. Those are merged
into data/companies.json, and from then on we poll each company's feed DIRECTLY.

Two kinds of sources:
  - JSON datasets (Simplify-style listings.json): give us token + company name
  - raw README markdown: mined with the same URL patterns, name falls back to a
    prettified slug (the quality gate + circuit breaker deal with the rest)

Junk control is downstream by design: the blocklist hides staffing agencies,
and the circuit breaker quarantines dead boards — so discovery can stay greedy.

Run with:  python run.py discover
"""

from __future__ import annotations

import json
import re

import requests

from . import registry

JSON_SOURCES = [
    # Current + upcoming cycles first (freshest tokens), then older cycles —
    # old boards mostly still exist, and dead ones get quarantined anyway.
    "https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/.github/scripts/listings.json",
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json",
    "https://raw.githubusercontent.com/vanshb03/Summer2026-Internships/dev/.github/scripts/listings.json",
    "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json",
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/dev/.github/scripts/listings.json",
    "https://raw.githubusercontent.com/Ouckah/Summer2025-Internships/dev/.github/scripts/listings.json",
]

MARKDOWN_SOURCES = [
    "https://raw.githubusercontent.com/speedyapply/2027-SWE-College-Jobs/main/README.md",
    "https://raw.githubusercontent.com/speedyapply/2026-SWE-College-Jobs/main/README.md",
    # Singapore / SEA. The lists above are US-facing, so on their own they
    # discover almost no regional employer: these three carry the SG boards
    # (banks, statutory boards, the regional quant desks) that never appear on
    # a US list. The 2024 one is deliberately kept - a board slug outlives the
    # cycle it was posted for, and dead ones get quarantined anyway.
    "https://raw.githubusercontent.com/didtheyghostme/Singapore-Summer2026-TechInternships/main/README.md",
    "https://raw.githubusercontent.com/kxrt/Singapore-Summer2024-TechInternships/main/README.md",
    "https://raw.githubusercontent.com/sushinoya/singapore-tech-internships/master/README.md",
]

# Pull the company token out of an ATS apply URL.
_PATTERNS = {
    "greenhouse": [
        re.compile(r"(?:job-boards|boards)\.greenhouse\.io/([a-z0-9][a-z0-9_\-]*)", re.I),
        re.compile(r"greenhouse\.io/embed/job_app\?for=([a-z0-9][a-z0-9_\-]*)", re.I),
        re.compile(r"//([a-z0-9][a-z0-9_\-]*)\.greenhouse\.io", re.I),
    ],
    "lever": [re.compile(r"jobs\.lever\.co/([a-z0-9][a-z0-9_\-]*)", re.I)],
    "ashby": [re.compile(r"jobs\.ashbyhq\.com/([a-z0-9][a-z0-9_\-]*)", re.I)],
    "smartrecruiters": [re.compile(r"jobs\.smartrecruiters\.com/([A-Za-z0-9][\w\-]*)")],
    "rippling": [re.compile(r"ats\.rippling\.com/(?:[a-z]{2}-[A-Z]{2}/)?([\w-]+)/jobs", re.I)],
    "workable": [re.compile(r"apply\.workable\.com/([a-z0-9][\w\-]*)/j/", re.I)],
    "breezy": [re.compile(r"//([\w-]+)\.breezy\.hr", re.I)],
    "recruitee": [re.compile(r"//([\w-]+)\.recruitee\.com", re.I)],
}

_BLOCKLIST = {"jobs", "www", "careers", "job", "embed", "search", "api", "boards", "job-boards"}

# Workday: both public URL shapes. Capture tenant, datacenter/host, and site.
_WD_SUB_RE = re.compile(
    r"https://([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([\w%-]+)",
    re.I,
)
_WD_SITE_RE = re.compile(
    r"https://(wd\d+\.myworkdaysite\.com)/(?:[a-z]{2}-[A-Z]{2}/)?recruiting/([\w-]+)/([\w%-]+)",
    re.I,
)
_WD_BAD_SITES = {"job", "jobs", "en", "en-us", "recruiting", "login"}

# Oracle Recruiting Cloud: per-tenant host + site number (CX_1, CX_2001, ...).
_ORC_RE = re.compile(
    r"https://([\w.-]+\.oraclecloud\.com)/hcmUI/CandidateExperience/[a-z\-]+/sites/(CX_[\w]+)",
    re.I,
)


def _prettify(slug: str) -> str:
    """A displayable company name for tokens mined without one."""
    return re.sub(r"[-_]+", " ", slug).strip().title()


def _extract_simple(text: str, names: dict[str, str]) -> dict:
    """{(ats, slug): company_name} for every simple-token ATS in a text blob."""
    found: dict[tuple[str, str], str] = {}
    for ats, patterns in _PATTERNS.items():
        for pattern in patterns:
            for slug in pattern.findall(text):
                if ats != "smartrecruiters":
                    slug = slug.lower()
                if slug.lower() in _BLOCKLIST:
                    continue
                name = names.get(f"{ats}:{slug.lower()}") or _prettify(slug)
                found.setdefault((ats, slug), name)
    return found


def _extract_workday(text: str, names: dict[str, str]) -> dict:
    """{(tenant, site): record} for every Workday tenant in a text blob."""
    found: dict[tuple[str, str], dict] = {}
    for m in _WD_SUB_RE.finditer(text):
        tenant, wd, site = m.group(1).lower(), m.group(2).lower(), m.group(3)
        if site.lower() in _WD_BAD_SITES:
            continue
        name = (names.get(f"workday:{tenant}:{site.casefold()}")
                or names.get(f"workday:{tenant}") or _prettify(tenant))
        found.setdefault((tenant, site), {"name": name, "tenant": tenant, "wd": wd, "site": site})
    for m in _WD_SITE_RE.finditer(text):
        host, tenant, site = m.group(1).lower(), m.group(2).lower(), m.group(3)
        if site.lower() in _WD_BAD_SITES:
            continue
        name = (names.get(f"workday:{tenant}:{site.casefold()}")
                or names.get(f"workday:{tenant}") or _prettify(tenant))
        found.setdefault(
            (tenant, site),
            {"name": name, "tenant": tenant, "wd": host.split(".")[0], "site": site, "host": host},
        )
    return found


def _extract_oracle(text: str, names: dict[str, str]) -> dict:
    """{(host, site): record} for every Oracle Recruiting Cloud tenant."""
    found: dict[tuple[str, str], dict] = {}
    for m in _ORC_RE.finditer(text):
        host, site = m.group(1).lower(), m.group(2)
        name = (names.get(f"oracle:{host}:{site.casefold()}")
                or names.get(f"oracle:{host}") or _prettify(host.split(".")[0]))
        found.setdefault((host, site), {"name": name, "host": host, "site": site})
    return found


def _listing_names(listings: list) -> dict[str, str]:
    """Map "ats:token" -> real company name, learned from each listing's own URL.

    JSON datasets pair a company_name with an apply URL; matching the patterns
    per listing (not per file) keeps names attached to the right token.
    """
    names: dict[str, str] = {}
    for item in listings:
        if not isinstance(item, dict):
            continue
        name = (item.get("company_name") or "").strip()
        if not name:
            continue
        blob = " ".join(str(item.get(k, "")) for k in ("url", "company_url"))
        for ats, patterns in _PATTERNS.items():
            for pattern in patterns:
                for slug in pattern.findall(blob):
                    names.setdefault(f"{ats}:{slug.lower()}", name)
        m = _WD_SUB_RE.search(blob) or _WD_SITE_RE.search(blob)
        if m:
            tenant = (m.group(2) if "myworkdaysite" in m.group(1) else m.group(1)).lower()
            site = m.group(3)
            names.setdefault(f"workday:{tenant}:{site.casefold()}", name)
            names.setdefault(f"workday:{tenant}", name)
        m = _ORC_RE.search(blob)
        if m:
            names.setdefault(
                f"oracle:{m.group(1).lower()}:{m.group(2).casefold()}", name
            )
            names.setdefault(f"oracle:{m.group(1).lower()}", name)
    return names


def discover() -> tuple[list[dict], int]:
    session = requests.Session()
    session.headers.update({"User-Agent": "intern-engine/3.0 (+github.com/intern-engine)"})

    simple: dict[tuple[str, str], str] = {}
    wd: dict[tuple[str, str], dict] = {}
    orc: dict[tuple[str, str], dict] = {}

    for url in JSON_SOURCES + MARKDOWN_SOURCES:
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            if url.endswith(".json"):
                data = resp.json()
                if isinstance(data, dict):
                    data = data.get("listings") or list(data.values())
                if not isinstance(data, list):
                    raise ValueError("source JSON is not a listings array")
                names = _listing_names(data)
                text = json.dumps(data)
            else:
                names = {}
                text = resp.text
            # Sources are ordered freshest-first.  First wins preserves the
            # current dataset's real company name instead of letting a stale
            # slug-derived name from a later source overwrite it.
            for key, value in _extract_simple(text, names).items():
                simple.setdefault(key, value)
            for key, value in _extract_workday(text, names).items():
                wd.setdefault(key, value)
            for key, value in _extract_oracle(text, names).items():
                orc.setdefault(key, value)
        except (requests.RequestException, ValueError) as exc:
            print(f"  source failed: {url} ({exc})")

    # Merge into existing companies.json, preserving full records (incl. wd/site).
    merged = {registry.board_key(c): c for c in registry.load(missing_ok=True)}

    for (ats, slug), name in simple.items():
        record = registry.validate_company({"name": name, "slug": slug, "ats": ats})
        merged.setdefault(registry.board_key(record), record)
    for info in wd.values():
        record = {
            "name": info["name"], "slug": info["tenant"], "ats": "workday",
            "wd": info["wd"], "site": info["site"],
        }
        if info.get("host"):
            record["host"] = info["host"]  # path-style tenant (myworkdaysite.com)
        record = registry.validate_company(record)
        merged.setdefault(registry.board_key(record), record)
    for info in orc.values():
        record = registry.validate_company({
            "name": info["name"], "slug": info["host"], "ats": "oracle",
            "host": info["host"], "site": info["site"],
        })
        merged.setdefault(registry.board_key(record), record)
    # Amazon is one fixed search endpoint, not discovered per-URL.
    amazon = {"name": "Amazon", "slug": "amazon", "ats": "amazon"}
    merged.setdefault(registry.board_key(amazon), amazon)

    companies = sorted(merged.values(), key=lambda c: c["name"].lower())
    registry.save(companies)

    return companies, len(simple) + len(wd) + len(orc) + 1
