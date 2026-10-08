"""Seed the Veldhara Logistics walkthrough company through real app routes."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEMO_NAME = "Veldhara Logistics Pvt Ltd."
REVIEWER = "Meera Joshi"
CURRENT_DESCRIPTION = "FY2026-27 reassessment (DPDPA + ISO 27001)"
PRIOR_DESCRIPTION = "FY2025-26 baseline (DPDPA + ISO 27001)"
INTERIM_DESCRIPTION = "Interim ISO 27001 check"
NIST_DESCRIPTION = "NIST CSF 2.0 baseline"

PRIOR_IDS = [
    "CH2.CONSENT.1",
    "CH2.CONSENT.3",
    "CH2.NOTICE.1",
    "CH2.SECURITY.1",
    "CH3.GRIEVANCE.1",
    "CH4.CHILD.1",
    "ISO.A5.1",
    "ISO.A5.18",
    "ISO.A5.19",
    "ISO.A5.24",
    "ISO.A5.30",
    "ISO.A6.3",
    "ISO.A8.5",
    "ISO.A8.13",
    "ISO.A8.25",
]
INTERIM_IDS = [
    "ISO.A5.1",
    "ISO.A5.18",
    "ISO.A5.24",
    "ISO.A5.30",
    "ISO.A6.3",
    "ISO.A8.13",
]

ANSWER_CYCLE = (
    "fully_implemented",
    "fully_implemented",
    "partially_implemented",
    "fully_implemented",
    "partially_implemented",
    "not_implemented",
    "fully_implemented",
    "planned",
)
NOTES = (
    "Process exists but is not documented.",
    "Owner identified, rollout planned next quarter.",
    "Evidence is available for part of the process only.",
    "The control is performed inconsistently across depots.",
    "A vendor dependency remains to be confirmed.",
    "The last review identified an open exception.",
    "Testing is planned but has not started.",
    "The process needs a current operating record.",
)
STRONG_WORDS = (
    "policy",
    "governance",
    "grievance",
    "classification",
    "continuity",
    "disaster",
    "physical",
)
WEAK_WORDS = (
    "incident",
    "breach",
    "supplier",
    "vendor",
    "third",
    "processor",
    "consent",
    "awareness",
    "training",
    "backup",
)


def _item(
    requirement_id: str,
    status: str,
    risk: str,
    current_state: str,
    evidence_quote: str = "",
    gap: str = "No gap identified.",
    action: str = "None required.",
) -> dict:
    maturity = {
        "compliant": 4,
        "partially_compliant": 3,
        "non_compliant": 2,
        "not_applicable": 0,
    }[status]
    return {
        "requirement_id": requirement_id,
        "compliance_status": status,
        "current_state": current_state,
        "gap_description": gap,
        "risk_level": risk,
        "remediation_action": action,
        "remediation_priority": {"high": 1, "medium": 2, "low": 3}[risk],
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": maturity,
        "root_cause_category": "process",
        "evidence_quote": evidence_quote,
        "needs_review": False,
    }


def _na_item(requirement_id: str, rationale: str) -> dict:
    return _item(
        requirement_id,
        "not_applicable",
        "low",
        rationale,
        gap="No gap identified.",
        action="None required.",
    )


ITEMS = {
    PRIOR_DESCRIPTION: {
        "dpdpa": [
            _item("CH2.CONSENT.1", "partially_compliant", "medium", "Consent language is present in core workflows but not consistently recorded.", "The records of processing describe consent and operational collection points.", "Consent records are incomplete for mobile collection.", "Document consent records for every mobile collection flow."),
            _item("CH2.CONSENT.3", "non_compliant", "high", "The driver app offers no way to withdraw consent once given.", "", "There is no consent withdrawal mechanism.", "Ship an in-app consent withdrawal flow that is as easy as giving consent."),
            _item("CH2.NOTICE.1", "partially_compliant", "medium", "Processing purposes and retention are recorded, but the notice set is not consistently linked to each channel.", "The records of processing list driver KYC, consignee contacts, and payroll purposes.", "Notice evidence is not linked to every collection channel.", "Map each collection channel to its current privacy notice."),
            _item("CH2.SECURITY.1", "non_compliant", "high", "Security safeguards exist, but backup encryption evidence was not available.", "The information security policy requires MFA for remote access.", "Backup encryption evidence is missing.", "Obtain and file the hosting provider backup encryption attestation."),
            _item("CH3.GRIEVANCE.1", "partially_compliant", "medium", "A named grievance officer handles complaints, but response records are not consistently retained.", "The privacy officer maintains the grievance register.", "Grievance response evidence is incomplete.", "Retain a complete grievance response record for each case."),
            _na_item("CH4.CHILD.1", "Scope answer SCP.2 = No: the company does not process children's data."),
        ],
        "iso27001": [
            _item("ISO.A5.1", "compliant", "low", "An approved information security policy is reviewed annually.", "Owner: Chief Information Security Officer. Approved by the board risk committee."),
            _item("ISO.A5.18", "non_compliant", "high", "Quarterly access reviews skipped two production systems.", "The quarterly review covered 9 of 11 production systems.", "Two production systems were left out of the quarterly access review.", "Extend the quarterly access review to every production system."),
            _item("ISO.A5.19", "non_compliant", "high", "Supplier security reviews are ad hoc and are not recorded consistently.", "", "Supplier security reviews are not performed on a repeatable schedule.", "Introduce a risk-based supplier security review calendar."),
            _item("ISO.A5.24", "non_compliant", "high", "An incident response plan exists but has never been tested.", "The plan exists but has not yet been tested.", "The incident response plan has not been exercised.", "Run and document an incident response tabletop exercise."),
            _item("ISO.A5.30", "partially_compliant", "medium", "A DR failover test was run but missed its recovery time objective.", "Failover completed in 3h 10m against a 4h RTO.", "The prior test record did not demonstrate an accepted recovery result.", "Retest failover and record the agreed recovery objective."),
            _item("ISO.A6.3", "compliant", "low", "Security awareness training was completed on the annual cycle.", "Training records were reviewed for the prior cycle."),
            _item("ISO.A8.5", "partially_compliant", "medium", "Remote access uses MFA, but privileged access evidence is incomplete.", "The information security policy requires MFA for remote access.", "Privileged access evidence is not complete for every system.", "Complete privileged access evidence for all production systems."),
            _item("ISO.A8.13", "partially_compliant", "medium", "Backups run, but restore testing is not evidenced.", "", "Backup restore has not been tested.", "Run and record a backup restore test."),
            _na_item("ISO.A8.25", "Scope answer ISO.SCP.3 = No software development."),
        ],
    },
    CURRENT_DESCRIPTION: {
        "dpdpa": [
            _item("CH2.CONSENT.1", "compliant", "low", "Consent language is recorded for the main collection workflows.", "The records of processing describe the collection purposes and retention periods."),
            _item("CH2.CONSENT.3", "non_compliant", "high", "The driver app still has no way to withdraw consent once given.", "I agree to location tracking", "There is no consent withdrawal mechanism in the driver app.", "Ship an in-app consent withdrawal flow that is as easy as giving consent."),
            _item("CH2.NOTICE.1", "partially_compliant", "medium", "Processing purposes are documented, but channel-level notice evidence is incomplete.", "The records of processing list driver KYC, consignee contacts, and payroll.", "Notice evidence is not linked to every collection channel.", "Map each collection channel to its current privacy notice."),
            _item("CH2.SECURITY.1", "partially_compliant", "medium", "Core security safeguards are documented, while backup encryption evidence remains outstanding.", "MFA is required for remote access.", "Backup encryption evidence is still missing.", "Obtain and file the hosting provider backup encryption attestation."),
            _item("CH3.GRIEVANCE.1", "compliant", "low", "A named grievance officer handles complaints and maintains a response process.", "The privacy officer maintains the grievance register."),
            _na_item("CH4.CHILD.1", "Scope answer SCP.2 = No: the company does not process children's data."),
        ],
        "iso27001": [
            _item("ISO.A5.1", "compliant", "low", "The approved information security policy is reviewed every 12 months.", "Owner: Chief Information Security Officer. Approved by the board risk committee."),
            _item("ISO.A5.18", "partially_compliant", "medium", "The quarterly access review now covers most systems but still skips two systems.", "The quarterly review covered 9 of 11 production systems.", "Two production systems remain outside the quarterly review.", "Extend the quarterly access review to every production system."),
            _item("ISO.A5.19", "non_compliant", "high", "Supplier security reviews remain ad hoc.", "", "Supplier security reviews are not performed on a repeatable schedule.", "Introduce a risk-based supplier security review calendar."),
            _item("ISO.A5.24", "partially_compliant", "medium", "An incident response plan exists but has never been tested.", "The plan exists but has not yet been tested.", "The incident response plan has not been exercised.", "Run and document an incident response tabletop exercise."),
            _item("ISO.A5.30", "compliant", "low", "DR failover completed within the recovery time objective.", "Failover completed in 3h 10m against a 4h RTO."),
            _item("ISO.A6.3", "partially_compliant", "medium", "Awareness training lapsed this year after being completed in the prior cycle.", "", "Annual awareness training was not completed this year.", "Restart annual awareness training and track completion."),
            _item("ISO.A8.5", "compliant", "low", "MFA and access controls are operating for remote and privileged access.", "MFA is required for remote access."),
            _item("ISO.A8.13", "partially_compliant", "medium", "Backups run, but restore testing is not evidenced.", "", "Backup restore has not been tested.", "Run and record a backup restore test."),
            _na_item("ISO.A8.25", "Scope answer ISO.SCP.3 = No software development."),
        ],
    },
    INTERIM_DESCRIPTION: {
        "iso27001": [
            _item("ISO.A5.1", "compliant", "low", "The approved information security policy is reviewed every 12 months.", "Owner: Chief Information Security Officer. Approved by the board risk committee."),
            _item("ISO.A5.18", "partially_compliant", "medium", "The quarterly access review still skips two systems.", "The quarterly review covered 9 of 11 production systems.", "Two production systems remain outside the quarterly review.", "Extend the quarterly access review to every production system."),
            _item("ISO.A5.24", "partially_compliant", "medium", "The incident response plan exists but has never been tested.", "The plan exists but has not yet been tested.", "The incident response plan has not been exercised.", "Run and document an incident response tabletop exercise."),
            _item("ISO.A5.30", "compliant", "low", "DR failover completed within the recovery time objective.", "Failover completed in 3h 10m against a 4h RTO."),
            _item("ISO.A6.3", "partially_compliant", "medium", "Awareness training lapsed this year.", "", "Annual awareness training was not completed this year.", "Restart annual awareness training and track completion."),
            _item("ISO.A8.13", "partially_compliant", "medium", "Backups run, but restore testing is not evidenced.", "", "Backup restore has not been tested.", "Run and record a backup restore test."),
        ],
    },
}

FINDINGS = {
    "prior_consent": {
        "description": PRIOR_DESCRIPTION,
        "framework": "dpdpa",
        "requirement": "CH2.CONSENT.3",
        "title": "Driver app consent cannot be withdrawn",
        "severity": "high",
        "action_title": "Add a driver app consent withdrawal flow",
        "owner": "Rhea Kapoor",
        "target": 30,
    },
    "prior_supplier": {
        "description": PRIOR_DESCRIPTION,
        "framework": "iso27001",
        "requirement": "ISO.A5.19",
        "title": "Supplier security reviews are ad hoc",
        "severity": "high",
        "action_title": "Create the supplier security review calendar",
        "owner": "Arjun Mehta",
        "target": 45,
    },
    "current_consent": {
        "description": CURRENT_DESCRIPTION,
        "framework": "dpdpa",
        "requirement": "CH2.CONSENT.3",
        "title": "Driver app consent withdrawal is unavailable",
        "severity": "high",
        "action_title": "Deliver driver app consent withdrawal",
        "owner": "Rhea Kapoor",
        "target": -20,
    },
    "current_supplier": {
        "description": CURRENT_DESCRIPTION,
        "framework": "iso27001",
        "requirement": "ISO.A5.19",
        "title": "Supplier assurance remains unscheduled",
        "severity": "high",
        "action_title": "Implement a risk-based supplier assurance cycle",
        "owner": None,
        "target": 60,
    },
    "current_training": {
        "description": CURRENT_DESCRIPTION,
        "framework": "iso27001",
        "requirement": "ISO.A6.3",
        "title": "Annual security awareness training lapsed",
        "severity": "medium",
        "action_title": "Restart annual security awareness training",
        "owner": "Arjun Mehta",
        "target": 30,
    },
}


def _at(anchor: date, offset: int) -> datetime:
    return datetime.combine(anchor + timedelta(days=offset), datetime.min.time(), tzinfo=timezone.utc).replace(hour=9)


def _expect(response, status: int, what: str):
    if response.status_code != status:
        raise RuntimeError(f"{what}: expected {status}, got {response.status_code}: {response.text[:500]}")
    return response


def _context(assessment) -> None:
    assessment.context_answers = json.dumps(
        {
            "CTX.DATA.1": ["identity", "financial", "location"],
            "CTX.DATA.2": ["mobile_app", "physical_forms", "third_party_apis"],
            "CTX.DATA.3": "yes",
            "CTX.DATA.4": "yes",
            "CTX.DATA.4a": "Singapore parent group",
            "CTX.POSTURE.1": "part_time_shared",
            "CTX.POSTURE.2": "internal_policy_only",
            "CTX.POSTURE.3": "internal_only",
            "CTX.POSTURE.4": "yes_recently_updated",
            "CTX.RISK.1": ["handles_sensitive_personal_data"],
            "CTX.RISK.2": "10k_to_1m",
            "CTX.RISK.3": "no",
            "CTX.INIT.1": "customer_due_diligence",
            "CTX.INIT.2": "3_to_6_months",
            "CTX.INIT.3": "50k_to_150k",
        },
        sort_keys=True,
    )
    assessment.context_profile = json.dumps(
        {
            "risk_tier": "HIGH",
            "priority_chapters": ["chapter_2", "chapter_3", "chapter_4"],
            "likely_not_applicable": ["CH4.CHILD.1"],
            "industry_context": "Freight and warehousing operations rely on mobile location data and third-party platforms.",
            "timeline_pressure": "MEDIUM",
            "framing_notes": "Focus on mobile consent, supplier assurance, access reviews, incident readiness, and recovery evidence.",
            "sdf_candidate": False,
            "processes_children_data": False,
            "cross_border_transfers": True,
            "has_breach_response": True,
        },
        sort_keys=True,
    )


def _check_scope_values(framework_ids: list[str], answers: dict[str, str]) -> dict[str, str]:
    from app.frameworks.registry import FrameworkRegistry

    questions = {
        question.id: question
        for framework_id in framework_ids
        for question in FrameworkRegistry.get(framework_id).scope_questions
    }
    checked = dict(answers)
    for question_id, value in answers.items():
        question = questions.get(question_id)
        valid = {option["value"] for option in question.options} if question else set()
        if value not in valid:
            replacement = next(iter(valid), value)
            checked[question_id] = replacement
            print(f"scope option adjusted: {question_id}={value} -> {replacement}")
    return checked


def _save_scope(db, http, assessment, answers: dict[str, str], applicable: list[str] | None) -> None:
    answers = _check_scope_values(assessment.frameworks, answers)
    _expect(
        http.post(f"/assessments/{assessment.id}/scope/save", data=answers, follow_redirects=False),
        303,
        f"save scope {assessment.description}",
    )
    assessment.scope_answers = json.dumps(answers, sort_keys=True)
    if applicable is not None:
        assessment.applicable_requirements = json.dumps(sorted(applicable))
    _context(assessment)
    db.commit()
    db.expire_all()


def _question_text(question: dict) -> str:
    return " ".join(
        str(question.get(key, ""))
        for key in ("section", "section_title", "chapter_title", "topic", "question", "guidance")
    ).lower()


def _answer_questions(questionnaire: dict, *, prior: bool = False) -> tuple[list[dict], dict[str, Counter]]:
    questions = [
        question
        for section in questionnaire["sections"]
        for question in section["questions"]
        if question.get("status") != "skipped"
    ]
    questions.sort(key=lambda question: (question.get("section", ""), question["id"]))
    positions: defaultdict[str, int] = defaultdict(int)
    note_index = 0
    responses: list[dict] = []
    counts: dict[str, Counter] = defaultdict(Counter)
    for question in questions:
        domain = str(question.get("section", "other"))
        position = positions[domain]
        positions[domain] += 1
        text = _question_text(question)
        if any(word in text for word in STRONG_WORDS):
            answer = "fully_implemented" if position % 10 < 7 else "partially_implemented"
        elif any(word in text for word in WEAK_WORDS):
            cycle_position = position % 20
            if cycle_position < 3:
                answer = "fully_implemented"
            elif cycle_position < 10:
                answer = "partially_implemented"
            elif cycle_position < 15:
                answer = "planned"
            else:
                answer = "not_implemented"
        else:
            answer = ANSWER_CYCLE[position % len(ANSWER_CYCLE)]
        if prior:
            if answer == "fully_implemented" and position % 3 == 0:
                answer = "partially_implemented"
            elif answer == "partially_implemented" and position % 4 == 0:
                answer = "not_implemented"
        notes = None
        if answer != "fully_implemented":
            notes = NOTES[note_index % len(NOTES)]
            note_index += 1
        responses.append(
            {
                "question_id": question["id"],
                "answer": answer,
                "notes": notes,
                "confidence": "medium",
            }
        )
        counts[domain][answer] += 1
    return responses, counts


def _print_answer_table(label: str, counts: dict[str, Counter]) -> None:
    print(f"Questionnaire table: {label}")
    for domain in sorted(counts):
        values = ", ".join(f"{answer}={count}" for answer, count in sorted(counts[domain].items()))
        print(f"  {domain}: {values}")


def _save_bulk_questionnaire(db, http, assessment, *, prior: bool = False, followup_ready: bool = False) -> list[dict]:
    from app.services.question_engine import build_adaptive_questionnaire

    questionnaire = build_adaptive_questionnaire(assessment.id, db)
    responses, counts = _answer_questions(questionnaire, prior=prior)
    if followup_ready:
        questions_by_id = {
            question["id"]: question
            for section in questionnaire["sections"]
            for question in section["questions"]
        }
        framework_ids_by_question = {
            question_id: {
                control.get("framework_id", control.get("framework"))
                for control in (question.get("controls") or question.get("member_controls") or [])
            }
            for question_id, question in questions_by_id.items()
        }
        if not any(
            response["answer"] in {"partially_implemented", "not_implemented"}
            and "dpdpa" in framework_ids_by_question.get(response["question_id"], set())
            for response in responses
        ):
            parent = next(
                response
                for response in responses
                if "dpdpa" in framework_ids_by_question.get(response["question_id"], set())
                and any(word in _question_text(questions_by_id[response["question_id"]]) for word in WEAK_WORDS)
            )
            parent["answer"] = "partially_implemented"
            parent["notes"] = "Process exists but is not documented."
            counts[questions_by_id[parent["question_id"]].get("section", "other")]["fully_implemented"] -= 1
            counts[questions_by_id[parent["question_id"]].get("section", "other")]["partially_implemented"] += 1
    _expect(
        http.post(f"/api/assessments/{assessment.id}/responses", json={"responses": responses}),
        201,
        f"save questionnaire {assessment.description}",
    )
    _print_answer_table(assessment.description, counts)
    db.expire_all()
    return responses


def _save_nist_questionnaire(db, http, assessment) -> None:
    from app.services.question_engine import build_adaptive_questionnaire

    questionnaire = build_adaptive_questionnaire(assessment.id, db)
    sections = sorted(questionnaire["sections"], key=lambda section: section["section_id"])
    selected = sections[: max(1, (len(sections) + 1) // 2)]
    selected_ids = {
        question["id"]
        for section in selected
        for question in section["questions"]
        if question.get("status") != "skipped"
    }
    all_questions = {
        question["id"]: question
        for section in questionnaire["sections"]
        for question in section["questions"]
        if question.get("status") != "skipped"
    }
    ordered_questions = sorted(all_questions.values(), key=lambda question: (question.get("section", ""), question["id"]))
    responses, _ = _answer_questions({"sections": [{"questions": [all_questions[qid] for qid in sorted(selected_ids)], "section_id": "selected"}]})
    response_by_id = {response["question_id"]: response for response in responses}
    for section in selected:
        fields = {"section_id": section["section_id"]}
        for question in section["questions"]:
            if question.get("status") == "skipped":
                continue
            response = response_by_id[question["id"]]
            fields[f"answer_{question['id']}"] = response["answer"]
            if response["notes"]:
                fields[f"notes_{question['id']}"] = response["notes"]
        _expect(
            http.post(f"/assessments/{assessment.id}/questionnaire/save", data=fields),
            200,
            f"save NIST questionnaire section {section['section_id']}",
        )
    displayed_counts: dict[str, Counter] = defaultdict(Counter)
    for question in ordered_questions:
        if question["id"] in selected_ids:
            displayed_counts[question.get("section", "other")][response_by_id[question["id"]]["answer"]] += 1
    _print_answer_table(assessment.description, displayed_counts)
    db.expire_all()


def _followup_text(row) -> str | None:
    values = []
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    for value in values:
        if "driver app" in value.lower() or "roadmap" in value.lower():
            return value
    return next((value for value in values if value not in {row.question_id, row.assessment_id}), None)


def _seed_followups(db, http, assessment, responses: list[dict]) -> list[str]:
    weak = {response["question_id"] for response in responses if response["answer"] in {"partially_implemented", "not_implemented"}}
    from app.services.question_engine import build_adaptive_questionnaire

    questionnaire = build_adaptive_questionnaire(assessment.id, db)
    candidates = [
        question
        for section in questionnaire["sections"]
        for question in section["questions"]
        if question.get("status") != "skipped" and question["id"] in weak
    ]
    def framework_ids(question: dict) -> set[str]:
        return {
            control.get("framework_id", control.get("framework"))
            for control in (question.get("controls") or question.get("member_controls") or [])
        }

    dpdpa_question = next(
        (question for question in candidates if "dpdpa" in framework_ids(question)),
        None,
    )
    iso_question = next(
        (question for question in candidates if "iso27001" in framework_ids(question)),
        None,
    )
    if dpdpa_question is None or iso_question is None:
        raise RuntimeError("Could not find two weak-domain follow-up parents.")
    selected = (dpdpa_question, iso_question)
    saved_ids = []
    for question in selected:
        qid = question["id"]
        fields = {
            "section_id": question["section"],
            f"answer_{qid}": next(response["answer"] for response in responses if response["question_id"] == qid),
            f"notes_{qid}": "Follow-up answer recorded for the walkthrough.",
            f"followup_FU.{qid}.1": (
                "The driver app consent screen currently records the initial choice but does not expose withdrawal. "
                "The vendor roadmap has a consent settings item planned for the next release."
                if "dpdpa" in framework_ids(question)
                else "The supplier review owner is collecting current assurance records from the TMS vendor. "
                "The next quarterly review will use a documented checklist and escalation path."
            ),
        }
        try:
            _expect(
                http.post(f"/assessments/{assessment.id}/questionnaire/save", data=fields),
                200,
                f"save follow-up {qid}",
            )
            db.expire_all()
            from app.models.questionnaire import QuestionnaireResponse

            row = (
                db.query(QuestionnaireResponse)
                .filter(
                    QuestionnaireResponse.assessment_id == assessment.id,
                    QuestionnaireResponse.question_id == f"FU.{qid}.1",
                )
                .first()
            )
            if row is None or not _followup_text(row):
                raise RuntimeError("follow-up row was not readable after the route returned success")
            saved_ids.append(row.question_id)
        except Exception:
            db.rollback()
            print("follow-ups skipped: needs S0b (follow-up storage fix)")
            return []
    return saved_ids


def _content_type(path: Path) -> str:
    return {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png": "image/png",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }[path.suffix.lower()]


def _upload_bytes(db, http, assessment_id: str, path: Path, category: str, received: int | None, anchor: date, *, allow_skip: bool = False, skipped: list[str]) -> str | None:
    response = http.post(
        f"/api/assessments/{assessment_id}/documents",
        data={"category": category},
        files={"file": (path.name, path.read_bytes(), _content_type(path))},
    )
    if allow_skip and 400 <= response.status_code < 500:
        message = "xlsx skipped: not accepted by this build (S6-F1 not merged); this gap is intentional"
        print(message)
        skipped.append(message)
        db.rollback()
        return None
    _expect(response, 201, f"upload {path.name}")
    evidence_id = response.json()["id"]
    if received is not None:
        from app.models.evidence import Evidence
        from app.services import evidence as evidence_service

        db.expire_all()
        evidence = db.get(Evidence, evidence_id)
        version = evidence_service.current_version(db, evidence_id)
        received_at = _at(anchor, received)
        evidence.created_at = received_at
        version.created_at = received_at
        db.commit()
        db.expire_all()
    return evidence_id


def _map(http, evidence_id: str, assessment_id: str, framework_id: str, requirement_id: str, relevance: str) -> None:
    _expect(
        http.post(
            f"/api/evidence/{evidence_id}/uses",
            json={
                "assessment_id": assessment_id,
                "framework_id": framework_id,
                "requirement_id": requirement_id,
                "relevance": relevance,
            },
        ),
        201,
        f"map {evidence_id} to {requirement_id}",
    )


def _upload_set(db, http, assessment, paths: dict[str, Path], anchor: date, received: int, skipped: list[str]) -> dict[str, str]:
    specs = {
        "policy": ("security_policy", received, False),
        "ropa": ("processing_records", received, False),
        "access_q2": ("access_control_policy", received, False),
        "incident_plan": ("breach_procedure", received, False),
        "dr_report": ("business_continuity", received, False),
        "consent_screen": ("consent_form", received, False),
        "access_export": ("access_control_policy", received, True),
        "stale_access": ("access_control_policy", None, False),
    }
    evidence_ids = {}
    for key, (category, file_date, allow_skip) in specs.items():
        path = paths.get(key)
        if path is None:
            if key == "consent_screen":
                message = "png skipped: Pillow is unavailable in this environment"
                print(message)
                skipped.append(message)
            continue
        evidence_id = _upload_bytes(
            db,
            http,
            assessment.id,
            path,
            category,
            file_date,
            anchor,
            allow_skip=allow_skip,
            skipped=skipped,
        )
        if evidence_id:
            evidence_ids[key] = evidence_id
    return evidence_ids


def _map_common(http, assessment, evidence_ids: dict[str, str]) -> None:
    mappings = (
        ("policy", "iso27001", "ISO.A5.1", "primary"),
        ("policy", "dpdpa", "CH2.SECURITY.1", "supporting"),
        ("ropa", "dpdpa", "CH2.NOTICE.1", "primary"),
        ("access_q2", "iso27001", "ISO.A5.18", "primary"),
    )
    for key, framework_id, requirement_id, relevance in mappings:
        if key in evidence_ids:
            _map(http, evidence_ids[key], assessment.id, framework_id, requirement_id, relevance)


def _set_basis(db, assessment, anchor: date, start_offset: int, end_offset: int, cutoff_offset: int) -> None:
    from app.services import report_basis

    report_basis.update_report_basis(
        db,
        assessment,
        period_start=anchor + timedelta(days=start_offset),
        period_end=anchor + timedelta(days=end_offset),
        evidence_cutoff=anchor + timedelta(days=cutoff_offset),
        prepared_by=REVIEWER,
        reviewed_by=None,
        actor=f"consultant:{REVIEWER}",
    )
    db.commit()


def _approve(db, http, assessment, requirement_ids: list[str]) -> None:
    from app.models.conclusion import Conclusion

    db.expire_all()
    rows = {
        (row.framework_id, row.requirement_id): row
        for row in db.query(Conclusion).filter(Conclusion.assessment_id == assessment.id).all()
    }
    for requirement_id in requirement_ids:
        framework_id = "dpdpa" if requirement_id.startswith("CH") else "iso27001"
        conclusion = rows[(framework_id, requirement_id)]
        _expect(
            http.post(
                f"/api/assessments/{assessment.id}/conclusions/{conclusion.id}/approve",
                data={"expected_version": conclusion.version, "reviewer_name": REVIEWER},
            ),
            200,
            f"approve {requirement_id}",
        )
        db.expire_all()


def _create_finding(db, http, assessment, spec: dict, anchor: date) -> str:
    from app.models.conclusion import Conclusion
    from app.models.action import Action

    conclusion = (
        db.query(Conclusion)
        .filter(
            Conclusion.assessment_id == assessment.id,
            Conclusion.framework_id == spec["framework"],
            Conclusion.requirement_id == spec["requirement"],
        )
        .one()
    )
    data = {
        "conclusion_id": conclusion.id,
        "conclusion_version": conclusion.version,
        "title": spec["title"],
        "description": conclusion.gaps_identified,
        "severity": spec["severity"],
        "priority": 1 if spec["severity"] == "high" else 2,
        "action_title": spec["action_title"],
        "action_target_date": str(anchor + timedelta(days=spec["target"])),
        "reviewer_name": REVIEWER,
    }
    if spec["owner"]:
        data["action_owner"] = spec["owner"]
    response = _expect(
        http.post(f"/api/assessments/{assessment.id}/findings", data=data),
        200,
        f"create finding {spec['title']}",
    )
    finding_id = response.json()["finding_id"]
    db.expire_all()
    return db.query(Action).filter(Action.finding_id == finding_id).one().id


def _release_and_snapshot(db, http, assessment, skipped: list[str]) -> None:
    _expect(
        http.post(f"/api/assessments/{assessment.id}/release", data={"reviewer_name": REVIEWER}),
        200,
        f"release {assessment.description}",
    )
    for snapshot_type in ("workpaper", "gap_report"):
        response = http.post(
            f"/api/assessments/{assessment.id}/snapshots",
            data={"type": snapshot_type, "reviewer_name": REVIEWER},
        )
        if snapshot_type == "gap_report" and response.status_code == 503:
            message = "gap_report skipped: renderer unavailable"
            print(message)
            skipped.append(message)
            continue
        _expect(response, 200, f"generate {snapshot_type} snapshot")
        snapshot_id = response.json()["snapshot_id"]
        _expect(
            http.post(
                f"/api/assessments/{assessment.id}/snapshots/{snapshot_id}/issue",
                data={"reviewer_name": REVIEWER},
            ),
            200,
            f"issue {snapshot_type} snapshot",
        )
    db.expire_all()


def _backdate_hierarchy(db, client, engagement, assessment, created_at: datetime) -> None:
    client.created_at = created_at
    engagement.created_at = created_at
    assessment.created_at = created_at
    db.commit()
    db.expire_all()


def _purge_existing(db, upload_root: Path) -> None:
    from sqlalchemy import delete

    from app.models.client import Client
    from app.services import retention

    client = db.query(Client).filter(Client.name == DEMO_NAME).first()
    if client is None:
        return
    engagements = list(
        db.query(retention.Engagement)
        .filter(retention.Engagement.client_id == client.id)
        .all()
    )
    for engagement in engagements:
        engagement.status = retention.ARCHIVED_STATUS
        db.commit()
        plan = retention.build_purge_plan(db, engagement)
        for _table_name, model, clause in retention._purge_scopes(plan):
            db.execute(delete(model).where(clause).execution_options(synchronize_session=False))
        db.commit()
        for root in plan.blob_roots:
            path = (upload_root / root).resolve()
            upload_resolved = upload_root.resolve()
            if path == upload_resolved or upload_resolved not in path.parents:
                raise RuntimeError(f"refusing to purge path outside upload root: {path}")
            if path.exists():
                shutil.rmtree(path)
    db.execute(delete(Client).where(Client.id == client.id))
    db.commit()
    print("Purged existing Veldhara rows only")


def _check_registry() -> None:
    from app.frameworks.registry import FrameworkRegistry

    required = {
        "dpdpa": [item["requirement_id"] for item in ITEMS[CURRENT_DESCRIPTION]["dpdpa"]],
        "iso27001": [
            item["requirement_id"]
            for item in ITEMS[CURRENT_DESCRIPTION]["iso27001"]
            + ITEMS[INTERIM_DESCRIPTION]["iso27001"]
        ],
        "nist_csf": ["NIST.GV.PO.01"],
    }
    missing = []
    for framework_id, requirement_ids in required.items():
        framework = FrameworkRegistry.get_or_none(framework_id)
        controls = {control.id for control in framework.all_controls()} if framework else set()
        missing.extend(f"{framework_id}/{requirement_id}" for requirement_id in set(requirement_ids) if requirement_id not in controls)
    if missing:
        raise RuntimeError(f"Framework registry missing required ids: {', '.join(sorted(missing))}")


def _fake_analysis(**kwargs) -> dict:
    description = kwargs["description"]
    if description not in ITEMS:
        raise RuntimeError(f"No scripted analysis table for {description}")
    result = {}
    for framework_id in kwargs["framework_ids"]:
        result[framework_id] = {
            "parsed": {
                "executive_summary": f"{framework_id} synthetic walkthrough summary",
                "assessments": copy.deepcopy(ITEMS[description].get(framework_id, [])),
            },
            "raw": "{}",
        }
    return {"frameworks": result, "synthesis": None, "total_usage": {}}


def _create_engagement_b(db, http, client, anchor: date):
    from app.models.assessment import Assessment
    from app.models.engagement import Engagement

    response = _expect(
        http.post(
            "/engagements",
            data={
                "client_mode": "existing",
                "client_id": client.id,
                "engagement_name": "NIST CSF 2.0 baseline",
                "engagement_type": "gap_assessment",
                "description": NIST_DESCRIPTION,
                "selected_frameworks": ["nist_csf"],
            },
            follow_redirects=False,
        ),
        303,
        "create NIST engagement",
    )
    db.expire_all()
    engagement = db.query(Engagement).filter(Engagement.name == "NIST CSF 2.0 baseline").one()
    assessment = db.query(Assessment).filter(Assessment.engagement_id == engagement.id).one()
    engagement.created_at = _at(anchor, -14)
    assessment.created_at = _at(anchor, -14)
    db.commit()
    db.expire_all()
    return engagement, assessment, response


def _seed(db, http, anchor: date) -> dict[str, str]:
    from scripts.demo.files import generate_demo_files
    from scripts.seed_test_companies import _add_assessment_to_engagement, _create_hierarchy

    upload_root = Path(os.environ["UPLOAD_DIR"])
    demo_files_dir = upload_root / "demo_files"
    if demo_files_dir.exists():
        shutil.rmtree(demo_files_dir)
    paths = generate_demo_files(demo_files_dir)
    skipped: list[str] = []
    print("Generated deterministic demo files")

    client, engagement_a, prior, _ = _create_hierarchy(
        db,
        http,
        name=DEMO_NAME,
        industry="other",
        size="large",
        engagement_name="FY2026-27 privacy and security assessment",
        frameworks=["dpdpa", "iso27001"],
        description=PRIOR_DESCRIPTION,
    )
    _backdate_hierarchy(db, client, engagement_a, prior, _at(anchor, -330))
    print(f"Created client and engagement A: {client.id} {engagement_a.id}")

    common_scope = {
        "SCP.1": "yes",
        "SCP.2": "no",
        "SCP.3": "possibly",
        "SCP.4": "both",
        "SCP.5": "yes",
        "SCP.6": "no",
        "ISO.SCP.1": "full_org",
        "ISO.SCP.2": "yes",
        "ISO.SCP.3": "no",
        "ISO.SCP.4": "yes_datacenter",
    }
    _save_scope(db, http, prior, common_scope, PRIOR_IDS)
    prior_files = _upload_set(db, http, prior, paths, anchor, -325, skipped)
    _map_common(http, prior, prior_files)
    _save_bulk_questionnaire(db, http, prior, prior=True)
    _expect(
        http.post(f"/api/assessments/{prior.id}/analyze", json={"reason": "document_led", "reviewer_name": REVIEWER}),
        200,
        "analyze prior",
    )
    _set_basis(db, prior, anchor, -485, -395, -320)
    _approve(db, http, prior, PRIOR_IDS)
    for key in ("prior_consent", "prior_supplier"):
        _create_finding(db, http, prior, FINDINGS[key], anchor)
    _release_and_snapshot(db, http, prior, skipped)
    from app.models.audit_event import AuditEvent
    from app.models.report_snapshot import ReportSnapshot

    release_event = (
        db.query(AuditEvent)
        .filter(AuditEvent.action == "assessment.released", AuditEvent.entity_id == prior.id)
        .order_by(AuditEvent.id.desc())
        .first()
    )
    if release_event:
        release_event.created_at = _at(anchor, -290)
    for snapshot in db.query(ReportSnapshot).filter(ReportSnapshot.assessment_id == prior.id).all():
        snapshot.generated_at = _at(anchor, -290)
    db.commit()
    print(f"Seeded and released PRIOR: {prior.id}")

    current = _add_assessment_to_engagement(
        db,
        engagement=engagement_a,
        client=client,
        description=CURRENT_DESCRIPTION,
        framework_ids=["dpdpa", "iso27001"],
        created_at=_at(anchor, -45),
    )
    current_scope = dict(common_scope)
    _save_scope(db, http, current, current_scope, PRIOR_IDS)
    current_files = _upload_set(db, http, current, paths, anchor, -40, skipped)
    _map_common(http, current, current_files)
    for key, framework_id, requirement_id, relevance in (
        ("incident_plan", "iso27001", "ISO.A5.24", "primary"),
        ("dr_report", "iso27001", "ISO.A5.30", "primary"),
        ("consent_screen", "dpdpa", "CH2.CONSENT.3", "primary"),
        ("access_export", "iso27001", "ISO.A5.18", "supporting"),
    ):
        if key in current_files:
            _map(http, current_files[key], current.id, framework_id, requirement_id, relevance)
    current_responses = _save_bulk_questionnaire(db, http, current, followup_ready=True)
    print("Attempting real follow-up save route")
    followup_ids = _seed_followups(db, http, current, current_responses)
    note = "follow-ups are stored but visible only if S0b also renders stored follow-ups"
    print(note)
    if note not in skipped:
        skipped.append(note)
    _expect(
        http.post(f"/api/assessments/{current.id}/analyze", json={"reason": "document_led", "reviewer_name": REVIEWER}),
        200,
        "analyze current",
    )
    _set_basis(db, current, anchor, -120, -30, -20)
    _approve(db, http, current, PRIOR_IDS)
    for key in ("current_consent", "current_supplier", "current_training"):
        _create_finding(db, http, current, FINDINGS[key], anchor)
    _release_and_snapshot(db, http, current, skipped)
    print(f"Seeded and released CURRENT: {current.id}")

    interim = _add_assessment_to_engagement(
        db,
        engagement=engagement_a,
        client=client,
        description=INTERIM_DESCRIPTION,
        framework_ids=["iso27001"],
        created_at=_at(anchor, -10),
    )
    interim_scope = {key: value for key, value in common_scope.items() if key.startswith("ISO.")}
    _save_scope(db, http, interim, interim_scope, INTERIM_IDS)
    _save_bulk_questionnaire(db, http, interim)
    _expect(
        http.post(f"/api/assessments/{interim.id}/analyze", json={"reason": "document_led", "reviewer_name": REVIEWER}),
        200,
        "analyze interim",
    )
    _set_basis(db, interim, anchor, -90, -15, -10)
    _approve(db, http, interim, ["ISO.A5.1", "ISO.A5.30", "ISO.A8.13"])
    print(f"Seeded INTERIM review queue: {interim.id}")

    engagement_b, nist, _ = _create_engagement_b(db, http, client, anchor)
    nist_scope = {
        "NIST.SCP.1": "no",
        "NIST.SCP.2": "tier2",
        "NIST.SCP.3": "no",
        "NIST.SCP.4": "current_only",
    }
    _save_scope(db, http, nist, nist_scope, None)
    nist_files = _upload_set(db, http, nist, {key: paths[key] for key in ("policy", "consent_screen") if key in paths}, anchor, -12, skipped)
    if "policy" in nist_files:
        _map(http, nist_files["policy"], nist.id, "nist_csf", "NIST.GV.PO.01", "primary")
    _save_nist_questionnaire(db, http, nist)
    print(f"Seeded NIST early state: {nist.id}")

    from app.services import assessment_stage

    stages = {
        "prior": assessment_stage.stage(db, prior),
        "current": assessment_stage.stage(db, current),
        "interim": assessment_stage.stage(db, interim),
        "nist": assessment_stage.stage(db, nist),
    }
    print("Stages:")
    for key, stage in stages.items():
        print(f"  {key}: {stage.stage} ({stage.label}, {stage.note})")
    compare = http.get(f"/assessments/{current.id}/compare/{prior.id}")
    _expect(compare, 200, "assessment comparison")
    print("Comparison smoke check: 200")

    from app.models.conclusion import Conclusion

    print("Manifest:")
    print(f"  client: {client.id}")
    print(f"  engagement_a: {engagement_a.id}")
    print(f"  engagement_b: {engagement_b.id}")
    print(f"  prior: {prior.id}")
    print(f"  current: {current.id}")
    print(f"  interim: {interim.id}")
    print(f"  nist: {nist.id}")
    for label, assessment in (("prior", prior), ("current", current), ("interim", interim), ("nist", nist)):
        states = Counter(row.outcome for row in db.query(Conclusion).filter(Conclusion.assessment_id == assessment.id).all())
        print(f"  conclusions {label}: {dict(sorted(states.items()))}")
    print(f"  followups stored: {len(followup_ids)}")
    print("URLs:")
    urls = (
        ("/", "dashboard"),
        (f"/engagements/{engagement_a.id}", "engagement A"),
        (f"/assessments/{current.id}", "current overview"),
        (f"/assessments/{current.id}?tab=scope", "current scope"),
        (f"/assessments/{current.id}/evidence", "current evidence"),
        (f"/assessments/{current.id}?tab=questionnaire", "current questionnaire"),
        (f"/assessments/{current.id}/conclusions", "current conclusions"),
        (f"/assessments/{interim.id}/conclusions", "interim review queue"),
        (f"/assessments/{current.id}/findings", "current findings"),
        (f"/assessments/{current.id}?tab=report", "current report"),
        (f"/assessments/{current.id}/report-summary", "current report summary"),
        (f"/assessments/{current.id}/snapshots", "current versions"),
        (f"/assessments/{current.id}/compare/{prior.id}", "comparison"),
        (f"/assessments/{prior.id}/snapshots", "prior versions"),
        (f"/assessments/{nist.id}", "NIST overview"),
        (f"/assessments/{nist.id}?tab=questionnaire", "NIST questionnaire"),
        (f"/assessments/{current.id}/rfi", "current RFI"),
    )
    for url, label in urls:
        print(f"  {url}  # {label}")
    print("Skipped:")
    if skipped:
        for message in dict.fromkeys(skipped):
            print(f"  {message}")
    else:
        print("  none")
    return {
        "client": client.id,
        "engagement_a": engagement_a.id,
        "engagement_b": engagement_b.id,
        "prior": prior.id,
        "current": current.id,
        "interim": interim.id,
        "nist": nist.id,
    }


def _parse_args(argv: list[str] | None) -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.environ.get("DEMO_DB", "data/demo.db"))
    args = parser.parse_args(argv)
    db_path = Path(args.db).expanduser().resolve()
    if db_path.name == "dpdpa.db" or "demo" not in db_path.name:
        raise SystemExit("refusing to run: the demo DB file name must contain 'demo' and must not be dpdpa.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def main(argv: list[str] | None = None) -> int:
    db_path = _parse_args(argv)
    upload_root = db_path.parent / "uploads" / "demo"
    os.environ["OPENROUTER_KEY"] = ""
    os.environ["ANALYSIS_PIPELINE_VERSION"] = "v1"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["UPLOAD_DIR"] = str(upload_root)

    from alembic import command
    from alembic.config import Config

    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(config, "head")
    print(f"Database ready: {db_path}")

    import app.models  # noqa: F401
    from fastapi.testclient import TestClient
    from app.config import settings
    from app.database import SessionLocal, get_db
    from app.main import app
    from app.services import document_processor, llm_client
    from app.routers import analysis

    if settings.openrouter_key:
        settings.openrouter_key = ""
        print("OPENROUTER_KEY cleared in process; this seed uses no LLM")

    def no_llm(*_args, **_kwargs):
        raise AssertionError("The demo must never call the LLM.")

    def vision_stub(_image_data: str, _media_type: str) -> str:
        return "VISIBLE TEXT: I agree to location tracking. SUMMARY: The screen shows an initial consent button and no withdrawal option."

    db = SessionLocal()
    anchor = date.today()
    try:
        with patch.object(llm_client, "_get_client", no_llm), patch.object(document_processor, "_call_claude_vision", vision_stub), patch.object(analysis, "run_multi_framework_analysis", _fake_analysis):
            if settings.openrouter_key or llm_client._get_client is not no_llm or document_processor._call_claude_vision is not vision_stub or analysis.run_multi_framework_analysis is not _fake_analysis:
                print("refusing to run: LLM stub not active")
                return 2

            def override_get_db():
                yield db

            app.dependency_overrides[get_db] = override_get_db
            try:
                with TestClient(app) as http:
                    _check_registry()
                    _purge_existing(db, upload_root)
                    _seed(db, http, anchor)
            finally:
                app.dependency_overrides.pop(get_db, None)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
