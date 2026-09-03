"""Generate a self-contained metrics + listings dashboard for GitHub Pages.

Writes docs/index.html with the run metrics, a run-history sparkline, and the
current open roles baked in (no external fetches, so it works the moment Pages
serves it). Filtering/search runs client-side in vanilla JS — the page stays a
single static file. Regenerated every run.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from html import escape

from . import config, filters, grouping, h1b, paths, radar, sponsorship, trends


def _hero(stats: dict, open_jobs: list[dict], proven_roles: int,
          us_context: bool = True) -> str:
    """The handful of numbers an applicant actually needs, and nothing else.

    This used to be ten equal-weight tiles where "Last run: 402.0s" sat beside
    "Open roles" — engine telemetry competing with the thing people came for.
    Operator metrics moved to a collapsed panel at the bottom of the page.
    """
    stated = sum(1 for r in open_jobs if not r.get("season_inferred"))
    remote = sum(1 for r in open_jobs
                 if filters.is_remote(r.get("location") or "", r.get("title") or ""))
    items = [
        (str(len(open_jobs)), "open roles", "every one linked to the employer"),
        (str(stated), "with a stated cycle", "the employer named it, we didn't guess"),
        # The H-1B tile is a US immigration statistic; off a US list it would
        # read "0 at proven H-1B sponsors", which says nothing true.
        *([(str(proven_roles), "at proven H-1B sponsors",
            f"USCIS approved {h1b.BADGE_THRESHOLD}+ petitions")]
          if us_context else []),
        (str(remote), "remote", "the posting's own words say so"),
    ]
    return "".join(
        f'<div class="hcard"><div class="hnum">{escape(v)}</div>'
        f'<div class="hlbl">{escape(label)}</div>'
        f'<div class="hsub">{escape(note)}</div></div>'
        for v, label, note in items
    )


def _engine_panel(stats: dict, by_category: dict, history: list[dict]) -> str:
    """Operator metrics, deliberately collapsed and last.

    Real and worth publishing — they're the evidence the pipeline works — but
    they answer "is the engine healthy", not "where do I apply".
    """
    latency = stats.get("detection_latency") or {}
    lat = (
        f"{latency['median_minutes']:.0f} min median"
        + (f" · {latency['p95_minutes']:.0f} min p95" if latency.get("p95_minutes") else "")
        + f" (n={latency.get('sample_size', 0)})"
        if latency.get("median_minutes") is not None and latency.get("sample_size", 0) >= 5
        else "calibrating — needs more roles with exact source timestamps"
    )
    life = stats.get("posting_lifetime") or {}
    lifetime = (
        f"{life['median_days']:.0f} days (n={life.get('sample_size', 0)})"
        if life.get("median_days") is not None and life.get("sample_size", 0) >= 5
        else "calibrating"
    )
    partial = stats.get("snapshots_partial") or 0
    facts = [
        ("Boards polled",
         f"{stats.get('fetched_ok', 0):,} of {stats.get('companies_total', 0):,} returned "
         f"successfully ({int(stats.get('fetch_success_rate', 0) * 100)}% of those "
         f"attempted, {int(stats.get('fetch_success_rate_registry', 0) * 100)}% of the "
         "full registry)"),
        ("Complete snapshots",
         f"{stats.get('snapshots_complete', 0):,} boards returned a provably complete "
         f"list; {partial} were capped by the ATS and so were not allowed to close "
         "any role this run"),
        ("Detection latency", lat),
        ("Median posting lifetime", lifetime),
        ("Quarantined boards", str(stats.get("quarantined", 0))),
        ("New this run", str(stats.get("new_this_run", 0))),
        ("Run duration", f"{stats.get('duration_seconds', 0)}s"),
    ]
    rows = "".join(
        f"<tr><th>{escape(k)}</th><td>{escape(v)}</td></tr>" for k, v in facts
    )
    return f"""
  <details class="engine" id="engine">
    <summary><strong>Engine health</strong> — how this list was actually built</summary>
    <div class="tscroll"><table class="kv">{rows}</table></div>
    <div class="panels">
      <div><h3>Roles by source</h3>{_bars(stats.get("roles_by_source", {}))}</div>
      <div><h3>Roles by cycle</h3>{_bars(stats.get("roles_by_cycle", {}))}</div>
      <div><h3>Roles by category</h3>{_bars(by_category)}</div>
      <div><h3>Sponsorship verdicts</h3>{_bars(stats.get("sponsorship_counts", {}))}</div>
    </div>
    {_sparkline(history)}
  </details>
