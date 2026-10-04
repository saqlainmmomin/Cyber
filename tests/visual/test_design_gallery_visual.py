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


@pytest.mark.parametrize("theme", ("light", "dark"))
@pytest.mark.parametrize("width,height", ((1440, 900), (1024, 900), (390, 780)))
def test_design_gallery_against_approved_baseline(width, height, theme):
    from design.harness.screenshot import render

    name = f"design-gallery-{theme}-{width}.png"
    baseline = ROOT / "design" / "baselines" / name
    assert baseline.exists(), f"missing approved baseline: {baseline}"
    assert render(
        Namespace(
            source=f"{APP_URL}/design",
            base_url=APP_URL,
            state=None,
            theme=theme,
            width=width,
            height=height,
            output=str(ROOT / "design" / "candidates" / name),
            baseline=str(baseline),
            diff=None,
            max_diff_percent=0.2,
            full_page=True,
            clip=None,
        )
    ) == 0
