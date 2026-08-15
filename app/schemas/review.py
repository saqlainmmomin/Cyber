from typing import Literal

from pydantic import BaseModel


class ReviewItemUpdate(BaseModel):
    review_status: Literal["accepted", "rejected"] | None = None
    compliance_status: str | None = None
    gap_description: str | None = None
    risk_level: str | None = None
    reviewer_notes: str | None = None


class ReviewApproval(BaseModel):
    reviewer_name: str


class ReviewRejection(BaseModel):
    reviewer_name: str
    rejection_reason: str | None = None
