"""The single normalized job record every connector produces.

Keeping one shape means the pipeline, store, and renderer never care which ATS a
role came from — adding a source touches only its connector.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Job:
    id: str               # stable: "<source>:<company_slug>:<external_id>"
    source: str
    company: str
    company_slug: str
    title: str
    location: str
    url: str
    posted_at: str | None = None   # real publish date, or None when unknown
    season: str = "Unspecified"    # cycle label, assigned by the pipeline
    category: str = "Other"
    sponsorship: str = "unknown"   # reserved for the F-1 H-1B feature
