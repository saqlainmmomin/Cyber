# Yozora visual harness

Install the pinned development dependencies and Chromium once:

```bash
pip install -r requirements-dev.txt
playwright install chromium
```

Serve the repository root in another terminal for approved mockups:

```bash
python3 -m http.server 8000
```

Render a mockup or app route at a deterministic viewport. The source may be a
repo-relative mockup path or a complete URL:

```bash
python3 design/harness/screenshot.py \
  docs/product/2026-10-01-app-design-mockups/screens/b7-mobile-shell.html \
  --width 390 --height 780 --theme dark \
  --output design/baselines/b7-mobile-shell-dark-390.png

python3 design/harness/screenshot.py http://127.0.0.1:8000/ \
  --width 1440 --height 900 --baseline design/baselines/b1-home-light-1440.png \
  --output design/candidates/b1-home-light-1440.png
```

Use `--state <name>` for mockup states, `--full-page` for a complete page, and
`--max-diff-percent 0.2` for `/design` baselines. The command writes a diff
beside the candidate when a baseline is supplied and fails above the fidelity
gate threshold or when a changed region is wider or taller than 40 pixels.

## S1 visual masks

The S1 visual tests pass the following selectors to both the approved mockup
render and the app candidate with `--mask`:

- `.nav a:not(:first-child)` masks future navigation entries below Home; those
  entries are present in the mockup but intentionally unavailable in S1.
- `.side-foot .nav a` masks the firm navigation item until its slice owns the
  destination.
- `.user .avatar, .user .name` masks the firm-specific account initial and
  name in the account tile.
- `.menu` masks the account-menu body, whose contents are intentionally
  workspace-specific in S1.

The app shell also marks these regions with `data-visual-mask`, so later slices
can remove a selector from the test and unmask their own content. The harness
always combines both sources of masks; `--mask` may be repeated or receive a
comma-separated selector list.
