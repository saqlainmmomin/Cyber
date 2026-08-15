"""
Multi-framework questionnaire builder.

Generates a unified questionnaire from Unified Control Clusters (UCCs).
For single-framework assessments, delegates to the existing DPDPA questionnaire
builder. For multi-framework, merges questions across frameworks using clusters.
"""

from __future__ import annotations

import logging

from app.frameworks.cluster_engine import resolve_clusters
from app.frameworks.mapping import UnifiedControlCluster
from app.frameworks.registry import FrameworkRegistry

logger = logging.getLogger(__name__)

ANSWER_OPTIONS = [
    "fully_implemented",
    "partially_implemented",
    "planned",
    "not_implemented",
    "not_applicable",
]

# Criticality rank for sorting within domain groups
_CRITICALITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def build_multi_questionnaire(
    framework_ids: list[str],
    excluded_controls: set[str] | None = None,
    context_profile: dict | None = None,
) -> list[dict]:
    """
    Build a unified questionnaire for one or more frameworks.

    For single-framework DPDPA, falls back to the existing build_questionnaire().
    For everything else, uses the UCC cluster engine.

    Returns a list of question dicts, each representing one cluster:
    {
        "cluster_id": str,
        "topic": str,
        "domain_group": str,
        "frameworks_covered": list[str],
        "primary_question": str,
        "primary_guidance": str,
        "follow_ups": list[dict],    # framework-specific sub-questions
        "controls": list[dict],      # {framework_id, control_id}
        "criticality": str,
        "answer_options": list[str],
        "relevance_weight": float,
        "context_note": str | None,
    }
    """
    if len(framework_ids) == 1 and framework_ids[0] == "dpdpa":
        return _build_dpdpa_questionnaire(context_profile)

    clusters = resolve_clusters(framework_ids, excluded_controls)
    questions = []

    for cluster in clusters:
        q = _cluster_to_question(cluster, framework_ids, context_profile)
        if q:
            questions.append(q)

    return questions


def _build_dpdpa_questionnaire(context_profile: dict | None) -> list[dict]:
    """Delegate to existing DPDPA questionnaire builder for backward compat."""
    from app.dpdpa.questionnaire import build_questionnaire

    legacy_qs = build_questionnaire(context_profile=context_profile)

    # Wrap in cluster-compatible format
    wrapped = []
    for q in legacy_qs:
        wrapped.append(
            {
                "cluster_id": f"SINGLE.{q['id']}",
                "topic": q.get("section_title", ""),
                "domain_group": _infer_domain_group_from_chapter(q.get("chapter", "")),
                "frameworks_covered": ["dpdpa"],
                "primary_question": q["question"],
                "primary_guidance": q.get("guidance", ""),
                "follow_ups": [],
                "controls": [{"framework_id": "dpdpa", "control_id": q["id"]}],
                "criticality": q.get("criticality", "medium"),
                "answer_options": ANSWER_OPTIONS,
                "relevance_weight": q.get("relevance_weight", 1.0),
                "context_note": q.get("context_note"),
                # Preserve legacy fields for backward compat
                "id": q["id"],
                "chapter": q.get("chapter", ""),
                "chapter_title": q.get("chapter_title", ""),
                "section": q.get("section", ""),
                "section_title": q.get("section_title", ""),
                "section_ref": q.get("section_ref", ""),
                "skip_if": q.get("skip_if"),
            }
        )
    return wrapped


