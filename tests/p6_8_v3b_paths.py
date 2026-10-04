"""File set of P6-8 V3-B (tasks/handoffs/2026-10-01-board-report-v3-deck.md, "V3-B file set").

Older file-set guards import this to allow exactly these paths for the V3-B PR (a scoped,
per-PR allowance; no guard is removed or loosened beyond these paths).
tests/test_p6_8_v3b_file_set.py is the guard for the set itself.
"""

V3B_APP_PATHS = (
    "app/services/board_derive.py", "app/services/board_view.py", "app/services/board_report.py",
    "app/services/board_exports.py", "app/services/report_content.py", "app/services/remediation_groups.py",
    "app/services/narrative.py", "app/routers/snapshots.py", "app/templates/pages/report_snapshots.html",
    "requirements.txt",
)
V3B_APP_PREFIXES = ("app/templates/reports/",)
V3B_EXCLUDES = [f":(exclude){path}" for path in V3B_APP_PATHS] + [f":(exclude){prefix}" for prefix in V3B_APP_PREFIXES]


def is_v3b_path(path):
    return path in V3B_APP_PATHS or path.startswith(V3B_APP_PREFIXES)
