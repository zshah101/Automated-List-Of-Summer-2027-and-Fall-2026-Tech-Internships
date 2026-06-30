"""The single normalized shape every connector returns.

No matter which ATS a job came from (Greenhouse, Lever, Ashby, ...), the rest
of the system only ever sees a `Job`. That decoupling is what lets us add new
sources later without touching the pipeline, store, or README generator.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Job:
    # Stable identity, formatted "<source>:<company_slug>:<external_id>".
    # This is how we dedup: the same posting always produces the same id.
    id: str

    source: str          # which ATS this came from, e.g. "greenhouse"
    company: str         # display name, e.g. "Stripe"
    company_slug: str    # the ATS token, e.g. "stripe"
    title: str
    location: str
    url: str             # the apply / posting link
    posted_at: str | None = None  # ISO timestamp from the ATS, if provided

    # Filled in by the pipeline after fetching:
    season: str = "Unspecified"   # "Summer 2027" | "Fall 2027" | ...
    category: str = "Other"       # "Software" | "Data & ML/AI" | ...
    sponsorship: str = "unknown"  # reserved for the F-1 H-1B feature (later)
