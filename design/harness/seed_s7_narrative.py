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

# Board-input rows carry the b5-board-inputs mockup's titles, context and actions.
B_NOTICE = _row("dpdpa", 2, "Notice in regional languages", "The privacy notice is available in English only.", "high", 3, "Customers who read Hindi or Marathi cannot give informed consent.", "Publish the notice in Hindi and Marathi.", [("Translate the notice", "client"), ("Check the translation", "consultant")])
B_BACKUPS = _row("dpdpa", 3, "Backups not encrypted at rest", "Backups of the payments database are stored unencrypted.", "medium", 1, "A lost backup would expose cardholder and account data.", "Encrypt backups and rotate the keys.", [("Enable encryption on backup storage", "client")])
B_ACCESS = _row("iso27001", 0, "Access reviews skip production systems", "Three production systems were left out of the Q1 access review.", "medium", 3, "Leavers and role changes on those systems may keep access they should not have.", "Extend the quarterly access review to every production system.", [("Add the three systems to the review scope", "client")])
B_RECOVERY = _row("iso27001", 1, "Disaster recovery test missed its objective", "Failover took six hours against a four-hour objective.", "low", 1, "A real outage would stop payments for longer than the business has agreed it can bear.", "Fix the failover runbook and run the test again.", [("Update the failover runbook", "client"), ("Observe the repeat test", "consultant")])
B_SUPPLIER = _row("iso27001", 2, "Supplier security reviews missing", "Two payment processors have no security review on file.", "low", 2, "Weak controls at a processor become the company’s exposure.", "Review both processors and set a yearly cycle.", [("Collect assurance reports from both processors", "shared")])
B_RETENTION = _row("dpdpa", 4, "Data retention schedule", "No schedule exists for payment dispute records.", "medium", 2, "Records are kept longer than needed, which increases breach impact.", "Agree retention periods and automate deletion.", [("Draft the retention schedule", "shared")])
B_PRIVILEGED = _row("iso27001", 3, "Privileged access list incomplete", "The list of privileged accounts has no owners recorded.", "low", 3, "Nobody is accountable for removing standing admin rights.", "Record an owner for every privileged account.", [("Assign owners", "client")])
B_INCIDENTS = _row("iso27001", 4, "Incident register lacks severity", "Incidents are logged without a severity rating.", "low", 4, "", "", [("Add the severity field", "client")])
B_VENDORS = _row("dpdpa", 5, "Vendor onboarding skips privacy checks", "New vendors are not asked how they handle personal data.", "low", 4, "", "", [("Draft the question set", "consultant")])
B_TRAINING = _row("iso27001", 5, "Staff awareness training not tracked", "Completion of annual training is not recorded.", "low", 4, "", "", [("Set up completion tracking", "client")])


def _blank(row):
    return {**row, "impact": "", "recommendation": ""}


BOARD_SPECS = {
    # Backups sit on requirement 4 so the three findings span three roadmap groups, as in the mockup.
    "partly": [BREACH, CONSENT, _blank(B_NOTICE), _blank({**B_BACKUPS, "index": 4})],
    "complete": [BREACH, {**CONSENT, "index": 2}, {**B_NOTICE, "index": 4}],
    "dense": [BREACH, CONSENT, B_NOTICE, B_BACKUPS, B_ACCESS, B_RECOVERY, B_SUPPLIER, B_RETENTION, B_PRIVILEGED, {**B_INCIDENTS, "index": 10}, B_VENDORS, B_TRAINING],
    "error": [BREACH, CONSENT],
}
# Initiative metadata by roadmap-group position (the group topics themselves come from
# the real control clusters, so they differ from the mockup's invented topics).
_INCIDENT = ("Strengthen incident response", "high", "high")
_CONSENT = ("Make consent easy to give and withdraw", "medium", "high")
_ACCESS = ("Close access review gaps", "low", "high")
BOARD_INITIATIVES = {
    "partly": [_INCIDENT, None, ("Close access review gaps", "low", None)],
    "complete": [_INCIDENT, _CONSENT, _ACCESS],
    "dense": [_INCIDENT, _CONSENT, _ACCESS, ("Encrypt backups", "medium", "medium"), ("Meet the recovery objective", "medium", "medium"), ("Review payment processors", "low", "medium")],
    "error": [_INCIDENT],
}
BOARD_ASK_COUNT = {"partly": 1, "complete": 3, "dense": 2, "error": 1}
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
        first.created_at = _time(-10)
        for position, (action_title, responsibility) in enumerate(actions[1:], start=1):
            db.add(Action(id=f"action-{finding.id}-{position}", finding_id=finding.id, title=action_title, owner=None, responsibility=responsibility or None, status="open", history_json="[]", created_at=_time(-10), updated_at=_time(-10)))
    db.flush()


