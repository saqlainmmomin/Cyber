"""Contract tests for the P6-NIST CSF 2.0 alignment."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import get_db
from app.frameworks import prompts
from app.frameworks.batching import control_batches
from app.frameworks.criteria import nist_csf_draft
from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
from app.frameworks.mappings.clusters import CONTROL_CLUSTERS
from app.frameworks.registry import FrameworkRegistry
from app.main import _register_frameworks, app
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.report import GapItem, GapReport
from app.services import conclusion_review, scoring
from app.services.scope_profiler import compute_scope_multi
from app.config import settings
from scripts import export_criteria_review

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _frameworks():
    _register_frameworks()


def _main_namespace(path: str) -> dict:
    merge_base = subprocess.run(
        ["git", "merge-base", "main", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    source = subprocess.check_output(
        ["git", "show", f"{merge_base}:{path}"], cwd=ROOT, text=True
    )
    namespace = {"__name__": f"_main_{Path(path).stem}"}
    exec(compile(source, path, "exec"), namespace)
    return namespace


def _controls(framework=NIST_CSF_DEFINITION):
    return {control.id: control for control in framework.all_controls()}


NEW_CONTROLS = {
    "NIST.GV.RM.05": ("Risk communication lines", "Defined channels exist across the organization for raising and escalating cybersecurity risk, including risk that originates with suppliers and other third parties.", "medium", ["governance", "risk-communication", "escalation", "third-party"], "GV.RM-05"),
    "NIST.GV.RM.06": ("Standardized risk method", "Cybersecurity risks are calculated, recorded, categorized and prioritized using one documented method that is shared across the organization.", "high", ["governance", "risk-methodology", "risk-scoring", "prioritization"], "GV.RM-06"),
    "NIST.GV.RM.07": ("Positive risk consideration", "Opportunities (positive risks) are described and brought into the organization's cybersecurity risk discussions alongside threats.", "low", ["governance", "risk-management", "opportunities"], "GV.RM-07"),
    "NIST.GV.SC.06": ("Supplier pre-engagement due diligence", "Before a formal relationship with a supplier or other third party begins, the organization plans for it and performs due diligence to reduce the associated risk.", "high", ["supply-chain", "due-diligence", "onboarding", "third-party"], "GV.SC-06"),
    "NIST.GV.SC.07": ("Supplier risk management over the relationship", "Risks from each supplier, its products and services, and other third parties are identified, recorded, prioritized, assessed, treated and monitored for as long as the relationship lasts.", "high", ["supply-chain", "third-party", "supplier-monitoring", "risk-assessment"], "GV.SC-07"),
    "NIST.GV.SC.08": ("Suppliers in incident planning and recovery", "Relevant suppliers and other third parties take part in the organization's incident planning, response and recovery activities.", "medium", ["supply-chain", "incident-response", "recovery", "third-party"], "GV.SC-08"),
    "NIST.GV.SC.09": ("Supply chain security across the life cycle", "Supply chain security practices form part of the cybersecurity and enterprise risk programs, and how well they perform is monitored across the life cycle of technology products and services.", "medium", ["supply-chain", "lifecycle-management", "performance-monitoring"], "GV.SC-09"),
    "NIST.GV.SC.10": ("Supplier exit provisions", "Supply chain risk management plans cover what must happen when a partnership or service agreement ends.", "medium", ["supply-chain", "offboarding", "contracts", "termination"], "GV.SC-10"),
    "NIST.ID.RA.07": ("Change and exception management", "Changes and exceptions are controlled, evaluated for their effect on risk, recorded and tracked to closure.", "high", ["risk-assessment", "change-management", "exceptions", "risk-acceptance"], "ID.RA-07"),
    "NIST.ID.RA.08": ("Vulnerability disclosure handling", "Established processes exist to receive, analyze and respond to vulnerabilities reported to the organization.", "medium", ["risk-assessment", "vulnerability-disclosure", "vulnerability-management"], "ID.RA-08"),
    "NIST.ID.RA.09": ("Hardware and software integrity verification", "Hardware and software are checked for authenticity and integrity before they are acquired and put into use.", "medium", ["risk-assessment", "integrity", "authenticity", "acquisition"], "ID.RA-09"),
    "NIST.ID.RA.10": ("Critical supplier pre-acquisition assessment", "Suppliers judged critical are assessed before their products or services are acquired.", "high", ["risk-assessment", "supply-chain", "critical-suppliers", "acquisition"], "ID.RA-10"),
    "NIST.ID.IM.04": ("Incident response and operational cyber plans", "Incident response plans and other cybersecurity plans that affect operations exist and are communicated, kept current and improved.", "critical", ["improvement", "incident-response-plan", "planning", "business-continuity"], "ID.IM-04"),
}


CHANGED_FIELDS = {
    "NIST.GV.OC.02": {"description": "Internal and external stakeholders are understood, and their needs and expectations about cybersecurity risk management are understood and taken into account."},
    "NIST.GV.OC.04": {"description": "Critical objectives, capabilities and services that external stakeholders rely on or expect from the organization are understood and communicated."},
    "NIST.GV.OC.05": {"title": "Organizational dependencies", "description": "The outcomes, capabilities and services that the organization itself relies on are understood and communicated."},
    "NIST.GV.RR.01": {"description": "Leaders own and answer for cybersecurity risk, and build a culture that is risk-aware, ethical and committed to continual improvement."},
    "NIST.GV.OV.02": {"title": "Risk strategy coverage review", "tags": ["governance", "oversight", "strategy-review"]},
    "NIST.GV.OV.03": {"title": "Risk management performance evaluation", "description": "The performance of organizational cybersecurity risk management is evaluated and reviewed to identify adjustments that are needed.", "tags": ["governance", "oversight", "performance-measurement"]},
    "NIST.GV.SC.02": {"title": "Supply chain roles and responsibilities"},
    "NIST.GV.SC.04": {"title": "Supplier criticality prioritization"},
    "NIST.ID.AM.08": {"title": "Asset life-cycle management"},
    "NIST.PR.AT.02": {"title": "Specialized role training"},
    "NIST.PR.IR.02": {"title": "Environmental threat protection"},
    "NIST.PR.PS.01": {"description": "Configuration management practices are defined and applied across the organization's hardware, software and platforms."},
    "NIST.DE.AE.02": {"title": "Adverse event analysis", "tags": ["detection", "event-analysis", "siem"]},
    "NIST.DE.AE.03": {"title": "Event correlation", "tags": ["detection", "correlation", "log-correlation"]},
    "NIST.DE.AE.06": {"title": "Adverse event information distribution", "tags": ["detection", "alerting", "information-distribution"]},
    "NIST.DE.AE.08": {"title": "Incident declaration", "tags": ["detection", "incident-declaration", "incident-criteria", "thresholds"]},
    "NIST.RS.MA.02": {"title": "Incident triage and validation"},
    "NIST.RS.MA.05": {"title": "Recovery initiation criteria"},
    "NIST.RS.AN.07": {"title": "Incident data collection and preservation"},
    "NIST.RS.CO.02": {"title": "Stakeholder incident notification"},
    "NIST.RC.RP.03": {"title": "Restoration asset integrity verification"},
}


def test_pack_shape_content_and_weights():
    expected_sections = {
        "gv_oc": ["OC.01", "OC.02", "OC.03", "OC.04", "OC.05"],
        "gv_rm": ["RM.01", "RM.02", "RM.03", "RM.04", "RM.05", "RM.06", "RM.07"],
        "gv_rr": ["RR.01", "RR.02", "RR.03", "RR.04"],
        "gv_po": ["PO.01", "PO.02"],
        "gv_ov": ["OV.01", "OV.02", "OV.03"],
        "gv_sc": [f"SC.{index:02d}" for index in range(1, 11)],
        "id_am": ["AM.01", "AM.02", "AM.03", "AM.04", "AM.05", "AM.07", "AM.08"],
        "id_ra": [f"RA.{index:02d}" for index in range(1, 11)],
        "id_im": ["IM.01", "IM.02", "IM.03", "IM.04"],
        "pr_aa": [f"AA.{index:02d}" for index in range(1, 7)],
        "pr_at": ["AT.01", "AT.02"],
        "pr_ds": ["DS.01", "DS.02", "DS.10", "DS.11"],
        "pr_ps": [f"PS.{index:02d}" for index in range(1, 7)],
        "pr_ir": [f"IR.{index:02d}" for index in range(1, 5)],
        "de_cm": ["CM.01", "CM.02", "CM.03", "CM.06", "CM.09"],
        "de_ae": ["AE.02", "AE.03", "AE.04", "AE.06", "AE.07", "AE.08"],
        "rs_ma": [f"MA.{index:02d}" for index in range(1, 6)],
        "rs_an": ["AN.03", "AN.06", "AN.07", "AN.08"],
        "rs_co": ["CO.02", "CO.03"],
        "rs_mi": ["MI.01", "MI.02"],
        "rc_rp": [f"RP.{index:02d}" for index in range(1, 7)],
        "rc_co": ["CO.03", "CO.04"],
    }
    assert NIST_CSF_DEFINITION.control_count() == 106
    for domain in NIST_CSF_DEFINITION.domains.values():
        for section_key, section in domain.sections.items():
            assert [control.reference.split("-")[0].split(".")[-1] + "." + control.reference.split("-")[-1] for control in section.controls] == expected_sections[section_key]
    assert [sum(len(section.controls) for section in domain.sections.values()) for domain in NIST_CSF_DEFINITION.domains.values()] == [31, 21, 22, 11, 13, 8]
    assert NIST_CSF_DEFINITION.get_control("NIST.RS.CO.04") is None
    controls = NIST_CSF_DEFINITION.all_controls()
    assert len({control.id for control in controls}) == 106
    for control in controls:
        _, function, category, number = control.id.split(".")
        assert control.reference == f"{function}.{category}-{number}"
    assert "106" in __import__("app.frameworks.definitions.nist_csf", fromlist=["__doc__"]).__doc__
    assert "82 subcategory" not in __import__("app.frameworks.definitions.nist_csf", fromlist=["__doc__"]).__doc__

    main = _main_namespace("app/frameworks/definitions/nist_csf.py")["NIST_CSF_DEFINITION"]
    current = _controls()
    original = _controls(main)
    for control_id, expected in NEW_CONTROLS.items():
        control = current[control_id]
        assert (control.title, control.description, control.criticality, control.tags, control.reference) == expected
    for control_id, changes in CHANGED_FIELDS.items():
        for field, expected in changes.items():
            assert getattr(current[control_id], field) == expected
        for field in ("id", "title", "description", "reference", "criticality", "tags", "test_criteria"):
            if field not in changes:
                assert getattr(current[control_id], field) == getattr(original[control_id], field)
    for control_id, control in current.items():
        if control_id not in NEW_CONTROLS and control_id not in CHANGED_FIELDS:
            assert control == original[control_id]
    for domain_key, domain in NIST_CSF_DEFINITION.domains.items():
        assert domain.weight == main.domains[domain_key].weight
        for section_key, section in domain.sections.items():
            assert section.weight == main.domains[domain_key].sections[section_key].weight


def test_questions_are_generated_from_aligned_controls():
    questions = NIST_CSF_DEFINITION.questions
    assert set(questions) == {control.id for control in NIST_CSF_DEFINITION.all_controls()}
    assert questions["NIST.DE.AE.08"].question == "Has your organization implemented incident declaration? (DE.AE-08)"
    assert questions["NIST.GV.SC.10"].question == "Has your organization implemented supplier exit provisions? (GV.SC-10)"
    assert all("RS.CO-04" not in f"{question.question} {question.guidance}" for question in questions.values())


EXPECTED_CLUSTER_DELTAS = {
    "NIST.GV.RM.05": ("CLUSTER_035", "NIST also expects defined lines of communication for cybersecurity risk, including risk from suppliers and other third parties."),
    "NIST.GV.RM.06": ("CLUSTER_035", "NIST expects one standard method for calculating, recording, categorizing and prioritizing cybersecurity risk."),
    "NIST.GV.RM.07": ("CLUSTER_035", "NIST also expects opportunities (positive risks) to be described and included in risk discussions."),
    "NIST.GV.SC.06": ("CLUSTER_010", "NIST expects planning and due diligence before a supplier or third-party relationship is formalized."),
    "NIST.ID.RA.10": ("CLUSTER_010", "NIST expects critical suppliers to be assessed before their products or services are acquired."),
    "NIST.GV.SC.10": ("CLUSTER_011", "NIST expects supply chain plans to cover obligations that continue after an agreement ends."),
    "NIST.GV.SC.08": ("CLUSTER_012", "NIST expects relevant suppliers to take part in incident planning, response and recovery."),
    "NIST.GV.SC.09": ("CLUSTER_012", "NIST also expects supply chain security practices to be monitored across the product and service life cycle."),
    "NIST.ID.RA.09": ("CLUSTER_012", "NIST expects hardware and software to be checked for authenticity and integrity before acquisition and use."),
    "NIST.GV.SC.07": ("CLUSTER_013", "NIST expects supplier risk to be assessed, treated and monitored for the whole relationship."),
    "NIST.ID.IM.04": ("CLUSTER_014", "NIST expects incident response and other operational cybersecurity plans to be established, communicated, maintained and improved."),
    "NIST.ID.RA.08": ("CLUSTER_043", "NIST expects a process to receive, analyze and respond to vulnerability disclosures."),
    "NIST.ID.RA.07": ("CLUSTER_044", "NIST expects changes and exceptions to be assessed for risk impact, recorded and tracked."),
    "NIST.PR.AA.06": ("CLUSTER_045", "NIST expects physical access to assets to be managed, monitored and enforced according to risk."),
    "NIST.PR.IR.02": ("CLUSTER_045", "NIST expects technology assets to be protected from environmental threats."),
    "NIST.PR.IR.03": ("CLUSTER_019", "NIST expects mechanisms that meet resilience requirements in both normal and adverse conditions."),
    "NIST.GV.SC.02": ("CLUSTER_011", "NIST expects cybersecurity roles and responsibilities for suppliers, customers and partners to be set, communicated and coordinated."),
    "NIST.GV.SC.04": ("CLUSTER_010", "NIST also expects suppliers to be known and prioritized by criticality."),
    "NIST.RS.MA.02": ("CLUSTER_015", "NIST expects incident reports to be triaged and validated."),
    "NIST.RS.MA.05": ("CLUSTER_015", "NIST expects defined criteria for starting incident recovery to be applied."),
    "NIST.DE.AE.06": ("CLUSTER_015", "NIST expects information on adverse events to reach authorized staff and tools."),
    "NIST.ID.IM.01": ("CLUSTER_016", "NIST expects improvements to be identified from evaluations such as assessments and audits."),
    "NIST.ID.IM.03": ("CLUSTER_016", "NIST expects improvements to be identified from running day-to-day processes and activities."),
    "NIST.RS.CO.02": ("CLUSTER_017", "NIST expects internal and external stakeholders to be notified of incidents."),
    "NIST.RS.CO.03": ("CLUSTER_017", "NIST also expects information to be shared with designated internal and external stakeholders."),
    "NIST.RC.RP.03": ("CLUSTER_019", "NIST expects backups and other restoration assets to be checked for integrity before they are used."),
    "NIST.ID.AM.07": ("CLUSTER_034", "NIST expects inventories of data and related metadata to be maintained for designated data types."),
    "NIST.ID.RA.04": ("CLUSTER_035", "NIST expects potential impacts and likelihoods of threats exploiting vulnerabilities to be identified and recorded."),
    "NIST.GV.RM.03": ("CLUSTER_035", "NIST expects cybersecurity risk management to be part of enterprise risk management."),
    "NIST.PR.PS.01": ("CLUSTER_038", "NIST expects configuration management practices to be established and applied."),
    "NIST.PR.PS.02": ("CLUSTER_038", "NIST expects software to be maintained, replaced and removed according to risk."),
    "NIST.PR.PS.03": ("CLUSTER_038", "NIST expects hardware to be maintained, replaced and removed according to risk."),
    "NIST.PR.PS.05": ("CLUSTER_038", "NIST expects installation and execution of unauthorized software to be prevented."),
    "NIST.DE.AE.08": ("CLUSTER_046", "NIST expects incidents to be declared when adverse events meet defined incident criteria."),
    "NIST.GV.OC.05": ("CLUSTER_051", "NIST expects the outcomes, capabilities and services the organization depends on to be understood and communicated."),
    "NIST.GV.OV.02": ("CLUSTER_051", "NIST expects the risk strategy to be reviewed and adjusted so it covers organizational requirements and risks."),
    "NIST.GV.OV.03": ("CLUSTER_051", "NIST expects risk management performance to be evaluated and reviewed for needed adjustments."),
    "NIST.RC.CO.03": ("CLUSTER_047", "NIST expects recovery progress to be communicated to designated internal and external stakeholders."),
    "NIST.RS.AN.07": ("CLUSTER_016", "NIST expects incident data and metadata to be collected with their integrity and provenance preserved."),
}


def test_clusters_are_complete_and_nist_only_changes_are_exact():
    current_by_id = {}
    for cluster in CONTROL_CLUSTERS:
        for member in cluster["controls"]:
            if member["framework"] == "nist_csf":
                current_by_id.setdefault(member["control"], []).append((cluster["cluster_id"], member.get("delta")))
    assert set(current_by_id) == {control.id for control in NIST_CSF_DEFINITION.all_controls()}
    assert all(len(matches) == 1 for matches in current_by_id.values())
    assert "NIST.RS.CO.04" not in current_by_id
    for control_id, expected in EXPECTED_CLUSTER_DELTAS.items():
        assert current_by_id[control_id] == [expected]
    assert sum(member["framework"] == "nist_csf" for member in next(c for c in CONTROL_CLUSTERS if c["cluster_id"] == "CLUSTER_001")["controls"]) == 6

    main_clusters = _main_namespace("app/frameworks/mappings/clusters.py")["CONTROL_CLUSTERS"]
    main_by_id = {cluster["cluster_id"]: cluster for cluster in main_clusters}
    for cluster in CONTROL_CLUSTERS:
        old = main_by_id[cluster["cluster_id"]]
        assert {key: value for key, value in cluster.items() if key != "controls"} == {key: value for key, value in old.items() if key != "controls"}
        current_non_nist = [member for member in cluster["controls"] if member["framework"] != "nist_csf"]
        old_non_nist = [member for member in old["controls"] if member["framework"] != "nist_csf"]
        assert current_non_nist == old_non_nist


# Snapshot of the nine D-NIST-G changes (label, reason, required, maps_to), verified against the handoff in review.
EXPECTED_CHANGED_EVIDENCE = {
    'risk_management_strategy': ('Cybersecurity risk management strategy, including risk appetite and tolerance statements', 'Evidence for organisational context (GV.OC-01, GV.OC-04, GV.OC-05) and risk management strategy, risk communication and opportunity handling (GV.RM-01 to GV.RM-05, GV.RM-07).', True, ('NIST.GV.OC.01', 'NIST.GV.OC.04', 'NIST.GV.OC.05', 'NIST.GV.RM.01', 'NIST.GV.RM.02', 'NIST.GV.RM.03', 'NIST.GV.RM.04', 'NIST.GV.RM.05', 'NIST.GV.RM.07')),
    'supplier_security': ('Supplier security policy, supplier register and sample supplier agreements', 'Evidence for supply chain risk management across the supplier life cycle (GV.SC-01 to GV.SC-10), critical-supplier assessment before acquisition (ID.RA-10), external service inventory (ID.AM-04) and provider monitoring (DE.CM-06).', True, ('NIST.GV.SC.01', 'NIST.GV.SC.02', 'NIST.GV.SC.03', 'NIST.GV.SC.04', 'NIST.GV.SC.05', 'NIST.GV.SC.06', 'NIST.GV.SC.07', 'NIST.GV.SC.08', 'NIST.GV.SC.09', 'NIST.GV.SC.10', 'NIST.ID.RA.10', 'NIST.ID.AM.04', 'NIST.DE.CM.06')),
    'risk_assessment': ('Cybersecurity risk assessment and risk register', "Evidence for threat identification, impact and likelihood, risk determination and response (ID.RA-03 to ID.RA-06) and the organisation's standard risk method (GV.RM-06).", True, ('NIST.ID.RA.03', 'NIST.ID.RA.04', 'NIST.ID.RA.05', 'NIST.ID.RA.06', 'NIST.GV.RM.06')),
    'vulnerability_management': ('Vulnerability and patch management procedure, with recent scan reports', 'Evidence for vulnerability identification (ID.RA-01), threat intelligence (ID.RA-02), vulnerability disclosure handling (ID.RA-08) and software maintenance (PR.PS-02).', True, ('NIST.ID.RA.01', 'NIST.ID.RA.02', 'NIST.ID.RA.08', 'NIST.PR.PS.02')),
    'configuration_baselines': ('Secure configuration / hardening baselines, software execution controls and integrity checks for acquired hardware and software', 'Evidence for configuration management, hardware maintenance and execution prevention (PR.PS-01, PR.PS-03, PR.PS-05) and authenticity and integrity checks before hardware and software are used (ID.RA-09).', False, ('NIST.PR.PS.01', 'NIST.PR.PS.03', 'NIST.PR.PS.05', 'NIST.ID.RA.09')),
    'change_management': ('Change management procedure, sample change records and the exception (risk acceptance) register', 'Evidence for change and exception management (ID.RA-07).', False, ('NIST.ID.RA.07',)),
    'logging_monitoring': ('Logging and monitoring standard, with evidence of alert review or SIEM use', 'Evidence for log generation (PR.PS-04), continuous monitoring (DE.CM-01, DE.CM-03, DE.CM-09) and adverse event analysis, correlation, distribution and threat context (DE.AE-02, DE.AE-03, DE.AE-06, DE.AE-07).', True, ('NIST.PR.PS.04', 'NIST.DE.CM.01', 'NIST.DE.CM.03', 'NIST.DE.CM.09', 'NIST.DE.AE.02', 'NIST.DE.AE.03', 'NIST.DE.AE.06', 'NIST.DE.AE.07')),
    'breach_procedure': ('Incident response plan and escalation procedures', 'Evidence for the incident response plan (ID.IM-04), incident management, containment, eradication and stakeholder communication (RS.MA-01 to RS.MA-05, RS.MI-01, RS.MI-02, RS.CO-02, RS.CO-03) and incident impact and declaration (DE.AE-04, DE.AE-08).', True, ('NIST.ID.IM.04', 'NIST.RS.MA.01', 'NIST.RS.MA.02', 'NIST.RS.MA.03', 'NIST.RS.MA.04', 'NIST.RS.MA.05', 'NIST.RS.MI.01', 'NIST.RS.MI.02', 'NIST.RS.CO.02', 'NIST.RS.CO.03', 'NIST.DE.AE.04', 'NIST.DE.AE.08')),
    'business_continuity': ('Recovery and business continuity plans, with latest test results', 'Evidence for recovery plan execution and communication (RC.RP-01, RC.RP-02, RC.RP-04 to RC.RP-06, RC.CO-03, RC.CO-04) and resilience mechanisms and capacity (PR.IR-03, PR.IR-04).', True, ('NIST.RC.RP.01', 'NIST.RC.RP.02', 'NIST.RC.RP.04', 'NIST.RC.RP.05', 'NIST.RC.RP.06', 'NIST.RC.CO.03', 'NIST.RC.CO.04', 'NIST.PR.IR.03', 'NIST.PR.IR.04')),
}


def test_evidence_requests_cover_every_control_and_merge_change_management():
    expected_types = [
        "csf_profiles", "risk_management_strategy", "security_policy", "roles_responsibilities", "hr_security", "leadership_oversight", "legal_register", "supplier_security", "asset_inventory", "risk_assessment", "vulnerability_management", "access_control_policy", "physical_security", "training_records", "cryptography_policy", "backup", "configuration_baselines", "change_management", "sdlc_policy", "logging_monitoring", "network_security", "breach_procedure", "incident_log", "business_continuity", "exercise_records",
    ]
    requests = NIST_CSF_DEFINITION.evidence_requests
    assert [request.document_type for request in requests] == expected_types
    assert len({control_id for request in requests for control_id in request.maps_to}) == 106
    assert {control_id for request in requests for control_id in request.maps_to} == {control.id for control in NIST_CSF_DEFINITION.all_controls()}
    request_map = {request.document_type: request for request in requests}
    main_requests = {
        request.document_type: request
        for request in _main_namespace("app/frameworks/definitions/nist_csf.py")["NIST_CSF_DEFINITION"].evidence_requests
    }
    for document_type, request in request_map.items():
        if document_type in EXPECTED_CHANGED_EVIDENCE:
            assert (request.label, request.reason, request.required, tuple(request.maps_to)) == EXPECTED_CHANGED_EVIDENCE[document_type], document_type
        else:
            assert request == main_requests[document_type], document_type
    assert request_map["change_management"].required is False
    assert request_map["change_management"].maps_to == ("NIST.ID.RA.07",)
    assert request_map["configuration_baselines"].label == "Secure configuration / hardening baselines, software execution controls and integrity checks for acquired hardware and software"
    assert request_map["logging_monitoring"].maps_to[-2:] == ("NIST.DE.AE.06", "NIST.DE.AE.07")
    assert request_map["breach_procedure"].maps_to[0] == "NIST.ID.IM.04"
    merged = compute_scope_multi({}, ["iso27001", "nist_csf"])
    change_items = [item for item in merged["evidence_checklist"] if item["document_type"] == "change_management"]
    assert len(change_items) == 1
    assert change_items[0]["frameworks"] == ["iso27001", "nist_csf"]
    assert change_items[0]["maps_to"] == ["ISO.A8.32", "ISO.A8.19", "NIST.ID.RA.07"]


def test_batches_and_prompts_match_the_aligned_pack():
    expected = [
        ("govern", ("gv_oc", "gv_rm", "gv_rr", "gv_po", "gv_ov"), 21, "NIST.GV.OC.01", "NIST.GV.OV.03"),
        ("govern", ("gv_sc",), 10, "NIST.GV.SC.01", "NIST.GV.SC.10"),
        ("identify", ("id_am", "id_ra", "id_im"), 21, "NIST.ID.AM.01", "NIST.ID.IM.04"),
        ("protect", ("pr_aa", "pr_at", "pr_ds", "pr_ps", "pr_ir"), 22, "NIST.PR.AA.01", "NIST.PR.IR.04"),
        ("detect", ("de_cm", "de_ae"), 11, "NIST.DE.CM.01", "NIST.DE.AE.08"),
        ("respond", ("rs_ma", "rs_an", "rs_co", "rs_mi"), 13, "NIST.RS.MA.01", "NIST.RS.MI.02"),
        ("recover", ("rc_rp", "rc_co"), 8, "NIST.RC.RP.01", "NIST.RC.CO.04"),
    ]
    batches = control_batches("nist_csf")
    assert [(b.domain_key, b.section_keys, len(b.control_ids), b.control_ids[0], b.control_ids[-1]) for b in batches] == expected
    assert [b.label for b in batches] == [f"{index}/7" for index in range(1, 8)]
    assert control_batches("dpdpa") == ()
    assert len(control_batches("iso27001")) == 6

    digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    prompt_kwargs = dict(
        company_name="Acme",
        industry="saas",
        company_size="sme",
        description="d",
        responses=[{"question_id": "SINGLE.ISO.A5.1", "answer": "yes"}],
        documents=[{"filename": "a.pdf", "category": "other", "text": "t"}],
        context_profile={"risk_tier": "HIGH", "industry_context": "x"},
        evidence={"ISO.A5.1": ["q"], "NIST.GV.OC.01": ["q"], "CH2.CONSENT.1": ["q"]},
        desk_review_summary={"coverage_summary": {"ISO.A5.1": "partial"}, "signal_flags": []},
        applicable_controls=None,
    )
    assert digest(prompts.build_framework_system_prompt("dpdpa")) == "3fc4f1c3ff6b62124716f6ca5ef29e1dd39461817d168fa4b047c2bef92e4ea6"
    assert digest(prompts.build_framework_user_prompt("dpdpa", **prompt_kwargs)) == "de658c512943c954425ea004165af0dd1cd88ade82f7376ac98d08aa957b3751"
    assert digest(prompts.build_framework_system_prompt("iso27001")) == "3c3bad7bd8818c1d5b28730e4462bbf91f2208b1eae32b89459e8e2d698116b3"
    assert digest(prompts.build_framework_user_prompt("iso27001", **prompt_kwargs)) == "6fe08745ef96857b893c623d0f468d2abca2aa6c3395affc64145807acedfd61"
    assert digest(prompts.build_framework_desk_review_system_prompt("iso27001")) == "9d2e926bae35b23030085da6e528b03df63c9352006cb0bb8948800a251222b2"
    nist_system = json.dumps(prompts.build_framework_system_prompt("nist_csf"))
    nist_desk = json.dumps(prompts.build_framework_desk_review_system_prompt("nist_csf"))
    assert "(106 total)" in nist_system
    assert "**NIST.ID.IM.04**" in nist_system
    assert "NIST.RS.CO.04" not in nist_system
    assert "Include ALL 106 control IDs" in nist_desk


def test_dependencies_and_criteria_pending_rule():
    ids = {control.id for control in NIST_CSF_DEFINITION.all_controls()}
    assert all(key in ids and set(values) <= ids for key, values in NIST_CSF_DEFINITION.dependencies.items())
    assert NIST_CSF_DEFINITION.dependencies["NIST.GV.RM.06"] == ["NIST.GV.RM.01"]
    assert NIST_CSF_DEFINITION.dependencies["NIST.GV.SC.06"] == ["NIST.GV.SC.01"]
    assert NIST_CSF_DEFINITION.dependencies["NIST.GV.SC.07"] == ["NIST.GV.SC.04"]
    assert NIST_CSF_DEFINITION.dependencies["NIST.GV.SC.10"] == ["NIST.GV.SC.05"]
    assert NIST_CSF_DEFINITION.dependencies["NIST.ID.RA.10"] == ["NIST.GV.SC.04"]
    assert NIST_CSF_DEFINITION.dependencies["NIST.RS.MA.01"] == ["NIST.DE.AE.08", "NIST.ID.IM.04"]
    assert {"NIST.ID.IM.04", "NIST.ID.RA.07"} <= set(NIST_CSF_DEFINITION.root_cause_clusters["process"]["typical_requirements"])

    pending = nist_csf_draft.CRITERIA_PENDING_IDS
    new_ids = frozenset(NEW_CONTROLS)
    # P6-2d drafted the 13 pending ids and emptied CRITERIA_PENDING_IDS.
    assert pending == frozenset()
    main = _main_namespace("app/frameworks/criteria/nist_csf_draft.py")
    main_draft = main["NIST_CSF_CRITERIA_DRAFT"]
    assert set(main_draft) - set(nist_csf_draft.NIST_CSF_CRITERIA_DRAFT) == set()
    assert set(nist_csf_draft.NIST_CSF_CRITERIA_DRAFT) - set(main_draft) <= new_ids
    for requirement_id, criteria in nist_csf_draft.NIST_CSF_CRITERIA_DRAFT.items():
        if requirement_id in new_ids:
            continue  # not present on main; drafted fresh by P6-2d
        assert [(c.statement, c.evidence_hint, c.source_basis, c.kind) for c in criteria] == [(c.statement, c.evidence_hint, c.source_basis, c.kind) for c in main_draft[requirement_id]]
        for criterion in criteria:
            assert nist_csf_draft.NIST_CSF_CRITERIA_REVIEW_META[criterion.id] == main["NIST_CSF_CRITERIA_REVIEW_META"][criterion.id]
    # The 13 new ids now have their own 2-5 drafted criteria, at least one design.
    all_ids = {control.id for control in NIST_CSF_DEFINITION.all_controls()}
    assert new_ids <= all_ids
    for requirement_id in new_ids:
        criteria = nist_csf_draft.NIST_CSF_CRITERIA_DRAFT[requirement_id]
        assert 2 <= len(criteria) <= 5, requirement_id
        assert any(c.kind == "design" for c in criteria), requirement_id
        for criterion in criteria:
            assert nist_csf_draft.NIST_CSF_CRITERIA_REVIEW_META[criterion.id][0] in {"high", "medium", "low"}
    # All 106 pack ids now have drafted criteria, and export covers exactly them.
    assert set(nist_csf_draft.NIST_CSF_CRITERIA_DRAFT) == all_ids
    rows = export_criteria_review.build_rows(framework="nist_csf")
    assert {row["requirement_id"] for row in rows} == all_ids
    assert not {row["requirement_id"] for row in rows} & {"NIST.RS.CO.04"}
    # A pack id genuinely missing from the draft still raises KeyError.
    with pytest.raises(KeyError):
        with pytest.MonkeyPatch.context() as monkeypatch:
            trimmed_draft = dict(nist_csf_draft.NIST_CSF_CRITERIA_DRAFT)
            del trimmed_draft["NIST.GV.OC.01"]
            monkeypatch.setattr(nist_csf_draft, "NIST_CSF_CRITERIA_DRAFT", trimmed_draft)
            export_criteria_review.build_rows(framework="nist_csf")


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


@pytest.fixture()
def legacy_environment(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy-nist.sqlite3"
    command.upgrade(_alembic_config(db_path), "head")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    db = sessionmaker(bind=engine)()
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as http:
            yield db, http
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_removed_control_remains_readable_in_legacy_rows(legacy_environment):
    db, http = legacy_environment
    client = Client(name="Legacy NIST", industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name="Legacy engagement", status="active")
    db.add(engagement)
    db.flush()
    main_ids = [control.id for control in _controls(_main_namespace("app/frameworks/definitions/nist_csf.py")["NIST_CSF_DEFINITION"]).values()]
    assessment = Assessment(company_name="Legacy NIST", industry="Technology", company_size="medium", selected_frameworks=json.dumps(["nist_csf"]), engagement_id=engagement.id, applicable_requirements=json.dumps(main_ids))
    db.add(assessment)
    db.flush()
    report = GapReport(assessment_id=assessment.id, overall_score=0.0, chapter_scores="{}", framework_scores="{}", executive_summary="legacy", raw_ai_response="{}")
    db.add(report)
    db.flush()
    for requirement_id, framework_id, chapter in (("NIST.RS.CO.04", "nist_csf", "respond"), ("NIST.GV.PO.01", "nist_csf", "govern")):
        db.add(GapItem(report_id=report.id, requirement_id=requirement_id, framework_id=framework_id, chapter=chapter, requirement_title="legacy title", compliance_status="partially_compliant", current_state="legacy state", gap_description="legacy gap", risk_level="medium", remediation_action="legacy action", remediation_priority=2, remediation_effort="medium", timeline_weeks=4, maturity_level=2, root_cause_category="process", evidence_quote="legacy quote"))
        conclusion = Conclusion(assessment_id=assessment.id, framework_id=framework_id, requirement_id=requirement_id, outcome="insufficient_evidence", rationale="legacy rationale", evidence_summary="legacy evidence", gaps_identified="legacy gap", risk_level="medium", recommended_action="legacy action", ai_proposed=True, version=1)
        db.add(conclusion)
        db.flush()
        db.add(ConclusionRevision(conclusion_id=conclusion.id, actor="system:analysis", action="proposed", citations_json="[]"))
    db.commit()

    assert http.get(f"/assessments/{assessment.id}/conclusions").status_code == 200
    assert http.get(f"/assessments/{assessment.id}/workpaper").status_code == 200
    cards = conclusion_review.conclusion_cards(db, assessment.id)
    assert any(card.conclusion.requirement_id == "NIST.RS.CO.04" for card in cards)
    result = scoring.score(assessment.id, ["nist_csf"], _session=db)
    assert result.per_framework["nist_csf"].control_count == 106


def test_protected_surface_guard_uses_three_dot_diff():
    # P6-1d excludes: reasoning-off request prefs (llm_client, config comment) and
    # registry evidence extraction alongside desk-review reuse (claude_analyzer).
    result = subprocess.run(
        ["git", "diff", "--stat", "main...HEAD", "--", "app/dpdpa", "tests/fixtures", "tests/support", "app/frameworks/schema.py", "app/frameworks/prompts.py", "app/frameworks/batching.py", "app/frameworks/compat.py", "app/frameworks/registry.py", "app/services", "app/routers", "app/models", "alembic", "app/config.py", ":(exclude)app/config.py", ":(exclude)app/services/claude_analyzer.py", ":(exclude)app/services/llm_client.py", "app/frameworks/definitions", ":(exclude)app/frameworks/definitions/nist_csf.py", "app/frameworks/criteria/dpdpa_draft.py", "app/frameworks/criteria/iso27001_draft.py", "tasks/criteria-review/dpdpa-criteria-v1.csv", "tasks/criteria-review/iso27001-criteria-v1.csv", "tasks/criteria-review/iso27001-descriptions-v1.csv"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert result.stdout == ""
