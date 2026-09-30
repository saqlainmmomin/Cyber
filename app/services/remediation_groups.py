"""Deterministic cross-framework remediation roadmap groups."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

from app.frameworks.registry import FrameworkRegistry
from app.services.report_content import ReportFinding


SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SINGLE_PREFIX = "SINGLE."


@lru_cache(maxsize=1)
def cluster_index() -> dict[tuple[str, str], tuple[str, str]]:
    from app.frameworks.mappings.clusters import CONTROL_CLUSTERS

    index: dict[tuple[str, str], tuple[str, str]] = {}
    for cluster in CONTROL_CLUSTERS:
        cluster_id = cluster["cluster_id"]
        topic = cluster["topic"]
        for member in cluster["controls"]:
            key = (member["framework"], member["control"])
            if key in index:
                raise ValueError(f"Control {key[0]}:{key[1]} appears in multiple clusters")
            index[key] = (cluster_id, topic)
    return index


def join_names(names) -> str:
    names = list(names)
    if len(names) <= 1:
        return names[0] if names else ""
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])} and {names[-1]}"


def _date_value(value):
    return value.isoformat() if value is not None else None


def _requirement_rank(framework_id: str) -> dict[str, int]:
    try:
        controls = FrameworkRegistry.get(framework_id).all_controls()
    except KeyError:
        return {}
    return {control.id: rank for rank, control in enumerate(controls)}


def build_groups(
    findings: Sequence[ReportFinding],
    framework_ids: Sequence[str],
) -> list[dict]:
    framework_rank = {framework_id: rank for rank, framework_id in enumerate(framework_ids)}
    for finding in findings:
        if finding.framework_id not in framework_rank:
            framework_rank[finding.framework_id] = len(framework_rank)
    requirement_ranks = {
        framework_id: _requirement_rank(framework_id)
        for framework_id in framework_rank
    }
    index = cluster_index()
    grouped: dict[tuple[str, str], list[ReportFinding]] = {}
    for finding in findings:
        group_id, topic = index.get(
            (finding.framework_id, finding.requirement_id),
            (
                f"{SINGLE_PREFIX}{finding.framework_id}:{finding.requirement_id}",
                finding.requirement_title,
            ),
        )
        grouped.setdefault((group_id, topic), []).append(finding)

    result = []
    for (group_id, topic), group_findings in grouped.items():
        if not any(finding.actions for finding in group_findings):
            continue
        closes = sorted(
            group_findings,
            key=lambda finding: (
                framework_rank.get(finding.framework_id, len(framework_rank)),
                requirement_ranks.get(finding.framework_id, {}).get(
                    finding.requirement_id, 10**9
                ),
                finding.title,
                finding.requirement_id,
            ),
        )
        frameworks = []
        for finding in closes:
            if finding.framework_name not in frameworks:
                frameworks.append(finding.framework_name)
        actions = []
        for finding in group_findings:
            for action in finding.actions:
                actions.append(
                    {
                        "_sort": (
                            action.target_date is None,
                            action.target_date,
                            SEVERITY_RANK.get(finding.severity, 4),
                            framework_rank.get(finding.framework_id, len(framework_rank)),
                            requirement_ranks.get(finding.framework_id, {}).get(
                                finding.requirement_id, 10**9
                            ),
                            action.title,
                            finding.title,
                            finding.requirement_id,
                        ),
                        "title": action.title,
                        "owner": action.owner,
                        "target_date": _date_value(action.target_date),
                        "status_label": action.status_label,
                        "framework_name": finding.framework_name,
                        "requirement_id": finding.requirement_id,
                        "finding_title": finding.title,
                    }
                )
        actions.sort(key=lambda action: action["_sort"])
        for action in actions:
            del action["_sort"]
        targets = [action["target_date"] for action in actions if action["target_date"] is not None]
        target_date = min(targets) if targets else None
        severity = min(
            (SEVERITY_RANK.get(finding.severity, 4) for finding in group_findings),
            default=4,
        )
        count = len(group_findings)
        if len(frameworks) > 1:
            headline = f"Addresses {count} findings across {join_names(frameworks)}"
        elif count > 1:
            headline = f"Addresses {count} findings in {frameworks[0]}"
        else:
            headline = f"Addresses 1 finding in {frameworks[0]}"
        result.append(
            {
                "_sort": (
                    target_date is None,
                    target_date,
                    severity,
                    -count,
                    topic.lower(),
                    group_id,
                ),
                "group_id": group_id,
                "topic": topic,
                "headline": headline,
                "frameworks": frameworks,
                "cross_framework": len(frameworks) > 1,
                "finding_count": count,
                "target_date": target_date,
                "actions": actions,
                "closes": [
                    {
                        "framework_id": finding.framework_id,
                        "framework_name": finding.framework_name,
                        "requirement_id": finding.requirement_id,
                        "requirement_title": finding.requirement_title,
                        "finding_title": finding.title,
                        "severity": finding.severity,
                    }
                    for finding in closes
                ],
            }
        )
    result.sort(key=lambda group: group["_sort"])
    for group in result:
        del group["_sort"]
    return result
