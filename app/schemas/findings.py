from datetime import date
from typing import Literal

from pydantic import BaseModel


class FindingCreateIn(BaseModel):
    conclusion_id: str | None = None
    conclusion_version: int
    title: str | None = None
    description: str | None = None
    severity: Literal["critical", "high", "medium", "low"]
    priority: int
    action_title: str | None = None
    action_owner: str | None = None
    action_target_date: date | None = None
    notes: str | None = None
    reviewer_name: str | None = None


class ActionCreateIn(BaseModel):
    title: str | None = None
    owner: str | None = None
    target_date: date | None = None
    notes: str | None = None
    reviewer_name: str | None = None


class ActionStatusIn(BaseModel):
    status: Literal["open", "in_progress", "closed", "verified"]
    expected_history_length: int
    notes: str | None = None
    reviewer_name: str | None = None


class ActionUpdateIn(BaseModel):
    title: str | None = None
    owner: str | None = None
    target_date: date | None = None
    expected_history_length: int
    notes: str | None = None
    reviewer_name: str | None = None
