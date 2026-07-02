"""Build data/h1b.json from the USCIS H-1B Employer Data Hub exports.

Run offline (once a year, when USCIS publishes a new fiscal year):

    python tools/build_h1b.py path/to/h1b_2022.csv path/to/h1b_2023.csv

Source files: https://www.uscis.gov/tools/reports-and-studies/h-1b-employer-data-hub
(uscis.gov blocks datacenter IPs; the Internet Archive keeps byte-identical
copies, e.g. https://web.archive.org/web/20260523021104id_/https://www.uscis.gov/sites/default/files/document/data/h1b_datahubexport-2023.csv)

Each export row is one employer+location; we aggregate approvals (initial +
continuing) per NORMALIZED employer name across all rows and years, drop
employers with zero approvals, and write a compact committed index that the
engine joins against company names at render time.
"""

import csv
import json
import os
import re
import sys
from datetime import UTC, datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from intern_engine import h1b, paths  # noqa: E402

_MIN_APPROVALS = 2  # drop the one-off long tail: halves the file, keeps the signal


def _to_int(value: str) -> int:
    digits = re.sub(r"[^\d]", "", value or "")
    return int(digits) if digits else 0


def build(csv_paths: list[str]) -> dict:
    totals: dict[str, int] = {}
    years: set[int] = set()
    rows = 0
    for path in csv_paths:
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                rows += 1
                name = h1b.normalize(row.get("Employer") or "")
                if not name:
                    continue
                year = _to_int(row.get("Fiscal Year") or "")
                if year:
                    years.add(year)
                approvals = _to_int(row.get("Initial Approval")) + _to_int(
                    row.get("Continuing Approval")
                )
                if approvals:
                    totals[name] = totals.get(name, 0) + approvals

    employers = {k: v for k, v in sorted(totals.items()) if v >= _MIN_APPROVALS}
    return {
        "source": "USCIS H-1B Employer Data Hub (public per-employer export)",
        "fiscal_years": sorted(years),
        "built_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "min_approvals": _MIN_APPROVALS,
        "employers": employers,
    }, rows


def main() -> None:
    csv_paths = sys.argv[1:]
    if not csv_paths:
        print(__doc__)
        sys.exit(1)
    index, rows = build(csv_paths)
    with open(paths.H1B_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = os.path.getsize(paths.H1B_PATH) // 1024
    print(f"Read {rows:,} rows from {len(csv_paths)} file(s).")
    print(f"Index: {len(index['employers']):,} employers with >= {_MIN_APPROVALS} "
          f"approvals, FY{min(index['fiscal_years'])}-{max(index['fiscal_years'])}")
    print(f"Wrote {paths.H1B_PATH} ({size_kb:,} KB)")


if __name__ == "__main__":
    main()
