"""Self-check: every open role must satisfy every accuracy invariant.

    python tools/verify_accuracy.py        # exit 0 = clean, 1 = violations

Checks each OPEN role in data/jobs.json against the rules the pipeline promises:
  1. season is a tracked cycle
  2. a title that states a tracked term+year agrees with the assigned season
  3. no title states an off-cycle year (those must be tombstoned, never listed)
  4. the location passes the US filter (config regions honored)
  5. it still reads as a tech internship (title-level filters)
  6. a real posted date exists and is inside max_age_days
  7. inferred (~) rows carry a posted date (that date is the inference's basis)
  8. the company isn't blocklisted
Plus cross-artifact consistency: the JSON API's open count matches the store.

Run it after any filter change or store surgery — it's the "did we break the
list" button.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from xml.etree import ElementTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from intern_engine import config, filters, paths, quality, registry, store  # noqa: E402

# Publish-gate thresholds. Set well below today's healthy numbers so normal
# variation never blocks a run — these catch decay and collapse, not a bad
# afternoon.
_MIN_REGISTRY_RATE = 0.80

# A "partial" snapshot is two very different things, and gating on the sum of
# them cost four production runs on 2026-08-07.
#
# `result-cap` is the DESIGNED outcome: a board with more intern hits than our
# per-search page budget. The engine handles it correctly — a capped board is
# simply not allowed to close roles — and it tells us nothing about health. Once
# the Oracle and Workday pagination bugs were fixed on 2026-08-06, honest
# cap-reporting moved the complete rate from an over-reported 96.7% to a true
# ~86%, and the old 85% floor started tripping on ordinary runs. Fixing the
# measurement is not a regression, so the gate had to stop treating it as one.
#
# `malformed-response` and `pagination-stalled` are the real signals: an ATS
# changed shape or stopped paginating. They get their own, much tighter ceiling,
# which is what "did the fetch layer break" actually means.
_MIN_COMPLETE_SNAPSHOT_RATE = 0.70   # a genuine collapse; today's runs sit ~86%
_MAX_DEGRADED_FETCH_RATE = 0.05      # today's runs sit ~1.2%
_REQUIRED_STATS = {
    "generated_at": str,
    "fetched_at": str,
    "rendered_at": str,
    "companies_total": int,
    "quarantined": int,
    "fetched_ok": int,
    "fetch_errors": int,
    "fetch_success_rate": (int, float),
    "fetch_success_rate_registry": (int, float),
    "snapshots_complete": int,
    "snapshots_partial": int,
    "partial_by_reason": dict,
    "degraded_fetches": int,
    "open_total": int,
    "roles_by_cycle": dict,
}


def main() -> None:
    cfg = config.load_config()
    cycles = config.cycles(cfg)
    blocklist = quality.load_blocklist()
    max_age = config.max_age_days(cfg)
    cutoff = (datetime.now(UTC) - timedelta(days=max_age)).strftime("%Y-%m-%d") if max_age else ""

    data = store.load(paths.JOBS_PATH)
    open_jobs = [r for r in data.values() if r.get("is_open")]
    problems: list[str] = []
    warnings: list[str] = []

    def _line(record: dict, rule: str) -> str:
        return (
            f"  [{rule}] {record.get('company', '?')[:28]} | "
            f"{(record.get('title') or '?')[:56]} | season={record.get('season')} "
            f"| loc={record.get('location')!r}"
        )

    def flag(record: dict, rule: str) -> None:
        problems.append(_line(record, rule))

    def warn(record: dict, rule: str) -> None:
        warnings.append(_line(record, rule))

    for r in open_jobs:
        title = r.get("title") or ""
        season = r.get("season")
        unstated = season == filters.NOT_STATED
        # NOT_STATED is a legitimate bucket, not a cycle: it means no employer
        # named one. Anything else must be a cycle we actually track.
        if season not in cycles and not unstated:
            flag(r, "untracked-season")
        seasons = r.get("seasons")
        if seasons is not None and (
            not isinstance(seasons, list)
            or season not in seasons
            or len(seasons) != len(set(seasons))
        ):
            flag(r, "season-list-incoherent")
        stated = filters.detect_season(title, cycles)
        if stated is not None and stated != season and stated not in (
                r.get("seasons") or []):
            flag(r, "title-season-mismatch")
        if stated is None and filters.states_explicit_year(title):
            flag(r, "off-cycle-year-in-title")
        # The two halves of the evidence contract, checked both ways. These
        # are what stop a fabricated cycle from ever reaching the list again:
        #   - a role in a CYCLE section must not be flagged as unstated
        #   - a role marked stated must actually carry a cycle, not NOT_STATED
        if unstated and not r.get("season_inferred"):
            flag(r, "unstated-but-marked-employer-stated")
        if not unstated and r.get("season_inferred"):
            flag(r, "cycle-claimed-without-employer-evidence")
        # A title that names its cycle can never be filed as unstated.
        if unstated and stated is not None:
            flag(r, "unstated-despite-cycle-in-title")
        if config.restrict_region(cfg) and not config.include_international(cfg) and \
                not filters.region_ok(r.get("location") or "",
                                      config.wanted_regions(cfg)):
            flag(r, "out-of-region")
        if not filters.is_internship(title):
            flag(r, "not-an-internship-title")
        if cfg.get("role_scope", "tech") == "tech" and not filters.is_tech(title):
            flag(r, "not-a-tech-title")
        posted = (r.get("posted_at") or "")[:10]
        # Age only disqualifies a role whose cycle we INFERRED, where recency
        # was the evidence. When the employer stated the cycle, an old posting
        # is just an early one — Amazon's "Fall 2026 (US)" internship opened
        # long before the cycle and is still both open and still Fall 2026.
        if cutoff and posted and posted < cutoff and r.get("season_inferred"):
            flag(r, "older-than-max-age")
        if not posted:
            # A warning, not a violation: some boards genuinely publish no
            # date, and one undated-but-real role must not block every publish.
            # (The published copy quotes date COVERAGE per run, not "every
            # role", precisely so this case can exist honestly.)
            warn(r, "missing-posted-date")
        if r.get("season_inferred") and not posted:
            flag(r, "inferred-without-posted-date")
        if quality.is_blocked(r.get("company") or "", blocklist):
            flag(r, "blocklisted-company")

    canonical: dict[tuple[str, str], list[dict]] = {}
    for record in open_jobs:
        value = record.get("canonical_id")
        if value:
            canonical.setdefault((record.get("source") or "", str(value)), []).append(record)
    for records in canonical.values():
        if len(records) > 1:
            for record in records:
                flag(record, "duplicate-canonical-id")

    api_path = os.path.join(paths.API_DIR, "jobs.json")
    try:
        with open(api_path, encoding="utf-8") as f:
            api = json.load(f)
        api_jobs = api.get("jobs")
        if not isinstance(api_jobs, list):
            raise ValueError("jobs must be a list")
        store_ids = {r["id"] for r in open_jobs}
        api_ids = {r.get("id") for r in api_jobs if isinstance(r, dict)}
        if api.get("count") != len(open_jobs) or api_ids != store_ids:
            problems.append(
                f"  [api-identity-drift] api has {len(api_ids)} ids/count={api.get('count')}, "
                f"store has {len(store_ids)} open ids (regenerate outputs)"
            )
    except (OSError, ValueError):
        problems.append("  [api-missing] docs/api/jobs.json unreadable")

    try:
        with open(paths.CSV_PATH, newline="", encoding="utf-8") as f:
            csv_rows = list(csv.DictReader(f))
        csv_ids = [row.get("id") for row in csv_rows]
        store_ids = {r["id"] for r in open_jobs}
        if len(csv_ids) != len(set(csv_ids)) or set(csv_ids) != store_ids:
            problems.append("  [csv-identity-drift] data/internships.csv differs from store")
    except (OSError, csv.Error):
        problems.append("  [csv-missing] data/internships.csv unreadable")

    docs_csv = os.path.join(paths.DOCS_DIR, "internships.csv")
    try:
        with open(paths.CSV_PATH, "rb") as left, open(docs_csv, "rb") as right:
            if left.read() != right.read():
                problems.append("  [csv-copy-drift] data and Pages CSV exports differ")
    except OSError:
        problems.append("  [csv-copy-missing] Pages CSV export is unreadable")

    for artifact in (paths.FEED_PATH,):
        try:
            ElementTree.parse(artifact)
        except (OSError, ElementTree.ParseError):
            problems.append(f"  [xml-invalid] {artifact} is not well-formed XML")

    for name in ("index.html", "confirm.html", "unsubscribe.html"):
        artifact = os.path.join(paths.DOCS_DIR, name)
        if not os.path.isfile(artifact) or os.path.getsize(artifact) == 0:
            problems.append(f"  [pages-artifact-missing] docs/{name} is missing or empty")

    # --- publish gates -------------------------------------------------------
    # Correctness checks above catch a bad ROW. These catch a bad RUN: a
    # collapse in volume means something upstream broke (an ATS changed shape,
    # a filter got too strict), and publishing it would quietly delete most of
    # the public list. Better to fail loudly and keep yesterday's good build.
    gates: list[str] = []
    floor = int(os.environ.get("MIN_OPEN_ROLES") or 0)
    if floor and len(open_jobs) < floor:
        gates.append(
            f"  [volume-floor] only {len(open_jobs)} open roles, floor is {floor}"
        )
    cycle_floor = int(os.environ.get("MIN_TRACKED_CYCLE_ROLES") or 0)
    if cycle_floor:
        for cycle in cycles:
            count = sum(
                1 for record in open_jobs
                if cycle in (record.get("seasons") or [record.get("season")])
            )
            if count < cycle_floor:
                gates.append(
                    f"  [cycle-floor] only {count} roles for {cycle}, floor is {cycle_floor}"
                )
    try:
        with open(paths.STATS_PATH, encoding="utf-8") as f:
            stats = json.load(f)
        if not isinstance(stats, dict):
            raise ValueError("stats must be an object")
        for field, expected in _REQUIRED_STATS.items():
            value = stats.get(field)
            wrong = not isinstance(value, expected) or isinstance(value, bool)
            if wrong:
                gates.append(f"  [stats-schema] {field} is missing or has the wrong type")

        timestamps: dict[str, datetime] = {}
        for field in ("generated_at", "fetched_at", "rendered_at"):
            value = stats.get(field)
            if not isinstance(value, str):
                continue  # the required-schema gate above already reports it
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                gates.append(f"  [stats-schema] {field} is not a timestamp")
                continue
            if parsed.tzinfo is None:
                gates.append(f"  [stats-schema] {field} is not timezone-aware")
                continue
            timestamps[field] = parsed.astimezone(UTC)
        fetched_dt = timestamps.get("fetched_at")
        generated_dt = timestamps.get("generated_at")
        rendered_dt = timestamps.get("rendered_at")
        if fetched_dt is not None:
            age = datetime.now(UTC) - fetched_dt
            if age < -timedelta(minutes=5):
                gates.append("  [stats-future] fetch timestamp is in the future")
            allow_stale = (os.environ.get("ALLOW_STALE_STATS") or "").lower() in {
                "1", "true", "yes",
            }
            if not allow_stale:
                max_hours = int(os.environ.get("MAX_STATS_AGE_HOURS") or 12)
                if age > timedelta(hours=max_hours):
                    gates.append(
                        f"  [stats-stale] last fetch is {age.total_seconds() / 3600:.1f}h old "
                        f"(limit {max_hours}h)"
                    )
        if generated_dt is not None and fetched_dt is not None \
                and generated_dt != fetched_dt:
            gates.append("  [stats-timestamp] generated_at must equal fetched_at")
        if rendered_dt is not None and fetched_dt is not None \
                and rendered_dt < fetched_dt:
            gates.append("  [stats-timestamp] rendered_at predates fetched_at")
        if rendered_dt is not None and rendered_dt > datetime.now(UTC) + timedelta(minutes=5):
            gates.append("  [stats-future] render timestamp is in the future")

        rate = stats.get("fetch_success_rate")
        if isinstance(rate, (int, float)) and rate < 0.5:
            gates.append(f"  [fetch-collapse] only {rate:.0%} of boards responded")
        # Attempted-board rate alone hides slow rot: quarantined endpoints are
        # never attempted, so that number stays high while the registry decays
        # underneath it. Gate on the registry-wide figure too.
        reg = stats.get("fetch_success_rate_registry")
        if isinstance(reg, (int, float)) and reg < _MIN_REGISTRY_RATE:
            gates.append(
                f"  [registry-decay] only {reg:.1%} of the full registry returned "
                f"(floor {_MIN_REGISTRY_RATE:.0%}) — quarantined boards are growing"
            )
        # A run that read almost nothing completely is not a snapshot worth
        # publishing, even if the roles it did see look fine.
        complete = stats.get("snapshots_complete")
        partial = stats.get("snapshots_partial")
        partial_by_reason = stats.get("partial_by_reason")
        if isinstance(complete, int) and isinstance(partial, int):
            total = complete + partial
            if total and complete / total < _MIN_COMPLETE_SNAPSHOT_RATE:
                gates.append(
                    f"  [snapshot-quality] only {complete}/{total} sources returned a "
                    f"complete snapshot (floor {_MIN_COMPLETE_SNAPSHOT_RATE:.0%})"
                )
            # The health half of the same measurement: boards that answered with
            # something we could not parse or could not page through.
            degraded = stats.get("degraded_fetches")
            if total and isinstance(degraded, int) and not isinstance(degraded, bool) \
                    and degraded / total > _MAX_DEGRADED_FETCH_RATE:
                gates.append(
                    f"  [fetch-degraded] {degraded}/{total} sources returned a "
                    f"malformed or non-paginating response "
                    f"(ceiling {_MAX_DEGRADED_FETCH_RATE:.0%}) — an ATS likely "
                    f"changed shape"
                )
            if isinstance(partial_by_reason, dict) and (
                any(
                    not isinstance(reason, str)
                    or isinstance(count, bool)
                    or not isinstance(count, int)
                    or count < 0
                    for reason, count in partial_by_reason.items()
                )
                or sum(partial_by_reason.values()) != partial
            ):
                gates.append("  [stats-arithmetic] partial reasons do not sum to snapshots_partial")
            if isinstance(partial_by_reason, dict):
                expected_degraded = sum(
                    partial_by_reason.get(reason, 0)
                    for reason in ("malformed-response", "pagination-stalled")
                    if isinstance(partial_by_reason.get(reason, 0), int)
                    and not isinstance(partial_by_reason.get(reason, 0), bool)
                )
                if stats.get("degraded_fetches") != expected_degraded:
                    gates.append(
                        "  [stats-arithmetic] degraded_fetches is inconsistent"
                    )
        companies_total = stats.get("companies_total")
        fetched_ok = stats.get("fetched_ok")
        fetch_errors = stats.get("fetch_errors")
        quarantined = stats.get("quarantined")
        if all(isinstance(v, int) and not isinstance(v, bool) for v in (
            companies_total, fetched_ok, fetch_errors, quarantined, complete, partial
        )):
            if fetched_ok + fetch_errors + quarantined != companies_total:
                gates.append("  [stats-arithmetic] board outcomes do not sum to registry total")
            if complete + partial != fetched_ok:
                gates.append("  [stats-arithmetic] snapshot outcomes do not sum to fetched_ok")
            attempted = companies_total - quarantined
            expected_attempted_rate = round(fetched_ok / max(attempted, 1), 3)
            expected_registry_rate = round(fetched_ok / max(companies_total, 1), 3)
            if stats.get("fetch_success_rate") != expected_attempted_rate:
                gates.append("  [stats-arithmetic] fetch_success_rate is inconsistent")
            if stats.get("fetch_success_rate_registry") != expected_registry_rate:
                gates.append("  [stats-arithmetic] registry success rate is inconsistent")
            registry_total = len(registry.load())
            if companies_total != registry_total:
                gates.append(
                    f"  [registry-drift] stats describe {companies_total} boards, "
                    f"registry has {registry_total}"
                )
        if stats.get("open_total") != len(open_jobs):
            gates.append("  [stats-store-drift] open_total differs from the job store")
        expected_cycles: dict[str, int] = {}
        for record in open_jobs:
            for label in record.get("seasons") or [record.get("season")]:
                if label:
                    expected_cycles[label] = expected_cycles.get(label, 0) + 1
        if stats.get("roles_by_cycle") != expected_cycles:
            gates.append("  [stats-store-drift] roles_by_cycle differs from the job store")
        try:
            with open(os.path.join(paths.API_DIR, "stats.json"), encoding="utf-8") as f:
                api_stats = json.load(f)
            if api_stats != stats:
                gates.append("  [stats-copy-drift] Pages stats differ from data/stats.json")
        except (OSError, ValueError):
            gates.append("  [stats-copy-missing] Pages stats export is unreadable")
    except (OSError, ValueError, registry.RegistryCorrupt):
        gates.append("  [stats-missing] data/stats.json unreadable")

    n_inferred = sum(1 for r in open_jobs if r.get("season_inferred"))
    by_cycle = {c: sum(1 for r in open_jobs if r.get("season") == c) for c in cycles}
    print(f"Checked {len(open_jobs)} open roles "
          f"({', '.join(f'{c}: {n}' for c, n in by_cycle.items())}; "
          f"{n_inferred} cycle-inferred, {len(open_jobs) - n_inferred} employer-stated).")
    if warnings:
        print(f"\n{len(warnings)} warning(s) (non-blocking):")
        print("\n".join(warnings))
    if problems or gates:
        if problems:
            print(f"\n{len(problems)} violation(s):")
            print("\n".join(problems))
        if gates:
            print(f"\n{len(gates)} publish gate(s) tripped:")
            print("\n".join(gates))
        sys.exit(1)
    print("All accuracy invariants hold.")


if __name__ == "__main__":
    main()
