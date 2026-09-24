"""TDD ("red") contract suite for P2-3, the immutable analysis pipeline.

Written before the implementation. It pins the interface that
``tasks/handoffs/2026-09-23-p2-3-immutable-analysis-pipeline.md`` specifies,
and must turn green WITHOUT edits to its assertions. Scenario numbers in the
docstrings match the handoff's "Test scenarios" section.

Module under contract (does not exist yet): ``app.services.analysis_pipeline``
-- ``CLAIMS_SCHEMA_VERSION``, ``PIPELINE_ACTOR``, ``OUTCOME_BY_STATUS``,
``HUMAN_DECISION_ACTIONS``, ``LOCKING_ACTIONS``, ``AnalysisPipelineError``,
``ConclusionConflict``, ``RunContext``, ``ConclusionState``, ``start_runs``,
``fail_runs``, ``load_conclusion_state`` and ``record_framework_run``; plus
the rewired ``app.routers.analysis`` (dual-write, D-P2-3-A), Alembic revision
``4e8c1a9d2b57`` and the ``scripts/migrate_legacy.py`` skip rule.

Every pipeline-dependent test resolves the module through ``pl()`` as its
first statement, so before implementation each fails with
``ModuleNotFoundError: No module named 'app.services.analysis_pipeline'`` --
a failure for the right reason, not a typo in this file. The schema tests
fail on the missing revision ``4e8c1a9d2b57``. The two standing guards
(scenario 12) pass today and must keep passing.

The analyzer is replaced at the router's import seam
(``app.routers.analysis.run_gap_analysis`` /
``run_multi_framework_analysis``), exactly as the existing analysis tests do,
so no LLM is ever called.

Test-DB strategy: identical to ``tests/test_citations.py`` -- a file-backed
SQLite database built by ``alembic upgrade head`` with
``PRAGMA foreign_keys=ON`` on every connection, ``settings.upload_dir``
redirected to ``tmp_path``, and ``app.services.evidence.extract_text``
replaced by a deterministic fake keyed on the uploaded bytes.
"""

from __future__ import annotations

import copy
import importlib
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import HTTPException
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.config import settings
from app.dpdpa.framework import get_all_requirements
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment, AssessmentDocument
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.models.engagement import Engagement
from app.models.evidence import EvidenceVersion
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport

REPO_ROOT = Path(__file__).resolve().parents[1]
P2_3_REVISION = "4e8c1a9d2b57"
P2_2_REVISION = "3d8b6f0a2c51"
SERVICE_MODULE = "app.services.analysis_pipeline"

REQS = [r["id"] for r in get_all_requirements()][:6]

POLICY_TEXT = (
    "Section 4 - Consent.\n\n"
    "The  company   obtains\tconsent before processing any personal data. "
    "Personal data is RETAINED for seven years."
)

ENVELOPE_KEYS = {
    "schema_version",
    "trigger_id",
    "framework_id",
    "model_tiers",
    "inputs",
    "gap_report_id",
    "desk_review_used",
    "claims",
    "error",
}
INPUT_KEYS = {
    "evidence_versions",
    "legacy_document_ids",
    "questionnaire_response_count",
    "applicable_requirements",
}
CLAIM_KEYS = {
    "requirement_id",
    "cluster_id",
    "outcome",
    "scope_enforced",
    "item",
    "quality",
    "conclusion_id",
    "revision_id",
    "disposition",
}
QUALITY_KEYS = {
    "citation_count",
    "evidence_quote_grounded",
    "unsupported_assertion",
    "needs_review",
    "desk_review_red_flags",
    "desk_review_absence",
    "contradictions",
}


def pl():
    """The module under contract. Imported lazily so a missing module fails
    each test individually (FAILED) instead of erroring collection."""

    return importlib.import_module(SERVICE_MODULE)


def ev():
    return importlib.import_module("app.services.evidence")


def cit():
    return importlib.import_module("app.services.citations")


def router():
    return importlib.import_module("app.routers.analysis")


# --------------------------------------------------------------------------- #
# Fixtures (same shape as tests/test_citations.py)
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    return root


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


@pytest.fixture()
def db_path(tmp_path) -> Path:
    path = tmp_path / "analysis_pipeline.sqlite3"
    command.upgrade(_alembic_config(path), "head")
    return path


def _fk_engine(db_path: Path):
    eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return eng


@pytest.fixture()
def engine(db_path):
    eng = _fk_engine(db_path)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def texts(monkeypatch) -> dict[bytes, str]:
    """Deterministic extractor: the extracted text of an upload is whatever
    this dict maps its bytes to (default: a fixed filler sentence)."""

    mapping: dict[bytes, str] = {}

    def _fake_extract(path, file_type):
        return mapping.get(Path(path).read_bytes(), "Filler text with nothing to cite.")

    monkeypatch.setattr(ev(), "extract_text", _fake_extract)
    return mapping


@pytest.fixture()
def gate(monkeypatch):
    """Neutralise everything around the analyzer that is not under contract:
    the questionnaire-completion gate (one expected question, ``Q1``) and
    initiative generation."""

    from app.frameworks import questionnaire_builder

    analysis = router()
    monkeypatch.setattr(analysis, "build_questionnaire", lambda **_kwargs: [{"id": "Q1"}])
    monkeypatch.setattr(analysis, "generate_initiatives", lambda *_args: [])
    monkeypatch.setattr(analysis, "generate_multi_framework_initiatives", lambda *_args: [])
    monkeypatch.setattr(questionnaire_builder, "build_multi_questionnaire", lambda *_a, **_k: [])
    return analysis


# --------------------------------------------------------------------------- #
# Seed and stub helpers
# --------------------------------------------------------------------------- #


def _seed(db, *, frameworks=("dpdpa",), applicable=None, answered=True, client_name="Acme Corp"):
    client = Client(name=client_name, industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name=f"{client_name} gap", status="active")
    db.add(engagement)
    db.flush()
    assessment = Assessment(
        company_name=client_name,
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(list(frameworks)),
        engagement_id=engagement.id,
        applicable_requirements=json.dumps(applicable) if applicable is not None else None,
    )
    db.add(assessment)
    db.flush()
    if answered:
        db.add(
            QuestionnaireResponse(
                assessment_id=assessment.id,
                question_id="Q1",
                answer="fully_implemented",
            )
        )
    db.commit()
    return assessment


