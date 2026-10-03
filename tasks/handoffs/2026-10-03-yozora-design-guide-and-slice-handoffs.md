# Yozora: update the design guide to the approved mockups, then regenerate the nine build handoffs

**Written:** 2026-10-03. **For:** a fresh Claude session. **Repo/worktree:** `/Users/saqlainmomin/cyberassess-docs`, branch `claude/app-design-kickoff`. PR #97 (mockups) is merged; this file and the last mockup follow-ups are in PR https://github.com/saqlainmmomin/Cyber/pull/98 (open; merging is Saqlain's). Keep committing to `claude/app-design-kickoff` while #98 is open; if it has been merged when you start, branch `claude/yozora-slice-handoffs` from `main` and open a new PR. Commit with the standard `Co-Authored-By` trailer only, no other attribution.

## Goal
The approved mockups are now the source of truth, but two downstream documents still describe the earlier design. You will:
- update `docs/product/yozora-design-system.md` (the design guide) so it matches the approved mockups;
- rewrite the nine Codex build handoffs (`tasks/handoffs/2026-10-01-yozora-s1-handoff.md` … `-s9-handoff.md`) so each one is a complete brief Codex can build from without asking.

A later fresh Claude session will orchestrate Codex through S1 to S9 and review its work. Your last step is to write that session's kickoff file.

**Done when:**
- The design guide matches the mockups, `IA-SPEC.md` and the flow map.
- All nine slice handoffs are rewritten, accurate against the current templates and tests, and read through end to end.
- The orchestration kickoff is written.
- Checks pass, the work is committed and pushed, and Results are filled in.

## Current state (what was decided; do not relitigate)
- **Mockups approved by Saqlain** (1 to 3 Oct 2026): 61 screens in `docs/product/2026-10-01-app-design-mockups/screens/`.
  - Shared CSS is in `design/`: `yozora-tokens.css`, `yozora-components.css`, `yozora-patterns.css`. `mockup-chrome.css` is mockup-only.
  - `design/tokens.json` is checked by `python3 design/tokens_tool.py check`.
- **Information architecture** is in `screens/IA-SPEC.md` and `docs/product/2026-10-01-app-design-mockups/flow-map.html`:
  - Side menu: Home, Clients, Engagements, Review, Evidence, Reports; Settings at the bottom.
  - Engagement tabs: Overview, Evidence, Findings and actions, Reports.
  - Assessment tabs: Overview, Scope, Questionnaire, Review, Report.
  - One five-stage stepper (Scope, Evidence, Questionnaire, Review, Report), on the assessment Overview only.
  - Sub-views use a single `.seg` row (Evidence: Inventory | Requests; Review: Queue | Conclusions | Findings | Workpaper; Report: Report | Versions | Applicability). Detail pages use the breadcrumb for depth.
  - Framework tabs inside Report, statement of applicability and Compare keep their `.tabs` row.
  - Breadcrumbs are always complete (client / engagement / assessment / page).
  - An engagement with one assessment opens straight on that assessment.
- **Evidence.** One inventory per engagement (`b4-evidence.html`) replaces the old Documents tab, AWS evidence tab and client-links page.
  - Status labels follow the real states: quarantined → Scanning, active → Available, rejected → Rejected, invalidated → Out of date.
  - Evidence reuse happens between assessments of the same engagement (`app/services/evidence_reuse.py`), not from earlier engagements.
- **Pre-fill (desk review)** runs per assessment and starts from the Questionnaire tab. `b4-desk_review` is Assessment / Questionnaire / Pre-fill from documents.
- **Retention** moves from client and engagement pages to firm Settings, under data housekeeping. The engagement keeps only Archive.
- **Client links** (`b6-magic_links` staff side, `b6-magic_upload` client page) are request cards: requested items, "N of M received", expiry, per-item checklist. They use the new `.req*` / `.mk` components in `yozora-patterns.css`.
- **Settled rules:**
  - Signed-in user assumed: no reviewer-name inputs in the designs. The build keeps a temporary name field until Track 4 auth.
  - Neutral score ring.
  - Firm accent must pass 4.5:1 at upload.
  - At most one primary per state, and none in states with no real action (never a disabled primary).
  - Control codes in small muted text in lists.
  - Priority as words (Do first, Next, Planned, Backlog).
  - Answer scale: Fully implemented, Partially implemented, Planned, Not implemented, Not applicable.
  - Screening is DPDPA-only.
  - Evidence reuse uses tick boxes plus one confirm button.
  - No combined cross-framework report view.
  - Statement of applicability saves in one action.
  - One Generate button follows the selected report tab.
  - Toasts last 4 s; errors stay until closed.
  - Delete confirms by typing the name.
  - The error page shows a reference code.
