"""Regression coverage for the operational SQLite and upload backup scripts."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import app.models  # noqa: F401 - register ORM tables
import pytest
from sqlalchemy import create_engine

from app.database import Base
from app.models import Assessment
import scripts.backup as backup_script
from scripts.backup import create_backup, database_path
from scripts.restore import restore_backup
import scripts.restore as restore_script


def _seed_database(db_path: Path) -> None:
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            Assessment.__table__.insert(),
            {
                "id": "assessment-1",
                "company_name": "Backup Co",
                "industry": "Technology",
                "company_size": "small",
                "status": "created",
            },
        )
    engine.dispose()


def _company_name(db_path: Path) -> str:
    with sqlite3.connect(db_path) as connection:
        return connection.execute("SELECT company_name FROM assessments").fetchone()[0]


def test_database_path_handles_relative_and_absolute_sqlite_urls():
    assert database_path("sqlite:///data/dpdpa.db") == Path("data/dpdpa.db")
    assert database_path("sqlite:////tmp/cyberassess.db") == Path("/tmp/cyberassess.db")


def test_backup_and_restore_round_trip_preserves_database_and_uploads(tmp_path):
    db_path = tmp_path / "live.db"
    upload_dir = tmp_path / "uploads"
    upload_file = upload_dir / "assessment-1" / "file.txt"
    upload_file.parent.mkdir(parents=True)
    upload_file.write_text("original evidence")
    _seed_database(db_path)

    backup_dir = create_backup(db_path, upload_dir, tmp_path / "backups")

    manifest = json.loads((backup_dir / "manifest.json").read_text())
    assert (backup_dir / db_path.name).is_file()
    assert (backup_dir / "uploads" / "assessment-1" / "file.txt").read_text() == "original evidence"
    assert manifest["sqlite_integrity_check"] == "ok"
    assert manifest["file_count"] == 1

    with sqlite3.connect(db_path) as connection:
        connection.execute("UPDATE assessments SET company_name = 'Mutated Co'")
        connection.commit()
    upload_file.unlink()

    safety_dir = restore_backup(backup_dir, db_path, upload_dir, force=True)

    assert _company_name(db_path) == "Backup Co"
    assert upload_file.read_text() == "original evidence"
    assert (safety_dir / db_path.name).is_file()
    assert _company_name(safety_dir / db_path.name) == "Mutated Co"


def test_backup_runs_in_the_same_second_create_distinct_directories(tmp_path, monkeypatch):
    db_path = tmp_path / "live.db"
    _seed_database(db_path)

    class FixedDatetime:
        values = [
            datetime(2026, 1, 1, 0, 0, 0, 100),
            datetime(2026, 1, 1, 0, 0, 0, 100),
            datetime(2026, 1, 1, 0, 0, 0, 200),
            datetime(2026, 1, 1, 0, 0, 0, 200),
        ]

        @classmethod
        def now(cls, tz=None):
            return cls.values.pop(0)

    monkeypatch.setattr(backup_script, "datetime", FixedDatetime)

    first_backup = create_backup(db_path, tmp_path / "uploads", tmp_path / "backups")
    second_backup = create_backup(db_path, tmp_path / "uploads", tmp_path / "backups")

    assert first_backup != second_backup
    assert first_backup.is_dir()
    assert second_backup.is_dir()


def test_restore_rejects_a_backup_that_failed_integrity_check(tmp_path):
    db_path = tmp_path / "live.db"
    upload_dir = tmp_path / "uploads"
    _seed_database(db_path)
    backup_dir = tmp_path / "invalid-backup"
    backup_dir.mkdir()
    (backup_dir / "manifest.json").write_text(json.dumps({"sqlite_integrity_check": "corrupt"}))

    with pytest.raises(ValueError, match="integrity"):
        restore_backup(backup_dir, db_path, upload_dir, force=True)

    assert _company_name(db_path) == "Backup Co"


def test_restore_rolls_back_when_the_restored_database_fails_integrity(tmp_path, monkeypatch):
    db_path = tmp_path / "live.db"
    upload_dir = tmp_path / "uploads"
    upload_file = upload_dir / "assessment-1" / "file.txt"
    upload_file.parent.mkdir(parents=True)
    upload_file.write_text("original evidence")
    _seed_database(db_path)
    backup_dir = create_backup(db_path, upload_dir, tmp_path / "backups")

    with sqlite3.connect(db_path) as connection:
        connection.execute("UPDATE assessments SET company_name = 'Mutated Co'")
        connection.commit()
    upload_file.write_text("mutated evidence")

    real_check_integrity = restore_script.check_integrity
    checks = 0

    def fail_after_backup_validation(path):
        nonlocal checks
        checks += 1
        if checks == 2:
            raise RuntimeError("simulated post-restore integrity failure")
        real_check_integrity(path)

    monkeypatch.setattr(restore_script, "check_integrity", fail_after_backup_validation)

    with pytest.raises(RuntimeError, match="simulated post-restore"):
        restore_backup(backup_dir, db_path, upload_dir, force=True)

    assert _company_name(db_path) == "Mutated Co"
    assert upload_file.read_text() == "mutated evidence"


def test_restore_preserves_live_data_when_database_safety_copy_fails_partway(tmp_path, monkeypatch):
    db_path = tmp_path / "live.db"
    upload_dir = tmp_path / "uploads"
    upload_file = upload_dir / "assessment-1" / "file.txt"
    upload_file.parent.mkdir(parents=True)
    upload_file.write_text("mutated evidence")
    _seed_database(db_path)
    backup_dir = create_backup(db_path, upload_dir, tmp_path / "backups")

    with sqlite3.connect(db_path) as connection:
        connection.execute("UPDATE assessments SET company_name = 'Mutated Co'")
        connection.commit()

    real_copy2 = restore_script.shutil.copy2

    def fail_during_safety_copy(source, destination, *args, **kwargs):
        if Path(source) == db_path and Path(destination).parent.name.startswith("pre-restore-"):
            Path(destination).write_bytes(b"partial safety copy")
            raise OSError("simulated disk-full failure")
        return real_copy2(source, destination, *args, **kwargs)

    monkeypatch.setattr(restore_script.shutil, "copy2", fail_during_safety_copy)

    with pytest.raises(OSError, match="disk-full"):
        restore_backup(backup_dir, db_path, upload_dir, force=True)

    assert _company_name(db_path) == "Mutated Co"
    assert upload_file.read_text() == "mutated evidence"
