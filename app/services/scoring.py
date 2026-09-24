"""
Deterministic compliance scoring engine.

Takes Claude's qualitative assessments and computes weighted quantitative scores.
Also handles root cause clustering and initiative generation (post-analysis).
"""

import json
import logging

from app.database import SessionLocal
from app.dpdpa.framework import ROOT_CAUSE_CLUSTERS
from app.schemas.scoring import ScoringResult

logger = logging.getLogger(__name__)

STATUS_SCORES = {
    "compliant": 100,
    "partially_compliant": 50,
    "non_compliant": 0,
}

# All statuses Claude is allowed to return. Anything outside this set is unexpected.
KNOWN_STATUSES = frozenset(STATUS_SCORES) | {"not_assessed", "not_applicable"}

RATING_THRESHOLDS = [
    (80, "Compliant"),
    (60, "Partially Compliant"),
    (40, "Needs Significant Improvement"),
    (0, "Non-Compliant"),
]

MATURITY_STATUS_SCORES = {
    "not_implemented": 0.0,
    "partial": 2.5,
    "implemented": 5.0,
    "not_applicable": 5.0,
    "unknown": 0.0,
}

_LEGACY_TO_MATURITY_STATUS = {
    "non_compliant": "not_implemented",
    "partially_compliant": "partial",
    "compliant": "implemented",
    "not_applicable": "not_applicable",
    "not_assessed": "unknown",
}

_MIN_CLUSTER_MAPPING_COVERAGE = 0.95
_WARNED_CLUSTER_COVERAGE: set[str] = set()

FRAMEWORK_ANALYSIS_FAILED = "failed"


def failed_framework_scores() -> dict:
    return {
        "status": FRAMEWORK_ANALYSIS_FAILED,
        "overall_score": None,
        "overall_rating": None,
        "domain_scores": {},
    }


def is_failed_framework_score(entry) -> bool:
    return isinstance(entry, dict) and entry.get("status") == FRAMEWORK_ANALYSIS_FAILED


def failed_framework_ids(framework_scores: dict, framework_ids: list[str]) -> list[str]:
    """Return failed framework ids in the selected-framework order."""
    return [
        framework_id
        for framework_id in framework_ids
        if is_failed_framework_score(framework_scores.get(framework_id))
    ]


def _validated_cluster_mapping(framework_id: str) -> dict[str, str]:
    """Reject frameworks whose controls are not meaningfully cluster-backed."""
    from app.frameworks.mappings.clusters import CONTROL_CLUSTERS
    from app.frameworks.registry import FrameworkRegistry

    framework = FrameworkRegistry.get_or_none(framework_id)
    if framework is None:
        raise ValueError(f"Unsupported framework '{framework_id}'")

    control_ids = {control.id for control in framework.all_controls()}
    control_clusters = {
        member["control"]: cluster["cluster_id"]
        for cluster in CONTROL_CLUSTERS
        for member in cluster["controls"]
        if member["framework"] == framework_id and member["control"] in control_ids
    }
    total = len(control_ids)
    coverage = (len(control_clusters) / total) if total else 0.0
    if coverage < _MIN_CLUSTER_MAPPING_COVERAGE:
        threshold = round(_MIN_CLUSTER_MAPPING_COVERAGE * 100)
        raise NotImplementedError(
            f"Framework '{framework_id}' has insufficient cluster mapping coverage: "
            f"{len(control_clusters)}/{total} controls mapped; at least {threshold}% is required"
        )
    if coverage < 1.0 and framework_id not in _WARNED_CLUSTER_COVERAGE:
        logger.warning(
            "Framework '%s' cluster mapping coverage is %.1f%% (%d/%d); "
            "unmapped controls use degraded singleton handling",
            framework_id,
            coverage * 100,
            len(control_clusters),
            total,
        )
        _WARNED_CLUSTER_COVERAGE.add(framework_id)
    return control_clusters


def _maturity_rating(score: float) -> str:
    return f"M{max(0, min(5, round(score)))}"


