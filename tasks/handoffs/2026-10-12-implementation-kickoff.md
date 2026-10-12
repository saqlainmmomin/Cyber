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
- **Freezes:** the judge prompt wording is frozen (P6-5c, E6), except for the N6 line, approved 2026-10-12. v2 stays parked. Scoring stays deterministic.
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

## Results

### Part 1. Pre-implementation check (2026-10-12)

**Verdict: GO, with six small changes to revision 4 that cost nothing now and would cost rework later.** Nothing blocks Part 2. Nothing in revision 4 needs to be re-done. I read the plan, both Codex reviews, the session record, flow-plan S3 to S9 and the E4 handoff, and checked each claim below in the code on `main` at d50cc61. Line numbers are from today; several in the plan have drifted by a few lines.

**Setup facts.**
- The kickoff was only on the unmerged branch `claude/document-reads-design`. #136 has since merged, so I fast-forwarded this worktree to `origin/main`.
- #137 (strip "synthetic" from two Veldhara originals) is still open.
- `scripts/demo/seed_intake.py` is untracked in this worktree and not mine. I will not touch or commit it.

#### 1. Is revision 4 the right approach?

Yes. The simpler alternative fails a decision Saqlain already made.

- **Simplest alternative:** remove the cap, batch desk review, and cache the existing per-framework extraction by file hash, framework and prompt fingerprint. A later run then pays only for new files. It needs no queue, no dispatcher, no reconciliation and no readiness gate.
- **Why it loses:** the work happens when the consultant clicks Run, not on arrival. That is the 20 to 30 minute end-of-assessment run Saqlain rejected on 2026-10-11 (plan Decisions table). So reading on arrival stays.
- **The design is right in shape.** The size comes from three things that are optional:
  - stage 6b (retire the setting and the off branches);
  - one extraction call per framework per part;
  - generation ids with re-read history.
  
  None of them has to be built to reach the goal. Stage 6b is already last. The other two are cheap to keep.
- **Cost model correction.** The UI enables three frameworks, not six (`app/routers/web.py:86`, `ENABLED_ASSESSMENT_FRAMEWORKS = ("dpdpa", "iso27001", "nist_csf")`; flow-plan P8). The plan's six-framework case is not reachable through the product today.
  - Estimate for 100 files, 100k words, three frameworks: 130 reader + 390 extraction = 520 read calls. That is about $0.5 and about 22 minutes at concurrency 6 and 15 s a call (33 minutes at 4).
  - Inputs: the plan's 1.6 tokens a word, $0.14 and $0.28 per million tokens, about 5k tokens of control text per extraction call (Codex review 2, N7). Not measured.
  - The Veldhara case (122 calls, about $0.08) is unchanged.
- **Where to look first:** the live run decides combined versus per-framework extraction and the part size. Stage 3 is fifth in the sequence, so those measurements arrive in time. Keep both choices open until the run's numbers are in.

#### 2. Does the edited sequence avoid rework? Conflicts still present

