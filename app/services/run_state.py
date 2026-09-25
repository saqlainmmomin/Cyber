"""Shared durable state mutations for analysis-run recovery."""

from __future__ import annotations

import json
from datetime import datetime

from app.models.analysis_run import AnalysisRun


def mark_run_failed(
    run: AnalysisRun,
    *,
    error_type: str,
    completed_at: datetime,
) -> None:
    """Apply the durable failed-run mutation without committing the session."""
    envelope = json.loads(run.claims_json)
    envelope["claims"] = []
    envelope["error"] = {"type": error_type}
    run.status = "failed"
    run.completed_at = completed_at
    run.claims_json = json.dumps(envelope, sort_keys=True)
