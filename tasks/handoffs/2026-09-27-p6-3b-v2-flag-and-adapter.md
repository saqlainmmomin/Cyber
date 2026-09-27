# P6-3b: v2 flag, desk-review branch and claim adapter `[AR: parity]`

This task wires the P6-3a grounding library (merged, dormant) into desk review behind a flag:

- **`analysis_pipeline_version`** (`"v1"` default). With `"v2"`, desk review runs Stage 0-1 (`run_stages_0_1`) instead of the v1 desk-review prompts.
- **An adapter** turns verified claims into the same five-key desk-review result v1 produces, so `DeskReviewFinding` rows, the P5-4 pre-fill (DPDPA-only and UCC-cluster), the desk-review UI and the v1 judge keep working unchanged.
- **The claim set is persisted** in `DeskReviewSummary.raw_ai_response` under a new `"claim_set"` key, never in `AnalysisRun` and never under a `"claims"` key.
- **A cheap LLM metadata fallback**, verified against the text, fills document-control fields the regex pass missed.

Flag off, nothing observable changes: v1 prompts, prompt fingerprints, golden DPDPA recordings, persisted rows and raw responses are byte-identical.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`, Part B (Stage 0 metadata, B.3 "Desk review under v2") and Track 1 task P6-3. Relevant decisions: **D-P6-B** (only verified claims are evidence), **D-P6-C** (claims tagged across frameworks as suggestions), **D-P6-E** (v2 behind a flag, v1 default until the P6-5 gate), plus Saqlain's answers Q1-Q6 in `tasks/handoffs/2026-09-26-p6-3-v2-stages-0-1.md` ("Answers", 2026-09-26). House rules: scoring is deterministic, JSON lives in TEXT columns, every LLM call goes through `llm_client` tiers.
**Owner:** Claude designs (this file + contract tests) → Codex implements → Claude runs an adversarial review (`[AR: parity]`, checkpoints below) → PR. Per `tasks/agent-ownership.md`, Phase 6 row "P6-3 v2 claims + grounding".
**Branch / worktree:** `claude/p6-3b-v2-flag-adapter` in `/Users/saqlainmomin/dpdpa-gap-tool-p6-3b`, from `origin/main` @ `e12f61a`. `main` already equals `origin/main`.
**Depends on:** P6-3a (merged: `app/services/grounding/`). **Blocks:** P6-4 (reads the claim set through `load_claim_set`), P6-5 (A/B needs the flag).

> **The contract tests are already written. They are the contract.** `tests/test_p6_3b_v2_flag.py` (20 tests) and `tests/test_p6_3b_metadata_fallback.py` (5 tests) were written by the designer before implementation. Before implementation 23 fail and 2 pass (the two structural guards, which must stay green). The 23 fail only for missing-code reasons: `ModuleNotFoundError` for `app.services.desk_review_v2` / `app.services.grounding.metadata_fallback`, `AttributeError` from `monkeypatch.setattr(settings, <new setting>)`, `KeyError` on `Settings.model_fields`, `TypeError` on `run_stages_0_1(..., max_workers=)`, and assertions on the missing citation path and importer. Your job is to make all 25 pass **without editing either file**. Do not weaken, skip, `xfail`, re-parametrize or delete any test. If you believe a test is wrong, leave it failing and explain in `## Results` which assertion, why, and what you think it should be. You may add your own tests in a separate file (`tests/test_p6_3b_extra.py`).
>
> The designer checked both files against a throwaway reference implementation of this spec (not in the repo; do not try to reproduce it, implement from this spec): all 25 passed three runs in a row; the full suite was **911 passed, 10 skipped, 0 failed** with the reference committed; and 18 targeted mutations each made at least one contract test fail (coverage `adequate` instead of `partial`; absence findings for uncovered requirements; ignoring the precomputed citation; v1 concurrency for v2; claim set stored under `"claims"`; failing every framework on an incomplete set; accepting unlocated metadata; locating metadata in the whole document; dropping screenshot claims; not appending `llm_calls`; sending the whole document to the fallback; ignoring the flag; wrapping Stage 1 in `call_tag(framework_id=...)`; running the fallback on image sources; blank `location`; ignoring `v2_metadata_fallback`; ignoring `max_workers`; building results for failed frameworks).

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, name, signature, setting, default, message constant, key name and data shape below.

> **v1 is additive-only.** The only edits allowed in `app/services/desk_review.py` are the 4-line branch (D-P6-3b-C) and the one citation expression (D-P6-3b-F). Every removed line of that file must lie inside `_persist_findings`' evidence block; `test_scenario_2_desk_review_v1_lines_are_only_added_to` enforces this. Do not refactor, reorder or "share" v1 code with v2. Duplicating the ~50-line persistence tail in `desk_review_v2.py` is intended.

> **Answer-key independence (D-P5-9-C). This is analyzer design, so the rule is absolute.** Do not open, grep, glob, list or read: anything under `validation/`; `tasks/handoffs/*p5-9*`; `docs/plans/2026-09-24-002-*`; `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`; `scripts/validation/**`; `tests/test_validation_harness.py`; any `answer_key.json`; `~/cyberassess-runs/**`. Scope every search to explicit paths (`grep -rn ... app/ tests/test_p6_3b_*.py`), never a bare repo-root search. `tests/test_answer_key_isolation.py` forbids the strings `answer_key`, `validation/companies`, `scripts.validation` and `scripts/validation` anywhere under `app/`.

> **Codex cannot write `.git`.** Do not run `git add`, `git commit`, `git branch`, `git stash` or anything else that writes the repository. The orchestrator commits. Read-only git (`diff`, `status`, `show`, `log`) is fine and the guards use it.

## Goal

1. With `analysis_pipeline_version = "v2"`, `run_desk_review` reads every document in full through `load_source_documents`, calls `run_stages_0_1` once for all in-scope frameworks, and persists the verified claims as ordinary desk-review findings with their exact grounded `text_span` citations.
2. P5-4 pre-fill keeps working from those findings: at most `partially_implemented` / `medium` (Q1), never from absence or signal rows (Q2), with screenshot-derived claims kept and flagged (Q3).
3. The whole claim set is stored for P6-4, which can load it and check freshness.
4. Failures fail closed per framework with a readable message, through the existing error vocabulary.
5. Flag off, v1 is byte-identical.

