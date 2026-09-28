"""TDD ("red") contract suite for P6-7a: the consultant requirement card and review queue.

Handoff: ``tasks/handoffs/2026-09-28-p6-7-requirement-card.md``. Plan:
``docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md``, Part D D1,
Part C.3 and D-P6-L. Written by the designer before the implementation; it must
turn green WITHOUT edits. If an assertion looks wrong, report it in the
handoff's Results; do not change it. Scenario numbers match the handoff.

Modules under contract (do not exist yet): ``app.services.requirement_card``,
``app.services.review_queue`` and ``app.routers.requirement_review``, plus the
new ``ConclusionCard.requirement`` field, the divergence gate in
``conclusion_review.decide`` and three templates. Before implementation these
tests fail with ``ModuleNotFoundError``, a 404 for the missing routes, or an
assertion on missing card markup. Scenario 14 (the file-set guard) passes before
and after.

No live LLM. v2 runs are produced by the real v2 pipeline (P6-3 Stages 0-1 and
the P6-4 judge) over invented text, with the P6-3b/P6-4 provider fakes; after
each fixture is built every ``llm_client.call_llm`` call fails the test.
Approvals always record a report basis first (``tests/report_period_helper.py``,
D-P6-G).
"""

from __future__ import annotations

import dataclasses
import importlib
import json
import re
import subprocess
from html import unescape
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.config import settings
from app.database import get_db
from app.main import app
from app.models.analysis_run import AnalysisRun
from app.models.audit_event import AuditEvent
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.evidence import EvidenceVersion
from app.services import conclusion_review, llm_client
from tests.report_period_helper import record_test_period
from tests.test_p6_3b_v2_flag import (
    Q_CONSENT,
    Q_DPO,
    Q_ROLES,
    add_evidence,
    policy_text,
    run_desk_review,
    seed_assessment,
)
from tests.test_p6_4_v2_judge import JudgeProvider, e2e_script, entry

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "grounding_fixtures"

# Exact copy pinned by the handoff (D-P6-7-E..J).
FALLBACK_LABEL = "Judged against the control description; no approved test criteria yet"
APPROVED_CRITERIA_LABEL = "Judged against approved test criteria"
V1_LABEL = (
    "Proposed by the v1 analysis: no criteria checklist or verified claims are "
    "available for this requirement."
)
NO_RUN_LABEL = "No analysis run is linked to this conclusion."
REASON_COMPLIANT = "Every test criterion is met by at least one verified claim."
NO_RESPONSE_LABEL = "No confirmed questionnaire response."
NO_CLAIMS_LABEL = "No verified claim addresses this requirement."
UNSUPPORTED_LABEL = "Unsupported assertion: no verified evidence supports this response or proposal."
SHARED_EVIDENCE_LABEL = "Evidence for this group is shown once, above."
MISSING_EVIDENCE_RFI_NOTE = "Approved insufficient-evidence conclusions are added to the next RFI version."
DIVERGENCE_ACK_REQUIRED = "Acknowledge the framework divergence note before approving this conclusion."
NO_DIVERGENCE = "This conclusion has no framework divergence note to acknowledge."
DIVERGENCE_STALE = (
    "The framework divergence note changed since you loaded it. Reload the card and review it again."
)
ACK_TOAST = "Framework divergence acknowledged"
ACK_ACTION = "conclusion.divergence_acknowledged"
SPAN_INVALID = "Citation span not found in this evidence version."
VERSION_NOT_FOUND = "Evidence version not found"
KEYBOARD_HINT = "Keyboard: j next, k previous"
STATE_RANK = {"pending": 0, "rejected": 1, "approved": 2, "edited": 2}
RISK_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
QUEUE_FLAGS = ("inconsistency", "unsupported_assertion", "divergence")
BULK_PHRASES = re.compile(r"approve all|approve selected|select all|approve framework", re.I)


def rc():
    """app.services.requirement_card, imported lazily so each test fails on its own."""
    return importlib.import_module("app.services.requirement_card")


def rq():
    return importlib.import_module("app.services.review_queue")


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "p6-7.sqlite3"
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    command.upgrade(config, "head")
    return path


@pytest.fixture()
def db(db_path):
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def http(db, db_path, monkeypatch):
    from app.routers.web import templates
    from app.template_config import configure_templates

    configure_templates(templates)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def flag_v2(monkeypatch):
    monkeypatch.setattr(settings, "analysis_pipeline_version", "v2")


def forbid_llm(monkeypatch):
    """After fixtures are built, P6-7 must never reach an LLM (no new LLM calls)."""

    def _refuse(*_args, **_kwargs):
        raise AssertionError("P6-7 must never call an LLM")

    monkeypatch.setattr(llm_client, "call_llm", _refuse)
    monkeypatch.setattr(llm_client, "_client", None)


# --------------------------------------------------------------------------- #
# Builders and HTML helpers
# --------------------------------------------------------------------------- #


def _trigger(db, assessment):
    from app.routers.analysis import trigger_analysis
    from app.schemas.analysis import CompletionOverride

    return trigger_analysis(
        assessment.id, db=db, override=CompletionOverride(reason="document_led", reviewer_name="Tester")
    )


def _add_response(db, assessment, question_id, answer):
    from app.models.questionnaire import QuestionnaireResponse

    db.add(QuestionnaireResponse(
        assessment_id=assessment.id, question_id=question_id, answer=answer, answer_source="human",
    ))
    db.commit()


def build_v2(
    db,
    monkeypatch,
    *,
    frameworks=("dpdpa", "iso27001"),
    text=None,
    script=e2e_script,
    responses=(("SINGLE.CH2.CONSENT.2", "fully_implemented"),),
    applicable=None,
):
    """A real v2 run (desk review Stage 0-1 + P6-4 judge) with provider fakes.

    With the default script: CH4.SDF.1 (DPDPA) is compliant and ISO.A5.2 is
    non-compliant on the same claims' cluster (CLUSTER_002 divergence);
    CH2.CONSENT.1 is compliant; CH2.CONSENT.2 has a positive response and no
    claim (unsupported assertion); requirements with no input are
    insufficient evidence.
    """
    JudgeProvider(script=script).install(monkeypatch)
    assessment = seed_assessment(db, frameworks)
    if applicable is not None:
        assessment.applicable_requirements = json.dumps(applicable)
        db.commit()
    add_evidence(
        db, assessment, filename="policy.pdf",
        text=text if text is not None else policy_text(Q_DPO, Q_ROLES, Q_CONSENT),
    )
    assert run_desk_review(db, assessment).status == "completed"
    for question_id, answer in responses:
        _add_response(db, assessment, question_id, answer)
    result = _trigger(db, assessment)
    assert result["status"] == "completed", result
    db.refresh(assessment)
    return assessment


