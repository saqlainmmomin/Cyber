"""Contract tests for P6-9: prior-period comparison in the board report.

Handoff: tasks/handoffs/2026-09-28-p6-9-soa-roadmap-comparison.md (D-P6-9-H, D-P6-9-I).
The comparison reads the previous *issued* board_report sidecar in the same engagement and
never re-renders or re-reads live data of the earlier assessment. On main these fail only
because app.services.prior_period and `prior_period` in the document do not exist yet.
Board report PDFs are stubbed (`stub_render`): WeasyPrint is not needed here.
"""

from __future__ import annotations

import json
import uuid
from datetime import date

from app.models.assessment import Assessment
from app.models.assessment_pack import AssessmentPack
from app.models.conclusion import Conclusion
from app.models.report_snapshot import ReportSnapshot
from app.services import approved_report, report_snapshots
from tests.p6_9_support import (  # noqa: F401  (fixtures are used by name)
    FAKE_PDF,
    PERIOD_1,
    PERIOD_2,
    _no_llm,
    _register_frameworks,
    build,
    db,
    db_path,
    gate,
    generate_board,
    http,
    issue,
    module,
    new_engagement,
    release,
    released_assessment,
    stub_render,
    upload_root,
)

P1_OUTCOMES = {
    ("dpdpa", "CH2.CONSENT.1"): ("non_compliant", "high"),
    ("dpdpa", "CH2.CONSENT.2"): ("compliant", "low"),
    ("dpdpa", "CH2.CONSENT.3"): ("partially_compliant", "medium"),
    ("iso27001", "ISO.A5.1"): ("partially_compliant", "medium"),
    ("iso27001", "ISO.A5.2"): ("compliant", "low"),
    ("iso27001", "ISO.A5.3"): ("insufficient_evidence", "medium"),
    ("iso27001", "ISO.A5.5"): ("compliant", "low"),
}
P2_OUTCOMES = {
    ("dpdpa", "CH2.CONSENT.1"): ("compliant", "low"),  # improved
    ("dpdpa", "CH2.CONSENT.2"): ("partially_compliant", "medium"),  # regressed
    ("dpdpa", "CH2.CONSENT.3"): ("partially_compliant", "medium"),  # unchanged
    ("dpdpa", "CH2.CONSENT.4"): ("non_compliant", "high"),  # new
    ("iso27001", "ISO.A5.1"): ("partially_compliant", "medium"),  # unchanged
    ("iso27001", "ISO.A5.2"): ("compliant", "low"),  # unchanged
    ("iso27001", "ISO.A5.3"): ("compliant", "low"),  # changed (from insufficient evidence)
    # ISO.A5.5 is no longer assessed
}
FRAMEWORKS = ["dpdpa", "iso27001"]
PERIOD_0 = {"period_start": date(2025, 10, 1), "period_end": date(2025, 12, 31), "evidence_cutoff": date(2026, 1, 15)}
OVERLAPPING = {"period_start": date(2026, 3, 1), "period_end": date(2026, 5, 31), "evidence_cutoff": date(2026, 6, 15)}


def _prior():
    return module("app.services.prior_period")


def _issued_period(db, http, gate, monkeypatch, engagement, *, period, outcomes=P1_OUTCOMES, company="Acme Analytics Pvt Ltd"):
    assessment, _ = released_assessment(
        db, http, gate, monkeypatch, engagement, frameworks=FRAMEWORKS, outcomes=outcomes, period=period, company=company,
    )
    release(db, assessment)
    snapshot_id = generate_board(http, assessment)
    issue(http, assessment, snapshot_id)
    db.expire_all()
    return assessment, db.get(ReportSnapshot, snapshot_id)


def _current(db, http, gate, monkeypatch, engagement, outcomes=P2_OUTCOMES):
    assessment, _ = released_assessment(
        db, http, gate, monkeypatch, engagement, frameworks=FRAMEWORKS, outcomes=outcomes, period=PERIOD_2,
    )
    release(db, assessment)
    return assessment