## Step 0 (before writing code)

1. The worktree exists with `.venv` symlinked and `.env` present; `main` == `origin/main` == `e12f61a`. Do not run `git branch` (Codex cannot write `.git`).
2. Run `.venv/bin/pytest -q -p no:cacheprovider` and record counts in `## Results`. The designer's run with this handoff's test files in place (uncommitted) gave **886 passed** for the pre-existing suite plus the 25 new tests (23 red as described above, 2 green), and one working-tree guard failure: `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes`, which fails whenever any file under `tests/` is modified and uncommitted. It goes green once the orchestrator commits. Before the designer's edits the suite was **886 passed, 10 skipped, 0 failed**. The previously flaky tests (`test_longitudinal_demo.py` scenario 9, `test_workpaper.py` smoke) passed. `tests/test_p5_6_rfi_rebuild.py::test_scenario_10_rendered_artifacts_are_frozen_and_complete` failed once in one of the designer's four full runs and passed in isolation and on the next full run; treat it as intermittent. If any of these flake, note it and move on.
3. Confirm these facts. **If any is false, stop and report.** Line numbers are from `e12f61a`.
   1. `app/services/desk_review.py:55` `run_desk_review(assessment_id, db)`. It raises `ValueError` when there are no documents (`:67-69`), builds `doc_id_by_filename` at `:82`, resets or creates the summary and commits at `:84-109` (`db.refresh(summary)` is `:109`), then truncates to 20,000 words at `:112` and runs the v1 units inside `llm_client.collect_calls()` at `:131` with `max_workers=settings.llm_max_concurrency` at `:164`. Both routes use it: `app/routers/desk_review.py:35` (sync API) and `app/routers/web.py:2541` (background task).
   2. `app/services/desk_review.py:584` `_persist_findings(db, assessment_id, framework_id, result, doc_id_by_filename, sources=())`. The evidence loop re-locates every quote with `cite_quotes(sources, [quote], preferred_filename=...)` at `:599-607`, which returns the **first** occurrence in the document. **Note:** `_persist_findings` lives in `desk_review.py`, not `claude_analyzer.py`.
   3. `app/services/desk_review.py:470` `_raw_response(framework_ids, results, errors, *, llm_calls=None) -> str` writes `{"schema_version": 2, "frameworks": {fid: {"status": "completed", "result": ...} | {"status": "error", "error": ...}}, "llm_calls": [...]}`. `:574` `_merge_document_catalogs(framework_ids, results)`. `:45-51` `DESK_REVIEW_PARTIAL_MESSAGE` and `DESK_REVIEW_ALL_FAILED_MESSAGE`. `:251-260` the non-blocking `persist_document_answers` call after a completed review.
   4. `app/services/grounding/pipeline.py:703` `run_stages_0_1(sources, framework_ids) -> ClaimSet` uses `settings.llm_max_concurrency` for all three `run_bounded` pools (`:781`, `:824`, `:861`) and wraps its calls in its own `llm_client.collect_calls()` (`:777`), so an outer collector never sees them.
   5. `app/services/grounding/claims.py:176` `ClaimSet.affected_framework_ids()`; `:132`/`:136` `to_json`/`from_json` round-trip; `:198` `claim_set_is_current(claim_set, sources, framework_ids)` compares a settings snapshot (`:94` `_setting_snapshot`: the `v2_*` P6-3a settings plus `llm_model_extract`) and the ordered source identities, **not** metadata.
   6. `app/services/grounding/pipeline.py:184` `_source_summaries` stores per-source `metadata = {"method": "regex", "fields": [{name, label, value, start, end, iso_date}]}`. `app/services/grounding/metadata.py` exports `METADATA_FIELD_NAMES`, `_VERSION` and `_date_iso`.
   7. `app/services/llm_client.py:80` `collect_calls()` replaces the collector for its context; `:91-106` `call_tag` only overrides supplied values, so a tag set outside cannot be reset to `None` inside.
   8. `app/services/question_engine.py:42` `CLUSTER_PREFILL_LEVELS = ("adequate", "partial")`; `:223-245` a UCC question is document-pre-filled only when every in-scope member's framework did not fail, its coverage is in those levels, and it has an evidence row with a `text_span` citation (`app/services/desk_review_findings.py:13` `finding_has_grounded_citation`). All-`adequate` gives `fully_implemented`/`high`, otherwise `partially_implemented`/`medium`.
   9. `app/services/auto_answer.py:115` DPDPA-only pre-fill needs coverage `adequate`/`partial` and is suppressed by any signal or absence row for the requirement (`:98-101`).
   10. `app/services/desk_review_findings.py:146` `failed_desk_review_frameworks(summary)` reads `raw_ai_response["frameworks"][fid]["status"] == "error"` when `schema_version == 2`.
   11. `app/services/analysis_pipeline.py:173` and `:456`: the `AnalysisRun` envelope's `"claims"` key holds per-requirement conclusion records. Nothing in this task writes to `AnalysisRun`.
   12. Coverage vocabulary is `adequate | partial | absent | not_covered` (`app/dpdpa/prompts.py:379`, `app/frameworks/prompts.py:251`). Catalog entries have `filename, document_type, coverage_areas, summary` (`app/frameworks/prompts.py:239`).
   13. `app/config.py:47` `llm_max_concurrency: int = 4`; `:56-66` the P6-3a `v2_*` settings, ending with `v2_structured_output`.
   14. `tests/test_p6_1b_framework_batching.py:153` pins the v1 prompt fingerprints; `app/services/grounding/prompts.py:16` `PROMPT_VERSION = "p6-3a.1"`.

## Decisions (made here so they are not relitigated)

### D-P6-3b-A: Module layout and the single-importer rule

