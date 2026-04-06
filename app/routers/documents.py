from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment, AssessmentDocument
from app.schemas.assessment import DocumentCategory, DocumentResponse
from app.services.document_processor import detect_file_type, extract_text, save_upload

router = APIRouter(prefix="/api/assessments/{assessment_id}/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    assessment_id: str,
    category: DocumentCategory = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    file_type = detect_file_type(file.filename or "")
    if not file_type:
        raise HTTPException(
            400,
            "Unsupported file type. Upload PDF, DOCX, PNG, JPG, JPEG, or WEBP files.",
        )

    content = await file.read()
    file_path = save_upload(assessment_id, file.filename or "document", content)

    extracted_text = extract_text(file_path, file_type)
    if not extracted_text.strip():
        raise HTTPException(
            422,
            "Could not extract text from this document. If it is a scanned PDF, "
            "try uploading it as a PNG or JPEG screenshot instead.",
        )

    doc = AssessmentDocument(
        assessment_id=assessment_id,
        filename=file.filename or "document",
        file_path=file_path,
        file_type=file_type,
        document_category=category.value,
        extracted_text=extracted_text,
    )
    db.add(doc)

    if assessment.status == "created":
        assessment.status = "documents_uploaded"
    db.commit()
    db.refresh(doc)

    return DocumentResponse(
        id=doc.id,
        assessment_id=doc.assessment_id,
        filename=doc.filename,
        file_type=doc.file_type,
        document_category=doc.document_category,
        text_length=len(doc.extracted_text or ""),
        uploaded_at=doc.uploaded_at,
    )


@router.get("", response_model=list[DocumentResponse])
def list_documents(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    docs = (
        db.query(AssessmentDocument)
        .filter(AssessmentDocument.assessment_id == assessment_id)
        .all()
    )
    return [
        DocumentResponse(
            id=d.id,
            assessment_id=d.assessment_id,
            filename=d.filename,
            file_type=d.file_type,
            document_category=d.document_category,
            text_length=len(d.extracted_text or ""),
            uploaded_at=d.uploaded_at,
        )
        for d in docs
    ]


@router.delete("/{document_id}", status_code=204)
def delete_document(assessment_id: str, document_id: str, db: Session = Depends(get_db)):
    doc = db.get(AssessmentDocument, document_id)
    if not doc or doc.assessment_id != assessment_id:
        raise HTTPException(404, "Document not found")
    db.delete(doc)
    db.commit()