def conclusion(db, assessment, framework_id, requirement_id) -> Conclusion:
    return db.query(Conclusion).filter_by(
        assessment_id=assessment.id, framework_id=framework_id, requirement_id=requirement_id,
    ).one()


def latest_run(db, assessment, framework_id) -> AnalysisRun:
    runs = db.query(AnalysisRun).filter_by(
        assessment_id=assessment.id, framework_id=framework_id, status="completed",
    ).all()
    return max(runs, key=lambda run: (run.completed_at, run.started_at))


def envelope_item(db, assessment, framework_id, requirement_id) -> tuple[dict, dict]:
    envelope = json.loads(latest_run(db, assessment, framework_id).claims_json)
    item = next(c["item"] for c in envelope["claims"] if c["requirement_id"] == requirement_id)
    return envelope, item


def claim_href(claim: dict) -> str:
    citation = claim["citation"]
    return (
        f"/evidence-versions/{citation['evidence_version_id']}/span"
        f"?ref={citation['location_ref']}#cited-span"
    )


def card_html(page: str, conclusion_id: str) -> str:
    start = page.index(f'id="conclusion-card-{conclusion_id}"')
    end = page.find('<div id="conclusion-card-', start + 1)
    return page[start:] if end == -1 else page[start:end]


def open_tag(html: str, attr: str, value: str | None = None) -> str:
    pattern = rf'<[a-z]+\b[^>]*\b{attr}="{re.escape(value)}"[^>]*>' if value is not None else (
        rf"<[a-z]+\b[^>]*\b{attr}\b[^>]*>"
    )
    match = re.search(pattern, html)
    assert match, f"no element with {attr}={value!r}"
    return match.group(0)


def li_body(html: str, attr: str, value: str) -> str:
    """The unescaped body of one ``<li attr="value">`` (the handoff pins: no nested li)."""
    tag = open_tag(html, attr, value)
    start = html.index(tag)
    end = html.index("</li>", start)
    return unescape(html[start:end])


def div_body(html: str, attr: str) -> str:
    """The unescaped body of one ``<div attr>`` block (the handoff pins: no nested div)."""
    tag = open_tag(html, attr)
    start = html.index(tag)
    end = html.index("</div>", start)
    return unescape(html[start:end])


def attr_values(html: str, attr: str) -> list[str]:
    return re.findall(rf'\b{attr}="([^"]*)"', html)


def chips(html: str) -> dict[str, str]:
    """{chip key: tone} for the requirement section of one card."""
    return {
        key: tone
        for key, tone in re.findall(r'data-quality-chip="([^"]+)" data-tone="([^"]+)"', html)
    }


def conclusions_page(http, assessment) -> str:
    page = http.get(f"/assessments/{assessment.id}/conclusions")
    assert page.status_code == 200
    return page.text


def approve(http, assessment, row: Conclusion, reviewer="Priya"):
    return http.post(
        f"/api/assessments/{assessment.id}/conclusions/{row.id}/approve",
        data={"expected_version": row.version, "reviewer_name": reviewer},
    )


def ack_url(assessment, row: Conclusion) -> str:
    return f"/api/assessments/{assessment.id}/divergence-notes/{row.id}/acknowledge"


def _git(*args) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


# --------------------------------------------------------------------------- #
# Scenario 1: the v2 card, criteria checklist and closed-set claim links
# --------------------------------------------------------------------------- #


def fallback_only(monkeypatch, framework_id="dpdpa"):
    """Pin every control to the fallback path, whatever criteria the pack ships (P6-2b)."""
    from app.frameworks.registry import FrameworkRegistry

    framework = FrameworkRegistry.get(framework_id)
    patched = tuple(dataclasses.replace(control, test_criteria=()) for control in framework.all_controls())
    monkeypatch.setattr(framework, "_all_controls_cache", patched)


def test_scenario_1_v2_card_criteria_checklist_links_only_verified_claims(db, http, monkeypatch, flag_v2):
    fallback_only(monkeypatch)
    assessment = build_v2(db, monkeypatch)
    forbid_llm(monkeypatch)
    page = conclusions_page(http, assessment)

    sdf = conclusion(db, assessment, "dpdpa", "CH4.SDF.1")
    html = card_html(page, sdf.id)
    section = open_tag(html, "data-requirement-card")
    assert 'data-requirement-source="v2"' in section
    assert 'data-criteria-source="fallback"' in section
    assert FALLBACK_LABEL in html
    assert open_tag(html, "data-proposal-reason")
    assert REASON_COMPLIANT in html

    envelope, item = envelope_item(db, assessment, "dpdpa", "CH4.SDF.1")
    verified = {claim["claim_id"]: claim for claim in envelope["verified_claims"]}
    assert item["cited_claim_ids"] and set(item["cited_claim_ids"]) <= set(verified)
    row = li_body(html, "data-criterion", "CH4.SDF.1.IMPLICIT")
    assert 'data-criterion-result="met"' in row and "✓" in row
    for claim_id in item["criteria"][0]["claim_ids"]:
        link = open_tag(row, "data-claim-link", claim_id)
        assert f'href="{claim_href(verified[claim_id])}"' in link
    # Closed set: every claim on the card is one of this requirement's cited, verified claims.
    shown = set(attr_values(html, "data-claim-link")) | set(attr_values(html, "data-claim"))
    assert shown == set(item["cited_claim_ids"])

    roles = conclusion(db, assessment, "iso27001", "ISO.A5.2")
    roles_html = card_html(page, roles.id)
    _, roles_item = envelope_item(db, assessment, "iso27001", "ISO.A5.2")
    row = li_body(roles_html, "data-criterion", "ISO.A5.2.IMPLICIT")
    assert 'data-criterion-result="not_met"' in row and "✗" in row
    assert set(attr_values(row, "data-claim-link")) == set(roles_item["criteria"][0]["claim_ids"]) != set()
    # The ISO claim never leaks onto the DPDPA card, and vice versa.
    assert not set(roles_item["cited_claim_ids"]) & shown

    quiet = conclusion(db, assessment, "iso27001", "ISO.A5.1")
    quiet_html = card_html(page, quiet.id)
    row = li_body(quiet_html, "data-criterion", "ISO.A5.1.IMPLICIT")
    assert 'data-criterion-result="no_evidence"' in row and "?" in row
    assert "data-claim-link" not in row

    # The service view carries the same closed set.
    cards = {card.conclusion.id: card for card in conclusion_review.conclusion_cards(db, assessment.id)}
    view = cards[sdf.id].requirement
    assert view.source == "v2" and view.criteria_source == "fallback"
    assert view.criteria_label == FALLBACK_LABEL
    assert [c.criterion_id for c in view.criteria] == ["CH4.SDF.1.IMPLICIT"]
    assert {c.claim_id for c in view.claims} == set(item["cited_claim_ids"])
    assert view.analysis_run_id == latest_run(db, assessment, "dpdpa").id