def _build_cluster_verdicts(
    items: list,
    control_clusters: dict[str, str],
) -> tuple[dict, dict[str, str]]:
    """Collapse legacy control rows to one deterministic verdict per cluster."""
    from app.schemas.scoring import ClusterVerdict

    status_rank = {
        "unknown": 0,
        "not_implemented": 1,
        "partial": 2,
        "implemented": 3,
        "not_applicable": 4,
    }
    grouped: dict[str, list] = {}
    for item in items:
        cluster_id = (
            item.cluster_id
            or control_clusters.get(item.requirement_id)
            or f"SINGLE.{item.requirement_id}"
        )
        grouped.setdefault(cluster_id, []).append(item)
        control_clusters[item.requirement_id] = cluster_id

    verdicts = {}
    for cluster_id, cluster_items in grouped.items():
        statuses = [
            _LEGACY_TO_MATURITY_STATUS.get(item.compliance_status, "unknown")
            for item in cluster_items
        ]
        applicable = [
            status for status in statuses
            if status not in ("not_applicable", "unknown")
        ]
        if applicable:
            status = min(applicable, key=status_rank.get)
        elif statuses and all(status == "not_applicable" for status in statuses):
            status = "not_applicable"
        else:
            status = "unknown"
        reasoning_parts = []
        for item in cluster_items:
            reasoning = item.gap_description or item.current_state or "No reasoning recorded."
            if reasoning not in reasoning_parts:
                reasoning_parts.append(reasoning)
        verdicts[cluster_id] = ClusterVerdict(
            cluster_id=cluster_id,
            status=status,
            score=MATURITY_STATUS_SCORES[status],
            reasoning=" ".join(reasoning_parts),
            evidence_ids=[],
        )
    return verdicts, control_clusters


def _derive_framework_score(
    framework_id: str,
    cluster_verdicts: dict,
    control_clusters: dict[str, str],
):
    from app.frameworks.registry import FrameworkRegistry
    from app.schemas.scoring import FrameworkScore

    framework = FrameworkRegistry.get(framework_id)
    legacy_status = {
        "not_implemented": "non_compliant",
        "partial": "partially_compliant",
        "implemented": "compliant",
    }
    propagated = []
    covered_controls = 0
    contributing_clusters: set[str] = set()
    for control in framework.all_controls():
        cluster_id = control_clusters.get(control.id)
        verdict = cluster_verdicts.get(cluster_id) if cluster_id else None
        if verdict is None:
            continue
        covered_controls += 1
        contributing_clusters.add(cluster_id)
        if verdict.status not in legacy_status:
            continue
        propagated.append({
            "requirement_id": control.id,
            "compliance_status": legacy_status[verdict.status],
        })

    legacy_score = compute_framework_scores(propagated, framework_id)
    overall_score = round(legacy_score["overall_score"] / 20, 2)
    domain_scores = {
        key: round(value["score"] / 20, 2)
        for key, value in legacy_score["domain_scores"].items()
        if value["applicable"]
    }
    return FrameworkScore(
        framework_id=framework_id,
        overall_score=overall_score,
        overall_rating=_maturity_rating(overall_score),
        by_domain=domain_scores,
        control_count=framework.control_count(),
        covered_control_count=covered_controls,
        contributing_clusters=sorted(contributing_clusters),
    )


def score(
    assessment_id: str | int,
    framework_ids: list[str],
    *,
    _session=None,
) -> ScoringResult:
    """Return cluster-first scores for every framework on an assessment."""
    from app.models.assessment import Assessment
    from app.models.report import GapItem, GapReport

    framework_ids = list(dict.fromkeys(framework_ids))
    if not framework_ids:
        raise ValueError("score() requires at least one framework id")

    merged_clusters: dict[str, str] = {}
    for framework_id in framework_ids:
        merged_clusters.update(_validated_cluster_mapping(framework_id))

    owns_session = _session is None
    db = _session or SessionLocal()
    try:
        assessment = db.get(Assessment, str(assessment_id))
        if assessment is None:
            raise ValueError(f"Assessment {assessment_id!r} does not exist")
        if set(assessment.frameworks) != set(framework_ids):
            raise ValueError(
                f"Assessment is not configured for exactly {framework_ids}"
            )
        report = (
            db.query(GapReport)
            .filter(GapReport.assessment_id == str(assessment_id))
            .first()
        )
        items = (
            db.query(GapItem).filter(GapItem.report_id == report.id).all()
            if report
            else []
        )
    finally:
        if owns_session:
            db.close()

    cluster_verdicts, control_clusters = _build_cluster_verdicts(
        items,
        merged_clusters,
    )
    per_framework = {
        framework_id: _derive_framework_score(
            framework_id,
            cluster_verdicts,
            control_clusters,
        )
        for framework_id in framework_ids
    }
    return ScoringResult(
        per_framework=per_framework,
        cluster_verdicts=cluster_verdicts,
        unique_clusters=len(cluster_verdicts),
        total_controls_evaluated=sum(
            framework_score.covered_control_count
            for framework_score in per_framework.values()
        ),
    )


