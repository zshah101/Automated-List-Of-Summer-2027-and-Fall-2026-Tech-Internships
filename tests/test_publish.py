"""The machine-readable outputs: Atom feed parses, JSON API round-trips."""

import json
import os
import xml.etree.ElementTree as ET

from intern_engine import paths, publish

STORE = {
    "a": {
        "id": "a", "company": "Stripe", "title": "SWE Intern", "season": "Summer 2027",
        "category": "Software", "location": "SF", "url": "https://stripe.com/jobs/1",
        "posted_at": "2026-06-01T00:00:00Z", "first_seen_at": "2026-06-02T00:00:00Z",
        "sponsorship": "no-sponsorship", "salary": None, "source": "greenhouse",
        "is_open": True,
    },
    "b": {
        "id": "b", "company": "Old Co", "title": "Closed Intern", "season": "Fall 2026",
        "category": "Software", "location": "NY", "url": "https://old.co",
        "first_seen_at": "2026-05-01T00:00:00Z", "sponsorship": "unknown",
        "source": "lever", "is_open": False,
    },
}


def _redirect(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "DOCS_DIR", str(tmp_path))
    monkeypatch.setattr(paths, "FEED_PATH", str(tmp_path / "feed.xml"))
    monkeypatch.setattr(paths, "API_DIR", str(tmp_path / "api"))


class TestFeed:
    def test_open_roles_and_recent_closed_discoveries_are_valid_xml(self, monkeypatch, tmp_path):
        _redirect(monkeypatch, tmp_path)
        store = dict(STORE)
        store["recently-closed"] = {
            **STORE["b"], "id": "recently-closed", "company": "Brief Co",
            "first_seen_at": "2026-08-05T10:00:00Z",
            "closed_at": "2026-08-05T12:00:00Z",
        }
        n = publish.write_feed(store, data_as_of="2026-08-06T14:00:00Z")
        assert n == 2
        tree = ET.parse(tmp_path / "feed.xml")
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entries = tree.getroot().findall("a:entry", ns)
        assert len(entries) == 2
        titles = [entry.find("a:title", ns).text for entry in entries]
        assert any("Stripe" in title and "🛂" in title for title in titles)
        assert any("Brief Co" in title for title in titles)
        assert tree.getroot().find("a:updated", ns).text == "2026-08-06T14:00:00Z"

    def test_xml_attribute_quotes_are_escaped(self, monkeypatch, tmp_path):
        _redirect(monkeypatch, tmp_path)
        store = {"a": {**STORE["a"], "url": 'https://x/\" onclick=\"bad'}}
        publish.write_feed(store, data_as_of="2026-08-06T14:00:00Z")
        root = ET.parse(tmp_path / "feed.xml").getroot()
        entry = root.find("{http://www.w3.org/2005/Atom}entry")
        link = next(child for child in entry if child.tag.endswith("link"))
        assert link.attrib == {"href": 'https://x/" onclick="bad'}


class TestApi:
    def test_jobs_json_shape(self, monkeypatch, tmp_path):
        _redirect(monkeypatch, tmp_path)
        n = publish.write_api(
            STORE, {"open_total": 1, "generated_at": "2026-08-06T14:00:00Z"}
        )
        assert n == 1
        with open(os.path.join(str(tmp_path / "api"), "jobs.json"), encoding="utf-8") as f:
            payload = json.load(f)
        assert payload["count"] == 1
        assert payload["generated_at"] == "2026-08-06T14:00:00Z"
        assert payload["data_as_of"] == "2026-08-06T14:00:00Z"
        assert payload["rendered_at"] >= payload["data_as_of"]
        job = payload["jobs"][0]
        assert job["company"] == "Stripe"
        assert job["sponsorship"] == "no-sponsorship"
        assert "is_open" not in job  # only open roles ship, flag is redundant


def _req(jid, **extra):
    rec = {
        "id": jid, "company": "GDIT",
        "title": "Summer 2027 Software Developer Internship",
        "season": "Summer 2027", "category": "Software",
        "location": "USA MD Annapolis Junction", "url": f"https://x/{jid}",
        "posted_at": "2026-08-06T00:00:00Z", "first_seen_at": "2026-08-07T10:45:44Z",
        "sponsorship": "unknown", "source": "workday", "is_open": True,
    }
    rec.update(extra)
    return rec


def test_feed_emits_one_entry_for_identical_requisitions():
    # A reader's feed app should not ping three times because one employer
    # filed three copies of the same job.
    publish.write_feed({r: _req(r) for r in ("a", "b", "c")})
    tree = ET.parse(paths.FEED_PATH)
    entries = tree.findall("{http://www.w3.org/2005/Atom}entry")
    assert len(entries) == 1
    summary = entries[0].find("{http://www.w3.org/2005/Atom}summary").text
    assert "3 openings" in summary


def test_feed_never_folds_a_closed_requisition_into_a_live_one():
    # `data_as_of` is pinned to the fixtures' own era on purpose. A closed
    # requisition only stays in the feed for _FEED_RETENTION_DAYS, measured
    # from this timestamp — so left to the wall clock this test quietly stopped
    # testing grouping at all and started failing on the retention cutoff
    # instead, two weeks after it was written.
    publish.write_feed({
        "a": _req("a"),
        "b": _req("b", is_open=False, closed_at="2026-08-07T12:00:00Z"),
    }, data_as_of="2026-08-07T12:00:00Z")
    tree = ET.parse(paths.FEED_PATH)
    entries = tree.findall("{http://www.w3.org/2005/Atom}entry")
    assert len(entries) == 2


def test_the_json_api_still_exports_every_requisition():
    # The API is the machine surface: grouping is a reading aid and must not
    # reach it, or a consumer loses two real application links.
    store = {r: _req(r) for r in ("a", "b", "c")}
    publish.write_api(store, {"open_total": 3})
    with open(os.path.join(paths.API_DIR, "jobs.json"), encoding="utf-8") as f:
        api = json.load(f)
    assert api["count"] == 3
    assert sorted(j["id"] for j in api["jobs"]) == ["a", "b", "c"]
