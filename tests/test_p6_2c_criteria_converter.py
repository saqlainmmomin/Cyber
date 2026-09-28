"""TDD ("red") contract suite for P6-2c-conv: the generalised criteria converter.

Written by the designer before the implementation. It pins the interface in
``tasks/handoffs/2026-09-28-p6-2c-iso-nist-criteria.md`` (decisions
D-P6-2c-A..K) and must turn green WITHOUT edits. If an assertion looks wrong,
report it in the handoff's Results; do not change it.

Two groups:

* **Converter contract (scenarios 1-9).** Synthetic tmp sheets only, so they
  run before Saqlain signs anything. They fail today because
  ``scripts/convert_criteria.py`` supports only ``dpdpa``.
* **Attachment contract (scenarios 10-11).** Skipped until the signed sheet
  for that framework is committed under ``tasks/criteria-review/signed/``.
  Once it is, they must pass: that is the per-framework conversion PR.

No network, no LLM.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SIGNED_DIR = REPO_ROOT / "tasks" / "criteria-review" / "signed"
NIST_SIGNED = SIGNED_DIR / "nist-csf-criteria-v1.csv"
ISO_SIGNED = SIGNED_DIR / "iso27001-criteria-v1.csv"
ISO_DESC_SIGNED = SIGNED_DIR / "iso27001-descriptions-v1.csv"
LEGACY_6GRAMS = REPO_ROOT / "scripts" / "data" / "iso27001_legacy_6gram_sha256.txt"

# A 6-word run from the pre-conversion ISO pack text (the legacy description
# of ISO.A5.1). Its hash is in LEGACY_6GRAMS; the words are cited, not copied.
LEGACY_RUN = "policies for information security shall be"


def converter():
    return importlib.import_module("scripts.convert_criteria")


def _columns() -> list[str]:
    from scripts import export_criteria_review

    return list(export_criteria_review.COLUMNS)


def _desc_columns() -> list[str]:
    from scripts import export_criteria_review

    return list(export_criteria_review.DESCRIPTION_COLUMNS)


def _write(tmp_path: Path, rows: list[dict[str, str]], columns: list[str], name: str) -> Path:
    path = tmp_path / name
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def _row(**overrides) -> dict[str, str]:
    row = {col: "" for col in _columns()}
    row.update(
        {
            "requirement_id": "NIST.GV.OC.01",
            "requirement_title": "Organizational mission understanding",
            "criticality": "high",
            "criterion_id": "NIST.GV.OC.01.TC1",
            "kind": "design",
            "statement": "A written mission statement exists and leadership approved it.",
            "evidence_hint": "risk_management_strategy",
            "source_basis": "NIST CSF 2.0 GV.OC-01",
            "drafter_confidence": "high",
            "decision": "approve",
        }
    )
    row.update(overrides)
    return row


def _iso_row(**overrides) -> dict[str, str]:
    base = {
        "requirement_id": "ISO.A5.15",
        "requirement_title": "Access control",
        "criticality": _iso_criticality("ISO.A5.15"),
        "criterion_id": "ISO.A5.15.TC1",
        "statement": "A written access policy sets need-to-know and least-privilege rules.",
        "evidence_hint": "access_control_policy",
        "source_basis": "ISO/IEC 27001:2022 A.5.15",
    }
    base.update(overrides)
    return _row(**base)


def _iso_criticality(control_id: str) -> str:
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION

    return {c.id: c.criticality for c in ISO27001_DEFINITION.all_controls()}[control_id]


def _iso_ids() -> list[str]:
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION

    return [c.id for c in ISO27001_DEFINITION.all_controls()]


def _nist_ids() -> list[str]:
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION

    return [c.id for c in NIST_CSF_DEFINITION.all_controls()]


def _desc_rows(**per_id_overrides) -> list[dict[str, str]]:
    """A complete, fully-approved description sheet: one clause row + all 93 Annex A rows."""
    rows = [
        {
            "requirement_id": "ISO.C9.2",
            "requirement_title": "Internal audit",
            "source": "clause",
            "current_reference": "Clause 9.2",
            "own_words_description": "The organisation audits its own ISMS on a planned cycle.",
            "decision": "approve",
            "edited_description": "",
            "reviewer_note": "",
        }
    ]
    for cid in _iso_ids():
        row = {
            "requirement_id": cid,
            "requirement_title": cid,
            "source": "annex_a",
            "current_reference": "Annex A",
            "own_words_description": f"Own-words summary for {cid}.",
            "decision": "approve",
            "edited_description": "",
            "reviewer_note": "",
        }
        row.update(per_id_overrides.get(cid, {}))
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# Scenario 1: framework registry of the converter
# --------------------------------------------------------------------------- #


def test_scenario_1_supported_frameworks_and_default_paths():
    mod = converter()
    assert mod.SUPPORTED_FRAMEWORKS == ("dpdpa", "iso27001", "nist_csf")
    assert mod.SIGNED_SHEETS == {
        "dpdpa": SIGNED_DIR / "dpdpa-criteria-v1.csv",
        "iso27001": ISO_SIGNED,
        "nist_csf": NIST_SIGNED,
    }
    crit = REPO_ROOT / "app" / "frameworks" / "criteria"
    assert mod.OUTPUT_MODULES == {
        "dpdpa": crit / "dpdpa.py",
        "iso27001": crit / "iso27001.py",
        "nist_csf": crit / "nist_csf.py",
    }
    assert mod.SIGNED_DESCRIPTION_SHEET == ISO_DESC_SIGNED
    assert mod.LEGACY_ISO_6GRAMS == LEGACY_6GRAMS


def test_scenario_1_unknown_framework_exits_nonzero(tmp_path):
    mod = converter()
    with pytest.raises(SystemExit) as excinfo:
        mod.main(["--framework", "gdpr", "--out", str(tmp_path / "x.py")])
    assert excinfo.value.code != 0


# --------------------------------------------------------------------------- #
# Scenario 2: NIST rows validate against the NIST pack, output in pack order
# --------------------------------------------------------------------------- #


def test_scenario_2_nist_rows_convert_in_pack_order():
    mod = converter()
    rows = [
        _row(requirement_id="NIST.RC.CO.04", requirement_title="x",
             criticality=_crit("NIST.RC.CO.04"), criterion_id="NIST.RC.CO.04.TC1"),
        _row(),
        _row(criterion_id="NIST.GV.OC.01.TC2", decision="edit", edited_statement="Edited."),
        _row(criterion_id="NIST.GV.OC.01.TC3", decision="reject"),
    ]
    result = mod.approved_criteria(rows, "nist_csf")
    assert list(result) == ["NIST.GV.OC.01", "NIST.RC.CO.04"]
    assert [tc.id for tc in result["NIST.GV.OC.01"]] == ["NIST.GV.OC.01.TC1", "NIST.GV.OC.01.TC2"]
    assert result["NIST.GV.OC.01"][1].statement == "Edited."


def _crit(control_id: str) -> str:
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION

    return {c.id: c.criticality for c in NIST_CSF_DEFINITION.all_controls()}[control_id]


@pytest.mark.parametrize(
    "overrides",
    [
        {"requirement_id": "NIST.RS.CO.04", "criterion_id": "NIST.RS.CO.04.TC1"},  # withdrawn, not in pack
        {"requirement_id": "CH2.CONSENT.1", "criterion_id": "CH2.CONSENT.1.TC1"},  # another framework's id
        {"criticality": "low"},
        {"decision": ""},
    ],
    ids=["withdrawn_id", "foreign_id", "criticality_mismatch", "unsigned"],
)
def test_scenario_2_invalid_nist_rows_raise(overrides):
    mod = converter()
    assert mod.approved_criteria([_row()], "nist_csf")  # the valid baseline converts
    with pytest.raises(ValueError):
        mod.approved_criteria([_row(**overrides)], "nist_csf")


# --------------------------------------------------------------------------- #
# Scenario 3: ISO Annex A rows convert; clause rows are deferred, not dropped silently
# --------------------------------------------------------------------------- #


def test_scenario_3_iso_annex_row_converts():
    mod = converter()
    result = mod.approved_criteria([_iso_row()], "iso27001")
    [tc] = result["ISO.A5.15"]
    assert tc.id == "ISO.A5.15.TC1"
    assert tc.source_basis == "ISO/IEC 27001:2022 A.5.15"


def test_scenario_3_signed_clause_rows_are_deferred():
    mod = converter()
    clause = _iso_row(requirement_id="ISO.C9.2", requirement_title="Internal audit",
                      criticality="critical", criterion_id="ISO.C9.2.TC1",
                      source_basis="ISO/IEC 27001:2022 cl.9.2.2")
    result = mod.approved_criteria([clause, _iso_row()], "iso27001")
    assert list(result) == ["ISO.A5.15"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"decision": ""},
        {"decision": "edit", "edited_statement": ""},
        {"criterion_id": "ISO.C9.2.X1"},
        {"kind": "advisory"},
    ],
    ids=["unsigned", "empty_edit", "bad_criterion_id", "bad_kind"],
)
def test_scenario_3_deferred_clause_rows_are_still_validated(overrides):
    mod = converter()
    clause = _iso_row(requirement_id="ISO.C9.2", requirement_title="Internal audit",
                      criticality="critical", criterion_id="ISO.C9.2.TC1")
    assert mod.approved_criteria([dict(clause)], "iso27001") == {}  # valid, deferred
    clause.update(overrides)
    with pytest.raises(ValueError):
        mod.approved_criteria([clause], "iso27001")


def test_scenario_3_unknown_iso_id_raises():
    mod = converter()
    assert mod.approved_criteria([_iso_row()], "iso27001")
    with pytest.raises(ValueError):
        mod.approved_criteria(
            [_iso_row(requirement_id="ISO.A9.9", criterion_id="ISO.A9.9.TC1")], "iso27001"
        )


# --------------------------------------------------------------------------- #
# Scenario 4: the own-words guard (D4 / E-C5) on ISO criteria
# --------------------------------------------------------------------------- #


def test_scenario_4_legacy_corpus_is_hashes_only():
    lines = [l for l in LEGACY_6GRAMS.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    assert len(lines) > 500
    assert all(len(l) == 64 and set(l) <= set("0123456789abcdef") for l in lines)
    assert lines == sorted(set(lines))
    assert hashlib.sha256(LEGACY_RUN.encode()).hexdigest() in set(lines)


def test_scenario_4_own_words_violations_normalises_and_reports():
    mod = converter()
    assert mod.own_words_violations("Staff read the Policies, for information-security; shall be it.") == [
        LEGACY_RUN
    ]
    assert mod.own_words_violations("An access policy exists and is approved.") == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"statement": f"Records show {LEGACY_RUN} reviewed yearly."},
        {"decision": "edit", "edited_statement": f"Records show {LEGACY_RUN} reviewed yearly."},
        {"evidence_hint": f"{LEGACY_RUN} documented"},
    ],
    ids=["statement", "edited_statement", "evidence_hint"],
)
def test_scenario_4_iso_row_copying_legacy_text_raises(overrides):
    mod = converter()
    assert mod.approved_criteria([_iso_row()], "iso27001")
    with pytest.raises(ValueError, match="ISO.A5.15.TC1"):
        mod.approved_criteria([_iso_row(**overrides)], "iso27001")


def test_scenario_4_a_rejected_row_is_not_checked_for_own_words():
    mod = converter()
    rows = [_iso_row(statement=f"Records show {LEGACY_RUN} reviewed.", decision="reject")]
    assert mod.approved_criteria(rows, "iso27001") == {}


def test_scenario_4_guard_is_iso_only():
    mod = converter()
    # NIST text is public domain; the ISO guard must not fire on it.
    result = mod.approved_criteria([_row(statement=f"Staff note {LEGACY_RUN} fine.")], "nist_csf")
    assert "NIST.GV.OC.01" in result


# --------------------------------------------------------------------------- #
# Scenario 5: ISO own-words descriptions sheet
# --------------------------------------------------------------------------- #


def test_scenario_5_descriptions_cover_annex_a_in_pack_order_and_defer_clauses(tmp_path):
    mod = converter()
    path = _write(tmp_path, _desc_rows(), _desc_columns(), "desc.csv")
    rows = mod.load_description_sheet(path)
    result = mod.approved_descriptions(rows)
    assert list(result) == _iso_ids()
    assert "ISO.C9.2" not in result
    assert result["ISO.A5.1"] == "Own-words summary for ISO.A5.1."


def test_scenario_5_edit_uses_edited_description():
    mod = converter()
    rows = _desc_rows(**{"ISO.A5.1": {"decision": "edit", "edited_description": "Better wording."}})
    assert mod.approved_descriptions(rows)["ISO.A5.1"] == "Better wording."


@pytest.mark.parametrize(
    "case",
    ["reject", "blank", "empty_edit", "missing_control", "duplicate", "unknown_id", "legacy_text"],
)
def test_scenario_5_invalid_description_sheets_raise(case):
    mod = converter()
    rows = _desc_rows()
    assert len(mod.approved_descriptions(rows)) == 93  # the valid baseline converts
    target = next(r for r in rows if r["requirement_id"] == "ISO.A5.1")
    if case == "reject":
        target["decision"] = "reject"  # every Annex A control needs a description; use edit
    elif case == "blank":
        target["decision"] = ""
    elif case == "empty_edit":
        target.update(decision="edit", edited_description="")
    elif case == "missing_control":
        rows.remove(target)
    elif case == "duplicate":
        rows.append(dict(target))
    elif case == "unknown_id":
        target["requirement_id"] = "ISO.A9.9"
    elif case == "legacy_text":
        target["own_words_description"] = f"The organisation keeps {LEGACY_RUN} current."
    with pytest.raises(ValueError):
        mod.approved_descriptions(rows)


def test_scenario_5_description_sheet_columns_are_checked(tmp_path):
    mod = converter()
    columns = [c for c in _desc_columns() if c != "reviewer_note"]
    rows = [{k: v for k, v in r.items() if k != "reviewer_note"} for r in _desc_rows()]
    path = _write(tmp_path, rows, columns, "desc.csv")
    with pytest.raises(ValueError):
        mod.load_description_sheet(path)


# --------------------------------------------------------------------------- #
# Scenario 6: rendering per framework
# --------------------------------------------------------------------------- #


def _exec(source: str) -> dict:
    namespace: dict = {}
    exec(compile(source, "<generated>", "exec"), namespace)  # noqa: S102
    return namespace


def test_scenario_6_nist_module_names_and_header():
    mod = converter()
    criteria = mod.approved_criteria([_row()], "nist_csf")
    source = mod.render_module(criteria, sheet_sha256="ab" * 32, criteria_version="criteria-v1",
                               framework="nist_csf")
    assert source.startswith('"""Generated by scripts/convert_criteria.py; do not edit by hand.')
    assert "tasks/criteria-review/signed/nist-csf-criteria-v1.csv" in source
    assert "dpdpa" not in source.lower()
    ns = _exec(source)
    assert ns["NIST_CSF_CRITERIA_VERSION"] == "criteria-v1"
    assert ns["NIST_CSF_CRITERIA_SHEET_SHA256"] == "ab" * 32
    assert ns["NIST_CSF_CRITERIA"] == criteria