def compute_delta(current_items: list, previous_items: list) -> dict:
    """Compare compliance status by requirement across two assessments."""
    previous_by_requirement = {
        item.requirement_id: item for item in previous_items
    }
    status_rank = {
        "non_compliant": 0,
        "partially_compliant": 1,
        "planned": 2,
        "compliant": 3,
        "not_applicable": 3,
    }
    status_score = {
        "non_compliant": 0,
        "partially_compliant": 50,
        "planned": 75,
        "compliant": 100,
        "not_applicable": 100,
    }

    deltas = []
    improved = 0
    regressed = 0
    unchanged = 0

    for item in current_items:
        previous = previous_by_requirement.get(item.requirement_id)
        if not previous:
            deltas.append(
                {
                    "requirement_id": item.requirement_id,
                    "requirement_title": item.requirement_title,
                    "old_status": None,
                    "new_status": item.compliance_status,
                    "score_delta": status_score.get(item.compliance_status, 0),
                    "status_changed": True,
                    "is_new": True,
                }
            )
            continue

        old_status = previous.compliance_status
        new_status = item.compliance_status
        old_rank = status_rank.get(old_status, 0)
        new_rank = status_rank.get(new_status, 0)
        if new_rank > old_rank:
            improved += 1
        elif new_rank < old_rank:
            regressed += 1
        else:
            unchanged += 1

        deltas.append(
            {
                "requirement_id": item.requirement_id,
                "requirement_title": item.requirement_title,
                "old_status": old_status,
                "new_status": new_status,
                "score_delta": (
                    status_score.get(new_status, 0)
                    - status_score.get(old_status, 0)
                ),
                "status_changed": new_status != old_status,
                "is_new": False,
            }
        )

    return {
        "deltas": sorted(
            deltas,
            key=lambda delta: (
                not delta["status_changed"],
                delta["requirement_id"],
            ),
        ),
        "summary": {
            "improved": improved,
            "regressed": regressed,
            "unchanged": unchanged,
        },
    }


def get_rating(score: float) -> str:
    for threshold, rating in RATING_THRESHOLDS:
        if score >= threshold:
            return rating
    return "Non-Compliant"


def compute_scores(assessments: list[dict]) -> dict:
    """Weighted DPDPA compliance score. Thin wrapper — see compute_framework_scores()."""
    result = compute_framework_scores(assessments, "dpdpa")
    return {
        "overall_score": result["overall_score"],
        "overall_rating": result["overall_rating"],
        "chapter_scores": result["domain_scores"],
    }


def compute_summary_stats(assessments: list[dict]) -> dict:
    """Compute counts for the dashboard summary."""
    counts = {
        "compliant": 0,
        "partially_compliant": 0,
        "non_compliant": 0,
        "not_assessed": 0,
        "not_applicable": 0,
    }
    critical_gaps = 0
    high_gaps = 0

    for a in assessments:
        status = a.get("compliance_status", "not_assessed")
        counts[status] = counts.get(status, 0) + 1
        if status in ("non_compliant", "partially_compliant"):
            risk = a.get("risk_level", "")
            if risk == "critical":
                critical_gaps += 1
            elif risk == "high":
                high_gaps += 1

    return {
        **counts,
        "total_requirements": sum(counts.values()),
        "critical_gaps": critical_gaps,
        "high_gaps": high_gaps,
    }


