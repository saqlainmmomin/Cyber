"""Regression guards for the per-framework scoring invariant."""

import ast
import io
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base, get_db
from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
from app.frameworks.definitions.gdpr import GDPR_DEFINITION
from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.report import GapItem, GapReport
from app.routers import analysis as analysis_router
from app.routers import reports as reports_router
from app.routers.web import router as web_router
from app.routers.web import templates
from app.schemas.report import ChapterScore
from app.services.scoring import compute_framework_scores, namespaced_domain_scores
from app.services import approved_report
from app.config import settings


@pytest.fixture
def db_session(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine)
    session = testing_session()
    monkeypatch.setattr("app.services.scoring.SessionLocal", testing_session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture(autouse=True)
def registered_frameworks():
    original = FrameworkRegistry._frameworks.copy()
    FrameworkRegistry.reset()
    for framework in (
        DPDPA_DEFINITION,
        ISO27001_DEFINITION,
        NIST_CSF_DEFINITION,
        GDPR_DEFINITION,
        HIPAA_DEFINITION,
        PCI_DSS_DEFINITION,
    ):
        FrameworkRegistry.register(framework)
    yield
    FrameworkRegistry._frameworks = original


@pytest.fixture
def client(db_session, monkeypatch):
    previous_settings = templates.env.globals.get("settings")
    templates.env.globals["settings"] = settings
    app = FastAPI()
    app.include_router(web_router)
    app.include_router(reports_router.router)
    app.include_router(analysis_router.router)

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    if previous_settings is None:
        templates.env.globals.pop("settings", None)
    else:
        templates.env.globals["settings"] = previous_settings


def _assessment(db_session, framework_ids, *, company_name="Acme"):
    assessment = Assessment(
        company_name=company_name,
        industry="it_services",
        company_size="sme",
        selected_frameworks=json.dumps(framework_ids),
        status="completed",
        review_status="approved",
    )
    db_session.add(assessment)
    db_session.commit()
    db_session.refresh(assessment)
    return assessment


def _scores(framework_id, status="compliant"):
    framework = FrameworkRegistry.get(framework_id)
    return compute_framework_scores(
        [
            {"requirement_id": control.id, "compliance_status": status}
            for control in framework.all_controls()
        ],
        framework_id,
    )


def _report(db_session, assessment, framework_scores, *, overall_score=0.0):
    report = GapReport(
        assessment_id=assessment.id,
        overall_score=overall_score,
        chapter_scores=json.dumps(namespaced_domain_scores(framework_scores)),
        framework_scores=json.dumps(framework_scores),
        executive_summary="Synthetic summary",
        raw_ai_response="{}",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    for framework_id, score in framework_scores.items():
        outcome = "compliant" if score.get("overall_score", 0) >= 99 else "partially_compliant"
        for control in FrameworkRegistry.get(framework_id).all_controls():
            conclusion = Conclusion(
                assessment_id=assessment.id,
                requirement_id=control.id,
                framework_id=framework_id,
                outcome=outcome,
                rationale="Synthetic rationale",
                evidence_summary="Synthetic evidence",
                gaps_identified="Synthetic gap",
                risk_level="medium",
                recommended_action="Synthetic action",
                ai_proposed=False,
                version=2,
            )
            db_session.add(conclusion)
            db_session.flush()
            db_session.add(
                ConclusionRevision(
                    conclusion_id=conclusion.id,
                    actor="consultant:Priya",
                    action="approved",
                    previous_outcome=outcome,
                    previous_rationale="Synthetic rationale",
                    citations_json="[]",
                    created_at=datetime.now(timezone.utc),
                )
            )
    db_session.commit()
    approved_report.record_release(db_session, assessment, actor="consultant:Priya")
    db_session.commit()
    return report


def _run_multi_analysis(db_session, assessment, monkeypatch):
    from app.routers import analysis

    framework_assessments = {
        framework_id: [{
            "requirement_id": FrameworkRegistry.get(framework_id).all_controls()[0].id,
            "compliance_status": "compliant",
            "current_state": "Implemented",
            "gap_description": "No gap",
            "risk_level": "low",
            "remediation_action": "Maintain",
        }]
        for framework_id in assessment.frameworks
    }
    monkeypatch.setattr(
        analysis,
        "run_multi_framework_analysis",
        lambda **_kwargs: {
            "frameworks": {
                framework_id: {
                    "parsed": {"assessments": assessments},
                    "raw": "{}",
                }
                for framework_id, assessments in framework_assessments.items()
            },
            "synthesis": None,
        },
    )
    monkeypatch.setattr(analysis, "generate_multi_framework_initiatives", lambda *_args: [])
    return analysis._run_multi_framework_analysis(
        assessment=assessment,
        assessment_id=assessment.id,
        responses=[],
        documents=[],
        context_profile=None,
        desk_review_data=None,
        applicable_requirements=None,
        selected_frameworks=assessment.frameworks,
        has_documents=False,
        db=db_session,
    )


def test_analysis_persists_per_framework_scores_and_namespaced_chapters(
    db_session, monkeypatch
):
    multi = _assessment(db_session, ["dpdpa", "iso27001"])
    _run_multi_analysis(db_session, multi, monkeypatch)

    report = db_session.query(GapReport).filter_by(assessment_id=multi.id).one()
    stored_frameworks = json.loads(report.framework_scores)
    stored_chapters = json.loads(report.chapter_scores)

    assert report.overall_score == 0.0
    assert set(stored_frameworks) == {"dpdpa", "iso27001"}
    assert all(scores["overall_score"] > 0 for scores in stored_frameworks.values())
    expected_chapter_keys = {
        f"{framework_id}:{domain_key}"
        for framework_id in multi.frameworks
        for domain_key in stored_frameworks[framework_id]["domain_scores"]
    }
    assert set(stored_chapters) == expected_chapter_keys
    for key, value in stored_chapters.items():
        assert re.fullmatch(r"[a-z0-9_]+:.+", key)
        assert set(value) == {"score", "rating", "title", "applicable"}
        ChapterScore(**value)


def test_single_framework_analysis_populates_framework_scores(db_session, monkeypatch):
    from app.routers import analysis
    from app.models.questionnaire import QuestionnaireResponse

    assessment = _assessment(db_session, ["dpdpa"])
    assessment.status = "questionnaire_done"
    db_session.add(
        QuestionnaireResponse(
            assessment_id=assessment.id,
            question_id="CH2.NOTICE.1",
            answer="fully_implemented",
        )
    )
    db_session.commit()
    monkeypatch.setattr(analysis, "build_questionnaire", lambda **_kwargs: [{"id": "CH2.NOTICE.1"}])
    monkeypatch.setattr(
        analysis,
        "run_gap_analysis",
        lambda **_kwargs: {
            "parsed": {
                "assessments": [{
                    "requirement_id": "CH2.NOTICE.1",
                    "compliance_status": "compliant",
                }],
                "executive_summary": "Synthetic summary",
            },
            "raw": "{}",
        },
    )
    monkeypatch.setattr(analysis, "generate_initiatives", lambda *_args: [])

    analysis.trigger_analysis(assessment.id, db_session)
    report = db_session.query(GapReport).filter_by(assessment_id=assessment.id).one()
    stored_frameworks = json.loads(report.framework_scores)
    expected = compute_framework_scores(
        [{"requirement_id": "CH2.NOTICE.1", "compliance_status": "compliant"}],
        "dpdpa",
    )

    assert report.overall_score == 0.0
    assert set(stored_frameworks) == {"dpdpa"}
    assert stored_frameworks["dpdpa"]["overall_score"] == expected["overall_score"]
    assert all(set(value) == {"score", "rating", "title", "applicable"}
               for value in json.loads(report.chapter_scores).values())


def test_blended_function_and_topic_maturity_are_gone():
    repo = Path(__file__).resolve().parents[1]
    for token in ("compute_unified_maturity", "maturity_by_topic"):
        result = subprocess.run(
            ["grep", "-rn", token, "app", "scripts"],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 1, result.stdout
    with pytest.raises(ImportError):
        from app.services.scoring import compute_unified_maturity  # noqa: F401


def test_no_template_reads_retired_score():
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["grep", "-rn", "overall_score", "app/templates"],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1, result.stdout

    token = re.compile(r"(?<![A-Za-z0-9_])overall_score(?![A-Za-z0-9_])")
    allowed_files = {
        "app/models/report.py",
        "app/services/scoring.py",
        "app/schemas/scoring.py",
        "app/legacy_migrations.py",
        "app/legacy_migrations_schema.py",
        "app/routers/analysis.py",
    }
    retired_score_hits = {}
    for path in (repo / "app").rglob("*.py"):
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))
        matching_lines = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "overall_score":
                matching_lines.add(node.lineno)
            elif isinstance(node, ast.keyword) and node.arg == "overall_score":
                matching_lines.add(node.lineno)
        if matching_lines:
            lines = source.splitlines()
            retired_score_hits[path.relative_to(repo).as_posix()] = [
                (line_number, lines[line_number - 1])
                for line_number in sorted(matching_lines)
            ]

    unexpected_files = sorted(set(retired_score_hits) - allowed_files)
    assert not unexpected_files, (
        "retired overall_score accesses found outside the allow-list: "
        + ", ".join(unexpected_files)
    )

    analysis_path = repo / "app/routers/analysis.py"
    analysis_source = analysis_path.read_text()
    analysis_hits = [
        (line_number, line)
        for line_number, line in enumerate(analysis_source.splitlines(), start=1)
        if token.search(line)
    ]
    analysis_tree = ast.parse(analysis_source, filename=str(analysis_path))
    allowed_analysis_lines = set()
    for node in ast.walk(analysis_tree):
        if (
            isinstance(node, ast.keyword)
            and node.arg == "overall_score"
            and isinstance(node.value, ast.Constant)
            and node.value.value == 0.0
        ):
            allowed_analysis_lines.update(
                range(node.lineno, node.end_lineno + 1)
            )
        if not isinstance(node, ast.DictComp) or len(node.generators) != 1:
            continue
        value = node.value
        generator = node.generators[0]
        iterator = generator.iter
        is_per_framework_iterator = (
            isinstance(iterator, ast.Call)
            and isinstance(iterator.func, ast.Attribute)
            and iterator.func.attr == "items"
            and isinstance(iterator.func.value, ast.Name)
            and iterator.func.value.id == "per_fw_scores"
        )
        is_overall_score_lookup = (
            isinstance(value, ast.Subscript)
            and isinstance(value.slice, ast.Constant)
            and value.slice.value == "overall_score"
        )
        if is_per_framework_iterator and is_overall_score_lookup:
            allowed_analysis_lines.update(
                range(node.lineno, node.end_lineno + 1)
            )

    disallowed_analysis_hits = [
        f"{analysis_path}:{line_number}: {line.rstrip()}"
        for line_number, line in analysis_hits
        if line_number not in allowed_analysis_lines
    ]
    assert not disallowed_analysis_hits, (
        "analysis.py contains an unapproved overall_score reference:\n"
        + "\n".join(disallowed_analysis_hits)
    )


def test_score_supports_order_deduplication_and_shared_clusters(db_session):
    multi = _assessment(db_session, ["dpdpa", "iso27001"])
    report = GapReport(
        assessment_id=multi.id,
        overall_score=0.0,
        chapter_scores="{}",
        executive_summary="Summary",
        raw_ai_response="{}",
    )
    db_session.add(report)
    db_session.flush()
    db_session.add(GapItem(
        report_id=report.id,
        requirement_id="CH4.SDF.1",
        framework_id="dpdpa",
        cluster_id=None,
        chapter="chapter_4",
        requirement_title="DPO",
        compliance_status="compliant",
        current_state="Implemented",
        gap_description="No gap",
        risk_level="low",
        remediation_action="Maintain",
        remediation_priority=3,
        remediation_effort="low",
        timeline_weeks=1,
    ))
    db_session.commit()

    from app.services.scoring import score

    forward = score(multi.id, ["dpdpa", "iso27001"], _session=db_session)
    reverse = score(multi.id, ["iso27001", "dpdpa"], _session=db_session)
    assert forward.per_framework == reverse.per_framework
    assert forward.unique_clusters == 1
    assert forward.total_controls_evaluated > forward.unique_clusters
    assert not hasattr(forward, "combined")

    single = _assessment(db_session, ["dpdpa"])
    assert set(score(single.id, ["dpdpa", "dpdpa"], _session=db_session).per_framework) == {"dpdpa"}
    with pytest.raises(ValueError, match="at least one"):
        score(single.id, [], _session=db_session)
    with pytest.raises(ValueError, match="not configured"):
        score(multi.id, ["dpdpa"], _session=db_session)
    with pytest.raises(ImportError):
        from app.schemas.scoring import CombinedScore  # noqa: F401


def test_comparison_renders_framework_deltas_and_missing_scores(client, db_session):
    old = _assessment(db_session, ["dpdpa", "iso27001"], company_name="Delta Co")
    new = _assessment(db_session, ["dpdpa", "iso27001"], company_name="Delta Co")
    _report(db_session, old, {"dpdpa": _scores("dpdpa"), "iso27001": _scores("iso27001", "partially_compliant")})
    _report(db_session, new, {"dpdpa": _scores("dpdpa", "partially_compliant"), "iso27001": _scores("iso27001")})

    response = client.get(f"/assessments/{new.id}/compare/{old.id}")
    assert response.status_code == 200
    assert "Framework Scores" in response.text
    assert "Overall Score" not in response.text
    assert "+50.0%" in response.text
    assert "-50.0%" in response.text

    old_single = _assessment(db_session, ["dpdpa"], company_name="Missing Co")
    new_multi = _assessment(db_session, ["dpdpa", "iso27001"], company_name="Missing Co")
    _report(db_session, old_single, {"dpdpa": _scores("dpdpa")})
    _report(db_session, new_multi, {"dpdpa": _scores("dpdpa"), "iso27001": _scores("iso27001")})
    missing = client.get(f"/assessments/{new_multi.id}/compare/{old_single.id}")
    assert missing.status_code == 200
    assert "ISO 27001" in missing.text
    assert "—" in missing.text


def test_report_api_has_only_framework_score_shapes(client, db_session):
    assessments = []
    for framework_ids in (["dpdpa"], ["dpdpa", "iso27001"]):
        assessment = _assessment(db_session, framework_ids)
        _report(db_session, assessment, {framework_id: _scores(framework_id)
                                         for framework_id in framework_ids})
        assessments.append(assessment)

    for assessment in assessments:
        for suffix in ("", "/summary", "/full"):
            response = client.get(f"/api/assessments/{assessment.id}/report{suffix}")
            assert response.status_code == 200, response.text
            payload = response.json()
            assert "overall_score" not in payload
            assert "overall_rating" not in payload
            assert ("framework_scores" in payload) or ("frameworks" in payload)


def test_pdf_has_one_score_section_per_framework_and_no_total(db_session):
    from app.utils.pdf_export import generate_pdf

    assessment = _assessment(db_session, ["dpdpa", "iso27001"])
    scores = {"dpdpa": _scores("dpdpa"), "iso27001": _scores("iso27001", "partially_compliant")}
    report = _report(db_session, assessment, scores)
    pdf_bytes = generate_pdf(
        report,
        [],
        assessment.company_name,
        selected_frameworks=assessment.frameworks,
        assessment=assessment,
    )
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    assert "Overall Score" not in text
    assert "DPDPA" in text
    assert "ISO 27001" in text
    assert "100%" in text
    assert "50%" in text


def test_legacy_reader_falls_back_only_for_single_framework(client, db_session):
    from app.services.scoring import report_framework_scores

    single = _assessment(db_session, ["dpdpa"], company_name="Legacy Co")
    single_report = GapReport(
        assessment_id=single.id,
        overall_score=61.5,
        chapter_scores=json.dumps({
            "chapter_2": {"score": 60, "rating": "Partially Compliant", "title": "Chapter 2"}
        }),
        framework_scores=None,
        executive_summary="Legacy",
        raw_ai_response="{}",
    )
    db_session.add(single_report)
    db_session.commit()
    fallback = report_framework_scores(single_report, single)
    assert fallback["dpdpa"]["overall_score"] == 61.5

    multi = _assessment(db_session, ["dpdpa", "iso27001"], company_name="Legacy Multi")
    multi_report = GapReport(
        assessment_id=multi.id,
        overall_score=77.0,
        chapter_scores="{}",
        framework_scores=None,
        executive_summary="Legacy",
        raw_ai_response="{}",
    )
    db_session.add(multi_report)
    db_session.commit()
    assert report_framework_scores(multi_report, multi) == {}
    response = client.get(f"/assessments/{multi.id}/report-summary")
    assert response.status_code == 200
    assert "Scores unavailable" in response.text
