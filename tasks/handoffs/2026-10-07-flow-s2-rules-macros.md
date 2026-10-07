# Flow rework S2: hierarchy rules, design-pass checklist, macros (Claude terminal account)

Owner: Claude, second account (design + spec lane). Orchestrator: Claude desktop (it verifies, reviews, commits and opens the PR). Written 2026-10-07.
Plan: `docs/plans/2026-10-07-001-flow-rework-plan.md`: read "Design pass", "Who does what", and slice S2. Decisions there are settled; don't re-open them.

You are working in a dedicated worktree on branch `claude/flow-s2-rules`. Leave your changes **uncommitted**; the orchestrator commits and opens the PR.

## Why
The owner's top concern: content must be easy to read and the important information must stand out. Every later slice that touches a screen ends with a design pass against the checklist you write here. S2 is the only purely design slice; there's no app-wide restyle.

## Deliverables
1. **`docs/product/2026-10-07-hierarchy-rules.md`**: one page (aim ≤ 600 words, a printable page). Contents:
   - **Type scale:** the 4-5 text roles a screen uses (page title, section heading, primary value/status, body, secondary/meta) mapped to the existing Yozora tokens and classes. Read `docs/product/yozora-design-system.md`, `design/tokens.json`, `design/yozora-components.css`, `app/static/css/yozora-components.css` and use what exists; don't invent new tokens unless one is clearly missing (if so, say so and add it to both CSS files consistently).
   - **One obvious next action per screen:** what the primary button looks like, where it sits, and that there's only one; secondary actions are visually lighter.
   - **Done state for every step:** a checkmark/done badge on the item, a toast on save, and a stepper tick for the stage. Nothing finishes silently.
   - **How an evidence/RFI item is written:** what it is (human label first, id/code secondary) and why it's requested (one plain sentence). Give two short good/bad examples.
   - **The design-pass checklist** (final wording of the five checks in the plan, "Design pass" section), as a copy-pasteable markdown checklist a PR can fill in per screen.
2. **Macros in `app/templates/components/`** (add to `ui.html` if that's where macros live, or a new `components/flow.html`; match how existing macros are written and imported):
   - `done_state(label, detail=None)`: the checkmark + label used when a step is complete.
   - `next_step(title, href, button_label, detail=None)`: the "next step" banner with the single primary action.
   - Use existing Yozora classes; add CSS only if needed, in `app/static/css/yozora-components.css` (and `design/yozora-components.css` if that is the mirrored source; check how the two relate before editing).
   - Don't apply them to any screen yet (later slices do). A short usage example belongs in the rules doc, not in a template.
   - One small render test is acceptable (macro renders with/without `detail`) only if it's a few lines; no snapshot or pixel tests.
3. **Flow doc follow-ups rows (decision P7/B):** in `docs/product/2026-10-06-consultant-journey-flow.html`, rewrite the Follow-ups rows that say follow-ups are "generated after analysis" to match decision B: follow-ups stay inline in the questionnaire, generated when an answer triggers them and answered in place. Change only those rows.

## Rules
- Docs + macros + (maybe) CSS only. No route, model, service or other template changes.
- No new pixel gates, path guards, snapshot tests.
- Plain, short sentences. No em dashes.
- If something in the plan is ambiguous, pick the simplest reading and note it in Results.

## Verification
- `.venv/bin/pytest -q -p no:cacheprovider` green (if you can run it; otherwise say so and the orchestrator runs it).
- Render both macros once (a throwaway Jinja snippet or the app) and confirm the HTML is sane; describe what you checked.

## Results
No blocking problems found. All changes uncommitted.

**Files changed**
- `docs/product/2026-10-07-hierarchy-rules.md` (new, 517 words): type scale, one next action, done state, RFI item wording with two good/bad pairs, the five-check design-pass checklist as a copyable block, macro usage example.
- `app/templates/components/ui.html`: added `done_state(label, detail=None)` and `next_step(title, href, button_label, detail=None)`, placed before `request_marker`. Same file and style as the existing macros; `next_step` reuses `link_button`, `done_state` reuses `icon`.
- `docs/product/2026-10-06-consultant-journey-flow.html`: rewrote the first Follow-ups row (the "created after analysis" one) to say follow-ups stay inline, generated when an answer triggers them, answered in place (decision B). No other row changed.

**Tokens/CSS:** none added. `design/yozora-components.css` and `app/static/css/yozora-components.css` are byte-identical mirrors, and neither was touched. The macros use existing classes (`.status`, `.sub`, `.rows`, `.solid`, `.ico.accent`, `.btn.primary`). `done-state` and `next-step` are marker classes with no CSS.

**Ambiguities**
- The "today" line for Follow-ups already says follow-ups are inline, so I left it alone per "change only those rows". Decision B in the DECISIONS list at the bottom of the flow doc is still worded as an open question; I did not touch it.
- `.sub` inside `.status` inherits the status layout, so detail text sits inline beside the label. I did not add CSS for it. Check it visually when first used.
- Rules doc says the primary button sits last in the page header actions, taken from the design system "Patterns" section.
- No render test added (a throwaway render was enough).

**Verification**
- Rendered both macros with and without `detail` via a throwaway Jinja script (scratchpad, not in the repo). Output is sane HTML: `done_state` gives a circle-check svg, bold label and optional `.sub`. `next_step` gives a `.rows.solid` row with arrow icon, title, optional `.sub`, and one `a.btn.primary`. `detail` omitted leaves no empty element.
- `.venv/bin/pytest -q -p no:cacheprovider`: 1594 passed, 30 skipped, 0 failed (242 s).
- I did not view the macros in a browser, so the visual layout is unchecked.