# ─── Initiative Generation ───────────────────────────────────────────────────

# Maps requirement_id prefix/exact → root cause. Claude now assigns these, but
# this is used as a fallback when Claude doesn't return root_cause_category.
_REQ_ROOT_CAUSE_FALLBACK: dict[str, str] = {
    "CH2.CONSENT": "process",
    "CM.RECORDS": "process",
    "CM.GRANULAR": "process",
    "CH2.NOTICE": "policy",
    "CH2.PURPOSE": "policy",
    "CH2.MINIMIZE": "policy",
    "CH2.ACCURACY": "policy",
    "CH2.SECURITY": "technology",
    "CH3.ACCESS": "process",
    "CH3.CORRECT": "process",
    "CH3.GRIEVANCE": "people",
    "CH3.NOMINATE": "process",
    "CH4.CHILD": "technology",
    "CH4.SDF": "governance",
    "CB.TRANSFER": "governance",
    "BN.NOTIFY": "process",
}

_EFFORT_RANK = {"low": 1, "medium": 2, "high": 3}
_EFFORT_FROM_RANK = {1: "low", 2: "medium", 3: "high"}

_BUDGET_BANDS = {
    ("low", "low"): "under_10k",
    ("low", "medium"): "10k_to_50k",
    ("low", "high"): "10k_to_50k",
    ("medium", "low"): "10k_to_50k",
    ("medium", "medium"): "50k_to_150k",
    ("medium", "high"): "50k_to_150k",
    ("high", "low"): "50k_to_150k",
    ("high", "medium"): "above_150k",
    ("high", "high"): "above_150k",
}


def _get_root_cause(assessment: dict) -> str:
    """Get root cause from Claude output or fall back to prefix mapping."""
    root = assessment.get("root_cause_category")
    if root in ROOT_CAUSE_CLUSTERS:
        return root
    req_id = assessment.get("requirement_id", "")
    for prefix, cluster in _REQ_ROOT_CAUSE_FALLBACK.items():
        if req_id.startswith(prefix):
            return cluster
    return "process"


def generate_initiatives(assessments: list[dict]) -> list[dict]:
    """
    Cluster non-compliant gap items by root cause and generate named initiatives.

    Returns a list of initiative dicts ready for saving to the Initiative model.
    """
    # Only gaps need remediation
    gaps = [
        a for a in assessments
        if a.get("compliance_status") in ("non_compliant", "partially_compliant")
    ]
    if not gaps:
        return []

    # Group by root cause
    clusters: dict[str, list[dict]] = {}
    for a in gaps:
        cluster = _get_root_cause(a)
        clusters.setdefault(cluster, []).append(a)

    initiatives = []
    for idx, (cluster, items) in enumerate(clusters.items(), start=1):
        req_ids = [a["requirement_id"] for a in items]
        max_priority = min(a.get("remediation_priority", 3) for a in items)  # lower = more urgent
        max_effort_rank = max(_EFFORT_RANK.get(a.get("remediation_effort", "medium"), 2) for a in items)
        max_timeline = max(a.get("timeline_weeks", 8) for a in items)
        effort = _EFFORT_FROM_RANK[max_effort_rank]

        # Determine budget band from effort + timeline
        timeline_band = "low" if max_timeline <= 4 else "medium" if max_timeline <= 12 else "high"
        budget = _BUDGET_BANDS.get((effort, timeline_band), "50k_to_150k")

        cluster_info = ROOT_CAUSE_CLUSTERS.get(cluster, {})
        title = _name_initiative(cluster, req_ids, cluster_info.get("title", cluster))

        initiatives.append({
            "initiative_id": f"INIT-{idx:03d}",
            "title": title,
            "root_cause": cluster_info.get("description", ""),
            "root_cause_category": cluster,
            "requirements_addressed": req_ids,
            "combined_effort": effort,
            "combined_timeline_weeks": max_timeline,
            "priority": max_priority,
            "budget_estimate_band": budget,
            "suggested_approach": _build_approach(cluster, req_ids),
        })

    # Sort by priority (most urgent first)
    initiatives.sort(key=lambda x: x["priority"])
    return initiatives