| Module | Contents |
|---|---|
| `app/services/desk_review_v2.py` (new) | `run_desk_review_v2`, `claims_to_desk_review_result`, `load_claim_set`, message constants, `_raw_response_v2`, `_incomplete_errors` |
| `app/services/grounding/metadata_fallback.py` (new) | `fill_metadata_gaps`, its prompt, schema, seam and constants (D-P6-3b-H) |
| `app/services/grounding/pipeline.py` | One keyword, `max_workers` (D-P6-3b-D). Nothing else |
| `app/services/desk_review.py` | The branch (C) and the citation expression (F). Nothing else |
| `app/config.py`, `.env.example` | Three settings (B) |

`desk_review_v2.py` is the **only** module outside `app/services/grounding/` that imports the package (scenario 11 asserts the importer list is exactly `["app/services/desk_review_v2.py"]`). It imports at module top:

```python
from app.services.desk_review import (
    DESK_REVIEW_ALL_FAILED_MESSAGE, DESK_REVIEW_PARTIAL_MESSAGE,
    _merge_document_catalogs, _persist_findings, _raw_response,
)
from app.services.grounding import ClaimBudgetExceeded, ClaimSet, load_source_documents, run_stages_0_1
from app.services.grounding.metadata_fallback import fill_metadata_gaps
```

`desk_review.py` imports `desk_review_v2` **lazily inside the branch**, so there is no import cycle. Tests patch `desk_review_v2.run_stages_0_1`, `desk_review_v2.run_desk_review_v2` and `metadata_fallback._call_llm`, so always call them through their module globals, never through a captured reference.

Do not touch `app/services/grounding/{prompts,claims,chunking,batches,schemas,sources,metadata}.py`: `test_scenario_11_p6_3a_prompts_unchanged` requires `git diff main` over them to be empty and `PROMPT_VERSION == "p6-3a.1"`.

### D-P6-3b-B: Settings

Add after `v2_structured_output` in `app/config.py` (import `Literal` from `typing`), each with a short comment, and document them commented out in `.env.example` after `# V2_STRUCTURED_OUTPUT=true`, exactly as `# ANALYSIS_PIPELINE_VERSION=v1`, `# V2_MAX_CONCURRENCY=6`, `# V2_METADATA_FALLBACK=true`. Do not change any existing default. Read settings at call time, never at import time.

| Setting | Type | Default | Meaning |
|---|---|---|---|
| `analysis_pipeline_version` | `Literal["v1", "v2"]` | `"v1"` | Which desk-review pipeline runs. v1 stays default until P6-5 (D-P6-E). An invalid value fails validation |
| `v2_max_concurrency` | `int` | `6` | Worker count for every v2 pool (Q6). `llm_max_concurrency` stays 4 for v1 |
| `v2_metadata_fallback` | `bool` | `True` | Run the LLM metadata fallback (H) after Stage 1 |

In P6-3b the flag changes **desk review only**. Analysis keeps the v1 judge, which reads the adapter's findings (scenario 7c). P6-4 adds the v2 judge.

### D-P6-3b-C: The branch

In `run_desk_review`, immediately after `db.refresh(summary)` (`:109`) and before `truncated = _truncate_documents(documents)`, insert exactly:

```python
    if settings.analysis_pipeline_version == "v2":
        from app.services.desk_review_v2 import run_desk_review_v2

        return run_desk_review_v2(db, assessment, summary, doc_id_by_filename)

```

So the "no documents" `ValueError`, the summary reset (old findings deleted, status `analyzing`) and the `assessment.desk_review_status = "analyzing"` commit are shared, and the v1 code below is untouched. Both routes (fact 1) get v2 through this one branch.

### D-P6-3b-D: Calling Stage 1 (concurrency, collectors, tags)

`run_stages_0_1` gains one keyword-only parameter:

```python
def run_stages_0_1(sources, framework_ids, *, max_workers: int | None = None) -> ClaimSet:
    workers = settings.llm_max_concurrency if max_workers is None else max_workers
```

and passes `max_workers=workers` to all three `run_bounded` calls. The default keeps P6-3a's behaviour (its scenario 13 monkeypatches `llm_max_concurrency`). Document the parameter in the docstring.

`run_desk_review_v2` calls it as `run_stages_0_1(sources, framework_ids, max_workers=settings.v2_max_concurrency)`, where `sources = load_source_documents(db, assessment.id)` (full text: no 20,000-word cap; evidence and legacy documents) and `framework_ids = assessment.frameworks`. It is called **outside any `call_tag` and outside any `collect_calls`**: `call_tag` cannot reset `framework_id` to `None`, so an outer framework tag would mislabel every cross-framework call, and `run_stages_0_1` collects its own records (fact 4). Scenario 3 checks the tags seen at call time.

### D-P6-3b-E: The adapter

```python
COVERAGE_WITH_CLAIMS = "partial"
COVERAGE_WITHOUT_CLAIMS = "not_covered"

def claims_to_desk_review_result(claim_set: ClaimSet, framework_id: str) -> dict:
```

Pure: no DB, no LLM. With `control_ids = [c.id for c in FrameworkRegistry.get(framework_id).all_controls()]` (definition order) and `chunk_by_id` from `claim_set.chunks`, it returns exactly these five keys:

- **`evidence_map`**: `{requirement_id: [item, ...]}` for each ID in `control_ids` order that has at least one verified claim with that ID in `claim.requirement_ids`; IDs without claims are absent. Items follow `claim_set.claims` order. Each item is exactly:
  ```python
  {
      "quote": claim.quote,                      # the raw slice, never model_quote
      "document": claim.filename,
      "location": chunk.heading or f"Part {chunk.ordinal}",
      "citation": claim.citation,                # D-P6-3a span citation; None for legacy sources
      "claim_id": claim.claim_id,
      "statement": claim.statement,
      "kind": claim.kind,
      "support": claim.support,
      "tag_status": claim.tag_status,            # "suggested" (D-P6-C)
      "needs_review": claim.needs_review,
      "derived_from_image": claim.derived_from_image,
  }
  ```
  A claim tagged across frameworks appears under each framework's result (D-P6-C). Screenshot-derived claims are kept (Q3); their `needs_review` is already `True`.
