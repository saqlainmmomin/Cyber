"""End-to-end coverage for finding #2 (PR #9 remediation): an incomplete
gap-analysis response must not reach persistence/scoring as a false 100%,
on both the single-framework and multi-framework analyzer paths.

Mocks at the `_call_llm` seam (not `run_gap_analysis`/
`run_multi_framework_analysis` themselves) so the real analyzer pipeline —
including `validate_and_filter` — actually runs.
"""

import json

from app.dpdpa.framework import get_all_requirements
from app.schemas.llm_output import IncompleteAssessmentError
from app.services import claude_analyzer


def _fake_response(text: str) -> dict:
    return {
        "text": text,
        "usage": {
            "input_tokens": 1,
            "output_tokens": 1,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        },
    }


def test_run_gap_analysis_raises_on_incomplete_response(monkeypatch):
    known_ids = {r["id"] for r in get_all_requirements()}
    one_id = next(iter(known_ids))
    incomplete_response = json.dumps(
        {
            "executive_summary": "s",
            "assessments": [{"requirement_id": one_id, "compliance_status": "compliant"}],
        }
    )
    monkeypatch.setattr(
        claude_analyzer, "_call_llm", lambda **_kwargs: _fake_response(incomplete_response)
    )

    try:
        claude_analyzer.run_gap_analysis(
            company_name="Acme",
            industry="saas",
            company_size="sme",
            description=None,
            responses=[],
            documents=[],
        )
        assert False, "expected IncompleteAssessmentError"
    except IncompleteAssessmentError:
        pass


def test_run_multi_framework_analysis_does_not_produce_false_complete_report(monkeypatch):
    from app.main import _register_frameworks
    from app.frameworks.registry import FrameworkRegistry

    _register_frameworks()
    fw_id = "iso27001"
    known_ids = {c.id for c in FrameworkRegistry.get(fw_id).all_controls()}
    one_id = next(iter(known_ids))
    incomplete_response = json.dumps(
        {
            "executive_summary": "s",
            "assessments": [{"requirement_id": one_id, "compliance_status": "compliant"}],
        }
    )
    monkeypatch.setattr(
        claude_analyzer, "_call_llm", lambda **_kwargs: _fake_response(incomplete_response)
    )

    result = claude_analyzer.run_multi_framework_analysis(
        framework_ids=[fw_id],
        company_name="Acme",
        industry="saas",
        company_size="sme",
        description=None,
        responses=[],
        documents=[],
    )

    fw_result = result["frameworks"][fw_id]
    # The per-framework try/except in run_multi_framework_analysis (already
    # the established partial-failure design for this path — see the
    # docstring in app/schemas/llm_output.py::IncompleteAssessmentError)
    # must catch the rejection and mark the framework as failed rather than
    # persist a report scored over the single surviving item.
    assert "error" in fw_result
    assert fw_result["parsed"]["assessments"] == []
