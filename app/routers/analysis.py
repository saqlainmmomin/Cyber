import logging
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dpdpa.framework import get_all_requirements
from app.dpdpa.questionnaire import build_questionnaire
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.initiative import Initiative
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.services import analysis_pipeline
from app.services.auto_answer import confirmed_response_clause
from app.services.claude_analyzer import run_gap_analysis, run_multi_framework_analysis
from app.services.conclusion_review import reviewer_actor
from app.services.desk_review_findings import load_desk_review_data
from app.services.evidence import analysis_documents
from app.services.scoring import (
    compute_framework_scores,
    failed_framework_scores,
    generate_initiatives,
    generate_multi_framework_initiatives,
    namespaced_domain_scores,
)
from app.schemas.analysis import CompletionOverride

router = APIRouter(prefix="/api/assessments/{assessment_id}", tags=["analysis"])
logger = logging.getLogger(__name__)

COMPLETION_THRESHOLD = 0.8
COMPLETION_GATE_MESSAGE = (
    "Questionnaire is incomplete: {answered} of {expected} in-scope core questions answered ({pct}%). "
    "Answer at least 80% of the in-scope questionnaire, or run analysis with a recorded consultant override. "
    "Pre-filled answers count only after a consultant confirms them."
)
COMPLETION_OVERRIDE_REASONS = {
    "document_led": "Documents are the primary evidence for this assessment",
    "client_answers_pending": "Client answers are pending and an interim AI proposal is needed",
    "scope_under_review": "Scope is still being confirmed with the client",
}
COMPLETION_OVERRIDE_EVENT = "analysis.completion_override"
COMPLETION_OVERRIDE_SCHEMA_VERSION = 1


class CompletionGateRefused(HTTPException):
    def __init__(self, *, answered: int, expected: int):
        self.answered = answered
        self.expected = expected
        pct = round((answered / expected) * 100) if expected else 0
        super().__init__(
            status_code=400,
            detail=COMPLETION_GATE_MESSAGE.format(
                answered=answered,
                expected=expected,
                pct=pct,
            ),
        )


def _applicable_requirement_ids(
    raw: str | None,
    *,
    assessment_id: str | None = None,
) -> set[str] | None:
    """None = no scope recorded (every requirement applies)."""
    if raw is None or raw == "":
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        logger.warning(
            "Invalid applicable_requirements for assessment gate",
            extra={"assessment_id": assessment_id},
        )
        return None
    if not isinstance(parsed, list):
        logger.warning(
            "Invalid applicable_requirements for assessment gate",
            extra={"assessment_id": assessment_id},
        )
        return None
    return {str(value) for value in parsed}

# Build a requirement title lookup once
_REQ_TITLES = {r["id"]: r["title"] for r in get_all_requirements()}
_REQ_CHAPTERS = {r["id"]: r["chapter"] for r in get_all_requirements()}


