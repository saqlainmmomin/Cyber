# P5-3: Framework-aware desk review, evidence extraction and signal persistence. One desk-review call per selected framework (DPDPA keeps its curated prompt, every other framework gets a registry-driven one), multi-requirement red flags stored once per requirement with `framework_id`/`flag_type`/`signal_group_id`, the keyword re-derivation retired, registry-driven evidence extraction on the multi path, and DPDPA-keyed pre-fill writes (desk review and screening) gated to the only questionnaire that can render them

**Plan:** `docs/plans/2026-09-24-001-cleanup-and-non-dpdpa-parity-plan.md`, task P5-3 ("Framework-aware desk review, evidence extraction and signal persistence"). It owns known gap **#1**'s root cause (the multi path has no pre-fill or tiering input because desk review is DPDPA-only; the questionnaire half is P5-4), known gap **#3** (a multi-requirement signal is stored against only its first requirement), and audit finding **A3** (desk review and multi-path evidence extraction are DPDPA-only whatever the framework selection). Plan-level decisions it implements against: **D-P5-A** (registry-driven code, acceptance on the three launch packs), **D-P5-C** ("Generalize the input before the questionnaire … No task may pre-fill ISO/NIST questions from DPDPA-keyed findings"), **D-P5-F** as decided by P5-1.
**Owner:** Claude designs (LLM output contract, schema change, citation interplay with P2-2's `citations_json`) → Codex implements. See `tasks/agent-ownership.md`, criteria "Foundational/gating" (P5-4 builds on this output) and "Judgment/architecture". Every fork is closed below.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, every constant, message, key name, column name, revision id and ordering below, and every test scenario. "The existing code makes step N awkward" is not a licence to redesign step N. Write down what you found and what you would need to change, then stop.

> **P5-4 depends on this task and reads the `D-P5-3-*` decisions below as a fixed contract**: the scoped-findings reader (D-P5-3-H), the one-row-per-requirement signal shape (D-P5-3-E), the `flag_type` vocabulary (D-P5-3-C) and the pre-fill gate (D-P5-3-L). They are written as rules, not suggestions. Do not weaken any of them "because P5-4 will replace this anyway".

**Depends on:** **P5-1 merged to `main`** (Step 0). P5-1 is being implemented now in `/Users/saqlainmomin/dpdpa-gap-tool-p5-1` (branch `codex/p5-1-correctness-bundle`). This handoff was written against `main` at `ad7bff0` (P5-8 merged) and treats every `D-P5-1-*` decision as shipped.
**Blocks:** P5-4 (adaptive UCC questionnaire).
**Runs in parallel with:** P5-5 (worktree `/Users/saqlainmomin/dpdpa-gap-tool-p5-5`). **Coordinates with:** P5-2 (not yet dispatched; see D-P5-3-P).
**No failing contract suite is pre-written.** `grep -rlnE "flag_type|signal_group_id|scoped_findings|framework_desk_review|ScreeningNotApplicable|DESK_REVIEW_FLAG_TYPES" tests/` finds nothing (checked at `ad7bff0`; the only `flag_type` hits in the repo are inside the DPDPA desk-review prompt text). **Codex writes `tests/test_p5_3_framework_desk_review.py` itself**, working from `## Test scenarios`. Every scenario listed is required. You may add cases, but you may not drop or weaken one. Existing test files may be changed **only** as listed in D-P5-3-E ("Lockstep head edits"). No other existing test file is modified.

## Step 0 (dispatching Claude session, before Codex starts)

**This handoff cannot be dispatched to Codex until P5-1 is merged to `main`.** Branch P5-3 from that `main` (`git worktree add ../dpdpa-gap-tool-p5-3 -b codex/p5-3-framework-aware-desk-review main`, symlink `.venv`, copy `.env`), then measure the baseline suite in the fresh worktree yourself and record it here before dispatch.

**Codex, your first action:** run

```bash
grep -n "^UNCONFIRMED_ANSWER_SOURCES\|^def confirmed_response_clause" app/services/auto_answer.py
grep -n "4e8c1a9d2b57" tests/test_correctness_bundle.py
.venv/bin/alembic heads
```

and confirm: (1) `app/services/auto_answer.py` defines `UNCONFIRMED_ANSWER_SOURCES = ("document", "inferred")` and `def confirmed_response_clause()` (P5-1's shipped names, D-P5-1-D); (2) `tests/test_correctness_bundle.py` exists (P5-1's suite); (3) the single Alembic head is `4e8c1a9d2b57`. **If any of these is not true, stop and report in `## Results`.** Do not re-implement P5-1's changes yourself and do not proceed on an unmerged base.

Then, **before editing any file**, record the two DPDPA byte-identity pins used by scenario 3 (D-P5-3-A):

```bash
.venv/bin/python - <<'PY'
import hashlib, json
from unittest.mock import patch
from tests.support.analyzer_mock import analyzer_request_key
from app.dpdpa.prompts import build_desk_review_system_prompt
from app.services import desk_review
DOCS = [{"id": "d1", "filename": "policy.pdf", "category": "privacy_policy", "text": "We obtain consent before processing."}]
print("system_sha256", hashlib.sha256(json.dumps(build_desk_review_system_prompt(), sort_keys=True).encode()).hexdigest())
seen = {}
def fake(**kw):
    seen.update(kw)
    return {"text": "{}", "usage": {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}
with patch.object(desk_review, "_call_llm", side_effect=fake):
    desk_review._call_claude_desk_review(DOCS, "Acme", "saas")
print("request_key", analyzer_request_key((), seen))
PY
```

Paste both values into `## Results` and into the test file as literals. For reference, the handoff author ran this snippet on `ad7bff0` and got `system_sha256 bf3dd3bb038f5651fbd225d21aba94a9c66936e2e1595a592cd7ae9ecd3544aa` and `request_key 4794fafe01bfeb7a88d6dfbbf85d801c2949712872893318ccebe909ab04a902`. P5-1 does not touch `app/dpdpa/prompts.py` or `desk_review.py`, so you should get the same values. If you get different ones, **use yours**, and report the difference in Results.

## Goal

1. Desk review on an ISO 27001, NIST CSF, or mixed assessment produces findings keyed to **that framework's own control IDs**, with that framework's red-flag patterns, one LLM call per selected framework. A failure on one framework does not lose the others.
2. A DPDPA-only desk review sends **byte-identical** LLM requests to today's.
3. A red flag that spans several requirements is visible to **every** one of them: pre-fill suppression, questionnaire deepening, the analysis prompt filter, the run envelope's quality counts, and the workpaper. Its `flag_type` is stored, so the question engine's keyword guessing goes.
4. Multi-path evidence extraction is per framework, so ISO and NIST get grounded extracted quotes instead of a wasted DPDPA-only call and a silent fall back to raw text.
5. Nothing writes DPDPA-keyed pre-fill rows (`"document"` or `"inferred"`) into an assessment whose questionnaire cannot render them. Findings and pre-fills already written that way stay in the database but are never read as belonging to a framework the assessment does not have.

## Current state

Grounded against `ad7bff0` on `main`. Relocate everything by symbol name, because line numbers drift, and P5-1 edits `analysis.py`, `auto_answer.py` and `web.py` before you start.

### Desk review is DPDPA-only (A3)

- `app/services/desk_review.py::run_desk_review(assessment_id, db)`: loads `analysis_documents`, resets or creates the `DeskReviewSummary` (deleting all prior `DeskReviewFinding` rows for the assessment), sets `desk_review_status="analyzing"`, commits, truncates the documents (`_truncate_documents`, `settings.max_total_document_words`, default **20000** words, `app/config.py`), then makes **one** call: `_call_claude_desk_review(documents=truncated, company_name=…, industry=…)`. On exception it sets `summary.status="error"`, `summary.error_message=str(e)` and returns. Otherwise `_persist_findings(db=, assessment_id=, result=, doc_id_by_filename=, sources=citable_sources(db, assessment_id))`, then `summary.document_catalog = json.dumps(result.get("document_catalog", []))`, `summary.coverage_summary = json.dumps(result.get("coverage_summary", {}))`, `summary.raw_ai_response = json.dumps(result)`, `status="completed"`, commit, then **unconditionally** `persist_document_answers(assessment_id, db)` (lazy import, failure logged as non-blocking).
- `_call_claude_desk_review(documents, company_name, industry)` builds `app.dpdpa.prompts.build_desk_review_system_prompt()` (no arguments) and `build_desk_review_user_prompt(documents, company_name, industry)` and calls `_call_llm(tier="judge", max_tokens=16000, temperature=0, system=…, messages=[…])`, then `_parse_json_response`.
- **Six test call sites depend on that seam's exact shape.** `tests/test_citations.py` and `tests/test_evidence_service.py` monkeypatch `desk_review._call_claude_desk_review` with a fake taking `(documents, company_name, industry)`; `tests/test_remaining_llm_call_sites.py` calls `_call_claude_desk_review([], "Acme", "saas")` positionally and patches `desk_review._call_llm`. So the DPDPA seam's name and signature cannot change (D-P5-3-A).
- `build_desk_review_system_prompt()` (`app/dpdpa/prompts.py`) is "…specializing in India's DPDPA", embeds the 41 requirements, and hard-codes **seven** `flag_type` values in its Level 4 text, in this order: `gdpr_copy_paste`, `template_artifact`, `ccpa_copy_paste`, `buried_consent`, `missing_timeline`, `scope_gap`, `data_minimization_concern`. Its output schema is `{document_catalog, evidence_map, absence_findings, signal_flags[{flag_type, description, severity, source_quote, document, location, requirement_ids}], coverage_summary}`.
- `build_desk_review_user_prompt(documents, company_name, industry)` is **framework-neutral text** ("## Organization … ## Documents for Review … Analyze these documents and provide the structured desk review output."). It is reused as-is (D-P5-3-C).
- **No caller gates desk review by framework.** `app/routers/desk_review.py::trigger_desk_review` (JSON) and `web.run_desk_review_web` (HTMX, background task with its own `SessionLocal`) run it whenever `analysis_documents` is non-empty. `documents_tab.html` offers it whenever `analysable_document_count` is truthy. The copy there is already framework-neutral.
- **No golden fixture pins desk review.** `tests/test_golden_dpdpa.py` pins `run_gap_analysis` (the single DPDPA analyzer path) through `tests/support/analyzer_mock.with_recorded_analyzer`, which patches `claude_analyzer._call_llm` and keys calls by `analyzer_request_key`. Its `desk_review_data` is a hand-built dict (`tests/support/canonical_dpdpa.py`, `signal_flags: []`), so it never touches desk review persistence. Step 0's pins stand in for the missing desk-review golden.

### `red_flag_patterns` is used, but not by desk review (a correction to the task brief)

`grep -rn "red_flag_patterns" app --include='*.py'` outside `definitions/` finds `app/frameworks/prompts.py::_build_red_flag_section`, which renders "## Skepticism Guidelines" into **the per-framework analysis system prompt** (`build_framework_system_prompt`). So the field is not unused. It is unused by desk review and by evidence extraction. `RedFlagPattern` (`app/frameworks/schema.py`) is a frozen dataclass with `pattern`, `description`, `severity` only. **It has no key/id field.** Measured counts: DPDPA 6, ISO 5, NIST 7, GDPR 6, HIPAA 6, PCI 6. DPDPA's six registry patterns are *not* the same list as the seven `flag_type`s in its desk-review prompt (the registry has "Policy without implementation evidence", the prompt has `scope_gap` and `data_minimization_concern`).

### Signal persistence loses requirements (gap #3)

- `desk_review._persist_findings`: `evidence_map` → one `finding_type="evidence"` row **per (requirement, quote)**; `absence_findings` → one `"absence"` row each; `signal_flags` → **one** `"signal"` row per flag with `requirement_id=req_ids[0] if req_ids else None`. `flag_type` is dropped. Citations are computed per item with `cite_quotes(sources, [quote], preferred_filename=doc_filename)`, or `[whole_item_citation(s) for s in sources if s.filename == doc_filename][:1]` when the quote is blank, and stored with `dumps_citations`. Absences get `citations_json="[]"`.
- `app/models/desk_review.py::DeskReviewFinding` columns: `id` (int autoincrement), `assessment_id`, `finding_type` (String 20), `requirement_id` (String 30, nullable), `document_id` (FK `assessment_documents.id` SET NULL), `content`, `severity`, `source_quote`, `source_location`, `citations_json` (P2-2), `created_at`. No `framework_id`, no `flag_type`.
- The longest control id in the registry is 18 characters, so `requirement_id` String(30) holds every framework's ids. All 400 control ids are globally unique across the six frameworks, and DPDPA ids carry no prefix (`CH2.CONSENT.1`).

### Every reader of `DeskReviewFinding` (the complete list; `grep -rn "DeskReviewFinding" app scripts --include='*.py'`)

| # | Reader | What it reads | Shape it assumes |
|---|---|---|---|
| F1 | `app/services/auto_answer.py::persist_document_answers` | `signal`/`absence` rows' `requirement_id` → `signal_req_ids` (suppresses pre-fill); `evidence` rows by `requirement_id` | per requirement |
| F2 | `app/services/question_engine.py::_load_desk_review_data` (DPDPA-only path) | evidence by requirement; signals list `{content, severity, requirement_id}`; absences; **the keyword re-derivation** (below) | per requirement |
| F3 | `app/routers/analysis.py::trigger_analysis` (the block after the gate, "Load desk review findings if available") | builds `desk_review_data = {coverage_summary, findings[{type, requirement_id, content, source_quote}], signal_flags[{content, severity, requirement_id}], absence_findings[{content, requirement_id}]}` | per row |
| F4 | `app/services/analysis_pipeline.py::_desk_review_quality` (via F3's `findings`) | counts `signal` findings **per requirement** → envelope `desk_review_red_flags` | per requirement |
| F5 | `app/routers/analysis.py` evidence-confidence lookups in `_persist_single_analysis` and `_persist_multi_framework_analysis` (via F3) | `evidence` findings' `requirement_id` and `coverage_summary` | per requirement |
| F6 | `app/services/claude_analyzer.py::_evidence_from_desk_review` (via F3) | `evidence` findings → `{requirement_id: [quote]}` | per requirement |
| F7 | `app/dpdpa/prompts.py::build_user_prompt` (single path, via F3) | `signal_flags`: `"- **SEV**: content (affects {requirement_id})"` | per signal |
| F8 | `app/frameworks/prompts.py::build_framework_user_prompt` (multi path, via F3) | `coverage_summary` filtered to `fw_control_ids`; `relevant_flags = [f for f in signal_flags if not f.get("requirement_id") or f["requirement_id"] in fw_control_ids]` | per signal, first id only |
| F9 | `app/services/workpaper.py::_desk_findings` | rows with `requirement_id IS NOT NULL`, grouped by `requirement_id`, with `resolve_citations` | per requirement |
| F10 | `app/routers/desk_review.py::get_desk_review` (JSON) and `trigger_desk_review` / `get_desk_review_status` (`.count()`) | `evidence_count`/`absence_count`/`signal_count` = row counts; per-row dicts, `citations` via `loads_citations` | per signal |
| F11 | `app/routers/web.py::desk_review_status_web` → `partials/desk_review_findings.html` | "Red Flags ({{ signals \| length }})", one card per signal row, "Related: {{ flag.requirement_id }}"; `total_findings = len(findings)` | per signal |
| F12 | `app/routers/web.py::generate_rfi_web` | `absence` and `signal` rows → `generate_rfi(desk_review_absences=…, desk_review_signals=…)`. `rfi_generator._build_evidence_items` reads **only** absences; signals are passed and ignored. | per row |
| F13 | `app/routers/web.py::run_desk_review_web` | snapshots old rows into `summary.legacy_history` with `{c.name: getattr(f, c.name) for c in f.__table__.columns}` (new columns are captured automatically), then deletes them | whole row |
| F14 | `app/services/retention.py` | purge by `assessment_id`; citation-reference count by `citations_json.contains(version_id)` | whole row |
| F15 | `scripts/seed_test_companies.py` | **writes** rows without `framework_id` (NovaPay fixture); also deletes by `assessment_id` | writer |

Per-requirement readers (F1, F2, F4, F5, F6, F9) outnumber per-signal readers (F7, F8, F10, F11, F12), and the existing `evidence` shape is already one row per requirement. This decides D-P5-3-E.

### The keyword re-derivation (a correction to the task brief's line numbers)

The keyword matching is **not** in `_modulate_question`. It is the tail of `question_engine._load_desk_review_data` (after P5-8, roughly lines 320-333): for every signal it lower-cases `content` and adds `gdpr_copy_paste` ("gdpr" or "copy"), `template_artifacts` ("template" or "generic"), `buried_consent` ("buried", or "consent" and "terms"), `scope_gaps` ("scope" or "gap"), `missing_timelines` ("timeline", or "missing" and "date") to a `signal_flags` set. `_modulate_question` (next function) matches signals to base questions by `signal.get("requirement_id") == req_id`, which is exactly where the truncation bites. The keyword set feeds only `_modulate_industry_question`'s `deepen_if.signal_flags` check. **The industry bank uses the plural vocabulary** (`app/dpdpa/industry_questions.py`: `template_artifacts`, `scope_gaps`, `gdpr_copy_paste`, `buried_consent`; `missing_timelines` is never used), while the LLM emits the **singular** `template_artifact`, `scope_gap`, `missing_timeline`. The two vocabularies never met; only the keyword guess connected them.

### Multi-path evidence extraction (A3)

- `claude_analyzer.run_multi_framework_analysis` step 1: if documents exist, `dr_evidence = _evidence_from_desk_review(desk_review_data)`; if non-empty it is used as-is, otherwise `_run_evidence_extraction(truncated_docs, desk_review_findings)`. `_run_evidence_extraction` uses `app.dpdpa.prompts.build_evidence_extraction_prompt` ("For each DPDPA requirement below … Include ALL requirement IDs"), `tier="extract"`, `max_tokens=8192`, `temperature=0`, the fixed system string "You are a document analyst. Extract exact quotes …", then `_ground_evidence_quotes`. Exceptions → warning, `None`.
- `build_framework_user_prompt` then keeps `fw_evidence = {k: v for k in evidence if k in fw_control_ids}`; empty → `_documents_section(documents)` (raw text). For ISO and NIST that filter always comes up empty.
- The single DPDPA path `run_gap_analysis` has the same step and is pinned by the golden test. `tests/test_golden_dpdpa.py::test_uncached_optional_call_is_not_swallowed` calls `_run_evidence_extraction([...])` with one positional argument. **Neither is changed** (D-P5-3-K).
- `tests/test_incomplete_assessment_e2e.py` calls `run_multi_framework_analysis(..., documents=[])` with `_call_llm` patched. No documents means no extraction call, which stays true.

### Pre-fill writers (the D-P5-C half)

- `persist_document_answers` writes one `QuestionnaireResponse(question_id=<coverage key>, answer_source="document")` per `adequate`/`partial` coverage key without a signal/absence row, on **any** assessment. On the multi path the questionnaire is keyed by cluster id (`question_engine._build_multi_framework_questionnaire`: `"id": ucc_q["cluster_id"]`, e.g. `CLUSTER_001` or `SINGLE.ISO.A5.1`), so these rows are never rendered. It also skips an existing row only when its source is `human`/`human_override`/`document_confirmed`: an existing `NULL`-source row or `"inferred"` row falls to the `else` branch and **a second row for the same `question_id` is added** (there is no unique constraint on `(assessment_id, question_id)`).
- `app/services/screening.py::run_screening_pass` runs on any assessment (the only caller is `web.submit_screening`, which renders `partials/screening_form.html` with `error=str(e)` on any exception). `_parse_inferences` keys inferences by DPDPA requirement id (`get_all_requirements()`), and `_persist_inferred_answers` writes `answer_source="inferred"` rows keyed by DPDPA ids.
- After P5-1, both sources are in `UNCONFIRMED_ANSWER_SOURCES`, so these rows are excluded from analysis and every gate (D-P5-1-D). They are otherwise inert on the multi path, with one visible leak: `web.assessment_detail`'s `response_count` counts every row (open question 4).

### Standing guards this task must respect

- `tests/test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` runs `git diff --name-only` (working tree against index) over a list that includes `app/routers/web.py` and `app/routers/analysis.py`. It **fails while your edits are uncommitted and passes once committed.** Do not modify it. Report it in Results as "working-tree guard, expected until commit". `tests/test_phase1_prefill.py` is on the same protected list: **do not modify it.**
- `tests/test_no_blended_scoring.py` guard (c): every line of `app/routers/analysis.py` containing `overall_score` must be one of the two allowed forms. Your `analysis.py` edit adds no such line.
- `tests/test_analysis_pipeline.py::test_legacy_consumers_do_not_read_the_new_tables` and `tests/test_pdf_updates.py` scenario 10: `scoring.py`, `review.py`, `reports.py`, `pdf_export.py` must not mention `Conclusion|AnalysisRun|analysis_pipeline`. You touch none of them.
- `grep -rn "relationship(" app/models/` must stay empty.
- Six test modules monkeypatch `app.routers.analysis.build_questionnaire`. You do not touch the gate.

## Decisions (made here so they are not relitigated)

### D-P5-3-A. DPDPA keeps its curated prompts; every other framework gets registry-driven ones. One dispatch point.

- **Rule:** the DPDPA desk-review prompt and the DPDPA evidence-extraction prompt stay exactly as they are and stay reached through their existing seams (`desk_review._call_claude_desk_review`, `claude_analyzer._run_evidence_extraction`). Every other registered framework (ISO, NIST, and with no code change GDPR/HIPAA/PCI) uses the new registry-driven builders in `app/frameworks/prompts.py` (D-P5-3-C, D-P5-3-K).
- **Why not make DPDPA registry-driven too:** DPDPA's desk-review prompt carries curated content the registry does not hold: seven flag types versus six registry patterns that don't correspond, and the data-minimisation focus block. Rebuilding it from `red_flag_patterns` would silently change DPDPA desk review, which must keep working identically, and would need a key field on `RedFlagPattern` in `app/frameworks/schema.py`, which P5-5 is editing concurrently. Moving DPDPA's curated text into the registry is open question 1.
- **The one special-case constant**, in `app/frameworks/prompts.py`:
  ```python
  CURATED_PROMPT_FRAMEWORK_ID = "dpdpa"  # keeps its hand-curated desk-review and evidence-extraction prompts (P5-3 D-P5-3-A)
  ```
  Both dispatchers (D-P5-3-B's `_desk_review_call`, D-P5-3-K's `_run_framework_evidence_extraction`) and `desk_review_flag_types` (D-P5-3-C) branch on this constant and nothing else. No other `== "dpdpa"` comparison is added anywhere in this task.
- **Byte identity (scenario 3):** for a DPDPA-only assessment, the request `_call_claude_desk_review` sends is unchanged (Step 0's `request_key`) and `build_desk_review_system_prompt()` is unchanged (Step 0's `system_sha256`).

### D-P5-3-B. One desk-review call per selected framework, with failure isolation

**Decision: one call per framework**, in `assessment.frameworks` order, sequentially, all sharing the same truncated document list.

Why:
1. **The output budget decides it.** The binding constraint is output tokens, not input. Every call returns `coverage_summary` for **every** control plus quotes. DPDPA's single call already uses `max_tokens=16000` for 41 requirements. A combined DPDPA + ISO + NIST call covers 228 controls, which is roughly 5.5 times DPDPA's output and far past what one response can return. A per-framework call is 41, 93 or 94 controls, the same scale the per-framework analyzer call already handles at `max_tokens=16384` with streaming.
2. **Failure isolation is the analyzer's existing pattern** (`run_multi_framework_analysis` catches per framework), and it matches P5-1's fail-closed intent (A2): one framework's failure must be visible and must not discard or corrupt the others.
3. **DPDPA byte identity** (D-P5-3-A) is only possible if DPDPA gets its own call.
4. **Cost, accepted:** the document text (at most `max_total_document_words` = 20000 words, truncated once by the existing `desk_review._truncate_documents`) is sent once per framework, so a three-framework desk review sends about three times the input tokens. Desk review is a manual, once-per-assessment trigger. Open question 3.

Implementation in `app/services/desk_review.py`:

```python
def _call_framework_desk_review(framework_id: str, documents: list[dict], company_name: str, industry: str) -> dict:
    """Registry-driven desk review for any framework except CURATED_PROMPT_FRAMEWORK_ID."""
    # system = build_framework_desk_review_system_prompt(framework_id)
    # user   = build_desk_review_user_prompt(documents, company_name, industry)   # app.dpdpa.prompts, framework-neutral
    # response = _call_llm(tier="judge", stream=True, max_tokens=16384, temperature=0,
    #                      system=system, messages=[{"role": "user", "content": user}])
    # log usage exactly like _call_claude_desk_review, prefixed f"Desk review ({framework_id}) tokens"
    # return _parse_json_response(response["text"])

def _desk_review_call(framework_id: str, *, documents, company_name, industry) -> dict:
    if framework_id == CURATED_PROMPT_FRAMEWORK_ID:
        return _call_claude_desk_review(documents=documents, company_name=company_name, industry=industry)
    return _call_framework_desk_review(framework_id, documents, company_name, industry)
```

- `_call_claude_desk_review` is **not modified**. It is called with keywords exactly as `run_desk_review` calls it today, so the existing fakes keep working. `stream=True`/`16384` for the generic call mirror the per-framework analyzer call (large responses). DPDPA keeps `16000`/non-streaming.
- Both seams are looked up as module globals at call time (tests patch `desk_review._call_claude_desk_review` and `desk_review._call_framework_desk_review`).

`run_desk_review(assessment_id, db)` keeps its signature. Its body, in this exact order:
1. Unchanged up to and including `truncated = _truncate_documents(documents)` (assessment lookup, documents, `doc_id_by_filename`, summary reset, `desk_review_status="analyzing"`, commit).
2. `framework_ids = assessment.frameworks` (the property).
3. For each `fw_id` in order: `try: results[fw_id] = _normalize_result(fw_id, _desk_review_call(fw_id, documents=truncated, company_name=assessment.company_name, industry=assessment.industry))` `except Exception as exc: errors[fw_id] = str(exc); logger.error("Desk review failed for %s: %s", fw_id, exc)`. `_normalize_result` is D-P5-3-D. A `ValueError` from `_parse_json_response` counts as that framework's failure.
4. **Every framework failed** (`not results`): `summary.status = "error"`; `summary.error_message = str(errors[framework_ids[0]])` when exactly one framework is selected (today's behaviour, unchanged), else `DESK_REVIEW_ALL_FAILED_MESSAGE.format(names=…)`; `summary.raw_ai_response = _raw_response(framework_ids, results, errors)`; `assessment.desk_review_status = "error"`; commit; return. No findings are written, and no pre-fill runs.
5. Otherwise, inside the existing persist `try`: `sources = citable_sources(db, assessment_id)` once; for each `fw_id` in `framework_ids` that is in `results`: `_persist_findings(db=db, assessment_id=assessment_id, framework_id=fw_id, result=results[fw_id], doc_id_by_filename=doc_id_by_filename, sources=sources)`. Then the summary aggregation (D-P5-3-G), `summary.status = "completed"`, `summary.error_message = DESK_REVIEW_PARTIAL_MESSAGE.format(names=…) if errors else None`, `summary.completed_at`, `assessment.desk_review_status = "completed"`, commit.
6. Pre-fill: the existing non-blocking `persist_document_answers` call, unchanged in place. The gate lives inside that function (D-P5-3-L).
7. The existing persist-failure `except` is unchanged.

Constants in `desk_review.py`:
```python
DESK_REVIEW_PARTIAL_MESSAGE = (
    "Desk review failed for {names}. Findings for the other frameworks were saved. "
    "Run desk review again to complete it."
)
DESK_REVIEW_ALL_FAILED_MESSAGE = "Desk review failed for every selected framework ({names}). Run desk review again."
RAW_RESPONSE_SCHEMA_VERSION = 2
```
`names` is always `", ".join(FrameworkRegistry.get(fw).name for fw in <failed ids in framework_ids order>)`.

**Why a partial failure stays `"completed"`, not a new status:** five readers gate on `status == "completed"` (F1, F2, F3, `web` timeline, polling). A new value would make every one of them silently ignore the frameworks that did succeed. A failed framework contributes **no** findings and **no** coverage keys, and nothing reads a missing coverage key as "absent" (F1 pre-fills only `adequate`/`partial`; F2 defaults to `active`; D-P5-3-K runs evidence extraction for a framework with no desk-review evidence). So the gap is self-healing downstream, and it is stated to the consultant (D-P5-3-I). Open question 6.

### D-P5-3-C. The registry-driven desk-review prompt, flag keys and flag vocabulary

In `app/frameworks/prompts.py`:

```python
UNCLASSIFIED_FLAG_TYPE = "unclassified"

def red_flag_key(pattern: RedFlagPattern) -> str:
    """Stable flag_type for a registry red-flag pattern: its `pattern` text slugified."""
    return re.sub(r"[^a-z0-9]+", "_", pattern.pattern.lower()).strip("_")

def desk_review_flag_types(framework_id: str) -> tuple[str, ...]:
    """The flag_type values a desk review for this framework may store."""
    if framework_id == CURATED_PROMPT_FRAMEWORK_ID:
        from app.dpdpa.prompts import DESK_REVIEW_FLAG_TYPES
        return DESK_REVIEW_FLAG_TYPES
    return tuple(red_flag_key(rf) for rf in FrameworkRegistry.get(framework_id).red_flag_patterns)
```

- `app/dpdpa/prompts.py` gains, next to `build_desk_review_system_prompt` and **without changing that function**:
  ```python
  DESK_REVIEW_FLAG_TYPES = (
      "gdpr_copy_paste", "template_artifact", "ccpa_copy_paste", "buried_consent",
      "missing_timeline", "scope_gap", "data_minimization_concern",
  )
  ```
- **Why slugified keys, not a new `key` field on `RedFlagPattern`:** a field means editing `app/frameworks/schema.py` and six definition files. P5-5 is editing `schema.py` and `iso27001.py`/`nist_csf.py` concurrently. The slug is deterministic, and it is unique per framework today. Measured keys, which scenario 2 pins as literals:
  - **ISO 27001:** `certification_without_evidence_of_operational_controls`, `statement_of_applicability_gaps`, `generic_policy_documents`, `no_management_review_evidence`, `risk_assessment_staleness`.
  - **NIST CSF:** `govern_function_absence`, `tier_mismatch_with_claims`, `detection_without_response_capability`, `asset_inventory_gaps`, `supply_chain_blind_spots`, `recovery_plan_never_tested`, `profile_without_action`.
  - The longest key in any framework is 59 characters (PCI), which is why `flag_type` is String(100) (D-P5-3-E).
- **`build_framework_desk_review_system_prompt(framework_id: str) -> list[dict]`** returns `[{"type": "text", "text": persona}, {"type": "text", "text": instructions, "cache_control": {"type": "ephemeral"}}]`, where `persona = _FRAMEWORK_PERSONAS.get(framework_id, _DEFAULT_PERSONA)`, `fw = FrameworkRegistry.get(framework_id)`, `controls_text = _build_controls_text(fw)` (the existing helper, so D4's reference-only content rule is inherited unchanged), `n = fw.control_count()`, and the **rendered** `instructions` text is exactly the following. Placeholders are in `<angle brackets>`. Write it as an f-string with JSON braces doubled so that the rendered text contains single braces:

  ```text
  You are performing a desk review of an organization's documents against <fw.name> (<fw.version>). This is the first step of a professional assessment: catalog what exists, map evidence to controls, identify what is missing, and flag red flags. Assess against <fw.name> only.

  ## <fw.name> Controls Reference

  <controls_text>

  ## Analysis Levels

  Perform ALL four analysis levels for each document:

  ### Level 1 - Document Catalog
  For each document, identify:
  - Document type (policy, procedure, standard, register, report, contract, or other)
  - Which <fw.name> controls it covers
  - A 1-2 sentence summary of what it contains

  ### Level 2 - Evidence Mapping
  For each control (<n> total), extract EXACT quotes from the documents that address that control. Include the document filename and approximate location (section heading, page, paragraph). Quote verbatim; do not paraphrase.

  ### Level 3 - Absence Detection
  For each control, identify what is MISSING from the documents. Be specific: name the missing element, not a generic gap.

  ### Level 4 - Signal Detection
  <signal_block>

  ## Control IDs

  Use only the control IDs listed in the Controls Reference above, exactly as written, in evidence_map, absence_findings, signal_flags requirement_ids and coverage_summary. List every control a red flag affects in its requirement_ids.

  ## Output Format

  Respond ONLY with valid JSON. No markdown fences, no commentary.

  {
    "document_catalog": [
      {"filename": "policy.pdf", "document_type": "Information Security Policy", "coverage_areas": ["<id0>"], "summary": "..."}
    ],
    "evidence_map": {
      "<id0>": [{"quote": "Exact quoted text from document...", "document": "policy.pdf", "location": "Section 3"}]
    },
    "absence_findings": [
      {"requirement_id": "<id1>", "description": "...", "severity": "high", "affected_documents": ["policy.pdf"]}
    ],
    "signal_flags": <signal_example>,
    "coverage_summary": {"<id0>": "adequate", "<id1>": "absent"}
  }

  Coverage levels: "adequate" (control well-addressed), "partial" (some mention but gaps), "absent" (explicitly missing despite a relevant document), "not_covered" (no relevant document uploaded).

  Include ALL <n> control IDs in coverage_summary. Be thorough and precise.
  ```

  - `<id0>`, `<id1>` = the ids of `fw.all_controls()[0]` and `[1]`.
  - `<signal_block>`, when `fw.red_flag_patterns` is non-empty: `Flag every instance of the following patterns. Use exactly the flag_type shown:` then a blank line, then one line per pattern in registry order, `- **<rf.pattern>** (flag_type: "<red_flag_key(rf)>", severity: <rf.severity>): <rf.description>`, then a blank line, then `Use only the flag_type values listed above. Do not flag anything that fits none of them.` When empty: `This framework defines no red-flag patterns. Return an empty signal_flags list.`
  - `<signal_example>`, when there are patterns: `[{"flag_type": "<first key>", "description": "...", "severity": "high", "source_quote": "...", "document": "policy.pdf", "location": "Section 2", "requirement_ids": ["<id0>", "<id1>"]}]`. When there are none: `[]`.
- The prompt must not contain the strings `DPDPA`, `Data Protection Board` or `data principal` (scenario 2).

### D-P5-3-D. Normalizing one framework's result before it is stored

`desk_review._normalize_result(framework_id: str, result: dict) -> dict` returns a new dict with exactly the keys `document_catalog`, `evidence_map`, `absence_findings`, `signal_flags`, `coverage_summary`. `ids = {c.id for c in FrameworkRegistry.get(framework_id).all_controls()}`, `vocab = set(desk_review_flag_types(framework_id))`:
- `document_catalog`: `result.get("document_catalog") or []`, kept as-is when it is a list, else `[]`.
- `evidence_map`: keys not in `ids` are dropped. Values that are not lists are dropped. List items that are not dicts are dropped.
- `absence_findings`: items that are not dicts are dropped. An item whose `requirement_id` is a non-empty string not in `ids` is dropped. An item with no `requirement_id` is kept, as a cross-cutting absence (today's behaviour).
- `signal_flags`: items that are not dicts are dropped. `requirement_ids` becomes `list(dict.fromkeys(r for r in (item.get("requirement_ids") or []) if isinstance(r, str) and r in ids))`, which dedupes, keeps order and drops ids from other frameworks. If that leaves it empty the flag is kept as cross-cutting. `flag_type` is kept if it is in `vocab`, else it becomes `UNCLASSIFIED_FLAG_TYPE` (this includes a missing value).
- `coverage_summary`: `{k: v for k, v in (result.get("coverage_summary") or {}).items() if k in ids}`, keeping order.
- One `logger.warning("Desk review (%s) dropped %d unknown control id(s)", framework_id, n)` when `n > 0`, where `n` counts dropped evidence keys, absences, signal ids and coverage keys.

This applies to DPDPA as well. Normal DPDPA output is unaffected. An id the model invented (for example a section id like `CH2.CONSENT`) used to be stored verbatim and is now dropped. That is intended: it keeps every stored `requirement_id` a real control of the stored `framework_id`.

### D-P5-3-E. Schema: one row per (signal, requirement), plus `framework_id`, `flag_type` and `signal_group_id`

**Decision: one row per requirement** (denormalized), not a JSON array column.
1. **It fixes gap #3 in every per-requirement reader without touching them** (F1, F2's `_modulate_question`, F4, F5, F6, F9). Each one filters or groups on `requirement_id` and becomes lossless automatically. With a JSON column, all six would have to learn to expand an array, and any reader that went on using the scalar `requirement_id` would stay silently truncated: the same trap, moved.
2. **It matches the existing shape.** `evidence` is already one row per (requirement, quote) and `absence` one row per requirement.
3. **Citations stay per requirement for free** (D-P5-3-F), and P5-4's "any member control with a signal deepens the cluster" rule is a plain per-requirement lookup.
4. **The cost** is duplicated `content`/`source_quote`/`citations_json` text across a group's rows, and per-signal readers (F7, F8, F10, F11, F12) must group. Grouping needs an explicit key, because grouping on text is fragile: that key is `signal_group_id`.

**Model** (`app/models/desk_review.py::DeskReviewFinding`), three columns added after `citations_json`:
```python
framework_id: Mapped[str | None] = mapped_column(String(50), nullable=True)  # NULL = legacy row = "dpdpa" (P5-3)
flag_type: Mapped[str | None] = mapped_column(String(100), nullable=True)    # signal rows only
signal_group_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # shared by the rows of one signal
```
There is no Python `default` on `framework_id`. A default of `"dpdpa"` would silently mislabel any future writer that forgets it. The writer always sets it (D-P5-3-F). `NULL` is interpreted by the reader rule in D-P5-3-H.

**Legacy rows. Decision: backfill in the migration, and also fall back at read time.**
- Every row written before P5-3 came from the DPDPA-only desk review (or the DPDPA-only NovaPay seed), so the migration sets `framework_id = 'dpdpa'` on every existing row. The database then describes itself.
- **`NULL` is still read as `"dpdpa"`** (`LEGACY_FINDING_FRAMEWORK_ID`, D-P5-3-H), because code that is not changed by this task still inserts rows without it: `scripts/seed_test_companies.py` (F15), and the direct inserts in `tests/test_workpaper.py`, `tests/test_analysis_pipeline.py`, `tests/test_phase1_prefill.py` (protected) and `tests/test_retention.py`. Those rows are DPDPA by construction.
- `flag_type` and `signal_group_id` are **not** backfilled. A legacy signal's type cannot be recovered: the keyword guess produced a *set* per row, not one value. Legacy rows keep `NULL`. Consequences are in D-P5-3-J.

**Alembic revision, pinned id `8b2d5f7e1c34`.** File `alembic/versions/8b2d5f7e1c34_p5_3_framework_keyed_desk_review_findings.py`. Hand-written, following P2-2's file (`3d8b6f0a2c51_p2_2_citations_json.py`) exactly in layout:

```python
"""P5-3: key desk review findings by framework, flag type and signal group.

Revision ID: 8b2d5f7e1c34
Revises: 4e8c1a9d2b57
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b2d5f7e1c34"
down_revision: Union[str, None] = "4e8c1a9d2b57"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("desk_review_findings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("framework_id", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("flag_type", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("signal_group_id", sa.String(length=36), nullable=True))

    # Every finding written before P5-3 came from the DPDPA-only desk review.
    op.execute(sa.text("UPDATE desk_review_findings SET framework_id = 'dpdpa' WHERE framework_id IS NULL"))


def downgrade() -> None:
    bind = op.get_bind()
    count = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM desk_review_findings "
            "WHERE flag_type IS NOT NULL OR signal_group_id IS NOT NULL "
            "OR (framework_id IS NOT NULL AND framework_id != 'dpdpa')"
        )
    ).scalar_one()
    if count:
        raise RuntimeError(
            "Refusing to downgrade past P5-3 revision 8b2d5f7e1c34: "
            f"{count} desk_review_findings rows hold framework-keyed data (a non-DPDPA "
            "framework_id, a flag_type or a signal_group_id). Downgrading would drop it "
            "and make non-DPDPA findings read as DPDPA -- restore a verified backup instead."
        )

    with op.batch_alter_table("desk_review_findings", schema=None) as batch_op:
        batch_op.drop_column("signal_group_id")
        batch_op.drop_column("flag_type")
        batch_op.drop_column("framework_id")
```

Rows that hold only the backfilled `'dpdpa'` downgrade losslessly, because `NULL` means DPDPA both before and after P5-3. No index is added: every query already filters on the indexed `assessment_id`.

**Lockstep head edits** (existing tests that hard-code the current head; change **only** the literal shown and nothing else in those files):
- `tests/test_retention.py`: `assert "4e8c1a9d2b57 (head)" in heads` → `"8b2d5f7e1c34 (head)"`.
- `tests/test_alembic_baseline_immutable.py`: both probe templates' `down_revision = "4e8c1a9d2b57"` → `"8b2d5f7e1c34"`. Otherwise the probe forks a second head.
- `tests/test_startup_invariants.py`: both `assert version == "4e8c1a9d2b57"` → `"8b2d5f7e1c34"`.
- `tests/test_data_integrity.py`: the three `"4e8c1a9d2b57"` version assertions (in the `downgrade -1` round-trip test and the two recovery tests) → `"8b2d5f7e1c34"`. The round trip now exercises this revision's downgrade on an empty database, which is what a round-trip test of the newest revision should do.
- `tests/test_analysis_pipeline.py::test_p2_3_revision_is_head_and_adds_link_and_uniqueness`: `assert script.get_current_head() == P2_3_REVISION` → `assert script.get_revision("8b2d5f7e1c34").down_revision == P2_3_REVISION`. Nothing else in that test or file changes.
- `tests/test_correctness_bundle.py` (P5-1): its scenario-10 assertion that `alembic heads` is `4e8c1a9d2b57` → `8b2d5f7e1c34`. This is the only line of P5-1's suite you touch. It supersedes D-P5-1-K's "head stays `4e8c1a9d2b57`" (which was scoped to P5-1).
- `tests/test_citations.py` only asserts `get_revision("4e8c1a9d2b57").down_revision`, which stays true. Don't change it.
- If `grep -rn "4e8c1a9d2b57" tests` finds any other **head** assertion (P2-1 found four the handoff missed), update only its literal, and list each one in Results as handoff drift.

### D-P5-3-F. The writer, and citations per requirement

`desk_review._persist_findings(db, assessment_id, framework_id, result, doc_id_by_filename, sources=())` gains the `framework_id` parameter, after `assessment_id`. It is called only with a normalized result (D-P5-3-D). No test calls it directly.
- **Evidence rows:** unchanged, plus `framework_id=framework_id`. `flag_type`/`signal_group_id` are `None`.
- **Absence rows:** unchanged, plus `framework_id=framework_id`.
- **Signal rows:** for each flag, compute `citations` **once**, exactly as today (the same `cite_quotes` / `whole_item_citation` expression), and `serialized = dumps_citations(citations)`. Then `group_id = str(uuid.uuid4())`, and for each `req_id in (flag["requirement_ids"] or [None])`, add one row with `finding_type="signal"`, `framework_id=framework_id`, `requirement_id=req_id`, `flag_type=flag["flag_type"]`, `signal_group_id=group_id`, `document_id=doc_id_by_filename.get(doc_filename)`, `content=flag.get("description", "")`, `severity=flag.get("severity", "medium")`, `source_quote=flag.get("source_quote", "")`, `source_location=flag.get("location", "")`, `citations_json=serialized`. Rows go in `requirement_ids` order.
- **Citations per requirement: every row of a group carries the same, complete `citations_json` string.** A citation points at an `EvidenceVersion` span (P2-2), and that span is the evidence for the flag on *each* requirement it affects. So each requirement's row is independently citable and independently resolvable: `validate_citations`, `resolve_citations` in the workpaper (F9), which shows the flag with its citation under every affected requirement, and P4-4's retention reference count (F14), which counts rows referencing a version (a group of N rows counts N, which only makes the "still referenced" check more conservative). Nothing splits or re-derives citations per requirement. The quote is the same quote.
- The source must no longer contain `req_ids[0]` (scenario 12).

### D-P5-3-G. What the summary stores when there are several frameworks

After the per-framework persists (D-P5-3-B step 5):
- `summary.coverage_summary = json.dumps(merged)`, where `merged` is each successful framework's normalized `coverage_summary` merged in `framework_ids` order (`merged.update(...)`). Control ids are globally unique, so nothing collides.
- `summary.document_catalog`: when exactly one framework **succeeded**, its normalized `document_catalog`, verbatim. When several did, merged by `filename`: the first entry seen for a filename (in `framework_ids` order) supplies `document_type` and `summary`, `coverage_areas` is the order-preserving union across frameworks, and entries without a `filename` are appended unchanged. The findings panel's "across N documents" count therefore stays a document count.
- `summary.raw_ai_response = _raw_response(framework_ids, results, errors)` = `json.dumps({"schema_version": RAW_RESPONSE_SCHEMA_VERSION, "frameworks": {fw: {"status": "completed", "result": results[fw]} if fw in results else {"status": "error", "error": errors[fw]} for fw in framework_ids}})`. The same shape is written in the all-failed case (D-P5-3-B step 4). Nothing reads `raw_ai_response` today (grep), so the shape change breaks no reader.
- `desk_review_findings.failed_desk_review_frameworks(summary) -> list[str]` (D-P5-3-H) parses it: the ids whose status is `"error"`, in stored order. Legacy raw (no `schema_version`, `NULL`, or invalid JSON) → `[]`.

### D-P5-3-H. One scoped reader of findings: the quarantine rule, and P5-4's input contract

New module **`app/services/desk_review_findings.py`**. It imports only models, `FrameworkRegistry` and `json`, so that `question_engine`, `auto_answer`, the routers and `analysis.py` can import it without pulling in `desk_review`'s LLM and evidence dependencies.

```python
LEGACY_FINDING_FRAMEWORK_ID = "dpdpa"

def finding_framework_id(finding: DeskReviewFinding) -> str:
    return finding.framework_id or LEGACY_FINDING_FRAMEWORK_ID

def scoped_findings(db, assessment, *, framework_ids: list[str] | None = None) -> list[DeskReviewFinding]:
    """This assessment's findings whose framework is selected (or in framework_ids), ordered by id."""

def group_signal_findings(findings) -> list[dict]:
    """One dict per signal (signal_group_id, or the row id for a legacy row), in first-row-id order."""

def load_desk_review_data(db, assessment) -> dict | None:
    """The analyzer's desk_review_data, built only from in-scope findings and coverage."""

def failed_desk_review_frameworks(summary: DeskReviewSummary | None) -> list[str]: ...
```

**The quarantine rule (binding on P5-4 and every later reader):** a finding belongs to framework `finding_framework_id(f)`. It is read **only** when that framework is in `assessment.frameworks`. `scoped_findings` does it in SQL: `DeskReviewFinding.assessment_id == assessment.id` and `framework_id IN (selected)`, plus `OR framework_id IS NULL` when `"dpdpa"` is selected; `.order_by(DeskReviewFinding.id)`. Coverage keys are read only when they are control ids of a selected framework. **Every reader in the table below that reads findings for display, prompting or pre-fill goes through `scoped_findings`/`load_desk_review_data`.**

`group_signal_findings(findings)`: over the `finding_type == "signal"` rows in the given (id) order, group by `f.signal_group_id or f"row:{f.id}"`. Each group dict has exactly the keys `signal_group_id` (`None` for a legacy row), `framework_id` (via `finding_framework_id`), `flag_type`, `content`, `severity`, `source_quote`, `source_location`, `document_id`, `citations_json` (all from the group's first row), `requirement_ids` (the order-preserving, deduped non-null `requirement_id`s of the group), and `requirement_id` (`requirement_ids[0]` or `None`, for readers that still print a single id).

`load_desk_review_data(db, assessment)`:
- The completed `DeskReviewSummary` (the same filter as today). If there is none → `None`.
- `findings = scoped_findings(db, assessment)`. `control_ids` = the union of `{c.id for c in FrameworkRegistry.get(fw).all_controls()}` over `assessment.frameworks`. `coverage = {k: v for k, v in json.loads(summary.coverage_summary or "{}").items() if k in control_ids}`.
- If `not findings and not coverage` → `None`. Nothing in scope counts as "no desk review". On an ISO-only assessment holding only legacy DPDPA findings, the analyzer therefore behaves as if desk review never ran, and runs evidence extraction for ISO (D-P5-3-K). One accepted side effect: a completed desk review with no findings and an empty coverage map now gives `desk_review_used = False` in the run envelope instead of `True`.
- Otherwise it returns exactly:
  ```python
  {
      "coverage_summary": coverage,
      "findings": [{"type": f.finding_type, "requirement_id": f.requirement_id, "content": f.content,
                    "source_quote": f.source_quote, "framework_id": finding_framework_id(f),
                    "flag_type": f.flag_type} for f in findings],
      "signal_flags": [{"content": g["content"], "severity": g["severity"], "requirement_id": g["requirement_id"],
                        "requirement_ids": g["requirement_ids"], "framework_id": g["framework_id"],
                        "flag_type": g["flag_type"]} for g in group_signal_findings(findings)],
      "absence_findings": [{"content": f.content, "requirement_id": f.requirement_id,
                            "framework_id": finding_framework_id(f)} for f in findings if f.finding_type == "absence"],
  }
  ```
  `findings` stays **one entry per row**, so F4's per-requirement red-flag count and F5/F6's evidence lookups become lossless with no change to them. The new keys are additive: every existing consumer reads only the keys it read before.

**Reader-by-reader changes (the complete list, F1-F15):**

| # | Change |
|---|---|
| F1 | D-P5-3-L. Uses `scoped_findings(db, assessment, framework_ids=["dpdpa"])`. The per-row loop is otherwise unchanged. With one row per requirement, suppression covers every requirement a signal names. |
| F2 | D-P5-3-J. `_load_desk_review_data(assessment_id, db)` loads the assessment and uses `scoped_findings(db, assessment, framework_ids=["dpdpa"])`. Coverage is filtered to DPDPA ids the same way. `_modulate_question` is **not changed**: per-requirement rows make its `requirement_id == req_id` match lossless. |
| F3 | `analysis.py`: the whole "Load desk review findings if available" block (the local `DeskReviewFinding, DeskReviewSummary` import through the end of the `desk_review_data = {…}` literal) is replaced by `desk_review_data = load_desk_review_data(db, assessment)`, imported at module level from `app.services.desk_review_findings`. That is the **only** `analysis.py` hunk in this task. |
| F4, F5, F6 | No code change. They become lossless through F3's per-row `findings`. |
| F7 | `app/dpdpa/prompts.py::build_user_prompt`: the `(affects …)` suffix becomes `f" (affects {', '.join(flag['requirement_ids'])})"` when `flag.get("requirement_ids")` is non-empty, else the existing `if flag.get("requirement_id")` form. For a single-requirement flag the text is byte-identical, and the golden (`signal_flags: []`) is unaffected. |
| F8 | D-P5-3-I. |
| F9 | **No change.** `workpaper._desk_findings` groups by `requirement_id`, and ids are globally unique, so a DPDPA row can never attach to an ISO Conclusion. A multi-requirement signal now appears under every affected requirement, each with its citations. That is the gap #3 fix reaching the workpaper. |
| F10 | `app/routers/desk_review.py::get_desk_review`: `findings = scoped_findings(db, assessment)`. `evidence`/`absences` items gain `"framework_id": finding_framework_id(f)`. `signals` = one item per `group_signal_findings(findings)` group with the keys `requirement_id`, `requirement_ids`, `framework_id`, `flag_type`, `content`, `severity`, `source_quote`, `source_location`, `document_id`, `citations` (`loads_citations(g["citations_json"])`). `signal_count = len(signals)`. New top-level key `"failed_frameworks": failed_desk_review_frameworks(summary)`. Every existing key stays, and `absences` still has no `citations` key (`test_citations` asserts both). `trigger_desk_review` gains `"failed_frameworks"` in its response. Its `finding_count` and `get_desk_review_status`'s count stay **row** counts (unchanged). |
| F11 | D-P5-3-I. |
| F12 | `web.generate_rfi_web`: `findings = scoped_findings(db, assessment)`. `absences` are built from its `absence` rows, with the same dict keys as today. `signals` = `[{"content": g["content"], "severity": g["severity"], "requirement_id": g["requirement_id"]} for g in group_signal_findings(findings)]`. Same keys, one per signal. Nothing else in that route changes. (P5-6 rebuilds the RFI.) |
| F13, F14 | No change. |
| F15 | **Not modified.** Its rows are read as DPDPA through `NULL`. |

### D-P5-3-I. The per-signal display surfaces and the analysis prompt filter

- **`web.desk_review_status_web`** (completed branch): `findings = scoped_findings(db, assessment)`. `evidence`/`absences` are the rows filtered by `finding_type`, as today. `signals = group_signal_findings(findings)`. `coverage` is filtered to selected-framework control ids (the same rule as `load_desk_review_data`). New context keys: `failed_framework_names` = `[FrameworkRegistry.get(fw).name for fw in failed_desk_review_frameworks(summary)]`, and `total_findings = len(evidence) + len(absences) + len(signals)`.
- **`partials/desk_review_findings.html`:**
  - (1) Directly after the green summary bar: `{% if failed_framework_names %}<div data-desk-review-failed-frameworks class="…amber alert styling…">Desk review failed for {{ failed_framework_names | join(", ") }}. Findings for the other frameworks were saved. Run desk review again to complete it.</div>{% endif %}`.
  - (2) In the red-flag card, `{% if flag.requirement_id %}<p …>Related: {{ flag.requirement_id }}</p>{% endif %}` becomes `{% if flag.requirement_ids %}<p …>Related: {{ flag.requirement_ids | join(", ") }}</p>{% endif %}`. The cards read `flag.content`/`flag.severity`/`flag.source_quote`, which the group dicts provide.
  - No other template line changes: no `|safe`, and no apostrophe in the new text.
- **`app/frameworks/prompts.py::build_framework_user_prompt`**, the red-flag filter (F8) becomes:
  ```python
  relevant_flags = [
      f for f in desk_review_summary["signal_flags"]
      if (set(f.get("requirement_ids") or ([f["requirement_id"]] if f.get("requirement_id") else [])) & fw_control_ids)
      or (not f.get("requirement_ids") and not f.get("requirement_id")
          and (f.get("framework_id") or LEGACY_FINDING_FRAMEWORK_ID) == framework_id)
  ]
  ```
  A flag is shown to a framework when **any** of its requirements belongs to that framework, or when it is cross-cutting and belongs to that framework. **Behaviour change, intended (A3):** a DPDPA cross-cutting red flag no longer appears in the ISO and NIST prompts. The rendered line format is unchanged. Import `LEGACY_FINDING_FRAMEWORK_ID` from `app.services.desk_review_findings`, or declare the same literal locally with a comment naming the source, if the import would create a cycle. Report which you used.

### D-P5-3-J. The keyword re-derivation is retired; `flag_type` is the only signal-type source

- In `question_engine._load_desk_review_data`, **delete** the whole block from the comment `# Extract signal flag types from signal content …` through the last `signal_flags.add(...)`. Replace it with:
  ```python
  signal_flags = {f.flag_type for f in findings if f.finding_type == "signal" and f.flag_type}
  ```
  over the DPDPA-scoped rows. `question_engine.py` must no longer contain `content_lower` (scenario 12).
- **One vocabulary.** In `app/dpdpa/industry_questions.py`, change the `deepen_if.signal_flags` values to the LLM's (singular) vocabulary: `"template_artifacts"` → `"template_artifact"` and `"scope_gaps"` → `"scope_gap"`, everywhere they occur (four `deepen_if` lines at `ad7bff0`: `IND.SAAS.1`'s pair, the `gdpr_copy_paste`/`scope_gaps` pair, and two `["scope_gaps"]`). `gdpr_copy_paste` and `buried_consent` are already right. Nothing else in that file changes. Scenario 7 asserts every `deepen_if.signal_flags` value across all industry banks is in `DESK_REVIEW_FLAG_TYPES`.
- **Legacy rows, accepted consequence:** a pre-P5-3 signal row (`flag_type IS NULL`) no longer deepens any industry question. It still deepens its own base question through `requirement_id`. Re-running desk review restores industry deepening with real types. Keeping the keyword fallback "for legacy rows only" is explicitly rejected: the plan retires it, and it misfires (any signal containing "gap" or "consent … terms" matched).
- `_modulate_industry_question` is unchanged.

### D-P5-3-K. Registry-driven multi-path evidence extraction

In `app/services/claude_analyzer.py`:
- **`run_gap_analysis` (single DPDPA path) is not changed**, and neither is `_run_evidence_extraction` (its signature and its prompt). The golden must pass unmodified.
- New `app/frameworks/prompts.py::build_framework_evidence_extraction_prompt(framework_id: str, documents: list[dict], desk_review_findings: list[dict] | None = None) -> str`. Its `docs_text` and `desk_review_context` are built exactly as `app.dpdpa.prompts.build_evidence_extraction_prompt` builds them (copy the logic, don't import the DPDPA function), and it renders:
  ```text
  ## Task: Evidence Extraction

  For each <fw.name> (<fw.version>) control below, find and quote the EXACT language from the organization's documents that is relevant to that control. Omit controls for which no relevant language exists.
  <desk_review_context>
  ## Controls
  <_build_controls_text(fw)>

  ## Organization Documents
  <docs_text>

  ## Output Format

  Respond ONLY with valid JSON:

  {
    "evidence": {
      "<id0>": ["Exact quoted text from document...", "Another relevant quote..."]
    }
  }

  Use only the control IDs listed above. Quote verbatim - do not paraphrase.
  ```
  "Omit controls with no relevant language" is deliberately different from DPDPA's "Include ALL requirement IDs": with 93-94 controls and the existing `max_tokens=8192`, listing every id would crowd out the quotes.
- New `_run_framework_evidence_extraction(framework_id, documents, desk_review_findings=None) -> dict | None`:
  - `framework_id == CURATED_PROMPT_FRAMEWORK_ID` → `return _run_evidence_extraction(documents, desk_review_findings)` (unchanged DPDPA call).
  - Otherwise, in a `try`: `_call_llm(tier="extract", max_tokens=8192, temperature=0, system=f"You are a document analyst. Extract exact quotes from documents that are relevant to each {fw.name} control. Be precise and quote verbatim.", messages=[{"role": "user", "content": build_framework_evidence_extraction_prompt(...)}])` → `_parse_json_response` → `_ground_evidence_quotes(parsed.get("evidence", {}), documents)` → keep only keys in the framework's control ids → `logger.info(f"Evidence extraction ({framework_id}): found quotes for {n} controls")` → return. On any exception: `logger.warning(f"Evidence extraction failed for {framework_id}, falling back to documents: {e}")`, return `None`. This is the same optional-call contract as today.
- New `_collect_framework_evidence(framework_ids, documents, desk_review_data) -> dict | None`: if `not documents` → `None`. Otherwise, for each `fw_id` in order: `control_ids` = that framework's control ids. `dr = {k: v for k, v in (_evidence_from_desk_review(desk_review_data) or {}).items() if k in control_ids}`. If `dr` is non-empty → `evidence.update(dr)`, `logger.info(f"Reusing desk review evidence for {fw_id} ({len(dr)} controls)")`, next framework. Else `fw_findings = [f for f in (desk_review_data or {}).get("findings", []) if f.get("requirement_id") in control_ids]`, `extracted = _run_framework_evidence_extraction(fw_id, documents, fw_findings or None)`, and `evidence.update(extracted)` if it is truthy. Return `evidence or None`.
- In `run_multi_framework_analysis`, step 1 (the `evidence = None / if truncated_docs: …` block) becomes `evidence = _collect_framework_evidence(framework_ids, truncated_docs, desk_review_data)`. Nothing else in the function changes. An extraction failure is **not** a framework failure: that framework's prompt falls back to raw documents, exactly as `build_framework_user_prompt` already does when `fw_evidence` is empty.
- **Behaviour on the old path:** a DPDPA + ISO assessment whose desk review predates P5-3 reuses the DPDPA desk-review evidence for DPDPA (as today) and now makes one ISO extraction call (today it made none, and ISO got raw text).

### D-P5-3-L. Pre-fill from desk review runs only where its rows can be rendered (D-P5-C), and never duplicates a row

In `app/services/auto_answer.py::persist_document_answers`:
- Right after the assessment lookup: `if assessment.frameworks != ["dpdpa"]: logger.info("Auto-answer: skipped for %s, pre-fill is keyed to the DPDPA-only questionnaire", assessment_id); return 0`. **Rule:** document pre-fill writes `QuestionnaireResponse` rows keyed by DPDPA requirement ids, and only the DPDPA-only questionnaire (`question_engine`'s `is_dpdpa_only` branch) renders rows keyed that way. Mixed assessments are included in the gate: their questionnaire is cluster-keyed, so a DPDPA-keyed pre-fill there is a row no human can confirm. **P5-4 owns cluster-keyed pre-fill.** It may widen this gate, but only to rows its questionnaire renders, and only with `answer_source="document"` (D-P5-1-D, no new confirmation state).
- Findings: `scoped_findings(db, assessment, framework_ids=["dpdpa"])` instead of the unfiltered query. Coverage: filtered to DPDPA control ids.
- **Existing-row rule** (replacing the `in ("human", "human_override", "document_confirmed")` skip and the `else` add): if a row exists for `req_id` and its `answer_source == "document"` → update it as today. If a row exists with **any other** source (including `NULL`, which is a legacy human answer per D-P5-1-D, and `"inferred"`) → skip it. If none exists → add, as today. This closes the duplicate-row path. It never overwrites or downgrades a confirmed answer, and it never creates a second unconfirmed row beside an existing one.
- `answer_source="document"` is unchanged. It is already in `UNCONFIRMED_ANSWER_SOURCES`, so every row this writes is excluded from analysis and gates until a human confirms it (D-P5-1-D, inherited).
- Update the module docstring's `"inferred"` line to `"inferred" → pre-filled from domain screening (DPDPA-only), awaiting confirmation`, and add one line: `Pre-fill runs only on DPDPA-only assessments (P5-3 D-P5-3-L).`

### D-P5-3-M. Screening runs only on DPDPA-only assessments

In `app/services/screening.py`:
```python
SCREENING_NOT_APPLICABLE_MESSAGE = (
    "Domain screening covers DPDPA requirements only, so it runs only on DPDPA-only assessments. "
    "Answer the questionnaire for this assessment directly."
)

class ScreeningNotApplicable(ValueError):
    """Raised before any LLM call when screening cannot pre-fill this assessment's questionnaire."""
```
- `run_screening_pass`: right after the `Assessment not found` check, `if assessment.frameworks != ["dpdpa"]: raise ScreeningNotApplicable(SCREENING_NOT_APPLICABLE_MESSAGE)`. Nothing is called, written or committed: `screening_results`, `screening_status` and `questionnaire_responses` are untouched.
- **Why the same predicate as D-P5-3-L, including mixed assessments:** `_parse_inferences` keys every inference by DPDPA requirement id, and only the DPDPA-only questionnaire renders those ids. The plan's minimum ("never writes DPDPA-keyed rows into an assessment without DPDPA") is implied by this rule. The stricter form also stops writing rows into a mixed assessment that no one can confirm. **P5-4 decides** whether screening applies to the DPDPA members of a mixed assessment, and corrects the screening copy (plan P5-4 scope). It may widen this gate.
- **Web:** `web.submit_screening` needs **no change**. Its existing `except Exception as e` renders `partials/screening_form.html` with `error=str(e)`, which shows the message. The `questionnaire_tab.html` screening section and its copy are **not** changed (P5-4 owns them, open question 5).
- The module docstring gains: `Runs only on DPDPA-only assessments (P5-3 D-P5-3-M).`

### D-P5-3-N. Rows already written with DPDPA ids into non-DPDPA assessments: quarantined by reader rule, not migrated or deleted

**Decision: no data-cleanup migration, and no deletion.** It is an application-level quarantine:
- **`DeskReviewFinding`:** after the backfill, pre-P5-3 rows on an ISO-only or NIST-only assessment are `framework_id='dpdpa'`, so D-P5-3-H's reader rule excludes them from every display, prompt and pre-fill. On a mixed assessment they are the DPDPA member's findings, which is correct. The next desk-review run replaces them (it deletes and snapshots into `legacy_history`, as today).
- **`QuestionnaireResponse` `"document"`/`"inferred"` rows keyed by DPDPA ids on a non-DPDPA-only assessment:** after P5-1 they are excluded from analysis and every gate (`confirmed_response_clause`). The cluster-keyed questionnaire never renders them, so nobody can confirm them. After this task nothing writes new ones (D-P5-3-L, D-P5-3-M).
- **Why not delete or retag:** deleting responses is irreversible (the P4-4 class of operation) and gains nothing, because the rows are provably inert. Retagging them to a new source would invent a confirmation state, which D-P5-1-D forbids. They stay as inert history. The one visible leak, `assessment_detail`'s `response_count`, is open question 4 for P5-4 (questionnaire stats).

### D-P5-3-O. What this task does not touch

- `app/frameworks/schema.py` and every file under `app/frameworks/definitions/` (P5-5's lane; D-P5-3-C's slug keys exist to avoid them).
- `build_desk_review_system_prompt`, `build_evidence_extraction_prompt`, `build_desk_review_user_prompt`, `_call_claude_desk_review`, `_run_evidence_extraction`, `run_gap_analysis`.
- The questionnaire builders (`_build_multi_framework_questionnaire`, `_modulate_question`, `_apply_screening`, `_modulate_industry_question`), `tier_engine`, `questionnaire_tab.html`, `screening_form.html`, `documents_tab.html`: P5-4.
- `app/services/workpaper.py`, `retention.py`, `rfi_generator.py`, `analysis_pipeline.py`, `scoring.py`, `review.py`, `reports.py`, `pdf_export.py`, `report_content.py`, `evidence.py`, `citations.py`.
- `scripts/seed_test_companies.py` (and every other script).
- The P5-1 gate, override, sentinel and release logic.
- No new assessment status, no new `answer_source` value, no new `DeskReviewSummary` column.

### D-P5-3-P. Coordination with P5-1, P5-2, P5-4 and P5-5

- **P5-1 (merged before this starts):** this task keeps `confirmed_response_clause()` on every response read that feeds analysis (it adds none), keeps the failed-framework sentinel untouched, and adds no pre-fill source outside `UNCONFIRMED_ANSWER_SOURCES`. The P5-1 files it touches are `analysis.py` (the F3 hunk only), `auto_answer.py` (inside `persist_document_answers` and the docstring only; P5-1's constants and clause are untouched), `web.py` (`desk_review_status_web`, `generate_rfi_web`) and `tests/test_correctness_bundle.py` (one literal).
- **P5-2 (not yet dispatched; its handoff must pre-declare a rule against this one).** Shared files and exact P5-3 regions:
  - `app/routers/analysis.py`: P5-3 changes **only** the desk-review-data block in `trigger_analysis` (F3), which becomes one line. P5-2 must not reintroduce a direct `DeskReviewFinding` query there: any reader it adds uses `load_desk_review_data`/`scoped_findings`.
  - `app/routers/web.py`: P5-3 changes only `desk_review_status_web` and `generate_rfi_web`. If P5-2 retires or reroutes `generate_rfi_web`, P5-2's version wins, keeping the scoping rule.
  - **Alembic:** if P5-2 adds a revision, whichever task merges second rebases its `down_revision` onto the other's head and updates the same head-pinning literals listed in D-P5-3-E. **Two heads must never land on `main`.**
  - If P5-2 lands first, rebase and keep both sides. The hunks are disjoint.
- **P5-4 (blocked by this):** inherits D-P5-3-E (one row per requirement, the `framework_id`/`flag_type` columns), D-P5-3-H (`scoped_findings`, `group_signal_findings`, `load_desk_review_data`, and the quarantine rule), D-P5-3-C (the flag vocabulary per framework), and the gates in D-P5-3-L/M (which it may widen only to rows its questionnaire renders). It must not reintroduce keyword matching on signal text.
- **P5-5 (running in parallel):** P5-5 edits `app/frameworks/schema.py`, `definitions/iso27001.py`, `definitions/nist_csf.py`, `scope_profiler.py`, scope templates and the scope routes in `web.py`. P5-3 touches none of those files except `web.py`, where the functions are disjoint. P5-5's open question 2 (scope answers in the analysis prompt) would touch `app/frameworks/prompts.py`. It is not in this task. If it is later scheduled, it must preserve `build_framework_user_prompt`'s F8 filter.

### D-P5-3-Q. Consistency audit against the standing guards

1. `analysis.py`: no new line containing `overall_score`. One hunk (F3).
2. `scoring.py`, `reports.py`, `pdf_export.py`, `review.py`: zero diff.
3. No `relationship(` in `app/models/`.
4. Templates: no `|safe`, no `CyberAssess`, no `overall_score`. The new banner text has no apostrophe.
5. The desk-review web and JSON routes are already mutating or read routes under P4-4's router-level archive guard. No new route is added.
6. `desk_review.py` no longer contains `req_ids[0]`, and `question_engine.py` no longer contains `content_lower`.

## Required approach

1. **Step 0** checks and pins.
2. `alembic/versions/8b2d5f7e1c34_p5_3_framework_keyed_desk_review_findings.py` and the three model columns (D-P5-3-E). Then the lockstep head literals.
3. `app/services/desk_review_findings.py` (new, D-P5-3-H).
4. `app/dpdpa/prompts.py`: `DESK_REVIEW_FLAG_TYPES` and the F7 `(affects …)` join. Nothing else.
5. `app/frameworks/prompts.py`: `CURATED_PROMPT_FRAMEWORK_ID`, `UNCLASSIFIED_FLAG_TYPE`, `red_flag_key`, `desk_review_flag_types`, `build_framework_desk_review_system_prompt`, `build_framework_evidence_extraction_prompt`, and the F8 filter.
6. `app/services/desk_review.py`: constants, `_call_framework_desk_review`, `_desk_review_call`, `_normalize_result`, `_raw_response`, the `run_desk_review` flow, and `_persist_findings(…, framework_id, …)` (D-P5-3-B/D/F/G).
7. `app/services/claude_analyzer.py`: `_run_framework_evidence_extraction`, `_collect_framework_evidence`, and the step-1 replacement (D-P5-3-K).
8. `app/services/question_engine.py` and `app/dpdpa/industry_questions.py` (D-P5-3-J, F2).
9. `app/services/auto_answer.py` (D-P5-3-L) and `app/services/screening.py` (D-P5-3-M).
10. `app/routers/analysis.py` (F3), `app/routers/desk_review.py` (F10), `app/routers/web.py` (F11, F12), `partials/desk_review_findings.html` (D-P5-3-I).
11. `tests/test_p5_3_framework_desk_review.py` (new). Copy (don't import) the fixture pattern from `tests/test_citations.py` (`_register_frameworks`, `upload_root`, `db_path`/`engine`/`db` on an Alembic-built, FK-enforcing SQLite, `http` with `app.dependency_overrides[get_db]`, `texts`, `_seed_hierarchy`, `_upload`) for desk-review scenarios. Copy the `gate` / `_stub_multi` pattern from `tests/test_analysis_pipeline.py` for analysis scenarios. Patch the seams `desk_review._call_claude_desk_review`, `desk_review._call_framework_desk_review`, `desk_review._call_llm`, `claude_analyzer._call_llm` and `screening._call_llm`. No test may touch `data/dpdpa.db`, the real `uploads/`, or the network.
12. `tasks/todo.md`: tick P5-3 in the existing Phase 5 style with a link to this handoff's Results. Don't edit the phase summary line.

## Key files

| File | Why |
|---|---|
| `alembic/versions/8b2d5f7e1c34_p5_3_framework_keyed_desk_review_findings.py` (new) | D-P5-3-E |
| `app/models/desk_review.py` | Three columns |
| `app/services/desk_review_findings.py` (new) | Scoped reader, grouping, `load_desk_review_data`, failed-framework parse (D-P5-3-H) |
| `app/services/desk_review.py` | Per-framework calls, normalization, writer, summary (D-P5-3-B/D/F/G) |
| `app/frameworks/prompts.py` | Registry-driven desk-review and extraction prompts, flag keys, F8 filter |
| `app/dpdpa/prompts.py` | `DESK_REVIEW_FLAG_TYPES`, F7 join only |
| `app/dpdpa/industry_questions.py` | `deepen_if` vocabulary only |
| `app/services/claude_analyzer.py` | Multi-path evidence (D-P5-3-K) |
| `app/services/question_engine.py` | `_load_desk_review_data` only (D-P5-3-J) |
| `app/services/auto_answer.py`, `app/services/screening.py` | Gates (D-P5-3-L/M) |
| `app/routers/analysis.py`, `app/routers/desk_review.py`, `app/routers/web.py` | F3, F10, F11/F12 |
| `app/templates/partials/desk_review_findings.html` | Banner, multi-id "Related" |
| `tests/test_p5_3_framework_desk_review.py` (new) | The contract |
| `tests/test_retention.py`, `test_alembic_baseline_immutable.py`, `test_startup_invariants.py`, `test_data_integrity.py`, `test_analysis_pipeline.py`, `test_correctness_bundle.py` | Head literals only (D-P5-3-E) |
| `app/frameworks/schema.py`, `app/frameworks/definitions/*`, `app/services/workpaper.py`, `retention.py`, `rfi_generator.py`, `analysis_pipeline.py`, `scoring.py`, `scripts/*`, `tests/test_phase1_prefill.py`, `tests/test_golden_dpdpa.py`, `tests/fixtures/*`, every other test | **Not modified** |

## Non-goals

- No cluster-level deepen, pre-fill or tiers on the UCC questionnaire, and no questionnaire stats (P5-4).
- No screening banks for ISO/NIST, and no change to screening copy or visibility (P5-4, plus the plan's deferred list).
- No `key` field on `RedFlagPattern`, and no change to any framework definition content (open question 1; P5-5's lane).
- No change to the DPDPA desk-review or extraction prompt text, or to the single-path analyzer.
- No parallel LLM calls. Calls are sequential, like the analyzer loop.
- No deletion or retagging of existing responses or findings (D-P5-3-N).
- No fix for `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting`'s intermittent ordering failure. It reproduces on unmodified `main` and is unrelated. Report it if you see it; don't fix it.

## Test scenarios

All in `tests/test_p5_3_framework_desk_review.py`. Each test's docstring starts with `Scenario N:`.

1. **Alembic.**
   - The head is `8b2d5f7e1c34` with `down_revision == "4e8c1a9d2b57"`. The three columns exist, are nullable, and have types String(50), String(100) and String(36).
   - A database upgraded to `4e8c1a9d2b57`, holding one legacy evidence row and one legacy signal row, then upgraded to head: both rows have `framework_id == "dpdpa"`, and `flag_type` and `signal_group_id` are NULL.
   - Downgrade to `4e8c1a9d2b57` succeeds with only those backfilled rows (the columns are gone and the row count is unchanged). It refuses with `"Refusing to downgrade past P5-3 revision 8b2d5f7e1c34"` when any row has `flag_type` set, when any has `signal_group_id` set, and when any has `framework_id = 'iso27001'`.
2. **Registry-driven prompt and flag keys.**
   - `[red_flag_key(rf) for rf in iso.red_flag_patterns]` and the NIST equivalent equal the D-P5-3-C literal lists. Keys are unique per framework for all six registered frameworks, and each is at most 100 characters.
   - `build_framework_desk_review_system_prompt("iso27001")`: 2 blocks; block 0 is the ISO persona; block 1 has `cache_control`; block 1 contains every ISO control id, every ISO pattern name and its `flag_type: "<key>"`, `Include ALL 93 control IDs`, and `"evidence_map": {`; it contains none of `DPDPA`, `Data Protection Board`, `data principal`. The same checks for NIST (94).
   - With `monkeypatch.setattr(iso, "red_flag_patterns", [])`: the prompt contains `This framework defines no red-flag patterns.` and `"signal_flags": []`.
   - `desk_review_flag_types("dpdpa") == DESK_REVIEW_FLAG_TYPES`, and every one of them appears in `build_desk_review_system_prompt()`'s text as `(flag_type: "<x>")`.
   - `build_framework_evidence_extraction_prompt("iso27001", docs)` contains ISO ids, `Omit controls for which no relevant language exists`, and no `DPDPA`.
3. **DPDPA byte identity.**
   - `sha256(json.dumps(build_desk_review_system_prompt(), sort_keys=True))` equals Step 0's pinned `system_sha256`.
   - With `desk_review._call_llm` patched to capture its kwargs, `desk_review._call_claude_desk_review(DOCS, "Acme", "saas")` (Step 0's `DOCS`) gives `analyzer_request_key((), kwargs)` equal to Step 0's `request_key`.
   - `run_desk_review` on a DPDPA-only assessment calls `_call_claude_desk_review` exactly once with keyword args `documents`/`company_name`/`industry`, and never calls `_call_framework_desk_review`.
4. **One call per framework, in order, with normalization.**
   - On a DPDPA + ISO + NIST assessment, with both seams patched: the calls happen in order dpdpa, iso27001, nist_csf, and each non-DPDPA call receives its own `framework_id`.
   - The ISO fake returns an `evidence_map` key `CH2.CONSENT.1` (DPDPA), a signal with `requirement_ids ["ISO.A5.1", "CH2.CONSENT.1", "ISO.A5.1"]`, `flag_type "made_up"`, and a coverage key `NIST.GV.OC.01`. Stored: no ISO-framework row with a DPDPA id; one signal group with `requirement_ids == ["ISO.A5.1"]` and `flag_type == "unclassified"`; coverage without `NIST.GV.OC.01`.
   - Every row has the `framework_id` of the call that produced it. `summary.coverage_summary` is the merge of the three coverages. `document_catalog` is merged by filename (two frameworks both catalog `policy.pdf` → one entry, with the union of `coverage_areas`).
   - `json.loads(summary.raw_ai_response)` has `schema_version == 2` and three `completed` entries.
   - A single-framework run stores that framework's catalog verbatim.
5. **Gap #3: a multi-requirement signal reaches every requirement.** This is the plan's regression, on a DPDPA-only assessment. The DPDPA fake returns a signal with `requirement_ids ["CH2.NOTICE.1", "CH2.CONSENT.1"]`, `flag_type "buried_consent"`, and a blank quote on an uploaded document, plus `coverage_summary {"CH2.CONSENT.1": "adequate"}` and an evidence quote for `CH2.CONSENT.1`.
   - Exactly two signal rows, with the same `signal_group_id`, `flag_type`, `content` and **identical** `citations_json` (a `whole_item` citation that `validate_citations` accepts on each row).
   - `persist_document_answers` does **not** pre-fill `CH2.CONSENT.1`. On `main` it did: assert against the row count.
   - `build_adaptive_questionnaire` marks both `CH2.NOTICE.1` and `CH2.CONSENT.1` as `deepened`, with `Signal detected` in both notes.
   - `load_desk_review_data` has one `signal_flags` entry with `requirement_ids == ["CH2.NOTICE.1", "CH2.CONSENT.1"]`, and two `findings` entries of type `signal`.
   - `analysis_pipeline._desk_review_quality(data, r)` returns 1 red flag for each of the two ids.
   - `app.dpdpa.prompts.build_user_prompt(...)` contains `(affects CH2.NOTICE.1, CH2.CONSENT.1)`.
   - The workpaper (`build_workpaper` or its row helper `_desk_findings`) lists the flag under both requirements.
   - `GET /api/assessments/{id}/desk-review` has `signal_count == 1`, and the signal has `requirement_ids` of both, `flag_type`, and `citations[0]["location_type"] == "whole_item"`.
   - The findings partial shows `Red Flags (1)` and `Related: CH2.NOTICE.1, CH2.CONSENT.1`.
   - On an ISO assessment, a signal spanning `ISO.A5.1` and `ISO.A5.2` appears in `build_framework_user_prompt("iso27001", …)`'s `### Red Flags`.
6. **Failure isolation.**
   - DPDPA + ISO + NIST, with the NIST call raising: `status == "completed"`; DPDPA and ISO findings saved, NIST none; `error_message == DESK_REVIEW_PARTIAL_MESSAGE.format(names=<NIST registry name>)`; `failed_desk_review_frameworks(summary) == ["nist_csf"]`; the partial contains `data-desk-review-failed-frameworks` and the NIST name; the JSON API has `failed_frameworks == ["nist_csf"]`.
   - Every call raising: `status == "error"`, the message is `DESK_REVIEW_ALL_FAILED_MESSAGE` with all three names, zero findings, and `persist_document_answers` is not called (patch it with a sentinel).
   - A DPDPA-only failure: `error_message == str(exc)` (unchanged behaviour).
   - A non-JSON response from the ISO call counts as ISO's failure only.
7. **Keyword retirement and vocabulary.**
   - `inspect.getsource(question_engine)` contains no `content_lower`.
   - On a DPDPA-only assessment with `industry="it_services"` (which `INDUSTRY_BANK_MAP` maps to the `it_saas` bank), a signal row with `flag_type "scope_gap"` and content that does not contain "scope" or "gap" deepens `IND.SAAS.1`.
   - A signal whose content says "GDPR" but whose `flag_type` is `buried_consent` does **not** trigger a `gdpr_copy_paste`-only question.
   - A legacy signal row (`flag_type` NULL) deepens its own base question and no industry question.
   - Every `deepen_if.signal_flags` value across every bank in `app/dpdpa/industry_questions.py` is in `DESK_REVIEW_FLAG_TYPES`.
8. **Multi-path evidence extraction.**
   - `run_multi_framework_analysis` on DPDPA + ISO + NIST with one document, and a `desk_review_data` holding DPDPA evidence only. Patch `claude_analyzer._call_llm` to answer `tier="extract"` calls from a table keyed by the control ids present in the prompt, and `judge`/`synthesize` calls with valid minimal JSON.
   - No DPDPA extraction call is made. One ISO and one NIST extraction call are made, each with `tier == "extract"` and `max_tokens == 8192`. The ISO prompt contains ISO ids and no `DPDPA`.
   - The ISO judge prompt contains `## Extracted Document Evidence` with a grounded ISO quote. An ungrounded quote is dropped. A returned key belonging to NIST is not attributed to ISO.
   - With the ISO extraction raising, the ISO judge prompt contains `## Supporting Documents` (raw fallback), the NIST prompt still has extracted evidence, and ISO is not marked failed.
   - With `documents=[]`, no extraction call is made.
   - `run_gap_analysis` is untouched. `tests/test_golden_dpdpa.py` passes unmodified (assert nothing here; the full suite covers it).
9. **Screening gate.**
   - On ISO-only and on DPDPA + ISO assessments, `run_screening_pass` raises `ScreeningNotApplicable` with exactly `SCREENING_NOT_APPLICABLE_MESSAGE`; `screening._call_llm` is never called; `screening_status`/`screening_results` are unchanged; no `QuestionnaireResponse` rows exist.
   - `POST /assessments/{id}/screening/submit` returns 200 with the message in the body.
   - On a DPDPA-only assessment screening runs as before (stub the LLM) and writes `inferred` rows.
10. **Pre-fill gate and no duplicates.**
    - On DPDPA + ISO and on ISO-only assessments with a completed desk review holding adequate DPDPA-id coverage: `persist_document_answers` returns 0 and writes nothing.
    - On DPDPA-only: pre-fills as today.
    - With an existing `NULL`-source row (set with Core `update`) and an existing `"inferred"` row for two covered ids, no second row is created for either. An existing `"document"` row is updated in place. The row count per `question_id` is never more than 1.
11. **Quarantine (D-P5-3-N).**
    - An ISO-only assessment holding a completed summary with DPDPA coverage, plus legacy DPDPA findings (one `framework_id NULL`, one `'dpdpa'`): `load_desk_review_data` is `None`; the findings partial shows `Red Flags` absent and `0 findings`; the JSON API lists no evidence, absences or signals; `scoped_findings` is empty; after `trigger_analysis` (stub the multi analyzer and capture its kwargs), `desk_review_data is None`.
    - A DPDPA + ISO assessment with a legacy NULL-framework cross-cutting DPDPA signal: `build_framework_user_prompt("iso27001", …)` has no `### Red Flags`, and the DPDPA prompt has it.
12. **Guards (D-P5-3-Q).**
    - `inspect.signature(desk_review._call_claude_desk_review)` has parameters `["documents", "company_name", "industry"]`, and `run_desk_review` has `["assessment_id", "db"]`.
    - `"req_ids[0]" not in inspect.getsource(desk_review)`.
    - No `relationship(` in `app/models/`.
    - `git diff --stat main -- app/frameworks/schema.py app/frameworks/definitions` is empty (run it with `subprocess`, as `test_retention` does for `alembic heads`).
    - `desk_review_findings.py` imports neither `llm_client` nor `app.services.desk_review`.
    - `DeskReviewFinding` has no Python-side default on `framework_id` (`DeskReviewFinding.__table__.c.framework_id.default is None`).

## Done criteria

- `tests/test_p5_3_framework_desk_review.py` passes. `.venv/bin/pytest -q` passes in full: **baseline + N passed, 9 skipped** (state the baseline you measured on the post-P5-1 `main`). Two exceptions are allowed:
  - the fresh-worktree teardown error from `tests/conftest.py::_guard_dev_database_untouched` (reported at `tests/test_workpaper.py::test_smoke_full_assessment_traceability`), and
  - `test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` failing **only** because of uncommitted changes.

  Also report `test_scenario_9`'s ordering flake if it appears.
- `tests/test_golden_dpdpa.py`, `tests/test_citations.py`, `tests/test_evidence_service.py`, `tests/test_remaining_llm_call_sites.py` and `tests/test_phase1_prefill.py` pass **unmodified**.
- `git diff --stat main -- tests/` shows only the new test file plus the D-P5-3-E head-literal files, and `git diff main -- <those files>` shows only revision-literal changes.
- `git diff --stat main` touches only the files in `## Key files` (plus `tasks/todo.md` and this handoff).
- `.venv/bin/alembic heads` prints exactly one head, `8b2d5f7e1c34`.
- **Smoke test** (per the project rule; record the outputs in Results). Use a fresh Alembic-built SQLite DB and the in-process ASGI `TestClient` if a socket bind is refused. Patch `desk_review._call_llm` with a dispatcher that answers from the system prompt's persona (DPDPA / ISO / NIST canned JSON, the ISO one including a two-control signal).
  1. On a DPDPA + ISO + NIST assessment with one uploaded PDF, run `POST /assessments/{id}/run-desk-review`. Paste `SELECT framework_id, finding_type, requirement_id, flag_type, signal_group_id FROM desk_review_findings ORDER BY id`.
  2. Paste `GET /api/assessments/{id}/desk-review` (the `signals` array and `failed_frameworks`).
  3. Re-run with the NIST answer raising. Paste the `desk-review-status` partial's banner text.
  4. On an ISO-only assessment, `POST /assessments/{id}/screening/submit`. Paste the error text and `SELECT COUNT(*) FROM questionnaire_responses WHERE assessment_id = …`.
  5. **Browser check** if a browser is available: the findings panel with the multi-id "Related" line and the failure banner. If none is available, say so. Do not claim it.

## Rollback

- **Code:** `git revert`. The DPDPA-only desk review and keyword guessing come back. New findings rows keep their extra columns, which the reverted model ignores.
- **Schema:** `alembic downgrade 4e8c1a9d2b57` succeeds only while no row holds a `flag_type`, a `signal_group_id` or a non-DPDPA `framework_id` (guarded). Once any post-P5-3 desk review has run, restore the pre-deploy backup (`scripts/restore.py`), or delete that assessment's findings and re-run desk review on the reverted code.
- `raw_ai_response` rows in the v2 shape are inert under the reverted code (nothing reads the column).
- The `industry_questions.py` vocabulary change reverts with the code.

## Open questions (deliberately flagged, not resolved here)

1. **Move DPDPA's curated desk-review content into the registry.** A `key` field on `RedFlagPattern`, DPDPA's seven flag types and its minimisation focus as definition data, and then one generic builder for all frameworks. This is deferred because it would change DPDPA desk review and collide with P5-5's `schema.py` work. Worth doing once P5-5 lands.
2. **Slug-derived flag keys depend on the pattern text.** Rewording a registry pattern changes its key, and stored rows keep the old one. If P5-4 or later keys *behaviour* on specific non-DPDPA flag types (not just "any signal"), add an explicit `key` field first.
3. **Input-token cost.** A three-framework desk review sends the documents three times. If cost matters, the next step is caching the document block (a shared cacheable user-content block), which depends on the unverified OpenRouter cache passthrough (CLAUDE.md gotcha).
4. **Orphaned DPDPA-keyed pre-fills stay counted in `assessment_detail`'s `response_count`** on non-DPDPA-only assessments (D-P5-3-N). P5-4's "questionnaire stats become real" should count confirmed, rendered responses only.
5. **The screening section is still offered on non-DPDPA-only assessments.** It now returns an explanatory message instead of writing rows no one can see. P5-4 decides whether to hide it, scope it to a mixed assessment's DPDPA members, and fix its copy.
6. **A partially failed desk review stays `"completed"`,** with the failure stated in `error_message`, the panel banner and the JSON API (D-P5-3-B). If P5-4's cluster derivation needs to distinguish "no finding" from "framework not reviewed", it should read `failed_desk_review_frameworks` rather than add a status.

## Report back

Append a `## Results` section to this file containing:
- Step 0's outputs (the P5-1 name checks, the head, the two pins).
- The shipped constants and signatures (`CURATED_PROMPT_FRAMEWORK_ID`, `UNCLASSIFIED_FLAG_TYPE`, `DESK_REVIEW_FLAG_TYPES`, `DESK_REVIEW_PARTIAL_MESSAGE`, `DESK_REVIEW_ALL_FAILED_MESSAGE`, `RAW_RESPONSE_SCHEMA_VERSION`, `LEGACY_FINDING_FRAMEWORK_ID`, `SCREENING_NOT_APPLICABLE_MESSAGE`, `ScreeningNotApplicable`, `red_flag_key`, `desk_review_flag_types`, `scoped_findings`, `group_signal_findings`, `load_desk_review_data`, `failed_desk_review_frameworks`, `_run_framework_evidence_extraction`, `_collect_framework_evidence`), copied from the code.
- The Alembic revision as shipped, and every head-literal edit (file:line), flagging any beyond D-P5-3-E's list.
- The F1-F15 table with what you actually changed at each site, and which import you used for F8's legacy constant.
- The rendered ISO desk-review system prompt's first 40 lines, and its Level 4 block.
- `pytest -q` output for the new file and for the full suite, with the baseline you measured, and the scenario-13 note.
- The smoke outputs.
- Anything this document got wrong about the current code. **Name it and stop if it forces a design change. Do not pick an alternative.**

Commits and PRs for this task carry **no** `Co-Authored-By: Claude` trailer and no "Generated with Claude Code" footer. Codex cannot commit (its sandbox refuses to write `.git`). Leave the tree uncommitted, and the reviewing session commits on your behalf.

## Results

Implemented by Codex (`gpt-5.6-sol`, `medium`). It stopped before appending this section because this handoff file did not exist yet in its worktree (uncommitted on `main` when the worktree was created) — it correctly refused to invent a replacement or guess a path, per its own read of the process rules, and left the tree uncommitted for reconciliation. This section is written by the dispatching Claude session from direct inspection of the diff, Codex's own log output, and independent re-verification, in the same style used for P5-8 and P5-1's equivalent cutoffs.

### Corrections Codex found to the task brief (all adopted)

- **`red_flag_patterns` is used, but not by desk review or evidence extraction** — it's already read by the per-framework *analysis* system prompt (`app/frameworks/prompts.py`). The brief's claim that it was wholly unused was wrong; the gap is narrower (desk review/extraction don't use it yet), and this task closes exactly that gap.
- **The keyword re-derivation lived in `_load_desk_review_data`, not `_modulate_question`** as the brief stated.
- **A real singular/plural vocabulary bug**: the LLM's desk-review prompt documents `flag_type: "scope_gap"` (singular), but `question_engine.py`'s keyword-matcher and `industry_questions.py`'s `deepen_if.signal_flags` both used `"scope_gaps"` (plural) — so the only reason they ever connected was the keyword-matching fallback silently bridging a naming mismatch. Fixed by standardizing on the LLM's singular vocabulary everywhere (`app/dpdpa/industry_questions.py`, 4 `deepen_if` lines) and asserting the alignment in a new test (scenario 7).

### Shipped constants and signatures

```python
# app/frameworks/prompts.py
CURATED_PROMPT_FRAMEWORK_ID = "dpdpa"  # keeps its hand-curated desk-review/extraction prompts
UNCLASSIFIED_FLAG_TYPE = "unclassified"

# app/services/desk_review.py
DESK_REVIEW_PARTIAL_MESSAGE = (
    "Desk review failed for {names}. Findings for the other frameworks were saved. "
    "Run desk review again to complete it."
)
DESK_REVIEW_ALL_FAILED_MESSAGE = (
    "Desk review failed for every selected framework ({names}). Run desk review again."
)
RAW_RESPONSE_SCHEMA_VERSION = 2

# app/services/desk_review_findings.py (new module)
LEGACY_FINDING_FRAMEWORK_ID = "dpdpa"

# app/services/screening.py
SCREENING_NOT_APPLICABLE_MESSAGE = (
    "Domain screening covers DPDPA requirements only, so it runs only on DPDPA-only assessments. "
    "Answer the questionnaire for this assessment directly."
)
class ScreeningNotApplicable(ValueError): ...
```

`app/dpdpa/prompts.py::DESK_REVIEW_FLAG_TYPES` (DPDPA's fixed vocabulary, singular forms) and the corresponding registry-driven equivalent in `app/frameworks/prompts.py` (`desk_review_flag_types(framework)`, `red_flag_key(pattern)`) are both present and used by both prompt-builder paths.

### The Alembic revision (as shipped)

`alembic/versions/8b2d5f7e1c34_p5_3_framework_keyed_desk_review_findings.py`, chained from `4e8c1a9d2b57` (verified: `alembic heads` → `8b2d5f7e1c34 (head)`). Adds nullable `framework_id`, `flag_type`, `signal_group_id` to `desk_review_findings`; backfills every pre-existing row to `framework_id='dpdpa'` (the only framework desk review could have produced before this task). The downgrade refuses (raises, doesn't silently drop) if any row holds framework-keyed data added after this revision — same data-loss-guard shape as the P1-2/P1-6 migrations.

**Six test files needed a literal-only Alembic-head edit** (D-P5-3-E's own list, all confirmed as the only changes to each file): `tests/test_alembic_baseline_immutable.py`, `tests/test_analysis_pipeline.py`, `tests/test_correctness_bundle.py`, `tests/test_data_integrity.py`, `tests/test_retention.py`, `tests/test_startup_invariants.py` — each a 1-4 line diff updating a hard-coded head string, nothing else (confirmed by `git diff` on each file).

### Verification (independently re-run by the dispatching Claude session after the handoff-file cutoff)

- **A real bug found and fixed post-Codex**: the new contract test's standing-guard scenario used `subprocess.run(["rg", ...])` to check for a forbidden `relationship(` pattern in `app/models`. `rg` (ripgrep) is not an installed binary on this machine — only a Claude-Code-internal shell alias, invisible to a Python subprocess — so the test failed with `FileNotFoundError`, not a real defect. Fixed by switching to `grep -rnE` (matching every other structural guard in this codebase's test suite, e.g. `test_no_blended_scoring.py`), same intent, same result (returncode 1, no match). This is an environment/tooling fix to the test itself, not a design change — no handoff decision was affected.
- `tests/test_p5_3_framework_desk_review.py`: **12 passed** (all required scenarios present, including the vocabulary-alignment scenario 7 and the standing-guards scenario 12).
- Full suite: **591 passed, 9 skipped, 0 failed** (after commit — see below). Before commit: 2 expected working-tree-guard false positives (`test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` and `test_retention.py::test_scenario_13_only_new_retention_test_file_changes` — both assert `git diff --name-only` is empty against a live uncommitted diff; both are P4-4/P3-x-era "protected surface" guards that only clear once this task's legitimate, handoff-authorized test-file edits are committed, the same idiom already documented for P5-1/P5-5/P5-8). The intermittent `test_scenario_9` ordering flake did not reproduce in this run.
- `git diff --stat main -- app/frameworks/schema.py app/frameworks/definitions`: **empty** — the protected framework-definition files were not touched, per D-P5-3-Q.
- **Smoke test** (from Codex's own run, captured in the dispatch log): a DPDPA + ISO 27001 + NIST CSF assessment's desk-review findings show `framework_id` set correctly per row (`dpdpa`, `iso27001`, `nist_csf`), a two-control ISO signal (`ISO.A5.1`, `ISO.A5.2`) stored as two rows sharing one `signal_group_id` with `flag_type="generic_policy_documents"` — the gap #3 fix, confirmed losslessly grouped rather than truncated to the first requirement. A simulated NIST failure produces the exact partial-failure banner (`DESK_REVIEW_PARTIAL_MESSAGE`) with DPDPA/ISO findings preserved. Screening on a non-DPDPA-only assessment returns `SCREENING_NOT_APPLICABLE_MESSAGE` and writes zero `QuestionnaireResponse` rows (`SMOKE_4_RESPONSE_COUNT 0`).

### Outcome

No deviations beyond the two corrections above (both adopted, not forced design changes) and the `rg`→`grep` test-tooling fix. Ready for adversarial review.
