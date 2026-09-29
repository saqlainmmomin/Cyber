"""TDD ("red") contract suite for P6-2b: the DPDPA criteria converter.

Written by the designer before the implementation. It pins the interface in
``tasks/handoffs/2026-09-28-p6-2b-dpdpa-criteria-converter.md`` (decisions
D-P6-2b-A..G) and must turn green WITHOUT edits. If an assertion looks wrong,
report it in the handoff's Results; do not change it.

Modules under contract (do not exist yet): ``scripts.convert_criteria`` and
``app.frameworks.criteria.dpdpa`` (the generated module, built by running the
script against the signed sheet). Before implementation, every test that
imports either one fails with ``ModuleNotFoundError``.

No network, no LLM. Everything here is CSV parsing, pure functions, and a
Stage-0/1 grounding run with zero sources (so the empty-claim-set branch is
exercised without needing an LLM stub).
"""

from __future__ import annotations

import csv
import importlib
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SIGNED_SHEET = REPO_ROOT / "tasks" / "criteria-review" / "signed" / "dpdpa-criteria-v1.csv"
SIGNED_SHA256 = "228df4d572b42aefdd9638017a6a84210802717c2ce400ed2cb172fb2e850a75"
GENERATED_MODULE = REPO_ROOT / "app" / "frameworks" / "criteria" / "dpdpa.py"


def converter():
    return importlib.import_module("scripts.convert_criteria")


def generated():
    return importlib.import_module("app.frameworks.criteria.dpdpa")


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


def _read_signed_rows() -> list[dict[str, str]]:
    with SIGNED_SHEET.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_sheet(tmp_path: Path, rows: list[dict[str, str]], columns: list[str], name: str = "sheet.csv") -> Path:
    path = tmp_path / name
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def _base_row(**overrides) -> dict[str, str]:
    from scripts import export_criteria_review

    row = {col: "" for col in export_criteria_review.COLUMNS}
    row.update(
        {
            "requirement_id": "CH2.CONSENT.1",
            "requirement_title": "Lawful basis for processing with free, specific, informed consent",
            "criticality": "critical",
            "criterion_id": "CH2.CONSENT.1.TC1",
            "kind": "design",
            "statement": "Consent requires a clear affirmative action.",
            "evidence_hint": "consent_forms",
            "source_basis": "DPDPA s.6(1)",
            "in_force_note": "note",
            "drafter_confidence": "high",
            "decision": "approve",
            "edited_statement": "",
            "reviewer_note": "",
        }
    )
    row.update(overrides)
    return row


# --------------------------------------------------------------------------- #
# Scenario 1: round trip on the real signed sheet
# --------------------------------------------------------------------------- #


def test_scenario_1_round_trip_on_the_signed_sheet_yields_150_criteria_over_41_requirements():
    mod = converter()
    rows = mod.load_sheet(SIGNED_SHEET)
    signed_rows = _read_signed_rows()
    assert len(rows) == len(signed_rows) == 150

    result = mod.approved_criteria(rows, "dpdpa")
    assert len(result) == 41
    total = sum(len(v) for v in result.values())
    assert total == 150

    by_id = {r["criterion_id"]: r for r in signed_rows}
    for req_id, criteria in result.items():
        for tc in criteria:
            sheet_row = by_id[tc.id]
            assert sheet_row["requirement_id"] == req_id
            assert sheet_row["decision"] == "approve"
            assert tc.statement == sheet_row["statement"]
            assert tc.kind == sheet_row["kind"]
            assert tc.evidence_hint == sheet_row["evidence_hint"]
            assert tc.source_basis == sheet_row["source_basis"]


# --------------------------------------------------------------------------- #
# Scenario 2: --check passes; generation is deterministic and matches committed
# --------------------------------------------------------------------------- #


def test_scenario_2_check_passes_against_the_committed_module():
    mod = converter()
    assert mod.main(["--framework", "dpdpa", "--sheet", str(SIGNED_SHEET), "--check"]) == 0


def test_scenario_2_generating_twice_is_byte_identical_and_matches_committed(tmp_path):
    mod = converter()
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    assert mod.main(["--framework", "dpdpa", "--sheet", str(SIGNED_SHEET), "--out", str(a)]) == 0
    assert mod.main(["--framework", "dpdpa", "--sheet", str(SIGNED_SHEET), "--out", str(b)]) == 0
    assert a.read_bytes() == b.read_bytes()
    assert a.read_bytes() == GENERATED_MODULE.read_bytes()


# --------------------------------------------------------------------------- #
# Scenario 3: the committed module's sha256 constant matches the sheet
# --------------------------------------------------------------------------- #


