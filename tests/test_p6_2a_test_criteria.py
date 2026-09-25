"""P6-2a: TestCriterion schema and the DPDPA draft criteria sheet."""

from __future__ import annotations

import re

from app.dpdpa.framework import get_all_requirements
from app.frameworks.criteria.dpdpa_draft import (
    DPDPA_CRITERIA_DRAFT,
    DPDPA_CRITERIA_REVIEW_META,
)
from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
from app.frameworks.definitions.gdpr import GDPR_DEFINITION
from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION
from app.frameworks.registry import FrameworkRegistry
from app.frameworks.schema import Control, TestCriterion
from scripts import export_criteria_review


def test_unmodified_control_has_no_criteria_and_registry_loads():
    ctrl = Control(id="X.1", title="t", description="d", reference="r", criticality="low")
    assert ctrl.test_criteria == ()

    definitions = [
        DPDPA_DEFINITION, ISO27001_DEFINITION, GDPR_DEFINITION,
        HIPAA_DEFINITION, NIST_CSF_DEFINITION, PCI_DSS_DEFINITION,
    ]
    saved = dict(FrameworkRegistry._frameworks)
    try:
        for fw in definitions:
            FrameworkRegistry.register(fw)
            assert FrameworkRegistry.get(fw.id).control_count() > 0
            # Draft criteria are not attached to any control until P6-2b.
            assert all(c.test_criteria == () for c in fw.all_controls())
    finally:
        FrameworkRegistry._frameworks.clear()
        FrameworkRegistry._frameworks.update(saved)


def test_draft_covers_exactly_the_41_requirements():
    ids = [r["id"] for r in get_all_requirements()]
    assert len(ids) == 41
    assert set(DPDPA_CRITERIA_DRAFT) == set(ids)


def test_draft_criteria_shape():
    seen: set[str] = set()
    for req_id, criteria in DPDPA_CRITERIA_DRAFT.items():
        assert 2 <= len(criteria) <= 5, req_id
        assert any(c.kind == "design" for c in criteria), req_id
        for c in criteria:
            assert isinstance(c, TestCriterion)
            assert re.fullmatch(re.escape(req_id) + r"\.TC[1-9]\d*", c.id), c.id
            assert c.id not in seen, c.id
            seen.add(c.id)
            assert c.kind in {"design", "operating"}, c.id
            for field in ("id", "statement", "kind", "evidence_hint", "source_basis"):
                assert getattr(c, field).strip(), (c.id, field)
    assert set(DPDPA_CRITERIA_REVIEW_META) == seen
    for cid, (confidence, note) in DPDPA_CRITERIA_REVIEW_META.items():
        assert confidence in {"high", "medium", "low"}, cid
        assert note.strip(), cid


def test_practice_criteria_are_capped_at_medium_confidence():
    for criteria in DPDPA_CRITERIA_DRAFT.values():
        for c in criteria:
            if c.source_basis.startswith("practice"):
                assert DPDPA_CRITERIA_REVIEW_META[c.id][0] != "high", c.id


def test_export_is_deterministic_and_complete(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    export_criteria_review.main(["--out", str(a)])
    export_criteria_review.main(["--out", str(b)])
    assert a.read_bytes() == b.read_bytes()

    lines = a.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(export_criteria_review.COLUMNS)
    total = sum(len(v) for v in DPDPA_CRITERIA_DRAFT.values())
    rows = export_criteria_review.build_rows("app.frameworks.criteria.dpdpa_draft")
    assert len(rows) == total
    assert all(r["decision"] == r["edited_statement"] == r["reviewer_note"] == "" for r in rows)
