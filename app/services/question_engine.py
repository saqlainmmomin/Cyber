"""
Question Selection Engine — builds an adaptive questionnaire from desk review findings,
context profile, and industry-specific question banks.

The engine merges two question sources:
  1. Base DPDPA questions (41 requirements from questionnaire.py)
  2. Industry-specific questions (from industry_questions.py)

Desk review findings modulate which questions appear:
  - Skip: strong document evidence → question skipped with reason
  - Deepen: signals/absences found → extra context shown, follow-up probes enabled
  - Add: signal flags → targeted questions injected

The output is a list of QuestionSets (sections) ready for the web UI.
"""

import json

from sqlalchemy.orm import Session

from app.dpdpa.framework import get_all_requirements
from app.dpdpa.industry_questions import get_industry_questions
from app.dpdpa.questionnaire import ANSWER_OPTIONS, _GUIDANCE_TEXT, _QUESTION_TEXT, build_questionnaire
from app.models.assessment import Assessment
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary


def build_adaptive_questionnaire(assessment_id: str, db: Session) -> dict:
    """
    Build an adaptive questionnaire combining base DPDPA + industry questions,
    modulated by desk review findings and context profile.

    Returns:
        {
            "sections": [...],         # Ordered list of question sections
            "stats": {                  # Summary stats for UI
                "total_questions": int,
                "skipped_questions": int,
                "deepened_questions": int,
                "industry_questions": int,
            }
        }
    """
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    context_profile = json.loads(assessment.context_profile) if assessment.context_profile else None
    industry = assessment.industry or "other"

    # Load desk review data
    desk_data = _load_desk_review_data(assessment_id, db)

    # 1. Build base DPDPA questions (41 requirements, context-weighted)
    base_questions = build_questionnaire(context_profile=context_profile)

    # 2. Get industry-specific questions
    industry_bank = get_industry_questions(industry)
    industry_qs = industry_bank["questions"]

    # 3. Apply desk review modulation to base questions
    modulated_base = []
    skipped_count = 0
    deepened_count = 0

    for q in base_questions:
        mod = _modulate_question(q, desk_data)
        if mod["status"] == "skipped":
            skipped_count += 1
        elif mod["status"] == "deepened":
            deepened_count += 1
        modulated_base.append(mod)

    # 4. Apply desk review modulation to industry questions
    modulated_industry = []
    for iq in industry_qs:
        mod = _modulate_industry_question(iq, desk_data, context_profile)
        if mod["status"] == "skipped":
            skipped_count += 1
        elif mod["status"] == "deepened":
            deepened_count += 1
        modulated_industry.append(mod)

    # 5. Ensure requirement coverage — every requirement must appear in at least one non-skipped question
    covered_reqs = set()
    for q in modulated_base:
        if q["status"] != "skipped":
            covered_reqs.add(q["id"])
    for q in modulated_industry:
        if q["status"] != "skipped":
            covered_reqs.update(q.get("maps_to", []))

    all_req_ids = {r["id"] for r in get_all_requirements()}
    uncovered = all_req_ids - covered_reqs

    # Un-skip any base question whose requirement is uncovered
    for q in modulated_base:
        if q["status"] == "skipped" and q["id"] in uncovered:
            q["status"] = "active"
            q["skip_reason"] = None
            q["desk_review_note"] = "Reinstated — no other question covers this requirement."
            uncovered.discard(q["id"])
            skipped_count -= 1

    # 6. Group into sections
    sections = _build_sections(modulated_base, modulated_industry)

    return {
        "sections": sections,
        "stats": {
            "total_questions": len(modulated_base) + len(modulated_industry) - skipped_count,
            "skipped_questions": skipped_count,
            "deepened_questions": deepened_count,
            "industry_questions": len(modulated_industry),
        },
    }


