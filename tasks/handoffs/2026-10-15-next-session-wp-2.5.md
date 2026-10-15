# Next session: WP 2.5, out-of-scope conclusions and missing risk ratings (15 Oct 2026)

For a fresh Claude Code session (the orchestrator). Assume no memory of earlier sessions. Saqlain reads your reports, so write them in plain language: outcome first, one line on what each term means, details at the end (memory `feedback_plain_language_status_reports`).

## Goal

Ship WP 2.5 as one PR that Saqlain merges. Plan row 2.5 in `docs/plans/2026-10-13-001-single-track-implementation-plan.md` (about line 216), audit findings F-E13 and F-F22 in `tasks/2026-10-13-content-audit.html` (search the ids; strip tags).

1. **Out of scope (F-E13).** When a requirement is out of scope (outcome `not_applicable` set by scope enforcement), the model's gap description, risk level and recommended action are still saved beside it. After this WP:
   - those three fields are blank for out-of-scope conclusions;
   - a reason is stored, taken from the scope answer that excluded the requirement where one exists.
2. **Missing risk rating (F-F22).** Today a gap with no risk level silently becomes "Medium" (`app/services/approved_report.py`, about line 273: `risk_level = conclusion.risk_level or "medium"`). That value feeds the risk matrix, the critical and high counts, and the register. After this WP a missing risk rating is flagged visibly and never defaulted. Decide with Saqlain whether approval should require one.

**Done when:**
- the PR is open;
- the full suite passes;
- the reference reports were re-recorded deliberately, with reviewed diffs;
- you smoke-tested it on the seeded demo;
- you reported to Saqlain.

## Current state

