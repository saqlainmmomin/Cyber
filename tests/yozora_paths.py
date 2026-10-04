"""Per-PR path allowance for the Yozora S1 design-system slice."""

YOZORA_S1_PATHS = (
    "app/database.py",
    "app/template_config.py",
    "app/templates/base.html",
    "app/static/css/style.css",
    "app/static/css/src/fonts.css",
    "app/static/css/src/shell.css",
    "app/static/css/yozora-tokens.css",
    "app/static/css/yozora-components.css",
    "app/static/css/yozora-patterns.css",
    "app/static/fonts/Inter-Medium.woff2",
    "app/static/fonts/Inter-Regular.woff2",
    "app/static/fonts/Inter-SemiBold.woff2",
    "app/static/fonts/OFL-Inter.txt",
    "app/static/fonts/README.md",
    "app/static/vendor/htmx-2.0.4.min.js",
    "design/tokens.json",
    "design/tokens_tool.py",
    "design/yozora-tokens.css",
    "design/yozora-components.css",
    "design/yozora-patterns.css",
    "design/harness/screenshot.py",
    "design/harness/README.md",
    "docs/product/yozora-design-system.md",
    "requirements-dev.txt",
    "tailwind.config.js",
    "tailwind.tokens.cjs",
    "tasks/todo.md",
    "tests/design_lint_allowlist.txt",
    "tests/test_design_lint.py",
    "tests/test_p6_0c_dev_hygiene.py",  # dev-requirements pin gained the S1 visual-harness packages
    "tests/test_design_tokens_in_sync.py",
    "tests/test_design_harness.py",
    "tests/test_white_label.py",
    "tests/test_yozora_shell.py",
    "tests/visual/test_shell_visual.py",
    "tests/visual/test_design_gallery_visual.py",
    "tests/yozora_paths.py",
)

YOZORA_S2_PATHS = (
    "app/config.py",
    "app/main.py",
    "app/routers/design.py",
    "app/static/css/yozora-components.css",
    "app/static/css/yozora-patterns.css",
    "app/static/css/yozora-tokens.css",
    "app/templates/components/engagement_status_badge.html",
    "app/templates/components/evidence_status_badge.html",
    "app/templates/components/layout.html",
    "app/templates/components/status_badge.html",
    "app/templates/components/ui.html",
    "app/templates/pages/design.html",
    "tailwind.tokens.cjs",
    "tasks/handoffs/2026-10-01-yozora-s2-handoff.md",
    "tasks/todo.md",
    "tests/design_lint_allowlist.txt",
    "tests/test_design_lint.py",
    "tests/test_yozora_s2.py",
    "tests/p6_10_support.py",  # Yozora per-PR allowance (guard file)
    "tests/test_p6_3a_grounding.py",  # Yozora per-PR allowance (guard file)
    "tests/test_p6_7_requirement_card.py",  # Yozora per-PR allowance (guard file)
    "tests/test_p6_7b_add_to_rfi.py",  # Yozora per-PR allowance (guard file)
    "tests/test_p6_8_b2_docx_xlsx.py",  # Yozora per-PR allowance (guard file)
    "tests/test_p6_8_board_report_v2.py",  # Yozora per-PR allowance (guard file)
    "tests/test_p6_8_v3a_data_capture.py",  # Yozora per-PR allowance (guard file)
    "tests/test_p6_9_file_set.py",  # Yozora per-PR allowance (guard file)
    "tests/test_retention.py",  # Yozora per-PR allowance (guard file)
    "tests/yozora_paths.py",
)

YOZORA_DESIGN_FILES = (
    "design/tokens.json",
    "design/tokens_tool.py",
    "design/yozora-components.css",
    "design/yozora-patterns.css",
    "design/yozora-tokens.css",
    "design/harness",
    "docs/product/yozora-design-system.md",
    "docs/product/2026-10-01-app-design-mockups",
    "tasks/handoffs/2026-10-01-yozora-s1-handoff.md",
)

# Per-PR allowance: V3-C board deck design pass (mockup, scope, dumbbell backend handoff).
V3C_MOCKUP_PATHS = (
    "docs/product/2026-10-04-board-deck-v3c-mockup/deck_template.html",
    "docs/product/2026-10-04-board-deck-v3c-mockup/render_deck.py",
    "docs/product/2026-10-04-board-deck-v3c-mockup/deck.pdf",
    "docs/product/2026-10-04-board-deck-v3c-mockup/deck-sparse.pdf",
    "tasks/2026-10-04-deliverables-quality-scope.md",
    "tasks/handoffs/2026-10-04-v3c-prior-domain-scores.md",
    "tests/test_p6_8_v3b_file_set.py",
)

YOZORA_ALL_PATHS = YOZORA_S1_PATHS + YOZORA_S2_PATHS + YOZORA_DESIGN_FILES + V3C_MOCKUP_PATHS
YOZORA_EXCLUDES = [f":(exclude){path}" for path in YOZORA_ALL_PATHS]
