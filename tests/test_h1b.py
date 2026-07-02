"""H-1B employer matching: precision-first, so most tests are about NOT matching."""

from intern_engine import h1b


def _index(employers):
    return {"fiscal_years": [2022, 2023], "employers": employers}


# --- name normalization -------------------------------------------------------

def test_normalize_strips_legal_suffixes():
    assert h1b.normalize("PALANTIR TECHNOLOGIES INC") == "palantir technologies"
    assert h1b.normalize("Google LLC") == "google"
    assert h1b.normalize("Stripe, Inc.") == "stripe"
    assert h1b.normalize("JPMORGAN CHASE & CO") == "jpmorgan chase"


def test_normalize_takes_dba_brand():
    assert h1b.normalize("0965688 BC LTD DBA PROCOGIA") == "procogia"


def test_normalize_keeps_identity_words():
    # "technologies"/"labs" are identity, not boilerplate — never stripped.
    assert h1b.normalize("Datadog Technologies") == "datadog technologies"


# --- matching -----------------------------------------------------------------

def test_exact_match():
    idx = _index({"nvidia": 851})
    assert h1b.approvals_for("NVIDIA Corp", idx) == 851


def test_alias_match():
    idx = _index({"meta platforms": 4510})
    assert h1b.approvals_for("Meta", idx) == 4510


def test_multi_token_prefix_sums_family():
    idx = _index({"jpmorgan chase bank": 900, "jpmorgan chase services": 100})
    assert h1b.approvals_for("JPMorgan Chase", idx) == 1000


def test_single_token_prefix_takes_max_not_sum():
    # "Google" must not inflate by summing subsidiaries with itself absent.
    idx = _index({"google fiber": 7, "google public sector": 9})
    assert h1b.approvals_for("Google", idx) == 9


def test_single_token_prefix_rejects_wide_ambiguity():
    # Four unrelated "Figure ..." companies -> refuse to guess.
    idx = _index({
        "figure ai": 5, "figure eight": 8, "figure markets": 3, "figure lending": 11,
    })
    assert h1b.approvals_for("Figure", idx) is None


def test_generic_and_short_names_never_prefix_match():
    idx = _index({"data systems international": 500, "gm financial": 40})
    assert h1b.approvals_for("Data", idx) is None
    assert h1b.approvals_for("GM!", idx) is None  # too short after cleanup, alias missed
    assert h1b.approvals_for("", idx) is None


def test_no_match_returns_none():
    assert h1b.approvals_for("Anduril", _index({"nvidia": 851})) is None


def test_empty_index_returns_none():
    assert h1b.approvals_for("Google", {"employers": {}}) is None


# --- presentation -------------------------------------------------------------

def test_badge_threshold():
    assert h1b.badge(h1b.BADGE_THRESHOLD) == "✓"
    assert h1b.badge(h1b.BADGE_THRESHOLD - 1) == ""
    assert h1b.badge(None) == ""


def test_pretty_count():
    assert h1b.pretty_count(43) == "43"
    assert h1b.pretty_count(1234) == "1.2k"
    assert h1b.pretty_count(6000) == "6k"
