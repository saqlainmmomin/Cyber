"""P1-3 rollback: restore the pre-migration backup that ``migrate_legacy.py`` made.

This is deliberately thin: it is a CLI wrapper around
``scripts.restore.restore_backup(backup_dir, db_path, upload_dir, *, force=False)``.
It adds no restore logic of its own — ``restore.py`` already takes the
pre-restore safety copy and verifies the backup manifest.

Usage::

    python scripts/rollback_legacy.py --backup-dir backups/20260922-101500-123456

Flags: ``--backup-dir`` (required), ``--db-url``, ``--upload-dir``, ``--force``
(skip the interactive confirmation ``restore_backup`` otherwise prompts for).

Returns 0 on a successful restore, non-zero if ``restore_backup`` raises.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from scripts.backup import database_path
from scripts.restore import restore_backup

def main(argv: list[str] | None = None) -> int:
    """Restore ``--backup-dir`` over the live database and upload directory."""

    parser = argparse.ArgumentParser(description="Roll back a CyberAssess migration.")
    parser.add_argument("--backup-dir", required=True)
    parser.add_argument("--db-url", default=settings.database_url)
    parser.add_argument("--upload-dir", default=settings.upload_dir)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    try:
        safety_dir = restore_backup(
            Path(args.backup_dir),
            database_path(args.db_url),
            Path(args.upload_dir),
            force=args.force,
        )
    except Exception as exc:
        print(f"Rollback failed: {exc}", file=sys.stderr)
        return 1

    print(f"Restored {args.backup_dir}; pre-restore safety copy: {safety_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
