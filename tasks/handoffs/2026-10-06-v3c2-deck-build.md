# V3-C2: build the approved V3-C deck design into the real board report (PDF)

**Written:** 6 Oct 2026. **For:** one Codex run in worktree `/Users/saqlainmomin/cyberassess-v3c2` (branch `claude/v3c2-deck`, from `origin/main` @ `9cf6977`). **Owner:** Claude reviews adversarially; Saqlain merges and approves by looking at rendered pages. No attribution lines in commits or PR bodies. Codex cannot write `.git`: the orchestrator commits.

## Goal
`app/services/board_report.render_html` produces a 16:9 deck that matches the approved V3-C mockup in `docs/product/2026-10-04-board-deck-v3c-mockup/` (approved 4 Oct, both `deck.pdf` dense and `deck-sparse.pdf`). The mockup is the visual authority; the existing real deck (25 slides) is the functional authority.

## Source of truth
- **Visual:** `deck_template.html` (697 lines, Jinja + WeasyPrint), `render_deck.py::view()` (the presenter prototype, including the action-title sentences and the vertical-rhythm `lay` rule), `pages/deck/*.png` and `pages/deck-sparse/*.png`. Read the PNGs.
- **Functional:** `app/templates/reports/board_report.html`, `app/services/board_view.py`, `tests/test_p6_8_v3b_deck.py`, `tests/test_p6_8_board_report_v2.py`.
- **Design rationale:** `tasks/2026-10-04-deliverables-quality-scope.md` ("Proposed changes to the mockup" table). No radar, no heat map, no donuts: waffle 10x10, sorted bullet bars with rating bands, dumbbell, 3x3 effort-benefit matrix, swimlane roadmap. Status colours reserved for status and always with a label.

## Scope: what to change
| Area | Work |
|---|---|
| `app/services/board_view.py` | Port the mockup `view()` into the real presenter: action titles, waffle cells, bullet-bar geometry, effort-benefit grid, lanes and horizons, dumbbell rows, `lay` rhythm, page map. Keep the existing public shape (`slides` list with `slide`, `number`, `section`, `title`; `obs_pages`, `reg_pages`) so tests and exporters keep working; add fields, don't rename. |
| `app/templates/reports/board_report.html` | Rebuild to the mockup (cover art + framework chips, contents with correct numbers, "How to read the ratings", executive summary with waffle and top-three risk cards, posture, domain status bars, risk profile, board asks, observations, roadmap swimlanes, effort-benefit matrix, since-last-report dumbbell, limits in two columns, sign-off, annexure). Section badge shows the section number, not the slide number. |
| CSS | Inline in the template as today, or `app/static/css/` if the existing deck already loads from there. Minimum type: body 11pt, table 9pt on the 13.33in slide. |
| Cover footer | The old fpdf2 cover path printed `????` for Devanagari; the HTML deck must render the firm and company names through the embedded Noto fonts. Add a render test with a Devanagari company name. |

**Out of scope:** `board_exports.py` (PPTX/XLSX parity is V3-C3), `board_report.build_document`, schema version, migrations, `app/services/prior_period.py`, anything under `validation/`, the Yozora templates and CSS.

## Data rules (do not break)
- **Per-domain prior scores** are in `document["prior_period"]["frameworks"][i]["domains"]` (shape in `tasks/handoffs/2026-10-04-v3c-prior-domain-scores.md`, merged #108). Read `entry.get("domains", [])`: v3 documents issued before #108 lack the key. Dumbbell shows only rows with `compared` true; a domain with no prior shows the current dot only, labelled "new". Never invent a prior score; the mockup's `MOCK_PRIOR_DOMAINS` must not appear in app code.
- **Do not hardcode framework short names.** The mockup has `short = {"dpdpa": "DPDPA", "iso27001": "ISO 27001"}`. Use the registry or the document's `framework_short`. All six frameworks must render.
- **No score combined across frameworks.** Waffle and counts are per framework; totals are counts only.
- **Framework-specific copy conditional** (`has_dpdpa`), never a default.
- **No numeric priority** in client output (V3-K); derived priority stays a label.
- **Only approved content** reaches the deck; the P6-10 narrative stays the only LLM text and keeps its `data-narrative` hooks.
- **Boilerplate once:** the "Narrative paragraphs are drafted from..." sentence appears in the methodology only.
- **Autoescape on; no new dependency.** Charts are inline SVG so WeasyPrint renders them identically.
- **Snapshots are write-once**; v1/v2 sidecars are not re-rendered (they use their frozen renderers).
- **Answer-key independence (D-P5-9-C):** never open `validation/` or any `answer_key.json`.

## Tests
The existing V3-B tests are the functional contract. Slide names and count change (the mockup adds `how-to-read`, `posture`, `effort-benefit`, renames `status-board` to `domain-status` and `risk-dashboard` to `risk-profile`, and merges `ratings`/`initiatives` content as the mockup shows), so:
1. Keep every semantic `data-*` hook the current tests read (`data-observation`, `data-register-row`, `data-narrative`, `data-board-ask`, `data-slide-footer`, `data-takeaway`, `data-prior-period-label`, `data-preview`, etc.). Move a hook with its content to the new slide; do not drop it.
2. Where the mockup replaces a slide, update `EXPECTED_SLIDES`, `SECTION_OF` and the page-count assertions in `tests/test_p6_8_v3b_deck.py` **deliberately** and list each edit and why in `## Results`. Never weaken an assertion to make it pass: change the slide name or number, not what is checked. Keep scenarios 3 to 13 (footer provenance, per-framework scores, narrative panel, roadmap derived priority, no numeric priority, theme colours, 16:9 PDF) semantically intact.
3. Add `tests/test_p6_8_v3c2_extra.py`: (a) page count equals slide count for the golden document and for a thin document (one framework, three findings, no prior period); (b) no slide has an empty bottom third (WeasyPrint box check or rendered-pixel row check); (c) minimum font size 9pt in tables and 11pt in body via computed style in the HTML; (d) dumbbell renders only compared domains and never a mock value; (e) each of the six frameworks renders without a KeyError; (f) Devanagari cover renders (non-`?` glyph path); (g) action titles contain only numbers present in the document.
4. File-set guards: add per-PR allowances (`:(exclude)` pathspec or `tests/yozora_paths.py` entry) for new paths. Never delete a guard. Full suite must pass: `pytest`.

## Verification (smoke test, required)
1. Render the golden document (`tests/golden/p6_8_v3_deck_document.json`) and a thin document to PDF with `pdftoppm -png -r 80`; save page images under `docs/product/2026-10-06-v3c2-renders/{dense,sparse}/`.
2. Compare each page side by side with `docs/product/2026-10-04-board-deck-v3c-mockup/pages/` and list any visible differences in `## Results`.
3. Paste the full `pytest` summary line.

## Results
(Codex fills this in: files changed, test edits with reasons, differences from the mockup, anything that forced a deviation. If the code forces a deviation from a decision, stop and report it here; do not pick an alternative.)
