#!/usr/bin/env python3
"""
Write the UCF sign-off tables: one markdown file per master domain plus an index.

    python scripts/ucf/make_signoff.py [--data DIR] [--out DIR]

Reads docs/ucf/drafts (or --data) with the library loader, writes docs/ucf/signoff
(or --out). Counting comes from validate.py (subset_counts), not a second copy.
Generated files (<CODE>.md, <CODE>-<n>.md, README.md) in the output folder are
replaced on every run.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate  # noqa: E402  (also puts the repo root on sys.path)

from app.frameworks.ucf.loader import Library, load_library  # noqa: E402
from app.frameworks.ucf.schema import FRAMEWORKS, Control  # noqa: E402

DEFAULT_OUT = validate.REPO_ROOT / "docs" / "ucf" / "signoff"
SPLIT_OVER = 18
CHUNK = 15
FW_LABEL = {"iso27001": "ISO", "nist_csf": "NIST", "dpdpa": "DPDPA"}
FW_LONG = {"iso27001": "ISO 27001", "nist_csf": "NIST CSF", "dpdpa": "DPDPA"}
GENERATED_RE = re.compile(r"^(?:[A-Z]{3}(?:-\d+)?|README)\.md$")
NO_FIELDS = "(fields not yet written)"


def cell(text: str) -> str:
    """Make text safe for one markdown table cell."""
    return text.replace("|", "\\|").replace("\r\n", "\n").replace("\n", "<br>").strip()


def short_ref(ref: str) -> str:
    ref = re.sub(r"^Annex\s+", "", ref.strip())
    return re.sub(r"^Sections?\s+", "s.", ref)


def sources_cell(lib: Library, cid: str) -> str:
    """One line per source framework, built from the mapping rows that point at the control."""
    groups: dict[tuple, list] = {}
    for row in lib.rows_by_control.get(cid, []):
        key = (FRAMEWORKS.index(row.source_framework) if row.source_framework in FRAMEWORKS else 99,
               row.source_framework, row.record_id, row.source_ref, row.coverage, row.remainder_of)
        groups.setdefault(key, []).append(row)
    lines: dict[str, list[str]] = {}
    for key in sorted(groups):
        _, fw, rid, ref, cov, rem = key
        rows = groups[key]
        n_atoms = len(lib.atoms_by_record.get(rid, []))
        label = short_ref(ref)
        if n_atoms > 1 and len({r.atom_id for r in rows}) < n_atoms:
            suffixes = sorted(r.atom_id[len(rid) + 1:] if r.atom_id.startswith(rid + "-") else r.atom_id for r in rows)
            label = f"{label}-{','.join(suffixes)}"
        note = f"{cov}, remainder of {rem}" if rem else cov
        lines.setdefault(fw, []).append(f"{label} ({note})")
    return "<br>".join(f"{FW_LABEL.get(fw, fw)}: {'; '.join(items)}" for fw, items in lines.items()) or "(no mapping row)"


def control_row(lib: Library, c: Control) -> str:
    statement = c.statement if c.has_fields and c.statement else NO_FIELDS
    owner = [c.owner_role or "(no owner)", (c.importance or "").lower()]
    if c.iso_theme:
        owner.append(c.iso_theme)
    cells = [
        c.id,
        f"**{cell(c.title)}**<br>{cell(statement)}",
        cell("\n".join(x for x in owner if x)),
        cell(c.test),
        cell(c.expected_evidence),
        sources_cell(lib, c.id),  # already uses <br>
        cell(c.note),
        "[ ]",
    ]
    return "| " + " | ".join(cells) + " |"


def shown_by_framework(lib: Library) -> dict[str, set[str]]:
    return {fw: lib.shown_controls(frozenset({fw})) for fw in FRAMEWORKS}


def split_counts(ids: list[str], shown: dict[str, set[str]]) -> dict[str, int]:
    out = {"total": len(ids), "unmapped": 0, "shared": 0}
    for fw in FRAMEWORKS:
        out[fw] = sum(1 for i in ids if i in shown[fw])
        out[fw + "_only"] = 0
    for i in ids:
        member = [fw for fw in FRAMEWORKS if i in shown[fw]]
        if not member:
            out["unmapped"] += 1
        elif len(member) == 1:
            out[member[0] + "_only"] += 1
        else:
            out["shared"] += 1
    return out


def chunks(items: list[str]) -> list[list[str]]:
    if len(items) <= SPLIT_OVER:
        return [items]
    n_files = math.ceil(len(items) / CHUNK)
    size = math.ceil(len(items) / n_files)
    return [items[i:i + size] for i in range(0, len(items), size)]


def domain_page(lib: Library, code: str, ids: list[str], shown: dict[str, set[str]], part: str) -> str:
    dom = lib.domains.get(code)
    name = dom.name if dom else f"{code} (domain not in domains.csv)"
    owner = dom.owner_role if dom else "unknown"
    k = split_counts(ids, shown)
    out = [
        f"# {name}{part}",
        "",
        f"Owner role: {owner}. Domain code: {code}.",
        "",
        f"{k['total']} controls. Shown with ISO 27001: {k['iso27001']}. Shown with NIST CSF: {k['nist_csf']}. "
        f"Shown with DPDPA: {k['dpdpa']}. Shared by two or more frameworks: {k['shared']}."
        + (f" Not yet mapped to any source: {k['unmapped']}." if k["unmapped"] else ""),
        "",
        "This table is a draft for sign-off. Tick the Sign cell once you have read the control, its test and its sources. "
        f"Library version {lib.library_version or 'unknown'}.",
        "",
        "| ID | Control | Owner and importance | Test | Expected evidence | Sources | Note | Sign |",
        "|---|---|---|---|---|---|---|---|",
    ]
    out += [control_row(lib, lib.controls[i]) for i in ids]
    return "\n".join(out) + "\n"


def readme(lib: Library, index: list[dict], shown: dict[str, set[str]]) -> str:
    out = [
        "# UCF sign-off tables",
        "",
        f"Draft for sign-off. Library version {lib.library_version or 'unknown'}. Generated by scripts/ucf/make_signoff.py; do not edit by hand.",
        "",
        "## Domains",
        "",
    ]
    if not index:
        out += ["No controls yet.", ""]
    else:
        out += ["| Domain | File | Controls | ISO only | NIST only | DPDPA only | Shared |", "|---|---|---|---|---|---|---|"]
        for row in index:
            k = row["counts"]
            files = ", ".join(f"[{f}]({f})" for f in row["files"])
            out.append(
                f"| {cell(row['name'])} ({row['code']}) | {files} | {k['total']} | {k['iso27001_only']} | "
                f"{k['nist_csf_only']} | {k['dpdpa_only']} | {k['shared']} |"
            )
        total = split_counts([i for r in index for i in r["ids"]], shown)
        out.append(
            f"| **Total** | | {total['total']} | {total['iso27001_only']} | {total['nist_csf_only']} | "
            f"{total['dpdpa_only']} | {total['shared']} |"
        )
        out.append("")
        out.append("ISO only, NIST only and DPDPA only count controls reached by that one framework. Shared means two or more. "
                   "Controls with no mapping row yet are in Controls but in none of the other columns.")
        out.append("")
    out += ["## Controls shown per framework subset", "",
            "| Subset | Controls shown | Records covered | Records in scope | Atoms mapped | Atoms in scope |", "|---|---|---|---|---|---|"]
    for c in validate.subset_counts(lib):
        label = " + ".join(FW_LONG[f] for f in FRAMEWORKS if f in c["subset"])
        out.append(
            f"| {label} | {c['controls']} | {c['records_covered']} | {c['records_total']} | {c['atoms_mapped']} | {c['atoms_total']} |"
        )
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write UCF sign-off tables.")
    ap.add_argument("--data", default=str(validate.DEFAULT_DATA), help="data folder (default docs/ucf/drafts)")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output folder (default docs/ucf/signoff)")
    args = ap.parse_args(argv)

    lib = load_library(args.data)
    for err in lib.load_errors:
        print(f"WARN {err}")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.iterdir():
        if old.is_file() and GENERATED_RE.match(old.name):
            old.unlink()

    shown = shown_by_framework(lib)
    by_domain: dict[str, list[str]] = {}
    for cid, c in lib.controls.items():
        by_domain.setdefault(c.domain, []).append(cid)
    order = [d.code for d in sorted(lib.domains.values(), key=lambda d: d.sort)]
    order += sorted(set(by_domain) - set(order))

    index: list[dict] = []
    written = 0
    for code in order:
        ids = sorted(by_domain.get(code, []))
        if not ids:
            continue
        parts = chunks(ids)
        files = []
        for n, part_ids in enumerate(parts, 1):
            fname = f"{code}.md" if len(parts) == 1 else f"{code}-{n}.md"
            suffix = "" if len(parts) == 1 else f" (part {n} of {len(parts)})"
            (out_dir / fname).write_text(domain_page(lib, code, part_ids, shown, suffix), encoding="utf-8")
            files.append(fname)
            written += 1
        dom = lib.domains.get(code)
        index.append({"code": code, "name": dom.name if dom else code, "files": files, "ids": ids,
                      "counts": split_counts(ids, shown)})
    (out_dir / "README.md").write_text(readme(lib, index, shown), encoding="utf-8")
    print(f"wrote {written} domain files and README.md to {out_dir} ({len(lib.controls)} controls)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
