"""P6-8 V3-B file-set guard (tasks/handoffs/2026-10-01-board-report-v3-deck.md, "V3-B file set")."""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

from tests.p6_8_v3b_paths import V3B_APP_PATHS, V3B_APP_PREFIXES  # noqa: E402
from tests.v3c_paths import V3C_PRIOR_DOMAINS_PATHS  # noqa: E402
V3B_OTHER = (
    "tasks/handoffs/2026-10-01-board-report-v3-deck.md", "tests/golden/p6_8_v3_deck_document.json",
    "tests/golden/p6_8_board_document.json", "tests/test_p6_8_v3b_extra.py", "tasks/todo.md",
)
# Existing tests that V3-B legitimately edits (D-P6-8-V3-S) or that gain a scoped V3-B allowance.
V3B_EXISTING_TEST_EDITS = (
    "tests/test_p6_8_board_report_v2.py", "tests/test_p6_9_roadmap.py", "tests/test_p6_9_soa.py",
    "tests/test_p6_9_prior_period.py", "tests/test_p6_8_b2_docx_xlsx.py", "tests/test_p6_10b_narrative.py",
    "tests/test_p6_2b_dpdpa_criteria.py",
    # per-PR V3-B guard allowances (designer pass) and the route list
    "tests/p6_10_support.py", "tests/test_p6_10a_remediation_draft.py", "tests/test_p6_4_cap_upload_limit.py",
    "tests/test_p6_4_whats_missing.py", "tests/test_p6_7_requirement_card.py", "tests/test_p6_7b_add_to_rfi.py",
    "tests/test_p6_8_v3a_data_capture.py", "tests/test_p6_9_file_set.py", "tests/test_p6_nist_csf2_alignment.py",
    "tests/test_report_snapshots.py",
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
        and f not in own_tests and f not in V3B_EXISTING_TEST_EDITS
        and f not in V3C_PRIOR_DOMAINS_PATHS  # V3-C prior domains per-PR allowance
    ]
    assert offenders == [], offenders
