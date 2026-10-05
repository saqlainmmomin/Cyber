"""Deterministic S8 versions-group specimens for report versions, SoA and comparison."""

from __future__ import annotations

import json

from design.harness.seed_s4 import SEED_ACTOR, _audit, _assessment, _time
from design.harness.seed_s7_report import _conclusion, _report


PREVIOUS_ASSESSMENT_ID = "assessment-s8-previous"

SCREEN_STATES = {
    "b6-report_snapshots": ("default", "empty", "error", "issue", "loading", "board", "unreleased"),
    "b6-soa": ("default", "empty", "error", "loading", "saving", "saved"),
    "b6-comparison": ("default", "empty", "error", "iso", "loading"),
}


def _seed_approved_report(db, assessment, *, release: bool = True) -> None:
    from app.frameworks.registry import FrameworkRegistry
    from app.services import approved_report

    assessment.status = "completed"
    controls = {
        framework_id: FrameworkRegistry.get_all_controls(framework_id)[:3]
        for framework_id in assessment.frameworks
    }
    assessment.scope_answers = json.dumps({})
    assessment.applicable_requirements = json.dumps(
        [control.id for framework_controls in controls.values() for control in framework_controls]
    )
    _report(db, assessment)
    for framework_id, framework_controls in controls.items():
        for index, control in enumerate(framework_controls):
            _conclusion(db, assessment, framework_id, control, index, approved=True)
    if release:
        approved_report.record_release(db, assessment, actor=SEED_ACTOR)


def _snapshot(db, assessment, snapshot_id, snapshot_type, *, issued, generated_days, size_bytes):
    from app.models.report_snapshot import ReportSnapshot

    generated_at = _time(generated_days)
    snapshot = ReportSnapshot(
        id=snapshot_id,
        assessment_id=assessment.id,
        type=snapshot_type,
        format="html" if snapshot_type == "workpaper" else "pdf",
        storage_path=f"reports/assessments/{assessment.id}/{snapshot_id}.pdf",
        generated_at=generated_at,
        is_issued=issued,
    )
    metadata = {
        "schema_version": 1,
        "sha256": (snapshot_id.replace("-", "") + "0" * 64)[:64],
        "size_bytes": size_bytes,
    }
    events = [
        _audit(
            f"audit-generated-{snapshot_id}",
            action="report_snapshot.generated",
            entity_type="report_snapshot",
            entity_id=snapshot_id,
            created_at=generated_at,
            metadata=metadata,
        )
    ]
    if issued:
        events.append(
            _audit(
                f"audit-issued-{snapshot_id}",
                action="report_snapshot.issued",
                entity_type="report_snapshot",
                entity_id=snapshot_id,
                created_at=_time(generated_days + 1),
            )
        )
    db.add_all([snapshot, *events])


def _seed_snapshots(db, assessment, state: str) -> None:
    if state in {"empty", "unreleased"}:
        return
    _snapshot(db, assessment, "snapshot-s8-gap-issued", "gap_report", issued=True, generated_days=-2, size_bytes=217088)
    _snapshot(db, assessment, "snapshot-s8-gap-draft", "gap_report", issued=False, generated_days=-1, size_bytes=221184)
    _snapshot(db, assessment, "snapshot-s8-board-issued", "board_report", issued=True, generated_days=-3, size_bytes=1433600)
    _snapshot(db, assessment, "snapshot-s8-board-draft", "board_report", issued=False, generated_days=-1, size_bytes=1474560)


def apply(db, screen, state, assessment, engagement, data):
    _seed_approved_report(
        db,
        assessment,
        release=not (screen == "b6-report_snapshots" and state == "unreleased"),
    )
    if screen == "b6-report_snapshots":
        if state == "unreleased":
            assessment.review_status = None
            return {"data_state": "database", "note": "Report data is present but has not been released."}
        _seed_snapshots(db, assessment, state)
    elif screen == "b6-comparison":
        previous = _assessment(
            PREVIOUS_ASSESSMENT_ID,
            engagement.id,
            assessment.company_name,
            "Prior assessment",
            tuple(assessment.frameworks),
            status="completed",
            days=-220,
        )
        db.add(previous)
        db.flush()
        _seed_approved_report(db, previous)
    return {
        "data_state": "preview-state" if state in {"error", "loading", "issue", "board", "saving", "saved", "iso"} else "database",
        "note": "Loading and interaction states use the live page shell with a deterministic preview state." if state in {"error", "loading", "issue", "board", "saving", "saved", "iso"} else "",
    }


def route(screen, state, assessment_id):
    if screen == "b6-report_snapshots":
        if state in {"empty", "unreleased"}:
            return f"/assessments/{assessment_id}/snapshots"
        query = f"?assessment_id={assessment_id}&state={state}"
        if state == "board":
            query += "&panel=board"
        return f"/design/pages/b6-report_snapshots{query}"
    if screen == "b6-soa":
        if state == "default":
            return f"/assessments/{assessment_id}/soa"
        return f"/design/pages/b6-soa?assessment_id={assessment_id}&state={state}"
    if screen == "b6-comparison":
        if state == "default":
            return f"/assessments/{assessment_id}/compare/{PREVIOUS_ASSESSMENT_ID}"
        return f"/design/pages/b6-comparison?assessment_id={assessment_id}&state={state}"
    raise ValueError(f"unknown screen {screen!r}")
