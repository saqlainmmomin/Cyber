"""HTTP contracts for assessment-scoped Evidence and its inventory fragment path."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

from app.models.assessment import Assessment
from app.models.evidence import Evidence
from app.services import evidence as evidence_service
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    seed_engagement,
    upload_root,
)


def _pdf(label: str) -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n" + label.encode()
    )


def _assessment_nav(page: str) -> str:
    match = re.search(
        r'<nav class="tabs" aria-label="Assessment">(.*?)</nav>',
        page,
        re.DOTALL,
    )
    assert match, "assessment tab row missing"
    return match.group(1)


def test_assessment_evidence_page_keeps_assessment_chrome_and_scope_empty_state(db, http):
    _client, _engagement, assessment = seed_engagement(db, name="Head office")

    page = http.get(f"/assessments/{assessment.id}/evidence")

    assert page.status_code == 200
    nav = _assessment_nav(page.text)
    assert [label for label in re.findall(r">([^<>]+)</a>", nav)] == [
        "Overview",
        "Scope",
        "Evidence",
        "Questionnaire",
        "Review",
        "Report",
    ]
    assert nav.count('aria-selected="true"') == 1
    assert 'href="/assessments/' + assessment.id + '/evidence" aria-selected="true"' in nav
    assert 'aria-label="Engagement"' not in page.text
    assert re.search(r'aria-pressed="true"[^>]*>Inventory</button>', page.text)
    assert f'href="/assessments/{assessment.id}/rfi"' in page.text
    assert 'name="assessment"' not in page.text
    assert "Showing" not in page.text
    assert "No evidence yet" in page.text
    assert "No evidence matches the filters" not in page.text

    filtered = http.get(f"/assessments/{assessment.id}/evidence?source=upload")
    assert filtered.status_code == 200
    assert "No evidence matches the filters" in filtered.text
    assert f'href="/assessments/{assessment.id}/evidence">Clear filters</a>' in filtered.text


def test_assessment_evidence_route_handles_legacy_and_unknown_assessments(db, http):
    standalone = Assessment(
        company_name="Unlinked client",
        name="Standalone review",
        industry="Technology",
        company_size="small",
        selected_frameworks=json.dumps(["dpdpa"]),
        engagement_id=None,
    )
    db.add(standalone)
    db.commit()

    legacy = http.get(f"/assessments/{standalone.id}/evidence", follow_redirects=False)
    assert legacy.status_code == 303
    assert legacy.headers["location"] == f"/assessments/{standalone.id}"
    assert http.get("/assessments/unknown-assessment/evidence").status_code == 404


def test_assessment_evidence_isolated_from_sibling_assessments(db, http, monkeypatch):
    _client, engagement, assessment_a = seed_engagement(db, name="Head office")
    assessment_b = Assessment(
        company_name=assessment_a.company_name,
        name="Payments subsidiary",
        industry=assessment_a.industry,
        company_size=assessment_a.company_size,
        selected_frameworks=json.dumps(["dpdpa"]),
        engagement_id=engagement.id,
    )
    db.add(assessment_b)
    db.commit()
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args, **_kwargs: "seeded text")

    for assessment, filename in (
        (assessment_a, "Head office policy.pdf"),
        (assessment_b, "Payments policy.pdf"),
    ):
        response = http.post(
            f"/assessments/{assessment.id}/upload",
            data={"category": "other"},
            files={"file": (filename, io.BytesIO(_pdf(filename)), "application/pdf")},
        )
        assert response.status_code == 200

    page_a = http.get(f"/assessments/{assessment_a.id}/evidence")
    page_b = http.get(f"/assessments/{assessment_b.id}/evidence")
    engagement_page = http.get(f"/engagements/{engagement.id}/evidence")
    assert "Head office policy.pdf" in page_a.text
    assert "Payments policy.pdf" not in page_a.text
    assert "Payments policy.pdf" in page_b.text
    assert "Head office policy.pdf" not in page_b.text
    assert "Head office policy.pdf" in engagement_page.text
    assert "Payments policy.pdf" in engagement_page.text


def test_assessment_evidence_preserves_scope_in_archive_and_version_fragments(db, http, monkeypatch):
    _client, engagement, assessment = seed_engagement(db, name="Head office")
    sibling = Assessment(
        company_name=assessment.company_name,
        name="Payments subsidiary",
        industry=assessment.industry,
        company_size=assessment.company_size,
        selected_frameworks=json.dumps(["dpdpa"]),
        engagement_id=engagement.id,
    )
    db.add(sibling)
    db.commit()
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args, **_kwargs: "seeded text")

    response = http.post(
        f"/assessments/{assessment.id}/upload",
        data={"category": "other"},
        files={"file": ("Head office policy.pdf", io.BytesIO(_pdf("v1")), "application/pdf")},
    )
    assert response.status_code == 200
    evidence = db.query(Evidence).one()
    page = http.get(f"/assessments/{assessment.id}/evidence")
    delete_match = re.search(
        rf'hx-delete="(/assessments/{re.escape(assessment.id)}/documents/{re.escape(evidence.id)}\?[^\"]+)"',
        page.text,
    )
    version_match = re.search(
        rf'hx-post="(/assessments/{re.escape(assessment.id)}/evidence/{re.escape(evidence.id)}/versions\?[^\"]+)"',
        page.text,
    )
    assert delete_match and "assessment=" + assessment.id in delete_match.group(1)
    assert version_match and "assessment=" + assessment.id in version_match.group(1)

    versioned = http.post(
        version_match.group(1),
        data={"change_reason": "Signed copy"},
        files={"file": ("Head office signed.pdf", io.BytesIO(_pdf("v2")), "application/pdf")},
    )
    assert versioned.status_code == 200
    assert "Head office signed.pdf" in versioned.text
    assert "assessment=" + assessment.id in versioned.text
    assert sibling.id not in versioned.text

    archived = http.delete(delete_match.group(1))
    assert archived.status_code == 200
    assert "Head office signed.pdf" not in archived.text
    assert "No evidence yet" in archived.text


def test_documents_redirect_to_assessment_evidence_and_engagement_scope_stays_valid(db, http):
    _client, engagement, assessment = seed_engagement(db)

    redirect = http.get(f"/assessments/{assessment.id}?tab=documents", follow_redirects=False)
    assert redirect.status_code == 303
    assert redirect.headers["location"] == f"/assessments/{assessment.id}/evidence"
    scoped = http.get(f"/engagements/{engagement.id}/evidence?assessment={assessment.id}")
    assert scoped.status_code == 200
    assert "No evidence matches the filters" not in scoped.text
    assert "No evidence yet" in scoped.text


def test_archived_assessment_evidence_is_read_only(db, http):
    _client, engagement, assessment = seed_engagement(db, status="archived")

    page = http.get(f"/assessments/{assessment.id}/evidence")

    assert page.status_code == 200
    assert 'data-archived-banner' in page.text
    assert "read-only" in page.text
    assert not re.search(r'<button[^>]*data-upload-open', page.text)


def test_rfi_uses_assessment_evidence_chrome_and_preserves_template_contract(db, http):
    _client, engagement, assessment = seed_engagement(db, name="Head office")

    page = http.get(f"/assessments/{assessment.id}/rfi")

    assert page.status_code == 200
    nav = _assessment_nav(page.text)
    assert [label for label in re.findall(r">([^<>]+)</a>", nav)] == [
        "Overview",
        "Scope",
        "Evidence",
        "Questionnaire",
        "Review",
        "Report",
    ]
    assert nav.count('aria-selected="true"') == 1
    assert 'href="/assessments/' + assessment.id + '/evidence" aria-selected="true"' in nav
    assert 'aria-label="Engagement"' not in page.text
    assert re.search(r'aria-pressed="true"[^>]*>Requests</button>', page.text)
    assert f'href="/assessments/{assessment.id}/evidence"' in page.text
    assert f'href="/assessments/{assessment.id}/rfi"' in page.text
    assert f'href="/engagements/{engagement.id}/requests"' in page.text
    assert "'" not in Path("app/templates/pages/rfi.html").read_text()


def test_assessment_tab_callers_keep_order_and_single_selection(db, http):
    _client, _engagement, assessment = seed_engagement(db, name="Head office")
    pages = (
        (f"/assessments/{assessment.id}?tab=overview", "Overview"),
        (f"/assessments/{assessment.id}/scope", "Scope"),
        (f"/assessments/{assessment.id}?tab=questionnaire", "Questionnaire"),
        (f"/assessments/{assessment.id}/evidence", "Evidence"),
        (f"/assessments/{assessment.id}/review-queue", "Review"),
        (f"/assessments/{assessment.id}?tab=report", "Report"),
        (f"/assessments/{assessment.id}/rfi", "Evidence"),
    )
    expected = ["Overview", "Scope", "Evidence", "Questionnaire", "Review", "Report"]

    for path, current in pages:
        page = http.get(path)
        assert page.status_code == 200, (path, page.status_code, page.text[:500])
        nav = _assessment_nav(page.text)
        assert re.findall(r">([^<>]+)</a>", nav) == expected
        assert nav.count('aria-selected="true"') == 1
        selected = re.search(r'<a href="([^"]+)" aria-selected="true">([^<]+)</a>', nav)
        assert selected and selected.group(2) == current


def test_fragment_clear_filters_stays_on_assessment_page_with_absolute_htmx_url(db, http, monkeypatch):
    _client, _engagement, assessment = seed_engagement(db, name="Head office")
    monkeypatch.setattr(evidence_service, "extract_text", lambda *_args, **_kwargs: "seeded text")
    http.post(
        f"/assessments/{assessment.id}/upload",
        data={"category": "other"},
        files={"file": ("Head office policy.pdf", io.BytesIO(_pdf("v1")), "application/pdf")},
    )
    evidence = db.query(Evidence).one()

    # htmx sends the absolute page URL, not a bare path.
    archived = http.delete(
        f"/assessments/{assessment.id}/documents/{evidence.id}?assessment={assessment.id}&source=aws",
        headers={"HX-Current-URL": f"http://testserver/assessments/{assessment.id}/evidence?source=aws"},
    )

    assert archived.status_code == 200
    assert f'href="/assessments/{assessment.id}/evidence"' in archived.text
