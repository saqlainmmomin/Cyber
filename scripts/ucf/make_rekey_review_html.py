#!/usr/bin/env python3
"""Build the single-file review page for the criteria and scope re-key.

    python3 scripts/ucf/make_rekey_review_html.py [--data DIR] [--out FILE]

Reads criteria_map.csv and scope_proposals.csv (run make_criteria_map.py and
make_scope_proposals.py first), the signed criteria and the library. Writes one
self-contained HTML file: a card per proposed criterion (choose its control), a
card per scope proposal (approve or change), the held-back scope cases, and the
question on the number of ISO scope questions. Choices are kept in the browser
and exported as JSON or Markdown. Stdlib only.
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
import make_criteria_map as cm  # noqa: E402  (also puts the repo root on sys.path)
import make_scope_proposals as sp  # noqa: E402
import validate  # noqa: E402

from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION  # noqa: E402
from app.frameworks.ucf.loader import Library, load_library  # noqa: E402

REVIEW_KEY = "ucf-rekey-review-1.0.0"
DEFAULT_OUT = validate.REPO_ROOT / "tasks" / "2026-10-14-ucf-rekey-review.html"
FW_ORDER = list(cm.CRITERIA)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def candidate(lib: Library, rid: str, cid: str, prim: str) -> dict:
    c = lib.controls[cid]
    asks = []
    for row in lib.rows_by_record.get(rid, []):
        if row.unified_control_id == cid and row.coverage in ("full", "partial"):
            atom = lib.atoms.get(row.atom_id)
            asks.append(f"{row.atom_id[len(rid) + 1:]}: {atom.paraphrase if atom else ''} ({row.coverage})")
    return {"id": cid, "title": c.title, "statement": c.statement, "asks": asks, "primary": cid == prim}


def build(data_dir: Path) -> dict:
    lib = load_library(data_dir)
    cmap = {r["criterion_id"]: r for r in read_csv(data_dir / "criteria_map.csv")}
    tcs = {tc.id: tc for m in cm.CRITERIA.values() for crits in m.values() for tc in crits}

    records = []
    for fw in FW_ORDER:
        for rid, crits in cm.CRITERIA[fw].items():
            open_rows = [cmap[tc.id] for tc in crits if cmap[tc.id]["basis"] == "proposed"]
            if not open_rows:
                continue
            rec = lib.records[rid]
            prim = cm.primary_control(lib, rid)
            records.append({
                "id": rid, "fw": fw, "ref": rec.reference, "title": rec.title,
                "cands": [candidate(lib, rid, c, prim) for c in cm.candidates(lib, rid)],
                "crits": [{"id": r["criterion_id"], "stmt": tcs[r["criterion_id"]].statement,
                           "kind": tcs[r["criterion_id"]].kind, "hint": tcs[r["criterion_id"]].evidence_hint,
                           "prop": r["unified_control_id"], "reason": r["reason"]} for r in open_rows],
            })

    counts = []
    for fw in FW_ORDER:
        rows = [r for r in cmap.values() if r["record_id"] in cm.CRITERIA[fw]]
        counts.append({"fw": fw, "total": len(rows), "auto": sum(r["basis"] == "auto" for r in rows),
                       "proposed": sum(r["basis"] == "proposed" for r in rows),
                       "decided": sum(r["basis"] == "decided" for r in rows)})
    per = {}
    for r in cmap.values():
        per[r["unified_control_id"]] = per.get(r["unified_control_id"], 0) + 1
    zero = [{"id": c, "title": lib.controls[c].title} for c in sorted(lib.controls) if not per.get(c)]

    labels = {(q.id, o["value"]): o["label"].replace(" \u2014 ", ": ")
              for q in ISO27001_DEFINITION.scope_questions for o in q.options}
    questions = [{"id": q.id, "q": q.question, "options": [labels[(q.id, o["value"])] for o in q.options]}
                 for q in ISO27001_DEFINITION.scope_questions]
    scope = [{"key": f"{r['question']}={r['answer']}:{r['unified_control_id']}", "q": r["question"],
              "answer": labels.get((r["question"], r["answer"]), r["answer"]), "cid": r["unified_control_id"],
              "title": lib.controls[r["unified_control_id"]].title,
              "statement": lib.controls[r["unified_control_id"]].statement,
              "src": r["source_records"], "reason": r["reason"]}
             for r in read_csv(data_dir / "scope_proposals.csv")]
    held = []
    for p in ISO27001_DEFINITION.applicability_proposals:
        for answer in p.answers:
            for rid in p.control_ids:
                for cid in sorted(lib.controls_of_record.get(rid, set())):
                    block = sp.blockers(lib, cid, set(p.control_ids))
                    if block:
                        held.append({"q": p.scope_question_id, "answer": labels.get((p.scope_question_id, answer), answer),
                                     "cid": cid, "title": lib.controls[cid].title, "via": sp.short(rid), "block": block})

    return {
        "reviewKey": REVIEW_KEY, "version": lib.library_version,
        "date": datetime.date.today().isoformat(),
        "counts": counts, "records": records, "zero": zero,
        "questions": questions, "scope": scope, "held": held,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the re-key review page.")
    ap.add_argument("--data", default=str(validate.DEFAULT_DATA))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)
    data = build(Path(args.data))
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028")
    html = (HERE / "rekey_review_template.html").read_text(encoding="utf-8").replace("/*__DATA__*/null", blob)
    Path(args.out).write_text(html, encoding="utf-8")
    n = sum(len(r["crits"]) for r in data["records"])
    print(f"wrote {args.out}: {n} criteria in {len(data['records'])} records, {len(data['scope'])} scope proposals, "
          f"{len(data['held'])} held-back cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
