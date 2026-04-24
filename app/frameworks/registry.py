"""
Framework registry — singleton that holds all registered compliance frameworks.

Frameworks register themselves on app startup. The rest of the system accesses
framework definitions exclusively through this registry.
"""

from __future__ import annotations

import logging

from app.frameworks.schema import Control, FrameworkDefinition

logger = logging.getLogger(__name__)


class FrameworkRegistry:
    """Thread-safe registry of compliance framework definitions."""

    _frameworks: dict[str, FrameworkDefinition] = {}

    @classmethod
    def register(cls, fw: FrameworkDefinition) -> None:
        if fw.id in cls._frameworks:
            logger.warning("Framework '%s' already registered — replacing", fw.id)
        cls._frameworks[fw.id] = fw
        logger.info(
            "Registered framework: %s v%s (%d controls)",
            fw.name,
            fw.version,
            fw.control_count(),
        )

    @classmethod
    def get(cls, framework_id: str) -> FrameworkDefinition:
        if framework_id not in cls._frameworks:
            raise KeyError(
                f"Framework '{framework_id}' not registered. "
                f"Available: {list(cls._frameworks.keys())}"
            )
        return cls._frameworks[framework_id]

    @classmethod
    def get_or_none(cls, framework_id: str) -> FrameworkDefinition | None:
        return cls._frameworks.get(framework_id)

    @classmethod
    def available(cls) -> list[dict]:
        """List registered frameworks with metadata."""
        return [
            {
                "id": fw.id,
                "name": fw.name,
                "version": fw.version,
                "description": fw.description,
                "control_count": fw.control_count(),
                "domain_count": len(fw.domains),
            }
            for fw in cls._frameworks.values()
        ]

    @classmethod
    def is_registered(cls, framework_id: str) -> bool:
        return framework_id in cls._frameworks

    @classmethod
    def all_ids(cls) -> list[str]:
        return list(cls._frameworks.keys())

    @classmethod
    def get_all_controls(cls, framework_id: str) -> list[Control]:
        return cls.get(framework_id).all_controls()

    @classmethod
    def get_all_controls_enriched(cls, framework_id: str) -> list[dict]:
        """Get controls with domain/section metadata — matches legacy get_all_requirements() format."""
        return cls.get(framework_id).all_controls_enriched()

    @classmethod
    def reset(cls) -> None:
        """Clear all registered frameworks (for testing)."""
        cls._frameworks.clear()
