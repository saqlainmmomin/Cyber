# Handoff: replace the 20,000-word document cap with a design that scales

## Goal
Think through and recommend one definitive way to feed an assessment's evidence to the AI without a hard total word cap. Today the app silently drops documents past 20,000 words. A real engagement is 50 to 100+ files and 20,000 to 100,000+ words. Saqlain: "I don't think we can operate with a cap like this." Done means a decision document in the Results section of this file: one recommended architecture (not a menu), why the others lose, what it costs per assessment, what breaks, a staged build plan with PR-sized steps, and the 2-3 questions only Saqlain can answer. No code, no prompt edits, no live LLM calls in this session.

## Current state (2026-10-10)
- `Settings.max_total_document_words = 20000` (`app/config.py:21`). `max_document_words = 200000` is a separate per-file extraction safety bound.
- The cap is applied in two places: `app/services/desk_review.py:680` and `app/services/claude_analyzer.py:421`. Both sort documents by a category priority list and keep documents until the total hits the cap; later ones are dropped (partly or wholly). Python's sort is stable, so with category "other" the order is upload order (`created_at`).
- v1 flow: desk review sends all kept documents in one prompt (`build_desk_review_user_prompt`), then gap analysis sends them again with the questionnaire. Models: extract, judge and synthesize all `deepseek/deepseek-v4-flash`; vision `anthropic/claude-sonnet-4` (`app/config.py:44-47`). Every call has a 600 s wall-clock deadline with one retry (`llm_request_deadline_seconds`).
- Recent work already added "Partly read by the analysis" notices for truncated documents (evidence fix B/C), so the auditor can see drops, but the drops still happen.
- A parked v2 pipeline exists: `app/services/grounding/` (`chunking.py`, `batches.py`, `sources.py`, `judge.py`, `missing.py`, `pipeline.py`) and `app/services/desk_review_v2.py`, `analysis_v2.py`, switched by `ANALYSIS_PIPELINE_VERSION=v2`. It was parked on 2026-09-30 (`tasks/` P6-5c record, memory `project_p6_5c_park_v2`). Read why before reusing any of it. Do not flip it.
- Test case: the Veldhara pack, 58 files, about 22,500 words, 93 Annex A controls, 11 PNGs (vision OCR). It lives in `/Users/saqlainmomin/dpdpa-demo-depth-pr/data/demo/veldhara-upload-pack/` (PR #135, unmerged). Ground truth is a held-out story; do not tune to it.
- A live run has NOT happened yet. Nothing is measured: all token and cost numbers are estimates.
- Evidence rows carry stable ids, per-document extracted text, a document type and summary from desk review (evidence page Summary and Key passages), and links to controls (manual links, RFI-derived, and citation-derived).

## Candidate directions to evaluate (not a menu to present back; pick and defend one, or a combination)
1. Just raise the cap. Check model context limits, quality at long context, latency against the 600 s deadline, cost, and the lost-in-the-middle risk.
2. Two-stage map then reason. Per document, one cheap call writes a structured digest (type, date, what it covers, key facts, exact quotable passages with offsets). Per control, reason over the relevant digests plus targeted raw passages.
3. Per-control retrieval. Chunk every document, select chunks per control (keyword, embeddings, or the control-to-document-type mapping and UCC clusters), judge each control on its own evidence slice. Bounded cost per control, scales linearly.
4. Reuse the parked v2 grounding pipeline (chunking, batches, judge, missing-evidence). Establish what actually failed and whether the failure is about this problem.
5. Prompt caching of a shared document block across per-control calls (OpenRouter cache passthrough is unverified per CLAUDE.md).
6. Hybrid of the above, with a clear stage order.

Judge each against: (a) the AI-coherence test (every AI step produces something the auditor can see, check against the original in one click, and act on; `tasks/2026-10-08-ai-coherence-map.md`), including never silently dropping evidence; (b) citation integrity, since quotes must resolve to verbatim text with offsets; (c) cost and latency for 100 files and 93 to 200+ controls across six frameworks; (d) fit with deterministic scoring (the LLM outputs qualitative strings only); (e) how much of the existing code and tests survive; (f) the held-out evaluation rule.

## Key files
- `/Users/saqlainmomin/dpdpa-next/CLAUDE.md`: gotchas and constraints.
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-08-ai-coherence-map.md`: the coherence test and the 13-step table; row 5 is this problem.
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-08-session-record.md`: decisions E1-E5 and the path rules (one item in flight, fixed sequence, parking lot).
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-09-parked-coverage-links.md`: parked decision B (suggested control links); closely related to per-control retrieval.
- `app/services/desk_review.py`, `app/services/claude_analyzer.py`, `app/services/llm_client.py`, `app/config.py`: current pipeline and models.
- `app/services/grounding/`, `desk_review_v2.py`, `analysis_v2.py`: parked v2.
- `app/services/evidence.py` (`analysis_documents`, around lines 850 to 990): how documents reach the pipeline.
- `app/dpdpa/prompts.py`, `app/frameworks/prompts.py`: prompt builders (read only).
- `docs/plans/2026-09-21-002-revised-implementation-plan.md`, `tasks/2026-09-21-adversarial-review.md`: decisions D1-D11 that bind.
- `docs/plans/2026-10-07-001-flow-rework-plan.md`: flow plan S3+.

## Constraints (decided; do not relitigate)
- No code changes, no prompt edits, no live LLM or API calls in this session. Read-only. Tests, if you run any, use `OPENROUTER_KEY=""` and never `env -u`.
- Never read `validation/companies/*/answer_key.json`. Never tune design choices against the planted gaps in the Veldhara story.
- v2 stays parked. You may recommend reopening it, but that is a recommendation for Saqlain, not an action, and it must say what has to be decided first.
- Scoring stays deterministic and server-side. Python 3.13. All LLM calls go through `app/services/llm_client.py` on OpenRouter with the tiered models.
- The fixed sequence in the session record stands: this is a design for Saqlain to slot in; it does not jump the queue by itself.
- Plain short sentences. No em dashes. No AI attribution anywhere.

## Verification
- Every claim about current behaviour cites file and line you actually read.
- Any cost number is labeled estimate, shows its inputs (tokens per file, calls per control, price per million tokens from `app/config.py` model names and a stated price source), and gives the 58-file, 93-control case and a 100-file, 6-framework case.
- The plan names the smoke test for each stage (what Saqlain runs in the app, and what a test asserts), and says how a dropped or unread document can never be silent.

## Report back
Append `## Results` to this file: recommendation first (three sentences), then the comparison, cost table, failure modes, staged PR plan, and the questions for Saqlain. Do not commit. Print where the results are.

## Results

Rewritten 2026-10-11 after discussion with Saqlain. Read-only: no code, no prompt edits, no LLM or API calls. The only thing run was a local word count over the Veldhara pack with `OPENROUTER_KEY=""` (no OCR, PNGs skipped). Status: **design for Codex review before any build.**

### Recommendation

Stop reviewing documents as a batch. Read each piece of evidence once, with one AI call, as soon as it is in scope for an assessment, and save what it is and the passages it holds, each tagged to controls with exact offsets. Conclusions are then updated per control, only where evidence changed, by the existing judge working from those saved passages, so there is no total word cap, no 20 to 30 minute wait at the end, and every file's read status is visible.

### Decisions taken in discussion (2026-10-11, Saqlain)

1. Evidence arrives over days, through consultant uploads and client magic links. Analysis must follow arrival, not wait for "all documents".
2. One analysis call per uploaded file. Its saved result feeds the judge and the report later.
3. A 20 to 30 minute end-of-assessment run is too long.
4. No vector store for now (reasons below).
5. Freeze scope, checked against the records: the written freeze covers the **judge prompt only**. P6-5c forbids "a third judge-prompt-wording attempt" (`tasks/2026-09-30-p6-5c-decision-park-v2.md`). E6 says "the v1 prompt stays frozen" in the context of sending criteria to the judge (`tasks/2026-10-08-session-record.md`, E6). CLAUDE.md says "retune the judge prompt". The desk-review and extraction prompts are not named in any decision. One guard exists: `tests/test_p6_1b_framework_batching.py:152-176` pins the ISO and NIST desk-review prompt fingerprints. That is a regression test; changing those prompts means updating it deliberately and saying so in the PR.

### What the code does today (read, with lines)

**How documents reach the AI**
- The cap is `max_total_document_words = 20000` (`app/config.py:21`). `max_document_words = 200000` (`app/config.py:20`) is the per-file extraction bound.
- Desk review is a batch run over every in-scope document. Each control batch resends the kept corpus (`app/services/desk_review.py:117-171`). Control batches: ISO 6, NIST 7, others 1 each (computed with `control_batches`; 412 controls across six frameworks).
- Gap analysis runs one extraction call per framework over the kept corpus (`app/services/claude_analyzer.py:256-312`, `:379-386`). Its quote check joins all documents into one string (`claude_analyzer.py:209`), so it proves a quote exists somewhere, not in which file.
- The judge already works on quotes, not documents, when extraction found any (`app/frameworks/prompts.py:583-621`). Raw documents reach it only as a fallback (`prompts.py:595`, `:597`, `:621`).

**Two stages cut different documents (a live bug)**
- Desk review and gap analysis cut **different** document sets.
  - Desk review keeps documents in upload order with no sort (`desk_review.py:692-709`). That order comes from `active_versions_in_scope`, ordered by `Evidence.created_at` (`app/services/evidence.py:848-855`).
  - Gap analysis sorts by a legacy DPDPA category list (`claude_analyzer.py:426-445`) that matches the old enum (`app/schemas/assessment.py:27-36`). ISO, NIST and other framework document types come from `evidence_requests` (`app/services/document_categories.py`), rank 99, and sort **after** "other".
  - The "Not read" and "Partly read" notices reflect only desk review's cut (`app/services/requirement_card.py:331-332`, `app/templates/partials/desk_review_findings.html:22-23`). The judge that writes the card may have read a different set.

**Where evidence enters and what consumes desk review**
- Text extraction, including vision OCR, already happens synchronously at upload: `ingest_upload` (`evidence.py:666-716`), `ingest_engagement_upload` (`evidence.py:719-775`), `ingest_new_version` (`evidence.py:778-818`). Callers: `app/routers/web.py:2326`, `:2436`; `app/routers/documents.py:44`; `app/routers/evidence.py:35`; `app/services/magic_links.py:544`. Evidence also enters an assessment by reuse (an `EvidenceUse` row, `evidence.py:615`).
- **Engagement uploads have no assessment** (`ingest_engagement_upload` passes `assessment_id=None`, `evidence.py:731-742`). The frameworks to read against are known only once the file is in scope for an assessment: direct upload, magic-link linking (evidence fix A), or reuse.
- Pre-fill reads `coverage_summary` plus evidence, absence and signal findings from desk review (`app/services/auto_answer.py:67-100`). It refreshes only answers whose source is "document".
- Conclusions already have a human lock: `LOCKING_ACTIONS = ("approved", "edited")` (`app/services/analysis_pipeline.py:63`, lock read at `:271-278`). A new run does not overwrite a locked conclusion.
- No vector store, embeddings or similarity search exist anywhere in `app/` or the requirements. Extracted text is one `Text` column per version (`app/models/evidence.py:52`). Desk review's per-file summary lives in one JSON blob per assessment, matched to files by filename only (`tasks/2026-10-09-parked-coverage-links.md`).
- Schema changes go through Alembic (`alembic/`, `alembic.ini`).

**The Veldhara pack, measured locally**
- 47 text files hold 21,986 words and 144,249 characters (6.6 characters per word).
- Spreadsheets are 17 files and 12,899 words (59%). One sheet alone is 6,922 words. The median file is 220 words.
- One PDF extracts 0 words without OCR. 11 PNGs need vision OCR.

### Why the alternatives lose

| Option | Verdict | Why |
|---|---|---|
| Batch desk review, cap raised | Loses | It assumes all evidence is present at once, which never happens. Every new file means re-reading everything. 17 desk-review units each resend the corpus (164k tokens for 100 files). One extraction call per framework must quote 100+ controls across every file, which pushes toward the 600 s deadline (`app/config.py:55`). It is still a cap, set by a context window not recorded in the repo. |
| Batch, but chunked (map then reduce at the end) | Loses on time | It fixes the cap, but all reading happens at the end: about 22 to 33 minutes for 100 files and six frameworks. Reading the same chunks on arrival costs the same and nobody waits. |
| Vector store and retrieval for the judge | Not now | Tagging at read time already says which passages support which control, so the judge needs a database lookup, not a search. A passage similarity search never picks is invisible, which is the silent-drop problem again. It needs an embedding model `llm_client.py` lacks, an index kept in step with file versions, and a re-check for the planned Bedrock move. Later uses that the auditor can see: consultant evidence search, or a second look for controls with no tagged passage. |
| Reopen parked v2 | No | v2 was parked for its judge (about 76% insufficient evidence). Its reading plans chunks times requirement batches (`app/services/grounding/pipeline.py:745-747`), over 2,600 calls for 100 files across six frameworks, against a 600-call limit (`app/config.py:73`). Reuse two deterministic modules only: `grounding/chunking.py` (offset-true parts for big files) and `grounding/metadata.py` (regex version, owner, approver, dates). Importing them does not flip `ANALYSIS_PIPELINE_VERSION`. |
| Prompt caching | Optimisation only | Unverified on OpenRouter for DeepSeek. It lowers cost, not time or risk. `llm_client.py:215` already records `cached_tokens`; check it in the live run. |

### The design

**1. Evidence read: one call per file, on arrival.**
- **Trigger.** A file version becomes in scope for an assessment through direct upload, magic-link linking, reuse, or a new version. Text extraction stays synchronous, as today. The read is queued, never run inside the upload request.
- **Unit.** One call per file, against the controls of every framework on that assessment. Files over 3,000 words are split with `grounding/chunking.py`, one call per part. Spreadsheet parts repeat the header row as context that is never citable.
- **Output, saved against the file version:**
  - type, period covered, owner, and a two-sentence summary;
  - document-control fields from `grounding/metadata.py`;
  - in-document issues, for example a draft, an expired review date, or an unsigned policy;
  - key passages, each a verbatim quote tagged with control ids and a strength (supports, partly supports, mentions).
- **Verification.** Each quote is located in its own file with `citations.locate_excerpt` (`app/services/citations.py:89-112`) and stored as a `chars:start-end` span. Quotes that do not resolve are dropped and counted.
- **Storage.** One new table (Alembic). Each row holds the evidence version, the framework, the part, the prompt fingerprint, the model, the status, the result JSON, the error and timestamps. One call can write rows for several frameworks. Adding a framework later reads only for that framework. Reused evidence with the same framework and prompt reuses the saved read.
- **Queue.** Row status is queued, running, read, failed or no text. A worker drains the queue with bounded concurrency. Rows left queued or running are re-queued at startup, because today's background tasks die with the process (`app/routers/web.py:3905`).

**2. What desk review becomes: a live view, not a run.** The batch outputs map like this:

| Today (batch) | Becomes |
|---|---|
| Document catalog (type, summary, coverage areas) | The per-file read. Coverage areas become "controls this file was quoted for", which is grounded. |
| Evidence map (quotes per control) | Saved, verified passages per control, across all read files |
| Coverage level per control (drives pre-fill) | Deterministic rule over the files' passage strengths, naming the file it rests on. Needs Saqlain's OK (Q1). |
| Absence findings | "Requested, not received" from the RFI status, plus "received, no passage found in N read files" (deterministic). No AI absence claim while collection is open. |
| Red flags | In-document issues from the read. Contradictions between files on the same control are left to the judge. |

**3. Update conclusions, per control, only when stale.**
- A control becomes stale when a read adds or removes passages for it, or when a consultant or RFI link changes.
- "Update conclusions" re-judges only the stale controls, using the existing control batches and the judge prompt unchanged. The judge gets the saved passages per control.
- Passages per control are capped deterministically: linked evidence first, then one passage per file in turn, then upload order. Passages not sent are listed on the card ("12 more passages in 7 files were not sent to the judge"), each one link away.
- Locked conclusions are never overwritten (existing rule). They show "new evidence since you approved", naming the file.
- Synthesis and the report run at report time, from current conclusions.

**4. Nothing is ever silent.**
- Every in-scope file version has read rows. A file with no text gets an explicit "no text extracted" row; `chunk_source` returns nothing for empty text (`grounding/chunking.py:81-82`), so the planner adds that row itself.
- A failed read shows on the evidence row, on the desk-review view, and on every card where the file is linked, with a "Re-read" action.
- "Update conclusions" lists any file still queued or failed before it runs.

### Cost and time (all estimates; replace with live numbers)

**Assumptions**
- 1.6 tokens per word (from 6.6 characters per word in the Veldhara text, at about 4 characters per token).
- $0.14 per million input and $0.28 per million output for `deepseek/deepseek-v4-flash`. This is the price passed to `scripts/validation/ab_compare.py` in the 2026-09-30 A/B run (back-solved from `~/cyberassess-runs/2026-09-30-p6-5-ab-abstain/ab_comparison.json`). Not re-checked against OpenRouter.
- The control list costs 30 tokens per control in every read call. Read output: 1.5k tokens (one framework) or 2.5k (six).
- Judge: 12k in and 3k out per batch unit. Synthesis: 6k in and 2k out per call.
- 35 s per read call and 45 s per judge call.
- Vision OCR is excluded: it happens at upload and nothing here changes it.

**Results**

| Case | Reads | Read cost | Update conclusions | Update cost | Total |
|---|---|---|---|---|---|
| Veldhara: 58 files, 22.5k words, ISO 93 controls | 61 calls (big sheets split) | $0.06 | 8 calls | $0.02 | **about $0.08** |
| 100 files, 100k words, six frameworks, 412 controls | about 130 calls | $0.36 | 24 calls | $0.05 | **about $0.41** |

- **Per file:** one call, about 30 to 40 s, whatever the size of the rest of the pack.
- **Update conclusions:** about 1.5 minutes for ISO alone; about 3 minutes for all six frameworks at concurrency 6, or 4.5 minutes at today's 4.
- **Bulk drop:** 100 files uploaded at once take about 13 minutes in the background at concurrency 6 (19 at 4). Each file's result appears as it finishes.
- **Today, for comparison:** about $0.06 for Veldhara, reading 20,000 of 22,500 words; about $0.20 for the 100-file case, reading 20,000 of 100,000 words.
- **Biggest cost driver:** the control list repeated in every read (12k tokens for six frameworks). Collapsing shared controls through the 52 UCC clusters, or prompt caching, would cut it. Do that only if the measured cost matters.

### What breaks or changes

1. The batch desk-review run, its routes (`app/routers/desk_review.py:35`, `app/routers/web.py:3838-3905`) and `DeskReviewSummary`'s role change. The page becomes a live view. Existing assessments need a backfill: queue reads for every in-scope file version, including legacy `AssessmentDocument` rows (`evidence.py:903-914`).
2. Pre-fill (`auto_answer.py`) switches from desk-review coverage to the per-control rule. Its "only refresh document-sourced answers" rule stays.
3. `_truncate_documents` (both copies), `max_total_document_words`, the extraction step inside gap analysis, and the judge's raw-document fallback all retire. The budget notices become read states.
4. `analysis_runs` and conclusion revisions currently assume whole-framework runs. Partial, stale-only runs must still record the run id and citations per conclusion (`analysis_pipeline.py`). This needs Codex verification.
5. The curated DPDPA single-framework path keeps byte-identical golden recordings (`app/config.py:60-64`, comment). Either move it last with re-recorded goldens, or leave it on the old path.
6. The desk-review prompt fingerprint test changes when the old prompt is removed. The judge fingerprints must not change.
7. Report generation reads conclusions and desk-review data. Every report consumer of `DeskReviewSummary` must read the new source.
8. SQLite writes from a background worker run concurrently with web requests. The worker must keep transactions short and never hold a lock during an LLM call.

### Failure modes and guards

| Failure | Guard |
|---|---|
| The read over-tags (many weak passages per control), and judge false positives rise (v1 decoy FP is already 58%) | Strength field, per-control passage cap with visible overflow, A/B gate before the default flips |
| A read fails twice | Failed status on every surface, "Re-read" action, listed before any update |
| No text (scanned PDF without OCR) | Explicit "no text extracted" row |
| A quote crosses a part boundary | Split at headings and lines; rejected quotes counted per file |
| A part lacks its document's context | The part header names the file, the part number and the nearest heading; quotes resolve by evidence id, not filename |
| A contradiction between files | Meets at the judge when both are tagged to the same control. Table-wide facts (cycles, removals) belong to the E5 deterministic checks |
| The process restarts mid-queue | Queued and running rows are re-queued at startup |
| A framework is added after reads | Reads only for the missing framework |
| Two files with the same name | Everything keyed by evidence version id, never filename |
| Approved conclusions shift under the consultant | Existing lock, plus a "new evidence since you approved" flag |

### Staged PR plan

Each PR names its loop step for the coherence test (path rule 1). One in flight at a time.

0. **Measure (no PR).** Ride on the live Veldhara run already queued (`tasks/handoffs/2026-10-09-demo-depth-review-and-live-test-kickoff.md`). Record tokens per word, seconds per call by stage, `cached_tokens`, and the model's context window from the OpenRouter catalog.
1. **One cut, told truthfully** (read step; no LLM or prompt change; small).
   - What: one selection function for desk review and gap analysis, and a document-level read status written by both. The card names files the **judge** did not read.
   - Test: cap patched to 50 words with three documents; both stages pick the same set; all three surfaces render it.
   - Click-through: Veldhara pack, the same unread files on the desk-review page, the evidence list and a linked card.
   - This fixes today's wrong notice even if nothing else ships.
2. **Read on arrival** (read step; new read prompt; behind a setting, default off).
   - What: the table, the queue, the trigger on every in-scope path, the per-file read, part splitting, quote location. The evidence page shows status, summary and tagged passages.
   - Tests: every in-scope version gets rows; parts cover every word exactly once; headers are never cited; quotes resolve to their own file; a forced failure marks only that file; restart re-queues; reuse with the same framework reads nothing new; a magic-link upload is read only after it is linked to an assessment.
   - Click-through: upload one file and see its read appear within a minute; then drop the Veldhara pack and watch files fill in.
3. **Live desk-review view and pre-fill from reads** (read and pre-fill steps).
   - What: the per-control passage view, the deterministic coverage rule, "requested, not received", in-document flags, and stale marking.
   - Tests: pre-fill output shape unchanged; human answers untouched; a new read marks only its controls stale.
   - Click-through: upload an access review and see the matching questions pre-fill, naming the file.
4. **Update conclusions from saved reads** (judge step; judge prompt byte-identical).
   - What: stale-only runs over saved passages, the passage cap with visible overflow, and lock flags.
   - Tests: judge fingerprints unchanged; only stale controls are sent; locked conclusions keep their outcome and gain the flag; run ids and citations are recorded per conclusion.
   - Click-through: approve one conclusion, upload new evidence for it, update, and see the flag instead of a change.
5. **Gate, then flip** (judge step).
   - What: A/B against today's v1 on the validation companies with `scripts/validation/ab_compare.py`, aggregate numbers only. Those packs fit under 20k words, so differences come from the reading method alone.
   - Gate: catch not lower, decoy and clean false positives not higher, stability not lower, cost reported.
   - Then one timed run on a 100-file synthetic pack with no answer key. If it passes, default on, remove the batch desk review and the cap. If not, the setting stays off and the result is recorded.
6. **Optional, only if measured need.** UCC-collapsed control lists, prompt caching, concurrency tuning, consultant evidence search.

Held-out rule: the part size, passage cap, ordering and strength levels come from token and latency arithmetic, fixed before any evaluation. Nobody reads `answer_key.json`. Veldhara is only a size and format test.

### Questions for Saqlain

1. **Pre-fill coverage rule.** Today the AI sets "adequate" or "partial" per control from all documents at once. Proposed: a deterministic rule over saved passages ("adequate" if any file strongly supports the control, "partial" if only partial support), naming the file. OK, or keep an AI call per control for this?
2. **Updating conclusions.** Should conclusions re-judge only when you click "Update conclusions", or automatically after new evidence settles? Recommendation: manual, so conclusions never shift while you are reviewing them.
3. **Sequence and decision B.** Step 1 right after the E4 build (it fixes a wrong notice); steps 2 to 5 before flow-plan S3, which overlaps S4 (RFI as a stage). And the read's control tags are the input for parked decision B (suggested links). Show them as confirm-first suggestions after step 3, or keep B parked?

## Status after Codex review (2026-10-11)

**Codex verdict: NO-GO as written.** Full review: `tasks/handoffs/2026-10-11-document-reads-codex-review.md` (29 findings: 4 blockers, 21 major, 4 minor). The read-on-arrival direction holds. Nothing is built. Do not start implementation from the Results section above as written.

Claude spot-checked three blockers in the code and confirmed them:
- F1: saving a run deletes and rebuilds the whole gap report, its items and initiatives (`app/routers/analysis.py`, report save paths). A stale-only run would wipe untouched controls.
- F4: the release manifest holds only frameworks, scope and conclusion versions (`app/services/approved_report.py:369-384`). New evidence on a locked conclusion changes none of them.
- F11: judge quotes are resolved against every source in the run (`app/services/analysis_pipeline.py:377`), so a quote can cite a file that was never sent for that control.
F2 (judge inputs beyond passages: answers, notes, follow-ups, context, scope) matches the prompt builder read for this design (`app/frameworks/prompts.py:455-621`).

### Recommended narrower first version (proposed, not yet approved)

All four blockers come from re-judging only changed controls. Drop that from the first version.

1. **Truthful cut.** One selection for desk review and gap analysis. Record what each stage actually received (extraction set and judge passages per run), not a global filename list (F19, F26).
2. **Read on arrival, stored and shown.** One call per in-scope file version. Covers read storage, one idempotent scope reconciliation for every entry and exit path, the queue and worker, quote location inside the part, and per-file display. Also: retention purge, legacy identity, offline seeds. Behind a setting, default off (F5 to F13, F23, F27).
3. **Desk review and gap analysis consume saved passages.** Same output shapes and contracts as today, so pre-fill, questionnaire, follow-ups, workpaper, reports and release are untouched. Every run judges all controls through the existing report save path. No raw-document fallback. Judge citations resolve only within the passages sent for that control (F11, F20, F21).
4. **Gate, then flip.** Make the A/B runner queue-aware with reader identity first, then the existing aggregate gate (F22, F28, F29).

Expected end-of-assessment run: desk review plus judge on saved passages, about 34 calls for six frameworks. Estimated a few minutes, not 20 to 30. Not measured.

**Deferred, each a separate later decision:**
- the live desk-review view (F14);
- stale-only partial updates (F1 to F3);
- pre-fill from per-file rules and its retraction (F15, F16);
- typed per-file issues (F17);
- RFI-status absence (F18; depends on flow-plan S4);
- release provenance for new evidence on locked conclusions (F4). The first version only shows a flag.

### Open questions for Saqlain

1. **Approve the narrower first version above?** If yes, Claude rewrites the Results section to match and sends it to Codex for a second review before any build.
2. **Curated DPDPA single-framework path.** Leave it on the old method with its golden recordings, and keep the cap machinery for it? Recommended: yes (F21).
3. **Sequence slot.** The fixed sequence (`tasks/2026-10-08-session-record.md`, path rule 5) must be edited on purpose to fit this in. Proposed: step 1 right after the E4 build, steps 2 to 4 before flow-plan S3.
4. **Updating conclusions.** Manual ("Update conclusions") or automatic? Recommended: manual.
5. **Read tags as suggested links (parked decision B).** Show them as confirm-first suggestions after step 3, or keep B parked? D8 requires that tags never silently become consultant-confirmed mappings.

**Questions that only matter for the deferred parts** (from Codex's open questions):
- What counts as complete control coverage for pre-fill (Codex Q1, F16)?
- How does a consultant acknowledge new evidence on a locked conclusion, and does it block release (Q2)?
- What marks evidence collection open or closed, and how do direct uploads and reuse satisfy RFI items (Q3)?
- Does the assessment period or evidence cut-off change passage selection, or only the report basis (Q5)?

**Not verified, needs the live run:**
- current provider price;
- the model's context window;
- prompt cache effectiveness;
- new-reader latency.
