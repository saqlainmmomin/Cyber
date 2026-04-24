"""
Cluster resolution engine — resolves which Unified Control Clusters apply
to a given set of selected frameworks.

For single-framework assessments, each control becomes its own singleton
cluster (no merge overhead). For multi-framework, overlapping controls
are grouped into UCCs using pre-defined mappings from mappings/clusters.py.
"""

from __future__ import annotations

import logging

from app.frameworks.mapping import MappedControl, UnifiedControlCluster
from app.frameworks.registry import FrameworkRegistry

logger = logging.getLogger(__name__)

# Domain group ordering for questionnaire presentation
DOMAIN_GROUP_ORDER = [
    "governance",
    "data_protection",
    "consent_rights",
    "security",
    "incident_response",
    "cross_border",
    "children_vulnerable",
    "audit_compliance",
    "other",
]

# Criticality rank for sorting (lower = more critical)
_CRITICALITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _load_cluster_mappings() -> list[dict]:
    """Load pre-defined UCC cluster mapping data."""
    try:
        from app.frameworks.mappings.clusters import CONTROL_CLUSTERS

        return CONTROL_CLUSTERS
    except ImportError:
        logger.warning("No cluster mappings found — all controls will be singleton clusters")
        return []


def _infer_domain_group(tags: list[str]) -> str:
    """Infer domain group from control tags for ordering."""
    tag_set = set(tags)

    if tag_set & {"governance", "dpo", "audit", "dpia", "compliance-audit"}:
        return "governance"
    if tag_set & {"consent", "lawful-basis", "granular-consent", "consent-withdrawal", "consent-management"}:
        return "consent_rights"
    if tag_set & {"data-subject-rights", "right-of-access", "right-to-rectification", "right-to-erasure", "grievance-redressal"}:
        return "consent_rights"
    if tag_set & {"privacy-notice", "transparency", "purpose-limitation", "data-minimization", "data-retention", "data-accuracy"}:
        return "data_protection"
    if tag_set & {"encryption", "access-control", "security-safeguards", "technical-measures"}:
        return "security"
    if tag_set & {"breach-notification", "incident-response", "breach-register"}:
        return "incident_response"
    if tag_set & {"cross-border", "data-transfer", "data-localization"}:
        return "cross_border"
    if tag_set & {"children-data", "age-verification", "parental-consent"}:
        return "children_vulnerable"
    if tag_set & {"audit", "independent-auditor", "compliance-audit"}:
        return "audit_compliance"
    return "other"


def _highest_criticality(control_ids: set[str], framework_ids: list[str]) -> str:
    """Find highest criticality across controls from any framework."""
    best = "low"
    best_rank = _CRITICALITY_RANK["low"]
    for fw_id in framework_ids:
        fw = FrameworkRegistry.get(fw_id)
        for ctrl in fw.all_controls():
            if ctrl.id in control_ids:
                rank = _CRITICALITY_RANK.get(ctrl.criticality, 3)
                if rank < best_rank:
                    best = ctrl.criticality
                    best_rank = rank
    return best


def _build_singleton_cluster(
    framework_id: str,
    control_id: str,
    ctrl_tags: list[str],
    ctrl_title: str,
) -> UnifiedControlCluster:
    """Create a single-control cluster (no cross-framework mapping)."""
    domain_group = _infer_domain_group(ctrl_tags)

    # Pull question from framework definition
    fw = FrameworkRegistry.get(framework_id)
    q_def = fw.questions.get(control_id)
    primary_question = q_def.question if q_def else ""
    primary_guidance = q_def.guidance if q_def else ""

    return UnifiedControlCluster(
        cluster_id=f"SINGLE.{control_id}",
        topic=ctrl_title,
        domain_group=domain_group,
        tags=ctrl_tags,
        controls=[MappedControl(framework_id=framework_id, control_id=control_id)],
        primary_question=primary_question,
        primary_guidance=primary_guidance,
    )


def resolve_clusters(
    framework_ids: list[str],
    excluded_controls: set[str] | None = None,
) -> list[UnifiedControlCluster]:
    """
    Resolve the set of assessment clusters for the given frameworks.

    For single-framework assessments: one cluster per control.
    For multi-framework: overlapping controls merged via UCC mappings,
    unmatched controls become singletons.

    Returns clusters sorted by domain group, then criticality.
    """
    excluded = excluded_controls or set()

    # Collect all controls across selected frameworks
    all_controls: dict[str, tuple[str, list[str], str]] = {}  # control_id -> (fw_id, tags, title)
    for fw_id in framework_ids:
        fw = FrameworkRegistry.get(fw_id)
        for ctrl in fw.all_controls():
            if ctrl.id not in excluded:
                all_controls[ctrl.id] = (fw_id, ctrl.tags, ctrl.title)

    if len(framework_ids) == 1:
        # Single framework — no merging needed
        clusters = []
        fw_id = framework_ids[0]
        for ctrl_id, (_, tags, title) in all_controls.items():
            clusters.append(_build_singleton_cluster(fw_id, ctrl_id, tags, title))
        return _sort_clusters(clusters, framework_ids)

    # Multi-framework — use UCC mappings
    cluster_defs = _load_cluster_mappings()
    claimed_controls: set[str] = set()
    clusters: list[UnifiedControlCluster] = []

    for cdef in cluster_defs:
        # Filter to controls that exist in our selected frameworks + not excluded
        mapped = []
        cluster_tags: set[str] = set(cdef.get("tags", []))

        for mc in cdef.get("controls", []):
            if mc["framework"] not in framework_ids:
                continue
            if mc["control"] not in all_controls:
                continue
            if mc["control"] in excluded:
                continue

            mapped.append(
                MappedControl(
                    framework_id=mc["framework"],
                    control_id=mc["control"],
                    specificity_delta=mc.get("delta"),
                )
            )
            # Merge tags from actual control
            _, ctrl_tags, _ = all_controls[mc["control"]]
            cluster_tags.update(ctrl_tags)

        if not mapped:
            continue

        domain_group = _infer_domain_group(list(cluster_tags))

        cluster = UnifiedControlCluster(
            cluster_id=cdef["cluster_id"],
            topic=cdef["topic"],
            domain_group=domain_group,
            tags=sorted(cluster_tags),
            controls=mapped,
            primary_question=cdef.get("primary_question", ""),
            primary_guidance=cdef.get("primary_guidance", ""),
        )
        clusters.append(cluster)
        claimed_controls.update(mc.control_id for mc in mapped)

    # Create singleton clusters for unclaimed controls
    for ctrl_id, (fw_id, tags, title) in all_controls.items():
        if ctrl_id not in claimed_controls:
            clusters.append(_build_singleton_cluster(fw_id, ctrl_id, tags, title))

    return _sort_clusters(clusters, framework_ids)


def _sort_clusters(
    clusters: list[UnifiedControlCluster],
    framework_ids: list[str],
) -> list[UnifiedControlCluster]:
    """Sort clusters by domain group order, then by criticality."""

    def sort_key(c: UnifiedControlCluster) -> tuple[int, int, str]:
        group_idx = (
            DOMAIN_GROUP_ORDER.index(c.domain_group)
            if c.domain_group in DOMAIN_GROUP_ORDER
            else len(DOMAIN_GROUP_ORDER)
        )
        crit = _highest_criticality(c.control_ids, framework_ids)
        crit_rank = _CRITICALITY_RANK.get(crit, 3)
        return (group_idx, crit_rank, c.topic)

    return sorted(clusters, key=sort_key)