def _load_desk_review_data(assessment_id: str, db: Session) -> dict:
    """Load desk review findings into a structured dict for question modulation."""
    dr_summary = (
        db.query(DeskReviewSummary)
        .filter(
            DeskReviewSummary.assessment_id == assessment_id,
            DeskReviewSummary.status == "completed",
        )
        .first()
    )

    if not dr_summary:
        return {"coverage": {}, "signals": [], "absences": [], "evidence": {}, "signal_flags": set(), "absence_req_ids": set()}

    coverage = json.loads(dr_summary.coverage_summary) if dr_summary.coverage_summary else {}

    findings = (
        db.query(DeskReviewFinding)
        .filter(DeskReviewFinding.assessment_id == assessment_id)
        .all()
    )

    evidence = {}  # requirement_id -> list of evidence findings
    signals = []
    absences = []

    for f in findings:
        if f.finding_type == "evidence" and f.requirement_id:
            evidence.setdefault(f.requirement_id, []).append({
                "content": f.content,
                "source_quote": f.source_quote,
                "source_location": f.source_location,
                "severity": f.severity,
            })
        elif f.finding_type == "signal":
            signals.append({
                "content": f.content,
                "severity": f.severity,
                "requirement_id": f.requirement_id,
            })
        elif f.finding_type == "absence":
            absences.append({
                "content": f.content,
                "requirement_id": f.requirement_id,
            })

    # Extract signal flag types from signal content for matching against question deepen_if
    signal_flags = set()
    for s in signals:
        content_lower = s["content"].lower()
        if "gdpr" in content_lower or "copy" in content_lower:
            signal_flags.add("gdpr_copy_paste")
        if "template" in content_lower or "generic" in content_lower:
            signal_flags.add("template_artifacts")
        if "buried" in content_lower or "consent" in content_lower and "terms" in content_lower:
            signal_flags.add("buried_consent")
        if "scope" in content_lower or "gap" in content_lower:
            signal_flags.add("scope_gaps")
        if "timeline" in content_lower or "missing" in content_lower and "date" in content_lower:
            signal_flags.add("missing_timelines")

    return {
        "coverage": coverage,
        "signals": signals,
        "absences": absences,
        "evidence": evidence,
        "signal_flags": signal_flags,
        "absence_req_ids": {a["requirement_id"] for a in absences if a["requirement_id"]},
    }


def _modulate_question(question: dict, desk_data: dict) -> dict:
    """Apply desk review modulation to a base DPDPA question."""
    q = {**question, "source": "base", "status": "active", "skip_reason": None, "desk_review_note": None,
         "desk_review_evidence": None, "follow_up_enabled": False, "maps_to": [question["id"]]}

    req_id = question["id"]
    coverage = desk_data["coverage"]

    # Skip if strong coverage found in desk review
    if coverage.get(req_id) == "adequate":
        evidence_items = desk_data["evidence"].get(req_id, [])
        if evidence_items:
            q["status"] = "skipped"
            q["skip_reason"] = "Covered by document evidence"
            q["desk_review_evidence"] = evidence_items
            return q

    # Deepen if absence or signal found for this requirement
    if req_id in desk_data["absence_req_ids"]:
        q["status"] = "deepened"
        q["desk_review_note"] = _build_absence_note(req_id, desk_data["absences"])
        q["follow_up_enabled"] = True

    for signal in desk_data["signals"]:
        if signal.get("requirement_id") == req_id:
            q["status"] = "deepened"
            q["desk_review_note"] = q.get("desk_review_note") or ""
            if q["desk_review_note"]:
                q["desk_review_note"] += " "
            q["desk_review_note"] += f"Signal detected: {signal['content']}"
            q["follow_up_enabled"] = True

    # Show evidence context even for active questions
    evidence_items = desk_data["evidence"].get(req_id, [])
    if evidence_items and q["status"] == "active":
        q["desk_review_evidence"] = evidence_items
        q["desk_review_note"] = "Your documents mention this area — please confirm the current state."

    return q


