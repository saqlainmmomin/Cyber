# Yozora S7 mockups: narrative, board inputs, recommended-action draft

**Written:** 3 Oct 2026. **For:** a fresh Claude session (terminal, other account). **Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (GitHub `saqlainmmomin/Cyber`). **Merging is Saqlain's.** You draw mockups only. No app code, no tests.

## Goal
Draw three screens that were added after the Yozora mockups were approved and so have none, so slice S7 can be built to pixel-checked designs instead of improvised: (1) the narrative page, (2) the board inputs page, (3) the recommended-action draft inside the requirement card. Done when each has a self-contained mockup file in the same format and quality as the 61 approved ones, covering every state below, in light and dark, passing the self-check, with a short summary Saqlain can approve. Saqlain approves them before S7 is dispatched.

## Setup
```bash
cd /Users/saqlainmomin/dpdpa-gap-tool
git fetch origin
git worktree add ../cyberassess-s7-mockups -b claude/yozora-s7-mockups origin/main
```
If PR #100 (Yozora S1) has merged, `origin/main` already links mockups to `app/static/css/yozora-tokens.css`; if not, branch from `origin/codex/yozora-s1` instead. Copy the head, link tags, SVG sprite and `?dark` switch from an existing approved mockup in the same family (`b5-requirement-card.html`, `b5-report.html`) so your links are right whichever state the repo is in.

## Read first
| Path | What |
|---|---|
| `docs/product/yozora-design-system.md` | Design guide, binding |
| `design/yozora-components.css`, `design/yozora-patterns.css`, `design/tokens.json` | The only components and tokens you may use |
| `docs/product/2026-10-01-app-design-mockups/screens/BRIEF.md` | Hard rules for a mockup batch (sentence case, no uppercase, one `.btn.primary` per state, no hex values, no numbered headings) |
| `.../screens/IA-SPEC.md` and `flow-map.html` | Where these pages sit: Assessment, Report sub-pages; breadcrumb and seg rows |
| `.../screens/b5-requirement-card.html`, `b5-report.html`, `b5-release.html`, `b5-findings.html`, `b5-finding-card.html` | Closest siblings: copy their shell, tone and density |
| `tasks/handoffs/2026-10-01-yozora-s7-handoff.md` (Notes about "No mockup") | What S7 will build from your designs |
| `app/templates/pages/narrative.html`, `pages/board_inputs.html`, `partials/remediation_draft.html` | The pages as they are today (functionality and every `data-*` you must keep room for) |
| `app/services/narrative.py`, `app/routers/drafting.py`, `app/routers/board_inputs.py`, `app/services/board_inputs.py` | What the pages do and what fields and states exist |

## The three screens
1. **Narrative** (`GET /assessments/{id}/narrative`): the consultant-accepted executive narrative that feeds the board report. Sections: an executive summary, a cross-framework section, and one per framework in scope; each section shows generated sentences with finding references (shown as R-xx labels), an accept action per section, a generate action, and a reviewer-name input (temporary until auth, keep it). Only accepted text reaches client output. States: no draft yet; draft generating or just generated (unaccepted); a section accepted; everything accepted; an error (generation failed); a framework not in scope is simply absent (framework names appear only for frameworks in scope).
2. **Board inputs** (`GET /assessments/{id}/board-inputs`): consultant data that the board deck needs: per finding "Why it matters" and "Recommendation"; per action a responsibility (client, consultant, shared); per remediation initiative (grouped actions) a title, complexity and benefit; and up to a few board asks. States: empty, partly filled, complete, a validation error. Keep it scannable for a dozen findings and eight initiatives; saves happen per row (HTMX), so show a saved indicator, not a page-level save button (one primary at most).
3. **Recommended-action draft** (inside the requirement card, `b5-requirement-card.html`): a button that asks the model to draft a recommended action for a conclusion, and the field that holds it. States: empty with the draft button; drafting; a draft present and editable with the model-draft label; saved. Show it inside the existing requirement card layout (state names to add to a copy of the card or a small specimen page, your choice, say which).

Where a state needs copy, write it plainly, sentence case, in the app's voice. Do not invent product behaviour; where a choice is yours, note it in the summary.

## Constraints (decisions already made, do not reopen)
- Components and tokens only from the files above. If something is missing, build without it and add a line to `screens/NEEDS-b5.md` describing the component and why; do not edit shared CSS.
- Exactly one `.btn.primary` per state, none in a state with no real action. No uppercase or `text-transform`, no numbered or lettered headings, no hex or inline colours, no `background-clip:text`, no blur-3xl.
- Priority wording is Do first, Next, Planned, Backlog, never numbers. Scores are never combined across frameworks. Framework names appear only where in scope.
- Keep room for every `data-*` and id the real templates carry (list them from the templates).
- Do not edit approved mockups. New files only, plus appends to `NEEDS-b5.md`, plus a row in `docs/product/yozora-migration-map.md` if a mockup file name is recorded there (check; if so, add rows, do not rewrite).
- Do not read `validation/companies/*/answer_key.json`. No credentials or client names; use the existing fictional companies from the other mockups.
- No attribution lines in commits or the PR.

