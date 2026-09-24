from datetime import datetime
from typing import Literal

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


class FrameworkScoreOut(BaseModel):
    status: Literal["scored", "failed"] = "scored"
    overall_score: float | None
    overall_rating: str | None
    domain_scores: dict[str, ChapterScore]


class ReportOut(BaseModel):
    id: str
    assessment_id: str
    framework_scores: dict[str, FrameworkScoreOut]
    chapter_scores: dict[str, ChapterScore]
    executive_summary: str
    gap_items: list[GapItemOut]
    remediation_roadmap: dict[str, list[GapItemOut]]
    initiatives: list[InitiativeOut]
    generated_at: datetime


class ReportSummary(BaseModel):
    framework_scores: dict[str, FrameworkScoreOut]
    requirement_counts: dict[str, int]
    total_requirements: int
    compliant: int
    partially_compliant: int
    non_compliant: int
    not_assessed: int
    critical_gaps: int
    high_gaps: int
    chapter_scores: dict[str, ChapterScore]
