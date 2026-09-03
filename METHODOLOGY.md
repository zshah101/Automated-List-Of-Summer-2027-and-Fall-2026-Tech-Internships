# Methodology

How every number on this list is produced, and what each one does and doesn't
claim. If something here doesn't match what the code does, that's a bug —
[open an issue](../../issues/new/choose).

## Where roles come from

Every role is read directly from the employer's own applicant tracking system
(ATS) — Greenhouse, Lever, Ashby, Workday, Oracle, SmartRecruiters, Workable,
Breezy, Recruitee, Rippling, Eightfold, and Amazon's jobs API. There are no
aggregator links, no scraped third-party lists, and no roles copied from other
GitHub repos. The **Apply** link is the employer's URL.

The registry of boards to poll (`data/companies.json`) is built by
`run.py discover` + `run.py harvest`, which probe candidate ATS slugs and keep
the ones that respond.

## What counts as a role we list

A posting must pass all of:

1. **It's an internship or co-op** — whole-word match on intern/internship/co-op
   in the title, and *not* a senior/staff/manager title.
2. **It's a tech role** — software, data, ML/AI, or security. A bare "engineer"
   isn't enough (that admits mechanical, civil, aerospace). Two adjacent
   categories are kept deliberately: **Quant** (quant dev / trading tech, which
   is software work students filter for) and a small number of **Hardware**
   roles whose titles are software-first (embedded, firmware). The dashboard's
   category filter separates all of them, so you can exclude either.
3. **It's in the configured region** — Singapore and core Southeast Asia
   (Singapore, Malaysia, Indonesia, Thailand, Vietnam, the Philippines) by
   default. The region is read from the posting's own location string: a named
   country, a country-prefixed component (`SG-Singapore`, `ID-Jakarta`), or a
   recognised regional hub city on its own (`Kuala Lumpur`, `Taguig`). A city
   only counts when nothing else in the string names a country, so a US
   namesake such as `Manila, AR` is never mistaken for the region. A bare
   "Remote" with no country named matches nothing.
4. **It maps to a tracked cycle** — see below.

The filters are precision-first: we would rather miss a role than list a wrong
one, because a wrong row costs a reader an application.

## Cycle: stated vs inferred

This is the distinction the whole list is organized around.

| Label | What it means |
|---|---|
| `Summer 2027` (plain) | The **employer stated it** — the cycle appears in the job title, or the posting's own text states a term+year. |
| `not stated` | The posting **never names a cycle** - not in the title, not in the text. We do not guess one. Earlier versions printed `~Summer 2027` here, derived from the posting month; audited against the live postings that guess was confirmed 0 times out of 60 and contradicted every time it was checkable, so it was removed. These roles are still listed (they are recent and real) in their own section. |

Inferred roles are listed in their own section, never mixed into a stated-cycle
section, and are excluded from the "with a stated cycle" count. They're real,
current tech internships — we just can't prove which cycle they're for.

A posting that names **two** cycles ("Fall 2026/Summer 2027") is recorded with
both and appears under each.

When enrichment later reads a posting's text and finds a stated cycle, the guess
is replaced and the `~` disappears. If the stated cycle turns out to be one we
don't track, the role leaves the list permanently.

## Dates

`posted_at` is the employer's own publication date wherever the board exposes
one. Each date carries a `posted_at_source` describing how good it is:

| `posted_at_source` | Meaning |
|---|---|
| `exact` | A real timestamp from the source. |
| `date_only` | The source published a calendar day, no clock time. |
| `relative_derived` | Computed from relative text ("Posted 6 Days Ago"). Approximate; superseded automatically when the detail page yields a real date. |

A role's date is frozen the first time we see it, so the list behaves like a
ladder. The **one** exception is precision: a higher-precision date replaces a
lower-precision one for the same role. It never regresses.

**Detection latency** (in Engine health) measures minutes between publication
and our first sight of a role. It counts only roles *published inside the
window* and only those with an `exact` timestamp — a `date_only` date would
invent up to 24 hours of fake latency. Both p50 and p95 are published with the
sample size, because a median alone hides the tail.

## Open vs closed

A role is closed for one of two reasons, recorded in `closed_reason`:

- **`gone-from-feed`** — **two consecutive** complete reads of the employer's
  board no longer return it. One miss only arms the closure (ATS search indexes
  have transient gaps); the second fires it. Strong evidence the posting is
  gone; not the same as the employer telling us so.
- **`out-of-scope`** — it's still posted, but it no longer passes our filters
  (wrong country, off-cycle, not a tech internship). Our verdict, not theirs.

Several ATS cap how many search results they return. A capped response looks
identical to "this company has no more roles", so every connector reports
whether its snapshot was **complete**, and a partial snapshot is never allowed
to close anything. Typically ~90 of ~3,450 boards hit a cap on a given run;
their roles simply carry over.