| # | Where | What conflicts | Fix (cheap, now) |
|---|---|---|---|
| C1 | Stage 1 and E4 | Same files: `app/services/requirement_card.py` (budget lists at `:169-170`, `:210-211`, `:331-332`, `:643-649`; E4 at `:660`, `:683`, `:806`), `app/templates/components/requirement_card_body.html` (`:17`), `tests/test_p6_7_requirement_card.py`. | Already handled: stage 1 waits for E4 to merge (kickoff Part 3). Keep it that way. Rule 2 would otherwise forbid it. |
| C2 | Stage 3 `reconcile_reads` and S3, S4, S7 | The plan calls `reconcile_reads` "after commit on every path in Codex's path table". That table was drawn on 2026-10-11 code. S4 adds an evidence-to-RFI-item link and a client-link scope path. S7 adds interview evidence. A path table rots the day the next slice lands. | Make the dispatcher sweep the reconciliation on a short interval (and nudge it after commit). The wanted set is already one query, `active_versions_in_scope` (`app/services/evidence.py:843-865`), crossed with the assessment's frameworks. Future write paths then need no instrumentation. Keep the startup and backfill calls. Add one test that lists every writer of `Evidence.assessment_id` and `EvidenceUse`. |
| C3 | Stage 4/5 and S7 | S7 stores meeting notes as Evidence with source "interview" (flow plan S7). `Evidence` has no source field today (`app/models/evidence.py:10-29`). Today every in-scope evidence row reaches desk review (`analysis_documents`, `evidence.py:879-915`). Under reads, interview notes would be read by the framework reader and enter judge passages. That puts the operating side (interviews) into the design side (documents), against P1. | Add one rule to stage 3: reads are created only for document-source evidence. S7 sets its source and is excluded, or included knowingly. State it in the plan now. |
| C4 | Stage 5 and S5 | S5 (side-by-side card, built before stage 5) shows "the cited document". Stage 5 keeps `document_id` empty for new-mode findings. Consumers of `document_id`: `app/routers/desk_review.py:97`, `:121`, `app/services/desk_review_findings.py:65`, `app/routers/web.py:3734`. | Build S5 against `citations_json` (versioned), never `document_id`. Add one line to the S5 scope. |
| C5 | Stage 5 and S6-F2 | S6-F2 stores an as-of date on `EvidenceVersion` and feeds it into desk-review prompts. Stage 5 replaces that input with a catalog line per file. The reader also extracts "period". Two sources for one fact, and a prompt edit against input that is about to change. | Rescope S6-F2 now: the date is an `EvidenceVersion` column, set at upload or read, and appears in the stage 5 catalog line. No separate prompt edit. Drop "period" from the reader or make it the source of that column. |
| C6 | Stage 2c and S8 | Stage 2c adds framework-conditional section refs on conclusions and the review queue. S8 later merges Queue and Conclusions into one screen (P4). If the refs are written in the two templates, S8 redoes them. | Write the refs in one service helper, not in templates. S8 then reuses it. |
| C7 | Stage 6 gate and S3 | Revision 3 says the stage 2 A/B baseline "stands alone" for stage 6. S3 removes the context-profile header from the analysis prompt (flow plan S3, P2) and changes input between the two. Comparing stage 6 to the stage 2 baseline confounds the two changes. | Stage 6 compares setting off versus on at the same commit only. Never against the stage 2 baseline. |

**Checked and fine:**
- Stage 2a/2b/2c against S3: 2a edits `_get_selected_frameworks` (`app/routers/questionnaire.py:321-327`), which the questionnaire routes use (`:167`, `:204`), not the context routes S3 deletes. 2b is already trimmed to the follow-up engine. S3 and S4 migrations form one linear Alembic chain behind 2a's new revision.
- S3 deletes `context_profiler`. 2a/2b/2c do not touch it.
- S4's new tables go on the purge list with stage 3's read tables (`app/services/retention.py`); the FK-order test covers both.
- S6-F3 (re-map to another RFI item) does not change read identity.
- S9 is content only.

#### 3. What is missing

