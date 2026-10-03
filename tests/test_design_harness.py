from PIL import Image, ImageDraw

from design.harness.screenshot import _clip_box, _diff_pixels, _largest_changed_region


def _changed_block(size: tuple[int, int], block_size: int) -> tuple[Image.Image, Image.Image]:
    baseline = Image.new("RGBA", size, (255, 255, 255, 255))
    candidate = baseline.copy()
    ImageDraw.Draw(candidate).rectangle(
        (10, 10, 9 + block_size, 9 + block_size),
        fill=(0, 0, 0, 255),
    )
    return baseline, candidate


def _compare(baseline: Image.Image, candidate: Image.Image) -> tuple[int, tuple[int, int, int]]:
    diff = Image.new("RGBA", baseline.size, (0, 0, 0, 0))
    changed = _diff_pixels(baseline, candidate, diff)
    return changed, _largest_changed_region(diff)


def test_identical_images_have_no_changed_region():
    image = Image.new("RGBA", (100, 100), (255, 255, 255, 255))

    changed, region = _compare(image, image.copy())

    assert changed == 0
    assert region == (0, 0, 0)


def test_fifty_pixel_changed_block_exceeds_region_limit():
    baseline, candidate = _changed_block((100, 100), 50)

    changed, region = _compare(baseline, candidate)

    assert changed > 0
    assert region[1:] == (50, 50)
    assert region[1] > 40 and region[2] > 40


def test_thirty_pixel_changed_block_stays_within_region_limit():
    baseline, candidate = _changed_block((100, 100), 30)

    changed, region = _compare(baseline, candidate)

    assert changed > 0
    assert region[1:] == (30, 30)
    assert not (region[1] > 40 and region[2] > 40)


def test_clip_config_spans_from_panel_top_to_home_row():
    class Locator:
        def __init__(self, box):
            self.box = box

        def bounding_box(self):
            return self.box

    class Page:
        boxes = {
            ".side-in": {"x": 12, "y": 52, "width": 244, "height": 836},
            '.side-in > .nav > a[aria-current="page"]': {"x": 20, "y": 160, "width": 228, "height": 32},
        }

        def locator(self, selector):
            return Locator(self.boxes[selector])

    assert _clip_box(
        Page(),
        {
            "top": ".side-in",
            "bottom": '.side-in > .nav > a[aria-current="page"]',
        },
    ) == {"x": 12, "y": 52, "width": 244, "height": 140}