def _craft_issued(db, assessment, document):
    """Store and issue a board_report version from a crafted document (pack/edition edge cases)."""
    board = module("app.services.board_report")
    snapshot_id = str(uuid.uuid4())
    document = {**document, "snapshot": {**document["snapshot"], "id": snapshot_id}}
    snapshot = report_snapshots.create_board_report_snapshot(
        db, assessment=assessment, snapshot_id=snapshot_id, pdf_content=FAKE_PDF,
        document_content=board.canonical_bytes(document), actor="consultant:Priya",
    )
    report_snapshots.issue_snapshot(db, snapshot, actor="consultant:Priya")
    db.commit()
    return snapshot


def test_scenario_1_compares_with_the_previous_issued_period_from_its_sidecar(db, http, gate, monkeypatch, stub_render):
    """D-P6-9-H/I: status, prior block, per-framework counts and score deltas, ordered changes, totals."""
    prior = _prior()
    engagement = new_engagement(db)
    p1, p1_snapshot = _issued_period(db, http, gate, monkeypatch, engagement, period=PERIOD_1)
    p1_document = report_snapshots.read_board_report_document(db, p1_snapshot)
    p2 = _current(db, http, gate, monkeypatch, engagement)
    document = build(db, p2)
    comparison = document["prior_period"]

    assert set(comparison) == {"status", "intro", "notes", "prior", "frameworks", "changes", "totals"}
    assert comparison["status"] == "compared"
    assert comparison["intro"] == prior.INTRO_TEXT
    metadata = report_snapshots.generated_event(db, p1_snapshot.id)
    assert comparison["prior"] == {
        "snapshot_id": p1_snapshot.id,
        "assessment_id": p1.id,
        "version_label": "v1",
        "generated_on": p1_document["snapshot"]["generated_on"],
        "period_label": "01 Jan 2026 to 31 Mar 2026",
        "cutoff_label": "15 Apr 2026",
        "document_sha256": metadata["document_sha256"],
        "schema_version": 2,
    }
    # Neither assessment recorded an AssessmentPack row, so criteria change cannot be ruled out.
    assert comparison["notes"] == [
        prior.CRITERIA_UNKNOWN_TEXT.format(name=framework["name"]) for framework in document["frameworks"]
    ]

    frameworks = {f["framework_id"]: f for f in comparison["frameworks"]}
    assert set(frameworks["dpdpa"]) == {
        "framework_id", "name", "compared", "prior_version", "current_version", "prior_pack_version",
        "current_pack_version", "prior_score", "current_score", "score_delta", "prior_rating",
        "current_rating", "counts",
    }
    assert frameworks["dpdpa"]["counts"] == {
        "improved": 1, "regressed": 1, "unchanged": 1, "changed": 0, "new": 1, "no_longer_assessed": 0,
    }
    assert frameworks["iso27001"]["counts"] == {
        "improved": 0, "regressed": 0, "unchanged": 2, "changed": 1, "new": 0, "no_longer_assessed": 1,
    }
    prior_scores = {f["framework_id"]: f["score"] for f in p1_document["summary"]["frameworks"]}
    current_scores = {f["framework_id"]: f["score"] for f in document["summary"]["frameworks"]}
    for framework_id in FRAMEWORKS:
        entry = frameworks[framework_id]
        assert entry["compared"] is True
        assert entry["prior_score"] == prior_scores[framework_id]
        assert entry["current_score"] == current_scores[framework_id]
        assert entry["score_delta"] == round(current_scores[framework_id] - prior_scores[framework_id], 1)

    assert [(c["direction"], c["framework_id"], c["requirement_id"]) for c in comparison["changes"]] == [
        ("regressed", "dpdpa", "CH2.CONSENT.2"),
        ("improved", "dpdpa", "CH2.CONSENT.1"),
        ("changed", "iso27001", "ISO.A5.3"),
        ("new", "dpdpa", "CH2.CONSENT.4"),
        ("no_longer_assessed", "iso27001", "ISO.A5.5"),
    ]
    regressed = comparison["changes"][0]
    assert regressed == {
        "framework_id": "dpdpa", "framework_name": "India DPDPA", "requirement_id": "CH2.CONSENT.2",
        "requirement_title": regressed["requirement_title"],
        "prior_outcome": "compliant", "prior_outcome_label": "Compliant",
        "current_outcome": "partially_compliant", "current_outcome_label": "Partially Compliant",
        "direction": "regressed", "direction_label": "Regressed",
    }
    assert comparison["changes"][3]["prior_outcome"] is None
    assert comparison["changes"][4]["current_outcome"] is None
    assert comparison["totals"] == {
        "prior": {key: p1_document["summary"]["totals"][key] for key in prior.TOTAL_KEYS},
        "current": {key: document["summary"]["totals"][key] for key in prior.TOTAL_KEYS},
    }
    assert prior.classify("non_compliant", "partially_compliant") == "improved"
    assert prior.classify("compliant", "not_applicable") == "changed"
    assert prior.classify("insufficient_evidence", "insufficient_evidence") == "unchanged"


