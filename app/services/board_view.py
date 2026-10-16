"""Ordered, presentation-neutral V3-C board-report view model."""

from __future__ import annotations

from copy import deepcopy
from math import ceil
import re
from typing import Mapping

from app.services import vocabulary as vocab


NEVER_COMBINED_NOTE = "Scores are per framework and are never combined; the totals above are counts."
EMPTY_ROADMAP_TEXT = "No remediation actions are recorded for the approved findings yet."

OUTCOMES = tuple(
    (key, vocab.outcome_label(key), color)
    for key, color in (
        ("compliant", "#0E8F86"),
        ("partially_compliant", "#E39A1F"),
        ("non_compliant", "#C0392B"),
        ("insufficient_evidence", "#9AA3B5"),
        ("not_applicable", "#D5D9E3"),
    )
)
OUTCOME_COLORS = {key: color for key, _, color in OUTCOMES}
SEVERITIES = vocab.RISK_LEVELS
SEVERITY_COLORS = {
    "critical": "#9B1C1C",
    "high": "#D9481E",
    "medium": "#F0A030",
    "low": "#3C9D6B",
}
RATING_COLORS = dict(zip(
    (label for _, label in vocab.SCORE_BANDS),
    ("#C0392B", "#D9481E", "#E39A1F", "#0E8F86"),
))
RATING_BANDS = tuple(
    (low, vocab.SCORE_BANDS[index + 1][0] if index + 1 < len(vocab.SCORE_BANDS) else 100, label, color)
    for index, ((low, label), color) in enumerate(zip(vocab.SCORE_BANDS, ("#CDD2DE", "#DCE0E9", "#E9ECF2", "#F5F6F9")))
)
LEVELS = {"high": 3, "medium": 2, "low": 1}
HORIZONS = (
    ("short", "Short term", "within 90 days"),
    ("medium", "Medium term", "91 to 180 days"),
    ("long", "Long term", "after 180 days"),
    ("unscheduled", "Not scheduled", "no target date"),
)
LANES = (("client", "Client"), ("shared", "Shared"), ("consultant", "Consultant"), (None, "Not recorded"))


def _pages(count: int, per_page: int) -> int:
    return max(1, ceil(count / per_page))


def _chunks(items: list, size: int) -> list[list]:
    return [items[index : index + size] for index in range(0, len(items), size)] or [[]]


def _pct(number: int | float, denominator: int | float) -> int:
    return round(100 * number / denominator) if denominator else 0


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


def readiness_document(document: Mapping) -> dict:
    """Derive display wording from numeric scores without changing issued data."""
    result = deepcopy(document)
    for row in result.get("observations", []):
        row.setdefault("framework_short", vocab.framework_display_name(row.get("framework_id", "")))
    framework_ids_by_name = {row.get("name"): row.get("framework_id") for row in result.get("frameworks", [])}
    for change in result.get("prior_period", {}).get("changes", []):
        if not change.get("framework_id"):
            change["framework_id"] = framework_ids_by_name.get(change.get("framework_name"), "")
    summary = result.get("summary", {})
    summary["limitations"] = [text.replace("framework(s)", "frameworks") for text in summary.get("limitations", [])]
    if result.get("schema_version", 1) >= 3:
        from app.services import board_derive

        result["takeaways"] = board_derive.build_takeaways(
            result.get("status_board", []), result.get("severity_dashboard", {}),
            summary.get("totals", {}), result.get("initiatives", []), result.get("observations", []),
        )
        result.setdefault("board_asks", {})["derived"] = board_derive.derived_asks(
            result.get("initiatives", []), result.get("observations", []),
            insufficient_evidence=summary.get("totals", {}).get("insufficient_evidence", 0),
            rfi_open=len(result.get("not_assessed", {}).get("rfi", {}).get("items", [])),
        )
    register = result.get("register") or result.get("appendices", {}).get("requirement_register", [])
    sections = {row["framework_id"]: row for row in result.get("framework_sections", [])}
    for rows in (
        result.get("summary", {}).get("frameworks", []),
        result.get("framework_sections", []),
        result.get("status_board", []),
    ):
        for row in rows:
            score = row.get("score")
            row["rating"] = vocab.score_band(score) if score is not None else None
            for domain in row.get("domains", []):
                value = domain.get("score")
                domain["rating"] = vocab.score_band(value) if value is not None else None
            if score is not None:
                framework_id = row["framework_id"]
                gaps = [item for item in register if item.get("framework_id") == framework_id and item.get("outcome") in {"partially_compliant", "non_compliant"}]
                if not register:
                    gaps = sections.get(framework_id, {}).get("gaps", [])
                row["headline"] = vocab.readiness_headline(
                    framework_id, score,
                    sum(item.get("risk_level") == "critical" for item in gaps),
                    sum(item.get("risk_level") == "high" for item in gaps),
                )
    appendices = result.get("appendices", {})
    if isinstance(appendices.get("methodology"), str):
        appendices["methodology"] = appendices["methodology"].replace("framework(s)", "frameworks")
        appendices["methodology"] = re.sub(
            r"(?<=Rating Thresholds:\n).*?(?=\n\n|$)",
            lambda _: vocab.score_threshold_text(), appendices["methodology"], flags=re.S,
        )
    return result


