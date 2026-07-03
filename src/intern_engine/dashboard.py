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

from . import config, h1b, paths, radar, sponsorship, trends


def _cards(stats: dict, proven_roles: int) -> str:
    latency = stats.get("detection_latency") or {}
    lat = (
        f"{latency['median_minutes']:.0f} min"
        if latency.get("median_minutes") is not None and latency.get("sample_size", 0) >= 5
        else "calibrating"
    )
    life = stats.get("posting_lifetime") or {}
    lifetime = (
        f"{life['median_days']:.0f} days"
        if life.get("median_days") is not None and life.get("sample_size", 0) >= 5
        else "calibrating"
    )
    items = [
        ("Open roles", stats.get("open_total", 0)),
        ("At proven H-1B sponsors ✓", proven_roles),
        ("Companies tracked", f"{stats.get('companies_total', 0):,}"),
        ("ATS sources", len(stats.get("companies_by_source", {}))),
        ("Fetch success", f"{int(stats.get('fetch_success_rate', 0) * 100)}%"),
        ("Quarantined boards", stats.get("quarantined", 0)),
        ("New this run", stats.get("new_this_run", 0)),
        ("Detection latency", lat),
        ("Median posting lifetime", lifetime),
        ("Last run", f"{stats.get('duration_seconds', 0)}s"),
    ]
    return "".join(
        f'<div class="card"><div class="num">{escape(str(v))}</div>'
        f'<div class="lbl">{escape(label)}</div></div>'
        for label, v in items
    )


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


def _rows(open_jobs: list[dict]) -> str:
    window = h1b.window_label()
    rows = []
    for r in open_jobs:
        posted = (r.get("posted_at") or "")[:10] or "—"
        url = r.get("url") or ""
        apply = f'<a href="{escape(url)}" target="_blank" rel="noopener">Apply</a>' if url else "—"
        sponsor = r.get("sponsorship", "unknown")
        flag = sponsorship.flag(sponsor)
        approvals = h1b.approvals_for(r.get("company") or "")
        proven = "1" if h1b.badge(approvals) else "0"
        check = (
            f' <span class="ok" title="~{h1b.pretty_count(approvals)} H-1B approvals '
            f'({escape(window)}, USCIS)">✓</span>' if proven == "1" else ""
        )
        salary = r.get("salary") or ""
        haystack = " ".join(
            str(r.get(k) or "") for k in ("company", "title", "location", "category")
        ).lower()
        rows.append(
            f'<tr data-cycle="{escape(r.get("season", ""))}" '
            f'data-category="{escape(r.get("category", ""))}" '
            f'data-sponsor="{escape(sponsor)}" '
            f'data-h1b="{proven}" '
            f'data-text="{escape(haystack)}">'
            f"<td>{escape(r.get('company', ''))}{check}</td>"
            f"<td>{escape(r.get('title', ''))} {flag}</td>"
            f"<td><span class='tag'>{escape(r.get('season', ''))}</span></td>"
            f"<td>{escape(r.get('category', ''))}</td>"
            f"<td>{escape((r.get('location') or '')[:48])}</td>"
            f"<td class='muted'>{escape(salary[:36])}</td>"
            f"<td>{escape(posted)}</td>"
            f"<td>{apply}</td>"
            "</tr>"
        )
    return "".join(rows)


def _options(values: list[str]) -> str:
    return "".join(f'<option value="{escape(v)}">{escape(v)}</option>' for v in values)


def _radar_rows(rows: list[dict]) -> str:
    out = []
    for r in rows:
        if r["status"] == "posted":
            status = (f'<a href="{escape(r["url"])}" target="_blank" rel="noopener">✅ open now</a>'
                      if r["url"] else "✅ open now")
        else:
            status = '<span class="muted">⏳ waiting</span>'
        out.append(
            f'<tr data-text="{escape(r["company"].lower())}">'
            f"<td>{escape(r['company'])}</td>"
            f"<td>{escape(radar.pretty_last(r))}</td>"
            f"<td>{escape(radar.pretty_expected(r))}</td>"
            f"<td>{status}</td></tr>"
        )
    return "".join(out)


def _radar_section(store_data: dict, cfg: dict) -> str:
    cycle = config.cycles(cfg)[0]
    rows = radar.rows(store_data, cycle)
    if not rows:
        return ""
    return f"""
  <h2 id="radar">📅 Drop Radar — when companies usually post
    (<span id="rcount">{len(rows)}</span>)</h2>
  <p class="muted" style="margin:0 0 8px">Each company's first intern posting last
  cycle, projected one year forward. "by …" = already up when the reference window
  opened; "waiting" = not seen in our tracked feeds yet.</p>
  <div class="filters"><input id="rq" type="search"
    placeholder="Search the radar — is your target company on it?" autocomplete="off"></div>
  <table><thead><tr><th>Company</th><th>Last cycle</th><th>Expected</th><th>Status</th>
  </tr></thead><tbody id="rrows">{_radar_rows(rows)}</tbody></table>
"""


