"""Render a mockup or app route and optionally compare it with a baseline.

The harness intentionally has no app-specific selectors.  Later slices can
reuse it by passing a different source URL and viewport.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping
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
        source_parts = urlsplit(source)
        path = Path(source_parts.path)
        if path.is_absolute():
            path = path.relative_to(REPO_ROOT)
        url = f"{base_url.rstrip('/')}/{path.as_posix()}"
        if source_parts.query or source_parts.fragment:
            url_parts = urlsplit(url)
            url = urlunsplit(
                (url_parts.scheme, url_parts.netloc, url_parts.path, source_parts.query, source_parts.fragment)
            )
    return _with_query(url, state=state, **({"dark": ""} if theme == "dark" else {}))


def _diff_pixels(baseline: Image.Image, candidate: Image.Image, diff: Image.Image) -> int:
    """Use pixelmatch when installed; keep a deterministic Pillow fallback."""
    try:
        from pixelmatch.contrib.PIL import pixelmatch

        return pixelmatch(
            baseline,
            candidate,
            diff,
            threshold=0.1,
            includeAA=False,
            diff_mask=True,
        )
    except ImportError:
        baseline_rgba = baseline.convert("RGBA")
        candidate_rgba = candidate.convert("RGBA")
        changed = ImageChops.difference(baseline_rgba, candidate_rgba)
        mask = changed.convert("L").point(lambda value: 255 if value else 0)
        diff.paste((255, 0, 0, 255), mask=mask)
        return sum(1 for value in mask.getdata() if value)


def _largest_changed_region(diff: Image.Image) -> tuple[int, int, int]:
    """Return (area, width, height) for the largest changed diff-mask component."""
    mask = diff.convert("RGBA")
    pixels = mask.load()
    width, height = mask.size
    changed = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if pixels[x, y][3]
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


def _apply_state(page, state: str | None) -> None:
    """Apply the shell-only states used by the S1 mobile baselines."""
    if state not in {"drawer-open", "drawer-account-menu"}:
        return
    page.evaluate(
        """
        (showMenu) => {
          document.documentElement.classList.add('drawer-open');
          if (showMenu) {
            document.getElementById('userMenu')?.classList.add('open');
            document.getElementById('userBtn')?.setAttribute('aria-expanded', 'true');
          }
        }
        """,
        state == "drawer-account-menu",
    )


def _mask_locators(page, selectors: list[str] | tuple[str, ...] | None):
    masks = page.locator("[data-visual-mask]").all()
    if isinstance(selectors, str):
        selectors = (selectors,)
    for selector_list in selectors or ():
        for selector in selector_list.split(","):
            selector = selector.strip()
            if selector:
                masks.extend(page.locator(selector).all())
    return masks


def _clip_box(page, clip: str | Mapping[str, str]) -> dict[str, int]:
    """Resolve a single-element or paired-edge clip into a screenshot box."""

    def box_for(selector: str) -> dict[str, float]:
        box = page.locator(selector).bounding_box()
        if box is None:
            raise RuntimeError(f"clip selector did not resolve to a visible element: {selector}")
        return box

    if isinstance(clip, str):
        box = box_for(clip)
        return {
            "x": round(box["x"]),
            "y": round(box["y"]),
            "width": round(box["width"]),
            "height": round(box["height"]),
        }

    try:
        top_selector = clip["top"]
        bottom_selector = clip["bottom"]
    except (KeyError, TypeError) as exc:
        raise ValueError("clip config must contain top and bottom selectors") from exc

    top = box_for(top_selector)
    bottom = box_for(bottom_selector)
    top_y = round(top["y"])
    bottom_y = round(bottom["y"] + bottom["height"])
    height = bottom_y - top_y
    if height <= 0:
        raise ValueError(f"clip bottom must be below clip top: {top_selector!r}, {bottom_selector!r}")
    return {
        "x": round(top["x"]),
        "y": top_y,
        "width": round(top["width"]),
        "height": height,
    }


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
        _apply_state(page, args.state)
        page.add_style_tag(
            content="*,:before,:after{animation:none!important;transition:none!important;caret-color:transparent!important}"
        )
        page.evaluate("document.fonts && document.fonts.ready")
        clip = None
        clip_selector = getattr(args, "clip", None)
        if clip_selector:
            clip = _clip_box(page, clip_selector)
        page.screenshot(
            path=str(output),
            full_page=args.full_page and clip is None,
            animations="disabled",
            mask=_mask_locators(page, getattr(args, "mask", None)),
            **({"clip": clip} if clip else {}),
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
    diff_path.parent.mkdir(parents=True, exist_ok=True)
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
    parser.add_argument("--clip", help="CSS selector whose bounding box should be captured")
    parser.add_argument(
        "--mask",
        action="append",
        default=[],
        help="CSS selector to mask; repeat or pass a comma-separated selector list",
    )
    parser.add_argument("--max-diff-percent", type=float, default=0.4)
    parser.add_argument("--full-page", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(render(parse_args()))
