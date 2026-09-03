"""The subscribable radar calendar (docs/radar.ics)."""

from intern_engine import config, publish, radar


def _rows(monkeypatch, rows):
    monkeypatch.setattr(radar, "rows", lambda *a, **k: rows)
    # The radar only exists on a US list (its windows are US-seeded), so the
    # writer's own mechanics are exercised under a US config.
    monkeypatch.setattr(
        config, "load_config",
        lambda: {**config.DEFAULTS, "regions": ["US"]},
    )


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


def test_ics_normalizes_carriage_returns_and_omits_expired_windows(monkeypatch, tmp_path):
    from intern_engine import paths
    monkeypatch.setattr(paths, "RADAR_ICS_PATH", str(tmp_path / "radar.ics"))
    monkeypatch.setattr(paths, "DOCS_DIR", str(tmp_path))
    _rows(monkeypatch, [
        {"company": "Good\r\nCompany", "status": "waiting", "rolling": False,
         "expected": "2026-09-01", "precision": "month", "source": "known",
         "note": "line1\rline2", "days_until": 26},
        {"company": "Expired", "status": "waiting", "rolling": False,
         "expected": "2026-03-01", "precision": "month", "source": "known",
         "note": "", "days_until": -158},
    ])
    assert publish.write_radar_ics(
        {}, "Summer 2027", data_as_of="2026-08-06T14:00:00Z"
    ) == 1
    raw = (tmp_path / "radar.ics").read_bytes()
    assert b"Expired" not in raw
    assert b"Good\\nCompany" in raw
    assert b"line1\\nline2" in raw
    assert b"\r\n" in raw and b"\r\r\n" not in raw


def test_ics_folding_moves_spaces_off_physical_line_endings():
    folded = publish._ics_fold("DESCRIPTION:" + "x" * 62 + "  more words")
    physical = folded.encode("utf-8").split(b"\r\n")
    assert len(physical) > 1
    assert all(not line.endswith((b" ", b"\t")) for line in physical)
    # Unfolding preserves both original separator spaces.
    assert folded.replace("\r\n ", "") == (
        "DESCRIPTION:" + "x" * 62 + "  more words"
    )


def test_no_calendar_events_off_a_us_list(monkeypatch, tmp_path):
    """The windows are hand-seeded US employers, so a SEA list gets no pings."""
    from intern_engine import paths
    monkeypatch.setattr(paths, "RADAR_ICS_PATH", str(tmp_path / "radar.ics"))
    monkeypatch.setattr(paths, "DOCS_DIR", str(tmp_path))
    monkeypatch.setattr(radar, "rows", lambda *a, **k: [
        {"company": "Meta", "status": "waiting", "rolling": False,
         "expected": "2026-08-01", "precision": "month", "source": "known",
         "note": "late Aug"},
    ])
    monkeypatch.setattr(
        config, "load_config",
        lambda: {**config.DEFAULTS, "regions": ["SEA"]},
    )
    assert publish.write_radar_ics({}, "Summer 2027") == 0
    text = open(str(tmp_path / "radar.ics"), encoding="utf-8").read()
    assert "BEGIN:VEVENT" not in text
