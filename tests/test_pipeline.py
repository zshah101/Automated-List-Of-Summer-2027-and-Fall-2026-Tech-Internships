from datetime import UTC

from intern_engine.pipeline import _detection_latency, _parse_iso


class TestParseIso:
    def test_z_suffix_is_utc_aware(self):
        dt = _parse_iso("2026-07-15T21:00:00Z")
        assert dt.tzinfo is not None
        assert dt.utcoffset().total_seconds() == 0

    def test_naive_and_date_only_assumed_utc(self):
        # Some ATS feeds ship timestamps with no offset (or a bare date);
        # they must come back aware or datetime arithmetic explodes.
        for raw in ("2026-07-15T18:00:00", "2026-07-15"):
            dt = _parse_iso(raw)
            assert dt.tzinfo is UTC

    def test_offset_normalized_to_utc(self):
        dt = _parse_iso("2026-07-15T14:00:00-04:00")
        assert dt.hour == 18
        assert dt.tzinfo is not None

    def test_garbage_is_none(self):
        assert _parse_iso("not a date") is None
        assert _parse_iso(None) is None


class TestDetectionLatency:
    def test_mixed_naive_and_aware_does_not_crash(self):
        # Regression: a single offset-less posted_at next to a Z-suffixed
        # first_seen_at crashed every run with TypeError (2026-07-15 outage).
        existing = {
            "a": {"posted_at": "2026-07-15T18:00:00",   # naive from the ATS
                  "first_seen_at": "2026-07-15T21:00:00Z"},
            "b": {"posted_at": "2026-07-15T10:00:00Z",
                  "first_seen_at": "2026-07-15T11:00:00Z"},
        }
        out = _detection_latency(existing)
        assert out["sample_size"] == 2
        assert out["median_minutes"] == 120.0  # median of 180 and 60

    def test_empty_store(self):
        out = _detection_latency({})
        assert out == {"median_minutes": None, "sample_size": 0, "window_days": 7}

    def test_old_backfills_outside_window_excluded(self):
        existing = {
            "old": {"posted_at": "2026-01-01T00:00:00Z",
                    "first_seen_at": "2026-07-15T00:00:00Z"},
        }
        assert _detection_latency(existing)["sample_size"] == 0
