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
from sqlalchemy import create_engine, event, inspect, text
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
    """Fresh database created via the real Alembic `upgrade head` command
    path — the same path app.main's startup and production both use — not
    `Base.metadata.create_all()`. This exercises the frozen baseline +
    retrofit revisions themselves rather than a live re-derivation of the
    ORM models, so a drift between the two (see
    TestAlembicContractParity below) is caught instead of silently masked.
    """
    engine = _fresh_engine(tmp_path)
    _alembic_upgrade(engine)
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

    def test_orphan_blocks_before_any_destructive_write(self, tmp_path):
        """The FK orphan preflight must run — and abort — before
        run_column_migrations touches anything: no gap_items ai_*
        backfill, and the retrofit revision (6fcd9e575309) must not be
        recorded as applied."""
        engine = _fresh_engine(tmp_path, "orphan_precheck.db")
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        _insert_legacy_data(cursor, now_str)
        # Orphan: gap_report referencing a nonexistent assessment.
        cursor.execute(
            "INSERT INTO gap_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("orphan-r2", "nonexistent-a", 0.0, "{}", "", "{}", None, None, now_str),
        )
        raw.commit()
        cursor.close()
        raw.close()

        with pytest.raises(RuntimeError, match="FK migration blocked"):
            _alembic_upgrade(engine)

        with engine.connect() as conn:
            # _insert_legacy_data's gap_item ("g1") is inserted without
            # ai_compliance_status, so it's NULL unless run_column_migrations'
            # backfill (UPDATE ... WHERE ai_compliance_status IS NULL) ran.
            ai_status = conn.execute(
                text("SELECT ai_compliance_status FROM gap_items WHERE id = 'g1'")
            ).scalar()
            assert ai_status is None, (
                "gap_items ai_* backfill ran despite the FK preflight failing first"
            )

            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            assert version != "6fcd9e575309", (
                "retrofit revision must not be recorded as applied when it aborted"
            )

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

            violations = conn.execute(text("PRAGMA foreign_key_check")).fetchall()
            assert violations == [], (
                f"database must pass a full FK integrity check after the SET NULL "
                f"cleanup, found: {violations}"
            )

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


# ---------------------------------------------------------------------------
# PR #16 remediation: automate the Alembic verification the plan requires
# (docs/plans/2026-09-21-002-revised-implementation-plan.md:312-317) instead
# of relying on a manual one-off check. Covers: (a) a fresh Alembic-built
# database's tables/columns/FKs/indexes match the ORM's own declared
# contract (modulo the few known, documented differences), and (b) the
# exact upgrade -> downgrade -1 -> upgrade round trip.
# ---------------------------------------------------------------------------


def _schema_snapshot(engine):
    """{table: {"columns": {name}, "fks": {(col, target_table, target_col)},
    "indexes": {name}}} for every non-Alembic-internal table."""
    insp = inspect(engine)
    snapshot = {}
    for table in insp.get_table_names():
        if table == "alembic_version":
            continue
        snapshot[table] = {
            "columns": {c["name"] for c in insp.get_columns(table)},
            "fks": {
                (fk["constrained_columns"][0], fk["referred_table"], fk["referred_columns"][0])
                for fk in insp.get_foreign_keys(table)
            },
            "indexes": {i["name"] for i in insp.get_indexes(table)},
        }
    return snapshot


