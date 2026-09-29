"""Deterministic detection of instruction-like evidence claims."""

from __future__ import annotations

import re
from collections.abc import Mapping

from app.frameworks.registry import FrameworkRegistry

INJECTION_PATTERNS_VERSION = "p6-5.1"
CONTEXT_CHARS = 300
CUT_MARK = "…"
MARKER_KEYS = (
    "override_instructions",
    "role_marker",
    "delimiter_forgery",
    "prompt_structure_forgery",
    "model_address",
    "verdict_directive",
    "output_field_directive",
)

_PATTERNS = {
    "override_instructions": re.compile(
        r"\b(?:ignore|disregard|forget|override|bypass)\s+"
        r"(?:(?:all|any|the|your|of)\s+)*"
        r"(?:previous|prior|above|earlier|preceding|system|original)\s+"
        r"(?:instructions?|prompts?|directions|directives|guidelines|rules)\b"
        r"|\b(?:ignore|disregard|forget)\s+(?:all\s+|any\s+)?your\s+"
        r"(?:instructions?|prompts?|guidelines|rules)\b",
        re.I,
    ),
    "role_marker": re.compile(
        r"(?m)^[ \t]*(?:SYSTEM|ASSISTANT|DEVELOPER)[ \t]*:"
        r"|<\|[a-z_]+\|>"
        r"|\[/?INST\]"
    ),
    "delimiter_forgery": re.compile(r"<<<|>>>"),
    "prompt_structure_forgery": re.compile(
        r"\[CLM-[0-9a-f]{16}\]"
        r"|^[ \t]*#{1,6}[ \t]*(\S+)",
        re.M,
    ),
    "model_address": re.compile(
        r"\byou\s+are\s+(?:now\s+)?(?:an?\s+|the\s+)?"
        r"(?:AI\s+(?:assistant|assessor|auditor|reviewer|model)|AI|LLM|"
        r"(?:large\s+)?language\s+model)\b"
        r"|\b(?:note|message|instructions?)\s+(?:to|for)\s+"
        r"(?:the\s+|any\s+)?(?:AI|LLM|(?:large\s+)?language\s+model)"
        r"(?:\s+(?:assessor|auditor|reviewer|system|model|assistant))?\s*[:,.]",
        re.I,
    ),
    "verdict_directive": re.compile(
        r"\b(?:mark|report|rate|treat|classify|record|score|set)\s+"
        r"(?:every|all|each|any|the following|these)\b[^.\n]{0,60}?\bas\s+"
        r"(?:fully\s+|being\s+)?"
        r"(?:compliant|satisfied|met|adequate|passed|effective|not\s+applicable)\b"
        r"(?!\s+or\b)",
        re.I,
    ),
    "output_field_directive": re.compile(
        r"\b(?:risk_level|claim_ids?|gap_statement|compliance_status|"
        r"overall_score|conclusion_outcome|criterion_id|requirement_id)\b",
        re.I,
    ),
}


def _registered_control_ids() -> set[str]:
    return {
        control.id
        for framework_id in FrameworkRegistry.all_ids()
        for control in FrameworkRegistry.get(framework_id).all_controls()
    }


def _structure_forgery(text: str) -> bool:
    if re.search(r"\[CLM-[0-9a-f]{16}\]", text):
        return True
    control_ids = _registered_control_ids()
    for match in re.finditer(r"(?m)^[ \t]*#{1,6}[ \t]*(\S+)", text):
        token = match.group(1).rstrip(":.,;")
        if token in control_ids:
            return True
    return False


def instruction_markers(text: str) -> tuple[str, ...]:
    """Return matching injection marker keys in the fixed contract order."""
    matches: list[str] = []
    for key in MARKER_KEYS:
        if key == "prompt_structure_forgery":
            matched = _structure_forgery(text)
        else:
            matched = _PATTERNS[key].search(text) is not None
        if matched:
            matches.append(key)
    return tuple(matches)


def claim_context(claim, source_text: str | None) -> str:
    """Return the bounded enclosing source line plus the claim statement."""
    if source_text is None or not (
        0 <= claim.start < claim.end <= len(source_text)
    ):
        window = claim.quote
    else:
        line_start = source_text.rfind("\n", 0, claim.start) + 1
        line_end = source_text.find("\n", claim.end)
        if line_end == -1:
            line_end = len(source_text)
        cut_start = max(line_start, claim.start - CONTEXT_CHARS)
        cut_end = min(line_end, claim.end + CONTEXT_CHARS)
        window = source_text[cut_start:cut_end]
        if cut_start != line_start:
            window = CUT_MARK + window
    return window + "\n" + claim.statement


def claim_markers(
    claim,
    source_texts: Mapping[str, str] | None,
) -> tuple[str, ...]:
    """Detect instruction markers in a claim and its bounded source context."""
    source_text = source_texts.get(claim.source_id) if source_texts else None
    return instruction_markers(claim_context(claim, source_text))
