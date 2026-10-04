"""HTTP contracts for the S6 evidence inventory and redirect slice."""

from __future__ import annotations

import io
import re

from app.models.assessment import Assessment
from app.models.evidence import Evidence
from app.services import evidence as evidence_service
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    upload_root,
)
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
    assert engagement.name in page.text
    assert 'name="source"' in page.text
    assert "Upload" in page.text
    assert 'data-nav-key="evidence"' in page.text
    assert 'id="document-list"' in page.text
    assert "/assessments//" not in page.text

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

    inventory = http.get(f"/engagements/{engagement.id}/evidence")
    assert inventory.status_code == 200
    assert "/assessments//" not in inventory.text
    delete_url = re.search(r'hx-delete="([^"]+/documents/' + re.escape(evidence.id) + r'[^"]*)"', inventory.text)
    version_url = re.search(r'hx-post="([^"]+/evidence/' + re.escape(evidence.id) + r'/versions[^"]*)"', inventory.text)
    assert delete_url and delete_url.group(1).startswith(f"/assessments/{assessment.id}/")
    assert version_url and version_url.group(1).startswith(f"/assessments/{assessment.id}/")

    versioned = http.post(
        version_url.group(1),
        data={"change_reason": "Signed copy"},
        files={"file": ("Privacy Policy signed.pdf", io.BytesIO(_pdf("v2")), "application/pdf")},
    )
    assert versioned.status_code == 200
    assert "Privacy Policy signed.pdf" in versioned.text

    archived = http.delete(delete_url.group(1))
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
            data={"category": "other"},
            files={"file": (filename, io.BytesIO(_pdf(filename)), "application/pdf")},
        )
        assert response.status_code == 200

    cross = http.get("/evidence?state=all")
    assert cross.status_code == 200
    assert "Every file across your engagements" in cross.text
    assert re.search(r"<th[^>]*>\s*Engagement\s*</th>", cross.text)
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


def test_unlinked_documents_redirects_to_assessment_overview(db, http):
    assessment = Assessment(
        company_name="Unlinked client",
        name="Standalone review",
        industry="Technology",
        company_size="small",
        selected_frameworks='["dpdpa"]',
        engagement_id=None,
    )
    db.add(assessment)
    db.commit()
    response = http.get(f"/assessments/{assessment.id}?tab=documents", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/assessments/{assessment.id}"
    overview = http.get(response.headers["location"])
    assert overview.status_code == 200


def test_inventory_counts_use_display_labels_and_upload_contract(db, http, monkeypatch):
    _client, engagement, assessment = seed_engagement(db)
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args, **_kwargs: "seeded text")
    uploaded = http.post(
        f"/assessments/{assessment.id}/upload",
        data={"category": "privacy_policy"},
        files={"file": ("Privacy notice.pdf", io.BytesIO(_pdf("v1")), "application/pdf")},
    )
    assert uploaded.status_code == 200
    page = http.get(f"/engagements/{engagement.id}/evidence?state=upload")
    assert "1 items · 1 available" in page.text
    assert 'accept=".pdf,.docx,.png,.jpg,.jpeg,.webp"' in page.text
    assert 'value="privacy_policy"' in page.text
    filtered_upload = http.get(
        f"/engagements/{engagement.id}/evidence?state=upload&source=upload&status=active&search=Privacy"
    )
    assert f"/assessments/{assessment.id}/upload?source=upload&amp;status=active&amp;search=Privacy" in filtered_upload.text


def test_design_preview_renders_all_workpaper_entry_states(db, http):
    for state in ("default", "legacy", "excluded"):
        page = http.get(f"/design/pages/workpaper_entry?state={state}")
        assert page.status_code == 200
        assert 'data-workpaper-entry' in page.text
    assert "1. Client response" not in page.text
    assert "4. Consultant decision" not in page.text
