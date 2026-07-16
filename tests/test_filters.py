from datetime import UTC, datetime

from intern_engine import filters

CYCLES = ["Summer 2027", "Fall 2026"]


class TestInternship:
    def test_matches_intern(self):
        assert filters.is_internship("Software Engineer Intern")
        assert filters.is_internship("Data Co-op")

    def test_rejects_substring_false_positive(self):
        # "internal" / "international" must not count as internships
        assert not filters.is_internship("Internal Tools Engineer")
        assert not filters.is_internship("International Operations")

    def test_rejects_senior(self):
        assert not filters.is_internship("Senior Software Intern")


class TestTech:
    def test_keeps_software_and_ml(self):
        assert filters.is_tech("Software Engineer Intern")
        assert filters.is_tech("Machine Learning Intern")
        assert filters.is_tech("Backend Developer Intern")

    def test_drops_non_tech_and_hardware(self):
        assert not filters.is_tech("Mechanical Engineering Intern")
        assert not filters.is_tech("Technical Recruiting Intern")
        assert not filters.is_tech("FPGA Hardware Intern")

    def test_drops_phd(self):
        assert not filters.is_tech("PhD Machine Learning Intern")


class TestSeason:
    def test_explicit_cycle(self):
        assert filters.detect_season("SWE Intern, Summer 2027", CYCLES) == "Summer 2027"
        assert filters.detect_season("Fall 2026 Data Intern", CYCLES) == "Fall 2026"

    def test_year_only_maps_to_cycle(self):
        assert filters.detect_season("2027 Software Engineer Intern", CYCLES) == "Summer 2027"

    def test_undated_is_dropped(self):
        assert filters.detect_season("Software Engineer Intern", CYCLES) is None

    def test_off_cycle_is_dropped(self):
        assert filters.detect_season("Summer 2026 Intern", CYCLES) is None
        assert filters.detect_season("Fall 2027 Intern", CYCLES) is None


class TestRegion:
    def test_us_match(self):
        assert filters.region_ok("San Francisco, CA", want_us=True, want_canada=False)
        assert filters.region_ok("New York, United States", want_us=True, want_canada=False)

    def test_canada_excluded_when_us_only(self):
        assert not filters.region_ok("Toronto, Ontario, Canada", want_us=True, want_canada=False)
        assert filters.region_ok("Toronto, Ontario, Canada", want_us=False, want_canada=True)

    def test_country_code_prefix_not_us(self):
        # "DE-Berlin" is Germany, not the Delaware state code
        assert not filters.region_ok("DE-Berlin-Trion", want_us=True, want_canada=False)

    def test_named_foreign_country_beats_state_code_lookalike(self):
        # "IN - Bangalore, India" is India, not Indiana
        assert not filters.is_united_states("IN - Bangalore, India")
        assert not filters.is_united_states("Munich, Germany")
        assert not filters.is_united_states("CA - Sydney, Australia")

    def test_explicit_us_token_wins_for_multi_country_strings(self):
        assert filters.is_united_states("New York, USA; Bangalore, India")

    def test_state_code_with_spaced_suffix_still_us(self):
        assert filters.is_united_states("Dallas, TX - Headquarters")


class TestCategory:
    def test_categories(self):
        assert filters.categorize("Software Engineer Intern") == "Software"
        assert filters.categorize("Machine Learning Intern") == "Data & ML/AI"
        assert filters.categorize("Cybersecurity Intern") == "Security"


class TestInferSeason:
    """Yearless titles bucketed from the posting date (detect_season stays strict)."""

    NOW = datetime(2026, 7, 15, tzinfo=UTC)

    def _infer(self, title, posted, **kw):
        return filters.infer_season(title, posted, CYCLES, now=self.NOW, **kw)

    def test_plain_intern_posted_after_april_is_next_summer(self):
        assert self._infer("Software Engineer Intern", "2026-07-10") == "Summer 2027"

    def test_summer_word_without_year(self):
        assert self._infer("Summer Intern - Backend", "2026-07-01") == "Summer 2027"

    def test_fall_word_maps_to_same_year_until_august(self):
        assert self._infer("Fall Software Intern", "2026-07-01") == "Fall 2026"

    def test_stale_posting_is_never_inferred(self):
        # 60 days old with a 45-day trust window -> evergreen sludge, drop.
        assert self._infer("Software Engineer Intern", "2026-05-01") is None

    def test_wider_window_accepts_older(self):
        assert self._infer("Software Engineer Intern", "2026-05-01",
                           max_age_days=90) == "Summer 2027"

    def test_no_posted_date_is_never_inferred(self):
        assert self._infer("Software Engineer Intern", None) is None

    def test_untracked_inferred_cycle_is_dropped(self):
        # "Fall Intern" posted in October -> Fall 2027, which we don't track.
        now = datetime(2026, 10, 20, tzinfo=UTC)
        assert filters.infer_season("Fall Intern", "2026-10-15", CYCLES, now=now) is None

    def test_explicit_year_never_reaches_inference(self):
        # Belt and suspenders: detect_season handles dated titles first.
        assert filters.detect_season("Software Intern Summer 2027", CYCLES) == "Summer 2027"


class TestTechScopeExclusions:
    def test_non_tech_roles_with_ai_bait_excluded(self):
        assert not filters.is_tech("Digital Marketer Intern-Align AI")
        assert not filters.is_tech("Account Management AI Intern")
        assert not filters.is_tech("Unpaid Programming Intern")

    def test_real_tech_titles_still_pass(self):
        assert filters.is_tech("Programming Intern")
        assert filters.is_tech("AI Software Engineer Intern")


class TestSeasonFromText:
    def test_stated_coop_term(self):
        assert filters.season_from_text(
            "Join our Fall 2026 co-op program in Boston."
        ) == "Fall 2026"

    def test_summer_of_phrasing_and_autumn_alias(self):
        assert filters.season_from_text(
            "an internship in the summer of 2027 at our NYC office"
        ) == "Summer 2027"
        assert filters.season_from_text(
            "This internship runs autumn 2026 through December."
        ) == "Fall 2026"

    def test_conflicting_mentions_never_override(self):
        # Grad-window boilerplate lists several terms -> no verdict.
        assert filters.season_from_text(
            "Internship candidates graduating between Fall 2026 and Summer 2027 "
            "are encouraged to apply."
        ) is None

    def test_far_away_mention_ignored(self):
        pad = "x " * 200
        assert filters.season_from_text(
            f"Our company was named a best employer of Summer 2026. {pad} "
            "This internship is fully remote."
        ) is None

    def test_empty_text(self):
        assert filters.season_from_text("") is None
