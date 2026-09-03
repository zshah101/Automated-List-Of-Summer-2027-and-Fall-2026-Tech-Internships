"""Connector parsing tests using mocked ATS responses (no network).

Each connector is fed a canned payload through a fake Net, so we verify the
schema-to-Job mapping for every source without hitting the internet.
"""

import asyncio

from intern_engine.connectors import (
    amazon,
    ashby,
    breezy,
    eightfold,
    greenhouse,
    lever,
    oracle,
    recruitee,
    rippling,
    smartrecruiters,
    workable,
    workday,
)
from intern_engine.models import (
    INCOMPLETE_CAPPED,
    INCOMPLETE_MALFORMED,
    INCOMPLETE_STALLED,
    Fetch,
    Job,
)


class FakeNet:
    """Stands in for net.Net: returns a preset payload for any request."""

    def __init__(self, payload):
        self.payload = payload
        self.urls = []

    async def get_json(self, url, **kwargs):
        self.urls.append(url)
        return self.payload

    async def post_json(self, url, **kwargs):
        self.urls.append(url)
        return self.payload


def _run(coro):
    """Run a connector and return its jobs.

    Connectors may return a bare list or a models.Fetch (jobs + completeness);
    these tests care about the parsing, so normalize to the job list. Tests that
    assert on completeness use `_fetch` instead.
    """
    return _fetch(coro).jobs


def _fetch(coro) -> Fetch:
    return Fetch.of(asyncio.run(coro))


def test_fetch_boundary_drops_unpersistable_rows_and_marks_snapshot_malformed():
    valid = Job(
        id="greenhouse:acme:1", source="greenhouse", company="Acme",
        company_slug="acme", title="Software Intern", location="Austin, TX",
        url="https://example.com/jobs/1",
    )
    bad = Job(
        id="greenhouse:acme:2", source="greenhouse", company="Acme",
        company_slug="acme", title="Software Intern", location="Austin, TX",
        url="",
    )

    result = Fetch.of(Fetch(
        [valid, bad], complete=False, incomplete_reason=INCOMPLETE_CAPPED,
    ))

    assert result.jobs == [valid]
    assert result.complete is False
    assert result.incomplete_reason == INCOMPLETE_MALFORMED


def test_greenhouse():
    payload = {"jobs": [{
        "id": 42, "title": "Software Engineer Intern",
        "location": {"name": "New York, NY"}, "absolute_url": "https://gh/42",
        "first_published": "2026-06-01T08:00:00-04:00",
        "updated_at": "2026-06-15T00:00:00Z",
    }]}
    jobs = _run(greenhouse.fetch({"name": "Acme", "slug": "acme"}, FakeNet(payload)))
    assert len(jobs) == 1
    j = jobs[0]
    assert j.id == "greenhouse:acme:42"
    assert j.title == "Software Engineer Intern"
    assert j.location == "New York, NY"
    assert j.url == "https://gh/42"
    assert j.posted_at == "2026-06-01T08:00:00-04:00"  # true publish date, not updated_at


def test_greenhouse_keeps_posting_id_and_exposes_canonical_alias_identity():
    shared = {
        "title": "Quantitative Trading Intern",
        "location": {"name": "Chicago, IL"},
        "absolute_url": "https://boards.greenhouse.io/job/1",
        "internal_job_id": 4441791005,
        "requisition_id": "431",
    }
    first = _run(greenhouse.fetch(
        {"name": "Chicago Trading Company", "slug": "chicagotradingcampus"},
        FakeNet({"jobs": [{**shared, "id": 4716932005}]}),
    ))[0]
    second = _run(greenhouse.fetch(
        {"name": "Chicago Trading Company", "slug": "ctccampusboard"},
        FakeNet({"jobs": [{**shared, "id": 4708230005}]}),
    ))[0]

    assert first.id == "greenhouse:chicagotradingcampus:4716932005"
    assert second.id == "greenhouse:ctccampusboard:4708230005"
    assert first.canonical_id == second.canonical_id == "4441791005"
    assert first.requisition_id == second.requisition_id == "431"
    assert first.board_key == "greenhouse:chicagotradingcampus"


def test_explicit_board_key_wins_over_the_legacy_fallback():
    payload = {"jobs": [{
        "id": 1, "title": "SWE Intern", "absolute_url": "https://gh/1",
    }]}
    company = {"name": "Acme", "slug": "acme", "board_key": "greenhouse:acme:campus"}
    job = _run(greenhouse.fetch(company, FakeNet(payload)))[0]
    assert job.board_key == "greenhouse:acme:campus"


