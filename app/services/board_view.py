"""Ordered, presentation-neutral V3-C board-report view model."""

from __future__ import annotations

from math import ceil
from typing import Mapping


NEVER_COMBINED_NOTE = "Scores are per framework and are never combined; the totals above are counts."
EMPTY_ROADMAP_TEXT = "No remediation actions are recorded for the approved findings yet."

OUTCOMES = (
    ("compliant", "Compliant", "#0E8F86"),
    ("partially_compliant", "Partially compliant", "#E39A1F"),
    ("non_compliant", "Non-compliant", "#C0392B"),
    ("insufficient_evidence", "Not concluded", "#9AA3B5"),
    ("not_applicable", "Not applicable", "#D5D9E3"),
)
OUTCOME_COLORS = {key: color for key, _, color in OUTCOMES}
SEVERITIES = ("critical", "high", "medium", "low")
SEVERITY_COLORS = {
    "critical": "#9B1C1C",
    "high": "#D9481E",
    "medium": "#F0A030",
    "low": "#3C9D6B",
}
RATING_COLORS = {
    "Compliant": "#0E8F86",
    "Partially Compliant": "#E39A1F",
    "Needs Significant Improvement": "#D9481E",
    "Non-Compliant": "#C0392B",
}
RATING_BANDS = (
    (0, 40, "Non-compliant", "#CDD2DE"),
    (40, 60, "Needs significant improvement", "#DCE0E9"),
    (60, 80, "Partially compliant", "#E9ECF2"),
    (80, 100, "Compliant", "#F5F6F9"),
)
LEVELS = {"high": 3, "medium": 2, "low": 1}
HORIZONS = (
    ("short", "Short term", "within 90 days"),
    ("medium", "Medium term", "91 to 180 days"),
    ("long", "Long term", "after 180 days"),
    ("unscheduled", "Not scheduled", "no target date"),
)
LANES = (("client", "Client"), ("shared", "Shared"), ("consultant", "Firm"))


def _pages(count: int, per_page: int) -> int:
    return max(1, ceil(count / per_page))


def _chunks(items: list, size: int) -> list[list]:
    return [items[index : index + size] for index in range(0, len(items), size)] or [[]]


def _pct(number: int | float, denominator: int | float) -> int:
    return round(100 * number / denominator) if denominator else 0


def _plural(number: int, singular: str, plural: str | None = None) -> str:
    return f"{number} {singular if number == 1 else (plural or singular + 's')}"


