"""Restore a verified CyberAssess backup while preserving current data for rollback."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sqlite3
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


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _file_sizes(directory: Path) -> dict[Path, int]:
    return {
        path.relative_to(directory): path.stat().st_size
        for path in directory.rglob("*")
        if path.is_file()
    }


def _copy_database_for_safety(db_path: Path, safety_db: Path) -> None:
    partial_db = safety_db.with_name(f".{safety_db.name}.partial")
    shutil.copy2(str(db_path), str(partial_db))
    if partial_db.stat().st_size != db_path.stat().st_size:
        raise RuntimeError("Pre-restore database safety copy size does not match the live database")
    partial_db.replace(safety_db)


def _checkpoint_wal(db_path: Path) -> None:
    try:
        connection = sqlite3.connect(db_path)
        try:
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            connection.close()
    except sqlite3.DatabaseError:
        return


def _assert_wal_empty(db_path: Path) -> None:
    wal_path = Path(f"{db_path}-wal")
    if wal_path.exists() and wal_path.stat().st_size > 0:
        raise RuntimeError("Live database has an active write-ahead log; stop the app and retry the restore")


def _copy_uploads_for_safety(upload_dir: Path, safety_uploads: Path) -> None:
    partial_uploads = safety_uploads.with_name(f".{safety_uploads.name}.partial")
    copied_file_count = copy_tree_and_count(upload_dir, partial_uploads)
    source_sizes = _file_sizes(upload_dir)
    copied_sizes = _file_sizes(partial_uploads)
    if copied_file_count != len(source_sizes) or source_sizes != copied_sizes:
        raise RuntimeError("Pre-restore uploads safety copy does not match the live uploads")
    partial_uploads.replace(safety_uploads)


def _restore_safety_copy(
    safety_dir: Path,
    db_path: Path,
    upload_dir: Path,
    *,
    db_live_existed: bool,
    upload_live_existed: bool,
    db_safety_copy_verified: bool,
    upload_safety_copy_verified: bool,
    db_moved_aside: bool,
    upload_moved_aside: bool,
    upload_removal_started: bool,
    db_restore_attempted: bool,
    upload_restore_attempted: bool,
) -> None:
    safety_db = safety_dir / db_path.name
    partial_db = safety_db.with_name(f".{safety_db.name}.partial")
    safety_uploads = safety_dir / "uploads"
    partial_uploads = safety_uploads.with_name(f".{safety_uploads.name}.partial")

    if db_moved_aside or (db_safety_copy_verified and db_restore_attempted):
        if db_path.exists():
            _remove_path(db_path)
        if safety_db.exists():
            shutil.move(str(safety_db), str(db_path))
    elif db_safety_copy_verified and not db_path.exists():
        shutil.move(str(safety_db), str(db_path))
    elif not db_live_existed and db_restore_attempted:
        _remove_path(db_path)
    else:
        _remove_path(safety_db)
    _remove_path(partial_db)

    if upload_moved_aside or (upload_safety_copy_verified and upload_removal_started):
        if upload_dir.exists():
            _remove_path(upload_dir)
        if safety_uploads.exists():
            shutil.move(str(safety_uploads), str(upload_dir))
    elif upload_safety_copy_verified and not upload_dir.exists():
        shutil.move(str(safety_uploads), str(upload_dir))
    elif not upload_live_existed and upload_restore_attempted:
        _remove_path(upload_dir)
    else:
        _remove_path(safety_uploads)
    _remove_path(partial_uploads)


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

    if db_path.exists():
        _checkpoint_wal(db_path)
        _assert_wal_empty(db_path)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    safety_dir = backup_dir.parent / f"pre-restore-{timestamp}"
    db_live_existed = db_path.exists()
    upload_live_existed = upload_dir.exists()
    if db_live_existed or upload_live_existed:
        safety_dir.mkdir(exist_ok=False)

    db_safety_copy_verified = False
    upload_safety_copy_verified = False
    db_moved_aside = False
    upload_moved_aside = False
    upload_removal_started = False
    db_restore_attempted = False
    upload_restore_attempted = False

    try:
        if db_live_existed:
            safety_db = safety_dir / db_path.name
            safety_db.parent.mkdir(parents=True, exist_ok=True)
            _copy_database_for_safety(db_path, safety_db)
            db_safety_copy_verified = True
            db_path.unlink()
            for suffix in ("-wal", "-shm"):
                sidecar_path = Path(f"{db_path}{suffix}")
                if sidecar_path.exists():
                    sidecar_path.unlink()
            db_moved_aside = True
        if upload_live_existed:
            safety_uploads = safety_dir / "uploads"
            _copy_uploads_for_safety(upload_dir, safety_uploads)
            upload_safety_copy_verified = True
            upload_removal_started = True
            shutil.rmtree(upload_dir)
            upload_moved_aside = True

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
                db_live_existed=db_live_existed,
                upload_live_existed=upload_live_existed,
                db_safety_copy_verified=db_safety_copy_verified,
                upload_safety_copy_verified=upload_safety_copy_verified,
                db_moved_aside=db_moved_aside,
                upload_moved_aside=upload_moved_aside,
                upload_removal_started=upload_removal_started,
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
    parser = argparse.ArgumentParser(
        description="Restore a verified CyberAssess backup. Stop the app before restoring."
    )
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