- **`coverage_summary`**: every ID in `control_ids`, in that order, mapped to `"partial"` if it is a key of `evidence_map`, else `"not_covered"` (Q1). Never `adequate` or `absent`.
- **`absence_findings`**: `[]`. **`signal_flags`**: `[]` (Q2). The DPDPA-only pre-fill suppression therefore never fires under v2 until P6-4.
- **`document_catalog`**: one entry per `claim_set.sources` item, in that order (including empty and image sources):
  ```python
  {
      "filename": source["filename"],
      "document_type": source["category"],
      "coverage_areas": [rid for rid in control_ids if rid is tagged on any claim from this source],
      "summary": f"{n} verified claim(s) extracted.",   # n = claims from this source, all frameworks
      "derived_from_image": source["derived_from_image"],
      "metadata": source["metadata"],                    # after the fallback, if it ran
  }
  ```

Do not pass the adapter output through `_normalize_result`; it is already normalised.

### D-P6-3b-F: `_persist_findings` accepts a precomputed citation

Replace only the evidence loop's `citations = (...)` expression with:

```python
            citations = (
                ([item["citation"]] if item["citation"] else [])
                if "citation" in item
                else cite_quotes(sources, [quote], preferred_filename=doc_filename)
                if quote.strip()
                else [
                    whole_item_citation(source)
                    for source in sources
                    if source.filename == doc_filename
                ][:1]
            )
```

