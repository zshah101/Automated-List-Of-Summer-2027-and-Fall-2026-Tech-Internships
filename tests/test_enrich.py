"""Enrichment behavior: free descriptions classify inline, stored verdicts are
carried over without refetching, and detail fetches backfill what they can."""

import asyncio

from intern_engine import enrich
from intern_engine.models import Job


class FakeNet:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    async def get_json(self, url, **kwargs):
        self.calls += 1
        return self.payload

    async def get_text(self, url, **kwargs):
        self.calls += 1
        return self.payload if isinstance(self.payload, str) else ""

    async def post_json(self, url, **kwargs):
        self.calls += 1
        return self.payload


def _job(jid="lever:acme:1", source="lever", description=None, url="https://x", slug="acme"):
    return Job(id=jid, source=source, company="Acme", company_slug=slug,
               title="SWE Intern", location="NY", url=url, description=description)


def _run(coro):
    return asyncio.run(coro)


class TestEnrich:
    def test_inline_description_classifies_without_fetch(self):
        net = FakeNet({})
        job = _job(description="We are unable to sponsor visas for this role.")
        enriched, fetched = _run(enrich.enrich_jobs([job], {}, net))
        assert job.sponsorship == "no-sponsorship"
        assert enriched == {job.id}
        assert fetched == 0 and net.calls == 0

    def test_stored_verdict_carried_over_no_refetch(self):
        net = FakeNet({})
        job = _job(jid="greenhouse:acme:9", source="greenhouse")
        existing = {"greenhouse:acme:9": {
            "sponsorship": "citizens-only", "enriched_at": "x", "skills": ["Python"],
        }}
        enriched, fetched = _run(enrich.enrich_jobs([job], existing, net))
        assert job.sponsorship == "citizens-only"
        assert enriched == set() and net.calls == 0

    def test_settled_record_without_skills_backfills_once_keeping_verdict(self):
        # Records that predate skill tags get ONE re-fetch for tags; the stored
        # sponsorship verdict must never flip even if the text now reads differently.
        net = FakeNet({"content": "Uses Python daily. Visa sponsorship is available."})
        job = _job(jid="greenhouse:acme:9", source="greenhouse")
        existing = {"greenhouse:acme:9": {"sponsorship": "citizens-only", "enriched_at": "x"}}
        enriched, fetched = _run(enrich.enrich_jobs([job], existing, net))
        assert job.sponsorship == "citizens-only"  # verdict kept, not re-classified
        assert job.skills == ["Python"]
        assert enriched == {job.id} and fetched == 1

    def test_greenhouse_detail_fetch(self):
        net = FakeNet({"content": "U.S. citizenship is required for this position."})
        job = _job(jid="greenhouse:acme:42", source="greenhouse")
        enriched, fetched = _run(enrich.enrich_jobs([job], {}, net))
        assert job.sponsorship == "citizens-only"
        assert enriched == {job.id} and fetched == 1

    def test_workday_detail_backfills_posted_date(self):
        net = FakeNet({"jobPostingInfo": {
            "jobDescription": "No visa sponsorship for this role.",
            "startDate": "2026-06-20",
        }})
        job = _job(
            jid="workday:acme:/job/NY/SWE_R1", source="workday",
            url="https://acme.wd5.myworkdayjobs.com/Careers/job/NY/SWE-Intern_R1",
        )
        assert job.posted_at is None
        _run(enrich.enrich_jobs([job], {}, net))
        assert job.sponsorship == "no-sponsorship"
        assert job.posted_at == "2026-06-20T00:00:00Z"

    def test_jobvite_detail_backfills_posted_date_and_description(self):
        net = FakeNet(
            """
            <script type="application/ld+json">
            {"@type":"JobPosting","datePosted":"2026-06-04",
             "description":"We cannot sponsor visas for this role."}
            </script>
            <div class="jv-job-detail-description" ng-non-bindable>
                <h6>Description</h6>
                <p>We cannot sponsor visas for this role.</p>
            </div>
            """
        )
        job = _job(
            jid="jobvite:medspeed:oBYfAfw8",
            source="jobvite",
            url="https://jobs.jobvite.com/medspeed/job/oBYfAfw8",
        )
        _run(enrich.enrich_jobs([job], {}, net))
        assert job.sponsorship == "no-sponsorship"
        assert job.posted_at == "2026-06-04T00:00:00Z"

    def test_failed_fetch_stays_unknown_and_retryable(self):
        class ExplodingNet(FakeNet):
            async def get_json(self, url, **kwargs):
                raise RuntimeError("board deleted")

        job = _job(jid="greenhouse:acme:7", source="greenhouse")
        enriched, _fetched = _run(enrich.enrich_jobs([job], {}, ExplodingNet({}))
                                  )
        assert job.sponsorship == "unknown"
        assert enriched == set()  # no enriched_at stamp -> retried next run

    def test_source_without_fetcher_still_classified(self):
        net = FakeNet({})
        job = _job(jid="rippling:acme:1", source="rippling")
        enriched, _ = _run(enrich.enrich_jobs([job], {}, net))
        assert job.sponsorship == "unknown"
        assert enriched == {job.id}  # settled: rippling has no text to fetch
        assert net.calls == 0

    def test_text_stated_cycle_replaces_inferred(self):
        net = FakeNet({})
        job = _job(description=(
            "Join our Fall 2026 co-op program in Boston. "
            "No visa sponsorship for this role."
        ))
        job.season, job.season_inferred = "Summer 2027", True
        _run(enrich.enrich_jobs([job], {}, net))
        assert job.season == "Fall 2026"
        assert job.season_inferred is False  # the company stated it -> not a guess

    def test_text_without_cycle_statement_keeps_inference(self):
        net = FakeNet({})
        job = _job(description="A great internship. Python required.")
        job.season, job.season_inferred = "Summer 2027", True
        _run(enrich.enrich_jobs([job], {}, net))
        assert job.season == "Summer 2027"
        assert job.season_inferred is True  # still an inference, still marked ~

    def test_title_stated_cycle_never_overridden_by_text(self):
        net = FakeNet({})
        job = _job(description="This internship runs Fall 2026 through December.")
        job.season, job.season_inferred = "Summer 2027", False  # year was in the title
        _run(enrich.enrich_jobs([job], {}, net))
        assert job.season == "Summer 2027"
