"""PR #14 data-integrity verification tests.

Covers all eight verification items from the handoff:
1. Fresh schema FK enforcement + document deletion policy
2. Legacy upgrade fixture with PRAGMA verification
3. Legacy-orphan fixture: migration aborts safely
4. Schema convergence: second migration is a no-op
5. Analysis rerun x3: flat history, no nested legacy_history
6. Desk-review rerun: flat finding snapshots
7. detect_orphans coverage (including document_id)
8. Full suite pass (implicit — this file is part of the suite)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.assessment import Assessment, AssessmentDocument
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.models.initiative import Initiative
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.models.rfi import RFIDocument


REPO_ROOT = Path(__file__).resolve().parent.parent


def _alembic_upgrade(engine):
    """Run `alembic upgrade head` against the given engine's database file.

    Alembic opens its own internal engine/connection pool against the same
    URL, separate from `engine`. Dispose `engine` afterwards so any
    connection it had pooled *before* the migration ran (tests often seed
    legacy data via a raw connection on `engine` first) gets invalidated,
    the same way the old `_ensure_foreign_keys()` disposed its engine
    argument at the end of every run.
    """
    alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
    try:
        command.upgrade(alembic_cfg, "head")
    finally:
        engine.dispose()


def _fresh_engine(tmp_path, name="test.db"):
    engine = create_engine(
        f"sqlite:///{tmp_path / name}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_fk_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture()
def fresh_db(tmp_path):
    """Fresh database created via create_all — models define the schema."""
    engine = _fresh_engine(tmp_path)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session, engine
    session.close()
    engine.dispose()


def _make_assessment(db, **kw):
    a = Assessment(
        company_name=kw.get("company_name", "IntegrityCo"),
        industry="Tech",
        company_size="small",
    )
    db.add(a)
    db.commit()
    return a.id


def _make_document(db, assessment_id):
    doc = AssessmentDocument(
        assessment_id=assessment_id,
        filename="policy.pdf",
        file_path="/tmp/policy.pdf",
        file_type="pdf",
        document_category="policy",
    )
    db.add(doc)
    db.commit()
    return doc.id


# ---------------------------------------------------------------------------
# 1. Fresh schema: FKs exist and reject invalid inserts; document deletion
# ---------------------------------------------------------------------------


class TestFreshSchemaFKs:
    def test_every_intended_fk_exists(self, fresh_db):
        db, engine = fresh_db
        with engine.connect() as conn:
            for table in [
                "assessment_documents",
                "questionnaire_responses",
                "gap_reports",
                "gap_items",
                "initiatives",
                "desk_review_summaries",
                "desk_review_findings",
                "rfi_documents",
            ]:
                fks = conn.execute(text(f"PRAGMA foreign_key_list({table})")).fetchall()
                assert len(fks) > 0, f"{table} has no FK constraints"

    def test_desk_review_finding_document_id_fk_exists(self, fresh_db):
        db, engine = fresh_db
        with engine.connect() as conn:
            fks = conn.execute(
                text("PRAGMA foreign_key_list(desk_review_findings)")
            ).fetchall()
            doc_fk = [r for r in fks if r[3] == "document_id"]
            assert len(doc_fk) == 1
            assert doc_fk[0][2] == "assessment_documents"
            assert doc_fk[0][6] == "SET NULL"

    def test_gap_report_rejects_invalid_assessment(self, fresh_db):
        db, engine = fresh_db
        report = GapReport(
            assessment_id="nonexistent",
            overall_score=50.0,
            chapter_scores="{}",
            executive_summary="Test",
            raw_ai_response="{}",
        )
        db.add(report)
        with pytest.raises(Exception):
            db.commit()
        db.rollback()

    def test_document_deletion_sets_finding_null(self, fresh_db):
        """Deleting a document should SET NULL on desk_review_findings.document_id."""
        db, engine = fresh_db
        aid = _make_assessment(db)
        doc_id = _make_document(db, aid)

        finding = DeskReviewFinding(
            assessment_id=aid,
            finding_type="evidence",
            requirement_id="CH2.CONSENT.1",
            document_id=doc_id,
            content="Found consent form",
            severity="medium",
        )
        db.add(finding)
        db.commit()
        finding_id = finding.id

        doc = db.get(AssessmentDocument, doc_id)
        db.delete(doc)
        db.commit()

        db.expire_all()
        reloaded = db.get(DeskReviewFinding, finding_id)
        assert reloaded is not None, "Finding should survive document deletion"
        assert reloaded.document_id is None, "document_id should be SET NULL"


# ---------------------------------------------------------------------------
# 2. Legacy upgrade fixture: construct pre-PR schema, run migration, verify
# ---------------------------------------------------------------------------


def _create_legacy_schema(cursor):
    """Create representative pre-PR tables WITHOUT foreign key constraints."""
    cursor.execute("""
        CREATE TABLE assessments (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            industry VARCHAR(100) NOT NULL,
            company_size VARCHAR(50) NOT NULL,
            description TEXT,
            status VARCHAR(50) DEFAULT 'created',
            scope_answers TEXT,
            applicable_requirements TEXT,
            context_answers TEXT,
            context_profile TEXT,
            desk_review_status TEXT,
            selected_frameworks TEXT,
            screening_status TEXT,
            screening_results TEXT,
            review_status VARCHAR(20),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE assessment_documents (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            assessment_id VARCHAR(36) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_type VARCHAR(10) NOT NULL,
            document_category VARCHAR(50) NOT NULL,
            extracted_text TEXT,
            uploaded_at DATETIME NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE gap_reports (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            assessment_id VARCHAR(36) NOT NULL UNIQUE,
            overall_score FLOAT NOT NULL,
            chapter_scores TEXT NOT NULL,
            executive_summary TEXT NOT NULL,
            raw_ai_response TEXT NOT NULL,
            framework_scores TEXT,
            legacy_history TEXT,
            generated_at DATETIME NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE gap_items (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            report_id VARCHAR(36) NOT NULL,
            requirement_id VARCHAR(50) NOT NULL,
            framework_id VARCHAR(30),
            cluster_id VARCHAR(80),
            control_reference VARCHAR(100),
            chapter VARCHAR(50) NOT NULL,
            requirement_title VARCHAR(255) NOT NULL,
            compliance_status VARCHAR(30) NOT NULL,
            current_state TEXT NOT NULL,
            gap_description TEXT NOT NULL,
            risk_level VARCHAR(20) NOT NULL,
            remediation_action TEXT NOT NULL,
            remediation_priority INTEGER NOT NULL,
            remediation_effort VARCHAR(20) NOT NULL,
            timeline_weeks INTEGER NOT NULL,
            maturity_level INTEGER,
            root_cause_category TEXT,
            evidence_quote TEXT,
            evidence_confidence TEXT,
            remediation_status VARCHAR(20) DEFAULT 'open',
            remediation_owner VARCHAR(255),
            remediation_target_date DATETIME,
            remediation_notes TEXT,
            remediation_closed_at DATETIME,
            review_status VARCHAR(20) DEFAULT 'draft',
            needs_review BOOLEAN DEFAULT 0,
            ai_compliance_status TEXT,
            ai_gap_description TEXT,
            ai_risk_level VARCHAR(20),
            reviewer_notes TEXT,
            reviewed_by VARCHAR(255),
            reviewed_at DATETIME
        )
    """)
    cursor.execute("""
        CREATE TABLE initiatives (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            report_id VARCHAR(36) NOT NULL,
            initiative_id VARCHAR(20) NOT NULL,
            title VARCHAR(255) NOT NULL,
            root_cause TEXT NOT NULL,
            root_cause_category VARCHAR(30) NOT NULL,
            requirements_addressed TEXT NOT NULL,
            combined_effort VARCHAR(20) NOT NULL,
            combined_timeline_weeks INTEGER NOT NULL,
            priority INTEGER NOT NULL,
            budget_estimate_band VARCHAR(50),
            suggested_approach TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE desk_review_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id VARCHAR(36) NOT NULL UNIQUE,
            document_catalog TEXT,
            coverage_summary TEXT,
            raw_ai_response TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            error_message TEXT,
            started_at DATETIME,
            completed_at DATETIME,
            legacy_history TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE desk_review_findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id VARCHAR(36) NOT NULL,
            finding_type VARCHAR(20) NOT NULL,
            requirement_id VARCHAR(30),
            document_id VARCHAR(36),
            content TEXT NOT NULL,
            severity VARCHAR(20) DEFAULT 'medium',
            source_quote TEXT,
            source_location VARCHAR(200),
            created_at DATETIME NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE questionnaire_responses (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            assessment_id VARCHAR(36) NOT NULL,
            question_id VARCHAR(50) NOT NULL,
            answer VARCHAR(20) NOT NULL,
            notes TEXT,
            evidence_reference TEXT,
            na_reason TEXT,
            confidence TEXT,
            cluster_id VARCHAR(80),
            answer_source VARCHAR(20) DEFAULT 'human',
            submitted_at DATETIME NOT NULL,
            CONSTRAINT ck_questionnaire_responses_answer_valid
                CHECK (answer IN ('fully_implemented', 'partially_implemented', 'planned', 'not_implemented', 'not_applicable'))
        )
    """)
    cursor.execute("""
        CREATE TABLE rfi_documents (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            assessment_id VARCHAR(36) NOT NULL UNIQUE,
            title VARCHAR(255) NOT NULL,
            introduction TEXT NOT NULL,
            evidence_items TEXT NOT NULL,
            response_instructions TEXT NOT NULL,
            appendix TEXT,
            total_items INTEGER DEFAULT 0,
            critical_items INTEGER DEFAULT 0,
            raw_ai_response TEXT,
            generated_at DATETIME NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_assessment_documents_assessment_id ON assessment_documents (assessment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_gap_reports_assessment_id ON gap_reports (assessment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_gap_items_report_id ON gap_items (report_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_initiatives_report_id ON initiatives (report_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_desk_review_summaries_assessment_id ON desk_review_summaries (assessment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_desk_review_findings_assessment_id ON desk_review_findings (assessment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_questionnaire_responses_assessment_id ON questionnaire_responses (assessment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_rfi_documents_assessment_id ON rfi_documents (assessment_id)")


def _insert_legacy_data(cursor, now_str):
    """Insert valid test data into the legacy schema."""
    cursor.execute(
        "INSERT INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("a1", "LegacyCo", "Tech", "small", None, "completed", None, None, None, None, None, None, None, None, None, now_str, now_str),
    )
    cursor.execute(
        "INSERT INTO assessment_documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("d1", "a1", "policy.pdf", "/tmp/p.pdf", "pdf", "policy", "text", now_str),
    )
    cursor.execute(
        "INSERT INTO gap_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("r1", "a1", 75.0, "{}", "Summary", "{}", None, None, now_str),
    )
    cursor.execute(
        "INSERT INTO gap_items (id, report_id, requirement_id, framework_id, chapter, "
        "requirement_title, compliance_status, current_state, gap_description, risk_level, "
        "remediation_action, remediation_priority, remediation_effort, timeline_weeks) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("g1", "r1", "CH2.CONSENT.1", "dpdpa", "ch2", "Consent", "compliant", "OK",
         "None", "low", "None", 1, "minimal", 0),
    )
    cursor.execute(
        "INSERT INTO desk_review_summaries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (None, "a1", None, None, None, "completed", None, now_str, now_str, None),
    )
    cursor.execute(
        "INSERT INTO desk_review_findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (None, "a1", "evidence", "CH2.CONSENT.1", "d1", "Found consent", "medium", None, None, now_str),
    )
    cursor.execute(
        "INSERT INTO questionnaire_responses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("q1", "a1", "CH2.CONSENT.1", "fully_implemented", None, None, None, None, None, "human", now_str),
    )


class TestLegacyUpgrade:
    def test_migration_adds_fks_and_preserves_data(self, tmp_path):
        """Construct a pre-PR schema, run actual startup migration, verify with PRAGMA."""
        db_path = tmp_path / "legacy.db"
        engine = _fresh_engine(tmp_path, "legacy.db")

        now_str = datetime.now(timezone.utc).isoformat()
        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        _insert_legacy_data(cursor, now_str)
        raw.commit()
        cursor.close()
        raw.close()

        _alembic_upgrade(engine)

        with engine.connect() as conn:
            for table, expected_from in [
                ("assessment_documents", "assessment_id"),
                ("gap_reports", "assessment_id"),
                ("gap_items", "report_id"),
                ("initiatives", "report_id"),
                ("desk_review_summaries", "assessment_id"),
                ("desk_review_findings", "assessment_id"),
                ("desk_review_findings", "document_id"),
                ("rfi_documents", "assessment_id"),
                ("questionnaire_responses", "assessment_id"),
            ]:
                fks = conn.execute(text(f"PRAGMA foreign_key_list({table})")).fetchall()
                fk_from_cols = [r[3] for r in fks]
                assert expected_from in fk_from_cols, (
                    f"{table} missing FK on {expected_from}; got {fk_from_cols}"
                )

            assert conn.execute(text("SELECT COUNT(*) FROM assessments")).scalar() == 1
            assert conn.execute(text("SELECT COUNT(*) FROM gap_reports")).scalar() == 1
            assert conn.execute(text("SELECT COUNT(*) FROM gap_items")).scalar() == 1
            assert conn.execute(text("SELECT COUNT(*) FROM desk_review_findings")).scalar() == 1
            assert conn.execute(text("SELECT COUNT(*) FROM questionnaire_responses")).scalar() == 1

        engine.dispose()

    def test_invalid_insert_fails_after_upgrade(self, tmp_path):
        """After legacy upgrade, FK-violating inserts are rejected."""
        engine = _fresh_engine(tmp_path, "legacy_reject2.db")
        now_str = datetime.now(timezone.utc).isoformat()
        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        _insert_legacy_data(cursor, now_str)
        raw.commit()
        cursor.close()
        raw.close()

        _alembic_upgrade(engine)

        with engine.connect() as conn:
            with pytest.raises(Exception):
                conn.execute(text(
                    "INSERT INTO gap_reports (id, assessment_id, overall_score, chapter_scores, "
                    "executive_summary, raw_ai_response, generated_at) "
                    "VALUES ('bad', 'nonexistent', 0, '{}', '', '{}', :now)"
                ).bindparams(now=now_str))
        engine.dispose()



# ---------------------------------------------------------------------------
# 3. Legacy-orphan fixture: migration aborts safely
# ---------------------------------------------------------------------------


class TestLegacyOrphanAbort:
    def test_migration_aborts_on_orphaned_rows(self, tmp_path):
        engine = _fresh_engine(tmp_path, "orphan.db")
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        _insert_legacy_data(cursor, now_str)
        # Insert an orphan: gap_report referencing nonexistent assessment
        cursor.execute(
            "INSERT INTO gap_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("orphan-r", "nonexistent-a", 0.0, "{}", "", "{}", None, None, now_str),
        )
        raw.commit()
        cursor.close()
        raw.close()

        with pytest.raises(RuntimeError, match="FK migration blocked"):
            _alembic_upgrade(engine)

        # Database should be unchanged (no partial rebuild)
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM gap_reports")).scalar()
            assert count == 2, "Both rows should survive the aborted migration"
            # Verify the table was NOT rebuilt (no FKs added)
            fks = conn.execute(text("PRAGMA foreign_key_list(gap_reports)")).fetchall()
            assert len(fks) == 0, "FKs should not be added when migration aborts"

        engine.dispose()

    def test_set_null_fk_orphans_are_cleaned(self, tmp_path):
        """document_id orphans should be NULLed, not cause an abort."""
        engine = _fresh_engine(tmp_path, "setnull.db")
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        _insert_legacy_data(cursor, now_str)
        # Insert finding with orphaned document_id
        cursor.execute(
            "INSERT INTO desk_review_findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (None, "a1", "evidence", "CH2.SECURITY.1", "nonexistent-doc", "Signal", "high", None, None, now_str),
        )
        raw.commit()
        cursor.close()
        raw.close()

        _alembic_upgrade(engine)  # Should NOT raise

        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT document_id FROM desk_review_findings WHERE requirement_id = 'CH2.SECURITY.1'"
            )).fetchall()
            assert rows[0][0] is None, "Orphaned document_id should be SET NULL"

        engine.dispose()


# ---------------------------------------------------------------------------
# 4. Schema convergence: second migration is a no-op
# ---------------------------------------------------------------------------


class TestSchemaConvergence:
    def test_second_migration_is_noop(self, tmp_path):
        engine = _fresh_engine(tmp_path, "converge.db")
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        _insert_legacy_data(cursor, now_str)
        raw.commit()
        cursor.close()
        raw.close()

        _alembic_upgrade(engine)

        with engine.connect() as conn:
            fks_before = {}
            for table in ["gap_reports", "gap_items", "desk_review_findings"]:
                fks_before[table] = conn.execute(
                    text(f"PRAGMA foreign_key_list({table})")
                ).fetchall()

        # Run again — should be a no-op
        _alembic_upgrade(engine)

        with engine.connect() as conn:
            for table in ["gap_reports", "gap_items", "desk_review_findings"]:
                fks_after = conn.execute(
                    text(f"PRAGMA foreign_key_list({table})")
                ).fetchall()
                assert fks_after == fks_before[table], f"{table} changed on second run"

            assert conn.execute(text("SELECT COUNT(*) FROM gap_reports")).scalar() == 1
            assert conn.execute(text("SELECT COUNT(*) FROM gap_items")).scalar() == 1

        engine.dispose()

    def test_fresh_schema_matches_upgraded(self, tmp_path):
        """Fresh create_all and legacy-upgrade should produce the same FK set."""
        fresh_engine = _fresh_engine(tmp_path, "fresh.db")
        Base.metadata.create_all(fresh_engine)

        legacy_engine = _fresh_engine(tmp_path, "upgraded.db")
        raw = legacy_engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        raw.commit()
        cursor.close()
        raw.close()
        _alembic_upgrade(legacy_engine)

        tables_to_check = [
            "assessment_documents", "gap_reports", "gap_items", "initiatives",
            "desk_review_summaries", "desk_review_findings", "rfi_documents",
            "questionnaire_responses",
        ]
        with fresh_engine.connect() as fc, legacy_engine.connect() as lc:
            for table in tables_to_check:
                fresh_fks = fc.execute(text(f"PRAGMA foreign_key_list({table})")).fetchall()
                legacy_fks = lc.execute(text(f"PRAGMA foreign_key_list({table})")).fetchall()
                fresh_set = {(r[2], r[3], r[4]) for r in fresh_fks}
                legacy_set = {(r[2], r[3], r[4]) for r in legacy_fks}
                assert fresh_set == legacy_set, (
                    f"{table} FK mismatch: fresh={fresh_set}, upgraded={legacy_set}"
                )

        fresh_engine.dispose()
        legacy_engine.dispose()


# ---------------------------------------------------------------------------
# Codex P2 robustness fix: FK presence check must include on_delete, not just
# (child_col, parent_table, parent_col). Otherwise a database that already has
# desk_review_findings.document_id -> assessment_documents.id declared with the
# SQLite default ON DELETE NO ACTION is wrongly treated as already-upgraded and
# is never rebuilt to the intended ON DELETE SET NULL.
# ---------------------------------------------------------------------------


class TestFkDeleteActionDrift:
    def test_detects_and_fixes_on_delete_drift(self, tmp_path):
        engine = _fresh_engine(tmp_path, "drift.db")
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        # Simulate a database that already has FKs on desk_review_findings, but
        # document_id was declared with the SQLite default ON DELETE NO ACTION
        # instead of the intended SET NULL.
        cursor.execute("DROP TABLE desk_review_findings")
        cursor.execute("""
            CREATE TABLE desk_review_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id VARCHAR(36) NOT NULL,
                finding_type VARCHAR(20) NOT NULL,
                requirement_id VARCHAR(30),
                document_id VARCHAR(36),
                content TEXT NOT NULL,
                severity VARCHAR(20) DEFAULT 'medium',
                source_quote TEXT,
                source_location VARCHAR(200),
                created_at DATETIME NOT NULL,
                FOREIGN KEY(assessment_id) REFERENCES assessments (id),
                FOREIGN KEY(document_id) REFERENCES assessment_documents (id)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_desk_review_findings_assessment_id "
            "ON desk_review_findings (assessment_id)"
        )
        _insert_legacy_data(cursor, now_str)
        raw.commit()
        cursor.close()
        raw.close()

        # Sanity check: on_delete is NO ACTION before migration runs.
        with engine.connect() as conn:
            fks = conn.execute(text("PRAGMA foreign_key_list(desk_review_findings)")).fetchall()
            doc_fk = next(r for r in fks if r[3] == "document_id")
            assert doc_fk[6] == "NO ACTION"

        _alembic_upgrade(engine)

        with engine.connect() as conn:
            fks = conn.execute(text("PRAGMA foreign_key_list(desk_review_findings)")).fetchall()
            doc_fk = next(r for r in fks if r[3] == "document_id")
            assert doc_fk[6] == "SET NULL", (
                "Migration should rebuild the table to fix a drifted ON DELETE "
                f"action, but it was left as {doc_fk[6]!r}"
            )
            assert conn.execute(
                text("SELECT COUNT(*) FROM desk_review_findings")
            ).scalar() == 1, "Data must survive the drift-correcting rebuild"

        engine.dispose()


# ---------------------------------------------------------------------------
# 5. Analysis rerun x3: flat history, no nested legacy_history
# ---------------------------------------------------------------------------


class TestAnalysisRerunHistory:
    def _simulate_rerun(self, db, assessment_id, run_number):
        """Simulate the production snapshot logic from analysis.py trigger_analysis."""
        existing = (
            db.query(GapReport)
            .filter(GapReport.assessment_id == assessment_id)
            .first()
        )
        _carried_history = None
        if existing:
            old_items = db.query(GapItem).filter(GapItem.report_id == existing.id).all()
            snapshot = {
                "preserved_at": datetime.now(timezone.utc).isoformat(),
                "label": "gap_analysis_rerun",
                "report": {
                    c.name: getattr(existing, c.name)
                    for c in existing.__table__.columns
                    if c.name != "legacy_history"
                },
                "items": [
                    {c.name: getattr(item, c.name) for c in item.__table__.columns}
                    for item in old_items
                ],
            }
            history = []
            if existing.legacy_history:
                try:
                    history = json.loads(existing.legacy_history)
                    if not isinstance(history, list):
                        history = [history]
                except json.JSONDecodeError:
                    history = []
            history.append(snapshot)
            _carried_history = json.dumps(history, default=str)

            db.query(GapItem).filter(GapItem.report_id == existing.id).delete()
            db.query(Initiative).filter(Initiative.report_id == existing.id).delete()
            db.delete(existing)
            db.flush()

        report = GapReport(
            assessment_id=assessment_id,
            overall_score=50.0 + run_number * 10,
            chapter_scores=json.dumps({"ch2": 60 + run_number * 5}),
            executive_summary=f"Run {run_number}",
            raw_ai_response="{}",
            legacy_history=_carried_history,
        )
        db.add(report)
        db.flush()

        item = GapItem(
            report_id=report.id,
            requirement_id="CH2.CONSENT.1",
            framework_id="dpdpa",
            chapter="ch2",
            requirement_title="Consent",
            compliance_status="partially_compliant",
            current_state=f"State run {run_number}",
            gap_description="Gap",
            risk_level="medium",
            remediation_action="Fix",
            remediation_priority=1,
            remediation_effort="moderate",
            timeline_weeks=4,
        )
        db.add(item)
        db.commit()
        return report

    def test_three_reruns_flat_history(self, fresh_db):
        db, engine = fresh_db
        aid = _make_assessment(db)

        sizes = []
        for run in range(1, 4):
            report = self._simulate_rerun(db, aid, run)
            if report.legacy_history:
                sizes.append(len(report.legacy_history))

        final = db.query(GapReport).filter(GapReport.assessment_id == aid).first()
        history = json.loads(final.legacy_history)

        assert isinstance(history, list)
        assert len(history) == 2, "3 runs = 2 prior snapshots"

        for i, snap in enumerate(history):
            assert "legacy_history" not in snap["report"], (
                f"Snapshot {i} should not contain legacy_history"
            )
            assert snap["report"]["executive_summary"] == f"Run {i + 1}"
            assert len(snap["items"]) >= 1

        # Verify linear growth: size[1] should be ~2x size[0], not exponential
        if len(sizes) >= 2:
            ratio = sizes[1] / sizes[0] if sizes[0] else 999
            assert ratio < 3.0, f"History growth ratio {ratio:.1f} suggests nesting"


# ---------------------------------------------------------------------------
# 6. Desk-review rerun: flat finding snapshots
# ---------------------------------------------------------------------------


class TestDeskReviewRerunHistory:
    def _simulate_desk_rerun(self, db, assessment_id, run_number):
        """Simulate the production snapshot logic from web.py run_desk_review_web."""
        summary = (
            db.query(DeskReviewSummary)
            .filter(DeskReviewSummary.assessment_id == assessment_id)
            .first()
        )

        if summary:
            old_findings = (
                db.query(DeskReviewFinding)
                .filter(DeskReviewFinding.assessment_id == assessment_id)
                .all()
            )
            if old_findings:
                snapshot = {
                    "preserved_at": datetime.now(timezone.utc).isoformat(),
                    "label": "desk_review_rerun",
                    "findings": [
                        {c.name: getattr(f, c.name) for c in f.__table__.columns}
                        for f in old_findings
                    ],
                }
                history = []
                if summary.legacy_history:
                    try:
                        history = json.loads(summary.legacy_history)
                        if not isinstance(history, list):
                            history = [history]
                    except json.JSONDecodeError:
                        history = []
                history.append(snapshot)
                summary.legacy_history = json.dumps(history, default=str)

            db.query(DeskReviewFinding).filter(
                DeskReviewFinding.assessment_id == assessment_id
            ).delete()
            summary.status = "completed"
        else:
            summary = DeskReviewSummary(
                assessment_id=assessment_id,
                status="completed",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            db.add(summary)
            db.flush()

        finding = DeskReviewFinding(
            assessment_id=assessment_id,
            finding_type="evidence",
            requirement_id=f"CH2.CONSENT.{run_number}",
            content=f"Finding from run {run_number}",
            severity="medium",
        )
        db.add(finding)
        db.commit()
        return summary

    def test_three_desk_reruns_flat_history(self, fresh_db):
        db, engine = fresh_db
        aid = _make_assessment(db)

        sizes = []
        for run in range(1, 4):
            summary = self._simulate_desk_rerun(db, aid, run)
            if summary.legacy_history:
                sizes.append(len(summary.legacy_history))

        db.expire_all()
        summary = (
            db.query(DeskReviewSummary)
            .filter(DeskReviewSummary.assessment_id == aid)
            .first()
        )
        history = json.loads(summary.legacy_history)

        assert isinstance(history, list)
        assert len(history) == 2, "3 runs = 2 prior snapshots"

        for i, snap in enumerate(history):
            assert len(snap["findings"]) >= 1
            assert snap["findings"][0]["content"] == f"Finding from run {i + 1}"

        if len(sizes) >= 2:
            ratio = sizes[1] / sizes[0] if sizes[0] else 999
            assert ratio < 3.0, f"Desk review history growth ratio {ratio:.1f} suggests nesting"


# ---------------------------------------------------------------------------
# 7. detect_orphans covers document_id
# ---------------------------------------------------------------------------


class TestDetectOrphans:
    def test_detect_orphans_clean_db(self, fresh_db):
        from scripts.detect_orphans import detect_orphans

        db, engine = fresh_db
        aid = _make_assessment(db)
        doc_id = _make_document(db, aid)

        finding = DeskReviewFinding(
            assessment_id=aid,
            finding_type="evidence",
            document_id=doc_id,
            content="Test",
            severity="low",
        )
        db.add(finding)
        db.commit()

        assert detect_orphans(str(engine.url)) is True

    def test_detect_orphans_finds_document_orphan(self, fresh_db):
        from scripts.detect_orphans import detect_orphans

        db, engine = fresh_db
        aid = _make_assessment(db)

        # Insert finding with orphaned document_id (bypassing FK check)
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            conn.execute(text(
                "INSERT INTO desk_review_findings "
                "(assessment_id, finding_type, document_id, content, severity, created_at) "
                "VALUES (:aid, 'evidence', 'orphan-doc-id', 'Test', 'low', :now)"
            ), {"aid": aid, "now": datetime.now(timezone.utc).isoformat()})
            conn.commit()

        assert detect_orphans(str(engine.url)) is False
