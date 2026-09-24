"""API endpoints for desk review pipeline (Call 0)."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.services.citations import loads_citations
from app.services.desk_review import run_desk_review
from app.services.desk_review_findings import (
    failed_desk_review_frameworks,
    finding_framework_id,
    group_signal_findings,
    scoped_findings,
)
from app.services.evidence import analysis_documents

router = APIRouter(prefix="/api/assessments/{assessment_id}/desk-review", tags=["desk-review"])


@router.post("")
def trigger_desk_review(assessment_id: str, db: Session = Depends(get_db)):
    """Trigger desk review analysis on uploaded documents."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    if not analysis_documents(db, assessment_id):
        raise HTTPException(400, "Upload documents before running desk review.")

    summary = run_desk_review(assessment_id, db)

    return {
        "status": summary.status,
        "finding_count": (
            db.query(DeskReviewFinding)
            .filter(DeskReviewFinding.assessment_id == assessment_id)
            .count()
        ),
        "failed_frameworks": failed_desk_review_frameworks(summary),
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

    findings = scoped_findings(db, assessment)
    selected_control_ids = {
        control.id
        for framework_id in assessment.frameworks
        for control in FrameworkRegistry.get(framework_id).all_controls()
    }
    raw_coverage = json.loads(summary.coverage_summary) if summary.coverage_summary else {}
    coverage = {
        requirement_id: level
        for requirement_id, level in raw_coverage.items()
        if requirement_id in selected_control_ids
    }

    # Group findings by type
    evidence = [f for f in findings if f.finding_type == "evidence"]
    absences = [f for f in findings if f.finding_type == "absence"]
    signals = group_signal_findings(findings)

    return {
        "status": summary.status,
        "document_catalog": json.loads(summary.document_catalog) if summary.document_catalog else [],
        "coverage_summary": coverage,
        "evidence_count": len(evidence),
        "absence_count": len(absences),
        "signal_count": len(signals),
        "findings": {
            "evidence": [
                {
                    "requirement_id": f.requirement_id,
                    "framework_id": finding_framework_id(f),
                    "content": f.content,
                    "source_quote": f.source_quote,
                    "source_location": f.source_location,
                    "document_id": f.document_id,
                    "citations": loads_citations(f.citations_json),
                }
                for f in evidence
            ],
            "absences": [
                {
                    "requirement_id": f.requirement_id,
                    "framework_id": finding_framework_id(f),
                    "content": f.content,
                    "severity": f.severity,
                }
                for f in absences
            ],
            "signals": [
                {
                    "requirement_id": signal["requirement_id"],
                    "requirement_ids": signal["requirement_ids"],
                    "framework_id": signal["framework_id"],
                    "flag_type": signal["flag_type"],
                    "content": signal["content"],
                    "severity": signal["severity"],
                    "source_quote": signal["source_quote"],
                    "source_location": signal["source_location"],
                    "document_id": signal["document_id"],
                    "citations": loads_citations(signal["citations_json"]),
                }
                for signal in signals
            ],
        },
        "failed_frameworks": failed_desk_review_frameworks(summary),
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
