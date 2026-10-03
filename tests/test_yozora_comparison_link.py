"""Yozora backend item 5: the comparison page links to the current assessment's report.

Handoff: tasks/handoffs/2026-10-03-yozora-backend-features.md. Fixtures are the comparison ones of
tests/test_no_blended_scoring.py.
"""

from tests.test_no_blended_scoring import (  # noqa: F401 - fixtures are used by name
    _assessment,
    _report,
    _scores,
    client,
    db_session,
    registered_frameworks,
)


def test_comparison_page_links_the_current_report(client, db_session):
    old = _assessment(db_session, ["dpdpa"], company_name="Link Co")
    new = _assessment(db_session, ["dpdpa"], company_name="Link Co")
    _report(db_session, old, {"dpdpa": _scores("dpdpa", "partially_compliant")})
    _report(db_session, new, {"dpdpa": _scores("dpdpa")})

    response = client.get(f"/assessments/{new.id}/compare/{old.id}")
    assert response.status_code == 200
    assert "data-current-report-link" in response.text
    assert "Open current report" in response.text
    # The current (newer) assessment's Report tab, not the previous one's.
    assert f'href="/assessments/{new.id}?tab=report"' in response.text
    assert f'href="/assessments/{old.id}?tab=report"' not in response.text