def test_scenario_6_iso_module_carries_descriptions():
    mod = converter()
    criteria = mod.approved_criteria([_iso_row()], "iso27001")
    descriptions = mod.approved_descriptions(_desc_rows())
    source = mod.render_module(criteria, sheet_sha256="cd" * 32, criteria_version="criteria-v1",
                               framework="iso27001", descriptions=descriptions,
                               descriptions_sha256="ef" * 32)
    assert "tasks/criteria-review/signed/iso27001-criteria-v1.csv" in source
    assert "tasks/criteria-review/signed/iso27001-descriptions-v1.csv" in source
    ns = _exec(source)
    assert ns["ISO27001_CRITERIA_VERSION"] == "criteria-v1"
    assert ns["ISO27001_CRITERIA_SHEET_SHA256"] == "cd" * 32
    assert ns["ISO27001_DESCRIPTIONS_SHEET_SHA256"] == "ef" * 32
    assert ns["ISO27001_CRITERIA"] == criteria
    assert ns["ISO27001_DESCRIPTIONS"] == descriptions
    assert list(ns["ISO27001_DESCRIPTIONS"]) == _iso_ids()


def test_scenario_6_iso_render_requires_descriptions():
    mod = converter()
    criteria = mod.approved_criteria([_iso_row()], "iso27001")
    with pytest.raises(ValueError):
        mod.render_module(criteria, sheet_sha256="cd" * 32, criteria_version="criteria-v1",
                          framework="iso27001")


