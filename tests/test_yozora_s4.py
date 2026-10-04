"""Focused route contracts for the S4 engagement surfaces."""

import json
from datetime import datetime, timezone

from app.models.audit_event import AuditEvent
from app.models.report_snapshot import ReportSnapshot
from app.services.engagement_factory import add_assessment_to_engagement
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    upload_root,
)
from tests.yozora_support import seed_engagement


def test_engagements_list_is_available_and_uses_the_engagement_row(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    page = http.get("/engagements")
    assert page.status_code == 200
    assert engagement.name in page.text
    assert f'href="/engagements/{engagement.id}"' in page.text


def test_engagements_list_empty_state_is_available(db, http):
    page = http.get("/engagements")
    assert page.status_code == 200
    assert "No engagements yet" in page.text


def test_reports_index_has_an_empty_state_without_issued_versions(http):
    page = http.get("/reports")
    assert page.status_code == 200
    assert "No issued reports" in page.text


def test_reports_index_links_an_issued_version_to_its_engagement_reports_tab(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    snapshot = ReportSnapshot(
        id="snapshot-s4-issued",
        engagement_id=engagement.id,
        type="integrated_report",
        format="pdf",
        storage_path=f"reports/engagements/{engagement.id}/snapshot-s4-issued.pdf",
        generated_at=datetime(2026, 9, 29, 12, tzinfo=timezone.utc),
        is_issued=True,
    )
    db.add_all([
        snapshot,
        AuditEvent(
            id="audit-s4-generated",
            actor="consultant:Reviewer",
            action="report_snapshot.generated",
            entity_type="report_snapshot",
            entity_id=snapshot.id,
            metadata_json=json.dumps({"size_bytes": 1024}),
            created_at=datetime(2026, 9, 29, 12, tzinfo=timezone.utc),
        ),
        AuditEvent(
            id="audit-s4-issued",
            actor="consultant:Reviewer",
            action="report_snapshot.issued",
            entity_type="report_snapshot",
            entity_id=snapshot.id,
            metadata_json="{}",
            created_at=datetime(2026, 9, 29, 14, tzinfo=timezone.utc),
        ),
    ])
    db.commit()
    page = http.get("/reports")
    assert page.status_code == 200
    assert "Integrated engagement report (PDF)" in page.text
    assert f'href="/engagements/{engagement.id}/integrated-reports"' in page.text


def test_two_assessment_engagement_renders_stage_and_next_step(db, http):
    client, engagement, _assessment = seed_engagement(db)
    add_assessment_to_engagement(
        db,
        engagement=engagement,
        client=client,
        name="Operations",
        description="Operations scope",
        framework_ids=["dpdpa"],
    )
    page = http.get(f"/engagements/{engagement.id}")
    assert page.status_code == 200
    assert "Stage and next step" in page.text
    assert "Upload evidence" in page.text or "Scope" in page.text
