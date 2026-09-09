import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.config import settings
from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
from app.frameworks.definitions.gdpr import GDPR_DEFINITION
from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.report import GapItem, GapReport
from app.routers.web import router, templates


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
    monkeypatch.setattr("app.services.scoring.SessionLocal", testing_session, raising=False)
    yield session
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
def client(db_session):
    previous_settings = templates.env.globals.get("settings")
    templates.env.globals["settings"] = settings
    app = FastAPI()
    app.include_router(router)

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    if previous_settings is None:
        templates.env.globals.pop("settings", None)
    else:
        templates.env.globals["settings"] = previous_settings


def _assessment(db_session, framework_ids):
    assessment = Assessment(
        company_name="Acme",
        industry="it_services",
        company_size="sme",
        selected_frameworks=json.dumps(framework_ids),
    )
    db_session.add(assessment)
    db_session.commit()
    db_session.refresh(assessment)
    return assessment


def _gap_item(report_id, requirement_id, status, cluster_id=None):
    return GapItem(
        report_id=report_id,
        requirement_id=requirement_id,
        framework_id="dpdpa",
        cluster_id=cluster_id,
        chapter="chapter_2",
        requirement_title=requirement_id,
        compliance_status=status,
        current_state="Current state",
        gap_description=f"{status} reasoning",
        risk_level="low",
        remediation_action="Maintain",
        remediation_priority=3,
        remediation_effort="low",
        timeline_weeks=1,
    )


def test_new_assessment_requires_at_least_one_framework(client):
    response = client.post(
        "/assessments",
        data={"company_name": "x", "industry": "other", "company_size": "sme"},
    )
    assert response.status_code == 400


def test_new_assessment_accepts_single_and_multi_frameworks(client):
    single = client.post(
        "/assessments",
        data={
            "company_name": "single",
            "industry": "other",
            "company_size": "sme",
            "selected_frameworks": "dpdpa",
        },
        follow_redirects=False,
    )
    multi = client.post(
        "/assessments",
        data={
            "company_name": "multi",
            "industry": "other",
            "company_size": "sme",
            "selected_frameworks": ["dpdpa", "iso27001", "nist_csf"],
        },
        follow_redirects=False,
    )
    assert single.status_code == 303
    assert multi.status_code == 303


def test_new_assessment_rejects_roadmap_framework(client):
    response = client.post(
        "/assessments",
        data={
            "company_name": "x",
            "industry": "other",
            "company_size": "sme",
            "selected_frameworks": "gdpr",
        },
    )
    assert response.status_code == 400


def test_picker_disables_roadmap_frameworks_and_submit(client):
    response = client.get("/assessments/new")
    assert response.status_code == 200
    assert response.text.count('title="Roadmap — control data present, analysis pipeline coming"') == 3
    assert 'value="gdpr" disabled' in response.text
    assert 'value="hipaa" disabled' in response.text
    assert 'value="pci_dss" disabled' in response.text
    assert 'id="create-assessment"' in response.text
    assert 'id="create-assessment" disabled' in response.text


def test_assessment_page_renders_framework_tabs_only_when_multi(client, db_session):
    multi = _assessment(db_session, ["dpdpa", "iso27001"])
    solo = _assessment(db_session, ["dpdpa"])
    assert 'class="framework-tabs' in client.get(f"/assessments/{multi.id}").text
    assert "hx-get=" in client.get(f"/assessments/{multi.id}").text
    reloaded = client.get(f"/assessments/{multi.id}?tab=questionnaire&framework=iso27001")
    assert f'hx-push-url="/assessments/{multi.id}?tab=questionnaire&amp;framework=iso27001"' in reloaded.text
    assert 'aria-selected="true"' in reloaded.text
    assert "ISO 27001" in reloaded.text
    assert f'href="/assessments/{multi.id}?tab=report&amp;framework=iso27001"' in reloaded.text
    assert 'class="framework-tabs' not in client.get(f"/assessments/{solo.id}").text


def test_assessment_model_rejects_explicit_empty_framework_list():
    with pytest.raises(ValueError, match="At least one framework"):
        Assessment(
            company_name="Acme",
            industry="other",
            company_size="sme",
            selected_frameworks="[]",
        )


def test_framework_tab_rejects_framework_outside_assessment(client, db_session):
    assessment = _assessment(db_session, ["dpdpa", "iso27001"])
    valid = client.get(f"/assessments/{assessment.id}/tab/iso27001")
    invalid = client.get(f"/assessments/{assessment.id}/tab/nist_csf")
    assert valid.status_code == 200
    assert "ISO 27001" in valid.text
    assert invalid.status_code == 404


