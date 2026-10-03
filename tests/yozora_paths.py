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
    "tests/test_white_label.py",
    "tests/test_yozora_shell.py",
    "tests/visual/test_shell_visual.py",
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

YOZORA_ALL_PATHS = YOZORA_S1_PATHS + YOZORA_DESIGN_FILES
YOZORA_EXCLUDES = [f":(exclude){path}" for path in YOZORA_ALL_PATHS]
