"""Deterministic S7 seeds for narrative and board-input previews."""

from __future__ import annotations

import json

from app.models.action import Action
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.initiative_metadata import InitiativeMetadata
from app.models.report import GapReport
from design.harness.seed_s4 import SEED_ACTOR, _time


SCREEN_STATES = {
    "b5-narrative": ("empty", "generating", "drafted", "partly-accepted", "accepted", "error", "not-released"),
    "b5-board-inputs": ("empty", "partly", "complete", "dense", "error"),
}


def _row(framework, index, title, description, severity, priority, impact, recommendation, actions):
    return {
        "framework": framework,
        "index": index,
        "title": title,
        "description": description,
        "severity": severity,
        "priority": priority,
        "impact": impact,
        "recommendation": recommendation,
        "actions": actions,
    }


BREACH = _row("dpdpa", 0, "Breach notification process", "No route exists to notify the Board and affected data principals within the required window.", "high", 1, "A late or missed notification exposes the company to regulatory action and loss of customer trust.", "Add a notification step to the incident procedure with named owners and a template.", [("Add notification step to the incident procedure", "client"), ("Review the template with legal counsel", "shared")])
CONSENT = _row("dpdpa", 1, "Consent withdrawal mechanism", "Withdrawal is possible only by emailing the data protection officer.", "high", 2, "Customers cannot withdraw consent as easily as they gave it, which the Act requires.", "Add a withdrawal control to account settings.", [("Build the withdrawal control", "client")])
NOTICE = _row("dpdpa", 2, "Notice in regional languages", "The privacy notice is available in English only.", "high", 3, "", "", [("Translate the notice", "client"), ("Check the translation", "consultant")])
BACKUPS = _row("dpdpa", 3, "Backups not encrypted at rest", "Backups of the payments database are stored unencrypted.", "medium", 1, "", "", [("Enable encryption on backup storage", "client")])
RETENTION = _row("dpdpa", 4, "Data retention schedule", "No retention schedule covers customer records.", "medium", 2, "", "", [("Publish a retention schedule", "")])
ACCESS = _row("iso27001", 0, "Access rights", "Access reviews skip some production systems.", "medium", 3, "", "", [("Extend the access review to production systems", "consultant")])
RECOVERY = _row("iso27001", 1, "Disaster recovery testing", "The last recovery test missed its objective.", "low", 1, "", "", [("Re-run the recovery test", "shared")])
SUPPLIER = _row("iso27001", 2, "Supplier security reviews", "Some payment processors have no supplier review on file.", "low", 2, "", "", [("Review the payment processors", "")])

NARRATIVE_SPEC = [BREACH, CONSENT, NOTICE, BACKUPS, RETENTION, ACCESS, RECOVERY, SUPPLIER]
DENSE_SPEC = NARRATIVE_SPEC + [
    _row("iso27001", 3, "Privileged access list incomplete", "Not every privileged account has a named owner.", "low", 3, "", "", [("Name an owner for each privileged account", "")]),
    _row("iso27001", 4, "Incident register lacks severity", "Incidents are logged without a severity.", "low", 4, "", "", [("Add severity to the incident register", "")]),
    _row("dpdpa", 5, "Vendor onboarding skips privacy checks", "New vendors are onboarded without a privacy review.", "low", 4, "", "", [("Add a privacy check to vendor onboarding", "")]),
    _row("iso27001", 5, "Staff awareness training not tracked", "Completion of awareness training is not recorded.", "low", 4, "", "", [("Track training completion", "consultant")]),
]
COMPLETE_SPEC = [BREACH, CONSENT, ACCESS]
BOARD_SPECS = {
    "partly": [BREACH, CONSENT, NOTICE, BACKUPS],
    "complete": COMPLETE_SPEC,
    "dense": DENSE_SPEC,
    "error": [BREACH, CONSENT],
}
ASKS = [
    "Approve funding for the incident response work",
    "Name an executive owner for the access review programme",
    "Set the date for the next recovery test",
]
SECTION_ORDER = ("executive", "cross-framework", "framework-dpdpa", "framework-iso27001")


