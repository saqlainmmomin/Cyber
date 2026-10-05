"""Contract tests for P6-8 B1: board report v2 (WeasyPrint + Noto) and the standalone Workpaper.

Handoff: tasks/handoffs/2026-09-28-p6-8-board-report-v2.md. Plan:
docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md, Part D (D0 #3, D2,
D3, D4) and decision D-P6-H. Written before the implementation; on `main` they fail only
because the P6-8 code does not exist yet. No network, no LLM.

Tests that render a PDF need WeasyPrint and its system libraries (Pango). Locally they
skip with a clear reason when those are missing; in CI (CYBERASSESS_REQUIRE_WEASYPRINT=1)
a missing renderer is a failure, never a skip.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import io
import json
import os
import re
import socket
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

import pdfplumber
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
from app.models.evidence import Evidence, EvidenceVersion
from app.models.questionnaire import QuestionnaireResponse
from app.models.report_snapshot import ReportSnapshot
from app.services import approved_report, board_view, report_basis, report_snapshots

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRE_ENV = "CYBERASSESS_REQUIRE_WEASYPRINT"
WEASYPRINT_PIN = "weasyprint==70.0"
APT_LIBS = "libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0"
FONT_SHA256 = {
    "NotoSans-Regular.ttf": "f3961a9cde016d41a4879aecda1474d3a36d6bf54fa0e4643de029cc2248b0e8",
    "NotoSans-Bold.ttf": "87cb2d84472a7d66da659ee47b6cdb9552326e8c128245231f191b6ac72529d9",
    "NotoSansDevanagari-Regular.ttf": "9c7d935139ea6a1e6ad9dbac4f6d27ece1e04bca8123c8888d00a0f9df4724cd",
    "NotoSansDevanagari-Bold.ttf": "ff2f76a23aad41e0608c2d7dbc4bacd247ff3bec78f0ec2a8fb106b561636e58",
}
LICENSE_FILES = ("OFL-NotoSans.txt", "OFL-NotoSansDevanagari.txt")
DEVANAGARI_COMPANY = "भारत डेटा प्राइवेट लिमिटेड"
RUPEE_TEXT = "Budget ₹12 lakh for consent tooling"
PERIOD = {
    "period_start": date(2026, 4, 1),
    "period_end": date(2026, 6, 30),
    "evidence_cutoff": date(2026, 7, 15),
}
PERIOD_TEXT = "Assessment period: 01 Apr 2026 to 30 Jun 2026"
CUTOFF_TEXT = "Evidence cut-off: 15 Jul 2026"
FIXED_GENERATED_AT = datetime(2026, 9, 28, 10, 0, tzinfo=timezone.utc)
DOCUMENT_KEYS = {
    "schema_version", "kind", "snapshot", "firm_name", "company_name", "engagement_name",
    "assessment_id", "frameworks", "basis", "release", "summary", "top_risks", "roadmap",
    "not_assessed", "framework_sections", "sign_off", "appendices", "source",
    "soa", "prior_period",  # P6-9 (D-P6-9-E): schema v2
    "observations", "initiatives", "status_board", "severity_dashboard", "takeaways", "board_asks", "theme",
}
# P6-8 V3-B: the v3 deck's slide titles in page order (D-P6-8-V3-G); SECTION_HEADINGS below is the
# v2 portrait layout, kept because schema v1/v2 documents still render through the frozen B2 path.
V3_SLIDE_HEADINGS = (
    "Assessment overview", "Executive summary", "Key observations", "Remediation roadmap",
    "Limits and assumptions", "Sign-off", "Methodology", "Requirement register",
    "Evidence and statement of applicability",
)
SECTION_HEADINGS = (
    "Management summary",
    "Top risks",
    "Remediation roadmap",
    "What we could not assess",
    "Sign-off",
    "Appendix A: Methodology",
    "Appendix B: Requirement register",
    "Appendix C: Evidence register",
)
BASE_METADATA_KEYS = {
    "schema_version", "type", "format", "storage_path", "sha256", "size_bytes",
    "assessment_id", "engagement_id", "review_status", "source",
}
BOARD_METADATA_KEYS = BASE_METADATA_KEYS | {
    "document_sha256", "document_size_bytes", "document_schema_version", "renderer",
}
# Never in a report whose frameworks are all standards (ISO 27001 / NIST CSF / PCI-DSS).
NON_LEGAL_FORBIDDEN = (
    "dpdpa",
    "digital personal data protection",
    "data principal",
    "data fiduciary",
    "legal counsel",
    "legal advice",
    "privacy professional",
    "cmmi",
    "maturity model",
)
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _module(name: str):
    """Import a P6-8 module lazily so each test fails on its own before implementation."""
    return importlib.import_module(name)


def _html_pdf():
    return _module("app.utils.html_pdf")


def _board():
    return _module("app.services.board_report")


def _standalone():
    return _module("app.services.standalone_workpaper")


def _require_renderer():
    """The renderer module must exist (fail otherwise); WeasyPrint itself may be absent locally."""
    html_pdf = _html_pdf()
    available, reason = html_pdf.weasyprint_status()
    if not available:
        if os.environ.get(REQUIRE_ENV) == "1":
            pytest.fail(f"{REQUIRE_ENV}=1 but WeasyPrint is unavailable: {reason}")
        pytest.skip(
            "WeasyPrint or its system libraries are not installed "
            f"({reason}). macOS: `brew install pango` and `pip install {WEASYPRINT_PIN}`."
        )
    return html_pdf


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
    path = tmp_path / "p6-8.sqlite3"
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
def _no_llm(monkeypatch):
    from app.services import llm_client

    def _refuse(*_args, **_kwargs):
        raise AssertionError("P6-8 tests must never call an LLM")

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


def _ids(framework_id: str, count: int) -> list[str]:
    return [control.id for control in FrameworkRegistry.get_all_controls(framework_id)][:count]


def _seed(db, *, frameworks, applicable, company=DEVANAGARI_COMPANY, prepared_by="Priya Sharma"):
    client = Client(name=company, industry="Technology", size="medium")
    db.add(client)
    db.flush()
    engagement = Engagement(client_id=client.id, name="FY26 privacy and security review", status="active")
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
    report_basis.update_report_basis(
        db, assessment, **PERIOD,
        prepared_by=prepared_by, reviewed_by="Ravi Menon", actor="consultant:Seed",
    )
    db.add(QuestionnaireResponse(assessment_id=assessment.id, question_id="Q1", answer="fully_implemented"))
    db.commit()
    return assessment


def _item(requirement_id, status="partially_compliant", risk="medium"):
    return {
        "requirement_id": requirement_id,
        "compliance_status": status,
        "current_state": "AI current state",
        "gap_description": "Gap exists" if status != "compliant" else "",
        "risk_level": risk,
        "remediation_action": "Fix the gap" if status != "compliant" else "",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "process",
        "evidence_quote": "",
        "needs_review": False,
    }


def _analyse(monkeypatch, gate, db, assessment, per_framework):
    """Run the real analysis route with both analyzer seams faked (never a network call)."""
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


def _evidence(db, assessment, filename, digest_char, *, status="active"):
    evidence = Evidence(
        engagement_id=assessment.engagement_id,
        assessment_id=assessment.id,
        original_filename=filename,
        storage_path=f"evidence/{filename}",
        file_hash_sha256=digest_char * 64,
        file_size_bytes=10,
        mime_type="application/pdf",
        status=status,
        uploaded_by="consultant",
    )
    db.add(evidence)
    db.flush()
    version = EvidenceVersion(
        evidence_id=evidence.id,
        version_number=1,
        storage_path=f"evidence/{filename}.v1",
        file_hash_sha256=digest_char * 64,
        file_size_bytes=10,
        status="active" if status == "active" else "rejected",
        original_filename=filename,
        mime_type="application/pdf",
    )
    db.add(version)
    db.flush()
    return version


def _latest_proposal(db, conclusion):
    return (
        db.query(ConclusionRevision)
        .filter_by(conclusion_id=conclusion.id, action="proposed")
        .order_by(ConclusionRevision.created_at.desc(), text("conclusion_revisions.rowid DESC"))
        .first()
    )


def _decide(db, conclusion, action="approved", **edits):
    """Consultant decision written directly (fixture data, not the gate under test)."""
    previous = conclusion.outcome
    for field, value in edits.items():
        setattr(conclusion, field, value)
    conclusion.version += 1
    db.add(
        ConclusionRevision(
            conclusion_id=conclusion.id,
            actor="consultant:Priya",
            action=action,
            previous_outcome=previous,
            previous_rationale=conclusion.rationale,
            citations_json=None,
            created_at=datetime.now(timezone.utc),
        )
    )


def _finding(http, assessment, conclusion, *, title, description, severity, priority, action, owner, target):
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
            "action_owner": owner,
            "action_target_date": target,
            "reviewer_name": "Priya",
        },
    )
    assert response.status_code == 200, response.text


def _engagement_fixture(db, http, gate, monkeypatch, *, frameworks=("dpdpa", "iso27001"), company=DEVANAGARI_COMPANY, release=True):
    """A released DPDPA + ISO assessment with findings, actions, evidence and one edited conclusion."""
    dp = _ids("dpdpa", 3) if "dpdpa" in frameworks else []
    iso = _ids("iso27001", 2) if "iso27001" in frameworks else []
    per_framework = {}
    if dp:
        per_framework["dpdpa"] = [
            _item(dp[0], "non_compliant", "high"),
            _item(dp[1], "compliant", "low"),
            _item(dp[2], "insufficient_evidence", "medium"),
        ]
    if iso:
        per_framework["iso27001"] = [
            _item(iso[0], "partially_compliant", "critical"),
            _item(iso[1], "not_applicable", "low"),
        ]
    assessment = _seed(db, frameworks=list(frameworks), applicable=dp + iso, company=company)
    conclusions = _analyse(monkeypatch, gate, db, assessment, per_framework)

    policy = _evidence(db, assessment, "privacy-policy.pdf", "a")
    _evidence(db, assessment, "isms-manual.pdf", "b")
    _evidence(db, assessment, "rejected-scan.pdf", "c", status="rejected")
    for conclusion in conclusions.values():
        proposal = _latest_proposal(db, conclusion)
        cited = dp and conclusion.requirement_id == dp[0]
        proposal.citations_json = json.dumps(
            [{
                "evidence_version_id": policy.id,
                "location_type": "whole_item",
                "location_ref": "whole",
                "excerpt": "Consent is collected by a pre-ticked box.",
            }] if cited else []
        )
    db.commit()
    for key, conclusion in conclusions.items():
        if iso and key == ("iso27001", iso[0]):
            _decide(
                db, conclusion, "edited",
                outcome="partially_compliant", rationale="Consultant rationale",
                gaps_identified="Consultant gap", risk_level="critical",
                recommended_action="Consultant action",
            )
        else:
            _decide(db, conclusion)
    db.commit()

    if dp:
        _finding(
            http, assessment, conclusions[("dpdpa", dp[0])],
            title="Consent is not freely given", description=RUPEE_TEXT,
            severity="high", priority=1, action="Replace pre-ticked consent",
            owner="Anita Rao", target="2026-11-30",
        )
    if iso:
        _finding(
            http, assessment, conclusions[("iso27001", iso[0])],
            title="Access reviews are informal", description="Quarterly reviews are not evidenced.",
            severity="critical", priority=1, action="Run quarterly access reviews",
            owner="Vikram Iyer", target="2026-10-31",
        )
    if release:
        approved_report.record_release(db, assessment, actor="consultant:Priya")
        db.commit()
    db.expire_all()
    return assessment, conclusions, dp, iso


def _generate(http, assessment, snapshot_type="board_report"):
    return http.post(
        f"/api/assessments/{assessment.id}/snapshots",
        data={"type": snapshot_type, "reviewer_name": "Priya"},
    )


def _pdf(content: bytes):
    return pdfplumber.open(io.BytesIO(content))


def _pdf_text(content: bytes) -> str:
    with _pdf(content) as pdf:
        return " ".join(" ".join((page.extract_text() or "").split()) for page in pdf.pages)


def _document(db, assessment, *, snapshot_id="00000000-0000-4000-8000-000000000001", version_label="v1"):
    return _board().build_document(
        db, assessment,
        snapshot_id=snapshot_id,
        version_label=version_label,
        generated_at=FIXED_GENERATED_AT,
    )


def _visible_text(html: str) -> str:
    body = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
    return " ".join(re.sub(r"<[^>]+>", " ", body).split())


def _files_state(db, upload_root):
    return (
        db.query(ReportSnapshot).count(),
        sorted(str(path.relative_to(upload_root)) for path in upload_root.rglob("*") if path.is_file()),
    )


# ---------------------------------------------------------------------------
# 1-2. Rendering stack: fonts, offline renderer, lazy import
# ---------------------------------------------------------------------------


def test_scenario_1_fonts_are_vendored_pinned_and_licensed():
    """Scenario 1 (D-P6-8-C): four Noto TTFs under app/assets, pinned by hash, OFL alongside, glyphs present."""
    from fontTools.ttLib import TTFont

    html_pdf = _html_pdf()
    assert html_pdf.FONT_DIR == REPO_ROOT / "app" / "assets" / "fonts" / "noto"
    assert html_pdf.FONT_FILES == FONT_SHA256
    assert tuple(html_pdf.LICENSE_FILES) == LICENSE_FILES
    total = 0
    for name, digest in FONT_SHA256.items():
        content = (html_pdf.FONT_DIR / name).read_bytes()
        total += len(content)
        assert hashlib.sha256(content).hexdigest() == digest, name
        cmap = TTFont(io.BytesIO(content)).getBestCmap()
        assert 0x20B9 in cmap, f"{name} lacks the rupee sign"
        if "Devanagari" in name:
            assert all(code in cmap for code in range(0x0915, 0x0939 + 1)), name
    assert total < 1_500_000
    for name in LICENSE_FILES:
        assert "SIL Open Font License" in (html_pdf.FONT_DIR / name).read_text(encoding="utf-8")

    css = html_pdf.font_face_css()
    assert css.count("@font-face") == 4
    urls = re.findall(r"url\(['\"]?([^'\")]+)", css)
    assert sorted(urls) == sorted(FONT_SHA256)
    assert "Noto Sans Devanagari" in html_pdf.FONT_STACK and "Noto Sans" in html_pdf.FONT_STACK
    assert WEASYPRINT_PIN in (REPO_ROOT / "requirements.txt").read_text().splitlines()


def test_scenario_2_renderer_unavailable_is_a_clean_503_and_the_app_starts_without_pango(
    db, http, gate, monkeypatch, upload_root
):
    """Scenario 2 (D-P6-8-C): WeasyPrint is imported lazily; a missing renderer refuses cleanly and writes nothing."""
    html_pdf = _html_pdf()
    probe = subprocess.run(
        [sys.executable, "-c", "import sys, app.main, app.routers.snapshots, app.services.board_report; print('weasyprint' in sys.modules)"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    assert probe.stdout.strip() == "False"

    monkeypatch.setattr(html_pdf, "weasyprint_status", lambda: (False, "OSError: no pango"))
    with pytest.raises(html_pdf.RendererUnavailable) as raised:
        html_pdf.render_pdf("<p>x</p>")
    assert raised.value.message == html_pdf.RENDERER_UNAVAILABLE_MESSAGE

    assessment, *_ = _engagement_fixture(db, http, gate, monkeypatch, frameworks=("dpdpa",))
    before = _files_state(db, upload_root)
    response = _generate(http, assessment)
    assert response.status_code == 503
    assert response.json()["detail"] == html_pdf.RENDERER_UNAVAILABLE_MESSAGE
    assert response.headers["X-Toast-Type"] == "error"
    assert _files_state(db, upload_root) == before


def test_scenario_3_renderer_is_offline_deterministic_and_fails_loud():
    """Scenario 3 (D-P6-8-C): only the vendored fonts may load; anything else stops the render."""
    html_pdf = _require_renderer()
    for html in (
        '<img src="https://example.invalid/logo.png"><p>x</p>',
        '<link rel="stylesheet" href="file:///etc/hosts"><p>x</p>',
        '<style>@import url("http://example.invalid/a.css");</style><p>x</p>',
    ):
        with pytest.raises(html_pdf.OfflineRenderError):
            html_pdf.render_pdf(html)

    page = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>t</title>"
        "<meta name='dcterms.created' content='2026-09-28T10:00:00+00:00'>"
        f"<style>{html_pdf.font_face_css()} html {{ font-family: {html_pdf.FONT_STACK}; }}</style>"
        f"</head><body><p>{DEVANAGARI_COMPANY}</p><p>{RUPEE_TEXT}</p></body></html>"
    )
    original_connect = socket.socket.connect

    def _no_network(*_args, **_kwargs):
        raise AssertionError("render attempted a network connection")

    socket.socket.connect = _no_network
    try:
        first = html_pdf.render_pdf(page)
        second = html_pdf.render_pdf(page)
    finally:
        socket.socket.connect = original_connect
    assert first == second and first.startswith(b"%PDF")
    with _pdf(first) as pdf:
        fonts = {char["fontname"] for page_ in pdf.pages for char in page_.chars}
    assert fonts and all("Noto-Sans" in name for name in fonts), fonts
    assert RUPEE_TEXT in _pdf_text(first)


# ---------------------------------------------------------------------------
# 4-5. The report document (D-P6-8-D): approved data only, deterministic, JSON-safe
# ---------------------------------------------------------------------------


def test_scenario_4_document_is_built_from_approved_data_only(db, http, gate, monkeypatch):
    """Scenario 4 (D-P6-8-D/F): every section reads approved rows, findings, actions, basis and evidence."""
    board = _board()
    assessment, conclusions, dp, iso = _engagement_fixture(db, http, gate, monkeypatch)
    # An out-of-scope, never-reviewed conclusion must not reach any client-facing section.
    stray = _ids("dpdpa", 5)[4]
    db.add(Conclusion(
        assessment_id=assessment.id, framework_id="dpdpa", requirement_id=stray,
        outcome="non_compliant", rationale="Unreviewed stray", evidence_summary="",
        gaps_identified="Stray gap", risk_level="critical", recommended_action="Stray action",
        ai_proposed=True, version=1,
    ))
    db.commit()
    assert approved_report.release_state(db, assessment).released
    document = _document(db, assessment)
    assert stray not in json.dumps(document["appendices"]) + json.dumps(document["framework_sections"])
    assert "Unreviewed stray" not in json.dumps(document)

    assert set(document) == DOCUMENT_KEYS
    assert document["schema_version"] == board.DOCUMENT_SCHEMA_VERSION == 3  # P6-10 (D-P6-10-K)
    assert document["kind"] == board.SNAPSHOT_TYPE == "board_report"
    assert document["snapshot"] == {
        "id": "00000000-0000-4000-8000-000000000001",
        "version_label": "v1",
        "generated_at": "2026-09-28T10:00:00+00:00",
        "generated_on": "28 Sep 2026",
    }
    assert document["company_name"] == DEVANAGARI_COMPANY
    assert document["engagement_name"] == "FY26 privacy and security review"
    assert [f["framework_id"] for f in document["frameworks"]] == ["dpdpa", "iso27001"]
    assert [f["legal"] for f in document["frameworks"]] == [True, False]
    assert document["basis"]["period_label"] == "01 Apr 2026 to 30 Jun 2026"
    assert document["basis"]["cutoff_label"] == "15 Jul 2026"
    assert document["basis"]["prepared_by"] == "Priya Sharma"
    assert document["release"]["released_by"] == "Priya"

    approved = approved_report.build_approved_report(db, assessment)
    register = document["appendices"]["requirement_register"]
    assert [(r["framework_id"], r["requirement_id"], r["outcome"], r["risk_level"]) for r in register] == [
        (row.framework_id, row.requirement_id, row.compliance_status, row.risk_level)
        for row in approved.rows
    ]
    by_key = {(r["framework_id"], r["requirement_id"]): r for r in register}
    assert by_key[("dpdpa", dp[0])]["citation"] == "privacy-policy.pdf v1, whole"
    assert by_key[("dpdpa", dp[1])]["citation"] is None
    assert by_key[("dpdpa", dp[1])]["citation_note"] == board.NO_CITATION_NOTE
    assert by_key[("iso27001", iso[0])]["decision_label"] == "Edited and approved"
    assert by_key[("iso27001", iso[0])]["citation_note"] == board.EDITED_CITATION_NOTE

    summary = {f["framework_id"]: f for f in document["summary"]["frameworks"]}
    assert summary["dpdpa"]["status"] == "scored" and summary["dpdpa"]["narrative"] is None
    assert summary["dpdpa"]["coverage"]["insufficient_evidence"] == 1
    assert "1 requirement(s) insufficient evidence" in summary["dpdpa"]["headline"]
    assert "%" in summary["dpdpa"]["headline"]
    assert document["summary"]["totals"] == {
        "requirements": 5, "gaps": 2, "critical_high_gaps": 2,
        "insufficient_evidence": 1, "not_applicable": 1,
    }

    risks = document["top_risks"]
    assert [r["title"] for r in risks] == ["Access reviews are informal", "Consent is not freely given"]
    assert [r["rank"] for r in risks] == [1, 2]
    assert risks[1]["description"] == RUPEE_TEXT
    assert risks[1]["citations"][0]["filename"] == "privacy-policy.pdf"
    assert risks[1]["citations"][0]["sha256_prefix"] == "a" * 12
    assert (risks[1]["owner"], risks[1]["target_date"]) == ("Anita Rao", "2026-11-30")
    assert board.TOP_RISKS_LIMIT == 10

    actions = document["roadmap"]["actions"]
    assert [a["title"] for a in actions] == ["Run quarterly access reviews", "Replace pre-ticked consent"]
    assert actions[1]["closes"] == [{
        "framework_name": FrameworkRegistry.get("dpdpa").name,
        "requirement_id": dp[0],
        "finding_title": "Consent is not freely given",
    }]
    assert document["roadmap"]["unplanned_gap_count"] == 0

    assert [r["requirement_id"] for r in document["not_assessed"]["insufficient_evidence"]] == [dp[2]]
    assert document["not_assessed"]["rfi"] == {"version_label": None, "items": []}

    sections = {s["framework_id"]: s for s in document["framework_sections"]}
    assert [g["requirement_id"] for g in sections["dpdpa"]["gaps"]] == [dp[0]]
    assert [g["requirement_id"] for g in sections["iso27001"]["gaps"]] == [iso[0]]
    assert sections["dpdpa"]["domains"] and all({"title", "score", "rating"} <= set(d) for d in sections["dpdpa"]["domains"])

    evidence = document["appendices"]["evidence_register"]
    assert [(e["filename"], e["version_number"], e["sha256_prefix"], e["cited"]) for e in evidence] == [
        ("isms-manual.pdf", 1, "b" * 12, False),
        ("privacy-policy.pdf", 1, "a" * 12, True),
    ]
    assert document["source"] == report_snapshots.source_manifest(db, assessment)
    assert document["sign_off"]["prepared_by"] == "Priya Sharma"
    assert document["sign_off"]["reviewed_by"] == "Ravi Menon"


def test_scenario_5_document_bytes_are_canonical_and_deterministic(db, http, gate, monkeypatch):
    """Scenario 5 (D-P6-8-D): canonical JSON, UTF-8 (Devanagari kept), identical for identical inputs."""
    board = _board()
    assessment, *_ = _engagement_fixture(db, http, gate, monkeypatch)
    first = board.canonical_bytes(_document(db, assessment))
    second = board.canonical_bytes(_document(db, assessment))
    assert first == second
    assert DEVANAGARI_COMPANY.encode("utf-8") in first
    assert json.loads(first) == _document(db, assessment)
    assert first == json.dumps(
        json.loads(first), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def test_scenario_6_framework_conditional_copy(db, http, gate, monkeypatch):
    """Scenario 6 (D-P6-8-G): ISO-only has no legal or DPDPA copy; DPDPA+ISO has both regimes."""
    board = _board()
    iso_only, *_ = _engagement_fixture(db, http, gate, monkeypatch, frameworks=("iso27001",), company="Iso Only Ltd")
    html = board.render_html(_document(db, iso_only), embed_fonts=False)
    lowered = _visible_text(html).lower()
    for phrase in NON_LEGAL_FORBIDDEN:
        assert phrase not in lowered, phrase
    assert "certification" in lowered

    mixed, *_ = _engagement_fixture(db, http, gate, monkeypatch, company="Mixed Ltd")
    mixed_text = _visible_text(board.render_html(_document(db, mixed), embed_fonts=False))
    assert "legal counsel" in mixed_text.lower() and "certification" in mixed_text.lower()
    # The DPDPA readiness note is conditional on DPDPA and on the as-of date (FIXED_GENERATED_AT < May 2027).
    from app.dpdpa.framework import DPDPA_READINESS_NOTE

    assert DPDPA_READINESS_NOTE in mixed_text
    assert DPDPA_READINESS_NOTE not in _visible_text(html)


# ---------------------------------------------------------------------------
# 7-9. Board report PDF, snapshot semantics, never re-render
# ---------------------------------------------------------------------------


def test_scenario_7_board_pdf_renders_devanagari_rupee_and_all_sections(db, http, gate, monkeypatch):
    """Scenario 7 (D0 #3, D2): Noto-only fonts, exact rupee text, Devanagari title and glyphs, section order."""
    _require_renderer()
    assessment, conclusions, dp, iso = _engagement_fixture(db, http, gate, monkeypatch)
    response = _generate(http, assessment)
    assert response.status_code == 200, response.text
    snapshot = db.get(ReportSnapshot, response.json()["snapshot_id"])
    assert (snapshot.type, snapshot.format) == ("board_report", "pdf")
    content = report_snapshots.read_snapshot_bytes(db, snapshot)

    document = report_snapshots.read_board_report_document(db, snapshot)
    slides = board_view.view(document)["slides"]
    with _pdf(content) as pdf:
        # P6-8 V3-B (D-P6-8-V3-G): 16:9 landscape deck, one page per slide (was A4 portrait).
        width, height = pdf.pages[0].width, pdf.pages[0].height
        assert abs(width - 960.0) < 1 and abs(height - 540.0) < 1
        assert all(abs(page.width - 960.0) < 1 and abs(page.height - 540.0) < 1 for page in pdf.pages)
        fonts = {char["fontname"] for page in pdf.pages for char in page.chars}
        cover = pdf.pages[0].extract_text() or ""
        page_texts = [page.extract_text() or "" for page in pdf.pages]
        page_count = len(pdf.pages)
    assert page_count == len(slides)
    # Noto Sans for body text, the Display (Barlow Condensed) face for titles (V3-A fonts).
    assert any("Noto-Sans" in name for name in fonts) and any(name.endswith("Display-Bold-Condensed") for name in fonts), fonts
    assert any("Devanagari" in name for name in fonts)
    missing = Counter(ch for ch in DEVANAGARI_COMPANY if not ch.isspace()) - Counter(cover)
    assert not missing, missing

    full = _pdf_text(content)
    assert "�" not in full
    assert RUPEE_TEXT in full
    # The v3 deck shows the period and cut-off values on the cover and in every footer (D-P6-8-V3-G),
    # not the v2 prose "Assessment period: ..." lines.
    assert document["basis"]["period_label"] in cover and document["basis"]["cutoff_label"] in cover
    for text_of_page in page_texts[1:]:
        assert document["basis"]["period_label"] in text_of_page and document["basis"]["cutoff_label"] in text_of_page
        assert "Confidential" in text_of_page
    assert document["snapshot"]["version_label"] == "v1" and "v1" in cover
    positions = []
    for heading in V3_SLIDE_HEADINGS:
        positions.append(full.index(heading, positions[-1] + 1 if positions else 0))
    assert positions == sorted(positions)
    assert "Prepared by" in full and "Priya Sharma" in full and "Reviewed by" in full and "Ravi Menon" in full
    assert "privacy-policy.pdf" in full  # the cited-document sha prefix is document-level only now (scenario 5 pins it)
    assert "30 Nov 2026" in full  # the initiative target date is shown on the roadmap (v2 display format)


def _v3_pdf_facts(db, http, gate, monkeypatch):
    _require_renderer()
    assessment, *_ = _engagement_fixture(db, http, gate, monkeypatch)
    snapshot = db.get(ReportSnapshot, _generate(http, assessment).json()["snapshot_id"])
    with _pdf(report_snapshots.read_snapshot_bytes(db, snapshot)) as pdf:
        return (
            pdf.metadata.get("Title"),
            {char["fontname"] for page in pdf.pages for char in page.chars},
            [page.extract_text() or "" for page in pdf.pages],
        )


# The three tests below pin behaviour the v2 scenario 7 had and the V3-B implementation lost. They are
# kept red on purpose: they are V3-B app bugs, not stale tests (see the designer pass report).


def test_scenario_7b_v3_pdf_title_metadata_survives_the_devanagari_cover(db, http, gate, monkeypatch):
    """The PDF Title is "Board report: <company>" (the pdfunite cover swap in render_pdf drops the document info)."""
    title, _fonts, _pages = _v3_pdf_facts(db, http, gate, monkeypatch)
    assert title == f"Board report: {DEVANAGARI_COMPANY}"


def test_scenario_7c_v3_pdf_uses_only_embedded_noto_and_display_fonts(db, http, gate, monkeypatch):
    """D0 #3 (Noto-only, embedded): the V3-B PDF additionally references Helvetica, Arial and Verdana."""
    _title, fonts, _pages = _v3_pdf_facts(db, http, gate, monkeypatch)
    stray = {name for name in fonts if not any(known in name for known in ("Noto-Sans", "NotoSans", "Display-"))}
    assert not stray, stray


def test_scenario_7d_v3_pdf_has_no_slide_with_an_empty_table(db, http, gate, monkeypatch):
    """board_view pads Key observations to 3 and Requirement register to 6 pages, so a 2-finding report has empty slides."""
    _title, _fonts, pages = _v3_pdf_facts(db, http, gate, monkeypatch)
    for heading, row_marker in (("Key observations", "R-0"), ("Requirement register", "Compliant")):
        marked = [text_of_page for text_of_page in pages if re.match(rf"\d+\s+{heading}\s", text_of_page)]
        assert marked and all(row_marker in text_of_page for text_of_page in marked), heading


def test_scenario_8_snapshot_is_write_once_with_a_hashed_document_sidecar(db, http, gate, monkeypatch, upload_root):
    """Scenario 8 (D-P6-8-B/D/E): PDF + JSON sidecar, pinned metadata, release gate, integrity on issue."""
    _require_renderer()
    board = _board()
    unreleased, *_ = _engagement_fixture(db, http, gate, monkeypatch, frameworks=("dpdpa",), company="Draft Co", release=False)
    before = _files_state(db, upload_root)
    refused = _generate(http, unreleased)
    assert refused.status_code == 403
    assert refused.json()["detail"] == approved_report.NOT_RELEASED_MESSAGE
    assert _files_state(db, upload_root) == before

    assessment, *_ = _engagement_fixture(db, http, gate, monkeypatch)
    first = db.get(ReportSnapshot, _generate(http, assessment).json()["snapshot_id"])
    second = db.get(ReportSnapshot, _generate(http, assessment).json()["snapshot_id"])
    metadata = report_snapshots.generated_event(db, first.id)
    assert set(metadata) == BOARD_METADATA_KEYS
    assert metadata["document_schema_version"] == board.DOCUMENT_SCHEMA_VERSION
    assert metadata["renderer"].startswith("weasyprint ")
    assert metadata["source"] == report_snapshots.source_manifest(db, assessment)
    sidecar = upload_root / f"reports/assessments/{assessment.id}/{first.id}.json"
    assert first.storage_path == f"reports/assessments/{assessment.id}/{first.id}.pdf"
    assert hashlib.sha256(sidecar.read_bytes()).hexdigest() == metadata["document_sha256"]
    assert metadata["document_size_bytes"] == len(sidecar.read_bytes())

    first_document = report_snapshots.read_board_report_document(db, first)
    assert first_document["snapshot"]["id"] == first.id
    assert first_document["snapshot"]["version_label"] == "v1"
    assert report_snapshots.read_board_report_document(db, second)["snapshot"]["version_label"] == "v2"
    assert board.canonical_bytes(first_document) == sidecar.read_bytes()

    with pytest.raises(report_snapshots.InvalidSnapshot):
        report_snapshots.create_snapshot(db, assessment=assessment, snapshot_type="board_report", content=b"%PDF", actor="consultant:Priya")
    db.rollback()
    with pytest.raises(report_snapshots.SnapshotNotFound):
        report_snapshots.read_board_report_document(
            db, db.get(ReportSnapshot, _generate(http, assessment, "workpaper").json()["snapshot_id"])
        )

    newest = db.get(ReportSnapshot, _generate(http, assessment).json()["snapshot_id"])
    newest_sidecar = upload_root / f"reports/assessments/{assessment.id}/{newest.id}.json"
    original = newest_sidecar.read_bytes()
    newest_sidecar.write_bytes(original.replace(b'"v3"', b'"v9"'))
    tampered = http.post(f"/api/assessments/{assessment.id}/snapshots/{newest.id}/issue", data={"reviewer_name": "Priya"})
    assert tampered.status_code == 500
    assert tampered.json()["detail"] == report_snapshots.INTEGRITY_MESSAGE
    db.expire_all()
    assert db.get(ReportSnapshot, newest.id).is_issued is False
    newest_sidecar.write_bytes(original)
    issued = http.post(f"/api/assessments/{assessment.id}/snapshots/{newest.id}/issue", data={"reviewer_name": "Priya"})
    assert issued.status_code == 200, issued.text

    page = http.get(f"/assessments/{assessment.id}/snapshots")
    assert page.status_code == 200
    assert 'data-snapshot-type="board_report"' in page.text
    assert report_snapshots.TYPE_LABELS["board_report"] == "Board report v2 (PDF)"
    assert f"/api/assessments/{assessment.id}/board-report/preview" in page.text


def test_scenario_9_stored_versions_are_never_re_rendered(db, http, gate, monkeypatch, upload_root):
    """Scenario 9 (D-P6-8-E): old gap-report, Workpaper and board-report bytes survive data changes and are served as stored."""
    _require_renderer()
    from app.routers import reports

    board = _board()
    standalone = _standalone()
    assessment, conclusions, dp, iso = _engagement_fixture(db, http, gate, monkeypatch)
    ids = {kind: _generate(http, assessment, kind).json()["snapshot_id"] for kind in ("gap_report", "workpaper", "board_report")}
    hashes = {
        kind: hashlib.sha256(report_snapshots.read_snapshot_bytes(db, db.get(ReportSnapshot, sid))).hexdigest()
        for kind, sid in ids.items()
    }
    old_document = report_snapshots.read_board_report_document(db, db.get(ReportSnapshot, ids["board_report"]))

    # Change the approved data the legal way: reopen, edit, re-approve, re-release.
    target = db.get(Conclusion, conclusions[("dpdpa", dp[1])].id)
    _decide(db, target, "reopened")
    db.commit()
    _decide(db, target, "edited", outcome="non_compliant", rationale="Now failing", gaps_identified="Gap", recommended_action="Fix", risk_level="high")
    db.commit()
    approved_report.record_release(db, assessment, actor="consultant:Priya")
    db.commit()
    new_id = _generate(http, assessment).json()["snapshot_id"]
    new_document = report_snapshots.read_board_report_document(db, db.get(ReportSnapshot, new_id))
    assert new_document["summary"]["totals"]["gaps"] == old_document["summary"]["totals"]["gaps"] + 1

    def _explode(*_args, **_kwargs):
        raise AssertionError("a stored version was re-rendered")

    monkeypatch.setattr(reports, "generate_pdf", _explode)
    monkeypatch.setattr(standalone, "render", _explode)
    monkeypatch.setattr(board, "render_pdf", _explode)
    monkeypatch.setattr(board, "render_html", _explode)
    monkeypatch.setattr(board, "build_document", _explode)
    db.expire_all()
    for kind, sid in ids.items():
        served = http.get(f"/api/assessments/{assessment.id}/snapshots/{sid}/file")
        assert served.status_code == 200, (kind, served.text)
        assert hashlib.sha256(served.content).hexdigest() == hashes[kind]
        assert served.headers["X-Snapshot-Sha256"] == hashes[kind]
    assert report_snapshots.read_board_report_document(db, db.get(ReportSnapshot, ids["board_report"])) == old_document


# ---------------------------------------------------------------------------
# 10. Standalone Workpaper
# ---------------------------------------------------------------------------


def test_scenario_10_workpaper_snapshot_is_standalone_and_offline(db, http, gate, monkeypatch):
    """Scenario 10 (D-P6-8-H): inline CSS only, no scripts or links out, same data as the live page."""
    standalone = _standalone()
    assessment, conclusions, dp, iso = _engagement_fixture(db, http, gate, monkeypatch)
    hostile = db.get(Conclusion, conclusions[("dpdpa", dp[1])].id)
    hostile.rationale = "<script>alert('x')</script> & more"
    db.commit()

    response = _generate(http, assessment, "workpaper")
    assert response.status_code == 200, response.text
    snapshot = db.get(ReportSnapshot, response.json()["snapshot_id"])
    html = report_snapshots.read_snapshot_bytes(db, snapshot).decode("utf-8")
    assert html == standalone.render(db, assessment)

    assert html.lstrip().lower().startswith("<!doctype html>")
    assert '<meta charset="utf-8">' in html.lower()
    assert html.count("<style>") == 1
    lowered = html.lower()
    for token in ("<script", "<link", "src=", "@import", "url(", "/static", "http://", "https://", "hx-", "<form", "<iframe"):
        assert token not in lowered, token
    assert all(href.startswith("#") for href in re.findall(r'href="([^"]*)"', html))
    assert "&lt;script&gt;alert(" in html
    assert DEVANAGARI_COMPANY in html
    assert f"{PERIOD_TEXT} · {CUTOFF_TEXT}" in html and "data-report-basis" in html

    live = http.get(f"/assessments/{assessment.id}/workpaper").text

    def _attrs(page, name):
        return sorted(re.findall(rf'{name}="([^"]*)"', page))

    for attribute in ("data-count", "data-decision-state", "data-workpaper-section", "data-in-scope", "data-revision-action", "data-run-status"):
        assert _attrs(html, attribute) == _attrs(live, attribute), attribute
    entry_ids = lambda page: sorted(re.findall(r'<article data-workpaper-entry id="([^"]+)"', page))  # noqa: E731
    assert entry_ids(html) == entry_ids(live) and entry_ids(html)
    live_counts = dict(re.findall(r'data-count="([^"]+)"[^>]*>\s*([0-9]+)', live))
    assert dict(re.findall(r'data-count="([^"]+)"[^>]*>\s*([0-9]+)', html)) == live_counts

    html_pdf = _html_pdf()
    if html_pdf.weasyprint_status()[0]:
        assert html_pdf.render_pdf(html).startswith(b"%PDF")  # the offline fetcher refuses any resource


# ---------------------------------------------------------------------------
# 11. Live preview shares the template; no user data inside CSS
# ---------------------------------------------------------------------------


def test_scenario_11_preview_shares_the_template_and_keeps_user_text_out_of_css(db, http, gate, monkeypatch, upload_root):
    """Scenario 11 (D-P6-8-I): live HTML preview, release-gated, writes nothing, same sections as the PDF."""
    board = _board()
    company = 'Acme "Quote" } body { display:none } Ltd'
    unreleased, *_ = _engagement_fixture(db, http, gate, monkeypatch, frameworks=("dpdpa",), company="Unreleased Co", release=False)
    assert http.get(f"/api/assessments/{unreleased.id}/board-report/preview").status_code == 403

    assessment, *_ = _engagement_fixture(db, http, gate, monkeypatch, company=company)
    before = _files_state(db, upload_root)
    events_before = db.query(AuditEvent).count()
    preview = http.get(f"/api/assessments/{assessment.id}/board-report/preview")
    assert preview.status_code == 200
    assert preview.headers["content-type"].startswith("text/html")
    assert _files_state(db, upload_root) == before
    assert db.query(AuditEvent).count() == events_before
    body = preview.text
    assert "data-preview" in body and board.PREVIEW_VERSION_LABEL in body
    assert "@font-face" not in body
    text_value = _visible_text(body)
    for heading in V3_SLIDE_HEADINGS:  # P6-8 V3-B: the preview shares the v3 deck template
        assert heading in text_value, heading

    styles = " ".join(re.findall(r"<style>(.*?)</style>", body, flags=re.S))
    assert "Acme" not in styles and "Quote" not in styles
    embedded = board.render_html(_document(db, assessment), embed_fonts=True)
    embedded_styles = " ".join(re.findall(r"<style>(.*?)</style>", embedded, flags=re.S))
    assert embedded_styles.count("@font-face") == 6  # P6-8 V3-B: Noto Sans (4) + the two Display faces
    assert "Acme" not in embedded_styles
    assert "Acme &#34;Quote&#34;" in embedded or "Acme &quot;Quote&quot;" in embedded


# ---------------------------------------------------------------------------
# 12. CI, Docker and dependency plumbing
# ---------------------------------------------------------------------------


def test_scenario_12_ci_and_docker_install_the_renderer():
    """Scenario 12 (D-P6-8-C): CI installs Pango and forbids skipping; the image has the libraries."""
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text()
    assert f"sudo apt-get install -y --no-install-recommends {APT_LIBS}" in workflow
    assert f'{REQUIRE_ENV}: "1"' in workflow
    assert "python -c \"from app.utils.html_pdf import render_pdf; render_pdf('<p>ok</p>')\"" in workflow
    assert workflow.index(APT_LIBS) < workflow.index("python -m pytest")
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    assert f"apt-get install -y --no-install-recommends {APT_LIBS}" in dockerfile
    assert dockerfile.index(APT_LIBS) < dockerfile.index("pip install")
    assert "rm -rf /var/lib/apt/lists/*" in dockerfile


# ---------------------------------------------------------------------------
# 13. Golden (D-P6-8-J): normalised document JSON, platform independent
# ---------------------------------------------------------------------------

GOLDEN = REPO_ROOT / "tests" / "golden" / "p6_8_board_document.json"
RECORD_ENV = "P6_8_RECORD_GOLDEN"


VOLATILE_DATE_KEYS = {"decided_on", "added_on", "released_on"}  # "today" in the fixture


def _normalise(document: dict) -> dict:
    """Replace ids (first-appearance order) and run-day dates so the golden only moves when content moves."""
    def _dates(value):
        if isinstance(value, dict):
            return {k: ("<run-date>" if k in VOLATILE_DATE_KEYS and v else _dates(v)) for k, v in value.items()}
        if isinstance(value, list):
            return [_dates(item) for item in value]
        return value

    raw = json.dumps(_dates(document), sort_keys=True, ensure_ascii=False)
    seen: dict[str, str] = {}
    raw = UUID_RE.sub(lambda m: seen.setdefault(m.group(0), f"<id:{len(seen) + 1}>"), raw)
    return json.loads(raw)


def test_scenario_13_document_golden(db, http, gate, monkeypatch):
    """Scenario 13 (D-P6-8-J): the document for the fixed fixture matches the recorded golden."""
    monkeypatch.setattr(settings, "firm_name", "Golden Advisory")
    assessment, *_ = _engagement_fixture(db, http, gate, monkeypatch)
    got = _normalise(_document(db, assessment))
    if os.environ.get(RECORD_ENV) == "1":
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(got, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        pytest.skip(f"golden recorded at {GOLDEN.relative_to(REPO_ROOT)}; review the diff before committing")
    assert GOLDEN.exists(), f"record the golden: {RECORD_ENV}=1 pytest {Path(__file__).name} -k golden"
    assert got == json.loads(GOLDEN.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 14. No LLM, and the P6-8 B1 file set
# ---------------------------------------------------------------------------

P6_8_B1_APP_ALLOWLIST = (
    "app/utils/html_pdf.py",
    "app/services/board_report.py",
    "app/services/standalone_workpaper.py",
    "app/services/report_snapshots.py",
    "app/routers/snapshots.py",
    "app/templates/reports/",
    "app/templates/pages/report_snapshots.html",
    "app/assets/fonts/noto/",
    # P6-10 (tasks/handoffs/2026-09-28-p6-10-remediation-and-narrative.md) lands after
    # P6-8 B1; tests/test_p6_10a_remediation_draft.py and tests/test_p6_10b_narrative.py
    # guard these files.
    "app/services/remediation_draft.py", "app/services/narrative.py", "app/routers/drafting.py",
    "app/main.py", "app/templates/partials/remediation_draft.html",
    "app/templates/components/conclusion_card.html", "app/templates/pages/narrative.html",
    # P6-8 B2 (DOCX/XLSX exporter); tests/test_p6_8_b2_docx_xlsx.py guards it.
    "app/services/board_exports.py",
    # P6-9 (tasks/handoffs/2026-09-28-p6-9-soa-roadmap-comparison.md) lands after B1;
    # tests/test_p6_9_file_set.py guards its file set.
    "app/services/soa.py", "app/services/remediation_groups.py", "app/services/prior_period.py",
    "app/routers/soa.py", "app/templates/pages/soa.html", "app/main.py",
    # P6-5 (tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md): judge claim quarantine persistence.
    "app/services/grounding/injection.py",
    "app/services/grounding/judge.py",
    "app/services/analysis_v2.py",
)
from tests.p6_8_v3a_paths import V3A_APP_PATHS, V3A_EXCLUDES  # P6-8 V3-A per-PR allowance
from tests.p6_8_v3b_paths import V3B_EXCLUDES, is_v3b_path  # P6-8 V3-B per-PR allowance
from tests.yozora_backend_paths import YOZORA_BACKEND_APP_PATHS, YOZORA_BACKEND_EXCLUDES  # Yozora backend per-PR allowance
from tests.yozora_paths import YOZORA_EXCLUDES, YOZORA_S1_PATHS, YOZORA_S2_PATHS, YOZORA_S3_PATHS, YOZORA_S4_PATHS, YOZORA_S5_PATHS, YOZORA_S6_PATHS  # Yozora S1/S2/S3/S4/S5 per-PR allowance

P6_8_FORBIDDEN_PATHS = (
    # Frozen fpdf2 reports and the canonical golden (D-P6-8-B).
    "app/utils/pdf_export.py", "app/utils/rfi_export.py", "app/routers/reports.py",
    "app/routers/integrated_reports.py", "tests/fixtures", "tests/support",
    # Parallel P6-7 (requirement card, review queue) owns these.
    "app/routers/review.py", "app/services/conclusion_review.py",
    "app/templates/components", "app/templates/partials", "app/templates/base.html",
    "app/routers/web.py",
    # Analyzer, LLM, scoring, packs, schema, scripts, answer keys.
    "app/services/claude_analyzer.py", "app/services/llm_client.py", "app/services/grounding",
    "app/services/desk_review.py", "app/services/desk_review_v2.py", "app/services/analysis_pipeline.py",
    "app/services/scoring.py", "app/services/approved_report.py", "app/services/report_content.py",
    "app/services/report_basis.py", "app/services/workpaper.py", "app/services/findings.py",
    "app/frameworks", "app/dpdpa", "app/models", "app/schemas", "alembic", "app/config.py",
    "scripts", "validation",
    # Stage C 2026-09-28 harness fix (magic-link evidence lookup) lands after P6-8 B1.
    ":(exclude)scripts/validation/run_company.py",
    # P6-10: the recommended-action draft control in the conclusion card and its partial.
    ":(exclude)app/templates/components/conclusion_card.html",
    ":(exclude)app/templates/partials/remediation_draft.html",
    # Stage C v1 baseline (2026-09-29): c4's CSF 2.0 questionnaire answers.
    ":(exclude)validation/companies/c4-healthsaas/client_visible/questionnaire_answers.json",
    # P6-5 (tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md) lands after P6-8 B1: judge claim
    # quarantine, injected-document live check and the A/B comparison; tests/test_p6_5_*.py guard them.
    ":(exclude)app/services/grounding/injection.py",
    ":(exclude)app/services/grounding/judge.py",
    ":(exclude)app/frameworks/criteria/__init__.py",
    ":(exclude)app/frameworks/criteria/iso27001.py",
    ":(exclude)app/frameworks/criteria/nist_csf.py",
    ":(exclude)app/frameworks/definitions/iso27001.py",
    ":(exclude)app/frameworks/definitions/nist_csf.py",
    ":(exclude)scripts/convert_criteria.py",
    ":(exclude)scripts/injection_pack_live.py",
    ":(exclude)scripts/validation/ab_compare.py",
    ":(exclude)scripts/validation/score.py",
    # P6-7b (tasks/handoffs/2026-09-28-p6-7b-add-to-rfi.md) lands after P6-8 B1: the
    # card's add-to-RFI control; tests/test_p6_7b_add_to_rfi.py guards it.
    ":(exclude)app/templates/components/requirement_card_body.html",
    # LLM request deadline (claude/llm-request-deadline): wall-clock cap per provider call.
    ":(exclude)app/config.py",
    ":(exclude)app/services/llm_client.py",
    # P6-8 V3-A (tasks/handoffs/2026-10-01-board-report-v3-deck.md): board-inputs migration and models.
    *V3A_EXCLUDES,
    # P6-8 V3-B (tasks/handoffs/2026-10-01-board-report-v3-deck.md): v3 document, deck and exports.
    *V3B_EXCLUDES,
    # Yozora backend features (tasks/handoffs/2026-10-03-yozora-backend-features.md).
    *YOZORA_BACKEND_EXCLUDES,
    *YOZORA_EXCLUDES,  # Yozora S1
)
# P6-7b lands after P6-8 B1 and legitimately touches these (add-to-RFI from the card).
P6_7B_APP_FILES = (
    "app/services/rfi_evidence_requests.py",
    "app/services/rfi_requests.py",
    "app/services/requirement_card.py",
    "app/routers/requirement_review.py",
    "app/templates/components/requirement_card_body.html",
    "app/templates/pages/rfi.html",
)


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout


def test_scenario_14_no_llm_and_b1_file_set():
    """Scenario 14 (D-P6-8-K): no LLM imports; P6-8 B1 touches only its own files (committed and working tree)."""
    for relative in ("app/services/board_report.py", "app/utils/html_pdf.py", "app/services/standalone_workpaper.py"):
        path = REPO_ROOT / relative
        if path.exists():
            source = path.read_text(encoding="utf-8")
            for token in ("llm_client", "claude_analyzer", "services.grounding", "call_llm", "openai"):
                assert token not in source, (relative, token)

    committed = _git("diff", "--name-only", "main...HEAD", "--", *P6_8_FORBIDDEN_PATHS).split()
    working = _git("diff", "--name-only", "HEAD", "--", *P6_8_FORBIDDEN_PATHS).split()
    assert committed == [] and working == [], committed + working

    changed_app = set(_git("diff", "--name-only", "main...HEAD", "--", "app").split())
    changed_app |= set(_git("diff", "--name-only", "HEAD", "--", "app").split())
    changed_app |= set(_git("ls-files", "--others", "--exclude-standard", "app").split())
    outside = sorted(
        path for path in changed_app
        if not path.startswith(P6_8_B1_APP_ALLOWLIST) and path not in P6_7B_APP_FILES
        and not path.startswith("app/frameworks/")  # P6-2e: signed ISO / NIST criteria
        and path not in V3A_APP_PATHS  # P6-8 V3-A
        and not is_v3b_path(path)  # P6-8 V3-B
        and path not in YOZORA_BACKEND_APP_PATHS  # Yozora backend
        and path not in YOZORA_S1_PATHS  # Yozora S1
        and path not in YOZORA_S2_PATHS  # Yozora S2
        and path not in YOZORA_S3_PATHS and path not in YOZORA_S4_PATHS and path not in YOZORA_S5_PATHS and path not in YOZORA_S6_PATHS  # Yozora S4/S5
    )
    outside = [path for path in outside if path not in ("app/config.py", "app/services/llm_client.py")]  # LLM request deadline
    assert outside == [], outside
