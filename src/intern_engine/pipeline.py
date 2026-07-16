"""The watcher + spotter.

One async pass per run: quarantine-check every tracked company (circuit
breaker), fetch the healthy ones concurrently (global + per-host concurrency
caps), normalize into one shape, keep the roles that match the configured
scope, de-duplicate across sources, enrich the keepers with posting text
(sponsorship classification + date backfill), merge into the store (detecting
what's new and what closed), and record run metrics + a history line.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import statistics
import time
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import httpx

from . import config, enrich, filters, health, models, observe, paths, quality, store, trends
from .connectors import (
    amazon,
    ashby,
    breezy,
    eightfold,
    greenhouse,
    lever,
    oracle,
    recruitee,
    rippling,
    smartrecruiters,
    workable,
    workday,
)
from .net import HostLimiter, Net

CONNECTORS = {
    "greenhouse": greenhouse.fetch,
    "lever": lever.fetch,
    "ashby": ashby.fetch,
    "smartrecruiters": smartrecruiters.fetch,
    "workday": workday.fetch,
    "amazon": amazon.fetch,
    "oracle": oracle.fetch,
    "rippling": rippling.fetch,
    "workable": workable.fetch,
    "breezy": breezy.fetch,
    "recruitee": recruitee.fetch,
    "eightfold": eightfold.fetch,
}

GLOBAL_CONCURRENCY = 32
PER_HOST_CONCURRENCY = 8
USER_AGENT = f"intern-engine/3.0 (+https://github.com/{config.repo_slug()})"


def _load_companies() -> list[dict]:
    with open(paths.COMPANIES_PATH, encoding="utf-8") as f:
        return json.load(f)


async def _fetch_one(company: dict, net: Net):
    """Return (company, jobs, error); never raises (failures are isolated)."""
    fetch = CONNECTORS.get(company.get("ats"))
    if fetch is None:
        return company, [], f"no connector for {company.get('ats')}"
    try:
        return company, await fetch(company, net), None
    except Exception as exc:  # noqa: BLE001 — one bad endpoint must not stop the run
        return company, [], f"{type(exc).__name__}: {exc}"


async def _fetch_all(companies: list[dict], enrich_after):
    """Fetch every company, then run `enrich_after(results, net)` on the same
    client session so enrichment reuses connections instead of reopening them."""
    limiter = HostLimiter(PER_HOST_CONCURRENCY)
    gate = asyncio.Semaphore(GLOBAL_CONCURRENCY)
    proxy = os.environ.get("WORKDAY_PROXY") or None

    common = dict(
        limits=httpx.Limits(max_connections=64, max_keepalive_connections=32),
        timeout=httpx.Timeout(20.0, connect=10.0),
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )

    async with httpx.AsyncClient(**common) as client:
        default_net = Net(client, limiter)
        workday_client = httpx.AsyncClient(proxy=proxy, **common) if proxy else None
        workday_net = Net(workday_client, limiter) if workday_client else default_net

        async def worker(company: dict):
            net = workday_net if company.get("ats") in ("workday", "oracle") else default_net
            async with gate:
                return await _fetch_one(company, net)

        try:
            results = await asyncio.gather(*(worker(c) for c in companies))
            enrich_result = await enrich_after(results, default_net, workday_net)
            return results, enrich_result
        finally:
            if workday_client is not None:
                await workday_client.aclose()


def _dedup(jobs: list) -> list:
    """Collapse the same role seen more than once (e.g. via two ATS).

    Keyed by company + normalized title; a posting that carries a real date wins
    over one that doesn't.
    """
    jobs = sorted(jobs, key=lambda j: (j.posted_at is None,))
    seen: set[tuple[str, str]] = set()
    unique = []
    for job in jobs:
        key = (job.company.lower().strip(), re.sub(r"[^a-z0-9]+", "", job.title.lower()))
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)
    return unique


def _keep_matching(results, cfg, blocklist, existing=None) -> tuple[list, set[str], int, Counter]:
    """Apply every scope filter; return (kept jobs, succeeded keys, errors, errors by ats).

    `existing` (the store) makes cycle assignment sticky for yearless titles: a
    season already on record — set by an earlier inference or verified from the
    posting's own text — is adopted as-is, never re-derived. Without this, a
    text-verified season would be re-guessed every run, and a role would flip
    "closed" the day its posting outgrew the inference recency window.
    """
    cycles = config.cycles(cfg)
    tech_only = cfg.get("role_scope", "tech") == "tech"
    restrict = config.restrict_region(cfg)
    include_intl = config.include_international(cfg)
    allowlist_only = config.allowlist_only(cfg)
    infer = config.infer_undated(cfg)
    infer_age = config.infer_max_age_days(cfg)
    max_age = config.max_age_days(cfg)
    cutoff = (
        (datetime.now(UTC) - timedelta(days=max_age)).strftime("%Y-%m-%d")
        if max_age else None
    )

    existing = existing or {}
    kept = []
    succeeded: set[str] = set()
    errors = 0
    errors_by_ats: Counter = Counter()
    dropped_no_year = 0  # tech internships we skip only because the title has no year
    for company, jobs, error in results:
        if error is not None:
            errors += 1
            errors_by_ats[company.get("ats", "?")] += 1
            continue
        succeeded.add(f"{company['ats']}:{company['slug']}")
        if quality.is_blocked(company["name"], blocklist):
            continue
        if allowlist_only and not quality.is_recognized(company["name"]):
            continue
        for job in jobs:
            if not filters.is_internship(job.title):
                continue
            if tech_only and not filters.is_tech(job.title):
                continue
            season = filters.detect_season(job.title, cycles)
            inferred = False
            if season is None:
                prior = existing.get(job.id) or {}
                if prior.get("season") in cycles:
                    season = prior["season"]  # sticky (see docstring)
                    inferred = bool(prior.get("season_inferred"))
                elif infer:
                    # The measured no-year pool dwarfed the explicit-year pool
                    # (~13x), so recent undated roles are bucketed by posting
                    # date, marked `~` everywhere they render, and checked
                    # against the posting text at enrichment time.
                    season = filters.infer_season(job.title, job.posted_at, cycles, infer_age)
                    inferred = season is not None
            if season is None:
                dropped_no_year += 1
                continue
            is_us = filters.is_united_states(job.location)
            if restrict and not is_us and not include_intl:
                continue
            loc = (job.location or "").strip()
            if not is_us and (not loc or loc == "—"):
                continue  # international roles need a real location
            posted_day = (job.posted_at or "")[:10]
            if cutoff and posted_day and posted_day < cutoff:
                continue
            job.season = season
            job.season_inferred = inferred
            job.category = filters.categorize(job.title)
            kept.append(job)
    return kept, succeeded, errors, errors_by_ats, dropped_no_year


def run_update() -> tuple[dict, dict, list[str]]:
    cfg = config.load_config()
    blocklist = quality.load_blocklist()
    companies = _load_companies()
    existing = store.load(paths.JOBS_PATH)

    health_data = health.load()
    active, benched = health.partition(companies, health_data)

    started = time.monotonic()
    kept: list = []
    enriched_ids: set[str] = set()
    detail_fetches = 0

    async def _enrich_stage(results, net, workday_net):
        """Filter first (cheap, sync), then enrich only the keepers."""
        nonlocal kept
        kept, succeeded, errors, errors_by_ats, no_year = _keep_matching(
            results, cfg, blocklist, existing
        )
        kept = _dedup(kept)
        # Workday/Oracle enrichment goes through the same proxied client as fetch.
        wd_jobs = [j for j in kept if j.source in ("workday", "oracle")]
        other = [j for j in kept if j.source not in ("workday", "oracle")]
        ids_a, n_a = await enrich.enrich_jobs(other, existing, net)
        ids_b, n_b = await enrich.enrich_jobs(wd_jobs, existing, workday_net)
        # Enrichment may have replaced an inferred cycle with the one the
        # posting text states; anything now off-cycle leaves the list.
        cycles = config.cycles(cfg)
        offcycle = sum(1 for j in kept if j.season not in cycles)
        kept = [j for j in kept if j.season in cycles]
        return succeeded, errors, errors_by_ats, ids_a | ids_b, n_a + n_b, no_year, offcycle

    results, (succeeded, errors, errors_by_ats, enriched_ids, detail_fetches, no_year,
              offcycle) = asyncio.run(_fetch_all(active, _enrich_stage))

    for company, _jobs, error in results:
        health.record(health_data, company, error)
    health.save(health_data)

    rows = []
    for job in kept:
        row = asdict(job)
        for field in models.TRANSIENT_FIELDS:
            row.pop(field, None)
        rows.append(row)

    new_ids = store.upsert(existing, rows, succeeded, enriched_ids)
    purged = store.purge(existing)
    store.save(paths.JOBS_PATH, existing)

    # Record the real posted dates we saw straight from the ATS. This is the
    # engine's own ground truth for the Drop Radar — it accrues every run and
    # eventually replaces the outside reference dataset entirely.
    observe.record_run(existing)

    stats = _build_stats(
        companies, benched, succeeded, errors, errors_by_ats, kept, existing, new_ids,
        len(enriched_ids), detail_fetches, purged, round(time.monotonic() - started, 1),
        no_year, offcycle,
    )
    _write_stats(stats)
    _append_history(stats)
    return stats, existing, new_ids


def _parse_iso(value: str) -> datetime | None:
    """Always returns a UTC-aware datetime: ATS feeds mix offset-less strings
    and date-only strings with full `Z`/`±HH:MM` timestamps, and one naive
    value next to an aware one makes the subtraction below raise TypeError."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def _detection_latency(existing: dict, window_days: int = 7) -> dict:
    """Median minutes between a role being published and us first seeing it.

    Only counts roles caught within `window_days` of their posting, so the figure
    reflects real-time detection rather than the one-off backfill of old roles.
    """
    window_minutes = window_days * 24 * 60
    deltas = []
    for record in existing.values():
        posted, seen = record.get("posted_at"), record.get("first_seen_at")
        if not posted or not seen:
            continue
        posted_dt, seen_dt = _parse_iso(posted), _parse_iso(seen)
        if not posted_dt or not seen_dt:
            continue
        minutes = (seen_dt - posted_dt).total_seconds() / 60
        if 0 <= minutes <= window_minutes:
            deltas.append(minutes)
    return {
        "median_minutes": round(statistics.median(deltas), 1) if deltas else None,
        "sample_size": len(deltas),
        "window_days": window_days,
    }


