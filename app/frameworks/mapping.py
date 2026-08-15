"""
Unified Control Cluster (UCC) — cross-framework control mapping.

A UCC groups controls from different frameworks that address the same
security/privacy concern. This enables de-duplicated questionnaires
where one question covers overlapping controls across frameworks.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MappedControl:
    """A control within a UCC, with optional framework-specific delta."""

    framework_id: str
    control_id: str
    specificity_delta: str | None = None  # what this framework uniquely adds


@dataclass
class UnifiedControlCluster:
    """Group of controls across frameworks that address the same concern."""

    cluster_id: str  # e.g. "UCC.ACCESS_CONTROL.001"
    topic: str  # human-readable topic name
    domain_group: str  # for ordering: "governance", "data_protection", "security", etc.
    tags: list[str] = field(default_factory=list)
    controls: list[MappedControl] = field(default_factory=list)
    primary_question: str = ""
    primary_guidance: str = ""

    @property
    def framework_ids(self) -> set[str]:
        return {mc.framework_id for mc in self.controls}

    @property
    def control_ids(self) -> set[str]:
        return {mc.control_id for mc in self.controls}

    @property
    def max_criticality(self) -> str:
        """Highest criticality across member controls (for ordering)."""
        # Will be set by cluster_engine based on registry lookups
        return getattr(self, "_max_criticality", "medium")

    def controls_for_framework(self, framework_id: str) -> list[MappedControl]:
        return [mc for mc in self.controls if mc.framework_id == framework_id]

    def has_framework(self, framework_id: str) -> bool:
        return framework_id in self.framework_ids

    def follow_ups_for(self, framework_id: str) -> list[MappedControl]:
        """Controls with specificity deltas for a given framework."""
        return [
            mc
            for mc in self.controls
            if mc.framework_id == framework_id and mc.specificity_delta
        ]
