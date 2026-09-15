"""Command-line entrypoint.

    python run.py harvest    # probe curated candidates -> data/companies.json
    python run.py discover   # mine public datasets for company tokens (big scale-up)
    python run.py update     # fetch -> filter -> enrich -> store -> publish everything
    python run.py render     # rebuild published artifacts from the store (no fetch)
    python run.py notify     # announce what `update` queued (run AFTER the push)
    python run.py mailcheck  # fail the run if the email digest has stalled
    python run.py all        # discover + harvest + update

`update` and `notify` are separate on purpose. Alerts promise a role is on the
list, so they may only go out once the run's data is actually published — see
intern_engine/outbox.py.
"""

import os
import sys
from datetime import UTC, datetime

# Make the package under src/ importable without installation.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from intern_engine import (  # noqa: E402
    dashboard,
    db,
    discover,
    harvester,
    mailer,
    notify,
    outbox,
    paths,
    pipeline,
    publish,
    readme,
    store,
    telegram,
    trends,
)


def cmd_harvest() -> None:
    found, candidates = harvester.harvest()
    print(f"Harvested {len(found)}/{len(candidates)} candidates -> data/companies.json")
    by_ats: dict[str, int] = {}
    for c in found:
        by_ats[c["ats"]] = by_ats.get(c["ats"], 0) + 1
    for ats, n in sorted(by_ats.items()):
        print(f"  {ats:<12} {n}")


def cmd_discover() -> None:
    companies, n_found = discover.discover()
    print(f"Discovered {n_found} tokens from public datasets.")
    print(f"Company list now has {len(companies)} companies -> data/companies.json")
    by_ats: dict[str, int] = {}
    for c in companies:
        by_ats[c["ats"]] = by_ats.get(c["ats"], 0) + 1
    for ats, n in sorted(by_ats.items()):
        print(f"  {ats:<12} {n}")