def _seed_narrative(db, assessment, state: str) -> None:
    from app.services import narrative

    refs = narrative.finding_refs(db, assessment)

    def cite(*positions):
        # 1-based positions in NARRATIVE_SPEC order (the mockup's R-01 to R-08).
        return [refs[position - 1].finding_id for position in positions]

    status_map = {
        "drafted": {key: "draft" for key in SECTION_ORDER},
        "partly-accepted": {"executive": "accepted", "cross-framework": "draft", "framework-dpdpa": "accepted", "framework-iso27001": "accepted-stale"},
        "accepted": {key: "accepted" for key in SECTION_ORDER},
        "error": {"executive": "accepted", "cross-framework": "accepted", "framework-dpdpa": "accepted"},
    }.get(state, {})
    sentences = {
        "executive": [
            ("Meridian Ledger Technologies has documented most of what a privacy and security programme needs, but some controls do not yet work as written.", cite(1, 6)),
            ("The most serious gaps are where customers act on their data and where incidents must be reported.", cite(1, 2)),
            ("Closing the access review and incident notification gaps would reduce the most exposure.", cite(1, 6)),
        ],
        "cross-framework": [
            ("Under both frameworks, controls exist on paper but are not applied everywhere.", cite(4, 6)),
            ("Access to some production systems is not reviewed, and backups are not encrypted at rest, which weakens safeguards the policies already promise.", cite(4, 6)),
        ],
        "framework-dpdpa": [
            ("The record of processing and the incident register are in place.", cite(1)),
            ("Consent can be withdrawn only by emailing the data protection officer, the privacy notice is in English only, and the breach procedure has no route to notify affected data principals.", cite(1, 2, 3)),
        ],
        "framework-iso27001": [
            ("The management system is documented and the policy set is current.", cite(6)),
            ("Operation lags the documents: access reviews skip some production systems, the last recovery test missed its objective, and some payment processors have no supplier review on file.", cite(6, 7, 8)),
        ],
    }
    # The mockup shows a dropped sentence only in the just-drafted state.
    dropped = {
        "framework-dpdpa": [{"text": "Most organisations at this stage benefit from a dedicated privacy officer.", "reason": "no_reference"}],
    } if state == "drafted" else {}
    for section_id in SECTION_ORDER:
        status = status_map.get(section_id, "none")
        if status == "none" or section_id not in narrative.section_ids(assessment, refs):
            continue
        sentence_rows = [{"text": text, "finding_ids": ids} for text, ids in sentences[section_id]]
        basis = narrative._basis_sha256(section_id, refs)
        draft = narrative._write_event(
            db,
            actor=SEED_ACTOR,
            action=narrative.AUDIT_DRAFTED,
            assessment_id=assessment.id,
            metadata={"section_id": section_id, "basis_sha256": basis, "status": "ok", "sentences": sentence_rows, "dropped": dropped.get(section_id, []), "prompt_sha256": narrative.prompt_sha256(), "prompt_version": narrative.PROMPT_VERSION, "calls": [], "error_type": None},
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
    for group, initiative in zip(groups, BOARD_INITIATIVES.get(state, [])):
        if initiative is None:
            continue
        title, complexity, benefit = initiative
        db.add(InitiativeMetadata(assessment_id=assessment.id, group_id=group["group_id"], title=title, complexity=complexity, benefit=benefit))
    # Through the real service, so the stored shape and the reviewer-name audit event are genuine.
    board_inputs.update_board_asks(db, assessment.id, ASKS[: BOARD_ASK_COUNT[state]], SEED_ACTOR)
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
