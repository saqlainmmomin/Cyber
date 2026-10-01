"""Shared fixtures and helpers for the P6-10 contract tests (Stages 3 and 4).

Handoff: tasks/handoffs/2026-09-28-p6-10-remediation-and-narrative.md.
Kept outside tests/support/ and tests/fixtures/ so those canonical-data guards stay untouched.

Every test runs against an Alembic-`head` SQLite database and the real FastAPI app. The real
`llm_client.call_llm` is replaced by a function that fails the test, so nothing here can reach
the network; each test patches the module-level `_call_llm` seam of the service under test with
a `FakeLLM` instead. Assessments are analysed through the real (v1, the default) analysis route
with both analyzer seams faked, exactly as the P6-8 suite does.
"""

from __future__ import annotations

import copy
import json
import subprocess
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.database import get_db
from app.frameworks.registry import FrameworkRegistry
from app.main import app
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.questionnaire import QuestionnaireResponse
from app.services import approved_report, report_basis

REPO_ROOT = Path(__file__).resolve().parents[1]
PERIOD = {
    "period_start": date(2026, 4, 1),
    "period_end": date(2026, 6, 30),
    "evidence_cutoff": date(2026, 7, 15),
}
REVIEWER = "Priya"
DP_FINDING_TITLE = "Consent is not freely given"
DP_FINDING_DESCRIPTION = "Consent is collected through a pre-ticked box on the signup page."
ISO_FINDING_TITLE = "Access reviews are informal"
ISO_FINDING_DESCRIPTION = "Quarterly user access reviews are not evidenced."

# Every app/ path P6-10a and P6-10b may add or change (handoff "Files touched").
P6_10_APP_FILES = (
    "app/services/remediation_draft.py",
    "app/services/narrative.py",
    "app/routers/drafting.py",
    "app/main.py",
    "app/templates/partials/remediation_draft.html",
    "app/templates/components/conclusion_card.html",
    "app/templates/pages/narrative.html",
    "app/services/board_report.py",
    "app/templates/reports/board_report.html",
    "app/templates/pages/report_snapshots.html",
    "app/services/board_exports.py",  # revision 2026-10-01: schema v3 joins the supported versions
)
# Nothing in these may change in the P6-10 PR (committed diff or working tree).
P6_10_FORBIDDEN_PATHS = (
    "app/services/llm_client.py", "app/services/grounding", "app/services/claude_analyzer.py",
    "app/services/analysis_pipeline.py", "app/services/analysis_v2.py", "app/services/scoring.py",
    "app/services/conclusion_review.py", "app/services/findings.py", "app/services/approved_report.py",
    "app/services/report_content.py", "app/services/report_basis.py", "app/services/report_snapshots.py",
    "app/services/requirement_card.py", "app/services/review_queue.py", "app/services/workpaper.py",
    "app/services/standalone_workpaper.py", "app/utils", "app/routers/conclusions.py",
    "app/routers/snapshots.py", "app/routers/web.py", "app/routers/reports.py", "app/routers/findings.py",
    "app/models", "app/schemas", "app/frameworks", "app/dpdpa", "app/config.py", "alembic",
    "tests/fixtures", "tests/support", "scripts", "validation", "requirements.txt",
)
# Existing modules that reach the LLM seam today (P6-10 adds exactly two).
EXISTING_LLM_MODULES = {
    "app/services/claude_analyzer.py",
    "app/services/context_profiler.py",
    "app/services/desk_review.py",
    "app/services/document_processor.py",
    "app/services/followup_engine.py",
    "app/services/grounding/judge.py",
    "app/services/grounding/metadata_fallback.py",
    "app/services/grounding/missing.py",
    "app/services/grounding/pipeline.py",
    "app/services/llm_client.py",
    "app/services/screening.py",
}
P6_10_LLM_MODULES = {"app/services/remediation_draft.py", "app/services/narrative.py"}


def git(*args) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


def changed_app_paths() -> set[str]:
    changed = set(git("diff", "--name-only", "main...HEAD", "--", "app").split())
    changed |= set(git("diff", "--name-only", "HEAD", "--", "app").split())
    changed |= set(git("ls-files", "--others", "--exclude-standard", "app").split())
    return changed


def assert_p6_10_file_set() -> None:
    committed = git("diff", "--name-only", "main...HEAD", "--", *P6_10_FORBIDDEN_PATHS).split()
    working = git("diff", "--name-only", "HEAD", "--", *P6_10_FORBIDDEN_PATHS).split()
    assert committed == [] and working == [], committed + working
    outside = sorted(path for path in changed_app_paths() if path not in P6_10_APP_FILES)
    assert outside == [], outside
    llm_modules = {
        str(path.relative_to(REPO_ROOT))
        for path in (REPO_ROOT / "app").rglob("*.py")
        if "call_llm" in path.read_text(encoding="utf-8")
    }
    assert llm_modules <= EXISTING_LLM_MODULES | P6_10_LLM_MODULES, sorted(
        llm_modules - EXISTING_LLM_MODULES - P6_10_LLM_MODULES
    )


