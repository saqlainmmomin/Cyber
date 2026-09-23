from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.evidence import EvidenceOut, EvidenceTransitionIn, EvidenceUseIn, EvidenceUseOut
from app.services import evidence as evidence_service

router = APIRouter(prefix="/api/evidence", tags=["evidence"])


def _raise_service_error(exc: evidence_service.EvidenceError):
    raise HTTPException(exc.status_code, exc.message)


def _detail(db: Session, evidence_id: str) -> dict:
    try:
        return evidence_service.evidence_detail(db, evidence_id)
    except evidence_service.EvidenceError as exc:
        _raise_service_error(exc)


@router.get("/{evidence_id}", response_model=EvidenceOut)
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    return _detail(db, evidence_id)


@router.post("/{evidence_id}/versions", response_model=EvidenceOut, status_code=201)
async def upload_version(
    evidence_id: str,
    file: UploadFile = File(...),
    change_reason: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        result = evidence_service.ingest_new_version(
            db,
            evidence_id=evidence_id,
            filename=file.filename or "document",
            content=await file.read(),
            change_reason=change_reason,
        )
        if not result.released:
            raise HTTPException(422, evidence_service.SCAN_REJECTED_MESSAGE)
        return evidence_service.evidence_detail(db, evidence_id)
    except evidence_service.EvidenceError as exc:
        _raise_service_error(exc)


@router.post("/{evidence_id}/transitions", response_model=EvidenceOut)
def transition_evidence(
    evidence_id: str,
    body: EvidenceTransitionIn,
    db: Session = Depends(get_db),
):
    try:
        evidence_service.transition_evidence(
            db,
            evidence_id=evidence_id,
            to_status=body.to_status,
            actor=evidence_service.CONSULTANT_ACTOR,
            reason=body.reason,
        )
        db.commit()
        return evidence_service.evidence_detail(db, evidence_id)
    except evidence_service.EvidenceError as exc:
        _raise_service_error(exc)


@router.post("/{evidence_id}/uses", response_model=EvidenceUseOut, status_code=201)
def map_evidence(
    evidence_id: str,
    body: EvidenceUseIn,
    db: Session = Depends(get_db),
):
    try:
        use = evidence_service.map_evidence(
            db,
            evidence_id=evidence_id,
            assessment_id=body.assessment_id,
            framework_id=body.framework_id,
            requirement_id=body.requirement_id,
            relevance=body.relevance,
            actor=evidence_service.CONSULTANT_ACTOR,
        )
        db.commit()
        return use
    except evidence_service.EvidenceError as exc:
        _raise_service_error(exc)


@router.delete("/{evidence_id}/uses/{use_id}", status_code=204)
def unmap_evidence(evidence_id: str, use_id: str, db: Session = Depends(get_db)):
    try:
        evidence_service.unmap_evidence(
            db,
            evidence_id=evidence_id,
            use_id=use_id,
            actor=evidence_service.CONSULTANT_ACTOR,
        )
        db.commit()
    except evidence_service.EvidenceError as exc:
        _raise_service_error(exc)
