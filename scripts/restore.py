"""Restore a verified CyberAssess backup while preserving current data for rollback."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from scripts.backup import check_integrity, copy_tree_and_count, count_files, database_path


def _read_manifest(backup_dir: Path) -> dict:
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"Backup manifest does not exist: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Backup manifest is invalid JSON: {manifest_path}") from exc
    if manifest.get("sqlite_integrity_check") != "ok":
        raise ValueError("Backup manifest does not confirm SQLite integrity")
    if not isinstance(manifest.get("db_source"), str) or not isinstance(manifest.get("file_count"), int):
        raise ValueError("Backup manifest is missing required database or upload metadata")
    return manifest


def _restore_safety_copy(
    safety_dir: Path,
    db_path: Path,
    upload_dir: Path,
    *,
    db_restore_attempted: bool,
    upload_restore_attempted: bool,
) -> None:
    safety_db = safety_dir / db_path.name
    safety_uploads = safety_dir / "uploads"
    if safety_db.exists():
        if db_path.exists():
            db_path.unlink()
        shutil.move(str(safety_db), str(db_path))
    elif db_restore_attempted and db_path.exists():
        db_path.unlink()
    if safety_uploads.exists():
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
        shutil.move(str(safety_uploads), str(upload_dir))
    elif upload_restore_attempted and upload_dir.exists():
        shutil.rmtree(upload_dir)


def restore_backup(backup_dir: Path, db_path: Path, upload_dir: Path, *, force: bool = False) -> Path:
    """Restore *backup_dir* and return the pre-restore safety-copy directory."""
    backup_dir = Path(backup_dir)
    db_path = Path(db_path)
    upload_dir = Path(upload_dir)
    manifest = _read_manifest(backup_dir)
    backup_db = backup_dir / Path(manifest["db_source"]).name
    backup_uploads = backup_dir / "uploads"
    if not backup_db.is_file() or not backup_uploads.is_dir():
        raise ValueError("Backup is missing its database or uploads directory")
    check_integrity(backup_db)
    if count_files(backup_uploads) != manifest["file_count"]:
        raise ValueError("Backup upload file count does not match its manifest")

    if not force:
        answer = input(f"Restore backup '{backup_dir}' and overwrite live data? [y/N] ")
        if answer.lower() not in {"y", "yes"}:
            raise RuntimeError("Restore cancelled")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safety_dir = backup_dir.parent / f"pre-restore-{timestamp}"
    safety_dir.mkdir(exist_ok=False)
    db_restore_attempted = False
    upload_restore_attempted = False

    try:
        if db_path.exists():
            safety_db = safety_dir / db_path.name
            safety_db.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(db_path), str(safety_db))
        if upload_dir.exists():
            shutil.move(str(upload_dir), str(safety_dir / "uploads"))

        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_restore_attempted = True
        shutil.copy2(backup_db, db_path)
        upload_restore_attempted = True
        restored_file_count = copy_tree_and_count(backup_uploads, upload_dir)

        check_integrity(db_path)
        if restored_file_count != manifest["file_count"]:
            raise RuntimeError("Restored upload file count does not match the backup manifest")
    except Exception:
        try:
            _restore_safety_copy(
                safety_dir,
                db_path,
                upload_dir,
                db_restore_attempted=db_restore_attempted,
                upload_restore_attempted=upload_restore_attempted,
            )
        except Exception as rollback_exc:
            raise RuntimeError(
                f"Restore failed and safety-copy rollback also failed: {rollback_exc}"
            ) from rollback_exc
        raise

    return safety_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore a verified CyberAssess backup.")
    parser.add_argument("backup_dir", help="Timestamped backup directory to restore")
    parser.add_argument("--force", action="store_true", help="Skip the overwrite confirmation prompt")
    args = parser.parse_args()

    try:
        safety_dir = restore_backup(
            Path(args.backup_dir),
            database_path(settings.database_url),
            Path(settings.upload_dir),
            force=args.force,
        )
    except Exception as exc:
        print(f"Restore failed: {exc}", file=sys.stderr)
        return 1

    print(f"Restored {args.backup_dir}; pre-restore safety copy: {safety_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
