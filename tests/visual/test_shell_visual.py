import os
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_VISUAL") != "1",
    reason="visual tests require RUN_VISUAL=1 and a local Chromium installation",
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("theme", "width"),
    [("light", 1440), ("dark", 1440), ("light", 1024), ("dark", 1024), ("light", 390), ("dark", 390)],
)
def test_home_shell_against_baseline(theme, width):
    from design.harness.screenshot import render
    from argparse import Namespace

    name = f"b1-home-{theme}-{width}.png"
    baseline = ROOT / "design" / "baselines" / name
    candidate = ROOT / "design" / "candidates" / name
    assert baseline.exists(), f"missing approved baseline: {baseline}"
    assert render(
        Namespace(
            source="docs/product/2026-10-01-app-design-mockups/screens/b1-home.html",
            base_url="http://127.0.0.1:8000",
            state="default",
            theme=theme,
            width=width,
            height=900 if width > 390 else 780,
            output=str(candidate),
            baseline=str(baseline),
            diff=None,
            max_diff_percent=0.4,
            full_page=False,
        )
    ) == 0
