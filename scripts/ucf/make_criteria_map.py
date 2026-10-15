#!/usr/bin/env python3
"""
Draft the criteria-to-control map: every signed test criterion attached to one unified control.

    python scripts/ucf/make_criteria_map.py [--data DIR]

Reads the signed criteria modules (app/frameworks/criteria/{iso27001,nist_csf,dpdpa}.py) and the
library mappings. Writes <data>/criteria_map.csv (columns in FORMAT.md):

- auto: the criterion's record maps (full or partial) to one control.
- proposed: the record maps to two or more controls. The script picks the candidate whose mapped
  atoms and text share the most distinctive words with the criterion, and says why. Saqlain decides.
- decided: kept as is from an existing criteria_map.csv. Never overwritten by a re-run.

Prints counts per framework and the number of criteria per control (controls with none are gaps).
Word matching only: no LLM calls.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate  # noqa: E402  (also puts the repo root on sys.path)

from app.frameworks.criteria.dpdpa import DPDPA_CRITERIA  # noqa: E402
from app.frameworks.criteria.iso27001 import ISO27001_CRITERIA  # noqa: E402
from app.frameworks.criteria.nist_csf import NIST_CSF_CRITERIA  # noqa: E402
from app.frameworks.ucf.loader import Library, load_library  # noqa: E402

CRITERIA = {"iso27001": ISO27001_CRITERIA, "nist_csf": NIST_CSF_CRITERIA, "dpdpa": DPDPA_CRITERIA}
COLUMNS = ("criterion_id", "record_id", "unified_control_id", "basis", "reason")
CLOSE_CALL = 0.15  # second-best within 15% of best: say so in the reason
WEAK = 3  # fewer shared words than this: say the match is weak

STOP = set("""a an and are as at be been by can each for from has have if in into is it its of on or
other such that the their them there these they this to was were when where which who with within
without e g eg i ie per all any are any not no one two least must should shall may also only both
than then those whether including include includes included""".split())


def stem(word: str) -> str:
    for suf in ("ations", "ation", "ings", "ing", "ies", "ied", "ed", "es", "s"):
        if len(word) > len(suf) + 3 and word.endswith(suf):
            return word[: -len(suf)] + ("y" if suf in ("ies", "ied") else "")
    return word


def words(text: str) -> set[str]:
    return {stem(w) for w in re.findall(r"[a-z][a-z0-9-]+", text.lower()) if w not in STOP and len(w) > 2}


def control_text(lib: Library, cid: str) -> str:
    c = lib.controls[cid]
    return " ".join((c.title, c.goal, c.statement, c.test, c.good_looks_like))


class Scorer:
    """IDF-weighted word overlap. Atoms of the record mapped to a control count double."""

    def __init__(self, lib: Library):
        docs = [words(control_text(lib, cid)) for cid in lib.controls]
        docs += [words(a.paraphrase) for a in lib.atoms.values()]
        df = Counter(w for d in docs for w in d)
        self.idf = {w: math.log(len(docs) / n) for w, n in df.items()}
        self.lib = lib

    def overlap(self, crit: set[str], other: set[str]) -> tuple[float, list[str]]:
        shared = crit & other
        return sum(self.idf.get(w, 1.0) for w in shared), sorted(shared, key=lambda w: -self.idf.get(w, 1.0))

    def score(self, crit_text: str, rid: str, cid: str) -> tuple[float, str, list[str]]:
        crit = words(crit_text)
        best_atom, best_atom_score, atom_words = "", 0.0, []
        for row in self.lib.rows_by_record.get(rid, []):
            if row.unified_control_id != cid or row.coverage not in ("full", "partial"):
                continue
            atom = self.lib.atoms.get(row.atom_id)
            if not atom:
                continue
            s, w = self.overlap(crit, words(atom.paraphrase))
            if s > best_atom_score:
                best_atom, best_atom_score, atom_words = row.atom_id, s, w
        ctl_score, ctl_words = self.overlap(crit, words(control_text(self.lib, cid)))
        return 2 * best_atom_score + ctl_score, best_atom, (atom_words + [w for w in ctl_words if w not in atom_words])


def primary_control(lib: Library, rid: str) -> str:
    return next((r.unified_control_id for r in lib.rows_by_record.get(rid, []) if r.primary), "")


def candidates(lib: Library, rid: str) -> list[str]:
    return sorted(lib.controls_of_record.get(rid, set()))


def load_decided(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {r["criterion_id"]: r for r in csv.DictReader(f) if r.get("basis") == "decided"}


def build(lib: Library, decided: dict[str, dict]) -> list[dict]:
    scorer = Scorer(lib)
    rows: list[dict] = []
    for fw, crit_map in CRITERIA.items():
        for rid, crits in crit_map.items():
            cands = candidates(lib, rid)
            for tc in crits:
                if tc.id in decided:
                    rows.append({k: decided[tc.id][k] for k in COLUMNS})
                    continue
                row = {"criterion_id": tc.id, "record_id": rid}
                if not cands:
                    row.update(unified_control_id="", basis="proposed", reason="record maps to no control; needs a home")
                elif len(cands) == 1:
                    row.update(unified_control_id=cands[0], basis="auto", reason="record maps to one control")
                else:
                    text = f"{tc.statement} {tc.evidence_hint}"
                    prim = primary_control(lib, rid)
                    scored = sorted(
                        ((*scorer.score(text, rid, c), c) for c in cands),
                        key=lambda t: (-t[0], t[3] != prim, t[3]),
                    )
                    best, atom, shared, cid = scored[0]
                    second = scored[1][0]
                    if best == 0:
                        reason = "no word match; defaulted to the record's primary control"
                        cid = prim or cid
                    else:
                        via = f"atom {atom}" if atom else "control text"
                        reason = f"best word match via {via} ({', '.join(shared[:4])})"
                        if len(shared) < WEAK:
                            reason += "; weak match"
                        if second >= best * (1 - CLOSE_CALL):
                            reason += f"; close call with {scored[1][3]}"
                    row.update(unified_control_id=cid, basis="proposed", reason=reason)
                rows.append(row)
    return rows


def framework_of(rid: str) -> str:
    return next(fw for fw, m in CRITERIA.items() if rid in m)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Draft the criteria-to-control map.")
    ap.add_argument("--data", default=str(validate.DEFAULT_DATA), help="data folder (default docs/ucf/drafts)")
    args = ap.parse_args(argv)

    lib = load_library(args.data)
    for err in lib.load_errors:
        print(f"WARN {err}")
    out = Path(args.data) / "criteria_map.csv"
    rows = build(lib, load_decided(out))

    unknown = sorted({r["record_id"] for r in rows if r["record_id"] not in lib.records})
    ids = [r["criterion_id"] for r in rows]
    dupes = sorted(i for i, n in Counter(ids).items() if n > 1)
    if unknown or dupes:
        print(f"FAIL records not in library: {unknown}; duplicate criterion ids: {dupes}")
        return 1

    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}")

    print("\nframework     criteria  auto  proposed  decided  records  multi-control records  no-control records")
    for fw, crit_map in CRITERIA.items():
        fr = [r for r in rows if framework_of(r["record_id"]) == fw]
        b = Counter(r["basis"] for r in fr)
        multi = sum(1 for rid in crit_map if len(candidates(lib, rid)) > 1)
        none = sum(1 for rid in crit_map if not candidates(lib, rid))
        print(f"{fw:<13} {len(fr):>8}  {b['auto']:>4}  {b['proposed']:>8}  {b['decided']:>7}  {len(crit_map):>7}  "
              f"{multi:>21}  {none:>18}")
    print(f"{'total':<13} {len(rows):>8}  {sum(r['basis'] == 'auto' for r in rows):>4}  "
          f"{sum(r['basis'] == 'proposed' for r in rows):>8}  {sum(r['basis'] == 'decided' for r in rows):>7}")
    close = sum("close call" in r["reason"] for r in rows)
    weak = sum("weak match" in r["reason"] or "no word match" in r["reason"] for r in rows)
    print(f"proposed rows marked close call: {close}; weak or no match: {weak}")

    per = Counter(r["unified_control_id"] for r in rows if r["unified_control_id"])
    zero = sorted(c for c in lib.controls if per[c] == 0)
    reach = {c for rid in (rid for m in CRITERIA.values() for rid in m) for c in candidates(lib, rid)}
    print(f"\ncriteria per control: {len(lib.controls) - len(zero)} controls have criteria, {len(zero)} have none")
    for c in zero:
        why = "candidate on a criteria record, but no criterion chosen" if c in reach else "no mapped record has criteria"
        print(f"  {c}  {lib.controls[c].title}  ({why})")
    print("\ncontrols by criteria count:", dict(sorted(Counter(per[c] for c in lib.controls).items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