class TestAlembicContractParity:
    """Fresh-vs-frozen-contract diff: a database built by the real Alembic
    `upgrade head` path must match a database built by
    `Base.metadata.create_all()` (the ORM's own declared target schema),
    except for documented, intentional differences."""

    # Legacy-compatibility artifact: created unconditionally by every
    # upgrade (app.legacy_migrations.run_column_migrations, also declared
    # in the baseline revision — see alembic/versions/6fc718bb9f09), but
    # not represented in the ORM models, so create_all() never produces it.
    _KNOWN_ALEMBIC_ONLY_INDEXES = {"gap_items": {"ix_gap_items_null_framework_id"}}

    def test_tables_columns_fks_indexes_match_orm_metadata(self, tmp_path):
        alembic_engine = _fresh_engine(tmp_path, "alembic_contract.db")
        _alembic_upgrade(alembic_engine)

        orm_engine = _fresh_engine(tmp_path, "orm_contract.db")
        Base.metadata.create_all(orm_engine)

        alembic_schema = _schema_snapshot(alembic_engine)
        orm_schema = _schema_snapshot(orm_engine)

        assert set(alembic_schema) == set(orm_schema), (
            f"table set mismatch: alembic-only={set(alembic_schema) - set(orm_schema)}, "
            f"orm-only={set(orm_schema) - set(alembic_schema)}"
        )

        for table, orm_contract in orm_schema.items():
            alembic_contract = alembic_schema[table]
            assert alembic_contract["columns"] == orm_contract["columns"], (
                f"{table} column mismatch: "
                f"alembic-only={alembic_contract['columns'] - orm_contract['columns']}, "
                f"orm-only={orm_contract['columns'] - alembic_contract['columns']}"
            )
            assert alembic_contract["fks"] == orm_contract["fks"], (
                f"{table} FK mismatch: alembic={alembic_contract['fks']}, orm={orm_contract['fks']}"
            )

            known_extra = self._KNOWN_ALEMBIC_ONLY_INDEXES.get(table, set())
            assert alembic_contract["indexes"] - orm_contract["indexes"] == known_extra, (
                f"{table} has undocumented Alembic-only indexes: "
                f"{alembic_contract['indexes'] - orm_contract['indexes'] - known_extra}"
            )
            assert orm_contract["indexes"] - alembic_contract["indexes"] == set(), (
                f"{table} is missing ORM-declared indexes: "
                f"{orm_contract['indexes'] - alembic_contract['indexes']}"
            )

        alembic_engine.dispose()
        orm_engine.dispose()


class TestAlembicRoundTrip:
    """`upgrade head -> downgrade -1 -> upgrade head` against a fresh,
    isolated SQLite database, using Alembic's own command path with an
    isolated `sqlalchemy.url` (never data/dpdpa.db)."""

    def test_fresh_upgrade_downgrade_upgrade_round_trip(self, tmp_path):
        db_path = tmp_path / "roundtrip.db"
        alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

        command.upgrade(alembic_cfg, "head")

        engine = create_engine(f"sqlite:///{db_path}")
        schema_before = _schema_snapshot(engine)
        engine.dispose()

        command.downgrade(alembic_cfg, "-1")
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(f"sqlite:///{db_path}")
        try:
            with engine.connect() as conn:
                current = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            assert current == "6fcd9e575309"

            schema_after = _schema_snapshot(engine)
            assert schema_after == schema_before, (
                "full schema contract must match exactly before and after the "
                "downgrade -1 -> upgrade head round trip, not just spot checks: "
                f"before={schema_before}, after={schema_after}"
            )
            assert "gap_items" in schema_after
            assert "framework_id" in schema_after["gap_items"]["columns"]
            assert ("assessment_id", "assessments", "id") in schema_after["assessment_documents"]["fks"]
        finally:
            engine.dispose()