def test_scenario_3_committed_sha256_constant_matches_the_signed_sheet():
    import hashlib

    mod = generated()
    actual = hashlib.sha256(SIGNED_SHEET.read_bytes()).hexdigest()
    assert actual == SIGNED_SHA256
    assert mod.DPDPA_CRITERIA_SHEET_SHA256 == actual


# --------------------------------------------------------------------------- #
# Scenario 4: decision rules on small synthetic tmp sheets
# --------------------------------------------------------------------------- #

SHEET_COLUMNS = None  # filled in lazily below since export_criteria_review is import-light


def _columns():
    global SHEET_COLUMNS
    if SHEET_COLUMNS is None:
        from scripts import export_criteria_review

        SHEET_COLUMNS = export_criteria_review.COLUMNS
    return SHEET_COLUMNS


def test_scenario_4_edit_uses_edited_statement():
    mod = converter()
    rows = [_base_row(decision="edit", edited_statement="The edited wording.")]
    result = mod.approved_criteria(rows, "dpdpa")
    [tc] = result["CH2.CONSENT.1"]
    assert tc.statement == "The edited wording."


def test_scenario_4_reject_drops_the_criterion():
    mod = converter()
    rows = [
        _base_row(decision="approve"),
        _base_row(criterion_id="CH2.CONSENT.1.TC2", decision="reject"),
    ]
    result = mod.approved_criteria(rows, "dpdpa")
    ids = {tc.id for tc in result["CH2.CONSENT.1"]}
    assert ids == {"CH2.CONSENT.1.TC1"}


def test_scenario_4_all_rejected_requirement_is_absent():
    mod = converter()
    rows = [_base_row(decision="reject")]
    result = mod.approved_criteria(rows, "dpdpa")
    assert "CH2.CONSENT.1" not in result


@pytest.mark.parametrize(
    "overrides",
    [
        {"decision": ""},
        {"decision": "edit", "edited_statement": ""},
        {"decision": "bogus"},
        {"requirement_id": "NOT.A.REAL.CONTROL"},
        {"criterion_id": "CH2.CONSENT.1.BADFORMAT"},
        {"kind": "advisory"},
        {"statement": ""},
        {"criticality": "medium"},  # sheet row says medium; pack control CH2.CONSENT.1 is critical
    ],
    ids=[
        "blank_decision", "empty_edit", "unknown_decision", "unknown_requirement_id",
        "bad_criterion_id_format", "bad_kind", "empty_statement", "criticality_mismatch",
    ],
)
def test_scenario_4_invalid_rows_raise_value_error(overrides):
    mod = converter()
    rows = [_base_row(**overrides)]
    with pytest.raises(ValueError):
        mod.approved_criteria(rows, "dpdpa")


def test_scenario_4_duplicate_criterion_id_raises():
    mod = converter()
    rows = [_base_row(), _base_row()]
    with pytest.raises(ValueError):
        mod.approved_criteria(rows, "dpdpa")


def test_scenario_4_extra_column_raises(tmp_path):
    mod = converter()
    columns = [*_columns(), "unexpected_column"]
    row = _base_row()
    row["unexpected_column"] = "x"
    path = _write_sheet(tmp_path, [row], columns)
    with pytest.raises(ValueError):
        mod.load_sheet(path)


def test_scenario_4_missing_column_raises(tmp_path):
    mod = converter()
    columns = [c for c in _columns() if c != "reviewer_note"]
    row = _base_row()
    del row["reviewer_note"]
    path = _write_sheet(tmp_path, [row], columns)
    with pytest.raises(ValueError):
        mod.load_sheet(path)


def test_scenario_4_main_exits_nonzero_on_an_unsigned_row(tmp_path):
    mod = converter()
    row = _base_row(decision="")
    path = _write_sheet(tmp_path, [row], _columns())
    out = tmp_path / "out.py"
    rc = mod.main(["--framework", "dpdpa", "--sheet", str(path), "--out", str(out)])
    assert rc != 0


# --------------------------------------------------------------------------- #
# Scenario 5: every DPDPA Control carries its approved criteria; ISO stays fallback
# --------------------------------------------------------------------------- #


def test_scenario_5_every_dpdpa_control_has_its_approved_criteria_and_judge_says_approved():
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
    from app.services.grounding.judge import criteria_for

    dpdpa_mod = generated()
    controls = DPDPA_DEFINITION.all_controls()
    assert len(controls) == 41
    for ctrl in controls:
        assert ctrl.test_criteria == dpdpa_mod.DPDPA_CRITERIA[ctrl.id]
        source, criteria = criteria_for(ctrl)
        assert source == "approved"
        assert len(criteria) == len(ctrl.test_criteria)


def test_scenario_5_an_iso_control_stays_fallback():
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
    from app.services.grounding.judge import criteria_for

    ctrl = ISO27001_DEFINITION.all_controls()[0]
    assert ctrl.test_criteria == ()
    source, criteria = criteria_for(ctrl)
    assert source == "fallback"
    assert len(criteria) == 1


