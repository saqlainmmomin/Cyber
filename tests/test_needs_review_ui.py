"""Persistence, route wiring, and rendering coverage for needs_review."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.main import _run_migrations
from app.models.assessment import Assessment, AssessmentDocument
from app.models.report import GapItem


def _item(**overrides):
    values = {
        "id": "item-1",
        "framework_id": "dpdpa",
        "requirement_id": "CH2.CONSENT.1",
        "requirement_title": "Consent",
        "review_status": "draft",
        "risk_level": "medium",
        "ai_compliance_status": "compliant",
        "compliance_status": "compliant",
        "ai_risk_level": "medium",
        "evidence_confidence": "weak",
        "ai_gap_description": "No evidence quote was supplied.",
        "gap_description": "No evidence quote was supplied.",
        "evidence_quote": None,
        "reviewer_notes": None,
        "needs_review": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _render_card(item):
    template_dir = Path(__file__).parents[1] / "app" / "templates"
    environment = Environment(loader=FileSystemLoader(template_dir))
    template = environment.get_template("partials/review_finding_card.html")
    return template.render(item=item, assessment=SimpleNamespace(id="assessment-1"))


def test_gap_item_needs_review_defaults_false_and_persists_true(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'needs-review.sqlite3'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        item = GapItem(
            report_id="report-1",
            requirement_id="CH2.CONSENT.1",
            chapter="Chapter 2",
            requirement_title="Consent",
            compliance_status="compliant",
            current_state="Implemented",
            gap_description="",
            risk_level="low",
            remediation_action="",
            remediation_priority=3,
            remediation_effort="low",
            timeline_weeks=2,
        )
        session.add(item)
        session.flush()
        assert item.needs_review is False

        item.needs_review = True
        session.commit()
        loaded = session.get(GapItem, item.id)
        assert loaded.needs_review is True
    finally:
        session.close()
        engine.dispose()


def test_migration_adds_needs_review_to_existing_gap_items():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE gap_items (
                    id TEXT PRIMARY KEY,
                    compliance_status TEXT,
                    gap_description TEXT,
                    risk_level TEXT,
                    ai_compliance_status TEXT,
                    ai_gap_description TEXT,
                    ai_risk_level TEXT,
                    framework_id TEXT
                )
                """
            )
        )

    assert "needs_review" not in {column["name"] for column in inspect(engine).get_columns("gap_items")}
    _run_migrations(engine)
    columns = {column["name"]: column for column in inspect(engine).get_columns("gap_items")}

    assert columns["needs_review"]["default"] == "0"


