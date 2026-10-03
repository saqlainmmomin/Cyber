"""Yozora backend item 7: read models for the redesigned screens (services only, no templates).

Handoff: tasks/handoffs/2026-10-03-yozora-backend-features.md. evidence_inventory, assessment_stage,
prefill_freshness and request_summary are pure reads over what the app already stores.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.desk_review import DeskReviewSummary
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.models.questionnaire import QuestionnaireResponse
from app.models.report_snapshot import ReportSnapshot
from app.services import (
    assessment_stage,
    evidence_inventory,
    magic_links,
    prefill_freshness,
    report_snapshots,
    request_summary,
)
from app.services.evidence_reuse import REUSE_CONFIRMED_ACTION
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    REPO_ROOT,
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    seed_engagement,
    upload_root,
)

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc)


def _evidence(
    db, engagement, *, filename, assessment=None, status="active", uploaded_by="consultant",
    mime="application/pdf", size=2048, created=T0, versions=1,
):
    evidence = Evidence(
        engagement_id=engagement.id,
        assessment_id=assessment.id if assessment else None,
        original_filename=filename,
        storage_path=f"evidence/{engagement.id}/{filename}",
        file_hash_sha256=hashlib.sha256(filename.encode()).hexdigest(),
        file_size_bytes=size,
        mime_type=mime,
        status=status,
        uploaded_by=uploaded_by,
        created_at=created,
    )
    db.add(evidence)
    db.flush()
    for number in range(1, versions + 1):
        db.add(
            EvidenceVersion(
                evidence_id=evidence.id,
                version_number=number,
                storage_path=f"evidence/{engagement.id}/{filename}.v{number}",
                file_hash_sha256=hashlib.sha256(f"{filename}{number}".encode()).hexdigest(),
                file_size_bytes=size * number,
                status=(
                    "superseded" if number < versions
                    else status if status in ("active", "quarantined", "rejected")
                    else "rejected"
                ),
                original_filename=filename if number == 1 else f"v{number} {filename}",
                mime_type=mime,
                extracted_text="text",
                created_at=created + timedelta(days=number - 1),
            )
        )
    db.flush()
    return evidence


def _use(db, evidence, assessment, requirement_id, framework_id="dpdpa", created=T0):
    use = EvidenceUse(
        evidence_id=evidence.id,
        assessment_id=assessment.id,
        requirement_id=requirement_id,
        framework_id=framework_id,
        relevance="supporting",
        created_at=created,
    )
    db.add(use)
    db.flush()
    return use


def _second_assessment(db, client, engagement, name):
    assessment = Assessment(
        company_name=client.name, industry=client.industry, company_size=client.size,
        engagement_id=engagement.id, selected_frameworks=json.dumps(["iso27001"]), name=name,
    )
    db.add(assessment)
    db.flush()
    return assessment


@pytest.fixture()
def inventory(db):
    client, engagement, head = seed_engagement(db, client_name="Meridian Ledger", name="FY2026 privacy readiness")
    head.name = "Head office"
    payments = _second_assessment(db, client, engagement, "Payments subsidiary")
    pilot = _second_assessment(db, client, engagement, "Pilot")
    link = magic_links.create_link(
        db, engagement_id=engagement.id, item_titles=["Access review"], expires_in_days=7, max_uploads=5, max_total_mb=10,
    )
    magic_links.set_contact(db, link.link, contact_name="Ananya Rao", contact_email=None)
    notice = _evidence(db, engagement, filename="Privacy notice.pdf", assessment=head, created=T0 + timedelta(days=11), versions=2)
    _use(db, notice, head, "DPDPA.5")
    _use(db, notice, head, "DPDPA.6")
    iam = _evidence(
        db, engagement, filename="aws_config_123_ap-south-1_iam.txt", uploaded_by="aws_config:123456789012",
        mime="text/plain", created=T0 + timedelta(days=13),
    )
    _use(db, iam, head, "A.5.15", "iso27001")
    _use(db, iam, payments, "A.8.2", "iso27001")
    access = _evidence(
        db, engagement, filename="Access review export Q4.xlsx", status="quarantined",
        uploaded_by=f"client_link:{link.link.id}",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", created=T0 + timedelta(days=14),
    )
    _use(db, access, head, "A.5.18", "iso27001")
    rejected = _evidence(db, engagement, filename="Old policy.pdf", assessment=payments, status="rejected", created=T0 + timedelta(days=2))
    retention_policy = _evidence(
        db, engagement, filename="Data retention policy.pdf", assessment=pilot, status="invalidated", created=T0 + timedelta(days=8),
    )
    _use(db, retention_policy, pilot, "DPDPA.8")
    reused_use = _use(db, retention_policy, head, "DPDPA.8")
    db.add(
        AuditEvent(
            actor="consultant:Priya", action=REUSE_CONFIRMED_ACTION, entity_type="evidence_use", entity_id=reused_use.id,
            metadata_json=json.dumps({"evidence_id": retention_policy.id, "source_assessment_id": pilot.id}),
        )
    )
    archived = _evidence(db, engagement, filename="Archived.pdf", assessment=head, status="archived")
    db.commit()
    return SimpleNamespace(
        client=client, engagement=engagement, head=head, payments=payments, pilot=pilot, notice=notice, iam=iam,
        access=access, rejected=rejected, retention_policy=retention_policy, archived=archived,
    )


# --- evidence_inventory ---------------------------------------------------------------------------


def test_inventory_rows_sources_statuses_and_supports(db, inventory):
    rows = evidence_inventory.inventory_rows(db, inventory.engagement.id)
    by_id = {row.evidence_id: row for row in rows}
    assert inventory.archived.id not in by_id  # archived is never listed
    assert [row.evidence_id for row in rows] == [
        inventory.access.id, inventory.iam.id, inventory.notice.id, inventory.retention_policy.id, inventory.rejected.id,
    ]  # newest first

    notice = by_id[inventory.notice.id]
    assert (notice.source, notice.source_label, notice.status_label) == ("upload", "Upload", "Available")
    assert notice.filename == "v2 Privacy notice.pdf" and notice.size_bytes == 4096  # the current version
    assert notice.type_label == "PDF" and notice.supports == ("DPDPA.5", "DPDPA.6")
    assert [ref.name for ref in notice.used_by] == ["Head office"]
    assert notice.updated_at == T0 + timedelta(days=12)
    assert notice.engagement_name == "FY2026 privacy readiness" and notice.client_name == "Meridian Ledger"

    iam = by_id[inventory.iam.id]
    assert (iam.source, iam.source_label, iam.type_label) == ("aws", "AWS", "Snapshot")
    assert {ref.name for ref in iam.used_by} == {"Head office", "Payments subsidiary"}
    assert iam.supports == ("A.5.15", "A.8.2")

    access = by_id[inventory.access.id]
    assert (access.source, access.source_label, access.contact_name) == ("client_link", "Client link", "Ananya Rao")
    assert (access.status_label, access.type_label) == ("Scanning", "XLSX")

    reused = by_id[inventory.retention_policy.id]
    assert (reused.source, reused.source_label, reused.origin) == ("reused", "Reused", "upload")
    assert reused.reused_from == "Pilot" and reused.status_label == "Out of date"
    assert by_id[inventory.rejected.id].status_label == "Rejected"


def test_inventory_assessment_filter_and_reuse_per_assessment(db, inventory):
    head_rows = evidence_inventory.inventory_rows(db, inventory.engagement.id, assessment_id=inventory.head.id)
    assert {row.evidence_id for row in head_rows} == {
        inventory.notice.id, inventory.iam.id, inventory.access.id, inventory.retention_policy.id,
    }
    by_id = {row.evidence_id: row for row in head_rows}
    assert by_id[inventory.iam.id].supports == ("A.5.15",)  # only what it supports in this assessment
    assert by_id[inventory.retention_policy.id].source == "reused"
    pilot_rows = evidence_inventory.inventory_rows(db, inventory.engagement.id, assessment_id=inventory.pilot.id)
    assert [(row.evidence_id, row.source) for row in pilot_rows] == [(inventory.retention_policy.id, "upload")]


def test_inventory_filters_and_search(db, inventory):
    engagement_id = inventory.engagement.id
    assert [row.evidence_id for row in evidence_inventory.inventory_rows(db, engagement_id, source="aws")] == [inventory.iam.id]
    assert [row.evidence_id for row in evidence_inventory.inventory_rows(db, engagement_id, source="client_link")] == [inventory.access.id]
    assert [row.evidence_id for row in evidence_inventory.inventory_rows(db, engagement_id, source="reused")] == [inventory.retention_policy.id]
    assert [row.evidence_id for row in evidence_inventory.inventory_rows(db, engagement_id, status="quarantined")] == [inventory.access.id]
    assert [row.evidence_id for row in evidence_inventory.inventory_rows(db, engagement_id, search="privacy NOTICE")] == [inventory.notice.id]
    assert [row.evidence_id for row in evidence_inventory.inventory_rows(db, engagement_id, search="a.8.2")] == [inventory.iam.id]
    assert [row.evidence_id for row in evidence_inventory.inventory_rows(db, engagement_id, search="ananya")] == [inventory.access.id]
    assert evidence_inventory.inventory_rows(db, engagement_id, status="archived") == []


def test_status_counts(db, inventory):
    rows = evidence_inventory.inventory_rows(db, inventory.engagement.id)
    assert evidence_inventory.status_counts(rows) == {
        "total": 5, "Scanning": 1, "Available": 2, "Rejected": 1, "Out of date": 1,
    }
    assert evidence_inventory.status_counts([]) == {
        "total": 0, "Scanning": 0, "Available": 0, "Rejected": 0, "Out of date": 0,
    }


def test_cross_engagement_rows(db, inventory):
    _client, other, other_assessment = seed_engagement(db, client=inventory.client, name="ISO surveillance")
    supplier = _evidence(db, other, filename="Supplier register.xlsx", assessment=other_assessment)
    _closed_client, archived_engagement, archived_assessment = seed_engagement(db, client_name="Loomwire", name="Old", status="archived")
    hidden = _evidence(db, archived_engagement, filename="Hidden.pdf", assessment=archived_assessment)
    db.commit()
    rows = evidence_inventory.cross_engagement_rows(db)
    ids = {row.evidence_id for row in rows}
    assert supplier.id in ids and inventory.notice.id in ids and hidden.id not in ids
    assert {row.engagement_name for row in rows} == {"FY2026 privacy readiness", "ISO surveillance"}
    only_other = evidence_inventory.cross_engagement_rows(db, engagement_id=other.id)
    assert [row.evidence_id for row in only_other] == [supplier.id]
    assert evidence_inventory.cross_engagement_rows(db, client_id=inventory.client.id, source="aws")[0].evidence_id == inventory.iam.id


def test_type_label_and_origin():
    assert evidence_inventory.origin_of("aws_securityhub:123") == "aws"
    assert evidence_inventory.origin_of("client_link:abc") == "client_link"
    assert evidence_inventory.origin_of("consultant:Priya") == "upload"
    assert evidence_inventory.type_label("application/octet-stream", "diagram.vsdx") == "VSDX"
    assert evidence_inventory.type_label("image/png", "flow.png") == "PNG"
    assert evidence_inventory.type_label("text/plain", "x.txt", "aws") == "Snapshot"


# --- prefill_freshness ----------------------------------------------------------------------------


def test_prefill_freshness_without_and_with_a_completed_prefill(db):
    _client, engagement, assessment = seed_engagement(db)
    first = _evidence(db, engagement, filename="Policy.pdf", assessment=assessment, created=T0)
    _evidence(db, engagement, filename="Notice.pdf", assessment=assessment, created=T0 + timedelta(days=1))
    _evidence(db, engagement, filename="Scanning.pdf", assessment=assessment, status="quarantined", created=T0)
    db.commit()
    assert prefill_freshness.freshness(db, assessment) == prefill_freshness.PrefillFreshness(2, 2, None)

    completed = T0 + timedelta(days=2)
    db.add(DeskReviewSummary(assessment_id=assessment.id, status="completed", completed_at=completed))
    db.commit()
    assert prefill_freshness.freshness(db, assessment) == prefill_freshness.PrefillFreshness(2, 0, completed)

    _evidence(db, engagement, filename="Late.pdf", assessment=assessment, created=T0 + timedelta(days=3))
    linked = _evidence(db, engagement, filename="Client upload.pdf", uploaded_by="client_link:x", created=T0)
    _use(db, linked, assessment, "DPDPA.5", created=T0 + timedelta(days=4))  # mapped after the pre-fill
    db.commit()
    result = prefill_freshness.freshness(db, assessment)
    assert (result.available, result.new_since_last_prefill) == (4, 2)
    assert first.id  # the earlier documents stay counted as available, not new


def test_prefill_that_did_not_complete_counts_everything_as_new(db):
    _client, engagement, assessment = seed_engagement(db)
    _evidence(db, engagement, filename="Policy.pdf", assessment=assessment)
    db.add(DeskReviewSummary(assessment_id=assessment.id, status="error", completed_at=None))
    db.commit()
    assert prefill_freshness.freshness(db, assessment) == prefill_freshness.PrefillFreshness(1, 1, None)


# --- assessment_stage -----------------------------------------------------------------------------


def _expect(result, stage, note, next_label=None, next_href=None):
    assert (result.stage, result.note, result.next_label, result.next_href) == (stage, note, next_label, next_href)
    assert result.label == assessment_stage.STAGE_LABELS[stage]


def test_stage_transitions_scope_evidence_and_questionnaire(db):
    _client, engagement, assessment = seed_engagement(db)
    base = f"/assessments/{assessment.id}"
    _expect(assessment_stage.stage(db, assessment), "scope", "Scope not set", "Set scope", f"{base}?tab=scope")

    assessment.scope_answers = json.dumps({})
    db.commit()
    _expect(assessment_stage.stage(db, assessment), "evidence", "No documents yet", "Upload evidence", f"{base}?tab=documents")

    _evidence(db, engagement, filename="Policy.pdf", assessment=assessment)
    db.commit()
    _expect(
        assessment_stage.stage(db, assessment), "evidence", "1 document ready to pre-fill",
        "Pre-fill questionnaire", f"{base}?tab=documents",
    )
    assessment.desk_review_status = "analyzing"
    db.commit()
    _expect(assessment_stage.stage(db, assessment), "evidence", "Pre-fill running")

    assessment.desk_review_status = "completed"
    db.commit()
    result = assessment_stage.stage(db, assessment)
    assert result.stage == "questionnaire" and result.next_label == "Continue questionnaire"
    answered, total = result.note.removesuffix(" answered").split(" of ")
    assert answered == "0" and int(total) > 0
    assert result.next_href == f"{base}?tab=questionnaire"


def test_stage_answering_a_question_moves_past_evidence_even_without_documents(db):
    _client, _engagement, assessment = seed_engagement(db)
    assessment.scope_answers = json.dumps({})
    db.add(QuestionnaireResponse(assessment_id=assessment.id, question_id="Q-unrendered", answer="fully_implemented"))
    db.commit()
    assert assessment_stage.stage(db, assessment).stage == "questionnaire"


@pytest.fixture()
def answered(db, monkeypatch):
    _client, _engagement, assessment = seed_engagement(db)
    assessment.scope_answers = json.dumps({})
    db.add(QuestionnaireResponse(assessment_id=assessment.id, question_id="Q1", answer="fully_implemented"))
    db.commit()
    monkeypatch.setattr(assessment_stage, "_questionnaire_counts", lambda _db, _a: (42, 42))
    return assessment


def _cards(monkeypatch, *states):
    monkeypatch.setattr(
        assessment_stage.conclusion_review, "conclusion_cards",
        lambda _db, _id: [SimpleNamespace(state=state) for state in states],
    )


def _release(monkeypatch, released, released_at=None):
    monkeypatch.setattr(
        assessment_stage.approved_report, "release_state",
        lambda _db, _a: SimpleNamespace(released=released, released_at=released_at),
    )


def test_stage_transitions_analysis_review_and_report(db, monkeypatch, answered):
    base = f"/assessments/{answered.id}"
    _cards(monkeypatch)
    _expect(assessment_stage.stage(db, answered), "questionnaire", "42 of 42 answered", "Run analysis", f"{base}?tab=questionnaire")
    answered.status = "analyzing"
    db.commit()
    _expect(assessment_stage.stage(db, answered), "questionnaire", "Analysis running")
    answered.status = "completed"
    db.commit()

    _cards(monkeypatch, "approved", "edited", "pending", "pending", "pending", "rejected")
    _expect(assessment_stage.stage(db, answered), "review", "2 of 6 approved", "Review 3 conclusions", f"{base}/conclusions")
    _cards(monkeypatch, "approved", "pending")
    assert assessment_stage.stage(db, answered).next_label == "Review 1 conclusion"

    _cards(monkeypatch, "approved", "edited", "rejected")
    _release(monkeypatch, False)
    _expect(assessment_stage.stage(db, answered), "report", "2 of 3 approved", "Release report", f"{base}?tab=report")

    _release(monkeypatch, True, datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc))
    _expect(assessment_stage.stage(db, answered), "report", "Released 15 Oct 2026", "Generate board report", f"{base}/snapshots")

    db.add(
        ReportSnapshot(
            assessment_id=answered.id, type=report_snapshots.BOARD_REPORT_SNAPSHOT_TYPE, format="pdf",
            storage_path="reports/x.pdf", generated_at=datetime(2026, 10, 16, tzinfo=timezone.utc),
        )
    )
    db.commit()
    _expect(assessment_stage.stage(db, answered), "report", "Board report generated 16 Oct 2026")


def test_stage_next_labels_are_the_handoff_vocabulary():
    assert assessment_stage.STAGES == ("scope", "evidence", "questionnaire", "review", "report")
    assert {
        assessment_stage.SET_SCOPE, assessment_stage.UPLOAD_EVIDENCE, assessment_stage.PREFILL,
        assessment_stage.CONTINUE_QUESTIONNAIRE, assessment_stage.RUN_ANALYSIS, assessment_stage.RELEASE_REPORT,
        assessment_stage.GENERATE_BOARD_REPORT,
    } == {
        "Set scope", "Upload evidence", "Pre-fill questionnaire", "Continue questionnaire", "Run analysis",
        "Release report", "Generate board report",
    }
    assert assessment_stage.review_label(4) == "Review 4 conclusions"


# --- request_summary ------------------------------------------------------------------------------


def _rfi_snapshot(db, assessment, *, issued):
    snapshot = ReportSnapshot(
        assessment_id=assessment.id, type=report_snapshots.RFI_SNAPSHOT_TYPE, format="json",
        storage_path=f"reports/assessments/{assessment.id}/rfi.json", is_issued=issued,
    )
    db.add(snapshot)
    db.flush()
    return snapshot


def test_request_summary_without_an_rfi(db):
    _client, engagement, assessment = seed_engagement(db)
    assert request_summary.engagement_summaries(db, engagement.id) == [
        request_summary.RequestSummary(assessment.id, assessment.display_name, None, None, 0, 0, None)
    ]


def test_request_summary_counts_items_received_through_links(db, monkeypatch):
    _client, engagement, assessment = seed_engagement(db)
    assessment.name = "Head office"
    issued = _rfi_snapshot(db, assessment, issued=True)
    _rfi_snapshot(db, assessment, issued=False)  # a newer draft, not yet with the client
    monkeypatch.setattr(
        report_snapshots, "read_rfi_document",
        lambda _db, _snapshot: {"items": [{"item_id": f"RFI-00{n}"} for n in (1, 2, 3)]},
    )
    created = magic_links.create_rfi_link(
        db, engagement_id=engagement.id, assessment_id=assessment.id, snapshot_id=issued.id,
        rfi_items=[("RFI-001", "RFI-001: Policy"), ("RFI-002", "RFI-002: Notice")],
        expires_in_days=7, max_uploads=5, max_total_mb=10,
    )
    evidence = _evidence(db, engagement, filename="Policy.pdf", uploaded_by=f"client_link:{created.link.id}")
    for item_key in ("item-1", "item-1"):  # two uploads for one item count once
        db.add(
            AuditEvent(
                actor=f"client_link:{created.link.id}", action="magic_link.upload_received", entity_type="magic_link",
                entity_id=created.link.id, metadata_json=json.dumps({"item_key": item_key, "evidence_id": evidence.id}),
            )
        )
    db.commit()
    summary = request_summary.assessment_summary(db, assessment)
    assert summary == request_summary.RequestSummary(
        assessment_id=assessment.id, assessment_name="Head office", version=1, items=3, received=1,
        active_links=1, latest_version=2,
    )


def test_read_models_call_no_model():
    for module in ("evidence_inventory", "assessment_stage", "prefill_freshness", "request_summary", "actions_export", "firm_settings"):
        source = (REPO_ROOT / "app" / "services" / f"{module}.py").read_text(encoding="utf-8")
        for token in ("llm_client", "call_llm", "claude_analyzer", "services.grounding", "openai", "anthropic"):
            assert token not in source, (module, token)
