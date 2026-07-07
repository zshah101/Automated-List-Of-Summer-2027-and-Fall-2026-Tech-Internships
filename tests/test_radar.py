"""Drop Radar: projection, live-status matching, source blending, honesty rules."""

from datetime import date

import pytest

from intern_engine import radar

TODAY = date(2026, 7, 3)


@pytest.fixture
def seasons(monkeypatch):
    data = {
        "cycle": "Summer 2026",
        "floor": "2025-11-10",
        "companies": {
            # notable via priority list, real early date
            "nvidia": {"name": "NVIDIA", "first_posted": "2025-08-24", "count": 58},
            # notable via count, date sits in the floor band -> latest bound
            "megacorp": {"name": "MegaCorp", "first_posted": "2025-11-12", "count": 7},
            # already posted this cycle (matched against the store below)
            "stripe": {"name": "Stripe", "first_posted": "2025-11-12", "count": 2},
            # NOT notable: unknown name, one listing -> filtered out
            "tiny shop": {"name": "Tiny Shop", "first_posted": "2025-09-01", "count": 1},
        },
    }
    monkeypatch.setattr(radar, "_seasons_cache", data)
    monkeypatch.setattr(radar, "_observed_cache", {"companies": {}})
    yield data
    monkeypatch.setattr(radar, "_seasons_cache", None)
    monkeypatch.setattr(radar, "_observed_cache", None)


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
    # Stripe is posted -> sorts first; the rest by soonest expected.
    assert rows[0]["company"] == "Stripe"
    waiting = [r["company"] for r in rows if r["status"] == "waiting"]
    assert waiting == ["NVIDIA", "MegaCorp"]
    nvidia = next(r for r in rows if r["company"] == "NVIDIA")
    assert nvidia["expected"] == "2026-08-24"
    assert nvidia["days_until"] == 52


def test_live_match_requires_open_and_right_cycle(seasons):
    rows = {r["company"]: r for r in radar.rows(STORE, "Summer 2027", today=TODAY)}
    assert rows["Stripe"]["status"] == "posted"          # normalized "Stripe, Inc." match
    assert rows["Stripe"]["url"] == "https://stripe/apply"
    assert rows["NVIDIA"]["status"] == "waiting"          # only Fall 2026 is open
    assert rows["MegaCorp"]["status"] == "waiting"        # role is closed


def test_floor_band_is_flagged_and_estimated_is_not(seasons):
    rows = {r["company"]: r for r in radar.rows(STORE, "Summer 2027", today=TODAY)}
    assert rows["MegaCorp"]["approx"] is True
    assert rows["MegaCorp"]["confidence"] == "floor"
    assert rows["NVIDIA"]["approx"] is False
    assert rows["NVIDIA"]["confidence"] == "estimated"
    assert radar.pretty_last(rows["MegaCorp"]).startswith("by ")
    assert "or earlier" in radar.pretty_expected(rows["MegaCorp"])


def test_engine_observed_beats_reference_and_is_verified(seasons, monkeypatch):
    # The engine saw NVIDIA's real Summer 2026 drop on Sep 2 (earlier than the
    # reference's Aug 24? no — later; point is it wins and is marked verified).
    monkeypatch.setattr(radar, "_observed_cache", {"companies": {
        "nvidia": {"name": "NVIDIA", "cycles": {"Summer 2026": {"first_posted": "2025-09-10", "count": 3}}},
    }})
    rows = {r["company"]: r for r in radar.rows(STORE, "Summer 2027", today=TODAY)}
    assert rows["NVIDIA"]["source"] == "engine"
    assert rows["NVIDIA"]["confidence"] == "verified"
    assert rows["NVIDIA"]["expected"] == "2026-09-10"   # projected from observed


def test_live_drop_date_is_shown_when_caught(seasons, monkeypatch):
    monkeypatch.setattr(radar, "_observed_cache", {"companies": {
        "stripe": {"name": "Stripe", "cycles": {"Summer 2027": {"first_posted": "2026-06-30", "count": 1}}},
    }})
    row = next(r for r in radar.rows(STORE, "Summer 2027", today=TODAY) if r["company"] == "Stripe")
    assert row["status"] == "posted"
    assert row["posted_on"] == "2026-06-30"
    assert radar.pretty_expected(row) == "dropped Jun 30"


def test_observed_only_company_appears_even_without_reference(seasons, monkeypatch):
    monkeypatch.setattr(radar, "_observed_cache", {"companies": {
        "openai": {"name": "OpenAI", "cycles": {"Summer 2026": {"first_posted": "2025-10-01", "count": 2}}},
    }})
    companies = [r["company"] for r in radar.rows(STORE, "Summer 2027", today=TODAY)]
    assert "OpenAI" in companies


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


def test_prev_cycle():
    assert radar.prev_cycle("Summer 2027") == "Summer 2026"
    assert radar.prev_cycle("Fall 2026") == "Fall 2025"


def test_plus_one_year_handles_leap_day():
    assert radar._plus_one_year("2024-02-29") == date(2025, 2, 28)


def test_empty_sources_return_no_rows(monkeypatch):
    monkeypatch.setattr(radar, "_seasons_cache", {})
    monkeypatch.setattr(radar, "_observed_cache", {"companies": {}})
    assert radar.rows(STORE, "Summer 2027", today=TODAY) == []
    monkeypatch.setattr(radar, "_seasons_cache", None)
    monkeypatch.setattr(radar, "_observed_cache", None)
