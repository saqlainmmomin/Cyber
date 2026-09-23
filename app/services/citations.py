"""Structured citations for immutable Evidence versions.

D-P2-2-A makes validated JSON arrays in conclusion revisions and desk-review findings the sole citation store; the standalone citations table is schema drift and is dropped.

D-P2-2-B closes the location vocabulary to verified character spans into immutable extracted text and explicit whole-item references; fabricated page or section references are not citations.

D-P2-2-C reimplements the analyzer's quote-grounding normalization with an offset map, without changing the analyzer, so accepted quotes resolve to raw extracted-text spans.

D-P2-2-D preserves the distinction between NULL (not captured) and the JSON array [] (captured with no source-grounded citation); writers in this module always write arrays.
"""

from __future__ import annotations

import json
import logging
import re
from array import array
from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.orm import Session

from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.services.evidence import active_versions_in_scope

logger = logging.getLogger(__name__)

LOCATION_TYPES = ("text_span", "whole_item")
CITATION_KEYS = ("evidence_version_id", "location_type", "location_ref", "excerpt")
WHOLE_ITEM_REF = "whole"
MAX_EXCERPT_CHARS = 2000
_TEXT_SPAN_REF = re.compile(r"^chars:(0|[1-9]\d*)-(0|[1-9]\d*)$")
_QUOTE_TABLE = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})
_HYPHEN_BREAK = re.compile(r"-\s*\n\s*")


class CitationError(Exception):
    status_code = 422

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class CitableSource:
    evidence_id: str
    version_id: str
    filename: str
    text: str


def normalize_with_offsets(text: str) -> tuple[str, list[int]]:
    removed = [False] * len(text)
    for match in _HYPHEN_BREAK.finditer(text):
        for index in range(match.start(), match.end()):
            removed[index] = True

    normalized: list[str] = []
    offsets: list[int] = []
    pending: int | None = None
    for index, raw_char in enumerate(text):
        if removed[index]:
            continue
        char = raw_char.translate(_QUOTE_TABLE)
        if char.isspace():
            if normalized and pending is None:
                pending = index
            continue
        if pending is not None:
            normalized.append(" ")
            offsets.append(pending)
            pending = None
        # Per-character lower() intentionally mirrors the grounding rules for
        # this corpus while keeping one raw offset per normalized character.
        lowered = char.lower()
        normalized.extend(lowered)
        offsets.extend([index] * len(lowered))
    return "".join(normalized), offsets


@lru_cache(maxsize=16)
def _normalized_source(text: str) -> tuple[str, array]:
    normalized, offsets = normalize_with_offsets(text)
    return normalized, array("l", offsets)


def locate_excerpt(text: str, excerpt: str) -> tuple[int, int] | None:
    normalized_excerpt, _ = normalize_with_offsets(excerpt)
    if not normalized_excerpt:
        return None
    normalized_text, offsets = _normalized_source(text)
    index = normalized_text.find(normalized_excerpt)
    if index == -1:
        return None
    return offsets[index], offsets[index + len(normalized_excerpt) - 1] + 1


def text_span_citation(source: CitableSource, excerpt: str) -> dict | None:
    span = locate_excerpt(source.text, excerpt)
    if span is None:
        return None
    start, end = span
    if end - start > MAX_EXCERPT_CHARS:
        return None
    return {
        "evidence_version_id": source.version_id,
        "location_type": "text_span",
        "location_ref": f"chars:{start}-{end}",
        "excerpt": source.text[start:end],
    }


def whole_item_citation(source: CitableSource) -> dict:
    return {
        "evidence_version_id": source.version_id,
        "location_type": "whole_item",
        "location_ref": WHOLE_ITEM_REF,
        "excerpt": "",
    }


def citable_sources(db: Session, assessment_id: str) -> list[CitableSource]:
    return [
        CitableSource(
            evidence_id=evidence.id,
            version_id=version.id,
            filename=version.original_filename,
            text=version.extracted_text or "",
        )
        for evidence, version in active_versions_in_scope(db, assessment_id)
    ]


def cite_quotes(
    sources: list[CitableSource],
    quotes: list[str],
    *,
    preferred_filename: str | None = None,
) -> list[dict]:
    if preferred_filename is None:
        candidates = list(sources)
    else:
        candidates = [s for s in sources if s.filename == preferred_filename]
        candidates.extend(s for s in sources if s.filename != preferred_filename)

    citations: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    dropped = 0
    for quote in quotes:
        if not quote.strip():
            continue
        citation = next(
            (
                candidate_citation
                for source in candidates
                if (candidate_citation := text_span_citation(source, quote)) is not None
            ),
            None,
        )
        if citation is None:
            dropped += 1
            continue
        identity = (
            citation["evidence_version_id"],
            citation["location_type"],
            citation["location_ref"],
        )
        if identity in seen:
            continue
        seen.add(identity)
        citations.append(citation)
    if dropped:
        logger.warning("Citation grounding dropped %d ungrounded quote(s)", dropped)
    return citations