# --------------------------------------------------------------------------- #
# Scenario 7: main() end to end on synthetic sheets
# --------------------------------------------------------------------------- #


def test_scenario_7_nist_main_writes_then_checks(tmp_path):
    mod = converter()
    sheet = _write(tmp_path, [_row()], _columns(), "nist.csv")
    out = tmp_path / "nist_csf.py"
    assert mod.main(["--framework", "nist_csf", "--sheet", str(sheet), "--out", str(out)]) == 0
    first = out.read_bytes()
    assert mod.main(["--framework", "nist_csf", "--sheet", str(sheet), "--out", str(out)]) == 0
    assert out.read_bytes() == first
    assert mod.main(["--framework", "nist_csf", "--sheet", str(sheet), "--out", str(out), "--check"]) == 0
    out.write_text(first.decode("utf-8") + "# hand edit\n", encoding="utf-8")
    assert mod.main(["--framework", "nist_csf", "--sheet", str(sheet), "--out", str(out), "--check"]) != 0
    ns = _exec(first.decode("utf-8"))
    assert ns["NIST_CSF_CRITERIA_SHEET_SHA256"] == hashlib.sha256(sheet.read_bytes()).hexdigest()


def test_scenario_7_iso_main_needs_and_uses_the_descriptions_sheet(tmp_path):
    mod = converter()
    sheet = _write(tmp_path, [_iso_row()], _columns(), "iso.csv")
    desc = _write(tmp_path, _desc_rows(), _desc_columns(), "desc.csv")
    out = tmp_path / "iso27001.py"
    args = ["--framework", "iso27001", "--sheet", str(sheet), "--out", str(out)]
    assert mod.main([*args, "--descriptions-sheet", str(tmp_path / "missing.csv")]) != 0
    assert mod.main([*args, "--descriptions-sheet", str(desc)]) == 0
    ns = _exec(out.read_text(encoding="utf-8"))
    assert ns["ISO27001_DESCRIPTIONS_SHEET_SHA256"] == hashlib.sha256(desc.read_bytes()).hexdigest()
    assert mod.main([*args, "--descriptions-sheet", str(desc), "--check"]) == 0