def _waffle(coverage: Mapping) -> tuple[list[dict], int]:
    """Return one cell per in-scope requirement, column-major, ordered by outcome."""
    cells = [
        color
        for key, _, color in OUTCOMES
        for _ in range(int(coverage.get(key, 0) or 0))
    ]
    return (
        [{"col": color, "x": index // 10, "y": index % 10} for index, color in enumerate(cells)],
        (len(cells) + 9) // 10,
    )


def _domain_rows(document: Mapping, framework_id: str) -> tuple[list[dict], list[dict]]:
    """Enrich status-board domains with stable IDs from framework_sections."""
    status = next(
        (row for row in document.get("status_board", []) if row.get("framework_id") == framework_id),
        {},
    )
    section = next(
        (row for row in document.get("framework_sections", []) if row.get("framework_id") == framework_id),
        {},
    )
    ids_by_title = {row.get("title"): row.get("domain_id") for row in section.get("domains", [])}
    domains = []
    for domain in status.get("domains", []):
        domains.append({**domain, "domain_id": domain.get("domain_id") or ids_by_title.get(domain.get("title"))})
    return (
        sorted((domain for domain in domains if domain.get("in_scope")), key=lambda domain: domain.get("score") or 0),
        [domain for domain in domains if not domain.get("in_scope")],
    )


def _prior_domain_rows(framework: Mapping) -> dict:
    return {
        row.get("domain_id"): row
        for row in framework.get("domains", [])
        if row.get("domain_id")
    }


def _short_name(framework: Mapping) -> str:
    """Prefer a document-provided short label, then the registry-derived display name."""
    return framework.get("framework_short") or framework.get("name") or framework.get("framework_id", "Framework")


def _date_label(value) -> str | None:
    if not value:
        return None
    from datetime import date

    return date.fromisoformat(str(value)[:10]).strftime("%d %b %Y")


def view(document: Mapping) -> dict:
    observations = list(document.get("observations") or [])
    register = list(
        document.get("register")
        or document.get("appendices", {}).get("requirement_register", [])
        or []
    )
    prior_entries = {
        row.get("framework_id"): row
        for row in (document.get("prior_period") or {}).get("frameworks", [])
        if row.get("compared")
    }
    summary = document.get("summary") or {}
    totals = summary.get("totals") or {}
    status_board = document.get("status_board") or []
    status_by_id = {row.get("framework_id"): row for row in status_board}
    framework_sections = {
        row.get("framework_id"): row for row in document.get("framework_sections", [])
    }

    frameworks = []
    for framework in summary.get("frameworks", []):
        framework_id = framework.get("framework_id")
        coverage = framework.get("coverage") or {}
        cells, columns = _waffle(coverage)
        prior = prior_entries.get(framework_id)
        status = status_by_id.get(framework_id, {})
        live_domains, out_domains = _domain_rows(document, framework_id)
        prior_domains = _prior_domain_rows(prior or {})
        current_sections = framework_sections.get(framework_id, {}).get("domains", [])
        current_domain_ids = {row.get("title"): row.get("domain_id") for row in current_sections}
        for domain in live_domains + out_domains:
            domain.setdefault("domain_id", current_domain_ids.get(domain.get("title")))
        frameworks.append(
            {
                **framework,
                "short": _short_name(framework),
                "cells": cells,
                "ncols": columns,
                "rating_col": RATING_COLORS.get(framework.get("rating"), "#9AA3B5"),
                "concluded": sum(int(coverage.get(key, 0) or 0) for key in ("compliant", "partially_compliant", "non_compliant")),
                "prior": prior,
                "delta": prior.get("score_delta") if prior else None,
                "outcomes": [
                    {
                        "k": key,
                        "label": label,
                        "col": color,
                        "n": int(coverage.get(key, 0) or 0),
                        "pct": _pct(coverage.get(key, 0) or 0, coverage.get("in_scope", 0) or 0),
                    }
                    for key, label, color in OUTCOMES
                ],
                "gaps": int(coverage.get("partially_compliant", 0) or 0)
                + int(coverage.get("non_compliant", 0) or 0),
                "domains": live_domains,
                "out_domains": out_domains,
                "sev": (summary.get("risk_matrix") or {}).get(framework_id, {severity: 0 for severity in SEVERITIES}),
                "status": status,
                "prior_domains": prior_domains,
            }
        )

    below = [framework for framework in frameworks if framework.get("rating") != "Compliant"]
    critical_high = int(totals.get("critical_high_gaps", 0) or 0)
    gaps = int(totals.get("gaps", 0) or 0)
    framework_count = len(frameworks)
    if framework_count and len(below) == framework_count:
        below_copy = (
            "neither framework is yet rated Compliant"
            if framework_count == 2
            else "no framework is yet rated Compliant"
        )
    else:
        below_copy = f"{', '.join(framework['short'] for framework in below) or 'no framework'} is below Compliant"
    exec_title = f"{critical_high} of {gaps} gaps are critical or high, and {below_copy}"

    met = sum(int(framework.get("coverage", {}).get("compliant", 0) or 0) for framework in frameworks)
    concluded = sum(framework["concluded"] for framework in frameworks)
    posture_title = f"{met} of {concluded} concluded requirements are met; {gaps} have gaps to close"
    all_domains = [(framework["short"], domain) for framework in frameworks for domain in framework["domains"]]
    weakest = sorted(all_domains, key=lambda item: item[1].get("score") or 0)[:2]
    domain_title = " and ".join(
        f"{domain['title']} ({domain.get('score', 0):.0f}%)" for _, domain in weakest
    ) + (" are the weakest areas" if len(weakest) > 1 else " is the weakest area")
    by_critical_high = sorted(all_domains, key=lambda item: -(item[1].get("crit_high", 0) or 0))
    top_critical_high = by_critical_high[0] if by_critical_high and by_critical_high[0][1].get("crit_high") else None
    risk_title = (
        f"{top_critical_high[1]['title']} holds {top_critical_high[1]['crit_high']} of the {critical_high} critical or high gaps"
        if top_critical_high
        else f"No critical or high gaps; {_plural(gaps, 'gap')} remain"
    )

    asks = document.get("board_asks") or {"consultant": [], "derived": []}
    decision_title = (
        f"The board is asked to make {_plural(len(asks.get('consultant', [])), 'decision')}; "
        f"{_plural(len(asks.get('derived', [])), 'item')} need management attention"
    )

    initiatives = list(document.get("initiatives") or [])
    short_initiatives = sum(1 for initiative in initiatives if initiative.get("horizon") == "short")
    overdue = sum(1 for initiative in initiatives if initiative.get("overdue"))
    roadmap_title = f"{short_initiatives} of {len(initiatives)} initiatives fall in the next 90 days"
    if overdue:
        roadmap_title += f"; {overdue} {'is' if overdue == 1 else 'are'} already overdue"

    grid = {f"{effort}-{benefit}": [] for effort in ("low", "medium", "high") for benefit in ("low", "medium", "high")}
    for initiative in initiatives:
        key = f"{initiative.get('complexity')}-{initiative.get('benefit')}"
        if key in grid:
            grid[key].append(initiative)
    high_benefit = [initiative for initiative in initiatives if initiative.get("benefit") == "high"]
    quick_wins = [initiative for initiative in high_benefit if initiative.get("complexity") == "low"]
    matrix_title = (
        f"{_plural(len(quick_wins), 'quick win')} among {len(high_benefit)} high-benefit initiatives"
        if quick_wins
        else f"No quick wins: all {len(high_benefit)} high-benefit initiatives need medium or high effort"
    )
    lanes = [lane for lane in LANES if any(initiative.get("responsibility") == lane[0] for initiative in initiatives)]
    horizons = [
        horizon
        for horizon in HORIZONS
        if horizon[0] != "unscheduled" or any(initiative.get("horizon") == "unscheduled" for initiative in initiatives)
    ]

    dumbbell = []
    for framework in frameworks:
        rows = []
        for domain in framework["domains"]:
            now = domain.get("score")
            if now is None:
                continue
            prior_domain = framework["prior_domains"].get(domain.get("domain_id"))
            if prior_domain and prior_domain.get("compared") and prior_domain.get("prior_score") is not None:
                was = prior_domain["prior_score"]
            else:
                was = None
            rows.append({"title": domain["title"], "now": now, "was": was})
        dumbbell.append({"name": framework.get("name"), "rows": sorted(rows, key=lambda row: row["now"])})

    since_title = (
        " and ".join(
            f"{framework['short']} {'rose' if framework['delta'] >= 0 else 'fell'} {abs(framework['delta']):.0f} points"
            for framework in frameworks
            if framework.get("prior") and framework.get("delta") is not None
        )
        + " since the last report"
        if prior_entries
        else "This first report sets the baseline for future comparisons"
    )
    severity_totals = {
        severity: sum(int(framework["sev"].get(severity, 0) or 0) for framework in frameworks)
        for severity in SEVERITIES
    }
    severity_dashboard = document.get("severity_dashboard") or {}
    severity_top = {
        severity: list((severity_dashboard.get(severity) or {}).get("top") or [])
        for severity in SEVERITIES
    }
    critical_high_domains = sorted(
        [
            (framework["short"], domain)
            for framework in frameworks
            for domain in framework["domains"]
            if domain.get("crit_high")
        ],
        key=lambda item: -(item[1].get("crit_high", 0) or 0),
    )[:6]

    max_domains = max([len(framework["domains"]) + len(framework["out_domains"]) for framework in frameworks] or [1])
    dumbbell_rows = sum(len(group["rows"]) + 1 for group in dumbbell) or 1
    layout = {
        "dom_row": round(min(28.0, max(15.5, 108 / max_domains)), 1),
        "dumb_row": round(min(14.0 if prior_entries else 28.0, max(9.6, 112 / dumbbell_rows)), 1),
        "ch_row": round(min(15.0, max(11.0, 70 / max(len(critical_high_domains), 1))), 1),
        "ask_h": round(min(124.0, (128 - 4 * (len(asks.get("consultant", [])) - 1)) / max(len(asks.get("consultant", [])), 1)), 1),
        "fwcard": 27 if len(frameworks) > 1 else 40,
        "dom_bar": 70 if len(frameworks) > 1 else 200,
    }

    observation_pages = _chunks(observations, 3)
    register_pages = _chunks(register, 12)
    has_prior = bool(prior_entries)
    page_map = {"read": 3, "overview": 4, "exec": 5, "obs": 10}
    page_map["roadmap"] = page_map["obs"] + len(observation_pages)
    page_map["annex"] = page_map["roadmap"] + 5

    slides: list[dict] = []

    def add(slide: str, section: str, title: str) -> None:
        slides.append({"slide": slide, "section": section, "title": title})

    add("cover", "cover", "Board report")
    add("contents", "contents", "Contents")
    add("how-to-read", "01", "How to read this report")
    add("overview", "01", f"We assessed {totals.get('requirements', 0)} requirements")
    add("executive-summary", "02", exec_title)
    add("posture", "02", posture_title)
    add("domain-status", "02", domain_title)
    add("risk-profile", "02", risk_title)
    add("board-asks", "02", decision_title)
    for index in range(len(observation_pages)):
        add("observations", "03", f"Key observations ({index + 1} of {len(observation_pages)})")
    add("roadmap", "04", roadmap_title)
    add("effort-benefit", "04", matrix_title)
    add("comparison", "04", since_title)
    add("limits", "04", f"{len(document.get('not_assessed', {}).get('insufficient_evidence', []))} requirements could not be concluded")
    add("sign-off", "04", "Sign-off")
    add("annexure", "05", "Annexure")
    add("methodology", "A1", "Methodology")
    for index in range(len(register_pages)):
        add("requirement-register", "A2", f"Requirement register ({index + 1} of {len(register_pages)})")
    add("evidence-and-soa", "A3", "Evidence register")

    numbered = [{**item, "number": number} for number, item in enumerate(slides, 1)]
    return {
        "slides": numbered,
        "theme": {
            "p1": document.get("theme", {}).get("primary", "#161A5C"),
            "p2": document.get("theme", {}).get("secondary", "#2D3FD3"),
            "p3": "#3FA9F5",
            "acc": document.get("theme", {}).get("accent", "#12B3A6"),
        },
        "fw": frameworks,
        "t": totals,
        "out": OUTCOMES,
        "out_col": OUTCOME_COLORS,
        "bands": RATING_BANDS,
        "level": LEVELS,
        "sev": SEVERITIES,
        "sev_col": SEVERITY_COLORS,
        "sev_tot": severity_totals,
        "sev_top": severity_top,
        "grid": grid,
        "lanes": lanes,
        "horizons": horizons,
        "dumb": dumbbell,
        "has_prior": has_prior,
        "pg": page_map,
        "lay": layout,
        "obs_pages": observation_pages,
        "reg_pages": register_pages,
        "observation_pages": len(observation_pages),
        "register_pages": len(register_pages),
        "never_combined_note": NEVER_COMBINED_NOTE,
        "empty_roadmap_text": EMPTY_ROADMAP_TEXT,
        "titles": {
            "exec": exec_title,
            "posture": posture_title,
            "domain": domain_title,
            "risk": risk_title,
            "decision": decision_title,
            "obs": f"{len(observations)} key observations",
            "roadmap": roadmap_title,
            "matrix": matrix_title,
            "since": since_title,
        },
        "met": met,
        "concluded": concluded,
        "docs_reviewed": len(document.get("appendices", {}).get("evidence_register", [])),
        "ch_doms": critical_high_domains,
        "ref_by_finding": {
            observation.get("finding_id"): observation.get("ref")
            for observation in observations
        },
        "framework_names": {
            framework.get("framework_id"): framework.get("name")
            for framework in document.get("frameworks", [])
        },
        "source": (
            f"Source: approved outcomes in report {document.get('snapshot', {}).get('version_label')} "
            f"(snapshot {str(document.get('snapshot', {}).get('id', ''))[:8]}), "
            f"evidence cut-off {document.get('basis', {}).get('cutoff_label')}."
        ),
        "has_dpdpa": any(framework.get("framework_id") == "dpdpa" for framework in document.get("frameworks", [])),
        "date_label": _date_label,
    }
