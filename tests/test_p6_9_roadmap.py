"""Contract tests for P6-9: cross-framework remediation roadmap (Actions grouped by UCC cluster).

Handoff: tasks/handoffs/2026-09-28-p6-9-soa-roadmap-comparison.md (D-P6-9-F). On main these
fail only because app.services.remediation_groups and `roadmap.groups` do not exist yet.
Grouping and ordering are deterministic; no LLM is involved.
"""

from __future__ import annotations

import random
from collections import Counter
from datetime import date

from app.frameworks.mappings.clusters import CONTROL_CLUSTERS
from app.frameworks.registry import FrameworkRegistry
from app.services import approved_report
from app.services.report_content import ReportAction, ReportFinding
from tests.p6_9_support import (  # noqa: F401  (fixtures are used by name)
    _no_llm,
    _register_frameworks,
    build,
    control_ids,
    db,
    db_path,
    finding,
    gate,
    http,
    module,
    new_engagement,
    released_assessment,
    upload_root,
)

ISO = "ISO 27001"
DPDPA = "India DPDPA"
NIST = "NIST CSF"


def _groups():
    return module("app.services.remediation_groups")


def _finding(framework_id, requirement_id, *, title, severity="high", priority=1, targets=(), finding_id=None):
    name = FrameworkRegistry.get(framework_id).name
    control = FrameworkRegistry.get(framework_id).get_control(requirement_id)
    return ReportFinding(
        finding_id=finding_id or f"F-{requirement_id}",
        title=title,
        description="d",
        severity=severity,
        priority=priority,
        status_label="Open",
        framework_id=framework_id,
        framework_name=name,
        requirement_id=requirement_id,
        requirement_title=control.title if control else requirement_id,
        outcome_label="Non Compliant",
        decision_label="Approved",
        decided_by="Priya",
        decided_at=None,
        decision_version=2,
        workpaper_ref="x",
        citations_captured=True,
        citations=[],
        actions=[
            ReportAction(title=f"{title} action {index}", owner=owner, target_date=target, status="open", status_label="Open")
            for index, (owner, target) in enumerate(targets, start=1)
        ],
    )


def test_scenario_1_cluster_membership_is_a_function():
    """D-P6-9-F: every (framework, control) sits in at most one UCC cluster, so grouping is unambiguous."""
    groups = _groups()
    counts = Counter((c["framework"], c["control"]) for cluster in CONTROL_CLUSTERS for c in cluster["controls"])
    assert max(counts.values()) == 1
    index = groups.cluster_index()
    assert len(index) == len(counts)
    for key in (("dpdpa", "CH2.SECURITY.1"), ("iso27001", "ISO.A5.15"), ("nist_csf", "NIST.PR.AA.05")):
        assert index[key] == ("CLUSTER_006", "Access Control Baseline"), key
    assert ("iso27001", "ISO.Z9.9") not in index
    assert groups.join_names(["A"]) == "A"
    assert groups.join_names(["A", "B"]) == "A and B"
    assert groups.join_names(["A", "B", "C"]) == "A, B and C"


def test_scenario_2_findings_sharing_a_cluster_form_one_cross_framework_group():
    """D-P6-9-F: one group per cluster; closes every Finding in it; actions ordered by target date."""
    groups = _groups()
    findings = [
        _finding("dpdpa", "CH2.SECURITY.1", title="Weak access to personal data", severity="high",
                 targets=[("Anita", date(2026, 12, 15))]),
        _finding("iso27001", "ISO.A5.15", title="Access policy missing", severity="critical",
                 targets=[("Vikram", date(2026, 11, 1))]),
        _finding("nist_csf", "NIST.PR.AA.05", title="Least privilege not enforced", severity="medium",
                 targets=[(None, None)]),
        _finding("iso27001", "ISO.A5.1", title="Policy not approved", severity="low",
                 targets=[("Ravi", date(2026, 10, 15))]),
        _finding("iso27001", "ISO.A7.1", title="Perimeter undefined", severity="high", targets=[]),
    ]
    result = groups.build_groups(findings, ["dpdpa", "iso27001", "nist_csf"])
    # ISO.A7.1 has no action anywhere in its group, so it is not a roadmap item.
    assert [g["group_id"] for g in result] == ["CLUSTER_001", "CLUSTER_006"]
    access = result[1]
    assert set(access) == {
        "group_id", "topic", "headline", "frameworks", "cross_framework", "finding_count",
        "target_date", "actions", "closes",
    }
    assert access["topic"] == "Access Control Baseline"
    assert access["frameworks"] == [DPDPA, ISO, NIST]
    assert access["cross_framework"] is True
    assert access["finding_count"] == 3
    assert access["headline"] == f"Addresses 3 findings across {DPDPA}, {ISO} and {NIST}"
    assert access["target_date"] == "2026-11-01"
    assert [a["title"] for a in access["actions"]] == [
        "Access policy missing action 1",
        "Weak access to personal data action 1",
        "Least privilege not enforced action 1",
    ]
    assert access["actions"][0] == {
        "title": "Access policy missing action 1", "owner": "Vikram", "target_date": "2026-11-01",
        "status_label": "Open", "framework_name": ISO, "requirement_id": "ISO.A5.15",
        "finding_title": "Access policy missing",
    }
    assert [(c["framework_id"], c["requirement_id"]) for c in access["closes"]] == [
        ("dpdpa", "CH2.SECURITY.1"), ("iso27001", "ISO.A5.15"), ("nist_csf", "NIST.PR.AA.05"),
    ]
    assert set(access["closes"][0]) == {
        "framework_id", "framework_name", "requirement_id", "requirement_title", "finding_title", "severity",
    }
    policy = result[0]
    assert policy["headline"] == f"Addresses 1 finding in {ISO}"
    assert policy["cross_framework"] is False


