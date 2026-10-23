"""
UCF library loader. Stdlib only.

load_library(data_dir) reads every table in the folder (see FORMAT.md), tolerates
files that do not exist yet, and never raises on bad data: problems are collected
in Library.load_errors so a validator can report them. A file with a bad header is
skipped entirely, with a message naming the missing and unexpected columns.
"""

from __future__ import annotations

import csv
import dataclasses
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .schema import (
    ATOM_COLUMNS,
    CONTROL_COLUMNS,
    DOMAIN_COLUMNS,
    FIELD_COLUMNS,
    KEY_SETTING_LAYERS,
    MAPPING_COLUMNS,
    RECORD_COLUMNS,
    ROLE_COLUMNS,
    Atom,
    Control,
    Domain,
    KeySetting,
    MappingRow,
    Record,
)

_TRUE = {"true", "yes", "1"}
_FALSE = {"false", "no", "0", ""}


@dataclass
class Library:
    data_dir: Path
    meta: dict = field(default_factory=dict)  # library.json
    domains: dict[str, Domain] = field(default_factory=dict)
    roles: list[str] = field(default_factory=list)
    records: dict[str, Record] = field(default_factory=dict)
    atoms: dict[str, Atom] = field(default_factory=dict)
    controls: dict[str, Control] = field(default_factory=dict)  # joined with fields
    mappings: list[MappingRow] = field(default_factory=list)
    files: dict[str, list[str]] = field(default_factory=dict)  # table kind -> file names read
    load_errors: list[str] = field(default_factory=list)
    duplicate_records: list[str] = field(default_factory=list)
    duplicate_atoms: list[str] = field(default_factory=list)
    duplicate_controls: list[str] = field(default_factory=list)  # "UC-X-01 in a.csv:3 and b.csv:7"
    duplicate_fields: list[str] = field(default_factory=list)
    orphan_fields: list[str] = field(default_factory=list)  # fields rows with no control
    # indexes (built by build_indexes), both directions. Only rows with a control and coverage != none.
    rows_by_atom: dict[str, list[MappingRow]] = field(default_factory=dict)  # includes `none` rows
    rows_by_control: dict[str, list[MappingRow]] = field(default_factory=dict)
    rows_by_record: dict[str, list[MappingRow]] = field(default_factory=dict)  # includes `none` rows
    atoms_by_record: dict[str, list[Atom]] = field(default_factory=dict)
    controls_of_record: dict[str, set[str]] = field(default_factory=dict)
    records_of_control: dict[str, set[str]] = field(default_factory=dict)

    @property
    def library_version(self) -> str:
        return str(self.meta.get("library_version", ""))

    def build_indexes(self) -> None:
        self.rows_by_atom, self.rows_by_control, self.rows_by_record = {}, {}, {}
        self.atoms_by_record = {}
        self.controls_of_record, self.records_of_control = {}, {}
        for atom in self.atoms.values():
            self.atoms_by_record.setdefault(atom.record_id, []).append(atom)
        for row in self.mappings:
            self.rows_by_atom.setdefault(row.atom_id, []).append(row)
            self.rows_by_record.setdefault(row.record_id, []).append(row)
            if row.unified_control_id:
                self.rows_by_control.setdefault(row.unified_control_id, []).append(row)
                if row.coverage in ("full", "partial"):
                    self.controls_of_record.setdefault(row.record_id, set()).add(row.unified_control_id)
                    self.records_of_control.setdefault(row.unified_control_id, set()).add(row.record_id)

    def shown_controls(self, frameworks: frozenset[str]) -> set[str]:
        """Control ids with at least one mapping row from a selected framework."""
        return {
            r.unified_control_id
            for r in self.mappings
            if r.unified_control_id and r.source_framework in frameworks
        }

    def remainder_slots(self) -> dict[str, set[str]]:
        """base control id -> control ids that some row names as its remainder slot."""
        out: dict[str, set[str]] = {}
        for r in self.mappings:
            if r.remainder_of and r.unified_control_id:
                out.setdefault(r.remainder_of, set()).add(r.unified_control_id)
        return out


