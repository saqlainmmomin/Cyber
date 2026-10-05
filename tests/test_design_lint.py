import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "app" / "templates"
CSS_ROOT = ROOT / "app" / "static" / "css" / "src"
ALLOWLIST = {
    line.strip()
    for line in (ROOT / "tests" / "design_lint_allowlist.txt").read_text().splitlines()
    if line.strip() and not line.startswith("#")
}
MIGRATED_TEMPLATES = {
    "components/engagement_status_badge.html",
    "components/evidence_status_badge.html",
    "components/status_badge.html",
    "components/layout.html",
    "components/ui.html",
    "pages/design.html",
    "pages/evidence_inventory.html",
    # Yozora per-PR allowance (S5)
    "partials/framework_hub_panel.html",
    "pages/design_assessment_preview.html",
    "partials/desk_review_prefilling.html",
    "pages/desk_review.html",  # s5-b4: live b4 page
}


def _template_files():
    return sorted(TEMPLATE_ROOT.rglob("*.html"))


def _lint_files():
    files = []
    for path in _template_files():
        relative = path.relative_to(TEMPLATE_ROOT).as_posix()
        if relative not in ALLOWLIST:
            files.append(path)
    files.extend(sorted(CSS_ROOT.rglob("*.css")))
    return files


def _contents():
    return [(path, path.read_text()) for path in _lint_files()]


def _assert_no_pattern(pattern, label):
    regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    failures = [str(path.relative_to(ROOT)) for path, text in _contents() if regex.search(text)]
    assert not failures, f"{label} found in: {', '.join(failures)}"


def test_no_uppercase_utility_or_text_transform():
    _assert_no_pattern(r"\buppercase\b|text-transform", "uppercase styling")


def test_no_hex_colours_or_arbitrary_tailwind_values():
    _assert_no_pattern(r"#[0-9a-f]{3,8}\b|\[[^\]]*(?:px|#)[^\]]*\]", "hard-coded design value")


def test_no_lettered_or_numbered_headings():
    _assert_no_pattern(
        r"<h[1-6][^>]*>\s*(?:(?:Step\s+)?\d+[.)]|[A-Z][.)])\s",
        "lettered or numbered heading",
    )


def test_no_forbidden_visual_effects():
    _assert_no_pattern(r"background-clip\s*:\s*text|blur-3xl", "forbidden visual effect")


def test_unmigrated_templates_are_explicitly_allowlisted():
    unmigrated = {
        path.relative_to(TEMPLATE_ROOT).as_posix()
        for path in _template_files()
        if path.name != "base.html"
    }
    assert unmigrated <= ALLOWLIST | MIGRATED_TEMPLATES


def test_shell_has_at_most_one_primary_marker():
    base = (TEMPLATE_ROOT / "base.html").read_text()
    assert base.count("btn primary") <= 1