def _item(requirement_id, status, *, quote="", current=None, gap=None, risk="medium",
          action=None, needs_review=False):
    """One validated analyzer item, in the exact GapAssessmentItem shape."""
    return {
        "requirement_id": requirement_id,
        "compliance_status": status,
        "current_state": current if current is not None else f"State of {requirement_id}",
        "gap_description": gap if gap is not None else f"Gap in {requirement_id}",
        "risk_level": risk,
        "remediation_action": action if action is not None else f"Fix {requirement_id}",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "process",
        "evidence_quote": quote,
        "needs_review": needs_review,
    }


def _stub_single(monkeypatch, items, *, side_effect=None, raises=None):
    analysis = router()

    def _fake(**_kwargs):
        if side_effect is not None:
            side_effect()
        if raises is not None:
            raise raises
        return {
            "parsed": {"executive_summary": "Synthetic summary", "assessments": copy.deepcopy(items)},
            "raw": "{}",
        }

    monkeypatch.setattr(analysis, "run_gap_analysis", _fake)


def _stub_multi(monkeypatch, per_framework, *, raises=None):
    """``per_framework`` maps framework id -> list of items, or the string
    ``"error"`` for a framework whose analyzer call failed (the shape
    ``run_multi_framework_analysis`` returns for a caught per-framework error)."""
    analysis = router()

    def _fake(**_kwargs):
        if raises is not None:
            raise raises
        frameworks = {}
        for fw_id, items in per_framework.items():
            if items == "error":
                frameworks[fw_id] = {
                    "parsed": {"executive_summary": "Analysis failed: boom", "assessments": []},
                    "raw": "boom",
                    "usage": {},
                    "error": "boom",
                }
            else:
                frameworks[fw_id] = {
                    "parsed": {"executive_summary": f"{fw_id} summary", "assessments": copy.deepcopy(items)},
                    "raw": "{}",
                }
        return {"frameworks": frameworks, "synthesis": None, "total_usage": {}}

    monkeypatch.setattr(analysis, "run_multi_framework_analysis", _fake)


def _pdf(tag: str) -> bytes:
    return b"%PDF-1.4\n% CyberAssess analysis pipeline test " + tag.encode() + b"\n%%EOF\n"


def _upload(db, texts, assessment, *, tag, text_value, filename):
    content = _pdf(tag)
    texts[content] = text_value
    return ev().ingest_upload(
        db,
        assessment_id=assessment.id,
        filename=filename,
        content=content,
        category="privacy_policy",
    )


def _runs(db, assessment_id):
    db.expire_all()
    return (
        db.query(AnalysisRun)
        .filter(AnalysisRun.assessment_id == assessment_id)
        .order_by(AnalysisRun.started_at, AnalysisRun.framework_id)
        .all()
    )


def _envelope(run) -> dict:
    return json.loads(run.claims_json)


def _conclusions(db, assessment_id, framework_id="dpdpa") -> dict[str, Conclusion]:
    db.expire_all()
    rows = (
        db.query(Conclusion)
        .filter(Conclusion.assessment_id == assessment_id, Conclusion.framework_id == framework_id)
        .all()
    )
    return {row.requirement_id: row for row in rows}


def _revisions(db, conclusion_id) -> list[ConclusionRevision]:
    db.expire_all()
    return (
        db.query(ConclusionRevision)
        .filter(ConclusionRevision.conclusion_id == conclusion_id)
        .order_by(ConclusionRevision.created_at, text("conclusion_revisions.rowid"))
        .all()
    )


def _all_revision_ids(db) -> set[str]:
    db.expire_all()
    return {row.id for row in db.query(ConclusionRevision).all()}


def _cluster_map(framework_id: str) -> dict[str, str]:
    from app.frameworks.mappings.clusters import CONTROL_CLUSTERS

    return {
        member["control"]: cluster["cluster_id"]
        for cluster in CONTROL_CLUSTERS
        for member in cluster["controls"]
        if member["framework"] == framework_id
    }


