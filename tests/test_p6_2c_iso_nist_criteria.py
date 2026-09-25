"""P6-2c: ISO 27001 (Annex A + clauses 4-10) and NIST CSF draft criteria sheets."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

from app.frameworks.criteria.iso27001_draft import (
    ISO27001_CLAUSE_REQUIREMENTS_DRAFT,
    ISO27001_CRITERIA_DRAFT,
    ISO27001_CRITERIA_REVIEW_META,
    ISO27001_OWN_WORDS_DRAFT,
)
from app.frameworks.criteria.nist_csf_draft import (
    NIST_CSF_CRITERIA_DRAFT,
    NIST_CSF_CRITERIA_REVIEW_META,
)
from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
from app.frameworks.schema import TestCriterion
from scripts import export_criteria_review

ROOT = Path(__file__).resolve().parent.parent

ISO_ANNEX_IDS = [c.id for c in ISO27001_DEFINITION.all_controls()]
ISO_CLAUSE_IDS = list(ISO27001_CLAUSE_REQUIREMENTS_DRAFT)
NIST_IDS = [c.id for c in NIST_CSF_DEFINITION.all_controls()]

# framework -> (draft, meta, the only citation prefix that may carry `high`)
DRAFTS = {
    "iso27001": (ISO27001_CRITERIA_DRAFT, ISO27001_CRITERIA_REVIEW_META, "ISO/IEC 27001:2022"),
    "nist_csf": (NIST_CSF_CRITERIA_DRAFT, NIST_CSF_CRITERIA_REVIEW_META, "NIST CSF 2.0"),
}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _shingles(text: str, n: int) -> set[tuple[str, ...]]:
    w = _words(text)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


# ── Coverage ──────────────────────────────────────────────────────────────

def test_iso_covers_every_annex_a_control_and_the_clauses_in_order():
    assert len(ISO_ANNEX_IDS) == 93
    assert len(ISO_CLAUSE_IDS) == 25
    assert all(re.fullmatch(r"ISO\.C(4|5|6|7|8|9|10)(\.\d+){1,2}", cid) for cid in ISO_CLAUSE_IDS)
    for required in ("ISO.C6.1.1", "ISO.C6.1.2", "ISO.C6.1.3", "ISO.C6.3", "ISO.C7.5",
                     "ISO.C9.2", "ISO.C10.1", "ISO.C10.2"):
        assert required in ISO_CLAUSE_IDS, required
    assert not set(ISO_CLAUSE_IDS) & set(ISO_ANNEX_IDS)
    # Clauses first, then Annex A in framework order.
    assert list(ISO27001_CRITERIA_DRAFT) == ISO_CLAUSE_IDS + ISO_ANNEX_IDS


def test_nist_covers_every_pack_requirement_in_order():
    assert len(NIST_IDS) == 94
    assert list(NIST_CSF_CRITERIA_DRAFT) == NIST_IDS


def test_iso_clause_requirements_are_complete():
    sections = {"context", "leadership", "planning", "support", "operation", "evaluation", "improvement"}
    for cid, req in ISO27001_CLAUSE_REQUIREMENTS_DRAFT.items():
        assert set(req) == {"title", "description", "criticality", "section", "reference"}, cid
        assert all(str(v).strip() for v in req.values()), cid
        assert req["criticality"] in {"critical", "high", "medium", "low"}, cid
        assert req["section"] in sections, cid
        assert req["description"] == ISO27001_OWN_WORDS_DRAFT[cid], cid


# ── Criteria shape and confidence ─────────────────────────────────────────

@pytest.mark.parametrize("framework", sorted(DRAFTS))
def test_draft_criteria_shape(framework):
    draft, meta, _ = DRAFTS[framework]
    seen: set[str] = set()
    for req_id, criteria in draft.items():
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
    assert set(meta) == seen
    for cid, (confidence, note) in meta.items():
        assert confidence in {"high", "medium", "low"}, cid
        assert isinstance(note, str), cid  # blank unless a version point matters


@pytest.mark.parametrize("framework", sorted(DRAFTS))
def test_practice_and_guidance_only_criteria_are_never_high(framework):
    draft, meta, primary = DRAFTS[framework]
    for criteria in draft.values():
        for c in criteria:
            if meta[c.id][0] != "high":
                continue
            assert not c.source_basis.startswith("practice"), c.id
            # 27002 guidance / CSF implementation examples / SP 800-53 alone cap at medium.
            assert primary in c.source_basis, c.id


@pytest.mark.parametrize("framework", sorted(DRAFTS))
def test_repo_departures_are_low(framework):
    draft, meta, _ = DRAFTS[framework]
    for criteria in draft.values():
        for c in criteria:
            if "[repo says" in c.source_basis:
                assert meta[c.id][0] == "low", c.id


# ── ISO own-words descriptions (D-P6-J, D4) ───────────────────────────────

def test_iso_own_words_cover_every_id():
    assert list(ISO27001_OWN_WORDS_DRAFT) == ISO_CLAUSE_IDS + ISO_ANNEX_IDS
    assert all(d.strip() for d in ISO27001_OWN_WORDS_DRAFT.values())


def test_iso_own_words_do_not_copy_the_repo_descriptions():
    """Verbatim-copy guard: the pack's descriptions are near-verbatim ISO text."""
    repo = {c.id: c.description for c in ISO27001_DEFINITION.all_controls()}
    repo_shingles = set().union(*(_shingles(d, 8) for d in repo.values()))
    for rid, own in ISO27001_OWN_WORDS_DRAFT.items():
        norm_own = " ".join(_words(own))
        for desc in repo.values():
            norm_repo = " ".join(_words(desc))
            assert norm_own != norm_repo, rid
            assert norm_repo not in norm_own, rid
        # No run of 8+ words shared with any current pack description.
        assert not _shingles(own, 8) & repo_shingles, rid


