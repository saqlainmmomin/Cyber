"""Strict schemas for validation company packs."""

from __future__ import annotations

from enum import Enum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.schemas.assessment import CompanySize, DocumentCategory, Industry

FrameworkId = Literal["dpdpa", "iso27001", "nist_csf"]
Outcome = Literal[
    "compliant",
    "partially_compliant",
    "non_compliant",
    "not_applicable",
    "insufficient_evidence",
]
AnswerValue = Literal[
    "fully_implemented",
    "partially_implemented",
    "planned",
    "not_implemented",
    "not_applicable",
]
GapClass = Literal[
    "honest_gap",
    "overclaim",
    "cross_document",
    "chained_dependency",
    "temporal",
    "quantitative",
    "wrong_citation",
    "joint_impossibility",
    "substance_over_form",
    "cross_framework_divergence",
    "artifact_discrepancy",
    "stale_evidence",
    "scope_coverage",
]
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9-]+$")]
ArtifactId = Annotated[str, StringConstraints(pattern=r"^E\d{2}$")]
GapId = Annotated[str, StringConstraints(pattern=r"^G\d{2}$")]
DecoyId = Annotated[str, StringConstraints(pattern=r"^D\d{2}$")]
TrailSource = Annotated[str, StringConstraints(pattern=r"^(?:evidence:E\d{2}|(?:answer|context|scope):[^\s:]+)$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CompanyMeta(StrictModel):
    slug: Slug
    company_name: str
    industry: Industry
    company_size: CompanySize
    engagement_name: str
    description: str
    frameworks: list[FrameworkId] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_frameworks(self):
        if len(self.frameworks) != len(set(self.frameworks)):
            raise ValueError("frameworks must not contain duplicates")
        return self


class IntakeAnswers(StrictModel):
    context: dict[str, str | list[str]]
    scope: dict[str, str]
    screening: dict[str, str] | None
    magic_link_items: list[str]


class AnswerEntry(StrictModel):
    answer: AnswerValue
    notes: str = ""
    evidence_reference: str = ""


class QuestionnaireAnswers(StrictModel):
    answers: dict[str, AnswerEntry]


class ControlRef(StrictModel):
    framework_id: FrameworkId
    requirement_id: str


class TrailEntry(StrictModel):
    source: TrailSource
    locator: str
    fact: str


class ProseSection(StrictModel):
    heading: str
    paragraphs: list[str]


class ProseContent(StrictModel):
    title: str
    subtitle: str
    sections: list[ProseSection]


class TableContent(StrictModel):
    title: str
    subtitle: str
    preamble: list[str]
    columns: list[str] = Field(min_length=1)
    rows: list[list[str]]
    footer: list[str]

    @model_validator(mode="after")
    def row_widths_match(self):
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("rows must have the same number of cells as columns")
        return self


class LinesContent(StrictModel):
    title: str
    lines: list[str]


class ExternalImageContent(StrictModel):
    image_path: str
    transcript: str


Content = ProseContent | TableContent | LinesContent | ExternalImageContent
RenderKind = Literal["prose", "table", "config", "console", "external_image"]
RenderFormat = Literal["pdf", "docx", "png", "jpg"]


class RenderSpec(StrictModel):
    kind: RenderKind
    format: RenderFormat
    degrade: Literal["none", "scan_light", "scan_heavy"] = "none"


class EvidenceSpec(StrictModel):
    artifact_id: ArtifactId
    filename: str
    category: DocumentCategory
    channel: Literal["consultant_upload", "magic_link"]
    magic_item: str | None = None
    consultant_maps_to: list[ControlRef] = Field(default_factory=list)
    render: RenderSpec
    content: Content

    @model_validator(mode="after")
    def validate_render_content(self):
        kind, fmt = self.render.kind, self.render.format
        allowed = {
            "prose": {"pdf", "docx"},
            "table": {"pdf", "docx", "png"},
            "config": {"pdf", "png"},
            "console": {"png", "jpg"},
            "external_image": {"png", "jpg"},
        }
        content_types = {
            "prose": ProseContent,
            "table": TableContent,
            "config": LinesContent,
            "console": LinesContent,
            "external_image": ExternalImageContent,
        }
        if fmt not in allowed[kind]:
            raise ValueError(f"render.format is not allowed for render.kind={kind}")
        if not isinstance(self.content, content_types[kind]):
            raise ValueError("content must match render.kind")
        if self.render.degrade != "none" and fmt not in {"png", "jpg"}:
            raise ValueError("render.degrade is supported only for png and jpg")
        if PurePosixPath(self.filename).name != self.filename:
            raise ValueError("filename must not contain a directory")
        if PurePosixPath(self.filename).suffix.lower().lstrip(".") != fmt:
            raise ValueError("filename extension must match render.format")
        if self.channel == "magic_link" and not self.magic_item:
            raise ValueError("magic_item is required for channel=magic_link")
        if self.channel == "consultant_upload" and self.magic_item is not None:
            raise ValueError("magic_item is only valid for channel=magic_link")
        if self.channel == "magic_link" and not self.consultant_maps_to:
            raise ValueError("consultant_maps_to is required for channel=magic_link")
        return self


class ControlTruth(StrictModel):
    default: Outcome
    overrides: dict[str, Outcome]


class PlantedGap(StrictModel):
    gap_id: GapId
    requirements: list[ControlRef] = Field(min_length=1)
    gap_class: GapClass
    actual_status: Literal["non_compliant", "partially_compliant"]
    surface_answer: AnswerValue
    probing_depth: int = Field(ge=1, le=5)
    severity_expected: Literal["high", "medium", "low"]
    description: str
    evidence_trail: list[TrailEntry] = Field(min_length=1)
    key_facts: list[str] = Field(min_length=1, max_length=4)
    what_followup_should_ask: str


class Decoy(StrictModel):
    decoy_id: DecoyId
    requirements: list[ControlRef] = Field(min_length=1)
    why_it_looks_like_a_gap: str
    why_it_is_compliant: str
    evidence_trail: list[TrailEntry] = Field(min_length=1)


class CleanControl(StrictModel):
    framework_id: FrameworkId
    requirement_id: str
    supporting_artifacts: list[ArtifactId]


class AnswerKey(StrictModel):
    schema_version: Literal[1]
    company_slug: Slug
    control_truth: dict[FrameworkId, ControlTruth]
    planted_gaps: list[PlantedGap]
    decoys: list[Decoy]
    clean_controls: list[CleanControl]
    authoring_notes: str

    @model_validator(mode="after")
    def validate_control_truth(self):
        gap_requirements: dict[tuple[str, str], str] = {}
        decoy_requirements: set[tuple[str, str]] = set()
        for gap in self.planted_gaps:
            for ref in gap.requirements:
                key = (ref.framework_id, ref.requirement_id)
                gap_requirements[key] = gap.actual_status
        for decoy in self.decoys:
            decoy_requirements.update((ref.framework_id, ref.requirement_id) for ref in decoy.requirements)
        overlap = gap_requirements.keys() & decoy_requirements
        if overlap:
            fw, requirement = sorted(overlap)[0]
            raise ValueError(f"requirement {fw}/{requirement} cannot be both a planted gap and decoy")

        for gap in self.planted_gaps:
            for ref in gap.requirements:
                truth = self.control_truth.get(ref.framework_id)
                if truth is None or truth.overrides.get(ref.requirement_id) != gap.actual_status:
                    raise ValueError(f"control_truth override must match planted gap {gap.gap_id} requirement {ref.requirement_id}")
        for decoy in self.decoys:
            for ref in decoy.requirements:
                truth = self.control_truth.get(ref.framework_id)
                if truth is None or truth.overrides.get(ref.requirement_id) != "compliant":
                    raise ValueError(f"control_truth override must be compliant for decoy {decoy.decoy_id} requirement {ref.requirement_id}")
        for control in self.clean_controls:
            truth = self.control_truth.get(control.framework_id)
            if truth is None or truth.overrides.get(control.requirement_id, truth.default) != "compliant":
                raise ValueError(f"clean control {control.requirement_id} must resolve to compliant")
        return self


def validate_pack_relations(
    company: CompanyMeta,
    intake: IntakeAnswers,
    evidence: list[EvidenceSpec],
    answer_key: AnswerKey | None = None,
) -> None:
    """Validate relationships whose fields live in separate pack files."""
    if company.frameworks == ["dpdpa"]:
        if intake.screening is None:
            raise ValueError("screening is required for DPDPA-only packs")
    elif intake.screening is not None:
        raise ValueError("screening must be null unless frameworks is [dpdpa]")
    if len({item.artifact_id for item in evidence}) != len(evidence):
        raise ValueError("artifact_id values must be unique")
    for item in evidence:
        if item.channel == "magic_link" and item.magic_item not in intake.magic_link_items:
            raise ValueError(f"magic_item {item.magic_item!r} must match a magic_link_items entry")
    if answer_key and answer_key.company_slug != company.slug:
        raise ValueError("answer_key.company_slug must match company.slug")


class OutcomeName(str, Enum):
    compliant = "compliant"
    partially_compliant = "partially_compliant"
    non_compliant = "non_compliant"
    not_applicable = "not_applicable"
    insufficient_evidence = "insufficient_evidence"
