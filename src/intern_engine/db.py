"""Optional Postgres (Supabase) sink for jobs, companies, and run metrics.

Best-effort by design: if SUPABASE_URL / SUPABASE_SERVICE_KEY aren't set (or the
client can't be built), every function no-ops and the engine runs exactly as
before. When configured, each run mirrors the data into Postgres - the source of
truth + analytics layer - while the README/CSV/dashboard remain exported views.
"""

from __future__ import annotations

import os

from . import config, filters, registry


def _client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
    except ImportError:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


def enabled() -> bool:
    return _client() is not None


def _company_rows(store_data: dict) -> list[dict]:
    """Registry rows plus historical employers still referenced by the store."""
    rows: dict[str, dict] = {}
    for company in registry.load():
        key = registry.board_key(company)
        rows[key] = {
            "key": key,
            "ats": company["ats"],
            "slug": company["slug"],
            "name": company["name"],
        }
    # Closed history can outlive a registry entry. Include those company keys
    # so a clean database can satisfy jobs.company_key's foreign key too.
    for record in store_data.values():
        source = record.get("source")
        slug = record.get("company_slug")
        if not source or not slug:
            continue
        key = record.get("board_key") or f"{source}:{slug}"
        rows.setdefault(key, {
            "key": key,
            "ats": source,
            "slug": slug,
            "name": record.get("company"),
        })
    return list(rows.values())


def _job_rows(store_data: dict) -> list[dict]:
    regions = config.wanted_regions(config.load_config())
    rows = []
    for r in store_data.values():
        location = r.get("location") or ""
        rows.append({
            "id": r["id"],
            "company_key": r.get("board_key") or (
                f"{r.get('source')}:{r.get('company_slug')}"
            ),
            "source": r.get("source"),
            "company": r.get("company"),
            "title": r.get("title"),
            "location": location,
            "url": r.get("url"),
            "category": r.get("category"),
            "season": r.get("season"),
            "seasons": r.get("seasons") or None,
            # The evidence columns. Without these the mirror can't tell a
            # stated cycle from a guess, or a real date from a derived one —
            # which is most of what makes this dataset worth querying.
            "season_inferred": bool(r.get("season_inferred")),
            "region": filters.region_of(location, regions),
            "sponsorship": r.get("sponsorship", "unknown"),
            "salary": r.get("salary"),
            "skills": r.get("skills") or None,
            "posted_at": r.get("posted_at"),
            "posted_at_source": r.get("posted_at_source"),
            "first_seen_at": r.get("first_seen_at"),
            "last_seen_at": r.get("last_seen_at"),
            "closed_at": r.get("closed_at"),
            "closed_reason": r.get("closed_reason"),
            "canonical_id": r.get("canonical_id"),
            "requisition_id": r.get("requisition_id"),
            "aliases": r.get("aliases") or None,
            "is_open": bool(r.get("is_open")),
        })
    return rows


def _run_row(stats: dict) -> dict:
    keep = (
        "duration_seconds", "companies_total", "fetched_ok", "fetch_errors",
        "fetch_success_rate", "roles_matched", "new_this_run", "open_total",
        "roles_by_source", "roles_by_cycle", "roles_by_region", "detection_latency",
        "fetched_at", "snapshots_complete", "snapshots_partial", "degraded_fetches",
    )
    return {k: stats.get(k) for k in keep}


def sync(store_data: dict, stats: dict) -> bool:
    """Mirror companies + all jobs + this run's metrics into Postgres."""
    client = _client()
    if client is None:
        return False
    try:
        # A Postgres function call is one transaction. Sending the complete
        # payload to the RPC means an exception while parsing/upserting any row
        # rolls back companies, jobs, and the run metric together. In
        # particular, no production-table batch is mutated before a later
        # "finalize" step that might never run.
        client.rpc(
            "replace_mirror_snapshot",
            {
                "p_companies": _company_rows(store_data),
                "p_jobs": _job_rows(store_data),
                "p_run": _run_row(stats),
            },
        ).execute()
        return True
    except Exception as exc:  # noqa: BLE001 - DB is a mirror; never break the run
        # Loud on purpose. The usual cause is a schema older than the writer
        # A missing RPC usually means db/schema.sql has not been deployed yet.
        print(f"  (Postgres sync FAILED: {type(exc).__name__}: {exc})")
        print(
            "   If this mentions a missing function or unknown column, re-run "
            "db/schema.sql; it migrates existing installations."
        )
        return False