# ── Export ────────────────────────────────────────────────────────────────

def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.parametrize("framework", sorted(DRAFTS))
def test_export_is_deterministic_and_complete(framework, tmp_path):
    draft, meta, _ = DRAFTS[framework]
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    da, db = tmp_path / "da.csv", tmp_path / "db.csv"
    extra = lambda p: ["--descriptions-out", str(p)] if framework == "iso27001" else []  # noqa: E731
    export_criteria_review.main(["--framework", framework, "--out", str(a), *extra(da)])
    export_criteria_review.main(["--framework", framework, "--out", str(b), *extra(db)])
    assert a.read_bytes() == b.read_bytes()

    lines = a.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(export_criteria_review.COLUMNS)
    rows = _read(a)
    assert [r["criterion_id"] for r in rows] == [c.id for v in draft.values() for c in v]
    assert all(r["drafter_confidence"] == meta[r["criterion_id"]][0] for r in rows)
    assert all(r["decision"] == r["edited_statement"] == r["reviewer_note"] == "" for r in rows)

    if framework == "iso27001":
        assert da.read_bytes() == db.read_bytes()
        assert da.read_text(encoding="utf-8").splitlines()[0] == ",".join(
            export_criteria_review.DESCRIPTION_COLUMNS
        )
        desc = _read(da)
        assert [r["requirement_id"] for r in desc] == ISO_CLAUSE_IDS + ISO_ANNEX_IDS
        assert [r["source"] for r in desc] == ["clause"] * 25 + ["annex_a"] * 93
        for r in desc[:25]:
            assert r["requirement_title"] == ISO27001_CLAUSE_REQUIREMENTS_DRAFT[r["requirement_id"]]["title"]
        assert all(r["own_words_description"] == ISO27001_OWN_WORDS_DRAFT[r["requirement_id"]] for r in desc)
        assert all(r["decision"] == r["edited_description"] == r["reviewer_note"] == "" for r in desc)


def test_committed_sheets_match_the_drafts(tmp_path):
    review = ROOT / "tasks" / "criteria-review"
    export_criteria_review.main(["--framework", "iso27001", "--out", str(tmp_path / "iso.csv"),
                                 "--descriptions-out", str(tmp_path / "iso-desc.csv")])
    export_criteria_review.main(["--framework", "nist_csf", "--out", str(tmp_path / "nist.csv")])
    assert (tmp_path / "iso.csv").read_bytes() == (review / "iso27001-criteria-v1.csv").read_bytes()
    assert (tmp_path / "iso-desc.csv").read_bytes() == (review / "iso27001-descriptions-v1.csv").read_bytes()
    assert (tmp_path / "nist.csv").read_bytes() == (review / "nist-csf-criteria-v1.csv").read_bytes()


def test_descriptions_out_is_iso_only():
    with pytest.raises(SystemExit):
        export_criteria_review.main(["--framework", "nist_csf", "--out", "unused.csv",
                                     "--descriptions-out", "unused.csv"])


# ── Isolation: drafts never reach the app ─────────────────────────────────

def test_no_app_module_imports_the_drafts_outside_criteria_package():
    pattern = re.compile(r"\b(iso27001_draft|nist_csf_draft)\b")
    criteria_pkg = ROOT / "app" / "frameworks" / "criteria"
    offenders = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "app").rglob("*.py")
        if criteria_pkg not in p.parents and pattern.search(p.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_drafts_are_not_attached_to_any_control():
    for fw in (ISO27001_DEFINITION, NIST_CSF_DEFINITION):
        assert all(c.test_criteria == () for c in fw.all_controls())
