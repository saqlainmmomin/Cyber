"""P1-3 rollback: restore the pre-migration backup that ``migrate_legacy.py`` made.

INTERFACE STUB ONLY — the body raises ``NotImplementedError``. Codex implements.

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

import argparse  # noqa: F401 - used by the implementation

from scripts.restore import restore_backup  # noqa: F401 - main() must call this

_NOT_IMPLEMENTED = "P1-3: implemented by Codex"


def main(argv: list[str] | None = None) -> int:
    """Restore ``--backup-dir`` over the live database and upload directory."""

    raise NotImplementedError(_NOT_IMPLEMENTED)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