def test_scenario_7_descriptions_sheet_is_iso_only(tmp_path):
    mod = converter()
    sheet = _write(tmp_path, [_row()], _columns(), "nist.csv")
    with pytest.raises(SystemExit) as excinfo:
        mod.main(["--framework", "nist_csf", "--sheet", str(sheet), "--out", str(tmp_path / "o.py"),
                  "--descriptions-sheet", str(sheet)])
    assert excinfo.value.code != 0


def test_scenario_7_main_exits_nonzero_on_legacy_iso_text(tmp_path):
    mod = converter()
    sheet = _write(tmp_path, [_iso_row(statement=f"Records show {LEGACY_RUN} set.")], _columns(), "iso.csv")
    desc = _write(tmp_path, _desc_rows(), _desc_columns(), "desc.csv")
    rc = mod.main(["--framework", "iso27001", "--sheet", str(sheet), "--out", str(tmp_path / "o.py"),
                   "--descriptions-sheet", str(desc)])
    assert rc != 0


# --------------------------------------------------------------------------- #
# Scenario 8: DPDPA is unchanged by the generalisation
# --------------------------------------------------------------------------- #


def test_scenario_8_dpdpa_check_still_passes_with_defaults():
    mod = converter()
    assert mod.main(["--framework", "dpdpa", "--check"]) == 0
    assert mod.main(["--check"]) == 0  # dpdpa stays the default framework