def test_scenario_2_claim_ids_outside_the_verified_set_never_render(db, http, monkeypatch, flag_v2):
    assessment = build_v2(db, monkeypatch)
    forbid_llm(monkeypatch)
    bogus = "CLM-0000000000000000"
    run = latest_run(db, assessment, "dpdpa")
    envelope = json.loads(run.claims_json)
    for claim in envelope["claims"]:
        if claim["requirement_id"] == "CH4.SDF.1":
            claim["item"]["criteria"][0]["claim_ids"].append(bogus)
            claim["item"]["cited_claim_ids"].append(bogus)
            claim["item"]["contradictions"].append({"claim_id": bogus, "response_ref": "x", "note": "forged"})
    run.claims_json = json.dumps(envelope, sort_keys=True)
    db.commit()

    sdf = conclusion(db, assessment, "dpdpa", "CH4.SDF.1")
    html = card_html(conclusions_page(http, assessment), sdf.id)
    assert bogus not in html and "forged" not in html
    view = {c.conclusion.id: c for c in conclusion_review.conclusion_cards(db, assessment.id)}[sdf.id].requirement
    assert all(bogus not in row.claim_ids for row in view.criteria)
    assert bogus not in {claim.claim_id for claim in view.claims}
    assert view.contradictions == ()


# --------------------------------------------------------------------------- #
# Scenario 3: what the client said vs what the evidence shows
# --------------------------------------------------------------------------- #


def contradiction_script(rid, criterion_ids, claim_ids, request):
    if rid == "CH2.CONSENT.1" and claim_ids:
        return entry(
            rid, criterion_ids, "partially_compliant", result="not_met", claim_ids=claim_ids[:1],
            contradictions=[{
                "claim_id": claim_ids[0], "response_ref": "CH2.CONSENT.1",
                "note": "The response says consent is not collected; the policy says it is.",
            }],
        )
    return e2e_script(rid, criterion_ids, claim_ids, request)


def test_scenario_3_client_said_vs_evidence_shows(db, http, monkeypatch, flag_v2):
    assessment = build_v2(db, monkeypatch)
    contradicted = build_v2(
        db, monkeypatch, frameworks=("dpdpa",), text=policy_text(Q_CONSENT),
        script=contradiction_script, responses=(("CH2.CONSENT.1", "not_implemented"),),
    )
    forbid_llm(monkeypatch)
    page = conclusions_page(http, assessment)

    unsupported = card_html(page, conclusion(db, assessment, "dpdpa", "CH2.CONSENT.2").id)
    said_body = div_body(unsupported, "data-client-said")
    assert "Fully implemented" in said_body and "Entered in the questionnaire" in said_body
    assert open_tag(unsupported, "data-unsupported-assertion")
    assert UNSUPPORTED_LABEL in unsupported
    assert NO_CLAIMS_LABEL in unsupported
    assert "data-claim=" not in unsupported

    sdf_html = card_html(page, conclusion(db, assessment, "dpdpa", "CH4.SDF.1").id)
    assert NO_RESPONSE_LABEL in div_body(sdf_html, "data-client-said")
    assert "data-unsupported-assertion" not in sdf_html
    _, item = envelope_item(db, assessment, "dpdpa", "CH4.SDF.1")
    body = li_body(sdf_html, "data-claim", item["cited_claim_ids"][0])
    assert Q_DPO in body and "policy.pdf" in body

    page = conclusions_page(http, contradicted)
    html = card_html(page, conclusion(db, contradicted, "dpdpa", "CH2.CONSENT.1").id)
    _, item = envelope_item(db, contradicted, "dpdpa", "CH2.CONSENT.1")
    contradiction = li_body(html, "data-contradiction", item["contradictions"][0]["claim_id"])
    assert "consent is not collected" in contradiction
    assert "Not implemented" in div_body(html, "data-client-said")


# --------------------------------------------------------------------------- #
# Scenario 4: evidence-quality chips (separate dimensions, never one number)
# --------------------------------------------------------------------------- #


def _dated(effective: str) -> str:
    return f"Kestrel Ledger Access Policy\nEffective Date: {effective}\n" + "\n".join((Q_DPO, Q_ROLES)) + "\n"


def omit_iso_a52(rid, criterion_ids, claim_ids, request):
    if rid == "ISO.A5.2":
        return None
    return e2e_script(rid, criterion_ids, claim_ids, request)


def test_scenario_4_quality_chips(db, http, monkeypatch, flag_v2):
    from app.frameworks.registry import FrameworkRegistry

    fixture_text = (FIXTURES / "infosec_policy.txt").read_text() + "\n" + Q_DPO + "\n" + Q_ROLES + "\n"
    everything = [
        control.id
        for framework_id in ("dpdpa", "iso27001")
        for control in FrameworkRegistry.get(framework_id).all_controls()
    ]
    # ISO.A5.3 has a response so the ISO batch still returns something while
    # ISO.A5.2 is omitted twice (analysis_incomplete) and ISO.A5.1 is out of scope.
    dated = build_v2(
        db, monkeypatch, text=fixture_text, script=omit_iso_a52,
        responses=(("SINGLE.CH2.CONSENT.2", "fully_implemented"), ("SINGLE.ISO.A5.3", "partially_implemented")),
        applicable=[rid for rid in everything if rid != "ISO.A5.1"],
    )
    late = build_v2(db, monkeypatch, frameworks=("dpdpa",), text=_dated("01 May 2026"))
    undated = build_v2(db, monkeypatch, frameworks=("dpdpa",))
    forbid_llm(monkeypatch)

    sdf = conclusion(db, dated, "dpdpa", "CH4.SDF.1")
    before = chips(card_html(conclusions_page(http, dated), sdf.id))
    assert before["currency:current"] == "ok"
    assert before["period:not_recorded"] == "neutral"
    assert before["scope:in_scope"] == "ok"
    assert before["kind:design"] == "neutral"

    for assessment in (dated, late, undated):
        record_test_period(db, assessment)  # period 01 Jan-31 Mar 2026, cut-off 15 Apr 2026
    db.commit()
    page = conclusions_page(http, dated)
    after = chips(card_html(page, sdf.id))
    assert after["period:dated"] == "ok"  # fixture header: Effective Date 14 March 2025
    assert "period:not_recorded" not in after
    assert chips(card_html(conclusions_page(http, late), conclusion(db, late, "dpdpa", "CH4.SDF.1").id))[
        "period:after_cutoff"
    ] == "warn"
    assert chips(card_html(conclusions_page(http, undated), conclusion(db, undated, "dpdpa", "CH4.SDF.1").id))[
        "period:undated"
    ] == "warn"

    excluded = chips(card_html(page, conclusion(db, dated, "iso27001", "ISO.A5.1").id))
    assert excluded["scope:excluded"] == "warn"
    assert excluded["currency:none"] == "neutral"
    assert not any(key.startswith(("period:", "kind:")) for key in excluded)  # nothing cited

    incomplete = chips(card_html(page, conclusion(db, dated, "iso27001", "ISO.A5.2").id))
    assert incomplete["analysis:incomplete"] == "warn"

    unscoped = chips(card_html(conclusions_page(http, undated), conclusion(db, undated, "dpdpa", "CH4.SDF.1").id))
    assert unscoped["scope:not_recorded"] == "neutral"

    # A superseded evidence version is visible on its own chip.
    from app.models.evidence import Evidence

    evidence = db.query(Evidence).filter_by(assessment_id=undated.id).one()
    version = db.query(EvidenceVersion).filter_by(evidence_id=evidence.id).one()
    version.status = "superseded"
    db.commit()
    stale = chips(card_html(conclusions_page(http, undated), conclusion(db, undated, "dpdpa", "CH4.SDF.1").id))
    assert stale["currency:superseded"] == "warn" and "currency:current" not in stale

    # Never a single confidence number (PR-022).
    for html in (card_html(page, sdf.id),):
        section = html[html.index("data-requirement-card"):]
        assert "confidence" not in section.lower()
        assert not re.search(r"\b\d{1,3}\s?%", section)


