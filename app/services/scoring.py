"""
Deterministic compliance scoring engine.

Takes Claude's qualitative assessments and computes weighted quantitative scores.
Also handles root cause clustering and initiative generation (post-analysis).
"""

import json
import logging

from app.dpdpa.framework import DPDPA_FRAMEWORK, ROOT_CAUSE_CLUSTERS, get_all_requirements

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


def get_rating(score: float) -> str:
    for threshold, rating in RATING_THRESHOLDS:
        if score >= threshold:
            return rating
    return "Non-Compliant"


def compute_scores(assessments: list[dict]) -> dict:
    """
    Compute weighted compliance scores from Claude's assessment output.

    Args:
        assessments: list of dicts with "requirement_id" and "compliance_status"

    Returns:
        {
            "overall_score": float,
            "overall_rating": str,
            "chapter_scores": {chapter_key: {"score": float, "rating": str, "title": str}}
        }
    """
    # Index assessments by requirement_id
    status_map = {a["requirement_id"]: a["compliance_status"] for a in assessments}

    # Build requirement lookup
    all_reqs = get_all_requirements()
    req_lookup = {r["id"]: r for r in all_reqs}

    chapter_scores = {}

    for chapter_key, chapter in DPDPA_FRAMEWORK.items():
        section_scores = []
        section_weights = []

        for section_key, section in chapter["sections"].items():
            scored_values = []
            for req in section["requirements"]:
                status = status_map.get(req["id"], "not_assessed")
                if status not in KNOWN_STATUSES:
                    logger.warning(
                        "Unexpected compliance_status %r for %s — treating as not_assessed",
                        status, req["id"],
                    )
                    status = "not_assessed"
                if status in STATUS_SCORES:
                    scored_values.append(STATUS_SCORES[status])

            if scored_values:
                section_avg = sum(scored_values) / len(scored_values)
                section_scores.append(section_avg)
                section_weights.append(section["weight"])

        if section_scores and section_weights:
            # Weighted average of sections within chapter
            total_weight = sum(section_weights)
            chapter_score = sum(
                s * w for s, w in zip(section_scores, section_weights)
            ) / total_weight
        else:
            chapter_score = 0.0

        chapter_scores[chapter_key] = {
            "score": round(chapter_score, 1),
            "rating": get_rating(chapter_score),
            "title": chapter["title"],
            "applicable": bool(section_scores),
        }

    # Overall score: weighted average of chapters
    overall_numerator = 0.0
    overall_denominator = 0.0
    for chapter_key, chapter in DPDPA_FRAMEWORK.items():
        if chapter_key in chapter_scores and chapter_scores[chapter_key]["applicable"]:
            overall_numerator += chapter_scores[chapter_key]["score"] * chapter["weight"]
            overall_denominator += chapter["weight"]

    overall_score = (
        round(overall_numerator / overall_denominator, 1) if overall_denominator > 0 else 0.0
    )

    return {
        "overall_score": overall_score,
        "overall_rating": get_rating(overall_score),
        "chapter_scores": chapter_scores,
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
    ("low", "low"): "under_5l",
    ("low", "medium"): "5l_to_25l",
    ("low", "high"): "5l_to_25l",
    ("medium", "low"): "5l_to_25l",
    ("medium", "medium"): "25l_to_1cr",
    ("medium", "high"): "25l_to_1cr",
    ("high", "low"): "25l_to_1cr",
    ("high", "medium"): "above_1cr",
    ("high", "high"): "above_1cr",
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
        budget = _BUDGET_BANDS.get((effort, timeline_band), "25l_to_1cr")

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


def compute_unified_maturity(
    per_framework_results: dict[str, dict],
    per_framework_scores: dict[str, dict],
) -> dict:
    """
    Compute unified maturity view across multiple frameworks.

    Args:
        per_framework_results: {fw_id: {"assessments": [...]}}
        per_framework_scores: {fw_id: compute_framework_scores() output}

    Returns unified maturity dict.
    """
    # Compute overall across frameworks (equal weight by default)
    fw_scores = [s["overall_score"] for s in per_framework_scores.values() if s.get("overall_score")]
    unified_score = round(sum(fw_scores) / len(fw_scores), 1) if fw_scores else 0.0

    # Compute per-topic maturity from maturity_level fields
    topic_maturity: dict[str, dict[str, list[int]]] = {}

    for fw_id, result in per_framework_results.items():
        for assessment in result.get("assessments", []):
            ml = assessment.get("maturity_level")
            if ml is not None:
                root_cause = assessment.get("root_cause_category", "other")
                topic_maturity.setdefault(root_cause, {}).setdefault(fw_id, []).append(ml)

    maturity_by_topic = {}
    for topic, fw_levels in topic_maturity.items():
        per_fw = {}
        all_levels = []
        for fw_id, levels in fw_levels.items():
            avg = round(sum(levels) / len(levels), 1)
            per_fw[fw_id] = avg
            all_levels.extend(levels)
        maturity_by_topic[topic] = {
            "avg_maturity": round(sum(all_levels) / len(all_levels), 1) if all_levels else 0,
            "per_framework": per_fw,
        }

    return {
        "overall_score": unified_score,
        "overall_rating": get_rating(unified_score),
        "framework_scores": per_framework_scores,
        "maturity_by_topic": maturity_by_topic,
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
        budget = _BUDGET_BANDS.get((effort, timeline_band), "25l_to_1cr")

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
