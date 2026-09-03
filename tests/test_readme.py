"""README/CSV generation: honest counts and a CSV that can't execute."""

import csv

import pytest

from intern_engine import paths, readme


def _rec(jid, **extra):
    rec = {
        "id": jid, "company": "Acme", "title": "Software Engineer Intern",
        "season": "Summer 2027", "season_inferred": False, "category": "Software",
        "location": "Singapore", "url": f"https://x/{jid}", "is_open": True,
        "posted_at": "2026-07-01T00:00:00Z", "first_seen_at": "2026-07-01T00:00:00Z",
        "sponsorship": "unknown", "skills": [],
    }
    rec.update(extra)
    return rec


@pytest.fixture
def outputs(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "README_PATH", str(tmp_path / "README.md"))
    monkeypatch.setattr(paths, "CSV_PATH", str(tmp_path / "internships.csv"))
    return tmp_path


class TestEvidenceSplit:
    """A cycle heading is a claim; only employer-stated roles may sit under it."""

    def test_inferred_roles_get_their_own_section(self, outputs):
        store = {
            "a": _rec("a"),
            "b": _rec("b", season_inferred=True, title="Backend Intern"),
        }
        readme.generate(store)
        text = (outputs / "README.md").read_text(encoding="utf-8")
        assert "## Summer 2027  (1 employer-stated)" in text
        assert "Recently posted — cycle not stated  (1 roles)" in text
        # No guessed cycle anywhere: the lane states the absence, not a value.
        assert "~Summer 2027" not in text
        assert "Likely cycle" not in text

    def test_hero_reports_the_split(self, outputs):
        store = {
            "a": _rec("a"),
            "b": _rec("b", season_inferred=True),
            "c": _rec("c", season_inferred=True),
        }
        readme.generate(store)
        text = (outputs / "README.md").read_text(encoding="utf-8")
        assert "1 have a cycle the employer stated" in text
        assert "2 are recent postings whose cycle isn't stated" in text

    def test_no_rolling_section_when_everything_is_stated(self, outputs):
        readme.generate({"a": _rec("a")})
        text = (outputs / "README.md").read_text(encoding="utf-8")
        assert "## Recently posted" not in text

    def test_role_rows_render_skill_tags(self, outputs):
        readme.generate({"a": _rec("a", skills=["Python", "React", "SQL"])})
        text = (outputs / "README.md").read_text(encoding="utf-8")
        assert "| Company | Role | Category | Location | Skills | Posted | Apply |" in text
        assert "| Python, SQL, React |" in text

    def test_role_rows_label_missing_skills(self, outputs):
        readme.generate({"a": _rec("a", skills=[])})
        text = (outputs / "README.md").read_text(encoding="utf-8")
        assert "| No skills listed |" in text


class TestMultiCycleRendering:
    def test_role_appears_under_every_cycle_it_states(self, outputs):
        store = {"a": _rec("a", title="SWE Internship (Fall 2026/Summer 2027)",
                           season="Summer 2027",
                           seasons=["Summer 2027", "Fall 2026"])}
        readme.generate(store)
        text = (outputs / "README.md").read_text(encoding="utf-8")
        assert "## Summer 2027  (1 employer-stated)" in text
        assert "## Fall 2026  (1 employer-stated)" in text

    def test_it_is_counted_once_not_twice(self, outputs):
        store = {"a": _rec("a", seasons=["Summer 2027", "Fall 2026"])}
        out = readme.generate(store)
        assert out["open"] == 1

    def test_the_cross_reference_names_only_the_other_cycle(self, outputs):
        store = {"a": _rec("a", seasons=["Summer 2027", "Fall 2026"])}
        readme.generate(store)
        text = (outputs / "README.md").read_text(encoding="utf-8")
        # Under Summer 2027 it should point at Fall 2026, and vice versa —
        # repeating the section's own cycle back at the reader is noise.
        assert "_(also open for Fall 2026)_" in text
        assert "_(also open for Summer 2027)_" in text
        assert "also open for Summer 2027, Fall 2026" not in text


class TestCsvCompleteness:
    def test_csv_holds_every_open_role_even_when_readme_caps(self, outputs):
        # The README caps rows per company for readability; the CSV is the
        # machine-readable export and must never silently drop roles.
        store = {str(i): _rec(str(i), title=f"SWE Intern {i}") for i in range(9)}
        readme.generate(store)
        rows = list(csv.DictReader((outputs / "internships.csv").open(encoding="utf-8")))
        assert len(rows) == 9

    def test_csv_carries_the_new_fields(self, outputs):
        store = {"a": _rec("a", title="Data Co-op", location="Remote - Singapore")}
        readme.generate(store)
        row = next(csv.DictReader((outputs / "internships.csv").open(encoding="utf-8")))
        assert row["id"]
        assert row["program"] == "Co-op"
        assert row["remote"] == "yes"

    def test_closed_roles_are_excluded(self, outputs):
        store = {"a": _rec("a"), "b": _rec("b", is_open=False)}
        readme.generate(store)
        rows = list(csv.DictReader((outputs / "internships.csv").open(encoding="utf-8")))
        assert len(rows) == 1