| # | Gap | Evidence | Add to |
|---|---|---|---|
| M1 | **No way for a file to become "explicitly unreadable".** Readiness (N5) refuses a framework run while any read is queued or failed. The plan lists "not readable" as a settled state but gives no action that sets it. One corrupt scan would block the whole framework. | plan Contracts, Readiness | Stage 4: a "Mark not readable" button that stores who, when and why, and shows on the card and the report as "excluded by consultant". This is also how "nothing dropped silently" holds when the consultant chooses to drop. |
| M2 | **Reader fields that nobody sees.** The reader returns type, period, owner and summary; stage 4 displays only the summary and passages. That is the "stored, never rendered" failure the coherence map found at step 4 (`tasks/2026-10-08-ai-coherence-map.md`). | plan Stage 4 | Stage 4: show type, period and owner on the evidence record, or drop them from the reader prompt. Treat the reader's type as a suggestion beside the consultant's upload category, not a second truth. |
| M3 | **Silent bulk re-read on a settings change.** Fingerprints include model id and prompt fingerprint. A model switch (Track 4, Bedrock Mumbai) or a prompt edit makes every read stale and the sweep queues them all. That is a surprise spend and a long background job. | plan Stage 3 read identity | Stage 3: re-reads caused by a fingerprint change need a cost preview and an explicit confirm. New uploads queue without asking. Also make `reads_max_concurrency` respect the provider's rate limit, since Bedrock quotas differ. |
| M4 | **Click-throughs for stages 3 to 5 need real reads.** `scripts/demo/seed_demo.py` stubs the LLM (`:1240-1263`). "Drop the Veldhara pack and watch files fill in" would cost money each time, or show nothing. | plan Stage 4 click-through | Stage 4: an env-gated deterministic fake reader at the reader seam, as `tests/support/analyzer_mock.py` does for analysis. The live run's captures can seed its fixtures (private folder, so it is Saqlain's call). |
| M5 | **Stage 1 manifest has a home, and it needs no migration.** The plan does not say where manifests live. | `app/models/analysis_run.py:10-21` (`claims_json` envelope per framework, created in `app/services/analysis_pipeline.py:179-215`, called at `app/routers/analysis.py:280`, `:539`); desk review keeps its budget lists in `raw_ai_response` (`app/services/desk_review.py:490-511`) | Put the gap-analysis manifest in the run envelope and the desk-review manifest in the same JSON. No new table, no Alembic revision in stage 1. |
| M6 | **Stage 1's selection function has two callers with different orders.** Desk review does not sort: it takes documents in upload order (`app/services/desk_review.py:692-708`). Gap analysis sorts by the legacy DPDPA category list (`app/services/claude_analyzer.py:419-456`, `:426` priority list), in the multi-framework path (`:521`) and in the curated DPDPA path (`:89`). The two stages drop different files today, and the plan's "both sort" is wrong for desk review. | | Stage 1: one function with an ordering argument. Registry frameworks use upload order (no DPDPA list in shared code). The curated DPDPA path keeps its priority list so the goldens stay byte for byte. The existing test `tests/test_remaining_llm_call_sites.py` ("truncation preserves document order") and the fingerprint test (`tests/test_p6_1b_framework_batching.py:152`) are updated deliberately. |
| M7 | **`analysis_documents` carries no version id.** Manifests are "by evidence version id" but the dict has `id` = evidence id (`app/services/evidence.py:895-903`). Duplicate filenames collide in `doc_id_by_filename` (`desk_review.py:82`). | | Stage 1: add `evidence_version_id` to the dict and key manifests and links by it, not by filename. |
| M8 | **Report coverage.** The plan says reports are untouched. Reports do not name unread or excluded files today (no `budget_` or "not read" reference in `app/utils/pdf_export.py`, `app/services/narrative.py`, `app/services/approved_report.py`). A released report can therefore hide a dropped file even after stage 1. | grep, no hits | Stage 1 or 5: one line in the report's evidence basis, "N files read, M not read (names)". Additive-only PDF rule applies: add a section, do not rewrite pages. Saqlain to confirm. |

Also checked and found fine: retention of read text (stage 3 purges reads before versions), the validation runner (settle-wait is in stage 6), the injection pack (stage 4 adds one for the reader), the coherence test wording for stage 5.

#### 4. Is stage 1 the right next code change after E4? Do its files avoid E4's?

- **Right change, right time.** The card says "Partly read by the analysis" from desk review's list alone (`app/services/desk_review.py:725-740`, `requirement_card.py:331-332`). Gap analysis cuts a different set (M6). Until stage 6 flips, which is after S3, S4 and stages 3 to 5, the cap is live and the card is wrong for the judge stage. Stage 1 is the cheapest fix.
- **Files:** `desk_review.py`, `claude_analyzer.py`, `evidence.py`, `analysis_pipeline.py` (envelope), `requirement_card.py`, `requirement_card_body.html`, `desk_review_findings.html`, `web.py:3729-3773` and their tests. Once E4 has merged, only the card files overlap E4's, and that is a rebase, not a conflict. Disjoint from the live run (no app change).
- **Keep it small.** The selection unification is the one throwaway part: stage 6 deletes `_truncate_documents`. The manifests, the card change and the version-id key are the durable parts. Build the selection function as thin as M6 describes.
- **Optional, after the run:** if the live run at 30,000 words shows acceptable latency and cost, raising `max_total_document_words` (`app/config.py:21`) is a one-line interim that removes most real cuts now. It does not replace stage 1. Decide after the numbers.

#### 5. Capture design for the live run (no app change)

**Seam.** Every LLM call, including vision OCR (`app/services/document_processor.py:449-457`) and the parked grounding client (`app/services/grounding/pipeline.py:45`), goes through `llm_client.call_llm`, which calls `_send(request_kwargs, tier, model, stream, attempt)` (`app/services/llm_client.py:237`, `:346`). A launcher that patches `llm_client._send` captures the full request body and the assembled response text. It runs in the caller's thread, so the `_tags` context variable (stage, framework, batch) is still visible there (the provider interaction runs in a worker thread that does not inherit it; `_send` is the last place that does). Parallel batches carry the tags through `app/services/parallel.py:6-34` (`copy_context`).

