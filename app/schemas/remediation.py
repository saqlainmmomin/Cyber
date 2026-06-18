from datetime import datetime
from typing import Literal

from pydantic import BaseModel


RemediationStatus = Literal["open", "in_progress", "closed", "accepted_risk"]


class RemediationUpdate(BaseModel):
    remediation_status: RemediationStatus | None = None
    remediation_owner: str | None = None
    remediation_target_date: datetime | None = None
    remediation_notes: str | None = None


class RemediationSummary(BaseModel):
    open: int = 0
    in_progress: int = 0
    closed: int = 0
    accepted_risk: int = 0
    total: int = 0
