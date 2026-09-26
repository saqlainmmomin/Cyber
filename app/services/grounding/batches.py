"""Deterministic cross-framework extraction batches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.config import settings
from app.frameworks.mappings.clusters import CONTROL_CLUSTERS
from app.frameworks.registry import FrameworkRegistry


@dataclass(frozen=True)
class RequirementBatch:
    index: int
    count: int
    group_keys: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    framework_ids: tuple[str, ...]

    @property
    def label(self) -> str:
        return f"b{self.index}/{self.count}"


def requirement_order(framework_ids: Sequence[str]) -> dict[str, tuple[int, int]]:
    order: dict[str, tuple[int, int]] = {}
    for framework_position, framework_id in enumerate(framework_ids):
        try:
            framework = FrameworkRegistry.get(framework_id)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        for index, control in enumerate(framework.all_controls()):
            order[control.id] = (framework_position, index)
    return order


def extraction_batches(framework_ids: Sequence[str]) -> tuple[RequirementBatch, ...]:
    framework_ids = tuple(framework_ids)
    if len(framework_ids) != len(set(framework_ids)):
        raise ValueError("framework_ids must not contain duplicates")
    order = requirement_order(framework_ids)
    controls_by_framework = {
        framework_id: FrameworkRegistry.get(framework_id).all_controls()
        for framework_id in framework_ids
    }
    known_ids = set(order)
    clustered_ids: set[str] = set()
    groups: list[tuple[str, tuple[str, ...]]] = []
    for cluster in CONTROL_CLUSTERS:
        members = {
            member["control"]
            for member in cluster.get("controls", [])
            if member.get("framework") in framework_ids and member.get("control") in known_ids
        }
        if not members:
            continue
        ids = tuple(sorted(members, key=order.__getitem__))
        clustered_ids.update(ids)
        groups.append((str(cluster["cluster_id"]), ids))

    for framework_id in framework_ids:
        framework = FrameworkRegistry.get(framework_id)
        for domain in framework.domains.values():
            for section_key, section in domain.sections.items():
                ids = tuple(
                    control.id
                    for control in section.controls
                    if control.id not in clustered_ids
                )
                if ids:
                    groups.append((f"{framework_id}:{section_key}", ids))

    maximum = settings.v2_extraction_batch_max_requirements
    if maximum <= 0:
        raise ValueError("v2_extraction_batch_max_requirements must be positive")
    packed: list[tuple[list[str], list[str]]] = []
    for group_key, group_ids in groups:
        for offset in range(0, len(group_ids), maximum):
            piece = list(group_ids[offset:offset + maximum])
            if packed and len(packed[-1][1]) + len(piece) > maximum:
                packed.append(([], []))
            if not packed:
                packed.append(([], []))
            packed[-1][0].append(group_key)
            packed[-1][1].extend(piece)

    count = len(packed)
    result = []
    for index, (group_keys, ids) in enumerate(packed, start=1):
        present = tuple(
            framework_id
            for framework_id in framework_ids
            if any(control.id in ids for control in controls_by_framework[framework_id])
        )
        result.append(
            RequirementBatch(
                index=index,
                count=count,
                group_keys=tuple(group_keys),
                requirement_ids=tuple(sorted(ids, key=order.__getitem__)),
                framework_ids=present,
            )
        )
    return tuple(result)
