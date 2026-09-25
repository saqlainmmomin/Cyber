"""Export a draft test-criteria module to a review CSV for sign-off (P6-2a).

Usage:
    python scripts/export_criteria_review.py \
        [--module app.frameworks.criteria.dpdpa_draft] \
        [--out tasks/criteria-review/dpdpa-criteria-v1.csv]

Rows follow framework order (domain, section, requirement), so the sheet can be
reviewed one domain at a time. Output is deterministic: running twice gives a
byte-identical file. The decision / edited_statement / reviewer_note columns
are left blank for the reviewer.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

COLUMNS = [
    "requirement_id",
    "requirement_title",
    "criticality",
    "criterion_id",
    "kind",
    "statement",
    "evidence_hint",
    "source_basis",
    "in_force_note",
    "drafter_confidence",
    "decision",
    "edited_statement",
    "reviewer_note",
]


def build_rows(module_name: str) -> list[dict[str, str]]:
    from app.dpdpa.framework import get_all_requirements

    module = importlib.import_module(module_name)
    draft = module.DPDPA_CRITERIA_DRAFT
    meta = module.DPDPA_CRITERIA_REVIEW_META

    rows: list[dict[str, str]] = []
    for req in get_all_requirements():  # framework order, grouped by domain
        for tc in draft[req["id"]]:
            confidence, in_force_note = meta[tc.id]
            rows.append(
                {
                    "requirement_id": req["id"],
                    "requirement_title": req["title"],
                    "criticality": req["criticality"],
                    "criterion_id": tc.id,
                    "kind": tc.kind,
                    "statement": tc.statement,
                    "evidence_hint": tc.evidence_hint,
                    "source_basis": tc.source_basis,
                    "in_force_note": in_force_note,
                    "drafter_confidence": confidence,
                    "decision": "",
                    "edited_statement": "",
                    "reviewer_note": "",
                }
            )
    return rows


def write_csv(rows: list[dict[str, str]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--module", default="app.frameworks.criteria.dpdpa_draft")
    parser.add_argument("--out", default=str(ROOT / "tasks" / "criteria-review" / "dpdpa-criteria-v1.csv"))
    args = parser.parse_args(argv)

    rows = build_rows(args.module)
    write_csv(rows, Path(args.out))
    print(f"Wrote {len(rows)} criteria to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