def test_scenario_2_prior_is_read_from_stored_bytes_never_rerendered_or_live(db, http, gate, monkeypatch, stub_render):
    """D-P6-9-I: changing the earlier assessment's live data changes nothing; nothing of it is rendered or written."""
    board = stub_render
    engagement = new_engagement(db)
    p1, p1_snapshot = _issued_period(db, http, gate, monkeypatch, engagement, period=PERIOD_1)
    p2 = _current(db, http, gate, monkeypatch, engagement)
    before = build(db, p2)["prior_period"]
    sidecar = report_snapshots.rfi_document_path(p1_snapshot)
    stored = sidecar.read_bytes()

    live = db.query(Conclusion).filter_by(assessment_id=p1.id, requirement_id="CH2.CONSENT.1").one()
    live.outcome = "compliant"
    db.commit()
    real_build = approved_report.build_approved_report

    def _guarded(session, assessment):
        assert assessment.id != p1.id, "the prior assessment's live data must not be read"
        return real_build(session, assessment)

    monkeypatch.setattr(approved_report, "build_approved_report", _guarded)
    monkeypatch.setattr(board, "render_pdf", lambda _d: (_ for _ in ()).throw(AssertionError("no render")))
    snapshots_before = db.query(ReportSnapshot).count()
    after = build(db, p2)["prior_period"]
    assert after == before
    assert sidecar.read_bytes() == stored
    assert db.query(ReportSnapshot).count() == snapshots_before


def test_scenario_3_selection_rules(db, http, gate, monkeypatch, stub_render):
    """D-P6-9-H: issued only; same engagement; other assessments; period ended before this one starts;
    latest such period wins; archived assessments and missing engagements give no prior."""
    prior = _prior()
    engagement = new_engagement(db)
    p0, p0_snapshot = _issued_period(db, http, gate, monkeypatch, engagement, period=PERIOD_0)
    p1, p1_snapshot = _issued_period(db, http, gate, monkeypatch, engagement, period=PERIOD_1)
    # A newer, never-issued draft of P1 is ignored.
    draft_id = generate_board(http, p1)
    # An overlapping period in the same engagement is not a prior period.
    _issued_period(db, http, gate, monkeypatch, engagement, period=OVERLAPPING)
    # Another engagement's issued report is never used.
    other = new_engagement(db, company="Other Client Ltd")
    _issued_period(db, http, gate, monkeypatch, other, period=PERIOD_1, company="Other Client Ltd")
    p2 = _current(db, http, gate, monkeypatch, engagement)

    comparison = build(db, p2)["prior_period"]
    assert comparison["prior"]["snapshot_id"] == p1_snapshot.id != draft_id
    # The same assessment's own issued version is never its own prior period.
    p2_snapshot = generate_board(http, p2)
    issue(http, p2, p2_snapshot)
    assert build(db, p2)["prior_period"]["prior"]["snapshot_id"] == p1_snapshot.id

    db.get(Assessment, p1.id).status = "archived"
    db.commit()
    assert build(db, p2)["prior_period"]["prior"]["snapshot_id"] == p0_snapshot.id

    lonely = _current(db, http, gate, monkeypatch, new_engagement(db, company="Lonely Ltd"))
    lonely_cmp = build(db, lonely)["prior_period"]
    assert lonely_cmp["status"] == "no_prior"
    assert lonely_cmp["notes"] == [prior.NO_PRIOR_TEXT]
    assert (lonely_cmp["prior"], lonely_cmp["frameworks"], lonely_cmp["changes"], lonely_cmp["totals"]) == (None, [], [], None)

    unlinked, _ = released_assessment(db, http, gate, monkeypatch, None, frameworks=FRAMEWORKS, outcomes=P2_OUTCOMES)
    release(db, unlinked)
    assert build(db, unlinked)["prior_period"]["status"] == "no_prior"


