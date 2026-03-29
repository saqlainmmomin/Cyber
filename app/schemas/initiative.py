from pydantic import BaseModel


class InitiativeOut(BaseModel):
    initiative_id: str
    title: str
    root_cause: str
    root_cause_category: str
    requirements_addressed: list[str]
    combined_effort: str
    combined_timeline_weeks: int
    priority: int
    budget_estimate_band: str | None
    suggested_approach: str