def test_report_view_mode_defaults_and_validation(client, db_session):
    multi = _assessment(db_session, ["dpdpa", "iso27001"])
    solo = _assessment(db_session, ["dpdpa"])
    for assessment in (multi, solo):
        db_session.add(
            GapReport(
                assessment_id=assessment.id,
                overall_score=0,
                chapter_scores="{}",
                executive_summary="Summary",
                raw_ai_response="{}",
                framework_scores=json.dumps(
                    {fid: {"overall_score": 0, "overall_rating": "N/A", "domain_scores": {}}
                     for fid in assessment.frameworks}
                ),
            )
        )
    db_session.commit()

    combined_page = client.get(
        f"/assessments/{multi.id}/report?view=combined&framework=iso27001"
    )
    assert "<!DOCTYPE html>" in combined_page.text
    assert 'hx-get="/assessments/' in combined_page.text
    assert "view=combined" in combined_page.text
    assert "framework=iso27001" in combined_page.text

    solo_page = client.get(f"/assessments/{solo.id}/report")
    assert "<!DOCTYPE html>" in solo_page.text
    assert "view=per_framework" in solo_page.text

    per_framework = client.get(
        f"/assessments/{multi.id}/report-summary?view=per_framework&framework=iso27001"
    )
    assert "<!DOCTYPE html>" not in per_framework.text
    assert 'data-view-mode="per_framework"' in per_framework.text
    assert "DPDPA" in per_framework.text
    assert "ISO 27001" in per_framework.text
    assert "view=combined&amp;framework=iso27001" in per_framework.text
    htmx_partial = client.get(
        f"/assessments/{multi.id}/report?view=combined&framework=iso27001",
        headers={"HX-Request": "true"},
    )
    assert "<!DOCTYPE html>" not in htmx_partial.text
    assert 'data-view-mode="combined"' in htmx_partial.text
    boosted_page = client.get(
        f"/assessments/{multi.id}/report?view=per_framework&framework=iso27001",
        headers={"HX-Request": "true", "HX-Boosted": "true"},
    )
    assert "<!DOCTYPE html>" in boosted_page.text
    assert "view=per_framework" in boosted_page.text
    assert "framework=iso27001" in boosted_page.text
    assert client.get(f"/assessments/{multi.id}/report?view=bogus").status_code == 400


def test_scoring_contract_shape_and_single_framework_consistency(db_session):
    assessment = _assessment(db_session, ["dpdpa"])
    report = GapReport(
        assessment_id=assessment.id,
        overall_score=100,
        chapter_scores="{}",
        executive_summary="Summary",
        raw_ai_response="{}",
    )
    db_session.add(report)
    db_session.flush()
    db_session.add(_gap_item(report.id, "CH2.NOTICE.1", "compliant"))
    db_session.commit()

    from app.schemas.scoring import ClusterVerdict
    from app.services.scoring import score

    result = score(assessment.id, ["dpdpa"], _session=db_session)
    assert set(result.per_framework) == {"dpdpa"}
    assert result.combined.overall_score == result.per_framework["dpdpa"].overall_score
    assert result.combined.by_framework == result.per_framework
    assert len(result.cluster_verdicts) == 1
    for verdict in result.cluster_verdicts.values():
        ClusterVerdict.model_validate(verdict.model_dump())


def test_scoring_wrapper_does_not_fabricate_other_frameworks(db_session):
    assessment = _assessment(db_session, ["iso27001"])
    from app.services.scoring import score

    with pytest.raises(NotImplementedError):
        score(assessment.id, ["iso27001"], _session=db_session)


def test_scoring_collapses_mapped_controls_and_matches_legacy_semantics(db_session):
    assessment = _assessment(db_session, ["dpdpa"])
    report = GapReport(
        assessment_id=assessment.id,
        overall_score=0,
        chapter_scores="{}",
        executive_summary="Summary",
        raw_ai_response="{}",
    )
    db_session.add(report)
    db_session.flush()
    db_session.add_all([
        _gap_item(report.id, "CH4.SDF.2", "compliant"),
        _gap_item(report.id, "CH4.SDF.4", "partially_compliant"),
        _gap_item(report.id, "CH2.NOTICE.1", "not_applicable"),
        _gap_item(report.id, "CH2.NOTICE.2", "not_assessed"),
    ])
    db_session.commit()

    from app.services.scoring import compute_scores, score

    result = score(assessment.id, ["dpdpa"], _session=db_session)
    assert result.cluster_verdicts["CLUSTER_004"].status == "partial"
    assert result.per_framework["dpdpa"].covered_control_count == 4
    assert result.combined.total_controls_evaluated == 4
    propagated_legacy = compute_scores([
        {"requirement_id": "CH4.SDF.2", "compliance_status": "partially_compliant"},
        {"requirement_id": "CH4.SDF.4", "compliance_status": "partially_compliant"},
    ])
    assert result.combined.overall_score == propagated_legacy["overall_score"] / 20


def test_scoring_rejects_missing_or_mismatched_assessment(db_session):
    assessment = _assessment(db_session, ["dpdpa", "iso27001"])
    from app.services.scoring import score

    with pytest.raises(ValueError, match="does not exist"):
        score("missing", ["dpdpa"], _session=db_session)
    with pytest.raises(ValueError, match="not configured as DPDPA-only"):
        score(assessment.id, ["dpdpa"], _session=db_session)


def test_scoring_schema_rejects_inconsistent_single_framework_combined_view():
    from pydantic import ValidationError

    from app.schemas.scoring import CombinedScore, FrameworkScore, ScoringResult

    framework = FrameworkScore(
        framework_id="dpdpa",
        overall_score=2.5,
        overall_rating="M2",
        by_domain={},
        control_count=1,
        covered_control_count=1,
        contributing_clusters=["SINGLE.X"],
    )
    with pytest.raises(ValidationError, match="single-framework combined"):
        ScoringResult(
            per_framework={"dpdpa": framework},
            combined=CombinedScore(
                overall_score=3.0,
                overall_rating="M3",
                by_framework={"dpdpa": framework},
                unique_clusters=0,
                total_controls_evaluated=1,
            ),
            cluster_verdicts={},
        )
