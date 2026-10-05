"""Deterministic S7 page specimens for review queue and conclusions."""

from __future__ import annotations

from app.models.conclusion import Conclusion, ConclusionRevision
from design.harness.seed_s4 import SEED_ACTOR, _time


SCREEN_STATES = {
    "b5-review-queue": ("default", "shared", "done", "empty"),
    "b5-conclusions": ("default", "legacy-bulk", "empty"),
}

LEGACY_ACTOR = "system:bulk-approve"
ROWS = (
    ("dpdpa", "CH2.CONSENT.3", "non_compliant", "high", "pending"),
    ("dpdpa", "CH2.SECURITY.1", "partially_compliant", "medium", "approved"),
    ("dpdpa", "CM.RECORDS.1", "compliant", "low", "approved"),
    ("iso27001", "ISO.A5.18", "non_compliant", "high", "pending"),
    ("iso27001", "ISO.A5.30", "partially_compliant", "medium", "pending"),
    ("iso27001", "ISO.A5.1", "compliant", "low", "edited"),
)

TEXT = {
    "ISO.A5.18": (
        "Three production systems were left out of the Q1 access review, so the requirement to review all systems is not met.",
        "Three production systems were not part of the Q1 access review.",
        "Extend the quarterly access review to every production system.",
        "Access reviews were completed for 11 of 14 production systems; the payments ledger, card vault and data warehouse were not reviewed.",
    ),
}


def _conclusion(assessment, framework_id, requirement_id, outcome, risk, cluster_id=None):
    rationale, gaps, action, evidence = TEXT.get(
        requirement_id,
        (
            "The evidence supports this outcome.",
            "None recorded." if outcome == "compliant" else "The control is not fully evidenced.",
            "None." if outcome == "compliant" else "Close the gap and provide evidence.",
            "The submitted policy describes the control.",
        ),
    )
    return Conclusion(
        id=f"conclusion-s7-{assessment.id}-{requirement_id}",
        assessment_id=assessment.id,
        framework_id=framework_id,
        requirement_id=requirement_id,
        cluster_id=cluster_id,
        outcome=outcome,
        rationale=rationale,
        evidence_summary=evidence,
        gaps_identified=gaps,
        risk_level=risk,
        recommended_action=action,
        ai_proposed=True,
        created_at=_time(-6),
        updated_at=_time(-5),
    )


def _revision(conclusion, actor, action, days):
    return ConclusionRevision(
        id=f"revision-{action}-{conclusion.id}",
        conclusion_id=conclusion.id,
        actor=actor,
        action=action,
        created_at=_time(days),
    )


def _seed(db, assessment, *, decisions=None, legacy=(), shared_cluster=None):
    decisions = decisions or {}
    for framework_id, requirement_id, outcome, risk, decision in ROWS:
        decision = decisions.get(requirement_id, decision)
        cluster_id = shared_cluster if requirement_id in {"ISO.A5.18", "CH2.SECURITY.1"} else None
        conclusion = _conclusion(assessment, framework_id, requirement_id, outcome, risk, cluster_id)
        db.add(conclusion)
        db.flush()
        db.add(_revision(conclusion, "system:analysis", "proposed", -6))
        if requirement_id in legacy:
            db.add(_revision(conclusion, LEGACY_ACTOR, "approved", -5))
        elif decision == "approved":
            db.add(_revision(conclusion, SEED_ACTOR, "approved", -5))
        elif decision == "edited":
            db.add(_revision(conclusion, SEED_ACTOR, "edited", -5))
    db.flush()


def apply(db, screen, state, assessment, engagement, data) -> dict:
    if state == "empty":
        return {"data_state": "database", "note": "No conclusions exist for the assessment."}
    if screen == "b5-review-queue":
        if state == "done":
            _seed(db, assessment, decisions={requirement_id: "approved" for _, requirement_id, *_ in ROWS})
            return {"data_state": "database", "note": "All six conclusions carry a consultant approval revision."}
        if state == "shared":
            _seed(db, assessment, shared_cluster="CLUSTER_006", decisions={"CH2.SECURITY.1": "pending"})
            return {"data_state": "database", "note": "Access rights and security safeguards share one evidence cluster."}
        _seed(db, assessment)
        return {"data_state": "database", "note": "Three pending and three decided conclusions."}
    if state == "legacy-bulk":
        _seed(db, assessment, legacy=("CH2.SECURITY.1", "CM.RECORDS.1"))
        return {"data_state": "database", "note": "Two approvals carry a non-consultant actor."}
    _seed(db, assessment)
    return {"data_state": "database", "note": "Three pending, two approved and one edited conclusion."}


def route(screen, state, assessment_id) -> str:
    return f"/assessments/{assessment_id}/review-queue" if screen == "b5-review-queue" else f"/assessments/{assessment_id}/conclusions"
