"""Regression coverage for the P6-3b adversarial review fixes."""

from __future__ import annotations

import json
from types import SimpleNamespace

from app.services import desk_review, desk_review_v2
from app.services.citations import CitableSource


class _RecordingDB:
    def __init__(self):
        self.rows = []
        self.commit_count = 0

    def add(self, row):
        self.rows.append(row)

    def flush(self):
        return None

    def commit(self):
        self.commit_count += 1


class _Stage1ClaimSet:
    llm_calls = ()

    def to_json(self):
        return json.dumps({"stage": 1})


def _review_objects():
    assessment = SimpleNamespace(
        id="assessment-1",
        frameworks=["dpdpa"],
        desk_review_status="analyzing",
    )
    summary = SimpleNamespace(
        assessment_id=assessment.id,
        status="analyzing",
        error_message=None,
        raw_ai_response=None,
        document_catalog=None,
        coverage_summary=None,
        completed_at=None,
    )
    return assessment, summary


def test_source_loading_failure_marks_summary_error(monkeypatch):
    assessment, summary = _review_objects()
    db = _RecordingDB()

    def fail_loading(*_args, **_kwargs):
        raise KeyError("missing active evidence version")

    monkeypatch.setattr(desk_review_v2, "load_source_documents", fail_loading)

    result = desk_review_v2.run_desk_review_v2(db, assessment, summary, {})

    assert result is summary
    assert summary.status == "error"
    assert summary.error_message == desk_review_v2.V2_FAILED_MESSAGE.format(
        error="KeyError: 'missing active evidence version'"
    )
    assert assessment.desk_review_status == "error"
    assert db.commit_count == 1


def test_metadata_fallback_failure_keeps_stage_one_claims(monkeypatch):
    assessment, summary = _review_objects()
    db = _RecordingDB()
    claim_set = _Stage1ClaimSet()
    adapted = {}

    monkeypatch.setattr(desk_review_v2, "load_source_documents", lambda *_args: [])
    monkeypatch.setattr(desk_review_v2, "run_stages_0_1", lambda *_args, **_kwargs: claim_set)

    def fail_fallback(*_args, **_kwargs):
        raise RuntimeError("metadata provider unavailable")

    monkeypatch.setattr(desk_review_v2, "fill_metadata_gaps", fail_fallback)
    monkeypatch.setattr(desk_review_v2, "_incomplete_errors", lambda _claim_set: {})

    def adapt(stage_one_claims, framework_id):
        adapted[framework_id] = stage_one_claims
        return {
            "document_catalog": [],
            "evidence_map": {},
            "absence_findings": [],
            "signal_flags": [],
            "coverage_summary": {},
        }

    monkeypatch.setattr(desk_review_v2, "claims_to_desk_review_result", adapt)
    monkeypatch.setattr(desk_review_v2, "_persist_findings", lambda **_kwargs: None)

    result = desk_review_v2.run_desk_review_v2(db, assessment, summary, {})

    assert result is summary
    assert summary.status == "completed"
    assert summary.error_message is None
    assert assessment.desk_review_status == "completed"
    assert adapted == {"dpdpa": claim_set}
    assert json.loads(summary.raw_ai_response)["claim_set"] == {"stage": 1}


def test_v1_citation_string_falls_back_to_quote_grounding():
    db = _RecordingDB()
    source = CitableSource(
        evidence_id="evidence-1",
        version_id="version-1",
        filename="policy.pdf",
        text="Section 4.2 requires consent before processing.",
    )

    desk_review._persist_findings(
        db=db,
        assessment_id="assessment-1",
        framework_id="dpdpa",
        result={
            "evidence_map": {
                "REQ-1": [
                    {
                        "document": "policy.pdf",
                        "quote": "requires consent",
                        "citation": "Section 4.2",
                    }
                ]
            },
            "absence_findings": [],
            "signal_flags": [],
        },
        doc_id_by_filename={},
        sources=[source],
    )

    citations = json.loads(db.rows[0].citations_json)
    assert citations[0]["evidence_version_id"] == "version-1"
    assert citations[0]["location_type"] == "text_span"
    assert citations[0]["excerpt"] == "requires consent"
