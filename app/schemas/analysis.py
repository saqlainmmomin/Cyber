from pydantic import BaseModel


class CompletionOverride(BaseModel):
    reason: str
    reviewer_name: str = ""
