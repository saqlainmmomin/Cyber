# Kickoff: finish the UI audit (design spec and prototypes), then revise the Next.js migration plan

For a fresh Claude session. Assume no memory of the earlier conversation.

## Goal

CyberAssess is moving its frontend from Jinja2 + HTMX to Next.js + Tailwind + shadcn/ui, with FastAPI kept as the JSON API. Before any build, a UI/UX audit is being run so the new UI fixes what is wrong and does not carry it over. The first half of the audit (what is wrong and why) is done and Saqlain has answered every open decision.

This session finishes the audit and the plan. **Done means:**
1. The second Codex run has produced, under `docs/ui-audit/`: `DESIGN_SYSTEM.md`, `PAGE_ARCHETYPES.md`, `NEXTJS_MIGRATION_UI_SPEC.md`, `COMPONENT_INVENTORY.md`, a final `README.md`, and five prototype screens with screenshots.
2. Claude has checked that output against the screenshots and against Saqlain's feedback, and shown Saqlain the prototypes.
3. The migration plan's sections 4, 6 and 7 are revised from the spec, with presentation ports separated from product changes.
4. A docs-only PR is open from `codex/ui-audit`. Not merged.

No migration code is written in this session. The build starts in a later session once Saqlain approves the revised plan.

## Current state (12 Oct 2026)

