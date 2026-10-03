"""Render a mockup or app route and optionally compare it with a baseline.

The harness intentionally has no app-specific selectors.  Later slices can
reuse it by passing a different source URL and viewport.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from PIL import Image, ImageChops


REPO_ROOT = Path(__file__).resolve().parents[2]


def _with_query(url: str, **params: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update({key: value for key, value in params.items() if value is not None})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _source_url(source: str, base_url: str, state: str | None, theme: str) -> str:
    if source.startswith(("http://", "https://")):
        url = source
    else:
        path = Path(source)
        if path.is_absolute():
            path = path.relative_to(REPO_ROOT)
        url = f"{base_url.rstrip('/')}/{path.as_posix()}"
    return _with_query(url, state=state, **({"dark": ""} if theme == "dark" else {}))


def _diff_pixels(baseline: Image.Image, candidate: Image.Image, diff: Image.Image) -> int:
    """Use pixelmatch when installed; keep a deterministic Pillow fallback."""
    try:
        from pixelmatch.contrib.PIL import pixelmatch

        return pixelmatch(baseline, candidate, diff, threshold=0.1)
    except ImportError:
        baseline_rgba = baseline.convert("RGBA")
        candidate_rgba = candidate.convert("RGBA")
        changed = ImageChops.difference(baseline_rgba, candidate_rgba)
        mask = changed.convert("L").point(lambda value: 255 if value else 0)
        diff.paste((255, 0, 0, 255), mask=mask)
        return sum(1 for value in mask.getdata() if value)


def _largest_changed_region(diff: Image.Image) -> tuple[int, int, int]:
    """Return (area, width, height) for the largest changed component."""
    mask = diff.convert("RGBA")
    pixels = mask.load()
    width, height = mask.size
    changed = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if pixels[x, y][0] or pixels[x, y][1] or pixels[x, y][2]
    }
    largest_area = 0
    largest_width = 0
    largest_height = 0
    while changed:
        start = changed.pop()
        stack = [start]
        area = 1
        min_x = max_x = start[0]
        min_y = max_y = start[1]
        while stack:
            x, y = stack.pop()
            for neighbour in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbour not in changed:
                    continue
                changed.remove(neighbour)
                stack.append(neighbour)
                area += 1
                min_x = min(min_x, neighbour[0])
                max_x = max(max_x, neighbour[0])
                min_y = min(min_y, neighbour[1])
                max_y = max(max_y, neighbour[1])
        largest_area = max(largest_area, area)
        largest_width = max(largest_width, max_x - min_x + 1)
        largest_height = max(largest_height, max_y - min_y + 1)
    return largest_area, largest_width, largest_height


def render(args: argparse.Namespace) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Install requirements-dev.txt and run `playwright install chromium`.") from exc

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    url = _source_url(args.source, args.base_url, args.state, args.theme)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=1,
        )
        page.emulate_media(reduced_motion="reduce")
        page.add_init_script(
            """localStorage.setItem('theme', %r);""" % ("dark" if args.theme == "dark" else "light")
        )
        if hasattr(page, "clock"):
            page.clock.install(time="2026-10-03T12:00:00Z")
        page.goto(url, wait_until="networkidle")
        page.add_style_tag(
            content="*,:before,:after{animation:none!important;transition:none!important;caret-color:transparent!important}"
        )
        page.evaluate("document.fonts && document.fonts.ready")
        masks = page.locator("[data-visual-mask]").all()
        page.screenshot(
            path=str(output),
            full_page=args.full_page,
            animations="disabled",
            mask=masks,
        )
        browser.close()

    if not args.baseline:
        print(f"wrote {output}")
        return 0

    baseline_path = Path(args.baseline)
    baseline = Image.open(baseline_path).convert("RGBA")
    candidate = Image.open(output).convert("RGBA")
    if baseline.size != candidate.size:
        print(f"size mismatch: baseline={baseline.size} candidate={candidate.size}", file=sys.stderr)
        return 1
    diff = Image.new("RGBA", baseline.size, (0, 0, 0, 0))
    changed = _diff_pixels(baseline, candidate, diff)
    diff_path = Path(args.diff or output.with_name(output.stem + "-diff.png"))
    diff.save(diff_path)
    percentage = changed / (baseline.width * baseline.height) * 100
    largest_area, largest_width, largest_height = _largest_changed_region(diff)
    print(
        f"{output}: {percentage:.4f}% differing pixels; "
        f"largest region area={largest_area}, size={largest_width}x{largest_height}px"
    )
    if percentage > args.max_diff_percent or (largest_width > 40 and largest_height > 40):
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Mockup path or absolute app URL")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--state")
    parser.add_argument("--theme", choices=("light", "dark"), default="light")
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--output", required=True)
    parser.add_argument("--baseline")
    parser.add_argument("--diff")
    parser.add_argument("--max-diff-percent", type=float, default=0.4)
    parser.add_argument("--full-page", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(render(parse_args()))
