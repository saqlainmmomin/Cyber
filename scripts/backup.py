"""Create a consistent local backup of CyberAssess data and uploads."""

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


def database_path(database_url: str) -> Path:
    """Return the SQLite file path represented by a sqlite:/// URL."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Backup only supports sqlite:/// database URLs")
    return Path(database_url.removeprefix(prefix))


def count_files(directory: Path) -> int:
    return sum(path.is_file() for path in directory.rglob("*")) if directory.exists() else 0


def copy_tree_and_count(source: Path, destination: Path) -> int:
    """Copy an upload tree and return the number of files copied successfully."""
    file_count = 0

    def copy_file(source_file: str, destination_file: str) -> str:
        nonlocal file_count
        copied_file = shutil.copy2(source_file, destination_file)
        file_count += 1
        return copied_file

    shutil.copytree(source, destination, copy_function=copy_file)
    return file_count


def check_integrity(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise RuntimeError(f"SQLite integrity check failed: {result}")


def create_backup(db_path: Path, upload_dir: Path, out_dir: Path) -> Path:
    """Back up a SQLite database and its upload tree, returning the backup directory."""
    db_path = Path(db_path)
    upload_dir = Path(upload_dir)
    out_dir = Path(out_dir)
    if not db_path.is_file():
        raise FileNotFoundError(f"Database file does not exist: {db_path}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_dir = out_dir / timestamp
    backup_dir.mkdir(parents=True, exist_ok=False)

    try:
        backup_db_path = backup_dir / db_path.name
        with sqlite3.connect(db_path) as source, sqlite3.connect(backup_db_path) as destination:
            source.backup(destination)
        check_integrity(backup_db_path)

        backup_upload_dir = backup_dir / "uploads"
        if upload_dir.exists():
            file_count = copy_tree_and_count(upload_dir, backup_upload_dir)
        else:
            backup_upload_dir.mkdir()
            file_count = 0

        manifest = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "db_source": str(db_path),
            "db_size_bytes": backup_db_path.stat().st_size,
            "upload_dir_source": str(upload_dir),
            "file_count": file_count,
            "sqlite_integrity_check": "ok",
        }
        (backup_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    except Exception:
        shutil.rmtree(backup_dir, ignore_errors=True)
        raise

    return backup_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Back up the CyberAssess SQLite database and uploads.")
    parser.add_argument("--out-dir", default="backups", help="Directory that will contain timestamped backups")
    args = parser.parse_args()

    try:
        backup_dir = create_backup(
            database_path(settings.database_url), Path(settings.upload_dir), Path(args.out_dir)
        )
    except Exception as exc:
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1

    print(backup_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