def validate_citations(
    db: Session,
    citations: list[dict],
    *,
    assessment_id: str,
) -> list[dict]:
    if not isinstance(citations, list):
        raise CitationError("Citations must be a list.")

    expected_keys = set(CITATION_KEYS)
    for index, citation in enumerate(citations):
        if not isinstance(citation, dict) or set(citation) != expected_keys:
            raise CitationError(
                f"Citation {index}: must have exactly the keys "
                f"{', '.join(CITATION_KEYS)}."
            )
    for index, citation in enumerate(citations):
        if not all(isinstance(citation[key], str) for key in CITATION_KEYS):
            raise CitationError(f"Citation {index}: all fields must be strings.")

    version_ids = {citation["evidence_version_id"] for citation in citations}
    versions = (
        db.query(EvidenceVersion).filter(EvidenceVersion.id.in_(version_ids)).all()
        if version_ids
        else []
    )
    version_by_id = {version.id: version for version in versions}
    evidence_ids = {version.evidence_id for version in versions}
    evidence_rows = (
        db.query(Evidence).filter(Evidence.id.in_(evidence_ids)).all()
        if evidence_ids
        else []
    )
    evidence_by_id = {evidence.id: evidence for evidence in evidence_rows}
    mapped_ids = {
        evidence_id
        for (evidence_id,) in (
            db.query(EvidenceUse.evidence_id)
            .filter(
                EvidenceUse.assessment_id == assessment_id,
                EvidenceUse.evidence_id.in_(evidence_ids),
            )
            .all()
            if evidence_ids
            else []
        )
    }

    normalized: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for index, citation in enumerate(citations):
        version_id = citation["evidence_version_id"]
        location_type = citation["location_type"]
        location_ref = citation["location_ref"]
        excerpt = citation["excerpt"]
        if location_type not in LOCATION_TYPES:
            raise CitationError(f"Citation {index}: unknown location_type '{location_type}'.")

        version = version_by_id.get(version_id)
        if version is None:
            raise CitationError(f"Citation {index}: evidence version '{version_id}' not found.")
        evidence = evidence_by_id.get(version.evidence_id)
        if (
            evidence is None
            or version.status != "active"
            or evidence.status != "active"
        ):
            raise CitationError(
                f"Citation {index}: evidence version '{version_id}' is not active "
                "and cannot be cited."
            )
        if evidence.assessment_id != assessment_id and evidence.id not in mapped_ids:
            raise CitationError(
                f"Citation {index}: evidence version '{version_id}' is not in scope "
                "for this assessment."
            )
        if location_type == "whole_item":
            if location_ref != WHOLE_ITEM_REF or excerpt != "":
                raise CitationError(
                    f"Citation {index}: whole_item citations must have location_ref "
                    "'whole' and an empty excerpt."
                )
        else:
            if len(excerpt) > MAX_EXCERPT_CHARS:
                raise CitationError(f"Citation {index}: excerpt exceeds 2000 characters.")
            match = _TEXT_SPAN_REF.fullmatch(location_ref)
            if match is None:
                raise CitationError(
                    f"Citation {index}: invalid text_span location_ref '{location_ref}'."
                )
            start, end = (int(value) for value in match.groups())
            extracted_text = version.extracted_text or ""
            if start >= end or end > len(extracted_text):
                raise CitationError(
                    f"Citation {index}: invalid text_span location_ref '{location_ref}'."
                )
            if excerpt != extracted_text[start:end]:
                raise CitationError(
                    f"Citation {index}: excerpt does not match the cited evidence text."
                )

        identity = (version_id, location_type, location_ref)
        if identity in seen:
            raise CitationError(f"Citation {index}: duplicate citation.")
        seen.add(identity)
        normalized.append({key: citation[key] for key in CITATION_KEYS})
    return normalized


def dumps_citations(citations: list[dict]) -> str:
    return json.dumps(
        [{key: citation[key] for key in CITATION_KEYS} for citation in citations],
        sort_keys=True,
    )


def loads_citations(raw: str | None) -> list[dict]:
    if raw is None:
        return []
    citations = json.loads(raw)
    if not isinstance(citations, list):
        raise CitationError("Stored citations are not a JSON array.")
    return citations


def attach_citations(
    db: Session,
    *,
    revision: ConclusionRevision,
    citations: list[dict],
) -> ConclusionRevision:
    if revision.citations_json is not None:
        raise CitationError("Citations on a conclusion revision are immutable once set.")
    conclusion = db.get(Conclusion, revision.conclusion_id)
    if conclusion is None:
        raise CitationError("Conclusion revision is not linked to an existing conclusion.")
    normalized = validate_citations(db, citations, assessment_id=conclusion.assessment_id)
    revision.citations_json = dumps_citations(normalized)
    db.flush()
    return revision


def resolve_citations(db: Session, raw: str | None) -> list[dict]:
    citations = loads_citations(raw)
    if not citations:
        return []
    version_ids = {citation["evidence_version_id"] for citation in citations}
    versions = db.query(EvidenceVersion).filter(EvidenceVersion.id.in_(version_ids)).all()
    version_by_id = {version.id: version for version in versions}
    evidence_ids = {version.evidence_id for version in versions}
    evidence_rows = (
        db.query(Evidence).filter(Evidence.id.in_(evidence_ids)).all()
        if evidence_ids
        else []
    )
    evidence_by_id = {evidence.id: evidence for evidence in evidence_rows}

    resolved: list[dict] = []
    for citation in citations:
        version = version_by_id.get(citation["evidence_version_id"])
        evidence = evidence_by_id.get(version.evidence_id) if version else None
        if version is None or evidence is None:
            resolved.append(
                {
                    **citation,
                    "resolved": False,
                    "evidence_id": None,
                    "filename": None,
                    "version_number": None,
                    "version_status": None,
                    "evidence_status": None,
                    "is_current": False,
                }
            )
            continue
        resolved.append(
            {
                **citation,
                "resolved": True,
                "evidence_id": evidence.id,
                "filename": version.original_filename,
                "version_number": version.version_number,
                "version_status": version.status,
                "evidence_status": evidence.status,
                "is_current": version.status == "active" and evidence.status == "active",
            }
        )
    return resolved
