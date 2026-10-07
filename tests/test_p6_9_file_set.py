"""Contract coverage for P6-9: the new modules must not call an LLM."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NEW_MODULES = (
    "app/services/soa.py",
    "app/services/remediation_groups.py",
    "app/services/prior_period.py",
    "app/routers/soa.py",
    "app/services/board_report.py",
)



def test_scenario_1_new_modules_have_no_llm_imports():
    for relative in NEW_MODULES:
        path = REPO_ROOT / relative
        if path.exists():
            source = path.read_text(encoding="utf-8")
            for token in ("llm_client", "claude_analyzer", "services.grounding", "call_llm", "openai", "anthropic"):
                assert token not in source, (relative, token)
