from typing import Literal

from pydantic import BaseModel, Field


class ConclusionDecisionIn(BaseModel):
    expected_version: int
    reviewer_name: str = ""
    reason: str = Field(default="", max_length=2000)


class ConclusionEditIn(ConclusionDecisionIn):
    outcome: Literal[
        "compliant",
        "partially_compliant",
        "non_compliant",
        "not_applicable",
        "insufficient_evidence",
    ]
    rationale: str
    gaps_identified: str
    risk_level: Literal["", "critical", "high", "medium", "low"]
    recommended_action: str
