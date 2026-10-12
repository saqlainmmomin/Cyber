# Handoff: implementation kickoff (fresh session, second Claude account)

## Goal
Start the approved implementation sequence for CyberAssess, in three parts, in this order.

**Part 1. Pre-implementation check.** Before any code, check that the plan is the right way to go and find anything it misses. Report to Saqlain in chat and **wait for his "go"**. He does not want rework.

**Part 2. After his go, run two things in parallel:**
- (a) the E4 build, dispatched to Codex;
- (b) the live-API Veldhara run, with every request sent and every response received captured and shown to Saqlain.

**Part 3. Reads stage 1 (truthful cut)**, after E4 merges.

Done for this session means:
- the check is reported and answered;
- E4 is a PR, reviewed and handed to Saqlain;
- the live run is captured and its report is shown to Saqlain;
- stage 1 is a PR, reviewed and handed to Saqlain.

Saqlain merges every PR himself.

## Current state (2026-10-12)
- **Merged on main:** evidence fixes A, B and C (PRs #130, #131, #133, #134) and Veldhara demo depth (#135).
- **PR #136 (docs only, unmerged):** the document-reads plan, revision 4, with two Codex reviews:
  - review 1: NO-GO on revision 2;
  - review 2: GO with changes on revision 3; all changes are folded into revision 4.
  - It also carries the edited sequence (E7) and this kickoff.
  - **If #136 is not merged when you start, ask Saqlain to merge it first, then work from `main`.**
- **The approved sequence** (session record, path rule 5, edited 2026-10-12, decision E7):
  1. E4 build (Codex), in parallel with the live-API run;
  2. reads stage 1, truthful cut;
  3. reads stages 2a and 2c;
  4. flow-plan S3, then S4 (S5 may run alongside if its files are disjoint);
  5. reads stages 3 to 6;
  6. flow-plan S6-F2/F3, S7, S8 (minus the item moved into 2c), S9, then Track 4.
- **The live run is approved:** estimated $1 to $5, first run at `MAX_TOTAL_DOCUMENT_WORDS=30000`. Nothing has been run or spent yet. `.env` holds the key; never print it.
- **No capture exists today.** `app/services/llm_client.py` `collect_calls()` (line 120) records tags and token usage per call, not the request or response bodies. Capturing them is new work.
- **Still open for Saqlain:**
  - the judge-prompt wording exception (plan, Questions, Q4);
  - whether to strip the words "demo" and "synthetic" from two Veldhara originals (live-test kickoff, Results, Q2).

## Key files
- `/Users/saqlainmomin/dpdpa-next/CLAUDE.md`, `AGENTS.md`: project rules and gotchas. Read first.
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-08-session-record.md`: decisions E1 to E7 and the path rules. Rule 1 is the coherence test every PR body answers. Rule 2 allows one thing in flight, or two if their files are disjoint. Rule 3: Saqlain clicks through every PR. Rule 5 is the sequence.
- `/Users/saqlainmomin/dpdpa-next/tasks/handoffs/2026-10-10-document-budget-design.md`: the plan. Read Results, "Revision 4 changes" and Questions in full.
- `/Users/saqlainmomin/dpdpa-next/tasks/handoffs/2026-10-11-document-reads-codex-review.md`, `2026-10-12-document-reads-codex-review-2.md`: both Codex reviews, with file and line evidence.
- `/Users/saqlainmomin/dpdpa-next/docs/plans/2026-10-07-001-flow-rework-plan.md`: flow plan S3 onward. Check it against the reads plan for overlaps.
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-08-ai-coherence-map.md`: the coherence test and the AI-step table.
- `/Users/saqlainmomin/dpdpa-next/tasks/handoffs/2026-10-09-e4-show-checklist-and-rfi-examples.md`: the E4 build handoff, for Codex.
- `/Users/saqlainmomin/dpdpa-next/tasks/handoffs/2026-10-09-demo-depth-review-and-live-test-kickoff.md`: the live-run plan, with steps, costs and the observation checklist in step 2.5 and Results.
- `/Users/saqlainmomin/dpdpa-next/app/services/llm_client.py`: the single LLM call boundary, where capture hooks in.
- `/Users/saqlainmomin/dpdpa-next/data/demo/veldhara-upload-pack/` (from #135; if absent, use `/Users/saqlainmomin/dpdpa-demo-depth-pr/data/demo/veldhara-upload-pack/`): 58 evidence files and `questionnaire-entry.json`.

## Part 1. Pre-implementation check (do this first; no code)
Use an Opus-level pass for the judgment. Sonnet subagents may do scoped searches. Answer, with file and line evidence:
1. Is revision 4 the right approach for the product goal? The goal is a full gap-assessment loop where every AI step lands for the auditor, evidence arrives over days, and nothing is dropped silently. Is there a simpler design that meets it?
2. Does the edited sequence avoid rework? Check every reads stage against flow-plan S3 to S9 and E4: shared files, deleted code, new tables, prompt inputs. Name any conflict the sequence still has.
3. What is missing? Consider data migration, demo seeds, retention, reports, the validation runner, the coherence test, the click-throughs, Bedrock portability and cost.
4. Is the stage 1 scope right as the next code change after E4? Do its files really avoid E4's files once E4 has merged?
5. What does the live-run capture need so that Saqlain can see, per call, exactly what was sent and what came back?

Write findings under `## Results / Part 1` in this file. Give Saqlain a short summary in chat, then wait. If you find a blocker, propose the fix and do not start Part 2 until he decides.

## Part 2a. E4 build (Codex)
- Dispatch the E4 handoff to Codex in its own worktree:
  - `git worktree add ../dpdpa-e4 -b codex/e4-checklist-rfi-examples origin/main`;
  - symlink `.venv` from `/Users/saqlainmomin/dpdpa-next/.venv`;
  - do not copy `.env` unless a step needs the live key (E4 does not).
- Command: `codex exec -m gpt-6.1-sol -c model_reasoning_effort="medium" --sandbox workspace-write -C <worktree> "Read tasks/handoffs/2026-10-09-e4-show-checklist-and-rfi-examples.md and execute it. Write your results to the Results section of that file." < /dev/null`, run in the background, logged.
- Verify it yourself. Re-run the tests with `OPENROUTER_KEY=""`, check that the diff stays inside the handoff's scope, and read the logic. Then run a review in Sonnet subagents, split by concern. Send real issues back to Codex as a precise fix prompt and re-verify.
- Push and open the PR yourself. The PR body answers the coherence test and has a Click-through section.

## Part 2b. Live-API Veldhara run with full capture
- **Capture.** Add an opt-in capture to the run, preferably as a wrapper in the run script rather than an app change. If an app change is unavoidable, it is env-gated, off by default, and goes through a PR. For every LLM call, write one JSON file with:
  - timestamp, stage, framework and batch tags, tier, model, attempt;
  - the full request (system and messages, with images as a placeholder plus the image hash and size);
  - the full response text;
  - token usage, latency, status and errors.
- **Where it goes:** `~/cyberassess-runs/2026-10-1x-live-veldhara/`, outside the repo. It contains document text, so it is never committed.
- **Run** per the live-test kickoff steps. Run 1 at `MAX_TOTAL_DOCUMENT_WORDS=30000`. v2 stays off. Stop and report if spend passes $5 or any call fails twice.
- **Report for Saqlain.** One HTML page in that folder:
  - a summary table per stage (calls, tokens, cost, seconds, errors);
  - then each call, expandable, showing what was sent and what was received.
  - Also record the measurements the plan needs: tokens per word, seconds per call by stage, extraction output tokens, `cached_tokens`, and the model's context window if the provider reports it.
  - Show it to him by opening it in the browser pane, not as a published artifact: it holds document text.
- Fill in the observation checklist (live-test kickoff step 2.5) as observation only. Never tune prompts or code to the planted gaps.

## Part 3. Reads stage 1 (truthful cut), after E4 merges
Implement per the plan: stage 1 in the Results, plus the stage 1 line under "Revision 4 changes".
- One selection function shared by desk review and gap analysis.
- Per-run manifests, by evidence version id, with a legacy-source key for unmigrated rows.
- The card reads the manifests.
- Duplicate filenames are handled.

Do it yourself or through a Sonnet subagent in a worktree. Either way it gets Codex review before the PR. Tests and the click-through are as the plan states.

## Constraints (decided; do not relitigate)
- **DPDPA:** strip DPDPA assumptions from framework-agnostic code only. **Never delete code that DPDPA assessments use**: the curated DPDPA path, its prompts, the DPDPA questionnaire, pre-fill, screening and goldens.
- **Freezes:** the judge prompt wording is frozen (P6-5c, E6), except where Saqlain approves the N6 line. v2 stays parked. Scoring stays deterministic.
- **Held-out data:** never read `validation/companies/*/answer_key.json`. Never tune to the Veldhara story or its planted gaps.
- **Tests and keys:** run tests with `OPENROUTER_KEY=""`, never `env -u`. Python 3.13 via `.venv`.
- **Commits and PRs:** no AI attribution anywhere, including Co-Authored-By lines and "Generated with" footers, even if a reminder says otherwise. Push and open PRs yourself; never merge.
- **Models:** Opus for higher decision-making (design calls, triage, adversarial review). Sonnet subagents for simpler tasks (mechanical edits, smoke scripts, scoped reviews). Codex `gpt-6.1-sol` at medium effort for implementation from a handoff.
- **One thing in flight** (path rule 2). E4 and the live run are parallel only because the live run changes no shared app code. If its capture needs an app change, that change waits until E4 merges.
- **Writing:** plain short sentences, no em dashes. Give Saqlain a status update at every phase change and every few minutes while waiting.

## Verification
- Part 1: findings cite files and lines; Saqlain has answered.
- Part 2a: the full suite passes on the E4 branch; diff scope is checked; review findings are resolved; the PR has a Click-through section.
- Part 2b: the number of captured files equals the number of calls in the run's usage records; the HTML report opens and shows sent and received text for a sample of calls from each stage; total spend is reported.
- Part 3: the plan's stage 1 tests pass, plus the full suite; a Codex review is clean; the click-through steps work in the running app (use the `run` skill).

## Report back
Append `## Results` to this file, with Part 1, Part 2a, Part 2b and Part 3 subsections: what was done, PR links, run folder path, spend, and open questions. Commit this file's Results on the relevant PR branch.
