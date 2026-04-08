import re
from typing import Literal

from pydantic import BaseModel, field_validator

AnswerLiteral = Literal[
    "fully_implemented",
    "partially_implemented",
    "planned",
    "not_implemented",
    "not_applicable",
]
ConfidenceLiteral = Literal["high", "medium", "low"]
QUESTION_ID_PATTERN = re.compile(r"^(CH[234]\.\w+\.\d+|CM\.\w+\.\d+|CB\.\w+\.\d+|BN\.\w+\.\d+|IND\.\w+\.\d+|FU\..+)$")


class QuestionSchema(BaseModel):
    id: str
    chapter: str
    chapter_title: str
    section: str
    section_title: str
    question: str
    guidance: str
    criticality: str
    section_ref: str
    answer_options: list[str]
    # Context-aware annotations (populated when assessment_id provided)
    relevance_weight: float = 1.0
    context_note: str | None = None
    skip_if: str | None = None


class QuestionnaireSection(BaseModel):
    """A section of the questionnaire with grouped questions."""
    section_id: str  # e.g., "chapter_2.consent"
    chapter: str
    chapter_title: str
    section: str
    section_title: str
    question_count: int
    questions: list[QuestionSchema]


class ResponseSubmit(BaseModel):
    question_id: str
    answer: AnswerLiteral
    notes: str | None = None
    evidence_reference: str | None = None
    na_reason: str | None = None  # "not_applicable_confirmed" | "not_applicable_assumed" | "deferred"
    confidence: ConfidenceLiteral | None = None

    @field_validator("question_id")
    @classmethod
    def validate_question_id(cls, value: str) -> str:
        if not QUESTION_ID_PATTERN.match(value):
            raise ValueError("question_id must be a valid questionnaire or follow-up ID")
        return value


class BulkResponseSubmit(BaseModel):
    responses: list[ResponseSubmit]


class ResponseOut(BaseModel):
    id: str
    question_id: str
    answer: str
    notes: str | None
    evidence_reference: str | None
    na_reason: str | None = None
    confidence: str | None = None

    model_config = {"from_attributes": True}
