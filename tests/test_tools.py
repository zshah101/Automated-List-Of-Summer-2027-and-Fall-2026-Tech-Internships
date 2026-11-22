"""Guards for tools/ — the scripts CI runs but unit tests never imported.

The Thursday audit workflow broke in production because connectors started
returning a `Fetch` and `tools/audit_seasons.py` still did `for j in fetched`.
Nothing caught it: the tools directory had zero tests, so a green suite meant
nothing about the code CI actually executes on a schedule.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import pkgutil

import pytest

from intern_engine import connectors, models, pipeline
from intern_engine.models import Fetch, Job


def _job(jid: str = "greenhouse:acme:1") -> Job:
    return Job(id=jid, source="greenhouse", company="Acme", company_slug="acme",
               title="Software Engineer Intern", location="Austin, TX",
               url="https://x/1", description="Summer 2027 internship.")


class TestConnectorReturnContract:
    """Every connector must return something Fetch.of understands."""

    def test_every_connector_module_is_importable(self):
        names = [m.name for m in pkgutil.iter_modules(connectors.__path__)]
        assert names, "no connector modules discovered"
        for name in names:
            importlib.import_module(f"intern_engine.connectors.{name}")

    def test_fetch_of_normalizes_both_shapes(self):
        # Connectors may return a bare list (whole-board reads) or a Fetch
        # (paginated reads). Callers must never have to care which.
        assert Fetch.of([_job()]).jobs[0].id == "greenhouse:acme:1"
        assert Fetch.of(Fetch([_job()], complete=False)).complete is False

    def test_fetch_result_is_not_iterable_by_accident(self):
        # The exact production bug: iterating a Fetch raised TypeError at
        # runtime. Keep that explicit so callers use `.jobs`.
        with pytest.raises(TypeError):
            list(Fetch([_job()]))


class TestAuditSeasonsListPath:
    """The list-sourced branch that actually failed on Thursday."""

    def test_list_sourced_descriptions_are_read_from_a_fetch(self, monkeypatch):
        import tools.audit_seasons as audit

        # 'lever' ships descriptions in its list payload, so it takes the
        # list-sourced branch rather than the per-role detail fetch. The
        # connector's job must carry the SAME id the store holds — that id is
        # what the branch joins on.
        listed = Job(**{**_job().__dict__, "id": "lever:acme:1", "source": "lever"})

        async def fake_connector(company, net):
            return Fetch([listed], complete=True)  # shape connectors return today

        monkeypatch.setitem(audit.CONNECTORS, "lever", fake_connector)

        async def fake_fetch_all(jobs, companies):
            return await audit._texts_for(jobs, companies)

        texts = asyncio.run(fake_fetch_all(
            [listed],
            [{"ats": "lever", "slug": "acme", "name": "Acme"}],
        ))
        assert texts["lever:acme:1"].status == "OK"
        assert texts["lever:acme:1"].text == "Summer 2027 internship."


class TestVerifyAccuracyImportable:
    def test_module_imports_and_exposes_a_main(self):
        mod = importlib.import_module("tools.verify_accuracy")
        assert callable(getattr(mod, "main", None))


class TestSnapshotGateCalibration:
    """The gate that blocked four production runs on 2026-08-07.

    Fixing the Oracle and Workday pagination bugs on 2026-08-06 made snapshot
    completeness HONEST: boards that had been silently reporting a truncated
    page as the whole list started saying "capped" instead. The true complete
    rate moved from an over-reported 96.7% to ~86%, and the 85% floor — set
    against the inflated number — began failing ordinary runs.

    A `result-cap` is the designed outcome for a board with more intern hits
    than our page budget, and the engine already refuses to close roles on one.
    It is not a health signal, so it must not sit in a health gate.
    """

    gate = importlib.import_module("tools.verify_accuracy")

    def test_a_healthy_run_is_not_blocked(self):
        # The exact numbers from the four failed runs (3476/4091 = 84.97%).
        assert 3476 / 4091 >= self.gate._MIN_COMPLETE_SNAPSHOT_RATE

    def test_a_real_collapse_is_still_caught(self):
        # Workday alone is ~36% of the registry; losing it must trip the gate.
        assert 0.55 < self.gate._MIN_COMPLETE_SNAPSHOT_RATE

    def test_ordinary_degradation_is_not_blocked(self):
        # 47 malformed/stalled out of 3992 on a normal run.
        assert 47 / 3992 <= self.gate._MAX_DEGRADED_FETCH_RATE

    def test_an_ats_changing_shape_is_caught(self):
        # Greenhouse is ~1,000 boards; if its payload changed, every one of
        # them would answer malformed and the ceiling has to trip.
        assert 1000 / 3992 > self.gate._MAX_DEGRADED_FETCH_RATE

    def test_caps_alone_can_never_trip_the_degradation_ceiling(self):
        # The regression guard for the whole redesign: the number the ceiling
        # reads must be built from broken responses only. If a future change
        # folded INCOMPLETE_CAPPED into degraded_fetches, a busy peak-season
        # afternoon would start blocking publishes all over again.
        source = inspect.getsource(pipeline)
        _, _, degraded = source.partition('"degraded_fetches"')
        computation = degraded[:degraded.index("),")]
        assert "INCOMPLETE_MALFORMED" in computation
        assert "INCOMPLETE_STALLED" in computation
        assert "INCOMPLETE_CAPPED" not in computation


class TestRegistryGate:
    """registry-decay held the whole site from 2026-11-16 to 11-21.

    It counted this run's provider trouble (Workday and Workable 429s, the
    Saturday Workday bot walls) as if it were quarantine growth. Decay must
    still block a publish; one bad run must not.
    """

    gate = importlib.import_module("tools.verify_accuracy")

    @staticmethod
    def _stats(total, ok, errors, benched, **extra):
        return {
            "companies_total": total, "fetched_ok": ok, "fetch_errors": errors,
            "quarantined": benched,
            "fetch_success_rate_registry": round(ok / total, 3), **extra,
        }

    def test_the_last_run_that_published_is_clean(self):
        # 2026-11-16 01:14: Workday 398 + Workable 102 errors, 464 benched.
        assert self.gate._registry_decay(self._stats(5454, 4490, 500, 464)) == ([], [])

    def test_a_429_storm_is_reported_not_frozen(self):
        stats = self._stats(5513, 4300, 749, 464,
                            errors_by_source={"workable": 140, "workday": 600, "ashby": 9})
        gates, warnings = self.gate._registry_decay(stats)
        assert gates == []
        assert len(warnings) == 1
        assert "[registry-shortfall] only 78.0%" in warnings[0]
        assert "workday 600, workable 140, ashby 9" in warnings[0]

    def test_real_decay_still_blocks(self):
        gates, _ = self.gate._registry_decay(self._stats(5000, 3900, 0, 1100))
        assert len(gates) == 1
        assert "[registry-decay] only 78.0% of the registry" in gates[0]
        assert "1100 of 5000 boards are quarantined" in gates[0]

    def test_weather_that_persists_becomes_decay(self):
        # Workday is ~35% of the registry. If it stays dark, three failed runs
        # quarantine its boards and the gate trips without anyone tuning it.
        gates, _ = self.gate._registry_decay(self._stats(5513, 3500, 100, 1913))
        assert gates

    def test_malformed_stats_are_left_to_the_schema_gate(self):
        assert self.gate._registry_decay({"companies_total": "5000"}) == ([], [])
        assert self.gate._registry_decay(self._stats(1, 1, 0, 0) | {"companies_total": 0}) == ([], [])

    def test_drift_only_binds_a_job_that_just_fetched(self):
        # CI and the audit re-verify committed stats; discovery grows the
        # registry in between. That tripped every audit from 08-27 to 11-12.
        assert self.gate._registry_drift(5454, 5513, allow_stale=False)
        assert self.gate._registry_drift(5454, 5513, allow_stale=True) == []
        assert self.gate._registry_drift(5513, 5513, allow_stale=False) == []

    def test_reasons_reach_the_actions_page(self, monkeypatch, capsys):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        self.gate._annotate([f"  [gate-{i}] reason" for i in range(12)])
        lines = capsys.readouterr().out.splitlines()
        assert lines[0] == "::error::[gate-0] reason"
        assert len(lines) == 11
        assert "2 more" in lines[-1]

    def test_warnings_annotate_as_warnings(self, monkeypatch, capsys):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        self.gate._annotate(["  [registry-shortfall] x"], level="warning")
        assert capsys.readouterr().out.splitlines() == ["::warning::[registry-shortfall] x"]

    def test_annotations_stay_out_of_local_runs(self, monkeypatch, capsys):
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
        self.gate._annotate(["  [x] y"])
        assert capsys.readouterr().out == ""


class TestDatePrecisionContract:
    """models.date_source underpins the never-downgrade rule in the store."""

    def test_ranking_is_ordered_worst_to_best(self):
        p = models.DATE_PRECISION
        assert p[None] < p["relative_derived"] < p["date_only"] < p["exact"]

    def test_shape_classification(self):
        assert models.date_source("2026-07-01") == "date_only"
        assert models.date_source("2026-07-01T00:00:00Z") == "date_only"
        assert models.date_source("2026-07-01T09:31:00Z") == "exact"
        assert models.date_source(None) is None
