"""Finish engagement purges whose database phase committed before file removal."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.services import retention


def run(db, *, list_only: bool = False, out=sys.stdout) -> int:
    pending = retention.pending_purges(db)
    for item in pending:
        print(
            f"PENDING {item.engagement_id} {item.purged_at.isoformat()} roots={len(item.blob_roots)}",
            file=out,
        )
    if list_only:
        return 0
    failed = False
    for item in pending:
        try:
            outcome = retention.complete_pending_purge(
                db,
                engagement_id=item.engagement_id,
                actor=retention.COMPLETION_SCRIPT_ACTOR,
            )
        except retention.RetentionError as exc:
            failed = True
            print(f"FAILED {item.engagement_id} {exc.message}", file=out)
            continue
        print(
            f"COMPLETED {item.engagement_id} removed={len(outcome.removed_roots)} missing={len(outcome.missing_roots)}",
            file=out,
        )
    return 1 if failed else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Complete committed engagement purges whose stored files remain."
    )
    parser.add_argument("--list", action="store_true", help="List pending purges without completing them")
    args = parser.parse_args(argv)
    db = SessionLocal()
    try:
        return run(db, list_only=args.list)
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
