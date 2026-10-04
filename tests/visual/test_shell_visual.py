import os
from argparse import Namespace
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_VISUAL") != "1",
    reason="visual tests require RUN_VISUAL=1 and a local Chromium installation",
)


ROOT = Path(__file__).resolve().parents[2]
APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:8000")
SIDE_TOP_CLIP = {
    "top": ".side-in",
    "bottom": '.side-in > .nav > a[data-nav-key="reports"]',
}


CASES = (
    ("b7-mobile-shell-top", None, 390, 780, ".top", False),
    ("b1-home-default-top", "default", 390, 780, ".top", False),
    ("b7-mobile-shell-sheet-navigation-closed", "navigation-closed", 390, 780, ".top", False),
    ("b7-mobile-shell-sheet-drawer-open", "drawer-open", 390, 780, SIDE_TOP_CLIP, False),
    ("b7-mobile-shell-sheet-drawer-account-menu", "drawer-account-menu", 390, 780, SIDE_TOP_CLIP, False),
    ("b1-home-default-side", "default", 1440, 860, SIDE_TOP_CLIP, False),
    ("b1-home-default-side", "default", 1024, 900, SIDE_TOP_CLIP, False),
)


@pytest.mark.parametrize("theme", ("light", "dark"))
@pytest.mark.parametrize("case_name,state,width,height,clip,full_page", CASES)
def test_app_shell_against_approved_baseline(case_name, state, width, height, clip, full_page, theme):
    from design.harness.screenshot import render

    name = f"{case_name}-{theme}-{width}.png"
    baseline = ROOT / "design" / "baselines" / name
    candidate = ROOT / "design" / "candidates" / name
    assert baseline.exists(), f"missing approved baseline: {baseline}"
    assert render(
        Namespace(
            source=APP_URL,
            base_url="http://127.0.0.1:8000",
            state=state,
            theme=theme,
            width=width,
            height=height,
            output=str(candidate),
            baseline=str(baseline),
            diff=None,
            max_diff_percent=0.4,
            full_page=full_page,
            clip=clip,
        )
    ) == 0