An item carrying a `"citation"` key uses it (keeping D-P6-3-I's exact span, which `cite_quotes` would replace with the first occurrence); `None` gives `[]` (legacy sources cannot be cited, D-P2-2-B). Items without the key behave exactly as today, so v1 is unchanged. `cite_quotes` is never called for an item with the key (scenario 6 spies on it). Absence and signal loops are untouched.

### D-P6-3b-G: Persistence (no migration)

`DeskReviewSummary.raw_ai_response` for a v2 run is `_raw_response(...)`'s JSON with two extra top-level keys:

```python
def _raw_response_v2(framework_ids, results, errors, claim_set: ClaimSet | None) -> str:
    payload = json.loads(_raw_response(framework_ids, results, errors,
                                       llm_calls=list(claim_set.llm_calls) if claim_set is not None else []))
    payload["analysis_pipeline_version"] = "v2"
    payload["claim_set"] = json.loads(claim_set.to_json()) if claim_set is not None else None
    return json.dumps(payload)
```

- `schema_version` stays 2 and the `frameworks` map is unchanged, so `failed_desk_review_frameworks` keeps working.
- `llm_calls` equals `claim_set["llm_calls"]`: Stage 1's records plus the fallback's (H appends them to the claim set). All have `framework_id: None`.
- **Never** a top-level `"claims"` key, and nothing written to `AnalysisRun` (fact 11). P6-4 will copy the claims it cites into its own envelope under a new key.
- A v1 run's raw response has neither extra key (scenario 2).
- Findings are persisted with `_persist_findings(db=db, assessment_id=assessment.id, framework_id=fid, result=results[fid], doc_id_by_filename=doc_id_by_filename)` and **no `sources`** argument: every v2 evidence item carries a precomputed citation, so `citable_sources` is not needed.

```python
CLAIM_SET_KEY = "claim_set"
PIPELINE_VERSION = "v2"

def load_claim_set(db: Session, assessment_id: str) -> ClaimSet | None:
    """The stored claim set from this assessment's DeskReviewSummary, or None when
    there is no summary, the raw response is missing or not JSON, or it has no
    dict under "claim_set" (v1 runs and budget/unexpected failures)."""
```

It returns `ClaimSet.from_json(json.dumps(payload["claim_set"]))` regardless of summary status. It does not check freshness; P6-4 calls `claim_set_is_current(claim_set, load_source_documents(db, id), assessment.frameworks)` before use. `claim_set_is_current` deliberately does not include the three new settings: none changes which claims are verified.

### D-P6-3b-H: Metadata LLM fallback (`grounding/metadata_fallback.py`)

```python
METADATA_FALLBACK_MAX_TOKENS = 1024
METADATA_FALLBACK_MAX_VALUE_CHARS = 80
DATE_FIELDS = ("document_date", "effective_date", "review_date", "next_review_date")
METADATA_FALLBACK_SCHEMA = {"name": "metadata_fallback_v1", "schema": {...}}
METADATA_FALLBACK_SYSTEM_PROMPT = "..."   # str constant

def _call_llm(*, tier: str, stream: bool = False, **request) -> dict:
    return llm_client.call_llm(tier, stream=stream, **request)

def build_metadata_fallback_user_prompt(source: SourceDocument, chunk_text: str, missing: Sequence[str]) -> str:
def fill_metadata_gaps(claim_set: ClaimSet, sources: Sequence[SourceDocument], *, max_workers: int | None = None) -> ClaimSet:
```

**Schema** (strict-compatible): `{"type": "object", "additionalProperties": false, "required": ["fields"], "properties": {"fields": {"type": "array", "items": {"type": "object", "additionalProperties": false, "required": ["name", "value"], "properties": {"name": {"type": "string", "enum": [METADATA_FIELD_NAMES...]}, "value": {"type": "string"}}}}}}`.

**System prompt** (constant, plain `str`, no document text): role (find document-control metadata in the opening excerpt of an organisation's document); the untrusted-text rule, worded like P6-3a's; copy each value exactly as written, at most 80 characters, omit fields not stated, never guess or reformat; one line defining the seven fields; the JSON shape; "Respond with JSON only." It must not contain any line matching `^- \S+ \[` (the tests' fake uses that to recognise extraction prompts).

**User prompt**, exactly: `"Find these fields: " + ", ".join(missing) + "\n" + prompts.wrap_untrusted(chunk_text, header_lines=(f"document: {source.filename[:200]}",))`. `missing` is in `METADATA_FIELD_NAMES` order. Reuse `wrap_untrusted` (it neutralises markers and strips newlines from headers); do not add wording to `prompts.py`.

**Which sources.** Walk `claim_set.sources` in order. Skip a source when it is not in `sources` (matched by `source_id`), has no chunk with `ordinal == 1` in `claim_set.chunks` (empty text), or `derived_from_image` is true (its text is a vision-model description, not the document). `missing` = names in `METADATA_FIELD_NAMES` absent from that source's regex fields; skip if empty. Each remaining source is one unit; `position` is its 1-based index among units and `count` the number of units.

**Request.** Per unit: `_call_llm(tier="extract", stream=False, temperature=0, max_tokens=min(settings.llm_max_output_tokens_framework, METADATA_FALLBACK_MAX_TOKENS), system=METADATA_FALLBACK_SYSTEM_PROMPT, messages=[{"role": "user", "content": <user prompt over the FIRST chunk's text only>}], response_schema=METADATA_FALLBACK_SCHEMA)`; omit the `response_schema` key when `settings.v2_structured_output` is false. Each call runs under `llm_client.call_tag(stage="metadata_fallback", batch=f"m{position}/{count}")` (no `framework_id`). All units run in one `run_bounded(..., max_workers=settings.v2_max_concurrency if max_workers is None else max_workers)` inside one `llm_client.collect_calls()`. No retries.

**Parsing and verification** (in the caller thread, unit order):
- Strip code fences, `json.loads`; the top level must be an object with a `fields` list. Otherwise, or if `_call_llm` raised, the unit counts as `failed` and adds nothing. **`fill_metadata_gaps` never raises** for model or transport problems.
- For each proposed item, in model order, count `fields_proposed`, then reject (count `fields_rejected`) when: it is not a dict; `name` is not in this unit's `missing`; `name` was already kept from this response (first wins); `value` is not a string, or `value.strip()` is empty or longer than 80 characters; `citations.locate_excerpt(first_chunk_text, value.strip())` is `None`; or `name == "version"` and the located raw slice does not match `metadata._VERSION`.
- A kept field is the dict `{"name", "label": None, "value": <raw slice source.text[start:end]>, "start", "end", "iso_date": _date_iso(raw) for DATE_FIELDS else None, "method": "llm_verified"}` with `start = chunk.start + s`, `end = chunk.start + e`. Count `fields_verified`.

**Result.** `dataclasses.replace(claim_set, sources=..., metrics=..., llm_calls=...)`:
- A source that gained at least one field gets `metadata = {"method": "regex+llm_verified", "fields": [...]}`: its regex fields each gain `"method": "regex"`, then the new fields, ordered by `METADATA_FIELD_NAMES`. Every other source dict is unchanged (identical object content, no `method` added).
- `metrics = {**claim_set.metrics, "metadata_fallback": {"calls", "failed", "fields_proposed", "fields_verified", "fields_rejected"}}` (all five keys, zeros included; `calls` = units attempted).
- `llm_calls = claim_set.llm_calls + <fallback records sorted by (batch, status)>`.
- `claims`, `rejected`, `failed_units`, `status`, `chunks` and everything else are unchanged. Metadata is never a coverage input.

`run_desk_review_v2` calls `fill_metadata_gaps(claim_set, sources)` only when `settings.v2_metadata_fallback` is true and Stage 1 returned a claim set (including an `incomplete` one). When the setting is false the claim set has no `metadata_fallback` metric and no fallback calls.

### D-P6-3b-I: Failure mapping (fail closed per framework)

Constants in `desk_review_v2.py`, used verbatim:

```python
V2_BUDGET_MESSAGE = (
    "Desk review was not run: the documents need {planned} claim-extraction calls, "
    "above the limit of {cap}. Remove or split documents, or raise v2_max_extraction_calls."
)
V2_FAILED_MESSAGE = "Desk review failed before any framework was reviewed: {error}"
V2_INCOMPLETE_MESSAGE = (
    "Desk review for {name} is incomplete: {count} grounding unit(s) failed "
    "(first error: {error}). Run desk review again."
)
```

`errors: dict[str, str]` is built as follows:

1. `ClaimBudgetExceeded as exc` → every framework gets `V2_BUDGET_MESSAGE.format(planned=exc.planned, cap=exc.cap)`; no claim set; no LLM call was made (P6-3a preflight).
2. Any other `Exception` from `run_stages_0_1` → `logger.exception(...)`, every framework gets `V2_FAILED_MESSAGE.format(error=f"{type(exc).__name__}: {exc}")`; no claim set.
3. A claim set (after the fallback, if enabled) → for each `fid` in `claim_set.affected_framework_ids()`: `units` = failed units whose `requirement_ids` intersect that framework's control IDs, and `errors[fid] = V2_INCOMPLETE_MESSAGE.format(name=FrameworkRegistry.get(fid).name, count=len(units), error=units[0].error)`.

Then `results = {fid: claims_to_desk_review_result(claim_set, fid) for fid in framework_ids if fid not in errors}`, and the v1 rules apply unchanged:
- **No results** → `summary.status = "error"`; `error_message` = the single framework's error when there is one framework, else `DESK_REVIEW_ALL_FAILED_MESSAGE.format(names=<all names, framework order>)`; raw response via `_raw_response_v2`; `assessment.desk_review_status = "error"`; commit; return. No findings.
- **Some results** → persist findings for successful frameworks only; `coverage_summary` merges their coverage in framework order; catalog = the single result's catalog, or `_merge_document_catalogs(successful_ids, results)`; `status = "completed"`; `error_message = DESK_REVIEW_PARTIAL_MESSAGE.format(names=<failed names>)` when any framework failed, else `None`; `completed_at`; `assessment.desk_review_status = "completed"`; commit; then the same non-blocking `persist_document_answers` call as v1 (`:251-260`). A persistence exception maps to `"error"` / `f"Failed to persist findings: {exc}"` exactly as v1 (`:262-267`).

Verified claims from successful units still feed non-affected frameworks (P6-3a D-P6-3-N). An affected framework gets no findings, no coverage and no pre-fills; the UCC engine already treats it as failed (fact 8).

### D-P6-3b-J: Pre-fill semantics under v2 (consequences, no code in the pre-fill path)

- **DPDPA-only:** `partial` coverage → `partially_implemented` / `medium` / `answer_source="document"`; `not_covered` → nothing. No absence or signal rows exist, so the suppression never fires (Q2). A legacy-only claim (no citation) still pre-fills here, because this path is coverage-based, same as v1.
- **UCC:** every in-scope member needs a claim with a grounded `text_span` citation, and the answer is always `partially_implemented` / `medium` because coverage is never `adequate`. Legacy-only claims do not ground a cluster (no citation), same as v1.
- Screenshot-derived claims count toward coverage and pre-fill (Q3: kept, flagged). See Open question 1.

### D-P6-3b-K: Guard updates (designer-owned; already applied, Codex must not edit)

Per the stale-guard convention (targeted `:(exclude)` entries naming the PR, never deleting a guard):
- `tests/test_p6_3a_grounding.py`: `PROTECTED_PATHS` gains `":(exclude)app/services/desk_review.py"` with a comment citing this handoff, and the dormancy scan skips exactly `P6_3B_GROUNDING_IMPORTERS = {"app/services/desk_review_v2.py"}`. Every other protected path and every other importer still fails.
- `tests/test_p6_nist_csf2_alignment.py::test_protected_surface_guard_uses_three_dot_diff`: adds `":(exclude)app/services/desk_review.py"` and `":(exclude)app/services/desk_review_v2.py"` with a P6-3b comment. It already excludes `app/config.py` and `app/services/grounding`.
- The P6-3b suite adds its own guards: the additive-only diff check on `desk_review.py`, the exact importer list, and the unchanged P6-3a prompt modules.

## Key files

| Path | Change |
|---|---|
| `app/config.py`, `.env.example` | Three settings (B) |
| `app/services/desk_review.py` | The branch (C) and the citation expression (F). Nothing else |
| `app/services/desk_review_v2.py` (new) | A, E, G, I |
| `app/services/grounding/pipeline.py` | `max_workers` keyword (D). Nothing else |
| `app/services/grounding/metadata_fallback.py` (new) | H |
| `tests/test_p6_3b_v2_flag.py`, `tests/test_p6_3b_metadata_fallback.py` (**already written; read-only for you**) | The contract |
| `tests/test_p6_3b_extra.py` (optional, new) | Any extra tests you add |
| `tasks/handoffs/2026-09-27-p6-3b-v2-flag-and-adapter.md` | Append `## Results` only |

## Do not touch

- **The contract tests:** `tests/test_p6_3b_v2_flag.py`, `tests/test_p6_3b_metadata_fallback.py`.
- **P6-3a's contract and guards:** `tests/test_p6_3a_grounding.py`, `tests/test_p6_3a_grounding_review_probes.py`, `tests/grounding_fixtures/**`, `tests/test_p6_nist_csf2_alignment.py` (the designer already made the guard edits in K).
- **v1 prompt text and golden recordings:** `app/dpdpa/**` (including `app/dpdpa/prompts.py`), `app/frameworks/**` (including `app/frameworks/prompts.py`), `tests/fixtures/**` (golden DPDPA recordings), `tests/support/**`, `tests/test_golden_dpdpa.py`, `tests/test_p6_1b_framework_batching.py` (pinned v1 fingerprints).
- **The P6-3a library except the one keyword:** `app/services/grounding/{__init__,prompts,claims,chunking,batches,schemas,sources,metadata}.py`. `PROMPT_VERSION` stays `"p6-3a.1"`.
- `app/services/claude_analyzer.py`, `desk_review_findings.py`, `auto_answer.py`, `question_engine.py`, `llm_client.py`, `parallel.py`, `citations.py`, `evidence.py`, `document_processor.py`, `analysis_pipeline.py`, `scoring.py`, `app/services/__init__.py`.
- `app/models/**`, `app/schemas/**`, `app/routers/**`, `app/templates/**`, `alembic/**`, and every other existing test file.
- `validation/**`, `scripts/validation/**`, and everything in the independence list above.

If you find you need to change any of these, stop and report.

## Non-goals

- The v2 judge, `insufficient_evidence`, criteria, absence/red-flag checks over claims (P6-4). Analysis keeps the v1 judge.
- Grouping claims by span, reducing `no_valid_requirement` waste (P6-3a smoke follow-ups): note, do not fix.
- Lifting the 5,000-word upload cap (Q4, separate task with P6-4). NFKC folding (Q5: no).
- Flipping the default (P6-5). Any UI, template, report or PDF change. A migration.

## Test scenarios (implemented in the two contract files)

How the suites fake the LLM: `FakeProvider` replaces `llm_client._client`, so the real `call_llm`, the real P6-3a pipeline and real call records run. It classifies a call as **support** when the user prompt has a `[cN]` / `statement:` block, **extraction** when the system prompt has `- <id> [` lines, and **metadata** otherwise. Extraction returns every tagged invented sentence found in the excerpt (text between `----` and the end marker), tagged with those of its IDs the batch shows; support answers `yes`; metadata answers a scripted object or `{"fields": []}`. DB tests use a `create_all` SQLite database and write `Evidence`/`EvidenceVersion`/`AssessmentDocument` rows directly.

1. **Settings.** Defaults `v1`, `6`, `True`; `llm_max_concurrency` default stays 4; `Settings(analysis_pipeline_version="v3")` raises; `.env.example` documents the three.
2. **Flag-off parity.** (a) With the flag at its default and then explicitly `"v1"`, a v1 desk review (curated seam faked) gives identical raw responses, finding rows and coverage (including v1's uncapped `adequate`/`absent`); `run_desk_review_v2` and `run_stages_0_1` are never reached; no provider call; v1's pool gets `llm_max_concurrency`; no `claim_set` / `analysis_pipeline_version` keys. (b) Every removed line of `desk_review.py` vs `main` lies inside `_persist_findings`' evidence block.
3. **Branch inputs.** With the flag `v2`: v1 seams are never called; `run_stages_0_1` is called once with `load_source_documents(...)` (a >20,000-word document arrives untruncated, a legacy document is included), `framework_ids == assessment.frameworks`, `max_workers == settings.v2_max_concurrency`, and no `framework_id` tag active.
4. **Persistence.** Raw response has `schema_version 2`, both frameworks `completed`, `analysis_pipeline_version "v2"`, a `claim_set` that round-trips and equals `load_claim_set(...)`, is `complete`, holds the three quotes and passes `claim_set_is_current`; no `"claims"` key; no `AnalysisRun` rows; `llm_calls == claim_set.llm_calls`, with 8 extraction, the support calls and 1 `metadata_fallback` record, all `framework_id None`. `load_claim_set` is `None` for an assessment without a review and after a v1 run.
5. **Adapter.** Over evidence, legacy, screenshot and empty sources with DPDPA + ISO: exact five keys; `absence_findings`/`signal_flags` empty; coverage lists every control in order, `partial` iff tagged, else `not_covered`; evidence keys in control order; every item field as in E; catalog per source; a cross-framework claim appears under both frameworks; legacy items have `citation None`; the screenshot claim is present with `derived_from_image` and `needs_review`. No claims → all `not_covered`, empty `evidence_map`.
6. **Precomputed citation.** `_persist_findings` stores the given span citation verbatim, stores `[]` for `citation: None`, and calls `cite_quotes` only for the item without the key.
7. **Pre-fill.** (a) DPDPA-only: one grounded evidence row whose citation slices the stored text exactly; coverage `partial`/`not_covered` only; no absence rows; exactly one response `CH2.CONSENT.1 / partially_implemented / medium / document`; the questionnaire shows it pre-filled. (b) UCC: `CLUSTER_002` (members `CH4.SDF.1`, `ISO.A5.2`) is pre-filled `partially_implemented`/`medium`/`document` and persisted; no `fully_implemented` anywhere; with only one member evidenced it stays `active` with the evidence note and `ISO.A5.2` is `not_covered`. (c) The v1 judge's `_evidence_from_desk_review(load_desk_review_data(...))` returns the claim quotes per requirement.
8. **Failures.** (a) Extraction parse failures in the ISO-only batches → claim set `incomplete`, affected `("iso27001",)`, summary `completed` with `DESK_REVIEW_PARTIAL_MESSAGE`, `failed_desk_review_frameworks == ["iso27001"]`, ISO's entry is `V2_INCOMPLETE_MESSAGE` with the unit count and `parse_failure`, findings and coverage are DPDPA-only. (b) Every unit raises → `error`, the single framework's `V2_INCOMPLETE_MESSAGE` (first error `RuntimeError: ...`), no findings. (c) Budget → `error`, `DESK_REVIEW_ALL_FAILED_MESSAGE`, each framework's `V2_BUDGET_MESSAGE.format(planned=8, cap=1)`, `claim_set None`, `llm_calls []`, zero provider calls. (d) An unexpected exception → `V2_FAILED_MESSAGE` with `KeyError: 'programming error'`.
9. **Concurrency.** `run_stages_0_1` passes `llm_max_concurrency` to its pools by default and `max_workers` when given.
10. **Route.** `POST /api/assessments/{id}/desk-review` on an Alembic-`head` database with the flag `v2` returns `completed`, no failed frameworks, two findings; `GET` returns both quotes.
11. **Structure.** The only importer of the package outside it is `app/services/desk_review_v2.py`; `PROMPT_VERSION == "p6-3a.1"` and the P6-3a prompt/claims/chunking/batches/schemas/sources/metadata modules are unchanged vs `main`.
12. **Metadata fallback** (second file). (a) Verified `owner` and `document_date` are added as raw slices with `method "llm_verified"`, `label None`, `iso_date "2025-03-12"`; an unlocated value, an unrequested name, a duplicate name and an 81-character value are rejected; the regex `version` gains `method "regex"`; source method `regex+llm_verified`; metric `{"calls": 1, "failed": 0, "fields_proposed": 6, "fields_verified": 2, "fields_rejected": 4}`; request kwargs as in H; user prompt's first line lists the six missing fields; claims unchanged; one record `("metadata_fallback", None, "m1/1", "extract")` appended after Stage 1's. (b) Only the first chunk is sent, so a value in a later chunk is rejected. (c) Image and empty sources are skipped; a raising call and a non-JSON answer count as `failed` and nothing raises; tags `m1/2`, `m2/2`. (d) `response_schema` is omitted when structured output is off; the schema's item is strict. (e) In a v2 desk review the fallback runs when `v2_metadata_fallback` is true (catalog metadata shows it) and makes no call and no metric when false.

## Verification (before reporting done)

1. `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_3b_v2_flag.py tests/test_p6_3b_metadata_fallback.py` must report **25 passed**, with both files unmodified (`git diff --stat -- tests/test_p6_3b_v2_flag.py tests/test_p6_3b_metadata_fallback.py` is empty once the orchestrator has committed them; before that, `git status` shows them untracked and you must not have edited them).
2. **Flag-off parity set**, all unmodified and green: `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_1b_framework_batching.py::test_unbatched_prompt_fingerprints_and_dpdpa_request_shape tests/test_golden_dpdpa.py tests/test_p6_3a_grounding.py tests/test_p6_3a_grounding_review_probes.py tests/test_p5_3_framework_desk_review.py tests/test_p5_4_adaptive_ucc_questionnaire.py tests/test_p6_1_llm_plumbing.py tests/test_citations.py tests/test_answer_key_isolation.py tests/test_phase1_prefill.py`.
3. `git diff -U0 main -- app/services/desk_review.py` shows only the branch insertion and the citation expression. `git diff main --stat -- app/dpdpa app/frameworks tests/fixtures tests/support app/services/grounding/prompts.py` is empty.
4. The full suite: `.venv/bin/pytest -q -p no:cacheprovider`. Expected: everything green except `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes` while `tests/` has uncommitted changes (it goes green after the orchestrator's commit). List any other failure and why.
5. **Live smoke (orchestrator-run; Codex runs it only if `OPENROUTER_KEY` is set and `openrouter.ai` is reachable, and otherwise says so and does not claim it).** Start the app with `ANALYSIS_PIPELINE_VERSION=v2` against a scratch database, create a DPDPA + ISO assessment, upload only `tests/grounding_fixtures/infosec_policy.txt` and `privacy_notice.txt`, and run desk review. Pass: `completed`, findings with `text_span` citations, at least one `CLUSTER_*` pre-fill at `partially_implemented`, `raw_ai_response.claim_set.status == "complete"`, every call `finish_reason == "stop"`, and `metadata_fallback` calls present. Paste the call totals, `metrics.metadata_fallback`, coverage counts per framework and the pre-fill count into `## Results`. Do not use anything under `validation/`.
6. When the orchestrator launches Codex with `codex exec`, stdin must be redirected: `codex exec ... < /dev/null`.

## Adversarial review checkpoints `[AR: parity]` (after Codex, before the PR)

The reviewer follows the same independence rule and scopes every search.

1. **Flag-off parity.** Is any v1 line changed beyond D-P6-3b-C/F? Does the citation expression evaluate exactly as before for items without a `"citation"` key (including an empty quote)? Are v1 fingerprints and golden recordings untouched? Is the flag read at call time?
2. **Grounding preserved.** Can any v2 evidence row carry a citation other than the claim's own span, or a quote other than the raw slice? Is `model_quote` ever persisted? Does any v2 path call `cite_quotes`/`text_span_citation`?
3. **Q1/Q2/Q3.** Can v2 ever produce `adequate`, `absent`, an absence row or a signal row? Are screenshot claims kept with both flags?
4. **Pre-fill.** Walk `question_engine` and `auto_answer` with v2 rows: UCC grounding, failed-framework quarantine, refresh of an existing document pre-fill on re-run, and human answers never overwritten.
5. **Failure mapping.** Is every framework in `affected_framework_ids()` failed with a message? Can an incomplete claim set ever look complete? Is `ClaimBudgetExceeded` distinguished from a crash? Is the summary ever left `analyzing`?
6. **Tags and records.** Is Stage 1 called outside any framework tag? Do all Stage 1 and fallback records reach `raw_ai_response.llm_calls`? Is the record order deterministic?
7. **Metadata fallback.** Is every kept value an exact slice of the first chunk? Can a value from another chunk, an unrequested field or a model-reformatted date get in? Are image sources skipped? Can it raise?
8. **Persistence.** Nothing in `AnalysisRun`; no `"claims"` key; `load_claim_set` tolerates v1 and malformed rows; the envelope round-trips.
9. **Concurrency.** v2 pools use `v2_max_concurrency`; v1 still uses `llm_max_concurrency`; no nested pools.
10. **Independence.** No path under `validation/` or `scripts/validation/` in the diff; no forbidden strings under `app/`.

## Open questions for Saqlain (defaults are in the design; say if you want different)

1. **Screenshot-derived claims and pre-fill.** Q3 keeps them flagged. Under D-P6-3b-J they also count toward `partial` coverage, so a screenshot description alone can pre-fill a question (`partially_implemented`, medium, still awaiting confirmation). Default: allow it. Alternative: exclude `derived_from_image` claims from coverage (they would still appear as evidence).
2. **Metadata fallback cost.** Nearly every document lacks at least one of the seven fields, so the fallback makes about one cheap call per non-image document. Default: on (`v2_metadata_fallback = True`). Alternative: default off until P6-4's currency checks consume the fields.

## Self-review (designer, before dispatch)

1. **`_persist_findings` location.** The brief placed it in `claude_analyzer.py`; it is in `desk_review.py` (fact 2). The citation change is specified there, as one expression, so the additive-only guard can bound it.
2. **Concurrency without breaking P6-3a.** Making the pipeline read `v2_max_concurrency` would have broken P6-3a scenario 13 (it asserts in-flight ≤ the monkeypatched `llm_max_concurrency`). A `max_workers` keyword keeps P6-3a's default and gives v2 its own setting.
3. **Fallback inside or outside Stage 1.** Inside `run_stages_0_1` it would have changed P6-3a's call records, fakes and determinism tests. It runs after, on the returned claim set, and appends its records, so `raw_ai_response.llm_calls` has one source.
4. **Freshness.** Metadata is not part of `claim_set_is_current`, and the new settings are not in the snapshot; neither changes which claims are verified. Stated in G so P6-4 does not add them by accident.
5. **Legacy documents.** Their claims verify but cannot be cited; the adapter carries `citation: None`, `_persist_findings` stores `[]`, and UCC pre-fill ignores them, matching v1.
6. **Guards.** Found a second guard the P6-3b diff trips (`test_p6_nist_csf2_alignment.py` guards `app/services`); added per-PR excludes there too, not only in P6-3a's scenario 17.
7. **Test fragility.** Parity compares finding rows without `evidence_version_id` (it differs per seeded assessment); the route test migrates a fresh database to `head`; the fake never depends on thread order.

## Results

Implemented with no deviations from D-P6-3b-A through D-P6-3b-K.

Files changed:

- `.env.example`
- `app/config.py`
- `app/services/desk_review.py` — only the v2 branch and precomputed-citation expression
- `app/services/desk_review_v2.py` — new adapter, persistence, loader, and failure mapping
- `app/services/grounding/metadata_fallback.py` — new verified metadata fallback
- `app/services/grounding/pipeline.py` — only the keyword-only `max_workers` override
- `tasks/todo.md`

The two P6-3b contract tests and all protected tests/files were left unmodified. No `.git` writes or commits were made.

Verification:

- Step 0 baseline: 888 passed, 10 skipped, 13 failed, 10 errors. The failures/errors were the expected pre-implementation P6-3b missing-code failures.
- Contract tests: 25 passed in 3.80s.
- Flag-off parity, prompt fingerprints, golden DPDPA, P6-3a, P5-3/P5-4, LLM plumbing, citations, isolation, and pre-fill set: 201 passed, 38 warnings in 24.15s.
- Full suite: 911 passed, 10 skipped, 282 warnings in 108.68s. No failures, including the expected dirty-tree retention guard.
- `git diff --check` and changed-file `py_compile` passed; the desk-review diff contains only the allowed branch and citation changes, and protected prompt/fixture/support paths are unchanged.

Deviation: the optional live smoke was not run because the user explicitly prohibited live LLM calls. No live-call result is claimed.

Review-fix round: source loading now maps failures to the v2 error state, metadata fallback is best-effort, and non-dict v1 citation values use quote grounding. Added `tests/test_p6_3b_review_fixes.py` (3 passed); `tests/test_golden_dpdpa.py` passed (8 passed). Contract/full-suite collection remained blocked by the environment's missing `boto3`; no live LLM calls were made.

- Orchestrator amendment: the precomputed-citation branch accepts only a dict or `None` (the contract pins `None` as "no citation, no relocation"); any other v1-model `citation` value (string, list) falls through to `cite_quotes` unchanged.
