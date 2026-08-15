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

from app.services.tier_engine import assign_tiers, compute_tier_stats

from app.dpdpa.framework import get_all_requirements
from app.dpdpa.industry_questions import get_industry_questions
from app.dpdpa.questionnaire import ANSWER_OPTIONS, _GUIDANCE_TEXT, _QUESTION_TEXT, build_questionnaire
from app.frameworks.questionnaire_builder import build_multi_questionnaire
from app.models.assessment import Assessment
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary

_DOMAIN_GROUP_TITLES: dict[str, str] = {
    "data_protection": "Data Protection",
    "consent_rights": "Consent & Individual Rights",
    "governance": "Governance & Accountability",
    "cross_border": "Cross-Border Transfers",
    "incident_response": "Incident Response & Breach Notification",
    "access_control": "Access Control",
    "cryptography": "Cryptography & Key Management",
    "asset_management": "Asset Management",
    "risk_management": "Risk Management",
    "supplier_relationships": "Supplier & Third-Party Management",
    "business_continuity": "Business Continuity",
    "compliance": "Compliance & Audit",
    "physical_security": "Physical Security",
    "network_security": "Network Security",
    "vulnerability_management": "Vulnerability Management",
    "identity_management": "Identity & Access Management",
    "security_monitoring": "Security Monitoring & Logging",
    "children_vulnerable": "Children & Vulnerable Individuals",
    "security": "Information Security Controls",
    "other": "Other Controls",
}


def _build_multi_framework_questionnaire(assessment: Assessment, framework_ids: list[str]) -> dict:
    """
    Build and return a questionnaire for multi-framework (non-DPDPA-only) assessments
    using the Unified Control Cluster engine. Questions are normalised into the same
    shape expected by section_questions.html.
    """
    context_profile = json.loads(assessment.context_profile) if assessment.context_profile else None
    excluded: set[str] | None = None
    if assessment.applicable_requirements:
        try:
            applicable = set(json.loads(assessment.applicable_requirements))
            excluded = None  # UCC engine uses include-list differently — pass None for now
        except (json.JSONDecodeError, TypeError):
            pass

    raw_questions = build_multi_questionnaire(framework_ids, excluded_controls=excluded, context_profile=context_profile)

    # Normalise UCC question dicts into the template-compatible shape
    normalised: list[dict] = []
    for ucc_q in raw_questions:
        normalised.append({
            # Identity
            "id": ucc_q["cluster_id"],
            "cluster_id": ucc_q["cluster_id"],
            # Display
            "question": ucc_q["primary_question"],
            "guidance": ucc_q.get("primary_guidance", ""),
            "criticality": ucc_q.get("criticality", "medium"),
            # Section grouping
            "chapter": ucc_q.get("domain_group", "other"),
            "chapter_title": _DOMAIN_GROUP_TITLES.get(ucc_q.get("domain_group", "other"), "Controls"),
            "section": ucc_q.get("domain_group", "other"),
            "section_title": _DOMAIN_GROUP_TITLES.get(ucc_q.get("domain_group", "other"), "Controls"),
            "section_ref": "",
            # Multi-framework metadata (shown in template if template uses them)
            "frameworks_covered": ucc_q.get("frameworks_covered", framework_ids),
            "follow_ups": ucc_q.get("follow_ups", []),
            # Status fields — no desk-review modulation on multi-framework path yet
            "status": "active",
            "skip_reason": None,
            "desk_review_note": ucc_q.get("context_note"),
            "desk_review_evidence": None,
            "tier": "standard",
            "source": "base",
            "follow_up_enabled": bool(ucc_q.get("follow_ups")),
            "maps_to": [c["control_id"] for c in ucc_q.get("controls", [])],
            # Pre-fill fields (unused on multi-framework path for now)
            "pre_fill_answer": None,
            "pre_fill_confidence": None,
            "pre_fill_source": None,
            "pre_fill_evidence_summary": None,
            "skip_if": None,
            "relevance_weight": ucc_q.get("relevance_weight", 1.0),
            "context_note": ucc_q.get("context_note"),
            "answer_options": ANSWER_OPTIONS,
        })

    # Group into sections by domain_group
    sections: dict[str, dict] = {}
    for q in normalised:
        sid = q["section"]
        if sid not in sections:
            sections[sid] = {
                "section_id": sid,
                "chapter_title": q["chapter_title"],
                "section_title": q["section_title"],
                "source": "base",
                "questions": [],
            }
        sections[sid]["questions"].append(q)

    section_list = list(sections.values())
    total = len(normalised)

    return {
        "sections": section_list,
        "stats": {
            "total_questions": total,
            "skipped_questions": 0,
            "pre_filled_questions": 0,
            "inferred_questions": 0,
            "deepened_questions": 0,
            "industry_questions": 0,
            "tier_counts": {"standard": total, "deep": 0, "light": 0},
        },
    }


