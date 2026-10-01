"""P6-2e: signed ISO 27001 and NIST CSF criteria reach the pack (converter, attachment, versions)."""

import csv
import hashlib

import pytest

from scripts import convert_criteria

SIGNED = convert_criteria.ROOT / "tasks" / "criteria-review" / "signed"


def _defs():
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION

    return {"iso27001": ISO27001_DEFINITION, "nist_csf": NIST_CSF_DEFINITION}


@pytest.mark.parametrize("framework", ["iso27001", "nist_csf"])
def test_generated_module_is_current_and_deterministic(framework):
    assert convert_criteria.main(["--framework", framework, "--check"]) == 0


@pytest.mark.parametrize("framework", ["iso27001", "nist_csf"])
def test_every_control_carries_signed_criteria(framework):
    definition = _defs()[framework]
    rows = convert_criteria.load_sheet(convert_criteria._sheet_path(framework))
    expected = [r for r in rows if not r["requirement_id"].startswith("ISO.C")]
    controls = definition.all_controls()
    assert all(c.test_criteria for c in controls)
    assert sum(len(c.test_criteria) for c in controls) == len(expected)
    assert definition.pack_version == f"{definition.version}+criteria-v1"


def test_iso_clause_rows_are_signed_but_deferred():
    rows = convert_criteria.load_sheet(convert_criteria._sheet_path("iso27001"))
    clause = [r for r in rows if r["requirement_id"].startswith("ISO.C")]
    assert len(clause) == 78
    emitted = {c.id for ctrl in _defs()["iso27001"].all_controls() for c in ctrl.test_criteria}
    assert not emitted & {r["criterion_id"] for r in clause}


def test_the_two_edited_rows_carry_clean_statements():
    for framework, cid in (("iso27001", "ISO.A6.1.TC4"), ("nist_csf", "NIST.GV.RM.05.TC3")):
        rows = {r["criterion_id"]: r for r in csv.DictReader(open(convert_criteria._sheet_path(framework), newline="", encoding="utf-8"))}
        assert rows[cid]["decision"] == "edit"
        text = next(c.statement for ctrl in _defs()[framework].all_controls() for c in ctrl.test_criteria if c.id == cid)
        assert text == rows[cid]["edited_statement"] and "(" not in text


def test_unsigned_sheet_is_refused(tmp_path):
    rows = convert_criteria.load_sheet(convert_criteria._sheet_path("nist_csf"))
    rows[0]["decision"] = ""
    with pytest.raises(ValueError, match="not fully signed"):
        convert_criteria.approved_criteria(rows, "nist_csf")


def test_unknown_requirement_is_refused_outside_deferred_prefix():
    rows = convert_criteria.load_sheet(convert_criteria._sheet_path("nist_csf"))
    rows[0]["requirement_id"] = "NIST.NOPE.01"
    rows[0]["criterion_id"] = "NIST.NOPE.01.TC1"
    with pytest.raises(ValueError, match="unknown requirement_id"):
        convert_criteria.approved_criteria(rows, "nist_csf")


def test_generated_header_names_the_sheet_hash():
    for framework in ("iso27001", "nist_csf"):
        text = convert_criteria._output_path(framework).read_text(encoding="utf-8")
        digest = hashlib.sha256(convert_criteria._sheet_path(framework).read_bytes()).hexdigest()
        assert digest in text and "do not edit by hand" in text