**What each call file holds** (`calls/NNNN.json`, one per `_send`):
- timestamp, stage, framework_id, batch, tier, model, attempt;
- request: system (string or blocks), messages, `max_tokens`, `temperature`, `response_format`, and whether it streamed;
- images replaced by a placeholder with sha256, byte size and media type, with the decoded image saved beside it in the same private folder so the report can show it;
- response: full text, `finish_reason`, usage (input, output, cache read, reasoning), latency in ms;
- status (ok, error, JSON parse failure computed with `is_json_text`) and the error type.

**What it does not hold:** API key or headers. `_send` sees only the body, and the client holds the key.

**Reconciliation.** The launcher also wraps `_record_call` (`llm_client.py:152`) and counts calls. The report shows both counts, so "captured files equal usage records" is checked in the run itself, not by me afterwards.

**Spend.** Tokens times the plan's price assumptions is the live meter, with a hard stop: when the running estimate passes $5, or one call fails twice, the next `_send` raises and the run stops. The actual spend comes from the provider's key-usage endpoint, read before and after the run (key never printed). `_usage_dict` drops the provider's own cost field (`llm_client.py:205-232`), so the endpoint delta is the ground truth. Reasoning tokens: the run records them (`reasoning_tokens` in usage) to confirm the `enabled: False` setting holds (`llm_client.py:79-82`).

**Where files go (all new, in `scripts/live/`, no app change):**
- `capture.py`: the patch and the file writer. Refuses an output folder inside the repo.
- `serve.py`: sets `DATABASE_URL` and `UPLOAD_DIR` to the run folder, `MAX_TOTAL_DOCUMENT_WORDS=30000`, `ANALYSIS_PIPELINE_VERSION=v1`, installs capture, starts the app in-process on 127.0.0.1. Saqlain can click through the real UI if he wants.
- `drive.py`: an HTTP driver (upload with `upload-manifest.csv` categories, enter `questionnaire-entry.json`, run desk review, run analysis). It reads only `evidence/`, the manifest and the entry file, never `scenario.json` or `coverage-matrix.csv`.
- `report.py`: writes `report.html` in the run folder.

**Showing it:** serve the run folder with a local static server and open it in the browser pane (not an Artifact, it holds document text).

**Reuse:** the same wrapper is what stage 6's runner needs ("captures read calls, retries, cost"). Built once, under `scripts/live/`, it saves that work later.

#### 6. The E4 handoff has drifted (for Codex)

`tasks/handoffs/2026-10-09-e4-show-checklist-and-rfi-examples.md` was written before #134 and #135 and its line references are stale:
- the v1 `criteria=()` is now at `app/services/requirement_card.py:660` and `:683` (not near 610);
- the guard that refuses v1 is `if card.source != "v2" or match is None` in `add_rfi_request` (`:781-818`, check at about `:806`), not at 418-419 and 743-746;
- `tests/test_p6_7b_add_to_rfi.py:413-463` currently asserts that v1 cards show no add control and the route refuses. E4 part 2c reverses that on purpose, so that test is updated deliberately, not worked around.

I will give Codex the corrected references in the dispatch prompt. The scope itself is unchanged.

#### Plan edits I will fold in on "go" (edit file: the plan, one revision, no redesign)

C2 (periodic sweep), C3 (interview rule), C4 and C5 (S5 and S6-F2 scope lines), C6 (section-ref helper), C7 (gate comparison), M1 to M3 (stage 3 and 4 lines), M5 to M8 (stage 1 lines), and the three-framework cost line. None changes a stage's order or what it delivers.

#### Questions for Saqlain (only these)

1. **Go for Part 2a and 2b as designed?** E4 to Codex in its own worktree. The live run with the capture above, a $5 hard stop, run 1 at `MAX_TOTAL_DOCUMENT_WORDS=30000`, v2 off.
2. **#137 (strip "synthetic") first?** The run uses the generated pack. If #137 merges first the pack matches what an auditor would see; if not, two files still carry the word and the run notes that. Your call; it does not change any measurement.
3. **Report coverage (M8):** do you want released reports to name unread and excluded files? Default is yes, as an additive line. Say no if you want the card only.

