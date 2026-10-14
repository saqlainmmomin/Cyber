"""WP 2.4: dated penalty ceiling and comparisons over shared controls."""

import json
import re
from datetime import date
from types import SimpleNamespace

import pytest

from app.frameworks.registry import FrameworkRegistry
from app.routers import reports
from app.services.scoring import compute_delta
from tests.test_no_blended_scoring import (  # noqa: F401
    _assessment, _report, _scores, make_engagement, client, db_session, registered_frameworks,
)


@pytest.mark.parametrize("as_of,suffix", [
    (date(2027, 5, 12), " (penalty provisions apply from 13 May 2027)"),
    (date(2027, 5, 13), ""),
    (date(2027, 5, 14), ""),
])
def test_penalty_ceiling_uses_commencement_date(as_of, suffix):
    from app.routers.web import penalty_exposure_text

    assert penalty_exposure_text(250, as_of) == (
        "Maximum statutory penalty under the DPDP Act schedule: up to ₹250 crore" + suffix
    )


def test_delta_separates_four_shared_from_89_added_controls():
    def row(index, status):
        return SimpleNamespace(requirement_id=f"C{index}", requirement_title=f"Control {index}",
                               compliance_status=status)

    result = compute_delta([row(i, "compliant") for i in range(93)],
                           [row(i, "partially_compliant") for i in range(4)])
    assert result["scope"] == {"compared": 4, "added": 89, "removed": 0}
    shared = [delta for delta in result["deltas"] if not delta["is_new"]]
    assert sum(delta["status_changed"] for delta in shared) == 4
    assert result["summary"] == {"improved": 4, "regressed": 0, "unchanged": 0}
    assert result["shared_average_change"] == 50.0
    reverse = compute_delta([row(i, "compliant") for i in range(4)],
                            [row(i, "compliant") for i in range(93)])
    assert reverse["scope"] == {"compared": 4, "added": 0, "removed": 89}
    assert reverse["shared_average_change"] == 0.0
    assert compute_delta([], [row(0, "compliant")])["shared_average_change"] is None


def test_comparison_requires_engagement_and_explains_different_scopes(client, db_session):
    client.app.include_router(reports.comparison_router)
    engagement = make_engagement(db_session, "Scope Co")
    other_engagement = make_engagement(db_session, "Other Co")
    old = _assessment(db_session, ["iso27001"], company_name="Same name", engagement_id=engagement.id)
    new = _assessment(db_session, ["iso27001"], company_name="Different name", engagement_id=engagement.id)
    other = _assessment(db_session, ["iso27001"], company_name="Same name", engagement_id=other_engagement.id)
    unlinked = _assessment(db_session, ["iso27001"], company_name="Same name")
    controls = FrameworkRegistry.get("iso27001").all_controls()
    old.applicable_requirements = json.dumps([control.id for control in controls[:4]])
    for assessment in (old, new, other, unlinked):
        _report(db_session, assessment, {"iso27001": _scores("iso27001", "partially_compliant" if assessment is old else "compliant")})

    for prefix in ("/assessments", "/api/assessments"):
        for invalid in (other, unlinked):
            response = client.get(f"{prefix}/{new.id}/compare/{invalid.id}")
            assert response.status_code == 400
            assert response.json()["detail"] == "Assessments must belong to the same engagement"
    response = client.get(f"/assessments/{new.id}/compare/{old.id}")
    assert response.status_code == 200
    assert "These reports cover different scopes, so the overall scores are not a like-for-like change." in response.text
    visible_text = re.sub(r"<[^>]+>", "", response.text)
    assert "100% of 93 controls" in visible_text
    assert "50% of 4 controls" in visible_text
    assert "Newly assessed: 89" in response.text
    assert "No longer assessed: 0" in response.text
    assert "4 changed" in response.text and "89 changed" not in response.text
    assert "average change +50.0 points" in response.text
    assert "+50.0%" not in response.text
    data = client.get(f"/api/assessments/{new.id}/compare/{old.id}").json()
    assert data["scope"] == {"compared": 4, "added": 89, "removed": 0}
    assert data["framework_deltas"][0]["scope"] == data["scope"]
    summary = client.get(f"/assessments/{new.id}/report-summary")
    assert f'href="/assessments/{new.id}/compare/{old.id}"' in summary.text
