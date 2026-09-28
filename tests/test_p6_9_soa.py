"""Contract tests for P6-9: ISO 27001 Statement of Applicability (SoA) in the board report.

Handoff: tasks/handoffs/2026-09-28-p6-9-soa-roadmap-comparison.md (D-P6-9-B, D-P6-9-C).
On main these fail only because app.services.soa, the SoA route and the schema-v2 document
keys do not exist yet. No network, no LLM.
"""

from __future__ import annotations

import json

from app.frameworks.registry import FrameworkRegistry
from app.models.audit_event import AuditEvent
from app.services import approved_report
from tests.p6_9_support import (  # noqa: F401  (fixtures are used by name)
    _no_llm,
    _register_frameworks,
    build,
    control_ids,
    db,
    db_path,
    decide,
    gate,
    http,
    module,
    new_engagement,
    released_assessment,
    upload_root,
    analyse,
    seed,
    item,
)

P6_8_DOCUMENT_KEYS = {
    "schema_version", "kind", "snapshot", "firm_name", "company_name", "engagement_name",
    "assessment_id", "frameworks", "basis", "release", "summary", "top_risks", "roadmap",
    "not_assessed", "framework_sections", "sign_off", "appendices", "source",
}
ISO_OUTCOMES = {
    "ISO.A5.1": ("compliant", "low"),
    "ISO.A5.2": ("partially_compliant", "high"),
    "ISO.A5.3": ("non_compliant", "critical"),
    "ISO.A5.4": ("insufficient_evidence", "medium"),
    "ISO.A5.5": ("not_applicable", "low"),
}


def _soa():
    return module("app.services.soa")


def _fixture(db, http, gate, monkeypatch, frameworks=("dpdpa", "iso27001")):
    outcomes = {("iso27001", rid): value for rid, value in ISO_OUTCOMES.items()}
    if "dpdpa" in frameworks:
        outcomes = {("dpdpa", control_ids("dpdpa")[0]): ("compliant", "low"), **outcomes}
    assessment, conclusions = released_assessment(
        db, http, gate, monkeypatch, new_engagement(db), frameworks=frameworks, outcomes=outcomes,
    )
    approved_report.record_release(db, assessment, actor="consultant:Priya")
    db.commit()
    db.expire_all()
    return assessment, conclusions


def test_scenario_1_document_schema_v2_and_soa_rows_cover_every_annex_a_control(db, http, gate, monkeypatch):
    """D-P6-9-B/E: schema v2 adds `soa` and `prior_period`; one SoA row per Annex A control, in pack order."""
    soa = _soa()
    board = module("app.services.board_report")
    assessment, _ = _fixture(db, http, gate, monkeypatch)
    document = build(db, assessment)

    assert board.DOCUMENT_SCHEMA_VERSION == 2 and document["schema_version"] == 2
    assert set(document) == P6_8_DOCUMENT_KEYS | {"soa", "prior_period"}
    assert all("pack_version" in framework for framework in document["frameworks"])

    statement = document["soa"]
    iso = FrameworkRegistry.get("iso27001")
    assert soa.FRAMEWORK_ID == "iso27001"
    assert set(statement) == {
        "framework_id", "framework_name", "framework_version", "intro", "reliance", "notes", "totals", "rows",
    }
    assert (statement["framework_id"], statement["framework_name"], statement["framework_version"]) == (
        "iso27001", iso.name, iso.version,
    )
    assert statement["intro"] == soa.INTRO_TEXT.format(framework=f"{iso.name}:{iso.version}")
    assert statement["reliance"] == soa.RELIANCE_TEXT
    rows = statement["rows"]
    assert [row["control_id"] for row in rows] == control_ids("iso27001")
    assert len(rows) == iso.control_count() == 93
    assert set(rows[0]) == {
        "control_id", "reference", "title", "theme", "applicability", "applicability_label", "outcome",
        "implementation_label", "justification", "justification_by", "justification_on",
    }
    by_id = {row["control_id"]: row for row in rows}
    expected = {
        "ISO.A5.1": ("applicable", "Applicable", "compliant", "Implemented"),
        "ISO.A5.2": ("applicable", "Applicable", "partially_compliant", "Partially implemented"),
        "ISO.A5.3": ("applicable", "Applicable", "non_compliant", "Not implemented"),
        "ISO.A5.4": ("applicable", "Applicable", "insufficient_evidence", "Not determined: insufficient evidence"),
        "ISO.A5.5": ("excluded", "Excluded", "not_applicable", "Not applicable"),
        "ISO.A5.6": ("not_assessed", "Not determined", None, soa.NOT_ASSESSED_LABEL),
    }
    for control_id, (applicability, applicability_label, outcome, implementation) in expected.items():
        row = by_id[control_id]
        assert (row["applicability"], row["applicability_label"], row["outcome"], row["implementation_label"]) == (
            applicability, applicability_label, outcome, implementation,
        ), control_id
    control = iso.get_control("ISO.A5.1")
    assert (by_id["ISO.A5.1"]["reference"], by_id["ISO.A5.1"]["title"]) == (control.reference, control.title)
    assert by_id["ISO.A5.1"]["theme"] == "Organizational Controls"
    assert by_id["ISO.A5.1"]["justification"] is None and by_id["ISO.A5.1"]["justification_by"] is None

    assert statement["totals"] == {
        "controls": 93, "applicable": 4, "excluded": 1, "not_assessed": 88, "pending": 0,
        "implemented": 1, "partially_implemented": 1, "not_implemented": 1, "not_determined": 1,
        "justification_missing": 93,
    }
    assert statement["notes"] == [
        soa.NOT_ASSESSED_NOTE.format(count=88),
        soa.MISSING_JUSTIFICATION_NOTE.format(count=93),
    ]