Everything else above is a plan edit I will make without asking, unless you object.

### Part 2a. E4 build (Codex) (2026-10-12)

**PR: https://github.com/saqlainmmomin/Cyber/pull/138** (branch `codex/e4-checklist-rfi-examples`, not merged). Ready for your click-through.

- **Dispatch.** Own worktree from `origin/main` (d50cc61), `gpt-6.1-sol` at medium effort. I added a "Drift notes" section to the E4 handoff first, because its line references were stale after #134 and #135. Scope was unchanged.
- **What it does.** v1 cards show the control's signed criteria under "Auditor checklist; not used by this analysis" with no met or unmet marks; v1 cards can add a suggested document to the RFI (idempotent); every scoped RFI request keeps its original text and then lists the mapped controls' signed statements, hints and source bases, a document example from a new 51-type catalogue, and blank Period and Sample size lines.
- **Verified by me, not on Codex's word.**
  - Full suite with `OPENROUTER_KEY=""`: 1,702 passed, 29 skipped on Codex's first pass (my own run: same). After the fix round: **1,716 passed, 29 skipped** (my own run).
  - Prompt fingerprint tests pass unchanged. No prompt, analyzer, grounding, scoring or LLM file is in the diff.
  - Diff scope checked against the handoff. One file outside it: `app/utils/rfi_export.py`. It is necessary, because the PDF and DOCX cut every request at 300 characters and all 55 ISO and NIST requests are longer (median about 2,300). A reviewer confirmed this by measurement and by rendering.
- **Review.** Two Sonnet reviewers (behaviour and tests; PDF/DOCX export), run on top of Codex's own five-lens review. Real findings, all fixed in one Codex round and re-verified:
  - major: the HTML RFI page collapsed the guidance into one run-on line (now pre-line, block level);
  - `KeyError` hazard for a stored document type outside the catalogue (now falls back to "other", with tests);
  - weak or missing tests (pass/fail marks absent, DPDPA scoped item, no-run card refuses add, unconditional PDF overlap, page number format, non-latin-1 text);
  - PDF orphan and widow pagination;
  - DOCX control characters and a leftover truncation.
- **Click-through done by me** on the live run's data (93 v1 ISO conclusions) against the E4 branch: A.5.18 shows 4 criteria with kinds, hints, basis, the label, no tick marks and an add control; the RFI page shows 30 requests with the guidance as separate lines, including the firewall example and the blank Period and Sample lines.
- **Update after your click-through feedback (same day).** You found the RFI text unreadable and asked why one access request carried so many lines. Cause: the RFI is organised by document type, which maps to many controls (access control policy: 7 controls, 20 criteria), and E4 printed every criterion of every mapped control under it. You chose Option A. Now the request lists "What to send" grouped by artifact (12 lines for access, down from about 60), with the per-criterion checks behind a fold on the RFI page and in a "Why We Ask" appendix in the PDF and DOCX. Source basis is kept off client documents because the signed strings contain auditor notes. Final full suite: **1,743 passed, 29 skipped**. PR #138 body was rewritten.
- **Left for you:** catalogue wording sign-off (table in the PR body) and your own click-through. The RFI page shows each request in full (380 to 5,900 characters). Say if you want it collapsed after the first paragraph.

### Part 2b. Live-API Veldhara run with full capture (2026-10-12)

**Result: complete, no failures, about $0.20.** Run 1, `MAX_TOTAL_DOCUMENT_WORDS=30000`, v2 off, one framework (ISO 27001), 57 files uploaded through the real routes and 93 conclusions produced.

| Item | Value |
|---|---|
| Run folder (private, never committed) | `~/cyberassess-runs/2026-10-12-live-veldhara/` |
| Report | `report.html` there (open it with a local static server; it embeds document text) |
| Calls captured | 55, equal to the app's 55 usage records (checked inside the run) |
| Failures, retries, parse errors, length cut-offs | 0 of each. Every call was attempt 1, `finish_reason=stop` |
| Estimated spend (plan prices) | $0.183 |
| Provider key usage delta | **$0.2024** (before 10.5991, after 10.8015). My price assumption was about 10% low |
| Hard stop | $5 estimated, or one request failing twice. Neither was near |
| Code used | `scripts/live/` on branch `claude/live-run-capture`, base d50cc61. No app file changed |