def view(document: Mapping) -> dict:
    document = readiness_document(document)
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

    below = [framework for framework in frameworks if framework.get("score") is not None and framework.get("rating") != vocab.score_band(80)]
    unscored = [framework for framework in frameworks if framework.get("score") is None]
    critical_high = int(totals.get("critical_high_gaps", 0) or 0)
    gaps = int(totals.get("gaps", 0) or 0)
    framework_count = len(frameworks)

    def names(items):
        labels = [framework["short"] for framework in items]
        return labels[0] if len(labels) == 1 else ", ".join(labels[:-1]) + " and " + labels[-1]

    if framework_count and len(below) == framework_count:
        below_copy = "neither framework is yet rated Ready" if framework_count == 2 else "no framework is yet rated Ready"
    elif below:
        below_copy = f"{names(below)} {'is' if len(below) == 1 else 'are'} below Ready"
    else:
        below_copy = "no scored framework is below Ready"
    if unscored:
        below_copy += f"; {names(unscored)} {'is' if len(unscored) == 1 else 'are'} not yet scored"
    exec_title = (
        f"No critical or high gaps are open, and {below_copy}"
        if critical_high == 0
        else f"{critical_high} of {vocab.plural(gaps, 'gap')} {'is' if gaps == 1 else 'are'} critical or high, and {below_copy}"
    )

    met = sum(int(framework.get("coverage", {}).get("compliant", 0) or 0) for framework in frameworks)
    concluded = sum(framework["concluded"] for framework in frameworks)
    posture_title = f"{met} of {vocab.plural(concluded, 'concluded requirement')} {'is' if concluded == 1 else 'are'} met; {gaps} {'has a gap' if gaps == 1 else 'have gaps'} to close"
    all_domains = [(framework["short"], domain) for framework in frameworks for domain in framework["domains"]]
    # Only scored domains can be the weakest; an unscored domain is not "0%".
    scored_domains = [item for item in all_domains if item[1].get("score") is not None]
    weakest = sorted(scored_domains, key=lambda item: item[1]["score"])[:2]
    domain_title = (
        " and ".join(f"{domain['title']} ({vocab.score_text(domain['score'])})" for _, domain in weakest)
        + (" are the weakest areas" if len(weakest) > 1 else " is the weakest area")
        if weakest
        else "No area has a score yet"
    )
    by_critical_high = sorted(all_domains, key=lambda item: -(item[1].get("crit_high", 0) or 0))
    top_critical_high = by_critical_high[0] if by_critical_high and by_critical_high[0][1].get("crit_high") else None
    risk_title = (
        f"{top_critical_high[1]['title']} holds {top_critical_high[1]['crit_high']} of the {critical_high} critical or high gaps"
        if top_critical_high
        else f"No critical or high gaps; {vocab.plural(gaps, 'gap')} {'remains' if gaps == 1 else 'remain'}"
    )

    asks = document.get("board_asks") or {"consultant": [], "derived": []}
    decision_title = (
        f"The board is asked to make {vocab.plural(len(asks.get('consultant', [])), 'decision')}; "
        f"{vocab.plural(len(asks.get('derived', [])), 'item')} {'needs' if len(asks.get('derived', [])) == 1 else 'need'} management attention"
    )

    initiatives = list(document.get("initiatives") or [])
    short_initiatives = sum(1 for initiative in initiatives if initiative.get("horizon") == "short")
    overdue = sum(1 for initiative in initiatives if initiative.get("overdue"))
    roadmap_title = f"{short_initiatives} of {vocab.plural(len(initiatives), 'initiative')} {'falls' if len(initiatives) == 1 else 'fall'} in the next 90 days"
    if overdue:
        roadmap_title += f"; {overdue} {'is' if overdue == 1 else 'are'} already overdue"

    grid = {f"{effort}-{benefit}": [] for effort in ("low", "medium", "high") for benefit in ("low", "medium", "high")}
    unsized = []
    for initiative in initiatives:
        key = f"{initiative.get('complexity')}-{initiative.get('benefit')}"
        if key in grid:
            grid[key].append(initiative)
        else:
            unsized.append(initiative)
    high_benefit = [initiative for initiative in initiatives if initiative.get("benefit") == "high" and initiative.get("complexity") in LEVELS]
    quick_wins = [initiative for initiative in high_benefit if initiative.get("complexity") == "low"]
    sized = len(initiatives) - len(unsized)
    if quick_wins:
        matrix_title = f"{vocab.plural(len(quick_wins), 'quick win')} among {vocab.plural(len(high_benefit), 'high-benefit initiative')}"
    elif len(high_benefit) == 1:
        matrix_title = "No quick wins: the one high-benefit initiative needs medium or high effort"
    elif high_benefit:
        matrix_title = f"No quick wins: all {len(high_benefit)} high-benefit initiatives need medium or high effort"
    elif sized:
        matrix_title = "No quick wins: no sized initiative is rated high benefit"
    else:
        matrix_title = "No initiative has been sized for effort and benefit yet"
    if unsized and sized:
        matrix_title += f"; {len(unsized)} not yet sized"
    lanes = [(key, vocab.responsibility_label(key, document.get("firm_name")) or label) for key, label in LANES if any(initiative.get("responsibility") == key for initiative in initiatives)]
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

    comparisons = [
        f"{framework['short']} {'rose' if framework['delta'] >= 0 else 'fell'} {abs(framework['delta']):.1f} points"
        for framework in frameworks if framework.get("delta") is not None
    ]
    if not prior_entries:
        since_title = "This first report sets the baseline for future comparisons"
    elif comparisons:
        since_title = " and ".join(comparisons) + " since the last report"
    else:
        since_title = "No framework could be compared with the last report"

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

    slides: list[dict] = []

    def add(slide: str, section: str, title: str) -> None:
        slides.append({"slide": slide, "section": section, "title": title})

    add("cover", "cover", "Board report")
    add("contents", "contents", "Contents")
    add("how-to-read", "01", "How to read this report")
    add("overview", "01", f"We assessed {totals.get('requirements', 0)} requirements")
    add("limits", "01", "Scope and limits")
    add("executive-summary", "02", exec_title)
    add("posture", "02", posture_title)
    add("domain-status", "02", domain_title)
    add("risk-profile", "02", risk_title)
    add("board-asks", "02", decision_title)
    for index in range(len(observation_pages)):
        add("observations", "03", f"Key observations ({index + 1} of {len(observation_pages)})")
    add("roadmap", "04", roadmap_title)
    add("effort-benefit", "04", matrix_title)
    add("comparison", "05", since_title)
    add("sign-off", "06", "Sign-off")
    add("appendix", "", "Appendix")
    add("methodology", "A1", "Methodology")
    for index in range(len(register_pages)):
        add("requirement-register", "A2", f"Requirement register ({index + 1} of {len(register_pages)})")
    add("evidence-and-soa", "A3", "Evidence register")

    numbered = [{**item, "number": number} for number, item in enumerate(slides, 1)]
    page_map = {
        key: next(item["number"] for item in numbered if item["slide"] == slide)
        for key, slide in {"read": "how-to-read", "overview": "overview", "exec": "executive-summary", "obs": "observations", "roadmap": "roadmap", "since": "comparison", "sign_off": "sign-off", "appendix": "appendix"}.items()
    }
    contents = [
        ("01", "How to read this report", "Assessment overview, scope and limits", page_map["read"]),
        ("02", "Executive summary", "Position, posture, domains, risk and decisions", page_map["exec"]),
        ("03", "Key observations", f"{len(observations)} approved findings", page_map["obs"]),
        ("04", "Remediation roadmap", "Initiatives, effort and benefit", page_map["roadmap"]),
        ("05", "Change since last report", "Comparison within each framework", page_map["since"]),
        ("06", "Sign-off", "Prepared and reviewed by the engagement team", page_map["sign_off"]),
        ("", "Appendix", "Methodology, requirement and evidence registers", page_map["appendix"]),
    ]
    return {
        "slides": numbered,
        "contents": contents,
        "unsized": unsized,
        "delta_text": vocab.delta_text,
        "display_reference": vocab.display_reference,
        "plural": vocab.plural,
        "responsibility_label": lambda value: vocab.responsibility_label(value, document.get("firm_name")),
        "severity_legend": vocab.severity_legend(f["framework_id"] for f in document.get("frameworks", [])),
        "cover_subtitle": vocab.cover_subtitle(f["framework_id"] for f in document.get("frameworks", [])),
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
        "threshold_text": vocab.score_threshold_text(),
        "score_text": vocab.score_text,
        "outcome_labels": vocab.OUTCOMES,
        "level": LEVELS,
        "priority_labels": vocab.PRIORITY_LABELS,
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
            f"(Report ID {str(document.get('snapshot', {}).get('id', ''))[:8]}), "
            f"evidence cut-off {document.get('basis', {}).get('cutoff_label')}."
        ),
        "date_label": _date_label,
    }
