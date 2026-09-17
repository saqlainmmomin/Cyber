"""
Desk Review Pipeline — Call 0 (pre-questionnaire document analysis).

Analyzes uploaded documents to produce:
- Document catalog (type, coverage, summary per doc)
- Evidence map (requirement_id -> evidence items with source quotes)
- Absence findings (missing provisions per requirement)
- Signal flags (red flags: GDPR copy-paste, buried consent, etc.)
- Coverage summary (requirement_id -> coverage level)
"""

import json
import logging
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.dpdpa.prompts import build_desk_review_system_prompt, build_desk_review_user_prompt
from app.models.assessment import Assessment, AssessmentDocument
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.services import llm_client

logger = logging.getLogger(__name__)


def run_desk_review(assessment_id: str, db: Session) -> DeskReviewSummary:
    """
    Run desk review analysis on all uploaded documents for an assessment.

    Creates/updates DeskReviewSummary and DeskReviewFinding records.
    Returns the summary record.
    """
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    # Load documents
    docs_db = (
        db.query(AssessmentDocument)
        .filter(AssessmentDocument.assessment_id == assessment_id)
        .all()
    )
    if not docs_db:
        raise ValueError("No documents uploaded for this assessment")

    documents = [
        {
            "id": d.id,
            "filename": d.filename,
            "category": d.document_category,
            "text": d.extracted_text or "",
        }
        for d in docs_db
    ]

    # Build document ID lookup for linking findings to documents
    doc_id_by_filename = {d.filename: d.id for d in docs_db}

    # Create or reset summary
    summary = (
        db.query(DeskReviewSummary)
        .filter(DeskReviewSummary.assessment_id == assessment_id)
        .first()
    )
    if summary:
        # Clear previous findings
        db.query(DeskReviewFinding).filter(
            DeskReviewFinding.assessment_id == assessment_id
        ).delete()
        summary.status = "analyzing"
        summary.error_message = None
        summary.started_at = datetime.now(timezone.utc)
        summary.completed_at = None
    else:
        summary = DeskReviewSummary(
            assessment_id=assessment_id,
            status="analyzing",
            started_at=datetime.now(timezone.utc),
        )
        db.add(summary)

    assessment.desk_review_status = "analyzing"
    db.commit()
    db.refresh(summary)

    # Truncate documents for prompt
    truncated = _truncate_documents(documents)

    try:
        result = _call_claude_desk_review(
            documents=truncated,
            company_name=assessment.company_name,
            industry=assessment.industry,
        )
    except Exception as e:
        logger.error(f"Desk review Claude call failed: {e}")
        summary.status = "error"
        summary.error_message = str(e)
        assessment.desk_review_status = "error"
        db.commit()
        return summary

    # Parse and persist results
    try:
        _persist_findings(
            db=db,
            assessment_id=assessment_id,
            result=result,
            doc_id_by_filename=doc_id_by_filename,
        )

        summary.document_catalog = json.dumps(result.get("document_catalog", []))
        summary.coverage_summary = json.dumps(result.get("coverage_summary", {}))
        summary.raw_ai_response = json.dumps(result)
        summary.status = "completed"
        summary.completed_at = datetime.now(timezone.utc)
        assessment.desk_review_status = "completed"
        db.commit()

        # Auto-create pre-filled questionnaire responses from document evidence
        try:
            from app.services.auto_answer import persist_document_answers
            pre_fill_count = persist_document_answers(assessment_id, db)
            if pre_fill_count:
                db.commit()
                logger.info(f"Desk review: pre-filled {pre_fill_count} responses from evidence")
        except Exception as e:
            # Pre-fill failure should not block the desk review result
            logger.warning(f"Auto-answer pre-fill failed (non-blocking): {e}")

    except Exception as e:
        logger.error(f"Desk review persist failed: {e}")
        summary.status = "error"
        summary.error_message = f"Failed to persist findings: {e}"
        assessment.desk_review_status = "error"
        db.commit()

    return summary


def _call_llm(*, tier: str, stream: bool = False, **request) -> dict:
    """Seam for the OpenRouter-backed client — patched directly in tests."""
    return llm_client.call_llm(tier, stream=stream, **request)


def _call_claude_desk_review(
    documents: list[dict],
    company_name: str,
    industry: str,
) -> dict:
    """Call the LLM for desk review analysis (Call 0)."""
    system_blocks = build_desk_review_system_prompt()
    user_prompt = build_desk_review_user_prompt(documents, company_name, industry)

    response = _call_llm(
        tier="judge",
        max_tokens=16000,
        temperature=0,
        system=system_blocks,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response["text"]

    # Log cache stats
    usage = response["usage"]
    logger.info(
        f"Desk review tokens — input: {usage['input_tokens']}, "
        f"output: {usage['output_tokens']}, "
        f"cache_read: {usage['cache_read_input_tokens']}, "
        f"cache_create: {usage['cache_creation_input_tokens']}"
    )

    return _parse_json_response(raw_text)


def _persist_findings(
    db: Session,
    assessment_id: str,
    result: dict,
    doc_id_by_filename: dict[str, str],
) -> None:
    """Persist desk review findings to the database."""

    # Evidence map -> findings
    for req_id, evidence_items in result.get("evidence_map", {}).items():
        for item in evidence_items:
            doc_filename = item.get("document", "")
            db.add(DeskReviewFinding(
                assessment_id=assessment_id,
                finding_type="evidence",
                requirement_id=req_id,
                document_id=doc_id_by_filename.get(doc_filename),
                content=item.get("quote", ""),
                severity="info",
                source_quote=item.get("quote", ""),
                source_location=item.get("location", ""),
            ))

    # Absence findings
    for finding in result.get("absence_findings", []):
        db.add(DeskReviewFinding(
            assessment_id=assessment_id,
            finding_type="absence",
            requirement_id=finding.get("requirement_id"),
            content=finding.get("description", ""),
            severity=finding.get("severity", "medium"),
        ))

    # Signal flags
    for flag in result.get("signal_flags", []):
        doc_filename = flag.get("document", "")
        req_ids = flag.get("requirement_ids", [])
        # Create one finding per signal flag (may map to multiple requirements)
        db.add(DeskReviewFinding(
            assessment_id=assessment_id,
            finding_type="signal",
            requirement_id=req_ids[0] if req_ids else None,
            document_id=doc_id_by_filename.get(doc_filename),
            content=flag.get("description", ""),
            severity=flag.get("severity", "medium"),
            source_quote=flag.get("source_quote", ""),
            source_location=flag.get("location", ""),
        ))

    db.flush()


def _truncate_documents(documents: list[dict]) -> list[dict]:
    """Enforce word limits for desk review prompt."""
    max_total = settings.max_total_document_words
    total_words = 0
    result = []

    for doc in documents:
        words = doc["text"].split()
        remaining = max_total - total_words
        if remaining <= 0:
            break
        if len(words) > remaining:
            doc = {**doc, "text": " ".join(words[:remaining]) + "\n\n[... truncated ...]"}
            words = words[:remaining]
        total_words += len(words)
        result.append(doc)

    return result


def _parse_json_response(text: str) -> dict:
    """Parse Claude's JSON response, handling potential markdown fences."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse desk review response as JSON: {e}\nResponse: {text[:500]}")