# --------------------------------------------------------------------------- #
# Scenario 5: missing evidence (the one-click RFI write is P6-7b)
# --------------------------------------------------------------------------- #


def test_scenario_5_missing_evidence_lists_judge_output_and_links_the_rfi(db, http, monkeypatch, flag_v2):
    assessment = build_v2(db, monkeypatch)
    forbid_llm(monkeypatch)
    page = conclusions_page(http, assessment)
    candidates = []
    for framework_id in ("dpdpa", "iso27001"):
        envelope = json.loads(latest_run(db, assessment, framework_id).claims_json)
        candidates += [
            (framework_id, claim["requirement_id"], claim["item"]["missing_evidence"])
            for claim in envelope["claims"] if claim["item"]["missing_evidence"]
        ]
    assert candidates, "fixture must produce at least one requirement with missing evidence"
    framework_id, requirement_id, missing = candidates[0]
    html = card_html(page, conclusion(db, assessment, framework_id, requirement_id).id)
    for request in missing:
        body = li_body(html, "data-missing-evidence", request["document_type"])
        assert request["what_it_would_show"] in body
    assert MISSING_EVIDENCE_RFI_NOTE in html
    assert f'href="/assessments/{assessment.id}/rfi"' in html
    # P6-7b adds the one-click add-to-RFI control on this section; its contract
    # (routes, states, idempotency) is tests/test_p6_7b_add_to_rfi.py. The only RFI
    # write the card may post to is that route.
    assert all(
        "/rfi-requests/" in url for url in re.findall(r'hx-post="([^"]*rfi[^"]*)"', html, re.I)
    )

    sdf_html = card_html(page, conclusion(db, assessment, "dpdpa", "CH4.SDF.1").id)
    assert "data-missing-evidence" not in sdf_html


# --------------------------------------------------------------------------- #
# Scenario 6: framework divergence note and the acknowledgement gate
# --------------------------------------------------------------------------- #


def test_scenario_6_divergence_must_be_acknowledged_before_approval(db, http, monkeypatch, flag_v2):
    assessment = build_v2(db, monkeypatch)
    forbid_llm(monkeypatch)
    record_test_period(db, assessment)
    db.commit()
    sdf = conclusion(db, assessment, "dpdpa", "CH4.SDF.1")
    roles = conclusion(db, assessment, "iso27001", "ISO.A5.2")
    run = latest_run(db, assessment, "dpdpa")
    envelope_before = run.claims_json

    html = card_html(conclusions_page(http, assessment), sdf.id)
    note = open_tag(html, "data-divergence-note", "CLUSTER_002")
    assert 'data-acknowledged="no"' in note
    for text in ("DPDPA", "CH4.SDF.1", "ISO 27001", "ISO.A5.2", "Compliant", "Non-Compliant"):
        assert text in html[html.index(note):]
    form = open_tag(html, "data-divergence-ack-form")
    assert f'hx-post="{ack_url(assessment, sdf)}"' in form
    assert f'hx-target="#conclusion-card-{sdf.id}"' in form
    assert f'name="analysis_run_id" value="{run.id}"' in html
    assert 'name="cluster_id" value="CLUSTER_002"' in html
    assert DIVERGENCE_ACK_REQUIRED in html  # the card's approval blocker

    # Approve and edit are refused until acknowledged; nothing is written.
    refused = approve(http, assessment, sdf)
    assert refused.status_code == 400 and refused.json() == {"detail": DIVERGENCE_ACK_REQUIRED}
    edited = http.post(
        f"/api/assessments/{assessment.id}/conclusions/{sdf.id}/edit",
        data={
            "expected_version": sdf.version, "reviewer_name": "Priya", "outcome": "compliant",
            "rationale": "Reviewed.", "gaps_identified": "", "risk_level": "low", "recommended_action": "",
        },
    )
    assert edited.status_code == 400 and edited.json() == {"detail": DIVERGENCE_ACK_REQUIRED}
    with pytest.raises(conclusion_review.InvalidDecision) as caught:
        conclusion_review.decide(
            db, assessment_id=assessment.id, conclusion_id=sdf.id, action="approved",
            expected_version=sdf.version, actor="consultant:Priya",
        )
    assert caught.value.message == DIVERGENCE_ACK_REQUIRED
    db.rollback()
    assert db.query(ConclusionRevision).filter_by(conclusion_id=sdf.id).count() == 1
    # Reject is a decision too, but it does not need the acknowledgement.
    card = {c.conclusion.id: c for c in conclusion_review.conclusion_cards(db, assessment.id)}[sdf.id]
    assert card.approval_blocker == DIVERGENCE_ACK_REQUIRED
    assert card.requirement.divergence.acknowledged is False

    # An acknowledgement belongs to one Conclusion: an event recorded against another
    # Conclusion never acknowledges this one, even with the same run and cluster.
    db.add(AuditEvent(
        actor="consultant:Someone", action=ACK_ACTION, entity_type="conclusion", entity_id=roles.id,
        metadata_json=json.dumps({
            "analysis_run_id": run.id, "cluster_id": "CLUSTER_002",
            "compliant": [], "non_compliant": [], "note": None,
        }, sort_keys=True),
    ))
    db.commit()
    html = card_html(conclusions_page(http, assessment), sdf.id)
    assert 'data-acknowledged="no"' in open_tag(html, "data-divergence-note", "CLUSTER_002")

    # A stale form (other run or cluster) is refused and writes nothing.
    stale = http.post(ack_url(assessment, sdf), data={
        "analysis_run_id": "not-the-run", "cluster_id": "CLUSTER_002", "note": "", "reviewer_name": "Priya",
    })
    assert stale.status_code == 409 and stale.json() == {"detail": DIVERGENCE_STALE}
    assert stale.headers["X-Toast-Type"] == "error"
    assert db.query(AuditEvent).filter_by(action=ACK_ACTION, entity_id=sdf.id).count() == 0

    # Unknown conclusion and a conclusion without a divergence note.
    missing = http.post(
        f"/api/assessments/{assessment.id}/divergence-notes/nope/acknowledge",
        data={"analysis_run_id": run.id, "cluster_id": "CLUSTER_002"},
    )
    assert missing.status_code == 404
    consent = conclusion(db, assessment, "dpdpa", "CH2.CONSENT.1")
    none = http.post(ack_url(assessment, consent), data={
        "analysis_run_id": run.id, "cluster_id": "CLUSTER_002", "reviewer_name": "Priya",
    })
    assert none.status_code == 400 and none.json() == {"detail": NO_DIVERGENCE}

    # Acknowledge: one append-only audit event, the card re-renders acknowledged.
    acked = http.post(ack_url(assessment, sdf), data={
        "analysis_run_id": run.id, "cluster_id": "CLUSTER_002",
        "note": "  ISO   A.5.2 needs a documented allocation;   DPDPA does not.  ", "reviewer_name": "Priya",
    })
    assert acked.status_code == 200
    assert acked.headers["X-Toast-Message"] == ACK_TOAST and acked.headers["X-Toast-Type"] == "success"
    assert f'id="conclusion-card-{sdf.id}"' in acked.text
    assert 'data-acknowledged="yes"' in acked.text
    assert "Acknowledged by Priya" in acked.text
    assert "ISO A.5.2 needs a documented allocation; DPDPA does not." in unescape(acked.text)
    assert "data-divergence-ack-form" not in acked.text
    events = db.query(AuditEvent).filter_by(action=ACK_ACTION, entity_id=sdf.id).all()
    assert len(events) == 1
    event = events[0]
    assert (event.entity_type, event.entity_id, event.actor) == ("conclusion", sdf.id, "consultant:Priya")
    metadata = json.loads(event.metadata_json)
    assert metadata == {
        "analysis_run_id": run.id,
        "cluster_id": "CLUSTER_002",
        "compliant": [["dpdpa", "CH4.SDF.1"]],
        "non_compliant": [["iso27001", "ISO.A5.2"]],
        "note": "ISO A.5.2 needs a documented allocation; DPDPA does not.",
    }
    assert event.metadata_json == json.dumps(metadata, sort_keys=True)

    # Idempotent: a second acknowledgement of the same note writes nothing.
    again = http.post(ack_url(assessment, sdf), data={
        "analysis_run_id": run.id, "cluster_id": "CLUSTER_002", "reviewer_name": "Someone else",
    })
    assert again.status_code == 200
    assert db.query(AuditEvent).filter_by(action=ACK_ACTION, entity_id=sdf.id).count() == 1

    # The run envelope is never mutated: it keeps "acknowledged": False as produced.
    db.refresh(run)
    assert run.claims_json == envelope_before
    assert json.loads(run.claims_json)["divergences"][0]["acknowledged"] is False

    # Per conclusion: the ISO side still needs its own acknowledgement.
    roles_html = card_html(conclusions_page(http, assessment), roles.id)
    assert 'data-acknowledged="no"' in open_tag(roles_html, "data-divergence-note", "CLUSTER_002")

    db.refresh(sdf)
    approved = approve(http, assessment, sdf)
    assert approved.status_code == 200, approved.text
    assert db.query(ConclusionRevision).filter_by(conclusion_id=sdf.id, action="approved").count() == 1