"""


def _bars(counter: dict) -> str:
    if not counter:
        return "<p class='muted'>none</p>"
    top = max(counter.values())
    rows = []
    for name, n in sorted(counter.items(), key=lambda kv: -kv[1]):
        pct = int(n / top * 100) if top else 0
        rows.append(
            f'<div class="bar"><span class="bname">{escape(str(name))}</span>'
            f'<span class="btrack"><span class="bfill" style="width:{pct}%"></span></span>'
            f'<span class="bval">{n}</span></div>'
        )
    return "".join(rows)


def _history_points(limit: int = 120) -> list[dict]:
    points = []
    try:
        with open(paths.HISTORY_PATH, encoding="utf-8") as f:
            for line in f.read().splitlines()[-limit:]:
                try:
                    points.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        pass
    return points


def _sparkline(points: list[dict]) -> str:
    """Inline SVG of open-role count across recent runs. No JS, no deps."""
    values = [p.get("open", 0) for p in points]
    if len(values) < 2:
        return "<p class='muted'>History chart appears after a few more runs.</p>"
    w, h, pad = 640, 80, 4
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    step = (w - 2 * pad) / (len(values) - 1)
    coords = [
        f"{pad + i * step:.1f},{h - pad - (v - lo) / span * (h - 2 * pad):.1f}"
        for i, v in enumerate(values)
    ]
    first_ts = (points[0].get("ts") or "")[:10]
    return (
        f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" class="spark" role="img" '
        f'aria-label="Open roles per run">'
        f'<polyline fill="none" stroke="var(--accent)" stroke-width="2" points="{" ".join(coords)}"/>'
        "</svg>"
        f'<p class="muted spark-caption">Open roles per run since {escape(first_ts)} — '
        f"now {values[-1]}, peak {hi}.</p>"
    )


def _visa_filters(us_context: bool) -> str:
    """The sponsorship dropdown - US visa language, so US lists only."""
    if not us_context:
        return ""
    return (
        '<select id="spon" title="What the posting itself says about visa '
        'sponsorship">'
        '<option value="">Any sponsorship status</option>'
        '<option value="no-restriction">No explicit restriction found</option>'
        '<option value="offers">Explicitly offers sponsorship</option>'
        '<option value="unknown">Sponsorship not stated</option>'
        '<option value="restricted">Explicitly restricted (🇺🇸 / 🛂)</option>'
        "</select>"
    )


def _h1b_filter(us_context: bool) -> str:
    if not us_context:
        return ""
    return ('<label class="chk"><input id="h1b" type="checkbox">'
            "<span>✓ proven H-1B sponsors only</span></label>")


def _visa_legend(us_context: bool) -> str:
    if not us_context:
        return ""
    return (
        "Sponsorship flags are auto-detected from posting text — treat them "
        "as a strong hint and verify on the posting itself. ✓ = USCIS "
        f"approved {h1b.BADGE_THRESHOLD}+ H-1B petitions for that employer "
        f"({escape(h1b.window_label() or 'recent years')}, per the public "
        '<a href="https://www.uscis.gov/tools/reports-and-studies/h-1b-employer-data-hub">'
        "Employer Data Hub</a>) — a history, not a promise; no ✓ only "
        "means no confident match."
    )


def _rows(open_jobs: list[dict], us_context: bool = True) -> str:
    window = h1b.window_label()
    rows = []
    for r in open_jobs:
        posted = (r.get("posted_at") or "")[:10] or "—"
        url = r.get("url") or ""
        apply = f'<a href="{escape(url)}" target="_blank" rel="noopener">Apply</a>' if url else "—"
        sponsor = r.get("sponsorship", "unknown")
        flag = sponsorship.flag(sponsor) if us_context else ""
        approvals = h1b.approvals_for(r.get("company") or "")
        proven = "1" if us_context and h1b.badge(approvals) else "0"
        check = (
            f' <span class="ok" title="~{h1b.pretty_count(approvals)} H-1B approvals '
            f'({escape(window)}, USCIS)">✓</span>' if proven == "1" else ""
        )
        salary = r.get("salary") or ""
        skills = [s for s in (r.get("skills") or []) if s][:6]
        chips = (
            '<span class="sks">'
            + "".join(f'<span class="sk">{escape(s)}</span>' for s in skills)
            + "</span>"
        ) if skills else ""
        haystack = " ".join(
            [str(r.get(k) or "") for k in
             ("company", "title", "location", "category", "season", "salary")]
            + skills
        ).lower()
        seasons = r.get("seasons") or [r.get("season", "")]
        if r.get("season_inferred"):
            # Deliberately not a cycle. The old "~Summer 2027" here was a
            # posting-date guess that the postings themselves confirmed 0/60
            # times, so there is nothing honest to put in this cell but the
            # absence of a claim.
            cycle_tag = (
                "<span class='tag tag-guess' title='This posting never states a "
                "cycle — in its title or its text. We are not guessing one.'>"
                "not stated</span>"
            )
        else:
            cycle_tag = "".join(
                f"<span class='tag' title='Stated by the employer'>{escape(s)}</span>"
                for s in seasons
            )
        remote = "1" if filters.is_remote(r.get("location") or "",
                                          r.get("title") or "") else "0"
        program = filters.program_type(r.get("title") or "")
        jid = r.get("id") or ""
        # No account, no server: the star writes to this browser's localStorage.
        save = (f'<button class="star" type="button" data-id="{escape(jid)}" '
                f'aria-label="Save this role" title="Save to your list">☆</button>')
        # The employer opened this exact job more than once (Copart has eight
        # live "Software Engineering Intern, Dallas" requisitions). One row
        # that says so, with every requisition still one click away.
        openings = r.get("openings") or 1
        extra_urls = [u for u in (r.get("opening_urls") or []) if u][:6]
        if openings > 1:
            apply = " ".join(
                [apply] + [
                    f'<a href="{escape(u)}" target="_blank" rel="noopener" '
                    f'title="Requisition {i + 2} of {openings}">#{i + 2}</a>'
                    for i, u in enumerate(extra_urls)
                ]
            )
        count_tag = (
            f'<span class="opens" title="This employer has {openings} separate '
            f'requisitions open for this same role and location — each one is a '
            f'real application">{openings} openings</span>'
        ) if openings > 1 else ""
        loc = escape((r.get("location") or "")[:48])
        # Sits beside the H-1B check in the company cell, mirroring the README
        # exactly — one vocabulary and one position across both surfaces.
        rmark = ("<span class='rmark' title='Remote — this role. The posting's "
                 "location or title says so.'>R</span>") if remote == "1" else ""
        rows.append(
            f'<tr data-id="{escape(jid)}" '
            f'data-cycle="{escape(r.get("season", ""))}" '
            f'data-cycles="{escape("|".join(seasons))}" '
            f'data-category="{escape(r.get("category", ""))}" '
            f'data-sponsor="{escape(sponsor)}" '
            f'data-h1b="{proven}" '
            f'data-remote="{remote}" '
            f'data-program="{escape(program)}" '
            f'data-posted="{escape(posted if posted != "—" else "")}" '
            f'data-inferred="{"1" if r.get("season_inferred") else "0"}" '
            f'data-openings="{openings}" '
            f'data-ids="{escape("|".join(r.get("opening_ids") or [jid]))}" '
            f'data-text="{escape(haystack)}">'
            f"<td class='c-save'>{save}</td>"
            f"<td>{escape(r.get('company', ''))}{check}{rmark}</td>"
            f"<td><span class='rt'>{escape(r.get('title', ''))}</span> "
            f"{flag}{count_tag}{chips}</td>"
            f"<td>{cycle_tag}</td>"
            f"<td>{escape(r.get('category', ''))}</td>"
            f"<td>{loc}</td>"
            f"<td class='muted'>{escape(salary[:36])}</td>"
            f"<td class='nowrap'>{escape(posted)}</td>"
            f"<td>{apply}</td>"
            "</tr>"
        )
    return "".join(rows)


def _options(values: list[str]) -> str:
    return "".join(f'<option value="{escape(v)}">{escape(v)}</option>' for v in values)


_CF_TITLE = {
    "verified": "The employer's own posted date, read from their careers API. We may have discovered the role after it went live — the date is theirs, not our discovery time.",
    "window": "Hand-verified typical opening month for this company (month-level, not a promise of the day).",
    "rolling": "This company posts year-round / on a rolling basis — worth checking anytime.",
}


def _radar_rows(rows: list[dict]) -> str:
    out = []
    for r in rows:
        if r["status"] == "open":
            status = (f'<a href="{escape(r["url"])}" target="_blank" rel="noopener">✅ open now</a>'
                      if r["url"] else "✅ open now")
        elif r["status"] == "dropped":
            status = '<span class="muted">🗓️ dropped</span>'
        else:
            status = '<span class="muted">⏳ waiting</span>'
        conf = r.get("confidence", "estimated")
        cf = (f'<span class="cf cf-{conf}" title="{escape(_CF_TITLE.get(conf, ""))}">'
              f'{escape(radar.confidence_note(r))}</span>')
        mark = "🎯 " if r.get("source") == "engine" else ""
        out.append(
            f'<tr data-text="{escape(r["company"].lower())}">'
            f"<td>{mark}{escape(r['company'])}</td>"
            f"<td>{escape(radar.pretty_last(r))}</td>"
            f"<td>{escape(radar.pretty_expected(r))}</td>"
            f"<td>{cf}</td>"
            f"<td>{status}</td></tr>"
        )
    return "".join(out)


def _radar_section(store_data: dict, cfg: dict, data_as_of: datetime | None = None) -> str:
    # data/known_windows.json seeds the radar with US marquee employers, and
    # radar.rows() emits them whether or not the store holds a US role. Off a
    # US list that is a forecast for companies this page doesn't even track.
    if not config.want_us(cfg):
        return ""
    cycle = config.cycles(cfg)[0]
    rows = radar.rows(store_data, cycle, today=data_as_of.date() if data_as_of else None)
    if not rows:
        return ""
    return f"""
  <h2 id="radar">📅 Drop Radar — when companies usually post
    (<span id="rcount">{len(rows)}</span>)</h2>
  <p class="muted" style="margin:0 0 8px">When each company usually opens — every
  date either read from the employer's own API or hand-checked.
  <span class="cf cf-verified">from the API</span> = the employer's own
  posted date, read from their careers API (🎯); <span class="cf cf-window">typical window</span> =
  hand-checked opening month for a marquee name;
  <span class="cf cf-rolling">rolling</span> = posts year-round.
  "waiting" = not seen in our tracked feeds yet.</p>
  <p style="margin:0 0 10px"><a href="radar.ics" class="ics">📅 Subscribe in your
    calendar</a> <span class="muted" style="font-size:12px">— add every expected
    drop date to Google/Apple Calendar and get a reminder a week before.</span></p>
  <div class="filters"><input id="rq" type="search"
    placeholder="Search the radar — is your target company on it?" autocomplete="off"></div>
  <div class="tscroll">
  <table><thead><tr><th>Company</th><th>Typical opening</th><th>Expected</th>
  <th>Confidence</th><th>Status</th>
  </tr></thead><tbody id="rrows">{_radar_rows(rows)}</tbody></table>
  </div>
