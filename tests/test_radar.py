"""Drop Radar: projection, live-status matching, and the honesty rules."""

from datetime import date

import pytest

from intern_engine import radar

TODAY = date(2026, 7, 3)


@pytest.fixture
def seasons(monkeypatch):
    data = {
        "cycle": "Summer 2026",
        "companies": {
            # notable via priority list, real early date
            "nvidia": {"name": "NVIDIA", "first_posted": "2025-08-24", "count": 58},
            # notable via count, backfill-window date -> approx
            "megacorp": {"name": "MegaCorp", "first_posted": "2025-11-05", "count": 7},
            # already posted this cycle (matched against the store below)
            "stripe": {"name": "Stripe", "first_posted": "2025-11-12", "count": 2},
            # NOT notable: unknown name, one listing -> filtered out
            "tiny shop": {"name": "Tiny Shop", "first_posted": "2025-09-01", "count": 1},
        },
    }
    monkeypatch.setattr(radar, "_seasons_cache", data)
    yield data
    monkeypatch.setattr(radar, "_seasons_cache", None)


STORE = {
    "a": {"company": "Stripe, Inc.", "season": "Summer 2027", "is_open": True,
          "url": "https://stripe/apply"},
    "b": {"company": "NVIDIA", "season": "Fall 2026", "is_open": True,
          "url": "https://nv/fall"},          # wrong cycle: must NOT count
    "c": {"company": "MegaCorp", "season": "Summer 2027", "is_open": False,
          "url": "https://mc/closed"},        # closed: must NOT count
}


def test_rows_project_one_year_and_sort_soonest_first(seasons):
    rows = radar.rows(STORE, "Summer 2027", today=TODAY)
    assert [r["company"] for r in rows] == ["NVIDIA", "MegaCorp", "Stripe"]
    assert rows[0]["expected"] == "2026-08-24"
    assert rows[0]["days_until"] == 52


def test_live_match_requires_open_and_right_cycle(seasons):
    rows = {r["company"]: r for r in radar.rows(STORE, "Summer 2027", today=TODAY)}
    assert rows["Stripe"]["status"] == "posted"          # normalized "Stripe, Inc." match
    assert rows["Stripe"]["url"] == "https://stripe/apply"
    assert rows["NVIDIA"]["status"] == "waiting"          # only Fall 2026 is open
    assert rows["MegaCorp"]["status"] == "waiting"        # role is closed


def test_backfill_window_is_flagged_approx(seasons):
    rows = {r["company"]: r for r in radar.rows(STORE, "Summer 2027", today=TODAY)}
    assert rows["MegaCorp"]["approx"] is True
    assert rows["NVIDIA"]["approx"] is False
    assert radar.pretty_last(rows["MegaCorp"]).startswith("by ")
    assert "or earlier" in radar.pretty_expected(rows["MegaCorp"])


def test_non_notable_companies_filtered(seasons):
    companies = [r["company"] for r in radar.rows(STORE, "Summer 2027", today=TODAY)]
    assert "Tiny Shop" not in companies


def test_pretty_expected_countdown(seasons):
    rows = {r["company"]: r for r in radar.rows(STORE, "Summer 2027", today=TODAY)}
    assert "any day now" not in radar.pretty_expected(rows["NVIDIA"])
    overdue = dict(rows["NVIDIA"], days_until=-3, status="waiting")
    assert "any day now" in radar.pretty_expected(overdue)
    soon = dict(rows["NVIDIA"], days_until=20, status="waiting")
    assert "in ~20d" in radar.pretty_expected(soon)


def test_plus_one_year_handles_leap_day():
    assert radar._plus_one_year("2024-02-29") == date(2025, 2, 28)


def test_empty_seasons_returns_no_rows(monkeypatch):
    monkeypatch.setattr(radar, "_seasons_cache", {})
    assert radar.rows(STORE, "Summer 2027", today=TODAY) == []
    monkeypatch.setattr(radar, "_seasons_cache", None)