def _human_revision(db, conclusion, action, *, at, actor="consultant"):
    revision = ConclusionRevision(
        conclusion_id=conclusion.id,
        actor=actor,
        action=action,
        previous_outcome=conclusion.outcome,
        previous_rationale=conclusion.rationale,
        citations_json=None,
        created_at=at,
    )
    db.add(revision)
    db.flush()
    return revision


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _later(minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


# --------------------------------------------------------------------------- #
# 1-2. First run, re-run
# --------------------------------------------------------------------------- #


def test_first_run_writes_run_conclusions_and_proposals(db, engine, gate, monkeypatch):
    """Scenario 1: one trigger on the legacy DPDPA path commits a ``running``
    AnalysisRun before the analyzer is called, then completes it with the
    exact envelope; every analyzed requirement gets one Conclusion (version 1,
    ai_proposed) and one ``proposed`` revision linked to the run; GapItems and
    Conclusions share the natural key (framework_id, requirement_id)."""
    P = pl()
    a = _seed(db)
    items = [
        _item(REQS[0], "compliant", current="Consent is captured", gap="None", risk="low"),
        _item(REQS[1], "partially_compliant"),
        _item(REQS[2], "non_compliant", risk="high"),
        _item(REQS[3], "not_applicable"),
        _item(REQS[4], "not_assessed"),
    ]
    seen_during_call: list[list[str]] = []

    def _peek():
        other = sessionmaker(bind=engine)()
        try:
            seen_during_call.append(
                [r.status for r in other.query(AnalysisRun).filter_by(assessment_id=a.id)]
            )
        finally:
            other.close()

    _stub_single(monkeypatch, items, side_effect=_peek)
    result = gate.trigger_analysis(a.id, db)

    assert seen_during_call == [["running"]], "the running row must be committed before the LLM call"

    (run,) = _runs(db, a.id)
    report = db.query(GapReport).filter_by(assessment_id=a.id).one()
    assert result["analysis_run_ids"] == {"dpdpa": run.id}
    assert result["report_id"] == report.id
    assert run.framework_id == "dpdpa"
    assert run.status == "completed"
    assert run.model_id == settings.llm_model_judge
    assert run.started_at is not None and run.completed_at is not None

    env = _envelope(run)
    assert set(env) == ENVELOPE_KEYS
    assert env["schema_version"] == P.CLAIMS_SCHEMA_VERSION == 1
    assert env["framework_id"] == "dpdpa"
    assert isinstance(env["trigger_id"], str) and len(env["trigger_id"]) == 36
    assert env["model_tiers"] == {
        "extract": settings.llm_model_extract,
        "judge": settings.llm_model_judge,
        "synthesize": settings.llm_model_synthesize,
    }
    assert set(env["inputs"]) == INPUT_KEYS
    assert env["inputs"]["questionnaire_response_count"] == 1
    assert env["gap_report_id"] == report.id
    assert env["desk_review_used"] is False
    assert env["error"] is None
    assert run.claims_json == json.dumps(env, sort_keys=True)

    expected_outcomes = {
        REQS[0]: "compliant",
        REQS[1]: "partially_compliant",
        REQS[2]: "non_compliant",
        REQS[3]: "not_applicable",
        REQS[4]: "insufficient_evidence",
    }
    conclusions = _conclusions(db, a.id)
    assert set(conclusions) == set(expected_outcomes)
    clusters = _cluster_map("dpdpa")
    assert [c["requirement_id"] for c in env["claims"]] == [i["requirement_id"] for i in items]
    for claim, item in zip(env["claims"], items):
        req = item["requirement_id"]
        conclusion = conclusions[req]
        (revision,) = _revisions(db, conclusion.id)

        assert set(claim) == CLAIM_KEYS
        assert set(claim["quality"]) == QUALITY_KEYS
        assert claim["item"] == item
        assert claim["outcome"] == expected_outcomes[req]
        assert claim["cluster_id"] == clusters.get(req)
        assert claim["scope_enforced"] is False
        assert claim["disposition"] == "created"
        assert claim["conclusion_id"] == conclusion.id
        assert claim["revision_id"] == revision.id

        assert conclusion.outcome == expected_outcomes[req]
        assert conclusion.rationale == item["current_state"]
        assert conclusion.gaps_identified == item["gap_description"]
        assert conclusion.risk_level == item["risk_level"]
        assert conclusion.recommended_action == item["remediation_action"]
        assert conclusion.evidence_summary == ""
        assert conclusion.cluster_id == clusters.get(req)
        assert conclusion.ai_proposed is True
        assert conclusion.version == 1

        assert revision.action == "proposed"
        assert revision.actor == P.PIPELINE_ACTOR == "system:analysis"
        assert revision.previous_outcome is None
        assert revision.previous_rationale is None
        assert revision.analysis_run_id == run.id
        assert revision.citations_json == "[]"

    gap_keys = {
        (g.framework_id, g.requirement_id)
        for g in db.query(GapItem).filter(GapItem.report_id == report.id)
    }
    assert gap_keys == {(c.framework_id, c.requirement_id) for c in conclusions.values()}


def test_rerun_appends_run_and_revision_history(db, gate, monkeypatch):
    """Scenario 2 (the plan's P2-3 test): two runs -> both AnalysisRuns exist;
    each Conclusion keeps its id, gains a second ``proposed`` revision linked
    to the second run, takes the second run's content and version 2; the
    second revision's previous_* hold the first proposal. An identical
    proposal is still recorded (and still bumps the version)."""
    pl()
    a = _seed(db)
    first = [_item(REQS[0], "compliant", current="Consent v1"), _item(REQS[1], "non_compliant")]
    second = [_item(REQS[0], "partially_compliant", current="Consent v2"), _item(REQS[1], "non_compliant")]

    _stub_single(monkeypatch, first)
    gate.trigger_analysis(a.id, db)
    before = _conclusions(db, a.id)
    ids_before = {req: c.id for req, c in before.items()}

    _stub_single(monkeypatch, second)
    gate.trigger_analysis(a.id, db)

    run1, run2 = _runs(db, a.id)
    assert (run1.status, run2.status) == ("completed", "completed")
    assert _envelope(run1)["trigger_id"] != _envelope(run2)["trigger_id"]
    assert [c["disposition"] for c in _envelope(run2)["claims"]] == ["applied", "applied"]

    after = _conclusions(db, a.id)
    assert {req: c.id for req, c in after.items()} == ids_before
    changed = after[REQS[0]]
    assert (changed.outcome, changed.rationale, changed.version) == ("partially_compliant", "Consent v2", 2)

    revisions = _revisions(db, changed.id)
    assert [r.action for r in revisions] == ["proposed", "proposed"]
    assert [r.analysis_run_id for r in revisions] == [run1.id, run2.id]
    assert (revisions[1].previous_outcome, revisions[1].previous_rationale) == ("compliant", "Consent v1")

    same = after[REQS[1]]
    assert same.version == 2
    assert [r.analysis_run_id for r in _revisions(db, same.id)] == [run1.id, run2.id]


# --------------------------------------------------------------------------- #
# 3-4. Human decisions are never overwritten
# --------------------------------------------------------------------------- #


def test_rerun_never_overwrites_a_human_decision(db, gate, monkeypatch):
    """Scenario 3: an approved or edited Conclusion is left byte-for-byte
    unchanged by a re-run (content, version, updated_at, ai_proposed); the
    run's proposal is still recorded as a ``proposal_withheld`` revision with
    its citations and run link. A reopened Conclusion is unlocked again and
    gets the proposal applied. The legacy GapItem view keeps today's re-run
    semantics (it shows the new AI verdict)."""
    pl()
    a = _seed(db)
    first = [_item(REQS[0], "compliant"), _item(REQS[1], "non_compliant"), _item(REQS[2], "non_compliant")]
    _stub_single(monkeypatch, first)
    gate.trigger_analysis(a.id, db)

    c = _conclusions(db, a.id)
    # Human decisions happen between run 1 and run 2, so they are stamped "now".
    _human_revision(db, c[REQS[0]], "approved", at=_now())
    # Simulate a P2-4 "edit": human content, version bumped, no longer AI-proposed.
    edited = c[REQS[1]]
    _human_revision(db, edited, "edited", at=_now())
    edited.outcome = "partially_compliant"
    edited.rationale = "Consultant-written rationale"
    edited.ai_proposed = False
    edited.version = 2
    _human_revision(db, c[REQS[2]], "approved", at=_now())
    _human_revision(db, c[REQS[2]], "reopened", at=_now())
    db.commit()

    columns = ("outcome", "rationale", "evidence_summary", "gaps_identified", "risk_level",
               "recommended_action", "cluster_id", "ai_proposed", "version", "updated_at")
    current = _conclusions(db, a.id)
    snapshot = {req: {col: getattr(current[req], col) for col in columns} for req in (REQS[0], REQS[1])}

    second = [_item(REQS[0], "non_compliant", current="AI now disagrees"),
              _item(REQS[1], "non_compliant", current="AI still says no"),
              _item(REQS[2], "partially_compliant", current="Reopened, re-proposed")]
    _stub_single(monkeypatch, second)
    gate.trigger_analysis(a.id, db)
    _run1, run2 = _runs(db, a.id)
    claims = {claim["requirement_id"]: claim for claim in _envelope(run2)["claims"]}

    after = _conclusions(db, a.id)
    for req in (REQS[0], REQS[1]):
        assert {col: getattr(after[req], col) for col in columns} == snapshot[req]
        latest = _revisions(db, after[req].id)[-1]
        assert latest.action == "proposal_withheld"
        assert latest.actor == "system:analysis"
        assert latest.analysis_run_id == run2.id
        assert latest.previous_outcome == after[req].outcome
        assert latest.previous_rationale == after[req].rationale
        assert latest.citations_json == "[]"
        assert claims[req]["disposition"] == "withheld"
        assert claims[req]["revision_id"] == latest.id
        assert claims[req]["outcome"] == "non_compliant"

    reopened = after[REQS[2]]
    assert (reopened.outcome, reopened.rationale, reopened.version) == (
        "partially_compliant", "Reopened, re-proposed", 2,
    )
    assert _revisions(db, reopened.id)[-1].action == "proposed"
    assert claims[REQS[2]]["disposition"] == "applied"

    report = db.query(GapReport).filter_by(assessment_id=a.id).one()
    gap = db.query(GapItem).filter_by(report_id=report.id, requirement_id=REQS[0]).one()
    assert gap.compliance_status == "non_compliant"


@pytest.mark.parametrize(
    ("actions", "locked"),
    [
        ((), False),
        (("approved",), True),
        (("edited",), True),
        (("rejected",), False),
        (("reopened",), False),
        (("approved", "reopened"), False),
        (("approved", "reopened", "approved"), True),
        (("edited", "rejected"), False),
        (("rejected", "edited"), True),
        (("approved", "proposed", "proposal_withheld"), True),
    ],
    ids=lambda v: "-".join(v) if isinstance(v, tuple) else str(v),
)
def test_lock_rule_is_the_latest_human_decision(db, actions, locked):
    """Scenario 4: a Conclusion is locked iff its most recent revision whose
    action is in HUMAN_DECISION_ACTIONS has an action in LOCKING_ACTIONS.
    System revisions (proposed / proposal_withheld) never unlock."""
    P = pl()
    assert P.HUMAN_DECISION_ACTIONS == ("approved", "edited", "rejected", "reopened")
    assert P.LOCKING_ACTIONS == ("approved", "edited")

    a = _seed(db)
    conclusion = Conclusion(
        assessment_id=a.id, requirement_id=REQS[0], framework_id="dpdpa",
        outcome="compliant", rationale="r", evidence_summary="", gaps_identified="g",
        risk_level="low", recommended_action="a", ai_proposed=True, version=3,
    )
    db.add(conclusion)
    db.flush()
    _human_revision(db, conclusion, "proposed", at=_later(0), actor="system:analysis")
    for minutes, action in enumerate(actions, start=1):
        actor = "system:analysis" if action in ("proposed", "proposal_withheld") else "consultant"
        _human_revision(db, conclusion, action, at=_later(minutes), actor=actor)
    db.commit()

    state = P.load_conclusion_state(db, assessment_id=a.id, framework_id="dpdpa")
    assert set(state) == {REQS[0]}
    assert state[REQS[0]].locked is locked
    assert state[REQS[0]].expected_version == 3
    assert state[REQS[0]].conclusion.id == conclusion.id
    assert P.load_conclusion_state(db, assessment_id=a.id, framework_id="iso27001") == {}


# --------------------------------------------------------------------------- #
# 5-6. Citations and recorded inputs
# --------------------------------------------------------------------------- #


def test_claims_cite_their_own_quote_against_evidence(db, texts, gate, monkeypatch):
    """Scenario 5: each claim cites exactly its own ``evidence_quote`` through
    the P2-2 path. A grounded quote becomes a ``text_span`` citation whose
    excerpt is the document's raw text; a fabricated quote gets ``[]`` and,
    on a compliant claim, the unsupported-assertion flag; a claim with no
    quote records ``evidence_quote_grounded: null``. Every revision stores an
    array (never NULL), and every stored citation re-validates."""
    P = pl()
    c = cit()
    a = _seed(db)
    policy = _upload(db, texts, a, tag="policy", text_value=POLICY_TEXT, filename="policy.pdf")
    items = [
        _item(REQS[0], "compliant", quote="obtains consent before processing"),
        _item(REQS[1], "compliant", quote="we encrypt everything at rest"),
        _item(REQS[2], "non_compliant", quote=""),
        _item(REQS[3], "partially_compliant", quote="retained for seven years", needs_review=True),
    ]
    _stub_single(monkeypatch, items)
    gate.trigger_analysis(a.id, db)

    (run,) = _runs(db, a.id)
    env = _envelope(run)
    assert env["inputs"]["evidence_versions"] == [
        {"evidence_id": policy.evidence.id, "version_id": policy.version.id, "filename": "policy.pdf"}
    ]
    claims = {claim["requirement_id"]: claim for claim in env["claims"]}
    conclusions = _conclusions(db, a.id)

    grounded = _revisions(db, conclusions[REQS[0]].id)[0]
    (citation,) = c.loads_citations(grounded.citations_json)
    assert citation["evidence_version_id"] == policy.version.id
    assert citation["location_type"] == "text_span"
    start, end = (int(x) for x in citation["location_ref"].removeprefix("chars:").split("-"))
    assert citation["excerpt"] == POLICY_TEXT[start:end] == "obtains\tconsent before processing"
    assert claims[REQS[0]]["quality"] == {
        "citation_count": 1, "evidence_quote_grounded": True, "unsupported_assertion": False,
        "needs_review": False, "desk_review_red_flags": 0, "desk_review_absence": False,
        "contradictions": None,
    }
    assert conclusions[REQS[0]].evidence_summary == "obtains consent before processing"

    assert _revisions(db, conclusions[REQS[1]].id)[0].citations_json == "[]"
    assert claims[REQS[1]]["quality"]["evidence_quote_grounded"] is False
    assert claims[REQS[1]]["quality"]["unsupported_assertion"] is True
    assert claims[REQS[1]]["quality"]["citation_count"] == 0
    assert conclusions[REQS[1]].evidence_summary == ""

    assert _revisions(db, conclusions[REQS[2]].id)[0].citations_json == "[]"
    assert claims[REQS[2]]["quality"]["evidence_quote_grounded"] is None
    assert claims[REQS[2]]["quality"]["unsupported_assertion"] is False

    assert claims[REQS[3]]["quality"]["citation_count"] == 1
    assert claims[REQS[3]]["quality"]["needs_review"] is True
    assert claims[REQS[3]]["quality"]["unsupported_assertion"] is False

    for conclusion in conclusions.values():
        for revision in _revisions(db, conclusion.id):
            assert revision.citations_json is not None
            c.validate_citations(db, c.loads_citations(revision.citations_json), assessment_id=a.id)


def test_run_records_its_inputs(db, texts, gate, monkeypatch):
    """Scenario 6: ``inputs`` records exactly what analysis was offered --
    the active version of in-scope, active Evidence (not a superseded v1, not
    archived Evidence), un-migrated legacy AssessmentDocument ids, the
    questionnaire response count and the assessment's applicable
    requirements. A quote found only in a legacy document is not citable."""
    pl()
    a = _seed(db, applicable=[REQS[0], REQS[1]])
    kept = _upload(db, texts, a, tag="kept-v1", text_value="Version one text.", filename="kept.pdf")
    content = _pdf("kept-v2")
    texts[content] = "Version two text about consent logs."
    v2 = ev().ingest_new_version(
        db, evidence_id=kept.evidence.id, filename="kept-v2.pdf", content=content,
        change_reason="Refresh",
    )
    archived = _upload(db, texts, a, tag="gone", text_value="Archived text.", filename="gone.pdf")
    ev().transition_evidence(db, evidence_id=archived.evidence.id, to_status="archived", actor="consultant")
    legacy = AssessmentDocument(
        assessment_id=a.id, filename="legacy.txt", file_path="/nonexistent/legacy.txt",
        file_type="txt", document_category="other",
        extracted_text="Only the legacy document says we pseudonymise backups.",
    )
    db.add(legacy)
    db.commit()

    _stub_single(monkeypatch, [
        _item(REQS[0], "compliant", quote="we pseudonymise backups"),
        _item(REQS[1], "compliant", quote="consent logs"),
    ])
    gate.trigger_analysis(a.id, db)

    (run,) = _runs(db, a.id)
    inputs = _envelope(run)["inputs"]
    assert inputs == {
        "evidence_versions": [
            {"evidence_id": kept.evidence.id, "version_id": v2.version.id, "filename": "kept-v2.pdf"}
        ],
        "legacy_document_ids": [legacy.id],
        "questionnaire_response_count": 1,
        "applicable_requirements": [REQS[0], REQS[1]],
    }
    conclusions = _conclusions(db, a.id)
    assert _revisions(db, conclusions[REQS[0]].id)[0].citations_json == "[]"
    cited = json.loads(_revisions(db, conclusions[REQS[1]].id)[0].citations_json)
    assert [x["evidence_version_id"] for x in cited] == [v2.version.id]


# --------------------------------------------------------------------------- #
# 7-8. Failure is closed and non-destructive
# --------------------------------------------------------------------------- #


def test_evidence_changing_mid_run_fails_the_run_closed(db, engine, texts, gate, monkeypatch):
    """Scenario 7: sources are snapshotted when the run starts. If a version
    the run would cite stops being active before the results are saved (here:
    another connection commits a supersession while the analyzer runs),
    ``attach_citations`` refuses it, and the whole save rolls back: the run is
    ``failed`` with error type ``CitationError``, no revision is written, the
    previous GapReport survives, and the assessment is in ``error``."""
    pl()
    a = _seed(db)
    policy = _upload(db, texts, a, tag="policy", text_value=POLICY_TEXT, filename="policy.pdf")
    items = [_item(REQS[0], "compliant", quote="obtains consent before processing")]
    _stub_single(monkeypatch, items)
    gate.trigger_analysis(a.id, db)
    report_id = db.query(GapReport).filter_by(assessment_id=a.id).one().id
    revisions_before = _all_revision_ids(db)
    conclusion_before = _conclusions(db, a.id)[REQS[0]]
    version_before = conclusion_before.version
    policy_version_id = policy.version.id

    def _supersede_mid_run():
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE evidence_versions SET status = 'superseded' WHERE id = :vid"),
                {"vid": policy_version_id},
            )

    _stub_single(monkeypatch, items, side_effect=_supersede_mid_run)
    with pytest.raises(HTTPException) as excinfo:
        gate.trigger_analysis(a.id, db)
    assert excinfo.value.status_code == 500

    _run1, run2 = _runs(db, a.id)
    assert run2.status == "failed"
    assert run2.completed_at is not None
    env = _envelope(run2)
    assert env["error"] == {"type": "CitationError"}
    assert env["claims"] == []
    assert env["gap_report_id"] is None
    assert _all_revision_ids(db) == revisions_before
    assert _conclusions(db, a.id)[REQS[0]].version == version_before
    assert db.query(GapReport).filter_by(assessment_id=a.id).one().id == report_id
    assert db.get(Assessment, a.id).status == "error"
    assert db.get(EvidenceVersion, policy_version_id).status == "superseded"


