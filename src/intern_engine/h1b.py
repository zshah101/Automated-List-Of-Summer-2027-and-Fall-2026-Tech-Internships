"""Company-level H-1B sponsorship history (the F-1 edge, level 2).

The sponsorship flags in `sponsorship.py` read what a posting SAYS. This module
adds what the company has DONE: how many H-1B petitions USCIS approved for that
employer, from the public H-1B Employer Data Hub. A row with a real track
record gets a ✓ — "this company has actually sponsored, recently, at scale."

The index (data/h1b.json) is built offline by tools/build_h1b.py from the
official USCIS per-employer CSVs and committed, so runs never depend on
uscis.gov being reachable. Matching is precision-first: an exact match on the
normalized name, a small alias table for brand-vs-legal-entity gaps, then a
word-boundary prefix match ("palantir" -> "palantir technologies"). A generic
token never matches, and wide prefix explosions are rejected.
"""

from __future__ import annotations

import json
import re

from . import paths

# Shown in the README / dashboard only at or above this many approvals across
# the index window — one-off petitions are not a signal an intern can bank on.
BADGE_THRESHOLD = 10

# Legal-suffix tokens stripped (repeatedly) from the END of a name. Kept
# conservative on purpose: "technologies", "systems", "labs" are identity, not
# boilerplate, so they stay.
_SUFFIXES = {
    "inc", "incorporated", "llc", "llp", "lp", "ltd", "limited", "corp",
    "corporation", "co", "company", "plc", "pllc", "pc", "sa", "ag", "gmbh",
    "bv", "nv", "se", "ulc",
}

# Brand name (normalized) -> employer name (normalized) when the public brand
# and the petitioning legal entity differ too much for a prefix match.
_ALIASES = {
    "google": "google",                       # resolved by prefix, kept for clarity
    "meta": "meta platforms",
    "ibm": "international business machines",
    "aws": "amazon web services",
    "gm": "general motors",
    "jpmorgan": "jpmorgan chase",
    "jp morgan": "jpmorgan chase",
    "jpmorganchase": "jpmorgan chase",
    "bofa": "bank of america",
    "amex": "american express",
    "byte dance": "bytedance",
    "x": "twitter",
}

# Names too generic to prefix-match on their own (exact/alias still allowed).
_GENERIC = {
    "the", "tech", "labs", "lab", "data", "cloud", "global", "digital",
    "systems", "software", "solutions", "group", "partners", "capital",
    "american", "united", "national", "first", "general", "one",
}

_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


def normalize(name: str) -> str:
    """One canonical form for both USCIS employer names and our company names."""
    n = (name or "").lower().strip()
    # "0965688 BC LTD DBA PROCOGIA" -> the DBA (doing-business-as) is the brand.
    if " dba " in f" {n} ":
        n = n.split(" dba ")[-1]
    n = _PUNCT_RE.sub(" ", n)
    n = _WS_RE.sub(" ", n).strip()
    tokens = n.split(" ")
    while len(tokens) > 1 and tokens[-1] in _SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


_index_cache: dict | None = None


def load() -> dict:
    """The committed employer -> approvals index ({} when not built yet)."""
    global _index_cache
    if _index_cache is None:
        try:
            with open(paths.H1B_PATH, encoding="utf-8") as f:
                _index_cache = json.load(f)
        except (OSError, ValueError):
            _index_cache = {}
    return _index_cache


def window_label() -> str:
    """Human label for the data window, e.g. "FY2022–2023"."""
    years = load().get("fiscal_years") or []
    if not years:
        return ""
    lo, hi = min(years), max(years)
    return f"FY{lo}" if lo == hi else f"FY{lo}–{hi}"


def approvals_for(company: str, index: dict | None = None) -> int | None:
    """Approved H-1B petitions for this company across the index window.

    None = no confident match (which is NOT evidence the company never
    sponsors — only a ✓ means something, its absence means nothing).
    """
    data = index if index is not None else load()
    employers = data.get("employers") or {}
    if not employers:
        return None

    name = normalize(company)
    if not name:
        return None

    hit = employers.get(name)
    if hit is not None:
        return hit

    alias = _ALIASES.get(name)
    if alias and alias in employers:
        return employers[alias]

    if name in _GENERIC or len(name) < 4:
        return None

    # Word-boundary prefix: "palantir" matches "palantir technologies";
    # "jpmorgan chase" matches "jpmorgan chase bank". Multi-token names sum
    # their subsidiary family. Single-token names are riskier — "figure" could
    # rope in several unrelated "Figure ..." companies — so they only match a
    # small candidate set and take the largest single entity, never the sum.
    prefix = name + " "
    candidates = [v for k, v in employers.items() if k.startswith(prefix)]
    single_token = " " not in name
    if not candidates or len(candidates) > (3 if single_token else 25):
        return None
    return max(candidates) if single_token else sum(candidates)


def badge(approvals: int | None) -> str:
    """'✓' when the company has a real, recent H-1B track record."""
    return "✓" if approvals is not None and approvals >= BADGE_THRESHOLD else ""


def pretty_count(approvals: int) -> str:
    """Compact human count: 43 -> '43', 1,234 -> '1.2k'."""
    if approvals >= 1000:
        return f"{approvals / 1000:.1f}k".replace(".0k", "k")
    return str(approvals)
