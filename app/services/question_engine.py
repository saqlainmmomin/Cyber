"""
Question Selection Engine — builds an adaptive questionnaire from desk review findings,
context profile, and industry-specific question banks, and modulates UCC cluster
questions from framework-keyed desk-review findings.

The engine merges two question sources:
  1. Base DPDPA questions (41 requirements from questionnaire.py)
  2. Industry-specific questions (from industry_questions.py)

Desk review findings modulate which questions appear:
  - Deepen: signals/absences found → extra context shown, follow-up probes enabled
  - Add: signal flags → targeted questions injected

The output is a list of QuestionSets (sections) ready for the web UI.
"""

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.tier_engine import assign_tiers, compute_tier_stats

from app.dpdpa.industry_questions import INDUSTRY_BANK_MAP, get_industry_questions
from app.dpdpa.questionnaire import ANSWER_OPTIONS, _GUIDANCE_TEXT, _QUESTION_TEXT, build_questionnaire
from app.frameworks.questionnaire_builder import (
    build_multi_questionnaire,
    compute_excluded_controls,
)
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.desk_review import DeskReviewSummary
from app.models.questionnaire import QuestionnaireResponse
from app.services.auto_answer import confirmed_response_clause
from app.services.desk_review_findings import (
    failed_desk_review_frameworks,
    finding_framework_id,
    finding_has_grounded_citation,
    scoped_findings,
)

CLUSTER_PREFILL_LEVELS = ("adequate", "partial")
CLUSTER_NOTE_ITEM_LIMIT = 3
CLUSTER_ABSENCE_ITEM = "{control_id}: No evidence found in documents: {content}"
CLUSTER_ABSENT_COVERAGE_ITEM = "{control_id}: The documents address this area but not this control."
CLUSTER_SIGNAL_ITEM = "Signal detected ({control_ids}): {content}"
CLUSTER_NOTE_OVERFLOW = " (+{n} more document findings)"
CLUSTER_PREFILL_NOTE = "Evidence found in your documents for every control this question covers. Please review and confirm."
CLUSTER_EVIDENCE_NOTE = "Your documents mention some of the controls this question covers. Please confirm the current state."
CLUSTER_UNREVIEWED_NOTE = "Desk review did not complete for {names}, so this question was not pre-filled from documents."

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


@dataclass(frozen=True)
class ClusterDeskData:
    coverage: dict[str, str]
    evidence: dict[str, list[dict]]
    absences: dict[str, list[str]]
    signals: dict[str, list[dict]]
    failed_frameworks: frozenset[str]


def is_dpdpa_only(assessment: Assessment) -> bool:
    """True when the assessment uses the DPDPA-only requirement-keyed questionnaire."""
    return assessment.frameworks == ["dpdpa"]


def _load_cluster_desk_data(assessment: Assessment, db: Session) -> ClusterDeskData | None:
    """Load framework-keyed desk-review findings for UCC question modulation."""
    summary = (
        db.query(DeskReviewSummary)
        .filter(
            DeskReviewSummary.assessment_id == assessment.id,
            DeskReviewSummary.status == "completed",
        )
        .first()
    )
    if not summary:
        return None

    control_framework = {
        control.id: framework_id
        for framework_id in assessment.frameworks
        for control in FrameworkRegistry.get(framework_id).all_controls()
    }
    try:
        raw_coverage = json.loads(summary.coverage_summary or "{}")
    except (json.JSONDecodeError, TypeError):
        raw_coverage = {}
    coverage = (
        {
            control_id: level
            for control_id, level in raw_coverage.items()
            if control_id in control_framework
        }
        if isinstance(raw_coverage, dict)
        else {}
    )

    evidence: dict[str, list[dict]] = {}
    absences: dict[str, list[str]] = {}
    signals: dict[str, list[dict]] = {}
    for finding in scoped_findings(db, assessment):
        requirement_id = finding.requirement_id
        if not requirement_id or requirement_id not in control_framework:
            continue
        framework_id = finding_framework_id(finding)
        if framework_id != control_framework[requirement_id]:
            continue

        if finding.finding_type == "evidence":
            evidence.setdefault(requirement_id, []).append({
                "control_id": requirement_id,
                "framework_id": control_framework[requirement_id],
                "content": (
                    f"{requirement_id} "
                    f"({FrameworkRegistry.get(control_framework[requirement_id]).name})"
                ),
                "source_quote": finding.source_quote or "",
                "source_location": finding.source_location or "",
                "severity": finding.severity,
                "grounded": finding_has_grounded_citation(finding),
            })
        elif finding.finding_type == "absence":
            absences.setdefault(requirement_id, []).append(finding.content or "")
        elif finding.finding_type == "signal":
            signals.setdefault(requirement_id, []).append({
                "group_key": finding.signal_group_id or f"row:{finding.id}",
                "content": finding.content or "",
            })

    failed_frameworks = frozenset(failed_desk_review_frameworks(summary)) & set(assessment.frameworks)
    return ClusterDeskData(
        coverage=coverage,
        evidence=evidence,
        absences=absences,
        signals=signals,
        failed_frameworks=failed_frameworks,
    )


