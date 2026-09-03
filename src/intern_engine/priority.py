"""Company prestige ranking, used to curate capped sections.

When a section has more roles than its cap, we keep roles from the most
recognizable / sought-after companies first. Lower rank = higher priority.
Edit this list to taste — it only affects which roles make the cut when a
section is over its limit, not what gets collected.
"""

from __future__ import annotations

import re

# Roughly ordered by how sought-after they are for SWE/ML interns.
TOP_COMPANIES = [
    "amazon", "google", "microsoft", "apple", "meta", "nvidia", "salesforce",
    "jpmorgan", "goldman", "morgan stanley", "capital one",
    "openai", "anthropic", "stripe", "databricks", "palantir", "scale ai",
    "ramp", "plaid", "coinbase", "robinhood", "airbnb", "dropbox", "notion",
    "figma", "snowflake", "datadog", "mongodb", "cloudflare", "pinterest",
    "reddit", "discord", "instacart", "doordash", "roblox", "unity", "duolingo",
    "brex", "mercury", "vercel", "replit", "perplexity", "cohere", "mistral ai",
    "hugging face", "together ai", "groq", "cerebras", "anduril",
    "applied intuition", "skydio", "neuralink", "two sigma", "jane street",
    "citadel", "optiver", "jump trading", "hudson river trading", "drw", "imc",
    "akuna", "samsara", "affirm", "sofi", "gusto", "asana", "gitlab",
    "hashicorp", "confluent", "elastic", "retool", "airtable", "benchling",
    "faire", "flexport", "lyft", "chime", "gemini", "kraken", "circle",
    "wealthsimple", "niantic", "twitch", "sentry", "postman", "linear",
    "sourcegraph", "amplitude", "segment", "twilio", "okta", "1password",
    "crowdstrike", "sentinelone", "wiz", "snyk", "rippling", "deel", "toast",
    "nubank", "whatnot", "ironclad", "vanta", "cockroach labs", "temporal",
    "fivetran", "airbyte", "dbt labs", "weights & biases", "pinecone",
    "runway", "character.ai", "glean", "harvey", "grammarly", "canva", "miro",
    "loom", "coursera", "webflow", "checkr", "lattice", "gong", "zapier",
    # Singapore / Southeast Asia. The cap decides which roles survive when a
    # section overflows, so a purely US ranking would drop the regional names
    # this list exists to surface.
    "sea", "shopee", "sea labs", "garena", "grab", "gojek", "goto",
    "bytedance", "tiktok", "lazada", "tokopedia", "traveloka", "agoda",
    "booking.com", "carousell", "ninja van", "shopback", "razer",
    "coda payments", "advance intelligence", "atome", "nium", "thunes",
    "aspire", "endowus", "stashaway", "syfe", "xendit", "dana", "ovo",
    "govtech", "gic", "temasek", "dbs", "ocbc", "uob", "sea group",
    "standard chartered", "hsbc", "singtel", "starhub", "singapore airlines",
    "a*star", "astar", "dso national laboratories", "dsta", "csit", "htx",
    "imda", "sea ai lab", "hyperscal", "vflow", "sleek", "peak xv",
    "squarepoint", "qube research", "jane street asia", "grasshopper",
    "quantedge", "dymon asia", "trafigura", "vitol",
]

_LEGAL_SUFFIXES = {
    "inc", "incorporated", "llc", "llp", "lp", "ltd", "limited", "corp",
    "corporation", "co", "company", "plc",
}
_PUNCT_RE = re.compile(r"[^a-z0-9]+")


def _key(company: str) -> str:
    words = _PUNCT_RE.sub(" ", (company or "").strip().lower()).split()
    if len(words) > 1 and words[0] == "the":
        words.pop(0)
    while len(words) > 1 and words[-1] in _LEGAL_SUFFIXES:
        words.pop()
    return " ".join(words)


_RANK = {_key(name): i for i, name in enumerate(TOP_COMPANIES)}
_ALIASES = {
    "amazon com services": "amazon",
    "amazon web services": "amazon",
    "alphabet": "google",
    "meta platforms": "meta",
    "jpmorgan chase": "jpmorgan",
    "jp morgan chase": "jpmorgan",
    "goldman sachs": "goldman",
    "salesforce com": "salesforce",
    "circle internet financial": "circle",
    "circle internet group": "circle",
    "cohere ai": "cohere",
    "kraken digital asset exchange": "kraken",
    "payward": "kraken",
    "functional software": "sentry",
    "sentry io": "sentry",
}
UNRANKED = 10_000


def rank(company: str) -> int:
    """Lower = more sought-after. Unknown companies sort last."""
    key = _key(company)
    canonical = _ALIASES.get(key, key)
    return _RANK.get(canonical, UNRANKED)