class TestCsvInjection:
    """Job titles are third-party text and land in a file people open in Excel."""

    def test_formula_prefixes_are_neutralized(self):
        for raw in ("=HYPERLINK(\"http://evil\",\"click\")",
                    "+1+1", "-2+3", "@SUM(A1:A9)"):
            out = readme._csv_safe(raw)
            assert out.startswith("'"), raw
            assert out[1:] == raw  # the value itself is preserved, just inert

    def test_ordinary_values_are_untouched(self):
        for raw in ("Software Engineer Intern", "Stripe", "$45/hr",
                    "2026-06-01T00:00:00Z", "New York, NY", ""):
            assert readme._csv_safe(raw) == raw

    def test_non_strings_pass_through(self):
        assert readme._csv_safe(None) is None
        assert readme._csv_safe(42) == 42


class TestHeaderCounts:
    """The README and the API must not report different totals as the same thing."""

    CFG = {"cycles": ["Summer 2027"], "regions": ["US"]}

    def test_capped_listing_reports_both_numbers(self):
        lines = readme._header(self.CFG, total_open=107, companies=3900,
                               new_week=11, shown=104)
        line = next(x for x in lines if "open roles" in x)
        assert "107 open roles" in line
        assert "104 listed below" in line

    def test_no_parenthetical_when_nothing_was_cut(self):
        lines = readme._header(self.CFG, total_open=104, companies=3900,
                               new_week=11, shown=104)
        line = next(x for x in lines if "open roles" in x)
        assert "104 open roles" in line
        assert "listed below" not in line

    def test_zero_inferred_roles_still_reports_all_stated_and_fetch_time(self):
        lines = readme._header(
            self.CFG, total_open=4, companies=3900, new_week=1,
            stated=4, inferred=0, data_as_of="2026-08-06T14:08:27Z",
        )
        assert any("4 have a cycle the employer stated · 0 are recent" in x
                   for x in lines)
        assert any("data as of Aug 06, 2026 at 14:08 UTC" in x for x in lines)


class TestIdenticalOpenings:
    """One row per job, one line per requisition kept reachable.

    Copart really has eight live "Software Engineering Intern, Dallas"
    requisitions. Eight identical rows is what a reader complained about; zero
    of them disappearing is what the data promises.
    """

    def _store(self, n=3):
        return {str(i): _rec(str(i)) for i in range(n)}

    def test_the_table_shows_one_row(self, outputs):
        readme.generate(self._store())
        text = (outputs / "README.md").read_text(encoding="utf-8")
        assert text.count("| Acme | Software Engineer Intern") == 1

    def test_the_row_says_how_many_openings(self, outputs):
        readme.generate(self._store())
        text = (outputs / "README.md").read_text(encoding="utf-8")
        assert "(3 openings)" in text

    def test_every_requisition_keeps_an_apply_link(self, outputs):
        readme.generate(self._store())
        text = (outputs / "README.md").read_text(encoding="utf-8")
        for jid in ("0", "1", "2"):
            assert f"https://x/{jid}" in text

    def test_the_headline_count_still_counts_openings(self, outputs):
        # "3 open roles" stays true — the grouping is a layout decision, not a
        # claim that two of the jobs stopped existing.
        readme.generate(self._store())
        text = (outputs / "README.md").read_text(encoding="utf-8")
        assert "3 open roles" in text
        assert "(1 listed below)" not in text

    def test_the_csv_still_exports_every_requisition(self, outputs):
        # The machine-readable export is where all three ids must survive.
        readme.generate(self._store())
        with open(paths.CSV_PATH, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert sorted(r["id"] for r in rows) == ["0", "1", "2"]

    def test_a_different_location_is_not_folded_away(self, outputs):
        store = self._store(2)
        store["1"]["location"] = "Kuala Lumpur, Malaysia"
        readme.generate(store)
        text = (outputs / "README.md").read_text(encoding="utf-8")
        assert text.count("| Acme | Software Engineer Intern") == 2
        # No row claims a count (the legend explaining the marker is not a row).
        rows = [ln for ln in text.splitlines() if ln.startswith("| Acme |")]
        assert rows and not any("openings)" in ln for ln in rows)