def test_lever():
    payload = [{
        "id": "abc", "text": "SWE Intern",
        "categories": {"location": "San Francisco"},
        "hostedUrl": "https://lever/abc", "createdAt": 1717200000000,
        "descriptionPlain": "Build things.",
        "additionalPlain": "We are unable to sponsor visas.",
        "salaryRange": {"min": 40000, "max": 60000, "currency": "USD", "interval": "per-year-salary"},
    }]
    jobs = _run(lever.fetch({"name": "Acme", "slug": "acme"}, FakeNet(payload)))
    assert jobs[0].id == "lever:acme:abc"
    assert jobs[0].location == "San Francisco"
    assert jobs[0].posted_at and jobs[0].posted_at.startswith("2024")
    assert "unable to sponsor" in jobs[0].description  # free text for the classifier
    assert jobs[0].salary == "40,000–60,000 USD/yr"


def test_ashby_skips_unlisted():
    payload = {"jobs": [
        {"title": "SWE Intern", "location": "SF", "jobUrl": "https://ashby/x/uuid1",
         "publishedAt": "2026-06-01T00:00:00Z", "isListed": True},
        {"title": "Hidden", "jobUrl": "https://ashby/x/uuid2", "isListed": False},
    ]}
    jobs = _run(ashby.fetch({"name": "Acme", "slug": "x"}, FakeNet(payload)))
    assert len(jobs) == 1
    assert jobs[0].id == "ashby:x:uuid1"
    assert jobs[0].posted_at == "2026-06-01T00:00:00Z"


def test_smartrecruiters():
    payload = {"content": [{
        "id": "p1", "name": "Data Science Intern",
        "location": {"city": "Austin", "region": "TX", "country": "us"},
        "uuid": "d93b3129-0e1e-4259-bf50-033bea69a26d",
        "refNumber": "REF280598V", "hybrid": True,
        "releasedDate": "2026-06-10T00:00:00Z",
    }]}
    jobs = _run(smartrecruiters.fetch({"name": "Acme", "slug": "Acme"}, FakeNet(payload)))
    assert jobs[0].id == "smartrecruiters:Acme:p1"
    assert "United States" in jobs[0].location
    assert jobs[0].location.endswith("(Hybrid)")
    assert jobs[0].canonical_id == "d93b3129-0e1e-4259-bf50-033bea69a26d"
    assert jobs[0].requisition_id == "REF280598V"
    assert jobs[0].posted_at == "2026-06-10T00:00:00Z"


def test_amazon():
    payload = {"jobs": [{
        "title": "SDE Intern", "job_path": "/en/jobs/1/sde",
        "normalized_location": "Seattle, Washington, USA",
        "posted_date": "June 1, 2026", "id_icims": "1",
    }]}
    jobs = _run(amazon.fetch({"name": "Amazon", "slug": "amazon"}, FakeNet(payload)))
    assert jobs[0].url == "https://www.amazon.jobs/en/jobs/1/sde"
    assert jobs[0].posted_at.startswith("2026-06-01")


def test_rippling():
    payload = [{
        "uuid": "u1", "name": "Backend Intern",
        "workLocation": {"label": "Remote, US"}, "url": "https://ats.rippling.com/x/jobs/u1",
    }]
    jobs = _run(rippling.fetch({"name": "Acme", "slug": "x"}, FakeNet(payload)))
    assert jobs[0].id == "rippling:x:u1"
    assert jobs[0].location == "Remote, US"


def test_workday_relative_dates():
    payload = {"jobPostings": [
        {"title": "SWE Intern", "externalPath": "/job/1", "locationsText": "Austin, TX",
         "postedOn": "Posted 3 Days Ago"},
        {"title": "Old Intern", "externalPath": "/job/2", "locationsText": "NY",
         "postedOn": "Posted 30+ Days Ago"},
    ]}
    company = {"name": "Acme", "slug": "acme", "wd": "wd5", "site": "Careers"}
    net = FakeNet(payload)
    result = _fetch(workday.fetch(company, net))
    jobs = result.jobs
    assert jobs[0].posted_at is not None        # "3 Days Ago" resolves to a date
    assert jobs[1].posted_at is None            # "30+ Days Ago" is too vague
    assert jobs[0].url.endswith("/Careers/job/1")
    # Both searches ran to exhaustion, so this is the company's whole list.
    assert result.complete
    # The two search terms return the same postings here; identity is the job
    # id, so the overlap collapses instead of double-listing every role.
    assert len(jobs) == 2
    # 2 postings < page size -> one request per term, no useless pagination.
    assert len(net.urls) == 2
    assert net.urls[0] == "https://acme.wd5.myworkdayjobs.com/wday/cxs/acme/Careers/jobs"


def test_workday_path_style_host():
    payload = {"jobPostings": [
        {"title": "SWE Intern", "externalPath": "/job/1", "locationsText": "AZ"},
    ]}
    company = {"name": "Microchip", "slug": "microchiphr", "wd": "wd5",
               "site": "External", "host": "wd5.myworkdaysite.com"}
    net = FakeNet(payload)
    jobs = _run(workday.fetch(company, net))
    assert net.urls[0] == "https://wd5.myworkdaysite.com/wday/cxs/microchiphr/External/jobs"
    assert jobs[0].url == "https://wd5.myworkdaysite.com/recruiting/microchiphr/External/job/1"