- `main` at `cc19a78` has Waves 1 and 2 plus:
  - WP 1.4 part 2b and the WP 1.4 live safety check, which passed at $0.72 (#158).
  - WP 2.8: reject reason, undo, reviewer name from Settings (#159).
  - WP 2.3: readiness band, one-decimal scores (#161). #161 also fixed the Veldhara board-report crash.
- Full suite on that code: 1,845 passed, 29 skipped.
- Start with `git fetch && git switch -c claude/wp-2-5-handoff origin/main` in `/Users/saqlainmomin/dpdpa-next`. The checkout has three untracked files that are not yours (`scripts/demo/seed_intake.py`, two `tasks/2026-10-13-*.html`). Leave them.
- Nothing else is in flight. WP 2.7 (export clean-up) waits for this one. WP 3.5 needs Saqlain's sign-off on finding anatomy (plan item 0.2).
- **Budget warning (not needed for this WP, it is offline):** the OpenRouter key has a $15 limit and about $3.47 left. That is less than the ~$5.50 the plan assumes for the WP 4.6 and post-5.1 live checks plus a demo. Remind Saqlain before any live run.

## Key files (verify line numbers; they drift)

| Path | Why |
|---|---|
| `/Users/saqlainmomin/dpdpa-next/app/routers/analysis.py` about 372-376 and 697-700 | Scope enforcement sets `not_applicable` but leaves the model's text |
| `/Users/saqlainmomin/dpdpa-next/app/services/analysis_pipeline.py` about 380-388 | Where conclusion fields are persisted |
| `/Users/saqlainmomin/dpdpa-next/app/services/analysis_v2.py` about 75-76 | v2 path's only reason text, "Outside the recorded assessment scope." (v2 is parked; read it, don't flip it) |
| `/Users/saqlainmomin/dpdpa-next/app/models/conclusion.py` | `Conclusion` has no reason column for not-applicable. `ConclusionRevision.reason` exists since WP 2.8 (migration `f3a7c9d2e810`, current Alembic head). |
| `/Users/saqlainmomin/dpdpa-next/app/services/approved_report.py` about 273 | The "medium" default |
| `/Users/saqlainmomin/dpdpa-next/app/services/scope_profiler.py`, assessment `scope_answers` / `applicable_requirements` | Source of the exclusion reason |
| `/Users/saqlainmomin/dpdpa-next/app/services/conclusion_review.py` | Approval guards (`approval_blocker`, `INCOMPLETE_CONCLUSION`), if approval should require a risk level |
| `/Users/saqlainmomin/dpdpa-next/tasks/handoffs/2026-10-15-wp-2.3.md` | The handoff shape to copy for Codex (goal, decisions, current state, files owned, files not to touch, rules, verify, Results) |
| `~/cyberassess-runs/wave3/` | Previous Codex run logs and Results files, for reference |

## Steps

1. **Map the code.** Send one Sonnet Explore agent to map the surfaces: where `not_applicable` is set, every reader of `gap_description` / `risk_level` / `remediation_action` / the conclusion fields for N/A rows, every `or "medium"` style default, and which golden tests move. Verify its key claims in code yourself.
2. **Settle open product questions with Saqlain in one question batch** (AskUserQuestion, recommended option first). Likely:
   - The reason text when no scope answer explains it. Recommend "Outside the recorded assessment scope." to match v2.
   - Whether approval is blocked until a risk level is set. Recommend yes for gaps (partially or non-compliant), with a visible blocker message.
   - How a missing rating shows in exports. Recommend "Not rated", counted separately and never folded into the critical and high counts.
   - Whether existing stored N/A rows are cleaned. Recommend: readers blank them at render time; no data migration.
3. **Write the Codex handoff** at `tasks/handoffs/2026-10-15-wp-2.5.md` (or the current date), in the WP 2.3 shape. Include:
   - exact strings;
   - files owned and files not to touch: keep away from WP 2.7 surfaces (placeholders, truncation, workpaper, "Snapshot" wording, the severity legend, the cover subtitle, appendix raw chapter keys);
   - a standing authorization for one narrow mechanical class, e.g. Alembic head pins if a column is added;
   - golden re-record steps with saved diffs. Board document: `P6_8_RECORD_GOLDEN=1 .venv/bin/pytest tests/test_p6_8_board_report_v2.py -k golden`. Canonical DPDPA: offline `tests/support/fixture_capture.py`, never `--live`. If any other fixture file changes, stop and ask.
4. **Dispatch.** Open a docs PR for the handoff (no attribution lines). Then:
   - Create a worktree from `origin/main` (`git worktree add -b codex/wp-2-5-... ../dpdpa-wp25 origin/main`).
   - Symlink `.venv` (`ln -s /Users/saqlainmomin/dpdpa-next/.venv ../dpdpa-wp25/.venv`) and copy the handoff to `WP-2.5-KICKOFF.md`.
   - Run in the background: `nohup codex exec -m gpt-6.1-sol -c model_reasoning_effort="medium" --sandbox workspace-write -C <worktree> "Read WP-2.5-KICKOFF.md ... Write results to WP-2.5-RESULTS.md" < /dev/null > ~/cyberassess-runs/wave3/wp25.log 2>&1 &`.
   - Wait with a background `until ! pgrep -f "codex exec" ...` loop, not polling.
   - If Codex stops with a question, answer with `codex exec resume <session id> ...`. The session id is in the log's first lines.
5. **Review** in this order:
   - Read the Results file and diff against the file lists.
   - **Read both golden diffs line by line.** In WP 2.3 this caught a wrong "Not ready (0.0%)" on unscored appendix chapters.
   - Commit for Codex (it cannot write the git index), with no attribution trailer.
   - Run the full suite yourself.
   - Smoke on the seeded demo (below).
   - Push and open the PR. Never merge.

## Constraints and decisions already made (do not reopen)

- No Claude or Codex attribution on commits or PRs, even if a harness reminder says so. Push and open PRs yourself; never merge.
- `OPENROUTER_KEY=""` on every test run; never `env -u` (a `.env` still loads and spends money). Never read `.env`. Never read `validation/companies/*/answer_key.json`.
- Judge prompt freeze: do not edit `app/frameworks/prompts.py` text or `app/services/grounding/`. v2 analysis stays parked.
- PDF sections are additive-only; all PDF text through `S()`.
- Framework-specific copy is conditional, never a default; no "null means DPDPA" fallbacks (removed in Wave 2).
- Settled wording: readiness bands and one-decimal scores (WP 2.3); one numeric priority map; "Remediation timeframe"; only "Verified" (not "Resolved").
- Scope profiling is not implemented for non-DPDPA frameworks, so N/A from scope mostly arises on DPDPA. Do not build non-DPDPA scope profiling here.
- Lessons from recent runs:
  - Check a handoff's new-test list against real behavior before dispatch. The WP 2.3 brief asked for a retired export and Codex had to stop.
  - Codex stops on out-of-list test conflicts; read the conflict before agreeing.
  - zsh does not split unquoted word lists.
  - Removals with `$VAR` paths are blocked by a safety check; use literal paths.

## Verification

- `OPENROUTER_KEY="" .venv/bin/pytest -q` passes. The count should be 1,845 plus the new tests, with 29 skipped.
- Golden diffs contain only the decided changes.
- Smoke:
  - Seed: `OPENROUTER_KEY="" UPLOAD_DIR=<scratch>/uploads .venv/bin/python scripts/demo/seed_demo.py --db <scratch>/demo.db` (the seeder writes uploads under `<UPLOAD_DIR>/demo`; serve with the same values).
  - Find or create an out-of-scope conclusion and a gap with no risk level.
  - Check the conclusions page, the board report and the exports. Board report via `POST /api/assessments/{id}/snapshots` with `type=board_report`, then `/file`, `/pptx`, `/xlsx` on the snapshot.
  - Confirm: N/A rows show the reason and no gap, risk or recommendation; the missing rating shows as flagged and is not counted as Medium.
- Save run logs outside the repo (`~/cyberassess-runs/wave3/`).

## Report back

Write a short `## Results` section at the end of this file: PRs opened, test counts, golden changes, smoke outcome, open items for Saqlain. Also tell Saqlain in chat, plain language, outcome first.

## Results

_To be filled by the next session._