class TestAdoptedDatabaseDowngradePolicy:
    """P2: downgrading a database that already holds data (including one
    adopted from before Alembic) must refuse rather than silently drop it.
    Downgrading an empty database (e.g. a throwaway test fixture) is still
    allowed so the round-trip test above keeps working."""

    def test_downgrade_refuses_when_data_present(self, tmp_path):
        db_path = tmp_path / "adopted.db"
        alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

        command.upgrade(alembic_cfg, "head")

        engine = create_engine(f"sqlite:///{db_path}")
        aid = _make_assessment(sessionmaker(bind=engine)())
        engine.dispose()

        with pytest.raises(RuntimeError, match="Refusing to downgrade"):
            command.downgrade(alembic_cfg, "base")

        # Data must survive the refused downgrade untouched: the retrofit
        # revision's own downgrade() is a genuine no-op (it never touches
        # application tables), so Alembic may legitimately record it as
        # rolled back to 6fc718bb9f09 before the *baseline* revision's
        # downgrade raises and aborts -- no table is ever dropped either
        # way. Re-running upgrade head must cleanly recover to head.
        engine = create_engine(f"sqlite:///{db_path}")
        try:
            with engine.connect() as conn:
                assert conn.execute(text("SELECT COUNT(*) FROM assessments")).scalar() == 1
                version_after_refusal = conn.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar()
            assert version_after_refusal in {"6fcd9e575309", "6fc718bb9f09"}, (
                "no application table should ever be dropped by a refused "
                f"downgrade, regardless of which step recorded {version_after_refusal!r}"
            )
        finally:
            engine.dispose()

        command.upgrade(alembic_cfg, "head")
        engine = create_engine(f"sqlite:///{db_path}")
        try:
            with engine.connect() as conn:
                assert conn.execute(text("SELECT COUNT(*) FROM assessments")).scalar() == 1
                assert conn.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar() == "6fcd9e575309"
        finally:
            engine.dispose()

    def test_downgrade_allowed_when_empty(self, tmp_path):
        db_path = tmp_path / "empty.db"
        alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

        command.upgrade(alembic_cfg, "head")
        command.downgrade(alembic_cfg, "base")  # must not raise

        engine = create_engine(f"sqlite:///{db_path}")
        try:
            tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
            assert tables == set(), f"expected all application tables dropped, found {tables}"
        finally:
            engine.dispose()


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


# ---------------------------------------------------------------------------
# PR #16 final remediation: two confirmed blockers from the adversarial
# review (see tasks/handoffs/2026-09-22-pr16-final-migration-closure.md).
#
# P1a: the orphan preflight only scanned tables slated for an FK rebuild,
# so an already-FK'd table's non-SET-NULL orphan could slip through while
# a different table's rebuild committed -- and a retry with nothing left
# to rebuild never re-verified anything, so it could stamp head over the
# still-present orphan.
#
# P1b: the legacy gap_items rebuild dropped the ad-hoc partial index
# `ix_gap_items_null_framework_id` (created by run_column_migrations
# before the rebuild) because FROZEN_TABLES["gap_items"] never declared
# it, which also broke the empty-adopted-database downgrade path (its
# `DROP INDEX` had nothing to drop).
# ---------------------------------------------------------------------------


def _make_fk_declared_gap_reports(cursor):
    """Replace `_create_legacy_schema`'s FK-less gap_reports with a variant
    that already declares its intended FK -- so
    `compute_fk_tables_to_rebuild` will NOT select it for rebuild -- while
    still allowing an orphan row to be inserted with FK enforcement off."""
    cursor.execute("DROP TABLE gap_reports")
    cursor.execute("""
        CREATE TABLE gap_reports (
            id VARCHAR(36) NOT NULL PRIMARY KEY,
            assessment_id VARCHAR(36) NOT NULL,
            overall_score FLOAT NOT NULL,
            chapter_scores TEXT NOT NULL,
            executive_summary TEXT NOT NULL,
            raw_ai_response TEXT NOT NULL,
            framework_scores TEXT,
            legacy_history TEXT,
            generated_at DATETIME NOT NULL,
            FOREIGN KEY(assessment_id) REFERENCES assessments (id)
        )
    """)
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_gap_reports_assessment_id "
        "ON gap_reports (assessment_id)"
    )


class TestLegacyGapItemsPartialIndexPreserved:
    """P1b: `ix_gap_items_null_framework_id` must survive a genuine legacy
    `upgrade head` that rebuilds gap_items for FK enforcement."""

    def test_partial_index_survives_legacy_rebuild(self, tmp_path):
        engine = _fresh_engine(tmp_path, "gap_items_index.db")
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)  # no FKs -> forces a gap_items rebuild
        _insert_legacy_data(cursor, now_str)
        raw.commit()
        cursor.close()
        raw.close()

        _alembic_upgrade(engine)

        with engine.connect() as conn:
            indexes = inspect(conn).get_indexes("gap_items")
            partial = next(
                (i for i in indexes if i["name"] == "ix_gap_items_null_framework_id"), None
            )
            assert partial is not None, (
                "ix_gap_items_null_framework_id must survive the legacy FK rebuild"
            )
            assert partial["column_names"] == ["id"]

            # Assert the WHERE predicate itself, not just the index's presence
            # -- a same-named index with no predicate would pass a name check.
            index_sql = conn.execute(
                text(
                    "SELECT sql FROM sqlite_master WHERE type='index' "
                    "AND name='ix_gap_items_null_framework_id'"
                )
            ).scalar()
            assert index_sql is not None
            assert "framework_id IS NULL" in index_sql

        engine.dispose()


