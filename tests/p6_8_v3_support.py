"""Shared support for the v3 board-deck contract tests (V3-A data capture, V3-B deck).

Handoff: tasks/handoffs/2026-10-01-board-report-v3-deck.md. The database, HTTP client and
released-assessment fixtures are the P6-8 B1 ones, re-exported so both parts build on the
same data. Nothing here calls a model.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.models.audit_event import AuditEvent
from tests.test_p6_8_board_report_v2 import (  # noqa: F401 - fixtures are used by name
    DEVANAGARI_COMPANY,
    FIXED_GENERATED_AT,
    _alembic_config,
    _document,
    _engagement_fixture,
    _generate,
    _no_llm,
    _register_frameworks,
    db,
    db_path,
    engine,
    gate,
    http,
    upload_root,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEWER = "Priya"
V3A_REVISION = "5e9a2c7d4b18"
PREVIOUS_REVISION = "8b2d5f7e1c34"
DISPLAY_FONT_SHA256 = {
    "BarlowCondensed-Bold.ttf": "e476562ec9c1e16cf16475895b511f08c804f438cc9a9f80a44ea50a0eeb5b65",
    "BarlowCondensed-SemiBold.ttf": "7b619d14bc2327509a9ef32b0890f709626f7ecc9ff61191c2a4314c5499d2d9",
}
DISPLAY_LICENSE_FILES = ("OFL-BarlowCondensed.txt",)
DEFAULT_THEME = {"primary": "#161A5C", "secondary": "#2D3FD3", "accent": "#12B3A6"}
DECK_FIXTURE = REPO_ROOT / "tests" / "golden" / "p6_8_v3_deck_document.json"


def load_deck_document() -> dict:
    """The synthetic v3 board-report document (V3-B): 120 requirements, 10 observations, 8 initiatives.

    It follows the pinned v3 schema of tasks/handoffs/2026-10-01-board-report-v3-deck.md and is
    derived from docs/product/2026-10-01-board-report-mockup/deck_document.json. A fresh deep copy per call.
    """
    import copy

    cached = getattr(load_deck_document, "_cache", None)
    if cached is None:
        cached = json.loads(DECK_FIXTURE.read_text(encoding="utf-8"))
        load_deck_document._cache = cached
    return copy.deepcopy(cached)


def git(*args) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


def events(db, action: str, entity_id: str | None = None) -> list[AuditEvent]:
    query = db.query(AuditEvent).filter(AuditEvent.action == action)
    if entity_id is not None:
        query = query.filter(AuditEvent.entity_id == entity_id)
    return sorted(query.all(), key=lambda event: (event.created_at, event.id))


def metadata(event: AuditEvent) -> dict:
    return json.loads(event.metadata_json)


def findings_and_actions(db, assessment):
    """The assessment's Findings (oldest first) and each one's Actions."""
    from app.models.action import Action
    from app.models.finding import Finding

    findings = (
        db.query(Finding).filter_by(assessment_id=assessment.id).order_by(Finding.created_at, Finding.id).all()
    )
    actions = {
        finding.id: db.query(Action).filter_by(finding_id=finding.id).order_by(Action.created_at, Action.id).all()
        for finding in findings
    }
    return findings, actions


def roadmap_groups(db, assessment) -> list[dict]:
    """The live roadmap groups, exactly as the board report builds them."""
    from app.services import remediation_groups, report_content

    findings = report_content.assessment_findings(db, assessment).findings
    return remediation_groups.build_groups(findings, list(assessment.frameworks))


@pytest.fixture()
def fixture_assessment(db, http, gate, monkeypatch):
    """Released DPDPA + ISO assessment: two approved Findings, one Action each, evidence, one edit."""
    assessment, conclusions, dp, iso = _engagement_fixture(db, http, gate, monkeypatch)
    return assessment
