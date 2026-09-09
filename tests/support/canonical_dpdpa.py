"""Canonical DPDPA fixture assembly shared by tests and capture script."""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pdfplumber
from sqlalchemy.orm import Session

from app.dpdpa.framework import get_all_requirements
from app.models.assessment import Assessment, AssessmentDocument
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.services.scoring import compute_scores

FIXED_NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


def ensure_dpdpa_registered() -> None:
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
    from app.frameworks.registry import FrameworkRegistry

    if not FrameworkRegistry.is_registered("dpdpa"):
        FrameworkRegistry.register(DPDPA_DEFINITION)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def extract_pdf_text(path: Path) -> str:
    page_logger = logging.getLogger("pdfminer.pdfpage")
    previous_level = page_logger.level
    page_logger.setLevel(logging.ERROR)
    try:
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    finally:
        page_logger.setLevel(previous_level)


def analyzer_kwargs(fixture_dir: Path) -> dict:
    answers = read_json(fixture_dir / "questionnaire_answers.json")
    evidence_paths = sorted((fixture_dir / "evidence").glob("*.pdf"))
    documents = [
        {
            "filename": path.name,
            "category": path.stem,
            "text": extract_pdf_text(path),
        }
        for path in evidence_paths
    ]
    evidence_quotes = [
        {
            "type": "evidence",
            "requirement_id": req_id,
            "content": entry.get("notes", ""),
            "source_quote": entry.get("evidence_quote", ""),
        }
        for req_id, entry in answers.items()
        if entry.get("evidence_quote")
    ]
    return {
        "company_name": "Meridian Retail Systems Pvt. Ltd.",
        "industry": "ecommerce",
        "company_size": "sme",
        "description": "Synthetic Indian retail SaaS company used only for deterministic tests.",
        "responses": [
            {
                "question_id": req_id,
                "answer": entry["answer"],
                "notes": entry.get("notes"),
                "na_reason": entry.get("na_reason"),
                "confidence": entry.get("confidence", "high"),
            }
            for req_id, entry in answers.items()
        ],
        "documents": documents,
        "context_profile": {
            "risk_level": "high",
            "handles_children_data": True,
            "cross_border_transfers": True,
            "likely_sdf": False,
        },
        # Synthetic evidence findings deliberately cover Call 1 so the DPDPA
        # golden has one stable analyzer request. Live capture uses the same path.
        "desk_review_data": {
            "coverage_summary": {},
            "findings": evidence_quotes,
            "signal_flags": [],
            "absence_findings": [],
        },
        "applicable_requirements": [item["id"] for item in get_all_requirements()],
    }


def synthetic_analyzer_response(fixture_dir: Path) -> dict:
    """Create transparent fake analyzer content for the offline characterization."""
    answers = read_json(fixture_dir / "questionnaire_answers.json")
    status_map = {
        "fully_implemented": ("compliant", 3),
        "partially_implemented": ("partially_compliant", 2),
        "planned": ("non_compliant", 1),
        "not_implemented": ("non_compliant", 0),
        "not_applicable": ("not_applicable", 0),
    }
    assessments = []
    for requirement in get_all_requirements():
        req_id = requirement["id"]
        answer = answers[req_id]
        status, maturity = status_map[answer["answer"]]
        assessments.append(
            {
                "requirement_id": req_id,
                "compliance_status": status,
                "current_state": answer["notes"],
                "gap_description": (
                    "No material gap identified in the synthetic evidence."
                    if status == "compliant"
                    else "The synthetic fixture shows that this control needs documented improvement."
                ),
                "risk_level": "low" if status == "compliant" else "high",
                "remediation_action": "Document, approve, and test the control with retained evidence.",
                "remediation_priority": 4 if status == "compliant" else 2,
                "remediation_effort": "low" if status == "compliant" else "medium",
                "timeline_weeks": 2 if status == "compliant" else 8,
                "maturity_level": maturity,
                "root_cause_category": "process",
                "evidence_quote": answer.get("evidence_quote"),
            }
        )
    parsed = {
        "executive_summary": (
            "Synthetic characterization: Meridian has partial DPDPA controls and must "
            "formalize evidence, operating procedures, and governance oversight."
        ),
        "assessments": assessments,
    }
    return {
        "text": json.dumps(parsed, sort_keys=True, separators=(",", ":")),
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        },
    }


def _synthetic_screening_response() -> str:
    statuses = ["compliant", "partially_compliant", "non_compliant"]
    return json.dumps(
        {
            "inferences": {
                requirement["id"]: {
                    "compliance_status": statuses[index % len(statuses)],
                    "confidence": "low",
                    "reasoning": "Synthetic screening inference for deterministic fixture coverage.",
                }
                for index, requirement in enumerate(get_all_requirements())
            }
        },
        sort_keys=True,
    )