def test_scenario_3_ordering_is_deterministic_and_input_order_independent():
    """D-P6-9-F: group key (no target last, earliest target, best severity, more findings, topic, id)."""
    groups = _groups()
    findings = [
        _finding("iso27001", "ISO.A5.1", title="A", severity="medium", targets=[(None, None)]),
        _finding("iso27001", "ISO.A5.4", title="B", severity="medium", targets=[(None, None)]),  # same cluster as A5.1
        _finding("iso27001", "ISO.A5.2", title="C", severity="critical", targets=[(None, None)]),
        _finding("iso27001", "ISO.A5.15", title="D", severity="medium", targets=[(None, None)]),
        _finding("iso27001", "ISO.A5.19", title="E", severity="low", targets=[("X", date(2027, 1, 1))]),
    ]
    first = groups.build_groups(findings, ["iso27001"])
    for seed in range(5):
        shuffled = findings[:]
        random.Random(seed).shuffle(shuffled)
        assert groups.build_groups(shuffled, ["iso27001"]) == first
    # E has the only target date; then no-target groups by severity (C critical), then count (A5.1+A5.4), then topic.
    assert [g["group_id"] for g in first] == ["CLUSTER_010", "CLUSTER_002", "CLUSTER_001", "CLUSTER_006"]
    governance = first[2]
    assert governance["headline"] == f"Addresses 2 findings in {ISO}"
    assert [c["requirement_id"] for c in governance["closes"]] == ["ISO.A5.1", "ISO.A5.4"]
    assert governance["target_date"] is None
    assert groups.build_groups([], ["iso27001"]) == []


def test_scenario_4_document_roadmap_keeps_b1_actions_and_adds_groups(db, http, gate, monkeypatch):
    """D-P6-9-F: `roadmap.actions` keeps the B1 shape (B2 reads it); `roadmap.groups` is added and rendered."""
    board = module("app.services.board_report")
    outcomes = {
        ("dpdpa", "CH2.SECURITY.1"): ("non_compliant", "high"),
        ("iso27001", "ISO.A5.15"): ("non_compliant", "critical"),
        ("nist_csf", "NIST.PR.AA.05"): ("partially_compliant", "medium"),
        ("iso27001", "ISO.A5.1"): ("partially_compliant", "medium"),
    }
    assessment, conclusions = released_assessment(
        db, http, gate, monkeypatch, new_engagement(db),
        frameworks=["dpdpa", "iso27001", "nist_csf"], outcomes=outcomes,
    )
    finding(http, assessment, conclusions[("dpdpa", "CH2.SECURITY.1")], title="Weak access", action="Role-based access", target="2026-12-15")
    finding(http, assessment, conclusions[("iso27001", "ISO.A5.15")], title="No access policy", severity="critical", action="Write access policy", target="2026-11-01")
    finding(http, assessment, conclusions[("nist_csf", "NIST.PR.AA.05")], title="Least privilege gaps", severity="medium", action="Enforce least privilege", target="2027-01-31")
    finding(http, assessment, conclusions[("iso27001", "ISO.A5.1")], title="Policy unapproved", severity="medium", action="Board approves policy", target="2026-10-15")
    approved_report.record_release(db, assessment, actor="consultant:Priya")
    db.commit()
    db.expire_all()

    document = build(db, assessment)
    roadmap = document["roadmap"]
    assert set(roadmap) == {"actions", "unplanned_gap_count", "groups"}
    assert [a["title"] for a in roadmap["actions"]] == [
        "Board approves policy", "Write access policy", "Role-based access", "Enforce least privilege",
    ]
    assert all(len(a["closes"]) == 1 for a in roadmap["actions"])
    assert [g["group_id"] for g in roadmap["groups"]] == ["CLUSTER_001", "CLUSTER_006"]
    access = roadmap["groups"][1]
    assert access["headline"] == f"Addresses 3 findings across {DPDPA}, {ISO} and {NIST}"
    assert [a["title"] for a in access["actions"]] == ["Write access policy", "Role-based access", "Enforce least privilege"]
    grouped = sorted(a["title"] for g in roadmap["groups"] for a in g["actions"])
    assert grouped == sorted(a["title"] for a in roadmap["actions"])  # every action in exactly one group

    html = board.render_html(document, embed_fonts=False)
    section = html[html.index('data-slide="roadmap"'):html.index('data-slide="initiatives"')]
    assert "grouped by shared control" in section
    assert section.count("data-roadmap-group=") == 2
    assert "Access Control Baseline" in section and access["headline"] in section
    for title in grouped:
        assert section.count(title) == 1, title
    assert "Target date" in section and "30 Nov 2026" not in section and "15 Dec 2026" in section


def test_scenario_5_no_actions_keeps_the_empty_state(db, http, gate, monkeypatch):
    board = module("app.services.board_report")
    assessment, _ = released_assessment(
        db, http, gate, monkeypatch, new_engagement(db), frameworks=["iso27001"],
        outcomes={("iso27001", "ISO.A5.1"): ("non_compliant", "high")},
    )
    approved_report.record_release(db, assessment, actor="consultant:Priya")
    db.commit()
    document = build(db, assessment)
    assert document["roadmap"]["groups"] == []
    html = board.render_html(document, embed_fonts=False)
    assert "No remediation actions are recorded for the approved findings yet." in html
