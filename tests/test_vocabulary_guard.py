"""One label guard plus boundary checks for the deferred readiness bands."""

from __future__ import annotations

import ast
from pathlib import Path
import re

from app.services import vocabulary as vocab

ROOT = Path(__file__).resolve().parents[1]
# These templates are outside the WP 1.1 conversion set. Some use the same words
# for evidence or questionnaire states.
TEMPLATE_ALLOWLIST = {
    "pages/design.html",
    "pages/design_s9_system.html",
    "pages/evidence_inventory.html",
    "pages/workpaper.html",
    "partials/section_questions.html",
    "partials/magic_links.html",
    "reports/workpaper_standalone.html",
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


def test_readiness_score_format_and_boundaries():
    for score, text, band in (
        (39.95, "40.0%", "Not ready"),
        (40.0, "40.0%", "Partly ready"),
        (59.96, "60.0%", "Partly ready"),
        (79.6, "79.6%", "Mostly ready"),
        (80.0, "80.0%", "Ready"),
    ):
        assert vocab.score_text(score) == text
        assert vocab.score_band(score) == band


def test_readiness_headlines_and_targets():
    targets = {
        "dpdpa": "Readiness for DPDP Act obligations",
        "iso27001": "Readiness for ISO 27001 certification",
        "nist_csf": "Readiness against NIST CSF 2.0 target profile",
        "gdpr": "Readiness for GDPR obligations",
        "hipaa": "Readiness for HIPAA Security Rule safeguards",
        "pci_dss": "Readiness for PCI DSS v4.0 assessment",
    }
    assert vocab.READINESS_TARGETS == targets
    for framework_id, target in targets.items():
        for critical, high, gaps in (
            (0, 0, "No critical or high gaps open."),
            (1, 0, "1 critical and 0 high gap open."),
            (0, 1, "0 critical and 1 high gap open."),
            (2, 9, "2 critical and 9 high gaps open."),
        ):
            assert vocab.readiness_headline(framework_id, 79.6, critical, high) == (
                f"{target}: Mostly ready (79.6%). {gaps}"
            )


def test_readiness_threshold_description():
    assert vocab.score_threshold_text() == (
        "Ready: 80% and above. Mostly ready: 60% to below 80%. "
        "Partly ready: 40% to below 60%. Not ready: below 40%. "
        "The band uses the exact score; scores are shown to one decimal."
    )
