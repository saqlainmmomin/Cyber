"""HTTP contracts for the S6 evidence inventory and redirect slice."""

from __future__ import annotations

import io

from app.models.evidence import Evidence
from app.services import evidence as evidence_service
from tests.yozora_support import db, http  # noqa: F401 - fixtures are used by name
from tests.yozora_support import seed_engagement


def _pdf(label: str) -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n" + label.encode()
    )


def test_inventory_and_documents_redirect_are_http_surfaces(db, http, monkeypatch):
    _client, engagement, assessment = seed_engagement(
        db,
        client_name="Meridian Ledger Technologies",
        name="FY2026 privacy readiness",
    )
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args, **_kwargs: "seeded text")

    page = http.get(f"/engagements/{engagement.id}/evidence")
    assert page.status_code == 200
    assert "Evidence inventory" in page.text
    assert 'name="source"' in page.text
    assert "Upload" in page.text
    assert 'data-nav-key="evidence"' in page.text
    assert 'id="document-list"' in page.text

    redirect = http.get(f"/assessments/{assessment.id}?tab=documents", follow_redirects=False)
    assert redirect.status_code == 303
    assert redirect.headers["location"] == f"/engagements/{engagement.id}/evidence?assessment={assessment.id}"

    uploaded = http.post(
        f"/assessments/{assessment.id}/upload",
        data={"category": "privacy_policy"},
        files={"file": ("Privacy Policy.pdf", io.BytesIO(_pdf("v1")), "application/pdf")},
    )
    assert uploaded.status_code == 200
    assert "Privacy Policy.pdf" in uploaded.text
    assert 'data-evidence-id=' in uploaded.text
    evidence = db.query(Evidence).one()

    versioned = http.post(
        f"/assessments/{assessment.id}/evidence/{evidence.id}/versions",
        data={"change_reason": "Signed copy"},
        files={"file": ("Privacy Policy signed.pdf", io.BytesIO(_pdf("v2")), "application/pdf")},
    )
    assert versioned.status_code == 200
    assert "Privacy Policy signed.pdf" in versioned.text

    archived = http.delete(f"/assessments/{assessment.id}/documents/{evidence.id}")
    assert archived.status_code == 200
    assert "Privacy Policy" not in archived.text


def test_cross_engagement_inventory_and_filter_round_trip(db, http, monkeypatch):
    _client_a, engagement_a, assessment_a = seed_engagement(
        db,
        client_name="Loomwire Labs",
        name="ISO 27001 surveillance review",
    )
    _client_b, engagement_b, assessment_b = seed_engagement(
        db,
        client_name="Kestrel Advisory",
        name="Advisory controls review",
    )
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args, **_kwargs: "seeded text")
    for assessment, filename in ((assessment_a, "Loomwire policy.pdf"), (assessment_b, "Kestrel policy.pdf")):
        response = http.post(
            f"/assessments/{assessment.id}/upload",
            data={"category": "general"},
            files={"file": (filename, io.BytesIO(_pdf(filename)), "application/pdf")},
        )
        assert response.status_code == 200

    cross = http.get("/evidence?state=all")
    assert cross.status_code == 200
    assert "Every file across your engagements" in cross.text
    assert "Engagement" in cross.text
    assert engagement_a.name in cross.text and engagement_b.name in cross.text

    filtered = http.get(
        f"/engagements/{engagement_a.id}/evidence?assessment={assessment_a.id}&source=upload&status=active"
    )
    assert filtered.status_code == 200
    assert "Loomwire policy.pdf" in filtered.text
    assert "Kestrel policy.pdf" not in filtered.text


def test_evidence_status_badge_keeps_service_labels_and_legacy_rows():
    from app.routers.web import templates

    for status, label in (
        ("quarantined", "Scanning"),
        ("active", "Available"),
        ("rejected", "Rejected"),
        ("invalidated", "Out of date"),
        ("superseded", "Superseded"),
        ("legacy", "Legacy (not migrated)"),
    ):
        assert label in templates.get_template("components/evidence_status_badge.html").render(status=status)
