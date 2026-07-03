"""Hiring-trend analytics computed from data we already keep.

Two questions students actually ask, answered from the store instead of vibes:

  1. "When do companies post?"  — weekly posting volume, from each role's real
     published date (posted_at covers ~100% of roles thanks to enrichment).
  2. "How long do I have?"      — median days a posting stays up, from roles
     we watched open AND close (posted_at -> closed_at).

The chart is server-rendered SVG baked into the static dashboard: one series,
one hue (the dashboard accent, validated against the dark surface), thin bars
with rounded data-ends, recessive gridlines, direct labels on the peak and the
latest week only, and a per-bar tooltip layer wired up by the dashboard JS.
"""

from __future__ import annotations

import os
import statistics
from datetime import UTC, datetime, timedelta
from html import escape

from . import paths

_MAX_LIFETIME_DAYS = 180  # beyond this, "closed" is a stale-req artifact, not a signal

# GitHub-native hues, validated (dataviz six checks) against each README surface.
_THEMES = {
    "light": {"accent": "#0969da", "grid": "#d0d7de", "ink": "#57606a", "value": "#24292f"},
    "dark": {"accent": "#2f81f7", "grid": "#30363d", "ink": "#8b949e", "value": "#e6edf3"},
}


def _parse_day(value: str | None) -> datetime | None:
    try:
        return datetime.strptime((value or "")[:10], "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return None


def _week_start(day: datetime) -> datetime:
    return day - timedelta(days=day.weekday())  # Monday


def weekly_postings(store_data: dict, weeks: int = 16, now: datetime | None = None) -> list[tuple[str, int]]:
    """[(monday_iso, roles_posted_that_week)] for the trailing `weeks` weeks.

    Buckets by the role's real published date; a role without one falls back to
    when we first saw it (still a real event, just later). Includes closed
    roles — the question is posting volume, not what happens to survive.
    """
    now = now or datetime.now(UTC)
    this_week = _week_start(now.replace(hour=0, minute=0, second=0, microsecond=0))
    starts = [this_week - timedelta(weeks=i) for i in range(weeks - 1, -1, -1)]
    counts = dict.fromkeys((s.strftime("%Y-%m-%d") for s in starts), 0)

    for record in store_data.values():
        day = _parse_day(record.get("posted_at")) or _parse_day(record.get("first_seen_at"))
        if day is None:
            continue
        key = _week_start(day).strftime("%Y-%m-%d")
        if key in counts:
            counts[key] += 1
    return list(counts.items())


def median_days_open(store_data: dict) -> tuple[float | None, int]:
    """(median posting lifetime in days, sample size) from posted -> closed."""
    lifetimes = []
    for record in store_data.values():
        if record.get("is_open"):
            continue
        posted = _parse_day(record.get("posted_at"))
        closed = _parse_day(record.get("closed_at"))
        if not posted or not closed:
            continue
        days = (closed - posted).days
        if 0 <= days <= _MAX_LIFETIME_DAYS:
            lifetimes.append(days)
    if not lifetimes:
        return None, 0
    return round(statistics.median(lifetimes), 1), len(lifetimes)


def _bar_path(x: float, y: float, w: float, h: float, r: float) -> str:
    """A baseline-anchored bar whose top (data end) has rounded corners."""
    r = min(r, w / 2, h)
    if h <= 0:
        return ""
    return (
        f"M{x:.1f},{y + h:.1f} "
        f"V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
        f"H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
        f"V{y + h:.1f} Z"
    )


def svg_bar_chart(buckets: list[tuple[str, int]], width: int = 640, height: int = 180) -> str:
    """Weekly-postings bar chart as a self-contained SVG snippet."""
    if not buckets or all(n == 0 for _, n in buckets):
        return "<p class='muted'>The posting-volume chart appears once dated roles accumulate.</p>"

    pad_l, pad_r, pad_t, pad_b = 34, 8, 18, 22
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b
    top = max(n for _, n in buckets)
    slot = plot_w / len(buckets)
    bar_w = max(slot - 2, 3)  # 2px surface gap between adjacent bars

    peak_i = max(range(len(buckets)), key=lambda i: buckets[i][1])
    last_i = len(buckets) - 1

    parts = [
        f'<svg viewBox="0 0 {width} {height}" class="chart" role="img" '
        f'aria-label="Internships posted per week, last {len(buckets)} weeks">'
    ]
    # Recessive gridlines at 0 / half / max, labels in muted ink.
    for frac in (0.0, 0.5, 1.0):
        gy = pad_t + plot_h - frac * plot_h
        val = round(top * frac)
        parts.append(
            f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width - pad_r}" y2="{gy:.1f}" '
            'stroke="var(--line)" stroke-width="1"/>'
            f'<text x="{pad_l - 6}" y="{gy + 4:.1f}" text-anchor="end" class="clabel">{val}</text>'
        )

    for i, (week, n) in enumerate(buckets):
        x = pad_l + i * slot + (slot - bar_w) / 2
        h = (n / top) * plot_h if top else 0
        y = pad_t + plot_h - h
        label = datetime.strptime(week, "%Y-%m-%d").strftime("%b %d")
        if n > 0:
            parts.append(
                f'<path d="{_bar_path(x, y, bar_w, h, 4)}" fill="var(--accent)" '
                f'class="cbar" data-tip="week of {escape(label)}: {n} role{"s" if n != 1 else ""}">'
                f"<title>week of {escape(label)}: {n}</title></path>"
            )
        # Direct labels only where they earn their ink: the peak and the newest.
        if i in (peak_i, last_i) and n > 0:
            parts.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{y - 5:.1f}" text-anchor="middle" '
                f'class="cvalue">{n}</text>'
            )
        if i % 4 == 0 or i == last_i:
            parts.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{height - 6}" text-anchor="middle" '
                f'class="clabel">{escape(label)}</text>'
            )

    parts.append("</svg>")
    return "".join(parts)