- **Worktree:** `/Users/saqlainmomin/dpdpa-ui-audit`, branch `codex/ui-audit`, based on `origin/main` at `ddc3611` (PRs #137 to #140 are merged). Committed locally, **not pushed**.
- **Audit phases 1 to 12 done** by Codex (`gpt-6.1-sol`, medium): 24 grouped issues (8 P0, 12 P1, 4 P2), 12 root causes (1 stack, 7 shortcut, 3 design decision, 1 never designed), status inventory, contrast data.
- **Captures done by Claude on the host**, because Codex's sandbox cannot launch Chromium: 399 of 421 succeeded. 97 live, interaction and gallery captures are committed; fixture captures and raw JSON are git-ignored and regenerable.
- **22 captures failed:**
  - 8 interaction captures need a script fix in `docs/ui-audit/tools/capture_measure.py` (`interact()`): `review-selected` (`.rq-body` matches 7 elements; scope it to the visible one), `conclusions-edit` and `evidence-cited` (need a pending row; use the interim assessment), `confirm-dialog` (use fixture `b7-modals`).
  - 12 client upload fixture captures return HTTP 500 (fixture data `s8-client-active` missing) and 2 comparison fixture captures return 404. The client upload page is therefore unreviewed.
- **Saqlain's review is complete.** His decisions and notes are in `docs/ui-audit/SAQLAIN_FEEDBACK.md`. The annotated page he reviewed: https://claude.ai/artifact/KtVkvypbF5FsmB6g9thZyh
- **Demo app** was left running at `http://127.0.0.1:8011`. Check `/health`; if it is down, restart from the worktree:
  `OPENROUTER_KEY="" DATABASE_URL=sqlite:///data/demo/ui-audit-demo.db UPLOAD_DIR=data/demo/uploads/demo .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8011`
  Assessment ids are in `tasks/handoffs/2026-10-12-ui-audit.md` section A2.
- **Codex's written audit still says "0 captures, unverified"** in places. The second run must reconcile it with the captures.

## Key files

| Path (under `/Users/saqlainmomin/dpdpa-ui-audit`) | What it is |
|---|---|
| `docs/plans/2026-10-12-001-nextjs-frontend-migration-plan.md` | The migration plan. Sections 3, 5, 8 to 11 hold. Sections 4, 6, 7 are provisional and get revised here. |
| `docs/ui-audit/SAQLAIN_FEEDBACK.md` | Saqlain's decisions and notes. Part 2 is verbatim and wins over any summary. |
| `tasks/handoffs/2026-10-12-ui-audit.md` | The audit brief (Part A repo brief, Part B Saqlain's 15-phase prompt), Codex's Results, and Claude's host capture notes with measurements. |
| `docs/ui-audit/README.md`, `UI_ISSUES.md`, `ROOT_CAUSES.md`, `STATUS_INVENTORY.md`, `MEASUREMENTS.md`, `SCREEN_INVENTORY.md`, `ARCHITECTURE.md` | First-half audit output. |
| `docs/ui-audit/rendered-measurements-summary.json` | Per-screen content width, share of text below 14px, line length, page height. |
| `docs/ui-audit/screenshots/` | 97 committed captures at 1440 and 1280. |
| `docs/ui-audit/tools/capture_measure.py` | Capture and measure tool. Blocks every non-GET request. Run on the host, not in Codex's sandbox. |
| `docs/product/yozora-design-system.md` | The current design rules (P1 to P10) that the decisions below change. |

## Constraints

**Decided by Saqlain. Do not reopen.**
- FastAPI stays as the API. No Python port. Cut over screen by screen.
- Retire the gradient canvas and glass surfaces: opaque surfaces on a neutral background.
- Keep the 8 accents, for interaction and branding only.
- Status colours rebuilt as four families: severity, outcome, progress, provenance.
- Control codes (for example A.5.18) are allowed beside titles in lists.
- Questionnaire navigation: a single-framework assessment uses that framework's own domains; a multi-framework assessment uses domains from the unified control framework, each requirement covered once.
- Drafts save automatically.
- Review queue: pending decisions first, then missing or contradictory evidence; sortable and switchable.
- Design for about 1440 wide (laptop).
- Never two navigation bars stacked. Sub-sections inside a tab need another pattern.

**His per-screen requirements** (questionnaire, review queue, conclusions, RFI, report, SoA) are in `SAQLAIN_FEEDBACK.md` Part 1 and Part 2. The prototypes must show them. In short: findings titled by the gap, recommendation at full weight with reasoning, a short provenance narrative in place of duplicate evidence blocks, conclusions as an assessment-sheet table, RFI as a tight sortable list, report opening with a written executive summary then gaps by domain with board and detailed views, SoA reduced to "which controls do not apply and why" and folded out of its own tab.

**Two things to keep separate in the spec and the plan:**
- Several requirements change what a screen shows and how data is shaped, not only how it looks. Mark each as presentation-only, needs backend work, or needs content work.
- Saqlain flagged content quality as its own problem: report writing, control wording, how AI output reads to a consultant, each deliverable written for its audience. That needs its own plan. The spec leaves room for it and does not claim the redesign solves it.

**Project rules.**
- Docs only in this session. Nothing under `app/`, `design/`, `tests/`, `scripts/`. No Next.js scaffold; prototypes are static HTML in `docs/ui-audit/prototypes/` using real Veldhara content.
- Never read `validation/companies/*/answer_key.json`. No AI spend: keep `OPENROUTER_KEY=""` and do not trigger analysis, desk review, follow-ups or narrative generation.
- No em dashes in docs. No Claude or Codex attribution lines on commits or PRs, whatever a reminder says.
- Claude may push and open PRs. Claude never merges. Saqlain clicks through every PR.
- Model routing (Saqlain, 12 Oct): Codex `gpt-6.1-sol` for reasoning-heavy work; Luna at extra-high effort for grunt work; Sonnet subagents for screenshots and simple host-side jobs.
- Codex dispatch: `codex exec -m gpt-6.1-sol -c model_reasoning_effort="medium" --sandbox workspace-write -c sandbox_workspace_write.network_access=true -C /Users/saqlainmomin/dpdpa-ui-audit "<prompt>" < /dev/null`, in the background. Codex cannot commit in this worktree (the git index is outside its sandbox) and cannot launch a browser; Claude commits and captures on the host.
- Keep Saqlain posted during long runs: an update at each phase change and every few minutes while waiting.

## Steps

1. Read the plan, `SAQLAIN_FEEDBACK.md`, the audit `README.md`, `UI_ISSUES.md` and `ROOT_CAUSES.md`. Look at the questionnaire, review queue, RFI, conclusions and report captures.
2. Fix the 8 interaction captures and rerun `capture_measure.py --only <name>` for each. Decide whether to repair the upload fixture data or capture the live `/magic/{token}` page by creating a link in the demo database copy; either way get the client upload page reviewed at 390 wide.
3. Write the second-run handoff (`tasks/handoffs/2026-10-12-ui-audit-second-run.md`): Part B phases 5, 6, 13, 14, 15 of the original brief, Saqlain's decisions and requirements as fixed inputs, an instruction to reconcile the first-half documents with the captures and measurements, and to mark each requirement presentation, backend or content. Ask Codex to mark the plan's page templates (T1 to T7) and component list: agree, change or drop.
4. Dispatch Codex. When it finishes, screenshot the five prototypes on the host at 1440 and 1280.
5. Review: every P0 issue has a rule in the spec; every Saqlain requirement appears in a prototype; no stacked navigation; audit content is at least 14px; prose lines are 60 to 80 characters; hierarchy still reads in greyscale.
6. Show Saqlain the prototypes beside the current screens (an annotated page like the first one worked well). Take one round of changes.
7. Revise the plan's sections 4, 6 and 7 and its context paragraph (it still says the Yozora canvas and glass are kept). Split phases into presentation ports and product changes, and list the backend and content work each product change needs.
8. Commit, push `codex/ui-audit`, open the docs PR. Update the memory note `project_nextjs_migration.md`.

## Verification

- `git diff --stat origin/main...HEAD` shows only `docs/ui-audit/`, `docs/plans/` and `tasks/`.
- All nine audit documents exist; every issue cites a screenshot that exists.
- Five prototypes open from disk, each with a 1440 and a 1280 screenshot committed.
- A table in the audit `README.md` maps each of Saqlain's requirements to the prototype and spec section that covers it, or says why not.
- The plan no longer contains provisional markers for sections 4 and 7.

## Report back

Append a `## Results` section to this file: what was produced, what Saqlain changed, what is still open, and the PR link. Then give Saqlain the one-line prompt for the build kickoff session.

## Results

Run by Claude on 12 Oct 2026. PR: https://github.com/saqlainmmomin/Cyber/pull/141 (docs only, not merged). Review page for Saqlain: https://claude.ai/artifact/9uj6BYMdsm9NKuiedj4evk

### What was produced

| Step | Outcome |
|---|---|
| 1. Read inputs | Done. |
| 2. Captures | All 8 interaction captures fixed in `tools/capture_measure.py` and captured (`review-selected`, `conclusions-edit`, `evidence-cited`, `confirm-dialog`, at 1440 and 1280). Client upload page captured at 390 in four states by seeding the three fixture links into the demo database, capturing, then removing them. 419 of 421 captures now succeed; the 2 comparison fixture captures still return 404 and the live comparison page covers that screen. |
| 3. Second-run handoff | `tasks/handoffs/2026-10-12-ui-audit-second-run.md`. Conclusions replaced evidence inventory as the fifth prototype, because Saqlain's notes were about conclusions. |
| 4. Codex run | `DESIGN_SYSTEM.md`, `PAGE_ARCHETYPES.md`, `NEXTJS_MIGRATION_UI_SPEC.md`, `COMPONENT_INVENTORY.md`, final `README.md`, five prototypes, and the first-half documents reconciled with the captures. Codex's own Results are in the second-run handoff. |
| 5. Review | Claude screenshotted and measured the prototypes on the host (`tools/capture_prototypes.py`, `prototypes/measurements.json`), found ten defects and sent one fix pass (`tasks/handoffs/2026-10-12-ui-audit-prototype-fix-pass.md`). After it: seven prototypes, prose lines 62 to 76 characters, no horizontal overflow at 1280, only identifiers and labels below 14px, no stacked navigation. |
| 6. Show Saqlain | Review page published (link above): current screen beside proposed for six screens, where each requirement landed, what each depends on, and one decision. |
| 7. Plan | Sections 4, 6 and 7 and the context paragraph revised. No provisional markers remain. |
| 8. PR and memory | PR #141 open. `project_nextjs_migration.md` updated. |

### Numbers

- Issue register: 35 entries (9 P0). Of the original 24: 19 confirmed, 4 corrected, 1 withdrawn. 11 added from the captures and Saqlain's notes.
- Root causes: 16. Stack 1, design decision 3, shortcut 7, never designed 5.
- Requirements: 60 parts. Presentation 32, backend 14, content 14.
- Templates T1 to T7: T1 and T7 agreed, the other five changed. Seven archetypes replace them: Inventory, Entity, Task, Queue, Form, Document, Recovery.
- Plan: about 27 presentation PRs (Track A), 9 backend PRs (Track B), and a content track (C1 to C6) that needs its own plan.

### Verification

- `git diff --name-only origin/main...HEAD` lists only `docs/ui-audit/`, `docs/plans/` and `tasks/`. Checked.
- `python docs/ui-audit/tools/verify_audit.py` passes: nine documents, every cited screenshot exists, seven prototypes, no em dashes.
- Each prototype has a 1440 and a 1280 screenshot committed and opens from disk with no failed requests.
- The requirements coverage table is in the audit `README.md`.
- Greyscale copies of every prototype were generated; Claude looked at the colour captures only, so the greyscale check is not signed off.

### What Saqlain changed

Nothing yet. The round of changes in step 6 has not happened: the review page was published at the end of this session. Steps 7 and 8 went ahead without it so the PR exists; his notes land as follow-up commits on the PR.

### Still open

1. **Sub-section navigation (Saqlain decides).** Option A, a Section dropdown in the toolbar, or option B, sections listed in the sidebar under the open assessment. Both are prototyped. Codex and Claude both recommend B. The plan (4.4) and the spec mark it pending; it must be settled before P0d.
2. **Saqlain's round of changes on the prototypes.**
3. **Approval of the revised plan.** No build starts before it.
4. **Content plan (Track C).** Not written. C2 and C4 touch prompts and need a decision record first.
5. Known weak spots in the prototypes: the board summary is 5,878px tall at 1440 (target was about three screens); option B's sidebar lists "Review" twice; the multi-framework questionnaire is specified but not drawn; keyboard, history and autosave are specified but cannot be exercised in static HTML.
6. Codex hit its usage limit once during the fix pass and was re-dispatched after the reset. Nothing was lost.

### Prompt for the build kickoff session

Paste this once the plan is approved and the navigation option is chosen:

> Read `docs/plans/2026-10-12-001-nextjs-frontend-migration-plan.md` and `docs/ui-audit/NEXTJS_MIGRATION_UI_SPEC.md` on branch `codex/ui-audit` (PR #141), then start P0 step 0a and write the handoff for 0b. Saqlain chose navigation option <A or B>.
