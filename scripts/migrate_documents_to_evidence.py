"""Migrate legacy AssessmentDocument rows into versioned Evidence records."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import logging
from pathlib import Path
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.models.assessment import Assessment, AssessmentDocument
from app.models.evidence import Evidence
from app.services import evidence as evidence_service
from scripts.backup import create_backup, database_path

logger = logging.getLogger(__name__)

MIGRATION_ACTOR = "system:migration"
MIGRATION_UPLOADED_BY = "migration:assessment_documents"


@dataclass
class DocumentMigrationStats:
    migrated: int = 0
    text_only: int = 0
    skipped_existing: int = 0
    skipped_orphan: int = 0
    skipped_empty: int = 0
    warnings: list[str] = field(default_factory=list)


def _warning(stats: DocumentMigrationStats, message: str) -> None:
    stats.warnings.append(message)
    logger.warning(message)


def run_document_migration(session: Session) -> DocumentMigrationStats:
    stats = DocumentMigrationStats()
    documents = (
        session.query(AssessmentDocument)
        .order_by(AssessmentDocument.uploaded_at, AssessmentDocument.id)
        .all()
    )
    for document in documents:
        if session.get(Evidence, document.id) is not None:
            stats.skipped_existing += 1
            continue
        assessment = session.get(Assessment, document.assessment_id)
        if assessment is None or assessment.engagement_id is None:
            message = (
                f"AssessmentDocument {document.id}: assessment {document.assessment_id} "
                "has no engagement; run scripts/migrate_legacy.py first."
            )
            stats.skipped_orphan += 1
            _warning(stats, message)
            continue

        candidates = [
            Path(document.file_path),
            Path(settings.upload_dir) / document.assessment_id / Path(document.file_path).name,
        ]
        source_path = next((path for path in candidates if path.is_file()), None)
        if source_path is not None:
            content = source_path.read_bytes()
            file_type = document.file_type
            change_reason = (
                "Migrated from assessment_documents "
                f"(original file copied from {document.file_path})."
            )
        elif (document.extracted_text or "").strip():
            content = document.extracted_text.encode("utf-8")
            file_type = "txt"
            change_reason = (
                "Migrated from assessment_documents: original file missing at "
                f"{document.file_path}; blob is the previously extracted text."
            )
            stats.text_only += 1
            _warning(
                stats,
                f"AssessmentDocument {document.id}: original file missing; migrated extracted text only.",
            )
        else:
            stats.skipped_empty += 1
            _warning(
                stats,
                f"AssessmentDocument {document.id}: original file and extracted text are both missing.",
            )
            continue

        created_blob: Path | None = None
        try:
            _evidence, version = evidence_service.receive_evidence(
                session,
                evidence_id=document.id,
                engagement_id=assessment.engagement_id,
                assessment_id=document.assessment_id,
                filename=document.filename,
                content=content,
                file_type=file_type,
                category=document.document_category,
                uploaded_by=MIGRATION_UPLOADED_BY,
                actor=MIGRATION_ACTOR,
                created_at=document.uploaded_at,
                change_reason=change_reason,
                allow_duplicate=True,
            )
            created_blob = evidence_service.blob_path(version.storage_path)
            evidence_service.release_from_quarantine(
                session,
                version_id=version.id,
                actor=MIGRATION_ACTOR,
            )
            version.extracted_text = document.extracted_text
            session.commit()
            stats.migrated += 1
        except Exception:
            session.rollback()
            if created_blob is not None:
                created_blob.unlink(missing_ok=True)
            raise
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate AssessmentDocument rows to Evidence.")
    parser.add_argument("--db-url", default=settings.database_url)
    parser.add_argument("--upload-dir", default=settings.upload_dir)
    parser.add_argument("--backup-out-dir", default="backups")
    parser.add_argument("--skip-backup", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    settings.upload_dir = args.upload_dir
    db_path = database_path(args.db_url)

    backup_dir = None
    if not args.skip_backup:
        try:
            backup_dir = create_backup(db_path, Path(settings.upload_dir), Path(args.backup_out_dir))
        except Exception as exc:
            print(f"Backup failed: {exc}", file=sys.stderr)
            return 1

    engine = create_engine(args.db_url, connect_args={"check_same_thread": False})
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        stats = run_document_migration(session)
    except Exception as exc:
        session.close()
        engine.dispose()
        print(f"Document migration failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
        engine.dispose()

    if backup_dir is not None:
        print(f"Backup: {backup_dir}")
    print(
        "Document migration complete: "
        f"{stats.migrated} migrated ({stats.text_only} text-only), "
        f"{stats.skipped_existing} already migrated, "
        f"{stats.skipped_orphan} orphaned, {stats.skipped_empty} empty"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
