"""S8 pixel gate: seed one state, serve the app and mockups, and compare screenshots.

    python design/harness/gate_s8.py b6-rfi:default b6-soa --out /tmp/s8-gate

Each target is ``screen`` (every registered state) or ``screen:state``. The
screen must be registered by an S8 group module and provide ``route``. Mockups
are served from the repository root with ``/static/`` mapped to ``app/static/``.
The gate uses the shared 0.4% differing-pixel threshold and rejects a changed
region larger than 40x40 pixels. Client screens are also captured at 390px.
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import io
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from argparse import Namespace
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from design.harness import screenshot  # noqa: E402
from design.harness.seed_s8 import _module_for, screen_states, seed_s8  # noqa: E402

MOCKUPS = "docs/product/2026-10-01-app-design-mockups/screens"
WIDTHS = (1440, 1024)
CLIENT_WIDTHS = (390, 1440)
CLIENT_SCREENS = {"b6-magic_upload", "b6-magic_invalid", "b7-link-expired"}
THEMES = ("light", "dark")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _MockupHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.startswith("/static/"):
            return str(REPO_ROOT / "app" / path.lstrip("/"))
        return super().translate_path(path)

    def log_message(self, *args):
        pass


def _start_mockup_server():
    port = _free_port()
    handler = functools.partial(_MockupHandler, directory=str(REPO_ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{port}"


def _start_app(db_path: str):
    port = _free_port()
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}", "OPENROUTER_KEY": "", "DEBUG": "1"}
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=REPO_ROOT,
        env=env,
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(base + "/health", timeout=1)
            break
        except Exception:
            try:
                urllib.request.urlopen(base + "/", timeout=1)
                break
            except urllib.error.HTTPError:
                break
            except Exception:
                time.sleep(0.3)
    return proc, base


HIDE_STATE_ROWS = (
    "document.querySelectorAll('span.chip').forEach(c => {"
    " if (c.textContent.trim() === 'State' && c.parentElement) c.parentElement.style.display = 'none'; });"
    " document.querySelectorAll('[data-mock-state]').forEach(s => { s.style.marginTop = '0'; });"
)


def _shoot(source: str, base_url: str, state: str | None, theme: str, width: int, output: Path, *, content: bool = False, mockup: bool = False) -> None:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        screenshot.render(
            Namespace(
                source=source,
                base_url=base_url,
                state=state,
                theme=theme,
                width=width,
                height=900,
                output=str(output),
                baseline=None,
                diff=None,
                max_diff_percent=0.4,
                full_page=True,
                clip=".page" if content else None,
                mask=[],
                prep_js=HIDE_STATE_ROWS if (content and mockup) else None,
            )
        )


def _compare(baseline: Path, candidate: Path, diff_path: Path) -> tuple[float, str, str]:
    base, cand = Image.open(baseline).convert("RGBA"), Image.open(candidate).convert("RGBA")
    note = ""
    if base.size != cand.size:
        note = f"size mismatch {base.size} vs {cand.size}"
        width, height = max(base.width, cand.width), max(base.height, cand.height)
        padded_base = Image.new("RGBA", (width, height), (255, 0, 255, 255))
        padded_candidate = Image.new("RGBA", (width, height), (255, 0, 255, 255))
        padded_base.paste(base, (0, 0))
        padded_candidate.paste(cand, (0, 0))
        base, cand = padded_base, padded_candidate
    diff = Image.new("RGBA", base.size, (0, 0, 0, 0))
    changed = screenshot._diff_pixels(base, cand, diff)
    diff.save(diff_path)
    pct = changed / (base.width * base.height) * 100
    _, region_width, region_height = screenshot._largest_changed_region(diff)
    return pct, f"{region_width}x{region_height}", note


def run(targets: list[str], out: Path, content: bool = False) -> int:
    out.mkdir(parents=True, exist_ok=True)
    mock_server, mock_base = _start_mockup_server()
    states = screen_states()
    jobs = []
    for target in targets:
        screen, _, state = target.partition(":")
        for item in ([state] if state else states[screen]):
            jobs.append((screen, item))
    failures = 0
    rows = []
    try:
        for screen, state in jobs:
            db_path = out / f"{screen}-{state}.sqlite3"
            info = seed_s8(db_path, screen=screen, state=state)
            module = _module_for(screen)
            path = module.route(screen, state, info["assessment_id"])
            proc, app_base = _start_app(str(db_path))
            try:
                widths = CLIENT_WIDTHS if screen in CLIENT_SCREENS else WIDTHS
                for theme in THEMES:
                    for width in widths:
                        stem = f"{screen}-{state}-{theme}-{width}"
                        base_png = out / f"{stem}-baseline.png"
                        candidate_png = out / f"{stem}-candidate.png"
                        diff_png = out / f"{stem}-diff.png"
                        _shoot(f"{MOCKUPS}/{screen}.html", mock_base, state, theme, width, base_png, content=content, mockup=True)
                        _shoot(app_base + path, app_base, None, theme, width, candidate_png, content=content)
                        pct, region, note = _compare(base_png, candidate_png, diff_png)
                        region_size = re.fullmatch(r"(\d+)x(\d+)", region)
                        oversized = region_size and all(int(value) > 40 for value in region_size.groups())
                        ok = pct <= 0.4 and not oversized and not note
                        failures += 0 if ok else 1
                        row = f"| {screen} | {state} | {theme} | {width} | {pct:.3f}% | {region} | {info['data_state']} | {'pass' if ok else 'FAIL'} {note} |"
                        rows.append(row)
                        print(row, flush=True)
            finally:
                proc.terminate()
                proc.wait(timeout=10)
    finally:
        mock_server.shutdown()
        results = out / ("results-content.md" if content else "results.md")
        header = "" if results.exists() else "| screen | state | theme | width | diff | largest region | data | verdict |\n|---|---|---|---|---|---|---|---|\n"
        with results.open("a") as handle:
            handle.write(header + "\n".join(rows) + "\n")
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="+")
    parser.add_argument("--out", default="/tmp/s8-gate")
    parser.add_argument("--content", action="store_true", help="compare only the main column and hide the mockup State row")
    args = parser.parse_args()
    raise SystemExit(run(args.targets, Path(args.out), args.content))
