"""API endpoints for desk review pipeline (Call 0)."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.services.desk_review import run_desk_review

router = APIRouter(prefix="/api/assessments/{assessment_id}/desk-review", tags=["desk-review"])


@router.post("")
def trigger_desk_review(assessment_id: str, db: Session = Depends(get_db)):
    """Trigger desk review analysis on uploaded documents."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    # Check documents exist
    from app.models.assessment import AssessmentDocument
    doc_count = (
        db.query(AssessmentDocument)
        .filter(AssessmentDocument.assessment_id == assessment_id)
        .count()
    )
    if doc_count == 0:
        raise HTTPException(400, "Upload documents before running desk review.")

    summary = run_desk_review(assessment_id, db)

    return {
        "status": summary.status,
        "finding_count": (
            db.query(DeskReviewFinding)
            .filter(DeskReviewFinding.assessment_id == assessment_id)
            .count()
        ),
        "message": "Desk review completed" if summary.status == "completed" else f"Desk review {summary.status}",
    }


@router.get("")
def get_desk_review(assessment_id: str, db: Session = Depends(get_db)):
    """Get desk review findings and summary."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    summary = (
        db.query(DeskReviewSummary)
        .filter(DeskReviewSummary.assessment_id == assessment_id)
        .first()
    )
    if not summary:
        raise HTTPException(404, "No desk review found. Upload documents and trigger desk review first.")

    findings = (
        db.query(DeskReviewFinding)
        .filter(DeskReviewFinding.assessment_id == assessment_id)
        .all()
    )

    # Group findings by type
    evidence = [f for f in findings if f.finding_type == "evidence"]
    absences = [f for f in findings if f.finding_type == "absence"]
    signals = [f for f in findings if f.finding_type == "signal"]

    return {
        "status": summary.status,
        "document_catalog": json.loads(summary.document_catalog) if summary.document_catalog else [],
        "coverage_summary": json.loads(summary.coverage_summary) if summary.coverage_summary else {},
        "evidence_count": len(evidence),
        "absence_count": len(absences),
        "signal_count": len(signals),
        "findings": {
            "evidence": [
                {
                    "requirement_id": f.requirement_id,
                    "content": f.content,
                    "source_quote": f.source_quote,
                    "source_location": f.source_location,
                    "document_id": f.document_id,
                }
                for f in evidence
            ],
            "absences": [
                {
                    "requirement_id": f.requirement_id,
                    "content": f.content,
                    "severity": f.severity,
                }
                for f in absences
            ],
            "signals": [
                {
                    "requirement_id": f.requirement_id,
                    "content": f.content,
                    "severity": f.severity,
                    "source_quote": f.source_quote,
                    "source_location": f.source_location,
                    "document_id": f.document_id,
                }
                for f in signals
            ],
        },
        "started_at": summary.started_at.isoformat() if summary.started_at else None,
        "completed_at": summary.completed_at.isoformat() if summary.completed_at else None,
    }


@router.get("/status")
def get_desk_review_status(assessment_id: str, db: Session = Depends(get_db)):
    """Lightweight status check for polling."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    summary = (
        db.query(DeskReviewSummary)
        .filter(DeskReviewSummary.assessment_id == assessment_id)
        .first()
    )

    if not summary:
        return {"status": "not_started"}

    finding_count = 0
    if summary.status == "completed":
        finding_count = (
            db.query(DeskReviewFinding)
            .filter(DeskReviewFinding.assessment_id == assessment_id)
            .count()
        )

    return {
        "status": summary.status,
        "finding_count": finding_count,
        "error_message": summary.error_message,
    }
