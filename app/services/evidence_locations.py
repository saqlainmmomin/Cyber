"""Human wording and links shared by evidence records and citations."""
from urllib.parse import urlencode


def location_label(ref: str) -> str:
    if ref == "whole":
        return "Whole document"
    if ref.startswith("page:"):
        return "Page " + ref[5:]
    if ref.startswith("chars:"):
        return "Characters " + ref[6:].replace("-", "–", 1)
    return ref


def cited_href(evidence_id: str, version_id: str, ref: str) -> str:
    """The evidence record, opened at the cited passage of one version."""
    return f"/evidence/{evidence_id}?" + urlencode({"version": version_id, "ref": ref}) + "#cited-span"
