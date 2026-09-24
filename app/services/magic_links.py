"""Scoped, expiring capability links for unauthenticated evidence intake."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.assessment import _new_id
from app.models.audit_event import AuditEvent
from app.models.evidence import Evidence, EvidenceVersion
from app.models.engagement import Engagement
from app.models.magic_link import MagicLink
from app.services import evidence as evidence_service

logger = logging.getLogger(__name__)

TOKEN_BYTES = 16
TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{22}$")
UPLOADS_PER_HOUR = 10
MAX_FILE_BYTES = 25 * 1024 * 1024
MULTIPART_OVERHEAD_BYTES = 64 * 1024
MAX_ITEMS = 20
MAX_ITEM_TITLE_CHARS = 200
EXPIRES_DAYS_RANGE = (1, 30)
MAX_UPLOADS_RANGE = (1, 100)
MAX_TOTAL_MB_RANGE = (1, 500)
RFI_SCOPE_VERSION = 2
RFI_UNKNOWN_ITEM_TEXT = "Choose requested items from this RFI version."
INVALID_LINK_MESSAGE = "This link is invalid or has expired. Contact your consultant for a new link."
FILE_TOO_LARGE_MESSAGE = "Files must be 25 MB or smaller."
UPLOAD_LIMIT_MESSAGE = "This link has reached its upload limit. Contact your consultant."
SECURITY_HEADERS = {
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "X-Robots-Tag": "noindex, nofollow",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
        "frame-ancestors 'none'; base-uri 'none'"
    ),
}


class MagicLinkError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class MagicLinkNotFound(MagicLinkError):
    status_code = 404


class MagicLinkValidationError(MagicLinkError):
    status_code = 422


class MagicLinkConflict(MagicLinkError):
    status_code = 409


class UploadLimitReached(MagicLinkError):
    status_code = 403


class PayloadTooLarge(MagicLinkError):
    status_code = 413


class RateLimited(MagicLinkError):
    status_code = 429

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Too many uploads in the last hour. Try again later.")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def generate_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def client_actor(link: MagicLink) -> str:
    return f"client_link:{link.id}"


def scope_items(link: MagicLink) -> list[dict]:
    return json.loads(link.scope_json)["items"]


@dataclass(frozen=True)
class CreatedLink:
    link: MagicLink
    token: str


@dataclass(frozen=True)
class LinkUsage:
    uploads_total: int
    uploads_last_hour: int
    bytes_total: int
    oldest_in_window: datetime | None


def _audit(
    db: Session,
    *,
    actor: str,
    action: str,
    entity_id: str,
    metadata: dict,
) -> None:
    db.add(
        AuditEvent(
            actor=actor,
            action=action,
            entity_type="magic_link",
            entity_id=entity_id,
            metadata_json=json.dumps(metadata, sort_keys=True),
        )
    )


def _validated_titles(
    db: Session,
    *,
    engagement_id: str,
    item_titles: list[str],
    expires_in_days: int,
    max_uploads: int,
    max_total_mb: int,
) -> list[str]:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise MagicLinkNotFound("Engagement not found")
    if engagement.status != "active":
        raise MagicLinkConflict("Magic links can only be created for active engagements.")

    titles = [title.strip() for title in item_titles if title.strip()]
    if not titles:
        raise MagicLinkValidationError("Add at least one requested item.")
    if len(titles) > MAX_ITEMS:
        raise MagicLinkValidationError("A link can request at most 20 items.")
    if any(len(title) > MAX_ITEM_TITLE_CHARS for title in titles):
        raise MagicLinkValidationError(
            "Requested item titles must be 200 characters or fewer."
        )
    if len({title.casefold() for title in titles}) != len(titles):
        raise MagicLinkValidationError("Requested item titles must be unique.")
    if not EXPIRES_DAYS_RANGE[0] <= expires_in_days <= EXPIRES_DAYS_RANGE[1]:
        raise MagicLinkValidationError("Expiry must be between 1 and 30 days.")
    if not MAX_UPLOADS_RANGE[0] <= max_uploads <= MAX_UPLOADS_RANGE[1]:
        raise MagicLinkValidationError("Upload limit must be between 1 and 100.")
    if not MAX_TOTAL_MB_RANGE[0] <= max_total_mb <= MAX_TOTAL_MB_RANGE[1]:
        raise MagicLinkValidationError("Total size limit must be between 1 and 500 MB.")

    return titles


def _insert_link(
    db: Session,
    *,
    engagement_id: str,
    scope: dict,
    item_keys: list[str],
    expires_in_days: int,
    max_uploads: int,
    max_total_mb: int,
    actor: str,
    extra_audit: dict | None = None,
) -> CreatedLink:
    token = generate_token()
    expires_at = _now() + timedelta(days=expires_in_days)
    audit_metadata = {
        "engagement_id": engagement_id,
        "expires_at": expires_at.isoformat(),
        "item_keys": item_keys,
        "max_size_bytes": max_total_mb * 1024 * 1024,
        "max_uploads": max_uploads,
    }
    if extra_audit:
        audit_metadata.update(extra_audit)

    link = MagicLink(
        id=_new_id(),
        engagement_id=engagement_id,
        token_digest=token_digest(token),
        scope_json=json.dumps(scope, sort_keys=True),
        max_uploads=max_uploads,
        max_size_bytes=max_total_mb * 1024 * 1024,
        expires_at=expires_at,
    )
    db.add(link)
    db.flush()
    _audit(
        db,
        actor=actor,
        action="magic_link.created",
        entity_id=link.id,
        metadata=audit_metadata,
    )
    db.flush()
    return CreatedLink(link=link, token=token)


def create_link(
    db: Session,
    *,
    engagement_id: str,
    item_titles: list[str],
    expires_in_days: int,
    max_uploads: int,
    max_total_mb: int,
    actor: str = "consultant",
) -> CreatedLink:
    titles = _validated_titles(
        db,
        engagement_id=engagement_id,
        item_titles=item_titles,
        expires_in_days=expires_in_days,
        max_uploads=max_uploads,
        max_total_mb=max_total_mb,
    )
    items = [
        {"key": f"item-{index}", "title": title}
        for index, title in enumerate(titles, start=1)
    ]
    return _insert_link(
        db,
        engagement_id=engagement_id,
        scope={"items": items, "version": 1},
        item_keys=[item["key"] for item in items],
        expires_in_days=expires_in_days,
        max_uploads=max_uploads,
        max_total_mb=max_total_mb,
        actor=actor,
    )


def create_rfi_link(
    db: Session,
    *,
    engagement_id: str,
    assessment_id: str,
    snapshot_id: str,
    rfi_items: list[tuple[str, str]],
    expires_in_days: int,
    max_uploads: int,
    max_total_mb: int,
    actor: str = "consultant",
) -> CreatedLink:
    titles = _validated_titles(
        db,
        engagement_id=engagement_id,
        item_titles=[title for _item_id, title in rfi_items],
        expires_in_days=expires_in_days,
        max_uploads=max_uploads,
        max_total_mb=max_total_mb,
    )
    item_ids = [item_id for item_id, _title in rfi_items]
    if (
        any(re.fullmatch(r"RFI-\d{3,}", item_id) is None for item_id in item_ids)
        or len(set(item_ids)) != len(item_ids)
    ):
        raise MagicLinkValidationError(RFI_UNKNOWN_ITEM_TEXT)
    items = [
        {"key": f"item-{index}", "rfi_item_id": item_id, "title": _validated_title}
        for index, ((item_id, title), _validated_title) in enumerate(
            zip(rfi_items, titles),
            start=1,
        )
    ]
    return _insert_link(
        db,
        engagement_id=engagement_id,
        scope={
            "items": items,
            "rfi": {"assessment_id": assessment_id, "snapshot_id": snapshot_id},
            "version": RFI_SCOPE_VERSION,
        },
        item_keys=[item["key"] for item in items],
        expires_in_days=expires_in_days,
        max_uploads=max_uploads,
        max_total_mb=max_total_mb,
        actor=actor,
        extra_audit={
            "rfi_assessment_id": assessment_id,
            "rfi_snapshot_id": snapshot_id,
            "rfi_item_ids": item_ids,
        },
    )


def revoke_link(
    db: Session,
    *,
    engagement_id: str,
    link_id: str,
    actor: str = "consultant",
) -> MagicLink:
    link = db.get(MagicLink, link_id)
    if link is None or link.engagement_id != engagement_id:
        raise MagicLinkNotFound("Magic link not found")
    if link.revoked_at is not None:
        raise MagicLinkConflict("Magic link is already revoked.")

    revoked_at = _now()
    link.revoked_at = revoked_at
    _audit(
        db,
        actor=actor,
        action="magic_link.revoked",
        entity_id=link.id,
        metadata={"engagement_id": engagement_id, "revoked_at": revoked_at.isoformat()},
    )
    db.flush()
    return link


def link_status(link: MagicLink, now: datetime | None = None) -> str:
    if link.revoked_at is not None:
        return "revoked"
    if _as_utc(link.expires_at) <= _as_utc(now or _now()):
        return "expired"
    return "active"


def resolve_token(db: Session, token: str) -> MagicLink | None:
    if not isinstance(token, str) or TOKEN_PATTERN.fullmatch(token) is None:
        logger.info("Rejected magic-link request: invalid, expired or revoked link")
        return None

    digest = token_digest(token)
    matches = db.query(MagicLink).filter(MagicLink.token_digest == digest).all()
    link = matches[0] if len(matches) == 1 else None
    engagement_id = (
        link.engagement_id
        if link is not None
        else "__invalid_magic_link_engagement__"
    )
    engagement = (
        db.query(Engagement)
        .filter(Engagement.id == engagement_id)
        .first()
    )
    if link is None:
        if len(matches) > 1:
            logger.error("Multiple magic links share a token digest")
        else:
            logger.info("Rejected magic-link request: invalid, expired or revoked link")
        return None

    if link_status(link) != "active":
        logger.info("Rejected magic-link request: invalid, expired or revoked link")
        return None
    if engagement is None or engagement.status != "active":
        logger.info("Rejected magic-link request: invalid, expired or revoked link")
        return None
    return link


def link_usage(db: Session, link: MagicLink) -> LinkUsage:
    rows = (
        db.query(Evidence.created_at, Evidence.file_size_bytes)
        .filter(
            Evidence.engagement_id == link.engagement_id,
            Evidence.uploaded_by == client_actor(link),
        )
        .all()
    )
    now = _now()
    cutoff = now - timedelta(hours=1)
    recent = [(_as_utc(created_at), size) for created_at, size in rows if _as_utc(created_at) > cutoff]
    oldest = min((created_at for created_at, _size in recent), default=None)
    return LinkUsage(
        uploads_total=len(rows),
        uploads_last_hour=len(recent),
        bytes_total=sum(size for _created_at, size in rows),
        oldest_in_window=oldest,
    )


def check_upload_allowed(db: Session, link: MagicLink) -> LinkUsage:
    usage = link_usage(db, link)
    if usage.uploads_last_hour >= UPLOADS_PER_HOUR:
        now = _now()
        retry_after = math.ceil(
            (_as_utc(usage.oldest_in_window) + timedelta(hours=1) - now).total_seconds()
        )
        raise RateLimited(max(1, min(3600, retry_after)))
    if usage.uploads_total >= link.max_uploads:
        raise UploadLimitReached(UPLOAD_LIMIT_MESSAGE)
    return usage


def receive_client_upload(
    db: Session,
    *,
    link: MagicLink,
    item_key: str,
    filename: str,
    content: bytes,
    usage: LinkUsage | None = None,
) -> evidence_service.IngestResult:
    item = next((item for item in scope_items(link) if item.get("key") == item_key), None)
    if item is None:
        raise MagicLinkValidationError("Choose one of the requested items.")

    if usage is None:
        usage = check_upload_allowed(db, link)
    if len(content) > MAX_FILE_BYTES:
        raise PayloadTooLarge(FILE_TOO_LARGE_MESSAGE)
    if usage.bytes_total + len(content) > link.max_size_bytes:
        raise PayloadTooLarge("This upload would exceed the total size limit for this link.")

    digest = evidence_service.sha256_hex(content)
    duplicate = (
        db.query(Evidence)
        .filter(
            Evidence.engagement_id == link.engagement_id,
            Evidence.uploaded_by == client_actor(link),
            Evidence.file_hash_sha256 == digest,
            Evidence.status.in_(evidence_service.BLOCKING_DUPLICATE_STATUSES),
        )
        .first()
    )
    if duplicate is not None:
        raise MagicLinkConflict("You have already uploaded this file through this link.")

    evidence_id = _new_id()
    actor = client_actor(link)
    _audit(
        db,
        actor=actor,
        action="magic_link.upload_received",
        entity_id=link.id,
        metadata={
            "evidence_id": evidence_id,
            "item_key": item_key,
            "magic_link_id": link.id,
            "sha256": digest,
            "size_bytes": len(content),
        },
    )
    return evidence_service.ingest_engagement_upload(
        db,
        engagement_id=link.engagement_id,
        filename=filename,
        content=content,
        category=None,
        uploaded_by=actor,
        change_reason=f"Client upload via magic link for requested item: {item['title']}",
        evidence_id=evidence_id,
        allow_duplicate=True,
    )


def magic_link_rows(db: Session, engagement_id: str) -> list[dict]:
    links = (
        db.query(MagicLink)
        .filter(MagicLink.engagement_id == engagement_id)
        .order_by(MagicLink.created_at.desc(), MagicLink.id.desc())
        .all()
    )
    rows = []
    for link in links:
        usage = link_usage(db, link)
        rows.append(
            {
                "id": link.id,
                "id_prefix": link.id[:8],
                "status": link_status(link),
                "created_at": link.created_at,
                "expires_at": link.expires_at,
                "items": [item["title"] for item in scope_items(link)],
                "uploads_used": usage.uploads_total,
                "max_uploads": link.max_uploads,
                "bytes_used": usage.bytes_total,
                "max_size_bytes": link.max_size_bytes,
            }
        )
    return rows


def client_upload_rows(db: Session, engagement_id: str) -> list[dict]:
    rows = (
        db.query(Evidence, EvidenceVersion)
        .join(
            EvidenceVersion,
            (EvidenceVersion.evidence_id == Evidence.id)
            & (EvidenceVersion.version_number == 1),
        )
        .filter(
            Evidence.engagement_id == engagement_id,
            Evidence.uploaded_by.like("client_link:%"),
        )
        .order_by(Evidence.created_at.desc(), Evidence.id.desc())
        .all()
    )
    return [
        {
            "id": evidence.id,
            "filename": evidence.original_filename,
            "status": evidence.status,
            "uploaded_at": evidence.created_at,
            "magic_link_id": evidence.uploaded_by.removeprefix("client_link:"),
            "change_reason": version.change_reason,
        }
        for evidence, version in rows
    ]


_MAGIC_TOKEN_RE = re.compile(r"(/magic/)[^/?#\s\"]+")


def redact_magic_tokens(text: str) -> str:
    return _MAGIC_TOKEN_RE.sub(r"\1[redacted]", text)


def _redact_log_value(value):
    if isinstance(value, str):
        return redact_magic_tokens(value)
    if isinstance(value, tuple):
        return tuple(_redact_log_value(item) for item in value)
    if isinstance(value, list):
        return [_redact_log_value(item) for item in value]
    if isinstance(value, dict):
        return {
            _redact_log_value(key): _redact_log_value(item) for key, item in value.items()
        }
    return value


class MagicTokenRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_magic_tokens(record.msg)
        record.args = _redact_log_value(record.args)
        return True
