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
    (circuit breaker,                   │                                (11 sources, one
     data/health.json)                  │  keep: internship? scope?       normalized Job[])
                                        │        target cycle? region?
                                        ▼
                                    enrich.py ──posting text──► sponsorship.py
                                        │       (detail fetch only        (citizens-only /
                                        │        for NEW matched roles)    no-sponsorship /
                                        ▼                                  offers / unknown)
                                     store.py ──► data/jobs.json
                                        │         (dedup · first-seen · open/closed
                                        │          · closed_at · retention purge)
        ┌───────────────┬───────────────┼────────────────┬──────────────┐
        ▼               ▼               ▼                ▼              ▼
    readme.py      dashboard.py     publish.py       notify.py       db.py
    README.md +    docs/index.html  docs/feed.xml    Discord         Postgres
    internships.csv (search/filter/ + docs/api/*.json webhook        (optional)
                    sparkline)      (RSS + JSON API)  (optional)
```

## Files

| File | Responsibility |
|---|---|
| `run.py` | CLI entrypoint: `harvest` \| `discover` \| `update` \| `all`. Puts `src/` on the path. |
| `src/intern_engine/models.py` | The `Job` dataclass — the one shape every connector returns. |
| `src/intern_engine/paths.py` | All file paths, computed from the repo root (CI-safe). |
| `src/intern_engine/config.py` | Loads `data/config.json`; derives the repo/Pages URLs. |
| `src/intern_engine/net.py` | Async HTTP with retry/backoff + per-host concurrency limits. |
| `src/intern_engine/connectors/` | One module per ATS: Greenhouse, Lever, Ashby, SmartRecruiters, Workday, Oracle, Amazon, Rippling, Workable, Breezy, Recruitee. |
| `src/intern_engine/filters.py` | Classification: internship? tech? season/year? US/Canada? category. |
| `src/intern_engine/sponsorship.py` | Phrase-anchored visa/citizenship classifier + display flags. |
| `src/intern_engine/h1b.py` | Joins companies against the USCIS H-1B employer index (✓ badge). |
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
| `src/intern_engine/readme.py` | Renders `README.md` + `data/internships.csv`. |
| `src/intern_engine/dashboard.py` | Renders the self-contained GitHub Pages dashboard. |
| `src/intern_engine/publish.py` | Renders the Atom feed + static JSON API under `docs/`. |
| `src/intern_engine/notify.py` | Optional Discord webhook alerts for newly spotted roles. |
| `src/intern_engine/db.py` | Optional Postgres (Supabase) mirror of jobs/companies/runs. |
| `.github/workflows/update.yml` | Scheduled CI (every 2h): run update, commit changes. |
| `.github/workflows/discover.yml` | Weekly CI: grow `data/companies.json` automatically. |
| `data/config.json` | Tunable settings (see below). |
| `data/companies.json` | Validated companies the pipeline reads. |
| `data/jobs.json` | The persistent job state (source of truth for the README). |
| `data/health.json` | Circuit-breaker state (auditable in git like everything else). |
| `data/history.jsonl` | One line of run metrics per run (feeds the dashboard chart). |
| `data/h1b.json` | Compact USCIS employer→approvals index (built by `tools/build_h1b.py`). |
| `data/seasons.json` | Last cycle's first-post date per company (built by `tools/build_seasons.py`). |
| `tools/build_h1b.py` | Offline builder: USCIS Data Hub CSVs → `data/h1b.json` (run yearly). |
| `tools/build_seasons.py` | Offline builder: last cycle's listing datasets → `data/seasons.json`. |

## Configuration (`data/config.json`)

```json
{
  "cycles": ["Summer 2027", "Fall 2026"],
  "regions": ["US"],
  "role_scope": "tech",
  "max_age_days": 270,
  "max_per_company": 3,
  "allowlist_only": false,
  "section_limits": { "Summer 2027": 100, "Fall 2026": 40 }
}
```

Sources: Greenhouse, Lever, Ashby, SmartRecruiters, Workday, Oracle Recruiting
Cloud, Amazon, Rippling, Workable, Breezy, and Recruitee. A company-level
quality gate (`data/blocklist.json` plus the optional `allowlist_only` mode)
keeps the list free of junk/no-name companies.

- `cycles` — the exact cycles to show; these become the section headings, in order.
  A role is kept ONLY if its title explicitly states the year (e.g. "2027" or
  "Fall 2026"); undated roles and other cycles are dropped.
- `regions` — `["US"]` (United States only), `["US", "Canada"]`, or `["Global"]`
  to disable the location filter.
- `role_scope` — `"tech"` keeps only tech roles; `"all"` keeps every internship.
- `max_age_days` — drop postings published longer ago than this (kills stale/evergreen reqs).
- `max_per_company` — cap roles shown per company per section, for variety.
- `section_limits` — max rows per section; over the cap, the most sought-after companies win.

Run `python run.py discover` to mine public datasets for company tokens and grow
`data/companies.json` — we then poll those feeds directly. A weekly workflow does
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
carry the raw value; the dashboard has a one-click "F-1 friendly" filter.

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

Every list shows what's open; the radar shows **what's coming**. Offline,
`tools/build_seasons.py` mines last cycle's public listing datasets for each
company's earliest SWE/DS/Quant intern posting date. At render time `radar.py`
projects that date one year forward, checks it against the live store (has the
company posted this cycle in our feeds?), and renders a countdown table:
README shows the next 20, the dashboard has all ~870 searchable, and
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
python -m pytest                # 93 tests, no network
```
