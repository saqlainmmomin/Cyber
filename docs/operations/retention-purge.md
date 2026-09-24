# Retention, archive, and purge

CyberAssess follows D11: engagements are archived reversibly, retention is configurable per client, and permanent purge is manual only after retention and dependency checks.

## Archive and retention

Archive an engagement from its page. The engagement leaves the normal portfolio views, remains readable, and becomes read-only together with every assessment and evidence item beneath it. Unarchive restores its previous active or closed status. Retention is set on the client page from 1 to 50 years; an engagement keeps at least the period recorded when it was archived, so lowering the client setting cannot make an existing archive eligible sooner.

## Permanent purge

Open the engagement page and choose the permanent purge preview. The preview lists the rows and storage folders that will be deleted, retained records, and every refusal reason. Purge is available only after retention has elapsed, dependencies are clear, and storage paths are valid. Type the engagement name exactly, then confirm the browser prompt. The server repeats every check under its write lock; a preview is never trusted.

The purge has two phases:

1. All engagement rows are deleted and the `engagement.purged` audit event is committed in one transaction.
2. The storage folders are removed, then `engagement.purge_blobs_removed` is committed.

If the process fails before phase 1 commits, rows and files remain intact and the purge can be retried. If it fails after phase 1, the audit event is the ledger: the client page shows “Files pending removal”, and the remaining folders can be finished from the client page or with:

```bash
python scripts/complete_purges.py --list
python scripts/complete_purges.py
```

The completion route is `POST /api/engagements/{engagement_id}/purge/complete`. Completion is explicit and idempotent; it never starts automatically.

The client row and audit log are retained, including the purge record and the two existing free-text audit keys. Backups are not scrubbed or rotated. Restoring a backup made before a purge resurrects the engagement and removes the purge audit rows from the restored database. Take a verified backup before the first real purge.

The purge enables SQLite `secure_delete` for the purge connection, which removes deleted row content from the database pages. It does not erase rollback-journal blocks, filesystem remnants of deleted files, or older backups.

Never runs automatically.