def _modulate_cluster_question(question: dict, desk: ClusterDeskData | None) -> dict:
    """Derive a UCC question state from its member-control desk-review data."""
    if desk is None:
        return question

    members = question["member_controls"]
    ids = [member["control_id"] for member in members]
    evidence_items = [
        evidence
        for control_id in ids
        for evidence in desk.evidence.get(control_id, [])
    ]
    evidence_or_none = evidence_items or None

    findings_notes: list[str] = []
    for control_id in ids:
        for content in desk.absences.get(control_id, []):
            findings_notes.append(CLUSTER_ABSENCE_ITEM.format(control_id=control_id, content=content))
        if not desk.absences.get(control_id) and desk.coverage.get(control_id) == "absent":
            findings_notes.append(CLUSTER_ABSENT_COVERAGE_ITEM.format(control_id=control_id))

    seen_signal_groups: set[str] = set()
    for control_id in ids:
        for signal in desk.signals.get(control_id, []):
            group_key = signal["group_key"]
            if group_key in seen_signal_groups:
                continue
            seen_signal_groups.add(group_key)
            affected = [
                member_id
                for member_id in ids
                if any(
                    item["group_key"] == group_key
                    for item in desk.signals.get(member_id, [])
                )
            ]
            findings_notes.append(CLUSTER_SIGNAL_ITEM.format(
                control_ids=", ".join(affected),
                content=signal["content"],
            ))

    if findings_notes:
        note = " ".join(findings_notes[:CLUSTER_NOTE_ITEM_LIMIT])
        if len(findings_notes) > CLUSTER_NOTE_ITEM_LIMIT:
            note += CLUSTER_NOTE_OVERFLOW.format(
                n=len(findings_notes) - CLUSTER_NOTE_ITEM_LIMIT,
            )
        return {
            **question,
            "status": "deepened",
            "follow_up_enabled": True,
            "desk_review_note": note,
            "desk_review_evidence": evidence_or_none,
            "pre_fill_answer": None,
            "pre_fill_confidence": None,
            "pre_fill_source": None,
            "pre_fill_evidence_summary": None,
        }

    prefillable = all(
        member["framework_id"] not in desk.failed_frameworks
        and desk.coverage.get(member["control_id"]) in CLUSTER_PREFILL_LEVELS
        and any(
            evidence["grounded"]
            for evidence in desk.evidence.get(member["control_id"], [])
        )
        for member in members
    )
    if ids and prefillable:
        all_adequate = all(desk.coverage[control_id] == "adequate" for control_id in ids)
        first_grounded = [
            next(evidence for evidence in desk.evidence[control_id] if evidence["grounded"])
            for control_id in ids
        ]
        return {
            **question,
            "status": "pre_filled",
            "pre_fill_source": "document",
            "pre_fill_answer": "fully_implemented" if all_adequate else "partially_implemented",
            "pre_fill_confidence": "high" if all_adequate else "medium",
            "pre_fill_evidence_summary": _summarize_evidence(first_grounded),
            "desk_review_evidence": evidence_items,
            "desk_review_note": CLUSTER_PREFILL_NOTE,
        }

    failed_members = list(dict.fromkeys(
        member["framework_id"]
        for member in members
        if member["framework_id"] in desk.failed_frameworks
    ))
    note_parts = []
    if evidence_items:
        note_parts.append(CLUSTER_EVIDENCE_NOTE)
    if failed_members:
        note_parts.append(CLUSTER_UNREVIEWED_NOTE.format(
            names=", ".join(FrameworkRegistry.get(framework_id).name for framework_id in failed_members),
        ))
    return {
        **question,
        "status": "active",
        "desk_review_evidence": evidence_or_none,
        "desk_review_note": " ".join(note_parts) if note_parts else question["context_note"],
        "pre_fill_answer": None,
        "pre_fill_confidence": None,
        "pre_fill_source": None,
        "pre_fill_evidence_summary": None,
    }


