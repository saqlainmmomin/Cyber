"""
Auto-Answer Service — persists document-based pre-filled questionnaire responses.

After desk review completes, this service creates QuestionnaireResponse records
for controls with adequate/partial document coverage. These responses are pre-filled
but require human confirmation — they are never auto-submitted to analysis.

Answer source tracking:
  - "document"            → pre-filled from desk review, awaiting confirmation
  - "document_confirmed"  → human confirmed the pre-filled answer
  - "human_override"      → human changed the pre-filled answer
  - "human"               → human entered from scratch (no pre-fill)
  - "inferred"            → inferred from screening pass (Phase 3, future)
"""

import json
import logging

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.models.questionnaire import QuestionnaireResponse

logger = logging.getLogger(__name__)


def persist_document_answers(assessment_id: str, db: Session) -> int:
    """
    Create QuestionnaireResponse records for controls with adequate/partial
    desk review coverage. These are pre-filled but require human confirmation.

    Does NOT overwrite existing human-entered responses.
    Does NOT pre-fill requirements that have desk review signals (red flags) —
    those must be answered manually to ensure proper scrutiny.

    Returns count of auto-created responses.
    """
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        logger.warning(f"Auto-answer: assessment {assessment_id} not found")
        return 0

    # Load desk review coverage summary
    dr_summary = (
        db.query(DeskReviewSummary)
        .filter(
            DeskReviewSummary.assessment_id == assessment_id,
            DeskReviewSummary.status == "completed",
        )
        .first()
    )
    if not dr_summary or not dr_summary.coverage_summary:
        logger.info(f"Auto-answer: no completed desk review for {assessment_id}")
        return 0

    coverage = json.loads(dr_summary.coverage_summary)

    # Load ALL findings (evidence, signals, absences)
    all_findings = (
        db.query(DeskReviewFinding)
        .filter(DeskReviewFinding.assessment_id == assessment_id)
        .all()
    )

    # Index evidence by requirement_id
    evidence_by_req: dict[str, list[DeskReviewFinding]] = {}
    # Collect requirement IDs that have signals or absences (suppress pre-fills)
    signal_req_ids: set[str] = set()

    for f in all_findings:
        if f.finding_type == "evidence" and f.requirement_id:
            evidence_by_req.setdefault(f.requirement_id, []).append(f)
        elif f.finding_type in ("signal", "absence") and f.requirement_id:
            signal_req_ids.add(f.requirement_id)

    # Load existing human responses to avoid overwriting
    existing_responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.assessment_id == assessment_id)
        .all()
    )
    existing_by_qid = {r.question_id: r for r in existing_responses}

    created_count = 0
    suppressed_count = 0

    for req_id, coverage_level in coverage.items():
        if coverage_level not in ("adequate", "partial"):
            continue

        # Don't pre-fill requirements with signals — force human scrutiny
        if req_id in signal_req_ids:
            suppressed_count += 1
            continue

        # Don't overwrite human-entered responses
        existing = existing_by_qid.get(req_id)
        if existing and existing.answer_source in ("human", "human_override", "document_confirmed"):
            continue

        # Map coverage to answer
        answer = (
            "fully_implemented" if coverage_level == "adequate"
            else "partially_implemented"
        )
        confidence = "high" if coverage_level == "adequate" else "medium"

        # Build notes from evidence quotes
        evidence_items = evidence_by_req.get(req_id, [])
        notes = _build_evidence_notes(evidence_items)
        evidence_ref = _build_evidence_reference(evidence_items)

        if existing and existing.answer_source == "document":
            # Update existing document pre-fill (e.g., desk review re-run)
            existing.answer = answer
            existing.confidence = confidence
            existing.notes = notes
            existing.evidence_reference = evidence_ref
        else:
            # Create new pre-fill response
            db.add(QuestionnaireResponse(
                assessment_id=assessment_id,
                question_id=req_id,
                answer=answer,
                notes=notes,
                evidence_reference=evidence_ref,
                confidence=confidence,
                answer_source="document",
            ))
            created_count += 1

    if created_count or suppressed_count:
        db.flush()
        logger.info(
            f"Auto-answer: created {created_count} document-based responses, "
            f"suppressed {suppressed_count} (signals found) "
            f"for assessment {assessment_id}"
        )

    return created_count


def _build_evidence_notes(findings: list) -> str:
    """Build notes from evidence findings for the pre-fill card."""
    if not findings:
        return "Document evidence found."

    parts = []
    for f in findings[:3]:
        quote = (f.source_quote or f.content or "")[:200].strip()
        location = f.source_location or ""
        if quote:
            entry = f'"{quote}"'
            if location:
                entry += f" ({location})"
            parts.append(entry)

    return " | ".join(parts) if parts else "Document evidence found."


def _build_evidence_reference(findings: list) -> str:
    """Build evidence reference string from findings."""
    if not findings:
        return ""

    sources = set()
    for f in findings:
        if f.source_location:
            sources.add(f.source_location)

    return "; ".join(sorted(sources)) if sources else ""