def _signup_section(cfg: dict) -> str:
    """Native email signup: inserts straight into Supabase under RLS (the
    publishable key is public by design; the policy only allows INSERT)."""
    endpoint = config.signup_endpoint(cfg)
    if not endpoint:
        return ""
    url, key = endpoint
    return f"""
  <div class="signup" id="subscribe">
    <h2>📬 Daily email alerts</h2>
    <p class="muted" style="margin:4px 0 10px">One email a day, only when new
    internships actually appeared. Unsubscribe with one click, address never shared.</p>
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
    fetch({json.dumps(url)} + '/rest/v1/email_subscribers', {{
      method: 'POST',
      headers: {{ 'apikey': {json.dumps(key)}, 'Content-Type': 'application/json',
                  'Prefer': 'return=minimal' }},
      body: JSON.stringify({{ email: email.value.trim().toLowerCase() }})
    }}).then(function (r) {{
      if (r.status === 201) {{ msg.textContent = "You're in — first digest lands with the next batch of new roles."; form.reset(); }}
      else if (r.status === 409) {{ msg.textContent = 'That address is already subscribed.'; }}
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
    cfg = config.load_config()
    updated = datetime.now(UTC).strftime("%b %d, %Y at %H:%M UTC")
    if config.include_international(cfg):
        region = "US + International"
    elif config.want_us(cfg):
        region = "United States"
    else:
        region = "Worldwide"

    cycles = sorted({r.get("season", "") for r in open_jobs if r.get("season")})
    categories = sorted({r.get("category", "") for r in open_jobs if r.get("category")})
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
<meta name="description" content="Summer 2027 & Fall 2026 tech internships, refreshed every 2 hours. Auto-detected visa sponsorship flags, proven H-1B sponsor badges, email alerts.">
<meta property="og:title" content="Internship Engine - Live Dashboard">
<meta property="og:description" content="{len(open_jobs)} open tech internships, refreshed every 2 hours. Visa-sponsorship flags + proven H-1B sponsor badges for international students.">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/atom+xml" title="New internships" href="feed.xml">
<style>
  :root {{ --bg:#0d1117; --card:#161b22; --line:#30363d; --txt:#e6edf3;
           --muted:#8b949e; --accent:#2f81f7; --green:#3fb950; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--txt);
          font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:32px 20px 64px; }}
  h1 {{ font-size:26px; margin:0 0 4px; }}
  .sub {{ color:var(--muted); margin:0 0 24px; }}
  .sub a {{ color:var(--accent); }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
           gap:12px; margin-bottom:28px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
           padding:16px; }}
  .num {{ font-size:24px; font-weight:700; }}
  .lbl {{ color:var(--muted); font-size:13px; margin-top:2px; }}
  h2 {{ font-size:16px; margin:26px 0 10px; }}
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
  .filters {{ display:flex; flex-wrap:wrap; gap:10px; margin:10px 0 4px; align-items:center; }}
  .filters input[type=search], .filters select {{
      background:var(--card); color:var(--txt); border:1px solid var(--line);
      border-radius:8px; padding:7px 10px; font-size:13.5px; }}
  .filters input[type=search] {{ flex:1; min-width:180px; }}
  .filters label.chk {{ color:var(--muted); font-size:13px; display:flex;
      align-items:center; gap:6px; cursor:pointer; }}
  table {{ width:100%; border-collapse:collapse; margin-top:8px; font-size:13.5px; }}
  th,td {{ text-align:left; padding:8px 10px; border-bottom:1px solid var(--line);
           vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; }}
  a {{ color:var(--accent); text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .tag {{ background:#1f6feb22; color:#79c0ff; padding:1px 7px; border-radius:20px; font-size:12px; }}
  .muted {{ color:var(--muted); }}
  .ok {{ color:var(--green); cursor:help; }}
  .signup {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
             padding:18px; margin:26px 0 6px; }}
  .signup h2 {{ margin:0; }}
  .signup form {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .signup input[type=email] {{ flex:1; min-width:220px; background:var(--bg);
      color:var(--txt); border:1px solid var(--line); border-radius:8px;
      padding:9px 12px; font-size:14px; }}
  .signup button {{ background:var(--accent); color:#fff; border:0; border-radius:8px;
      padding:9px 18px; font-size:14px; font-weight:600; cursor:pointer; }}
  .signup button:hover {{ filter:brightness(1.1); }}
  footer {{ color:var(--muted); font-size:12px; margin-top:36px; }}
</style></head><body><div class="wrap">
  <h1>Internship Engine - Live Dashboard</h1>
  <p class="sub">{region} tech internships, refreshed automatically. Updated {escape(updated)}.
  <a href="feed.xml">RSS feed</a> · <a href="api/jobs.json">JSON API</a> ·
  <a href="https://github.com/{escape(repo)}">GitHub</a></p>
  <div class="grid">{_cards(stats, proven_roles)}</div>
  {_sparkline(_history_points())}
  {_signup_section(cfg)}
  <h2>Internships posted per week</h2>
  <p class="muted" style="margin:0 0 8px">Real published dates across every role the
  engine has tracked — watch this spike when {escape(config.cycles(cfg)[0])}
  recruiting opens up.</p>
  {trends.svg_bar_chart(trends.weekly_postings(store_data))}
  <div class="panels">
    <div><h2>Roles by source</h2>{_bars(stats.get("roles_by_source", {}))}</div>
    <div><h2>Roles by cycle</h2>{_bars(stats.get("roles_by_cycle", {}))}</div>
    <div><h2>Roles by category</h2>{_bars(by_category)}</div>
    <div><h2>Sponsorship verdicts</h2>{_bars(stats.get("sponsorship_counts", {}))}</div>
  </div>
  <h2>Open roles (<span id="count">{len(open_jobs)}</span>)</h2>
  <div class="filters">
    <input id="q" type="search" placeholder="Search company, role, location…" autocomplete="off">
    <select id="cycle"><option value="">All cycles</option>{_options(cycles)}</select>
    <select id="cat"><option value="">All categories</option>{_options(categories)}</select>
    <label class="chk"><input id="f1" type="checkbox">
      F-1 friendly only (hide 🇺🇸 citizens-only and 🛂 no-sponsorship)</label>
    <label class="chk"><input id="h1b" type="checkbox">
      ✓ proven H-1B sponsors only</label>
  </div>
  <table><thead><tr><th>Company</th><th>Role</th><th>Cycle</th><th>Category</th>
  <th>Location</th><th>Salary</th><th>Posted</th><th></th></tr></thead>
  <tbody id="rows">{_rows(open_jobs)}</tbody></table>
  {_radar_section(store_data, cfg)}
  <footer>Generated by the engine on each run. Companies polled across
  {len(stats.get("companies_by_source", {}))} ATS platforms. Sponsorship flags are
  auto-detected from posting text — verify on the posting itself.
  ✓ = USCIS approved {h1b.BADGE_THRESHOLD}+ H-1B petitions for that employer
  ({escape(h1b.window_label() or "recent years")}, per the public
  <a href="https://www.uscis.gov/tools/reports-and-studies/h-1b-employer-data-hub">
  Employer Data Hub</a>); no ✓ only means no confident match.</footer>
</div>
<script>
(function () {{
  var q = document.getElementById('q'), cycle = document.getElementById('cycle'),
      cat = document.getElementById('cat'), f1 = document.getElementById('f1'),
      h1b = document.getElementById('h1b'),
      rows = Array.prototype.slice.call(document.getElementById('rows').rows),
      count = document.getElementById('count');
  function apply() {{
    var text = q.value.trim().toLowerCase(), cy = cycle.value, ca = cat.value,
        safe = f1.checked, proven = h1b.checked, shown = 0;
    rows.forEach(function (tr) {{
      var ok = (!text || tr.dataset.text.indexOf(text) !== -1)
        && (!cy || tr.dataset.cycle === cy)
        && (!ca || tr.dataset.category === ca)
        && (!safe || (tr.dataset.sponsor !== 'citizens-only'
                      && tr.dataset.sponsor !== 'no-sponsorship'))
        && (!proven || tr.dataset.h1b === '1');
      tr.style.display = ok ? '' : 'none';
      if (ok) shown++;
    }});
    count.textContent = shown;
  }}
  [q, cycle, cat, f1, h1b].forEach(function (el) {{
    el.addEventListener('input', apply); el.addEventListener('change', apply);
  }});
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


def _write_unsubscribe(cfg: dict) -> None:
    """One-click unsubscribe target for digest emails (?t=<secret token>).

    Calls the security-definer RPC in Supabase: the token is the only
    credential, so the page needs nothing but the public key.
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
</style></head><body>
<div class="box"><h1 id="h">Unsubscribing…</h1><p id="p">One moment.</p></div>
<script>
(function () {{
  var h = document.getElementById('h'), p = document.getElementById('p');
  var token = new URLSearchParams(location.search).get('t');
  if (!token) {{ h.textContent = 'Missing link token'; p.textContent =
    'Use the unsubscribe link from one of our emails.'; return; }}
  fetch({json.dumps(url)} + '/rest/v1/rpc/unsubscribe_email', {{
    method: 'POST',
    headers: {{ 'apikey': {json.dumps(key)}, 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ token: token }})
  }}).then(function (r) {{
    if (r.ok) {{ h.textContent = "You're unsubscribed"; p.textContent =
      'No more emails. You can re-subscribe on the dashboard anytime.'; }}
    else {{ h.textContent = 'Something went wrong'; p.textContent =
      'Try the link again in a minute.'; }}
  }}).catch(function () {{ h.textContent = 'Network error'; p.textContent =
    'Try the link again in a minute.'; }});
}})();
</script>
</body></html>"""
    with open(os.path.join(paths.DOCS_DIR, "unsubscribe.html"), "w", encoding="utf-8") as f:
        f.write(page)