def test_analyzer_failures_mark_the_run_failed_and_write_nothing(db, gate, monkeypatch):
    """Scenario 8: an analyzer exception -> run ``failed`` with the exception
    type (no message), HTTP 500 as today, no Conclusion or revision; an empty
    response -> ``EmptyAssessment``. Earlier conclusions are untouched. A
    trigger refused by the 400 gate creates no AnalysisRun at all."""
    pl()
    from app.schemas.llm_output import IncompleteAssessmentError

    a = _seed(db)
    _stub_single(monkeypatch, [_item(REQS[0], "compliant")])
    gate.trigger_analysis(a.id, db)
    revisions_before = _all_revision_ids(db)

    _stub_single(monkeypatch, [], raises=IncompleteAssessmentError("client text must not be stored"))
    with pytest.raises(HTTPException) as excinfo:
        gate.trigger_analysis(a.id, db)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail.startswith("Analysis failed")

    _stub_single(monkeypatch, [])
    with pytest.raises(HTTPException) as excinfo:
        gate.trigger_analysis(a.id, db)
    assert excinfo.value.status_code == 500

    ok, raised, empty = _runs(db, a.id)
    assert ok.status == "completed"
    for run, error_type in ((raised, "IncompleteAssessmentError"), (empty, "EmptyAssessment")):
        env = _envelope(run)
        assert run.status == "failed"
        assert run.completed_at is not None
        assert env["error"] == {"type": error_type}
        assert env["claims"] == []
        assert "client text" not in run.claims_json
    assert _all_revision_ids(db) == revisions_before
    assert len(_conclusions(db, a.id)) == 1

    refused = _seed(db, answered=False, client_name="Refused Co")
    with pytest.raises(HTTPException) as excinfo:
        gate.trigger_analysis(refused.id, db)
    assert excinfo.value.status_code == 400
    assert _runs(db, refused.id) == []


