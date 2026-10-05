"""Deterministic S7 analysis-group preview fixtures."""

from __future__ import annotations

import json

from design.harness.seed_s4 import SEED_ACTOR, _audit, _time

SCREEN_STATES = {
    "b5-analysis": ("running", "complete", "error", "error-all", "gate", "gate-no-override"),
    "b5-release": ("blocked", "ready", "confirm", "released", "stale"),
    "b5-basis": ("empty", "filled", "invalid", "locked", "saved"),
    "b5-review-finding-card": ("draft", "needs-review", "notes", "accepted", "rejected"),
}


def route(screen: str, state: str, assessment_id: str) -> str:
    return f"/design/pages/{screen}?state={state}&assessment_id={assessment_id}"


def _controls(assessment, count=3):
    from app.frameworks.registry import FrameworkRegistry
    return {framework_id: list(FrameworkRegistry.get_all_controls(framework_id)[:count]) for framework_id in assessment.frameworks}


def _gap_report(db, assessment, scores=None):
    from app.models.report import GapReport
    db.add(GapReport(id=f"gap-report-{assessment.id}", assessment_id=assessment.id, overall_score=0.0, chapter_scores="{}", executive_summary="Seeded analysis report.", raw_ai_response="{}", framework_scores=json.dumps(scores) if scores else None, generated_at=_time(-1)))
    db.flush()


def _conclusions(db, assessment, approved):
    from app.models.conclusion import Conclusion, ConclusionRevision
    controls = _controls(assessment)
    assessment.applicable_requirements = json.dumps([control.id for controls_for_framework in controls.values() for control in controls_for_framework])
    assessment.scope_answers = json.dumps({})
    db.flush()
    for framework_id, framework_controls in controls.items():
        for index, control in enumerate(framework_controls):
            conclusion = Conclusion(id=f"conclusion-s7a-{framework_id}-{index}", assessment_id=assessment.id, framework_id=framework_id, requirement_id=control.id, outcome="partially_compliant", rationale="Seeded conclusion.", evidence_summary="Seeded evidence summary.", gaps_identified="Seeded gap.", risk_level="medium", recommended_action="Seeded recommendation.", ai_proposed=True, created_at=_time(-6), updated_at=_time(-5))
            db.add(conclusion)
            db.flush()
            db.add(ConclusionRevision(id=f"revision-proposed-{conclusion.id}", conclusion_id=conclusion.id, actor="system:analysis", action="proposed", created_at=_time(-6)))
            if index < approved.get(framework_id, 0):
                db.add(ConclusionRevision(id=f"revision-approved-{conclusion.id}", conclusion_id=conclusion.id, actor=SEED_ACTOR, action="approved", created_at=_time(-5)))
    db.flush()


def _basis_names(db, assessment):
    db.add(_audit(f"audit-basis-names-{assessment.id}", action="assessment.report_basis_updated", entity_type="assessment", entity_id=assessment.id, created_at=_time(-26), metadata={"after": {"period_start": "2025-04-01", "period_end": "2026-03-31", "evidence_cutoff": "2026-03-15", "prepared_by": "Arjun Mehta", "reviewed_by": "Priya Sharma"}}))
    db.flush()


def _release(db, assessment):
    from app.services import approved_report
    event = approved_report.record_release(db, assessment, actor=SEED_ACTOR)
    event.created_at = _time(-6)
    db.flush()


def _finding_item(db, assessment, state):
    from app.models.report import GapItem
    _gap_report(db, assessment)
    db.add(GapItem(id="gap-item-s7-consent", report_id=f"gap-report-{assessment.id}", requirement_id="CH2.CONSENT.3", framework_id="dpdpa", chapter="Consent", requirement_title="Consent withdrawal mechanism", compliance_status="non_compliant", current_state="Withdrawal is by email only.", gap_description="Users cannot withdraw consent in the product. The only route is an email to the data protection officer.", risk_level="high", remediation_action="Add a withdrawal control to the preference page.", remediation_priority=1, remediation_effort="medium", timeline_weeks=6, evidence_quote=None if state == "needs-review" else "The consent preference page lets users view their choices. Changes are requested through the data protection officer.", evidence_confidence="weak", review_status={"accepted": "accepted", "rejected": "rejected"}.get(state, "draft"), needs_review=state == "needs-review", ai_compliance_status="non_compliant", ai_risk_level="high", reviewer_notes="The mechanism exists in the mobile app. Evidence is for the web product only." if state == "rejected" else None))
    db.flush()


def apply(db, screen, state, assessment, engagement, data):
    from design.harness.seed_s5 import _seed_documents, _seed_questionnaire_responses
    if screen == "b5-analysis":
        if state == "running":
            assessment.status = "analyzing"
            _seed_documents(db, engagement, assessment, 14, "s7a")
            _seed_questionnaire_responses(db, assessment, complete=True)
        elif state == "complete":
            assessment.status = "completed"
            _gap_report(db, assessment)
            _conclusions(db, assessment, {"dpdpa": 2, "iso27001": 1})
        elif state == "error":
            from app.services.scoring import failed_framework_scores
            assessment.status = "error"
            _gap_report(db, assessment, {"iso27001": failed_framework_scores()})
            _conclusions(db, assessment, {"dpdpa": 0})
        elif state == "error-all":
            assessment.status = "error"
        elif state == "gate":
            assessment.status = "created"
            _seed_documents(db, engagement, assessment, 14, "s7a")
        else:
            assessment.status = "created"
            assessment.applicable_requirements = json.dumps([])
        return {"data_state": "database", "note": f"seeded {screen}/{state}"}
    if screen == "b5-release":
        _gap_report(db, assessment)
        if state == "blocked":
            _conclusions(db, assessment, {"dpdpa": 3, "iso27001": 0})
        else:
            _conclusions(db, assessment, {"dpdpa": 3, "iso27001": 3})
            if state in {"released", "stale"}:
                _release(db, assessment)
            if state == "stale":
                from app.models.conclusion import Conclusion
                conclusion = db.get(Conclusion, "conclusion-s7a-dpdpa-0")
                conclusion.version += 1
                conclusion.rationale = "Seeded conclusion, changed after release."
        return {"data_state": "database", "note": f"seeded {screen}/{state}"}
    if screen == "b5-basis":
        if state != "empty":
            _basis_names(db, assessment)
        if state == "locked":
            _gap_report(db, assessment)
            _conclusions(db, assessment, {"dpdpa": 2, "iso27001": 0})
        return {"data_state": "database", "note": f"seeded {screen}/{state}"}
    _finding_item(db, assessment, state)
    return {"data_state": "database", "note": f"seeded {screen}/{state}"}
