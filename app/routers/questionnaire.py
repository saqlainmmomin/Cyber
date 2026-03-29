import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dpdpa.context_questions import CONTEXT_BLOCKS, get_context_questions
from app.dpdpa.questionnaire import build_questionnaire
from app.models.assessment import Assessment
from app.models.questionnaire import QuestionnaireResponse
from app.schemas.context import (
    ContextBlockOut,
    ContextProfileOut,
    ContextQuestionOut,
    ContextResponse,
    ContextSubmit,
)
from app.schemas.questionnaire import (
    BulkResponseSubmit,
    QuestionSchema,
    QuestionnaireSection,
    ResponseOut,
)
from app.services.context_profiler import derive_risk_profile

router = APIRouter(tags=["questionnaire"])


# --- Context Gathering (Phase 1) ---


@router.get(
    "/api/context-questions",
    response_model=list[ContextBlockOut],
)
def get_context_questionnaire():
    """Return the Phase 1 context gathering questions grouped by block."""
    blocks = []
    for block in CONTEXT_BLOCKS:
        questions = [
            ContextQuestionOut(
                id=q["id"],
                question=q["question"],
                type=q["type"],
                options=q.get("options"),
                depends_on=q.get("depends_on"),
                block_id=block["id"],
                block_title=block["title"],
                block_description=block["description"],
            )
            for q in block["questions"]
        ]
        blocks.append(
            ContextBlockOut(
                id=block["id"],
                title=block["title"],
                description=block["description"],
                questions=questions,
            )
        )
    return blocks


@router.post(
    "/api/assessments/{assessment_id}/context",
    response_model=ContextResponse,
    status_code=201,
)
def submit_context(
    assessment_id: str,
    data: ContextSubmit,
    db: Session = Depends(get_db),
):
    """Submit Phase 1 context answers and generate risk profile."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    # Store raw answers
    answers_list = [{"question_id": a.question_id, "answer": a.answer} for a in data.answers]
    assessment.context_answers = json.dumps(answers_list)

    # Derive risk profile via Claude
    profile = derive_risk_profile(
        context_answers=answers_list,
        industry=assessment.industry,
        company_size=assessment.company_size,
    )
    assessment.context_profile = json.dumps(profile)

    if assessment.status == "created":
        assessment.status = "context_gathered"

    db.commit()
    db.refresh(assessment)

    return ContextResponse(
        answers=data.answers,
        profile=ContextProfileOut(**profile),
    )


@router.get(
    "/api/assessments/{assessment_id}/context",
    response_model=ContextResponse,
)
def get_context(assessment_id: str, db: Session = Depends(get_db)):
    """Retrieve stored context answers and risk profile for an assessment."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    if not assessment.context_answers:
        raise HTTPException(404, "No context submitted for this assessment")

    answers = json.loads(assessment.context_answers)
    profile = json.loads(assessment.context_profile) if assessment.context_profile else None

    return ContextResponse(
        answers=answers,
        profile=ContextProfileOut(**profile) if profile else None,
    )


# --- Compliance Questionnaire (Phase 2) ---


@router.get("/api/questionnaire", response_model=list[QuestionSchema])
def get_questionnaire(
    assessment_id: str | None = Query(None, description="Assessment ID for context-aware annotations"),
    db: Session = Depends(get_db),
):
    """
    Return the DPDPA compliance questionnaire.

    If assessment_id is provided and the assessment has a context profile,
    questions are returned with context-aware annotations.
    """
    context_profile = None
    if assessment_id:
        assessment = db.get(Assessment, assessment_id)
        if assessment and assessment.context_profile:
            context_profile = json.loads(assessment.context_profile)

    return build_questionnaire(context_profile=context_profile)


@router.get(
    "/api/assessments/{assessment_id}/questionnaire/sections",
    response_model=list[QuestionnaireSection],
)
def get_questionnaire_sections(
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """Return the questionnaire grouped by section, with context-aware annotations."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    context_profile = None
    if assessment.context_profile:
        context_profile = json.loads(assessment.context_profile)

    questions = build_questionnaire(context_profile=context_profile)
    return _group_into_sections(questions)


@router.get(
    "/api/assessments/{assessment_id}/questionnaire/sections/{section_id}",
    response_model=QuestionnaireSection,
)
def get_questionnaire_section(
    assessment_id: str,
    section_id: str,
    db: Session = Depends(get_db),
):
    """Return a single section of the questionnaire."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    context_profile = None
    if assessment.context_profile:
        context_profile = json.loads(assessment.context_profile)

    questions = build_questionnaire(context_profile=context_profile)
    sections = _group_into_sections(questions)

    for section in sections:
        if section.section_id == section_id:
            return section

    raise HTTPException(404, f"Section '{section_id}' not found")


def _group_into_sections(questions: list[dict]) -> list[QuestionnaireSection]:
    """Group flat question list into sections."""
    sections_map: dict[str, list] = {}
    section_meta: dict[str, dict] = {}

    for q in questions:
        section_id = f"{q['chapter']}.{q['section']}"
        if section_id not in sections_map:
            sections_map[section_id] = []
            section_meta[section_id] = {
                "chapter": q["chapter"],
                "chapter_title": q["chapter_title"],
                "section": q["section"],
                "section_title": q["section_title"],
            }
        sections_map[section_id].append(q)

    return [
        QuestionnaireSection(
            section_id=sid,
            **section_meta[sid],
            question_count=len(qs),
            questions=qs,
        )
        for sid, qs in sections_map.items()
    ]


@router.post(
    "/api/assessments/{assessment_id}/responses",
    response_model=list[ResponseOut],
    status_code=201,
)
def submit_responses(
    assessment_id: str,
    data: BulkResponseSubmit,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    # Delete existing responses for this assessment (allow re-submission)
    db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment_id
    ).delete()

    records = []
    for resp in data.responses:
        record = QuestionnaireResponse(
            assessment_id=assessment_id,
            question_id=resp.question_id,
            answer=resp.answer,
            notes=resp.notes,
            evidence_reference=resp.evidence_reference,
            na_reason=resp.na_reason,
            confidence=resp.confidence,
        )
        db.add(record)
        records.append(record)

    assessment.status = "questionnaire_done"
    db.commit()
    for r in records:
        db.refresh(r)
    return records


@router.get(
    "/api/assessments/{assessment_id}/responses",
    response_model=list[ResponseOut],
)
def get_responses(assessment_id: str, db: Session = Depends(get_db)):
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    return (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.assessment_id == assessment_id)
        .all()
    )
