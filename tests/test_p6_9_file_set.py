"""Scope guard for P6-9 (handoff D-P6-9-K): no LLM, and only the P6-9 file set changes under app/.

Green before implementation (nothing under app/ changed) and must stay green after it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
P6_9_APP_ALLOWLIST = (
    "app/services/soa.py",
    "app/services/remediation_groups.py",
    "app/services/prior_period.py",
    "app/services/board_report.py",
    "app/routers/soa.py",
    "app/main.py",
    "app/templates/reports/board_report.html",
    "app/templates/pages/soa.html",
    "app/templates/pages/report_snapshots.html",
)
from tests.p6_8_v3a_paths import V3A_APP_PATHS, V3A_EXCLUDES  # P6-8 V3-A per-PR allowance
from tests.yozora_backend_paths import YOZORA_BACKEND_APP_PATHS, YOZORA_BACKEND_EXCLUDES  # Yozora backend per-PR allowance
from tests.yozora_paths import YOZORA_EXCLUDES, YOZORA_S1_PATHS, YOZORA_S2_PATHS  # Yozora S1/S2 per-PR allowance

P6_9_FORBIDDEN_PATHS = (
    # Frozen fpdf2 reports and goldens (D-P6-H).
    "app/utils/pdf_export.py", "app/utils/rfi_export.py", "app/routers/reports.py",
    "app/routers/integrated_reports.py", "tests/fixtures", "tests/support",
    # B1 plumbing and parallel P6-8 B2 / P6-7b / P6-10 surfaces.
    "app/utils/html_pdf.py", "app/services/report_snapshots.py", "app/routers/snapshots.py",
    "app/services/standalone_workpaper.py", "app/templates/reports/workpaper_standalone.html",
    "app/services/rfi_requests.py", "app/services/requirement_card.py", "app/services/review_queue.py",
    "app/routers/requirement_review.py", "app/routers/review.py", "app/routers/web.py",
    "app/services/conclusion_review.py", "app/templates/components", "app/templates/partials",
    "app/templates/base.html",
    # Readers, scoring, analyzer, LLM, packs (incl. UCC mappings, read-only), schema, scripts.
    "app/services/approved_report.py", "app/services/report_content.py", "app/services/report_basis.py",
    "app/services/findings.py", "app/services/remediation_rollup.py", "app/services/scoring.py",
    "app/services/claude_analyzer.py", "app/services/llm_client.py", "app/services/grounding",
    "app/services/analysis_pipeline.py", "app/services/analysis_v2.py", "app/services/desk_review.py",
    "app/services/desk_review_v2.py", "app/frameworks", "app/dpdpa", "app/models", "app/schemas",
    "alembic", "app/config.py", "requirements.txt", "requirements-dev.txt", "scripts", "validation",
    ":(exclude)scripts/validation/run_company.py",
    # P6-5b (tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md) lands after P6-9: harness only.
    ":(exclude)scripts/validation/ab_compare.py",
    ":(exclude)scripts/validation/score.py",
    # P6-2e: signed ISO / NIST criteria.
    ":(exclude)app/frameworks/criteria/__init__.py",
    ":(exclude)app/frameworks/criteria/iso27001.py",
    ":(exclude)app/frameworks/criteria/nist_csf.py",
    ":(exclude)app/frameworks/definitions/iso27001.py",
    ":(exclude)app/frameworks/definitions/nist_csf.py",
    ":(exclude)scripts/convert_criteria.py",
    # LLM request deadline (claude/llm-request-deadline): wall-clock cap per provider call.
    ":(exclude)app/config.py",
    ":(exclude)app/services/llm_client.py",
    # P6-8 B2 (tasks/handoffs/2026-09-28-p6-8-b2-docx-xlsx.md): two GET export routes and the openpyxl pin;
    # tests/test_p6_8_b2_docx_xlsx.py guards both (the requirements diff must be exactly the pin).
    ":(exclude)app/routers/snapshots.py",
    ":(exclude)requirements.txt",
    # P6-8 V3-A (tasks/handoffs/2026-10-01-board-report-v3-deck.md): board-inputs migration, models, page, theme, display font.
    *V3A_EXCLUDES,
    # Yozora backend features (tasks/handoffs/2026-10-03-yozora-backend-features.md).
    *YOZORA_BACKEND_EXCLUDES,
    *YOZORA_EXCLUDES,  # Yozora S1
    # P6-10 (tasks/handoffs/2026-09-28-p6-10-remediation-and-narrative.md, revised 2026-10-01): the
    # recommended-action draft control and partial; tests/test_p6_10a_remediation_draft.py guards them.
    ":(exclude)app/templates/components/conclusion_card.html",
    ":(exclude)app/templates/partials/remediation_draft.html",
)
# P6-10 lands after P6-9: drafting router, narrative service and page, plus board_exports (schema v3).
P6_10_APP_FILES = (
    "app/services/remediation_draft.py", "app/services/narrative.py", "app/routers/drafting.py",
    "app/templates/partials/remediation_draft.html", "app/templates/components/conclusion_card.html",
    "app/templates/pages/narrative.html", "app/services/board_exports.py",
)
NEW_MODULES = (
    "app/services/soa.py",
    "app/services/remediation_groups.py",
    "app/services/prior_period.py",
    "app/routers/soa.py",
    "app/services/board_report.py",
)


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout


def test_scenario_1_no_llm_and_p6_9_file_set():
    for relative in NEW_MODULES:
        path = REPO_ROOT / relative
        if path.exists():
            source = path.read_text(encoding="utf-8")
            for token in ("llm_client", "claude_analyzer", "services.grounding", "call_llm", "openai", "anthropic"):
                assert token not in source, (relative, token)

    committed = _git("diff", "--name-only", "main...HEAD", "--", *P6_9_FORBIDDEN_PATHS).split()
    working = _git("diff", "--name-only", "HEAD", "--", *P6_9_FORBIDDEN_PATHS).split()
    assert committed == [] and working == [], committed + working

    changed_app = set(_git("diff", "--name-only", "main...HEAD", "--", "app").split())
    changed_app |= set(_git("diff", "--name-only", "HEAD", "--", "app").split())
    changed_app |= set(_git("ls-files", "--others", "--exclude-standard", "app").split())
    outside = sorted(path for path in changed_app if path not in P6_9_APP_ALLOWLIST and not path.startswith("app/frameworks/"))
    outside = [path for path in outside if path not in ("app/config.py", "app/services/llm_client.py")]  # LLM request deadline
    outside = [path for path in outside if path not in ("app/services/board_exports.py", "app/routers/snapshots.py")]  # P6-8 B2
    outside = [path for path in outside if path not in V3A_APP_PATHS]  # P6-8 V3-A
    outside = [path for path in outside if path not in P6_10_APP_FILES]  # P6-10
    outside = [path for path in outside if path not in YOZORA_BACKEND_APP_PATHS]  # Yozora backend
    outside = [path for path in outside if path not in YOZORA_S1_PATHS]  # Yozora S1
    outside = [path for path in outside if path not in YOZORA_S2_PATHS]  # Yozora S2
    assert outside == [], outside
