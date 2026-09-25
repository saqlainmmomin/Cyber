"""P6-0e: DPDPA pack correctness (section refs, breach timeline, penalties, readiness note)."""

from __future__ import annotations

import io
import logging
import re
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pdfplumber
import pytest

from app.dpdpa.framework import (
    DPDPA_FIDUCIARY_OBLIGATIONS_COMMENCE,
    DPDPA_FRAMEWORK,
    DPDPA_READINESS_NOTE,
    get_all_requirements,
)
from tests.integration.conftest import client, create_test_assessment, db_session  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parents[1]
BEFORE = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
AFTER = datetime(2027, 6, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


def _fixed(now: datetime):
    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz is not None else now.replace(tzinfo=None)

    return _FixedDatetime


def _pdf_text(pdf_bytes: bytes) -> str:
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return re.sub(r"\s+", " ", text)


# Snapshot of main @ dc64829 (requirement id -> (title, criticality)).
MAIN_REQUIREMENTS = {
    "CH2.CONSENT.1": ("Lawful basis for processing with free, specific, informed consent", "critical"),
    "CH2.CONSENT.2": ("Itemised consent for multiple purposes", "high"),
    "CH2.CONSENT.3": ("Consent withdrawal mechanism", "critical"),
    "CH2.CONSENT.4": ("Consent Manager registration and interoperability", "medium"),
    "CH2.CONSENT.5": ("Verifiable parental consent for children's data", "critical"),
    "CH2.NOTICE.1": ("Notice at or before collection of personal data", "critical"),
    "CH2.NOTICE.2": ("Notice for previously collected data", "high"),
    "CH2.NOTICE.3": ("Notice contains contact details of DPO or grievance officer", "medium"),
    "CH2.PURPOSE.1": ("Processing only for stated purpose", "critical"),
    "CH2.PURPOSE.2": ("Legitimate uses without consent properly identified", "high"),
    "CH2.MINIMIZE.1": ("Collection limited to what is necessary", "high"),
    "CH2.MINIMIZE.2": ("Data retention limited to purpose fulfilment", "high"),
    "CH2.MINIMIZE.3": ("Retention schedule and deletion procedures", "medium"),
    "CH2.ACCURACY.1": ("Reasonable efforts to ensure data accuracy", "medium"),
    "CH2.SECURITY.1": ("Reasonable security safeguards implemented", "critical"),
    "CH2.SECURITY.2": ("Encryption and access controls", "critical"),
    "CH2.SECURITY.3": ("Data Processor contractual safeguards", "high"),
    "CH3.ACCESS.1": ("Summary of personal data and processing activities", "high"),
    "CH3.CORRECT.1": ("Mechanism for correction and completion of data", "high"),
    "CH3.CORRECT.2": ("Mechanism for erasure of personal data", "high"),
    "CH3.GRIEVANCE.1": ("Grievance redressal mechanism available", "critical"),
    "CH3.GRIEVANCE.2": ("Timely response to grievances", "high"),
    "CH3.NOMINATE.1": ("Nomination mechanism for death or incapacity", "medium"),
    "CH4.CHILD.1": ("No tracking or behavioural monitoring of children", "critical"),
    "CH4.CHILD.2": ("No processing detrimental to child's well-being", "critical"),
    "CH4.CHILD.3": ("Age verification mechanism", "high"),
    "CH4.SDF.1": ("Data Protection Officer (DPO) appointed", "critical"),
    "CH4.SDF.2": ("Independent Data Auditor appointed", "high"),
    "CH4.SDF.3": ("Data Protection Impact Assessment (DPIA) conducted", "high"),
    "CH4.SDF.4": ("Periodic audit completed", "high"),
    "CM.RECORDS.1": ("Consent records maintained", "high"),
    "CM.RECORDS.2": ("Consent refresh and re-validation process", "medium"),
    "CM.GRANULAR.1": ("Granular consent options available", "high"),
    "CM.GRANULAR.2": ("No consent bundling with service access", "critical"),
    "CB.TRANSFER.1": ("Data transfers only to non-restricted jurisdictions", "critical"),
    "CB.TRANSFER.2": ("Contractual safeguards for cross-border transfers", "high"),
    "CB.TRANSFER.3": ("Data localisation where required", "high"),
    "BN.NOTIFY.1": ("Breach notification to Data Protection Board", "critical"),
    "BN.NOTIFY.2": ("Breach notification to affected Data Principals", "critical"),
    "BN.NOTIFY.3": ("Incident response plan documented", "high"),
    "BN.NOTIFY.4": ("Breach register maintained", "medium"),
}
TITLE_CHANGES = {
    "CH2.ACCURACY.1": "Data accuracy ensured for decision-making and onward disclosure",
    "CH2.NOTICE.1": "Notice accompanying the consent request",
}
MAIN_CHAPTER_WEIGHTS = {
    "chapter_2": 0.3, "chapter_3": 0.2, "chapter_4": 0.2,
    "consent_management": 0.1, "cross_border": 0.1, "breach_notification": 0.1,
}
MAIN_SECTION_WEIGHTS = {
    "chapter_2.consent": 0.25, "chapter_2.notice": 0.15, "chapter_2.purpose_limitation": 0.15,
    "chapter_2.data_minimization": 0.15, "chapter_2.accuracy": 0.1, "chapter_2.security": 0.2,
    "chapter_3.right_to_access": 0.25, "chapter_3.right_to_correction": 0.25,
    "chapter_3.grievance_redressal": 0.3, "chapter_3.nomination": 0.2,
    "chapter_4.children_data": 0.4, "chapter_4.significant_data_fiduciary": 0.6,
    "consent_management.consent_records": 0.5, "consent_management.granular_consent": 0.5,
    "cross_border.transfer_controls": 1.0, "breach_notification.incident_management": 1.0,
}


def test_1_section_refs_corrected():
    expected = {
        "CH2.CONSENT.1": "Section 6(1), 6(3)",
        "CH2.CONSENT.2": "Section 6(1)",
        "CM.GRANULAR.1": "Section 6(1)",
        "CH2.CONSENT.3": "Section 6(4), 6(6)",
        "CH2.NOTICE.3": "Section 5(1), 8(9); DPDP Rules 2025 r.3, r.9",
        "CH2.MINIMIZE.1": "Section 6(1)",
        "CH2.SECURITY.1": "Section 8(5)",
        "CH3.CORRECT.2": "Section 12(3)",
        "CH4.CHILD.1": "Section 9(3)",
        "CH4.CHILD.2": "Section 9(2)",
        "CH4.SDF.4": "Section 10(2)(c)(ii)",
        "BN.NOTIFY.1": "Section 8(6); DPDP Rules 2025 r.7(2)",
        "BN.NOTIFY.2": "Section 8(6); DPDP Rules 2025 r.7(1)",
        "BN.NOTIFY.4": "Section 8(6)",
    }
    refs = {req["id"]: req["section_ref"] for req in get_all_requirements()}
    for req_id, ref in expected.items():
        assert refs[req_id] == ref, req_id


def test_2_no_72_hours_attributed_to_section_8_6():
    offenders = []
    for path in (REPO_ROOT / "app").rglob("*"):
        if path.suffix not in {".py", ".html"}:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for sentence in re.split(r"(?<=[.;])\s+", line):
                if "72" in sentence and "8(6)" in sentence:
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {sentence.strip()}")
    assert offenders == []


def test_3_penalty_map_matches_schedule():
    from app.routers.web import _PENALTY_MAP, _compute_business_impact

    penalties = dict(_PENALTY_MAP)
    assert penalties["BN.NOTIFY"] == 200
    assert penalties["CH4.SDF"] == 150
    assert penalties["CH2.SECURITY"] == 250
    assert penalties["CH4.CHILD"] == 200

    def impact(req_id):
        item = SimpleNamespace(
            requirement_id=req_id, framework_id="dpdpa",
            compliance_status="non_compliant", risk_level="high",
        )
        return _compute_business_impact([item])["max_penalty_cr"]

    assert impact("BN.NOTIFY.1") == 200
    assert impact("CH4.SDF.2") == 150
    assert impact("CH2.CONSENT.5") == 200  # s.9 children, Schedule item 3
    assert impact("CH2.CONSENT.1") == 50


def _board_pdf(frameworks, now):
    from app.utils import pdf_export

    report = SimpleNamespace(overall_score=0, chapter_scores="{}", executive_summary="Smoke.")
    with patch("app.utils.pdf_export.datetime", _fixed(now)):
        return _pdf_text(pdf_export.generate_pdf(report, [], "Example", selected_frameworks=frameworks))


def test_4_readiness_note_in_board_pdf_is_gated():
    note = re.sub(r"\s+", " ", DPDPA_READINESS_NOTE)
    assert note in _board_pdf(["dpdpa"], BEFORE)
    assert note in _board_pdf(["dpdpa", "iso27001"], BEFORE)
    assert note not in _board_pdf(["iso27001"], BEFORE)
    assert note not in _board_pdf(["dpdpa"], AFTER)
    assert BEFORE.date() < DPDPA_FIDUCIARY_OBLIGATIONS_COMMENCE < AFTER.date()
    assert DPDPA_FIDUCIARY_OBLIGATIONS_COMMENCE == date(2027, 5, 13)


def test_4b_readiness_note_in_integrated_pdf_is_gated():
    from app.frameworks.registry import FrameworkRegistry
    from app.utils import pdf_export

    def render(framework_ids, now):
        section = SimpleNamespace(
            assessment_id="a1", label="Baseline",
            created_at=BEFORE, analysed_at=BEFORE,
            frameworks=[(FrameworkRegistry.get(fid).name, "v1") for fid in framework_ids],
            scope_label="No scope restriction recorded", scores=[],
            findings=SimpleNamespace(findings=[], omitted_count=0),
        )
        data = SimpleNamespace(engagement_name="E", client_name="C", sections=[section], excluded=[])
        with patch("app.utils.pdf_export.datetime", _fixed(now)):
            return _pdf_text(pdf_export.generate_integrated_pdf(data))

    note = re.sub(r"\s+", " ", DPDPA_READINESS_NOTE)
    assert note in render(["dpdpa"], BEFORE)
    assert note not in render(["iso27001"], BEFORE)
    assert note not in render(["dpdpa"], AFTER)


def _summary(client, db_session, frameworks, now):  # noqa: F811
    from app.models.assessment import Assessment
    from tests.integration.test_report import _seed_report

    assessment_id = create_test_assessment(client, selected_frameworks=frameworks)
    assessment = db_session.get(Assessment, assessment_id)
    assessment.status = "completed"
    db_session.commit()
    _seed_report(db_session, assessment_id)
    with patch("app.routers.web.datetime", _fixed(now)):
        response = client.get(f"/assessments/{assessment_id}/report-summary")
    assert response.status_code == 200
    return response.text


def test_5_readiness_note_on_web_summary_is_gated(client, db_session):  # noqa: F811
    assert "data-dpdpa-readiness-note" in _summary(client, db_session, "dpdpa", BEFORE)
    assert "data-dpdpa-readiness-note" not in _summary(client, db_session, "iso27001", BEFORE)
    assert "data-dpdpa-readiness-note" not in _summary(client, db_session, "dpdpa", AFTER)


def test_5b_penalty_copy_does_not_claim_per_incident():
    template = (REPO_ROOT / "app/templates/partials/report_summary.html").read_text(encoding="utf-8")
    assert "per incident" not in template.lower()
    assert "per-incident" not in template.lower()


def test_6_ids_titles_criticality_weights_unchanged():
    current = {req["id"]: (req["title"], req["criticality"]) for req in get_all_requirements()}
    assert set(current) == set(MAIN_REQUIREMENTS)
    for req_id, (title, criticality) in MAIN_REQUIREMENTS.items():
        assert current[req_id][1] == criticality, req_id
        assert current[req_id][0] == TITLE_CHANGES.get(req_id, title), req_id
    assert {k: v["weight"] for k, v in DPDPA_FRAMEWORK.items()} == MAIN_CHAPTER_WEIGHTS
    assert {
        f"{ck}.{sk}": sec["weight"]
        for ck, ch in DPDPA_FRAMEWORK.items()
        for sk, sec in ch["sections"].items()
    } == MAIN_SECTION_WEIGHTS


def test_7_red_flag_keys_unchanged():
    from app.frameworks.prompts import red_flag_key
    from app.frameworks.registry import FrameworkRegistry

    keys = [red_flag_key(p) for p in FrameworkRegistry.get("dpdpa").red_flag_patterns]
    assert keys == [
        "gdpr_copy_paste_language", "template_artifacts", "ccpa_artifacts",
        "buried_consent", "missing_dpdpa_timelines", "policy_without_implementation_evidence",
    ]
