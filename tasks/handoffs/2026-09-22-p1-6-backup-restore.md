# P1-6: Backup/restore script

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 1, task P1-6.
**Owner:** Codex.
**Depends on:** nothing — no dependency on P1-1 through P1-5. Start immediately.
**Blocks:** nothing in Phase 1. (Phase 2 will extend this to also cover the `evidence` blob directory once P2-1 introduces it — out of scope here.)

## Goal

Two scripts: `scripts/backup.py` copies the SQLite database file and the document-upload directory into a timestamped backup folder; `scripts/restore.py` restores both from a chosen backup and verifies integrity before declaring success. This exists so that Phase 1's schema migration (P1-1/P1-2/P1-3) has a tested rollback path, and so the 24h RPO / 4h RTO target (decision D9 in `tasks/2026-09-21-adversarial-review.md`) is demonstrably achievable, not just documented.

## Current state

- Database: SQLite file at the path in `settings.database_url` (`sqlite:///data/dpdpa.db` by default — parse the path out of the URL, don't hardcode `data/dpdpa.db`).
- Uploaded documents: `settings.upload_dir` (default `uploads/`), with one subdirectory per `assessment_id` (see `app/services/document_processor.py:32`, `dest_dir = os.path.join(settings.upload_dir, assessment_id)`).
- No backup/restore tooling exists today. `scripts/detect_orphans.py` is the closest existing example of a standalone operational script in this repo — match its style (plain functions, `if __name__ == "__main__":` entry point, imports `app.config.settings`, no framework/CLI library beyond stdlib `argparse`).
- No `backups/` directory or convention exists yet — create one, gitignored.

## Required approach

### `scripts/backup.py`

1. Read the DB file path from `settings.database_url` (strip the `sqlite:///` prefix; handle both relative and absolute forms — the existing codebase only uses the relative default, but don't assume that).
2. Create a timestamped backup directory: `backups/<YYYYMMDD-HHMMSS>/`.
3. Copy the DB file into it using SQLite's **online backup API** (`sqlite3.Connection.backup()` via a raw `sqlite3.connect()`, or equivalent through SQLAlchemy's raw connection), not a plain file copy — a plain `shutil.copy` on a live SQLite file can capture a mid-write, inconsistent state. If the app is not expected to be running concurrently during backup, a plain copy is acceptable but must still open the source with a read lock check first (e.g., attempt `PRAGMA quick_check` after copy) — prefer the online backup API since it handles both cases correctly with minimal extra code.
4. Recursively copy the entire `upload_dir` tree into `backups/<timestamp>/uploads/`.
5. After copying, run `PRAGMA integrity_check` (or `quick_check` for speed) against the **copied** DB file and abort with a non-zero exit code and clear stderr message if it fails — never leave a backup directory that looks complete but contains a corrupt DB.
6. Write a small `manifest.json` into the backup directory: `{"created_at": ISO8601, "db_source": <path>, "db_size_bytes": int, "upload_dir_source": <path>, "file_count": int, "sqlite_integrity_check": "ok"}`. This is what `restore.py` reads back and what a human checks without opening the DB.
7. Print the backup directory path on success. Exit non-zero on any failure (missing source DB, disk full, integrity check failure) — never partially write and report success.
8. Accept an optional `--out-dir` argument (default `backups/`) so tests can point it at a scratch directory.

### `scripts/restore.py`

1. Accept a required positional argument: the backup directory to restore from (e.g., `backups/20260922-143000/`).
2. Validate `manifest.json` exists and `sqlite_integrity_check == "ok"` before touching anything live — refuse to restore from a backup that failed its own integrity check at creation time.
3. Before overwriting the live DB or upload directory, move the *current* live DB and upload dir aside to a `pre-restore-<timestamp>/` safety copy (do not delete them) — a bad restore should never destroy the only remaining good copy.
4. Copy the backup's DB file into the live DB path, copy the backup's `uploads/` tree into the live `upload_dir` path.
5. Run `PRAGMA integrity_check` against the now-live DB and verify the file count under the restored upload dir matches `manifest.json`'s `file_count`. If either check fails, abort, restore the `pre-restore-<timestamp>/` safety copy back into place, and exit non-zero — never leave the app pointing at a DB that failed its own restore's verification.
6. Print a summary (what was restored from, what the pre-restore safety copy path is) on success.
7. Accept `--force` to skip an interactive confirmation prompt (for test/CI use); without it, prompt for confirmation before overwriting the live DB, since this is a destructive operation on whatever is currently running.

### Documentation

Add a short section to `AGENTS.md`/`CLAUDE.md` (or a new `docs/operations/backup-restore.md` if either file would exceed the ≤250-word cap in `CLAUDE.md`'s own contract — prefer the new file) covering:
- The 24h RPO / 4h RTO target from decision D9.
- A `cron` example for a nightly `python scripts/backup.py` run with basic log redirection.
- How to run `scripts/restore.py` manually, including the `pre-restore-*` safety-copy behavior.

## Key files

| File | Why it matters |
|---|---|
| `app/config.py` | `settings.database_url`, `settings.upload_dir` — the two things being backed up. |
| `scripts/detect_orphans.py` | Style/convention reference for a standalone operational script in this repo. |
| `app/services/document_processor.py:32` | Confirms the on-disk layout of `upload_dir` (one subdirectory per assessment id). |
| `.gitignore` | Add `backups/` so backup artifacts never get committed. |
| `AGENTS.md`, `CLAUDE.md` | Where to add the operations doc pointer (or create `docs/operations/backup-restore.md` if the word budget doesn't fit). |

## Non-goals

- Do NOT back up or restore the `evidence`/`evidence_versions` blob storage from Phase 2 — that table doesn't exist yet; this task covers only the current `AssessmentDocument`/`upload_dir` model.
- Do NOT implement automatic scheduling (cron/systemd timer installation) — document the cron line, don't install it.
- Do NOT implement remote/offsite backup (S3, etc.) — local `backups/` directory only, per the plan's scope for P1-6.
- Do NOT touch `app/main.py`, models, or any route — this is a standalone ops script, fully decoupled from the running app.

## Test to pass

Add `tests/test_backup_restore.py`:
1. Seed a small SQLite DB (via existing test fixtures/conftest patterns) with at least one assessment row, plus a fake `uploads/<assessment_id>/file.txt`.
2. Run `backup.py` (import and call its functions directly, or invoke as a subprocess against a temp dir via `--out-dir`) — assert the backup directory contains the DB copy, the uploads copy, and a `manifest.json` with `sqlite_integrity_check: "ok"`.
3. Mutate the live DB (e.g., insert another row) and delete a file from `uploads/`.
4. Run `restore.py --force` pointed at the backup directory — assert the live DB no longer has the mutation (matches pre-mutation state) and the deleted upload file is back.
5. Assert a `pre-restore-*` safety-copy directory was created containing the mutated (pre-restore) state.
6. Negative test: hand-craft a backup directory with a `manifest.json` claiming `sqlite_integrity_check: "corrupt"` (or a genuinely corrupted DB file) and assert `restore.py` refuses to proceed and exits non-zero without touching the live DB.

## Done criteria

- `python scripts/backup.py` run against the current dev DB produces a `backups/<timestamp>/` directory with `dpdpa.db`, a mirrored `uploads/` tree, and a valid `manifest.json`.
- `python scripts/restore.py backups/<timestamp>/ --force` round-trips cleanly: DB and uploads match what was backed up, verified by the integrity check and file-count check described above.
- The corrupt-manifest negative test passes — restore refuses and leaves the live DB untouched.
- `pytest -q` passes including the new `tests/test_backup_restore.py`.
- `backups/` is gitignored.

## Rollback

This task adds new standalone scripts and one new test file; nothing existing is modified except `.gitignore` and (optionally) `AGENTS.md`/`CLAUDE.md`. `git revert` the commit if it fails review — no schema or route impact to unwind.

## Report back

Append a `## Results` section to this file: sample `manifest.json` output, `pytest -q` output for the new test file, and the exact backup/restore command lines a human would run in production.

## Results

Implemented `scripts/backup.py` and `scripts/restore.py`, with `backups/` gitignored and
operations guidance in `docs/operations/backup-restore.md`. Backups use SQLite's online backup
API, copy the uploads tree, and write a verified manifest. Restore rejects invalid manifests,
moves existing live data to a sibling `pre-restore-<timestamp>/` safety copy, and automatically
rolls it back if post-restore integrity or upload-count verification fails.

Focused verification:

```text
$ pytest -q tests/test_backup_restore.py
....                                                                     [100%]
4 passed
```

CLI smoke backup against the current development database produced:

```json
{
  "created_at": "2026-09-22T05:28:17.521341+00:00",
  "db_source": "data/dpdpa.db",
  "db_size_bytes": 1740800,
  "upload_dir_source": "uploads",
  "file_count": 10,
  "sqlite_integrity_check": "ok"
}
```

The full `pytest -q` suite could not collect because separately untracked Alembic migration
work imports `alembic.command`, but Alembic is not installed in the active environment. The
focused backup/restore tests, CLI `--help` checks, and `py_compile` all pass.

Production commands (stop the application before restore):

```bash
python scripts/backup.py
python scripts/restore.py backups/<YYYYMMDD-HHMMSS>/
# For unattended recovery only:
python scripts/restore.py backups/<YYYYMMDD-HHMMSS>/ --force
```