- **Kept features the app does not have yet** (each needs backend work in its slice):
  - Add assessment (engagement Overview)
  - Export actions (Findings and actions)
  - Open current report (comparison page)
  - Email the firm (expired-link pages), backed by a new firm Settings field "Contact email for clients"
  - Client contact name and email on magic links
  - Firm-level retention period
- **Migration map** `docs/product/yozora-migration-map.md` lists all 72 templates with must-keep ids, `hx-*`, `data-*` and referencing tests. It already has a 2026-10-02 revision note and updated rows for the moved surfaces; check it is complete.
- **History and Results** (read for context): `tasks/handoffs/2026-10-01-yozora-mockup-revisions-kickoff.md` (Results and the 2026-10-03 update), `tasks/handoffs/2026-10-01-yozora-mockup-approvals.md`, `tasks/handoffs/2026-10-01-app-design-system-handoff.md` (Results).

## Key files
| Path | What |
|---|---|
| `/Users/saqlainmomin/cyberassess-docs/docs/product/yozora-design-system.md` | Design guide; you update it |
| `/Users/saqlainmomin/cyberassess-docs/docs/product/yozora-fidelity-gate.md` | Five build gates: tokens single source, `/design` gallery route, pixel gate thresholds, human gate, lint |
| `/Users/saqlainmomin/cyberassess-docs/docs/product/yozora-migration-map.md` | Template → slice, target pattern, must-keep attributes, tests |
| `/Users/saqlainmomin/cyberassess-docs/docs/product/2026-10-01-app-design-mockups/screens/IA-SPEC.md` | Binding IA spec |
| `/Users/saqlainmomin/cyberassess-docs/docs/product/2026-10-01-app-design-mockups/flow-map.html` | Approved flow map; serve it to read |
| `/Users/saqlainmomin/cyberassess-docs/docs/product/2026-10-01-app-design-mockups/screens/*.html` | Approved mockups (b1 to b7) plus `gallery.html` |
| `/Users/saqlainmomin/cyberassess-docs/docs/product/2026-10-01-app-design-mockups/approval-walkthrough.html` | Screen list by batch |
| `/Users/saqlainmomin/cyberassess-docs/design/` | Tokens, components, patterns CSS and `tokens_tool.py` |
| `/Users/saqlainmomin/cyberassess-docs/tasks/handoffs/2026-10-01-yozora-s{1..9}-handoff.md` | Current slice handoffs: thin and template-generated; you rewrite them |
| `/Users/saqlainmomin/cyberassess-docs/app/templates/`, `app/routers/`, `app/services/`, `tests/` | Real app code. Use it to check every template, route, model field and test reference |
| `/Users/saqlainmomin/cyberassess-docs/tests/test_p6_2b_dpdpa_criteria.py` | CI file-set guard. This file and `2026-10-03-yozora-codex-orchestration.md` are already allow-listed in `YOZORA_DESIGN_FILES` |
| `/Users/saqlainmomin/cyberassess-docs/tasks/agent-ownership.md` | Claude/Codex task split and the review-before-merge process |
| `/Users/saqlainmomin/cyberassess-docs/CLAUDE.md` | Project gotchas (Python 3.13, `S()` for PDF text, framework copy conditional, etc.) |

## Work
1. **Design guide (`yozora-design-system.md`).** Change the status line to approved (Saqlain, 3 Oct 2026). Then add or correct:
   - **Information architecture:** a new section summarising IA-SPEC (menu, tab rows, sub-view `.seg` rule, breadcrumb rule, stepper placement, single-assessment redirect), with a link to IA-SPEC and the flow map.
   - **Components table:** add every component that now exists in the CSS but is missing from the table. Grep `yozora-components.css` and `yozora-patterns.css`. Examples:
     - progress bar, key-value grid, stat, code block, disclosure, select chevron, date input, `.touch` 44px, file input / dropzone (`.drop`), loading button, tooltip, `sr-only`, `hide-md` / `hide-sm`
     - static table (`.static`), filter toolbar (`.tools`, `.tools.keep-row`)
     - request card (`.req*`, `.mk`, `.req-pick`)
   - **Stepper row:** add "assessment Overview only".
   - **Missing-before-build list:** remove items that now exist. Keep the breadcrumb overflow component, and say that at 390 deep pages currently hide the client and engagement crumbs with `hide-sm`.
   - **Copy rules:** evidence status words, priority words, answer scale, control-code display.
   - **One-primary rule:** the "no primary when there is no real action" clause.
   - **Accessibility:** re-measure contrast for any new colour pairs the `.req` components introduced.

   Keep it terse, files-win-over-doc. Do not invent rules the mockups don't show. If the mockups disagree with each other, list the conflict in Results rather than choosing silently.
