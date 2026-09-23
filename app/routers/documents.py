from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment, AssessmentDocument
from app.schemas.assessment import DocumentCategory, DocumentResponse
from app.services import evidence as evidence_service

router = APIRouter(prefix="/api/assessments/{assessment_id}/documents", tags=["documents"])


def _document_response(row: dict, assessment_id: str) -> DocumentResponse:
    return DocumentResponse(
        id=row["id"],
        assessment_id=assessment_id,
        filename=row["filename"],
        file_type=row["file_type"],
        document_category=row["category"],
        text_length=row["text_length"],
        uploaded_at=row["uploaded_at"],
        status=row["status"],
    )


def _raise_service_error(exc: evidence_service.EvidenceError):
    raise HTTPException(exc.status_code, exc.message)


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    assessment_id: str,
    category: DocumentCategory = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        result = evidence_service.ingest_upload(
            db,
            assessment_id=assessment_id,
            filename=file.filename or "document",
            content=await file.read(),
            category=category.value,
        )
        if not result.released:
            raise HTTPException(422, evidence_service.SCAN_REJECTED_MESSAGE)
        return _document_response(
            next(
                row
                for row in evidence_service.evidence_panel_rows(db, assessment_id)
                if row["id"] == result.evidence.id
            ),
            assessment_id,
        )
    except evidence_service.EvidenceError as exc:
        _raise_service_error(exc)


@router.get("", response_model=list[DocumentResponse])
def list_documents(assessment_id: str, db: Session = Depends(get_db)):
    if db.get(Assessment, assessment_id) is None:
        raise HTTPException(404, "Assessment not found")
    return [
        _document_response(row, assessment_id)
        for row in evidence_service.evidence_panel_rows(db, assessment_id)
    ]


@router.delete("/{document_id}", status_code=204)
def delete_document(assessment_id: str, document_id: str, db: Session = Depends(get_db)):
    evidence = db.get(evidence_service.Evidence, document_id)
    if evidence is None:
        legacy = db.get(AssessmentDocument, document_id)
        if legacy is not None and legacy.assessment_id == assessment_id:
            raise HTTPException(
                409,
                "Legacy document: run scripts/migrate_documents_to_evidence.py before archiving it.",
            )
        raise HTTPException(404, "Document not found")
    if evidence.assessment_id != assessment_id:
        raise HTTPException(404, "Document not found")
    try:
        evidence_service.transition_evidence(
            db,
            evidence_id=document_id,
            to_status="archived",
            actor=evidence_service.CONSULTANT_ACTOR,
        )
        db.commit()
    except evidence_service.EvidenceError as exc:
        _raise_service_error(exc)
