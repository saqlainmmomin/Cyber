"""Test helper for P6-6 (D-P6-G): record an assessment period so approvals are allowed.

Existing suites that approve Conclusions call this once from their seed helper.
Kept outside tests/support/ so the fixture/support guards stay untouched.
It goes through the real service, so the approval gate itself is never bypassed.
"""

from __future__ import annotations

from datetime import date

TEST_PERIOD_START = date(2026, 1, 1)
TEST_PERIOD_END = date(2026, 3, 31)
TEST_EVIDENCE_CUTOFF = date(2026, 4, 15)


def record_test_period(db, assessment, *, actor: str = "consultant:Test Seed") -> None:
    from app.services.report_basis import update_report_basis

    update_report_basis(
        db,
        assessment,
        period_start=TEST_PERIOD_START,
        period_end=TEST_PERIOD_END,
        evidence_cutoff=TEST_EVIDENCE_CUTOFF,
        prepared_by=None,
        reviewed_by=None,
        actor=actor,
    )