def _render(store_data: dict, stats: dict):
    """Regenerate every published artifact from the store. Returns (readme
    summary, feed entry count, calendar event count)."""
    data_as_of = stats.get("fetched_at") or stats.get("generated_at")
    try:
        data_as_of_dt = datetime.fromisoformat(data_as_of.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise pipeline.StatsCorrupt("cannot render without a valid fetch timestamp") from exc
    stats["rendered_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    trends.write_readme_charts(store_data, now=data_as_of_dt)
    summary = readme.generate(store_data, data_as_of=data_as_of)
    dashboard.generate(store_data, stats)
    feed_entries = publish.write_feed(store_data, data_as_of=data_as_of)
    publish.write_api(store_data, stats)
    ics_events = publish.write_radar_ics(store_data, data_as_of=data_as_of)
    pipeline.write_stats(stats)
    return summary, feed_entries, ics_events


def cmd_render() -> None:
    """Rebuild the published artifacts from the store, without fetching.

    Used by the weekly season audit, which rewrites cycles in the store: the
    README/CSV/API/dashboard are stale the moment it does, and committing only
    the store left the public pages disagreeing with the data.
    """
    store_data = store.load(paths.JOBS_PATH)
    stats = pipeline.load_stats()
    # The store just changed, so the fetch-time counts in stats.json describe a
    # different dataset. Recompute the ones derived from the store; leave the
    # fetch metrics (which only a real run can produce) as the last run's.
    stats = pipeline.restat(store_data, stats)
    summary, feed_entries, ics_events = _render(store_data, stats)
    print("Rendered from the existing store:")
    print(f"  README open roles      {summary['open']}")
    print(f"  feed entries           {feed_entries}")
    print(f"  radar calendar events  {ics_events}")


def cmd_update() -> None:
    # paths.COMPANIES_PATH is absolute; checking a CWD-relative path here made
    # `run.py` work only from the repo root, contradicting what paths.py promises.
    if not os.path.exists(paths.COMPANIES_PATH):
        print("No data/companies.json yet — run `python run.py harvest` first.")
        sys.exit(1)
    stats, store_data, new_ids = pipeline.run_update()
    summary, feed_entries, ics_events = _render(store_data, stats)
    # NOTE: no db.sync here. The Postgres mirror updates in `notify`, which the
    # workflow runs only after the accuracy gate passed and the push landed —
    # otherwise a run the gate would reject could still reach the mirror.
    # Queue, don't send: these roles aren't published until the workflow's
    # commit lands, and an alert for an unpublished role is a broken promise.
    pending = outbox.queue(new_ids)
    print("Update complete:")
    for k, v in stats.items():
        print(f"  {k:<24} {v}")
    print(f"  README open roles      {summary['open']}")
    print(f"  feed entries           {feed_entries}")
    print(f"  radar calendar events  {ics_events}")
    print(f"  queued for alerts      {len(pending)}")


def cmd_notify() -> None:
    """Announce what's been published. Run only after a successful push.

    The two channels are independent. Discord announces the outbox (this run's
    newly-found roles); the daily email digest is driven by the store's own
    news window and its per-role sent list, so it must be attempted even when
    the outbox is empty — an empty outbox means "no new roles since the last
    run", not "no digest is due".
    """
    store_data = store.load(paths.JOBS_PATH)

    # Each channel drains its OWN queue: a Telegram timeout must not strand a
    # role Discord already announced, and vice versa.
    for channel, send, label in (
        ("discord", notify.send_new_roles, "Discord alert"),
        ("telegram", telegram.send_new_roles, "Telegram push"),
    ):
        pending = outbox.load(channel)
        if not pending:
            print(f"  {label:20} nothing queued")
            continue
        # Only what actually went out (or can never go out) leaves the queue;
        # anything held back is announced on the next run instead of lost.
        done = send(store_data, pending)
        still = outbox.drain(done, channel)
        print(f"  {label:20} {len(done)} handled, {len(still)} still queued")

    sent = mailer.send_digest(store_data)
    print(f"  email digest         {f'sent to {sent} subscribers' if sent else 'not due'}")

    # "not due" and "the database has been unreachable for three weeks" printed
    # identically until now, which is how a 24-day outage went unnoticed. Say
    # which one it is, every run.
    state = mailer.load_state()
    waiting = len(mailer.pending_roles(store_data, state))
    ok, reason = mailer.health(state, waiting)
    print(f"  email health         {'ok' if ok else 'FAILING'} - {reason}")
    if not ok:
        # Picked up as an annotation on the Actions run; `run.py mailcheck`
        # turns the same verdict into a red run, which is what actually
        # reaches a human by email.
        print(f"::error title=Email digest is not going out::{reason}")

    # The mirror syncs here — after the gate and the push — so data the gate
    # would have rejected can never reach it.
    stats = pipeline.load_stats()
    if db.sync(store_data, stats):
        print("  Postgres mirror      synced")


def cmd_mailcheck() -> None:
    """Fail the run when the digest is not reaching people.

    Deliberately a separate command from `notify`: it runs after the alert
    state has been committed, so turning the job red to raise a human never
    costs the delivery ledger it was complaining about.
    """
    store_data = store.load(paths.JOBS_PATH)
    state = mailer.load_state()
    waiting = len(mailer.pending_roles(store_data, state))
    ok, reason = mailer.health(state, waiting)
    if ok:
        print(f"Email digest healthy - {reason}")
        return
    print(f"::error title=Email digest is not going out::{reason}")
    print(f"Email digest FAILING - {reason}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "update"
    if cmd == "harvest":
        cmd_harvest()
    elif cmd == "discover":
        cmd_discover()
    elif cmd == "update":
        cmd_update()
    elif cmd == "render":
        cmd_render()
    elif cmd == "notify":
        cmd_notify()
    elif cmd == "mailcheck":
        cmd_mailcheck()
    elif cmd == "all":
        cmd_discover()
        cmd_harvest()
        cmd_update()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
