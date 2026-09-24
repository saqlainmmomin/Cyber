"""Web routes for consultant-confirmed evidence reuse suggestions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.engagement import Engagement
from app.routers.web import templates
from app.services import conclusion_review, evidence as evidence_service
from app.services import evidence_reuse

router = APIRouter(include_in_schema=False)


def _framework_names(assessment: Assessment) -> dict[str, str]:
    return {
        framework_id: (
            FrameworkRegistry.get_or_none(framework_id).name
            if FrameworkRegistry.get_or_none(framework_id)
            else framework_id.upper()
        )
        for framework_id in assessment.frameworks
    }


def _page_context(
    request: Request,
    db: Session,
    assessment: Assessment,
    *,
    candidates: list[evidence_reuse.ReuseCandidate] | None = None,
    error: str | None = None,
) -> dict:
    engagement = db.get(Engagement, assessment.engagement_id) if assessment.engagement_id else None
    client = db.get(Client, engagement.client_id) if engagement else None
    return {
        "request": request,
        "assessment": assessment,
        "engagement": engagement,
        "client": client,
        "candidates": candidates if candidates is not None else evidence_reuse.reuse_candidates(db, assessment.id),
        "framework_names": _framework_names(assessment),
        "target_framework_ids": assessment.frameworks,
        "threshold": evidence_reuse.REUSE_AGE_WARNING_DAYS,
        "error": error,
    }


@router.get("/assessments/{assessment_id}/evidence-reuse")
def evidence_reuse_page(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, evidence_reuse.ASSESSMENT_NOT_FOUND)
    return templates.TemplateResponse(
        "pages/evidence_reuse.html",
        _page_context(request, db, assessment),
    )


@router.post("/assessments/{assessment_id}/evidence-reuse/{source_use_id}/confirm")
def confirm_evidence_reuse(
    request: Request,
    assessment_id: str,
    source_use_id: str,
    acknowledge_warnings: str | None = Form(None),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, evidence_reuse.ASSESSMENT_NOT_FOUND)
    actor = conclusion_review.reviewer_actor(reviewer_name)
    try:
        evidence_reuse.confirm_reuse(
            db,
            assessment_id=assessment_id,
            source_use_id=source_use_id,
            acknowledge_warnings=acknowledge_warnings == "yes",
            actor=actor,
        )
    except evidence_reuse.ReuseNotFound as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    except (evidence_reuse.ReuseError, evidence_service.EvidenceError) as exc:
        db.rollback()
        return templates.TemplateResponse(
            "pages/evidence_reuse.html",
            _page_context(request, db, assessment, error=exc.message),
            status_code=exc.status_code,
        )
    db.commit()
    return RedirectResponse(
        f"/assessments/{assessment_id}/evidence-reuse",
        status_code=303,
    )
