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

Revision 4, 2026-10-12 (revision 3 plus the changes required by Codex review 2, listed under "Revision 4 changes"; where they differ, revision 4 wins). Revision 3: Replaces revision 1 (2026-10-10, chunked batch) and revision 2 (2026-10-11, read on arrival with stale-only re-judging). Revision 2 was reviewed by Codex: **NO-GO as written**, 29 findings (`tasks/handoffs/2026-10-11-document-reads-codex-review.md`). This revision answers those findings within the narrower scope Saqlain approved. Status: **design for Codex's second review. Nothing is built.**

### Recommendation

Read each in-scope file once, as it arrives, with small calls whose results are saved per file version and shown on the evidence record. Desk review and gap analysis keep their outputs, contracts and report persistence exactly as today; they only stop reading whole documents and work from the saved passages instead, and every run still judges every control. Before that, shared code that is meant to serve every framework stops assuming DPDPA. DPDPA assessments keep every feature they use today.

### Decisions (Saqlain)

| Date | Decision |
|---|---|
| 2026-10-11 | Evidence arrives over days, so reading follows arrival, not "all documents in". |
| 2026-10-11 | One analysis per uploaded file, saved and reused by the judge and the report. |
| 2026-10-11 | A 20 to 30 minute end-of-assessment run is too long. |
| 2026-10-11 | No vector store for now. |
| 2026-10-12 | **Narrower first version approved.** No stale-only re-judging, no live desk-review view, no pre-fill rule changes, no release-policy changes in this work. |
| 2026-10-12 | **Strip DPDPA assumptions from framework-agnostic code; keep everything DPDPA assessments use.** "I don't want you to delete code that is being used by DPDPA assessment. I only want you to delete things or remove things that are supposed to be framework agnostic, but are using DPDPA-specific plumbing." (Corrects Claude's first reading, which would have deleted the curated DPDPA path and screening.) |
| 2026-10-12 | Finish this plan first, then return to the original action list. |
| 2026-10-12 | **Initiative grouping:** one framework-neutral root-cause map shared by ISO, NIST, GDPR, HIPAA and PCI gaps. DPDPA keeps its own clusters for DPDPA gaps. (Was Q1.) Codex review 2 (N2) found the shared path already does this (`app/services/scoring.py:731-736`); Claude's question was based on a misreading. The real leak is the shared initiative advice text, fixed in stage 2c. |
| 2026-10-12 | **DPDPA goldens:** re-record them deliberately in the stage 6 flip PR, after the gate passes, with the old recordings kept in git history. (Was Q2.) |

Freeze scope (checked 2026-10-11): the written freeze covers the judge prompt wording only (P6-5c; E6; CLAUDE.md). The desk-review prompt is not frozen. `tests/test_p6_1b_framework_batching.py:152` pins desk-review fingerprints and must be updated deliberately where the desk-review input changes.

### What changed from revision 2, by Codex finding

| Finding | How revision 3 handles it |
|---|---|
| F1, F2, F3 (stale-only runs) | Removed from scope. Every run judges every control, through the existing report save path. A run snapshots the read set it used. |
| F4 (release cannot see new evidence on locked conclusions) | Already true today. This work shows a card flag when a locked conclusion's run used an older read set than the current one. Release policy is unchanged and deferred. |
| F5, F6 (missed entry and exit paths) | One idempotent scope reconciliation, run after commit on every path in Codex's path table, at startup and by a backfill command (stage 3). |
| F7 (legacy rows) | Legacy `AssessmentDocument` rows must be migrated to evidence first; rows that cannot be migrated are listed as "not migrated, not read", never skipped quietly. |
| F8 (extraction failures) | Extraction status is stored separately from read status. Marker-only OCR output is "OCR failed", not "read". |
| F9 (reuse identity) | One call per part per framework, so every read row has a single-framework identity with a full fingerprint. No reuse of combined-call slices. |
| F10, F11 (citations) | Quotes are located inside the part's own text and offset to the file. The judge's quotes resolve only against the passages sent for that control. |
| F12, F13 (queue, retention) | One lifespan-managed dispatcher, atomic claims, bounded attempts, publish only if still in scope. Purge covers reads before versions. |
| F14 to F18 (live view, pre-fill, issues, RFI) | Out of scope. Desk review keeps its stored fields and finding rows, so every consumer is unchanged. |
| F19, F26 (truthful cut) | Stage 1 records what each stage actually received, per run, and fixes the two inaccurate claims. |
| F20 (empty evidence, small frameworks) | In saved-passage mode every registry framework uses the existing batched builder; small frameworks are one batch. The existing "no extracted quotes" line covers empty batches. No raw documents. |
| F21 (curated DPDPA path) | Kept, because DPDPA assessments use it. In stage 5 it takes saved passages through the same adapter, into the quote input it already accepts. Its goldens stay as the setting-off characterization, and a new setting-on fixture is added. They are re-recorded deliberately in the stage 6 flip PR, after the gate (decided 2026-10-12). |
| F22 (A/B runner) | Queue settlement, reader identity and isolated caches are prerequisites for the stage 5 gate. |
| F23 (seeds) | Offline seeds and loaders disable the dispatcher or write deterministic read fixtures. |
| F24 (reports) | Untouched. Reports and narrative read conclusions and approved findings as today. |
| F25 (PR sizes) | Six stages, each behind one setting until its gate. |
| F27, F28, F29 (chunker, budgets, timings) | Reader settings independent of v2 settings, strict part bound, budgets pinned below, timings labelled as assumptions. |

### Current code facts this revision relies on

Revision 2's facts stand except where Codex corrected them (F26):
- Registry frameworks always extract; curated DPDPA can reuse desk-review evidence instead (`app/services/claude_analyzer.py:324`, `:369`).
- Only unknown category strings rank after "other"; framework document types that share a legacy category keep its priority (`claude_analyzer.py:426`, `app/services/document_categories.py:31`).

DPDPA code found on 2026-10-12 (read, with lines), sorted by Saqlain's rule.

**Kept: used by DPDPA assessments.** None of this is touched by stage 2.
- The curated single-framework analysis path for `["dpdpa"]` assessments (`app/routers/analysis.py:263-299`, `_persist_single_analysis` at `:357`, `run_gap_analysis` at `claude_analyzer.py:43`, `:78`, `_run_evidence_extraction` at `claude_analyzer.py:222-253`).
- The curated DPDPA desk-review and extraction prompts (`CURATED_PROMPT_FRAMEWORK_ID`, `app/frameworks/prompts.py:19`, `:192-193`; `app/services/desk_review.py:131`, `:369`; `claude_analyzer.py:263-268`, `:360-369`).
- The DPDPA-only questionnaire, its pre-fill and screening (`app/services/question_engine.py:85-87`, `:403`; `app/services/auto_answer.py:63-64`; `app/services/screening.py:46-50`).
- The DPDPA goldens (`tests/test_golden_dpdpa.py`, `tests/support/analyzer_mock.py`) and DPDPA content (`app/frameworks/definitions/dpdpa.py:8-14`, conditional copy such as the board readiness note).

**Candidates: shared code that assumes DPDPA.** Stage 2 makes these framework-agnostic. Codex is to confirm each one, and to find any others.
- **Gap-analysis truncator.** The shared multi-framework path ranks every framework's documents by the legacy DPDPA category list (`claude_analyzer.py:426-445`, called at `:521`). Stage 1 replaces it with one framework-neutral selection.
- **Upload categories.** The legacy DPDPA document categories (`app/schemas/assessment.py:27-36`) are offered for every framework's uploads (`app/services/document_categories.py:31-33`).
- **"No framework means DPDPA" defaults**, in about 15 places:
  - `Assessment.frameworks` returns `["dpdpa"]` when the field is unset or invalid (`app/models/assessment.py:57-62`);
  - `app/frameworks/compat.py:13`;
  - `app/routers/questionnaire.py:321-327`;
  - `app/routers/analysis.py:141`, `:256`;
  - `app/routers/assessments.py:144`;
  - `app/utils/pdf_export.py:951`;
  - findings, gap items and remediation rows with a null `framework_id` read as DPDPA (`app/services/desk_review_findings.py:9`, `:30`; `app/frameworks/prompts.py:541`; `app/routers/web.py:3126`, `:3274`; `app/utils/pdf_export.py:651`, `:726`; `app/templates/partials/report_summary.html:23`; `app/models/desk_review.py:45`).
  - A data backfill for gap items already exists (`app/legacy_migrations.py:230-245`).
- **Initiative grouping.** `scoring.generate_initiatives` groups every framework's gaps by DPDPA root-cause clusters, with a DPDPA requirement-prefix fallback (`app/services/scoring.py:12`, `:465-497`, `:527`). ISO or NIST gaps fall into DPDPA groupings or into none.
- **Context interview.** The risk-context blocks for every assessment come from `app/dpdpa/context_questions.py` (`app/routers/web.py:19`, `:2471-2496`; `app/routers/questionnaire.py:7`, `:39`). Codex is to check whether the wording is DPDPA-specific.
- **Scope profiler.** It imports DPDPA requirements (`app/services/scope_profiler.py:14`) but is called for every assessment (`app/routers/web.py:2013`, `:2194`, `:2250`, `:2282`; `app/services/rfi_requests.py:26`). CLAUDE.md says non-DPDPA scope profiling is not implemented. Codex is to check whether shared code depends on the DPDPA import.

**Validation baseline.** Validation company c1 is DPDPA-only; c2 and c3 include DPDPA (`validation/companies/*/company.json`, frameworks field only). Fixing shared defaults should not change c1. The initiative and truncator changes can change c2 to c4.

### The plan, in stages

Each stage names its loop step for the coherence test (path rule 1). One in flight at a time. Stages 3 to 5 share one setting, `evidence_reads_mode` (`off` or `on`), default `off` until the stage 6 gate passes.

**Stage 1. Truthful cut** (read step; no LLM or prompt change; small)
- What: one selection function used by desk review and gap analysis. Each run records a manifest per stage: the documents extraction received, and the passages the judge received per control, by evidence version id. The card's "not read" notice reads that manifest, not desk review's filename list. Fix the two over-broad claims (F26) in tests.
- Tests: with the cap patched to 50 words, both stages pick the same set, and the manifests match what the prompts contained. Duplicate filenames are told apart. Reused desk-review quotes outside the cut are labelled as such.
- Click-through: Veldhara pack (over 20k words). The same unread files appear on the desk-review page, the evidence list and a linked card.
- Survives later stages: the manifest is how stages 4 and 5 prove what the judge saw.

**Stage 2. Shared code stops assuming DPDPA** (all loop steps; no prompt change; DPDPA features untouched)
- What, for each confirmed candidate above:
  - Framework fallbacks raise or use the assessment's real framework list instead of `["dpdpa"]`. Assessments with no stored frameworks are migrated once (Alembic). Every live row already has a list; Codex is to confirm.
  - Null `framework_id` on findings, gap items and remediation rows is backfilled (extending `app/legacy_migrations.py:230-245` to every affected table). The read-time "null means DPDPA" fallbacks are then removed.
  - Upload categories offered for an assessment come from its own frameworks plus "other". The legacy DPDPA categories are offered only when DPDPA is in scope.
  - Initiative grouping uses one framework-neutral root-cause map for every non-DPDPA framework (decided 2026-10-12). DPDPA keeps its clusters for DPDPA gaps.
  - The context interview and the scope profiler: fixed only if Codex confirms a DPDPA dependency in shared code. Otherwise they are left alone and recorded as checked.
- Kept: everything in the "Kept" list above, unchanged.
- Gate: run the full suite, including the DPDPA goldens, which must pass byte for byte. Then an A/B on all validation companies with `scripts/validation/ab_compare.py`, before versus after, aggregate numbers only (catch not lower, decoy and clean false positives not higher, stability not lower, cost reported). The gate stands alone, so stage 6 is measured against this baseline.
- Click-through: one DPDPA-only assessment works exactly as before, screening included. An ISO-only assessment shows ISO upload categories only, and its initiatives are not DPDPA-named.

**Stage 3. Read storage and scope reconciliation** (read step; no LLM; behind the setting)
- Read identity: one row per (evidence version, framework, part). The fingerprint covers source text hash, framework pack version, read schema version, prompt fingerprint, model id and part settings. A row is reused only when every field matches.
- Reconciliation: `reconcile_reads(assessment)` computes the wanted rows from the active scope (`active_versions_in_scope` plus the assessment's frameworks). It queues missing rows and marks rows that left scope inactive, keeping them for provenance. It is called after commit on every path in Codex's path table, at startup, and by a backfill command. Engagement-only receipts get nothing until they are in scope.
- Extraction status on the version: ok, OCR failed, pages omitted, rows truncated. Shown separately from read status.
- Legacy rows: migrate first; anything not migratable is listed as "not migrated, not read".
- Retention: purge removes reads before versions; archiving pauses that scope.
- Seeds: offline loaders run with the setting off or write deterministic fixtures.
- Tests: upload, map, unmap, replace, archive, restore, framework add and remove, each with a fake provider. Every committed in-scope version is accounted for exactly once. A rolled-back upload leaves no row. Purge racing a queued row.
- Click-through: with the setting on, upload a file; the evidence row shows "Queued for reading" per framework.

**Stage 4. Reader and per-file display** (read step; one new reader prompt; behind the setting)
- Dispatcher: one per process, started by the app lifespan. A claim is an atomic update with a token. At most 2 attempts. A short session to claim, none held during the provider call, a short session to publish. Publish only if the token still holds and the version is still in scope. At startup, running rows go back to queued (single-process assumption, as `app/services/run_recovery.py:24` warns). A separate `reads_max_concurrency` setting is counted against the shared provider budget.
- Parts: `grounding/chunking.chunk_source` called directly with reader settings: at most 3,000 words, strict tail bound, the preceding heading carried as non-citable context. Spreadsheet parts repeat the header row as non-citable context.
- Calls per part:
  - (a) one framework-free reader call: type, period, owner, two-sentence summary, merged deterministically per file. Regex fields from `grounding/metadata.py`, with missing values shown as unknown.
  - (b) one extraction call per framework using `build_framework_evidence_extraction_prompt` unchanged, with only that part.
- Quotes: located inside the part's raw text, offset to the file, at most 2,000 characters. The first occurrence within the part wins. Quotes inside context-only text are rejected. Rejections are counted per file.
- Display: the evidence record shows read status per framework (queued, reading, read, read with nothing relevant, failed with "Re-read", not readable), the summary, and the passages per control.
- Hostile input: add a prompt-injection test pack for the new reader seam (F17 note).
- Tests: parts cover every word once; context is never cited; a forced failure marks one row; a restart after a claim re-queues it; a rolled-back upload never runs a read.
- Click-through: upload one file and its read appears; then drop the Veldhara pack and watch the files fill in.

**Stage 5. Desk review and gap analysis on saved passages** (pre-fill and judge steps; desk-review prompt input changes; judge wording unchanged; behind the setting)
- Desk review:
  - It runs only when the consultant starts it, as today. It first lists any reads still queued or failed.
  - Its evidence map and catalog are built deterministically from the saved reads, with no LLM.
  - Per existing control batch, one call receives the batch's saved passages plus a one-line catalog of every file, and returns coverage, absence and red flags in today's JSON shape.
  - `DeskReviewSummary` and `DeskReviewFinding` keep their fields, so the questionnaire, pre-fill, follow-ups, workpaper, evidence viewer and stage labels are unchanged. New-mode findings carry versioned citations; `document_id` stays empty for them.
  - The desk-review fingerprint test is updated deliberately.
- Gap analysis:
  - The extraction step is replaced by saved passages per control. Order: consultant-linked evidence first, then one passage per file in turn, then upload order. At most 10 passages and 2,500 tokens per control.
  - Passages left out are recorded in the run manifest and listed on the card.
  - Every registry framework goes through the batched builder; small frameworks form one batch. The curated DPDPA path keeps its own builder (see below). No raw documents.
  - Judge citations resolve only within the passages sent for that control.
  - Judge fingerprints for equal inputs are unchanged.
- DPDPA: the curated desk-review prompt, the curated judge path for `["dpdpa"]` assessments and DPDPA inside multi-framework runs keep their prompts. Their document input is replaced by the same saved-passage adapter: passages for desk review, and the quote evidence the curated judge already accepts (`claude_analyzer.py:78-120`) for the judge. With the setting off, the DPDPA goldens still pass byte for byte. A new setting-on DPDPA fixture is added.
- Locked conclusions: never overwritten (existing rule). The card shows "evidence changed since you approved" when the current read set differs from the one recorded on the approving run.
- Click-through: run desk review and analysis on Veldhara with the setting on. Pre-fill, cards and report work as before. Every card's sources link to passages that were actually sent.

**Stage 6. Gate, flip, remove the cap** (judge step)
- Runner: the A/B runner waits for reads to settle, records the reader mode and fingerprints, isolates caches per arm, and captures read calls, retries, cost and elapsed time.
- Gate: setting off versus on, on all validation companies, aggregate only, the same four conditions. Then one timed run on a 100-file synthetic pack with no answer key, plus multi-arrival, restart and failure smoke checks.
- Then: if the gate passes, the default goes on, and `_truncate_documents`, `max_total_document_words`, the in-analysis extraction call and the raw-document fallback are deleted. If it fails, the setting stays off and the result is recorded.

**Deferred, each its own later decision**
- live desk-review view;
- stale-only re-judging;
- pre-fill strength and retraction rules;
- typed per-file issues;
- RFI-status absence (after flow-plan S4);
- release provenance for new evidence on locked conclusions;
- one combined read call across frameworks (only if bulk-drop time is a problem);
- read tags as suggested links (parked decision B stays parked).

### Budgets (fixed before any evaluation)

| Item | Budget |
|---|---|
| Part size | at most 3,000 words, strict |
| Reader call | part text plus 1k instructions; 500 output tokens |
| Extraction call | part text plus 30 tokens per control plus 1.5k instructions; output at most 1k tokens |
| Passages sent per control | at most 10, at most 2,500 tokens, consultant-linked first |
| Desk-review call (stage 5) | about 12k input, 3k output per batch |
| Judge call | about 12k input, 3k output per batch (as today) |

### Cost and time (estimates; replace with measurements)

**Assumptions**
- 1.6 tokens per word (rough: 6.6 characters per word at about 4 per token is 1.65).
- $0.14 per million input and $0.28 per million output, the prices of the 2026-09-30 A/B run; Codex reproduced that arithmetic. Not re-checked today.
- Part counts are assumed from the file mix: 61 parts for Veldhara (two large sheets split) and 130 for the 100-file case.
- Service times are assumptions, not measurements: 15 s per read call, 45 s per desk-review or judge call. Vision OCR at upload is excluded.

**Results**

| Case | Read calls | Read cost | End-of-assessment calls | End-of-assessment cost | Total |
|---|---|---|---|---|---|
| Veldhara: 58 files, 22.5k words, ISO | 122 (61 reader + 61 extraction) | $0.08 | 12 (6 desk review + 6 judge) | $0.03 | about $0.11 |
| 100 files, 100k words, six frameworks | 910 (130 reader + 780 extraction) | $0.80 | 35 (17 desk review + 17 judge + 1 cross-framework synthesis) | $0.09 | about $0.89 |

- **One file arriving:** its calls run in parallel, so about one call's time plus queue wait.
- **End-of-assessment run:** Veldhara about 1.5 minutes at concurrency 6 (3 at 4); six frameworks about 5 minutes at 6 (8 at 4). Today's equivalent re-reads every document.
- **Bulk drop, in the background:** 58 files about 5 minutes at concurrency 6; 100 files across six frameworks about 38 minutes at 6 (57 at 4). Each file's result appears as it finishes. This is the price of single-framework read identity (F9). A combined call across frameworks would cut it about 6 times, and is deferred until measured.
- **Today, for comparison:** about $0.06 for Veldhara, reading 20,000 of 22,500 words; about $0.20 for 100 files, reading 20,000 of 100,000 words.

### Revision 4 changes (after Codex review 2: GO with changes)

Review: `tasks/handoffs/2026-10-12-document-reads-codex-review-2.md`. Claude confirmed N2 and N6 in code. Each change below is binding for the stage it names.

**Stage boundaries, re-cut**
- Stage 1: unchanged. Manifests need a legacy-source key for unmigrated `AssessmentDocument` rows until migration finishes (`app/services/evidence.py:891-913`). Add a duplicate-filename catalog and viewer case (N10).
- **Stage 2a. Explicit frameworks (N1).** A **new** Alembic revision backfills and validates `assessments.selected_frameworks`, `desk_review_findings.framework_id` and `gap_items.framework_id`. Historical revisions are never edited. Missing selections with known legacy DPDPA provenance become `["dpdpa"]`; invalid or ambiguous ones are refused with a report, never defaulted. A migration preflight counts null and invalid rows first. Make every seed and test writer explicit (`scripts/seed_test_companies.py:1286-1296`, `:1348-1357`). Convert `tests/test_legacy_dpdpa_framework_id.py` into migration characterization. Only then remove the "null or unset means DPDPA" readers: `Assessment.frameworks`, the questionnaire, analysis and assessment readers, the PDF default, the desk-finding reader and query, the signal prompt fallback, the gap and remediation readers and links, and the conclusion-review lookup (`app/services/conclusion_review.py:420-427`, missed by revision 3). `compat.py` requires an explicit framework or is marked legacy-only. The legacy creation API (`app/routers/assessments.py:47-54`) creates DPDPA explicitly. That is used by DPDPA, so it is kept, not made framework-selectable.
- **Stage 2b. Framework-aware follow-ups (N3), trimmed 2026-10-12.** Flow-plan S3 deletes the context wizard and the context-profiler LLM call, so fixing their DPDPA wording now would be rework. Stage 2b covers only the follow-up engine (`app/services/followup_engine.py:98`, `:188`): a framework-aware branch, with existing DPDPA requests preserved. The context interview and the profiler are left to S3. Narrow non-DPDPA prompt changes are allowed in the follow-up engine. The judge freeze stands.
- **Stage 2c. Categories and initiative text (N2).**
  - Upload categories: legacy DPDPA categories only when DPDPA is in scope; stored strings stay valid.
  - The shared initiative advice (`app/services/scoring.py:567-589`, used by `generate_multi_framework_initiatives`) becomes framework-neutral. DPDPA members of mixed initiatives keep their privacy actions.
  - The curated `generate_initiatives`, its DPDPA clusters, prefix fallback and naming are kept (DPDPA-only path, `app/routers/analysis.py:494`).
  - Moved in from flow-plan S8 (2026-10-12): framework-conditional section refs on conclusions and the review queue (today DPDPA refs are hard-coded).
- Stage 2 gate (N9): the aggregate A/B stays, plus per-framework regression checks in its outputs. Add offline all-six-framework checks for creation, categories, context, follow-ups and initiative copy. The DPDPA goldens pass unchanged; they pass `initiatives=[]`, so add a curated-initiative characterization test.
- Stage 3 (N4): shared read results are separate from assessment membership. A read is inactive only when no remaining scope needs it. Test two assessments sharing one version: unmap, remove a framework and archive only one of them. Claims and publication check assessment and engagement archive state, not only active evidence.
- **Stage 5a.** Saved-passage adapter plus desk-review persistence (registry and curated), default off. **Stage 5b.** Judge integration (registry and curated), default off. Resolve N5 to N7 before 5a.
- **Stage 6a.** The gate, then flip the default to on, with rollback kept. **Stage 6b.** Separately, retire the setting and the off branches, only after every endpoint and loader uses saved reads and offline seeds have read fixtures or stubs. The DPDPA goldens are re-recorded in 6b, as decided (N8).

**Contracts fixed before stage 5**
- **Readiness (N5).** Desk review and analysis run only when every required read for each framework is read, read with nothing relevant, or explicitly unreadable. If any are queued, reading or failed, that framework refuses to run, with a visible error naming the files. The other frameworks run. Failed-framework pre-fill suppression is kept. Partial execution is a later decision.
- **Empty evidence (N6).**
  - Add an explicit saved-evidence empty state that distinguishes "no relevant passages in N read files" from "no files uploaded".
  - Today `evidence={}` with `documents=[]` renders "No supporting documents uploaded" (`app/frameworks/prompts.py:599-621`, `:718-726`). And moving a small framework from `control_ids=None` to all ids changes the final instruction line (`prompts.py:623-626`).
  - So small frameworks keep the full-framework wording, and the new empty-state line is recorded as a narrow wording exception to the judge freeze, for Saqlain to approve (Q4).
  - Test empty and nonempty inputs for every framework; all unchanged request fingerprints are preserved.
  - Curated DPDPA gets an explicit saved-read branch: passing `documents=[]` to today's runner skips evidence loading (`app/services/claude_analyzer.py:89-106`).
- **Budgets (N7).**
  - Per-control limits are maxima. Every desk-review and judge request also gets a total input bound, covering controls, answers, catalog, passages and instructions, of 48k tokens. A batch that would exceed it is split.
  - The existing judge output ceiling (`llm_max_output_tokens_framework`, `app/config.py:65`) is kept until measured.
  - An extraction reply cut off at its length limit is a failed read, not empty evidence.
  - The unchanged extraction prompt embeds full control text: about 5k tokens for ISO before any document (Codex offline check). Read input estimates are revised up accordingly; the stage 6 runner measures the real figure.
- **Reader identity (Codex Q2, Q3).** The framework-free reader result is its own row: (evidence version, part, reader fingerprint), with no framework. Every published result gets an immutable generation id. A "Re-read" adds a generation and never edits one. Run manifests record generation ids, so old run inputs survive re-reads and setting changes.
- **Attempts (Codex Q4).** "At most 2 attempts" means queue attempts. Each attempt is one `llm_client` call with its own internal retry. The dispatcher counts an attempt's thread against the shared budget until the thread exits, including after a deadline. Shutdown stops claiming and waits up to one deadline.
- **Empty-text uploads (Codex Q5).** These are already refused with a visible upload error and rolled back (`app/services/evidence.py:703-715`). That is not silent, so no failed-receipt row is added.
- **Time corrections.**
  - A one-part file across six frameworks needs seven calls, so two waves at concurrency 4 or 6.
  - A combined extraction call across frameworks would cut 910 calls to 260 (3.5 times, not 6).
  - The six-framework end-of-assessment cost includes one cross-framework synthesis call at about 8k input and 2k output.

### Questions for Saqlain

Questions 1 and 2 were answered on 2026-10-12 (see Decisions).

3. **Sequence slot.** The fixed sequence (`tasks/2026-10-08-session-record.md`, path rule 5) has to be edited on purpose. Proposed: stages 1 and 2 right after the E4 build; stages 3 to 6 before flow-plan S3.

4. **Judge wording exception (N6).** In saved-passage mode, a framework with no relevant passages needs a new line in the judge prompt, "no relevant passages in N read files", instead of today's "No supporting documents uploaded". Nothing else in the judge prompt changes. Approve this narrow exception to the judge freeze? Recommended: yes, it is the only honest wording.

Unverified until the live run: current provider price, the model's context window, prompt cache effect, read and judge latency.