## Output
`docs/product/2026-10-01-app-design-mockups/screens/b5-narrative.html`, `b5-board-inputs.html`, and either `b5-requirement-card.html` extra states or `b5-recommended-action.html`. Use `?state=<name>` and `?dark` switches like the siblings. Add the three screens to `flow-map.html` and `IA-SPEC.md` where the Report sub-pages are listed (append, keep structure).

## Verification
1. Run the self-check from `BRIEF.md` (the grep for uppercase, text-transform, hex, numbered headings; count `.btn.primary` per state).
2. Serve (`python3 -m http.server` from the repo root, but note `/static/` font URLs 404 under a plain server; screenshots may use fallback fonts) and screenshot every state light and dark at 1440 and 390 (Playwright or the browser pane). Check no horizontal overflow at 390.
3. Look at each screenshot yourself before reporting.

## Report back
Append `## Results` to this file: the files added, the states per screen, choices you made that Saqlain should confirm, NEEDS entries, and screenshot paths (put the PNGs under `docs/product/2026-10-01-app-design-mockups/screens/` only if sibling screenshots live there; otherwise a scratch folder and say where). Commit on `claude/yozora-s7-mockups` (no attribution), do not push or open the PR: give Saqlain the exact `git push` and `gh pr create` commands.

## Results