def test_scenario_7_acknowledgement_belongs_to_one_run(db, http, monkeypatch, flag_v2):
    assessment = build_v2(db, monkeypatch)  # the provider fake stays installed for the re-run
    record_test_period(db, assessment)
    db.commit()
    sdf = conclusion(db, assessment, "dpdpa", "CH4.SDF.1")
    first_run = latest_run(db, assessment, "dpdpa")
    assert http.post(ack_url(assessment, sdf), data={
        "analysis_run_id": first_run.id, "cluster_id": "CLUSTER_002", "reviewer_name": "Priya",
    }).status_code == 200
    db.refresh(sdf)
    assert approve(http, assessment, sdf).status_code == 200
    db.refresh(sdf)
    reopened = http.post(
        f"/api/assessments/{assessment.id}/conclusions/{sdf.id}/reopen",
        data={"expected_version": sdf.version, "reviewer_name": "Priya"},
    )
    assert reopened.status_code == 200

    # Re-analysis produces a new run and the same divergence: a new acknowledgement is required.
    result = _trigger(db, assessment)
    assert result["status"] == "completed"
    forbid_llm(monkeypatch)
    second_run = latest_run(db, assessment, "dpdpa")
    assert second_run.id != first_run.id
    html = card_html(conclusions_page(http, assessment), sdf.id)
    assert 'data-acknowledged="no"' in open_tag(html, "data-divergence-note", "CLUSTER_002")
    assert f'name="analysis_run_id" value="{second_run.id}"' in html
    db.refresh(sdf)
    assert approve(http, assessment, sdf).json() == {"detail": DIVERGENCE_ACK_REQUIRED}
    # The first acknowledgement is history, never rewritten.
    events = db.query(AuditEvent).filter_by(action=ACK_ACTION, entity_id=sdf.id).all()
    assert [json.loads(e.metadata_json)["analysis_run_id"] for e in events] == [first_run.id]


# --------------------------------------------------------------------------- #
# Scenario 8: v1 fallback and conclusions with no linked run
# --------------------------------------------------------------------------- #


def _v1_items():
    return [
        {
            "requirement_id": "CH2.CONSENT.1", "compliance_status": "compliant",
            "current_state": "Consent is collected before processing.", "evidence_quote": Q_CONSENT,
            "gap_description": "", "risk_level": "low", "remediation_action": "",
        },
        {
            "requirement_id": "CH4.SDF.1", "compliance_status": "non_compliant",
            "current_state": "No DPO is appointed.",
            "evidence_quote": "A sentence the model invented that is not in any document.",
            "gap_description": "No DPO.", "risk_level": "low", "remediation_action": "Appoint a DPO.",
        },
    ]