def test_migration_adds_needs_review_against_full_gap_items_schema():
    """Same migration, but against the real column set (NOT NULLs and all), not the
    stripped 8-column table above — guards against the ALTER/UPDATE/INDEX statements
    in `_run_migrations` interacting badly with columns the stripped table omits."""
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE gap_items (
                    id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    requirement_id TEXT NOT NULL,
                    framework_id TEXT,
                    cluster_id TEXT,
                    control_reference TEXT,
                    chapter TEXT NOT NULL,
                    requirement_title TEXT NOT NULL,
                    compliance_status TEXT NOT NULL,
                    current_state TEXT NOT NULL,
                    gap_description TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    remediation_action TEXT NOT NULL,
                    remediation_priority INTEGER NOT NULL,
                    remediation_effort TEXT NOT NULL,
                    timeline_weeks INTEGER NOT NULL,
                    maturity_level INTEGER,
                    root_cause_category TEXT,
                    evidence_quote TEXT,
                    evidence_confidence TEXT,
                    remediation_status TEXT DEFAULT 'open',
                    remediation_owner TEXT,
                    remediation_target_date DATETIME,
                    remediation_notes TEXT,
                    remediation_closed_at DATETIME,
                    review_status TEXT DEFAULT 'draft',
                    ai_compliance_status TEXT,
                    ai_gap_description TEXT,
                    ai_risk_level TEXT,
                    reviewer_notes TEXT,
                    reviewed_by TEXT,
                    reviewed_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO gap_items (
                    id, report_id, requirement_id, framework_id, chapter, requirement_title,
                    compliance_status, current_state, gap_description, risk_level,
                    remediation_action, remediation_priority, remediation_effort, timeline_weeks
                ) VALUES (
                    'item-1', 'report-1', 'CH2.CONSENT.1', NULL, 'Chapter 2', 'Consent',
                    'compliant', 'Implemented', '', 'low',
                    '', 3, 'low', 2
                )
                """
            )
        )

    assert "needs_review" not in {column["name"] for column in inspect(engine).get_columns("gap_items")}
    _run_migrations(engine)
    columns = {column["name"]: column for column in inspect(engine).get_columns("gap_items")}

    assert columns["needs_review"]["default"] == "0"
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT framework_id, needs_review FROM gap_items WHERE id = 'item-1'")
        ).fetchone()
    # The framework_id backfill in the same migration still runs correctly
    # alongside the new column add against the full, constrained schema.
    assert row[0] == "dpdpa"
    assert row[1] == 0


def test_single_framework_analysis_persists_needs_review_flag(tmp_path, monkeypatch):
    from app.routers import analysis

    engine = create_engine(f"sqlite:///{tmp_path / 'analysis.sqlite3'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        assessment = Assessment(
            company_name="Acme",
            industry="saas",
            company_size="sme",
            status="questionnaire_done",
        )
        session.add(assessment)
        session.flush()
        session.add(
            AssessmentDocument(
                assessment_id=assessment.id,
                filename="policy.pdf",
                file_path="policy.pdf",
                file_type="pdf",
                document_category="privacy_policy",
                extracted_text="Synthetic evidence.",
            )
        )
        session.commit()

        monkeypatch.setattr(analysis, "build_questionnaire", lambda **_kwargs: [])
        monkeypatch.setattr(
            analysis,
            "run_gap_analysis",
            lambda **_kwargs: {
                "parsed": {
                    "executive_summary": "summary",
                    "assessments": [{
                        "requirement_id": "CH2.CONSENT.1",
                        "compliance_status": "compliant",
                        "needs_review": True,
                    }],
                },
                "raw": "{}",
            },
        )
        monkeypatch.setattr(
            analysis,
            "compute_scores",
            lambda _assessments: {"overall_score": 3.0, "chapter_scores": {}},
        )
        monkeypatch.setattr(analysis, "generate_initiatives", lambda _assessments: [])

        result = analysis.trigger_analysis(assessment.id, session)
        item = session.query(GapItem).one()

        assert result["status"] == "completed"
        assert item.needs_review is True
    finally:
        session.close()
        engine.dispose()


def test_multi_framework_analysis_persists_needs_review_flag(tmp_path, monkeypatch):
    from app.routers import analysis
    from app.frameworks import questionnaire_builder
    from app.main import _register_frameworks

    _register_frameworks()

    engine = create_engine(f"sqlite:///{tmp_path / 'multi-analysis.sqlite3'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        assessment = Assessment(
            company_name="Acme",
            industry="saas",
            company_size="sme",
            status="questionnaire_done",
            selected_frameworks=json.dumps(["iso27001"]),
        )
        session.add(assessment)
        session.flush()
        session.add(
            AssessmentDocument(
                assessment_id=assessment.id,
                filename="policy.pdf",
                file_path="policy.pdf",
                file_type="pdf",
                document_category="privacy_policy",
                extracted_text="Synthetic evidence.",
            )
        )
        session.commit()

        monkeypatch.setattr(questionnaire_builder, "build_multi_questionnaire", lambda *_a, **_kw: [])
        monkeypatch.setattr(questionnaire_builder, "compute_excluded_controls", lambda *_a, **_kw: [])
        monkeypatch.setattr(
            analysis,
            "run_multi_framework_analysis",
            lambda **_kwargs: {
                "frameworks": {
                    "iso27001": {
                        "parsed": {
                            "assessments": [{
                                "requirement_id": "ISO.A5.1",
                                "compliance_status": "compliant",
                                "needs_review": True,
                            }],
                        },
                        "raw": "{}",
                    },
                },
                "synthesis": None,
            },
        )
        monkeypatch.setattr(analysis, "compute_framework_scores", lambda *_a, **_kw: {"overall_score": 3.0})
        monkeypatch.setattr(
            analysis,
            "compute_unified_maturity",
            lambda *_a, **_kw: {"overall_score": 3.0, "framework_scores": {}},
        )
        monkeypatch.setattr(analysis, "generate_multi_framework_initiatives", lambda *_a, **_kw: [])

        result = analysis.trigger_analysis(assessment.id, session)
        item = session.query(GapItem).one()

        assert result["status"] == "completed"
        assert item.needs_review is True
    finally:
        session.close()
        engine.dispose()


def test_review_card_shows_distinct_needs_review_marker():
    rendered = _render_card(_item(needs_review=True))

    assert "Needs review" in rendered
    assert "model flagged this verdict" in rendered
    assert "text-amber-700 dark:text-amber-300" in rendered


def test_review_card_omits_needs_review_marker_for_false_flag():
    rendered = _render_card(_item(needs_review=False))

    assert "Needs review" not in rendered
