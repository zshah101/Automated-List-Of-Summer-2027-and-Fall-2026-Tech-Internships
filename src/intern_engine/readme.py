"""Render the public-facing README.md (the product) + a CSV tracker.

Plain, professional, human voice. No decorative emojis. Sections are exactly the
configured cycles, in order. Roles are sorted by their PUBLISHED date (newest on
top), and that date is frozen per role so the page behaves like a ladder.
"""

from __future__ import annotations

import csv
import io
import json
import os
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from . import (
    config,
    filters,
    grouping,
    h1b,
    paths,
    priority,
    radar,
    skills,
    sponsorship,
)


def _engine_metrics() -> str:
    """One-line observability summary from the last run, if available."""
    try:
        with open(paths.STATS_PATH, encoding="utf-8") as f:
            stats = json.load(f)
    except (OSError, ValueError):
        return ""
    sources = len(stats.get("companies_by_source", {}))
    total = stats.get("companies_total", 0)
    ok = stats.get("fetched_ok", 0)
    # Both denominators, because quoting only the attempted-boards rate reads as
    # "we polled everything" when quarantined endpoints were never tried.
    line = (
        f"_Engine (last run): {ok:,} of {total:,} registered boards returned "
        f"successfully across {sources} ATS platforms "
        f"({int(stats.get('fetch_success_rate', 0) * 100)}% of boards attempted, "
        f"{int(stats.get('fetch_success_rate_registry', 0) * 100)}% of the full "
        f"registry) · completed in {stats.get('duration_seconds', 0)}s"
    )
    partial = stats.get("snapshots_partial")
    if partial:
        line += (
            f" · {partial} board(s) returned a capped result set, so their roles "
            "were not eligible to be closed this run"
        )
    coverage = stats.get("posted_date_coverage")
    if coverage is not None:
        line += f" · employer or source-derived date on {int(coverage * 100)}% of open roles"
    return line + "._"


def _as_of(value: str | None = None) -> datetime:
    try:
        return datetime.strptime((value or "")[:19], "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=UTC
        )
    except ValueError:
        return datetime.now(UTC)


def _now_str(data_as_of: str | None = None) -> str:
    return _as_of(data_as_of).strftime("%b %d, %Y at %H:%M UTC")


def _md_cell(text: str) -> str:
    return (text or "—").replace("|", "/").replace("\n", " ").strip() or "—"


def _short_location(loc: str, limit: int = 40) -> str:
    loc = _md_cell(loc)
    if len(loc) <= limit:
        return loc
    parts = [p.strip() for p in loc.replace(";", ",").split(",") if p.strip()]
    if len(parts) > 1:
        return f"{parts[0]} +{len(parts) - 1} more"
    return loc[: limit - 1].rstrip() + "…"


def _date_str(record: dict) -> str:
    """The published date string we sort/display by (frozen per role)."""
    # Display only a REAL published date (no first_seen fallback) — undated -> dash.
    return record.get("posted_at") or ""


def _sort_key(record: dict):
    # Dated roles first (newest), undated sink to the bottom; first_seen breaks
    # ties so undated roles still have a stable, newest-first order.
    return ((record.get("posted_at") or "")[:10], (record.get("first_seen_at") or "")[:19])


def _pretty_date(record: dict) -> str:
    iso = _date_str(record)
    if not iso:
        return "—"
    try:
        return datetime.strptime(iso[:10], "%Y-%m-%d").strftime("%b %d, %Y")
    except ValueError:
        return iso[:10]


