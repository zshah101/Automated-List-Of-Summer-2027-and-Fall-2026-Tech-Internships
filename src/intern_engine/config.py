"""Tunable settings, loaded from data/config.json (with safe defaults).

Change behavior without touching code:
  - cycles        : the exact intern cycles to show, e.g. ["Summer 2027", "Fall 2026"].
                    These become the section headings, in this order.
  - default_cycle : where to put roles that have no clear term/year (e.g. just
                    "Software Engineer Intern"). Must be one of `cycles`.
  - regions       : which countries to track, e.g. ["SEA"] for Singapore +
                    core Southeast Asia, ["Singapore"] for one country, ["US"]
                    or ["US", "Canada"] for North America, or ["Global"] to
                    disable the location filter entirely. Group tokens ("SEA")
                    expand to their members; see filters.REGION_GROUPS.
  - role_scope    : "tech" (SWE/data/ML/quant/hardware/...) or "all" internships.
"""

from __future__ import annotations

import json
import os
import re

from . import filters, paths

DEFAULTS = {
    "cycles": ["Summer 2027", "Fall 2026"],
    "default_cycle": "Summer 2027",
    "regions": ["SEA"],
    "role_scope": "tech",
}


class ConfigError(RuntimeError):
    """Configuration exists but is unsafe or has the wrong shape.

    A bad configuration controls publication scope.  Silently falling back to
    defaults can therefore publish the wrong cycle or disable the USA filter,
    so malformed files are deliberately fatal.
    """

_FALLBACK_REPO = "zshah101/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships"


def repo_slug() -> str:
    """"owner/name" for this repo: from Actions env, else the git remote."""
    env = os.environ.get("GITHUB_REPOSITORY")
    if env and "/" in env:
        return env
    try:
        with open(os.path.join(paths.ROOT, ".git", "config"), encoding="utf-8") as f:
            m = re.search(r"github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?\s", f.read())
            if m:
                return m.group(1)
    except OSError:
        pass
    return _FALLBACK_REPO


def pages_base() -> str:
    """The GitHub Pages base URL serving docs/ (dashboard, feed, JSON API)."""
    owner, _, name = repo_slug().partition("/")
    return f"https://{owner.lower()}.github.io/{name}"

_GLOBAL_TOKENS = {"global", "international", "worldwide", "any", "all"}
# What a user may write in data/config.json -> the canonical region key that
# filters.py matches on. Group tokens ("sea") expand via filters.REGION_GROUPS.
_REGION_ALIASES = {
    "us": "us", "usa": "us", "u.s.": "us", "united states": "us",
    "america": "us",
    "canada": "canada", "ca": "canada",
    "singapore": "singapore", "sg": "singapore",
    "malaysia": "malaysia", "my": "malaysia",
    "indonesia": "indonesia", "id": "indonesia",
    "thailand": "thailand", "th": "thailand",
    "vietnam": "vietnam", "viet nam": "vietnam", "vn": "vietnam",
    "philippines": "philippines", "ph": "philippines",
    "sea": "sea", "southeast asia": "sea", "south-east asia": "sea",
    "south east asia": "sea", "asean": "sea",
}