def test_runs_are_never_deleted(db, gate, monkeypatch):
    """Scenario 8: across success, failure and success, every AnalysisRun,
    Conclusion and ConclusionRevision row ever written still exists."""
    pl()
    a = _seed(db)
    seen_runs: set[str] = set()
    seen_conclusions: set[str] = set()
    seen_revisions: set[str] = set()

    def _check():
        db.expire_all()
        runs = {r.id for r in db.query(AnalysisRun).all()}
        conclusions = {c.id for c in db.query(Conclusion).all()}
        revisions = {r.id for r in db.query(ConclusionRevision).all()}
        assert seen_runs <= runs and seen_conclusions <= conclusions and seen_revisions <= revisions
        seen_runs.update(runs)
        seen_conclusions.update(conclusions)
        seen_revisions.update(revisions)

    _stub_single(monkeypatch, [_item(REQS[0], "compliant"), _item(REQS[1], "non_compliant")])
    gate.trigger_analysis(a.id, db)
    _check()
    _stub_single(monkeypatch, [], raises=RuntimeError("provider down"))
    with pytest.raises(HTTPException):
        gate.trigger_analysis(a.id, db)
    _check()
    _stub_single(monkeypatch, [_item(REQS[0], "non_compliant")])
    gate.trigger_analysis(a.id, db)
    _check()
    assert len(seen_runs) == 3
    assert len(seen_revisions) == 3
    # REQS[1] was not in the third run's output: its conclusion is left alone, not deleted.
    assert _conclusions(db, a.id)[REQS[1]].version == 1