def test_scenario_8_v1_fallback_and_legacy_cards(db, http, monkeypatch):
    from app.frameworks.registry import FrameworkRegistry
    from app.services import analysis_pipeline

    forbid_llm(monkeypatch)
    assessment = seed_assessment(db, ("dpdpa",))
    add_evidence(db, assessment, filename="policy.pdf", text=policy_text(Q_CONSENT))
    context = analysis_pipeline.start_runs(db, assessment_id=assessment.id, framework_ids=["dpdpa"])
    analysis_pipeline.record_framework_run(
        db, context, framework_id="dpdpa", assessments=_v1_items(),
        desk_review_data=None, gap_report_id="legacy-report",
    )
    legacy = Conclusion(
        assessment_id=assessment.id, requirement_id="CH2.CONSENT.2", framework_id="dpdpa",
        outcome="insufficient_evidence", rationale="Migrated.", evidence_summary="",
        gaps_identified="Unknown.", risk_level="medium", recommended_action="Collect evidence.",
        ai_proposed=True, version=1,
    )
    db.add(legacy)
    db.flush()
    db.add(ConclusionRevision(conclusion_id=legacy.id, actor="system:migration", action="proposed"))
    db.commit()

    page = conclusions_page(http, assessment)
    consent = conclusion(db, assessment, "dpdpa", "CH2.CONSENT.1")
    html = card_html(page, consent.id)
    assert 'data-requirement-source="v1"' in open_tag(html, "data-requirement-card")
    assert V1_LABEL in html
    assert FALLBACK_LABEL not in html
    assert "data-criterion=" not in html and "data-divergence-note" not in html
    consent_chips = chips(html)
    assert consent_chips["grounding:grounded"] == "ok"
    assert consent_chips["currency:current"] == "ok"
    assert consent_chips["scope:not_recorded"] == "neutral"

    sdf = conclusion(db, assessment, "dpdpa", "CH4.SDF.1")
    sdf_html = card_html(page, sdf.id)
    sdf_chips = chips(sdf_html)
    assert sdf_chips["grounding:ungrounded"] == "warn"
    assert sdf_chips["currency:none"] == "neutral"
    requests = [
        request for request in FrameworkRegistry.get("dpdpa").evidence_requests
        if "CH4.SDF.1" in request.maps_to
    ][:3]
    for request in requests:
        assert open_tag(sdf_html, "data-missing-evidence", request.document_type)

    legacy_html = card_html(page, legacy.id)
    assert 'data-requirement-source="none"' in open_tag(legacy_html, "data-requirement-card")
    assert NO_RUN_LABEL in legacy_html

    cards = {card.conclusion.id: card for card in conclusion_review.conclusion_cards(db, assessment.id)}
    assert cards[consent.id].requirement.source == "v1"
    assert cards[consent.id].requirement.criteria == ()
    assert cards[consent.id].requirement.divergence is None
    assert cards[legacy.id].requirement.source == "none"

    # v1 approvals need no acknowledgement (only the P6-6 period gate).
    record_test_period(db, assessment)
    db.commit()
    db.refresh(consent)
    assert approve(http, assessment, consent).status_code == 200


# --------------------------------------------------------------------------- #
# Scenario 9: the review queue
# --------------------------------------------------------------------------- #


QUEUE_ITEM = re.compile(r"<div data-queue-item\b[^>]*>")


def queue_items(html: str) -> list[dict]:
    items = []
    for tag in QUEUE_ITEM.findall(html):
        values = dict(re.findall(r'\b(data-[a-z-]+|tabindex)="([^"]*)"', tag))
        items.append({
            "conclusion_id": values["data-conclusion-id"],
            "index": int(values["data-queue-index"]),
            "state": values["data-state"],
            "risk": values["data-risk"],
            "flags": tuple(flag for flag in values["data-flags"].split(",") if flag),
            "tabindex": values.get("tabindex"),
            "position": html.index(tag),
        })
    return items


def queue_groups(html: str) -> list[tuple[str, str, str]]:
    """(group key, data-shared, group html) in page order."""
    starts = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(
        r'<section data-queue-group="([^"]+)" data-shared="(yes|no)"', html)]
    groups = []
    for index, (start, key, shared) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(html)
        groups.append((key, shared, html[start:end]))
    return groups


def item_key(item: dict) -> tuple:
    return (
        STATE_RANK[item["state"]],
        RISK_RANK[item["risk"]],
        tuple(flag not in item["flags"] for flag in QUEUE_FLAGS),
    )


def test_scenario_9_review_queue_sorts_flags_groups_and_navigates(db, http, monkeypatch, flag_v2):
    assessment = build_v2(db, monkeypatch)
    forbid_llm(monkeypatch)
    record_test_period(db, assessment)
    db.commit()
    consent = conclusion(db, assessment, "dpdpa", "CH2.CONSENT.1")
    assert approve(http, assessment, consent).status_code == 200

    assert http.get("/assessments/not-an-assessment/review-queue").status_code == 404
    response = http.get(f"/assessments/{assessment.id}/review-queue")
    assert response.status_code == 200
    html = response.text
    items = queue_items(html)
    by_id = {item["conclusion_id"]: item for item in items}
    all_ids = {row.id for row in db.query(Conclusion).filter_by(assessment_id=assessment.id)}
    assert len(items) == len(all_ids) and set(by_id) == all_ids
    assert [item["index"] for item in items] == list(range(len(items)))
    assert all(item["tabindex"] == "-1" for item in items)

    sdf = conclusion(db, assessment, "dpdpa", "CH4.SDF.1")
    roles = conclusion(db, assessment, "iso27001", "ISO.A5.2")
    quiet = conclusion(db, assessment, "iso27001", "ISO.A5.1")
    unsupported = conclusion(db, assessment, "dpdpa", "CH2.CONSENT.2")
    # Deterministic risk: the LLM said "low" for ISO.A5.2; the pack criticality decides.
    assert by_id[roles.id]["risk"] == "high"
    assert "divergence" in by_id[roles.id]["flags"] and "divergence" in by_id[sdf.id]["flags"]
    assert "unsupported_assertion" in by_id[unsupported.id]["flags"]
    assert by_id[consent.id]["state"] == "approved"

    groups = queue_groups(html)
    shared = [g for g in groups if g[0] == "CLUSTER_002"]
    assert len(shared) == 1 and shared[0][1] == "yes"
    group_html = shared[0][2]
    members = [item["conclusion_id"] for item in queue_items(group_html)]
    assert {roles.id, sdf.id} <= set(members)
    assert members.index(roles.id) < members.index(sdf.id)  # open high risk before low risk
    assert by_id[roles.id]["position"] < by_id[quiet.id]["position"]  # divergence flag breaks the tie
    # Shared evidence is shown once for the group; the member cards point to it.
    shared_claims = set(attr_values(group_html, "data-shared-claim"))
    for framework_id, row in (("dpdpa", sdf), ("iso27001", roles)):
        _, item = envelope_item(db, assessment, framework_id, row.requirement_id)
        assert set(item["cited_claim_ids"]) <= shared_claims
    assert SHARED_EVIDENCE_LABEL in group_html
    assert "data-evidence-shared" in group_html and "data-claim=" not in group_html
    # ...while every Conclusion keeps its own decision controls (D3).
    for row in (sdf, roles):
        assert f'hx-post="/api/assessments/{assessment.id}/conclusions/{row.id}/approve"' in group_html

    # Invariants of the pinned order: members sorted within a group, groups by their first member.
    for key, _shared, group in groups:
        member_items = [by_id[item["conclusion_id"]] for item in queue_items(group)]
        keys = [item_key(item) for item in member_items]
        assert keys == sorted(keys), key
    firsts = [item_key(by_id[queue_items(group)[0]["conclusion_id"]]) for _key, _shared, group in groups]
    assert firsts == sorted(firsts)

    # Keyboard navigation and no bulk approval.
    assert KEYBOARD_HINT in html and "data-queue-keys" in html
    script = html[html.index("<script data-queue-nav"):]
    script = script[: script.index("</script>")]
    for token in ('"j"', '"k"', "scrollIntoView", "INPUT", "TEXTAREA", "SELECT", "data-queue-item"):
        assert token in script
    assert not BULK_PHRASES.search(html)
    assert f'href="/assessments/{assessment.id}/review-queue"' in conclusions_page(http, assessment)