def _seed_findings(db, assessment, spec, *, release=True) -> None:
    from app.frameworks.registry import FrameworkRegistry
    from app.services import approved_report
    from app.services import findings as finding_service

    controls = {
        framework_id: FrameworkRegistry.get_all_controls(framework_id)
        for framework_id in assessment.frameworks
    }
    applicable = [controls[row["framework"]][row["index"]].id for row in spec]
    assessment.applicable_requirements = json.dumps(applicable)
    assessment.scope_answers = json.dumps({})
    db.add(
        GapReport(
            id=f"gap-report-{assessment.id}",
            assessment_id=assessment.id,
            overall_score=0.0,
            chapter_scores="{}",
            executive_summary="Seeded analysis report.",
            raw_ai_response="{}",
            framework_scores=None,
            generated_at=_time(-12),
        )
    )
    db.flush()

    conclusions = []
    for index, row in enumerate(spec):
        control = controls[row["framework"]][row["index"]]
        conclusion = Conclusion(
            id=f"conclusion-narrative-{assessment.id}-{index}",
            assessment_id=assessment.id,
            framework_id=row["framework"],
            requirement_id=control.id,
            outcome="partially_compliant",
            rationale="Seeded approved conclusion.",
            evidence_summary="Seeded evidence summary.",
            gaps_identified=row["description"],
            risk_level=row["severity"],
            recommended_action=row["recommendation"] or "Close the gap.",
            ai_proposed=True,
            created_at=_time(-12),
            updated_at=_time(-11),
        )
        db.add(conclusion)
        db.flush()
        db.add(ConclusionRevision(id=f"revision-proposed-{conclusion.id}", conclusion_id=conclusion.id, actor="system:analysis", action="proposed", created_at=_time(-12)))
        db.add(ConclusionRevision(id=f"revision-approved-{conclusion.id}", conclusion_id=conclusion.id, actor=SEED_ACTOR, action="approved", created_at=_time(-11)))
        conclusions.append(conclusion)
    db.flush()

    if release:
        approved_report.record_release(db, assessment, actor=SEED_ACTOR)
        db.flush()

    for conclusion, row in zip(conclusions, spec):
        actions = row["actions"]
        finding = finding_service.create_finding(
            db,
            assessment_id=assessment.id,
            conclusion_id=conclusion.id,
            conclusion_version=conclusion.version,
            title=row["title"],
            description=row["description"],
            severity=row["severity"],
            priority=row["priority"],
            action_title=actions[0][0],
            action_owner=None,
            action_target_date=None,
            notes=None,
            actor=SEED_ACTOR,
            now=_time(-10),
        )
        finding.business_impact = row["impact"] or None
        finding.recommendation = row["recommendation"] or None
        first = db.query(Action).filter(Action.finding_id == finding.id).one()
        first.responsibility = actions[0][1] or None
        for position, (action_title, responsibility) in enumerate(actions[1:], start=1):
            db.add(Action(id=f"action-{finding.id}-{position}", finding_id=finding.id, title=action_title, owner=None, responsibility=responsibility or None, status="open", history_json="[]", created_at=_time(-10), updated_at=_time(-10)))
    db.flush()


