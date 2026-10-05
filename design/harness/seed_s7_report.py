"""Deterministic report and no-report specimens for the S7 design harness."""

from __future__ import annotations

import json

from design.harness.seed_s4 import SEED_ACTOR, _time

SCREEN_STATES = {
    "b5-report": ("released", "not-released", "loading"),
    "b5-no-report": ("default",),
}


def _conclusion(db, assessment, framework_id, control, index, *, approved: bool) -> None:
    from app.models.conclusion import Conclusion, ConclusionRevision

    conclusion_id = f"conclusion-report-{assessment.id}-{framework_id}-{index}"
    db.add(
        Conclusion(
            id=conclusion_id,
            assessment_id=assessment.id,
            framework_id=framework_id,
            requirement_id=control.id,
            outcome=("partially_compliant" if index % 3 == 0 else "compliant"),
            rationale="Seeded consultant conclusion for the report specimen.",
            evidence_summary="Seeded evidence is available for this control.",
            gaps_identified="A documented operating check is still useful." if index % 3 == 0 else "None.",
            risk_level="high" if index % 3 == 0 else "low",
            recommended_action="Document and test the operating check." if index % 3 == 0 else "Maintain the current control.",
            ai_proposed=True,
            created_at=_time(-12),
            updated_at=_time(-11),
        )
    )
    db.flush()
    db.add(ConclusionRevision(
        id=f"revision-proposed-{conclusion_id}",
        conclusion_id=conclusion_id,
        actor="system:analysis",
        action="proposed",
        created_at=_time(-12),
    ))
    if approved:
        db.add(ConclusionRevision(
            id=f"revision-approved-{conclusion_id}",
            conclusion_id=conclusion_id,
            actor=SEED_ACTOR,
            action="approved",
            created_at=_time(-11),
        ))


def _report(db, assessment, *, failed_iso: bool = False) -> None:
    from app.models.report import GapReport
    from app.services.scoring import failed_framework_scores

    scores = {"iso27001": failed_framework_scores()} if failed_iso else None
    db.add(GapReport(
        id=f"gap-report-{assessment.id}",
        assessment_id=assessment.id,
        overall_score=0.0,
        chapter_scores="{}",
        executive_summary="Seeded analysis report.",
        raw_ai_response="{}",
        framework_scores=json.dumps(scores) if scores else None,
        generated_at=_time(-12),
    ))
    db.flush()


def apply(db, screen, state, assessment, engagement, data):
    from app.frameworks.registry import FrameworkRegistry

    if screen == "b5-no-report":
        assessment.scope_answers = json.dumps({})
        return {"data_state": "database", "note": "Assessment without a GapReport."}

    assessment.status = "completed"
    controls = {
        framework_id: FrameworkRegistry.get_all_controls(framework_id)[: (3 if state == "not-released" else 2)]
        for framework_id in assessment.frameworks
    }
    assessment.scope_answers = json.dumps({})
    assessment.applicable_requirements = json.dumps([
        control.id for framework_controls in controls.values() for control in framework_controls
    ])
    _report(db, assessment, failed_iso=state == "not-released")
    for framework_id, framework_controls in controls.items():
        for index, control in enumerate(framework_controls):
            _conclusion(
                db,
                assessment,
                framework_id,
                control,
                index,
                approved=state == "released",
            )
    if state == "released":
        from app.services import approved_report

        approved_report.record_release(db, assessment, actor=SEED_ACTOR)
    return {
        "data_state": "preview-state" if state == "loading" else "database",
        "note": "Loading uses the live report shell with a deterministic preview state." if state == "loading" else "",
    }


def route(screen, state, assessment_id):
    """Live report route; loading goes through the b5-report-loading preview of the same shell."""
    if screen == "b5-report" and state == "loading":
        return f"/design/pages/b5-report-loading?assessment_id={assessment_id}"
    return f"/assessments/{assessment_id}/report"
