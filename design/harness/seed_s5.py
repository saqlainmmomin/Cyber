"""Seed deterministic S5 assessment-workflow specimens into throwaway SQLite databases.

The harness reuses S4's builders and frozen clock. States that represent an in-flight
browser operation are recorded as preview states in the output rather than pretending that
the database completed work it cannot perform by itself.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.models  # noqa: F401 - register every model before create_all()
from app.database import Base
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.models.firm_settings import FirmSettings
from app.models.assessment import Assessment, AssessmentDocument
from app.models.engagement import Engagement
from design.harness.seed_s4 import (
    FROZEN_NOW,
    _assessment,
    _client,
    _engagement,
    _report_basis_event,
    _seed_evidence,
    _seed_review_stage,
    _time,
)


SCREEN_STATES = {
    "b3-hub": ("default", "empty", "evidence", "questionnaire", "report", "loading", "error", "archived", "prefill"),
    "b3-scope": ("default", "error", "saving", "edit"),
    "b3-scope-complete": ("default", "iso", "loading", "error"),
    "b3-questionnaire": ("prefill", "prefilling", "default", "context", "screened", "noscreen", "error", "running", "complete", "findings"),
    "b3-screening-form": ("default", "loading", "error", "complete", "screened"),
    "b3-context-complete": ("default", "generating", "error"),
    "b3-question-step": ("org", "data", "data-yes", "last", "saving", "error"),
    "b3-followups": ("loaded", "loading", "error", "none"),
    "b3-sections": ("default", "saved", "loading", "empty", "error"),
    "b3-section-questions": ("default", "errors", "saved", "loading"),
    "b4-desk_review": ("ready", "running", "findings", "rerun", "error"),
}


def _register_frameworks() -> None:
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
    from app.frameworks.definitions.gdpr import GDPR_DEFINITION
    from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
    from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION
    from app.frameworks.registry import FrameworkRegistry

    for framework in (
        DPDPA_DEFINITION,
        ISO27001_DEFINITION,
        GDPR_DEFINITION,
        HIPAA_DEFINITION,
        NIST_CSF_DEFINITION,
        PCI_DSS_DEFINITION,
    ):
        FrameworkRegistry.register(framework)


def _base_data(
    db: Session,
    *,
    iso_only: bool = False,
    dpdpa_only: bool = False,
    include_assessment: bool = True,
) -> dict:
    clients = [
        _client("client-meridian", "Meridian Ledger Technologies", "Fintech", "large"),
        _client("client-loomwire", "Loomwire Labs", "IT services", "medium"),
        _client("client-kestrel", "Kestrel Advisory", "Professional services", "small"),
    ]
    engagements = [
        _engagement("eng-meridian-s5", clients[0].id, "FY2026 privacy readiness"),
        _engagement("eng-loomwire-s5", clients[1].id, "NIST baseline"),
        _engagement("eng-kestrel-s5", clients[2].id, "Advisory controls review"),
    ]
    frameworks = ("iso27001",) if iso_only else ("dpdpa",) if dpdpa_only else ("dpdpa", "iso27001")
    assessments = []
    if include_assessment:
        assessments.append(
            _assessment(
                "assessment-s5",
                engagements[0].id,
                clients[0].name,
                "Head office",
                frameworks,
            )
        )
    db.add_all([*clients, *engagements, *assessments])
    db.flush()
    return {"clients": clients, "engagements": engagements, "assessments": assessments}


def _scope(assessment: Assessment) -> None:
    assessment.scope_answers = json.dumps({})
    assessment.updated_at = _time(-2)


def _context(assessment: Assessment) -> None:
    assessment.context_answers = json.dumps({"organisation_type": "technology", "data_volume": "medium"})
    assessment.context_profile = json.dumps({"profile": "technology", "risk_band": "medium"})


def _seed_documents(
    db: Session,
    engagement: Engagement,
    assessment: Assessment,
    count: int,
    prefix: str,
    uploaded_start: int = -30,
    filenames: tuple[str, ...] | None = None,
) -> None:
    """Seed both S4 evidence rows and the legacy documents consumed by analysis_documents()."""
    _seed_evidence(db, engagement, assessment, count, prefix)
    for index in range(count):
        document_id = f"{prefix}-legacy-{index:03d}"
        db.add(
            AssessmentDocument(
                id=document_id,
                assessment_id=assessment.id,
                filename=filenames[index] if filenames else f"policy-{index + 1}.pdf",
                file_path=f"evidence/{engagement.id}/{document_id}.pdf",
                file_type="pdf",
                document_category="policy",
                extracted_text=(
                    "Access rights are reviewed quarterly by the system owner. "
                    "Evidence is retained by the control owner."
                ),
                uploaded_at=_time(uploaded_start + index),
            )
        )


def _seed_questionnaire_responses(db: Session, assessment: Assessment, *, complete: bool) -> None:
    from app.models.questionnaire import QuestionnaireResponse
    from app.services.question_engine import build_adaptive_questionnaire

    questionnaire = build_adaptive_questionnaire(assessment.id, db)
    selected_questions = []
    if complete:
        selected_questions = [
            question
            for section in questionnaire.get("sections", [])
            for question in section.get("questions", [])
            if question.get("status") != "skipped"
        ]
    else:
        # Keep the list visibly in progress while leaving document pre-fills
        # awaiting confirmation. Each section gets its own deterministic count.
        targets = (4, 0, 3, 1, 0, 2)
        for index, section in enumerate(questionnaire.get("sections", [])):
            candidates = [
                question
                for question in section.get("questions", [])
                if question.get("status") not in {"skipped", "pre_filled"}
            ]
            selected_questions.extend(candidates[: targets[index] if index < len(targets) else 0])
    for question in selected_questions:
        db.add(
            QuestionnaireResponse(
                assessment_id=assessment.id,
                question_id=question["id"],
                answer="fully_implemented",
                submitted_at=_time(-4),
            )
        )
    db.flush()


def _freeze_runtime_timestamps(db: Session, assessment: Assessment) -> None:
    """Normalize defaults from builders that use the process clock."""
    from app.models.audit_event import AuditEvent
    from app.models.questionnaire import QuestionnaireResponse

    for response in db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment.id
    ):
        response.submitted_at = _time(-4)
    for event in db.query(AuditEvent).filter(
        AuditEvent.action == "assessment.released",
        AuditEvent.entity_id == assessment.id,
    ):
        event.created_at = FROZEN_NOW


def _desk_summary(
    db: Session,
    assessment: Assessment,
    *,
    status: str,
    findings: bool = False,
    completed_at=None,
    document_count: int = 6,
) -> None:
    from app.frameworks.registry import FrameworkRegistry

    controls = [
        control.id
        for framework_id in assessment.frameworks
        for control in FrameworkRegistry.get_all_controls(framework_id)[:2]
    ]
    dpdpa_controls = [control.id for control in FrameworkRegistry.get_all_controls("dpdpa")[:9]]
    coverage_ids = list(dict.fromkeys([*dpdpa_controls[:6], *controls]))
    summary = DeskReviewSummary(
        assessment_id=assessment.id,
        document_catalog=json.dumps([{"id": f"evidence-s5-{i:03d}", "filename": f"policy-{i + 1}.pdf"} for i in range(document_count)]),
        coverage_summary=json.dumps({control_id: "partial" for control_id in coverage_ids}),
        raw_ai_response="{}",
        status=status,
        error_message="The document analysis service timed out." if status == "error" else None,
        started_at=_time(-3),
        completed_at=completed_at or (_time(-1) if status == "completed" else None),
    )
    db.add(summary)
    if not findings:
        return
    db.flush()
    findings = [
            DeskReviewFinding(
                assessment_id=assessment.id,
                finding_type="evidence",
                requirement_id=control_id,
                document_id=None,
                content="The policy describes the control and its operating owner.",
                severity="medium",
                source_quote="Access rights are reviewed quarterly by the system owner.",
                source_location=f"Policy {index + 1}, page 4",
                framework_id="dpdpa",
                created_at=_time(-1),
            )
            for index, control_id in enumerate(dpdpa_controls[:6])
        ]
    findings.extend(
        [
            DeskReviewFinding(
                assessment_id=assessment.id,
                finding_type="absence",
                requirement_id=control_id,
                document_id=None,
                content="No retained evidence of the latest access review was found.",
                severity="high",
                source_quote=None,
                source_location=None,
                framework_id="dpdpa",
                created_at=_time(-1),
            )
            for control_id in dpdpa_controls[6:]
        ]
    )
    findings.extend(
        [
            DeskReviewFinding(
                assessment_id=assessment.id,
                finding_type="signal",
                requirement_id=None,
                document_id=None,
                content="The policy is current, but operating evidence is incomplete.",
                severity="medium",
                source_quote="Evidence is retained by the control owner.",
                source_location="Policy 2026, page 5",
                framework_id="dpdpa",
                flag_type="evidence_gap",
                signal_group_id="s5-signal-1",
                created_at=_time(-1),
            ),
        ]
    )
    db.add_all(findings)


# s5-prefill: b4 desk-review results (mockup b4-desk_review.html, findings state).
B4_DOCUMENTS = (
    "Breach response procedure.docx",
    "Consent form, mobile app.pdf",
    "Retention schedule.pdf",
    "Privacy notice.pdf",
    "Data flow diagram, payments.png",
    "Information security policy.pdf",
)
B4_ERROR_MESSAGE = "The analysis service did not respond within 10 minutes. Your documents are unchanged."


def _b4_doc(index: int) -> str:
    return f"evidence-s5-legacy-{index:03d}"


def _b4_desk_review(db: Session, assessment: Assessment, state: str) -> None:
    """Seed the b4 results page: 34 findings (18 evidence, 9 gaps, 7 red flags), ISO failed."""
    from app.frameworks.registry import FrameworkRegistry

    status = {"running": "analyzing", "error": "error"}.get(state, "completed")
    dpdpa = [control.id for control in FrameworkRegistry.get_all_controls("dpdpa")]
    levels = ["adequate"] * 14 + ["partial"] * 9 + ["absent"] * 6 + ["not_covered"] * 3
    summary = DeskReviewSummary(
        assessment_id=assessment.id,
        document_catalog=json.dumps([{"id": _b4_doc(i), "filename": name} for i, name in enumerate(B4_DOCUMENTS)]),
        coverage_summary=json.dumps(dict(zip(dpdpa, levels))) if status == "completed" else None,
        raw_ai_response=json.dumps({
            "schema_version": 2,
            "frameworks": {"dpdpa": {"status": "completed"}, "iso27001": {"status": "error"}},
        }) if status == "completed" else "{}",
        status=status,
        error_message=B4_ERROR_MESSAGE if status == "error" else None,
        started_at=_time(-3),
        completed_at=_time(-1) if status == "completed" else None,
    )
    db.add(summary)
    if status != "completed":
        return
    db.flush()

    def finding(kind: str, **values) -> DeskReviewFinding:
        return DeskReviewFinding(
            assessment_id=assessment.id, finding_type=kind, framework_id="dpdpa", created_at=_time(-1), **values,
        )

    signals = [
        ("Breach notice promises customers 72 hours and never mentions the Data Protection Board", "critical", 0, "Page 3",
         "We will notify affected customers within 72 hours of confirming a personal data breach.", "BN.NOTIFY.1"),
        ("Marketing consent is pre-selected on the sign-up form", "high", 1, "Page 1",
         "[x] I agree to receive offers and updates from Meridian Ledger partners.", "CH2.CONSENT.1"),
        ("KYC records are kept with no end date", "medium", 2, "Page 2",
         "KYC records are retained for the life of the account and thereafter until further notice.", "CH2.MINIMIZE.2"),
        ("The privacy notice is available in English only", "medium", 3, "Page 1",
         "This notice is published in English.", "CH2.CONSENT.1"),
        ("Withdrawal of consent needs a written request", "medium", 1, "Page 2",
         "To withdraw consent, write to the Data Protection Officer.", "CH2.CONSENT.3"),
        ("Processors are not bound to delete data at the end of the contract", "low", 5, "Page 6",
         "The vendor may retain copies of customer data for its records.", "CH2.SECURITY.3"),
        ("Grievances have no stated response time", "low", 3, "Page 4",
         "We will look into every complaint we receive.", "CH3.GRIEVANCE.2"),
    ]
    rows = [
        finding("signal", content=content, severity=severity, document_id=_b4_doc(doc), source_location=page,
                source_quote=quote, requirement_id=requirement, flag_type="evidence_gap",
                signal_group_id=f"s5-b4-signal-{index}")
        for index, (content, severity, doc, page, quote, requirement) in enumerate(signals)
    ]
    absences = [
        ("CH2.CONSENT.5", "No process for verifiable parental consent for users under 18", "high"),
        ("CH3.GRIEVANCE.2", "The privacy notice names no response time", "medium"),
        ("CB.TRANSFER.1", "The hosting agreement does not list processing locations", "medium"),
        ("CH2.CONSENT.4", "No Consent Manager is registered or named", "medium"),
        ("CH4.SDF.3", "No data protection impact assessment is on file", "medium"),
        ("CH4.SDF.4", "No periodic audit report is on file", "low"),
        ("CM.RECORDS.1", "Consent records are not retained after withdrawal", "low"),
        ("BN.NOTIFY.4", "No breach register is kept", "low"),
        ("CH3.NOMINATE.1", "No nomination mechanism is described", "low"),
    ]
    rows += [finding("absence", requirement_id=requirement, content=content, severity=severity)
             for requirement, content, severity in absences]
    evidence = [
        ("CH3.GRIEVANCE.1", 3, "Page 4", "Complaints can be sent to our Data Protection Officer, who acknowledges every complaint within 48 hours."),
        ("CB.TRANSFER.3", 4, "Whole image", "Customer records flow from the app to the payments service hosted in ap-south-1."),
    ] + [
        (requirement, index % len(B4_DOCUMENTS), f"Page {index + 2}", "The policy describes the control and its operating owner.")
        for index, requirement in enumerate(dpdpa[:16])
    ]
    rows += [finding("evidence", requirement_id=requirement, document_id=_b4_doc(doc), source_location=page,
                     source_quote=quote, content=quote, severity="low")
             for requirement, doc, page, quote in evidence]
    db.add_all(rows)


def _apply_state(db: Session, screen: str, state: str, assessment: Assessment, engagement: Engagement) -> dict:
    data_state = (
        "preview-state"
        if state in {"loading", "error", "running", "saving", "generating", "prefilling", "rerun", "errors"}
        else "database"
    )
    if screen == "b3-hub" and state == "empty":
        data_state = "preview-state"
        return {"assessment_id": assessment.id, "data_state": data_state}

    if screen == "b3-hub" and state in {"default", "archived", "loading", "error"}:
        # The mockup draws archived and the transient loading/error panel states over the
        # review stage (three of six approved); loading/error are applied with ?state=.
        _seed_review_stage(db, assessment, approved=3, pending=3)

    if screen == "b3-hub" and state == "archived":
        # Read-only because its engagement is archived (the banner copy); the assessment
        # itself stays live so its review period still shows in the meta line.
        engagement.status = "archived"
    if screen == "b3-hub" and state in {"report"}:
        # Every conclusion approved and the report not yet released: "Release report".
        _seed_review_stage(db, assessment, approved=6, pending=0)
    elif screen == "b3-hub" and state == "questionnaire":
        _scope(assessment)
        _context(assessment)
        _seed_questionnaire_responses(db, assessment, complete=False)
    elif screen == "b3-hub" and state == "evidence":
        _scope(assessment)
    elif screen == "b3-hub" and state == "prefill":
        _scope(assessment)
        _seed_documents(db, engagement, assessment, 5, "evidence-s5")
    elif screen == "b3-scope":
        if state in {"edit", "saving"}:
            _scope(assessment)
        if state == "error":
            assessment.status = "error"
    elif screen == "b3-scope-complete":
        _scope(assessment)
        if state == "iso":
            assessment.selected_frameworks = json.dumps(["iso27001"])
    elif screen == "b3-questionnaire":
        _scope(assessment)
        _context(assessment)
        if state in {"prefill", "prefilling", "findings", "default", "context", "screened", "complete", "running", "error", "noscreen"}:
            _seed_documents(db, engagement, assessment, 5, "evidence-s5")
        if state in {"default", "context", "screened", "complete", "running", "error", "noscreen"}:
            assessment.desk_review_status = "completed"
            _desk_summary(
                db,
                assessment,
                status="completed",
                findings=True,
                document_count=5,
            )
            _seed_questionnaire_responses(db, assessment, complete=state == "complete")
        if state == "prefilling":
            assessment.desk_review_status = "analyzing"
            _desk_summary(db, assessment, status="analyzing")
        elif state == "findings":
            assessment.desk_review_status = "completed"
            _desk_summary(db, assessment, status="completed", findings=True, document_count=5)
        elif state == "error":
            assessment.status = "error"
        elif state == "running":
            _seed_review_stage(db, assessment, approved=0, pending=0)
            assessment.status = "analyzing"
        elif state in {"complete", "screened"}:
            _seed_review_stage(db, assessment, approved=2, pending=2)
        elif state == "noscreen":
            assessment.selected_frameworks = json.dumps(["iso27001"])
            assessment.screening_status = None
        elif state == "context":
            assessment.context_answers = None
            assessment.context_profile = None
    elif screen == "b3-screening-form":
        _scope(assessment)
        _context(assessment)
        if state in {"complete", "screened"}:
            assessment.screening_status = "completed"
            assessment.screening_results = json.dumps({"domain-access": {"status": "fully_implemented", "confidence": "high"}})
        if state == "error":
            assessment.status = "error"
        if state == "loading":
            data_state = "preview-state"
    elif screen == "b3-context-complete":
        _scope(assessment)
        _context(assessment)
        if state == "error":
            assessment.status = "error"
        if state == "generating":
            data_state = "preview-state"
    elif screen == "b3-question-step":
        _scope(assessment)
        if state in {"data", "data-yes", "last", "saving"}:
            _context(assessment)
        if state in {"saving", "error"}:
            data_state = "preview-state"
    elif screen == "b3-followups":
        _scope(assessment)
        _context(assessment)
        if state in {"loading", "error"}:
            data_state = "preview-state"
    elif screen == "b3-sections":
        _scope(assessment)
        _context(assessment)
        if state in {"loading", "error", "empty"}:
            data_state = "preview-state"
    elif screen == "b3-section-questions":
        _scope(assessment)
        _context(assessment)
        if state in {"errors", "saved", "loading"}:
            data_state = "preview-state"
    elif screen == "b4-desk_review":
        _scope(assessment)
        _context(assessment)
        _seed_documents(db, engagement, assessment, 6, "evidence-s5", filenames=B4_DOCUMENTS)
        assessment.desk_review_status = {"ready": None, "running": "analyzing", "error": "error"}.get(state, "completed")
        if state != "ready":
            _b4_desk_review(db, assessment, state)
        data_state = "preview-state" if state in {"running", "rerun"} else "database"
    return {"assessment_id": assessment.id, "data_state": data_state}


def seed_s5(output: str | Path, *, screen: str = "b3-hub", state: str = "default") -> dict:
    """Create one deterministic database for one S5 screen state and stamp Alembic head."""
    _register_frameworks()
    if screen not in SCREEN_STATES:
        raise ValueError(f"unknown screen {screen!r}")
    if state not in SCREEN_STATES[screen]:
        raise ValueError(f"unknown state {state!r} for {screen}")

    output_path = Path(output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    engine = create_engine(f"sqlite:///{output_path}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(FirmSettings(id=1, archived_retention_years=7, accent_theme="midnight", updated_at=FROZEN_NOW))
        data = _base_data(
            db,
            iso_only=(screen == "b3-scope-complete" and state == "iso")
            or (screen == "b3-questionnaire" and state == "noscreen"),
            dpdpa_only=(screen in {"b3-questionnaire", "b3-screening-form"} and state != "noscreen"),
            include_assessment=True,
        )
        assessment = data["assessments"][0] if data["assessments"] else None
        result = (
            _apply_state(db, screen, state, assessment, data["engagements"][0])
            if assessment is not None
            else {"assessment_id": None, "data_state": "preview-state"}
        )
        if assessment is not None:
            db.add(_report_basis_event(assessment))
            _freeze_runtime_timestamps(db, assessment)
        db.flush()
        db.commit()
    engine.dispose()

    alembic_config = Config(str(REPO_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", f"sqlite:///{output_path}")
    command.stamp(alembic_config, "head")
    return {
        "output": str(output_path),
        "screen": screen,
        "state": state,
        "assessment_id": result["assessment_id"],
        "data_state": result["data_state"],
        "frozen_now": FROZEN_NOW.isoformat(),
        "alembic": "head",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="/tmp/yozora-s5.sqlite3")
    parser.add_argument("--screen", choices=tuple(SCREEN_STATES), default="b3-hub")
    parser.add_argument("--state", default="default")
    args = parser.parse_args()
    print(json.dumps(seed_s5(args.output, screen=args.screen, state=args.state), sort_keys=True))


if __name__ == "__main__":
    main()
