"""P6-8 V3-B file-set guard (tasks/handoffs/2026-10-01-board-report-v3-deck.md, "V3-B file set")."""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

V3B_APP_PATHS = (
    "app/services/board_derive.py", "app/services/board_view.py", "app/services/board_report.py",
    "app/services/board_exports.py", "app/services/report_content.py", "app/services/remediation_groups.py",
    "app/services/narrative.py", "app/routers/snapshots.py", "app/templates/pages/report_snapshots.html",
    "requirements.txt",
)
V3B_APP_PREFIXES = ("app/templates/reports/",)
V3B_OTHER = (
    "tasks/handoffs/2026-10-01-board-report-v3-deck.md", "tests/golden/p6_8_v3_deck_document.json",
    "tests/golden/p6_8_board_document.json", "tests/test_p6_8_v3b_extra.py",
)


def test_v3b_changes_stay_in_the_v3b_file_set():
    committed = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    ).stdout.split()
    own_tests = {f for f in committed if f.startswith("tests/") and "v3b" in f or f.startswith("tests/p6_8_v3_")}
    offenders = [
        f for f in committed
        if f not in V3B_APP_PATHS and f not in V3B_OTHER and not f.startswith(V3B_APP_PREFIXES)
        and f not in own_tests and f != "tests/test_p6_2b_dpdpa_criteria.py" and f != "tests/test_p6_8_b2_docx_xlsx.py"
    ]
    assert offenders == [], offenders