## Visa sponsorship

Detected from the posting's own text by phrase matching, never inferred from the
company. Four verdicts:

| Verdict | Meaning |
|---|---|
| `citizens-only` 🇺🇸 | Requires US citizenship, a clearance, or ITAR/US-person status. |
| `no-sponsorship` 🛂 | The posting says it won't sponsor a work visa. |
| `offers` | The posting explicitly says sponsorship is available. |
| `unknown` | The text says nothing conclusive. **This is most postings.** |

The dashboard filter names each verdict separately on purpose. An earlier
"F-1 friendly" toggle merely *hid* the explicit negatives, so ~97% of what it
returned was actually `unknown` — presented as if it had been checked. It
hadn't.

The classifier is versioned. When its rules change, every stored verdict from an
older version is re-derived from the posting text, so improvements reach the
whole live list rather than only roles found after the change.

## The ✓ H-1B badge

**Shown only while the United States is a tracked region.** The badge and the
🇺🇸 / 🛂 flags are read off US immigration data and US-visa phrasing, so on the
Southeast Asia list they are suppressed everywhere they would otherwise render
rather than shown blank. The classifier still runs — its text is shared with
skill and cycle extraction — but its verdicts are not published.

✓ means USCIS approved a meaningful number of H-1B petitions for that employer
in the published fiscal-year window, matched against the public
[H-1B Employer Data Hub](https://www.uscis.gov/tools/reports-and-studies/h-1b-employer-data-hub).

It is **a history, not a promise**. It says nothing about internship
sponsorship, about current policy, or about this specific role. No ✓ only means
we couldn't confidently match the employer.

## Drop Radar

A forecast of when companies usually open, from two sources:

- **🎯 verified** — the engine observed the drop itself from the company's
  careers API. `data/observed.json` records, per company and cycle, the earliest
  date seen *and the distinct role ids behind it*, so the sample count is
  auditable rather than a counter that inflates every run.
- **typical window** — a hand-verified opening *month* for a marquee name.
  A month, not a promise of a day.

"Waiting" means we haven't seen it in *our tracked feeds*, not that it isn't
posted somewhere. Only roles whose cycle the employer stated become
observations; a guess is never projected forward as if it were fact.

## "N openings" on a row

Employers really do open the same job several times. Copart currently has eight
live `Software Engineering Intern` requisitions for Dallas; GDIT filed
RQ225450, RQ225456 and RQ225469 for one Annapolis Junction role in a single
morning. Each one is a separate requisition with its own id and its own
application, so none of them is a duplicate and we delete none of them.

Showing you eight identical rows is still bad reading, so a row that says
**"3 openings"** means: *this employer has three separate live requisitions for
the same title, in the same place, for the same cycle.* Every one of them is
linked from that row (`Apply`, then `#2`, `#3`, …).

What this is **not**: it is not deduplication and it never merges two things
that might be different jobs. A different location, a different work mode
(on-site vs remote), a different cycle, or a closed-vs-open pair are always
separate rows. The only thing folded is an exact repeat.

The counts do not change. "165 open roles" still counts requisitions, so a row
saying "3 openings" contributes 3. The CSV and the JSON API are never grouped —
they always carry one record per requisition, with every id.

Separately, one *genuine* duplicate is removed rather than grouped: when a
company runs more than one career site on the same ATS tenant, the same
requisition can appear on both under different URLs. We collapse those only
when the ATS's own requisition number proves they are one posting.

## Counts you'll see, and what they mean

| Where | Number | Denominator |
|---|---|---|
| Hero / API | open roles | every open role in the store |
| Hero | with a stated cycle | roles whose employer named the cycle |
| README tables | "listed below" | after a per-company display cap |
| Any row | "N openings" | separate live requisitions for the same job (see above) |
| `internships.csv` | every open role | no cap, never grouped — the full export |
| Engine health | fetch success | shown against *both* boards attempted and the full registry |

## Verifying any of this yourself

```bash
python -m pytest              # the full test suite, no network
python tools/verify_accuracy.py   # every open role against every invariant
```

`verify_accuracy.py` runs in CI **before** anything is published. If it fails,
the run stops and the previous good build stays live.

## Known limitations

- Most postings never mention sponsorship, so `unknown` dominates — by design.
- Cycle inference is a heuristic; that's exactly why those roles are separated.
- The H-1B data lags by fiscal years and matches on employer name (US only).
- Skill tags come from keyword matching over posting text and will miss things.
- We only see roles posted to the ATS platforms we support.
- Region detection reads the location string; unusual formats may be missed.
  Regional-hub cities are recognised from a fixed list, so a role posted with
  only a smaller city's name and no country will be missed.
- Most boards in the registry were discovered from US-facing datasets, so
  Southeast Asian coverage is still growing; `data/candidates.json` and the
  regional sources in `discover.py` are where it is widened.