The 58 originals in the pack were generated from `main` before #137, so two files still carry the word "synthetic". The 2025 baseline was not uploaded (the guide forbids it). The December 2023 file was uploaded and left unmapped, as a stale-evidence test. Total words after extraction and OCR: **23,469**.

#### Stages and cost

| Stage | Calls | Input tok | Output tok | Est. cost | Seconds | Notes |
|---|---|---|---|---|---|---|
| Context profile | 1 | 999 | 236 | $0.000 | 7 | on the extract model |
| Vision OCR (11 PNG, 1 more image) | 12 | 19,951 | 3,112 | **$0.107** | 94 (upload stage) | Sonnet 4. **58% of the cost** |
| Desk review (ISO, 6 batches) | 6 | 242,790 | 62,205 | $0.051 | 244 | each batch resends all 57 documents |
| Evidence extraction (ISO) | 1 | 67,573 | 6,033 | $0.011 | 219 | one call for all 93 controls |
| Judge (ISO, 6 batches) | 6 | 22,241 | 21,973 | $0.009 | 182 (last batch) | |
| Follow-ups | 29 | 13,175 | 8,113 | $0.004 | 304 | one call per not-fully-implemented answer |
| **Total** | **55** | | | **$0.183** | | desk review plus analysis: 648 s (10.8 min) |

#### Measurements the reads plan needs

