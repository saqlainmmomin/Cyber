#!/usr/bin/env python3
"""
Write Saqlain's criteria choices into criteria_map.csv as basis `decided`.

    python scripts/ucf/apply_rekey_decisions.py DECISIONS.json [--by NAME] [--on DATE] [--accept-remaining NOTE] [--data DIR]

DECISIONS.json is the review page export (tasks/2026-10-14-ucf-rekey-decisions.json):
`criteria` maps a criterion id to {status, unified_control_id, note}. `accept` and `change` rows become
`decided` with the chosen control. `flag` rows stay `proposed` and are listed. `--accept-remaining`
then marks every row still `proposed` as `decided` on its proposed control, with NOTE in the reason.
The chosen control must be one the criterion's record maps to. Scope choices are not handled here.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_criteria_map as cm  # noqa: E402
import validate  # noqa: E402

from app.frameworks.ucf.loader import load_library  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Apply re-key review decisions to criteria_map.csv.")
    ap.add_argument("decisions", help="review page JSON export")
    ap.add_argument("--by", default="Saqlain Momin")
    ap.add_argument("--on", default=datetime.date.today().isoformat())
    ap.add_argument("--accept-remaining", metavar="NOTE", help="also accept every remaining proposed row, noting NOTE")
    ap.add_argument("--data", default=str(validate.DEFAULT_DATA))
    args = ap.parse_args(argv)

    lib = load_library(args.data)
    path = Path(args.data) / "criteria_map.csv"
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    by_id = {r["criterion_id"]: r for r in rows}
    choices = json.loads(Path(args.decisions).read_text(encoding="utf-8")).get("criteria", {})

    stamp = f"{args.by} {args.on}"
    errors, flagged, applied = [], [], 0
    for cid, d in sorted(choices.items()):
        row = by_id.get(cid)
        if row is None:
            errors.append(f"{cid}: not in criteria_map.csv")
            continue
        if d.get("status") == "flag":
            flagged.append(f"{cid}: {d.get('note', '')}")
            continue
        if d.get("status") not in ("accept", "change"):
            continue
        ctl = d.get("unified_control_id", "")
        if ctl not in cm.candidates(lib, row["record_id"]):
            errors.append(f"{cid}: {ctl or '(empty)'} is not a control that {row['record_id']} maps to")
            continue
        verb = "kept proposal" if ctl == row["unified_control_id"] else f"changed from {row['unified_control_id']}"
        note = " ".join((d.get("note") or "").split())
        row.update(unified_control_id=ctl, basis="decided",
                   reason=f"decided by {stamp}: {verb}" + (f". {note}" if note else ""))
        applied += 1

    if errors:
        print("FAIL nothing written:")
        for e in errors:
            print(f"  {e}")
        return 1

    bulk = 0
    if args.accept_remaining:
        for row in rows:
            if row["basis"] == "proposed" and row["unified_control_id"] and row["criterion_id"] not in choices:
                row.update(basis="decided", reason=f"decided by {stamp}: {args.accept_remaining} (was: {row['reason']})")
                bulk += 1

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cm.COLUMNS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    left = sum(r["basis"] == "proposed" for r in rows)
    print(f"applied {applied} choices, accepted {bulk} remaining proposals; {left} rows still proposed")
    for f_ in flagged:
        print(f"  flagged, still proposed: {f_}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
