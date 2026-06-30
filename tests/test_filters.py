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


class TestCategory:
    def test_categories(self):
        assert filters.categorize("Software Engineer Intern") == "Software"
        assert filters.categorize("Machine Learning Intern") == "Data & ML/AI"
        assert filters.categorize("Cybersecurity Intern") == "Security"
