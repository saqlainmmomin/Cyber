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
