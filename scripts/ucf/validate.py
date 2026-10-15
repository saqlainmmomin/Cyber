#!/usr/bin/env python3
"""
UCF library validator: one run, one exit code (0 pass, 1 any failure).

    python scripts/ucf/validate.py [--data DIR] [--write-lock]
    python scripts/ucf/validate.py --why UC-GOV-01        # query: what a control covers
    python scripts/ucf/validate.py --records-of UC-GOV-01 # query: records a control covers
    python scripts/ucf/validate.py --controls-of ISO.A5.1 # query: controls covering a record

Query flags print their answer and exit without running the checks (exit 1 on an
unknown id). Checks are described in docs/plans/2026-10-13-001-single-track-implementation-plan.md
section 7.6 and tasks/handoffs/2026-10-13-ucf-part-1-kickoff.md (Track 3).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.frameworks.ucf.loader import Library, load_library, parse_control_id  # noqa: E402
from app.frameworks.ucf.schema import (  # noqa: E402
    ALLOWED_PAIRS,
    CONTROL_TYPES,
    COVERAGES,
    FRAMEWORK_SUBSETS,
    FRAMEWORKS,
    FREQUENCIES,
    IMPORTANCE,
    ISO_THEMES,
    KEY_SETTING_LAYERS,
    MATCH_TYPES,
    ORIGIN_ID_RANGES,
    ORIGINS,
    PRIVACY_ID_RANGE,
    RECORD_KINDS,
    Control,
    subset_label,
)

DEFAULT_DATA = REPO_ROOT / "docs" / "ucf" / "drafts"
MAX_SHOWN = 10
# A statement may name no owner role, except where the role is the thing being appointed.
ALLOW_ROLE_IN_STATEMENT = {"UC-PGV-01": {"Data Protection Officer"}}
GENERIC_IMPLEMENTERS = ("system owners", "the team", "the security team", "the lead", "the manager",
                        "analysts", "responders", "reviewers", "analyst", "responder", "reviewer")
GENERIC_RE = re.compile(r"\b(?:" + "|".join(re.escape(x) for x in GENERIC_IMPLEMENTERS) + r")\b", re.IGNORECASE)

# -- patterns ----------------------------------------------------------------

FRAMEWORK_NAME_RE = re.compile(r"\b(?:ISO|27001|27002|NIST|CSF|DPDPA?|GDPR|HIPAA|PCI|SOC\s*2)\b", re.IGNORECASE)
_UNIT = r"(?:business\s+days?|minutes?|hours?|days?|weeks?|months?|years?)"
NUMBER_UNIT_RE = re.compile(rf"(?<![\w.])(\d+(?:\.\d+)?)\s*(?:-\s*)?({_UNIT}\b|%)", re.IGNORECASE)
WITHIN_RE = re.compile(
    rf"\bwithin\s+(\d+(?:\.\d+)?)\b(?!\s*(?:-\s*)?(?:{_UNIT}\b|%))", re.IGNORECASE
)
DIGITS_RE = re.compile(r"\d+(?:\.\d+)?")
CONTROL_CODE_RE = re.compile(r"UC-|\bA\.\d|\b[A-Z]{2,3}\.[A-Z]{2}[-.]\d|\bCH\d|\bs\.\d|\br\.\d")


@dataclass
class CheckResult:
    number: int
    title: str
    items: list[str] = field(default_factory=list)  # failures
    infos: list[str] = field(default_factory=list)
    count: int | None = None  # override for len(items)

    @property
    def n(self) -> int:
        return len(self.items) if self.count is None else self.count

    @property
    def passed(self) -> bool:
        return self.n == 0


# -- helpers -----------------------------------------------------------------


def norm_unit(unit: str) -> str:
    unit = re.sub(r"\s+", " ", unit.lower())
    return unit if unit == "%" else re.sub(r"s$", "", unit)


def number_tokens(text: str) -> set[str]:
    """Normalized 'N unit' tokens, e.g. '72 hour', '10 business day', '95%'."""
    return {f"{m.group(1)}{'' if m.group(2) == '%' else ' '}{norm_unit(m.group(2))}" for m in NUMBER_UNIT_RE.finditer(text)}


def within_numbers(text: str) -> set[str]:
    return {m.group(1) for m in WITHIN_RE.finditer(text)}


def framework_hits(text: str) -> list[str]:
    return sorted({m.group(0).upper() for m in FRAMEWORK_NAME_RE.finditer(text)})


def ctl_ref(c: Control | None, cid: str) -> str:
    return f"{cid} ({c.src})" if c is not None and c.src else cid


# -- check 0: load -----------------------------------------------------------


def check_load(lib: Library) -> CheckResult:
    r = CheckResult(0, "files load")
    r.items += lib.load_errors
    r.items += [f"duplicate record id {d}" for d in lib.duplicate_records]
    r.infos.append(
        "files read: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(lib.files.items())) if lib.files else "no files found"
    )
    for kind in ("atoms", "controls", "mappings", "fields"):
        if kind not in lib.files:
            r.infos.append(f"no {kind}_*.csv yet")
    return r


# -- check 1: coverage -------------------------------------------------------


def repo_record_ids() -> dict[str, set[str]]:
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION

    return {
        "iso27001": {c.id for c in ISO27001_DEFINITION.all_controls()},
        "nist_csf": {c.id for c in NIST_CSF_DEFINITION.all_controls()},
        "dpdpa": {c.id for c in DPDPA_DEFINITION.all_controls()},
    }


def check_coverage(lib: Library) -> CheckResult:
    r = CheckResult(1, "coverage, primary, row validity")
    out = r.items
    slots = lib.remainder_slots()

    # records, atoms
    for rec in lib.records.values():
        if rec.framework not in FRAMEWORKS:
            out.append(f"record {rec.record_id}: unknown framework {rec.framework!r} ({rec.src})")
        if rec.kind not in RECORD_KINDS:
            out.append(f"record {rec.record_id}: unknown kind {rec.kind!r} ({rec.src})")
        if not lib.atoms_by_record.get(rec.record_id):
            out.append(f"record {rec.record_id}: no atoms")
    out += [f"duplicate atom id {d}" for d in lib.duplicate_atoms]
    for atom in lib.atoms.values():
        rec = lib.records.get(atom.record_id)
        if rec is None:
            out.append(f"atom {atom.atom_id}: record {atom.record_id} does not exist ({atom.src})")
        elif rec.framework != atom.framework:
            out.append(f"atom {atom.atom_id}: framework {atom.framework} differs from record's {rec.framework}")
        if not atom.atom_id.startswith(atom.record_id + "-"):
            out.append(f"atom {atom.atom_id}: id does not start with '{atom.record_id}-' ({atom.src})")

    # rows
    for row in lib.mappings:
        w = f"row {row.src}"
        atom = lib.atoms.get(row.atom_id)
        if atom is None:
            out.append(f"{w}: atom {row.atom_id!r} does not exist")
        else:
            if atom.record_id != row.record_id:
                out.append(f"{w}: record_id {row.record_id} differs from atom's record {atom.record_id}")
            if atom.framework != row.source_framework:
                out.append(f"{w}: source_framework {row.source_framework} differs from atom's {atom.framework}")
        if row.source_framework not in FRAMEWORKS:
            out.append(f"{w}: unknown source_framework {row.source_framework!r}")
        if row.match_type not in MATCH_TYPES:
            out.append(f"{w}: unknown match_type {row.match_type!r}")
        if row.coverage not in COVERAGES:
            out.append(f"{w}: unknown coverage {row.coverage!r}")
        if (row.match_type, row.coverage) not in ALLOWED_PAIRS and row.match_type in MATCH_TYPES and row.coverage in COVERAGES:
            out.append(f"{w}: match_type {row.match_type} with coverage {row.coverage} is not an allowed pair")
        if not row.reason:
            out.append(f"{w}: empty reason")
        if row.match_type == "none" or row.coverage == "none":
            if row.unified_control_id:
                out.append(f"{w}: a none row must not name a control ({row.unified_control_id})")
            if row.primary:
                out.append(f"{w}: a none row cannot be primary")
        elif not row.unified_control_id:
            out.append(f"{w}: empty unified_control_id on a {row.match_type}/{row.coverage} row")
        if row.unified_control_id and row.unified_control_id not in lib.controls:
            out.append(f"{w}: control {row.unified_control_id} does not exist")
        if row.remainder_of and row.remainder_of not in lib.controls:
            out.append(f"{w}: remainder_of {row.remainder_of} does not exist")
        if row.remainder_of and not row.unified_control_id:
            out.append(f"{w}: remainder_of set on a row with no control")
        if row.remainder_immaterial and not row.immaterial_reason:
            out.append(f"{w}: remainder_immaterial=true without immaterial_reason")
        if row.remainder_immaterial and row.coverage != "partial":
            out.append(f"{w}: remainder_immaterial on a non-partial row")

    # atoms: covered one of four ways
    for atom in lib.atoms.values():
        rows = lib.rows_by_atom.get(atom.atom_id, [])
        if not rows:
            out.append(f"atom {atom.atom_id}: no mapping row ({atom.src})")
            continue
        if any(x.coverage == "full" and x.unified_control_id for x in rows):
            continue
        if any(x.match_type == "none" and x.coverage == "none" and x.reason for x in rows):
            continue
        partials = [x for x in rows if x.coverage == "partial" and x.unified_control_id]
        if not partials:
            out.append(f"atom {atom.atom_id}: no full, partial or none row")
            continue
        mapped = {x.unified_control_id for x in rows}
        for p in partials:
            if p.remainder_immaterial and p.immaterial_reason:
                continue
            if mapped & (slots.get(p.unified_control_id, set()) - {p.unified_control_id}):
                continue
            out.append(f"atom {atom.atom_id}: partial row to {p.unified_control_id} has no remainder slot row and no immaterial reason")

    # exactly one primary per record
    for rid, rec in lib.records.items():
        rows = lib.rows_by_record.get(rid, [])
        atoms = lib.atoms_by_record.get(rid, [])
        if not rows or not atoms:
            continue  # already reported above
        mapped_rows = [x for x in rows if x.unified_control_id]
        primaries = [x for x in rows if x.primary]
        if mapped_rows and len(primaries) != 1:
            out.append(f"record {rid}: {len(primaries)} primary rows, expected exactly 1")
        elif not mapped_rows and primaries:
            out.append(f"record {rid}: primary row on a record whose atoms are all none")
        elif mapped_rows and not any(x.unified_control_id for x in primaries):
            out.append(f"record {rid}: primary row names no control")

    # repo cross-check
    try:
        repo = repo_record_ids()
    except Exception as exc:  # noqa: BLE001 - lazily imported, any failure means skip
        r.infos.append(f"WARN repo cross-check skipped ({type(exc).__name__}: {exc})")
    else:
        for fw, ids in repo.items():
            have = {
                x.record_id for x in lib.records.values()
                if x.framework == fw and not (fw == "iso27001" and x.kind == "clause")
            }
            for rid in sorted(ids - have):
                out.append(f"repo cross-check: {fw} record {rid} is in the repo but not in records_*.csv")
            for rid in sorted(have - ids):
                out.append(f"repo cross-check: {fw} record {rid} is in records_*.csv but not in the repo")
        r.infos.append("repo cross-check ran (iso27001 annex, nist_csf, dpdpa; ISO.C clause records are extra)")
    return r


# -- check 2: control fields -------------------------------------------------


def check_fields(lib: Library) -> CheckResult:
    r = CheckResult(2, "control fields and source mapping")
    out = r.items
    roles = set(lib.roles)
    no_fields = [c for c in lib.controls.values() if not c.has_fields]
    generic_warn: list[str] = []
    if not lib.controls:
        out.append("no controls loaded (controls_*.csv missing or empty)")
    if no_fields:
        r.infos.append(f"controls without a fields row: {len(no_fields)} of {len(lib.controls)}")
    out += [f"fields row for unknown control {d}" for d in lib.orphan_fields]
    out += [f"duplicate fields row {d}" for d in lib.duplicate_fields]
    for c in lib.controls.values():
        ref = ctl_ref(c, c.id)
        if not c.has_fields:
            out.append(f"{ref}: no fields row (statement, test missing)")
        else:
            if not c.statement:
                out.append(f"{ref}: empty statement")
            if not c.test:
                out.append(f"{ref}: empty test")
            allowed = ALLOW_ROLE_IN_STATEMENT.get(c.id, set())
            for role in sorted(roles - allowed - {"Top Management"}):
                if re.search(rf"\b{re.escape(role)}\b", c.statement, re.IGNORECASE):
                    out.append(f"{c.id} statement names an owner role ({role})")
            g = sorted({m.group(0).lower() for m in GENERIC_RE.finditer(c.statement)})
            if g:
                generic_warn.append(f"{c.id}: {', '.join(g)}")
            code = c.fields_src.split(":")[0].removeprefix("fields_").removesuffix(".csv").split("_")[0]
            if code != c.domain:
                out.append(f"{c.id}: fields row in fields_{code}.csv but control domain is {c.domain}")
            if c.control_type and c.control_type not in CONTROL_TYPES:
                out.append(f"{ref}: control_type {c.control_type!r} not allowed")
            if c.frequency and c.frequency not in FREQUENCIES:
                out.append(f"{ref}: frequency {c.frequency!r} not allowed")
            for e in c.key_settings_errors:
                out.append(f"{ref}: key_settings {e}")
        if not c.owner_role:
            out.append(f"{ref}: empty owner_role")
        elif c.owner_role not in roles:
            out.append(f"{ref}: owner_role {c.owner_role!r} is not in roles.csv")
        if c.importance and c.importance not in IMPORTANCE:
            out.append(f"{ref}: importance {c.importance!r} not allowed")
        if c.iso_theme and c.iso_theme not in ISO_THEMES:
            out.append(f"{ref}: iso_theme {c.iso_theme!r} not allowed")
        if not lib.rows_by_control.get(c.id):
            out.append(f"{ref}: no mapping row points at this control")
    r.infos.append(f"WARN {len(generic_warn)} statements name a generic implementer")
    r.infos += [f"    {w}" for w in generic_warn[:MAX_SHOWN]]
    return r


# -- check 3: uniqueness -----------------------------------------------------


def check_uniqueness(lib: Library) -> CheckResult:
    r = CheckResult(3, "no duplicate controls or (atom, control) pairs")
    out = r.items
    out += [f"control id in two places: {d}" for d in lib.duplicate_controls]
    for c in lib.controls.values():
        parsed = parse_control_id(c.id)
        if c.domain not in lib.domains:
            out.append(f"{ctl_ref(c, c.id)}: domain {c.domain!r} is not in domains.csv")
        if parsed and parsed[0] != c.domain:
            out.append(f"{ctl_ref(c, c.id)}: id code {parsed[0]} differs from domain column {c.domain}")
    pairs: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in lib.mappings:
        if row.unified_control_id:
            pairs[(row.atom_id, row.unified_control_id)].append(row.src)
    for (atom, cid), srcs in sorted(pairs.items()):
        if len(srcs) > 1:
            out.append(f"atom {atom} maps to {cid} {len(srcs)} times ({', '.join(srcs)})")
    # records mapping to a control through two atoms (allowed)
    via: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in lib.mappings:
        if row.unified_control_id:
            via[(row.record_id, row.unified_control_id)].add(row.atom_id)
    multi = sum(1 for atoms in via.values() if len(atoms) > 1)
    r.infos.append(f"INFO {multi} (record, control) pairs reached through two or more atoms (allowed)")
    return r


# -- check 4: framework subsets ----------------------------------------------


def check_subsets(lib: Library) -> CheckResult:
    r = CheckResult(4, "framework subsets: no framework names, numbers by layer, no out-of-scope slots")
    # key -> set of subset labels where it fails
    bad: dict[str, set[str]] = defaultdict(set)
    per_subset: Counter[str] = Counter()
    slots = lib.remainder_slots()
    slot_ids = set().union(*slots.values()) if slots else set()
    for subset in FRAMEWORK_SUBSETS:
        label = subset_label(subset)
        shown = lib.shown_controls(subset) & set(lib.controls)
        layers = {"base"} | set(subset)
        for cid in sorted(shown):
            c = lib.controls[cid]
            if not c.has_fields:
                continue
            allowed = [ks.setting for ks in c.key_settings if ks.layer in layers]
            anywhere = [ks for ks in c.key_settings]
            allowed_tokens = set().union(*(number_tokens(s) for s in allowed)) if allowed else set()
            allowed_digits = set().union(*(set(DIGITS_RE.findall(s)) for s in allowed)) if allowed else set()
            for fname, text in c.text_fields().items():
                if not text:
                    continue
                for hit in framework_hits(text):
                    bad[f"{c.id} {fname}: names a framework ({hit})"].add(label)
                if fname == "key_settings":
                    continue
                for tok in sorted(number_tokens(text)):
                    if tok in allowed_tokens:
                        continue
                    other = [ks.layer for ks in anywhere if tok in number_tokens(ks.setting)]
                    why = f"only under layer {','.join(sorted(set(other)))}, not in scope" if other else "not in key_settings"
                    bad[f"{c.id} {fname}: number '{tok}' {why}"].add(label)
                for num in sorted(within_numbers(text)):
                    if num in allowed_digits:
                        continue
                    other = [ks.layer for ks in anywhere if num in DIGITS_RE.findall(ks.setting)]
                    why = f"only under layer {','.join(sorted(set(other)))}, not in scope" if other else "not in key_settings"
                    bad[f"{c.id} {fname}: 'within {num}' {why}"].add(label)
            # privacy domains only with dpdpa
            dom = lib.domains.get(c.domain)
            if dom and dom.privacy and "dpdpa" not in subset:
                bad[f"{c.id}: privacy-domain control shown without dpdpa"].add(label)
        # (c) remainder slots shown only when a selected framework maps to them
        for slot in sorted(slot_ids & shown):
            if not any(x.unified_control_id == slot and x.source_framework in subset for x in lib.mappings):
                bad[f"{slot}: remainder slot shown with no selected framework mapping to it"].add(label)
    for key, labels in bad.items():
        for label in labels:
            per_subset[label] += 1
    r.items = [f"{k}  [subsets: {', '.join(sorted(v))}]" for k, v in sorted(bad.items())]
    if per_subset:
        r.infos.append("failures by subset: " + ", ".join(f"{k}={v}" for k, v in sorted(per_subset.items())))
    return r


# -- check 5: both directions ------------------------------------------------


def check_directions(lib: Library) -> CheckResult:
    r = CheckResult(5, "both directions resolve")
    out = r.items
    for rid, cids in sorted(lib.controls_of_record.items()):
        if rid not in lib.records:
            out.append(f"record {rid} (named by a mapping row) does not exist")
        for cid in sorted(cids):
            if cid not in lib.controls:
                out.append(f"record {rid} -> control {cid} does not exist")
    for cid, rids in sorted(lib.records_of_control.items()):
        if cid not in lib.controls:
            out.append(f"control {cid} (named by a mapping row) does not exist")
        for rid in sorted(rids):
            if rid not in lib.records:
                out.append(f"control {cid} -> record {rid} does not exist")
    loss = {
        cid: sorted(rid for rid in rids if lib.controls_of_record.get(rid) == {cid})
        for cid, rids in lib.records_of_control.items()
    }
    ranked = sorted(((len(v), cid) for cid, v in loss.items() if v), reverse=True)
    r.infos.append(
        f"controls reaching records: {len(lib.records_of_control)}; records with coverage: {len(lib.controls_of_record)} of {len(lib.records)}"
    )
    if ranked:
        r.infos.append(f"records that lose ALL coverage if a control is retired (top {min(MAX_SHOWN, len(ranked))} of {len(ranked)} controls):")
        r.infos += [f"    {cid}: {n} records" for n, cid in ranked[:MAX_SHOWN]]
    else:
        r.infos.append("no control is the sole cover of any record")
    return r


# -- check 6: questions ------------------------------------------------------


def check_questions(lib: Library) -> CheckResult:
    r = CheckResult(6, "questions: one obligation, no control code, no framework name")
    shown = sorted(set().union(*(lib.shown_controls(s) for s in FRAMEWORK_SUBSETS)) & set(lib.controls))
    with_q = warn = 0
    warnings: list[str] = []
    for cid in shown:
        c = lib.controls[cid]
        q = c.question
        if not q:
            continue
        with_q += 1
        if not q.endswith("?"):
            r.items.append(f"{cid}: question does not end with '?'")
        if q.count("?") != 1:
            r.items.append(f"{cid}: question has {q.count('?')} question marks, expected 1")
        if ";" in q:
            r.items.append(f"{cid}: question contains a semicolon")
        m = CONTROL_CODE_RE.search(q)
        if m:
            r.items.append(f"{cid}: question contains a control code ({m.group(0)!r})")
        hits = framework_hits(q)
        if hits:
            r.items.append(f"{cid}: question names a framework ({', '.join(hits)})")
        low = q.lower()
        if low.count(" and ") > 1 or " as well as " in low or " and/or " in low or " both " in low:
            warn += 1
            warnings.append(f"{cid}: {q}")
    r.infos.append(f"shown controls: {len(shown)}; with a question: {with_q}; without: {len(shown) - with_q}")
    r.infos.append(f"WARN {warn} questions look compound")
    r.infos += [f"    {w}" for w in warnings[:MAX_SHOWN]]
    return r


# -- check 7: id stability ---------------------------------------------------


def lock_hash(domain: str, title: str) -> str:
    return hashlib.sha1(f"{domain}|{title}".encode("utf-8")).hexdigest()


def lock_payload(lib: Library) -> dict:
    return {
        "library_version": lib.library_version,
        "controls": {cid: lock_hash(c.domain, c.title) for cid, c in sorted(lib.controls.items())},
        "records": sorted(lib.records),
    }


def check_ids(lib: Library) -> CheckResult:
    r = CheckResult(7, "id stability")
    out = r.items
    seen: set[str] = set()
    for c in lib.controls.values():
        parsed = parse_control_id(c.id)
        if not parsed:
            out.append(f"{ctl_ref(c, c.id)}: id does not match UC-<CODE>-<NN>")
            continue
        if c.id in seen:
            out.append(f"{c.id}: duplicate id")
        seen.add(c.id)
        _, num = parsed
        if c.origin not in ORIGINS:
            out.append(f"{ctl_ref(c, c.id)}: origin {c.origin!r} not one of {', '.join(ORIGINS)}")
            continue
        dom = lib.domains.get(c.domain)
        if dom and dom.privacy:
            lo, hi = PRIVACY_ID_RANGE
            if c.origin != "dpdpa":
                out.append(f"{ctl_ref(c, c.id)}: privacy-domain control must have origin dpdpa, got {c.origin}")
        else:
            lo, hi = ORIGIN_ID_RANGES[c.origin]
        if not lo <= num <= hi:
            out.append(f"{ctl_ref(c, c.id)}: number {num:02d} outside {lo:02d}-{hi:02d} for origin {c.origin}")
    lock_path = lib.data_dir / "ids.lock.json"
    if not lock_path.exists():
        r.infos.append("no lock yet (created at first signed version)")
        return r
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock_version, lock_controls, lock_records = lock["library_version"], lock["controls"], lock["records"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        out.append(f"ids.lock.json: unreadable ({type(exc).__name__}: {exc})")
        return r
    if lock_version != lib.library_version:
        r.infos.append(f"lock is for library_version {lock_version}, library is {lib.library_version}: lock not enforced")
        return r
    for cid, h in sorted(lock_controls.items()):
        c = lib.controls.get(cid)
        if c is None:
            out.append(f"{cid}: removed since lock {lock_version} (bump library_version)")
        elif lock_hash(c.domain, c.title) != h:
            out.append(f"{cid}: domain or title changed since lock {lock_version} (bump library_version)")
    for rid in lock_records:
        if rid not in lib.records:
            out.append(f"record {rid}: removed since lock {lock_version} (bump library_version)")
    r.infos.append(f"lock {lock_version} enforced: {len(lock_controls)} controls, {len(lock_records)} records")
    return r


# -- counts ------------------------------------------------------------------


def subset_counts(lib: Library) -> list[dict]:
    """Per framework subset: controls shown, records covered/total, atoms mapped/total, controls by domain."""
    out = []
    domain_order = sorted(lib.domains.values(), key=lambda d: d.sort)
    for subset in FRAMEWORK_SUBSETS:
        shown = lib.shown_controls(subset) & set(lib.controls)
        recs = [rid for rid, rec in lib.records.items() if rec.framework in subset]
        covered = sum(1 for rid in recs if lib.controls_of_record.get(rid, set()) & shown)
        atoms = [a for a in lib.atoms.values() if a.framework in subset]
        mapped = sum(
            1 for a in atoms if any(x.unified_control_id and x.coverage != "none" for x in lib.rows_by_atom.get(a.atom_id, []))
        )
        by_dom = Counter(lib.controls[c].domain for c in shown)
        parts = [
            f"{d.code} {by_dom[d.code]}"
            for d in domain_order
            if by_dom.get(d.code) and (not d.privacy or "dpdpa" in subset)
        ]
        parts += [f"{k}? {v}" for k, v in by_dom.items() if k not in lib.domains]
        out.append(
            {
                "subset": subset,
                "label": subset_label(subset),
                "shown": shown,
                "controls": len(shown),
                "records_covered": covered,
                "records_total": len(recs),
                "atoms_mapped": mapped,
                "atoms_total": len(atoms),
                "by_domain": parts,
            }
        )
    return out


def print_counts(lib: Library) -> None:
    print("COUNTS")
    print(f"  {'subset':<28}{'controls':>9}{'records covered/total':>24}{'atoms mapped/total':>21}")
    rows = subset_counts(lib)
    for c in rows:
        rc, am = f"{c['records_covered']}/{c['records_total']}", f"{c['atoms_mapped']}/{c['atoms_total']}"
        print(f"  {c['label']:<28}{c['controls']:>9}{rc:>24}{am:>21}")
    print("  controls shown by domain:")
    for c in rows:
        print(f"  {c['label']}: " + (", ".join(c["by_domain"]) or "(none)"))


# -- queries -----------------------------------------------------------------


def query_why(lib: Library, cid: str) -> int:
    c = lib.controls.get(cid)
    rows = lib.rows_by_control.get(cid, [])
    if c is None and not rows:
        print(f"{cid}: unknown control")
        return 1
    if c is not None:
        print(f"{cid}  {c.title}  [{c.domain}, origin {c.origin}, owner {c.owner_role or '-'}]")
        if c.goal:
            print(f"  goal: {c.goal}")
    print(f"{len(rows)} mapping rows reach {cid}:")
    for row in sorted(rows, key=lambda x: (x.record_id, x.atom_id)):
        atom = lib.atoms.get(row.atom_id)
        flags = ("primary " if row.primary else "") + (f"remainder_of {row.remainder_of}" if row.remainder_of else "")
        print(f"  {row.record_id}  {row.atom_id}  {row.match_type}/{row.coverage}  {flags.strip()}")
        if atom:
            print(f"      atom: {atom.paraphrase}")
        print(f"      reason: {row.reason}")
    return 0


def query_records_of(lib: Library, cid: str) -> int:
    if cid not in lib.controls and cid not in lib.records_of_control:
        print(f"{cid}: unknown control")
        return 1
    rids = sorted(lib.records_of_control.get(cid, set()))
    print(f"{cid} covers {len(rids)} records:")
    for rid in rids:
        rec = lib.records.get(rid)
        sole = " (sole cover)" if lib.controls_of_record.get(rid) == {cid} else ""
        print(f"  {rid}  {rec.reference + '  ' + rec.title if rec else '(unknown record)'}{sole}")
    return 0


def query_controls_of(lib: Library, rid: str) -> int:
    rec = lib.records.get(rid)
    rows = lib.rows_by_record.get(rid, [])
    if rec is None and not rows:
        print(f"{rid}: unknown record")
        return 1
    print(f"{rid}  {rec.title if rec else '(unknown record)'}")
    for atom in lib.atoms_by_record.get(rid, []):
        print(f"  {atom.atom_id}: {atom.paraphrase}")
        for row in lib.rows_by_atom.get(atom.atom_id, []):
            ctl = lib.controls.get(row.unified_control_id)
            name = f"{row.unified_control_id}  {ctl.title}" if ctl else (row.unified_control_id or "(no control)")
            print(f"      -> {name}  {row.match_type}/{row.coverage}{'  PRIMARY' if row.primary else ''}")
            print(f"         {row.reason}")
    return 0


# -- main --------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate the UCF library data.")
    ap.add_argument("--data", default=str(DEFAULT_DATA), help="data folder (default docs/ucf/drafts)")
    ap.add_argument("--why", metavar="UC-ID", help="print the records and atoms a control covers, then exit")
    ap.add_argument("--records-of", metavar="UC-ID", help="print the records a control covers, then exit")
    ap.add_argument("--controls-of", metavar="RECORD_ID", help="print the controls covering a record, then exit")
    ap.add_argument("--write-lock", action="store_true", help="write ids.lock.json from the current data (only if check 7 passes)")
    args = ap.parse_args(argv)

    lib = load_library(args.data)

    if args.why or args.records_of or args.controls_of:
        code = 0
        if args.why:
            code |= query_why(lib, args.why)
        if args.records_of:
            code |= query_records_of(lib, args.records_of)
        if args.controls_of:
            code |= query_controls_of(lib, args.controls_of)
        return code

    print(f"UCF validate: {Path(args.data)}  library_version {lib.library_version or '?'}")
    print(f"loaded: {len(lib.records)} records, {len(lib.atoms)} atoms, {len(lib.controls)} controls, "
          f"{len(lib.mappings)} mapping rows, {sum(c.has_fields for c in lib.controls.values())} fields rows")
    print()

    results: list[CheckResult] = []
    checks = [check_load, check_coverage, check_fields, check_uniqueness, check_subsets,
              check_directions, check_questions, check_ids]
    for fn in checks:
        try:
            res = fn(lib)
        except Exception as exc:  # noqa: BLE001 - a bug in a check must show as a FAIL, not a traceback
            res = CheckResult(len(results), fn.__name__, [f"internal error {type(exc).__name__}: {exc}"])
        results.append(res)
        status = "PASS" if res.passed else "FAIL"
        print(f"CHECK {res.number} {status}  {res.title}" + ("" if res.passed else f"  ({res.n} issues)"))
        for item in res.items[:MAX_SHOWN]:
            print(f"    - {item}")
        if res.n > MAX_SHOWN:
            print(f"    ... and {res.n - MAX_SHOWN} more")
        for info in res.infos:
            print(f"    {info}")
    print()
    print_counts(lib)
    print()

    if args.write_lock:
        ok = all(r.passed for r in results if r.number in (0, 7)) and not lib.duplicate_controls
        if ok:
            path = lib.data_dir / "ids.lock.json"
            path.write_text(json.dumps(lock_payload(lib), indent=2) + "\n", encoding="utf-8")
            print(f"wrote {path}")
        else:
            print("lock NOT written: load or id checks failed")

    failed = sum(1 for r in results if not r.passed)
    print("RESULT PASS" if not failed else f"RESULT FAIL ({failed} checks failed)")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