class TestMixedLegacyOrphanState:
    """P1a: the preflight must scan every FK_SPEC table for orphans, not
    only the ones selected for rebuild. gap_reports here already has its
    FK declared (so it's excluded from the rebuild list) but carries an
    orphan; gap_items has no FK (so it IS selected for rebuild). The
    orphan on gap_reports must still block the migration before gap_items
    is touched."""

    def _build_mixed_state_db(self, tmp_path, name):
        engine = _fresh_engine(tmp_path, name)
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        _make_fk_declared_gap_reports(cursor)
        _insert_legacy_data(cursor, now_str)
        cursor.execute(
            "INSERT INTO gap_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("orphan-r", "nonexistent-a", 0.0, "{}", "", "{}", None, None, now_str),
        )
        raw.commit()
        cursor.close()
        raw.close()
        return engine

    def test_first_upgrade_aborts_before_any_write(self, tmp_path):
        engine = self._build_mixed_state_db(tmp_path, "mixed_orphan.db")

        with engine.connect() as conn:
            # Sanity: gap_reports already has its FK (excluded from the
            # rebuild list); gap_items does not (included).
            assert len(conn.execute(text("PRAGMA foreign_key_list(gap_reports)")).fetchall()) == 1
            assert len(conn.execute(text("PRAGMA foreign_key_list(gap_items)")).fetchall()) == 0

        with pytest.raises(RuntimeError, match="FK migration blocked"):
            _alembic_upgrade(engine)

        with engine.connect() as conn:
            # gap_items must still be untouched: no FK added, no ai_*
            # backfill (part of run_column_migrations, which must run
            # strictly after the preflight completes).
            assert len(conn.execute(text("PRAGMA foreign_key_list(gap_items)")).fetchall()) == 0
            ai_status = conn.execute(
                text("SELECT ai_compliance_status FROM gap_items WHERE id = 'g1'")
            ).scalar()
            assert ai_status is None, (
                "run_column_migrations must not have run before the mixed-state "
                "preflight aborted"
            )

            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            assert version != "6fcd9e575309", (
                "retrofit revision must not be recorded as applied when it aborted"
            )

        engine.dispose()

    def test_retry_without_repair_still_fails_and_never_stamps_head(self, tmp_path):
        engine = self._build_mixed_state_db(tmp_path, "mixed_orphan_retry.db")

        with pytest.raises(RuntimeError, match="FK migration blocked"):
            _alembic_upgrade(engine)
        with pytest.raises(RuntimeError, match="FK migration blocked"):
            _alembic_upgrade(engine)

        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            assert version != "6fcd9e575309", (
                "a retry with the orphan still present must never record the "
                "retrofit revision as applied"
            )
        engine.dispose()


class TestApplyFkRebuildAlwaysVerifiesIntegrity:
    """P1a (defense in depth): `apply_fk_rebuild` itself must always run
    `PRAGMA foreign_key_check`, even when `tables_to_rebuild` is empty --
    not just rely on the preflight to have caught every case first. This
    calls `apply_fk_rebuild` directly (bypassing `preflight_fk_orphans`) to
    prove the integrity check is unconditional at that layer too."""

    def test_empty_rebuild_list_still_raises_on_existing_violation(self, tmp_path):
        from app.legacy_migrations import apply_fk_rebuild
        from app.legacy_migrations_schema import FROZEN_TABLES

        engine = _fresh_engine(tmp_path, "already_fkd_with_orphan.db")
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        _make_fk_declared_gap_reports(cursor)
        _insert_legacy_data(cursor, now_str)
        cursor.execute(
            "INSERT INTO gap_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("orphan-r", "nonexistent-a", 0.0, "{}", "", "{}", None, None, now_str),
        )
        raw.commit()
        cursor.close()
        raw.close()

        with pytest.raises(RuntimeError, match="Foreign key violations"):
            apply_fk_rebuild(engine, [], FROZEN_TABLES)