# --------------------------------------------------------------------------- #
# Scenario 6: pack_version
# --------------------------------------------------------------------------- #


def test_scenario_6_dpdpa_pack_version_is_version_plus_criteria_version():
    dpdpa_mod = generated()
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION

    assert DPDPA_DEFINITION.version == "2023"
    assert DPDPA_DEFINITION.criteria_version == dpdpa_mod.DPDPA_CRITERIA_VERSION
    assert dpdpa_mod.DPDPA_CRITERIA_VERSION == "criteria-v1"
    assert DPDPA_DEFINITION.pack_version == "2023+criteria-v1"


def test_scenario_6_every_other_framework_pack_version_equals_version():
    from app.frameworks.definitions.gdpr import GDPR_DEFINITION
    from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
    from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION

    for fw in (GDPR_DEFINITION, HIPAA_DEFINITION, ISO27001_DEFINITION, NIST_CSF_DEFINITION, PCI_DSS_DEFINITION):
        assert fw.pack_version == fw.version, fw.id


def test_scenario_6_new_engagement_stores_pack_version_on_the_assessment_pack(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import app.models  # noqa: F401 - register all ORM tables
    from app.database import Base
    from app.models.assessment_pack import AssessmentPack
    from app.models.client import Client
    from app.services.engagement_factory import create_engagement_with_assessment

    engine = create_engine(
        f"sqlite:///{tmp_path / 'p6_2b.sqlite3'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        client = Client(name=f"Acme {uuid.uuid4().hex[:6]}", industry="Technology", size="medium")
        db.add(client)
        db.flush()
        engagement = create_engagement_with_assessment(
            db,
            client=client,
            engagement_name="Acme gap",
            engagement_type="gap_assessment",
            description=None,
            framework_ids=["dpdpa"],
        )
        assessment = engagement.assessments[0] if hasattr(engagement, "assessments") else None
        packs = (
            db.query(AssessmentPack)
            .filter(AssessmentPack.assessment_id == (assessment.id if assessment else None))
            .all()
        ) if assessment else db.query(AssessmentPack).all()
        [pack] = [p for p in packs if p.framework_id == "dpdpa"]
        assert pack.pack_version == "2023+criteria-v1"
    finally:
        db.close()
        engine.dispose()


# --------------------------------------------------------------------------- #
# Scenario 7: the v2 pipeline's claim-set pack_versions uses pack_version
# --------------------------------------------------------------------------- #


def test_scenario_7_claim_set_pack_versions_uses_pack_version():
    from app.services.grounding.pipeline import run_stages_0_1

    claim_set = run_stages_0_1(sources=[], framework_ids=("dpdpa",))
    assert claim_set.pack_versions == {"dpdpa": "2023+criteria-v1"}


def test_scenario_7b_fresh_claim_set_is_current_and_old_version_is_stale():
    # D-P6-2b-E: claims.py must compare against pack_version too, or every
    # DPDPA claim set built after this change would read as stale forever.
    import dataclasses

    from app.services.grounding.claims import claim_set_is_current
    from app.services.grounding.pipeline import run_stages_0_1

    claim_set = run_stages_0_1(sources=[], framework_ids=("dpdpa",))
    assert claim_set_is_current(claim_set, [], ("dpdpa",))
    old = dataclasses.replace(claim_set, pack_versions={"dpdpa": "2023"})
    assert not claim_set_is_current(old, [], ("dpdpa",))


# --------------------------------------------------------------------------- #
# Scenario 8: nothing in app/ imports dpdpa_draft outside the criteria package
# --------------------------------------------------------------------------- #


def test_scenario_8_no_app_module_imports_dpdpa_draft_outside_criteria_package():
    import re

    pattern = re.compile(r"\bdpdpa_draft\b")
    criteria_pkg = REPO_ROOT / "app" / "frameworks" / "criteria"
    offenders = [
        str(p.relative_to(REPO_ROOT))
        for p in (REPO_ROOT / "app").rglob("*.py")
        if criteria_pkg not in p.parents and pattern.search(p.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_scenario_8_generated_module_does_not_import_dpdpa_draft():
    source = GENERATED_MODULE.read_text(encoding="utf-8")
    assert "dpdpa_draft" not in source


# --------------------------------------------------------------------------- #
# Scenario 9: claude_analyzer.py never references test_criteria (v1 untouched)
# --------------------------------------------------------------------------- #


def test_scenario_9_claude_analyzer_does_not_reference_test_criteria():
    source = (REPO_ROOT / "app" / "services" / "claude_analyzer.py").read_text(encoding="utf-8")
    assert "test_criteria" not in source


# --------------------------------------------------------------------------- #
# Scenario 10: only dpdpa is supported for now
# --------------------------------------------------------------------------- #


def test_scenario_10_iso27001_framework_exits_nonzero(tmp_path):
    mod = converter()
    out = tmp_path / "out.py"
    with pytest.raises(SystemExit) as excinfo:
        mod.main(["--framework", "iso27001", "--sheet", str(SIGNED_SHEET), "--out", str(out)])
    assert excinfo.value.code != 0


# --------------------------------------------------------------------------- #
# Scenario 11: scope guard
# --------------------------------------------------------------------------- #

P6_2B_ALLOWED_FILES = {
    "tasks/criteria-review/signed/dpdpa-criteria-v1.csv",
    "scripts/convert_criteria.py",
    "app/frameworks/criteria/dpdpa.py",
    "app/frameworks/criteria/__init__.py",
    "app/frameworks/definitions/dpdpa.py",
    "app/frameworks/schema.py",
    "app/services/engagement_factory.py",
    "app/services/grounding/pipeline.py",
    "app/services/grounding/claims.py",
    "tests/test_p6_2a_test_criteria.py",
    "tests/test_p6_2b_dpdpa_criteria.py",
    "tasks/handoffs/2026-09-28-p6-2b-dpdpa-criteria-converter.md",
    "tasks/todo.md",
    # Stale guards (:(exclude) lines) and fallback-era expectations updated for P6-2b.
    "tests/test_longitudinal_demo.py",
    "tests/test_p5_4_adaptive_ucc_questionnaire.py",
    "tests/test_p6_1b_framework_batching.py",
    "tests/test_p6_3a_grounding.py",
    "tests/test_p6_3b_v2_flag.py",
    "tests/test_p6_4_cap_upload_limit.py",
    "tests/test_p6_4_v2_judge.py",
    "tests/test_p6_4_whats_missing.py",
    "tests/test_p6_6_report_foundations.py",
    "tests/test_p6_nist_csf2_alignment.py",
    "tests/test_p6_7_requirement_card.py",
    # Stage C 2026-09-28 harness fix (magic-link evidence lookup) lands after P6-2b.
    "scripts/validation/run_company.py",
    "tests/test_validation_harness.py",
    "tests/test_p6_6_report_foundations.py",
    # Stage C v1 baseline results and c4's CSF 2.0 answers (2026-09-29) land after P6-2b.
    "tasks/handoffs/2026-09-28-next-phase-6-kickoff.md",
    "validation/companies/c4-healthsaas/client_visible/questionnaire_answers.json",
    "tests/test_p6_8_board_report_v2.py",
}
# P6-8 B1 (PR #80) lands after P6-2b; tests/test_p6_8_board_report_v2.py guards its file set.
P6_8_B1_FILES = (
    ".github/workflows/tests.yml", "Dockerfile", "requirements.txt", "app/assets/fonts/noto/",
    "app/routers/snapshots.py", "app/services/board_report.py", "app/services/report_snapshots.py",
    "app/services/standalone_workpaper.py", "app/templates/pages/report_snapshots.html",
    "app/templates/reports/", "app/utils/html_pdf.py", "tasks/handoffs/2026-09-28-p6-8-board-report-v2.md",
    "tests/golden/p6_8_board_document.json", "tests/test_p5_6_rfi_rebuild.py",
    "tests/test_p6_8_board_report_v2.py", "tests/test_report_snapshots.py",
)
# P6-5 (tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md) lands after P6-2b: the injected-document
# pack and quarantine, and the aggregate-only A/B comparison; its contract tests guard them.
P6_5_FILES = (
    "app/services/grounding/injection.py", "app/services/grounding/judge.py", "app/services/analysis_v2.py",
    "scripts/injection_pack_live.py", "scripts/validation/ab_compare.py", "scripts/validation/run_company.py",
    "scripts/validation/score.py", "tests/injection_pack/", "tests/test_p6_5_injection_pack.py",
    "tests/test_p6_5_ab_compare.py", "tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md", "tasks/todo.md",
    "tests/test_p6_3a_grounding.py", "tests/test_p6_4_cap_upload_limit.py", "tests/test_p6_4_whats_missing.py",
    "tests/test_p6_6_report_foundations.py", "tests/test_p6_7_requirement_card.py",
    "tests/test_p6_8_board_report_v2.py", "tests/test_p6_2b_dpdpa_criteria.py",
)


def test_scenario_11_only_p6_2b_files_change():
    committed = subprocess.run(
        ["git", "diff", "--name-only", "main...HEAD"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    ).stdout.split()
    offenders = [f for f in committed if f not in P6_2B_ALLOWED_FILES and not f.startswith(P6_8_B1_FILES)
                and not f.startswith(P6_5_FILES)]
    assert offenders == [], offenders