def _name_initiative(cluster: str, req_ids: list[str], default_title: str) -> str:
    """Generate a descriptive initiative name based on requirement composition."""
    patterns = [
        (["CH2.CONSENT", "CM."], "Consent Management Platform Implementation"),
        (["CH2.SECURITY", "BN.NOTIFY"], "Security Controls & Breach Response Program"),
        (["CH4.SDF"], "Significant Data Fiduciary Compliance Program"),
        (["CH4.CHILD"], "Children's Data Protection Program"),
        (["CB.TRANSFER"], "Cross-Border Data Transfer Governance"),
        (["CH2.NOTICE", "CH2.PURPOSE", "CH2.MINIMIZE"], "Privacy Policy & Documentation Sprint"),
        (["CH3."], "Data Principal Rights Enablement"),
    ]
    for prefixes, name in patterns:
        if any(any(r.startswith(p) for p in prefixes) for r in req_ids):
            return name
    return f"{default_title} Remediation Program"


def _build_approach(cluster: str, req_ids: list[str]) -> str:
    """Build a concise suggested approach for an initiative."""
    approaches = {
        "policy": (
            f"Engage a privacy counsel to draft/update {len(req_ids)} policy documents. "
            "Conduct a policy gap review workshop. Publish updated policies to all stakeholders."
        ),
        "people": (
            f"Define DPO/privacy roles and responsibilities. "
            f"Run a targeted privacy awareness training program covering {len(req_ids)} requirement areas. "
            "Conduct role-based training for data handlers."
        ),
        "process": (
            f"Map and document {len(req_ids)} operational processes. "
            "Implement process controls, SLAs, and tracking mechanisms. "
            "Run a tabletop exercise to validate process coverage."
        ),
        "technology": (
            f"Evaluate and procure/configure tools addressing {len(req_ids)} technical control gaps. "
            "Prioritize encryption, consent management, and access control tooling. "
            "Run penetration test post-implementation."
        ),
        "governance": (
            f"Establish privacy governance committee. "
            f"Implement DPIA process and annual audit cadence covering {len(req_ids)} governance requirements. "
            "Develop board-level privacy reporting dashboard."
        ),
    }
    return approaches.get(cluster, f"Address {len(req_ids)} identified gaps through targeted remediation.")


# ─── Multi-Framework Scoring ─────────────────────────────────────────────


def compute_framework_scores(assessments: list[dict], framework_id: str) -> dict:
    """
    Compute weighted compliance scores for any registered framework.

    Same algorithm as compute_scores() but loads weights from FrameworkRegistry
    instead of hardcoded DPDPA_FRAMEWORK.
    """
    from app.frameworks.registry import FrameworkRegistry

    fw = FrameworkRegistry.get(framework_id)
    framework_dict = fw.as_legacy_framework_dict()

    status_map = {a["requirement_id"]: a["compliance_status"] for a in assessments}

    domain_scores = {}
    for domain_key, domain in framework_dict.items():
        section_scores = []
        section_weights = []

        for section_key, section in domain["sections"].items():
            scored_values = []
            for req in section["requirements"]:
                status = status_map.get(req["id"], "not_assessed")
                if status not in KNOWN_STATUSES:
                    status = "not_assessed"
                if status in STATUS_SCORES:
                    scored_values.append(STATUS_SCORES[status])

            if scored_values:
                section_avg = sum(scored_values) / len(scored_values)
                section_scores.append(section_avg)
                section_weights.append(section["weight"])

        if section_scores and section_weights:
            total_weight = sum(section_weights)
            score = sum(s * w for s, w in zip(section_scores, section_weights)) / total_weight
        else:
            score = 0.0

        domain_scores[domain_key] = {
            "score": round(score, 1),
            "rating": get_rating(score),
            "title": domain["title"],
            "applicable": bool(section_scores),
        }

    # Overall score: weighted average of domains
    overall_numerator = 0.0
    overall_denominator = 0.0
    for domain_key, domain in framework_dict.items():
        if domain_key in domain_scores and domain_scores[domain_key]["applicable"]:
            overall_numerator += domain_scores[domain_key]["score"] * domain["weight"]
            overall_denominator += domain["weight"]

    overall_score = round(overall_numerator / overall_denominator, 1) if overall_denominator > 0 else 0.0

    return {
        "overall_score": overall_score,
        "overall_rating": get_rating(overall_score),
        "domain_scores": domain_scores,
    }


