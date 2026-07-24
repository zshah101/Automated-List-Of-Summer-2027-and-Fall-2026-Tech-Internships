from intern_engine.harvester import detect


class FakeResponse:
    def __init__(self, status_code=200, text="", payload=None):
        self.status_code = status_code
        self.text = text
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


class FakeSession:
    def __init__(self, jobvite_html):
        self.jobvite_html = jobvite_html

    def get(self, url, timeout=12):
        if "jobvite" in url:
            return FakeResponse(text=self.jobvite_html)
        return FakeResponse(payload={"jobs": []})


def test_detect_jobvite_uses_medspeed_slug():
    html = """
    <ul class="jv-job-list jv-search-list">
        <li class="row"><a href="/medspeed/job/oBYfAfw8" class="flex-row">
            <div class="jv-job-list-name">Box Truck Medical Delivery Driver</div>
            <div class="ml-auto jv-job-list-location">Little Rock, Arkansas</div>
        </a></li>
    </ul>
    """
    result = detect({"name": "MedSpeed", "slug": "medspeed"}, FakeSession(html))
    assert result == {"name": "MedSpeed", "slug": "medspeed", "ats": "jobvite"}