- **Tokens per word:** 1.54 to 1.64 in text calls (mean about 1.6). The plan's 1.6 holds. Images are about 1,700 input tokens each.
- **Seconds per call:** desk review mean 112 s (p50 103, max 166) at about 10.4k output tokens, so roughly 90 tokens a second. Judge mean 81 s (max 182). Follow-ups mean 10 s. Vision mean 7.7 s. Extraction 219 s (one call). A reader call of about 500 output tokens should be about 5 to 10 s, so the plan's 15 s assumption looks reasonable. Still unmeasured for the real reader prompt.
- **Extraction output tokens:** 6,033 for 93 controls (ceiling 65,536). Desk review output averaged 10.4k and peaked at 13,511 against a 16,384 ceiling (82%). **A denser pack could truncate desk review.** No truncation in this run.
- **Extraction input composition (call #50 file):** 292,702 characters: desk-review context 112k (38%, about 26k tokens), controls 20k (7%, about 5k tokens, which matches Codex's figure), documents 160k (55%). So today's extraction call carries roughly as many desk-review tokens as document tokens. The reads plan's per-part extraction drops this.
- **Cached tokens:** 0 on all 55 calls, including 6 desk-review calls with the same system block. OpenRouter prompt-cache passthrough is **not observed** for this model. Treat caching as no help.
- **Reasoning tokens:** 0 on all calls (the `reasoning: enabled False` setting holds).
- **Context window:** the provider response does not report it. The largest request that succeeded was 67,573 input tokens. A 100k-word pack at 1.6 tokens a word is about 160k tokens before controls, so today's single extraction call would not fit a 128k window and would also run past 600 s. That is the real reason the cap exists.
- **Concurrency:** `llm_max_concurrency=4`. Six desk-review batches took 244 s wall against 671 s of call time.

#### Observation checklist (observation only; nothing was tuned)

1. **Evidence page Summary and Key passages.** All 57 evidence pages return 200 with a Summary section. 34 of 57 have Key passages. (Method: fetched `/evidence/{id}` on a copy of the run database with no LLM key.)
2. **Conclusion cards.** 93 cards, outcomes: 39 compliant, 52 partially compliant, 2 non-compliant. 52 cards have a grounded citation with a page or character label and 41 have none ("No supporting citation"). The app dropped 51 ungrounded quotes during citation grounding and 7 at extraction. Citations name the filename and `Characters x to y`.
3. **"N files linked, M cited" and false "Missing evidence".** Cannot be judged on this run. All 93 cards say "No files linked", because the guide's manual path does not map evidence to controls (control references are consultant notes only). 51 cards show "Missing evidence". This is a finding about the flow, not the AI: a policy uploaded to the assessment is in scope for analysis but is not linked to any control, so every card says nothing is linked.
4. **Size-limit notices.** None appeared. 23,469 words is under the 30,000 setting, so nothing was cut. Seeing the notices needs run 2 at the 20,000 default (about $0.20). Not run, as the kickoff specified one run.
5. **OCR.** 12 vision calls, all readable. The email chain screenshot came back with its full text, dates and senders. Output 172 to 316 tokens each.
6. **Pre-fill.** **0 of 93 questions were pre-filled.** Every question has status "deepened", because desk review wrote an absence finding for every control (93 absence rows, 225 evidence rows, 18 signals; coverage 43 adequate and 50 partial). Reconstructed on a copy of the run database with the entered answers removed: still 93 deepened, 0 pre-filled. In this run, the pre-fill step produced nothing the consultant could confirm.
7. **Planted gaps (observation only).** All five were found in the rationale, with correct figures:
   - monthly access reviews (A.5.18, Critical): two incomplete cycles, two omitted systems, eight open removals, four enabled terminated users. Cited to the Statement of Applicability workbook, not to the access review document or export;
   - supplier assurance (A.5.19 non-compliant, A.5.21 and A.5.22 partial): cited to the Statement of Applicability workbook;
   - incident exercise (A.5.24, A.5.25 partial): no grounded citation;
   - annual training (A.6.3 partial): 81% completion, 52 overdue; no grounded citation, flagged "Unsupported assertion";
   - restore tests (A.8.13 partial): cited to the backup log (characters 543 to 609), correct.
   
   One contradiction: A.5.30 is **Compliant** with the rationale "separate restore tests are performed", which A.8.13 contradicts. The card flags it ("Unsupported assertion", "Quote not found in the evidence"), but the proposal itself is wrong.

#### What this means for the plan (for Saqlain to weigh; no edits made)

- The reads plan's cost and time estimates are the right order of magnitude. Vision OCR, which the plan excludes, is the largest single cost at upload (58% here) and needs its own line.
- Desk review output nearing its ceiling and the 219 s single extraction call are the two near-limit points at today's 23k words.
- No caching to count on.
- Stage 1's "card says what the judge actually received" matters here: the judge saw only quotes from one extraction call, and 41 of 93 cards ended with no grounded citation.
- Run 2 at the 20,000 default would show the size-limit notices and a second cost point (about $0.20, about 11 minutes).

**To look at it yourself:** `report.html` in the run folder shows every call, what was sent and what came back. To browse the app on the run's data: `DATABASE_URL=sqlite:///<run>/app.db UPLOAD_DIR=<run>/uploads OPENROUTER_KEY="" .venv/bin/python -m uvicorn app.main:app` from the repo root, then `/assessments/c0176706-523c-4bb7-a2ee-7b177708c728/conclusions`.

### Part 3. Reads stage 1 (truthful cut)

**Not started.** Per the kickoff it waits for E4 to merge (#138), because stage 1 edits the same card files. Plan revision 5 already holds its scope (M5 to M8: manifests in the run envelope, version id on documents, upload order for registry frameworks with the curated DPDPA order kept, report line naming unread files).

### Summary, PRs and open questions

| Item | Link | State |
|---|---|---|
| Plan revision 5, session record E8, this file | docs-only PR on `claude/plan-revision-5` | open |
| E4 build | https://github.com/saqlainmmomin/Cyber/pull/138 | open, needs your click-through and catalogue sign-off |
| Live capture tooling | https://github.com/saqlainmmomin/Cyber/pull/139 | open, no app change |

Spend: about $0.20 on the provider key for the live run (hard cap was $5). No other spend.

Open questions for Saqlain:
1. **Merge order.** #138 first (stage 1 waits on it). #139 and the docs PR are independent.
2. **Run 2 at the 20,000-word default?** About $0.20 and 11 minutes. It is the only way to see the size-limit notices on a real run and gives a second cost point. Not run, because the kickoff specified one run.
3. **Interim cap raise.** Run 1 shows a 23.4k-word pack costs about $0.07 for desk review, extraction and judge, and takes 11 minutes at the current design. Raising `max_total_document_words` (`app/config.py:21`) is a one-line interim until stage 6. Your call; it does not replace stage 1.
4. **#137** (strip "synthetic") is still open. The live pack was generated before it.
5. **Pre-fill produced nothing in run 1** (0 of 93), because desk review wrote an absence finding on every control. That is an observation, not a tuning request. It is the first thing to decide how to treat when stage 5 reshapes desk review.
