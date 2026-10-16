"""WP 2.5 scope reasons and risk counting contract."""

import pytest

from app.services import board_derive, scope_profiler, vocabulary as vocab
from app.schemas.llm_output import GapAssessmentItem


@pytest.mark.parametrize("requirement, answer, reason", [
    ("CB.TRANSFER.1", "SCP.1", "the organisation does not transfer personal data outside India"),
    ("CH4.CHILD.1", "SCP.2", "the organisation does not process children's personal data"),
    ("CH4.SDF.1", "SCP.3", "the organisation is not designated, or likely to be designated, a Significant Data Fiduciary"),
    ("CH2.SECURITY.3", "SCP.5", "the organisation does not use third-party processors"),
])
def test_exclusion_reason(requirement, answer, reason):
    assert scope_profiler.exclusion_reason(requirement, {answer: "no"}) == f"Out of scope: {reason} (scope answer {answer}: No)."
    assert scope_profiler.exclusion_reason(requirement, {}) == "Outside the recorded assessment scope."
    assert scope_profiler.exclusion_reason(requirement, {answer: "yes"}) == "Outside the recorded assessment scope."


def test_exclusion_reason_non_dpdpa():
    assert scope_profiler.exclusion_reason("ISO.A5.1", {"SCP.2": "no"}) == "Outside the recorded assessment scope."


@pytest.mark.parametrize("risk", [None, "", "urgent", " High "])
def test_risk_normalization_and_display(risk):
    expected = "high" if risk == " High " else ""
    assert vocab.normalize_risk(risk) == expected
    assert vocab.risk_display("not_applicable", risk) == ""
    assert vocab.risk_display("partially_compliant", risk) == ("High" if expected else "Not rated")


@pytest.mark.parametrize("fields", [{}, {"risk_level": None}])
def test_model_schema_keeps_missing_risk_blank(fields):
    assert GapAssessmentItem(requirement_id="REQ", compliance_status="compliant", **fields).risk_level == ""


def test_unrated_gap_excluded_from_risk_matrix_and_severity_dashboard():
    sections = [{"framework_id": "dpdpa", "name": "India DPDPA"}]
    register = [{"framework_id": "dpdpa", "outcome": "partially_compliant", "risk_level": ""}]
    assert board_derive.build_risk_matrix(sections, register) == {"dpdpa": {"critical": 0, "high": 0, "medium": 0, "low": 0}}
    dashboard = board_derive.build_severity_dashboard(sections, register)
    assert set(dashboard) == {"critical", "high", "medium", "low"}
    assert all(row["total"] == 0 for row in dashboard.values())