def _load_screening_data(assessment: Assessment) -> dict:
    """Load screening inferences from the assessment if available."""
    if not assessment.screening_results or assessment.screening_status != "completed":
        return {}
    try:
        return json.loads(assessment.screening_results)
    except (json.JSONDecodeError, TypeError):
        return {}


def build_adaptive_questionnaire(assessment_id: str, db: Session) -> dict:
    """
    Build an adaptive questionnaire combining base questions, modulated by desk
    review findings and context profile.

    For DPDPA-only assessments: uses the legacy 41-requirement engine with
    industry questions and full desk-review modulation.

    For multi-framework (or non-DPDPA) assessments: uses build_multi_questionnaire
    which resolves Unified Control Clusters across the selected frameworks.

    Returns:
        {
            "sections": [...],
            "stats": {...}
        }
    """
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    # Determine selected frameworks — default to DPDPA for legacy assessments
    selected_frameworks: list[str] = ["dpdpa"]
    if assessment.selected_frameworks:
        try:
            selected_frameworks = json.loads(assessment.selected_frameworks)
        except (json.JSONDecodeError, TypeError):
            pass

    # Route multi-framework assessments to the UCC-based engine
    is_dpdpa_only = selected_frameworks == ["dpdpa"] or selected_frameworks == []
    if not is_dpdpa_only:
        return _build_multi_framework_questionnaire(assessment, selected_frameworks)


    context_profile = json.loads(assessment.context_profile) if assessment.context_profile else None
    industry = assessment.industry or "other"
    risk_tier = context_profile.get("risk_tier", "MEDIUM") if context_profile else "MEDIUM"
    screening_data = _load_screening_data(assessment)

    # Applicable requirements from scope (None = all requirements)
    applicable_req_ids: set[str] | None = None
    if assessment.applicable_requirements:
        applicable_req_ids = set(json.loads(assessment.applicable_requirements))

    # Load desk review data
    desk_data = _load_desk_review_data(assessment_id, db)

    # 1. Build base DPDPA questions (41 requirements, context-weighted)
    base_questions = build_questionnaire(context_profile=context_profile)

    # 2. Get industry-specific questions
    industry_bank = get_industry_questions(industry)
    industry_qs = industry_bank["questions"]

    # 3. Apply desk review modulation to base questions
    # Also skip questions whose requirements are outside the scoped applicable set
    modulated_base = []
    skipped_count = 0
    deepened_count = 0
    pre_filled_count = 0
    inferred_count = 0

    for q in base_questions:
        # Skip questions outside scope before desk-review modulation
        if applicable_req_ids is not None and q["id"] not in applicable_req_ids:
            mod = {**q, "status": "skipped", "skip_reason": "Not applicable per scope definition"}
            skipped_count += 1
            modulated_base.append(mod)
            continue
        mod = _modulate_question(q, desk_data)
        # Apply screening modulation after desk review (screening only touches still-active questions)
        if screening_data and mod["status"] == "active":
            mod = _apply_screening(mod, screening_data)
        if mod["status"] == "skipped":
            skipped_count += 1
        elif mod["status"] == "deepened":
            deepened_count += 1
        elif mod["status"] == "pre_filled":
            if mod.get("pre_fill_source") == "inferred":
                inferred_count += 1
            else:
                pre_filled_count += 1
        modulated_base.append(mod)

    # 4. Apply desk review modulation to industry questions
    modulated_industry = []
    for iq in industry_qs:
        mod = _modulate_industry_question(iq, desk_data, context_profile)
        if mod["status"] == "skipped":
            skipped_count += 1
        elif mod["status"] == "deepened":
            deepened_count += 1
        elif mod["status"] == "pre_filled":
            pre_filled_count += 1
        modulated_industry.append(mod)

    # 5. Ensure requirement coverage — every applicable requirement must appear in at least one non-skipped question
    # pre_filled questions count as covered since they present the control to the user for confirmation
    covered_reqs = set()
    for q in modulated_base:
        if q["status"] not in ("skipped",):
            covered_reqs.add(q["id"])
    for q in modulated_industry:
        if q["status"] != "skipped":
            covered_reqs.update(q.get("maps_to", []))

    all_req_ids = {r["id"] for r in get_all_requirements()}
    # Only check coverage for applicable requirements
    required_req_ids = applicable_req_ids if applicable_req_ids is not None else all_req_ids
    uncovered = required_req_ids - covered_reqs

    # Un-skip any base question whose requirement is uncovered and in scope
    for q in modulated_base:
        if q["status"] == "skipped" and q["id"] in uncovered:
            # Don't reinstate questions that were excluded by scope
            if q.get("skip_reason") == "Not applicable per scope definition":
                continue
            q["status"] = "active"
            q["skip_reason"] = None
            q["desk_review_note"] = "Reinstated — no other question covers this requirement."
            uncovered.discard(q["id"])
            skipped_count -= 1

    # 6. Assign assessment depth tiers
    assign_tiers(modulated_base, risk_tier)
    assign_tiers(modulated_industry, risk_tier)
    all_questions = modulated_base + modulated_industry
    tier_counts = compute_tier_stats(all_questions)

    # 7. Group into sections
    sections = _build_sections(modulated_base, modulated_industry)

    return {
        "sections": sections,
        "stats": {
            "total_questions": len(modulated_base) + len(modulated_industry) - skipped_count,
            "skipped_questions": skipped_count,
            "pre_filled_questions": pre_filled_count,
            "inferred_questions": inferred_count,
            "deepened_questions": deepened_count,
            "industry_questions": len(modulated_industry),
            "tier_counts": tier_counts,
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
    """Apply desk review modulation to a base DPDPA question.

    Priority order (signals override pre-fills):
      1. Absence found      → DEEPEN (no pre-fill, follow-ups enabled)
      2. Signal found        → DEEPEN (no pre-fill, follow-ups enabled)
      3. Adequate coverage   → PRE-FILL as fully_implemented (high confidence)
      4. Partial coverage    → PRE-FILL as partially_implemented (medium confidence)
      5. No desk review data → ACTIVE (default)

    Rationale: documents describe intent, not operational reality. When the
    desk review finds a red flag (signal) for a requirement, we must force
    human scrutiny even if the document coverage looks adequate on the surface.
    """
    q = {**question, "source": "base", "status": "active", "skip_reason": None, "desk_review_note": None,
         "desk_review_evidence": None, "follow_up_enabled": False, "maps_to": [question["id"]],
         "pre_fill_answer": None, "pre_fill_confidence": None, "pre_fill_source": None,
         "pre_fill_evidence_summary": None}

    req_id = question["id"]
    coverage = desk_data["coverage"]

    # ── 1. Check for signals and absences FIRST (override pre-fills) ────
    has_signal = False

    if req_id in desk_data["absence_req_ids"]:
        q["status"] = "deepened"
        q["desk_review_note"] = _build_absence_note(req_id, desk_data["absences"])
        q["follow_up_enabled"] = True
        has_signal = True

    for signal in desk_data["signals"]:
        if signal.get("requirement_id") == req_id:
            q["status"] = "deepened"
            q["desk_review_note"] = q.get("desk_review_note") or ""
            if q["desk_review_note"]:
                q["desk_review_note"] += " "
            q["desk_review_note"] += f"Signal detected: {signal['content']}"
            q["follow_up_enabled"] = True
            has_signal = True

    # Attach evidence context to deepened questions so the assessor can see
    # both the document text AND the signal side-by-side
    if has_signal:
        evidence_items = desk_data["evidence"].get(req_id, [])
        if evidence_items:
            q["desk_review_evidence"] = evidence_items
        return q

    # ── 2. Pre-fill if adequate/partial coverage with NO signals ────────
    if coverage.get(req_id) in ("adequate", "partial"):
        evidence_items = desk_data["evidence"].get(req_id, [])
        if evidence_items:
            is_adequate = coverage.get(req_id) == "adequate"
            q["status"] = "pre_filled"
            q["pre_fill_answer"] = (
                "fully_implemented" if is_adequate else "partially_implemented"
            )
            q["pre_fill_confidence"] = "high" if is_adequate else "medium"
            q["pre_fill_source"] = "document"
            q["pre_fill_evidence_summary"] = _summarize_evidence(evidence_items)
            q["desk_review_evidence"] = evidence_items
            q["desk_review_note"] = (
                "Evidence found in your documents. Please review and confirm."
            )
            return q

    # ── 3. Default: active question with evidence context if available ──
    evidence_items = desk_data["evidence"].get(req_id, [])
    if evidence_items and q["status"] == "active":
        q["desk_review_evidence"] = evidence_items
        q["desk_review_note"] = "Your documents mention this area — please confirm the current state."

    return q


def _apply_screening(question: dict, screening_data: dict) -> dict:
    """
    Apply screening inference to an active (not yet desk-review modulated) question.

    Confidence mapping:
      high  + compliant/partially_compliant → PRE-FILL as inferred (purple badge)
      low   + any status                   → DEEPEN (force human scrutiny)
      medium + any status                  → ACTIVE with screening context note
    """
    req_id = question["id"]
    inf = screening_data.get(req_id)
    if not inf:
        return question

    status = inf.get("compliance_status", "not_assessed")
    confidence = inf.get("confidence", "low")
    reasoning = inf.get("reasoning", "")

    q = {**question}

    if confidence == "high" and status in ("compliant", "partially_compliant"):
        answer_map = {
            "compliant": "fully_implemented",
            "partially_compliant": "partially_implemented",
        }
        q["status"] = "pre_filled"
        q["pre_fill_answer"] = answer_map[status]
        q["pre_fill_confidence"] = "high"
        q["pre_fill_source"] = "inferred"
        q["pre_fill_evidence_summary"] = reasoning[:250] if reasoning else "Inferred from domain screening answers."
        q["desk_review_note"] = "Pre-filled from domain screening. Please confirm."
    elif confidence == "low":
        q["status"] = "deepened"
        q["follow_up_enabled"] = True
        q["desk_review_note"] = (
            f"Low-confidence inference from screening — detailed review required. "
            f"{reasoning[:200]}" if reasoning else
            "Screening could not confidently assess this control. Please answer in detail."
        )
    else:
        # medium confidence: leave active but add a context note
        q["desk_review_note"] = (
            f"Screening hint ({status.replace('_', ' ')}): {reasoning[:200]}"
            if reasoning else f"Screening suggests: {status.replace('_', ' ')}. Please confirm."
        )

    return q


def _summarize_evidence(evidence_items: list[dict]) -> str:
    """Build a concise evidence summary for pre-fill cards."""
    quotes = []
    for e in evidence_items[:3]:
        quote = (e.get("source_quote") or e.get("content") or "")[:150]
        if quote:
            quotes.append(quote.strip())
    return " | ".join(quotes) if quotes else "Document evidence found."


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
        "pre_fill_answer": None,
        "pre_fill_confidence": None,
        "pre_fill_source": None,
        "pre_fill_evidence_summary": None,
    }

    has_signal = False

    # ── 1. Check deepen_if conditions FIRST (override pre-fills) ────
    deepen_conditions = question.get("deepen_if", {})

    # Deepen if signal flags match
    flag_triggers = deepen_conditions.get("signal_flags", [])
    if flag_triggers and desk_data["signal_flags"] & set(flag_triggers):
        matched = desk_data["signal_flags"] & set(flag_triggers)
        q["status"] = "deepened"
        q["desk_review_note"] = f"Document review flagged: {', '.join(matched)}. Please provide specific details."
        q["follow_up_enabled"] = True
        has_signal = True

    # Deepen if absence findings match
    absence_triggers = deepen_conditions.get("absence_findings", [])
    if absence_triggers:
        matched_absences = set(absence_triggers) & desk_data["absence_req_ids"]
        if matched_absences:
            q["status"] = "deepened"
            note = _build_absence_note_for_reqs(matched_absences, desk_data["absences"])
            q["desk_review_note"] = (q["desk_review_note"] or "") + (" " if q["desk_review_note"] else "") + note
            q["follow_up_enabled"] = True
            has_signal = True

    # Attach evidence for mapped requirements
    evidence_items = []
    for req_id in question["maps_to"]:
        evidence_items.extend(desk_data["evidence"].get(req_id, []))

    if has_signal:
        if evidence_items:
            q["desk_review_evidence"] = evidence_items
        return q

    # ── 2. Pre-fill if skip_if conditions met (NO signals) ────────
    skip_conditions = question.get("skip_if", {})
    desk_coverage = skip_conditions.get("desk_review_coverage", {})
    if desk_coverage:
        all_adequate = all(
            desk_data["coverage"].get(req_id) == status
            for req_id, status in desk_coverage.items()
        )
        if all_adequate and desk_coverage:
            q["status"] = "pre_filled"
            q["pre_fill_answer"] = "fully_implemented"
            q["pre_fill_confidence"] = "high"
            q["pre_fill_source"] = "document"
            q["pre_fill_evidence_summary"] = _summarize_evidence(evidence_items)
            q["desk_review_evidence"] = evidence_items
            q["desk_review_note"] = "Evidence found in your documents for mapped requirements. Please review and confirm."
            return q

    # ── 3. Default: active question with evidence context if available ──
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
