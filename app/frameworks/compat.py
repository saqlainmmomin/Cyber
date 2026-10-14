"""
Backward-compatible helpers that delegate to the framework registry.

Drop-in replacements for direct imports from app.dpdpa.framework.
Callers can switch imports gradually without changing their logic.
"""

from __future__ import annotations

from app.frameworks.registry import FrameworkRegistry


def get_all_requirements(framework_id: str) -> list[dict]:
    """
    Drop-in replacement for app.dpdpa.framework.get_all_requirements().

    Returns enriched control dicts with chapter/section metadata.
    """
    return FrameworkRegistry.get_all_controls_enriched(framework_id)


def get_requirement_count(framework_id: str) -> int:
    return FrameworkRegistry.get(framework_id).control_count()


def get_framework_dict(framework_id: str) -> dict:
    """
    Returns the nested dict format (chapter → section → requirements)
    used by scoring.py and prompts.py.
    """
    return FrameworkRegistry.get(framework_id).as_legacy_framework_dict()


def get_root_cause_clusters(framework_id: str) -> dict:
    return FrameworkRegistry.get(framework_id).root_cause_clusters


def get_dependencies(framework_id: str) -> dict[str, list[str]]:
    return FrameworkRegistry.get(framework_id).dependencies
