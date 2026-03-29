from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate, AssessmentResponse

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@router.post("", response_model=AssessmentResponse, status_code=201)
def create_assessment(data: AssessmentCreate, db: Session = Depends(get_db)):
    assessment = Assessment(
        company_name=data.company_name,
        industry=data.industry.value,
        company_size=data.company_size.value,
        description=data.description,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("", response_model=list[AssessmentResponse])
def list_assessments(db: Session = Depends(get_db)):
    return db.query(Assessment).order_by(Assessment.created_at.desc()).all()


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    return assessment


@router.delete("/{assessment_id}", status_code=204)
def delete_assessment(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    db.delete(assessment)
    db.commit()
