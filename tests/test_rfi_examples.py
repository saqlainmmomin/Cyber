"""Keep the evidence examples aligned with framework and upload vocabularies."""

import pytest

from app.frameworks.registry import FrameworkRegistry
from app.services.document_categories import DPDPA_DOCUMENT_TYPES, LEGACY_UPLOAD_CATEGORIES
from app.services.rfi_examples import DOCUMENT_EXAMPLES


def test_catalogue_covers_every_registered_framework_request():
    from app.main import _register_frameworks

    _register_frameworks()
    assert len(FrameworkRegistry.all_ids()) == 6
    for framework_id in FrameworkRegistry.all_ids():
        missing = {
            request.document_type
            for request in FrameworkRegistry.get(framework_id).evidence_requests
        } - DOCUMENT_EXAMPLES.keys()
        assert not missing, f"Missing {framework_id} evidence examples: {sorted(missing)}"


def test_catalogue_covers_dpdpa_and_legacy_upload_types():
    required = set(DPDPA_DOCUMENT_TYPES) | set(LEGACY_UPLOAD_CATEGORIES) | {"other"}
    assert required <= DOCUMENT_EXAMPLES.keys()


def test_catalogue_covers_all_conditional_dpdpa_requests():
    from app.services.scope_profiler import _build_evidence_checklist

    checklist = _build_evidence_checklist(True, True, True, True, "both")
    assert {item["document_type"] for item in checklist} <= DOCUMENT_EXAMPLES.keys()


@pytest.mark.parametrize("document_type", DOCUMENT_EXAMPLES)
def test_each_example_has_plain_artifacts_and_context(document_type):
    example = DOCUMENT_EXAMPLES[document_type]
    assert set(example) == {"example_artifacts", "good_looks_like"}
    for value in example.values():
        assert isinstance(value, str) and value.strip()
        assert "\u2014" not in value


def test_access_and_firewall_examples_identify_review_records():
    access = DOCUMENT_EXAMPLES["access_control_policy"]["example_artifacts"]
    assert "dated user list per system" in access
    assert "reviewer sign-off and removals" in access
    firewall = DOCUMENT_EXAMPLES["network_security"]["example_artifacts"]
    assert "current firewall rules with change dates" in firewall