def _line_chart_svg(buckets: list[tuple[str, int]], theme: dict,
                    width: int = 720, height: int = 200) -> str:
    """A standalone SVG document (for the README <picture> embed): weekly
    posting volume as a line with a soft area fill. Transparent background so
    it sits on GitHub's own surface; every color is a literal (no CSS vars)."""
    pad_l, pad_r, pad_t, pad_b = 38, 14, 22, 26
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b
    values = [n for _, n in buckets]
    top = max(values) if values else 0

    head = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" '
        f'aria-label="Internships posted per week, last {len(buckets)} weeks">'
        f"<title>Internships posted per week</title>"
    )
    if not buckets or top == 0:
        return (
            head
            + f'<text x="{width / 2}" y="{height / 2}" text-anchor="middle" '
            f'fill="{theme["ink"]}" font-size="13" '
            f'font-family="-apple-system,Segoe UI,Roboto,sans-serif">'
            "chart appears as dated roles accumulate</text></svg>"
        )

    step = plot_w / (len(buckets) - 1) if len(buckets) > 1 else plot_w
    pts = [
        (pad_l + i * step, pad_t + plot_h - (n / top) * plot_h)
        for i, n in enumerate(values)
    ]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = (
        f"M{pts[0][0]:.1f},{pad_t + plot_h} L{line.replace(' ', ' L')} "
        f"L{pts[-1][0]:.1f},{pad_t + plot_h} Z"
    )

    parts = [head, '<g font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="11">']
    for frac in (0.0, 0.5, 1.0):
        gy = pad_t + plot_h - frac * plot_h
        parts.append(
            f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width - pad_r}" y2="{gy:.1f}" '
            f'stroke="{theme["grid"]}" stroke-width="1"/>'
            f'<text x="{pad_l - 6}" y="{gy + 4:.1f}" text-anchor="end" '
            f'fill="{theme["ink"]}">{round(top * frac)}</text>'
        )
    parts.append(f'<path d="{area}" fill="{theme["accent"]}" fill-opacity="0.12"/>')
    parts.append(
        f'<polyline points="{line}" fill="none" stroke="{theme["accent"]}" '
        'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    # Direct labels where they earn their ink: the peak and the newest point.
    peak_i = max(range(len(values)), key=values.__getitem__)
    last_i = len(values) - 1
    for i in {peak_i, last_i}:
        x, y = pts[i]
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{theme["accent"]}"/>'
            f'<text x="{x:.1f}" y="{y - 9:.1f}" text-anchor="middle" '
            f'fill="{theme["value"]}" font-weight="600">{values[i]}</text>'
        )
    for i, (week, _n) in enumerate(buckets):
        if i % 4 == 0 or i == last_i:
            label = datetime.strptime(week, "%Y-%m-%d").strftime("%b %d")
            parts.append(
                f'<text x="{pts[i][0]:.1f}" y="{height - 8}" text-anchor="middle" '
                f'fill="{theme["ink"]}">{escape(label)}</text>'
            )
    parts.append("</g></svg>")
    return "".join(parts)


def write_readme_charts(store_data: dict) -> None:
    """docs/trends-{light,dark}.svg — redrawn every run, embedded in README
    via <picture> so each GitHub theme gets a chart drawn for its surface."""
    buckets = weekly_postings(store_data)
    for mode, theme in _THEMES.items():
        with open(os.path.join(paths.DOCS_DIR, f"trends-{mode}.svg"), "w",
                  encoding="utf-8") as f:
            f.write(_line_chart_svg(buckets, theme))