def test_scenario_4_matching_across_pack_versions_and_editions(db, http, gate, monkeypatch, stub_render):
    """D-P6-9-J: match on (framework, requirement id) after aliases; criteria bumps compare with a note;
    a different edition is not compared; a framework new in this period is noted."""
    prior = _prior()
    engagement = new_engagement(db)
    p1, _ = released_assessment(
        db, http, gate, monkeypatch, engagement, frameworks=FRAMEWORKS, outcomes=P1_OUTCOMES, period=PERIOD_1,
    )
    release(db, p1)
    base = build(db, p1)
    p2 = _current(db, http, gate, monkeypatch, engagement)
    db.add_all([
        AssessmentPack(assessment_id=p2.id, framework_id="dpdpa", pack_version="2023+criteria-v1"),
        AssessmentPack(assessment_id=p2.id, framework_id="iso27001", pack_version="2022"),
    ])
    db.commit()
    current = build(db, p2)
    assert [f["pack_version"] for f in current["frameworks"]] == ["2023+criteria-v1", "2022"]

    crafted = json.loads(json.dumps(base))
    for framework in crafted["frameworks"]:
        framework["pack_version"] = {"dpdpa": "2023", "iso27001": "2022"}[framework["framework_id"]]
        if framework["framework_id"] == "iso27001":
            framework["version"] = "2013"
    for row in crafted["appendices"]["requirement_register"]:
        if row["requirement_id"] == "CH2.CONSENT.1":
            row["requirement_id"] = "DPDPA.OLD.CONSENT"
    _craft_issued(db, p1, crafted)
    monkeypatch.setattr(prior, "REQUIREMENT_ID_ALIASES", {("dpdpa", "DPDPA.OLD.CONSENT"): "CH2.CONSENT.1"})

    comparison = build(db, p2)["prior_period"]
    names = {f["framework_id"]: f["name"] for f in current["frameworks"]}
    assert comparison["status"] == "compared"
    assert comparison["notes"] == [
        prior.CRITERIA_CHANGED_TEXT.format(name=names["dpdpa"], prior="2023", current="2023+criteria-v1"),
        prior.EDITION_CHANGED_TEXT.format(name=names["iso27001"], prior="2013", current="2022"),
    ]
    frameworks = {f["framework_id"]: f for f in comparison["frameworks"]}
    assert frameworks["dpdpa"]["compared"] is True
    assert (frameworks["dpdpa"]["prior_pack_version"], frameworks["dpdpa"]["current_pack_version"]) == ("2023", "2023+criteria-v1")
    iso = frameworks["iso27001"]
    assert (iso["compared"], iso["prior_version"], iso["current_version"]) == (False, "2013", "2022")
    assert (iso["counts"], iso["score_delta"], iso["prior_score"]) == (None, None, None)
    # The alias matched the renamed id, so CH2.CONSENT.1 is "improved", not new + no longer assessed.
    changes = {(c["framework_id"], c["requirement_id"]): c["direction"] for c in comparison["changes"]}
    assert changes[("dpdpa", "CH2.CONSENT.1")] == "improved"
    assert ("dpdpa", "DPDPA.OLD.CONSENT") not in changes
    assert all(framework_id == "dpdpa" for framework_id, _ in changes)

    # A schema-1 (P6-8 B1) sidecar has no pack_version: compared, with the "not recorded" note.
    legacy = json.loads(json.dumps(base))
    legacy["schema_version"] = 1
    legacy.pop("soa")
    legacy.pop("prior_period")
    for framework in legacy["frameworks"]:
        framework.pop("pack_version")
    legacy["frameworks"] = [f for f in legacy["frameworks"] if f["framework_id"] == "dpdpa"]
    _craft_issued(db, p1, legacy)
    comparison = build(db, p2)["prior_period"]
    assert comparison["prior"]["schema_version"] == 1
    assert comparison["notes"] == [
        prior.CRITERIA_UNKNOWN_TEXT.format(name=names["dpdpa"]),
        prior.NOT_IN_PRIOR_TEXT.format(name=names["iso27001"]),
    ]
    assert [f["compared"] for f in comparison["frameworks"]] == [True, False]


