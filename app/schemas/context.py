"""Schemas for Phase 1 context gathering."""

from pydantic import BaseModel, field_validator


class ContextAnswer(BaseModel):
    question_id: str
    answer: str | list[str]  # single_select/text → str, multi_select → list[str]

    @field_validator("question_id")
    @classmethod
    def validate_question_id(cls, value: str) -> str:
        if not value.startswith("CTX."):
            raise ValueError("question_id must start with CTX.")
        return value

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("answer must not be blank")
            return stripped

        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("answer must not be empty")
        return cleaned


class ContextSubmit(BaseModel):
    answers: list[ContextAnswer]


class ContextQuestionOut(BaseModel):
    id: str
    question: str
    type: str  # single_select, multi_select, text
    options: list[str] | None = None
    depends_on: dict[str, str] | None = None
    block_id: str
    block_title: str
    block_description: str


class ContextBlockOut(BaseModel):
    id: str
    title: str
    description: str
    questions: list[ContextQuestionOut]


class ContextProfileOut(BaseModel):
    risk_tier: str  # HIGH, MEDIUM, LOW
    priority_chapters: list[str]
    likely_not_applicable: list[str]
    sdf_candidate: bool
    processes_children_data: bool
    cross_border_transfers: bool
    has_breach_response: bool
    industry_context: str
    timeline_pressure: str
    framing_notes: str


class ContextResponse(BaseModel):
    answers: list[ContextAnswer]
    profile: ContextProfileOut | None = None