# --------------------------------------------------------------------------- #
# Scenario 10: queue risk is deterministic and never an LLM number
# --------------------------------------------------------------------------- #


def test_scenario_10_queue_risk_matches_the_judge_table_without_importing_grounding(db, monkeypatch):
    from app.frameworks.registry import FrameworkRegistry
    from app.services.grounding import judge

    module = rq()
    outcomes = ("compliant", "partially_compliant", "non_compliant", "insufficient_evidence", "not_applicable")
    for criticality in ("critical", "high", "medium", "low", "unknown"):
        for outcome in outcomes:
            assert module.deterministic_queue_risk(criticality, outcome) == judge.deterministic_risk(
                criticality, outcome
            ), (criticality, outcome)
    control = FrameworkRegistry.get("iso27001").get_control("ISO.A5.2")
    assert module.queue_risk("iso27001", "ISO.A5.2", "non_compliant") == judge.deterministic_risk(
        control.criticality, "non_compliant"
    )
    assert module.queue_risk("iso27001", "NOT.A.CONTROL", "non_compliant") == "medium"
    assert module.QUEUE_FLAGS == QUEUE_FLAGS

    # The v1 LLM risk ("low") never drives the queue.
    forbid_llm(monkeypatch)
    from app.services import analysis_pipeline

    assessment = seed_assessment(db, ("dpdpa",))
    context = analysis_pipeline.start_runs(db, assessment_id=assessment.id, framework_ids=["dpdpa"])
    analysis_pipeline.record_framework_run(
        db, context, framework_id="dpdpa", assessments=_v1_items(),
        desk_review_data=None, gap_report_id="legacy-report",
    )
    db.commit()
    expected = judge.deterministic_risk(
        FrameworkRegistry.get("dpdpa").get_control("CH4.SDF.1").criticality, "non_compliant"
    )
    assert expected != "low"
    entries = {
        entry.card.conclusion.requirement_id: entry
        for group in module.review_queue(db, assessment.id)
        for entry in group.entries
    }
    assert entries["CH4.SDF.1"].risk == expected

    sources = "\n".join(
        (REPO_ROOT / path).read_text()
        for path in (
            "app/services/requirement_card.py",
            "app/services/review_queue.py",
            "app/routers/requirement_review.py",
        )
    )
    for token in ("services.grounding", "llm_client", "call_llm", "analysis_v2"):
        assert token not in sources, token
    assert not re.search(r"from app\.services import[^\n]*\bgrounding\b", sources)


# --------------------------------------------------------------------------- #
# Scenario 11: the evidence span viewer
# --------------------------------------------------------------------------- #


def test_scenario_11_span_viewer_highlights_the_cited_span(db, http, monkeypatch, flag_v2):
    assessment = build_v2(db, monkeypatch)
    forbid_llm(monkeypatch)
    envelope, item = envelope_item(db, assessment, "dpdpa", "CH4.SDF.1")
    claim = next(c for c in envelope["verified_claims"] if c["claim_id"] == item["cited_claim_ids"][0])
    citation = claim["citation"]
    href = claim_href(claim).split("#", 1)[0]

    page = http.get(href)
    assert page.status_code == 200
    mark = re.search(r'<mark id="cited-span" data-cited-span>(.*?)</mark>', page.text, re.S)
    assert mark and mark.group(1) == Q_DPO
    assert "policy.pdf" in page.text and "Version 1" in page.text
    assert "Current version" in page.text
    assert citation["location_ref"] in page.text
    for token in ("<form", "hx-post", "hx-put", "hx-delete"):
        assert token not in page.text.lower()

    vid = citation["evidence_version_id"]
    for ref in ("chars:5-1", "chars:0-999999", "page:3", ""):
        bad = http.get(f"/evidence-versions/{vid}/span", params={"ref": ref})
        assert bad.status_code == 400 and SPAN_INVALID in bad.text, ref
    assert http.get("/evidence-versions/nope/span", params={"ref": "chars:0-5"}).status_code == 404
    whole = http.get(f"/evidence-versions/{vid}/span", params={"ref": "whole"})
    assert whole.status_code == 200 and "Whole document cited" in whole.text
    assert "cited-span" not in whole.text

    version = db.get(EvidenceVersion, vid)
    version.status = "superseded"
    db.commit()
    assert "Superseded version" in http.get(href).text


# --------------------------------------------------------------------------- #
# Scenario 12: approved criteria replace the fallback label, requirement by requirement
# --------------------------------------------------------------------------- #


def test_scenario_12_approved_criteria_label(db, http, monkeypatch, flag_v2):
    from app.frameworks.registry import FrameworkRegistry
    from app.frameworks.schema import TestCriterion

    framework = FrameworkRegistry.get("dpdpa")
    patched = tuple(
        dataclasses.replace(
            control,
            test_criteria=(
                TestCriterion("CH4.SDF.1.TC1", "A DPO is named.", "design", "dpo_appointment", "practice"),
                TestCriterion("CH4.SDF.1.TC2", "The DPO reports to the board.", "design", "dpo_appointment", "practice"),
            ),
        )
        if control.id == "CH4.SDF.1"
        else dataclasses.replace(control, test_criteria=())
        for control in framework.all_controls()
    )
    monkeypatch.setattr(framework, "_all_controls_cache", patched)
    assessment = build_v2(db, monkeypatch, frameworks=("dpdpa",))
    forbid_llm(monkeypatch)
    page = conclusions_page(http, assessment)
    html = card_html(page, conclusion(db, assessment, "dpdpa", "CH4.SDF.1").id)
    assert 'data-criteria-source="approved"' in open_tag(html, "data-requirement-card")
    assert APPROVED_CRITERIA_LABEL in html and FALLBACK_LABEL not in html
    assert attr_values(html, "data-criterion") == ["CH4.SDF.1.TC1", "CH4.SDF.1.TC2"]
    assert "A DPO is named." in html and "The DPO reports to the board." in html
    other = card_html(page, conclusion(db, assessment, "dpdpa", "CH2.CONSENT.1").id)
    assert FALLBACK_LABEL in other


