"""Persistent job state, stored as a single human-diffable JSON file.

Why JSON and not SQLite for this repo: the file is committed back to the repo by
GitHub Actions each run, so a text file gives clean diffs ("3 jobs added") and
zero binary/database-persistence headaches. The store is a dict keyed by job id.

Two jobs of work happen here:
  - first-seen tracking: the moment WE first saw a job (powers "🆕" + sorting)
  - open/closed tracking: a job not seen in a successful fetch is marked closed
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        # sort_keys keeps the file order stable so git diffs stay small.
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


# Fields we refresh on every run for jobs we've seen before.
# NOTE: posted_at is deliberately NOT here — we freeze the published date the
# first time we see a role so the "Posted" column never shifts on later runs
# (the report behaves like a ladder: old roles sink, new ones land on top).
_REFRESH_FIELDS = (
    "title", "location", "url",
    "season", "category", "sponsorship", "company", "source", "company_slug",
)


def upsert(existing: dict, jobs: list[dict], succeeded_keys: set[str]) -> list[str]:
    """Merge freshly-fetched jobs into the existing store.

    Returns the list of NEWLY-seen job ids (this is the "Spotter" result).

    `succeeded_keys` is the set of "<source>:<slug>" we fetched successfully this
    run. We only mark a job closed if its company was fetched successfully but
    the job wasn't in the results — so a network blip never wrongly closes jobs.
    """
    ts = now_iso()
    seen_ids: set[str] = set()
    new_ids: list[str] = []

    for job in jobs:
        jid = job["id"]
        seen_ids.add(jid)
        if jid in existing:
            record = existing[jid]
            for key in _REFRESH_FIELDS:
                if key in job:
                    record[key] = job[key]
            record["last_seen_at"] = ts
            record["is_open"] = True
        else:
            record = dict(job)
            record["first_seen_at"] = ts
            record["last_seen_at"] = ts
            record["is_open"] = True
            existing[jid] = record
            new_ids.append(jid)

    # Close jobs that belong to a successfully-fetched company but didn't appear.
    for jid, record in existing.items():
        company_key = f"{record.get('source')}:{record.get('company_slug')}"
        if company_key in succeeded_keys and jid not in seen_ids:
            record["is_open"] = False

    return new_ids