# ---------------------------------------------------------------------------
# Database, app and LLM fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "p6-10.sqlite3"
    command.upgrade(_alembic_config(path), "head")
    return path


@pytest.fixture()
def engine(db_path):
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine
    engine.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


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


@pytest.fixture(autouse=True)
def _no_network_llm(monkeypatch):
    from app.services import llm_client

    def _refuse(*_args, **_kwargs):
        raise AssertionError("P6-10 tests must never reach llm_client.call_llm; patch the service seam")

    monkeypatch.setattr(llm_client, "call_llm", _refuse)


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    return root


@pytest.fixture()
def gate(monkeypatch):
    from app.frameworks import questionnaire_builder
    from app.routers import analysis

    monkeypatch.setattr(analysis, "build_questionnaire", lambda **_kwargs: [{"id": "Q1"}])
    monkeypatch.setattr(analysis, "generate_initiatives", lambda *_args: [])
    monkeypatch.setattr(analysis, "generate_multi_framework_initiatives", lambda *_args: [])
    monkeypatch.setattr(questionnaire_builder, "build_multi_questionnaire", lambda *_a, **_k: [])
    return analysis


class FakeLLM:
    """Stands in for a service's `_call_llm` seam. `responder(request)` returns reply text
    (str), a dict to JSON-encode, or raises. Every request is recorded."""

    def __init__(self, responder):
        self.responder = responder
        self.requests: list[dict] = []

    def __call__(self, *, tier, stream=False, **request):
        from app.services import llm_client

        request = {"tier": tier, "stream": stream, **request}
        self.requests.append(request)
        usage = {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        }
        try:
            reply = self.responder(request)
        except Exception as exc:
            # What the real client records for a provider error, so per-call records stay honest.
            llm_client._record_call(
                tier=tier, model="fake-model", usage=None, latency_ms=0, finish_reason=None,
                status="error", error_type=type(exc).__name__,
            )
            raise
        if isinstance(reply, (dict, list)):
            reply = json.dumps(reply)
        llm_client._record_call(
            tier=tier, model="fake-model", usage=usage, latency_ms=0, finish_reason="stop",
            status="ok", error_type=None,
        )
        return {"text": reply, "usage": usage}


def user_prompt(request: dict) -> str:
    return "\n".join(
        message["content"] if isinstance(message["content"], str) else json.dumps(message["content"])
        for message in request["messages"]
    )


# ---------------------------------------------------------------------------
# Assessment fixture
# ---------------------------------------------------------------------------


def ids(framework_id: str, count: int) -> list[str]:
    return [control.id for control in FrameworkRegistry.get_all_controls(framework_id)][:count]


def _item(requirement_id, status="partially_compliant", risk="medium", action="Fix the gap"):
    return {
        "requirement_id": requirement_id,
        "compliance_status": status,
        "current_state": "AI current state",
        "gap_description": "Gap exists" if status != "compliant" else "",
        "risk_level": risk,
        "remediation_action": action if status != "compliant" else "",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "process",
        "evidence_quote": "",
        "needs_review": False,
    }


def _seed(db, *, frameworks, applicable, company=None):
    company = company or f"Acme Data {uuid.uuid4().hex[:8]} Private Limited"
    client = Client(name=company, industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name="FY26 review", status="active")
    db.add(engagement)
    db.flush()
    assessment = Assessment(
        company_name=company,
        industry="Technology",
        company_size="medium",
        selected_frameworks=json.dumps(frameworks),
        engagement_id=engagement.id,
        applicable_requirements=json.dumps(applicable),
    )
    db.add(assessment)
    db.flush()
    # P6-6 approval gate (D-P6-G): a period must be recorded before any approval.
    report_basis.update_report_basis(
        db, assessment, **PERIOD,
        prepared_by="Priya Sharma", reviewed_by="Ravi Menon", actor="consultant:Seed",
    )
    db.add(QuestionnaireResponse(assessment_id=assessment.id, question_id="Q1", answer="fully_implemented"))
    db.commit()
    return assessment