def test_workable():
    payload = {"results": [{
        "title": "AI Inference Engineer Intern", "shortcode": "ABC123",
        "published": "2026-06-10T00:00:00Z", "remote": False,
        "location": {"country": "United States", "city": "Burlingame", "region": "California"},
    }], "nextPage": None}
    jobs = _run(workable.fetch({"name": "Quadric", "slug": "quadric"}, FakeNet(payload)))
    assert jobs[0].id == "workable:quadric:ABC123"
    assert jobs[0].url == "https://apply.workable.com/quadric/j/ABC123/"
    assert jobs[0].location == "Burlingame, California, United States"
    assert jobs[0].posted_at == "2026-06-10T00:00:00Z"


def test_workable_does_not_retry_provider_wide_rate_limits():
    class RecordingNet(FakeNet):
        async def post_json(self, url, **kwargs):
            assert kwargs["retries"] == 0
            return await super().post_json(url, **kwargs)

    payload = {"results": [], "nextPage": None}
    result = _fetch(workable.fetch(
        {"name": "Acme", "slug": "acme"}, RecordingNet(payload),
    ))
    assert result.complete is True


def test_breezy():
    payload = [{
        "id": "fa06", "name": "SWE Intern", "url": "https://acme.breezy.hr/p/fa06-swe",
        "published_date": "2026-06-15T16:41:15.395Z",
        "location": {"name": "Provo, UT"}, "salary": "$25/hr",
    }]
    jobs = _run(breezy.fetch({"name": "Acme", "slug": "acme"}, FakeNet(payload)))
    assert jobs[0].id == "breezy:acme:fa06"
    assert jobs[0].location == "Provo, UT"
    assert jobs[0].salary == "$25/hr"
    assert jobs[0].posted_at.startswith("2026-06-15")


class TestSnapshotCompleteness:
    """A capped response must say so, or the store closes live roles.

    Every source here caps its result count. A capped page is indistinguishable
    from "this company has no more roles" unless the connector reports it — and
    the store closes anything a complete fetch didn't return.
    """

    def test_full_page_with_more_pending_is_incomplete(self):
        # A full page and a server total far above it: the rest was cut off.
        posting = {"title": "SWE Intern", "externalPath": "/job/1",
                   "locationsText": "Austin, TX"}
        payload = {"total": 5000, "jobPostings": [posting] * 20}
        company = {"name": "Medtronic", "slug": "medtronic", "wd": "wd1",
                   "site": "MedtronicCareers"}
        result = _fetch(workday.fetch(company, FakeNet(payload)))
        assert result.complete is False

    def test_short_page_is_complete(self):
        payload = {"total": 1, "jobPostings": [
            {"title": "SWE Intern", "externalPath": "/job/1", "locationsText": "TX"},
        ]}
        company = {"name": "Acme", "slug": "acme", "wd": "wd5", "site": "Careers"}
        assert _fetch(workday.fetch(company, FakeNet(payload))).complete is True

    def test_amazon_reports_truncation(self):
        job = {"title": "SDE Intern", "job_path": "/en/jobs/1/sde",
               "normalized_location": "Seattle, WA", "id_icims": "1"}
        capped = {"hits": 9000, "jobs": [job] * 100}
        assert _fetch(amazon.fetch({}, FakeNet(capped))).complete is False
        whole = {"hits": 1, "jobs": [job]}
        assert _fetch(amazon.fetch({}, FakeNet(whole))).complete is True

    def test_smartrecruiters_reports_truncation(self):
        posting = {"id": "p1", "name": "Data Science Intern",
                   "location": {"city": "Austin", "region": "TX", "country": "us"}}
        company = {"name": "Acme", "slug": "Acme"}
        capped = {"totalFound": 900, "content": [posting] * 100}
        assert _fetch(smartrecruiters.fetch(company, FakeNet(capped))).complete is False
        whole = {"totalFound": 1, "content": [posting]}
        assert _fetch(smartrecruiters.fetch(company, FakeNet(whole))).complete is True

    def test_whole_board_connectors_are_complete_when_well_formed(self):
        # Greenhouse reads the entire board in one call — nothing to truncate.
        payload = {"jobs": [{"id": 1, "title": "SWE Intern",
                             "location": {"name": "NY"},
                             "absolute_url": "https://gh/1"}]}
        result = _fetch(greenhouse.fetch({"name": "Acme", "slug": "acme"},
                                         FakeNet(payload)))
        assert result.complete is True

    def test_an_empty_board_is_still_complete(self):
        # A real board with zero openings must be able to close its old roles.
        result = _fetch(greenhouse.fetch({"name": "Acme", "slug": "acme"},
                                         FakeNet({"jobs": []})))
        assert result.jobs == []
        assert result.complete is True

    def test_malformed_200_is_not_an_empty_board(self):
        # The dangerous case: an API answering `{}` or an error object parses
        # fine and yields zero jobs, which is indistinguishable from "no
        # openings" — and would close EVERY role that employer has.
        company = {"name": "Acme", "slug": "acme"}
        for payload in ({}, {"error": "rate limited"}, {"jobs": None}, []):
            result = _fetch(greenhouse.fetch(company, FakeNet(payload)))
            assert result.jobs == []
            assert result.complete is False, payload

    def test_every_whole_board_connector_rejects_garbage(self):
        garbage = {"unexpected": "shape"}
        company = {"name": "Acme", "slug": "acme", "host": "h", "domain": "d"}
        for mod in (greenhouse, lever, ashby, breezy, recruitee, rippling):
            result = _fetch(mod.fetch(company, FakeNet(garbage)))
            assert result.complete is False, mod.__name__

    def test_eightfold_full_page_without_a_total_is_incomplete(self):
        # `int(data.get("count") or 0)` made a missing count read as 0, so
        # `start >= 0` was trivially true and a truncated page looked complete.
        position = {"id": 1, "name": "SWE Intern", "locations": ["NY"],
                    "t_create": 1782086400}
        company = {"name": "Netflix", "slug": "netflix", "ats": "eightfold",
                   "host": "explore.jobs.netflix.net", "domain": "netflix.com"}
        full = {"positions": [position] * 100}  # a full page, no count field
        assert _fetch(eightfold.fetch(company, FakeNet(full))).complete is False


