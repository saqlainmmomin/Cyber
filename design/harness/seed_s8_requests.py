"""Deterministic Requests and RFI specimens for the S8 visual gate."""

from __future__ import annotations

import hashlib
import json

from app.models.audit_event import AuditEvent
from app.models.evidence import Evidence, EvidenceVersion
from app.models.magic_link import MagicLink
from app.services import magic_links, rfi_requests
from design.harness.seed_s4 import _time


SCREEN_STATES = {
    "b6-magic_links": ("default", "empty", "error", "loading", "newlink", "revoke"),
    "b6-rfi": ("default", "error", "issue", "loading", "noscope", "versions"),
}

SEED_ACTOR = "consultant:Priya Sharma"
FIXED_TOKEN = "s8-fixed-fake-token"


def _scope_link(
    db,
    *,
    link_id: str,
    engagement_id: str,
    items: list[dict],
    contact_name: str | None,
    contact_email: str | None,
    expires_at,
    revoked_at=None,
    rfi: dict | None = None,
) -> MagicLink:
    scope = {"items": items, "version": 2 if rfi else 1}
    if rfi:
        scope["rfi"] = rfi
    link = MagicLink(
        id=link_id,
        engagement_id=engagement_id,
        token_digest=hashlib.sha256(FIXED_TOKEN.encode("ascii")).hexdigest(),
        scope_json=json.dumps(scope, sort_keys=True),
        max_uploads=20,
        max_size_bytes=100 * 1024 * 1024,
        expires_at=expires_at,
        revoked_at=revoked_at,
        contact_name=contact_name,
        contact_email=contact_email,
        created_at=_time(-14),
    )
    db.add(link)
    db.flush()
    db.add(
        AuditEvent(
            actor=SEED_ACTOR,
            action="magic_link.created",
            entity_type="magic_link",
            entity_id=link.id,
            metadata_json=json.dumps({"fixture": True}, sort_keys=True),
            created_at=link.created_at,
        )
    )
    return link


def _receipt(db, *, link: MagicLink, item_key: str, evidence_id: str, filename: str, engagement_id: str) -> None:
    created_at = _time(-5)
    db.add(
        Evidence(
            id=evidence_id,
            engagement_id=engagement_id,
            assessment_id=None,
            original_filename=filename,
            storage_path=f"evidence/{engagement_id}/{evidence_id}.pdf",
            file_hash_sha256=hashlib.sha256(evidence_id.encode()).hexdigest(),
            file_size_bytes=2048,
            mime_type="application/pdf",
            status="active",
            uploaded_by=f"client_link:{link.id}",
            created_at=created_at,
        )
    )
    db.add(
        EvidenceVersion(
            id=f"{evidence_id}-v1",
            evidence_id=evidence_id,
            version_number=1,
            storage_path=f"evidence/{engagement_id}/{evidence_id}.pdf",
            file_hash_sha256=hashlib.sha256(evidence_id.encode()).hexdigest(),
            file_size_bytes=2048,
            change_reason="Client upload through the seeded request link",
            status="released",
            original_filename=filename,
            mime_type="application/pdf",
            extracted_text="Seeded evidence receipt",
            created_at=created_at,
        )
    )
    db.add(
        AuditEvent(
            actor=f"client_link:{link.id}",
            action="magic_link.upload_received",
            entity_type="magic_link",
            entity_id=link.id,
            metadata_json=json.dumps(
                {"evidence_id": evidence_id, "item_key": item_key, "magic_link_id": link.id},
                sort_keys=True,
            ),
            created_at=created_at,
        )
    )


