# Backup and restore

CyberAssess targets a 24-hour recovery point objective (RPO) and a four-hour recovery
time objective (RTO), per decision D9. Run a verified local backup nightly:

```cron
0 2 * * * cd /path/to/CyberAssess && python scripts/backup.py >> logs/backup.log 2>&1
```

This creates `backups/<timestamp>/` containing an online SQLite snapshot, a copy of the
uploads tree, and `manifest.json`. The backup command checks SQLite integrity before it
reports success.

To restore a chosen backup, first stop the application, then run:

```bash
python scripts/restore.py backups/20260922-143000/
```

Confirm the prompt, or add `--force` for an unattended recovery. Before any live data is
overwritten, restore moves the current database and uploads into a sibling
`pre-restore-<timestamp>/` safety copy. If restored SQLite integrity or upload file-count
verification fails, it automatically puts that safety copy back.