def test_scenario_5_tampered_prior_is_reported_not_silently_skipped(db, http, gate, monkeypatch, stub_render):
    """D-P6-9-I: a sidecar failing its hash gives `unavailable` (alone) or a skip note (when another prior verifies)."""
    prior = _prior()
    engagement = new_engagement(db)
    p1, p1_snapshot = _issued_period(db, http, gate, monkeypatch, engagement, period=PERIOD_1)
    p2 = _current(db, http, gate, monkeypatch, engagement)
    sidecar = report_snapshots.rfi_document_path(p1_snapshot)
    sidecar.write_bytes(sidecar.read_bytes().replace(b'"v1"', b'"v9"'))

    comparison = build(db, p2)["prior_period"]
    assert comparison["status"] == "unavailable"
    assert comparison["notes"] == [prior.UNAVAILABLE_TEXT.format(snapshot=p1_snapshot.id[:8])]
    assert comparison["prior"] is None and comparison["changes"] == []

    _p0, p0_snapshot = _issued_period(db, http, gate, monkeypatch, engagement, period=PERIOD_0)
    comparison = build(db, p2)["prior_period"]
    assert comparison["status"] == "compared"
    assert comparison["prior"]["snapshot_id"] == p0_snapshot.id
    assert comparison["notes"][0] == prior.SKIPPED_TEXT.format(count=1)


def test_scenario_6_comparison_section_renders_between_frameworks_and_sign_off(db, http, gate, monkeypatch, stub_render):
    """D-P6-9-G: always rendered; per-framework only (no combined score); first period shows the empty text."""
    board = stub_render
    prior = _prior()
    engagement = new_engagement(db)
    first, _ = _issued_period(db, http, gate, monkeypatch, engagement, period=PERIOD_1)
    first_html = board.render_html(build(db, first), embed_fonts=False)
    assert "<h2>Prior-period comparison</h2>" in first_html
    assert prior.NO_PRIOR_TEXT in first_html

    p2 = _current(db, http, gate, monkeypatch, engagement)
    document = build(db, p2)
    html = board.render_html(document, embed_fonts=False)
    positions = [
        html.index('data-section="framework"'),
        html.index('data-section="comparison"'),
        html.index('data-section="sign-off"'),
    ]
    assert positions == sorted(positions)
    section = html[positions[1]:positions[2]]
    assert section.count("data-comparison-framework=") == 2
    for framework in document["prior_period"]["frameworks"]:
        assert f"{framework['score_delta']:+.1f} points" in section
    assert "Regressed" in section and "No longer assessed" in section and "Newly assessed" in section
    assert "01 Jan 2026 to 31 Mar 2026" in section
    assert "combined" not in section.lower() and "overall" not in section.lower()
