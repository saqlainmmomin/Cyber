"""Pure, deterministic derivations used by the V3 board report."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Iterable, Mapping, Sequence

from app.frameworks.registry import FrameworkRegistry
from app.services.remediation_groups import cluster_index

HORIZON_SHORT_DAYS = 90
HORIZON_MEDIUM_DAYS = 180
HORIZONS = ("short", "medium", "long", "unscheduled")
OPEN_STATUS_LABELS = ("Open", "In progress")
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _as_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _date_string(value) -> str | None:
    parsed = _as_date(value)
    return parsed.isoformat() if parsed else None


def _severity(value) -> str:
    return str(value or "").strip().lower()


def priority_for(severities: Iterable[str]) -> str:
    rank = min((SEVERITY_ORDER.get(_severity(value), 4) for value in severities), default=4)
    return {0: "high", 1: "high", 2: "medium", 3: "low"}.get(rank, "low")


def responsibility_for(values: Iterable[str | None]) -> str | None:
    clean = [str(value).strip() for value in values if value and str(value).strip()]
    if not clean:
        return None
    return clean[0] if len(set(clean)) == 1 else "shared"


def horizon_for(target_date: date | None, generated_on: date) -> str:
    target = _as_date(target_date)
    generated = _as_date(generated_on) or date.today()
    if target is None:
        return "unscheduled"
    days = (target - generated).days
    if days <= HORIZON_SHORT_DAYS:
        return "short"
    if days <= HORIZON_MEDIUM_DAYS:
        return "medium"
    return "long"


def is_overdue(target_date: date | None, generated_on: date, status_label: str) -> bool:
    target = _as_date(target_date)
    generated = _as_date(generated_on) or date.today()
    return bool(target and target < generated and str(status_label or "").strip() in OPEN_STATUS_LABELS)


def observation_ref(rank: int) -> str:
    return f"R-{int(rank):02d}"


def initiative_ref(number: int) -> str:
    return f"I-{int(number)}"


def action_ref(number: int) -> str:
    return f"A-{int(number):02d}"


def _framework_name(framework_id: str) -> str:
    framework = FrameworkRegistry.get_or_none(framework_id)
    return framework.name if framework else framework_id


def _clause_for(framework_id: str, requirement_id: str) -> str:
    framework = FrameworkRegistry.get_or_none(framework_id)
    if framework:
        for domain in framework.as_legacy_framework_dict().values():
            sections = domain["sections"].values() if isinstance(domain["sections"], dict) else domain["sections"]
            for section in sections:
                for requirement in section["requirements"]:
                    if requirement["id"] == requirement_id:
                        return requirement.get("section_ref") or requirement_id
    return requirement_id


def reference_clauses(
    framework_id: str,
    requirement_id: str,
    in_scope_framework_ids: Sequence[str],
) -> list[dict]:
    """Return own and same-cluster clauses, grouped in scope order."""

    allowed = set(in_scope_framework_ids)
    keys = [(framework_id, requirement_id)]
    cluster = cluster_index().get((framework_id, requirement_id))
    if cluster:
        keys.extend(
            key
            for key, candidate in cluster_index().items()
            if candidate[0] == cluster[0] and key[0] in allowed and key not in keys
        )
    grouped: dict[str, list[str]] = {}
    for candidate_framework, control_id in keys:
        if candidate_framework in allowed:
            grouped.setdefault(candidate_framework, []).append(
                _clause_for(candidate_framework, control_id)
            )
    return [
        {
            "framework_id": candidate_framework,
            "framework_name": _framework_name(candidate_framework),
            "clauses": list(dict.fromkeys(grouped[candidate_framework]))[:4],
        }
        for candidate_framework in in_scope_framework_ids
        if grouped.get(candidate_framework)
    ]


def _domain_title(row: Mapping) -> str:
    return str(row.get("domain_title") or "").split(" — ", 1)[-1]


def build_status_board(framework_sections: Sequence[Mapping], register: Sequence[Mapping]) -> list[dict]:
    result = []
    for section in framework_sections:
        framework_id = section.get("framework_id")
        rows = [row for row in register if row.get("framework_id") == framework_id]
        domains = []
        for domain in section.get("domains", []):
            domain_rows = [row for row in rows if _domain_title(row) == domain.get("title")]
            gaps = [row for row in domain_rows if row.get("outcome") in {"partially_compliant", "non_compliant"}]
            severity = Counter(_severity(row.get("risk_level")) for row in gaps)
            domains.append(
                {
                    "title": domain.get("title"),
                    "in_scope": len(domain_rows),
                    "gaps": len(gaps),
                    "crit_high": severity["critical"] + severity["high"],
                    "ie": sum(row.get("outcome") == "insufficient_evidence" for row in domain_rows),
                    "score": domain.get("score"),
                    "rating": domain.get("rating"),
                }
            )
        result.append(
            {
                "framework_id": framework_id,
                "name": section.get("name"),
                "version": section.get("version"),
                "score": section.get("score"),
                "rating": section.get("rating"),
                "in_scope": len(rows),
                "domains": domains,
            }
        )
    return result


def build_risk_matrix(framework_sections: Sequence[Mapping], register: Sequence[Mapping]) -> dict:
    result = {}
    for section in framework_sections:
        framework_id = section.get("framework_id")
        counts = Counter(
            _severity(row.get("risk_level"))
            for row in register
            if row.get("framework_id") == framework_id
            and row.get("outcome") in {"partially_compliant", "non_compliant"}
        )
        result[framework_id] = {
            severity: counts.get(severity, 0)
            for severity in ("critical", "high", "medium", "low")
        }
    return result


def build_severity_dashboard(framework_sections: Sequence[Mapping], register: Sequence[Mapping]) -> dict:
    names = {section.get("framework_id"): section.get("name") for section in framework_sections}
    counters = {severity: Counter() for severity in ("critical", "high", "medium", "low")}
    for row in register:
        if row.get("outcome") not in {"partially_compliant", "non_compliant"}:
            continue
        severity = _severity(row.get("risk_level"))
        if severity in counters:
            label = f"{names.get(row.get('framework_id'), row.get('framework_id'))} · {_domain_title(row)}"
            counters[severity][label] += 1
    return {
        severity: {
            "total": sum(counter.values()),
            "distinct": len(counter),
            "top": [
                {"label": label, "count": count}
                for label, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:4]
            ],
        }
        for severity, counter in counters.items()
    }


def _finding_ref_for_action(action: Mapping, observations: Sequence[Mapping]) -> str | None:
    for observation in observations:
        if action.get("finding_id") and observation.get("finding_id") == action.get("finding_id"):
            return observation.get("ref")
    for observation in observations:
        if (
            observation.get("requirement_id") == action.get("requirement_id")
            and observation.get("framework_name") == action.get("framework_name")
        ):
            return observation.get("ref")
    return None


def build_initiatives(
    groups: Sequence[Mapping],
    metadata: Mapping[str, Mapping] | None,
    observations: Sequence[Mapping],
    generated_on: date,
) -> list[dict]:
    metadata = metadata or {}
    result = []
    action_number = 0
    for initiative_number, group in enumerate(groups, start=1):
        group_meta = metadata.get(group.get("group_id"), {}) or {}
        actions = []
        for source in group.get("actions", []):
            action_number += 1
            target = _date_string(source.get("target_date"))
            obs_ref = _finding_ref_for_action(source, observations)
            actions.append(
                {
                    "finding_id": source.get("finding_id"),
                    "finding_title": source.get("finding_title"),
                    "framework_name": source.get("framework_name"),
                    "obs_ref": obs_ref,
                    "overdue": is_overdue(target, generated_on, source.get("status_label")),
                    "owner": source.get("owner"),
                    "ref": action_ref(action_number),
                    "requirement_id": source.get("requirement_id"),
                    "responsibility": source.get("responsibility"),
                    "status_label": source.get("status_label"),
                    "target_date": target,
                    "title": source.get("title"),
                }
            )
        severities = [close.get("severity") for close in group.get("closes", [])]
        result.append(
            {
                "actions": actions,
                "benefit": group_meta.get("benefit"),
                "complexity": group_meta.get("complexity"),
                "cross_framework": bool(group.get("cross_framework")),
                "frameworks": list(group.get("frameworks", [])),
                "group_id": group.get("group_id"),
                "horizon": horizon_for(group.get("target_date"), generated_on),
                "obs_refs": sorted({action["obs_ref"] for action in actions if action.get("obs_ref")}),
                "overdue": any(action["overdue"] for action in actions),
                "owner": next((action["owner"] for action in actions if action.get("owner")), None),
                "priority": priority_for(severities),
                "ref": initiative_ref(initiative_number),
                "responsibility": responsibility_for(action.get("responsibility") for action in actions),
                "target_date": _date_string(group.get("target_date")),
                "title": group_meta.get("title") or group.get("topic"),
                "topic": group.get("topic"),
            }
        )
    return result


def build_takeaways(
    status_board: Sequence[Mapping],
    severity_dashboard: Mapping,
    totals: Mapping,
    initiatives: Sequence[Mapping],
    observations: Sequence[Mapping],
) -> dict:
    domains = [domain for section in status_board for domain in section.get("domains", [])]
    scoped = [domain for domain in domains if domain.get("in_scope")]
    clean = sum(domain.get("gaps", 0) == 0 for domain in scoped)
    weakest = sorted(
        (domain for domain in scoped if domain.get("score") is not None),
        key=lambda domain: (domain.get("score"), domain.get("title", "")),
    )[:2]
    status = f"{clean} of {len(scoped)} in-scope domain(s) have no approved gaps"
    if len(weakest) == 2:
        status += f"; the weakest are {weakest[0]['title']} ({weakest[0]['score']:.0f}%) and {weakest[1]['title']} ({weakest[1]['score']:.0f}%)."
    elif len(weakest) == 1:
        status += f"; the weakest is {weakest[0]['title']} ({weakest[0]['score']:.0f}%)."
    else:
        status += "."
    covered = {
        action.get("obs_ref")
        for initiative in initiatives
        for action in initiative.get("actions", [])
        if action.get("obs_ref")
    }
    cross = sum(
        bool(initiative.get("cross_framework"))
        for initiative in initiatives
        if initiative.get("cross_framework")
    )
    return {
        "status_board": status,
        "dashboard": (
            f"{totals.get('gaps', 0)} approved gap(s), {totals.get('critical_high_gaps', 0)} of them critical or high; "
            f"{severity_dashboard.get('critical', {}).get('total', 0)} critical gap(s) in "
            f"{severity_dashboard.get('critical', {}).get('distinct', 0)} domain(s)."
        ),
        "roadmap": f"{len(initiatives)} initiative(s) cover {len(covered)} of {len(observations)} key observations; {cross} close a weakness once across more than one framework.",
    }


def derived_asks(
    initiatives: Sequence[Mapping],
    observations: Sequence[Mapping],
    *,
    insufficient_evidence: int = 0,
    rfi_open: int = 0,
) -> list[str]:
    actions = [action for initiative in initiatives for action in initiative.get("actions", [])]
    by_ref = {observation.get("ref"): observation for observation in observations}
    overdue = sum(action.get("overdue", False) for action in actions)
    unowned = sum(
        not action.get("owner")
        and _severity(by_ref.get(action.get("obs_ref"), {}).get("rating")) in {"critical", "high"}
        for action in actions
    )
    unscheduled = sum(not action.get("target_date") for action in actions)
    result = []
    if overdue:
        result.append(f"{overdue} remediation action(s) past their target date.")
    if unowned:
        result.append(f"{unowned} action(s) on critical or high findings have no owner.")
    if unscheduled:
        result.append(f"{unscheduled} action(s) have no target date.")
    if insufficient_evidence or rfi_open:
        result.append(f"{insufficient_evidence} requirement(s) could not be concluded; {rfi_open} evidence request(s) are open.")
    return result
