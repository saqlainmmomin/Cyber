from design import tokens_tool


def test_generated_design_files_match_tokens_json():
    assert tokens_tool.check() == 0


def test_line_strong_is_preserved_until_the_contrast_decision():
    tokens = tokens_tool.load_tokens()
    assert tokens[":root"]["--line-strong"] == "rgba(30,36,56,.14)"
    assert tokens["[data-theme=dark]"]["--line-strong"] == "rgba(255,255,255,.13)"


def test_generated_component_and_pattern_copies_are_byte_identical():
    files = tokens_tool.generated_files()
    assert files[tokens_tool.STATIC_CSS_DIR / "yozora-components.css"] == (
        tokens_tool.DESIGN_DIR / "yozora-components.css"
    ).read_text()
    assert files[tokens_tool.STATIC_CSS_DIR / "yozora-patterns.css"] == (
        tokens_tool.DESIGN_DIR / "yozora-patterns.css"
    ).read_text()
