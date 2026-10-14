"""Uploads use the selected frameworks without changing the judge vocabulary."""

import pytest

from app.frameworks.registry import FrameworkRegistry
from app.services.document_categories import (
    LEGACY_UPLOAD_CATEGORIES,
    document_categories,
    upload_categories,
)
from tests.yozora_support import (  # noqa: F401
    _register_frameworks, db, db_path, engine, http, upload_root, seed_engagement,
)


def test_dpdpa_preserves_legacy_categories_and_framework_types():
    categories = upload_categories(["dpdpa"])
    assert categories == document_categories(["dpdpa"])
    assert categories[:len(LEGACY_UPLOAD_CATEGORIES) - 1] == LEGACY_UPLOAD_CATEGORIES[:-1]
    assert "grievance_mechanism" in categories
    assert categories[-1] == "other"


def test_iso_has_its_own_categories_only():
    expected = tuple(dict.fromkeys(
        request.document_type for request in FrameworkRegistry.get("iso27001").evidence_requests
    )) + ("other",)
    assert upload_categories(["iso27001"]) == expected
    assert "privacy_policy" in expected  # ISO A.5.34 requests this explicitly.
    assert "consent_form" not in expected


def test_mixed_scope_combines_categories_without_duplicates():
    categories = upload_categories(["dpdpa", "iso27001"])
    assert set(categories) == set(upload_categories(["dpdpa"])) | set(upload_categories(["iso27001"]))
    assert len(categories) == len(set(categories))
    assert categories[-1] == "other"


@pytest.mark.parametrize("path", ["/api/assessments/{id}/documents", "/assessments/{id}/upload"])
def test_upload_rejects_out_of_scope_category_before_ingest(db, http, monkeypatch, path):
    from app.services import evidence

    _, _, assessment = seed_engagement(db, frameworks=("iso27001",))

    def unexpected_ingest(*args, **kwargs):
        pytest.fail("An out-of-scope category must not reach ingestion")

    monkeypatch.setattr(evidence, "ingest_upload", unexpected_ingest)
    response = http.post(
        path.format(id=assessment.id),
        data={"category": "consent_form"},
        files={"file": ("policy.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == (422 if path.startswith("/api") else 200)
    assert "Unknown document category" in response.text


def test_iso_evidence_dropdown_uses_assessment_categories(db, http):
    _, _, assessment = seed_engagement(db, frameworks=("iso27001",))
    response = http.get(f"/assessments/{assessment.id}/evidence")
    assert response.status_code == 200
    category_select = response.text.split('id="upload-category"', 1)[1].split('</select>', 1)[0]
    assert 'value="statement_of_applicability"' in category_select
    assert 'value="other"' in category_select
    assert 'value="consent_form"' not in category_select
    assert 'value="dpia"' not in category_select