def test_scenario_2_justification_is_an_append_only_audit_trail(db, http, gate, monkeypatch):
    """D-P6-9-C: justifications are audit events; latest wins; unchanged writes nothing; bad input refused."""
    soa = _soa()
    assessment, _ = _fixture(db, http, gate, monkeypatch)

    def events():
        return (
            db.query(AuditEvent)
            .filter_by(action=soa.AUDIT_ACTION, entity_type="assessment", entity_id=assessment.id)
            .count()
        )

    assert soa.AUDIT_ACTION == "assessment.soa_justification_updated"
    saved = soa.record_justification(
        db, assessment, requirement_id="ISO.A5.5",
        justification="  No  outsourced\n development.  ", actor="consultant:Priya",
    )
    assert saved == "No outsourced development."
    db.commit()
    assert events() == 1
    event = db.query(AuditEvent).filter_by(action=soa.AUDIT_ACTION).one()
    assert json.loads(event.metadata_json) == {
        "framework_id": "iso27001", "requirement_id": "ISO.A5.5",
        "before": None, "after": "No outsourced development.",
    }

    # Unchanged text writes nothing.
    soa.record_justification(db, assessment, requirement_id="ISO.A5.5", justification="No outsourced development.", actor="consultant:Priya")
    assert events() == 1
    soa.record_justification(db, assessment, requirement_id="ISO.A5.5", justification="Development is not outsourced.", actor="consultant:Ravi")
    db.commit()
    assert events() == 2
    current = soa.current_justifications(db, assessment)
    assert current["ISO.A5.5"].text == "Development is not outsourced."
    assert current["ISO.A5.5"].recorded_by == "Ravi"

    # Clearing records an event and removes the justification; history keeps all three.
    soa.record_justification(db, assessment, requirement_id="ISO.A5.5", justification="   ", actor="consultant:Ravi")
    db.commit()
    assert events() == 3 and "ISO.A5.5" not in soa.current_justifications(db, assessment)
    soa.record_justification(db, assessment, requirement_id="ISO.A5.1", justification="Policy set approved by the board.", actor="consultant:Priya")
    db.commit()

    for requirement_id, text, message in (
        ("ISO.A5.1", "x" * (soa.JUSTIFICATION_MAX_CHARS + 1), soa.TOO_LONG_MESSAGE),
        ("ISO.Z9.9", "fine", soa.UNKNOWN_CONTROL_MESSAGE),
        (control_ids("dpdpa")[0], "fine", soa.UNKNOWN_CONTROL_MESSAGE),
    ):
        try:
            soa.record_justification(db, assessment, requirement_id=requirement_id, justification=text, actor="consultant:Priya")
        except soa.SoAError as exc:
            assert exc.message == message and exc.status_code == 400
        else:
            raise AssertionError(f"{requirement_id} was accepted")
    db.rollback()
    assert events() == 4

    row = {r["control_id"]: r for r in build(db, assessment)["soa"]["rows"]}["ISO.A5.1"]
    assert row["justification"] == "Policy set approved by the board."
    assert row["justification_by"] == "Priya"
    assert isinstance(row["justification_on"], str) and len(row["justification_on"]) == 10


