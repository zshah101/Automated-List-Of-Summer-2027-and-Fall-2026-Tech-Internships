from intern_engine import store
from intern_engine.models import Job
from intern_engine.pipeline import _dedup


def _job_dict(jid, title="Software Engineer Intern"):
    return {
        "id": jid, "source": "greenhouse", "company_slug": "stripe",
        "company": "Stripe", "title": title, "location": "San Francisco, CA",
        "url": "https://example.com", "posted_at": None,
        "season": "Summer 2027", "category": "Software",
    }


class TestUpsert:
    def test_new_seen_closed_lifecycle(self):
        existing: dict = {}
        keys = {"greenhouse:stripe"}

        new_ids = store.upsert(existing, [_job_dict("a")], keys)
        assert new_ids == ["a"]
        assert existing["a"]["is_open"] is True
        first_seen = existing["a"]["first_seen_at"]

        # Same job again -> not "new", first_seen frozen.
        assert store.upsert(existing, [_job_dict("a")], keys) == []
        assert existing["a"]["first_seen_at"] == first_seen

        # Job disappears from a company we DID reach -> marked closed.
        store.upsert(existing, [], keys)
        assert existing["a"]["is_open"] is False

    def test_unreached_company_is_not_closed(self):
        existing: dict = {}
        store.upsert(existing, [_job_dict("a")], {"greenhouse:stripe"})
        # This run did NOT successfully reach stripe -> must not close its jobs.
        store.upsert(existing, [], succeeded_keys=set())
        assert existing["a"]["is_open"] is True


class TestDedup:
    def test_collapses_same_role_and_prefers_dated(self):
        undated = Job(id="1", source="greenhouse", company="Stripe",
                      company_slug="stripe", title="Software Engineer Intern",
                      location="SF", url="a", posted_at=None)
        dated = Job(id="2", source="lever", company="Stripe",
                    company_slug="stripe", title="Software Engineer  Intern!",
                    location="SF", url="b", posted_at="2026-06-01T00:00:00Z")
        out = _dedup([undated, dated])
        assert len(out) == 1
        assert out[0].posted_at == "2026-06-01T00:00:00Z"

    def test_keeps_distinct_titles(self):
        a = Job(id="1", source="ashby", company="Verkada", company_slug="verkada",
                title="Backend SWE Intern", location="CA", url="a", posted_at=None)
        b = Job(id="2", source="ashby", company="Verkada", company_slug="verkada",
                title="Frontend SWE Intern", location="CA", url="b", posted_at=None)
        assert len(_dedup([a, b])) == 2
