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

    def test_apostrophe_short_year(self):
        assert filters.detect_season("SWE Intern - Summer '27", CYCLES) == "Summer 2027"
        assert filters.detect_season("Fall '26 Data Intern", CYCLES) == "Fall 2026"

    def test_graduation_year_in_title_is_not_a_cycle(self):
        # "Class of 2027" names the student, not the internship term.
        assert filters.detect_season("Software Intern (Class of 2027)", CYCLES) is None
        assert filters.detect_season("SWE Intern - Graduating 2027", CYCLES) is None

    def test_stated_cycle_wins_over_graduation_year(self):
        assert filters.detect_season(
            "Summer 2027 SWE Intern (Class of 2028)", CYCLES
        ) == "Summer 2027"

    def test_is_cycle_label(self):
        assert filters.is_cycle_label("Summer 2026")
        assert filters.is_cycle_label("Fall 2027")
        assert not filters.is_cycle_label("Unspecified")
        assert not filters.is_cycle_label("")
        assert not filters.is_cycle_label(None)


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

    def test_other_americas_are_not_us(self):
        assert not filters.is_united_states("Remote - Latin America")
        assert not filters.is_united_states("South America")
        # "North America" remains US-eligible (US-inclusive remote regions).
        assert filters.is_united_states("Remote (North America)")

    def test_canada_vetoes_state_code_lookalike(self):
        # The Magna leak: "Milton, Ontario, CA" read the trailing CA as
        # California. A province name / "Canada" beats a bare state code…
        assert not filters.is_united_states("Milton, Ontario, CA")
        assert not filters.is_united_states("Toronto, ON, Canada")
        # …but a full US state name still wins ("Ontario, California" is a
        # real US city), and explicit US tokens are untouched.
        assert filters.is_united_states("Ontario, California")
        assert filters.is_united_states("Ontario, California, United States")


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

    def test_explicit_offcycle_year_is_never_reinferred(self):
        # "Summer 2026 Intern" was refused by detect_season for a reason —
        # the posting date must not override the year the company wrote.
        assert self._infer("Summer 2026 Intern: Cyber Security", "2026-07-10") is None
        assert self._infer("Fall 2027 Software Intern", "2026-07-10") is None

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
    NOW = datetime(2026, 7, 15, tzinfo=UTC)

    def _stated(self, text, **kw):
        return filters.season_from_text(text, now=self.NOW, **kw)

    def test_stated_coop_term(self):
        assert self._stated(
            "Join our Fall 2026 co-op program in Boston."
        ) == "Fall 2026"

    def test_summer_of_phrasing_and_autumn_alias(self):
        assert self._stated(
            "an internship in the summer of 2027 at our NYC office"
        ) == "Summer 2027"
        assert self._stated(
            "This internship runs autumn 2026 through December."
        ) == "Fall 2026"

    def test_conflicting_mentions_never_override(self):
        # Grad-window boilerplate lists several terms -> no verdict.
        assert self._stated(
            "Internship candidates enrolled between Fall 2026 and Summer 2027 "
            "are encouraged to apply."
        ) is None

    def test_far_away_mention_ignored(self):
        pad = "x " * 200
        assert self._stated(
            f"Our company was named a best employer of Summer 2026. {pad} "
            "This internship is fully remote."
        ) is None

    def test_empty_text(self):
        assert self._stated("") is None

    # --- month+year mentions (mapped through the calendar) -------------------

    def test_start_date_month_maps_to_term(self):
        # The Doctors Without Borders case: "start date July 2026" is Summer
        # 2026, no matter what the posting date suggested.
        assert self._stated(
            "ESTIMATED START DATE: Anticipated start date for July 2026. "
            "DURATION: 6 months."
        ) == "Summer 2026"

    def test_month_with_day_and_range(self):
        assert self._stated(
            "The internship runs June 8, 2027 through August 2027 in Austin."
        ) == "Summer 2027"

    def test_graduation_month_is_not_a_cycle(self):
        # The Fortive case: a graduation window must never bucket the role.
        assert self._stated(
            "Currently pursuing a BS in Computer Science. Graduating "
            "December 2026 or later. Strong understanding of networks."
        ) is None

    def test_company_history_dates_ignored(self):
        # The Nio case: "Founded in November 2014" is company history — killed
        # by both the plausible-year window and the context guard.
        assert self._stated(
            "Founded in November 2014, our internship program pairs you with "
            "senior researchers."
        ) is None

    def test_grad_window_term_mentions_are_guarded(self):
        # The Palantir case: "graduating in Winter 2027 or Spring 2028" is the
        # candidate's timeline, not the internship cycle.
        assert self._stated(
            "Must be planning on graduating in Winter 2027 or Spring 2028. "
            "This should be your final internship before graduating."
        ) is None

    def test_degree_window_month_mentions_are_guarded(self):
        # The Datasite case: a degree window phrased with months.
        assert self._stated(
            "Bachelor's degree in CS, Engineering or Data Science preferrably "
            "between May and August 2026. This is a 10-12 week internship."
        ) is None

    def test_implausible_year_ignored(self):
        assert self._stated(
            "Our internship program has run every summer since May 2019."
        ) is None