def test_recruitee():
    payload = {"offers": [{
        "id": 99, "title": "Data Intern", "city": "Amsterdam", "country": "Netherlands",
        "careers_url": "https://acme.recruitee.com/o/data-intern",
        "created_at": "2026-06-01", "description": "<p>No visa sponsorship.</p>",
    }]}
    jobs = _run(recruitee.fetch({"name": "Acme", "slug": "acme"}, FakeNet(payload)))
    assert jobs[0].id == "recruitee:acme:99"
    assert jobs[0].location == "Amsterdam, Netherlands"
    assert "sponsorship" in jobs[0].description


def test_oracle():
    payload = {"items": [{"requisitionList": [
        {"Id": "9", "Title": "ML Intern", "PrimaryLocation": "Dearborn, MI",
         "PostedDate": "2026-06-05", "secondaryLocations": [
             {"Name": "Austin, TX", "CountryCode": "US"},
         ]},
    ]}]}
    company = {"name": "Ford", "slug": "ford", "host": "x.oraclecloud.com", "site": "CX_1"}
    jobs = _run(oracle.fetch(company, FakeNet(payload)))
    assert jobs[0].id == "oracle:ford:9"
    assert jobs[0].posted_at == "2026-06-05"
    assert jobs[0].location == "Dearborn, MI; Austin, TX, United States"


def test_eightfold():
    payload = {"count": 1, "positions": [{
        "id": 790316547536, "ats_job_id": "JR31938",
        "name": "AI/ML Scientist Intern, Fall 2026",
        "locations": ["Los Gatos,California,United States of America"],
        "location": "Los Gatos,California,United States of America",
        "t_create": 1782086400, "t_update": 1782090000,
        "canonicalPositionUrl": "https://explore.jobs.netflix.net/careers/job/790316547536",
        "job_description": "<p>Experience with Python and PyTorch. "
                           "Unable to sponsor visas for this role.</p>",
    }]}
    company = {"name": "Netflix", "slug": "netflix", "ats": "eightfold",
               "host": "explore.jobs.netflix.net", "domain": "netflix.com"}
    jobs = _run(eightfold.fetch(company, FakeNet(payload)))
    assert len(jobs) == 1
    j = jobs[0]
    assert j.id == "eightfold:netflix:790316547536"
    assert j.company == "Netflix"
    assert j.title == "AI/ML Scientist Intern, Fall 2026"
    assert j.location == "Los Gatos, California, United States of America"
    assert j.posted_at == "2026-06-22T00:00:00Z"
    assert j.url.endswith("/790316547536")
    assert "Python" in j.description and "sponsor" in j.description


def test_eightfold_no_positions():
    company = {"name": "Netflix", "slug": "netflix", "ats": "eightfold",
               "host": "explore.jobs.netflix.net", "domain": "netflix.com"}
    jobs = _run(eightfold.fetch(company, FakeNet({"count": 0, "positions": []})))
    assert jobs == []