class TestEmptyAdoptedLegacyDowngrade:
    """Matrix item 7: an empty, adopted, genuinely-legacy database (no FKs,
    no data) still requires a gap_items rebuild on upgrade. That rebuild
    must not leave the database unable to downgrade to base -- the P1b bug
    this handoff fixes -- and a data-bearing equivalent must still refuse
    before any table drop, then recover to head cleanly."""

    def test_upgrade_then_downgrade_base_leaves_no_tables(self, tmp_path):
        db_path = tmp_path / "empty_legacy.db"
        engine = _fresh_engine(tmp_path, "empty_legacy.db")

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)  # no data inserted -> stays empty
        raw.commit()
        cursor.close()
        raw.close()
        engine.dispose()

        alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

        command.upgrade(alembic_cfg, "head")

        with create_engine(f"sqlite:///{db_path}").connect() as conn:
            fks = conn.execute(text("PRAGMA foreign_key_list(gap_items)")).fetchall()
            assert len(fks) == 1, "legacy gap_items should have been FK-rebuilt"

        command.downgrade(alembic_cfg, "base")  # must not raise "no such index"

        engine = create_engine(f"sqlite:///{db_path}")
        try:
            tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
            assert tables == set(), f"expected all application tables dropped, found {tables}"
        finally:
            engine.dispose()

    def test_data_bearing_adopted_db_refuses_then_recovers_to_head(self, tmp_path):
        db_path = tmp_path / "data_bearing_legacy.db"
        engine = _fresh_engine(tmp_path, "data_bearing_legacy.db")
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)
        _insert_legacy_data(cursor, now_str)
        raw.commit()
        cursor.close()
        raw.close()
        engine.dispose()

        alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

        command.upgrade(alembic_cfg, "head")

        with pytest.raises(RuntimeError, match="Refusing to downgrade"):
            command.downgrade(alembic_cfg, "base")

        engine = create_engine(f"sqlite:///{db_path}")
        try:
            with engine.connect() as conn:
                assert conn.execute(text("SELECT COUNT(*) FROM gap_items")).scalar() == 1
        finally:
            engine.dispose()

        command.upgrade(alembic_cfg, "head")  # clean recovery
        engine = create_engine(f"sqlite:///{db_path}")
        try:
            with engine.connect() as conn:
                assert conn.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar() == "6fcd9e575309"
                indexes = inspect(conn).get_indexes("gap_items")
                assert any(i["name"] == "ix_gap_items_null_framework_id" for i in indexes)
        finally:
            engine.dispose()


# ---------------------------------------------------------------------------
# Adversarial re-review finding: rebuilding a parent table can corrupt an
# already-FK'd child table's FK metadata.
#
# `_rebuild_table_for_fks` renames the table being rebuilt to
# `_{table_name}_pre_fk`, recreates it under its original name, then drops
# the renamed copy. SQLite's default `ALTER TABLE ... RENAME` behavior
# (`legacy_alter_table=OFF`) rewrites the FK clause of every OTHER table
# that references the renamed table to point at its new (temporary) name.
# A sibling table that already has its correct FK to the table being
# rebuilt -- so it is NOT itself in `tables_to_rebuild` -- had its FK
# silently rewritten to reference `_{table_name}_pre_fk`; once that
# temp table was dropped, the sibling was left with a dangling FK the
# moment the (non-transactional, SQLite DDL) transaction committed. The
# fix wraps the rebuild in `PRAGMA legacy_alter_table=ON`, which disables
# that cross-table FK rewrite.
# ---------------------------------------------------------------------------