def _string_list(value, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ConfigError(f"{field} must be a list of strings")
    cleaned = [v.strip() for v in value]
    if (not allow_empty and not cleaned) or any(not v for v in cleaned):
        raise ConfigError(f"{field} must contain non-empty values")
    if len({v.casefold() for v in cleaned}) != len(cleaned):
        raise ConfigError(f"{field} contains duplicates")
    return cleaned


def _bounded_int(cfg: dict, field: str, default: int, *, minimum: int = 0,
                 maximum: int = 100_000) -> int:
    value = cfg.get(field, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{field} must be an integer")
    if not minimum <= value <= maximum:
        raise ConfigError(f"{field} must be between {minimum} and {maximum}")
    return value


def validate_config(raw: object) -> dict:
    """Return a normalized config or raise :class:`ConfigError`."""
    if not isinstance(raw, dict):
        raise ConfigError(f"config must be an object, got {type(raw).__name__}")

    cfg = {**DEFAULTS, **raw}
    cfg["cycles"] = _string_list(cfg.get("cycles"), "cycles")
    if not all(re.fullmatch(r"(?:Summer|Fall|Spring|Winter) 20\d{2}", c)
               for c in cfg["cycles"]):
        raise ConfigError("cycles must use labels such as 'Summer 2027'")

    cfg["regions"] = _string_list(cfg.get("regions"), "regions")
    supported = _GLOBAL_TOKENS | set(_REGION_ALIASES)
    unknown = [r for r in cfg["regions"] if r.casefold() not in supported]
    if unknown:
        raise ConfigError(f"unsupported regions: {', '.join(unknown)}")

    if cfg.get("role_scope") not in {"tech", "all"}:
        raise ConfigError("role_scope must be 'tech' or 'all'")
    default_cycle = cfg.get("default_cycle")
    if default_cycle not in cfg["cycles"]:
        raise ConfigError("default_cycle must be one of cycles")

    for field in ("allowlist_only", "include_international", "infer_undated"):
        if field in cfg and not isinstance(cfg[field], bool):
            raise ConfigError(f"{field} must be true or false")

    cfg["max_age_days"] = _bounded_int(cfg, "max_age_days", 365, maximum=3_650)
    cfg["max_per_company"] = _bounded_int(
        cfg, "max_per_company", 0, maximum=10_000
    )
    cfg["infer_max_age_days"] = _bounded_int(
        cfg, "infer_max_age_days", 45, minimum=1, maximum=365
    )

    limits = cfg.get("section_limits", {})
    if not isinstance(limits, dict):
        raise ConfigError("section_limits must be an object")
    normalized_limits: dict[str, int] = {}
    for label, value in limits.items():
        if label not in cfg["cycles"]:
            raise ConfigError(f"section_limits contains untracked cycle {label!r}")
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ConfigError(f"section limit for {label!r} must be a non-negative integer")
        normalized_limits[label] = value
    cfg["section_limits"] = normalized_limits

    for field in ("supabase_url", "supabase_publishable_key"):
        if field in cfg and not isinstance(cfg[field], str):
            raise ConfigError(f"{field} must be a string")
    return cfg


def load_config() -> dict:
    if not os.path.exists(paths.CONFIG_PATH):
        return validate_config(DEFAULTS)
    try:
        with open(paths.CONFIG_PATH, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"{paths.CONFIG_PATH} is unreadable: {exc}") from exc
    return validate_config(raw)


def cycles(cfg: dict) -> list[str]:
    return list(cfg.get("cycles") or DEFAULTS["cycles"])


def restrict_region(cfg: dict) -> bool:
    regions = cfg.get("regions") or []
    if not regions:
        # Fail closed.  An empty list must never silently turn a USA-only
        # deployment into a global one, even when a caller bypasses validation.
        return True
    return not any(str(r).lower() in _GLOBAL_TOKENS for r in regions)


def wanted_regions(cfg: dict) -> list[str]:
    """Canonical region keys to filter on; empty when the filter is off.

    Group tokens are left intact for :func:`filters.resolve_regions`, which is
    the single place that knows what "sea" contains.
    """
    if not restrict_region(cfg):
        return []
    keys: list[str] = []
    for value in cfg.get("regions") or []:
        key = _REGION_ALIASES.get(str(value).strip().casefold())
        if key and key not in keys:
            keys.append(key)
    return keys


# A group reads better under its own name than as a list of six countries.
_GROUP_LABELS = {"sea": "Singapore & Southeast Asia"}


def region_label(cfg: dict) -> str:
    """One human-readable phrase for the tracked region, for page furniture."""
    keys = wanted_regions(cfg)
    if not keys:
        return "Worldwide"
    parts = [
        _GROUP_LABELS.get(key) or filters.REGION_LABELS.get(key, key.title())
        for key in keys
    ]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " & " + parts[-1]


def want_us(cfg: dict) -> bool:
    """Whether the US is tracked - the switch for every US-visa feature.

    The H-1B badges, the sponsorship flags and the Drop Radar are all built on
    US immigration data, so they are shown only when US roles are on the list.
    """
    return "us" in wanted_regions(cfg)


def want_canada(cfg: dict) -> bool:
    return "canada" in wanted_regions(cfg)


def section_limit(cfg: dict, label: str):
    """Max rows to show for a section, or None for no cap."""
    return (cfg.get("section_limits") or {}).get(label)


def max_age_days(cfg: dict):
    """Drop roles published longer ago than this many days. 0/None = no limit."""
    return cfg.get("max_age_days", 365)


def max_per_company(cfg: dict):
    """Max roles to show per company per section, for variety. 0/None = no limit."""
    return cfg.get("max_per_company", 0)


def infer_undated(cfg: dict) -> bool:
    """Whether recent roles with no stated cycle enter ``Not stated``.

    The historical name remains for config compatibility; no cycle is inferred
    from a date anymore.
    """
    return bool(cfg.get("infer_undated", True))


def infer_max_age_days(cfg: dict) -> int:
    """Only infer a cycle for roles posted within this many days — recency is
    what makes the inference trustworthy."""
    return int(cfg.get("infer_max_age_days", 45))


def allowlist_only(cfg: dict) -> bool:
    """When true, show only recognizable (priority-listed) companies. Off by default."""
    return bool(cfg.get("allowlist_only", False))


def include_international(cfg: dict) -> bool:
    """When true, also keep non-US roles (shown in a separate International section)."""
    return bool(cfg.get("include_international", False))


def signup_endpoint(cfg: dict) -> tuple[str, str] | None:
    """(supabase_url, publishable_key) for the email signup form, when configured.

    These are PUBLIC values by design (the key is Supabase's client-side
    "publishable" key; row-level security is what protects the data).
    """
    url = (cfg.get("supabase_url") or "").rstrip("/")
    key = cfg.get("supabase_publishable_key") or ""
    return (url, key) if url and key else None
