"""Convert a signed criteria review sheet into a framework criteria module."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.frameworks.schema import TestCriterion

CRITERIA_VERSION = "criteria-v1"
# framework -> (signed sheet name, generated module name, constant prefix, deferred requirement-id prefixes)
# Deferred rows are signed and validated but not emitted: their requirements are not in the pack yet
# (ISO clauses 4-10, P5-7). Regenerate once the requirements exist and the prefix is dropped.
FRAMEWORK_CONFIG = {
    "dpdpa": ("dpdpa-criteria-v1.csv", "dpdpa.py", "DPDPA", ()),
    "iso27001": ("iso27001-criteria-v1.csv", "iso27001.py", "ISO27001", ("ISO.C",)),
    "nist_csf": ("nist-csf-criteria-v1.csv", "nist_csf.py", "NIST_CSF", ()),
}
SUPPORTED_FRAMEWORKS = tuple(FRAMEWORK_CONFIG)
SIGNED_SHEET = ROOT / "tasks" / "criteria-review" / "signed" / FRAMEWORK_CONFIG["dpdpa"][0]
DEFAULT_OUTPUT = ROOT / "app" / "frameworks" / "criteria" / FRAMEWORK_CONFIG["dpdpa"][1]
SHEET_DISPLAY_PATH = "tasks/criteria-review/signed/dpdpa-criteria-v1.csv"


def _sheet_path(framework: str) -> Path:
    return ROOT / "tasks" / "criteria-review" / "signed" / FRAMEWORK_CONFIG[framework][0]


def _output_path(framework: str) -> Path:
    return ROOT / "app" / "frameworks" / "criteria" / FRAMEWORK_CONFIG[framework][1]


def _sheet_columns() -> list[str]:
    from scripts import export_criteria_review

    return list(export_criteria_review.COLUMNS)


def load_sheet(path: str | Path) -> list[dict[str, str]]:
    """Load a review sheet after checking its exact expected columns."""
    sheet_path = Path(path)
    with sheet_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = _sheet_columns()
        if (
            reader.fieldnames is None
            or len(reader.fieldnames) != len(columns)
            or set(reader.fieldnames) != set(columns)
        ):
            actual = reader.fieldnames or []
            raise ValueError(
                "criteria sheet columns do not match export_criteria_review.COLUMNS: "
                f"expected {columns!r}, got {actual!r}"
            )
        return [dict(row) for row in reader]


def _pack_requirements(framework: str) -> list[dict[str, str]]:
    if framework not in FRAMEWORK_CONFIG:
        raise ValueError(f"unsupported framework: {framework}; supported: {', '.join(FRAMEWORK_CONFIG)}")
    if framework == "dpdpa":
        from app.dpdpa.framework import get_all_requirements

        return get_all_requirements()

    import importlib

    module = importlib.import_module(
        {"iso27001": "app.frameworks.definitions.iso27001", "nist_csf": "app.frameworks.definitions.nist_csf"}[framework]
    )
    definition = getattr(module, {"iso27001": "ISO27001_DEFINITION", "nist_csf": "NIST_CSF_DEFINITION"}[framework])
    return [
        {"id": control.id, "criticality": control.criticality}
        for control in definition.all_controls()
    ]


def _value(row: Mapping[str, str], field: str, criterion_id: str) -> str:
    value = row.get(field)
    if value is None:
        raise ValueError(f"missing {field} for {criterion_id or '<unknown criterion>'}")
    return value


def approved_criteria(
    rows: Sequence[Mapping[str, str]], framework: str
) -> dict[str, tuple[TestCriterion, ...]]:
    """Validate signed rows and return approved criteria in pack order."""
    columns = _sheet_columns()
    requirements = _pack_requirements(framework)
    requirement_map = {requirement["id"]: requirement for requirement in requirements}
    grouped: dict[str, list[TestCriterion]] = {
        requirement["id"]: [] for requirement in requirements
    }
    seen_ids: set[str] = set()

    for row in rows:
        row_keys = set(row)
        if row_keys != set(columns):
            raise ValueError(
                "criteria row columns do not match export_criteria_review.COLUMNS: "
                f"expected {columns!r}, got {sorted(row_keys)!r}"
            )

        requirement_id = _value(row, "requirement_id", "")
        criterion_id = _value(row, "criterion_id", requirement_id)
        deferred = requirement_id.startswith(FRAMEWORK_CONFIG[framework][3]) if FRAMEWORK_CONFIG[framework][3] else False
        if requirement_id not in requirement_map and not deferred:
            raise ValueError(f"unknown requirement_id: {requirement_id}")
        if criterion_id in seen_ids:
            raise ValueError(f"duplicate criterion_id: {criterion_id}")
        seen_ids.add(criterion_id)

        if not re.fullmatch(re.escape(requirement_id) + r"\.TC[1-9]\d*", criterion_id):
            raise ValueError(
                f"criterion_id must match <requirement_id>.TC<n>: {criterion_id}"
            )

        requirement = requirement_map.get(requirement_id)
        if requirement is not None and _value(row, "criticality", criterion_id) != requirement["criticality"]:
            raise ValueError(f"criticality mismatch for {criterion_id}")

        kind = _value(row, "kind", criterion_id)
        if kind not in {"design", "operating"}:
            raise ValueError(f"invalid kind for {criterion_id}: {kind!r}")

        statement = _value(row, "statement", criterion_id)
        if not statement.strip():
            raise ValueError(f"empty statement for {criterion_id}")

        decision = _value(row, "decision", criterion_id)
        if decision not in {"approve", "edit", "reject"}:
            raise ValueError(f"sheet not fully signed: {criterion_id} has decision {decision!r}")
        if decision == "edit":
            statement = _value(row, "edited_statement", criterion_id)
            if not statement.strip():
                raise ValueError(f"empty edited_statement for {criterion_id}")
        if decision == "reject" or requirement is None:
            continue

        grouped[requirement_id].append(
            TestCriterion(
                id=criterion_id,
                statement=statement,
                kind=kind,
                evidence_hint=_value(row, "evidence_hint", criterion_id),
                source_basis=_value(row, "source_basis", criterion_id),
            )
        )

    return {
        requirement_id: tuple(criteria)
        for requirement_id, criteria in grouped.items()
        if criteria
    }


def render_module(
    criteria: Mapping[str, Sequence[TestCriterion]],
    *,
    sheet_sha256: str,
    criteria_version: str,
    framework: str = "dpdpa",
) -> str:
    """Render the deterministic generated criteria module."""
    prefix = FRAMEWORK_CONFIG[framework][2]
    sheet_display = f"tasks/criteria-review/signed/{FRAMEWORK_CONFIG[framework][0]}"
    lines = [
        '"""Generated by scripts/convert_criteria.py; do not edit by hand.',
        f"Source sheet: {sheet_display}",
        f"Source sheet SHA-256: {sheet_sha256}",
        "Regenerate this file from the signed sheet when criteria change.",
        '"""',
        "",
        "from app.frameworks.schema import TestCriterion",
        "",
        f"{prefix}_CRITERIA_VERSION = {criteria_version!r}",
        f"{prefix}_CRITERIA_SHEET_SHA256 = {sheet_sha256!r}",
        "",
        f"{prefix}_CRITERIA: dict[str, tuple[TestCriterion, ...]] = {{",
    ]
    for requirement_id, requirement_criteria in criteria.items():
        lines.append(f"    {requirement_id!r}: (")
        for criterion in requirement_criteria:
            lines.extend(
                [
                    "        TestCriterion(",
                    f"            id={criterion.id!r},",
                    f"            statement={criterion.statement!r},",
                    f"            kind={criterion.kind!r},",
                    f"            evidence_hint={criterion.evidence_hint!r},",
                    f"            source_basis={criterion.source_basis!r},",
                    "        ),",
                ]
            )
        lines.append("    ),")
    lines.extend(["}", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--framework",
        choices=SUPPORTED_FRAMEWORKS,
        default="dpdpa",
        help="framework criteria to convert",
    )
    parser.add_argument("--sheet", default=None, help="signed criteria CSV path (default: the framework's signed sheet)")
    parser.add_argument("--out", default=None, help="generated Python module path (default: the framework's module)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate in memory and fail if the output differs from the committed module",
    )
    args = parser.parse_args(argv)

    sheet_path = Path(args.sheet) if args.sheet else _sheet_path(args.framework)
    output_path = Path(args.out) if args.out else _output_path(args.framework)
    try:
        rows = load_sheet(sheet_path)
        criteria = approved_criteria(rows, args.framework)
        rendered = render_module(
            criteria,
            sheet_sha256=hashlib.sha256(sheet_path.read_bytes()).hexdigest(),
            criteria_version=CRITERIA_VERSION,
            framework=args.framework,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.check:
        try:
            current = output_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot read generated module {output_path}: {exc}", file=sys.stderr)
            return 1
        if current != rendered:
            print(f"error: generated module differs from {output_path}", file=sys.stderr)
            return 1
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote {len(criteria)} requirements to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