@contextmanager
def synthetic_screening_transport():
    """Replace screening's provider client while exercising its real parse/persist path."""
    response = SimpleNamespace(content=[SimpleNamespace(text=_synthetic_screening_response())])
    messages = SimpleNamespace(create=lambda **_kwargs: response)
    client = SimpleNamespace(messages=messages)
    with patch("app.services.screening.anthropic.Anthropic", return_value=client):
        yield


@dataclass
class CanonicalAssessment:
    fixture_dir: Path
    session: Session
    assessment: Assessment

    @property
    def analyzer_kwargs(self) -> dict:
        return analyzer_kwargs(self.fixture_dir)


def seed_assessment(session: Session, fixture_dir: Path) -> Assessment:
    ensure_dpdpa_registered()
    kwargs = analyzer_kwargs(fixture_dir)
    screening = read_json(fixture_dir / "screening_answers.json")
    assessment = Assessment(
        id="00000000-0000-4000-8000-000000000003",
        company_name=kwargs["company_name"],
        industry=kwargs["industry"],
        company_size=kwargs["company_size"],
        description=kwargs["description"],
        status="questionnaire_done",
        context_profile=json.dumps(kwargs["context_profile"], sort_keys=True),
        selected_frameworks='["dpdpa"]',
        screening_status="not_started",
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )
    session.add(assessment)
    session.flush()

    from app.services.screening import run_screening_pass

    with synthetic_screening_transport():
        run_screening_pass(assessment.id, screening, session)

    answers = read_json(fixture_dir / "questionnaire_answers.json")
    for req_id, entry in answers.items():
        session.add(
            QuestionnaireResponse(
                assessment_id=assessment.id,
                question_id=req_id,
                answer=entry["answer"],
                notes=entry.get("notes"),
                evidence_reference=entry.get("evidence_quote"),
                na_reason=entry.get("na_reason"),
                confidence=entry.get("confidence", "high"),
                answer_source="human",
                submitted_at=FIXED_NOW,
            )
        )
    for path in sorted((fixture_dir / "evidence").glob("*.pdf")):
        session.add(
            AssessmentDocument(
                assessment_id=assessment.id,
                filename=path.name,
                file_path=str(path),
                file_type="pdf",
                document_category=path.stem,
                extracted_text=extract_pdf_text(path),
                uploaded_at=FIXED_NOW,
            )
        )
    session.commit()
    return assessment


def materialize_report(session: Session, assessment: Assessment, analyzer_output: dict):
    existing = session.query(GapReport).filter_by(assessment_id=assessment.id).first()
    if existing:
        session.query(GapItem).filter_by(report_id=existing.id).delete()
        session.delete(existing)
        session.flush()

    parsed = analyzer_output["parsed"]
    items = parsed["assessments"]
    scores = compute_scores(items)
    report = GapReport(
        id="00000000-0000-4000-8000-000000000030",
        assessment_id=assessment.id,
        overall_score=scores["overall_score"],
        chapter_scores=json.dumps(scores["chapter_scores"], sort_keys=True),
        executive_summary=parsed["executive_summary"],
        raw_ai_response=analyzer_output["raw"],
        generated_at=FIXED_NOW,
    )
    session.add(report)
    requirements = {item["id"]: item for item in get_all_requirements()}
    gap_items = []
    for index, item in enumerate(items, start=1):
        requirement = requirements[item["requirement_id"]]
        gap_item = GapItem(
            id=f"00000000-0000-4000-8000-{index:012d}",
            report_id=report.id,
            requirement_id=item["requirement_id"],
            framework_id=None,
            cluster_id=None,
            control_reference=None,
            chapter=requirement["chapter"],
            requirement_title=requirement["title"],
            compliance_status=item["compliance_status"],
            current_state=item["current_state"],
            gap_description=item["gap_description"],
            risk_level=item["risk_level"],
            remediation_action=item["remediation_action"],
            remediation_priority=item["remediation_priority"],
            remediation_effort=item["remediation_effort"],
            timeline_weeks=item["timeline_weeks"],
            maturity_level=item["maturity_level"],
            root_cause_category=item["root_cause_category"],
            evidence_quote=item.get("evidence_quote"),
            evidence_confidence="strong" if item.get("evidence_quote") else "weak",
        )
        session.add(gap_item)
        gap_items.append(gap_item)
    session.commit()
    return report, gap_items