class TestMalformedResponses:
    """A malformed HTTP 200 is not an empty board — for EVERY connector.

    Six whole-board connectors were fixed first; the five paginated ones still
    read `{}` as "short page, therefore exhausted" and reported complete, which
    lets one bad response close an entire employer's roles.
    """

    COMPANY = {"name": "Acme", "slug": "acme", "wd": "wd5", "site": "S",
               "host": "h.oraclecloud.com", "domain": "d"}
    MODULES = (greenhouse, lever, ashby, breezy, recruitee, rippling,
               amazon, eightfold, oracle, smartrecruiters, workable, workday)

    def test_no_connector_reports_complete_on_an_empty_object(self):
        for mod in self.MODULES:
            result = _fetch(mod.fetch(self.COMPANY, FakeNet({})))
            assert result.complete is False, mod.__name__

    def test_no_connector_reports_complete_on_an_error_payload(self):
        for mod in self.MODULES:
            result = _fetch(mod.fetch(self.COMPANY,
                                      FakeNet({"error": "rate limited"})))
            assert result.jobs == [], mod.__name__
            assert result.complete is False, mod.__name__


class TestAmazonLocation:
    """Amazon's search is worldwide, so the country half has to be right."""

    def _loc(self, **fields):
        return amazon._location(fields)

    def test_us_roles_expand_the_state(self):
        # normalized_location said "Westboro, Wisconsin"; city/state say MA.
        assert self._loc(city="Westboro", state="MA", country_code="US",
                         normalized_location="Westboro, Wisconsin, USA") == \
            "Westboro, Massachusetts, USA"

    def test_foreign_roles_are_named_not_state_coded(self):
        from intern_engine import filters
        # "Toronto, ON, CA" handed the region filter California; "Bangalore,
        # KA, IN" handed it Indiana. Both then passed as US.
        for fields, country in (
            (dict(city="Toronto", state="ON", country_code="CA"), "Canada"),
            (dict(city="Bangalore", state="KA", country_code="IN"), "India"),
            (dict(city="Munich", state="BY", country_code="DE"), "Germany"),
        ):
            loc = self._loc(**fields)
            assert loc.endswith(country), loc
            assert not filters.is_united_states(loc), loc

    def test_unknown_country_is_not_guessed_as_us(self):
        from intern_engine import filters
        loc = self._loc(city="Somewhere", state="ZZ", country_code="ZZ")
        assert not filters.is_united_states(loc), loc

    def test_missing_country_only_reads_us_for_a_real_state_code(self):
        from intern_engine import filters
        assert filters.is_united_states(self._loc(city="Austin", state="TX"))
        # "BC" is not a US state — don't silently default the country to US.
        assert not filters.is_united_states(self._loc(city="Vancouver", state="BC"))


class TestErrorEnvelopes:
    """An error wearing an empty board's clothes must not read as complete.

    `{"error": "rate limited", "jobs": []}` passed the earlier shape check —
    the container IS a list — and closed every role that employer had. Only a
    TRUTHY error disqualifies: Amazon ships `"error": null` on healthy pages.
    """

    COMPANY = {"name": "Acme", "slug": "acme", "wd": "wd5", "site": "S",
               "host": "h.oraclecloud.com", "domain": "d"}
    ENVELOPES = {
        greenhouse: {"error": "rate limited", "jobs": []},
        ashby: {"error": "rate limited", "jobs": []},
        recruitee: {"error": "x", "offers": []},
        workable: {"error": "x", "results": []},
        smartrecruiters: {"error": "x", "content": []},
        workday: {"error": "x", "jobPostings": []},
        eightfold: {"error": "x", "positions": []},
        amazon: {"error": "throttled", "jobs": [], "hits": 0},
        oracle: {"error": "x", "items": []},
    }

    def test_error_with_a_wellformed_empty_container_is_incomplete(self):
        for mod, payload in self.ENVELOPES.items():
            result = _fetch(mod.fetch(self.COMPANY, FakeNet(payload)))
            assert result.jobs == [], mod.__name__
            assert result.complete is False, mod.__name__

    def test_amazon_null_error_field_is_a_healthy_response(self):
        payload = {"error": None, "hits": 1, "jobs": [{
            "title": "SDE Intern", "job_path": "/j/1", "id_icims": "1",
            "city": "Seattle", "state": "WA", "country_code": "US",
        }]}
        result = _fetch(amazon.fetch({}, FakeNet(payload)))
        assert result.complete is True
        assert len(result.jobs) == 1

    def test_junk_list_members_poison_completeness(self):
        # `[{}]` parses as a list of dicts but yields id ":None" rows. Those
        # are dropped, and their presence means the listing can't be trusted
        # to close anything.
        result = _fetch(greenhouse.fetch({"name": "Acme", "slug": "acme"},
                                         FakeNet({"jobs": [{}]})))
        assert result.jobs == []
        assert result.complete is False