# --------------------------------------------------------------------------- #
# Scenario 13: one card pass per page, no LLM, card field shape
# --------------------------------------------------------------------------- #


def test_scenario_13_single_card_pass_and_field_shape(db, http, monkeypatch, flag_v2):
    """The queue builds every card in one conclusion_cards call; the card field is additive."""
    assessment = build_v2(db, monkeypatch)
    forbid_llm(monkeypatch)
    real = conclusion_review.conclusion_cards
    calls = []

    def _spy(db_arg, assessment_id):
        calls.append(assessment_id)
        return real(db_arg, assessment_id)

    monkeypatch.setattr(conclusion_review, "conclusion_cards", _spy)
    assert http.get(f"/assessments/{assessment.id}/review-queue").status_code == 200
    assert calls == [assessment.id]

    fields = {field.name: field for field in dataclasses.fields(conclusion_review.ConclusionCard)}
    assert "requirement" in fields and fields["requirement"].default is None
    assert list(fields)[-1] == "requirement"
    module = rc()
    assert module.FALLBACK_CRITERIA_LABEL == FALLBACK_LABEL
    assert module.DIVERGENCE_ACK_REQUIRED_MESSAGE == DIVERGENCE_ACK_REQUIRED
    assert module.DIVERGENCE_ACK_ACTION == ACK_ACTION
    for name in ("RequirementCard", "CriterionRow", "ClaimView", "QualityChip", "DivergenceNote"):
        assert dataclasses.is_dataclass(getattr(module, name)), name
        assert getattr(module, name).__dataclass_params__.frozen, name


# --------------------------------------------------------------------------- #
# Scenario 14: file-set guard (green before and after implementation)
# --------------------------------------------------------------------------- #

P6_7_APP_FILES = {
    "app/main.py",
    "app/services/requirement_card.py",
    "app/services/review_queue.py",
    "app/services/conclusion_review.py",
    "app/routers/requirement_review.py",
    "app/templates/components/conclusion_card.html",
    "app/templates/components/requirement_card_body.html",
    "app/templates/pages/conclusions.html",
    "app/templates/pages/review_queue.html",
    "app/templates/pages/evidence_span.html",
}
P6_7_FORBIDDEN = (
    "app/services/analysis_v2.py", "app/services/grounding", "app/services/analysis_pipeline.py",
    "app/services/scoring.py", "app/services/report_basis.py", "app/services/report_snapshots.py",
    "app/services/rfi_requests.py", "app/services/citations.py", "app/models", "alembic",
    "app/routers/reports.py", "app/routers/review.py", "app/routers/web.py", "app/routers/conclusions.py",
    "app/utils", "app/templates/base.html", "app/templates/pages/workpaper.html",
    "app/templates/components/workpaper_entry.html", "requirements.txt", ".github", "Dockerfile",
    "scripts", "validation", "app/frameworks", "app/dpdpa", "app/config.py",
)

# P6-2b (PR #79) lands after P6-7a and legitimately touches these (approved DPDPA
# criteria, pack version); tests/test_p6_2b_*.py guard them.
P6_2B_APP_FILES = (
    "app/frameworks/criteria/dpdpa.py", "app/frameworks/definitions/dpdpa.py",
    "app/frameworks/schema.py", "app/services/engagement_factory.py",
    "app/services/grounding/claims.py", "app/services/grounding/pipeline.py",
)
# P6-8 B1 (PR #80) lands after P6-7a and legitimately touches these (board report
# v2, standalone Workpaper, Noto fonts); tests/test_p6_8_board_report_v2.py guards them.
P6_8_B1_FILES = (
    "app/utils/html_pdf.py", "app/services/board_report.py",
    "app/services/standalone_workpaper.py", "app/services/report_snapshots.py",
    "app/routers/snapshots.py", "app/templates/reports", "app/templates/pages/report_snapshots.html",
    "app/assets/fonts/noto", ".github/workflows/tests.yml", "Dockerfile", "requirements.txt",
    # P6-8 B2 (DOCX/XLSX exporter); tests/test_p6_8_b2_docx_xlsx.py guards it.
    "app/services/board_exports.py",
)
# P6-7b (tasks/handoffs/2026-09-28-p6-7b-add-to-rfi.md) lands after P6-7a and
# legitimately touches these; tests/test_p6_7b_add_to_rfi.py guards them.
P6_7B_APP_FILES = (
    "app/services/rfi_evidence_requests.py", "app/services/rfi_requests.py",
    "app/templates/pages/rfi.html",
)
# P6-9 (tasks/handoffs/2026-09-28-p6-9-soa-roadmap-comparison.md) lands after P6-7a and
# adds the SoA, roadmap-group and comparison files; tests/test_p6_9_file_set.py guards them.
P6_9_APP_FILES = (
    "app/services/soa.py", "app/services/remediation_groups.py", "app/services/prior_period.py",
    "app/routers/soa.py", "app/templates/pages/soa.html",
)
# P6-5 (tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md) lands after P6-7a: judge claim
# quarantine, injected-document live check and the A/B comparison; tests/test_p6_5_*.py guard them.
P6_5_FILES = (
    "app/services/grounding/injection.py", "app/services/grounding/judge.py",
    "app/services/analysis_v2.py", "scripts/injection_pack_live.py",
    "scripts/validation/ab_compare.py", "scripts/validation/score.py",
)


def _changed(*args: str) -> set[str]:
    return set(_git("diff", "--name-only", *args, "--", "app").split())


def test_scenario_14_p6_7_touches_only_its_files():
    changed = _changed("main...HEAD") | _changed("HEAD") | set(
        _git("ls-files", "--others", "--exclude-standard", "app").split()
    )
    changed -= set(P6_2B_APP_FILES) | set(P6_7B_APP_FILES)
    changed -= set(P6_2B_APP_FILES)
    changed -= set(P6_9_APP_FILES)
    changed = {path for path in changed if not path.startswith(P6_8_B1_FILES + P6_5_FILES)}
    assert changed <= P6_7_APP_FILES, sorted(changed - P6_7_APP_FILES)
    # Stage C 2026-09-28 harness fix: magic-link evidence lookup in the runner.
    p6_2b = [f":(exclude){path}" for path in (*P6_2B_APP_FILES, "scripts/convert_criteria.py", *P6_8_B1_FILES, "scripts/validation/run_company.py", *P6_7B_APP_FILES, *P6_5_FILES)]
    forbidden = _git("diff", "--name-only", "main...HEAD", "--", *P6_7_FORBIDDEN, *p6_2b).split()
    forbidden += _git("diff", "--name-only", "HEAD", "--", *P6_7_FORBIDDEN, *p6_2b).split()
    assert forbidden == []