# --------------------------------------------------------------------------- #
# 9. Multi-framework
# --------------------------------------------------------------------------- #


def _controls(framework_id: str, n: int = 2) -> list[str]:
    from app.frameworks.registry import FrameworkRegistry

    return [c.id for c in FrameworkRegistry.get(framework_id).all_controls()[:n]]


def test_multi_framework_writes_one_run_per_framework(db, gate, monkeypatch):
    """Scenario 9: one run per selected framework, sharing one trigger_id. A
    framework whose analyzer call failed gets a ``failed`` run
    (``FrameworkAnalysisError``) and no Conclusions; the others complete and
    get Conclusions scoped to their own framework_id. A whole-call exception
    fails every run."""
    pl()
    frameworks = ["dpdpa", "iso27001", "gdpr"]
    a = _seed(db, frameworks=frameworks)
    dpdpa, gdpr = _controls("dpdpa"), _controls("gdpr")
    _stub_multi(monkeypatch, {
        "dpdpa": [_item(dpdpa[0], "compliant"), _item(dpdpa[1], "non_compliant")],
        "iso27001": "error",
        "gdpr": [_item(gdpr[0], "partially_compliant")],
    })
    result = gate.trigger_analysis(a.id, db)

    runs = {run.framework_id: run for run in _runs(db, a.id)}
    assert set(runs) == set(frameworks)
    assert result["analysis_run_ids"] == {fw: runs[fw].id for fw in frameworks}
    assert len({_envelope(run)["trigger_id"] for run in runs.values()}) == 1
    report = db.query(GapReport).filter_by(assessment_id=a.id).one()

    assert runs["iso27001"].status == "failed"
    assert _envelope(runs["iso27001"])["error"] == {"type": "FrameworkAnalysisError"}
    assert _conclusions(db, a.id, "iso27001") == {}

    for fw, expected in (("dpdpa", set(dpdpa)), ("gdpr", {gdpr[0]})):
        env = _envelope(runs[fw])
        assert runs[fw].status == "completed"
        assert env["framework_id"] == fw
        assert env["gap_report_id"] == report.id
        conclusions = _conclusions(db, a.id, fw)
        assert set(conclusions) == expected
        for conclusion in conclusions.values():
            (revision,) = _revisions(db, conclusion.id)
            assert revision.analysis_run_id == runs[fw].id

    _stub_multi(monkeypatch, {}, raises=RuntimeError("provider down"))
    with pytest.raises(HTTPException) as excinfo:
        gate.trigger_analysis(a.id, db)
    assert excinfo.value.status_code == 500
    latest = [run for run in _runs(db, a.id) if run.id not in {r.id for r in runs.values()}]
    assert sorted(run.framework_id for run in latest) == sorted(frameworks)
    assert {run.status for run in latest} == {"failed"}
    assert {json.dumps(_envelope(run)["error"]) for run in latest} == {'{"type": "RuntimeError"}'}


# --------------------------------------------------------------------------- #
# 10. Optimistic locking against a concurrent consultant write (D6)
# --------------------------------------------------------------------------- #


def test_concurrent_human_write_fails_the_run_instead_of_overwriting(db, gate, monkeypatch):
    """Scenario 10: an applied proposal is a compare-and-swap on
    ``Conclusion.version``. If the version moves between
    ``load_conclusion_state`` and the write (a consultant saved in between),
    the run fails closed with ``ConclusionConflict``; nothing is written."""
    P = pl()
    assert issubclass(P.ConclusionConflict, P.AnalysisPipelineError)
    a = _seed(db)
    _stub_single(monkeypatch, [_item(REQS[0], "compliant")])
    gate.trigger_analysis(a.id, db)
    revisions_before = _all_revision_ids(db)

    real = P.load_conclusion_state

    def _load_then_race(session, **kwargs):
        state = real(session, **kwargs)
        session.execute(
            text("UPDATE conclusions SET version = version + 1 WHERE assessment_id = :aid"),
            {"aid": a.id},
        )
        return state

    monkeypatch.setattr(P, "load_conclusion_state", _load_then_race)
    _stub_single(monkeypatch, [_item(REQS[0], "non_compliant")])
    with pytest.raises(HTTPException) as excinfo:
        gate.trigger_analysis(a.id, db)
    assert excinfo.value.status_code == 500

    _run1, run2 = _runs(db, a.id)
    assert run2.status == "failed"
    assert _envelope(run2)["error"] == {"type": "ConclusionConflict"}
    assert _all_revision_ids(db) == revisions_before
    assert _conclusions(db, a.id)[REQS[0]].outcome == "compliant"


# --------------------------------------------------------------------------- #
# 11. Claim quality, scope enforcement, duplicates, unknown statuses
# --------------------------------------------------------------------------- #