def _is_new(record: dict, hours: int = 48) -> bool:
    # For a grouped row, "new" means any of its openings is new. The row's
    # representative is the oldest member on purpose (stable id), so reading
    # only its own first_seen would hide a requisition added this morning.
    seen = (record.get("opening_newest") or record.get("first_seen_at") or "")[:19]
    if not seen:
        return False
    try:
        seen_dt = datetime.strptime(seen, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
    except ValueError:
        return False
    return datetime.now(UTC) - seen_dt <= timedelta(hours=hours)


REMOTE_MARK = "🆁"  # U+1F181 — a squared R, so it reads as a badge, not a word


def _cells(record: dict,
           us_context: bool = True) -> tuple[str, str, str, str, str, str, str]:
    """Table cells for one role.

    `us_context` carries whether the US is a tracked region. The ✓ H-1B badge
    and the 🇺🇸 / 🛂 flags are read off US immigration data, so on a list that
    holds no US roles they would be blank at best and misleading at worst.
    """
    company = _md_cell(record.get("company"))
    if us_context and h1b.badge(h1b.approvals_for(record.get("company") or "")):
        company += " ✓"
    # The remote mark sits beside the H-1B ✓ in the first column, where the eye
    # already goes for row-level markers, instead of trailing a title that can
    # run 60 characters. Every table row IS one role, so a per-role marker is
    # unambiguous here — the legend says "this role", not "this company".
    if filters.is_remote(record.get("location") or "", record.get("title") or ""):
        company += f" {REMOTE_MARK}"
    title = _md_cell(record.get("title"))
    is_open = record.get("is_open", True)
    badges = " ".join(
        b for b in (sponsorship.flag(record.get("sponsorship")) if us_context else "",
                    "🆕" if _is_new(record) and is_open else "")
        if b
    )
    if badges:
        title = f"{title} {badges}"
    # The employer opened this same job more than once. Say so on the row and
    # link every requisition, rather than repeating the row N times.
    openings = record.get("openings") or 1
    if openings > 1:
        title += f" _({openings} openings)_"
    ordered_skills = skills.sort_by_signal(record.get("skills"), record.get("title"))[:4]
    skill_tags = _md_cell(", ".join(ordered_skills)) if ordered_skills else "No skills listed"
    url = record.get("url") or ""
    apply = "Closed" if not is_open else (f"[Apply]({url})" if url else "—")
    if is_open and url and openings > 1:
        extra = [u for u in (record.get("opening_urls") or []) if u]
        apply = " ".join(
            [f"[Apply]({url})"]
            + [f"[#{i + 2}]({u})" for i, u in enumerate(extra[:6])]
        )
    return (
        company, title,
        _md_cell(record.get("category")),
        _short_location(record.get("location")),
        skill_tags,
        _pretty_date(record),
        apply,
    )


def _row(record: dict, cycle: str | None = None, us_context: bool = True) -> str:
    company, title, category, location, skill_tags, posted, apply = _cells(
        record, us_context)
    # A multi-cycle posting appears under each cycle it names. Naming the OTHER
    # cycles here explains why the same title shows up twice — repeating this
    # section's own cycle would just be noise.
    others = [s for s in (record.get("seasons") or []) if s != cycle]
    if len(record.get("seasons") or []) > 1 and others:
        title += f" _(also open for {', '.join(others)})_"
    return (f"| {company} | {title} | {category} | {location} | {skill_tags} | "
            f"{posted} | {apply} |")


def _rolling_row(record: dict, us_context: bool = True) -> str:
    """A row in the cycle-not-stated lane.

    There is deliberately no "likely cycle" column any more. It used to print
    `~Summer 2027`, which was a posting-date guess: checked against the live
    postings it was confirmed 0 times out of 60 and contradicted every time it
    could be checked. These rows now say what's true — nobody stated a cycle.
    """
    company, title, category, location, skill_tags, posted, apply = _cells(
        record, us_context)
    return (f"| {company} | {title} | {category} | {location} | {skill_tags} | "
            f"{posted} | {apply} |")


def _region_label(cfg: dict) -> str:
    return config.region_label(cfg)


def _company_count() -> tuple[int, int]:
    """(board endpoints, unique employers).

    They differ — a company with two ATS accounts is two endpoints — and
    calling the endpoint count "companies" overstated the employer reach by
    ~85. Both numbers are real; they just answer different questions.
    """
    try:
        with open(paths.COMPANIES_PATH, encoding="utf-8") as f:
            companies = json.load(f)
    except (OSError, ValueError):
        return 0, 0
    return len(companies), len({(c.get("name") or "").strip().lower() for c in companies})


def _raw_feed_url() -> str:
    """The feed served straight from the repo (no Pages dependency)."""
    return f"https://raw.githubusercontent.com/{config.repo_slug()}/main/docs/feed.xml"


def _email_subscribe_url() -> str:
    """One-click feed-to-email signup, prefilled with our feed."""
    return f"https://feedrabbit.com/subscriptions/new?url={quote(_raw_feed_url(), safe='')}"


def _header(cfg: dict, total_open: int, companies: int, new_week: int,
            employers: int | None = None,
            shown: int | None = None, stated: int | None = None,
            inferred: int | None = None,
            data_as_of: str | None = None) -> list[str]:
    """The README's opening block.

    `total_open` is every open role (what the API and dashboard report); `shown`
    is how many survived the per-company cap in these tables. They differ, and
    the page used to print only the smaller one under the same wording as the
    API's larger one — so the two disagreed with no way to tell which was real.

    `stated` / `inferred` split the total by cycle EVIDENCE. Leading with that
    split is the whole pitch: a smaller number you can trust beats a bigger one
    that quietly includes 46% guesses.
    """
    count_phrase = f"{total_open} open roles"
    if shown is not None and shown != total_open:
        count_phrase = f"{total_open} open roles ({shown} listed below)"
    region = _region_label(cfg)
    cycles = config.cycles(cfg)
    cycles_phrase = " and ".join(cycles)
    pages = config.pages_base()

    repo = config.repo_slug()
    stats_url = quote(f"{pages}/api/stats.json", safe="")
    # The masthead is centered HTML: GitHub renders it, and it gives the page a
    # real header block instead of a left-aligned pile of bold lines. Markdown
    # inside needs the blank lines around it to keep parsing as markdown.
    # The H1 is the repo's shop window, so it names the cycle AND the region
    # this deployment actually tracks - a title that says one thing while the
    # table below lists another is the fastest way to lose a reader's trust.
    return [
        '<div align="center">',
        "",
        f"# 🎓 {cycles[0]} Tech Internships"
        + (f" — {region}" if config.restrict_region(cfg) else ""),
        "",
        "**A self-updating engine that tracks tech internships so you don't have "
        "to.**",
        "",
        f"[![CI](https://img.shields.io/github/actions/workflow/status/{repo}/ci.yml"
        f"?branch=main&label=tests&style=flat-square&color=3fb950)]"
        f"(https://github.com/{repo}/actions/workflows/ci.yml)&nbsp;"
        f"[![Open roles](https://img.shields.io/badge/dynamic/json?label=open%20roles"
        f"&query=open_total&url={stats_url}&color=2f81f7&style=flat-square)]({pages}/)&nbsp;"
        "![Updates](https://img.shields.io/badge/updates-every%2030%20min-3fb950"
        "?style=flat-square)&nbsp;"
        f"[![RSS](https://img.shields.io/badge/RSS-subscribe-e67e22?style=flat-square)]"
        f"({pages}/feed.xml)",
        "",
        f"### {count_phrase} · {new_week} new this week",
        "",
        f"{(employers or companies):,} employers tracked · data as of "
        f"{_now_str(data_as_of)}",
        "",
        (f"_{stated} have a cycle the employer stated · {inferred} are recent "
         "postings whose cycle isn't stated (listed separately, never mixed in)._"
         if stated is not None and inferred is not None else ""),
        "",
        f"**[🖥️ Live dashboard]({pages}/)** · "
        f"**[📡 RSS]({pages}/feed.xml)** · "
        f"**[⚙️ JSON API]({pages}/api/jobs.json)** · "
        f"**[✉️ Email alerts]({pages}/#subscribe)**",
        "",
        "</div>",
        "",
        "> [!TIP]",
        "> **⭐ Star this repo** to save it and get updates when new roles are added.",
        "",
        "Instead of refreshing a dozen career pages by hand, it reads company "
        "hiring feeds directly and keeps one live list — newest roles on top, "
        "refreshed automatically throughout the day.",
        "",
        # Native signup posts into our own Supabase list (RLS: insert-only).
        # The Feedrabbit link is the zero-account fallback via the raw feed URL,
        # which works even when GitHub Pages is off.
        f"**🔔 New roles in your inbox:** [subscribe by email]({pages}/#subscribe) "
        "- one email a day, only when new internships actually appeared, "
        f"unsubscribe from any email in two clicks. (Prefer RSS-to-email? "
        "[Feedrabbit works too]"
        f"({_email_subscribe_url()}).)",
        "",
        "---",
        "",
        "## What this is",
        "",
        "This is an engine, not a hand-kept list. It polls company career feeds "
        "every 30 minutes, finds the internships, removes duplicates, and "
        "rebuilds this page on its own.",
        "",
        "Every link comes straight from the source — so it's real and current, "
        "not a stale list someone forgot to update. Speed matters.",
        "",
        "## What makes this different",
        "",
        # A table, not a bullet list: each row leads with the claim in the left
        # column so the section can be SKIMMED. As paragraphs these ran four
        # lines each and the distinguishing word was buried mid-sentence.
        "| | |",
        "|---|---|",
        # Both of these are built on US immigration data and a US-seeded radar,
        # so they are claims this page can only make while it lists US roles.
        *(("| 📅 **[Drop Radar](#drop-radar)** | A forecast of **what's coming**. "
           "Each marquee company's typical opening window, replaced by the real "
           "drop date the moment the engine catches it live. Windows are "
           "estimates and labelled as such; only dates the engine saw itself "
           "are marked verified. |",
           "| 🛂 **Visa intel, computed** | 🇺🇸 / 🛂 flags detected automatically "
           "from every job description, plus ✓ for employers with a real H-1B "
           "track record (USCIS data, FY2022-23 — a history, not a promise). "
           "The big lists crowdsource this by hand; here it's code. Most "
           "postings say nothing either way, and those show as unknown rather "
           "than guessed. |") if config.want_us(cfg) else ()),
        *((f"| 🌏 **Built for {region}** | Every role is filtered to the "
           "region above, from the posting's own location. Country-prefixed "
           "and city-only postings are both understood, so a bare "
           "\"Kuala Lumpur\" or \"SG-Singapore\" is never missed. |",)
          if not config.want_us(cfg) else ()),
        "| 📆 **A real date on nearly every role** | Taken from the job portal "
        "itself wherever the portal states one, so newest-first actually means "
        "newest. The exact coverage figure is printed at the bottom of this "
        "page every run. |",
        "| 🧰 **Skill tags + pay, extracted** | Every posting's text is scanned "
        "for the stack it wants (Python, C++, PyTorch, …) and the pay it "
        f"states — searchable on the [dashboard]({pages}/), and included in the "
        "CSV and API. |",
        f"| 🔔 **Alerts your way** | [Email digests]({pages}/#subscribe) or "
        f"[RSS]({pages}/feed.xml) — point any reader, or a Slack/Discord RSS "
        f"integration, at it. Plus a [live dashboard]({pages}/) with search, "
        "filters, and a saved-roles list that never leaves your browser. |",
        f"| ⚙️ **An engine, not a spreadsheet** | {companies:,} job-board "
        f"endpoints ({(employers or companies):,} distinct employers; some run "
        "more than one board) polled every 30 minutes across 12 ATS platforms. "
        "Full source and tests in this repo. |",
        "",
        "## Scope",
        "",
        "| | |",
        "|---|---|",
        "| **Roles** | Software Engineering, Data Science & Machine Learning "
        "(and closely related technical internships) |",
        f"| **Region** | {region}"
        + (" (primary), with a separate International section"
           if config.include_international(cfg) else "")
        + " |",
        f"| **Cycles** | {cycles_phrase} |",
        "",
        "## About",
        "",
        f"I built this for the search I'm doing myself, so it tracks {region} "
        "— that's where I'm applying. Everything is filtered from each "
        "posting's own stated location, and the same engine can be pointed at "
        "another region by editing one line of "
        "[`data/config.json`](data/config.json).",
        "",
        "Use it to spot roles early and apply before they fill up. Being first "
        "genuinely helps.",
        "",
        "## Where this is going",
        "",
        "I'm building this in the open and adding to it as it grows.",
        "",
        "**Recently shipped:** email alerts · the live dashboard · "
        f"{region} coverage",
        "",
        "**Next up:** personalized alerts (pick your categories) · per-company "
        "hiring pages · a ghost-posting detector",
        "",
        "If it helps you, a star means a lot and tells me to keep going.",
        "",
        "## How to use",
        "",
        # Collapsed by default: it's a reference legend, and expanded it pushed
        # the first actual role most of a screen further down.
        "<details>",
        "<summary><b>Reading the table — flags, dates, and the cycle split</b>"
        " (click to expand)</summary>",
        "",
        "- Roles are grouped by cycle below - **newest posting on top, oldest at the bottom.**",
        "- A cycle section holds only roles whose **employer stated that cycle** - "
        "in the title, or in the posting's own text. Postings that name no cycle "
        "anywhere are in *Recently posted — cycle not stated* further down, with "
        "**no cycle guessed for them**. Same quality bar, different amount of "
        "evidence.",
        "- The **Posted** column is the date the company published the role.",
        "- **_(3 openings)_ after a role title** = the employer has that many "
        "separate live requisitions for the same job, in the same place, for "
        "the same cycle. They're all real and each takes its own application, "
        "so they're linked individually (**Apply**, then **#2**, **#3**) "
        "instead of repeating the row. Counts still count requisitions, and "
        "the CSV export is never grouped.",
        f"- **{REMOTE_MARK} after a company name** = **this role is remote** — "
        "the posting's own location or title says so. It marks the role on that "
        "row, not the whole company.",
        # The visa markers only appear on rows when the US is tracked, so the
        # legend that explains them only appears then either.
        *(("- **Flags after a role title:** 🇺🇸 = requires U.S. citizenship or a "
           "security clearance · 🛂 = the posting says it won't sponsor a work "
           "visa · 🆕 = spotted in the last 48 hours. Sponsorship flags are "
           "detected automatically from each job description - treat them as a "
           "strong hint and confirm on the posting.",
           "- **✓ after a company name** = a real H-1B track record: USCIS "
           f"approved {h1b.BADGE_THRESHOLD}+ petitions for that employer in "
           f"{h1b.window_label() or 'recent fiscal years'} (matched "
           "automatically against the official [H-1B Employer Data Hub]"
           "(https://www.uscis.gov/tools/reports-and-studies/h-1b-employer-data-hub)). "
           "No ✓ doesn't mean they won't sponsor - it means we can't prove "
           "they have.")
          if config.want_us(cfg) else
          ("- **🆕 after a role title** = spotted in the last 48 hours.",
           "- **Work passes:** most roles here are open to students studying "
           "in the country concerned; in Singapore a non-resident intern "
           "normally needs a Work Holiday Pass or a Training Employment Pass, "
           "which the employer applies for. Postings rarely say either way, so "
           "confirm before you count on it.")),
        "- Track your applications with [`data/internships.csv`](data/internships.csv) "
        "(opens in Excel / Google Sheets).",
        "- Missing a company? Adding one takes a single line, see "
        "[CONTRIBUTING.md](CONTRIBUTING.md).",
        "",
        "</details>",
        "",
        "---",
        "",
    ]


def _footer() -> list[str]:
    return [
        "---",
        "",
        "## Hiring timeline",
        "",
        "Internships posted per week, from each role's real published date - "
        "redrawn automatically on every run. When this line takes off, "
        "recruiting season is open:",
        "",
        "<picture>",
        '  <source media="(prefers-color-scheme: dark)" srcset="docs/trends-dark.svg">',
        '  <img alt="Internships posted per week, drawn from real published dates" '
        'src="docs/trends-light.svg">',
        "</picture>",
        "",
        "## How it stays current",
        "",
        "A small Python engine reads public company hiring feeds directly, keeps the "
        "roles that match the scope above, de-duplicates across sources, records each "
        "role's published date once (so it never shifts), and regenerates this page "
        "through GitHub Actions. It polls every company concurrently (async) with "
        "retry/backoff and per-host rate limits. The full source is in this repo.",
        "",
        _engine_metrics(),
        "",
        "## How this list is built",
        "",
        "[METHODOLOGY.md](METHODOLOGY.md) documents exactly what every label "
        "claims — what separates a stated cycle from an inferred one, what the ✓ "
        "H-1B badge does and doesn't mean, how a role gets closed, and which "
        "limitations are known. Anything on this page that doesn't match the "
        "code is a bug worth reporting.",
        "",
        "## Contributing",
        "",
        "Adding a company takes one line, see [CONTRIBUTING.md](CONTRIBUTING.md), "
        "or just [open a request](../../issues/new?template=add-company.yml) with "
        "the board URL. **Spotted something wrong?** "
        "[Report the exact field](../../issues/new?template=wrong-data.yml) — "
        "wrong country, wrong cycle, closed role, bad sponsorship flag. Those "
        "reports usually fix a rule, which fixes every other role too.",
        "",
        "Also here: [PRIVACY.md](PRIVACY.md) (what the email list stores — an "
        "address and nothing else) · [SECURITY.md](SECURITY.md) · "
        "[ARCHITECTURE.md](ARCHITECTURE.md) · [MIT licensed](LICENSE).",
        "",
        "Built by one student with AI assistance, in the open. The part that "
        "matters isn't who typed it — it's that the rules, the tests, and every "
        "run's output are all public and checkable.",
        "",
        "## Note on dates",
        "",
        "The **Posted** column shows when a role was published, with the newest at the "
        "top. I pull the posting date straight from each job portal, but a lot of them "
        "don't expose one publicly, so those rows show a dash (—) for now instead of a "
        "guessed date. The ones that do publish a date are dated. Know the real date for "
        "a dashed role? Open a PR and I'll merge it.",
        "",
        "Roles can close at any time, so always confirm on the company's own site before "
        "applying.",
        "",
    ]


def _select(rows: list[dict], limit, per_company) -> list[dict]:
    """Pick which rows to show, then order them newest-first for display.

    1) cap each company to `per_company` (variety, newest kept),
    2) if still over `limit`, keep the most sought-after companies first,
    3) display newest on top.
    """
    rows = sorted(rows, key=_sort_key, reverse=True)
    if per_company:
        seen: dict[str, int] = {}
        capped = []
        for r in rows:
            c = (r.get("company") or "").strip().lower()
            if seen.get(c, 0) >= per_company:
                continue
            seen[c] = seen.get(c, 0) + 1
            capped.append(r)
        rows = capped
    if limit and len(rows) > limit:
        rows = sorted(rows, key=lambda r: priority.rank(r.get("company")))[:limit]
    return sorted(rows, key=lambda r: _date_str(r)[:10], reverse=True)


IN_REGION = "in-region"
OUT_OF_REGION = "International"


def _region_of(record: dict, regions) -> str:
    """Which of the page's two lanes a role belongs in.

    Deliberately coarse. The store carries the specific country (stats and the
    API break it out), but the page needs one primary section per cycle plus
    the International overflow - one section per SEA country would fragment a
    list this size into eight near-empty tables.
    """
    if not regions:
        return IN_REGION  # "Global": the location filter is off, so nothing is out
    location = record.get("location") or ""
    return IN_REGION if filters.region_ok(location, regions) else OUT_OF_REGION


def _new_this_week(open_jobs: list[dict], data_as_of: str | None = None) -> int:
    cutoff = (_as_of(data_as_of) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    return sum(1 for r in open_jobs if (r.get("first_seen_at") or "") >= cutoff)


def _radar_section(store_data: dict, cycle: str, cap: int = 30,
                   data_as_of: str | None = None) -> list[str]:
    """The Drop Radar: which companies haven't posted yet, and when to expect
    them — from the engine's own observed dates + hand-verified opening windows.

    The README teaser leads with the FORECAST (waiting, soonest first) — that's
    the radar's unique value; "open now" rows just echo the list above — then
    shows a few recent drops as proof the forecast is real. The dashboard keeps
    the full, searchable list."""
    rows = radar.rows(store_data, cycle, today=_as_of(data_as_of).date())
    if not rows:
        return []
    waiting = [r for r in rows if r["status"] == "waiting" and radar.is_actionable(r)]
    opened = [r for r in rows if r["status"] == "open"]
    dropped = [r for r in rows if r["status"] == "dropped"]
    # Forecast first (what to watch for), then a handful of recent drops as proof.
    ordered = waiting + opened[:8] + dropped[:4]

    pages = config.pages_base()
    verified = sum(1 for r in rows if r.get("source") == "engine")
    lines = [
        '<a id="drop-radar"></a>',
        "",
        f"## 📅 Drop Radar — when companies usually post for {cycle}",
        "",
        "Stop refreshing career pages. 🎯 = the employer's **own posted date**, "
        "read from their careers API. (We may have discovered the role after it "
        "went live — the date is the employer's, not our discovery time.) "
        "The rest are typical opening "
        "**months**, hand-checked against each company's careers page and "
        "public recruiting guides. ✅ = already live in the list above.",
        "",
        "> **Heads up:** companies trend *earlier* every cycle, and \"~Aug\" is a "
        "month, not a day. Treat \"expected\" as when to **start watching**, and "
        "\"rolling\" companies as worth checking year-round.",
        "",
        "| Company | Typical opening | Expected this cycle | Status |",
        "|---|---|---|---|",
    ]
    for r in ordered[:cap]:
        if r["status"] == "open":
            status = f"✅ [open now]({r['url']})" if r["url"] else "✅ open now"
        elif r["status"] == "dropped":
            status = "🗓️ dropped"
        else:
            status = "⏳ waiting"
        mark = "🎯 " if r.get("source") == "engine" else ""
        lines.append(
            f"| {mark}{_md_cell(r['company'])} | {radar.pretty_last(r)} | "
            f"{radar.pretty_expected(r)} | {status} |"
        )
    verified_note = (f"**{verified}** dated from our own live observations 🎯 "
                     "(this grows every cycle). " if verified else "")
    lines.extend([
        "",
        f"_{len(rows)} companies on the [full radar]({pages}/#radar). {verified_note}"
        "\"~Aug\" = hand-verified typical month, not a promise of the day; "
        "\"rolling\" = posts year-round; \"waiting\" = not seen in our tracked "
        "feeds yet, not a guarantee it isn't out somewhere else._",
        "",
    ])
    return lines


def _closed_section(store_data: dict, cycles: list[str],
                    days: int = 14, cap: int = 40,
                    data_as_of: str | None = None) -> list[str]:
    """Roles that recently closed, kept visible (collapsed) so nobody wastes an
    application on a listing that just died. Only tracked cycles appear here —
    an off-cycle tombstone (text-verified "Summer 2026") was never on the list,
    so it has no business in its obituary either."""
    cutoff = (_as_of(data_as_of) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
    closed = [
        r for r in store_data.values()
        if not r.get("is_open") and (r.get("closed_at") or "") >= cutoff
        and r.get("season") in cycles
    ]
    if not closed:
        return []
    closed.sort(key=lambda r: r.get("closed_at") or "", reverse=True)
    closed = closed[:cap]
    lines = [
        "<details>",
        f"<summary><strong>Recently closed</strong> — {len(closed)} roles that "
        f"left the list in the last {days} days</summary>",
        "",
        "_Why each one left is in the last column, because the two reasons carry "
        "different evidence. **Gone from feed** = two consecutive complete reads "
        "of the employer's board no longer returned it (strong, but not the "
        "employer telling us directly). **Out of scope** = still posted, but it no longer "
        "passes our filters — our call, not theirs. **Not recorded** = closed "
        "before we started tracking the reason._",
        "",
        "| Company | Role | Cycle | Closed | Why |",
        "|---|---|---|---|---|",
    ]
    _WHY = {
        "gone-from-feed": "gone from feed",
        "out-of-scope": "out of scope",
    }
    for r in closed:
        closed_on = (r.get("closed_at") or "")[:10]
        why = _WHY.get(r.get("closed_reason"), "not recorded")
        lines.append(
            f"| {_md_cell(r.get('company'))} | {_md_cell(r.get('title'))} "
            f"| {_md_cell(r.get('season'))} | {closed_on} | {why} |"
        )
    lines.extend(["", "</details>", ""])
    return lines


def generate(store_data: dict, data_as_of: str | None = None) -> dict:
    cfg = config.load_config()
    cycles = config.cycles(cfg)
    per_company = config.max_per_company(cfg)
    regions = config.wanted_regions(cfg)
    us_context = config.want_us(cfg)

    open_jobs = [r for r in store_data.values() if r.get("is_open")]
    # The honesty split. A cycle section is a claim ("this role is for Summer
    # 2027"), so it may only contain roles whose employer actually SAID so.
    # Date-inferred roles are real, recent, worth applying to — but their cycle
    # is our guess, and mixing them in presented 46% of the list with more
    # certainty than the evidence supports. They get their own lane below.
    stated = [r for r in open_jobs if not r.get("season_inferred")]
    inferred = [r for r in open_jobs if r.get("season_inferred")]

    groups: dict[tuple[str, str], list[dict]] = {}
    for r in stated:
        # A multi-cycle posting ("Fall 2026/Summer 2027") belongs in EVERY
        # cycle it states — that's the point of keeping the full set.
        for cyc in (r.get("seasons") or [r.get("season", "")]):
            groups.setdefault((_region_of(r, regions), cyc), []).append(r)

    sections: list[tuple[str, str, list[dict]]] = []
    displayed: list[dict] = []
    seen_display: set[str] = set()
    for region in (IN_REGION, OUT_OF_REGION):
        for cycle in cycles:
            # Group BEFORE selecting, so an employer that opened one job eight
            # times spends one row of the per-company budget instead of eight —
            # the cap exists for variety, and eight copies of one title is the
            # opposite of variety.
            rows = _select(
                grouping.group(groups.get((region, cycle)) or []),
                config.section_limit(cfg, cycle),
                per_company,
            )
            if rows:
                heading = (cycle if region == IN_REGION
                           else f"{cycle} ({OUT_OF_REGION})")
                sections.append((heading, cycle, rows))
                for r in rows:
                    if r.get("id") not in seen_display:
                        seen_display.add(r.get("id"))
                        displayed.append(r)

    rolling_rows = _select(grouping.group(inferred), None, per_company)
    # Count OPENINGS, not rows: a row that says "3 openings" has put three of
    # the total on the page, and "165 open roles (158 listed below)" would
    # otherwise under-report what a reader can actually reach.
    shown_total = sum(
        r.get("openings") or 1 for r in (*displayed, *rolling_rows)
    )

    endpoints, employers = _company_count()
    lines = _header(cfg, len(open_jobs), endpoints,
                    _new_this_week(open_jobs, data_as_of), employers=employers,
                    shown=shown_total, stated=len(stated), inferred=len(inferred),
                    data_as_of=data_as_of)
    
    for heading, cycle, rows in sections:
        lines.append(f"## {heading}  ({len(rows)} employer-stated)")
        lines.append("")
        lines.append("| Company | Role | Category | Location | Skills | Posted | Apply |")
        lines.append("|---|---|---|---|---|---|---|")
        lines.extend(_row(r, cycle, us_context) for r in rows)
        lines.append("")

    if rolling_rows:
        lines.extend([
            f"## Recently posted — cycle not stated  ({len(rolling_rows)} roles)",
            "",
            "These postings never name a cycle — not in the title, not in the "
            "posting text — so neither do we. They're recent tech internships "
            "(posted within the last few weeks), often exactly the early drops "
            "worth applying to first; we just can't tell you which cycle "
            "they're for, and we'd rather say so than guess. The moment a "
            "posting's own text states a cycle, the role moves up into that "
            "section automatically.",
            "",
            "| Company | Role | Category | Location | Skills | Posted | Apply |",
            "|---|---|---|---|---|---|---|",
        ])
        lines.extend(_rolling_row(r, us_context) for r in rolling_rows)
        lines.append("")

    if not displayed and not rolling_rows:
        lines.append(
            "_No matching roles right now, the list fills as companies post. "
            "Star it and check back._"
        )
        lines.append("")

    # data/known_windows.json holds US marquee employers only, so off a US
    # list the radar has nothing to forecast and renders as an empty promise.
    if us_context:
        lines.extend(_radar_section(store_data, cycles[0], data_as_of=data_as_of))
    lines.extend(_closed_section(store_data, cycles, data_as_of=data_as_of))
    lines.extend(_footer())

    with open(paths.README_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # The CSV is the machine-readable export: EVERY open role belongs in it,
    # not just the rows that survived the README's per-company display cap.
    _write_csv(sorted(open_jobs, key=lambda r: _date_str(r)[:10], reverse=True))

    return {"open": shown_total, "companies": employers}



def _csv_safe(value):
    """Neutralize spreadsheet formula injection.

    Excel, Sheets and LibreOffice all execute a cell that opens with =, +, -
    or @. Job titles and company names come from third parties, so a posting
    titled `=HYPERLINK(...)` would run in the spreadsheet of anyone who opened
    our CSV. Prefixing an apostrophe makes the cell inert text; nothing is lost
    for ordinary values, which never start with those characters.
    """
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def _write_csv(open_jobs: list[dict]) -> None:
    fields = [
        "id", "company", "title", "season", "season_inferred", "seasons", "program",
        "remote", "category", "location", "sponsorship", "h1b_approvals",
        "salary", "skills", "posted_at", "posted_at_source", "first_seen_at",
        "url",
    ]
    buffer = io.StringIO()
    # Keep committed exports byte-stable on Windows and Linux. CSV consumers
    # accept LF, and it avoids all rows changing under core.autocrlf.
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore",
                            lineterminator="\n")
    writer.writeheader()
    for r in open_jobs:
        row = {k: r.get(k, "") for k in fields}
        row["h1b_approvals"] = h1b.approvals_for(r.get("company") or "") or ""
        row["skills"] = "; ".join(r.get("skills") or [])
        row["seasons"] = "; ".join(r.get("seasons") or [])
        row["program"] = filters.program_type(r.get("title") or "")
        row["remote"] = "yes" if filters.is_remote(
            r.get("location") or "", r.get("title") or "") else ""
        writer.writerow({k: _csv_safe(v) for k, v in row.items()})

    # Written twice: data/ is the repo tracker people clone, docs/ is what
    # GitHub Pages serves — the dashboard links to the latter, and without the
    # copy that link 404s.
    text = buffer.getvalue()
    os.makedirs(paths.DOCS_DIR, exist_ok=True)
    for target in (paths.CSV_PATH, os.path.join(paths.DOCS_DIR, "internships.csv")):
        with open(target, "w", newline="", encoding="utf-8") as f:
            f.write(text)