**Branch:** `claude/yozora-s7-mockups`, worktree `../cyberassess-s7-mockups`, branched from `origin/main` (PR #100 not merged; mockups link `design/*.css`, so no S1 branch was needed). One commit, no attribution. Not pushed.

**Files added** (in `docs/product/2026-10-01-app-design-mockups/screens/`): `b5-narrative.html`, `b5-board-inputs.html`, `b5-recommended-action.html`. Edited by append: `flow-map.html` (Report and Review link lists), `IA-SPEC.md` (Report seg and screen table), `NEEDS-b5.md`. `yozora-migration-map.md` not touched: it records no mockup file names, only "no approved mockup" in the notes of three S7 rows, which should read "see b5-narrative / b5-board-inputs / b5-recommended-action" when S7 is dispatched.

**States** (`?state=`, `?dark`):
- Narrative: empty, generating, drafted, partly-accepted (includes a stale accepted section), accepted, error (failed plus draft limit reached), not-released.
- Board inputs: empty, partly, complete, dense (12 findings, 8 initiatives), error (over-length text).
- Recommended action: empty, drafting, drafted, edited, error, gaps-required, limit, saved.

**Checks:** grep for uppercase, text-transform, hex, background-clip, blur-3xl is clean. `.btn.primary` per state: 0 or 1 everywhere (0 in narrative accepted and not-released, all board-inputs states, and recommended-action saved). I looked at the 1440 and 390 shots in light and dark for the drafted, error and drafting states of each page and found two defects (clipped seg label at 390, a validation error that didn't match its text), both fixed and re-shot. All 80 shots ran with no horizontal overflow at 390; I did not eyeball every one. Screenshots: `/private/tmp/claude-501/-Users-saqlainmomin-dpdpa-gap-tool/ca44453a-8acc-497b-a106-84fd27183000/scratchpad/shots/` (`<file>_<state>_<1440|390><l|d>.png`). Sibling shots live elsewhere, so none were added to the repo. Served by plain `http.server`, so fonts are fallback.

**Choices to confirm:**
1. **Recommended action is a specimen page, not the requirement card.** The real field (`remediation_draft.html`) is included from `conclusion_card.html`, in the conclusion edit form, so `b5-recommended-action.html` copies that card's edit layout.
2. **Seg order:** Report, Versions, Applicability, Narrative, Board inputs (appended). Existing report mockups lack the two buttons; S7 should build to the spec.
3. **One primary on narrative:** the first section still waiting gets "Save and accept" as primary, the rest are secondary. Page-level "Draft missing or stale sections" is primary only when nothing is drafted yet.
4. **Section labels** are clean ("Executive overview", "Across frameworks", "DPDPA 2023 posture"): the app today appends ids like "(executive)". Sections present: only frameworks in scope.
5. **Finding refs (R-xx)** show as chips under the text ("Cites"), plus an "Approved findings" disclosure. I did not assume refs are embedded in the text. Accepted sections stay an editable textarea, matching the app; no "accepted by/when" line, since the template shows none.
6. **Board inputs:** no page-level save. Each row has a ghost "Save" and a status (Saved, Saving, Unsaved changes, Not saved); responsibility selects save on change as today. Added derived cues: "Filled in / Needs input" per card and a three-chip count summary. Decision inputs are unnumbered (names `ask_1..3` kept). Labels "Not recorded", "High/Medium/Low", "Client/Consultant/Shared" mirror the select values.
7. **Copy changes:** "Save & Approve" became "Save and approve" in the draft notice. The recommended-action draft shows an "AI draft" label, a "Draft again" button once a draft exists (the router has a `regenerate` flag), and keeps the suggested-owner-role hint ("not saved"). Error copy is the real strings from `remediation_draft.py`. Narrative "draft limit" copy is mine, from the three-drafts cap in `narrative.py`.

**NEEDS-b5 entries added:** inline save-state component, character counter on `.field`, reference-chip as link.

**To publish:**
```bash
cd /Users/saqlainmomin/cyberassess-s7-mockups
git push -u origin claude/yozora-s7-mockups
gh pr create --base main --head claude/yozora-s7-mockups --title "Yozora S7 mockups: narrative, board inputs, recommended-action draft" --body "Three mockups for screens added after approval, with all states in light and dark. Adds flow-map and IA-SPEC rows and NEEDS-b5 entries. Mockups and docs only."
```

## Review and decisions (3 Oct 2026)
Review by a read-only subagent, full report `/private/tmp/claude-501/s7-review/report.md` (screenshots in `.../shots/`). Hard rules passed (no uppercase, hex, numbered headings; all classes exist; no overflow at 390). Defects found: narrative textarea shows plain text where the real accept requires a trailing `[R-xx]` on every sentence; narrative "Draft failed" and "Draft limit" per-section states cannot occur (failures are toasts); recommended-action gaps-required and limit states are 400/429 toasts, not in-field, and the limit state wrongly drops the draft button; disabled primaries in narrative generating and recommended-action drafting; "Reviewer name" should read "Consultant name"; per-section "Drafting" is not real (one blocking request); invented copy ("It is 1,732 now", "Draft section", "All sections accepted"); "Board inputs" seg label clips at 390; sibling report mockups lack the two new buttons; recommended-action page lacks a Review seg row.

Saqlain's answers:
| # | Question | Answer |
|---|---|---|
| A | Failure and limit states | In-field for recommended action only (draft failed swaps in the field). Narrative failures and limits are toasts; redraw those mockup states to match. Gaps-required and limit for recommended action become toast states, and the limit state keeps the draft button. |
| B | Narrative refs | Inline `[R-xx]` markers in the textarea as today; Cites chips stay as a read-only helper only. |
| C | Busy state | Non-primary loading button ("Drafting…", spinner), no primary until the draft returns. No disabled primaries. |
| D | Seg row and Draft again | Update the four sibling report mockups with Narrative and Board inputs seg buttons and fix the 390 clip; keep "Draft again" (S7 sends `regenerate=1`; the router supports it). |
| Mockup choices 1, 2, 3, 4, 6, 7 | Accepted as recommended by the reviewer. |

Revisions applied on branch `claude/yozora-s7-mockups` (see Results below once done).

### Revisions applied (commit 279d1ef on `claude/yozora-s7-mockups`, not pushed)
Narrative: textarea carries trailing `[R-xx]` refs, Cites chips read-only; failure and limit are toast specimens; one page-level busy state (secondary `.btn.loading`, no primary); "Consultant name"; invented copy removed; wording taken from the code constants. Recommended action: drafting busy button non-primary; failed stays in-field; gaps-required, limit (draft button kept), stale, not-open and not-draftable are toast states with real copy; Review seg row added. Board inputs: invented counts and empty-state copy removed, "Decision 1/2/3" labels, real validation messages. Seg row: Narrative and Board inputs added to b5-report, b5-no-report, b6-soa, b6-report_snapshots; all six Report seg rows wrap at 390 (no shared CSS change). b5-release and b5-basis have no Report seg row. NEEDS-b5 gained two lines.
Checks: hard-rule greps clean; every state 0 or 1 `.btn.primary`; no overflow at 390; reviewer looked at the main states (not narrative drafted at 390).
**For S7 (raise in the S7 dispatch):** the narrative draft failure and limit toasts send a type but no message today, so S7 must add a message header; the 422 line-level accept error says "[F1, F3]" while the page uses R-xx aliases (mismatch to fix in S7); busy buttons show only a spinner because `.btn.loading` hides the label.