"""


def _signup_section(cfg: dict) -> str:
    """Privacy-preserving double-opt-in request through a narrow RPC."""
    endpoint = config.signup_endpoint(cfg)
    if not endpoint:
        return ""
    url, key = endpoint
    return f"""
  <div class="signup" id="subscribe">
    <h2>📬 Daily email alerts</h2>
    <p class="muted" style="margin:4px 0 10px">One email a day, only when new
    internships actually appeared. Confirm by email first; address never shared.</p>
    <form id="subform">
      <input id="subemail" type="email" required placeholder="you@school.edu" autocomplete="email">
      <button type="submit">Subscribe</button>
    </form>
    <p id="submsg" class="muted" role="status"></p>
  </div>
<script>
(function () {{
  var form = document.getElementById('subform'), email = document.getElementById('subemail'),
      msg = document.getElementById('submsg');
  form.addEventListener('submit', function (ev) {{
    ev.preventDefault();
    msg.textContent = 'Subscribing…';
    fetch({json.dumps(url)} + '/rest/v1/rpc/request_email_subscription', {{
      method: 'POST',
      headers: {{ 'apikey': {json.dumps(key)}, 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ address: email.value.trim().toLowerCase() }})
    }}).then(function (r) {{
      if (r.ok) {{ msg.textContent = 'Check your inbox. If that address can subscribe, a confirmation link is on its way.'; form.reset(); }}
      else {{ msg.textContent = 'Hmm, that did not work — try again in a minute.'; }}
    }}).catch(function () {{ msg.textContent = 'Network error — try again in a minute.'; }});
  }});
}})();
</script>"""


def generate(store_data: dict, stats: dict) -> None:
    open_jobs = [r for r in store_data.values() if r.get("is_open")]
    open_jobs.sort(
        key=lambda r: ((r.get("posted_at") or "")[:10], (r.get("first_seen_at") or "")),
        reverse=True,
    )
    # One row per job, not per requisition. `open_jobs` stays the full list —
    # every count on this page is still a count of real openings — but the
    # table shows an employer's eight identical Dallas reqs as one row saying
    # "8 openings" instead of eight rows a reader has to scroll past.
    display_jobs = grouping.group(open_jobs)
    cfg = config.load_config()
    try:
        data_as_of_dt = datetime.strptime(
            (stats.get("fetched_at") or stats.get("generated_at") or "")[:19],
            "%Y-%m-%dT%H:%M:%S",
        ).replace(tzinfo=UTC)
    except ValueError:
        data_as_of_dt = datetime.now(UTC)
    data_as_of = data_as_of_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    updated = data_as_of_dt.strftime("%b %d, %Y at %H:%M UTC")
    region = config.region_label(cfg)
    if config.include_international(cfg) and config.restrict_region(cfg):
        region = f"{region} + International"
    # Every H-1B / visa control below is built on US immigration data.
    us_context = config.want_us(cfg)

    # Real cycles first, "Not stated" pinned last — it's the absence of a
    # cycle, so alphabetical order (which drops it between Fall and Summer)
    # would read as if it were one.
    cycles = sorted(
        {r.get("season", "") for r in open_jobs if r.get("season")},
        key=lambda s: (s == filters.NOT_STATED, s),
    )
    categories = sorted({r.get("category", "") for r in open_jobs if r.get("category")})
    cycles_phrase = " & ".join(config.cycles(cfg))
    repo = config.repo_slug()
    proven_roles = sum(
        1 for r in open_jobs
        if h1b.badge(h1b.approvals_for(r.get("company") or ""))
    )
    by_category: dict[str, int] = {}
    for r in open_jobs:
        cat = r.get("category") or "Other"
        by_category[cat] = by_category.get(cat, 0) + 1

    html_doc = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Internship Engine - Live Dashboard</title>
<meta name="description" content="{escape(cycles_phrase)} tech internships in {escape(region)}, refreshed every 30 minutes. Live search, filters and email alerts.">
<meta property="og:title" content="Internship Engine - Live Dashboard">
<meta property="og:description" content="{len(open_jobs)} open tech internships in {escape(region)}, refreshed every 30 minutes, straight from each employer's own job board.">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/atom+xml" title="New internships" href="feed.xml">
<style>
  :root {{ --bg:#0b0e14; --card:#141922; --raise:#1b212c; --line:#2a313d;
           --line-soft:#222833;
           --txt:#e8eef6; --muted:#8b96a8; --accent:#4d9dff; --accent-deep:#2f81f7;
           --green:#3fb950; --star:#e3b341;
           --r:14px; --r-sm:9px;
           --shadow:0 1px 2px #0006, 0 8px 24px -12px #000a;
           --shadow-lift:0 2px 4px #0007, 0 16px 32px -14px #000c;
           --ease:cubic-bezier(.2,.7,.3,1); }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--txt);
          font:15px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
          -webkit-text-size-adjust:100%; -webkit-font-smoothing:antialiased;
          /* A single soft light source at the top so the page has a horizon
             instead of reading as one flat slab of #0d1117. */
          background-image:radial-gradient(1100px 420px at 50% -140px,#1b2534 0%,transparent 70%);
          background-repeat:no-repeat; }}
  .wrap {{ max-width:1160px; margin:0 auto; padding:40px 20px 72px; }}
  .top {{ margin-bottom:22px; }}
  h1 {{ font-size:33px; line-height:1.15; margin:0 0 7px; letter-spacing:-.028em;
        font-weight:760;
        background:linear-gradient(180deg,#fff,#b9c6d8);
        -webkit-background-clip:text; background-clip:text; color:transparent; }}
  .sub {{ color:var(--muted); margin:0 0 8px; max-width:62ch; }}
  .links {{ margin:0; font-size:13.5px; color:var(--muted); }}
  .links a {{ transition:color .15s var(--ease); }}
  /* Hero: four applicant-facing numbers. auto-fit with a 2-col floor keeps
     phones at 2x2 instead of a ragged orphan row. */
  .hero {{ display:grid; gap:12px; margin:0 0 34px;
           grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); }}
  .hcard {{ position:relative; overflow:hidden;
            background:linear-gradient(180deg,var(--raise),var(--card));
            border:1px solid var(--line); border-radius:var(--r);
            padding:18px 18px 16px; box-shadow:var(--shadow);
            transition:transform .2s var(--ease), box-shadow .2s var(--ease),
                       border-color .2s var(--ease); }}
  /* A 1px specular line along the top edge — the cheapest way to make a flat
     card read as a lit surface rather than a rectangle. */
  .hcard::before {{ content:""; position:absolute; inset:0 0 auto; height:1px;
      background:linear-gradient(90deg,transparent,#ffffff26 30%,#ffffff26 70%,transparent); }}
  .hcard:hover {{ transform:translateY(-2px); box-shadow:var(--shadow-lift);
                  border-color:#3a4453; }}
  .hnum {{ font-size:35px; font-weight:760; line-height:1; letter-spacing:-.035em;
           background:linear-gradient(180deg,#fff,#c3cfdf);
           -webkit-background-clip:text; background-clip:text; color:transparent; }}
  .hlbl {{ font-size:14px; font-weight:600; margin-top:8px; letter-spacing:-.005em; }}
  .hsub {{ color:var(--muted); font-size:12.5px; margin-top:3px; line-height:1.45; }}
  @media(max-width:560px) {{
    h1 {{ font-size:25px; }}
    .hero {{ grid-template-columns:1fr 1fr; gap:9px; }}
    .hcard {{ padding:13px; border-radius:11px; }}
    .hnum {{ font-size:26px; }}
    .hsub {{ display:none; }}   /* the label carries it at this width */
  }}
  h2 {{ font-size:19px; margin:34px 0 10px; letter-spacing:-.01em; }}
  h3 {{ font-size:14px; margin:16px 0 6px; color:var(--txt); }}
  .note {{ font-size:12.5px; margin:8px 0 0; max-width:76ch; }}
  .empty {{ margin:20px 0; }}
  .panels {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  @media(max-width:680px) {{ .panels {{ grid-template-columns:1fr; }} }}
  .bar {{ display:flex; align-items:center; gap:10px; margin:6px 0; font-size:13px; }}
  .bname {{ width:120px; color:var(--muted); }}
  .btrack {{ flex:1; height:8px; background:#21262d; border-radius:6px; overflow:hidden; }}
  .bfill {{ display:block; height:100%; background:var(--accent); }}
  .bval {{ width:36px; text-align:right; }}
  .spark {{ width:100%; height:80px; display:block; background:var(--card);
            border:1px solid var(--line); border-radius:10px; }}
  .spark-caption {{ font-size:12px; margin:6px 0 0; }}
  .chart {{ width:100%; height:auto; display:block; background:var(--card);
            border:1px solid var(--line); border-radius:10px; }}
  .cbar {{ cursor:default; }}
  .cbar:hover {{ filter:brightness(1.25); }}
  .cvalue {{ fill:var(--txt); font-size:11px; font-weight:600; }}
  .clabel {{ fill:var(--muted); font-size:10px; }}
  #tip {{ position:fixed; display:none; background:#1c2128; color:var(--txt);
          border:1px solid var(--line); border-radius:6px; padding:4px 9px;
          font-size:12px; pointer-events:none; z-index:10; white-space:nowrap; }}
  /* The filter bar sticks: on a long list you can retarget the search without
     scrolling back to the top. */
  .filters {{ display:flex; flex-wrap:wrap; gap:8px; margin:10px 0 4px;
      align-items:center; position:sticky; top:0; z-index:5;
      background:color-mix(in srgb,var(--bg) 88%,transparent);
      -webkit-backdrop-filter:blur(12px); backdrop-filter:blur(12px);
      padding:10px 0; border-bottom:1px solid var(--line); }}
  .filters input[type=search], .filters select, .ghost {{
      background:var(--card); color:var(--txt); border:1px solid var(--line);
      border-radius:var(--r-sm); padding:8px 11px; font-size:13.5px;
      transition:border-color .15s var(--ease), background .15s var(--ease),
                 box-shadow .15s var(--ease), transform .12s var(--ease); }}
  .filters input[type=search] {{ flex:1 1 240px; min-width:180px; }}
  .filters select {{ cursor:pointer; }}
  .filters select:hover, .ghost:hover, .filters input[type=search]:hover {{
      border-color:#3f4a5a; background:var(--raise); }}
  .filters input[type=search]:focus, .filters select:focus, .ghost:focus-visible,
  .star:focus-visible {{ outline:none; border-color:var(--accent);
      box-shadow:0 0 0 3px #4d9dff33; }}
  .star:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px;
      border-radius:6px; }}
  /* Buttons get a real pressed state — a control that doesn't move on click
     reads as broken on touch, where there's no hover to confirm the hit. */
  .ghost {{ cursor:pointer; color:var(--muted); font-weight:500; }}
  .ghost:hover {{ color:var(--txt); }}
  .ghost:active {{ transform:translateY(1px); }}
  .filters label.chk {{ color:var(--muted); font-size:13px; display:flex;
      align-items:center; gap:7px; cursor:pointer; white-space:nowrap;
      padding:8px 11px; border:1px solid transparent; border-radius:var(--r-sm);
      transition:color .15s var(--ease), background .15s var(--ease),
                 border-color .15s var(--ease); }}
  .filters label.chk:hover {{ color:var(--txt); background:var(--card);
      border-color:var(--line); }}
  .filters label.chk input {{ accent-color:var(--accent-deep); cursor:pointer;
      width:15px; height:15px; margin:0; }}
  /* Secondary filters: a disclosure on phones, always-open and inline above it.
     `display:contents` lets the inner controls join the .filters flex row, so
     desktop looks like one continuous bar rather than a nested box.
     The element ships `open` — a CLOSED <details> hides its children through
     the UA stylesheet in a way `display:contents` can't override, so the
     desktop filters would silently vanish. A width check below collapses it
     on phones instead. */
  /* `display:contents` was the original approach here and it silently does
     NOT work on <details> in Chromium — the element keeps its own block box,
     so every secondary control rendered full-width on its own line instead of
     joining the bar. Making .fbody a flex row of its own gets the intended
     layout without depending on that behaviour. */
  .more {{ width:100%; }}
  .more > summary {{ display:none; }}
  .more > .fbody {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
  @media(max-width:680px) {{
    .more > summary {{ display:list-item; cursor:pointer; color:var(--muted);
        font-size:13px; padding:6px 0; list-style-position:inside; }}
    .more > summary:hover {{ color:var(--txt); }}
    .more > .fbody {{ padding:8px 0 2px; }}
    .more:not([open]) > .fbody {{ display:none; }}
  }}
  /* A wide table must scroll inside its OWN box. Without this the 9-column
     job table set the page width, so at 390px the document came out 731px
     wide and the whole dashboard scrolled sideways on a phone. */
  .tscroll {{ overflow-x:auto; -webkit-overflow-scrolling:touch; margin-top:8px;
              border:1px solid var(--line); border-radius:var(--r);
              box-shadow:var(--shadow); background:var(--card); }}
  table {{ width:100%; border-collapse:collapse; font-size:13.5px; }}
  th,td {{ text-align:left; padding:11px 13px;
           border-bottom:1px solid var(--line-soft); vertical-align:top; }}
  tbody tr:last-child td {{ border-bottom:0; }}
  tbody tr {{ transition:background .13s var(--ease); }}
  tbody tr:hover {{ background:#ffffff0b; }}
  thead th {{ position:sticky; top:0; z-index:1; background:var(--raise);
              border-bottom:1px solid var(--line);
              text-transform:uppercase; font-size:11px; letter-spacing:.05em; }}
  .rt {{ font-weight:600; }}
  .nowrap {{ white-space:nowrap; }}
  .c-save {{ width:34px; padding-right:0; }}
  .star {{ background:none; border:0; color:#55606f; font-size:17px;
           cursor:pointer; padding:0 2px; line-height:1;
           transition:color .15s var(--ease), transform .15s var(--ease); }}
  .star:hover {{ color:var(--star); transform:scale(1.22); }}
  .star:active {{ transform:scale(.9); }}
  .star.on {{ color:var(--star); text-shadow:0 0 12px #e3b34166; }}
  /* Saved rows carry a gold edge instead of only a wash, so they're findable
     while scrolling a long list. */
  tr.saved {{ background:#e3b3410f; box-shadow:inset 2px 0 0 var(--star); }}
  .pill {{ display:inline-block; background:#2ea04322; color:var(--green);
           border-radius:20px; padding:0 7px; font-size:11px; margin-left:4px; }}
  /* The remote marker, beside the H-1B check. A filled rounded square so it
     reads as a badge at a glance rather than a stray capital letter — the
     same shape the README's 🆁 glyph has. Tabular-figure font keeps the R
     optically centred in the box. */
  .rmark {{ display:inline-flex; align-items:center; justify-content:center;
            width:17px; height:17px; vertical-align:-3px;
            background:var(--green); color:#07240f; border-radius:5px;
            font:700 11px/1 ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace;
            letter-spacing:0; margin-left:6px; cursor:help;
            box-shadow:0 0 0 1px #2ea04355; }}
  @media(max-width:680px) {{
    /* Give the columns room to be readable while scrolling, rather than
       squeezing nine of them into 390px and wrapping every title to four
       lines. The box scrolls; the page never does. */
    .tscroll table {{ min-width:940px; }}
    .tscroll td:nth-child(2) {{ min-width:150px; }}  /* company */
    .tscroll td:nth-child(3) {{ min-width:230px; }}  /* role */
    .filters {{ position:static; }}   /* a sticky bar this tall eats the screen */
    /* Every line before the first job is a line the reader has to scroll past. */
    .note-long {{ display:none; }}
    .wrap {{ padding-top:26px; }}
  }}
  th {{ color:var(--muted); font-weight:600; }}
  a {{ color:var(--accent); text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .tag {{ display:inline-block; background:#1f6feb26; color:#8ecbff;
          border:1px solid #1f6feb3d; padding:1px 8px;
          border-radius:20px; font-size:12px; margin:0 2px 2px 0; white-space:nowrap; }}
  .tag-guess {{ background:#8b949e14; color:var(--muted); border:1px dashed #3a4453; }}
  .engine {{ margin-top:38px; border:1px solid var(--line); border-radius:var(--r);
             background:var(--card); padding:0 18px; box-shadow:var(--shadow);
             transition:border-color .15s var(--ease); }}
  .engine:hover {{ border-color:#3a4453; }}
  .engine[open] {{ padding-bottom:16px; }}
  .engine summary {{ cursor:pointer; padding:15px 0; font-size:14.5px;
                     font-weight:550; transition:color .15s var(--ease); }}
  .engine summary:hover {{ color:var(--accent); }}
  .kv th {{ width:200px; font-weight:600; color:var(--muted); }}
  .kv td {{ color:var(--txt); }}
  /* "3 openings" — a fact about the employer's board, not a status of ours,
     so it is a quiet outline rather than another coloured pill competing
     with the cycle tags. */
  .opens {{ display:inline-block; border:1px solid #d2992255; color:#e3b341;
            background:#d2992214; padding:0 7px; border-radius:20px;
            font-size:11.5px; margin-left:6px; white-space:nowrap; cursor:help; }}
  .sks {{ display:block; margin-top:3px; }}
  .sk {{ display:inline-block; background:#8b949e1a; color:var(--muted);
         border:1px solid var(--line); padding:0 6px; border-radius:10px;
         font-size:11px; margin:1px 3px 0 0; }}
  .cf {{ padding:2px 9px; border-radius:20px; font-size:11.5px; white-space:nowrap;
         border:1px solid transparent; }}
  .ics {{ display:inline-block; padding:9px 16px; font-size:13px; }}
  .cf-verified {{ background:#2ea04322; color:var(--green); border-color:#2ea04340; }}
  .cf-window {{ background:#1f6feb22; color:#8ecbff; border-color:#1f6feb40; }}
  .cf-rolling {{ background:#8b949e1c; color:var(--muted); border-color:#8b949e33; }}
  .muted {{ color:var(--muted); }}
  .ok {{ color:var(--green); cursor:help; }}
  .signup {{ background:linear-gradient(180deg,var(--raise),var(--card));
             border:1px solid var(--line); border-radius:var(--r);
             padding:20px; margin:26px 0 6px; box-shadow:var(--shadow);
             position:relative; overflow:hidden; }}
  .signup::before {{ content:""; position:absolute; inset:0 0 auto; height:1px;
      background:linear-gradient(90deg,transparent,#ffffff26 30%,#ffffff26 70%,transparent); }}
  .signup h2 {{ margin:0; }}
  .signup form {{ display:flex; gap:9px; flex-wrap:wrap; }}
  .signup input[type=email] {{ flex:1; min-width:220px; background:var(--bg);
      color:var(--txt); border:1px solid var(--line); border-radius:var(--r-sm);
      padding:10px 13px; font-size:14px;
      transition:border-color .15s var(--ease), box-shadow .15s var(--ease); }}
  .signup input[type=email]:focus {{ outline:none; border-color:var(--accent);
      box-shadow:0 0 0 3px #4d9dff33; }}
  /* Primary action: gradient + a lifted shadow in the accent's own hue, so it
     reads as the one thing on the page you're meant to press. */
  .signup button, .ics {{
      background:linear-gradient(180deg,var(--accent),var(--accent-deep));
      color:#fff; border:0; border-radius:var(--r-sm);
      padding:10px 20px; font-size:14px; font-weight:650; cursor:pointer;
      box-shadow:0 1px 2px #0006, 0 6px 16px -8px #2f81f7cc;
      transition:transform .15s var(--ease), box-shadow .15s var(--ease),
                 filter .15s var(--ease); }}
  .signup button:hover, .ics:hover {{ transform:translateY(-1px); filter:brightness(1.08);
      box-shadow:0 2px 4px #0007, 0 12px 22px -8px #2f81f7; text-decoration:none; }}
  .signup button:active, .ics:active {{ transform:translateY(0); filter:brightness(.97);
      box-shadow:0 1px 2px #0008; }}
  footer {{ color:var(--muted); font-size:12px; margin-top:36px; }}
  /* Anyone who asked the OS to stop animations gets no transforms at all. */
  @media (prefers-reduced-motion:reduce) {{
    * {{ transition-duration:.01ms !important; animation-duration:.01ms !important; }}
    .hcard:hover, .signup button:hover, .ics:hover {{ transform:none; }}
  }}
</style></head><body><div class="wrap">
  <header class="top">
    <h1>{escape(region)} tech internships</h1>
    <p class="sub">Read straight from {stats.get('companies_total', 0):,} employer
    job boards. Data as of {escape(updated)}.</p>
    <p class="links"><a href="feed.xml">RSS</a> · <a href="api/jobs.json">JSON API</a>
    · <a href="internships.csv">CSV</a> ·
    <a href="https://github.com/{escape(repo)}">source</a> ·
    <a href="https://github.com/{escape(repo)}/blob/main/METHODOLOGY.md">methodology</a></p>
  </header>
  <div class="hero">{_hero(stats, open_jobs, proven_roles, us_context)}</div>

  <h2 id="roles">Open roles <span class="muted">(<span id="count">{len(open_jobs)}</span>
    showing)</span></h2>
  <div class="filters" id="filters">
    <input id="q" type="search" placeholder="Search company, role, location, or skill (try “Python”)…" autocomplete="off">
    <select id="cycle"><option value="">All cycles</option>{_options(cycles)}</select>
    <label class="chk" title="Show only the roles you've starred (stored in this browser)">
      <input id="savedonly" type="checkbox"><span>★ saved (<span id="savedn">0</span>)</span></label>
    <!-- Secondary filters. A real <details> so phones get a one-tap disclosure
         instead of seven stacked rows between the hero and the first job; CSS
         forces it open (and hides the summary) from 681px up. -->
    <details class="more" open>
      <summary>More filters</summary>
      <div class="fbody">
        <select id="cat"><option value="">All categories</option>{_options(categories)}</select>
        <select id="age">
          <option value="">Posted anytime</option>
          <option value="2">Last 48 hours</option>
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
        </select>
        {_visa_filters(us_context)}
        <select id="program">
          <option value="">Internships &amp; co-ops</option>
          <option value="Internship">Internships</option>
          <option value="Co-op">Co-ops</option>
        </select>
        <label class="chk"><input id="remote" type="checkbox"><span><span class="rmark">R</span> remote only</span></label>
        {_h1b_filter(us_context)}
        <label class="chk" title="Show only roles whose employer named the cycle themselves">
          <input id="stated" type="checkbox"><span>employer-stated cycle only</span></label>
        <button id="export" class="ghost" type="button" title="Download your saved roles as CSV">
          Export saved</button>
        <button id="reset" class="ghost" type="button">Clear filters</button>
      </div>
    </details>
  </div>
  <p class="muted note">★ saves to <strong>this browser only</strong><span
  class="note-long"> — no account, no sign-in, nothing sent anywhere</span>.
  <span class="tag tag-guess">not stated</span> = the posting names no cycle
  anywhere, so we don't guess one<span class="note-long">; a plain tag is the
  cycle the employer actually stated, in the title or the posting text</span>.</p>
  <div class="tscroll">
  <table><thead><tr><th class="c-save" title="Save"></th><th>Company</th><th>Role</th>
  <th>Cycle</th><th>Category</th>
  <th>Location</th><th>Salary</th><th>Posted</th><th></th></tr></thead>
  <tbody id="rows">{_rows(display_jobs, us_context)}</tbody></table>
  </div>
  <p id="empty" class="muted empty" hidden>No roles match those filters.
    <button class="ghost" type="button" id="reset2">Clear filters</button></p>

  {_signup_section(cfg)}
  {_radar_section(store_data, cfg, data_as_of_dt)}

  <h2>Internships posted per week</h2>
  <p class="muted" style="margin:0 0 8px">Real published dates across every role the
  engine has tracked — watch this spike when {escape(config.cycles(cfg)[0])}
  recruiting opens up.</p>
  {trends.svg_bar_chart(trends.weekly_postings(store_data, now=data_as_of_dt))}

  {_engine_panel(stats, by_category, _history_points())}

  <footer>Generated by the engine on each run across
  {len(stats.get("companies_by_source", {}))} ATS platforms covering {escape(region)}.
  {_visa_legend(us_context)}
  Roles can close at any time; always confirm on the company's own site.</footer>
</div>
<script>
(function () {{
  // spon and h1b are rendered only while US roles are tracked, so every read
  // of those two below has to tolerate a missing element.
  var q = document.getElementById('q'), cycle = document.getElementById('cycle'),
      cat = document.getElementById('cat'), spon = document.getElementById('spon'),
      h1b = document.getElementById('h1b'), age = document.getElementById('age'),
      stated = document.getElementById('stated'),
      program = document.getElementById('program'),
      remote = document.getElementById('remote'),
      savedonly = document.getElementById('savedonly'),
      savedn = document.getElementById('savedn'),
      empty = document.getElementById('empty'),
      rows = Array.prototype.slice.call(document.getElementById('rows').rows),
      count = document.getElementById('count');

  // --- saved roles -----------------------------------------------------------
  // Deliberately localStorage and nothing else: a tracker that needs an account
  // is a tracker most people bounce off, and we have no business holding anyone's
  // application list on a server. Everything here stays in this browser.
  var KEY = 'ie.saved.v1', saved = {{}};
  try {{ saved = JSON.parse(localStorage.getItem(KEY) || '{{}}') || {{}}; }} catch (e) {{ saved = {{}}; }}
  // Remove ids no longer present in the current artifact. Otherwise the badge
  // counts invisible roles that cannot be viewed, exported, or unstarred.
  //
  // A row can stand for several requisitions (an employer that opened the same
  // job three times). Every one of those ids has to count as present, and a
  // star on a requisition that is now represented by a sibling has to MOVE to
  // the surviving row — otherwise folding the display would quietly delete
  // roles a reader had saved.
  var currentIds = {{}};
  rows.forEach(function (tr) {{
    var ids = (tr.dataset.ids || tr.dataset.id).split('|');
    ids.forEach(function (id) {{ currentIds[id] = true; }});
    if (ids.length > 1 && !saved[tr.dataset.id]) {{
      for (var i = 0; i < ids.length; i++) {{
        if (saved[ids[i]]) {{ saved[tr.dataset.id] = saved[ids[i]]; break; }}
      }}
    }}
    ids.forEach(function (id) {{ if (id !== tr.dataset.id) delete saved[id]; }});
  }});
  Object.keys(saved).forEach(function (id) {{ if (!currentIds[id]) delete saved[id]; }});
  function persist() {{
    try {{ localStorage.setItem(KEY, JSON.stringify(saved)); }} catch (e) {{ /* private mode */ }}
  }}
  persist();
  function savedCount() {{ return Object.keys(saved).length; }}
  function paintRow(tr) {{
    var on = !!saved[tr.dataset.id], btn = tr.querySelector('.star');
    if (btn) {{
      btn.textContent = on ? '★' : '☆';
      btn.classList.toggle('on', on);
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    }}
    tr.classList.toggle('saved', on);
  }}
  function paintAll() {{ rows.forEach(paintRow); savedn.textContent = savedCount(); }}

  document.getElementById('rows').addEventListener('click', function (ev) {{
    var btn = ev.target.closest ? ev.target.closest('.star') : null;
    if (!btn) return;
    var tr = btn.closest('tr'), id = tr.dataset.id;
    if (saved[id]) {{ delete saved[id]; }} else {{ saved[id] = Date.now(); }}
    persist(); paintRow(tr); savedn.textContent = savedCount();
    if (savedonly.checked) apply();
  }});

  // Same formula-injection guard the server-side CSV uses: Excel/Sheets execute
  // a cell starting with = + - or @, and these cells are third-party job text.
  // Quoting alone doesn't stop it — the leading apostrophe does.
  function csvCell(v) {{
    var s = String(v == null ? '' : v);
    if (/^[=+\\-@\\t\\r]/.test(s)) s = "'" + s;
    return '"' + s.replace(/"/g, '""') + '"';
  }}
  document.getElementById('export').addEventListener('click', function () {{
    var head = ['company', 'role', 'cycle', 'category', 'location', 'salary', 'posted', 'url'],
        lines = [head.join(',')];
    rows.forEach(function (tr) {{
      if (!saved[tr.dataset.id]) return;
      var td = tr.cells, link = tr.querySelector('a[href]');
      lines.push([td[1], td[2], td[3], td[4], td[5], td[6], td[7]]
        .map(function (c) {{ return csvCell(c.innerText.trim()); }})
        .concat(csvCell(link ? link.href : '')).join(','));
    }});
    if (lines.length === 1) {{ alert('Star a few roles first — then this exports them.'); return; }}
    var blob = new Blob([lines.join('\\n')], {{ type: 'text/csv;charset=utf-8' }}),
        a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'my-saved-internships.csv';
    a.click(); URL.revokeObjectURL(a.href);
  }});

  function cutoffISO(days) {{
    var d = new Date(new Date({json.dumps(data_as_of)}).getTime() - days * 86400000);
    return d.toISOString().slice(0, 10);
  }}
  // What each sponsorship option actually means. The old single "F-1 friendly"
  // checkbox only HID the explicit negatives, so ~97% of what it returned was
  // simply postings that never mention sponsorship — shown to students as if
  // it had been checked. Each verdict is now nameable on its own.
  function sponsorOK(mode, value) {{
    var restricted = (value === 'citizens-only' || value === 'no-sponsorship');
    if (mode === 'no-restriction') return !restricted;
    if (mode === 'offers') return value === 'offers';
    if (mode === 'unknown') return value === 'unknown' || !value;
    if (mode === 'restricted') return restricted;
    return true;
  }}
  function apply() {{
    var text = q.value.trim().toLowerCase(), cy = cycle.value, ca = cat.value,
        sp = spon ? spon.value : '', proven = h1b ? h1b.checked : false, shown = 0,
        minPosted = age.value ? cutoffISO(parseInt(age.value, 10)) : '',
        statedOnly = stated.checked, prog = program.value,
        remoteOnly = remote.checked, onlySaved = savedonly.checked;
    rows.forEach(function (tr) {{
      // A multi-cycle posting matches EVERY cycle it states, so filtering to
      // "Fall 2026" still finds a "Fall 2026/Summer 2027" requisition.
      var cycles = (tr.dataset.cycles || tr.dataset.cycle || '').split('|');
      var ok = (!text || tr.dataset.text.indexOf(text) !== -1)
        && (!cy || cycles.indexOf(cy) !== -1)
        && (!ca || tr.dataset.category === ca)
        && sponsorOK(sp, tr.dataset.sponsor)
        && (!proven || tr.dataset.h1b === '1')
        // "Internship / Co-op" satisfies either filter — the employer said both.
        && (!prog || tr.dataset.program.indexOf(prog) !== -1)
        && (!remoteOnly || tr.dataset.remote === '1')
        && (!onlySaved || !!saved[tr.dataset.id])
        && (!minPosted || (tr.dataset.posted && tr.dataset.posted >= minPosted))
        && (!statedOnly || tr.dataset.inferred === '0');
      tr.style.display = ok ? '' : 'none';
      // Count OPENINGS, not rows. A row standing for eight requisitions is
      // eight jobs you can apply to, and the headline number has to agree
      // with the one in the hero and the JSON API.
      if (ok) shown += parseInt(tr.dataset.openings || '1', 10) || 1;
    }});
    count.textContent = shown;
    empty.hidden = shown !== 0;
  }}
  var controls = [q, cycle, cat, age, spon, program, remote, h1b, stated,
                  savedonly].filter(Boolean);
  controls.forEach(function (el) {{
    el.addEventListener('input', apply); el.addEventListener('change', apply);
  }});
  function reset() {{
    controls.forEach(function (el) {{
      if (el.type === 'checkbox') el.checked = false; else el.value = '';
    }});
    apply();
  }}
  document.getElementById('reset').addEventListener('click', reset);
  document.getElementById('reset2').addEventListener('click', reset);

  // The secondary-filter disclosure ships open so desktop (where its summary is
  // hidden) always shows every control, even with JS off. Phones get it
  // collapsed — but only if the reader hasn't already opened it themselves.
  var more = document.querySelector('.more'), touched = false;
  if (more) {{
    more.addEventListener('toggle', function () {{ touched = true; }});
    var fit = window.matchMedia('(max-width: 680px)');
    function sync() {{ if (!touched) more.open = !fit.matches; }}
    sync();
    (fit.addEventListener ? fit.addEventListener('change', sync)
                          : fit.addListener(sync));
  }}
  paintAll();
  // Radar search (separate list, separate box).
  var rq = document.getElementById('rq');
  if (rq) {{
    var rrows = Array.prototype.slice.call(document.getElementById('rrows').rows),
        rcount = document.getElementById('rcount');
    rq.addEventListener('input', function () {{
      var text = rq.value.trim().toLowerCase(), shown = 0;
      rrows.forEach(function (tr) {{
        var ok = !text || tr.dataset.text.indexOf(text) !== -1;
        tr.style.display = ok ? '' : 'none';
        if (ok) shown++;
      }});
      rcount.textContent = shown;
    }});
  }}
  // Chart hover tooltip: one floating div fed by each bar's data-tip.
  var tip = document.createElement('div'); tip.id = 'tip'; document.body.appendChild(tip);
  document.querySelectorAll('.cbar').forEach(function (bar) {{
    bar.addEventListener('mousemove', function (ev) {{
      tip.textContent = bar.dataset.tip; tip.style.display = 'block';
      tip.style.left = (ev.clientX + 12) + 'px'; tip.style.top = (ev.clientY - 28) + 'px';
    }});
    bar.addEventListener('mouseleave', function () {{ tip.style.display = 'none'; }});
  }});
}})();
</script>
</body></html>"""

    os.makedirs(paths.DOCS_DIR, exist_ok=True)
    with open(paths.DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(html_doc)

    _write_unsubscribe(cfg)
    _write_confirmation(cfg)


def _write_unsubscribe(cfg: dict) -> None:
    """Unsubscribe target for digest emails (?t=<secret token>).

    Calls the security-definer RPC in Supabase: the token is the only
    credential, so the page needs nothing but the public key.

    The RPC fires on a CLICK, never on page load. Corporate mail security
    scanners fetch every link in an incoming email to check it — a page that
    unsubscribed on load meant those subscribers were silently removed by their
    own employer's spam filter, having never opened the mail. Requiring a real
    click is what keeps an automated fetch from being a destructive action.
    """
    endpoint = config.signup_endpoint(cfg)
    if not endpoint:
        return
    url, key = endpoint
    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Unsubscribe - Internship Engine</title>
<style>
  body {{ margin:0; background:#0d1117; color:#e6edf3;
          font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }}
  .box {{ max-width:520px; margin:18vh auto 0; padding:32px 24px; background:#161b22;
          border:1px solid #30363d; border-radius:12px; text-align:center; }}
  a {{ color:#2f81f7; }}
  button {{ background:#2f81f7; color:#fff; border:0; border-radius:8px;
            padding:11px 22px; font-size:15px; font-weight:600; cursor:pointer;
            margin-top:8px; }}
  button:hover {{ filter:brightness(1.1); }}
  button[disabled] {{ opacity:.6; cursor:default; }}
</style></head><body>
<div class="box">
  <h1 id="h">Unsubscribe?</h1>
  <p id="p">Confirm below and you'll stop receiving the daily digest.</p>
  <button id="go">Yes, unsubscribe me</button>
</div>
<script>
(function () {{
  var h = document.getElementById('h'), p = document.getElementById('p'),
      go = document.getElementById('go');
  var token = new URLSearchParams(location.search).get('t');
  if (!token) {{
    h.textContent = 'Missing link token';
    p.textContent = 'Use the unsubscribe link from one of our emails.';
    go.style.display = 'none';
    return;
  }}
  // Deliberately click-gated: mail security scanners fetch every link in an
  // email, and unsubscribing on page load let those scanners remove real
  // subscribers who never even opened the message.
  go.addEventListener('click', function () {{
    go.disabled = true;
    h.textContent = 'Unsubscribing…';
    p.textContent = 'One moment.';
    fetch({json.dumps(url)} + '/rest/v1/rpc/unsubscribe_email', {{
      method: 'POST',
      headers: {{ 'apikey': {json.dumps(key)}, 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ token: token }})
    }}).then(function (r) {{
      go.style.display = 'none';
      if (r.ok) {{
        h.textContent = "You're unsubscribed";
        p.textContent = 'No more emails. You can re-subscribe on the dashboard anytime.';
      }} else {{
        h.textContent = 'Something went wrong';
        p.textContent = 'Try the link again in a minute.';
        go.style.display = ''; go.disabled = false;
      }}
    }}).catch(function () {{
      h.textContent = 'Network error';
      p.textContent = 'Try the link again in a minute.';
      go.disabled = false;
    }});
  }});
}})();
</script>
</body></html>"""
    with open(os.path.join(paths.DOCS_DIR, "unsubscribe.html"), "w", encoding="utf-8") as f:
        f.write(page)


def _write_confirmation(cfg: dict) -> None:
    """Click-gated double-opt-in target; scanners cannot confirm on page load."""
    endpoint = config.signup_endpoint(cfg)
    if not endpoint:
        return
    url, key = endpoint
    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Confirm email alerts - Internship Engine</title>
<style>
  body {{ margin:0; background:#0d1117; color:#e6edf3;
          font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }}
  .box {{ max-width:520px; margin:18vh auto 0; padding:32px 24px; background:#161b22;
          border:1px solid #30363d; border-radius:12px; text-align:center; }}
  button {{ background:#2f81f7; color:#fff; border:0; border-radius:8px;
            padding:11px 22px; font-size:15px; font-weight:600; cursor:pointer; }}
  button[disabled] {{ opacity:.6; cursor:default; }}
</style></head><body><div class="box">
  <h1 id="h">Confirm email alerts?</h1>
  <p id="p">Confirm below to join the daily internship digest.</p>
  <button id="go">Confirm my email</button>
</div><script>
(function () {{
  var h=document.getElementById('h'), p=document.getElementById('p'),
      go=document.getElementById('go'), token=new URLSearchParams(location.search).get('t');
  if (!token) {{ h.textContent='Missing link token'; p.textContent='Use the link from your confirmation email.'; go.style.display='none'; return; }}
  go.addEventListener('click', function () {{
    go.disabled=true; h.textContent='Confirming…'; p.textContent='One moment.';
    fetch({json.dumps(url)} + '/rest/v1/rpc/confirm_email_subscription', {{
      method:'POST', headers:{{'apikey':{json.dumps(key)},'Content-Type':'application/json'}},
      body:JSON.stringify({{token:token}})
    }}).then(function (r) {{
      if (!r.ok) throw new Error('confirm failed');
      h.textContent="You're subscribed"; p.textContent='Your first digest arrives with the next batch of new roles.'; go.style.display='none';
    }}).catch(function () {{ h.textContent='Something went wrong'; p.textContent='Try the link again in a minute.'; go.disabled=false; }});
  }});
}})();
</script></body></html>"""
    with open(os.path.join(paths.DOCS_DIR, "confirm.html"), "w", encoding="utf-8") as f:
        f.write(page)