def _seed_legacy_links(db, engagement, *, include_links: bool, revoke: bool) -> None:
    if not include_links:
        return
    maya = _scope_link(
        db,
        link_id="s8-legacy-link-maya-000000000000000000000",
        engagement_id=engagement.id,
        items=[
            {"key": "item-1", "title": "Data processing register"},
            {"key": "item-2", "title": "Breach response plan"},
            {"key": "item-3", "title": "Vendor due diligence records"},
        ],
        contact_name="Maya Chen",
        contact_email="maya.chen@example.com",
        expires_at=_time(7),
    )
    _receipt(db, link=maya, item_key="item-1", evidence_id="s8-maya-evidence-001", filename="Data processing register.pdf", engagement_id=engagement.id)

    arjun = _scope_link(
        db,
        link_id="s8-legacy-link-arjun-000000000000000000000",
        engagement_id=engagement.id,
        items=[
            {"key": "item-1", "title": "Privacy notice"},
            {"key": "item-2", "title": "Incident response test"},
        ],
        contact_name="Arjun Rao",
        contact_email="arjun.rao@example.com",
        expires_at=_time(4),
    )
    _receipt(db, link=arjun, item_key="item-1", evidence_id="s8-arjun-evidence-001", filename="Privacy notice.pdf", engagement_id=engagement.id)
    _receipt(db, link=arjun, item_key="item-2", evidence_id="s8-arjun-evidence-002", filename="Incident response test.pdf", engagement_id=engagement.id)

    _scope_link(
        db,
        link_id="s8-legacy-link-grace-000000000000000000000",
        engagement_id=engagement.id,
        items=[{"key": "item-1", "title": "Backup restore test report"}],
        contact_name="Grace Lin",
        contact_email="grace.lin@example.com",
        expires_at=_time(5),
        revoked_at=_time(-1) if revoke else None,
    )


def _seed_rfi(db, assessment, engagement, *, state: str) -> None:
    if state == "noscope":
        assessment.scope_answers = None
        return
    assessment.scope_answers = json.dumps({"SCP.1": "yes", "ISO.SCP.1": "full_org"}, sort_keys=True)
    assessment.updated_at = _time(-2)
    first = rfi_requests.generate_version(db, assessment, omitted=(), actor=SEED_ACTOR)
    first.generated_at = _time(-12)
    db.flush()
    rfi_requests.issue_version(db, assessment, first.id, actor=SEED_ACTOR)
    db.flush()
    second = rfi_requests.generate_version(db, assessment, omitted=(), actor=SEED_ACTOR)
    second.generated_at = _time(-3)
    db.flush()
    current_document = rfi_requests.page_context(db, assessment)["current_items"]
    item_ids = [item["item_id"] for item in current_document[:4]]
    created = rfi_requests.create_client_link(
        db,
        assessment,
        first.id,
        item_ids=item_ids,
        expires_in_days=7,
        max_uploads=20,
        max_total_mb=100,
        actor=SEED_ACTOR,
    )
    magic_links.set_contact(db, created.link, contact_name="Maya Chen", contact_email="maya.chen@example.com")
    created.link.token_digest = hashlib.sha256(FIXED_TOKEN.encode("ascii")).hexdigest()
    created.link.created_at = _time(-6)
    db.flush()
    if item_ids:
        _receipt(db, link=created.link, item_key="item-1", evidence_id="s8-rfi-evidence-001", filename="Data processing register.pdf", engagement_id=engagement.id)
        if len(item_ids) > 1:
            _receipt(db, link=created.link, item_key="item-2", evidence_id="s8-rfi-evidence-002", filename="Breach response plan.pdf", engagement_id=engagement.id)


def apply(db, screen: str, state: str, assessment, engagement, data) -> dict:
    assessment.name = "Head office"
    assessment.company_name = "Meridian Ledger Technologies"
    if screen == "b6-magic_links":
        assessment.scope_answers = json.dumps({"SCP.1": "yes"}, sort_keys=True)
        _seed_legacy_links(db, engagement, include_links=state != "empty", revoke=state == "revoke")
        return {"data_state": "database", "note": "Legacy request links use a fixed fake token digest."}
    _seed_rfi(db, assessment, engagement, state=state)
    return {"data_state": "database", "note": "RFI versions and links are generated from the live services."}


def route(screen: str, state: str, assessment_id: str) -> str:
    return f"/design/pages/{screen}?assessment_id={assessment_id}&state={state}"