# --------------------------------------------------------------------------- #
# Scenario 9: generated modules never import the drafts
# --------------------------------------------------------------------------- #


def test_scenario_9_rendered_modules_do_not_import_drafts():
    mod = converter()
    nist = mod.render_module(mod.approved_criteria([_row()], "nist_csf"), sheet_sha256="0" * 64,
                             criteria_version="criteria-v1", framework="nist_csf")
    iso = mod.render_module(mod.approved_criteria([_iso_row()], "iso27001"), sheet_sha256="0" * 64,
                            criteria_version="criteria-v1", framework="iso27001",
                            descriptions=mod.approved_descriptions(_desc_rows()),
                            descriptions_sha256="0" * 64)
    for source in (nist, iso):
        assert "_draft" not in source


# --------------------------------------------------------------------------- #
# Scenario 10: NIST attachment (skipped until Saqlain's signed sheet is committed)
# --------------------------------------------------------------------------- #

needs_nist = pytest.mark.skipif(not NIST_SIGNED.exists(), reason="NIST sheet not signed yet (P6-2c review)")
needs_iso = pytest.mark.skipif(
    not (ISO_SIGNED.exists() and ISO_DESC_SIGNED.exists()),
    reason="ISO sheets not signed yet (P6-2c review)",
)


@needs_nist
def test_scenario_10_nist_controls_carry_the_generated_criteria():
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
    from app.services.grounding.judge import criteria_for

    gen = importlib.import_module("app.frameworks.criteria.nist_csf")
    assert converter().main(["--framework", "nist_csf", "--check"]) == 0
    assert gen.NIST_CSF_CRITERIA_SHEET_SHA256 == hashlib.sha256(NIST_SIGNED.read_bytes()).hexdigest()
    assert NIST_CSF_DEFINITION.version == "2.0"
    assert NIST_CSF_DEFINITION.criteria_version == gen.NIST_CSF_CRITERIA_VERSION == "criteria-v1"
    assert NIST_CSF_DEFINITION.pack_version == "2.0+criteria-v1"
    for ctrl in NIST_CSF_DEFINITION.all_controls():
        assert ctrl.test_criteria == gen.NIST_CSF_CRITERIA.get(ctrl.id, ())
        source, _ = criteria_for(ctrl)
        assert source == ("approved" if ctrl.test_criteria else "fallback")