2. **Rewrite S1 to S9.** Keep the slice split from the migration map, adjusting membership where the IA moved things: desk review partials go with the questionnaire; retention splits between S3 (Settings) and S4 (archive); magic links and RFI move under Evidence. Each handoff must stand alone for Codex and contain:
   - **Goal and definition of done.**
   - **Exact screens** (mockup file names and the states to match).
   - **Templates in scope**, plus routes and view functions, found by grepping `app/routers/web.py` and friends.
   - **Must-keep ids, `hx-*` and `data-*`**, copied from the migration map and verified against the template.
   - **Tests that reference those templates, and the asserted strings likely to change.** Grep each test for the strings and list them, so test edits are deliberate.
   - **Backend dependency.** The server-side work for the redesign is a separate PR, https://github.com/saqlainmmomin/Cyber/pull/99 (spec: `tasks/handoffs/2026-10-03-yozora-backend-features.md` on branch `claude/yozora-backend-features`). It covers firm settings, firm-level retention, Add assessment, the actions export, Open current report, magic-link client contacts, "Email the firm", and read models (evidence inventory, assessment stage and next step, pre-fill freshness, request summary). Slice handoffs must not re-specify that work. Name PR #99 as a dependency in the slices that use it (S3 settings and retention, S4 engagement Overview and Findings and actions, S5 stage and pre-fill, S6 evidence inventory, S8 client links, comparison and invalid page), and say which service or route each template calls. If #99 is merged by then, cite the real function names from the code.
   - **The temporary reviewer-name field rule.**
   - **File-set guard:** the per-slice `:(exclude)` / allow-list entry to add. Never delete a guard.
   - **Screenshot gate:** widths, themes, thresholds, baselines from the approved mockups.
   - **Dependency order:** S1 shell → S2 component layer and `/design` → S3 to S8 → S9 system states, dark and mobile pass.
   - **What to stop and ask about.**
   - **An empty Results section for Codex.**

   S1 must include the token generator flip (`tokens.json` → `app/static/css/yozora-tokens.css` and the Tailwind theme) and `tests/test_design_tokens_in_sync.py`, per the fidelity gate. Read every handoff through after writing it. They were template-generated before; make sure each is specific.
3. **Migration map.** Fix any rows you find stale while doing step 2, for example templates whose slice changed. Do not regenerate it wholesale.
4. **Orchestration kickoff.** Write `tasks/handoffs/2026-10-03-yozora-codex-orchestration.md` for the next fresh Claude session, which will dispatch Codex slice by slice and review its work. Include:
   - the slice order and dependencies;
   - how to dispatch (see memory note: Codex model choice, no attribution, parallel worktrees only for independent slices);
   - the review checklist per Codex PR (gates from the fidelity gate, must-keep attributes, tests, screenshots shown to Saqlain beside baselines and diffs);
   - where Codex writes Results;
   - the rule that Saqlain merges;
   - the open backend decisions;
   - a check of whether P6-10 and V3-B are merged before S1 starts, since the 1 Oct work order put them ahead of the app build.

## Constraints
- Docs only on this branch: no app code changes.
- Do not read `validation/companies/*/answer_key.json` (held-out evaluation set).
- Do not change the approved mockups or IA. If something is ambiguous, record it as an open question for Saqlain.
- Sentence case and plain language in all docs. No numbered or lettered headings inside product docs (the P2 rule applies to the design guide's own UI examples, not to markdown step lists in handoffs).
- Keep handoffs self-contained: absolute paths, no references to "this conversation". No credentials, no real client names (use the fictional sample companies).
- Use subagents for parallel per-slice research if useful: Sonnet locally (memory note on model budget). You own the final text and must read every handoff yourself.

## Verification (before reporting done)
- `python3 design/tokens_tool.py check` passes.
- `/Users/saqlainmomin/dpdpa-gap-tool/.venv/bin/python -m pytest tests/test_p6_2b_dpdpa_criteria.py -q` passes, including the file-set guard.
- **Template coverage:** a script confirms every template in `app/templates/` appears in exactly one slice handoff or is marked out of scope (print the count; expected 72).
- **Mockup coverage:** every mockup file in `screens/` is referenced by at least one slice handoff.
- **Must-keep spot-check:** for each slice, pick three must-keep attributes at random and confirm they exist in the named template.
- **Proof:** paste the command outputs into Results.

## Report back
Append `## Results` to this file. Cover:
- what changed in the design guide;
- each slice handoff's scope in one line;
- the backend changes per slice;
- conflicts or open questions for Saqlain;
- the verification outputs;
- the line to paste into the orchestration session (`Read tasks/handoffs/2026-10-03-yozora-codex-orchestration.md and execute it. Write your results to the Results section of that file.`).

Commit and push to the branch.
