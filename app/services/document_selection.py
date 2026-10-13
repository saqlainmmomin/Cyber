"""Select bounded document inputs and record their versioned provenance."""

from app.config import settings


DPDPA_PRIORITY = (
    "privacy_policy", "consent_form", "breach_procedure", "dpia",
    "retention_policy", "processing_records", "data_flow_diagram",
    "vendor_agreement", "other",
)


def ordered_documents(documents: list[dict], ordering: str) -> list[dict]:
    if ordering == "upload":
        return list(documents)
    if ordering == "dpdpa":
        ranks = {category: index for index, category in enumerate(DPDPA_PRIORITY)}
        return sorted(documents, key=lambda doc: ranks.get(doc.get("category"), 99))
    raise ValueError(f"Unknown document ordering: {ordering}")


def select_documents(documents: list[dict], ordering: str = "upload") -> list[dict]:
    """Keep the historical truncation text while sharing the selection policy."""
    remaining = settings.max_total_document_words
    selected = []
    for doc in ordered_documents(documents, ordering):
        if remaining <= 0:
            break
        words = doc.get("text", "").split()
        if len(words) > remaining:
            doc = {**doc, "text": " ".join(words[:remaining]) + "\n\n[... truncated ...]"}
        selected.append(doc)
        remaining -= min(len(words), remaining)
    return selected


def source_identity(doc: dict) -> dict:
    version_id = doc.get("evidence_version_id")
    legacy_id = doc.get("legacy_document_id")
    if version_id is None and legacy_id is None:
        legacy_id = doc.get("id")
    return {
        "evidence_version_id": version_id,
        "legacy_document_id": legacy_id,
        "evidence_id": doc.get("id"),
        "legacy_source_key": f"legacy:{legacy_id}" if version_id is None and legacy_id else None,
        "filename": doc.get("filename", ""),
    }


def selection_manifest(documents: list[dict], ordering: str = "upload") -> list[dict]:
    remaining = settings.max_total_document_words
    entries = []
    for doc in ordered_documents(documents, ordering):
        count = len(doc.get("text", "").split())
        sent = min(count, max(remaining, 0))
        status = "not_read" if remaining <= 0 else "partial" if sent < count else "read"
        entries.append({**source_identity(doc), "status": status, "words_sent": sent, "total_words": count})
        remaining -= sent
    return entries


def _normalized(text: str) -> str:
    import re

    text = re.sub(r"-\s*\n\s*", "", text)
    return re.sub(r"\s+", " ", text.translate(str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'}))).strip().casefold()


def stage_manifest(
    documents: list[dict],
    selected: list[dict],
    *,
    ordering: str,
    control_ids: list[str],
    evidence: dict | None = None,
    reused: dict | None = None,
    extraction_ran: bool = True,
    raw_judge: bool = False,
) -> dict:
    """Describe actual extraction inputs and judge quotes without editing prompts."""
    selection = selection_manifest(documents, ordering)
    sent_entries = [entry for entry in selection if entry["status"] != "not_read"]
    normalized_texts = {
        text: _normalized(text)
        for text in dict.fromkeys(doc.get("text", "") for doc in documents + selected)
    }
    normalized_documents = [(doc, normalized_texts[doc.get("text", "")]) for doc in documents]
    normalized_selected = [normalized_texts[doc.get("text", "")] for doc in selected]
    passages = {}
    for control_id in control_ids:
        quotes = (evidence or {}).get(control_id, [])
        if not quotes:
            continue
        entries = []
        for quote in quotes:
            normalized = _normalized(quote)
            reused_quote = any(normalized == _normalized(item) for item in (reused or {}).get(control_id, []))
            matches = [doc for doc, text in normalized_documents if normalized and normalized in text]
            within_cut = bool(normalized) and any(normalized in text for text in normalized_selected)
            for doc in matches:
                identity = source_identity(doc)
                entries.append({**identity, "quote": quote, "reused_from_desk_review": reused_quote, "outside_cut": not within_cut})
            if not matches:
                entries.append({**source_identity({}), "quote": quote, "reused_from_desk_review": reused_quote, "outside_cut": False, "source_unresolved": True})
        passages[control_id] = entries
    return {
        "schema_version": 1,
        "ordering": ordering,
        "selection": selection,
        "extraction": {"mode": "documents" if extraction_ran else "reused_desk_review" if reused else "not_run", "documents": sent_entries if extraction_ran else []},
        "judge": {"documents": sent_entries if raw_judge else [], "passages": passages},
    }
