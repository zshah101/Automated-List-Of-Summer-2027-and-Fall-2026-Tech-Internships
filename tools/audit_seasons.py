"""Audit date-inferred cycles against each posting's own text.

For every OPEN role whose cycle was inferred from its posting date, fetch the
posting text (list payload where the ATS ships it, detail endpoint otherwise)
and compare with the cycle the text states, if any:

  CONFIRMED  text states the cycle we inferred      -> un-mark (it's stated now)
  MOVED      text states another tracked cycle      -> rebucket + un-mark
  OFF-CYCLE  text states a cycle we don't track     -> remove the record
  NO-SIGNAL  text states nothing explicit           -> keep the inference + ~

Read-only by default; --apply rewrites data/jobs.json. The engine performs this
same check for every NEW role at first enrichment (see enrich.py) and stored
seasons are sticky (see pipeline._keep_matching), so one audit pass brings the
backlog in line and it stays in line.

    python tools/audit_seasons.py           # report only
    python tools/audit_seasons.py --apply   # report + repair the store
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from intern_engine import config, enrich, filters, paths, sponsorship, store  # noqa: E402
from intern_engine.models import Job  # noqa: E402
from intern_engine.net import HostLimiter, Net  # noqa: E402
from intern_engine.pipeline import CONNECTORS, USER_AGENT  # noqa: E402


def _record_to_job(record: dict) -> Job:
    return Job(
        id=record["id"], source=record.get("source", ""),
        company=record.get("company", ""), company_slug=record.get("company_slug", ""),
        title=record.get("title", ""), location=record.get("location", ""),
        url=record.get("url", ""), posted_at=record.get("posted_at"),
    )


async def _texts_for(jobs: list[Job], companies: list[dict]) -> dict[str, str]:
    """job id -> posting text, via detail fetchers or the company list payload."""
    by_key = {(c["ats"], c["slug"]): c for c in companies}
    texts: dict[str, str] = {}
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(20.0, connect=10.0),
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        net = Net(client, HostLimiter(8))
        list_sourced: dict[tuple[str, str], list[Job]] = {}
        for job in jobs:
            fetcher = enrich._FETCHERS.get(job.source)  # noqa: SLF001 — same package's tool
            if fetcher is not None:
                try:
                    texts[job.id] = await fetcher(job, net) or ""
                except Exception as exc:  # noqa: BLE001 — audit one role, not none
                    print(f"  (fetch failed: {job.company} — {type(exc).__name__})")
            else:
                list_sourced.setdefault((job.source, job.company_slug), []).append(job)

        for key, wanted in list_sourced.items():
            company = by_key.get(key)
            if company is None:
                continue
            try:
                fetched = await CONNECTORS[key[0]](company, net)
            except Exception as exc:  # noqa: BLE001
                print(f"  (list fetch failed: {key[1]} — {type(exc).__name__})")
                continue
            descriptions = {j.id: j.description or "" for j in fetched}
            for job in wanted:
                texts[job.id] = descriptions.get(job.id, "")
    return texts


def main() -> None:
    apply_fixes = "--apply" in sys.argv
    cfg = config.load_config()
    cycles = config.cycles(cfg)

    data = store.load(paths.JOBS_PATH)
    inferred = [r for r in data.values() if r.get("is_open") and r.get("season_inferred")]
    with open(paths.COMPANIES_PATH, encoding="utf-8") as f:
        companies = json.load(f)
    print(f"Auditing {len(inferred)} open inferred roles against posting text…")

    jobs = [_record_to_job(r) for r in inferred]
    texts = asyncio.run(_texts_for(jobs, companies))

    verdicts: dict[str, list] = {"CONFIRMED": [], "MOVED": [], "OFF-CYCLE": [], "NO-SIGNAL": []}
    for record in inferred:
        text = sponsorship.strip_html(texts.get(record["id"], ""))
        stated = filters.season_from_text(text)
        if stated is None:
            verdicts["NO-SIGNAL"].append((record, None))
        elif stated == record.get("season"):
            verdicts["CONFIRMED"].append((record, stated))
        elif stated in cycles:
            verdicts["MOVED"].append((record, stated))
        else:
            verdicts["OFF-CYCLE"].append((record, stated))

    for verdict, rows in verdicts.items():
        print(f"\n{verdict} ({len(rows)})")
        for record, stated in rows:
            was = record.get("season")
            note = f"{was} -> {stated}" if stated and stated != was else (stated or was)
            print(f"  {record.get('company','')[:26]:<26} | {note:<26} | "
                  f"{record.get('title','')[:56]}")

    if not apply_fixes:
        print("\nDry run — pass --apply to repair the store.")
        return

    for record, _stated in verdicts["CONFIRMED"]:
        data[record["id"]]["season_inferred"] = False
    for record, stated in verdicts["MOVED"]:
        data[record["id"]]["season"] = stated
        data[record["id"]]["season_inferred"] = False
    for record, _stated in verdicts["OFF-CYCLE"]:
        del data[record["id"]]
    store.save(paths.JOBS_PATH, data)
    print(f"\nApplied: {len(verdicts['CONFIRMED'])} confirmed, "
          f"{len(verdicts['MOVED'])} moved, {len(verdicts['OFF-CYCLE'])} removed. "
          f"Store saved.")


if __name__ == "__main__":
    main()
