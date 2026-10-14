"""Framework-specific initiative wording and stable section references."""

import pytest

from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
from app.frameworks.registry import FrameworkRegistry
from app.services.scoring import generate_multi_framework_initiatives
from app.services.vocabulary import section_reference, upload_category_label


@pytest.fixture(autouse=True)
def frameworks(monkeypatch):
    definitions = (DPDPA_DEFINITION, ISO27001_DEFINITION, NIST_CSF_DEFINITION)
    monkeypatch.setattr(FrameworkRegistry, "_frameworks", {fw.id: fw for fw in definitions})


def gap(requirement_id, cluster):
    return {
        "requirement_id": requirement_id,
        "root_cause_category": cluster,
        "compliance_status": "non_compliant",
    }


@pytest.mark.parametrize("cluster", ["policy", "people", "process", "technology", "governance"])
def test_iso_initiative_uses_requirement_title_without_privacy_wording(cluster):
    initiative = generate_multi_framework_initiatives({"iso27001": [gap("ISO.A5.1", cluster)]})[0]
    approach = initiative["suggested_approach"]
    assert "Policies for information security" in approach
    assert cluster in approach
    for phrase in ("DPO", "privacy counsel", "DPIA", "consent management"):
        assert phrase not in approach


@pytest.mark.parametrize("cluster, expected", [
    ("policy", "Engage a privacy counsel to draft/update 1 policy documents. Conduct a policy gap review workshop. Publish updated policies to all stakeholders."),
    ("people", "Define DPO/privacy roles and responsibilities. Run a targeted privacy awareness training program covering 1 requirement areas. Conduct role-based training for data handlers."),
    ("process", "Map and document 1 operational processes. Implement process controls, SLAs, and tracking mechanisms. Run a tabletop exercise to validate process coverage."),
    ("technology", "Evaluate and procure/configure tools addressing 1 technical control gaps. Prioritize encryption, consent management, and access control tooling. Run penetration test post-implementation."),
    ("governance", "Establish privacy governance committee. Implement DPIA process and annual audit cadence covering 1 governance requirements. Develop board-level privacy reporting dashboard."),
])
def test_dpdpa_initiative_preserves_exact_approach(cluster, expected):
    initiative = generate_multi_framework_initiatives({"dpdpa": [gap("CH2.CONSENT.1", cluster)]})[0]
    assert initiative["suggested_approach"] == expected


def test_mixed_initiative_keeps_each_framework_member_approach():
    dpdpa = [gap("CH2.CONSENT.1", "policy")]
    iso = [gap("ISO.A5.1", "policy")]
    expected_dpdpa = generate_multi_framework_initiatives({"dpdpa": dpdpa})[0]["suggested_approach"]
    expected_iso = generate_multi_framework_initiatives({"iso27001": iso})[0]["suggested_approach"]
    mixed = generate_multi_framework_initiatives({"iso27001": iso, "dpdpa": dpdpa})
    assert len(mixed) == 1
    assert mixed[0]["suggested_approach"] == f"{expected_dpdpa} {expected_iso}"


@pytest.mark.parametrize("framework_id, requirement_id, reference, prefixed", [
    ("dpdpa", "CH2.CONSENT.1", "Section 6(1), 6(3)", "India DPDPA Section 6(1), 6(3)"),
    ("iso27001", "ISO.A5.1", "Annex A.5.1", "ISO 27001 Annex A.5.1"),
    ("nist_csf", "NIST.GV.OC.01", "GV.OC-01", "NIST CSF GV.OC-01"),
])
def test_section_references_preserve_screen_labels(framework_id, requirement_id, reference, prefixed):
    assert section_reference(framework_id, requirement_id) == reference
    assert section_reference(framework_id, requirement_id, include_framework=True) == prefixed


def test_upload_category_label_uses_registry_and_retains_unknown_stored_values():
    assert upload_category_label("isms_scope") == "ISMS scope statement and boundaries"
    assert upload_category_label("retired_category") == "retired_category"