def _cluster_to_question(
    cluster: UnifiedControlCluster,
    framework_ids: list[str],
    context_profile: dict | None,
) -> dict | None:
    """Convert a UCC cluster into a questionnaire question dict."""

    # Determine primary question — use cluster's if set, else from first framework's question
    primary_q = cluster.primary_question
    primary_g = cluster.primary_guidance

    if not primary_q:
        # Fall back to first control's question from framework definition
        for mc in cluster.controls:
            fw = FrameworkRegistry.get(mc.framework_id)
            q_def = fw.questions.get(mc.control_id)
            if q_def and q_def.question:
                primary_q = q_def.question
                primary_g = q_def.guidance
                break

    if not primary_q:
        # Last resort — generate from topic
        primary_q = f"Has your organization implemented controls for: {cluster.topic}?"

    # Build follow-up questions for framework-specific deltas
    follow_ups = []
    for mc in cluster.controls:
        if mc.specificity_delta:
            fw = FrameworkRegistry.get(mc.framework_id)
            ctrl = fw.get_control(mc.control_id)
            follow_ups.append(
                {
                    "framework_id": mc.framework_id,
                    "framework_name": fw.name,
                    "control_id": mc.control_id,
                    "control_reference": ctrl.reference if ctrl else "",
                    "question": mc.specificity_delta,
                }
            )

    # Determine criticality (highest across all member controls)
    criticality = _max_criticality(cluster, framework_ids)

    # Relevance weighting from context profile
    relevance_weight = 1.0
    context_note = None
    if context_profile:
        relevance_weight, context_note = _compute_cluster_relevance(
            cluster, context_profile
        )

    return {
        "cluster_id": cluster.cluster_id,
        "topic": cluster.topic,
        "domain_group": cluster.domain_group,
        "frameworks_covered": sorted(cluster.framework_ids),
        "primary_question": primary_q,
        "primary_guidance": primary_g,
        "follow_ups": follow_ups,
        "controls": [
            {"framework_id": mc.framework_id, "control_id": mc.control_id}
            for mc in cluster.controls
        ],
        "criticality": criticality,
        "answer_options": ANSWER_OPTIONS,
        "relevance_weight": relevance_weight,
        "context_note": context_note,
    }


def _max_criticality(cluster: UnifiedControlCluster, framework_ids: list[str]) -> str:
    """Find highest criticality across all controls in the cluster."""
    best = "low"
    best_rank = _CRITICALITY_RANK["low"]
    for mc in cluster.controls:
        fw = FrameworkRegistry.get_or_none(mc.framework_id)
        if not fw:
            continue
        ctrl = fw.get_control(mc.control_id)
        if ctrl:
            rank = _CRITICALITY_RANK.get(ctrl.criticality, 3)
            if rank < best_rank:
                best = ctrl.criticality
                best_rank = rank
    return best


def _compute_cluster_relevance(
    cluster: UnifiedControlCluster,
    profile: dict,
) -> tuple[float, str | None]:
    """Compute relevance weight and context note for a cluster."""
    weight = 1.0
    notes = []

    risk_tier = profile.get("risk_tier", "MEDIUM")
    if risk_tier == "HIGH":
        # Boost critical clusters for high-risk orgs
        for mc in cluster.controls:
            fw = FrameworkRegistry.get_or_none(mc.framework_id)
            if fw:
                ctrl = fw.get_control(mc.control_id)
                if ctrl and ctrl.criticality == "critical":
                    weight *= 1.2
                    break

    # Boost cross-border clusters if org transfers data internationally
    if profile.get("cross_border_transfers") and cluster.domain_group == "cross_border":
        weight *= 1.3
        notes.append("Your organization transfers data internationally — these controls are directly applicable.")

    # Boost children data clusters
    if profile.get("processes_children_data") and cluster.domain_group == "children_vulnerable":
        weight *= 1.3
        notes.append("You process children's data — heightened requirements apply.")

    # Industry context
    if profile.get("industry_context") and weight > 1.1:
        notes.append(profile["industry_context"])

    return round(weight, 2), " ".join(notes) if notes else None


def _infer_domain_group_from_chapter(chapter: str) -> str:
    """Map DPDPA chapter keys to domain groups for backward compat."""
    mapping = {
        "chapter_2": "data_protection",
        "chapter_3": "consent_rights",
        "chapter_4": "governance",
        "consent_management": "consent_rights",
        "cross_border": "cross_border",
        "breach_notification": "incident_response",
    }
    return mapping.get(chapter, "other")