@router.post("/analyze")
def trigger_analysis(
    assessment_id: str,
    db: Session = Depends(get_db),
    override: CompletionOverride | None = None,
):
    """Trigger DPDPA gap analysis using Claude."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    # Load context profile if available
    context_profile = None
    if assessment.context_profile:
        try:
            context_profile = json.loads(assessment.context_profile)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in context_profile for assessment %s", assessment_id)

    # Gather questionnaire responses
    responses_db = (
        db.query(QuestionnaireResponse)
        .filter(
            QuestionnaireResponse.assessment_id == assessment_id,
            confirmed_response_clause(),
        )
        .all()
    )
    responses = [
        {
            "question_id": r.question_id,
            "answer": r.answer,
            "notes": r.notes,
            "na_reason": r.na_reason,
            "confidence": r.confidence,
        }
        for r in responses_db
    ]

    # Gather documents
    documents = [
        {"filename": d["filename"], "category": d["category"], "text": d["text"]}
        for d in analysis_documents(db, assessment_id)
    ]

    _selected_fw = ["dpdpa"]
    if assessment.selected_frameworks:
        try:
            _selected_fw = json.loads(assessment.selected_frameworks)
        except json.JSONDecodeError:
            pass

    _is_multi = len(_selected_fw) > 1 or _selected_fw != ["dpdpa"]

    if _is_multi:
        from app.frameworks.questionnaire_builder import (
            build_multi_questionnaire,
            compute_excluded_controls,
        )
        excluded = compute_excluded_controls(
            _selected_fw,
            assessment.applicable_requirements,
        )
        _multi_qs = build_multi_questionnaire(
            _selected_fw,
            excluded_controls=excluded,
            context_profile=context_profile,
        )
        expected_question_ids = {
            q["cluster_id"] for q in _multi_qs
            if not q.get("cluster_id", "").startswith("IND.")
        }
    else:
        expected_question_ids = {
            q["id"] for q in build_questionnaire(context_profile=context_profile)
            if not q["id"].startswith(("IND.", "FU."))
        }
        applicable_ids = _applicable_requirement_ids(
            assessment.applicable_requirements,
            assessment_id=assessment_id,
        )
        if applicable_ids is not None:
            expected_question_ids &= applicable_ids
    answered_question_ids = {
        r.question_id
        for r in responses_db
        if r.question_id in expected_question_ids and (r.answer or "").strip()
    }
    total_expected = len(expected_question_ids)
    completion_ratio = (len(answered_question_ids) / total_expected) if total_expected else 0.0
    has_documents = bool(documents)

    gate_blocked = bool(total_expected) and completion_ratio < COMPLETION_THRESHOLD
    if gate_blocked and override is None:
        raise CompletionGateRefused(
            answered=len(answered_question_ids),
            expected=total_expected,
        )
    if gate_blocked and override is not None and override.reason not in COMPLETION_OVERRIDE_REASONS:
        raise HTTPException(400, "Choose a valid override reason.")

    if not responses and not documents:
        raise HTTPException(
            400,
            "Submit questionnaire responses or upload documents before running analysis.",
        )

    if gate_blocked:
        metadata = {
            "schema_version": COMPLETION_OVERRIDE_SCHEMA_VERSION,
            "reason": override.reason,
            "answered": len(answered_question_ids),
            "expected": total_expected,
            "completion_pct": round(completion_ratio * 100),
            "threshold_pct": 80,
            "framework_ids": list(_selected_fw),
        }
        db.add(
            AuditEvent(
                actor=reviewer_actor(override.reviewer_name),
                action=COMPLETION_OVERRIDE_EVENT,
                entity_type="assessment",
                entity_id=assessment_id,
                metadata_json=json.dumps(metadata, sort_keys=True),
            )
        )
        logger.info(
            "Running analysis with completion override",
            extra={
                "assessment_id": assessment_id,
                "reason": override.reason,
                "answered": len(answered_question_ids),
                "expected": total_expected,
            },
        )

    # Update status
    assessment.status = "analyzing"
    db.commit()

    # Load desk review findings if available
    desk_review_data = load_desk_review_data(db, assessment)

    # Load applicable requirements from scope (if defined)
    applicable_requirements = None
    if assessment.applicable_requirements:
        try:
            applicable_requirements = json.loads(assessment.applicable_requirements)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in applicable_requirements for assessment %s", assessment_id)

    # Determine frameworks for this assessment
    selected_frameworks = ["dpdpa"]
    if assessment.selected_frameworks:
        try:
            selected_frameworks = json.loads(assessment.selected_frameworks)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in selected_frameworks for assessment %s", assessment_id)

    is_multi = len(selected_frameworks) > 1 or selected_frameworks != ["dpdpa"]

    if is_multi:
        return _run_multi_framework_analysis(
            assessment=assessment,
            assessment_id=assessment_id,
            responses=responses,
            documents=documents,
            context_profile=context_profile,
            desk_review_data=desk_review_data,
            applicable_requirements=applicable_requirements,
            selected_frameworks=selected_frameworks,
            has_documents=has_documents,
            db=db,
        )

    # --- Legacy single-framework DPDPA path ---
    run_context = analysis_pipeline.start_runs(
        db,
        assessment_id=assessment_id,
        framework_ids=["dpdpa"],
    )
    db.commit()
    try:
        result = run_gap_analysis(
            company_name=assessment.company_name,
            industry=assessment.industry,
            company_size=assessment.company_size,
            description=assessment.description,
            responses=responses,
            documents=documents,
            context_profile=context_profile,
            desk_review_data=desk_review_data,
            applicable_requirements=applicable_requirements,
        )
    except Exception as e:
        analysis_pipeline.fail_runs(db, run_context, error_type=type(e).__name__)
        assessment.status = "error"
        db.commit()
        raise HTTPException(500, f"Analysis failed: {str(e)}")

    parsed = result["parsed"]
    raw = result["raw"]

    assessments = parsed.get("assessments")
    if not assessments:
        analysis_pipeline.fail_runs(db, run_context, error_type="EmptyAssessment")
        assessment.status = "error"
        db.commit()
        raise HTTPException(500, "Claude returned an empty or malformed assessment. Try running analysis again.")

    try:
        return _persist_single_analysis(
            assessment=assessment,
            assessment_id=assessment_id,
            assessments=assessments,
            parsed=parsed,
            raw=raw,
            responses=responses,
            documents=documents,
            desk_review_data=desk_review_data,
            applicable_requirements=applicable_requirements,
            has_documents=has_documents,
            db=db,
            run_context=run_context,
        )
    except Exception as exc:
        db.rollback()
        analysis_pipeline.fail_runs(db, run_context, error_type=type(exc).__name__)
        assessment.status = "error"
        db.commit()
        raise HTTPException(
            500,
            f"Analysis results could not be saved ({type(exc).__name__}). Run analysis again.",
        ) from exc


def _persist_single_analysis(
    *,
    assessment: Assessment,
    assessment_id: str,
    assessments: list[dict],
    parsed: dict,
    raw: str,
    responses: list[dict],
    documents: list[dict],
    desk_review_data: dict | None,
    applicable_requirements: list[str] | None,
    has_documents: bool,
    db: Session,
    run_context: analysis_pipeline.RunContext,
) -> dict:
    # Server-side scope enforcement: ensure out-of-scope requirements are not_applicable
    if applicable_requirements:
        applicable_set = set(applicable_requirements)
        for a in assessments:
            if a.get("requirement_id") and a["requirement_id"] not in applicable_set:
                a["compliance_status"] = "not_applicable"

    framework_id = assessment.frameworks[0]
    per_fw_scores = {
        framework_id: compute_framework_scores(assessments, framework_id)
    }

    # Preserve existing report data before re-run, then delete
    existing = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )
    _carried_history = None
    if existing:
        old_items = db.query(GapItem).filter(GapItem.report_id == existing.id).all()
        snapshot = {
            "preserved_at": datetime.now().isoformat(),
            "label": "gap_analysis_rerun",
            "report": {
                c.name: getattr(existing, c.name)
                for c in existing.__table__.columns
                if c.name != "legacy_history"
            },
            "items": [
                {c.name: getattr(item, c.name) for c in item.__table__.columns}
                for item in old_items
            ],
        }
        history = []
        if existing.legacy_history:
            try:
                history = json.loads(existing.legacy_history)
                if not isinstance(history, list):
                    history = [history]
            except json.JSONDecodeError:
                history = []
        history.append(snapshot)
        _carried_history = json.dumps(history, default=str)

        db.query(GapItem).filter(GapItem.report_id == existing.id).delete()
        db.query(Initiative).filter(Initiative.report_id == existing.id).delete()
        db.delete(existing)
        db.flush()  # delete before the replacement INSERT: gap_reports.assessment_id is unique

    report = GapReport(
        assessment_id=assessment_id,
        overall_score=0.0,
        chapter_scores=json.dumps(namespaced_domain_scores(per_fw_scores)),
        framework_scores=json.dumps(per_fw_scores),
        executive_summary=parsed.get("executive_summary", ""),
        raw_ai_response=raw,
        legacy_history=_carried_history,
    )
    db.add(report)
    db.flush()
    analysis_pipeline.record_framework_run(
        db,
        run_context,
        framework_id="dpdpa",
        assessments=assessments,
        desk_review_data=desk_review_data,
        gap_report_id=report.id,
    )

    # Build evidence confidence lookup
    _dr_evidence_reqs = set()
    _dr_coverage = {}
    if desk_review_data:
        _dr_coverage = desk_review_data.get("coverage_summary", {})
        for f in desk_review_data.get("findings", []):
            if f.get("type") == "evidence" and f.get("requirement_id"):
                _dr_evidence_reqs.add(f["requirement_id"])

    _response_ids = {r["question_id"] for r in responses}

    def _compute_evidence_confidence(req_id: str) -> str:
        has_dr_evidence = req_id in _dr_evidence_reqs or _dr_coverage.get(req_id) == "adequate"
        has_response = req_id in _response_ids
        if has_dr_evidence and has_response:
            return "strong"
        if has_dr_evidence or (has_response and has_documents):
            return "moderate"
        if has_response:
            return "weak"
        return "weak"

    for a in assessments:
        req_id = a["requirement_id"]
        item = GapItem(
            report_id=report.id,
            requirement_id=req_id,
            framework_id="dpdpa",
            chapter=_REQ_CHAPTERS.get(req_id, "unknown"),
            requirement_title=_REQ_TITLES.get(req_id, req_id),
            compliance_status=a["compliance_status"],
            current_state=a.get("current_state", ""),
            gap_description=a.get("gap_description", ""),
            risk_level=a.get("risk_level", "medium"),
            remediation_action=a.get("remediation_action", ""),
            remediation_priority=a.get("remediation_priority", 3),
            remediation_effort=a.get("remediation_effort", "medium"),
            timeline_weeks=a.get("timeline_weeks", 8),
            maturity_level=a.get("maturity_level"),
            root_cause_category=a.get("root_cause_category"),
            evidence_quote=a.get("evidence_quote"),
            evidence_confidence=_compute_evidence_confidence(req_id),
            review_status="draft",
            needs_review=a.get("needs_review", False),
            ai_compliance_status=a["compliance_status"],
            ai_gap_description=a.get("gap_description", ""),
            ai_risk_level=a.get("risk_level", "medium"),
        )
        db.add(item)

    initiatives_data = generate_initiatives(assessments)
    for init_data in initiatives_data:
        initiative = Initiative(
            report_id=report.id,
            initiative_id=init_data["initiative_id"],
            title=init_data["title"],
            root_cause=init_data["root_cause"],
            root_cause_category=init_data["root_cause_category"],
            requirements_addressed=json.dumps(init_data["requirements_addressed"]),
            combined_effort=init_data["combined_effort"],
            combined_timeline_weeks=init_data["combined_timeline_weeks"],
            priority=init_data["priority"],
            budget_estimate_band=init_data.get("budget_estimate_band"),
            suggested_approach=init_data["suggested_approach"],
        )
        db.add(initiative)

    assessment.status = "completed"
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.id,
        "status": "completed",
        "per_framework_scores": {
            fw_id: scores["overall_score"] for fw_id, scores in per_fw_scores.items()
        },
        "initiatives_generated": len(initiatives_data),
        "message": "Gap analysis completed successfully",
        "analysis_run_ids": dict(run_context.run_ids),
    }


def _run_multi_framework_analysis(
    assessment: Assessment,
    assessment_id: str,
    responses: list[dict],
    documents: list[dict],
    context_profile: dict | None,
    desk_review_data: dict | None,
    applicable_requirements: list[str] | None,
    selected_frameworks: list[str],
    has_documents: bool,
    db: Session,
) -> dict:
    """Run and persist the multi-framework analysis."""
    run_context = analysis_pipeline.start_runs(
        db,
        assessment_id=assessment_id,
        framework_ids=list(selected_frameworks),
    )
    db.commit()
    try:
        result = run_multi_framework_analysis(
            framework_ids=selected_frameworks,
            company_name=assessment.company_name,
            industry=assessment.industry,
            company_size=assessment.company_size,
            description=assessment.description,
            responses=responses,
            documents=documents,
            context_profile=context_profile,
            desk_review_data=desk_review_data,
            applicable_controls=applicable_requirements,
        )
    except Exception as e:
        analysis_pipeline.fail_runs(db, run_context, error_type=type(e).__name__)
        assessment.status = "error"
        db.commit()
        raise HTTPException(500, f"Multi-framework analysis failed: {str(e)}")

    framework_results = result.get("frameworks", {})
    failed_frameworks = [
        framework_id
        for framework_id in selected_frameworks
        if not framework_results.get(framework_id)
        or "error" in framework_results[framework_id]
    ]
    if failed_frameworks:
        analysis_pipeline.fail_runs(
            db,
            run_context,
            error_type="FrameworkAnalysisError",
            framework_ids=failed_frameworks,
        )
    db.commit()

    if len(failed_frameworks) == len(selected_frameworks):
        assessment.status = "error"
        db.commit()
        raise HTTPException(500, "Analysis failed for every selected framework. Run analysis again.")

    try:
        return _persist_multi_framework_analysis(
            assessment=assessment,
            assessment_id=assessment_id,
            responses=responses,
            documents=documents,
            context_profile=context_profile,
            desk_review_data=desk_review_data,
            applicable_requirements=applicable_requirements,
            selected_frameworks=selected_frameworks,
            has_documents=has_documents,
            db=db,
            result=result,
            run_context=run_context,
        )
    except Exception as exc:
        db.rollback()
        analysis_pipeline.fail_runs(db, run_context, error_type=type(exc).__name__)
        assessment.status = "error"
        db.commit()
        raise HTTPException(
            500,
            f"Analysis results could not be saved ({type(exc).__name__}). Run analysis again.",
        ) from exc


def _persist_multi_framework_analysis(
    assessment: Assessment,
    assessment_id: str,
    responses: list[dict],
    documents: list[dict],
    context_profile: dict | None,
    desk_review_data: dict | None,
    applicable_requirements: list[str] | None,
    selected_frameworks: list[str],
    has_documents: bool,
    db: Session,
    result: dict,
    run_context: analysis_pipeline.RunContext,
) -> dict:
    """Persist the multi-framework report and append-only analysis records."""
    from app.frameworks.registry import FrameworkRegistry

    # Preserve existing report data before re-run, then delete
    existing = db.query(GapReport).filter(GapReport.assessment_id == assessment_id).first()
    _carried_history = None
    if existing:
        old_items = db.query(GapItem).filter(GapItem.report_id == existing.id).all()
        snapshot = {
            "preserved_at": datetime.now().isoformat(),
            "label": "gap_analysis_rerun",
            "report": {
                c.name: getattr(existing, c.name)
                for c in existing.__table__.columns
                if c.name != "legacy_history"
            },
            "items": [
                {c.name: getattr(item, c.name) for c in item.__table__.columns}
                for item in old_items
            ],
        }
        history = []
        if existing.legacy_history:
            try:
                history = json.loads(existing.legacy_history)
                if not isinstance(history, list):
                    history = [history]
            except json.JSONDecodeError:
                history = []
        history.append(snapshot)
        _carried_history = json.dumps(history, default=str)

        db.query(GapItem).filter(GapItem.report_id == existing.id).delete()
        db.query(Initiative).filter(Initiative.report_id == existing.id).delete()
        db.delete(existing)
        db.flush()  # delete before the replacement INSERT: gap_reports.assessment_id is unique

    # Score each framework independently. There is intentionally no aggregate.
    per_fw_scores = {}
    per_fw_assessments = {}
    all_gap_items_data = []
    combined_raw = []
    combined_executive = []

    for fw_id in selected_frameworks:
        fw_result = result["frameworks"].get(fw_id)
        if not fw_result or "error" in fw_result:
            per_fw_assessments[fw_id] = []
            per_fw_scores[fw_id] = failed_framework_scores()
            continue

        parsed = fw_result["parsed"]
        fw_assessments = parsed.get("assessments", [])
        per_fw_assessments[fw_id] = fw_assessments

        # Server-side scope enforcement
        if applicable_requirements:
            applicable_set = set(applicable_requirements)
            for a in fw_assessments:
                if a.get("requirement_id") and a["requirement_id"] not in applicable_set:
                    a["compliance_status"] = "not_applicable"

        # Score this framework
        per_fw_scores[fw_id] = compute_framework_scores(fw_assessments, fw_id)

        if parsed.get("executive_summary"):
            combined_executive.append(f"**{fw_id.upper()}:** {parsed['executive_summary']}")

        combined_raw.append(fw_result.get("raw", ""))

        # Build control title/chapter lookups from registry
        fw = FrameworkRegistry.get(fw_id)
        fw_ctrl_map = {c.id: c for c in fw.all_controls()}

        for a in fw_assessments:
            req_id = a["requirement_id"]
            ctrl = fw_ctrl_map.get(req_id)
            all_gap_items_data.append({
                **a,
                "framework_id": fw_id,
                "chapter": ctrl.reference if ctrl else "unknown",
                "requirement_title": ctrl.title if ctrl else req_id,
                "control_reference": ctrl.reference if ctrl else "",
            })

    # Synthesis executive summary
    synthesis = result.get("synthesis")
    executive_summary = ""
    if synthesis and synthesis.get("parsed", {}).get("unified_executive_summary"):
        executive_summary = synthesis["parsed"]["unified_executive_summary"]
    elif combined_executive:
        executive_summary = "\n\n".join(combined_executive)

    # Create report
    report = GapReport(
        assessment_id=assessment_id,
        overall_score=0.0,
        chapter_scores=json.dumps(namespaced_domain_scores(per_fw_scores)),
        framework_scores=json.dumps(per_fw_scores),
        executive_summary=executive_summary,
        raw_ai_response="\n\n---\n\n".join(combined_raw),
        legacy_history=_carried_history,
    )
    db.add(report)
    db.flush()
    for framework_id in selected_frameworks:
        framework_result = result["frameworks"].get(framework_id)
        if framework_result and "error" not in framework_result:
            analysis_pipeline.record_framework_run(
                db,
                run_context,
                framework_id=framework_id,
                assessments=per_fw_assessments[framework_id],
                desk_review_data=desk_review_data,
                gap_report_id=report.id,
            )

    # Build evidence confidence lookup
    _dr_evidence_reqs = set()
    _dr_coverage = {}
    if desk_review_data:
        _dr_coverage = desk_review_data.get("coverage_summary", {})
        for f in desk_review_data.get("findings", []):
            if f.get("type") == "evidence" and f.get("requirement_id"):
                _dr_evidence_reqs.add(f["requirement_id"])

    _response_ids = {r["question_id"] for r in responses}

    def _evidence_confidence(req_id: str) -> str:
        has_dr = req_id in _dr_evidence_reqs or _dr_coverage.get(req_id) == "adequate"
        has_resp = req_id in _response_ids
        if has_dr and has_resp:
            return "strong"
        if has_dr or (has_resp and has_documents):
            return "moderate"
        return "weak"

    # Create gap items with framework_id
    for a in all_gap_items_data:
        req_id = a["requirement_id"]
        item = GapItem(
            report_id=report.id,
            requirement_id=req_id,
            chapter=a.get("chapter", "unknown"),
            requirement_title=a.get("requirement_title", req_id),
            compliance_status=a["compliance_status"],
            current_state=a.get("current_state", ""),
            gap_description=a.get("gap_description", ""),
            risk_level=a.get("risk_level", "medium"),
            remediation_action=a.get("remediation_action", ""),
            remediation_priority=a.get("remediation_priority", 3),
            remediation_effort=a.get("remediation_effort", "medium"),
            timeline_weeks=a.get("timeline_weeks", 8),
            maturity_level=a.get("maturity_level"),
            root_cause_category=a.get("root_cause_category"),
            evidence_quote=a.get("evidence_quote"),
            evidence_confidence=_evidence_confidence(req_id),
            framework_id=a.get("framework_id"),
            control_reference=a.get("control_reference"),
            review_status="draft",
            needs_review=a.get("needs_review", False),
            ai_compliance_status=a["compliance_status"],
            ai_gap_description=a.get("gap_description", ""),
            ai_risk_level=a.get("risk_level", "medium"),
        )
        db.add(item)

    # Generate cross-framework initiatives
    initiatives_data = generate_multi_framework_initiatives(per_fw_assessments)
    for init_data in initiatives_data:
        initiative = Initiative(
            report_id=report.id,
            initiative_id=init_data["initiative_id"],
            title=init_data["title"],
            root_cause=init_data.get("root_cause", ""),
            root_cause_category=init_data["root_cause_category"],
            requirements_addressed=json.dumps(init_data["requirements_addressed"]),
            combined_effort=init_data["combined_effort"],
            combined_timeline_weeks=init_data["combined_timeline_weeks"],
            priority=init_data["priority"],
            budget_estimate_band=init_data.get("budget_estimate_band"),
            suggested_approach=init_data["suggested_approach"],
        )
        db.add(initiative)

    failed = [
        framework_id
        for framework_id in selected_frameworks
        if not result["frameworks"].get(framework_id)
        or "error" in result["frameworks"][framework_id]
    ]
    assessment.status = "error" if failed else "completed"
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.id,
        "status": "incomplete" if failed else "completed",
        "frameworks_analyzed": list(per_fw_scores),
        "per_framework_scores": {fw_id: s["overall_score"] for fw_id, s in per_fw_scores.items()},
        "initiatives_generated": len(initiatives_data),
        "failed_frameworks": failed,
        "message": (
            f"Analysis failed for {', '.join(FrameworkRegistry.get(fw_id).name for fw_id in failed)}. "
            "Results for the other frameworks were saved. Run analysis again to complete the assessment."
            if failed
            else f"Multi-framework analysis completed ({len(selected_frameworks)} frameworks)"
        ),
        "analysis_run_ids": dict(run_context.run_ids),
    }
