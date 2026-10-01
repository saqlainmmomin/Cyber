"""File set of P6-8 V3-A (tasks/handoffs/2026-10-01-board-report-v3-deck.md, D-P6-8-V3-A).

Older file-set guards import this to allow exactly these paths for the V3-A PR (a scoped,
per-PR allowance; no guard is removed or loosened beyond these paths).
tests/test_p6_8_v3a_data_capture.py is the guard for the set itself.
"""

V3A_APP_PATHS = (
    "alembic/versions/5e9a2c7d4b18_p6_8_v3a_board_inputs.py",
    "app/models/finding.py", "app/models/action.py", "app/models/assessment.py",
    "app/models/initiative_metadata.py", "app/models/__init__.py",
    "app/services/board_inputs.py", "app/services/firm_theme.py",
    "app/routers/board_inputs.py", "app/main.py", "app/config.py",
    "app/templates/pages/board_inputs.html", "app/templates/pages/findings.html",
    "app/utils/html_pdf.py", "app/services/retention.py",
    "app/assets/fonts/noto/BarlowCondensed-Bold.ttf", "app/assets/fonts/noto/BarlowCondensed-SemiBold.ttf",
    "app/assets/fonts/noto/OFL-BarlowCondensed.txt",
)
V3A_EXCLUDES = [f":(exclude){path}" for path in V3A_APP_PATHS]
