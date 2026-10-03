# Yozora fidelity gate

Purpose: make drift between the approved mockups and the shipped app mechanically detectable. Owner of the spec: Claude. Owner of the harness build: Codex (slice S1/S2). Decided 2026-10-01.

## Gates (a slice is not done until all five pass)

1. **Single source of values.** `design/tokens.json` is the only place values live. `design/tokens_tool.py` (exists) parses the CSS today; at S1 it flips: the generator writes `app/static/css/yozora-tokens.css` and `tailwind.config.js` theme from `tokens.json`. Test `tests/test_design_tokens_in_sync.py` regenerates in memory and fails on any diff.
2. **Gallery route.** `GET /design` (debug-only, 404 when `ENV=production`) renders every component in every state, light and dark, from the real Jinja components, not copies. Baseline: `screens/gallery.html`.
3. **Pixel gate.** Playwright screenshots of `/design` and of each migrated screen at 1440 and 1024 (and 390 for client-facing pages), light and dark, against approved baselines stored in `design/baselines/<screen>-<theme>-<width>.png` (generated from the approved mockups served at the same viewport, with seeded demo data and fonts vendored so rendering is deterministic). Chromium fixed to the version in `requirements-dev`; animations disabled; clock frozen; `deviceScaleFactor` 1.
   - **Thresholds:** per-pixel colour tolerance 0.1 (pixelmatch), then fail when more than **0.4%** of pixels differ on app screens, **0.2%** on `/design`. Any single changed region over 40x40 px fails regardless of the total. These start strict on purpose; loosening needs a written reason in the PR.
   - Dynamic regions (timestamps, generated ids) are masked via `data-visual-mask`; structural regions that differ between an approved mockup and an in-progress slice are compared with an explicit clip instead of painted masks.
4. **Human gate.** Saqlain sees the screenshots (candidate beside baseline, plus the diff image) before merge. CI green is necessary, not sufficient.
5. **Lint (grep-able, run in pytest).** In `app/templates` and `app/static/css/src`:
   - no `uppercase` or `text-transform`;
   - no hex colours or Tailwind arbitrary values (`[#...]`, `[12px]`);
   - no lettered or numbered headings (`^(Step )?\d+[.)]`, `^[A-Z][.)]\s`) and no `<h[1-6]>` starting with them;
   - at most one `.btn.primary` per rendered page in the screenshot run;
   - no `background-clip:text`, no `blur-3xl`.

## Rules for the builder

If a visual detail is not in `docs/product/yozora-design-system.md` or the approved mockup, stop and ask; do not invent. Keep every must-keep id, `hx-*` and `data-*` from `docs/product/yozora-migration-map.md`. Add `:(exclude)` allowances to the per-PR file-set guard; never delete guards (see memory note on stale guards).
