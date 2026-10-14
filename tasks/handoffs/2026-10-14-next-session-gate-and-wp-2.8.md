# Next session: safety check for WP 1.4, then WP 2.8 (14 Oct 2026, evening)

For a fresh Claude Code session (the orchestrator). Assume no memory of earlier sessions. Saqlain reads your reports, so write them in plain language: outcome first, one line on what each term means, details at the end (see memory `feedback_plain_language_status_reports`).

Two jobs. They do not depend on each other, so run them side by side: dispatch WP 2.8 to Codex first (it runs in the background), then do the safety check yourself.

## Where things stand

- `main` has Waves 1 and 2: WP 1.1, 1.2, 1.3, 1.4 non-prompt parts (2a explicit frameworks, 2c upload categories, initiative text, section refs), 2.4 (dated penalty, same-scope comparison) and 2.6 (gap report and checklist retired). PR #155 (the last "null means DPDPA" fallbacks) may still be open. Check with `gh pr view 155 --repo saqlainmmomin/Cyber --json state`. If it is open, branch from `main` anyway; it touches different lines from both jobs below.
- Full suite on main before #155: 1,798 passed / 29 skipped. With #155: 1,812 / 29 on that branch (the extra tests come from WP 2.4 and WP 2.6).
- The plan is `docs/plans/2026-10-13-001-single-track-implementation-plan.md` (WP rows in section 6). Previous start file: `tasks/handoffs/2026-10-14-wave-2-start-here.md`. Handoff shape to copy for Codex: `tasks/handoffs/2026-10-14-wp-2.4.md` (goal, decisions, inputs, files owned, files not to touch, rules, verify, Results).

## Job 1: the safety check (lane O, you do this yourself)

### What it is

Wave 2 changed shared code so it stops assuming "no framework means DPDPA" (WP 1.4 parts 2a and 2c). The plan requires one live test run to prove DPDPA results did not get worse, and to measure the other frameworks. It is "WP 1.4 gate" in the plan (row 0.5 and the WP 1.4 row). It is also where the last unbuilt piece, part 2b, belongs.

### Spend limit (decided by Saqlain, 14 Oct)

- **Hard limit for this check: $1.50.** The plan's total approved cap is $7 for three checks (WP 1.4, WP 4.6, and the one after WP 5.1), and one demo run. This check must leave about $5.50 for the rest.
- Estimate the cost before the run (companies x runs x average cost from earlier run logs in `~/cyberassess-runs/`). If the estimate is above $1.50, cut the company set or the number of runs. Do not ask for more.
- If a live run passes $1.50 while running, stop it and report. Never raise the limit yourself. Saqlain once typed "$125"; he confirmed $1.50 when asked. $125 is NOT approved.
- Aggregate numbers only. Never read `validation/companies/*/answer_key.json` yourself and never tune a prompt against a specific planted gap (decision D-P5-9-C). The scoring script reads the keys internally and writes aggregates; use only its output.
- `OPENROUTER_KEY` comes from the environment the app already loads. Never read `.env`, never print the key.

### Steps