def test_claim_quality_scope_and_duplicates(db, gate, monkeypatch):
    """Scenario 11: out-of-scope requirements are recorded as enforced
    ``not_applicable``; desk-review red flags and absences are counted per
    requirement; ``contradictions`` is ``null`` (not assessed by this
    pipeline version); a duplicate requirement keeps its first occurrence
    only; an unknown status maps to ``insufficient_evidence``."""
    P = pl()
    a = _seed(db, applicable=[REQS[0], REQS[1], REQS[3]])
    db.add(DeskReviewSummary(assessment_id=a.id, status="completed", coverage_summary="{}"))
    for req, kind in ((REQS[0], "signal"), (REQS[0], "signal"), (REQS[1], "absence"), (REQS[3], "evidence")):
        db.add(DeskReviewFinding(
            assessment_id=a.id, finding_type=kind, requirement_id=req, content=f"{kind} finding",
            severity="high", citations_json="[]",
        ))
    db.commit()

    items = [
        _item(REQS[0], "non_compliant", needs_review=True),
        _item(REQS[1], "non_compliant"),
        _item(REQS[2], "compliant"),  # out of scope -> enforced not_applicable
        _item(REQS[0], "compliant"),  # duplicate -> ignored
        _item(REQS[3], "fully_compliant"),  # unknown status
    ]
    _stub_single(monkeypatch, items)
    gate.trigger_analysis(a.id, db)

    (run,) = _runs(db, a.id)
    env = _envelope(run)
    assert env["desk_review_used"] is True
    assert [c["requirement_id"] for c in env["claims"]] == [REQS[0], REQS[1], REQS[2], REQS[3]]
    claims = {claim["requirement_id"]: claim for claim in env["claims"]}

    assert claims[REQS[0]]["quality"]["desk_review_red_flags"] == 2
    assert claims[REQS[0]]["quality"]["needs_review"] is True
    assert claims[REQS[0]]["outcome"] == "non_compliant"
    assert claims[REQS[1]]["quality"]["desk_review_absence"] is True
    assert claims[REQS[1]]["quality"]["desk_review_red_flags"] == 0
    assert claims[REQS[2]]["scope_enforced"] is True
    assert claims[REQS[2]]["outcome"] == "not_applicable"
    assert claims[REQS[2]]["item"]["compliance_status"] == "not_applicable"
    assert claims[REQS[3]]["outcome"] == "insufficient_evidence"
    assert all(claim["quality"]["contradictions"] is None for claim in env["claims"])

    conclusions = _conclusions(db, a.id)
    assert set(conclusions) == {REQS[0], REQS[1], REQS[2], REQS[3]}
    assert conclusions[REQS[0]].outcome == "non_compliant"
    assert conclusions[REQS[2]].outcome == "not_applicable"
    assert conclusions[REQS[3]].outcome == "insufficient_evidence"
    assert len(_revisions(db, conclusions[REQS[0]].id)) == 1

    from scripts.migrate_legacy import OUTCOME_MAP

    assert P.OUTCOME_BY_STATUS == OUTCOME_MAP


# --------------------------------------------------------------------------- #
# 12. Legacy consumers are untouched (D-P2-3-A)
# --------------------------------------------------------------------------- #


def test_legacy_report_path_is_unchanged(db, gate, monkeypatch):
    """Scenario 12: the GapReport/GapItem write is exactly today's (one item
    per analyzer item, draft review status, AI fields), and deterministic
    scoring still reads GapItems and works."""
    pl()
    from app.services.scoring import score

    a = _seed(db)
    items = [_item(REQS[0], "compliant"), _item(REQS[1], "non_compliant")]
    _stub_single(monkeypatch, items)
    result = gate.trigger_analysis(a.id, db)
    assert set(result) == {
        "report_id", "status", "per_framework_scores", "initiatives_generated", "message",
        "analysis_run_ids",
    }
    report = db.query(GapReport).filter_by(assessment_id=a.id).one()
    gap_items = db.query(GapItem).filter_by(report_id=report.id).all()
    assert sorted((g.requirement_id, g.compliance_status, g.review_status, g.ai_compliance_status)
                  for g in gap_items) == sorted(
        (i["requirement_id"], i["compliance_status"], "draft", i["compliance_status"]) for i in items
    )
    assert score(a.id, ["dpdpa"], _session=db).per_framework["dpdpa"].covered_control_count > 0


