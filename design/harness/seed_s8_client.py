"""Seed the S8 client upload and invalid-link specimens."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.evidence import Evidence, EvidenceVersion
from app.models.magic_link import MagicLink
from app.services.magic_links import token_digest
from design.harness.seed_s4 import FROZEN_NOW


ACTIVE_TOKEN = "AbCdEfGhIjKlMnOpQrStUv"
EXPIRED_TOKEN = "BcDeFgHiJkLmNoPqRsTuVw"
REVOKED_TOKEN = "CdEfGhIjKlMnOpQrStUvWx"

SCREEN_STATES = {
    "b6-magic_upload": ("default", "uploading", "done", "error"),
    "b6-magic_invalid": ("expired", "revoked", "unknown"),
    "b7-link-expired": ("expired",),
}

_ITEMS = (
    {
        "key": "item-0",
        "title": "Consent withdrawal procedure",
        "description": "",
    },
    {
        "key": "item-1",
        "title": "Breach notification runbook",
        "description": "",
    },
    {
        "key": "item-2",
        "title": "Access review export Q4",
        "description": "A spreadsheet export of the last quarter's user access reviews.",
    },
    {
        "key": "item-3",
        "title": "Vendor data-processing register",
        "description": "The vendors that handle personal data and what each one handles.",
    },
)


def _link(
    engagement_id: str,
    *,
    link_id: str,
    token: str,
    expires_at: datetime,
    revoked_at: datetime | None = None,
) -> MagicLink:
    return MagicLink(
        id=link_id,
        engagement_id=engagement_id,
        token_digest=token_digest(token),
        scope_json=json.dumps({"version": 1, "items": list(_ITEMS)}, sort_keys=True),
        max_uploads=20,
        max_size_bytes=100 * 1024 * 1024,
        expires_at=expires_at,
        revoked_at=revoked_at,
        contact_name="Ananya Rao",
        contact_email="ananya@kestrel.example",
        created_at=FROZEN_NOW - timedelta(days=8),
    )


def _received_evidence(engagement_id: str, link_id: str, index: int, filename: str, title: str) -> tuple[Evidence, EvidenceVersion]:
    evidence_id = f"s8-client-evidence-{index}"
    digest = (f"s8-client-{index}" * 8)[:64]
    evidence = Evidence(
        id=evidence_id,
        engagement_id=engagement_id,
        assessment_id=None,
        original_filename=filename,
        storage_path=f"evidence/{engagement_id}/{evidence_id}/v1.pdf",
        file_hash_sha256=digest,
        file_size_bytes=1_024 * (index + 1),
        mime_type="application/pdf",
        status="active",
        uploaded_by=f"client_link:{link_id}",
        created_at=FROZEN_NOW - timedelta(days=2 + index),
    )
    version = EvidenceVersion(
        id=f"{evidence_id}-v1",
        evidence_id=evidence_id,
        version_number=1,
        storage_path=evidence.storage_path,
        file_hash_sha256=digest,
        file_size_bytes=evidence.file_size_bytes,
        change_reason=f"Client upload via magic link for requested item: {title}",
        status="active",
        original_filename=filename,
        mime_type="application/pdf",
        extracted_text="Seeded client evidence.",
        created_at=evidence.created_at,
    )
    return evidence, version


def apply(db: Session, screen: str, state: str, assessment, engagement, data) -> dict:
    """Seed one shared Kestrel-style client link fixture for every client state."""
    active = _link(
        engagement.id,
        link_id="s8-client-active",
        token=ACTIVE_TOKEN,
        expires_at=datetime(2026, 10, 18, 12, tzinfo=timezone.utc),
    )
    expired = _link(
        engagement.id,
        link_id="s8-client-expired",
        token=EXPIRED_TOKEN,
        expires_at=datetime(2026, 10, 15, 12, tzinfo=timezone.utc),
    )
    revoked = _link(
        engagement.id,
        link_id="s8-client-revoked",
        token=REVOKED_TOKEN,
        expires_at=datetime(2026, 10, 18, 12, tzinfo=timezone.utc),
        revoked_at=FROZEN_NOW - timedelta(days=1),
    )
    db.add_all([active, expired, revoked])
    db.flush()
    evidence = [
        _received_evidence(
            engagement.id,
            active.id,
            0,
            "consent-withdrawal-v3.pdf",
            _ITEMS[0]["title"],
        ),
        _received_evidence(
            engagement.id,
            active.id,
            1,
            "breach-runbook-2026.docx",
            _ITEMS[1]["title"],
        ),
    ]
    db.add_all([row for pair in evidence for row in pair])
    db.flush()

    if screen == "b6-magic_upload" and state == "default":
        return {"data_state": "database", "note": "Live active fixed fake token with two received items."}
    return {
        "data_state": "preview-state",
        "note": "State is rendered through the group-owned PREVIEW_PAGES fixture; the database keeps the fixed fake-token context.",
    }


def route(screen: str, state: str, assessment_id: str) -> str:
    if screen == "b6-magic_upload" and state == "default":
        return f"/magic/{ACTIVE_TOKEN}"
    if screen == "b6-magic_upload":
        return f"/design/pages/b6-magic_upload?state={state}"
    return f"/design/pages/{screen}?state={state}"
