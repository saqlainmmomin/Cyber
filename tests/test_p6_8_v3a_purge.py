"""Contract test for P6-8 V3-A: a retention purge removes the new board-input rows (D-P6-8-V3-B).

The purge is the most destructive path in the app (tasks/agent-ownership.md, P4-4), so the new
`initiative_metadata` table must be in `retention.PURGE_ORDER` and scoped to the purged
engagement's assessments. Everything else V3-A adds is a column on a row the purge already
deletes. Handoff: tasks/handoffs/2026-10-01-board-report-v3-deck.md.
"""

from __future__ import annotations

from app.models.assessment import Assessment
from app.models.engagement import Engagement
from app.models.finding import Finding
from app.services import retention
from tests.test_retention import (  # noqa: F401 - fixtures are used by name
    _archive,
    _backdate_archive,
    _full_engagement,
    _register_frameworks,
    db,
    db_path,
    engine,
    gate,
    http,
    upload_root,
)


def _add_board_inputs(db, assessment_id: str, group_id: str) -> None:
    from app.models import InitiativeMetadata  # lazy: a missing model is a clean red, not a collection error

    for finding in db.query(Finding).filter_by(assessment_id=assessment_id).all():
        finding.business_impact = "Why it matters"
        finding.recommendation = "What to do"
    db.add(InitiativeMetadata(assessment_id=assessment_id, group_id=group_id, title="Initiative", complexity="low", benefit="high"))
    db.get(Assessment, assessment_id).board_asks_json = '{"asks": ["Approve"], "by": "Priya"}'
    db.commit()


def test_purge_removes_board_inputs_of_the_purged_engagement_only(db, http, gate, upload_root):
    from app.models import InitiativeMetadata

    assert retention.PURGE_ORDER.index("initiative_metadata") < retention.PURGE_ORDER.index("assessments")
    target = _full_engagement(db, http, gate, upload_root, sentinel="PURGE-SENTINEL-7Q")
    control = _full_engagement(db, http, gate, upload_root, client=target["client"], sentinel="CONTROL-SENTINEL-3K")
    _add_board_inputs(db, target["assessment"].id, "G-TARGET")
    _add_board_inputs(db, control["assessment"].id, "G-CONTROL")
    _archive(http, target["engagement"].id)
    _backdate_archive(db, target["engagement"].id, years=7)
    target_engagement = db.get(Engagement, target["engagement"].id)
    target_assessment_id = target["assessment"].id
    target_id, target_name = target_engagement.id, target_engagement.name

    plan = retention.build_purge_plan(db, target_engagement)
    assert plan.row_counts["initiative_metadata"] == 1

    response = http.post(
        f"/api/engagements/{target_id}/purge", data={"confirm_name": target_name, "reviewer_name": "Priya"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["row_counts"] == plan.row_counts
    db.expire_all()
    assert db.query(InitiativeMetadata).filter_by(assessment_id=target_assessment_id).count() == 0
    survivors = db.query(InitiativeMetadata).all()
    assert [(row.assessment_id, row.group_id) for row in survivors] == [(control["assessment"].id, "G-CONTROL")]
    control_finding = db.query(Finding).filter_by(assessment_id=control["assessment"].id).first()
    assert control_finding.business_impact == "Why it matters"
    assert db.get(Assessment, control["assessment"].id).board_asks_json is not None