def test_scenario_3_soa_page_and_save_route(db, http, gate, monkeypatch):
    """D-P6-9-D: GET /assessments/{id}/soa lists 93 rows; POST saves with a toast; errors write nothing."""
    soa = _soa()
    assessment, _ = _fixture(db, http, gate, monkeypatch)
    page = http.get(f"/assessments/{assessment.id}/soa")
    assert page.status_code == 200, page.text
    assert page.text.count("data-soa-row=") == 93
    assert 'data-soa-row="ISO.A5.5" data-applicability="excluded"' in page.text
    assert page.text.count("data-soa-justification-form") == 93
    assert f'hx-post="/api/assessments/{assessment.id}/soa/justifications"' in page.text
    assert "Rationale for ISO.A5.5" in page.text  # approved rationale shown as a hint, not stored

    saved = http.post(
        f"/api/assessments/{assessment.id}/soa/justifications",
        data={"requirement_id": "ISO.A5.5", "justification": "Not in scope: no outsourcing.", "reviewer_name": "Priya"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"status": "saved", "requirement_id": "ISO.A5.5", "justification": "Not in scope: no outsourcing."}
    assert saved.headers["X-Toast-Message"] == soa.SAVED_MESSAGE
    assert saved.headers["X-Toast-Type"] == "success"
    assert soa.current_justifications(db, assessment)["ISO.A5.5"].recorded_by == "Priya"
    assert "Not in scope: no outsourcing." in http.get(f"/assessments/{assessment.id}/soa").text

    before = db.query(AuditEvent).filter_by(action=soa.AUDIT_ACTION).count()
    too_long = http.post(
        f"/api/assessments/{assessment.id}/soa/justifications",
        data={"requirement_id": "ISO.A5.5", "justification": "y" * 1001, "reviewer_name": "Priya"},
    )
    assert too_long.status_code == 400
    assert too_long.json()["detail"] == soa.TOO_LONG_MESSAGE
    assert too_long.headers["X-Toast-Type"] == "error"
    assert db.query(AuditEvent).filter_by(action=soa.AUDIT_ACTION).count() == before

    assert http.post(
        "/api/assessments/does-not-exist/soa/justifications",
        data={"requirement_id": "ISO.A5.5", "justification": "x"},
    ).status_code == 404

    dpdpa_only = seed(db, new_engagement(db), frameworks=["dpdpa"], applicable=control_ids("dpdpa")[:1])
    assert http.get(f"/assessments/{dpdpa_only.id}/soa").status_code == 404
    refused = http.post(
        f"/api/assessments/{dpdpa_only.id}/soa/justifications",
        data={"requirement_id": "ISO.A5.5", "justification": "x"},
    )
    assert refused.status_code == 404 and refused.json()["detail"] == soa.NOT_IN_SCOPE_MESSAGE

    versions = http.get(f"/assessments/{assessment.id}/snapshots")
    assert f'data-soa-link href="/assessments/{assessment.id}/soa"' in versions.text
    assert "data-soa-link" not in http.get(f"/assessments/{dpdpa_only.id}/snapshots").text


def test_scenario_4_soa_is_conditional_on_iso_and_rendered_as_appendix_d(db, http, gate, monkeypatch):
    """D-P6-9-B/G: no SoA without ISO; with ISO it is the last section, 'Appendix D', one row per control."""
    board = module("app.services.board_report")
    dpdpa_only, _ = released_assessment(
        db, http, gate, monkeypatch, new_engagement(db), frameworks=["dpdpa"],
        outcomes={("dpdpa", control_ids("dpdpa")[0]): ("compliant", "low")},
    )
    approved_report.record_release(db, dpdpa_only, actor="consultant:Priya")
    db.commit()
    document = build(db, dpdpa_only)
    assert document["soa"] is None
    html = board.render_html(document, embed_fonts=False)
    assert 'data-section="soa"' not in html and "Statement of Applicability" not in html

    assessment, _ = _fixture(db, http, gate, monkeypatch)
    html = board.render_html(build(db, assessment), embed_fonts=False)
    assert "<h2>Appendix D: Statement of Applicability</h2>" in html
    assert html.index('data-section="evidence-register"') < html.index('data-section="soa"')
    assert html.count("data-soa-control=") == 93
    assert "Justification not recorded" in html
    style = html[html.index("<style>"):html.index("</style>")]
    assert "ISO.A5" not in style


def test_scenario_5_status_comes_only_from_approved_decisions(db, http, gate, monkeypatch):
    """D-P6-9-B: an unapproved proposal is 'pending', never its AI outcome; an edit uses the edited outcome."""
    soa = _soa()
    engagement = new_engagement(db)
    ids = ["ISO.A5.1", "ISO.A5.2", "ISO.A5.3"]
    assessment = seed(db, engagement, frameworks=["iso27001"], applicable=ids)
    conclusions = analyse(
        monkeypatch, gate, db, assessment,
        {"iso27001": [item("ISO.A5.1", "compliant", "low"), item("ISO.A5.2", "non_compliant", "high"), item("ISO.A5.3", "compliant", "low")]},
    )
    decide(db, conclusions[("iso27001", "ISO.A5.1")])
    decide(db, conclusions[("iso27001", "ISO.A5.2")], "edited", outcome="not_applicable", risk_level="low")
    db.commit()  # ISO.A5.3 stays an unreviewed AI proposal
    statement = soa.build_soa(db, assessment, approved_report.build_approved_report(db, assessment))
    rows = {row["control_id"]: row for row in statement["rows"]}
    assert (rows["ISO.A5.1"]["applicability"], rows["ISO.A5.1"]["outcome"]) == ("applicable", "compliant")
    assert (rows["ISO.A5.2"]["applicability"], rows["ISO.A5.2"]["outcome"]) == ("excluded", "not_applicable")
    assert (rows["ISO.A5.3"]["applicability"], rows["ISO.A5.3"]["outcome"]) == ("pending", None)
    assert rows["ISO.A5.3"]["applicability_label"] == "Awaiting decision"
    assert rows["ISO.A5.3"]["implementation_label"] == soa.PENDING_LABEL
    assert statement["totals"]["pending"] == 1
    dpdpa_assessment = seed(db, engagement, frameworks=["dpdpa"], applicable=control_ids("dpdpa")[:1])
    assert soa.build_soa(db, dpdpa_assessment, approved_report.build_approved_report(db, dpdpa_assessment)) is None
