"""Human wording shared by evidence records, citations and span views."""


def location_label(ref: str) -> str:
    if ref == "whole":
        return "Whole document"
    if ref.startswith("page:"):
        return "Page " + ref[5:]
    if ref.startswith("chars:"):
        return "Characters " + ref[6:].replace("-", "–", 1)
    return ref
