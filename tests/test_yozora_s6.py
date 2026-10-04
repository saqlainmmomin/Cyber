"""HTTP contracts for the S6 evidence inventory and redirect slice."""

from __future__ import annotations

import io
import re
from datetime import datetime, timedelta, timezone

from app.models.assessment import Assessment, AssessmentDocument
from app.models.desk_review import DeskReviewSummary
from app.models.evidence import Evidence, EvidenceVersion
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
    # An engagement with no evidence shows the empty state; the filters appear once it has items.
    assert "No evidence yet" in page.text
    assert 'name="source"' not in page.text
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
    assert 'name="source"' in inventory.text
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
    assert "No evidence yet" in archived.text


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
    assert '<span class="sub">1 item</span>' in page.text
    assert "1 available" in page.text
    assert 'accept=".pdf,.docx,.png,.jpg,.jpeg,.webp"' in page.text
    assert 'value="privacy_policy"' in page.text
    filtered_upload = http.get(
        f"/engagements/{engagement.id}/evidence?state=upload&source=upload&status=active&search=Privacy"
    )
    assert f"/assessments/{assessment.id}/upload?source=upload&amp;status=active&amp;search=Privacy" in filtered_upload.text


def test_upload_fragment_preserves_scope_filters_and_row_actions(db, http, monkeypatch):
    _client, engagement, assessment = seed_engagement(db)
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args, **_kwargs: "seeded text")
    for filename in ("Privacy notice.pdf", "Security policy.pdf"):
        response = http.post(
            f"/assessments/{assessment.id}/upload",
            data={"category": "privacy_policy"},
            files={"file": (filename, io.BytesIO(_pdf(filename)), "application/pdf")},
        )
        assert response.status_code == 200
    fragment = http.post(
        f"/assessments/{assessment.id}/upload?assessment={assessment.id}&source=upload&status=active&search=policy",
        data={"category": "privacy_policy"},
        files={"file": ("Security policy v2.pdf", io.BytesIO(_pdf("v2")), "application/pdf")},
    )
    assert fragment.status_code == 200
    assert "Security policy v2.pdf" in fragment.text
    assert 'name="source"' not in fragment.text
    assert fragment.text.count('data-evidence-id=') == fragment.text.count('hx-delete="')
    assert fragment.text.count('data-evidence-id=') == fragment.text.count('hx-post="')
    encoded = f"assessment={assessment.id}&amp;source=upload&amp;status=active&amp;search=policy"
    assert fragment.text.count(encoded) >= 2
    assert engagement.id not in fragment.text.split("<table", 1)[-1].split("</table>", 1)[0]


def test_prefill_note_uses_real_freshness_data(db, http, monkeypatch):
    _client, engagement, assessment = seed_engagement(db)
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args, **_kwargs: "seeded text")
    first = http.post(
        f"/assessments/{assessment.id}/upload",
        data={"category": "privacy_policy"},
        files={"file": ("Before review.pdf", io.BytesIO(_pdf("before")), "application/pdf")},
    )
    assert first.status_code == 200
    first_version = db.query(EvidenceVersion).one()
    db.add(
        DeskReviewSummary(
            assessment_id=assessment.id,
            document_catalog="{}",
            coverage_summary="{}",
            raw_ai_response="{}",
            status="completed",
            completed_at=first_version.created_at - timedelta(seconds=1),
        )
    )
    db.commit()
    second = http.post(
        f"/assessments/{assessment.id}/upload",
        data={"category": "privacy_policy"},
        files={"file": ("After review.pdf", io.BytesIO(_pdf("after")), "application/pdf")},
    )
    assert second.status_code == 200
    page = http.get(f"/engagements/{engagement.id}/evidence?assessment={assessment.id}")
    assert page.status_code == 200
    assert 'data-prefill-note' in page.text
    assert "2 new documents since the" in page.text


def test_legacy_migration_notice_is_rendered_from_real_legacy_row(db, http):
    _client, engagement, assessment = seed_engagement(db)
    db.add(
        AssessmentDocument(
            assessment_id=assessment.id,
            filename="Legacy policy.pdf",
            file_path="legacy/policy.pdf",
            file_type="pdf",
            document_category="privacy_policy",
            extracted_text="legacy text",
        )
    )
    db.commit()
    page = http.get(f"/engagements/{engagement.id}/evidence?assessment={assessment.id}")
    assert page.status_code == 200
    assert "Legacy documents need migration" in page.text


