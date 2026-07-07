"""The engine's own posted-date memory: earliest-wins, monotonic, per cycle."""

from intern_engine import observe


def test_records_earliest_real_date_per_company_and_cycle():
    store = {
        "1": {"company": "NVIDIA", "season": "Summer 2027", "posted_at": "2026-09-10T00:00:00Z"},
        "2": {"company": "NVIDIA", "season": "Summer 2027", "posted_at": "2026-09-03T12:00:00Z"},
        "3": {"company": "NVIDIA", "season": "Fall 2026", "posted_at": "2026-03-01T00:00:00Z"},
    }
    out = observe.update_from_store(store, {"companies": {}})
    cycles = out["companies"]["nvidia"]["cycles"]
    assert cycles["Summer 2027"]["first_posted"] == "2026-09-03"   # earliest wins
    assert cycles["Summer 2027"]["count"] == 2
    assert cycles["Fall 2026"]["first_posted"] == "2026-03-01"


def test_ignores_records_without_posted_date_or_cycle():
    store = {
        "1": {"company": "Foo", "season": "Summer 2027"},                # no posted_at
        "2": {"company": "Bar", "posted_at": "2026-01-01T00:00:00Z"},    # no season
    }
    out = observe.update_from_store(store, {"companies": {}})
    assert out["companies"] == {}


def test_is_monotonic_across_runs():
    prior = {"companies": {
        "stripe": {"name": "Stripe", "cycles": {"Summer 2027": {"first_posted": "2026-06-30", "count": 1}}},
    }}
    # A later run where the role has closed/purged (empty store) must not erase it.
    out = observe.update_from_store({}, prior)
    assert out["companies"]["stripe"]["cycles"]["Summer 2027"]["first_posted"] == "2026-06-30"


def test_normalizes_company_variants_together():
    store = {
        "1": {"company": "Stripe, Inc.", "season": "Summer 2027", "posted_at": "2026-06-30T00:00:00Z"},
        "2": {"company": "Stripe", "season": "Summer 2027", "posted_at": "2026-06-25T00:00:00Z"},
    }
    out = observe.update_from_store(store, {"companies": {}})
    keys = list(out["companies"])
    assert len(keys) == 1
    assert out["companies"][keys[0]]["cycles"]["Summer 2027"]["first_posted"] == "2026-06-25"
