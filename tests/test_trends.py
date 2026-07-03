"""Trend aggregation + chart rendering (pure functions, frozen clock)."""

from datetime import UTC, datetime

from intern_engine import trends

NOW = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)  # a Wednesday


def _rec(posted=None, first_seen=None, closed=None, is_open=True):
    return {
        "posted_at": posted, "first_seen_at": first_seen,
        "closed_at": closed, "is_open": is_open,
    }


# --- weekly bucketing -----------------------------------------------------------

def test_weekly_postings_buckets_by_monday_week():
    store = {
        "a": _rec(posted="2026-06-29T00:00:00Z"),   # Monday this week
        "b": _rec(posted="2026-07-01T09:00:00Z"),   # same week
        "c": _rec(posted="2026-06-24T00:00:00Z"),   # previous week
    }
    buckets = dict(trends.weekly_postings(store, weeks=4, now=NOW))
    assert buckets["2026-06-29"] == 2
    assert buckets["2026-06-22"] == 1


def test_weekly_postings_falls_back_to_first_seen():
    store = {"a": _rec(first_seen="2026-07-01T05:00:00Z")}
    buckets = dict(trends.weekly_postings(store, weeks=2, now=NOW))
    assert buckets["2026-06-29"] == 1


def test_weekly_postings_ignores_out_of_window_and_undated():
    store = {
        "old": _rec(posted="2025-01-01T00:00:00Z"),
        "undated": _rec(),
    }
    buckets = trends.weekly_postings(store, weeks=4, now=NOW)
    assert len(buckets) == 4
    assert all(n == 0 for _, n in buckets)


def test_weekly_postings_window_length_and_order():
    buckets = trends.weekly_postings({}, weeks=16, now=NOW)
    assert len(buckets) == 16
    weeks = [w for w, _ in buckets]
    assert weeks == sorted(weeks)          # oldest -> newest
    assert weeks[-1] == "2026-06-29"       # current week last


# --- posting lifetime -----------------------------------------------------------

def test_median_days_open():
    store = {
        "a": _rec(posted="2026-06-01", closed="2026-06-11", is_open=False),  # 10d
        "b": _rec(posted="2026-06-01", closed="2026-06-21", is_open=False),  # 20d
        "c": _rec(posted="2026-06-01", closed="2026-06-15", is_open=True),   # open: excluded
        "d": _rec(posted=None, closed="2026-06-15", is_open=False),          # undated: excluded
    }
    median, sample = trends.median_days_open(store)
    assert (median, sample) == (15, 2)


def test_median_days_open_rejects_stale_artifacts():
    store = {"a": _rec(posted="2025-01-01", closed="2026-06-30", is_open=False)}
    assert trends.median_days_open(store) == (None, 0)


# --- the chart ------------------------------------------------------------------

def test_svg_chart_renders_bars_labels_and_tooltips():
    store = {
        "a": _rec(posted="2026-06-29T00:00:00Z"),
        "b": _rec(posted="2026-06-29T01:00:00Z"),
        "c": _rec(posted="2026-06-22T00:00:00Z"),
    }
    svg = trends.svg_bar_chart(trends.weekly_postings(store, weeks=8, now=NOW))
    assert svg.count('class="cbar"') == 2          # two non-empty weeks
    assert 'data-tip="week of Jun 29: 2 roles"' in svg
    assert "<title>" in svg                        # native fallback tooltip
    assert 'class="cvalue">2<' in svg              # peak/latest direct label
    assert 'aria-label="Internships posted per week' in svg


def test_svg_chart_empty_state():
    out = trends.svg_bar_chart(trends.weekly_postings({}, weeks=4, now=NOW))
    assert "<svg" not in out and "appears once" in out


# --- the standalone README chart --------------------------------------------------

def test_line_chart_svg_standalone_for_both_themes():
    buckets = trends.weekly_postings(
        {"a": _rec(posted="2026-06-29T00:00:00Z"), "b": _rec(posted="2026-06-22T00:00:00Z")},
        weeks=8, now=NOW,
    )
    for theme in trends._THEMES.values():
        svg = trends._line_chart_svg(buckets, theme)
        assert svg.startswith("<svg xmlns=")           # standalone document
        assert "var(--" not in svg                     # no CSS vars in a file embed
        assert theme["accent"] in svg
        assert "<polyline" in svg and "fill-opacity" in svg
        assert 'font-weight="600">1<' in svg           # peak/latest direct label


def test_line_chart_svg_empty_state_is_valid_svg():
    svg = trends._line_chart_svg(trends.weekly_postings({}, weeks=4, now=NOW),
                                 trends._THEMES["light"])
    assert svg.startswith("<svg xmlns=") and "accumulate" in svg
