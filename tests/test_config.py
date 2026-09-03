import pytest

from intern_engine import config, paths


def test_missing_config_uses_validated_safe_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "CONFIG_PATH", str(tmp_path / "missing.json"))
    cfg = config.load_config()
    assert cfg["regions"] == ["SEA"]
    assert cfg["role_scope"] == "tech"
    assert cfg["default_cycle"] in cfg["cycles"]


def test_malformed_existing_config_is_fatal(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text('{"regions":', encoding="utf-8")
    monkeypatch.setattr(paths, "CONFIG_PATH", str(path))
    with pytest.raises(config.ConfigError, match="unreadable"):
        config.load_config()


@pytest.mark.parametrize(
    "raw, message",
    [
        ({"regions": []}, "regions must contain"),
        ({"regions": ["Mars"]}, "unsupported regions"),
        ({"regions": ["Atlantis"]}, "unsupported regions"),
        ({"cycles": ["2027 Summer"]}, "cycles must use labels"),
        ({"default_cycle": "Spring 2030"}, "default_cycle"),
        ({"include_international": "yes"}, "true or false"),
        ({"max_age_days": True}, "must be an integer"),
    ],
)
def test_scope_configuration_rejects_unsafe_shapes(raw, message):
    with pytest.raises(config.ConfigError, match=message):
        config.validate_config(raw)


def test_empty_regions_fail_closed_even_for_unvalidated_callers():
    assert config.restrict_region({"regions": []}) is True


class TestRegionTokens:
    """A config token has to survive the trip to a filter-ready region key."""

    def test_group_token_expands_to_its_members(self):
        cfg = config.validate_config({"regions": ["SEA"]})
        assert config.wanted_regions(cfg) == ["sea"]
        assert config.region_label(cfg) == "Singapore & Southeast Asia"
        assert config.restrict_region(cfg)
        assert not config.want_us(cfg)

    def test_aliases_and_case_are_accepted(self):
        for token in ("sea", "Southeast Asia", "ASEAN", "south east asia"):
            assert config.wanted_regions({"regions": [token]}) == ["sea"]
        assert config.wanted_regions({"regions": ["sg"]}) == ["singapore"]
        assert config.wanted_regions({"regions": ["Singapore"]}) == ["singapore"]

    def test_us_and_canada_still_resolve(self):
        cfg = config.validate_config({"regions": ["US", "Canada"]})
        assert config.wanted_regions(cfg) == ["us", "canada"]
        assert config.want_us(cfg) and config.want_canada(cfg)
        assert config.region_label(cfg) == "United States & Canada"

    def test_global_turns_the_filter_off(self):
        cfg = config.validate_config({"regions": ["Global"]})
        assert config.wanted_regions(cfg) == []
        assert config.region_label(cfg) == "Worldwide"
