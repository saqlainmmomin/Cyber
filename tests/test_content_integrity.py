"""
Content integrity checks for framework definitions and UCC cluster mappings.

These tests are the definition of done for framework-content work
(see tasks/handoffs/2026-07-11-ucc-content-completion.md). They enforce:

1. Every cluster references real framework/control ids.
2. A control belongs to at most ONE cluster — the cluster engine claims a
   control for every cluster that lists it, so duplicate membership means
   the same control is asked about twice in a multi-framework assessment.
3. Every control is either clustered or explicitly listed in
   INTENTIONAL_SINGLETONS (a deliberate, reviewed decision — not an omission).
4. Every question has guidance text; every control has a question and tags.
"""

from collections import Counter

from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
from app.frameworks.definitions.gdpr import GDPR_DEFINITION
from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION
from app.frameworks.mappings.clusters import CONTROL_CLUSTERS, INTENTIONAL_SINGLETONS

DEFINITIONS = {
    d.id: d
    for d in (
        DPDPA_DEFINITION,
        ISO27001_DEFINITION,
        GDPR_DEFINITION,
        HIPAA_DEFINITION,
        NIST_CSF_DEFINITION,
        PCI_DSS_DEFINITION,
    )
}

CONTROL_IDS = {fw_id: {c.id for c in d.all_controls()} for fw_id, d in DEFINITIONS.items()}

CLUSTERED_IDS = {
    member["control"] for cluster in CONTROL_CLUSTERS for member in cluster["controls"]
}


def test_cluster_ids_unique():
    ids = [c["cluster_id"] for c in CONTROL_CLUSTERS]
    dupes = [k for k, n in Counter(ids).items() if n > 1]
    assert not dupes, f"Duplicate cluster_ids: {dupes}"


def test_cluster_members_reference_real_controls():
    bad = []
    for cluster in CONTROL_CLUSTERS:
        for member in cluster["controls"]:
            fw, ctrl = member["framework"], member["control"]
            if fw not in CONTROL_IDS:
                bad.append(f"{cluster['cluster_id']}: unknown framework {fw!r}")
            elif ctrl not in CONTROL_IDS[fw]:
                bad.append(f"{cluster['cluster_id']}: {fw} has no control {ctrl!r}")
    assert not bad, "\n".join(bad)


def test_no_control_in_multiple_clusters():
    membership: dict[str, list[str]] = {}
    for cluster in CONTROL_CLUSTERS:
        for member in cluster["controls"]:
            membership.setdefault(member["control"], []).append(cluster["cluster_id"])
    dupes = {ctrl: cls for ctrl, cls in membership.items() if len(cls) > 1}
    assert not dupes, (
        f"{len(dupes)} controls claimed by multiple clusters "
        f"(each gets asked twice in multi-framework assessments):\n"
        + "\n".join(f"  {c}: {cls}" for c, cls in sorted(dupes.items()))
    )


def test_every_cluster_merges_at_least_two_controls():
    thin = [c["cluster_id"] for c in CONTROL_CLUSTERS if len(c["controls"]) < 2]
    assert not thin, f"Clusters with <2 controls (should be singletons instead): {thin}"


def test_cluster_prompts_and_tags_populated():
    bad = [
        c["cluster_id"]
        for c in CONTROL_CLUSTERS
        if not c.get("primary_question") or not c.get("primary_guidance") or not c.get("tags")
    ]
    assert not bad, f"Clusters missing question/guidance/tags: {bad}"


def test_every_control_clustered_or_intentional_singleton():
    missing: dict[str, list[str]] = {}
    for fw_id, ids in CONTROL_IDS.items():
        allowed = INTENTIONAL_SINGLETONS.get(fw_id, set())
        orphans = sorted(ids - CLUSTERED_IDS - allowed)
        if orphans:
            missing[fw_id] = orphans
    assert not missing, (
        "Controls neither clustered nor listed in INTENTIONAL_SINGLETONS:\n"
        + "\n".join(f"  {fw} ({len(ids)}): {', '.join(ids)}" for fw, ids in missing.items())
    )


def test_intentional_singletons_are_valid_and_not_clustered():
    bad = []
    for fw_id, ids in INTENTIONAL_SINGLETONS.items():
        if fw_id not in CONTROL_IDS:
            bad.append(f"unknown framework {fw_id!r}")
            continue
        for ctrl in ids:
            if ctrl not in CONTROL_IDS[fw_id]:
                bad.append(f"{fw_id}: no such control {ctrl!r}")
            elif ctrl in CLUSTERED_IDS:
                bad.append(f"{fw_id}: {ctrl} is in a cluster AND listed as singleton")
    assert not bad, "\n".join(bad)


def test_every_control_has_question():
    missing = {
        fw_id: sorted(ids - set(d.questions))
        for fw_id, d in DEFINITIONS.items()
        if (ids := CONTROL_IDS[fw_id]) - set(d.questions)
    }
    assert not missing, f"Controls without questions: {missing}"


def test_every_question_has_guidance():
    missing = {
        fw_id: sorted(k for k, q in d.questions.items() if not q.guidance.strip())
        for fw_id, d in DEFINITIONS.items()
        if any(not q.guidance.strip() for q in d.questions.values())
    }
    assert not missing, (
        "Questions missing guidance text:\n"
        + "\n".join(f"  {fw} ({len(ids)}): {', '.join(ids)}" for fw, ids in missing.items())
    )


def test_every_control_has_tags():
    missing = {
        fw_id: sorted(c.id for c in d.all_controls() if not c.tags)
        for fw_id, d in DEFINITIONS.items()
        if any(not c.tags for c in d.all_controls())
    }
    assert not missing, f"Controls without semantic tags: {missing}"