class WorkdayPagingNet:
    """Real-shaped pages where later responses lose the valid total."""

    def __init__(self, intern_total=45):
        self.intern_total = intern_total
        self.calls = []

    async def post_json(self, url, **kwargs):
        body = kwargs["json"]
        term, offset = body["searchText"], body["offset"]
        self.calls.append((term, offset))
        if term != "intern":
            return {"total": 0, "jobPostings": []}
        count = min(20, max(0, self.intern_total - offset))
        postings = [
            {
                "title": f"Intern {offset + i}",
                "externalPath": f"/job/{offset + i}",
                "locationsText": "Minneapolis, MN",
            }
            for i in range(count)
        ]
        # This is the observed Workday failure shape: a credible total on page
        # zero, then 0 on a later *full* page despite more results existing.
        return {"total": self.intern_total if offset == 0 else 0,
                "jobPostings": postings}


def test_workday_keeps_first_positive_total_when_later_full_page_says_zero():
    company = {"name": "Medtronic", "slug": "medtronic", "wd": "wd1",
               "site": "MedtronicCareers"}
    net = WorkdayPagingNet(45)
    result = _fetch(workday.fetch(company, net))

    assert result.complete is True
    assert len(result.jobs) == 45
    assert ("intern", 40) in net.calls


def test_workday_reports_an_intentional_result_cap_separately():
    company = {"name": "Medtronic", "slug": "medtronic", "wd": "wd1",
               "site": "MedtronicCareers"}
    result = _fetch(workday.fetch(company, WorkdayPagingNet(500)))
    assert result.complete is False
    assert result.incomplete_reason == INCOMPLETE_CAPPED


def test_workday_stops_when_a_tenant_repeats_the_same_page():
    postings = [
        {
            "title": f"Software Intern {index}",
            "externalPath": f"/job/{index}",
            "locationsText": "Austin, TX",
        }
        for index in range(20)
    ]
    net = FakeNet({"total": 200, "jobPostings": postings})

    result = _fetch(workday.fetch(
        {"name": "Acme", "slug": "acme", "site": "External", "wd": "wd5"},
        net,
    ))

    assert len(result.jobs) == 20
    assert result.complete is False
    assert result.incomplete_reason == INCOMPLETE_STALLED
    assert len(net.urls) == 4  # two calls per search term, not ten


class OraclePagingNet:
    """Oracle returns an inner Limit of 25 despite the requested limit of 50."""

    def __init__(self, internship_total):
        self.internship_total = internship_total
        self.calls = []

    async def get_json(self, url, **kwargs):
        finder = kwargs["params"]["finder"]
        keyword = finder.split("keyword=", 1)[1].split(",", 1)[0]
        offset = int(finder.rsplit("offset=", 1)[1])
        self.calls.append((keyword, offset, kwargs["params"]["limit"]))
        total = self.internship_total if keyword == "internship" else 0
        count = min(25, max(0, total - offset))
        requisitions = [
            {
                "Id": f"{keyword}-{offset + i}",
                "Title": "Software Engineering Internship",
                "PrimaryLocation": "New York, NY",
            }
            for i in range(count)
        ]
        return {"items": [{
            "Offset": offset,
            "Limit": 25,
            "TotalJobsCount": total,
            "requisitionList": requisitions,
        }]}


def test_oracle_uses_returned_inner_limit_and_marks_the_cap_incomplete():
    company = {"name": "JPMorgan Chase", "slug": "jpmc",
               "host": "jpmc.oraclecloud.com", "site": "CX_1001"}
    net = OraclePagingNet(215)
    result = _fetch(oracle.fetch(company, net))
    offsets = [offset for query, offset, _ in net.calls if query == "internship"]

    assert offsets == list(range(0, 200, 25))
    assert all(limit == "50" for query, _, limit in net.calls if query == "internship")
    assert len(result.jobs) == 200
    assert result.complete is False
    assert result.incomplete_reason == INCOMPLETE_CAPPED


def test_oracle_exact_total_is_complete_with_the_server_limit():
    company = {"name": "Acme", "slug": "acme",
               "host": "acme.oraclecloud.com", "site": "CX_1"}
    net = OraclePagingNet(50)
    result = _fetch(oracle.fetch(company, net))
    assert [offset for query, offset, _ in net.calls if query == "internship"] == [0, 25]
    assert result.complete is True
    assert result.incomplete_reason is None


class SmartQueryNet:
    def __init__(self, capped=False):
        self.capped = capped
        self.calls = []

    async def get_json(self, url, **kwargs):
        query = kwargs["params"]["q"]
        offset = kwargs["params"]["offset"]
        self.calls.append((query, offset))
        if self.capped and query == "intern":
            return {
                "totalFound": 900,
                "content": [
                    {"id": f"intern-{offset + i}", "name": "Engineering Intern"}
                    for i in range(100)
                ],
            }
        if self.capped:
            return {"totalFound": 0, "content": []}
        return {"totalFound": 1, "content": [{
            "id": query,
            "uuid": f"canonical-{query}",
            "name": f"{query.title()} role",
        }]}


