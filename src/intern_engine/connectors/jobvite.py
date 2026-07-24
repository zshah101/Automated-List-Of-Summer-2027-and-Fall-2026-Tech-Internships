"""Jobvite hosted-careers pages.

The public search pages are server-rendered HTML, not JSON. We scan the jobs
list pages directly and then use the job detail page's JSON-LD to backfill the
posted date plus the full description text.
"""

from __future__ import annotations

import asyncio
import json
import re
from html import unescape

from ..models import Job
from ..net import Net

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

_MAX_PAGES = 10
_PAGE_DELAY_SECONDS = 0.15


async def _sleep(seconds: float) -> None:
    await asyncio.sleep(seconds)


def _origin(company: dict) -> str | None:
    slug = (company.get("slug") or "").strip()
    if not slug:
        return None
    return "https://jobs.jobvite.com"


def _search_url(origin: str, company_slug: str, page: int) -> str:
    return f"{origin}/{company_slug}/search?p={page}"


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _job_id(url: str) -> str:
    match = re.search(r"/job/([^/?#]+)", url)
    return match.group(1) if match else url.rsplit("/", 1)[-1]


def _json_ld_nodes(html: str) -> list[dict]:
    nodes: list[dict] = []
    for raw in re.findall(r'<script\b[^>]*type="application/ld\+json"[^>]*>([\s\S]*?)</script>', html):
        try:
            data = json.loads(raw)
        except Exception:  # noqa: BLE001 - malformed JSON-LD should not break the run
            continue
        if isinstance(data, list):
            nodes.extend(node for node in data if isinstance(node, dict))
        elif isinstance(data, dict) and isinstance(data.get("@graph"), list):
            nodes.extend(node for node in data["@graph"] if isinstance(node, dict))
        elif isinstance(data, dict):
            nodes.append(data)
    return nodes


def _job_posting_node(nodes: list[dict]) -> dict | None:
    for node in nodes:
        node_type = node.get("@type")
        if node_type == "JobPosting" or (isinstance(node_type, list) and "JobPosting" in node_type):
            return node
    for node in nodes:
        if node.get("datePosted"):
            return node
    return None


def _parse_list_page(html: str, origin: str, company_slug: str, company_name: str) -> tuple[list[Job], str | None]:
    jobs: list[Job] = []
    next_page: str | None = None
    for card in re.findall(r'<li class="row">([\s\S]*?)</li>', html):
        href = re.search(r'href="([^"]*/job/[^"]+)"', card)
        title = re.search(r'<div class="jv-job-list-name">\s*([\s\S]*?)\s*</div>', card)
        location = re.search(r'<div class="ml-auto jv-job-list-location">\s*([\s\S]*?)\s*</div>', card)
        if not href or not title:
            continue
        path = href.group(1)
        jobs.append(
            Job(
                id=f"jobvite:{company_slug}:{_job_id(path)}",
                source="jobvite",
                company=company_name,
                company_slug=company_slug,
                title=_collapse(title.group(1)),
                location=_collapse(location.group(1)) if location else "",
                url=f"{origin}{path}",
            )
        )
    next_link = re.search(r'<a href="([^"]*p=(\d+)[^"]*)" class="jv-pagination-next">', html)
    if next_link:
        next_page = next_link.group(2)
    return jobs, next_page


async def fetch(company: dict, net: Net) -> list[Job]:
    origin = _origin(company)
    if not origin:
        raise ValueError(f"jobvite: cannot derive board origin for {company.get('name')}")

    jobs: list[Job] = []
    company_name = (company.get("name") or company.get("slug") or "").strip()
    company_slug = (company.get("slug") or "").strip() or company_name.lower().replace(" ", "-")
    page = 0
    seen_first_url: str | None = None
    for _ in range(_MAX_PAGES):
        if page > 0:
            await _sleep(_PAGE_DELAY_SECONDS)
        # Redirect behavior is configured once on the shared httpx client in
        # pipeline._fetch_all.  `redirect` is not an httpx request argument.
        html = await net.get_text(_search_url(origin, company_slug, page), headers=HEADERS)
        page_jobs, next_page = _parse_list_page(html, origin, company_slug, company_name)
        if not page_jobs:
            break
        if seen_first_url == page_jobs[0].url:
            break
        seen_first_url = page_jobs[0].url
        jobs.extend(page_jobs)
        if next_page is None:
            break
        page = int(next_page)
    return jobs


async def enrich_date(job: Job, net: Net) -> str | None:
    html = await net.get_text(job.url, headers=HEADERS)
    nodes = _json_ld_nodes(html)
    posting = _job_posting_node(nodes)
    if posting is None:
        return None
    start = posting.get("datePosted") or posting.get("startDate")
    if not job.posted_at and isinstance(start, str) and len(start) == 10:
        job.posted_at = f"{start}T00:00:00Z"
    desc = posting.get("description") or posting.get("jobDescription")
    if isinstance(desc, str) and desc.strip():
        return desc
    desc_match = re.search(
        r'<div class="jv-job-detail-description"[^>]*>\s*<h6>Description</h6>([\s\S]*?)</div>',
        html,
        re.I,
    )
    return desc_match.group(1) if desc_match else None