def _build_stats(companies, benched, succeeded, errors, errors_by_ats, kept, existing,
                 new_ids, enriched, detail_fetches, purged, duration,
                 dropped_no_year=0, dropped_offcycle_text=0) -> dict:
    open_records = [r for r in existing.values() if r.get("is_open")]
    attempted = len(companies) - len(benched)
    dated = sum(1 for r in open_records if r.get("posted_at"))
    return {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": duration,
        "companies_total": len(companies),
        "companies_by_source": dict(Counter(c["ats"] for c in companies)),
        "quarantined": len(benched),
        "fetched_ok": len(succeeded),
        "fetch_errors": errors,
        "errors_by_source": dict(errors_by_ats),
        "fetch_success_rate": round(len(succeeded) / max(attempted, 1), 3),
        "roles_matched": len(kept),
        "roles_cycle_inferred": sum(1 for j in kept if j.season_inferred),
        "dropped_no_year_in_title": dropped_no_year,
        "dropped_offcycle_by_text": dropped_offcycle_text,
        "roles_by_source": dict(Counter(j.source for j in kept)),
        "roles_by_cycle": dict(Counter(j.season for j in kept)),
        "roles_by_region": dict(Counter(
            "US" if filters.is_united_states(j.location) else "International" for j in kept
        )),
        "sponsorship_counts": dict(Counter(
            r.get("sponsorship", "unknown") for r in open_records
        )),
        "posted_date_coverage": round(dated / max(len(open_records), 1), 3),
        "enriched_this_run": enriched,
        "enrichment_detail_fetches": detail_fetches,
        "purged_this_run": purged,
        "new_this_run": len(new_ids),
        "open_total": len(open_records),
        "detection_latency": _detection_latency(existing),
        "posting_lifetime": dict(zip(
            ("median_days", "sample_size"), trends.median_days_open(existing),
            strict=True,
        )),
    }


def _write_stats(stats: dict) -> None:
    with open(paths.STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


_HISTORY_KEEP = 1000  # ~3 months of 2-hourly runs


def _append_history(stats: dict) -> None:
    """One compact line per run — the time series behind the dashboard chart."""
    line = json.dumps({
        "ts": stats["generated_at"],
        "open": stats["open_total"],
        "new": stats["new_this_run"],
        "companies": stats["companies_total"],
        "ok_rate": stats["fetch_success_rate"],
        "quarantined": stats["quarantined"],
        "secs": stats["duration_seconds"],
    }, ensure_ascii=False)
    lines = []
    try:
        with open(paths.HISTORY_PATH, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        pass
    lines.append(line)
    with open(paths.HISTORY_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines[-_HISTORY_KEEP:]) + "\n")