def test_smartrecruiters_unions_targeted_queries_and_deduplicates_by_posting_id():
    company = {"name": "Bosch", "slug": "BoschGroup"}
    net = SmartQueryNet()
    result = _fetch(smartrecruiters.fetch(company, net))
    assert {query for query, _ in net.calls} == {
        "internship", "co-op", "student", "intern",
    }
    assert {job.id.rsplit(":", 1)[-1] for job in result.jobs} == {
        "internship", "co-op", "student", "intern",
    }
    assert result.complete is True


def test_smartrecruiters_marks_a_broad_query_cap_incomplete():
    company = {"name": "Bosch", "slug": "BoschGroup"}
    result = _fetch(smartrecruiters.fetch(company, SmartQueryNet(capped=True)))
    assert len(result.jobs) == 300
    assert result.complete is False
    assert result.incomplete_reason == INCOMPLETE_CAPPED


def test_smartrecruiters_alias_postings_keep_stable_ids_and_share_canonical_id():
    shared = {
        "uuid": "d93b3129-0e1e-4259-bf50-033bea69a26d",
        "jobId": "d93b3129-0e1e-4259-bf50-033bea69a26d",
        "refNumber": "REF280598V",
        "name": "Vehicle Motion Engineering Internship",
    }
    first = _run(smartrecruiters.fetch(
        {"name": "Bosch", "slug": "Bosch"},
        FakeNet({"totalFound": 1, "content": [{**shared, "id": "744000139649345"}]}),
    ))[0]
    second = _run(smartrecruiters.fetch(
        {"name": "Bosch", "slug": "BoschGroup"},
        FakeNet({"totalFound": 1, "content": [{**shared, "id": "744000140462550"}]}),
    ))[0]
    assert first.id != second.id
    assert first.canonical_id == second.canonical_id == shared["uuid"]
    assert first.requisition_id == second.requisition_id == "REF280598V"


def test_smartrecruiters_iso_country_codes_never_masquerade_as_us_states():
    from intern_engine import filters

    cases = (
        ("Tel Aviv", "IL", "il", "Israel"),
        ("Buenos Aires", "AR", "ar", "Argentina"),
        ("Bogota", "CO", "co", "Colombia"),
        ("Jakarta", "ID", "id", "Indonesia"),
        ("Podgorica", "ME", "me", "Montenegro"),
    )
    for city, region, code, country in cases:
        location = smartrecruiters._location({
            "city": city,
            "region": region,
            "country": code,
            "fullLocation": f"{city}, {region}",
        })
        assert location.endswith(country)
        assert not filters.is_united_states(location), location

    ambiguous = smartrecruiters._location({
        "city": "Tel Aviv", "region": "IL", "fullLocation": "Tel Aviv, IL",
    })
    assert ambiguous == "Tel Aviv"
    assert not filters.is_united_states(ambiguous)


def test_recruitee_uses_publish_date_and_preserves_mixed_location_evidence():
    payload = {"offers": [{
        "id": 99,
        "title": "Data Intern",
        "location": "Remote job",
        "locations": [
            {"city": "London", "country_code": "GB"},
            {"city": "Boston", "state": "MA", "country_code": "US"},
        ],
        "remote": True,
            "published_at": "2026-07-03T10:30:00Z",
            "created_at": "2026-01-01T00:00:00Z",
            "careers_url": "https://acme.recruitee.com/o/data-intern",
        }]}
    job = _run(recruitee.fetch(
        {"name": "Acme", "slug": "acme"}, FakeNet(payload),
    ))[0]
    assert job.posted_at == "2026-07-03T10:30:00Z"
    assert "London, United Kingdom" in job.location
    assert "Boston, MA, United States" in job.location
    assert job.location.endswith("(Remote)")


def test_fetch_reason_distinguishes_malformed_payload_from_a_cap():
    company = {"name": "Acme", "slug": "acme"}
    malformed = _fetch(greenhouse.fetch(company, FakeNet({"error": "rate limited"})))
    assert malformed.incomplete_reason == INCOMPLETE_MALFORMED


