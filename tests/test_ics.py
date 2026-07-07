"""The subscribable radar calendar (docs/radar.ics)."""

from intern_engine import publish, radar


def _rows(monkeypatch, rows):
    monkeypatch.setattr(radar, "rows", lambda *a, **k: rows)


def test_ics_has_events_only_for_dated_waiting_rows(monkeypatch, tmp_path):
    from intern_engine import paths
    monkeypatch.setattr(paths, "RADAR_ICS_PATH", str(tmp_path / "radar.ics"))
    monkeypatch.setattr(paths, "DOCS_DIR", str(tmp_path))
    _rows(monkeypatch, [
        {"company": "Meta", "status": "waiting", "rolling": False, "expected": "2026-08-01",
         "precision": "month", "source": "known", "note": "late Aug"},
        {"company": "NVIDIA", "status": "waiting", "rolling": False, "expected": "2026-08-24",
         "precision": "day", "source": "engine", "note": ""},
        {"company": "Microsoft", "status": "waiting", "rolling": True, "expected": "",
         "precision": "day", "source": "known", "note": ""},          # rolling: skipped
        {"company": "Anduril", "status": "open", "rolling": False, "expected": "2026-06-10",
         "precision": "day", "source": "engine", "note": ""},          # already open: skipped
    ])
    n = publish.write_radar_ics({}, "Summer 2027")
    assert n == 2
    text = open(str(tmp_path / "radar.ics"), encoding="utf-8").read()
    assert text.startswith("BEGIN:VCALENDAR")
    assert text.strip().endswith("END:VCALENDAR")
    assert text.count("BEGIN:VEVENT") == 2
    assert "DTSTART;VALUE=DATE:20260801" in text
    assert "DTSTART;VALUE=DATE:20260824" in text
    assert "Microsoft" not in text and "Anduril" not in text
    # verified rows get the 🎯 marker; every event has a week-before reminder
    assert "🎯 NVIDIA" in text
    assert text.count("TRIGGER:-P7D") == 2
    # CRLF line endings per RFC 5545
    assert b"\r\n" in open(str(tmp_path / "radar.ics"), "rb").read()


def test_ics_escapes_special_characters(monkeypatch, tmp_path):
    from intern_engine import paths
    monkeypatch.setattr(paths, "RADAR_ICS_PATH", str(tmp_path / "radar.ics"))
    monkeypatch.setattr(paths, "DOCS_DIR", str(tmp_path))
    _rows(monkeypatch, [
        {"company": "A; B, Inc.", "status": "waiting", "rolling": False,
         "expected": "2026-09-01", "precision": "month", "source": "known", "note": "x"},
    ])
    publish.write_radar_ics({}, "Summer 2027")
    text = open(str(tmp_path / "radar.ics"), encoding="utf-8").read()
    assert "A\\; B\\, Inc." in text