# --------------------------------------------------------------------------- #
# Scenario 11: ISO attachment + own-words descriptions (skipped until signed)
# --------------------------------------------------------------------------- #


@needs_iso
def test_scenario_11_iso_controls_carry_generated_criteria_and_descriptions():
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION

    mod = converter()
    gen = importlib.import_module("app.frameworks.criteria.iso27001")
    assert mod.main(["--framework", "iso27001", "--check"]) == 0
    assert gen.ISO27001_CRITERIA_SHEET_SHA256 == hashlib.sha256(ISO_SIGNED.read_bytes()).hexdigest()
    assert gen.ISO27001_DESCRIPTIONS_SHEET_SHA256 == hashlib.sha256(ISO_DESC_SIGNED.read_bytes()).hexdigest()
    assert ISO27001_DEFINITION.version == "2022"
    assert ISO27001_DEFINITION.pack_version == "2022+criteria-v1"
    for ctrl in ISO27001_DEFINITION.all_controls():
        assert ctrl.description == gen.ISO27001_DESCRIPTIONS[ctrl.id]
        assert ctrl.test_criteria == gen.ISO27001_CRITERIA.get(ctrl.id, ())
        assert mod.own_words_violations(ctrl.description) == [], ctrl.id
        for tc in ctrl.test_criteria:
            assert mod.own_words_violations(tc.statement) == [], tc.id
    for qdef in ISO27001_DEFINITION.questions.values():
        assert mod.own_words_violations(qdef.guidance) == [], qdef.control_id


@needs_iso
def test_scenario_11_iso_definition_source_has_no_description_literals():
    """The near-verbatim ISO text leaves the source file, not just the runtime objects."""
    source = (REPO_ROOT / "app" / "frameworks" / "definitions" / "iso27001.py").read_text(encoding="utf-8")
    literal_descriptions = [
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", None) == "Control"
        for kw in node.keywords
        if kw.arg == "description" and isinstance(kw.value, ast.Constant)
    ]
    assert literal_descriptions == []
