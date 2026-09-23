from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.database import Base
from app.models.assessment import Assessment
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem
from app.routers import analysis


def test_legacy_dpdpa_analysis_persists_framework_id(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.sqlite3'}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    assessment = Assessment(
        company_name="Legacy Co",
        industry="Technology",
        company_size="small",
    )
    db.add(assessment)
    db.flush()
    db.add(
        QuestionnaireResponse(
            assessment_id=assessment.id,
            question_id="DPDPA.TEST",
            answer="fully_implemented",
        )
    )
    db.commit()

    monkeypatch.setattr(
        analysis,
        "build_questionnaire",
        lambda **_kwargs: [{"id": "DPDPA.TEST"}],
    )
    monkeypatch.setattr(
        analysis,
        "run_gap_analysis",
        lambda **_kwargs: {
            "parsed": {
                "assessments": [
                    {
                        "requirement_id": "DPDPA.TEST",
                        "compliance_status": "compliant",
                    }
                ],
                "executive_summary": "Test summary",
            },
            "raw": "test response",
        },
    )
    monkeypatch.setattr(
        analysis,
        "compute_framework_scores",
        lambda *_args: {
            "overall_score": 100.0,
            "overall_rating": "Compliant",
            "domain_scores": {},
        },
    )
    monkeypatch.setattr(analysis, "generate_initiatives", lambda _assessments: [])

    try:
        analysis.trigger_analysis(assessment.id, db)
        db.expire_all()

        item = db.query(GapItem).one()
        assert item.framework_id == "dpdpa"
    finally:
        db.close()
        engine.dispose()
