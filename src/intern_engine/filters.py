"""All the text classification: is it an internship? is it tech? which season?

These are deliberately simple, central, and easy to tune. As we see real data
we widen/narrow these patterns here, in one place.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

# --- internship detection (whole words, never substrings) --------------------
_INTERN_RE = re.compile(r"\b(intern|interns|internship|co[\s-]?op)\b", re.IGNORECASE)
_SENIOR_RE = re.compile(
    r"\b(senior|sr|staff|principal|manager|director|\blead\b|vp|head)\b",
    re.IGNORECASE,
)

# --- tech-role detection -----------------------------------------------------
# We keep ONLY software / data / ML / security roles. A role must match an
# INCLUDE term and must NOT match an EXCLUDE term. The exclude list removes
# non-software engineering (mechanical, aerospace, electrical/hardware, etc.)
# and non-technical roles (recruiting, sales, marketing, ...). Note we do NOT
# treat a bare "engineer" as tech — that word alone lets in mech/aero/civil.
_INCLUDE_RE = re.compile(
    r"\b("
    r"software|developer|swe|full[\s-]?stack|front[\s-]?end|back[\s-]?end|"
    r"web developer|web engineer|mobile|ios|android|devops|sre|site reliability|"
    r"infrastructure|platform engineer|platform engineering|distributed systems|"
    r"operating system|compiler|embedded|firmware|"
    r"cyber|cybersecurity|appsec|application security|information security|infosec|"
    r"security engineer|"
    r"data science|data scientist|data engineer|data analyst|analytics engineer|"
    r"machine learning|ml|deep learning|ai|artificial intelligence|nlp|computer vision|"
    r"research scientist|applied scientist|research engineer|ml engineer|ai engineer|"
    r"quantitative developer|quant developer|computer science|programming"
    r")\b",
    re.IGNORECASE,
)
_EXCLUDE_RE = re.compile(
    r"\b("
    r"mechanical|aerospace|aeronautical|astrodynamics|aerodynamic|propulsion|avionics|"
    r"guidance|navigation|gnc|naval|civil engineer|chemical|chemistry|chemist|"
    r"biology|biological|materials|structural|thermal|fluid|manufacturing|"
    r"industrial engineer|electrical|fpga|asic|pcb|analog|photonics|optical|"
    r"hardware|physical design|silicon|semiconductor|vlsi|rtl|"
    r"recruit|recruiting|recruiter|sales|account executive|account manager|"
    r"account management|marketing|marketer|unpaid|"
    r"legal|counsel|accounting|human resources|people operations|people team|talent|"
    r"communications|supply chain|business development|product design|product designer|"
    r"product manager|product management|ux design|graphic design|industrial design|"
    r"phd|ph\.d|doctoral"
    r")\b",
    re.IGNORECASE,
)

# --- season detection --------------------------------------------------------
_YEAR_RE = re.compile(r"\b(20\d\d)\b")


def is_internship(title: str) -> bool:
    return bool(_INTERN_RE.search(title)) and not _SENIOR_RE.search(title)


def is_tech(title: str) -> bool:
    """Keep software/data/ML/security roles; reject hardware/mech/non-tech."""
    if _EXCLUDE_RE.search(title):
        return False
    return bool(_INCLUDE_RE.search(title))


_CYCLE_RE = re.compile(r"(Summer|Fall|Spring|Winter)\s+(\d{4})", re.IGNORECASE)


def detect_season(title: str, cycles=("Summer 2027", "Fall 2026"), *_ignored) -> str | None:
    """Bucket a title into a cycle ONLY if the year is explicit in the title.

    This is strict on purpose: a role must actually state its year (e.g. "2027"
    or "Fall 2026"). Titles with no year fall through to `infer_season`, which
    reasons from the posting date instead and marks the result as inferred —
    a stated year always wins over an inference.

    Examples (cycles = Summer 2027, Fall 2026):
      "Software Engineer Intern, Summer 2027"  -> "Summer 2027"
      "2027 Software Engineer Intern"          -> "Summer 2027"  (year explicit)
      "Fall 2026 Data Science Intern"          -> "Fall 2026"
      "Software Engineer Intern"               -> None  (no year -> drop)
      "Summer 2026 Intern"                     -> None  (past -> drop)
      "Fall 2027 Intern"                       -> None  (cycle not tracked)
    """
    parsed = []  # (term, year, label)
    for label in cycles:
        m = _CYCLE_RE.match(label.strip())
        if m:
            parsed.append((m.group(1).capitalize(), m.group(2), label))

    years = set(_YEAR_RE.findall(title))
    if not years:
        return None  # no explicit year in the title -> drop

    t = title.lower()
    if "summer" in t:
        term = "Summer"
    elif "fall" in t or "autumn" in t:
        term = "Fall"
    elif "spring" in t:
        term = "Spring"
    elif "winter" in t:
        term = "Winter"
    else:
        term = None

    # 1) exact term + year match (e.g. "Summer 2027")
    for cterm, cyear, label in parsed:
        if cyear in years and term == cterm:
            return label
    # 2) year matches a tracked cycle and the title has no conflicting term
    #    (e.g. "2027 Software Engineer Intern" -> the 2027 cycle)
    for _cterm, cyear, label in parsed:
        if cyear in years and term is None:
            return label
    # year stated but term conflicts (e.g. "Fall 2027") -> not a tracked cycle
    return None


# For yearless titles: the month a term's recruiting rolls over to next year.
# Posting month <= rollover -> that term THIS year is still the plausible target;
# after it -> companies are hiring for the term NEXT year. ("Summer Intern"
# posted in March means this summer; posted in July it means next summer.)
_TERM_ROLLOVER_MONTH = {"Summer": 4, "Fall": 8, "Spring": 2, "Winter": 10}


def infer_season(title: str, posted_at: str | None,
                 cycles=("Summer 2027", "Fall 2026"),
                 max_age_days: int = 45,
                 now: datetime | None = None) -> str | None:
    """Best-effort cycle for a title with NO explicit year, from its posting date.

    `detect_season` stays strict (a stated year always wins and never lands
    here). This handles the measured majority of real postings whose titles
    just say "Software Engineer Intern": a role *posted recently* is recruiting
    for the next upcoming cycle of its term (default term: Summer, the dominant
    intern cycle). Recency is what makes the guess sound, so postings older
    than `max_age_days` — evergreen/stale listings — are never inferred.

    Returns a tracked cycle label, or None (leave the role dropped).
    """
    if not posted_at:
        return None  # no date -> nothing to reason from
    try:
        posted = datetime.strptime(posted_at[:10], "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return None
    now = now or datetime.now(UTC)
    age_days = (now - posted).days
    if not (-1 <= age_days <= max_age_days):  # -1 tolerates feed timezone skew
        return None

    t = title.lower()
    if "summer" in t:
        term = "Summer"
    elif "fall" in t or "autumn" in t:
        term = "Fall"
    elif "spring" in t:
        term = "Spring"
    elif "winter" in t:
        term = "Winter"
    else:
        term = "Summer"

    year = posted.year if posted.month <= _TERM_ROLLOVER_MONTH[term] else posted.year + 1
    label = f"{term} {year}"
    return label if label in cycles else None


# --- season stated in posting TEXT (verifies date-inferred cycles) ------------
_TEXT_CYCLE_RE = re.compile(r"\b(summer|fall|autumn|winter|spring)\s+(?:of\s+)?(20\d\d)\b", re.I)
_INTERNISH_RE = re.compile(
    r"\b(intern(?:ship)?s?|co[\s-]?op|start\s+date|program|term|semester)\b", re.I
)


def season_from_text(text: str, near: int = 90) -> str | None:
    """The cycle a posting's own text states, or None.

    Precision-first, mirroring detect_season's ethos: a "<term> <year>" mention
    only counts when internship-ish words sit within `near` characters (skips
    stray dates), and a verdict is returned only when every counted mention
    agrees — a posting listing several terms (grad-window boilerplate) never
    overrides the date inference.
    """
    if not text:
        return None
    labels = set()
    for m in _TEXT_CYCLE_RE.finditer(text):
        lo = max(0, m.start() - near)
        if _INTERNISH_RE.search(text[lo:m.end() + near]):
            term = m.group(1).capitalize()
            labels.add(f"{'Fall' if term == 'Autumn' else term} {m.group(2)}")
    return labels.pop() if len(labels) == 1 else None


# --- location: US / Canada detection -----------------------------------------
# Full state/province names are matched case-insensitively; the 2-letter codes
# are matched case-SENSITIVELY (uppercase) so "OR"/"IN" don't match the words
# "or"/"in" inside a city name.
_US_STATES = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming",
    "district of columbia",
]
_CA_PROVINCES = [
    "ontario", "quebec", "british columbia", "alberta", "manitoba",
    "saskatchewan", "nova scotia", "new brunswick", "newfoundland", "labrador",
    "prince edward island", "yukon", "northwest territories", "nunavut",
]
_US_CODES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC", "US", "USA",
]
_CA_CODES = ["ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "NL", "PE", "YT", "NT", "NU"]

_US_COUNTRY = ("united states", "u.s.a", "u.s.", "u.s", "usa", "america")
_CA_COUNTRY = ("canada", "canadian")

# Countries that appear in ATS location strings and must never read as US, even
# when a state-code lookalike sits next to them ("IN - Bangalore, India" is not
# Indiana). An explicit US token still wins for multi-country strings.
_NON_US_COUNTRIES = (
    "india", "united kingdom", "germany", "france", "poland", "ireland",
    "netherlands", "spain", "italy", "portugal", "romania", "hungary",
    "czech", "slovakia", "sweden", "switzerland", "belgium", "austria",
    "denmark", "norway", "finland", "greece", "turkey", "israel",
    "united arab emirates", "saudi arabia", "qatar", "egypt", "nigeria",
    "kenya", "south africa", "brazil", "mexico", "argentina", "colombia",
    "chile", "peru", "costa rica", "japan", "china", "singapore", "korea",
    "taiwan", "hong kong", "philippines", "indonesia", "vietnam", "thailand",
    "malaysia", "pakistan", "bangladesh", "sri lanka", "australia",
    "new zealand",
)
_NON_US_RE = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in _NON_US_COUNTRIES) + r")\b"
)

_US_NAME_RE = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in _US_STATES) + r")\b", re.IGNORECASE
)
_CA_NAME_RE = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in _CA_PROVINCES) + r")\b", re.IGNORECASE
)
# case-sensitive; (?!-) avoids matching country-style prefixes like "DE-Berlin"
# (Germany) as the US state code DE (Delaware).
_US_CODE_RE = re.compile(r"\b(" + "|".join(_US_CODES) + r")\b(?!-)")
_CA_CODE_RE = re.compile(r"\b(" + "|".join(_CA_CODES) + r")\b(?!-)")


def is_united_states(location: str) -> bool:
    if not location:
        return False
    low = location.lower()
    if any(token in low for token in _US_COUNTRY):
        return True
    if _NON_US_RE.search(low):
        return False  # a named foreign country outranks state-name/code guesses
    if _US_NAME_RE.search(low):
        return True
    if _US_CODE_RE.search(location):
        return True
    return False


def is_canada(location: str) -> bool:
    if not location:
        return False
    low = location.lower()
    if any(token in low for token in _CA_COUNTRY):
        return True
    if _CA_NAME_RE.search(low):
        return True
    if _CA_CODE_RE.search(location):
        return True
    return False


def is_us_or_canada(location: str) -> bool:
    return is_united_states(location) or is_canada(location)


def region_ok(location: str, want_us: bool, want_canada: bool) -> bool:
    """True if the location matches one of the wanted regions.

    Conservative: a bare "Remote" with no country mentioned matches nothing.
    """
    if want_us and is_united_states(location):
        return True
    if want_canada and is_canada(location):
        return True
    return False


# --- category tagging (first match wins; order = specific before generic) -----
_CATEGORY_PATTERNS = [
    ("Quant", re.compile(r"\b(quant|quantitative|trading|trader)\b", re.IGNORECASE)),
    (
        "Data & ML/AI",
        re.compile(
            r"\b(data|machine learning|\bml\b|\bai\b|artificial intelligence|"
            r"deep learning|nlp|computer vision|research scientist|"
            r"applied scientist|analytics)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Hardware",
        re.compile(
            r"\b(hardware|electrical|firmware|asic|fpga|robotics|mechanical|"
            r"chip|silicon|manufacturing|industrial|analog|photonics|optical)\b",
            re.IGNORECASE,
        ),
    ),
    ("Security", re.compile(r"\b(cyber|infosec|appsec|security)", re.IGNORECASE)),
    (
        "Software",
        re.compile(
            r"\b(software|developer|swe|backend|frontend|full[\s-]?stack|"
            r"mobile|ios|android|devops|sre|infrastructure|platform|systems|"
            r"cloud|web|compiler|embedded|firmware|engineer|engineering|"
            r"programming|computer science)\b",
            re.IGNORECASE,
        ),
    ),
]


def categorize(title: str) -> str:
    for name, pattern in _CATEGORY_PATTERNS:
        if pattern.search(title):
            return name
    return "Other"