def _modulate_industry_question(question: dict, desk_data: dict, context_profile: dict | None) -> dict:
    """Apply desk review modulation to an industry-specific question."""
    q = {
        "id": question["id"],
        "question": question["text"],
        "guidance": question["guidance"],
        "criticality": question["criticality"],
        "category": question["category"],
        "maps_to": question["maps_to"],
        "answer_options": ANSWER_OPTIONS,
        "source": "industry",
        "status": "active",
        "skip_reason": None,
        "desk_review_note": None,
        "desk_review_evidence": None,
        "follow_up_enabled": False,
        "follow_up_triggers": question.get("follow_up_triggers", {}),
        "relevance_weight": 1.0,
        "context_note": None,
        "skip_if": None,
        "chapter": None,
        "chapter_title": "Industry-Specific",
        "section": question["category"],
        "section_title": _category_title(question["category"]),
        "section_ref": "",
    }

    # Check skip_if conditions
    skip_conditions = question.get("skip_if", {})
    desk_coverage = skip_conditions.get("desk_review_coverage", {})
    if desk_coverage:
        all_adequate = all(
            desk_data["coverage"].get(req_id) == status
            for req_id, status in desk_coverage.items()
        )
        if all_adequate and desk_coverage:
            q["status"] = "skipped"
            q["skip_reason"] = "Covered by document evidence for mapped requirements"
            return q

    # Check deepen_if conditions
    deepen_conditions = question.get("deepen_if", {})

    # Deepen if signal flags match
    flag_triggers = deepen_conditions.get("signal_flags", [])
    if flag_triggers and desk_data["signal_flags"] & set(flag_triggers):
        matched = desk_data["signal_flags"] & set(flag_triggers)
        q["status"] = "deepened"
        q["desk_review_note"] = f"Document review flagged: {', '.join(matched)}. Please provide specific details."
        q["follow_up_enabled"] = True

    # Deepen if absence findings match
    absence_triggers = deepen_conditions.get("absence_findings", [])
    if absence_triggers:
        matched_absences = set(absence_triggers) & desk_data["absence_req_ids"]
        if matched_absences:
            q["status"] = "deepened"
            note = _build_absence_note_for_reqs(matched_absences, desk_data["absences"])
            q["desk_review_note"] = (q["desk_review_note"] or "") + (" " if q["desk_review_note"] else "") + note
            q["follow_up_enabled"] = True

    # Attach evidence for mapped requirements
    evidence_items = []
    for req_id in question["maps_to"]:
        evidence_items.extend(desk_data["evidence"].get(req_id, []))
    if evidence_items:
        q["desk_review_evidence"] = evidence_items
        if q["status"] == "active":
            q["desk_review_note"] = "Your documents contain relevant information — please confirm the current implementation."

    return q


def _build_absence_note(req_id: str, absences: list[dict]) -> str:
    """Build a note about missing evidence for a requirement."""
    relevant = [a for a in absences if a["requirement_id"] == req_id]
    if relevant:
        return f"No evidence found in documents: {relevant[0]['content']}"
    return "No evidence found in uploaded documents for this requirement."


def _build_absence_note_for_reqs(req_ids: set, absences: list[dict]) -> str:
    """Build a note about missing evidence for multiple requirements."""
    notes = []
    for a in absences:
        if a["requirement_id"] in req_ids:
            notes.append(a["content"])
    if notes:
        return f"Missing from documents: {notes[0]}"
    return "No evidence found in uploaded documents for related requirements."


def _category_title(category: str) -> str:
    """Convert category slug to display title."""
    titles = {
        "data_isolation": "Data Isolation",
        "data_lifecycle": "Data Lifecycle",
        "api_data_sharing": "API & Data Sharing",
        "cloud_infra": "Cloud Infrastructure",
        "consent_ux": "Consent in Product",
        "breach_response": "Breach Response",
        "rights_management": "Rights Management",
        "analytics": "Analytics & Tracking",
        "data_governance": "Data Governance",
        "vendor_management": "Vendor Management",
        "people": "People & Training",
        "purpose_limitation": "Purpose Limitation",
    }
    return titles.get(category, category.replace("_", " ").title())


def _build_sections(base_questions: list[dict], industry_questions: list[dict]) -> list[dict]:
    """
    Group questions into ordered sections.

    Base DPDPA questions are grouped by chapter+section (existing behavior).
    Industry questions are grouped by category into a separate "Industry-Specific" chapter.
    Skipped questions are included but marked — the UI decides whether to show them.
    """
    sections = {}

    # Base questions — grouped by chapter.section
    for q in base_questions:
        sid = f"{q['chapter']}.{q['section']}"
        if sid not in sections:
            sections[sid] = {
                "section_id": sid,
                "chapter_title": q["chapter_title"],
                "section_title": q["section_title"],
                "source": "base",
                "questions": [],
            }
        sections[sid]["questions"].append(q)

    # Industry questions — grouped by category
    for q in industry_questions:
        sid = f"industry.{q['category']}"
        if sid not in sections:
            sections[sid] = {
                "section_id": sid,
                "chapter_title": "Industry-Specific",
                "section_title": q["section_title"],
                "source": "industry",
                "questions": [],
            }
        sections[sid]["questions"].append(q)

    # Order: base sections first (by chapter order), then industry sections
    base_order = [s for s in sections.values() if s["source"] == "base"]
    industry_order = [s for s in sections.values() if s["source"] == "industry"]

    return base_order + industry_order