# -- reading -----------------------------------------------------------------


def _read_table(path: Path, columns: tuple[str, ...], errors: list[str]) -> list[tuple[int, dict[str, str]]]:
    """Return (line_number, row) pairs, or [] with an error if the file is unusable."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"{path.name}: cannot read ({exc})")
        return []
    if not text.strip():
        errors.append(f"{path.name}: empty file, no header row")
        return []
    reader = csv.reader(text.splitlines(keepends=True))
    try:
        header = [h.strip() for h in next(reader)]
    except (StopIteration, csv.Error) as exc:
        errors.append(f"{path.name}: unreadable header ({exc})")
        return []
    missing = [c for c in columns if c not in header]
    extra = [c for c in header if c not in columns]
    dup = sorted({c for c in header if header.count(c) > 1})
    if missing or extra or dup:
        parts = []
        if missing:
            parts.append(f"missing {missing}")
        if extra:
            parts.append(f"unexpected {extra}")
        if dup:
            parts.append(f"duplicated {dup}")
        errors.append(f"{path.name}: bad header, {'; '.join(parts)}; expected {list(columns)}")
        return []
    rows: list[tuple[int, dict[str, str]]] = []
    try:
        for cells in reader:
            line = reader.line_num
            if not any(c.strip() for c in cells):
                continue
            if len(cells) != len(header):
                errors.append(f"{path.name}:{line}: row has {len(cells)} cells, header has {len(header)}")
                continue
            rows.append((line, {h: c.strip() for h, c in zip(header, cells)}))
    except csv.Error as exc:
        errors.append(f"{path.name}: csv error near line {reader.line_num} ({exc})")
    return rows


def _bool(value: str, where: str, column: str, errors: list[str]) -> bool:
    v = value.strip().lower()
    if v in _TRUE:
        return True
    if v not in _FALSE:
        errors.append(f"{where}: {column} must be true or false, got {value!r}")
    return False


def parse_key_settings(raw: str) -> tuple[tuple[KeySetting, ...], tuple[str, ...]]:
    """'layer: setting | layer: setting' -> settings plus syntax errors."""
    settings: list[KeySetting] = []
    errors: list[str] = []
    for part in (p.strip() for p in raw.split("|")):
        if not part:
            continue
        layer, sep, setting = part.partition(":")
        layer, setting = layer.strip(), setting.strip()
        if not sep or not setting:
            errors.append(f"entry {part!r} is not 'layer: setting'")
            continue
        if layer not in KEY_SETTING_LAYERS:
            errors.append(f"unknown layer {layer!r} in {part!r}")
        settings.append(KeySetting(layer, setting))
    return tuple(settings), tuple(errors)


def _files(data_dir: Path, pattern: str) -> list[Path]:
    return sorted(p for p in data_dir.glob(pattern) if p.is_file())


def load_library(data_dir: str | Path) -> Library:
    data_dir = Path(data_dir)
    lib = Library(data_dir=data_dir)
    errors = lib.load_errors
    if not data_dir.is_dir():
        errors.append(f"{data_dir}: data directory does not exist")
        return lib

    def note(kind: str, path: Path) -> None:
        lib.files.setdefault(kind, []).append(path.name)

    # library.json
    meta_path = data_dir / "library.json"
    if meta_path.exists():
        note("library", meta_path)
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if not isinstance(meta, dict) or not meta.get("library_version"):
                errors.append("library.json: needs an object with a library_version")
            else:
                lib.meta = meta
        except (OSError, ValueError) as exc:
            errors.append(f"library.json: cannot parse ({exc})")
    else:
        errors.append("library.json: missing")

    # domains.csv, roles.csv
    p = data_dir / "domains.csv"
    if p.exists():
        note("domains", p)
        for line, row in _read_table(p, DOMAIN_COLUMNS, errors):
            where = f"{p.name}:{line}"
            try:
                sort = int(row["sort"])
            except ValueError:
                errors.append(f"{where}: sort must be an integer, got {row['sort']!r}")
                sort = 0
            if row["code"] in lib.domains:
                errors.append(f"{where}: duplicate domain code {row['code']}")
                continue
            lib.domains[row["code"]] = Domain(
                row["code"], row["name"], row["owner_role"], _bool(row["privacy"], where, "privacy", errors), sort, where
            )
    else:
        errors.append("domains.csv: missing")
    p = data_dir / "roles.csv"
    if p.exists():
        note("roles", p)
        lib.roles = [row["role"] for _, row in _read_table(p, ROLE_COLUMNS, errors) if row["role"]]
    else:
        errors.append("roles.csv: missing")

    # records
    for p in _files(data_dir, "records_*.csv"):
        note("records", p)
        for line, row in _read_table(p, RECORD_COLUMNS, errors):
            where = f"{p.name}:{line}"
            rec = Record(**row, src=where)
            if rec.record_id in lib.records:
                lib.duplicate_records.append(f"{rec.record_id} at {where} and {lib.records[rec.record_id].src}")
                continue
            lib.records[rec.record_id] = rec

    # atoms
    for p in _files(data_dir, "atoms_*.csv"):
        note("atoms", p)
        for line, row in _read_table(p, ATOM_COLUMNS, errors):
            where = f"{p.name}:{line}"
            nv = _bool(row.pop("needs_verification"), where, "needs_verification", errors)
            atom = Atom(**row, needs_verification=nv, src=where)
            if atom.atom_id in lib.atoms:
                lib.duplicate_atoms.append(f"{atom.atom_id} at {where} and {lib.atoms[atom.atom_id].src}")
                continue
            lib.atoms[atom.atom_id] = atom

    # control skeletons
    for p in _files(data_dir, "controls_*.csv"):
        note("controls", p)
        for line, row in _read_table(p, CONTROL_COLUMNS, errors):
            where = f"{p.name}:{line}"
            ctl = Control(**row, src=where)
            if ctl.id in lib.controls:
                lib.duplicate_controls.append(f"{ctl.id} at {where} and {lib.controls[ctl.id].src}")
                continue
            lib.controls[ctl.id] = ctl

    # mappings
    for p in _files(data_dir, "mappings_*.csv"):
        note("mappings", p)
        for line, row in _read_table(p, MAPPING_COLUMNS, errors):
            where = f"{p.name}:{line}"
            primary = _bool(row.pop("primary"), where, "primary", errors)
            immaterial = _bool(row.pop("remainder_immaterial"), where, "remainder_immaterial", errors)
            lib.mappings.append(MappingRow(**row, primary=primary, remainder_immaterial=immaterial, src=where))

    # fields, joined to controls
    seen_fields: dict[str, str] = {}
    for p in _files(data_dir, "fields_*.csv"):
        note("fields", p)
        for line, row in _read_table(p, FIELD_COLUMNS, errors):
            where = f"{p.name}:{line}"
            cid = row["id"]
            if cid in seen_fields:
                lib.duplicate_fields.append(f"{cid} at {where} and {seen_fields[cid]}")
                continue
            seen_fields[cid] = where
            if cid not in lib.controls:
                lib.orphan_fields.append(f"{cid} at {where}")
                continue
            settings, ks_errors = parse_key_settings(row["key_settings"])
            values = {k: v for k, v in row.items() if k not in ("id", "key_settings")}
            lib.controls[cid] = dataclasses.replace(
                lib.controls[cid],
                has_fields=True,
                fields_src=where,
                key_settings_raw=row["key_settings"],
                key_settings=settings,
                key_settings_errors=ks_errors,
                **values,
            )

    lib.build_indexes()
    return lib


_ID_RE = re.compile(r"^UC-([A-Z]{3})-(\d{2})$")


def parse_control_id(cid: str) -> tuple[str, int] | None:
    """'UC-GOV-07' -> ('GOV', 7), or None when the id is malformed."""
    m = _ID_RE.match(cid)
    return (m.group(1), int(m.group(2))) if m else None
