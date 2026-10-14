# Next session: start here (13 Oct 2026)

## State in five lines

1. Docs PR #142 (single track plan, Phase 0 answers, handoffs) is merged. This file lives on branch `claude/wave1-context` (docs PR, awaiting Saqlain's merge).
2. Wave 1 (Codex, lane C) ran three work packages from `main`: WP 2.2, WP 1.3, WP 1.1.
3. #143, #144 and #145 are all merged. The queue is unblocked.
4. Saqlain took the vocabulary decisions below on 13 Oct; the plan and session record (E9) carry them.
5. Next work is the queue below; every item needs its own handoff file from the orchestrator.

## What is merged and what is waiting

| WP | PR | State | Tests |
|---|---|---|---|
| 2.2 statute citations | https://github.com/saqlainmmomin/Cyber/pull/143 | Merged | 1,749 passed / 29 skipped on branch |
| 1.3 reads stage 1, truthful cut (branch `codex/reads-stage-1`) | https://github.com/saqlainmmomin/Cyber/pull/144 | Merged | 1,761 passed / 29 skipped on branch |
| 1.1 vocabulary module (branch `codex/vocabulary-module`) | https://github.com/saqlainmmomin/Cyber/pull/145 | Merged | 1,750 passed / 29 skipped on branch |

Each PR passed its own full suite; the combined suite on main is not yet verified, so run it first. The try-import fallback for framework display names in `app/services/approved_report.py` (from #144) can now be deleted and is the first small cleanup. CI registers no checks on these PRs.

## Decisions recorded 13 Oct

- Citations are de-duplicated, concise but traceable. Legal items are verified by Saqlain later.
- One numeric priority map: critical 1, high 2, medium 3, low 4 (`vocabulary.PRIORITY_BY_RISK`).
- Immediate, Short-term, Medium-term, Long-term name the remediation timeframe (PDF windows 0-4 weeks, 1-3 months, 3-6 months, 6-12 months). The field is "Remediation timeframe" (finding editor, actions export).
- Findings and actions use Verified and "Closed and awaiting verification". "Resolved" is retired.
- Board initiative priority uses the same map (stored 1 to 4, shown as the word). Board document and deck goldens were re-recorded.
- Older findings are not migrated.
- PDF evidence-basis line sits under "Documents analyzed:" before the Disclaimer. The report states per-framework counts when cuts differ.
- Edition names stay short in chips and headings and appear in full where a document names the standard.
- Issued-snapshot re-exports use the new word. WP 2.1 will freeze wording at issue time.

## Known issues and parked items

- HTML board report preview returns 500 on the Veldhara demo: `app/services/board_view.py:201` formats a None score with `:.0f`. Present on `main`, not caused by Wave 1.
- Demo seed has no document manifest, desk-review summary, industry questions, or non-Open findings.
- Not done in #144: PPTX/XLSX evidence line, duplicate-filename notice polish, replaced-file notice, extraction-failure marker.
- Not done in #145: unconverted templates allowlist (`design.html`, `design_s9_system.html`, `evidence_inventory.html`, `workpaper.html`, `section_questions.html`, `magic_links.html`, `workpaper_standalone.html`, `board_report.html`); legacy outcome maps (`LEGACY_OUTCOMES`, `LEGACY_PDF_OUTCOMES`) remain until WP 2.3; `framework_label(full=True)` ignores `full`; guard test blind spots (prose and f-strings); `board_derive.is_overdue` compares label text from stored snapshots.
- Left for legal review: pack text "Section 8(4)-(6)" for BN.NOTIFY.3; `app/dpdpa/questionnaire.py:90` says Section 6 where the pack says 4(1); `app/frameworks/mappings/clusters.py:1013` and `1026` differ from the pack.

## The queue

Lanes per `docs/plans/2026-10-13-001-single-track-implementation-plan.md` section 6A (O desktop Claude orchestrator, T terminal Claude, C Codex).

| Item | Lane | Unlock condition |
|---|---|---|
| WP 1.2 stage and status rollup | C | Unblocked |
| WP 1.4 non-prompt parts | C | Unblocked |
| WP 1.4 prompt part | O | Phase 0 sign-offs |
| WP 2.3 score band switch to Readiness (moves goldens) | C | Unblocked (WP 1.1 merged) |
| WP 2.4 to 2.8 | C | Unblocked (WP 1.1 merged; see plan Phase 2 table) |
| WP 3.5 | C | Orchestrator writes the spec first |
| Phase 0 sign-offs, evaluation gates | O | Saqlain's answers |
| UCF part 1 | T | Kickoff already written: `tasks/handoffs/2026-10-13-ucf-part-1-kickoff.md`, branch `claude/ucf-part-1`, worktree `~/dpdpa-ucf` |

## How to start

First 10 minutes:

1. `git fetch`
2. `git switch main && git pull`
3. `OPENROUTER_KEY="" .venv/bin/pytest -q` on main (about 6 minutes). Each PR passed its own suite; this is the first combined run.
4. Delete the try-import fallback for framework display names in `app/services/approved_report.py`.
5. Remove the Wave 1 worktrees and local branches (run these yourself, one path per command):
   - `git worktree remove ~/dpdpa-w1-vocab`
   - `git worktree remove ~/dpdpa-w1-reads`
   - `git worktree remove ~/dpdpa-w1-cite`
   - `git branch -d codex/vocabulary-module`
   - `git branch -d codex/reads-stage-1`
   - `git branch -d codex/statute-citations`
6. Pick WP 1.2, WP 1.4 (non-prompt) or WP 2.3 and write its handoff.

Handoff shape, at `tasks/handoffs/2026-10-DD-wp-<id>.md`: goal, inputs, files owned, files not to touch, rules, one verify command, Results section. Dispatch from a separate worktree, one run per directory, up to three on disjoint file sets.

## Orchestrator rules that held this session

- No Claude or Codex attribution on any commit or PR.
- Push and open PRs yourself; never merge. Saqlain merges.
- Run tests with `OPENROUTER_KEY=""`; never read `.env` or answer keys.
- Use Sonnet subagents for scoped reviews, split by concern.
- Keep the main context clean; read files in narrow ranges.
- State a status line at each phase change and during long waits.

## Lessons

- Codex runs took about 20 minutes each, edit `tasks/todo.md` despite the brief (revert it), leave changes uncommitted (index is outside the sandbox) and leave Results files untracked in the worktree.
- Sonnet review subagents split by concern found real defects every time: one fix round each, then re-verify with a fresh full suite.
- Haiku subagents can launch the demo from a worktree and take Playwright screenshots (venv python has playwright, chromium cached; seed with `scripts/demo/seed_demo.py`, ports 8143 to 8145).
- zsh does not word-split unquoted variables; pass worktree paths as explicit arguments.
- Poll long suites in short loops; foreground commands cap at 120 seconds.
- Review page: https://claude.ai/artifact/LEhDYhruutgdK4xF9EgSRN (source `tasks/2026-10-13-wave-1-review.html`, untracked). Run logs, PR bodies and screenshots are in `~/cyberassess-runs/wave1/`.
