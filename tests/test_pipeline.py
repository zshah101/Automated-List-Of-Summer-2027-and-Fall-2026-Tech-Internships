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


class TestStickySeasons:
    """A season already on record wins over re-inference (see _keep_matching)."""

    CFG = {"cycles": ["Summer 2027", "Fall 2026"], "regions": ["US"],
           "role_scope": "tech", "infer_undated": True, "infer_max_age_days": 45}

    def _results(self, posted_days_ago):
        from datetime import UTC, datetime, timedelta

        from intern_engine.models import Job
        posted = (datetime.now(UTC) - timedelta(days=posted_days_ago)).strftime("%Y-%m-%d")
        job = Job(id="greenhouse:acme:1", source="greenhouse", company="Acme",
                  company_slug="acme", title="Software Engineer Intern",
                  location="New York, NY", url="https://x",
                  posted_at=f"{posted}T00:00:00Z")
        return [({"ats": "greenhouse", "slug": "acme", "name": "Acme"}, [job], None)]

    def _keep(self, results, existing):
        from intern_engine.pipeline import _keep_matching
        kept, *_ = _keep_matching(results, self.CFG, {}, existing)
        return kept

    def test_fresh_undated_role_is_date_inferred(self):
        kept = self._keep(self._results(3), {})
        assert [(j.season, j.season_inferred) for j in kept] == [("Summer 2027", True)]

    def test_text_verified_season_on_record_beats_reinference(self):
        existing = {"greenhouse:acme:1": {"season": "Fall 2026", "season_inferred": False}}
        kept = self._keep(self._results(3), existing)
        assert [(j.season, j.season_inferred) for j in kept] == [("Fall 2026", False)]

    def test_sticky_season_outlives_inference_recency_window(self):
        # 60 days old: a fresh inference would refuse, but the role is already
        # on record — it must stay open instead of flipping closed.
        existing = {"greenhouse:acme:1": {"season": "Summer 2027", "season_inferred": True}}
        kept = self._keep(self._results(60), existing)
        assert [(j.season, j.season_inferred) for j in kept] == [("Summer 2027", True)]

    def test_stale_undated_role_without_record_still_dropped(self):
        assert self._keep(self._results(60), {}) == []

    def test_verified_offcycle_season_is_sticky_dropped(self):
        # Text verification recorded "Summer 2026": the role must stay off the
        # list — never re-inferred back in from its posting date.
        existing = {"greenhouse:acme:1": {"season": "Summer 2026", "season_inferred": False}}
        assert self._keep(self._results(3), existing) == []

    def test_explicit_offcycle_title_beats_stale_sticky_season(self):
        # A store written by older code may hold "Summer 2027" for a title
        # that literally says "Summer 2026" — the title's own year wins.
        from datetime import UTC, datetime, timedelta

        from intern_engine.models import Job
        posted = (datetime.now(UTC) - timedelta(days=2)).strftime("%Y-%m-%d")
        job = Job(id="workday:stevens:1", source="workday", company="Stevens",
                  company_slug="stevens", title="Summer 2026 Intern: Cyber Security",
                  location="Hoboken, NJ", url="https://x",
                  posted_at=f"{posted}T00:00:00Z")
        results = [({"ats": "workday", "slug": "stevens", "name": "Stevens"}, [job], None)]
        existing = {"workday:stevens:1": {"season": "Summer 2027", "season_inferred": True}}
        assert self._keep(results, existing) == []

    def test_legacy_unspecified_season_still_reinferred(self):
        # Only a real "<Term> <Year>" label is a verdict; junk labels fall
        # through to inference as before.
        existing = {"greenhouse:acme:1": {"season": "Unspecified"}}
        kept = self._keep(self._results(3), existing)
        assert [(j.season, j.season_inferred) for j in kept] == [("Summer 2027", True)]


class TestRegionConfig:
    """regions config must be honored end-to-end (Canada was silently dropped)."""

    def _results(self, location):
        from datetime import UTC, datetime, timedelta

        from intern_engine.models import Job
        posted = (datetime.now(UTC) - timedelta(days=3)).strftime("%Y-%m-%d")
        job = Job(id="greenhouse:acme:1", source="greenhouse", company="Acme",
                  company_slug="acme", title="Software Engineer Intern, Summer 2027",
                  location=location, url="https://x",
                  posted_at=f"{posted}T00:00:00Z")
        return [({"ats": "greenhouse", "slug": "acme", "name": "Acme"}, [job], None)]

    def _keep(self, results, regions):
        from intern_engine.pipeline import _keep_matching
        cfg = {"cycles": ["Summer 2027", "Fall 2026"], "regions": regions,
               "role_scope": "tech"}
        kept, *_ = _keep_matching(results, cfg, {}, {})
        return kept

    def test_us_only_drops_canada(self):
        assert self._keep(self._results("Toronto, Ontario, Canada"), ["US"]) == []

    def test_us_and_canada_keeps_canada(self):
        kept = self._keep(self._results("Toronto, Ontario, Canada"), ["US", "Canada"])
        assert len(kept) == 1

    def test_us_and_canada_still_keeps_us(self):
        kept = self._keep(self._results("New York, NY"), ["US", "Canada"])
        assert len(kept) == 1
