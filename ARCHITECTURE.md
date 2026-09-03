# Architecture

[![CI](https://github.com/zshah101/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/actions/workflows/ci.yml/badge.svg)](https://github.com/zshah101/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11-blue)
![async](https://img.shields.io/badge/I%2FO-async%20httpx-success)

A dependency-light Python engine that reads public ATS job feeds directly,
keeps only the internships in scope (configurable cycle / region / role scope),
classifies visa sponsorship from real posting text, tracks every role's
lifecycle over time, and regenerates the public `README.md`, a CSV, an Atom
feed, a JSON API, and a live dashboard. GitHub Actions runs it on a schedule
and commits the refreshed output.

## Data flow

```
public datasets + README mines          data/candidates.json (curated slugs)
        │  python run.py discover               │  python run.py harvest
        ▼                                       ▼
   discover.py ──ATS tokens──►  data/companies.json  ◄──probe & merge── harvester.py
                                        │
                                        │  python run.py update
                                        ▼
    health.py ──skips quarantined──►  pipeline.py ──concurrent fetch──►  connectors/*.py
    (circuit breaker,                   │                                (12 sources, each
     data/health.json)                  │  keep: internship? scope?       returning a Fetch:
                                        │        target cycle? region?    Job[] + complete?)
                                        ▼
                                    enrich.py ──posting text──► sponsorship.py
                                        │       (detail fetch only        (citizens-only /
                                        │        for NEW matched roles)    no-sponsorship /
                                        ▼                                  offers / unknown)
                                     store.py ──► data/jobs.json
                                        │         (dedup · first-seen · open/closed
                                        │          · closed_reason · retention purge)
        ┌───────────────┬───────────────┼────────────────┬──────────────┐
        ▼               ▼               ▼                ▼              ▼
    readme.py      dashboard.py     publish.py       db.py         outbox.py
    README.md +    docs/index.html  docs/feed.xml    Postgres       data/outbox.json
    internships.csv (search/filter/ + docs/api/*.json (optional)     (roles awaiting
                    sparkline)      (RSS + JSON API)                  an alert)
                                        │
                                 git commit && push   ← the publish boundary
                                        │
                                        ▼  python run.py notify
                                notify.py + mailer.py
                                Discord      email digest
```

### Why alerts are a separate command

An alert says "this role is on the list", so it may only go out once the run's
data is actually published. `update` therefore queues new roles in
`data/outbox.json`; the workflow commits and pushes; only then does `notify`
drain the queue and send. A failed push leaves the queue full, so those roles
go out with the next successful publish — exactly once.

### Evidence, not just data

Three fields exist purely so the output can say how much it actually knows.
They're what separate this from a list that asserts everything with equal
confidence:

| Field | Question it answers |
|---|---|
| `season_inferred` | Did the **employer** name this cycle, or did we infer it from the posting date? Inferred roles render in their own README section and are excluded from the "stated cycle" count. |
| `posted_at_source` | `exact` / `date_only` / `relative_derived`. Drives which dates may supersede which, and which are eligible for the latency metric. |
| `closed_reason` | `gone-from-feed` (evidence from a complete snapshot) vs `out-of-scope` (our own verdict). |

Plus `classifier_v`: a stored sponsorship verdict is only trusted while the
classifier that produced it is current. Bump `sponsorship.VERSION` and every
stale record is re-read from posting text on the next run, so a rule fix reaches
the whole live list instead of only roles found afterwards.

`seasons` holds every cycle a title states, for the postings that name two.

### Two reasons a role leaves the list

`store.upsert` distinguishes them, because they need different evidence:

| `closed_reason` | Meaning | Evidence required |
|---|---|---|
| `gone-from-feed` | **Two consecutive** complete reads no longer return it | `Fetch.complete` true on both runs; one miss only arms the closure |
| `out-of-scope` | It's still posted, but fails our filters (wrong country, off-cycle, not tech) | none — our own verdict |

Several ATS cap search results (Workday/Oracle at 200 per term, Amazon at
1,000, SmartRecruiters/Eightfold at 300). A capped page looks exactly like "no
more roles", so connectors report `complete=False` when they may have been cut
off, and a partial snapshot is never allowed to close anything. Roughly 90 of
~3,450 boards hit a cap on a typical run.

## Files

| File | Responsibility |
|---|---|
| `run.py` | CLI entrypoint: `harvest` \| `discover` \| `update` \| `render` \| `notify` \| `all`. Puts `src/` on the path. |
| `src/intern_engine/models.py` | The `Job` dataclass, and `Fetch` (a connector's jobs + whether its snapshot was complete). |
| `src/intern_engine/paths.py` | All file paths, computed from the repo root (CI-safe). |
| `src/intern_engine/config.py` | Loads `data/config.json`; derives the repo/Pages URLs. |
| `src/intern_engine/net.py` | Async HTTP with retry/backoff + per-host concurrency limits. |
| `src/intern_engine/connectors/` | One module per ATS: Greenhouse, Lever, Ashby, SmartRecruiters, Workday, Oracle, Amazon, Rippling, Workable, Breezy, Recruitee, Eightfold. |
| `src/intern_engine/filters.py` | Classification: internship? tech? season/year? US/Canada? category. |
| `src/intern_engine/sponsorship.py` | Phrase-anchored visa/citizenship classifier + display flags. |
| `src/intern_engine/h1b.py` | Joins companies against the USCIS H-1B employer index (✓ badge). Rendered only when `regions` includes the US. |
| `src/intern_engine/enrich.py` | Fetches posting text for new matched roles; backfills exact dates. |
| `src/intern_engine/trends.py` | Weekly posting-volume chart + median posting-lifetime metric. |
| `src/intern_engine/radar.py` | Drop Radar: last cycle's first-post dates projected onto this cycle. |
| `src/intern_engine/mailer.py` | Daily email digests to our own subscriber list (Brevo, opt-in). |
| `src/intern_engine/health.py` | Circuit breaker: quarantines repeatedly-failing boards, self-heals. |
| `src/intern_engine/harvester.py` | Probes candidate slugs across 7 ATS, merges hits into the registry. |
| `src/intern_engine/discover.py` | Mines public datasets/READMEs for ATS tokens at scale. |
| `src/intern_engine/quality.py` | Company quality gate: blocklist + optional allowlist-only mode. |
| `src/intern_engine/priority.py` | Company prestige ranking for capped sections. |
| `src/intern_engine/store.py` | Persistent JSON store: dedup, first-seen, open/closed, retention. |
| `src/intern_engine/pipeline.py` | Orchestrates fetch → filter → enrich → store; writes stats + history. |
| `src/intern_engine/grouping.py` | Display-only: folds an employer's repeated requisitions for one job into a single "N openings" entry. Never deletes a record — that's `pipeline._dedup`'s job. |
| `src/intern_engine/readme.py` | Renders `README.md` + `data/internships.csv`. |
| `src/intern_engine/dashboard.py` | Renders the self-contained GitHub Pages dashboard. |
| `src/intern_engine/publish.py` | Renders the Atom feed + static JSON API under `docs/`. |
| `src/intern_engine/notify.py` | Optional Discord webhook alerts for newly spotted roles. |
| `src/intern_engine/outbox.py` | Queue of roles awaiting an alert; drained only after a successful publish. |
| `src/intern_engine/observe.py` | The engine's own record of real posting dates, by company and cycle. |
| `src/intern_engine/names.py` | Employer display names: override map + slug-artifact cleanup. |
| `src/intern_engine/db.py` | Optional Postgres (Supabase) mirror of jobs/companies/runs. Runs in `notify`, after the accuracy gate and the push. |
| `.github/workflows/update.yml` | Scheduled CI (every 30 min): run update, commit, push, then send alerts. |
| `.github/workflows/discover.yml` | Daily CI: grow `data/companies.json` automatically. |
| `data/config.json` | Tunable settings (see below). |
| `data/companies.json` | Validated companies the pipeline reads. |
| `data/company_names.json` | Display-name overrides for slug-derived employer names. |
| `data/outbox.json` | Roles queued for an alert, drained only after a successful publish. |
| `db/schema.sql` | Supabase tables, RLS policies, and the unsubscribe RPC. |
| `data/jobs.json` | The persistent job state (source of truth for the README). |
| `data/health.json` | Circuit-breaker state (auditable in git like everything else). |
| `data/history.jsonl` | One line of run metrics per run (feeds the dashboard chart). |
| `data/h1b.json` | Compact USCIS employer→approvals index (built by `tools/build_h1b.py`). |
| `tools/build_h1b.py` | Offline builder: USCIS Data Hub CSVs → `data/h1b.json` (run yearly). |
| `tools/audit_seasons.py` | Audit date-inferred cycles against posting text; `--apply` repairs the store. |
| `tools/verify_accuracy.py` | Every open role vs every invariant, plus publish gates. Runs in CI before publishing. |

## Configuration (`data/config.json`)

```json
{
  "cycles": ["Summer 2027", "Fall 2026"],
  "regions": ["SEA"],
  "role_scope": "tech",
  "max_age_days": 270,
  "max_per_company": 3,
  "allowlist_only": false,
  "infer_undated": true,
  "infer_max_age_days": 45,
  "section_limits": { "Summer 2027": 300, "Fall 2026": 150 }
}
```

Sources: Greenhouse, Lever, Ashby, SmartRecruiters, Workday, Oracle Recruiting
Cloud, Amazon, Rippling, Workable, Breezy, and Recruitee. A company-level
quality gate (`data/blocklist.json` plus the optional `allowlist_only` mode)
keeps the list free of junk/no-name companies.

- `cycles` — the exact cycles to show; these become the section headings, in order.
  A year stated in the title always wins (e.g. "2027", "Fall 2026", "Summer '27"
  — but a graduation year like "Class of 2027" never counts). Titles with no
  year are bucketed from their posting date when posted within
  `infer_max_age_days` (marked `~` everywhere they render), then checked against
  the posting text at enrichment. The text reader understands both "<term>
  <year>" and month+year start dates ("start date July 2026" → Summer 2026),
  guarded three ways: the year must be plausible for a live posting, all counted
  mentions must agree, and graduation/company-history dates ("graduating in
  December 2027", "founded in November 2014") are excluded. A cycle the text
  states replaces the guess; an off-cycle statement closes the role AND records
  the verdict, so it can never be re-inferred back in. Once stored, a season is
  sticky — never re-derived on later runs. `tools/audit_seasons.py` re-audits
  the backlog on demand. Older undated roles and other cycles are dropped.
- `regions` — which countries to keep. A group token (`["SEA"]` = Singapore,
  Malaysia, Indonesia, Thailand, Vietnam, the Philippines), single countries
  (`["Singapore"]`, `["US", "Canada"]`), or `["Global"]` to disable the location
  filter. Tokens are mapped to region keys in `config._REGION_ALIASES` and
  matched in `filters.region_ok`; groups are defined in `filters.REGION_GROUPS`.
  Setting a non-US region also hides the US-visa surfaces (H-1B badge,
  🇺🇸 / 🛂 flags, Drop Radar), which have no meaning outside the US.
- `role_scope` — `"tech"` keeps only tech roles; `"all"` keeps every internship.
- `max_age_days` — drop postings published longer ago than this (kills stale/evergreen reqs).
- `max_per_company` — cap roles shown per company per section, for variety.
- `section_limits` — max rows per section; over the cap, the most sought-after companies win.

Run `python run.py discover` to mine public datasets for company tokens and grow
`data/companies.json` — we then poll those feeds directly. A daily workflow does
this automatically.

## Design choices

- **One normalized `Job`** decouples the whole system from any specific ATS —
  adding a source is a single new connector module + one line in
  `pipeline.CONNECTORS`.
- **JSON store, not a DB** — the state file is committed by CI each run, so a
  human-diffable text file beats a binary database here.
- **Fault isolation** — each company is fetched in its own task with its own
  `try/except`; one dead endpoint never breaks a run, and jobs are only marked
  "closed" for companies that fetched successfully.
- **Circuit breaker** — boards that fail 3+ runs in a row are quarantined with
  an exponential backoff window (6h → 72h cap) and retried automatically, so
  dead slugs from public datasets cost nothing and recoveries need no human.
- **Enrichment is O(new roles), not O(all jobs)** — posting text is fetched once
  per matched role, the verdict is stored, and it is never re-fetched.
- **Stable ids** (`<source>:<slug>:<external_id>`) make dedup automatic.
- **Frozen posted dates** — a role's published date is recorded once; blanks may
  be backfilled later (better data), but a real date never shifts.

## Sponsorship detection (the F-1 edge)

`sponsorship.py` classifies each posting's text into `citizens-only`
(citizenship / clearance / ITAR), `no-sponsorship`, `offers`, or `unknown`,
using phrase-anchored patterns of what employers actually write ("unable to
sponsor", "must be a U.S. citizen", ...). Precision is deliberately favored
over recall: EEO boilerplate that merely mentions "citizenship status" does not
trigger. The README shows 🇺🇸 / 🛂 flags; the CSV, API, feed, and dashboard
carry the raw value; the dashboard filter names each verdict separately
(explicitly offers / no explicit restriction / not stated / explicitly
restricted) rather than collapsing them into one "F-1 friendly" toggle, which
only hid the negatives and presented ~97% unknowns as if they'd been checked.

That covers what a posting *says*. `h1b.py` adds what the company has *done*:
`tools/build_h1b.py` aggregates the official USCIS H-1B Employer Data Hub
exports (per-employer approval counts) into a compact committed index, and at
render time each company is matched against it — normalized legal names
(suffix stripping, DBA handling), a small alias table, then word-boundary
prefix matching with ambiguity guards (entity resolution, precision-first: a
single-token name never sums unrelated employer families). A company with 10+
recent approvals gets a ✓ in every surface plus a "proven H-1B sponsors only"
dashboard filter. The index ships in the repo, so runs never depend on
uscis.gov being reachable (it blocks datacenter IPs anyway).

## Workday (enterprise tier) & the optional proxy

Workday is per-tenant (each company has its own host + `site`) and bot-protected.
Discovery extracts tenant/site pairs from public data — both URL shapes
(`{tenant}.wdN.myworkdayjobs.com` and `wdN.myworkdaysite.com/recruiting/…`) —
and the connector paginates past the API's 20-per-page cap. Failures are
isolated per company and repeated failures are quarantined by the breaker.

Workday blocks **datacenter/cloud IPs** more aggressively than home IPs, so the
GitHub Actions runner may be refused for some tenants. To recover them, set a repo
secret named **`WORKDAY_PROXY`** to a proxy URL (e.g. a cheap residential/rotating
proxy: `http://user:pass@host:port`). The workflow passes it through, and only the
Workday/Oracle connectors use it. Unset = they run direct (default).

## Data layer (optional Postgres / Supabase)

The JSON store is the always-available default. When `SUPABASE_URL` and
`SUPABASE_SERVICE_KEY` are set, each run also mirrors the data into Postgres via
`db.py` (best-effort - missing creds simply skip it): a normalized schema of
`companies`, `jobs` (with first/last-seen history + open/closed state), and a
`scrape_runs` metrics table, plus a `company_posting_stats` view (e.g. average
days a company's postings stay live). The README, CSV, feed, API, and dashboard
remain exported views, so the presentation layer is decoupled from the data layer.

## Alerts

- **RSS/Atom** (`docs/feed.xml`): ordered by when the engine first spotted each
  role — point any RSS reader, or a Slack/Discord RSS integration, at it and new
  roles arrive as notifications. Zero infrastructure.
- **Discord webhook** (optional): set the `DISCORD_WEBHOOK_URL` secret and each
  run posts its newly found roles to your channel.
- **Email digests** (our own list): the dashboard's signup form inserts straight
  into Supabase under row-level security — the public can subscribe but never
  read, enumerate, or modify the list. `mailer.py` sends at most one digest a
  day, only when something new appeared, via Brevo's transactional API
  (`BREVO_API_KEY` + `MAIL_FROM` secrets; unset = silent no-op). Every email
  carries a one-click unsubscribe link — a per-subscriber secret token handled
  by a security-definer RPC, so `docs/unsubscribe.html` needs only public keys.

## Drop Radar

Every list shows what's open; the radar shows **what's coming**. `observe.py`
records, per company and cycle, the earliest posting date the engine saw itself
along with the **distinct role ids** behind it (the count used to be bumped once
per role per run, which an hourly schedule inflated without limit). At render
time `radar.py` projects last cycle's observed date one year forward, checks it against the live store (has the
company posted this cycle in our feeds?), and renders a countdown table:
README shows the forecast plus recent drops, the dashboard has every row
searchable (currently ~54 — only companies we can say something real about), and
`docs/api/radar.json` serves the raw data. Honesty rules: dates inside the
reference dataset's backfill window render as "by <date>" (a latest bound, not
a drop day), and "waiting" means "not seen in our tracked feeds", never "not
posted anywhere".

## Trends

`trends.py` answers two timing questions from data the store already keeps:
weekly posting volume (from real published dates — the dashboard bar chart) and
the median days a posting stays open (from roles watched open → closed, shown
as a stat card once the sample is big enough to mean something).

## Running locally

```bash
python -m venv .venv
.\.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python run.py all               # discover + harvest + update
python -m pytest                # 266 tests, no network
python tools/verify_accuracy.py # every open role vs every invariant
```
