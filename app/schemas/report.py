from datetime import datetime

from pydantic import BaseModel

from app.schemas.initiative import InitiativeOut


class GapItemOut(BaseModel):
    requirement_id: str
    chapter: str
    requirement_title: str
    compliance_status: str
    current_state: str
    gap_description: str
    risk_level: str
    remediation_action: str
    remediation_priority: int
    remediation_effort: str
    timeline_weeks: int
    maturity_level: int | None = None
    root_cause_category: str | None = None
    evidence_quote: str | None = None
    dependencies: list[str] | None = None  # Prerequisite requirement IDs


class ChapterScore(BaseModel):
    score: float
    rating: str
    title: str


class ReportOut(BaseModel):
    id: str
    assessment_id: str
    overall_score: float
    overall_rating: str
    chapter_scores: dict[str, ChapterScore]
    executive_summary: str
    gap_items: list[GapItemOut]
    remediation_roadmap: dict[str, list[GapItemOut]]
    initiatives: list[InitiativeOut]
    generated_at: datetime


class ReportSummary(BaseModel):
    overall_score: float
    overall_rating: str
    total_requirements: int
    compliant: int
    partially_compliant: int
    non_compliant: int
    not_assessed: int
    critical_gaps: int
    high_gaps: int
    chapter_scores: dict[str, ChapterScore]
