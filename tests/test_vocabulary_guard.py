"""One label guard plus boundary checks for the deferred readiness bands."""

from __future__ import annotations

import ast
from pathlib import Path
import re

from app.services import vocabulary as vocab

ROOT = Path(__file__).resolve().parents[1]
# These templates are outside the WP 1.1 conversion set. Some use the same words
# for evidence or questionnaire states; the board template also has old bands.
TEMPLATE_ALLOWLIST = {
    "pages/design.html",
    "pages/design_s9_system.html",
    "pages/evidence_inventory.html",
    "pages/workpaper.html",
    "partials/section_questions.html",
    "partials/magic_links.html",
    "reports/workpaper_standalone.html",
    "reports/board_report.html",
}
# This service builds its prompt inline. Prompt wording is out of scope.
PROMPT_FUNCTIONS = {("app/services/followup_engine.py", "_build_followup_prompt")}
LABELS = {
    *vocab.OUTCOMES.values(),
    *vocab.REVIEW_STATES.values(),
    *vocab.LEGACY_OUTCOMES.values(),
    "Non Compliant",
}
TEMPLATE_LABEL = re.compile(
    r"[\"'](?:" + "|".join(re.escape(label) for label in sorted(LABELS))
    + r")[\"']|>\s*(?:" + "|".join(re.escape(label) for label in sorted(LABELS)) + r")\s*<"
)


def test_vocabulary_guard():
    violations = []
    for path in sorted((ROOT / "app").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        if path.name == "vocabulary.py" or "prompt" in path.stem or "definitions" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        prompt_nodes = {
            id(child)
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and (relative, node.name) in PROMPT_FUNCTIONS
            for child in ast.walk(node)
        }
        for node in ast.walk(tree):
            if id(node) in prompt_nodes:
                continue
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in LABELS:
                violations.append(f"{relative}:{node.lineno}: {node.value!r}")
    for path in sorted((ROOT / "app/templates").rglob("*.html")):
        if path.relative_to(ROOT / "app/templates").as_posix() in TEMPLATE_ALLOWLIST:
            continue
        for match in TEMPLATE_LABEL.finditer(path.read_text(encoding="utf-8")):
            line = path.read_text(encoding="utf-8").count("\n", 0, match.start()) + 1
            violations.append(f"{path.relative_to(ROOT)}:{line}: {match.group()!r}")
    assert not violations, "Labels must come from vocabulary.py:\n" + "\n".join(violations)

    # WP 2.3 consumes these later. Check unrounded boundaries here without adding
    # a separate suite or changing any current scoring/export behavior.
    assert [vocab.score_band(score) for score in (-1, 0, 39.9, 40, 59.9, 60, 79.6, 80, 100)] == [
        "Not ready", "Not ready", "Not ready", "Partly ready", "Partly ready",
        "Mostly ready", "Mostly ready", "Ready", "Ready",
    ]


def test_one_numeric_priority_map_one_priority_per_risk_level():
    from app.services import approved_report, findings, vocabulary as vocab
    from app.services.grounding import judge

    assert vocab.PRIORITY_BY_RISK == {"critical": 1, "high": 2, "medium": 3, "low": 4}
    assert findings.PRIORITY_BY_SEVERITY is vocab.PRIORITY_BY_RISK
    assert approved_report.PRIORITY_BY_RISK is vocab.PRIORITY_BY_RISK
    assert judge.PRIORITY_BY_RISK is vocab.PRIORITY_BY_RISK
    assert sorted(vocab.PRIORITY_BY_RISK.values()) == sorted(vocab.PRIORITY_LABELS)
