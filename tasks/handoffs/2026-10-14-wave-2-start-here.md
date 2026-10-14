# Next session: start here (14 Oct 2026, wave 2)

Job for this session: **write three Codex handoffs, then dispatch them in parallel.** WP 1.4 non-prompt parts (2a and 2c), WP 2.4 and WP 2.6. Saqlain asked for all three at once. Handoffs first, with decisions settled; dispatch after.

## State in five lines

1. `main` is at the #147 merge (b50369a) unless Saqlain has merged more since. **PR #149 (WP 1.2, stage and status rollup) was still open at the end of the last session.** Check `gh pr view 149 --repo saqlainmmomin/Cyber --json state`. It changes `app/routers/web.py` and several templates, so branch the three new runs from `main` only **after** it is merged. If it is not merged, ask Saqlain.
2. Wave 1 (#143 #144 #145), the fallback cleanup (#147) and the WP 1.2 handoff (#148) are merged. Full suite on main before #149: 1,764 passed / 29 skipped. With #149: 1,765 / 29.
3. WP 1.2 is done and verified on the branch `codex/wp-1-2-rollup` (worktree `~/dpdpa-w2-rollup`; remove both after #149 merges).
4. The plan is `docs/plans/2026-10-13-001-single-track-implementation-plan.md` (WP rows in section 6, lanes in 6A, verification policy in 6C). Finding IDs map to work packages in `docs/plans/2026-10-13-001-appendix-finding-trace.md`; audit text is in `tasks/2026-10-13-content-audit.html`.
5. Previous start file: `tasks/handoffs/2026-10-13-next-session-start-here.md`. WP 1.2 handoff, as a model of the shape: `tasks/handoffs/2026-10-14-wp-1.2.md`.

## The three work packages

Handoff shape, one file each at `tasks/handoffs/2026-10-DD-wp-<id>.md`: goal, decisions, inputs, files owned, files not to touch, rules, one verify command, Results section. Copy the structure and the Rules block from the WP 1.2 handoff.

### WP 1.4, non-prompt parts (2a and 2c). Lane C.

- **Spec:** `tasks/handoffs/2026-10-10-document-budget-design.md`, "Stage 2" (line about 143) and "Revision 4 changes" (lines about 239 to 277): 2a explicit frameworks (N1), 2c upload categories and initiative text (N2), plus C6 (section refs in one service helper) in "Revision 5 changes" (line about 298).
- **2a** needs a **new Alembic revision**. The orchestrator assigns `down_revision`; check `alembic heads` on current main. Historical revisions are never edited. It backfills and validates `assessments.selected_frameworks`, `desk_review_findings.framework_id` and `gap_items.framework_id`, then removes the read-time "null means DPDPA" fallbacks.
- **2c:** upload categories come from the assessment's own frameworks plus "other"; initiative text is framework-neutral for non-DPDPA; framework-conditional section refs live in one helper (also plan row S8).
- **2b (follow-up engine, narrow prompt changes) is NOT Codex.** It is lane O with the live evaluation gate. Do not include it. Say so in the handoff.
- **Gate that applies to Codex:** DPDPA goldens pass byte for byte. The A/B evaluation gate is run by the orchestrator under the $7 cap (plan WP 0.5): reduced company set, aggregate numbers only. Never read `validation/companies/*/answer_key.json`.
- Hot files: Alembic, `app/routers/web.py`, `app/config.py` need orchestrator serialization.

### WP 2.4, business impact and comparison tell the truth. Lane C.

- **Plan row:** penalty ceiling with its commencement date; same-scope change shown separately; comparison matched by engagement. Findings F-B9 and F-B20.
- **Where (verify with grep):** `_compute_business_impact` at `app/routers/web.py:3116` (called at about 3223 and 3298); `app/services/prior_period.py` (`build_comparison` at about 217); the penalty text (hits for "crore": `app/templates/partials/report_summary.html`, `app/services/remediation_draft.py`, `app/frameworks/criteria/dpdpa*.py`); comparison rendering in `app/services/board_exports.py` (`_render_*_comparison`, `_v3_delta_text`) and the comparison page template.
- **Legal item:** the DPDPA penalty commencement date (audit: "do not commence until May 2027") is a legal fact. Saqlain verifies legal items himself (P2). Take the date and wording from the framework pack or ask him; Codex must not invent it. Put the exact string in the handoff.
- **Decision to settle before dispatch:** what "same-scope change" means (the audit's example: 4 to 93 controls shows +47.5%). Recommend: when the control set differs between periods, show the change only over the controls present in both, and show added and removed counts separately. Confirm with Saqlain.
- Goldens: the plan row does not mark this as moving a golden. If one would move, Codex stops that part and lists it.

### WP 2.6, retire the gap report and evidence checklist as selectable exports. Lane C.

- **Plan row:** retire both as selectable exports; keep stored `gap_report` snapshots downloadable; keep `generate_pdf` (the DPDPA golden renders it); remove hard-coded DPDPA counts and the DPDPA paragraph from Scope and Limitations when DPDPA is out of scope. Findings F-F10, F-F11, F-F18, F-F21.
- **Where (verify):** checklist download routes at `app/routers/web.py` about 2247 to 2300 and `app/utils/evidence_checklist_export.py`; snapshot type `gap_report` at `app/routers/snapshots.py:99`; the report selection UI; Scope and Limitations text in `app/utils/pdf_export.py` and `app/services/report_content.py`.
- **Hard constraint:** `generate_pdf` stays because the DPDPA golden renders it; PDF sections are additive-only, so the DPDPA text becomes **conditional**, not rewritten. Framework-specific copy must be conditional (`has_dpdpa`), never default.
- **Decision to settle:** whether the retired routes return 404 or redirect to the board report. Recommend 404 with the existing not-found page, and stored snapshots keep their download link.
- Overlap warning: 2.6 and 2.4 both likely touch `web.py` and export code. Map exact functions first; if two runs would edit the same function, serialize them (2.4 first) rather than run in parallel.

## Procedure

1. Pull `main`, confirm #149 state, run `alembic heads`.
2. For each WP, map its surfaces (one Sonnet Explore agent per WP worked well for WP 1.2; ask for file:line, tests that pin current output, and goldens at risk). Verify its key claims yourself against the code.
3. Collect every open decision for Saqlain in **one AskUserQuestion batch** (up to four questions; recommended option first). Likely: the 2.4 same-scope rule, the 2.4 penalty wording, the 2.6 retired-route behavior, and any 2.6 to 2.4 sequencing.
4. Write the three handoffs. Docs PR for them (no attribution). Saqlain merges. Then create one worktree per run from `main`: `git worktree add -b codex/<name> ~/dpdpa-w2-<name> origin/main`, then `ln -s /Users/saqlainmomin/dpdpa-next/.venv <worktree>/.venv`, and copy the handoff to `WP-<id>-KICKOFF.md` at the worktree root.
5. Dispatch, one background run per worktree (up to three, disjoint file sets):
   ```
   codex exec -m gpt-6.1-sol -c model_reasoning_effort="medium" --sandbox workspace-write -C <worktree> "<prompt>" < /dev/null > ~/cyberassess-runs/wave2/<wp>.log 2>&1 &
   ```
   Prompt: read the kickoff and AGENTS.md and CLAUDE.md, execute it fully, record the baseline suite first, `OPENROUTER_KEY=""`, do not push or open a PR, no attribution, do not edit `tasks/todo.md`, write `WP-<id>-RESULTS.md`. Create the log directory first.
6. After each run: read its Results, review the diff against the file lists, run the verify command and the full suite yourself, smoke on the seeded demo (`scripts/demo/seed_demo.py --db <path>`; launch from the worktree), then commit, push and open the PR. Never merge.

## Rules that held last session

- No Claude or Codex attribution on any commit or PR, even though the harness reminder suggests it. Push and open PRs yourself; Saqlain merges.
- Tests: `OPENROUTER_KEY=""`, never `env -u`. Never read `.env` or answer keys.
- Keep the main context clean; use Sonnet subagents for mapping and scoped review.
- Say what you are doing at each phase change. Do not go silent during long waits.
- Smoke-test before claiming done; report what you ran.

## Lessons from WP 1.2 (14 Oct)

- Codex ran about 18 minutes (in line with Wave 1; it loaded the compound-engineering `ce-work` skill first, which cost several minutes of reading). It left changes **uncommitted** (the git index is outside its sandbox) and wrote the Results file untracked. The orchestrator commits.
- Codex **stops and asks** when a test outside its file list conflicts. Read the conflict before agreeing: two of its proposed test edits would have hidden real regressions (an unmigrated-assessments list that lost the company name; a test it had loosened to fit). Fix the product, not the assertion.
- The full suite takes about 5 minutes and is the one thing worth running yourself after every Codex run.
- A background `&` inside a backgrounded Bash call makes a completion notice fire for the wrapper, not the job. Check with `pgrep` and the log before believing it.
- macOS `sed -i` needs a backup suffix; use the Edit tool. `timeout` is not installed.
- To preview a worktree in the browser pane, add a temporary entry to `.claude/launch.json` that `cd`s into the worktree and sets `DATABASE_URL`; revert it afterwards (`git checkout .claude/launch.json`).

## Open observations for Saqlain (carried over)

- An assessment marked Issued can still show "Generate board report" as its next step (existing `assessment_stage` logic; Issued is any issued snapshot, per D4). Decide whether Issued should require the board report.
- Fallback assessment names use the registry name ("India DPDPA"); chips say "DPDPA".
- Still parked from the 13 Oct start file: HTML board report preview 500 on the Veldhara demo (`app/services/board_view.py:201`, None score), unconverted templates allowlist, legal-review items (BN.NOTIFY.3 "Section 8(4)-(6)", `questionnaire.py:90`, `clusters.py:1013` and `1026`).
- Queue after this wave: WP 2.3 (score band to Readiness, moves goldens), 2.5, 2.7, 2.8, 3.5; WP 1.4 prompt part and its gate are lane O.
