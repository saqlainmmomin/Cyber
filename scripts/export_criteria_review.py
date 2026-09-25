"""Export a draft test-criteria module to a review CSV for sign-off (P6-2a, P6-2c).

Usage:
    python scripts/export_criteria_review.py [--framework dpdpa|iso27001|nist_csf] \
        [--module app.frameworks.criteria.<fw>_draft] [--out <criteria csv>] \
        [--descriptions-out <descriptions csv>]   # iso27001 only

Defaults write tasks/criteria-review/{dpdpa,iso27001,nist-csf}-criteria-v1.csv;
iso27001 also writes iso27001-descriptions-v1.csv (own-words descriptions,
D-P6-J). Rows follow framework order (ISO: clauses 4-10 first, then Annex A),
so a sheet can be reviewed one domain at a time. Output is deterministic:
running twice gives byte-identical files. The decision / edited_* /
reviewer_note columns are left blank for the reviewer.
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

REVIEW_DIR = ROOT / "tasks" / "criteria-review"

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

DESCRIPTION_COLUMNS = [
    "requirement_id",
    "requirement_title",
    "source",
    "current_reference",
    "own_words_description",
    "decision",
    "edited_description",
    "reviewer_note",
]

# framework -> (draft module, criteria dict, review-meta dict, default criteria csv)
FRAMEWORKS = {
    "dpdpa": ("app.frameworks.criteria.dpdpa_draft", "DPDPA_CRITERIA_DRAFT",
              "DPDPA_CRITERIA_REVIEW_META", "dpdpa-criteria-v1.csv"),
    "iso27001": ("app.frameworks.criteria.iso27001_draft", "ISO27001_CRITERIA_DRAFT",
                 "ISO27001_CRITERIA_REVIEW_META", "iso27001-criteria-v1.csv"),
    "nist_csf": ("app.frameworks.criteria.nist_csf_draft", "NIST_CSF_CRITERIA_DRAFT",
                 "NIST_CSF_CRITERIA_REVIEW_META", "nist-csf-criteria-v1.csv"),
}
ISO_DESCRIPTIONS_CSV = "iso27001-descriptions-v1.csv"


def _requirements(framework: str, module) -> list[dict[str, str]]:
    """Requirements in framework order: id, title, criticality, reference, source."""
    if framework == "dpdpa":
        from app.dpdpa.framework import get_all_requirements

        return [
            {"id": r["id"], "title": r["title"], "criticality": r["criticality"]}
            for r in get_all_requirements()  # grouped by domain
        ]
    if framework == "iso27001":
        from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION

        clauses = [
            {"id": cid, "title": c["title"], "criticality": c["criticality"],
             "reference": c["reference"], "source": "clause"}
            for cid, c in module.ISO27001_CLAUSE_REQUIREMENTS_DRAFT.items()
        ]
        annex = [
            {"id": c.id, "title": c.title, "criticality": c.criticality,
             "reference": c.reference, "source": "annex_a"}
            for c in ISO27001_DEFINITION.all_controls()
        ]
        return clauses + annex
    if framework == "nist_csf":
        from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION

        return [
            {"id": c.id, "title": c.title, "criticality": c.criticality}
            for c in NIST_CSF_DEFINITION.all_controls()
        ]
    raise ValueError(f"unknown framework: {framework}")


def build_rows(module_name: str | None = None, framework: str = "dpdpa") -> list[dict[str, str]]:
    default_module, draft_attr, meta_attr, _ = FRAMEWORKS[framework]
    module = importlib.import_module(module_name or default_module)
    draft = getattr(module, draft_attr)
    meta = getattr(module, meta_attr)

    rows: list[dict[str, str]] = []
    for req in _requirements(framework, module):
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


def build_description_rows(module_name: str | None = None) -> list[dict[str, str]]:
    """ISO own-words descriptions (D-P6-J): clauses first, then Annex A."""
    module = importlib.import_module(module_name or FRAMEWORKS["iso27001"][0])
    own = module.ISO27001_OWN_WORDS_DRAFT
    return [
        {
            "requirement_id": req["id"],
            "requirement_title": req["title"],
            "source": req["source"],
            "current_reference": req["reference"],
            "own_words_description": own[req["id"]],
            "decision": "",
            "edited_description": "",
            "reviewer_note": "",
        }
        for req in _requirements("iso27001", module)
    ]


def write_csv(rows: list[dict[str, str]], out: Path, columns: list[str] = COLUMNS) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--framework", choices=sorted(FRAMEWORKS), default="dpdpa")
    parser.add_argument("--module", default=None, help="draft module (default: the framework's)")
    parser.add_argument("--out", default=None, help="criteria CSV path")
    parser.add_argument("--descriptions-out", default=None, help="iso27001 only: descriptions CSV path")
    args = parser.parse_args(argv)
    if args.descriptions_out and args.framework != "iso27001":
        parser.error("--descriptions-out applies to --framework iso27001 only")

    out = Path(args.out) if args.out else REVIEW_DIR / FRAMEWORKS[args.framework][3]
    rows = build_rows(args.module, args.framework)
    write_csv(rows, out)
    print(f"Wrote {len(rows)} criteria to {out}")

    if args.framework == "iso27001":
        desc_out = Path(args.descriptions_out) if args.descriptions_out else REVIEW_DIR / ISO_DESCRIPTIONS_CSV
        desc_rows = build_description_rows(args.module)
        write_csv(desc_rows, desc_out, DESCRIPTION_COLUMNS)
        print(f"Wrote {len(desc_rows)} descriptions to {desc_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