class TestWorkdayRequisitionIdentity:
    """One requisition, two of the tenant's career sites, one listing.

    Tencent runs OA_Huoshui_Platform and Tencent_Careers. R107752 appears on
    both — `..._R107752` on one and `..._R107752-1` on the other — with a
    byte-identical description (verified live 2026-08-07). The externalPath
    alone makes that look like two jobs, which is how it reached the published
    list twice. `bulletFields` carries the real number.
    """

    company = {"name": "Tencent", "slug": "tencent", "wd": "wd1",
               "site": "Tencent_Careers"}

    def _job(self, posting):
        payload = {"jobPostings": [posting]}
        return _run(workday.fetch(self.company, FakeNet(payload)))[0]

    def test_reads_the_requisition_number(self):
        job = self._job({"title": "Research Intern", "bulletFields": ["R107752"],
                         "externalPath": "/job/US-California-Palo-Alto/RI_R107752",
                         "locationsText": "US-California-Palo Alto"})
        assert job.requisition_id == "R107752"

    def test_accepts_the_per_site_uniquifier_suffix(self):
        job = self._job({"title": "Research Intern", "bulletFields": ["R107752"],
                         "externalPath": "/job/US-California-Palo-Alto/RI_R107752-1",
                         "locationsText": "US-California-Palo Alto"})
        assert job.requisition_id == "R107752"

    def test_both_sites_agree_on_one_canonical_identity(self):
        bare = self._job({"title": "Research Intern", "bulletFields": ["R107752"],
                          "externalPath": "/job/US-California-Palo-Alto/RI_R107752",
                          "locationsText": "US-California-Palo Alto"})
        suffixed = self._job({"title": "Research Intern", "bulletFields": ["R107752"],
                              "externalPath": "/job/US-California-Palo-Alto/RI_R107752-1",
                              "locationsText": "US-California-Palo Alto"})
        assert bare.id != suffixed.id                    # different postings...
        assert bare.canonical_id == suffixed.canonical_id  # ...one requisition

    def test_the_same_requisition_in_two_cities_stays_two_openings(self):
        # A req advertised in Austin and Seattle is two places someone can
        # work. Merging on the number alone would delete one of them.
        austin = self._job({"title": "SWE Intern", "bulletFields": ["R1"],
                            "externalPath": "/job/Austin/SWE_R1",
                            "locationsText": "Austin, TX"})
        seattle = self._job({"title": "SWE Intern", "bulletFields": ["R1"],
                             "externalPath": "/job/Seattle/SWE_R1-1",
                             "locationsText": "Seattle, WA"})
        assert austin.canonical_id != seattle.canonical_id

    def test_a_bullet_the_path_does_not_confirm_is_refused(self):
        # bulletFields is a free-form display slot; some tenants put a location
        # or a job family in it. Only a path that ends in the same token proves
        # it is the requisition number.
        job = self._job({"title": "SWE Intern", "bulletFields": ["Austin TX 4"],
                         "externalPath": "/job/Austin/SWE_R9",
                         "locationsText": "Austin, TX"})
        assert job.requisition_id is None
        assert job.canonical_id is None

    def test_a_tenant_that_sends_no_bullets_still_works(self):
        job = self._job({"title": "SWE Intern", "externalPath": "/job/Austin/SWE_R9",
                         "locationsText": "Austin, TX"})
        assert job.requisition_id is None
        assert job.canonical_id is None

    def test_req_numbers_are_scoped_to_the_tenant(self):
        # "R1" means different jobs at different employers, and canonical ids
        # are grouped per SOURCE — without the tenant they would collide.
        posting = {"title": "SWE Intern", "bulletFields": ["R1"],
                   "externalPath": "/job/Austin/SWE_R1", "locationsText": "Austin, TX"}
        mine = _run(workday.fetch(self.company, FakeNet({"jobPostings": [posting]})))[0]
        theirs = _run(workday.fetch(
            {"name": "Copart", "slug": "copart", "wd": "wd12", "site": "copart"},
            FakeNet({"jobPostings": [posting]}),
        ))[0]
        assert mine.canonical_id != theirs.canonical_id


class TestSEALocationsSurviveNormalization:
    """A region filter can only see what the connectors emit.

    Both of these platforms map ISO codes through a fixed table and degrade an
    unmapped one to "International (XX)" so it can't be misread as a US state.
    That safety net is also a trap: an unmapped SG posting becomes unreadable
    to the region filter, so the tracked countries have to be in the table.
    """

    def test_smartrecruiters_names_the_sea_countries(self):
        from intern_engine import filters

        for code, country in (("sg", "Singapore"), ("my", "Malaysia"),
                              ("th", "Thailand"), ("vn", "Vietnam"),
                              ("ph", "Philippines"), ("id", "Indonesia")):
            loc = smartrecruiters._location({"city": "X", "country": code})
            assert country in loc, loc
            assert filters.region_ok(loc, ["sea"]), loc

    def test_oracle_names_the_sea_countries(self):
        for code, country in (("SG", "Singapore"), ("MY", "Malaysia"),
                              ("TH", "Thailand"), ("VN", "Vietnam"),
                              ("PH", "Philippines"), ("ID", "Indonesia")):
            assert oracle._COUNTRIES[code] == country

    def test_amazon_names_the_sea_countries(self):
        from intern_engine import filters

        loc = amazon._location({"city": "Singapore", "country_code": "SG"})
        assert filters.region_ok(loc, ["sea"]), loc
