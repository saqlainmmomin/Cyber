import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate, AssessmentResponse

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@router.get("/frameworks/available", tags=["frameworks"])
def list_available_frameworks():
    """List all registered compliance frameworks."""
    from app.frameworks.registry import FrameworkRegistry

    frameworks = []
    for fw_id in sorted(FrameworkRegistry.all_ids()):
        fw = FrameworkRegistry.get(fw_id)
        frameworks.append({
            "id": fw.id,
            "name": fw.name,
            "version": fw.version,
            "control_count": fw.control_count(),
            "domain_count": len(fw.domains),
            "scope_questions": len(fw.scope_questions),
        })
    return {"frameworks": frameworks}


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


class FrameworkSelection(BaseModel):
    framework_ids: list[str]


@router.post("/{assessment_id}/frameworks", status_code=200)
def set_frameworks(
    assessment_id: str,
    data: FrameworkSelection,
    db: Session = Depends(get_db),
):
    """Select which compliance frameworks this assessment covers."""
    from app.frameworks.registry import FrameworkRegistry

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    # Validate all framework IDs
    for fw_id in data.framework_ids:
        if not FrameworkRegistry.is_registered(fw_id):
            available = FrameworkRegistry.all_ids()
            raise HTTPException(
                400,
                f"Unknown framework '{fw_id}'. Available: {sorted(available)}",
            )

    if not data.framework_ids:
        raise HTTPException(400, "At least one framework must be selected")

    assessment.selected_frameworks = json.dumps(data.framework_ids)
    db.commit()
    db.refresh(assessment)

    # Return framework metadata
    frameworks_info = []
    for fw_id in data.framework_ids:
        fw = FrameworkRegistry.get(fw_id)
        frameworks_info.append({
            "id": fw.id,
            "name": fw.name,
            "version": fw.version,
            "control_count": fw.control_count(),
        })

    return {
        "assessment_id": assessment_id,
        "selected_frameworks": data.framework_ids,
        "frameworks": frameworks_info,
    }


@router.get("/{assessment_id}/frameworks")
def get_frameworks(assessment_id: str, db: Session = Depends(get_db)):
    """Get the selected frameworks for an assessment."""
    from app.frameworks.registry import FrameworkRegistry

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    selected = ["dpdpa"]
    if assessment.selected_frameworks:
        try:
            selected = json.loads(assessment.selected_frameworks)
        except json.JSONDecodeError:
            pass

    frameworks_info = []
    for fw_id in selected:
        fw = FrameworkRegistry.get_or_none(fw_id)
        if fw:
            frameworks_info.append({
                "id": fw.id,
                "name": fw.name,
                "version": fw.version,
                "control_count": fw.control_count(),
            })

    return {
        "assessment_id": assessment_id,
        "selected_frameworks": selected,
        "frameworks": frameworks_info,
    }


@router.delete("/{assessment_id}", status_code=204)
def delete_assessment(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    db.delete(assessment)
    db.commit()