def _seed_narrative(db, assessment, state: str) -> None:
    from app.services import narrative

    refs = narrative.finding_refs(db, assessment)
    by_title = {ref.title: ref for ref in refs}
    section_refs = {
        "executive": refs[:3],
        "cross-framework": tuple(ref for ref in refs if ref.framework_id == "dpdpa")[:1] + tuple(ref for ref in refs if ref.framework_id == "iso27001")[:1],
        "framework-dpdpa": tuple(ref for ref in refs if ref.framework_id == "dpdpa")[:3],
        "framework-iso27001": tuple(ref for ref in refs if ref.framework_id == "iso27001")[:3],
    }
    status_map = {
        "drafted": {key: "draft" for key in SECTION_ORDER},
        "partly-accepted": {"executive": "accepted", "cross-framework": "draft", "framework-dpdpa": "accepted", "framework-iso27001": "accepted-stale"},
        "accepted": {key: "accepted" for key in SECTION_ORDER},
        "error": {key: "accepted" for key in SECTION_ORDER},
    }.get(state, {})
    sentences = {
        "executive": [
            "The assessment shows documented controls with gaps in customer response and operating evidence.",
            "The most significant exposure is concentrated in notification, access review and recovery practice.",
        ],
        "cross-framework": [
            "Controls exist on paper but are not applied consistently across the privacy and security frameworks.",
            "Access review and backup safeguards need the same accountable operating rhythm.",
        ],
        "framework-dpdpa": [
            "The privacy programme has gaps in notice, consent withdrawal and incident response.",
            "These gaps leave customer-facing obligations dependent on manual follow-up.",
        ],
        "framework-iso27001": [
            "The security management system is documented, but operating evidence is incomplete.",
            "Access reviews, recovery testing and supplier oversight need consistent execution.",
        ],
    }
    for section_id in SECTION_ORDER:
        status = status_map.get(section_id, "none")
        if status == "none" or section_id not in narrative.section_ids(assessment, refs):
            continue
        refs_for_section = section_refs[section_id]
        sentence_rows = [
            {"text": text, "finding_ids": [ref.finding_id for ref in refs_for_section]}
            for text in sentences[section_id]
        ]
        basis = narrative._basis_sha256(section_id, refs)
        draft = narrative._write_event(
            db,
            actor=SEED_ACTOR,
            action=narrative.AUDIT_DRAFTED,
            assessment_id=assessment.id,
            metadata={"section_id": section_id, "basis_sha256": basis, "status": "ok", "sentences": sentence_rows, "dropped": [], "prompt_sha256": narrative.prompt_sha256(), "prompt_version": narrative.PROMPT_VERSION, "calls": [], "error_type": None},
        )
        if status.startswith("accepted"):
            narrative._write_event(
                db,
                actor=SEED_ACTOR,
                action=narrative.AUDIT_ACCEPTED,
                assessment_id=assessment.id,
                metadata={"section_id": section_id, "basis_sha256": "0" * 64 if status == "accepted-stale" else basis, "sentences": sentence_rows, "source_event_id": draft.id},
            )
    db.flush()


def _seed_board(db, assessment, state: str) -> None:
    from app.services import board_inputs, remediation_groups, report_content

    if state == "empty":
        return
    _seed_findings(db, assessment, BOARD_SPECS[state])
    findings = report_content.assessment_findings(db, assessment).findings
    groups = remediation_groups.build_groups(findings, assessment.frameworks)
    saved_positions = {"partly": (0, 2), "complete": (0, 1, 2), "error": (0,)}.get(state, ())
    for position in saved_positions:
        if position >= len(groups):
            continue
        group = groups[position]
        db.add(InitiativeMetadata(assessment_id=assessment.id, group_id=group["group_id"], title={0: "Strengthen incident response", 1: "Close access review gaps", 2: "Fix the notice"}.get(position, "Initiative"), complexity="high" if position == 0 else "low", benefit="high" if position == 0 else None))
    if state in ("partly", "complete", "error"):
        assessment.board_asks_json = json.dumps({"consultant": ASKS[:3] if state == "complete" else ASKS[:1], "by": "Priya Sharma"})
    db.flush()


def apply(db, screen, state, assessment, engagement, data) -> dict:
    if screen == "b5-board-inputs":
        _seed_board(db, assessment, state)
        if state == "error":
            return {"data_state": "preview-state", "note": "Stored rows are real board inputs; validation copy is drawn by the preview."}
        return {"data_state": "database", "note": "Findings, actions, initiative metadata and board decisions are seeded through the real services."}

    _seed_findings(db, assessment, NARRATIVE_SPEC, release=state != "not-released")
    if state == "not-released":
        return {"data_state": "database", "note": "Approved conclusions exist without a release event."}
    _seed_narrative(db, assessment, state)
    if state == "generating":
        return {"data_state": "preview-state", "note": "The in-flight draft state is rendered by the design preview."}
    if state == "error":
        return {"data_state": "preview-state", "note": "Failure and draft-limit messages are X-Toast-Message response headers."}
    return {"data_state": "database", "note": "Narrative events use the real service audit-event format and basis hashes."}


def route(screen: str, state: str, assessment_id: str) -> str:
    if screen == "b5-narrative" and state == "generating":
        return f"/design/pages/b5-narrative?state=generating&assessment_id={assessment_id}"
    if screen == "b5-board-inputs" and state == "error":
        return f"/design/pages/b5-board-inputs?state=error&assessment_id={assessment_id}"
    return f"/assessments/{assessment_id}/{ 'narrative' if screen == 'b5-narrative' else 'board-inputs' }"