def _analyse(monkeypatch, gate, db, assessment, per_framework):
    """Run the real (v1 default) analysis route with both analyzer seams faked."""
    from app.routers import analysis

    def _single(**_kwargs):
        (items,) = per_framework.values()
        return {"parsed": {"executive_summary": "Synthetic", "assessments": copy.deepcopy(items)}, "raw": "{}"}

    def _multi(**_kwargs):
        return {
            "frameworks": {
                framework_id: {
                    "parsed": {"executive_summary": "Synthetic", "assessments": copy.deepcopy(items)},
                    "raw": "{}",
                }
                for framework_id, items in per_framework.items()
            },
            "synthesis": None,
            "total_usage": {},
        }

    monkeypatch.setattr(analysis, "run_gap_analysis", _single)
    monkeypatch.setattr(analysis, "run_multi_framework_analysis", _multi)
    gate.trigger_analysis(assessment.id, db)
    db.expire_all()
    return {
        (row.framework_id, row.requirement_id): row
        for row in db.query(Conclusion).filter_by(assessment_id=assessment.id).all()
    }


def latest_proposal(db, conclusion):
    return (
        db.query(ConclusionRevision)
        .filter_by(conclusion_id=conclusion.id, action="proposed")
        .order_by(ConclusionRevision.created_at.desc(), text("conclusion_revisions.rowid DESC"))
        .first()
    )


def decide_directly(db, conclusion, action="approved", **edits):
    """Consultant decision written directly (fixture data, not the gate under test)."""
    previous = conclusion.outcome
    for field, value in edits.items():
        setattr(conclusion, field, value)
    conclusion.version += 1
    db.add(
        ConclusionRevision(
            conclusion_id=conclusion.id,
            actor=f"consultant:{REVIEWER}",
            action=action,
            previous_outcome=previous,
            previous_rationale=conclusion.rationale,
            citations_json=None,
            created_at=datetime.now(timezone.utc),
        )
    )


def create_finding(http, assessment, conclusion, *, title, description, severity, priority, action):
    response = http.post(
        f"/api/assessments/{assessment.id}/findings",
        data={
            "conclusion_id": conclusion.id,
            "conclusion_version": conclusion.version,
            "title": title,
            "description": description,
            "severity": severity,
            "priority": priority,
            "action_title": action,
            "action_owner": "Anita Rao",
            "action_target_date": "2026-11-30",
            "reviewer_name": REVIEWER,
        },
    )
    assert response.status_code == 200, response.text


def analysed_assessment(db, gate, monkeypatch, *, frameworks=("dpdpa", "iso27001")):
    """Analysed, nothing approved yet. DPDPA: non-compliant, compliant, insufficient evidence,
    partially compliant. ISO: partially compliant, not applicable."""
    dp = ids("dpdpa", 4) if "dpdpa" in frameworks else []
    iso = ids("iso27001", 2) if "iso27001" in frameworks else []
    per_framework = {}
    if dp:
        per_framework["dpdpa"] = [
            _item(dp[0], "non_compliant", "high"),
            _item(dp[1], "compliant", "low"),
            _item(dp[2], "insufficient_evidence", "medium"),
            _item(dp[3], "partially_compliant", "medium"),
        ]
    if iso:
        per_framework["iso27001"] = [
            _item(iso[0], "partially_compliant", "critical"),
            _item(iso[1], "not_applicable", "low"),
        ]
    assessment = _seed(db, frameworks=list(frameworks), applicable=dp + iso)
    conclusions = _analyse(monkeypatch, gate, db, assessment, per_framework)
    for conclusion in conclusions.values():
        # Evidence support captured (an empty citation list), so approval is not blocked.
        latest_proposal(db, conclusion).citations_json = "[]"
    db.commit()
    return assessment, conclusions, dp, iso


def released_assessment(db, http, gate, monkeypatch, *, frameworks=("dpdpa", "iso27001"), findings=True):
    """Everything approved, one Finding per framework (unless findings=False), released."""
    assessment, conclusions, dp, iso = analysed_assessment(db, gate, monkeypatch, frameworks=frameworks)
    for conclusion in conclusions.values():
        decide_directly(db, conclusion)
    db.commit()
    if dp and findings:
        create_finding(
            http, assessment, conclusions[("dpdpa", dp[0])],
            title=DP_FINDING_TITLE, description=DP_FINDING_DESCRIPTION,
            severity="high", priority=1, action="Replace pre-ticked consent",
        )
    if iso and findings:
        create_finding(
            http, assessment, conclusions[("iso27001", iso[0])],
            title=ISO_FINDING_TITLE, description=ISO_FINDING_DESCRIPTION,
            severity="critical", priority=1, action="Run quarterly access reviews",
        )
    approved_report.record_release(db, assessment, actor=f"consultant:{REVIEWER}")
    db.commit()
    db.expire_all()
    return assessment, conclusions, dp, iso


def events(db, action: str, entity_id: str | None = None) -> list[AuditEvent]:
    query = db.query(AuditEvent).filter(AuditEvent.action == action)
    if entity_id is not None:
        query = query.filter(AuditEvent.entity_id == entity_id)
    return query.order_by(AuditEvent.created_at, text("audit_events.rowid")).all()


def metadata(event: AuditEvent) -> dict:
    return json.loads(event.metadata_json)