class TestParentRebuildDoesNotCorruptSiblingFks:
    """A parent table needing an FK rebuild (assessment_documents, or
    gap_reports) must not corrupt the FK metadata of a sibling table that
    already has its correct FK declared (desk_review_findings, or
    gap_items/initiatives) and is therefore excluded from the rebuild."""

    def test_assessment_documents_rebuild_preserves_desk_review_findings_fk(self, tmp_path):
        engine = _fresh_engine(tmp_path, "parent_child_docs.db")
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)  # assessment_documents has no FK -> rebuilt

        # desk_review_findings ALREADY has its correct FKs (assessment_id,
        # and document_id -> assessment_documents ON DELETE SET NULL) -- so
        # it is excluded from tables_to_rebuild, but assessment_documents
        # (its parent) is rebuilt this run.
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
                FOREIGN KEY(document_id) REFERENCES assessment_documents (id) ON DELETE SET NULL
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

        # Sanity: assessment_documents needs rebuild, desk_review_findings does not.
        with engine.connect() as conn:
            assert len(conn.execute(text("PRAGMA foreign_key_list(assessment_documents)")).fetchall()) == 0
            assert len(conn.execute(text("PRAGMA foreign_key_list(desk_review_findings)")).fetchall()) == 2

        _alembic_upgrade(engine)  # must succeed on the FIRST attempt, not just a retry

        with engine.connect() as conn:
            fks = conn.execute(text("PRAGMA foreign_key_list(desk_review_findings)")).fetchall()
            doc_fk = next(r for r in fks if r[3] == "document_id")
            assert doc_fk[2] == "assessment_documents", (
                "desk_review_findings.document_id must still reference "
                f"assessment_documents, not a rebuild temp table: {doc_fk}"
            )
            assert doc_fk[6] == "SET NULL"

            violations = conn.execute(text("PRAGMA foreign_key_check")).fetchall()
            assert violations == [], f"no dangling FKs after the rebuild, found: {violations}"

            assert conn.execute(text("SELECT COUNT(*) FROM desk_review_findings")).scalar() == 1

        engine.dispose()

    def test_gap_reports_rebuild_preserves_gap_items_and_initiatives_fks(self, tmp_path):
        engine = _fresh_engine(tmp_path, "parent_child_reports.db")
        now_str = datetime.now(timezone.utc).isoformat()

        raw = engine.raw_connection()
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        _create_legacy_schema(cursor)  # gap_reports has no FK -> rebuilt

        # gap_items and initiatives ALREADY have their correct FK to
        # gap_reports -- excluded from tables_to_rebuild -- while gap_reports
        # (their parent) is rebuilt this run.
        cursor.execute("DROP TABLE gap_items")
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
                reviewed_at DATETIME,
                FOREIGN KEY(report_id) REFERENCES gap_reports (id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_gap_items_report_id ON gap_items (report_id)")

        cursor.execute("DROP TABLE initiatives")
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
                suggested_approach TEXT NOT NULL,
                FOREIGN KEY(report_id) REFERENCES gap_reports (id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_initiatives_report_id ON initiatives (report_id)")

        _insert_legacy_data(cursor, now_str)
        raw.commit()
        cursor.close()
        raw.close()

        with engine.connect() as conn:
            assert len(conn.execute(text("PRAGMA foreign_key_list(gap_reports)")).fetchall()) == 0
            assert len(conn.execute(text("PRAGMA foreign_key_list(gap_items)")).fetchall()) == 1
            assert len(conn.execute(text("PRAGMA foreign_key_list(initiatives)")).fetchall()) == 1

        _alembic_upgrade(engine)  # must succeed on the FIRST attempt

        with engine.connect() as conn:
            for table in ("gap_items", "initiatives"):
                fks = conn.execute(text(f"PRAGMA foreign_key_list({table})")).fetchall()
                assert len(fks) == 1
                assert fks[0][2] == "gap_reports", (
                    f"{table}.report_id must still reference gap_reports, not a "
                    f"rebuild temp table: {fks[0]}"
                )

            violations = conn.execute(text("PRAGMA foreign_key_check")).fetchall()
            assert violations == [], f"no dangling FKs after the rebuild, found: {violations}"

            assert conn.execute(text("SELECT COUNT(*) FROM gap_items")).scalar() == 1

        engine.dispose()
