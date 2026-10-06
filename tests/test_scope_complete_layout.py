"""Scope tab readability: ruled checklist groups with counts and block-level detail lines."""

from __future__ import annotations

import json
import re

from tests.test_p5_5_scoping_evidence import (  # noqa: F401 - fixtures are used by name
    _assessment,
    client,
    db_session,
    registered_frameworks,
)


def _scope_page(client, db_session) -> str:
    assessment = _assessment(db_session, ["dpdpa", "iso27001"])
    assessment.scope_answers = json.dumps({"SCP.1": "no", "ISO.SCP.4": "fully_remote"})
    db_session.commit()
    response = client.get(f"/assessments/{assessment.id}?tab=scope")
    assert response.status_code == 200
    return response.text


def test_checklist_groups_are_ruled_and_counted(client, db_session):
    page = _scope_page(client, db_session)
    groups = re.findall(
        r'<div class="between" data-checklist-group="(required|recommended)"[^>]*><h3>(Required|Recommended)</h3><span class="sub num">(\d+) items?</span></div>',
        page,
    )
    assert [group for group, _heading, _count in groups] == ["required", "recommended"]
    assert page.index('data-checklist-group="required"') < page.index('data-checklist-group="recommended"')
    required_count = int(groups[0][2])
    recommended_count = int(groups[1][2])
    assert page.count("data-checklist-item") == required_count + recommended_count
    assert "Scope confirmed" in page and "Evidence request" in page


def test_checklist_reasons_sit_on_their_own_line(client, db_session):
    page = _scope_page(client, db_session)
    rows = re.findall(r'<div class="check-row" data-checklist-item[^>]*>(.*?)</div></div>', page)
    assert rows
    for row in rows:
        assert re.search(r'</b><span class="sub" style="display:block;margin-top:var\(--s-1\)">', row)


def test_excluded_and_proposed_lists_use_line_lists(client, db_session):
    page = _scope_page(client, db_session)
    assert '<ul class="line-list mt" data-scope-excluded>' in page
    assert '<ul class="line-list mt" data-scope-proposed>' in page
    assert "proposed as likely not applicable" in page
    assert "Cross-border transfers: not applicable" in page
    assert 'class="checks mt"' not in page
    assert "data-rfi-link" in page
