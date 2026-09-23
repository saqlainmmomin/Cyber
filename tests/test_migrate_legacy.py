"""TDD ("red") suite for P1-3, the one-shot legacy-data migration script.

These tests are written before the implementation. They pin down the interface
Codex must implement in ``scripts/migrate_legacy.py`` and
``scripts/rollback_legacy.py``:

``scripts.migrate_legacy``
    ``MigrationStats``
        ``@dataclass`` with int counts: ``clients``, ``engagements``,
        ``assessment_packs``, ``conclusions``, ``conclusion_revisions``,
        ``findings``, ``actions`` (plus ``warnings: list[str]`` and a ``total``
        property). Counts are rows *created by this call* — a second, idempotent
        run returns all zeros.
    ``run_migration(session: Session) -> MigrationStats``
        Migrates every legacy row reachable from ``session`` and commits.
    ``main(argv: list[str] | None = None) -> int``
        CLI. Calls ``scripts.backup.create_backup(db_path, upload_dir, out_dir)``
        before any write unless ``--skip-backup`` (hidden, test-only) is passed;
        returns non-zero without writing if the backup raises. Flags:
        ``--db-url``, ``--upload-dir``, ``--backup-out-dir``, ``--skip-backup``.
    ``OUTCOME_MAP``, ``UNKNOWN_PACK_VERSION``, ``MIGRATION_ACTOR``
        Module constants referenced by these tests.

``scripts.rollback_legacy``
    ``main(argv: list[str] | None = None) -> int``
        Wraps ``scripts.restore.restore_backup(backup_dir, db_path, upload_dir,
        force=...)``. Flags: ``--backup-dir``, ``--db-url``, ``--upload-dir``,
        ``--force``.

Test-DB strategy: a real file-backed SQLite database built by ``alembic upgrade
head`` (same pattern as ``tests/test_target_schema.py``), with
``PRAGMA foreign_keys=ON`` enabled on every connection, so the P1-2 FK
constraints are genuinely enforced rather than mocked away.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, func, insert, select, text
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401 - register all ORM tables
from app.models.action import Action
from app.models.assessment import Assessment
from app.models.assessment_pack import AssessmentPack
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.finding import Finding
from app.models.report import GapItem, GapReport

import scripts.migrate_legacy as migrate_legacy
import scripts.rollback_legacy as rollback_legacy
from scripts.backup import create_backup
from scripts.migrate_legacy import MigrationStats, run_migration


REPO_ROOT = Path(__file__).resolve().parents[1]

#: Every new table this migration is allowed to write into, with the FK columns
#: whose targets must exist afterwards (scenario 3, orphan detection).
FK_CHECKS: tuple[tuple[str, str, str, str], ...] = (
    ("engagements", "client_id", "clients", "id"),
    ("assessments", "engagement_id", "engagements", "id"),
    ("assessment_packs", "assessment_id", "assessments", "id"),
    ("conclusions", "assessment_id", "assessments", "id"),
    ("conclusion_revisions", "conclusion_id", "conclusions", "id"),
    ("findings", "assessment_id", "assessments", "id"),
    ("findings", "conclusion_id", "conclusions", "id"),
    ("actions", "finding_id", "findings", "id"),
)

#: Tables Phase 2 owns — the migration must leave them empty.
PHASE_2_TABLES = ("evidence", "evidence_versions", "evidence_uses", "citations", "magic_links")

COUNTED_MODELS = {
    "clients": Client,
    "engagements": Engagement,
    "assessment_packs": AssessmentPack,
    "conclusions": Conclusion,
    "conclusion_revisions": ConclusionRevision,
    "findings": Finding,
    "actions": Action,
}


# --------------------------------------------------------------------------- #
# DB fixture: real sqlite file built through Alembic, FKs enforced
# --------------------------------------------------------------------------- #


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def _fresh_engine(db_path: Path):
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def _build_db(db_path: Path):
    command.upgrade(_alembic_config(db_path), "head")
    return _fresh_engine(db_path)


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    """``Assessment.selected_frameworks`` has a validator that rejects unknown
    framework ids, and the registry is only populated by ``app.main``'s startup
    hook. Seeding legacy rows therefore needs the catalog registered."""

    from app.main import _register_frameworks as register

    register()


@pytest.fixture()
def db(tmp_path):
    """Yield ``(session, engine, db_path)`` for an empty, current-schema DB."""

    db_path = tmp_path / "migrate-legacy.sqlite3"
    engine = _build_db(db_path)
    session = sessionmaker(bind=engine)()
    try:
        yield session, engine, db_path
    finally:
        session.close()
        engine.dispose()


# --------------------------------------------------------------------------- #
# Seed helpers — explicit, non-null values for every required column
# --------------------------------------------------------------------------- #


def _gap_item_kwargs(**overrides) -> dict:
    """Sane, fully non-null defaults for a legacy ``GapItem``.

    Defaults describe a reviewed-but-untouched item: ``remediation_status`` is
    ``None`` (never touched) and ``reviewed_at`` is ``None`` (never approved),
    so the base row produces one ``Conclusion``, one ``ConclusionRevision`` and
    no ``Finding``/``Action``. Override per scenario.
    """

    defaults = {
        "requirement_id": "DPDPA-5.1",
        "framework_id": "dpdpa",
        "cluster_id": "UCC-ACCESS-01",
        "control_reference": "S.5(1)",
        "chapter": "Chapter II",
        "requirement_title": "Notice to Data Principal",
        "compliance_status": "partially_compliant",
        "current_state": "A privacy notice exists but omits the grievance channel.",
        "gap_description": "Notice does not disclose the grievance officer contact.",
        "risk_level": "high",
        "remediation_action": "Publish an updated notice naming the grievance officer.",
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "policy",
        "evidence_quote": "See privacy-notice.pdf, section 3.",
        "evidence_confidence": "moderate",
        "remediation_status": None,
        "remediation_owner": None,
        "remediation_target_date": None,
        "remediation_notes": None,
        "remediation_closed_at": None,
        "review_status": "draft",
        "needs_review": False,
        "ai_compliance_status": "non_compliant",
        "ai_gap_description": "AI draft: no grievance officer named anywhere.",
        "ai_risk_level": "critical",
        "reviewer_notes": None,
        "reviewed_by": None,
        "reviewed_at": None,
    }
    defaults.update(overrides)
    return defaults


def _seed_legacy_assessment(
    session: Session,
    *,
    company_name: str,
    frameworks: list[str],
    gap_items: list[dict] | None = None,
    description: str | None = None,
    created_at: datetime | None = None,
    industry: str = "Technology",
    company_size: str = "medium",
    framework_scores: dict | None = None,
    legacy_history: list | None = None,
) -> Assessment:
    """Insert one legacy ``Assessment`` (+ optional ``GapReport`` and items).

    ``gap_items=None`` means "no GapReport at all" — the empty-assessment shape.
    ``gap_items=[]`` means a GapReport with zero items.
    """

    assessment = Assessment(
        company_name=company_name,
        industry=industry,
        company_size=company_size,
        description=description,
        status="completed",
        selected_frameworks=json.dumps(frameworks),
        created_at=created_at or datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
    )
    session.add(assessment)
    session.flush()

    if gap_items is not None:
        scores = framework_scores if framework_scores is not None else {
            fw: {"score": 61.5, "maturity": 2, "requirement_count": len(gap_items)}
            for fw in frameworks
        }
        report = GapReport(
            assessment_id=assessment.id,
            overall_score=61.5,
            chapter_scores=json.dumps({"Chapter II": 60.0}),
            executive_summary=f"Summary for {company_name}.",
            raw_ai_response=json.dumps({"items": len(gap_items)}),
            framework_scores=json.dumps(scores, sort_keys=True),
            legacy_history=json.dumps(legacy_history if legacy_history is not None else []),
        )
        session.add(report)
        session.flush()
        for item_kwargs in gap_items:
            # Use a Core insert, not the ORM constructor: GapItem.remediation_status
            # has a Python-side ``default="open"``, which SQLAlchemy applies even
            # when the caller explicitly passes ``remediation_status=None`` to the
            # mapped class's __init__ (the default fires whenever the resolved
            # value is None, not only when the attribute was left unset). A Core
            # insert bypasses that default, so an explicit None here is genuinely
            # persisted as NULL — matching a real legacy row that was never
            # touched, as opposed to one explicitly reopened with status "open".
            session.execute(insert(GapItem).values(report_id=report.id, **item_kwargs))

    session.commit()
    return assessment


def _seed_three_assessment_fixture(session: Session) -> dict[str, Assessment]:
    """The plan's canonical fixture: single-framework, multi-framework, empty.

    Returns ``{"single": ..., "multi": ..., "empty": ...}``.
    """

    single = _seed_legacy_assessment(
        session,
        company_name="Acme Health Pvt Ltd",
        frameworks=["dpdpa"],
        description="DPDPA gap assessment FY26",
        created_at=datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc),
        gap_items=[
            _gap_item_kwargs(requirement_id="DPDPA-5.1"),
            _gap_item_kwargs(
                requirement_id="DPDPA-6.1",
                compliance_status="not_assessed",
                requirement_title="Consent Manager Registration",
            ),
            _gap_item_kwargs(
                requirement_id="DPDPA-8.5",
                compliance_status="non_compliant",
                requirement_title="Breach Notification",
                remediation_status="in_progress",
                remediation_owner="ciso@acme.example",
                remediation_target_date=datetime(2026, 6, 30, 0, 0),
                remediation_notes="Vendor selection underway.",
                reviewed_by="consultant@cyberassess.example",
                reviewed_at=datetime(2026, 2, 1, 10, 30, tzinfo=timezone.utc),
                review_status="approved",
            ),
        ],
    )

    multi = _seed_legacy_assessment(
        session,
        company_name="Globex Manufacturing",
        frameworks=["dpdpa", "iso27001"],
        description=None,
        created_at=datetime(2026, 2, 20, 14, 0, tzinfo=timezone.utc),
        industry="Manufacturing",
        company_size="large",
        gap_items=[
            _gap_item_kwargs(
                requirement_id="ISO-A.5.1",
                framework_id="iso27001",
                cluster_id="UCC-POLICY-01",
                requirement_title="Policies for Information Security",
                compliance_status="compliant",
                evidence_quote=None,
                remediation_status="open",
            ),
            _gap_item_kwargs(
                requirement_id="DPDPA-9.1",
                compliance_status="not_applicable",
                requirement_title="Children's Data",
                remediation_status="closed",
                remediation_closed_at=datetime(2026, 3, 5, 8, 0, tzinfo=timezone.utc),
                remediation_owner="dpo@globex.example",
            ),
        ],
    )

    empty = _seed_legacy_assessment(
        session,
        company_name="Initech Services",
        frameworks=["dpdpa"],
        description=None,
        created_at=datetime(2026, 3, 10, 11, 0, tzinfo=timezone.utc),
        gap_items=None,
    )

    return {"single": single, "multi": multi, "empty": empty}


# --------------------------------------------------------------------------- #
# Query helpers
# --------------------------------------------------------------------------- #


def _count(session: Session, model) -> int:
    return session.execute(select(func.count()).select_from(model)).scalar_one()


def _snapshot_counts(session: Session) -> dict[str, int]:
    return {name: _count(session, model) for name, model in COUNTED_MODELS.items()}


def _client_for_assessment(session: Session, assessment: Assessment) -> Client:
    """Walk assessment -> engagement -> client with explicit queries.

    This codebase declares no SQLAlchemy ``relationship()`` attributes, so there
    is no ``.engagement`` / ``.client`` to navigate.
    """

    assert assessment.engagement_id is not None, (
        f"assessment {assessment.id} was not linked to an engagement"
    )
    engagement = session.get(Engagement, assessment.engagement_id)
    assert engagement is not None
    client = session.get(Client, engagement.client_id)
    assert client is not None
    return client


def _gap_items_for(session: Session, assessment: Assessment) -> list[GapItem]:
    report = session.execute(
        select(GapReport).where(GapReport.assessment_id == assessment.id)
    ).scalar_one_or_none()
    if report is None:
        return []
    return list(
        session.execute(select(GapItem).where(GapItem.report_id == report.id)).scalars()
    )


def _orphan_rows(session: Session) -> list[str]:
    problems: list[str] = []
    for child, child_col, parent, parent_col in FK_CHECKS:
        rows = session.execute(
            text(
                f"SELECT COUNT(*) FROM {child} c "
                f"LEFT JOIN {parent} p ON c.{child_col} = p.{parent_col} "
                f"WHERE c.{child_col} IS NOT NULL AND p.{parent_col} IS NULL"
            )
        ).scalar_one()
        if rows:
            problems.append(f"{child}.{child_col} -> {parent}.{parent_col}: {rows} orphans")
    return problems


def _framework_scores_by_assessment(session: Session) -> dict[str, str | None]:
    return {
        row.assessment_id: row.framework_scores
        for row in session.execute(select(GapReport)).scalars()
    }


# --------------------------------------------------------------------------- #
# Scenario 1 — client.name == assessment.company_name for every migrated row
# --------------------------------------------------------------------------- #


def test_client_name_matches_assessment_company_name(db):
    session, _engine, _db_path = db
    seeded = _seed_three_assessment_fixture(session)

    run_migration(session)
    session.expire_all()

    for assessment in seeded.values():
        session.refresh(assessment)
        client = _client_for_assessment(session, assessment)
        assert client.name == assessment.company_name

    # One Client per distinct company_name, one Engagement per Assessment.
    assert _count(session, Client) == 3
    assert _count(session, Engagement) == 3


def test_same_company_name_shares_client_but_not_engagement(db):
    session, _engine, _db_path = db
    first = _seed_legacy_assessment(
        session,
        company_name="Duplicate Co",
        frameworks=["dpdpa"],
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        gap_items=[_gap_item_kwargs()],
    )
    second = _seed_legacy_assessment(
        session,
        company_name="Duplicate Co",
        frameworks=["dpdpa"],
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        gap_items=[_gap_item_kwargs(requirement_id="DPDPA-7.1")],
    )

    run_migration(session)
    session.expire_all()
    session.refresh(first)
    session.refresh(second)

    assert _count(session, Client) == 1, "same company_name must reuse one Client"
    assert _count(session, Engagement) == 2, "one Engagement per Assessment, always"
    assert first.engagement_id != second.engagement_id
    assert (
        _client_for_assessment(session, first).id
        == _client_for_assessment(session, second).id
    )


# --------------------------------------------------------------------------- #
# Scenario 2 — Conclusion count == GapItem count
# --------------------------------------------------------------------------- #


def test_conclusion_count_matches_gap_item_count(db):
    session, _engine, _db_path = db
    seeded = _seed_three_assessment_fixture(session)
    total_items = _count(session, GapItem)

    stats = run_migration(session)
    session.expire_all()

    assert isinstance(stats, MigrationStats)
    assert stats.conclusions == total_items
    assert _count(session, Conclusion) == total_items

    for assessment in seeded.values():
        expected = len(_gap_items_for(session, assessment))
        actual = session.execute(
            select(func.count())
            .select_from(Conclusion)
            .where(Conclusion.assessment_id == assessment.id)
        ).scalar_one()
        assert actual == expected, f"{assessment.company_name}: {actual} != {expected}"


def test_conclusion_fields_copy_from_gap_item(db):
    session, _engine, _db_path = db
    assessment = _seed_legacy_assessment(
        session,
        company_name="Field Mapping Co",
        frameworks=["dpdpa"],
        gap_items=[_gap_item_kwargs()],
    )
    item = _gap_items_for(session, assessment)[0]

    run_migration(session)
    session.expire_all()

    conclusion = session.execute(
        select(Conclusion).where(Conclusion.assessment_id == assessment.id)
    ).scalar_one()
    assert conclusion.requirement_id == item.requirement_id
    assert conclusion.framework_id == item.framework_id
    assert conclusion.cluster_id == item.cluster_id
    assert conclusion.risk_level == item.risk_level
    assert conclusion.outcome == migrate_legacy.OUTCOME_MAP[item.compliance_status]
    assert conclusion.rationale == item.gap_description
    assert conclusion.gaps_identified == item.gap_description
    assert conclusion.recommended_action == item.remediation_action
    assert conclusion.evidence_summary == item.evidence_quote
    assert conclusion.ai_proposed is True
    assert conclusion.version == 1


def test_null_evidence_quote_yields_empty_evidence_summary(db):
    """See decision D-B in scripts/migrate_legacy.py: the source column is
    nullable, the target column is not. Either resolution must leave
    ``evidence_summary`` falsy rather than fabricating text."""

    session, _engine, _db_path = db
    assessment = _seed_legacy_assessment(
        session,
        company_name="No Evidence Co",
        frameworks=["dpdpa"],
        gap_items=[_gap_item_kwargs(evidence_quote=None)],
    )

    run_migration(session)
    session.expire_all()

    conclusion = session.execute(
        select(Conclusion).where(Conclusion.assessment_id == assessment.id)
    ).scalar_one()
    assert not conclusion.evidence_summary


def test_assessment_packs_created_per_framework(db):
    session, _engine, _db_path = db
    seeded = _seed_three_assessment_fixture(session)

    stats = run_migration(session)
    session.expire_all()

    # 1 (single) + 2 (multi) + 1 (empty, defaults to dpdpa) == 4
    assert stats.assessment_packs == 4
    assert _count(session, AssessmentPack) == 4

    multi_packs = list(
        session.execute(
            select(AssessmentPack).where(
                AssessmentPack.assessment_id == seeded["multi"].id
            )
        ).scalars()
    )
    assert {pack.framework_id for pack in multi_packs} == {"dpdpa", "iso27001"}
    assert all(
        pack.pack_version == migrate_legacy.UNKNOWN_PACK_VERSION for pack in multi_packs
    )


# --------------------------------------------------------------------------- #
# Scenario 3 — no orphaned rows anywhere
# --------------------------------------------------------------------------- #


def test_no_orphaned_rows_after_migration(db):
    session, _engine, _db_path = db
    _seed_three_assessment_fixture(session)

    run_migration(session)
    session.expire_all()

    assert _orphan_rows(session) == []

    # Phase 2 tables stay untouched.
    for table in PHASE_2_TABLES:
        count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
        assert count == 0, f"{table} must remain empty until Phase 2"


# --------------------------------------------------------------------------- #
# Scenario 4 — GapReport.framework_scores byte-identical round trip
# --------------------------------------------------------------------------- #


def test_framework_scores_and_legacy_history_are_untouched(db):
    session, _engine, _db_path = db
    _seed_legacy_assessment(
        session,
        company_name="Scores Co",
        frameworks=["dpdpa", "iso27001"],
        legacy_history=[{"run": 1, "overall_score": 42.0}],
        gap_items=[_gap_item_kwargs()],
    )
    before_scores = _framework_scores_by_assessment(session)
    before_history = {
        report.assessment_id: report.legacy_history
        for report in session.execute(select(GapReport)).scalars()
    }
    before_item_count = _count(session, GapItem)

    run_migration(session)
    session.expire_all()

    assert _framework_scores_by_assessment(session) == before_scores
    after_history = {
        report.assessment_id: report.legacy_history
        for report in session.execute(select(GapReport)).scalars()
    }
    assert after_history == before_history
    assert _count(session, GapItem) == before_item_count, "GapItem rows must be preserved"
    assert _count(session, GapReport) == len(before_scores)


# --------------------------------------------------------------------------- #
# Scenario 5 — idempotency
# --------------------------------------------------------------------------- #


def test_second_run_creates_zero_new_rows(db):
    session, _engine, _db_path = db
    _seed_three_assessment_fixture(session)

    first_stats = run_migration(session)
    session.expire_all()
    after_first = _snapshot_counts(session)
    assert first_stats.total > 0

    second_stats = run_migration(session)
    session.expire_all()
    after_second = _snapshot_counts(session)

    assert after_second == after_first
    assert second_stats.total == 0
    for name in COUNTED_MODELS:
        assert getattr(second_stats, name) == 0, f"{name} was re-created on rerun"


# --------------------------------------------------------------------------- #
# Scenario 6 — not_assessed -> insufficient_evidence, with a warning
# --------------------------------------------------------------------------- #


def test_not_assessed_maps_to_insufficient_evidence_and_warns(db, caplog):
    session, _engine, _db_path = db
    assessment = _seed_legacy_assessment(
        session,
        company_name="Unassessed Co",
        frameworks=["dpdpa"],
        gap_items=[
            _gap_item_kwargs(
                requirement_id="DPDPA-6.1", compliance_status="not_assessed"
            )
        ],
    )

    with caplog.at_level(logging.WARNING, logger="scripts.migrate_legacy"):
        run_migration(session)
    session.expire_all()

    conclusion = session.execute(
        select(Conclusion).where(Conclusion.assessment_id == assessment.id)
    ).scalar_one()
    assert conclusion.outcome == "insufficient_evidence"

    warnings = [rec.getMessage() for rec in caplog.records if rec.levelno >= logging.WARNING]
    assert any(
        assessment.id in message and "DPDPA-6.1" in message for message in warnings
    ), f"expected a warning naming the assessment and requirement, got: {warnings}"


# --------------------------------------------------------------------------- #
# Scenario 7 — ConclusionRevision rows
# --------------------------------------------------------------------------- #


def _revisions_for(session: Session, conclusion_id: str) -> list[ConclusionRevision]:
    return list(
        session.execute(
            select(ConclusionRevision)
            .where(ConclusionRevision.conclusion_id == conclusion_id)
            .order_by(ConclusionRevision.created_at)
        ).scalars()
    )


def test_unreviewed_gap_item_creates_one_proposed_revision(db):
    session, _engine, _db_path = db
    assessment = _seed_legacy_assessment(
        session,
        company_name="Unreviewed Co",
        frameworks=["dpdpa"],
        gap_items=[_gap_item_kwargs(reviewed_at=None, reviewed_by=None)],
    )

    run_migration(session)
    session.expire_all()

    conclusion = session.execute(
        select(Conclusion).where(Conclusion.assessment_id == assessment.id)
    ).scalar_one()
    revisions = _revisions_for(session, conclusion.id)
    assert len(revisions) == 1
    assert revisions[0].action == "proposed"
    assert revisions[0].actor == migrate_legacy.MIGRATION_ACTOR
    assert revisions[0].citations_json is None


def test_reviewed_gap_item_creates_proposed_then_approved_revisions(db):
    session, _engine, _db_path = db
    reviewed_at = datetime(2026, 2, 1, 10, 30, tzinfo=timezone.utc)
    assessment = _seed_legacy_assessment(
        session,
        company_name="Reviewed Co",
        frameworks=["dpdpa"],
        gap_items=[
            _gap_item_kwargs(
                compliance_status="partially_compliant",
                ai_compliance_status="non_compliant",
                ai_gap_description="AI draft rationale.",
                reviewed_by="consultant@cyberassess.example",
                reviewed_at=reviewed_at,
                review_status="approved",
            )
        ],
    )

    run_migration(session)
    session.expire_all()

    conclusion = session.execute(
        select(Conclusion).where(Conclusion.assessment_id == assessment.id)
    ).scalar_one()
    revisions = _revisions_for(session, conclusion.id)
    assert [rev.action for rev in revisions] == ["proposed", "approved"]

    approved = revisions[1]
    assert approved.actor == "consultant@cyberassess.example"
    assert approved.created_at.replace(tzinfo=timezone.utc) == reviewed_at
    assert approved.previous_outcome == "non_compliant"
    assert approved.previous_rationale == "AI draft rationale."


def test_reviewed_gap_item_without_reviewer_falls_back_to_unknown_actor(db):
    session, _engine, _db_path = db
    assessment = _seed_legacy_assessment(
        session,
        company_name="Anonymous Reviewer Co",
        frameworks=["dpdpa"],
        gap_items=[
            _gap_item_kwargs(
                reviewed_by=None,
                reviewed_at=datetime(2026, 2, 2, 9, 0, tzinfo=timezone.utc),
                ai_compliance_status=None,
                ai_gap_description=None,
            )
        ],
    )

    run_migration(session)
    session.expire_all()

    conclusion = session.execute(
        select(Conclusion).where(Conclusion.assessment_id == assessment.id)
    ).scalar_one()
    approved = _revisions_for(session, conclusion.id)[1]
    assert approved.actor == "unknown"
    # No AI values recorded -> fall back to the proposed values.
    assert approved.previous_outcome == conclusion.outcome
    assert approved.previous_rationale == conclusion.rationale


# --------------------------------------------------------------------------- #
# Scenario 8 — Finding/Action creation gated on remediation_status
# --------------------------------------------------------------------------- #


def test_null_remediation_status_creates_no_finding_or_action(db):
    session, _engine, _db_path = db
    _seed_legacy_assessment(
        session,
        company_name="Untouched Remediation Co",
        frameworks=["dpdpa"],
        gap_items=[_gap_item_kwargs(remediation_status=None)],
    )

    stats = run_migration(session)
    session.expire_all()

    assert stats.findings == 0
    assert stats.actions == 0
    assert _count(session, Finding) == 0
    assert _count(session, Action) == 0


def test_bare_open_remediation_status_with_no_other_fields_still_creates_finding(db):
    """A genuinely-open, not-yet-triaged item is not the same as an untouched one.

    ``remediation_status="open"`` with no owner/target_date/notes/closed_at is a
    completely ordinary real-world state (a finding was opened but nobody has
    been assigned yet) — it must never be conflated with ``remediation_status
    is None`` ("never touched"), no matter how the two look alike on an
    otherwise-empty row. The spec is explicit: "treat an explicit 'open' value
    the same as any other status -- it's still a real Finding."
    """
    session, _engine, _db_path = db
    _seed_legacy_assessment(
        session,
        company_name="Freshly Opened Co",
        frameworks=["dpdpa"],
        gap_items=[
            _gap_item_kwargs(
                remediation_status="open",
                remediation_owner=None,
                remediation_target_date=None,
                remediation_notes=None,
                remediation_closed_at=None,
            )
        ],
    )

    stats = run_migration(session)
    session.expire_all()

    assert stats.findings == 1
    assert stats.actions == 1
    assert _count(session, Finding) == 1
    assert _count(session, Action) == 1


@pytest.mark.parametrize("remediation_status", ["open", "in_progress", "closed"])
def test_set_remediation_status_creates_one_finding_and_one_action(db, remediation_status):
    session, _engine, _db_path = db
    assessment = _seed_legacy_assessment(
        session,
        company_name=f"Remediating Co {remediation_status}",
        frameworks=["dpdpa"],
        gap_items=[
            _gap_item_kwargs(
                remediation_status=remediation_status,
                remediation_owner="owner@example.com",
                remediation_target_date=datetime(2026, 9, 30, 0, 0),
            )
        ],
    )
    item = _gap_items_for(session, assessment)[0]

    stats = run_migration(session)
    session.expire_all()

    assert stats.findings == 1
    assert stats.actions == 1

    finding = session.execute(select(Finding)).scalar_one()
    conclusion = session.execute(select(Conclusion)).scalar_one()
    assert finding.assessment_id == assessment.id
    assert finding.conclusion_id == conclusion.id
    assert finding.title == item.requirement_title
    assert finding.description == item.gap_description
    assert finding.severity == item.risk_level
    assert finding.priority == item.remediation_priority
    assert finding.status in migrate_legacy.FINDING_STATUSES

    action = session.execute(select(Action)).scalar_one()
    assert action.finding_id == finding.id
    assert action.title == item.remediation_action
    assert action.owner == "owner@example.com"
    assert action.target_date is not None
    assert action.status == "open", "no remediation_closed_at -> action stays open"

    history = json.loads(action.history_json)
    assert isinstance(history, list) and len(history) == 1
    entry = history[0]
    assert entry["actor"] == migrate_legacy.MIGRATION_ACTOR
    assert entry["action"] == "imported"
    assert entry["notes"] == "Migrated from legacy GapItem remediation fields"
    datetime.fromisoformat(entry["timestamp"])  # must be parseable ISO 8601


def test_closed_remediation_produces_closed_action(db):
    session, _engine, _db_path = db
    _seed_legacy_assessment(
        session,
        company_name="Closed Remediation Co",
        frameworks=["dpdpa"],
        gap_items=[
            _gap_item_kwargs(
                remediation_status="open",
                remediation_closed_at=datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc),
            )
        ],
    )

    run_migration(session)
    session.expire_all()

    action = session.execute(select(Action)).scalar_one()
    assert action.status == "closed"


def test_unknown_remediation_status_falls_back_to_open_with_warning(db, caplog):
    session, _engine, _db_path = db
    _seed_legacy_assessment(
        session,
        company_name="Weird Status Co",
        frameworks=["dpdpa"],
        gap_items=[_gap_item_kwargs(remediation_status="banana")],
    )

    with caplog.at_level(logging.WARNING, logger="scripts.migrate_legacy"):
        run_migration(session)
    session.expire_all()

    finding = session.execute(select(Finding)).scalar_one()
    assert finding.status == "open"
    assert any("banana" in rec.getMessage() for rec in caplog.records)


# --------------------------------------------------------------------------- #
# Scenario 9 — empty DB
# --------------------------------------------------------------------------- #


def test_empty_database_migrates_cleanly_and_creates_nothing(db):
    session, _engine, _db_path = db
    assert _count(session, Assessment) == 0

    stats = run_migration(session)
    session.expire_all()

    assert stats.total == 0
    assert _snapshot_counts(session) == dict.fromkeys(COUNTED_MODELS, 0)
    assert _orphan_rows(session) == []


def test_assessment_without_gap_report_still_gets_client_engagement_and_pack(db):
    session, _engine, _db_path = db
    assessment = _seed_legacy_assessment(
        session,
        company_name="No Report Co",
        frameworks=["dpdpa"],
        gap_items=None,
    )

    stats = run_migration(session)
    session.expire_all()
    session.refresh(assessment)

    assert stats.clients == 1
    assert stats.engagements == 1
    assert stats.assessment_packs == 1
    assert stats.conclusions == 0
    assert _client_for_assessment(session, assessment).name == "No Report Co"


# --------------------------------------------------------------------------- #
# Scenario 10 — mandatory backup at the CLI level
# --------------------------------------------------------------------------- #


def test_main_aborts_without_writing_when_backup_fails(db, tmp_path, monkeypatch):
    session, _engine, db_path = db
    _seed_three_assessment_fixture(session)
    before = _snapshot_counts(session)

    def _explode(*_args, **_kwargs):
        raise RuntimeError("simulated backup failure")

    monkeypatch.setattr(migrate_legacy, "create_backup", _explode)

    exit_code = migrate_legacy.main(
        [
            "--db-url",
            f"sqlite:///{db_path}",
            "--upload-dir",
            str(tmp_path / "uploads"),
            "--backup-out-dir",
            str(tmp_path / "backups"),
        ]
    )

    assert exit_code != 0, "a failed backup must abort with a non-zero exit code"
    session.expire_all()
    assert _snapshot_counts(session) == before, "no rows may be written when backup fails"


def test_main_with_skip_backup_runs_the_migration(db, tmp_path):
    session, _engine, db_path = db
    _seed_three_assessment_fixture(session)

    exit_code = migrate_legacy.main(
        [
            "--db-url",
            f"sqlite:///{db_path}",
            "--upload-dir",
            str(tmp_path / "uploads"),
            "--skip-backup",
        ]
    )

    assert exit_code == 0
    session.expire_all()
    assert _count(session, Client) == 3
    assert _count(session, Conclusion) == _count(session, GapItem)


def test_main_takes_a_backup_before_writing(db, tmp_path):
    session, _engine, db_path = db
    _seed_three_assessment_fixture(session)
    backups = tmp_path / "backups"
    uploads = tmp_path / "uploads"
    uploads.mkdir()

    exit_code = migrate_legacy.main(
        [
            "--db-url",
            f"sqlite:///{db_path}",
            "--upload-dir",
            str(uploads),
            "--backup-out-dir",
            str(backups),
        ]
    )

    assert exit_code == 0
    created = [path for path in backups.iterdir() if path.is_dir()]
    assert len(created) == 1, f"expected exactly one backup directory, got {created}"
    assert (created[0] / "manifest.json").is_file()


# --------------------------------------------------------------------------- #
# Done criteria — rollback_legacy.py restores pre-migration state (real I/O)
# --------------------------------------------------------------------------- #


def test_rollback_legacy_restores_pre_migration_state(tmp_path):
    db_path = tmp_path / "live.sqlite3"
    uploads = tmp_path / "uploads"
    (uploads / "assessment-1").mkdir(parents=True)
    (uploads / "assessment-1" / "policy.txt").write_text("original evidence")
    backups = tmp_path / "backups"

    engine = _build_db(db_path)
    session = sessionmaker(bind=engine)()
    try:
        _seed_three_assessment_fixture(session)
        before = _snapshot_counts(session)
        assert before["clients"] == 0
    finally:
        session.close()
        engine.dispose()

    backup_dir = create_backup(db_path, uploads, backups)

    engine = _build_db(db_path)
    session = sessionmaker(bind=engine)()
    try:
        run_migration(session)
        session.expire_all()
        assert _count(session, Client) == 3
    finally:
        session.close()
        engine.dispose()

    # Simulate post-migration damage to the upload tree too.
    (uploads / "assessment-1" / "policy.txt").write_text("corrupted")

    exit_code = rollback_legacy.main(
        [
            "--backup-dir",
            str(backup_dir),
            "--db-url",
            f"sqlite:///{db_path}",
            "--upload-dir",
            str(uploads),
            "--force",
        ]
    )
    assert exit_code == 0

    engine = _build_db(db_path)
    session = sessionmaker(bind=engine)()
    try:
        assert _snapshot_counts(session) == before
        assert _count(session, Assessment) == 3
        assert _count(session, GapItem) == 5
    finally:
        session.close()
        engine.dispose()

    assert (uploads / "assessment-1" / "policy.txt").read_text() == "original evidence"


def test_migration_stats_is_a_dataclass_with_the_expected_counters():
    stats = MigrationStats()
    for name in COUNTED_MODELS:
        assert getattr(stats, name) == 0
    assert stats.total == 0