def namespaced_domain_scores(per_framework_scores: dict[str, dict]) -> dict:
    """Flatten per-framework domains into the report chapter-score shape.

    The framework id remains part of every key so chapter scores can never be
    mistaken for a cross-framework aggregate.
    """
    from app.frameworks.registry import FrameworkRegistry

    namespaced = {}
    for framework_id, framework_scores in per_framework_scores.items():
        if is_failed_framework_score(framework_scores):
            continue
        framework = FrameworkRegistry.get_or_none(framework_id)
        framework_name = framework.name if framework else framework_id.upper()
        for domain_key, domain_score in framework_scores.get("domain_scores", {}).items():
            namespaced[f"{framework_id}:{domain_key}"] = {
                "score": domain_score["score"],
                "rating": domain_score["rating"],
                "title": f"{framework_name} — {domain_score['title']}",
                "applicable": domain_score.get("applicable", True),
            }
    return namespaced


def report_framework_scores(report, assessment) -> dict[str, dict]:
    """Read a report's per-framework scores, with one legacy fallback."""
    try:
        parsed = json.loads(getattr(report, "framework_scores", None))
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    if len(assessment.frameworks) != 1:
        return {}

    try:
        domain_scores = json.loads(report.chapter_scores or "{}")
    except (json.JSONDecodeError, TypeError):
        domain_scores = {}
    framework_id = assessment.frameworks[0]
    return {
        framework_id: {
            "overall_score": report.overall_score,
            "overall_rating": get_rating(report.overall_score),
            "domain_scores": domain_scores,
        }
    }


def generate_multi_framework_initiatives(
    all_assessments: dict[str, list[dict]],
) -> list[dict]:
    """
    Generate cross-framework initiatives by clustering gaps across all frameworks.

    Args:
        all_assessments: {fw_id: [assessment dicts]}
    """
    # Merge all gaps
    all_gaps = []
    for fw_id, assessments in all_assessments.items():
        for a in assessments:
            if a.get("compliance_status") in ("non_compliant", "partially_compliant"):
                all_gaps.append({**a, "framework_id": fw_id})

    if not all_gaps:
        return []

    # Group by root cause (same logic, but works across frameworks)
    clusters: dict[str, list[dict]] = {}
    for a in all_gaps:
        root = a.get("root_cause_category", "process")
        if root not in ("policy", "people", "process", "technology", "governance"):
            root = "process"
        clusters.setdefault(root, []).append(a)

    initiatives = []
    for idx, (cluster, items) in enumerate(clusters.items(), start=1):
        req_ids = [a["requirement_id"] for a in items]
        fw_ids = sorted(set(a.get("framework_id", "") for a in items))
        max_priority = min(a.get("remediation_priority", 3) for a in items)
        max_effort_rank = max(_EFFORT_RANK.get(a.get("remediation_effort", "medium"), 2) for a in items)
        max_timeline = max(a.get("timeline_weeks", 8) for a in items)
        effort = _EFFORT_FROM_RANK[max_effort_rank]
        timeline_band = "low" if max_timeline <= 4 else "medium" if max_timeline <= 12 else "high"
        budget = _BUDGET_BANDS.get((effort, timeline_band), "50k_to_150k")

        initiatives.append({
            "initiative_id": f"INIT-{idx:03d}",
            "title": f"{cluster.title()} Remediation — {', '.join(fw_ids)}",
            "root_cause": "",
            "root_cause_category": cluster,
            "requirements_addressed": req_ids,
            "frameworks_addressed": fw_ids,
            "combined_effort": effort,
            "combined_timeline_weeks": max_timeline,
            "priority": max_priority,
            "budget_estimate_band": budget,
            "suggested_approach": _build_approach(cluster, req_ids),
        })

    initiatives.sort(key=lambda x: x["priority"])
    return initiatives