def _build_multi_framework_questionnaire(
    assessment: Assessment,
    framework_ids: list[str],
    db: Session,
) -> dict:
    """
    Build and return a questionnaire for multi-framework (non-DPDPA-only) assessments
    using the Unified Control Cluster engine. Questions are normalised into the same
    shape expected by section_questions.html.
    """
    context_profile = json.loads(assessment.context_profile) if assessment.context_profile else None
    excluded = compute_excluded_controls(
        framework_ids,
        assessment.applicable_requirements,
    )

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
            # Status fields — defaults; _modulate_cluster_question sets them (P5-4)
            "status": "active",
            "skip_reason": None,
            "desk_review_note": ucc_q.get("context_note"),
            "desk_review_evidence": None,
            "tier": "standard",
            "source": "base",
            "follow_up_enabled": bool(ucc_q.get("follow_ups")),
            "maps_to": [c["control_id"] for c in ucc_q.get("controls", [])],
            "member_controls": [
                {"framework_id": c["framework_id"], "control_id": c["control_id"]}
                for c in ucc_q.get("controls", [])
            ],
            # Pre-fill fields — defaults; _modulate_cluster_question sets them (P5-4)
            "pre_fill_answer": None,
            "pre_fill_confidence": None,
            "pre_fill_source": None,
            "pre_fill_evidence_summary": None,
            "skip_if": None,
            "relevance_weight": ucc_q.get("relevance_weight", 1.0),
            "context_note": ucc_q.get("context_note"),
            "answer_options": ANSWER_OPTIONS,
        })

    desk = _load_cluster_desk_data(assessment, db)
    questions = [_modulate_cluster_question(question, desk) for question in normalised]
    risk_tier = context_profile.get("risk_tier", "MEDIUM") if context_profile else "MEDIUM"
    assign_tiers(questions, risk_tier)

    # Group into sections by domain_group
    sections: dict[str, dict] = {}
    for q in questions:
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
    total = len(questions)

    return {
        "sections": section_list,
        "stats": {
            "total_questions": total,
            "skipped_questions": 0,
            "pre_filled_questions": sum(q["status"] == "pre_filled" for q in questions),
            "inferred_questions": 0,
            "deepened_questions": sum(q["status"] == "deepened" for q in questions),
            "industry_questions": 0,
            "tier_counts": compute_tier_stats(questions),
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

    # Route non-DPDPA-only assessments to the UCC-based engine
    if not is_dpdpa_only(assessment):
        return _build_multi_framework_questionnaire(assessment, assessment.frameworks, db)


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
    industry_bank_key = INDUSTRY_BANK_MAP.get(industry, "generic")
    industry_chapter_title = (
        "Industry-Specific" if industry_bank_key != "generic" else "Additional Questions"
    )

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
        mod = _modulate_industry_question(iq, desk_data, context_profile, industry_chapter_title)
        if mod["status"] == "skipped":
            skipped_count += 1
        elif mod["status"] == "deepened":
            deepened_count += 1
        elif mod["status"] == "pre_filled":
            pre_filled_count += 1
        modulated_industry.append(mod)

    # 5. Assign assessment depth tiers
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
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        return {"coverage": {}, "signals": [], "absences": [], "evidence": {}, "signal_flags": set(), "absence_req_ids": set()}

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

    dpdpa_ids = {
        control.id for control in FrameworkRegistry.get("dpdpa").all_controls()
    }
    raw_coverage = json.loads(dr_summary.coverage_summary) if dr_summary.coverage_summary else {}
    coverage = {
        requirement_id: level
        for requirement_id, level in raw_coverage.items()
        if requirement_id in dpdpa_ids
    }

    findings = scoped_findings(db, assessment, framework_ids=["dpdpa"])

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

    signal_flags = {
        finding.flag_type
        for finding in findings
        if finding.finding_type == "signal" and finding.flag_type
    }

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


def _modulate_industry_question(
    question: dict,
    desk_data: dict,
    context_profile: dict | None,
    chapter_title: str,
) -> dict:
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
        "chapter_title": chapter_title,
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
    Industry questions are grouped by category into a separate chapter.
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
                "chapter_title": q["chapter_title"],
                "section_title": q["section_title"],
                "source": "industry",
                "questions": [],
            }
        sections[sid]["questions"].append(q)

    # Order: base sections first (by chapter order), then industry sections
    base_order = [s for s in sections.values() if s["source"] == "base"]
    industry_order = [s for s in sections.values() if s["source"] == "industry"]

    return base_order + industry_order


def questionnaire_progress(questionnaire: dict, assessment_id: str, db: Session) -> dict:
    """Confirmed answers to rendered questions, and live pre-fills awaiting confirmation."""
    rendered_questions = [
        question
        for section in questionnaire["sections"]
        for question in section.get("questions", [])
        if question.get("status") != "skipped"
    ]
    rendered = {question["id"] for question in rendered_questions}
    rows = (
        db.query(QuestionnaireResponse.question_id, QuestionnaireResponse.answer)
        .filter(
            QuestionnaireResponse.assessment_id == assessment_id,
            confirmed_response_clause(),
        )
        .all()
    )
    answered = {
        question_id
        for question_id, answer in rows
        if question_id in rendered and (answer or "").strip()
    }
    awaiting_confirmation = sum(
        question.get("status") == "pre_filled" and question["id"] not in answered
        for question in rendered_questions
    )
    return {
        "answered_questions": len(answered),
        "awaiting_confirmation": awaiting_confirmation,
    }