def test_inventory_count_strip_includes_non_available_statuses(db, http, monkeypatch):
    _client, engagement, assessment = seed_engagement(db)
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args, **_kwargs: "seeded text")
    for index, filename in enumerate(("Scanning.pdf", "Rejected.pdf", "Out of date.pdf")):
        response = http.post(
            f"/assessments/{assessment.id}/upload",
            data={"category": "other"},
            files={"file": (filename, io.BytesIO(_pdf(str(index))), "application/pdf")},
        )
        assert response.status_code == 200
    rows = db.query(Evidence).order_by(Evidence.created_at, Evidence.id).all()
    rows[0].status = "quarantined"
    rows[1].status = "rejected"
    rows[2].status = "invalidated"
    db.commit()
    page = http.get(f"/engagements/{engagement.id}/evidence?assessment={assessment.id}")
    assert page.status_code == 200
    assert "3 items" in page.text
    assert "1 scanning" in page.text
    assert "1 rejected" in page.text
    assert "1 out of date" in page.text
    empty = http.get(f"/engagements/{engagement.id}/evidence?search=does-not-exist")
    assert "No evidence matches the filters" in empty.text
    assert 'href="/engagements/' in empty.text


def test_evidence_detail_uses_display_labels_and_existing_actions(db, http, monkeypatch):
    _client, engagement, assessment = seed_engagement(db)
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args, **_kwargs: "seeded text")
    uploaded = http.post(
        f"/assessments/{assessment.id}/upload",
        data={"category": "privacy_policy"},
        files={"file": ("Privacy notice.pdf", io.BytesIO(_pdf("detail")), "application/pdf")},
    )
    assert uploaded.status_code == 200
    evidence = db.query(Evidence).one()
    detail = http.get(f"/evidence/{evidence.id}")
    assert detail.status_code == 200
    assert "Privacy policy" in detail.text
    assert "privacy_policy" not in detail.text
    assert "MIME type" not in detail.text
    assert f'hx-delete="/assessments/{assessment.id}/documents/{evidence.id}"' in detail.text
    assert f'hx-post="/assessments/{assessment.id}/evidence/{evidence.id}/versions"' in detail.text


def test_reuse_markup_is_data_driven_and_unchecked_by_default(db, http, monkeypatch):
    _client, engagement, source = seed_engagement(db, name="Pilot assessment")
    target = Assessment(
        company_name=source.company_name,
        name="Current assessment",
        industry=source.industry,
        company_size=source.company_size,
        selected_frameworks='["dpdpa"]',
        engagement_id=engagement.id,
    )
    db.add(target)
    db.flush()
    evidence = Evidence(
        id="reuse-evidence",
        engagement_id=engagement.id,
        assessment_id=source.id,
        document_category="privacy_policy",
        original_filename="Pilot policy.pdf",
        storage_path="evidence/reuse-evidence",
        file_hash_sha256="a" * 64,
        file_size_bytes=100,
        mime_type="application/pdf",
        status="active",
        uploaded_by="consultant",
        created_at=datetime.now(timezone.utc) - timedelta(days=10),
    )
    db.add(evidence)
    db.add(EvidenceVersion(
        id="reuse-version",
        evidence_id=evidence.id,
        version_number=1,
        storage_path="evidence/reuse-evidence-v1",
        file_hash_sha256="b" * 64,
        file_size_bytes=100,
        original_filename="Pilot policy.pdf",
        mime_type="application/pdf",
        status="active",
        extracted_text="pilot policy",
        created_at=datetime.now(timezone.utc) - timedelta(days=10),
    ))
    from app.models.evidence import EvidenceUse

    db.add(EvidenceUse(
        id="reuse-source-use",
        evidence_id=evidence.id,
        assessment_id=source.id,
        framework_id="dpdpa",
        requirement_id="DPDPA.8",
        relevance="supports",
    ))
    db.commit()
    page = http.get(f"/assessments/{target.id}/evidence-reuse")
    assert page.status_code == 200
    assert re.search(r"Confirm reuse of\s*<span[^>]*>1</span>", page.text)
    assert len(re.findall(r"<form[^>]*data-reuse-confirm(?:\s|>)", page.text)) == 1
    assert 'data-reuse-error role="alert"' in page.text and 'hidden></div>' in page.text
    assert 'data-reuse-select checked' not in page.text


def test_design_preview_renders_all_workpaper_entry_states(db, http):
    for state in ("default", "legacy", "excluded"):
        page = http.get(f"/design/pages/workpaper_entry?state={state}")
        assert page.status_code == 200
        assert 'data-workpaper-entry' in page.text
        assert 'aria-label="Assessment"' in page.text and "Open in conclusions" in page.text
    assert "1. Client response" not in page.text
    assert "4. Consultant decision" not in page.text


def test_design_aws_preview_uses_real_page_and_panel_with_fixture_result(db, http):
    page = http.get("/design/pages/aws_evidence?state=result")
    assert page.status_code == 200
    assert 'data-aws-setup' in page.text
    assert 'data-aws-result' in page.text
    assert 'data-aws-pull-form' in page.text
    assert page.text.count('data-copy-trigger="aws-') == 4
