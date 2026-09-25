"""Deterministic control batching for large registry-defined frameworks."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.frameworks.registry import FrameworkRegistry
from app.frameworks.schema import Control


@dataclass(frozen=True)
class ControlBatch:
    index: int
    count: int
    domain_key: str
    section_keys: tuple[str, ...]
    control_ids: tuple[str, ...]

    @property
    def label(self) -> str:
        return f"{self.index}/{self.count}"


def _merge_batches(first: dict, second: dict) -> dict:
    section_keys = list(first["section_keys"])
    for section_key in second["section_keys"]:
        if section_key not in section_keys:
            section_keys.append(section_key)
    return {
        "domain_key": first["domain_key"],
        "section_keys": section_keys,
        "control_ids": first["control_ids"] + second["control_ids"],
    }


def _domain_batches(domain_key: str, sections, max_controls: int) -> list[dict]:
    batches: list[dict] = []
    current: dict | None = None

    for section_key, section in sections.items():
        controls: list[Control] = list(section.controls)
        chunks = [
            controls[start : start + max_controls]
            for start in range(0, len(controls), max_controls)
        ]
        if len(chunks) > 1 and len(chunks[-1]) == 1:
            chunks[-2].extend(chunks[-1])
            chunks.pop()

        for chunk in chunks:
            if not chunk:
                continue
            if current and len(current["control_ids"]) + len(chunk) > max_controls:
                batches.append(current)
                current = None
            if current is None:
                current = {
                    "domain_key": domain_key,
                    "section_keys": [section_key],
                    "control_ids": [control.id for control in chunk],
                }
            else:
                if section_key not in current["section_keys"]:
                    current["section_keys"].append(section_key)
                current["control_ids"].extend(control.id for control in chunk)

    if current:
        batches.append(current)

    # A singleton batch is not usable by the desk-review prompt. Keep the
    # merge within this domain so batches never cross a domain boundary.
    index = 0
    while index < len(batches):
        if len(batches[index]["control_ids"]) != 1 or len(batches) == 1:
            index += 1
            continue
        if index > 0:
            batches[index - 1] = _merge_batches(batches[index - 1], batches[index])
            batches.pop(index)
        elif index + 1 < len(batches):
            batches[index + 1] = _merge_batches(batches[index], batches[index + 1])
            batches.pop(index)
        else:
            index += 1

    return batches


def control_batches(framework_id: str) -> tuple[ControlBatch, ...]:
    """Return deterministic domain/section batches for a large framework."""
    framework = FrameworkRegistry.get(framework_id)
    if framework.control_count() <= settings.llm_batch_threshold_controls:
        return ()

    max_controls = settings.llm_batch_max_controls
    if max_controls < 1:
        raise ValueError("llm_batch_max_controls must be at least 1")

    raw_batches: list[dict] = []
    for domain_key, domain in framework.domains.items():
        raw_batches.extend(_domain_batches(domain_key, domain.sections, max_controls))

    count = len(raw_batches)
    return tuple(
        ControlBatch(
            index=index,
            count=count,
            domain_key=batch["domain_key"],
            section_keys=tuple(batch["section_keys"]),
            control_ids=tuple(batch["control_ids"]),
        )
        for index, batch in enumerate(raw_batches, start=1)
    )
