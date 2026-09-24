import io
import json

import pytest
from docx import Document
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
from app.frameworks.definitions.gdpr import GDPR_DEFINITION
from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.routers.web import router


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
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
    app = FastAPI()
    app.include_router(router)

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client


def _assessment(db_session, industry="it_services"):
    assessment = Assessment(
        company_name="Acme",
        industry=industry,
        company_size="sme",
        selected_frameworks=json.dumps(["dpdpa"]),
    )
    db_session.add(assessment)
    db_session.commit()
    db_session.refresh(assessment)
    return assessment


def test_context_submit_stub_is_removed(client, db_session):
    assessment = _assessment(db_session)

    response = client.post(f"/assessments/{assessment.id}/context/submit")

    assert response.status_code == 404


def test_scope_profiler_reduced_signatures_preserve_behavior():
    from app.services.scope_profiler import compute_scope, compute_scope_multi

    scope_answers = {
        "SCP.1": "no",
        "SCP.2": "no",
        "SCP.3": "no",
        "SCP.4": "employee",
        "SCP.5": "no",
    }

    direct = compute_scope(scope_answers)
    multi = compute_scope_multi(scope_answers, ["dpdpa"])

    assert direct["applicable_requirements"] == multi["applicable_requirements"]
    assert direct["excluded_requirements"] == multi["excluded_requirements"]
    assert direct["evidence_checklist"] == multi["evidence_checklist"]


def test_scope_exclusion_stays_skipped_when_requirement_has_no_other_question(db_session):
    from app.dpdpa.framework import get_all_requirements
    from app.services.question_engine import build_adaptive_questionnaire

    assessment = _assessment(db_session)
    excluded_id = "CH4.SDF.1"
    assessment.applicable_requirements = json.dumps(
        [requirement["id"] for requirement in get_all_requirements() if requirement["id"] != excluded_id]
    )
    db_session.commit()

    result = build_adaptive_questionnaire(assessment.id, db_session)
    questions = [
        question
        for section in result["sections"]
        for question in section["questions"]
    ]
    excluded_questions = [question for question in questions if question["id"] == excluded_id]

    assert len(excluded_questions) == 1
    assert excluded_questions[0]["status"] == "skipped"
    assert excluded_questions[0]["skip_reason"] == "Not applicable per scope definition"


def test_industry_question_chapter_title_reflects_resolved_bank(db_session):
    from app.services.question_engine import build_adaptive_questionnaire

    bespoke = _assessment(db_session)
    generic = _assessment(db_session, industry="fintech")

    bespoke_result = build_adaptive_questionnaire(bespoke.id, db_session)
    generic_result = build_adaptive_questionnaire(generic.id, db_session)

    bespoke_sections = [section for section in bespoke_result["sections"] if section["source"] == "industry"]
    generic_sections = [section for section in generic_result["sections"] if section["source"] == "industry"]

    assert bespoke_sections
    assert generic_sections
    assert {section["chapter_title"] for section in bespoke_sections} == {"Industry-Specific"}
    assert {section["chapter_title"] for section in generic_sections} == {"Additional Questions"}


def test_rfi_docx_includes_framework_label():
    from app.utils.rfi_export import generate_rfi_docx

    document = Document(
        io.BytesIO(
            generate_rfi_docx(
                title="Evidence request",
                company_name="Example Client",
                introduction="Please respond.",
                evidence_items=[],
                response_instructions="Reply securely.",
                framework_label="DPDPA",
            )
        )
    )

    body = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "DPDPA Compliance Gap Assessment" in body
