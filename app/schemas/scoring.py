from typing import Literal

from pydantic import BaseModel, Field, model_validator


Status = Literal[
    "not_implemented",
    "partial",
    "implemented",
    "not_applicable",
    "unknown",
]
MaturityRating = Literal["M0", "M1", "M2", "M3", "M4", "M5"]


class ClusterVerdict(BaseModel):
    cluster_id: str
    status: Status
    score: float = Field(ge=0.0, le=5.0)
    reasoning: str
    evidence_ids: list[str]

    @model_validator(mode="after")
    def validate_deterministic_score(self):
        expected = {
            "not_implemented": 0.0,
            "partial": 2.5,
            "implemented": 5.0,
            "not_applicable": 5.0,
            "unknown": 0.0,
        }[self.status]
        if self.score != expected:
            raise ValueError(f"score for {self.status} must be {expected}")
        return self


class FrameworkScore(BaseModel):
    framework_id: str
    overall_score: float = Field(ge=0.0, le=5.0)
    overall_rating: MaturityRating
    by_domain: dict[str, float]
    control_count: int = Field(ge=0)
    covered_control_count: int = Field(ge=0)
    contributing_clusters: list[str]


class CombinedScore(BaseModel):
    overall_score: float = Field(ge=0.0, le=5.0)
    overall_rating: MaturityRating
    by_framework: dict[str, FrameworkScore]
    unique_clusters: int = Field(ge=0)
    total_controls_evaluated: int = Field(ge=0)


class ScoringResult(BaseModel):
    """Top-level return of scoring.score() for a multi-framework assessment."""

    per_framework: dict[str, FrameworkScore]
    combined: CombinedScore
    cluster_verdicts: dict[str, ClusterVerdict]

    @model_validator(mode="after")
    def validate_derived_views(self):
        if self.combined.unique_clusters != len(self.cluster_verdicts):
            raise ValueError("combined.unique_clusters must match cluster_verdicts")
        if set(self.per_framework) != {
            score.framework_id for score in self.per_framework.values()
        }:
            raise ValueError("per_framework keys must match framework_id values")
        if self.combined.by_framework != self.per_framework:
            raise ValueError("combined.by_framework must equal per_framework")

        if len(self.per_framework) == 1:
            only_score = next(iter(self.per_framework.values()))
            if (
                self.combined.overall_score != only_score.overall_score
                or self.combined.overall_rating != only_score.overall_rating
                or self.combined.total_controls_evaluated != only_score.covered_control_count
            ):
                raise ValueError(
                    "single-framework combined values must equal the framework score"
                )
        return self