def test_release_readers_do_not_read_ai_outcomes():
    """Scenario 12: release readers use the approved Conclusions reader."""
    result = subprocess.run(
        [
            "grep", "-nE", r"\bGapItem\b|\bInitiative\b|report_framework_scores|chapter_scores\)|\.executive_summary",
            "app/routers/reports.py", "app/utils/review_gate.py",
            "app/services/report_content.py", "app/routers/integrated_reports.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.stdout == "", result.stdout


def test_pipeline_code_never_deletes_runs_or_conclusions():
    """Scenario 12 (standing guard): the pipeline module contains no delete,
    and the analysis router deletes nothing but the legacy GapItem /
    Initiative / GapReport rows it already replaced before P2-3."""
    source = (REPO_ROOT / "app" / "services" / "analysis_pipeline.py")
    if source.exists():
        assert "delete" not in source.read_text(encoding="utf-8")
    for line in (REPO_ROOT / "app" / "routers" / "analysis.py").read_text(encoding="utf-8").splitlines():
        if "delete" in line:
            assert "AnalysisRun" not in line and "Conclusion" not in line, line


# --------------------------------------------------------------------------- #
# 13. Alembic
# --------------------------------------------------------------------------- #


def test_p2_3_revision_is_head_and_adds_link_and_uniqueness(db_path, engine, db):
    """Scenario 13: head is 4e8c1a9d2b57 on top of 3d8b6f0a2c51; it adds the
    nullable ``conclusion_revisions.analysis_run_id`` FK (indexed) and a
    unique index on conclusions (assessment_id, framework_id,
    requirement_id), which is enforced."""
    script = ScriptDirectory.from_config(_alembic_config(db_path))
    assert script.get_revision("8b2d5f7e1c34").down_revision == P2_3_REVISION
    assert script.get_revision(P2_3_REVISION).down_revision == P2_2_REVISION

    inspector = inspect(engine)
    columns = {col["name"]: col for col in inspector.get_columns("conclusion_revisions")}
    assert columns["analysis_run_id"]["nullable"] is True
    assert any(
        fk["referred_table"] == "analysis_runs" and fk["constrained_columns"] == ["analysis_run_id"]
        for fk in inspector.get_foreign_keys("conclusion_revisions")
    )
    assert "ix_conclusion_revisions_analysis_run_id" in {
        i["name"] for i in inspector.get_indexes("conclusion_revisions")
    }
    unique = {i["name"]: i for i in inspector.get_indexes("conclusions")}[
        "uq_conclusions_assessment_framework_requirement"
    ]
    assert unique["unique"] in (True, 1)
    assert unique["column_names"] == ["assessment_id", "framework_id", "requirement_id"]

    a = _seed(db)
    for _ in range(2):
        db.add(Conclusion(
            assessment_id=a.id, requirement_id=REQS[0], framework_id="dpdpa", outcome="compliant",
            rationale="r", evidence_summary="", gaps_identified="g", risk_level="low",
            recommended_action="a", ai_proposed=True,
        ))
    with pytest.raises(Exception, match="UNIQUE"):
        db.commit()
    db.rollback()


def test_p2_3_upgrade_refuses_duplicate_conclusions(tmp_path):
    """Scenario 13: a database at 3d8b6f0a2c51 holding two conclusions for
    one (assessment, framework, requirement) refuses to upgrade instead of
    failing half-way or silently dropping a row."""
    path = tmp_path / "dupes.sqlite3"
    config = _alembic_config(path)
    command.upgrade(config, P2_2_REVISION)
    eng = create_engine(f"sqlite:///{path}")
    with eng.begin() as conn:
        conn.execute(text(
            "INSERT INTO assessments (id, company_name, industry, company_size, status, version, "
            "created_at, updated_at) VALUES ('a1', 'Dup Co', 'Tech', 'small', 'created', 1, "
            "'2026-09-23 00:00:00', '2026-09-23 00:00:00')"
        ))
        for cid in ("c1", "c2"):
            conn.execute(text(
                "INSERT INTO conclusions (id, assessment_id, requirement_id, framework_id, outcome, "
                "rationale, evidence_summary, gaps_identified, risk_level, recommended_action, "
                "ai_proposed, version, created_at, updated_at) VALUES (:cid, 'a1', 'CH2.CONSENT.1', "
                "'dpdpa', 'compliant', 'r', '', 'g', 'low', 'a', 1, 1, '2026-09-23 00:00:00', "
                "'2026-09-23 00:00:00')"
            ), {"cid": cid})
    eng.dispose()
    with pytest.raises(RuntimeError, match="Refusing to add uq_conclusions_assessment_framework_requirement"):
        command.upgrade(config, "head")
    eng = create_engine(f"sqlite:///{path}")
    with eng.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == P2_2_REVISION
        assert conn.execute(text("SELECT COUNT(*) FROM conclusions")).scalar() == 2
    eng.dispose()


def test_p2_3_downgrade_refuses_while_revisions_link_runs(db, db_path, engine, gate, monkeypatch):
    """Scenario 13: downgrading past 4e8c1a9d2b57 refuses while any revision
    is linked to a run; once cleared it drops the column and index, and
    re-upgrading restores them."""
    pl()
    a = _seed(db)
    _stub_single(monkeypatch, [_item(REQS[0], "compliant")])
    gate.trigger_analysis(a.id, db)
    db.close()
    engine.dispose()

    config = _alembic_config(db_path)
    with pytest.raises(RuntimeError, match="Refusing to downgrade past P2-3"):
        command.downgrade(config, P2_2_REVISION)

    eng = create_engine(f"sqlite:///{db_path}")
    with eng.begin() as conn:
        conn.execute(text("UPDATE conclusion_revisions SET analysis_run_id = NULL"))
    eng.dispose()
    command.downgrade(config, P2_2_REVISION)
    inspector = inspect(create_engine(f"sqlite:///{db_path}"))
    assert "analysis_run_id" not in {c["name"] for c in inspector.get_columns("conclusion_revisions")}
    assert "uq_conclusions_assessment_framework_requirement" not in {
        i["name"] for i in inspector.get_indexes("conclusions")
    }
    command.upgrade(config, "head")
    inspector = inspect(create_engine(f"sqlite:///{db_path}"))
    assert "analysis_run_id" in {c["name"] for c in inspector.get_columns("conclusion_revisions")}


# --------------------------------------------------------------------------- #
# 14. Coexistence with the P1-3 legacy migration script
# --------------------------------------------------------------------------- #


def test_migrate_legacy_skips_pipeline_owned_assessments(db, gate, monkeypatch):
    """Scenario 14: ``scripts/migrate_legacy.run_migration`` must not map
    GapItems of an assessment that has AnalysisRuns (its Conclusions are
    owned by the pipeline). Without the skip it would crash on the second
    ``proposed`` revision (``scalar_one_or_none``) and create one Finding per
    ``open`` GapItem."""
    pl()
    from app.models.finding import Finding
    from scripts.migrate_legacy import run_migration

    a = _seed(db)
    _stub_single(monkeypatch, [_item(REQS[0], "compliant"), _item(REQS[1], "non_compliant")])
    gate.trigger_analysis(a.id, db)
    gate.trigger_analysis(a.id, db)
    revisions_before = _all_revision_ids(db)

    stats = run_migration(db)

    assert stats.conclusions == 0
    assert stats.conclusion_revisions == 0
    assert stats.findings == 0 and stats.actions == 0
    assert any(a.id in warning and "analysis pipeline" in warning for warning in stats.warnings)
    assert _all_revision_ids(db) == revisions_before
    assert db.query(Finding).filter_by(assessment_id=a.id).count() == 0


# --------------------------------------------------------------------------- #
# 15. Citation lookup cost does not scale with requirements x document size
# --------------------------------------------------------------------------- #


def test_each_source_text_is_normalized_once_per_run(db, texts, gate, monkeypatch):
    """Scenario 15: locating N quotes across S sources normalizes each
    source's text at most once (``app.services.citations`` memoizes the
    text side of ``locate_excerpt``), instead of N x S times."""
    pl()
    c = cit()
    a = _seed(db)
    bodies = [f"Document {n} unique body {n * 7919} " + ("filler words " * 400) for n in range(3)]
    bodies[2] += " ".join(f"control statement {i} is implemented." for i in range(6))
    for n, body in enumerate(bodies):
        _upload(db, texts, a, tag=f"src{n}", text_value=body, filename=f"src{n}.pdf")

    real = c.normalize_with_offsets
    calls: list[str] = []

    def _spy(value):
        calls.append(value)
        return real(value)

    monkeypatch.setattr(c, "normalize_with_offsets", _spy)
    items = [_item(req, "compliant", quote=f"control statement {i} is implemented")
             for i, req in enumerate(REQS)]
    _stub_single(monkeypatch, items)
    gate.trigger_analysis(a.id, db)

    for body in bodies:
        assert calls.count(body) <= 1, "a source text was re-normalized for every quote"
    cited = [
        json.loads(r.citations_json)
        for conclusion in _conclusions(db, a.id).values()
        for r in _revisions(db, conclusion.id)
    ]
    assert all(len(x) == 1 for x in cited)