1. **Part 2b (small, narrow).** `app/services/followup_engine.py`, around lines 98 and 188: add a framework-aware branch so non-DPDPA assessments do not get DPDPA-flavored follow-up requests. Existing DPDPA requests stay exactly as they are. Spec: `tasks/handoffs/2026-10-10-document-budget-design.md`, "Stage 2b" (revision 4 changes, about line 255). The judge prompt freeze stands: do not edit `app/frameworks/prompts.py` text or any file under `app/services/grounding/`. If the follow-up branch needs a prompt change that touches frozen text, stop and write down what you would change; do not make it.
2. **Offline checks first, no money spent.** Full suite with `OPENROUTER_KEY=""`; the DPDPA golden tests; the judge request fingerprint tests (`tests/test_p6_1b_framework_batching.py`, `tests/test_remaining_llm_call_sites.py`). A new offline test for each framework's follow-up request (all six frameworks) belongs here.
3. **Pick the reduced company set.** Two or three of the five packs in `validation/companies/` (c0-example is the sample; c1 to c4 are the real ones). Choose by slug and their client-visible README, never by looking at answer keys. Include one DPDPA-only company, one with ISO or NIST, and keep the set the same for both sides.
4. **Run before and after.** "Before" is the commit just before Wave 2: `d7b8227` (merge of PR #151). "After" is your branch with 2b. Same companies, 2 stability runs each, same settings. Use `scripts/validation/run_company.py <slug> --runs 2 --llm live --out <dir>` then `scripts/validation/ab_compare.py --arm before=<dir> --arm after=<dir> --baseline before --out <file>`. Check each script's `--help` first; the earlier gate's record is `tasks/handoffs/2026-09-28-p6-5-v2-ab-and-flip.md` and its run directories under `~/cyberassess-runs/2026-09-30-p6-5-v2-abstain`.
5. **Judge the result by the rule in the spec:** catch rate not lower; false positives on decoys and clean controls not higher; stability not lower; cost reported. A small change inside normal noise is a pass; say how many runs and how large the swing was.
6. **Report in plain language:** pass or fail in one sentence, what it cost in dollars against the $1.50, what you ran, and the aggregate table at the end. Save run logs outside the repo (`~/cyberassess-runs/wave2/gate/`). Do not commit run output.

### Rules for this job

- No Claude or Codex attribution on commits or PRs. Push and open PRs yourself; never merge.
- Tests: `OPENROUTER_KEY=""` for every offline run; never `env -u` (a `.env` file still loads and would spend money). The live run is the only run with a key.
- If the gate fails, do not "fix" it by loosening the comparison. Report what dropped and stop.

## Job 2: WP 2.8, reject needs a reason, and undo (lane C, Codex)

### What it is (plan row 2.8, finding F-A16)

- Reject requires a stored reason. Today the old Jinja Reject form sends "Not stated" as the reason until the Next.js port (audit item A7). That default must go; a reject with no reason is refused with a visible error and nothing is saved.
- Undo is added to the API for a decision (reopen already exists: `POST /api/assessments/{id}/conclusions/{conclusion_id}/reopen` in `app/routers/conclusions.py`). Undo of a reject or approve returns the conclusion to its prior reviewable state and records who did it and when; it does not delete history.
- The reviewer name defaults from Settings (firm settings; `app/routers/firm_settings.py`) instead of being retyped or blank.

### What you do

1. Map the surfaces with one Sonnet Explore agent: where reject is sent from (the "Not stated" string, the review queue and conclusion card templates, `app/routers/conclusions.py`, `app/routers/review.py`, `app/services/conclusion_review.py`), where reviewer name is read, and which tests pin the current behavior. Verify its key claims in code yourself.
2. Settle any open product decision with Saqlain in one question batch. Likely: wording of the refusal message; whether "undo" is available after the report is released (recommend: no, only before release, and say so in the error); whether the Settings default can be overridden per review (recommend: yes).
3. Write `tasks/handoffs/2026-10-DD-wp-2.8.md` in the same shape as the WP 2.4 handoff, including a files-owned list that keeps it away from WP 2.3 and 2.5 (export code, scoring, `pdf_export.py`, `board_report.py`).
4. Docs PR for the handoff; Saqlain merges; then one worktree from `main`, symlink `.venv`, copy the kickoff to `WP-2.8-KICKOFF.md`, and dispatch one background Codex run: `codex exec -m gpt-6.1-sol -c model_reasoning_effort="medium" --sandbox workspace-write -C <worktree> "<prompt>" < /dev/null > ~/cyberassess-runs/wave3/wp28.log 2>&1 &` (create the log directory first).
5. After the run: read Results, review the diff against the file lists, run the verify command and the full suite yourself, smoke on the seeded demo (`scripts/demo/seed_demo.py --db <path>`; the seeder writes uploads under `<UPLOAD_DIR>/demo`, so serve with that path), then commit, push, open the PR. Never merge.

## Do not start yet (waiting)

- WP 2.3 (score band wording) and WP 2.5 (out-of-scope conclusions): both deliberately change a reference report. They merge only after the safety check above passes, and one at a time so each report is re-recorded on its own.
- WP 2.7 (export clean-up): after 2.3.
- WP 3.5 (finding anatomy storage): needs Saqlain's sign-off on the finding anatomy (plan item 0.2).

## Lessons that held in Wave 2 (read before dispatching Codex)

- Codex stops and asks when a test outside its file list conflicts. Read the conflict before agreeing. Most were mechanical (head pins, fixtures). Two proposed edits were really product questions; fix the product, not the assertion.
- Give a standing authorization for one narrow mechanical class (head pins and downgrade targets) up front; it saved several round trips.
- Codex cannot commit (the git index is outside its sandbox). The orchestrator commits, pushes and opens the PR. Save its Results files to `~/cyberassess-runs/<wave>/` before removing the worktree.
- To resume a stopped Codex run: `cd <worktree> && codex exec resume <session id> -m gpt-6.1-sol -c model_reasoning_effort="medium" -c sandbox_mode="workspace-write" "<answers>" < /dev/null > <log> 2>&1 &`. The session id is in the first lines of its log.
- A background `&` inside a backgrounded Bash call makes the "finished" notice fire for the wrapper, not the job. Check `pgrep` and the log. In zsh, quote or array-ize word lists (a plain `for b in $LIST` does not split).
- A handoff test written too strictly can be wrong (the WP 2.6 mixed-framework case). Check a handoff's new-test list against the real behavior before dispatch.
- The full suite takes about 5 minutes and is the one thing worth running yourself after every Codex run.

## Open items for Saqlain (carried over)

- Legal: confirm 13 May 2027 is also the commencement date for the DPDPA penalty provisions and that the Schedule wording in the report is accurate; older legal-review items (BN.NOTIFY.3 "Section 8(4)-(6)", `questionnaire.py:90`, `clusters.py:1013` and `1026`).
- Bug: HTML board-report preview returns 500 on the Veldhara demo (`app/services/board_view.py:201`, None score). Small side job if he wants it.
- Follow-ups already listed in PRs #152 and #153: `prior_period` still subtracts raw scores across scope; `reports.py:get_comparable_assessments` still matches by company name; "India DPDPA —" prefix on domain names; `_framework_structure_text` prints catalog counts, not in-scope counts; board cover fallback and severity legend still DPDPA-flavored (WP 2.7).
- Still unmerged older branches, about 30 merged ones can be deleted on his word; worktrees with unsaved work: `~/dpdpa-ucf`, `~/dpdpa-s6f1`, `~/dpdpa-doc-reads-review-2`, `~/dpdpa-evidence-c`.
