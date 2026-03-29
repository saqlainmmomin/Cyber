"""Schemas for Phase 1 context gathering."""

from pydantic import BaseModel


class ContextAnswer(BaseModel):
    question_id: str
    answer: str | list[str]  # single_select/text → str, multi_select → list[str]


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
