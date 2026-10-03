"""Ordered, presentation-neutral V3 board-report view model."""

from __future__ import annotations

from math import ceil
from typing import Mapping


NEVER_COMBINED_NOTE = "Scores are per framework and are never combined; the totals above are counts."


def _pages(count: int, per_page: int) -> int:
    return max(1, ceil(count / per_page))


def view(document: Mapping) -> dict:
    observations = list(document.get("observations") or [])
    register = list(
        document.get("register")
        or document.get("appendices", {}).get("requirement_register", [])
        or []
    )
    prior = document.get("prior_period") or {}
    slides: list[dict] = []

    section_numbers = {
        "overview": "01", "ratings": "01",
        "executive-summary": "02", "status-board": "02", "risk-dashboard": "02", "board-asks": "02",
        "observations": "03",
        "roadmap": "04", "initiatives": "04", "comparison": "04", "limits": "04", "sign-off": "04",
        "annexure": "05", "methodology": "05", "requirement-register": "05", "evidence-and-soa": "05",
    }

    def add(slide: str, section: str, title: str) -> None:
        slides.append({"slide": slide, "section": section, "title": title})

    add("cover", "cover", "Board report")
    add("contents", "contents", "Contents")
    add("overview", "overview", "Assessment overview")
    add("ratings", "ratings", "Framework ratings")
    add("executive-summary", "executive-summary", "Executive summary")
    add("status-board", "status-board", "Status board")
    add("risk-dashboard", "risk-dashboard", "Risk dashboard")
    add("board-asks", "board-asks", "Board asks")
    observation_pages = _pages(len(observations), 4)
    register_pages = _pages(len(register), 21)
    for index in range(observation_pages):
        add("observations", "observations", "Key observations")
    add("roadmap", "roadmap", "Remediation roadmap")
    add("initiatives", "initiatives", "Initiatives and actions")
    if prior.get("status") == "compared":
        add("comparison", "comparison", "Prior-period comparison")
    add("limits", "limits", "Limits and assumptions")
    add("sign-off", "sign-off", "Sign-off")
    add("annexure", "annexure", "Annexure")
    add("methodology", "methodology", "Methodology")
    for index in range(register_pages):
        add("requirement-register", "requirement-register", "Requirement register")
    add("evidence-and-soa", "evidence-and-soa", "Evidence and statement of applicability")

    numbered = []
    for number, item in enumerate(slides, 1):
        numbered.append({**item, "number": number})
    for item in numbered:
        item["section"] = section_numbers.get(item["slide"])
    return {
        "slides": numbered,
        "theme": dict(document.get("theme") or {}),
        "observation_pages": observation_pages,
        "register_pages": register_pages,
        "never_combined_note": NEVER_COMBINED_NOTE,
    }
