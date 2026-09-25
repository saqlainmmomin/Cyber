# P6-1b: Batch large frameworks on the v1 pipeline

This task makes the **current v1 pipeline** complete ISO 27001 and NIST CSF analyses. Today it cannot. Large frameworks get split into deterministic domain/section batches for the desk-review and judge calls. DPDPA behaviour and every golden recording stay as they are. The point is a P5-9 Stage C baseline that means something for ISO and NIST, and a v1 reference that P6-5 can compare v2 against.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`, Track 1, task P6-1b (Part A1 describes the problem). Relevant decisions: **D-P6-E** (v1 stays the default until P5-9 proves v2) and the P5-1 fail-closed contract (`app/schemas/llm_output.py` `IncompleteAssessmentError`).
**Owner:** Claude designs (this file) → Codex implements → Claude reviews. Per `tasks/agent-ownership.md`, the review is required because this changes the analysis call shape that the baseline measures.
**Branch / worktree:** `codex/p6-1b-v1-framework-batching`, from `main`.
**Depends on:** P6-1 (merged, PR #54, `main` @ `b7ddcf7`). The design uses `run_bounded`, `collect_calls`, `call_tag` and the call records.
**Blocks:** the **P5-9 Stage C baseline**. It now runs after P6-1b merges, not after P6-1.
**Runs in parallel with:** P6-2a/P6-2b (criteria content). Their files don't overlap with this task's.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, setting name, default, key name, grouping rule and test scenario below.

> **DPDPA and unbatched frameworks are byte-identical. This is a hard constraint.** Any framework at or under the threshold, and DPDPA's curated desk-review path in every case, must behave exactly as on `main`. That means the same prompts, the same seam kwargs, the same number of calls, no retry and the same result dicts. `tests/fixtures/**`, `tests/support/**` and `app/dpdpa/**` are not touched.

> **Answer-key independence (D-P5-9-C).** Do not open, grep, list or read any of the following:
> - `validation/companies/*/answer_key.json` or any other file under `validation/companies/` (client-visible pack content included)
> - `tasks/handoffs/*p5-9*`
> - `docs/plans/2026-09-24-002-*`
> - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
>
> The only exception is running the harness commands in Verification step 3 (the orchestrator does this), which read the pack as a black box. Batch boundaries come from the framework definitions only, and nothing is tuned toward a planted gap. `tests/test_answer_key_isolation.py` forbids the strings `answer_key`, `validation/companies`, `scripts.validation` and `scripts/validation` anywhere under `app/`, so keep them out of comments and docstrings too.

## Why (live evidence, 2026-09-25)

The P5-9 harness was smoke-run live on the ISO-only example pack. It used real OpenRouter with `deepseek/deepseek-v4-flash` on every text tier.

| Call | Input | Output | `finish_reason` | Latency | Outcome |
|---|---|---|---|---|---|
| ISO desk review (1 call, 93 controls) | — | **15,901** of 16,384 | `stop` | ~491 s | Succeeded, ~500 tokens short of truncation |
| ISO analysis judge (1 call, 93 controls × 12 fields) | 8,051 | **16,384** of 16,384 | `length` | ~169 s | Truncated JSON → parse/`validate_and_filter` failure → `FrameworkAnalysisError` → assessment `error` |

That is about **170 output tokens per control** for both call types. DPDPA (41 controls) fits in one call. ISO (93) and NIST (94) do not. With v1 in this state, ISO and NIST analysis fails outright, so the Stage C baseline and the P6-5 v1→v2 comparison would have nothing to compare for either framework. v2 (P6-3/P6-4) fixes this structurally, but it sits behind a flag and needs weeks. This task gives v1 the minimum change needed to finish.

## Step 0 (before writing code)

1. Create the worktree with `git worktree add ../dpdpa-gap-tool-p6-1b -b codex/p6-1b-v1-framework-batching main`. Symlink `.venv` and copy `.env` into it.
2. Run `.venv/bin/pytest -q`. Record the pass/skip/fail counts and the `main` commit in `## Results`. Three failures are known and pre-existing:
   - `tests/test_remediation_tracking.py::test_scenario_10_engagement_rollup_and_tracker_page` (a hardcoded date)
   - `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_13_structural_guards` (a stale two-dot guard that always fails on `main`)
   - `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting`, which fails about 3 runs in 4 because assessment ordering is nondeterministic. It is being fixed separately.
3. **Record the prompt fingerprints on `main`, before any edit.** Run this and paste the output into `## Results`. Scenario 2 pins these values:
   ```bash
   .venv/bin/python - <<'EOF'
   import hashlib, json
   from app.main import _register_frameworks
   _register_frameworks()
   from app.frameworks import prompts as p
   kw = dict(company_name="Acme", industry="saas", company_size="sme", description="d",
             responses=[{"question_id": "SINGLE.ISO.A5.1", "answer": "yes"}],
             documents=[{"filename": "a.pdf", "category": "other", "text": "t"}],
             context_profile={"risk_tier": "HIGH", "industry_context": "x"},
             evidence={"ISO.A5.1": ["q"], "NIST.GV.OC.01": ["q"], "CH2.CONSENT.1": ["q"]},
             desk_review_summary={"coverage_summary": {"ISO.A5.1": "partial"}, "signal_flags": []},
             applicable_controls=None)
   h = lambda o: hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()
   for fid in ("dpdpa", "iso27001", "nist_csf"):
       print(fid, "system", h(p.build_framework_system_prompt(fid)))
       print(fid, "user", h(p.build_framework_user_prompt(framework_id=fid, **kw)))
       if fid != "dpdpa":
           print(fid, "desk", h(p.build_framework_desk_review_system_prompt(fid)))
   EOF
   ```
   For reference, the designer's run of this snippet on `main` @ `b7ddcf7` printed the values below. If yours differ on an unmodified `main`, stop and report.
   ```
   dpdpa system 3fc4f1c3ff6b62124716f6ca5ef29e1dd39461817d168fa4b047c2bef92e4ea6
   dpdpa user de658c512943c954425ea004165af0dd1cd88ade82f7376ac98d08aa957b3751
   iso27001 system 3c3bad7bd8818c1d5b28730e4462bbf91f2208b1eae32b89459e8e2d698116b3
   iso27001 user 6fe08745ef96857b893c623d0f468d2abca2aa6c3395affc64145807acedfd61
   iso27001 desk 9d2e926bae35b23030085da6e528b03df63c9352006cb0bb8948800a251222b2
   nist_csf system c8ddf65a8220b571733a65298503f3aff65be22ca6c21413216282f982ddf121
   nist_csf user 9fa1ded32cda08bb882873f83bb2d13e1b20a9a1b0fa84c45690569e02bb283f
   nist_csf desk 14705771d2e67febe08ab3a58e022039aea1a4360aef37a0ae0595fa25d414ec
   ```
4. Confirm these facts. **If any is false, stop and report.** The line numbers are from `main` @ `b7ddcf7`.
   1. `app/services/claude_analyzer.py:493-546`: `run_framework(fw_id)` builds the prompts and makes **one** `_call_llm(tier="judge", stream=True, max_tokens=16384, ...)` per framework (L513-520). It validates with `validate_and_filter(parsed, known_ids)` (L525) against the **whole** framework's control IDs.
   2. `claude_analyzer.py:548-564`: `run_bounded(run_framework, framework_ids, max_workers=settings.llm_max_concurrency)`. Any exception becomes the error dict `{"parsed": {"executive_summary": f"Analysis failed: {error}", "assessments": []}, "raw": str(error), "usage": {}, "error": str(error)}`.
   3. `app/schemas/llm_output.py:97-195`: `validate_and_filter` raises `IncompleteAssessmentError` when any known ID is missing (L183-190). It returns only `{"executive_summary", "assessments"}` (L192-195).
   4. `claude_analyzer.py:253-308`: `_run_framework_evidence_extraction` uses `max_tokens=8192` (L273), and its prompt says "Omit controls for which no relevant language exists". Any exception returns `None`, and the judge falls back to documents (L302-308).
   5. `app/services/desk_review.py:116-139`: one `run_bounded` unit per framework, calling `_normalize_result(framework_id, _desk_review_call(...))` under `call_tag(stage="desk_review", framework_id=...)`. `_call_framework_desk_review` (L260-286) uses `max_tokens=16384` and `stream=True`. The curated DPDPA seam `_call_claude_desk_review` (L229-257) uses `max_tokens=16000`.
   6. `app/frameworks/prompts.py`:
      - `build_framework_desk_review_system_prompt` reads `controls[1].id` (L156). A desk-review prompt therefore needs at least 2 controls.
      - `build_framework_system_prompt` states "({ctrl_count} total)" at L374.
      - `build_framework_user_prompt` falls back to raw documents when the framework has no evidence (L501-511) and ends with "Assess this organization against all {fw.name} controls" (L515).
   7. `app/services/llm_client.py:84-96`: `call_tag(*, stage=None, framework_id=None)`. `_record_call` (L99-127) always writes exactly the 11 P6-1 keys. `tests/test_p6_1_llm_plumbing.py:180-192` asserts that exact key set.
   8. `app/routers/analysis.py:563-582`: a framework result containing `"error"` is failed through `analysis_pipeline.fail_runs(..., error_type="FrameworkAnalysisError")`. The consultant message is at L833-838.
   9. Control counts and structure match the batch table in D-P6-1b-B: ISO 93 controls in 4 domains / 14 sections, NIST CSF 94 in 6 domains / 22 sections, DPDPA 41. No ISO or NIST section has more than 25 controls.
   10. `tests/test_golden_dpdpa.py` drives only `run_gap_analysis` (the legacy DPDPA path, `app/dpdpa/prompts.py`), through `tests/support/analyzer_mock.py`. This task does not touch that path.

## Goal

1. ISO 27001 and NIST CSF desk review and analysis complete on v1 with every LLM call ending `finish_reason=stop`.
2. Frameworks at or under the threshold (DPDPA today) are byte-identical to `main`.
3. Incomplete coverage still **fails closed** per framework. Nothing produces a partial report that looks complete.
4. Every batch call is visible in the call records, with its batch identity.

## Decisions (made here so they are not relitigated)

### D-P6-1b-A: Settings and the threshold

Add these to `app/config.py`, and document them commented-out in `.env.example` next to `LLM_MAX_CONCURRENCY`:

| Setting | Type | Default | Meaning |
|---|---|---|---|
| `llm_batch_threshold_controls` | int | `50` | A framework with **more** controls than this is batched in desk review and judge. At or under it, one call, exactly as today |
| `llm_batch_max_controls` | int | `25` | Upper bound on controls per batch (D-P6-1b-B) |

**Why 50.**
- Observed cost is about 170 output tokens per control, for both the judge (16,384 truncated at 93 controls) and desk review (15,901 at 93).
  - 50 controls ≈ 8.5k tokens, about half the 16,384 ceiling. That leaves roughly 2× headroom for a more verbose run or model.
  - DPDPA at 41 ≈ 7k stays a single call, so its behaviour and every recording are untouched.
  - ISO (93) and NIST (94) are well over the threshold.
- Anything between 42 and about 60 would give the same result today. 50 is a round number in that band.

**Why 25.** 25 × 170 ≈ 4.3k output tokens per batch, about 26% of the ceiling. It is small enough that a truncated batch would be surprising. It is large enough that each batch covers one whole Annex A theme or NIST function in most cases, which keeps related controls in the same prompt.

### D-P6-1b-B: Batch plan (new module `app/frameworks/batching.py`)

```python
@dataclass(frozen=True)
class ControlBatch:
    index: int                      # 1-based
    count: int                      # total batches for this framework
    domain_key: str
    section_keys: tuple[str, ...]
    control_ids: tuple[str, ...]    # framework-definition order

    @property
    def label(self) -> str:         # "2/6", used as the call-record tag (D-P6-1b-K)
        return f"{self.index}/{self.count}"

def control_batches(framework_id: str) -> tuple[ControlBatch, ...]:
    """() when the framework has <= settings.llm_batch_threshold_controls controls."""
```

**Grouping algorithm.** It is deterministic, reads nothing but the framework definition, and never looks at assessment data.

1. If `fw.control_count() <= settings.llm_batch_threshold_controls`, return `()`.
2. Walk `fw.domains` in definition order. **Batches never cross a domain boundary.** Inside each domain, walk its `sections` in definition order, keeping a `current` list of controls:
   - A section with more than `M = llm_batch_max_controls` controls is first cut into consecutive chunks of `M`. A trailing chunk of 1 control is merged into the chunk before it. No current section needs this; it is there for robustness.
   - For each chunk, if `current` is non-empty and `len(current) + len(chunk) > M`, emit `current` as a batch and start a new one. Then append the chunk to `current`.
   - At the end of the domain, emit `current`.
3. Any batch with fewer than 2 controls is merged into the batch before it in the same framework. If it is the first batch, it is merged into the one after it. The desk-review prompt needs 2 IDs (fact 6).
4. Number the batches from 1 and set `count`. `section_keys` lists the sections that contributed controls.

**Resulting batch table** (computed against `main`; scenario 3 pins it):

| Framework | Batch | Domain | Sections | Controls | Range |
|---|---|---|---|---|---|
| iso27001 | 1/6 | organizational | policies, threat_intelligence, access_identity, supplier_relations | 23 | ISO.A5.1 .. ISO.A5.23 |
| iso27001 | 2/6 | organizational | incident_continuity, legal_compliance | 14 | ISO.A5.24 .. ISO.A5.37 |
| iso27001 | 3/6 | people | screening_employment, remote_work | 8 | ISO.A6.1 .. ISO.A6.8 |
| iso27001 | 4/6 | physical | perimeter_access, equipment | 14 | ISO.A7.1 .. ISO.A7.14 |
| iso27001 | 5/6 | technological | tech_access, tech_operations, tech_logging | 24 | ISO.A8.1 .. ISO.A8.24 |
| iso27001 | 6/6 | technological | tech_sdlc | 10 | ISO.A8.25 .. ISO.A8.34 |
| nist_csf | 1/6 | govern | gv_oc, gv_rm, gv_rr, gv_po, gv_ov, gv_sc | 23 | NIST.GV.OC.01 .. NIST.GV.SC.05 |
| nist_csf | 2/6 | identify | id_am, id_ra, id_im | 16 | NIST.ID.AM.01 .. NIST.ID.IM.03 |
| nist_csf | 3/6 | protect | pr_aa, pr_at, pr_ds, pr_ps, pr_ir | 22 | NIST.PR.AA.01 .. NIST.PR.IR.04 |
| nist_csf | 4/6 | detect | de_cm, de_ae | 11 | NIST.DE.CM.01 .. NIST.DE.AE.08 |
| nist_csf | 5/6 | respond | rs_ma, rs_an, rs_co, rs_mi | 14 | NIST.RS.MA.01 .. NIST.RS.MI.02 |
| nist_csf | 6/6 | recover | rc_rp, rc_co | 8 | NIST.RC.RP.01 .. NIST.RC.CO.04 |

NIST batches are exactly its six functions. ISO batches follow the four Annex A themes (A.5–A.8), with the two large themes (A.5 has 37 controls, A.8 has 34) split at a section boundary. DPDPA returns `()`.

**Where the module lives.** `app/frameworks/batching.py` is a new file. `app/frameworks/schema.py` and `app/frameworks/definitions/**` are **not** touched, because P5-3's guard pins them (see D-P6-1b-L).

### D-P6-1b-C: Prompt builders gain `control_ids` (omitted means byte-identical)

`app/frameworks/prompts.py`. Each builder gains a keyword-only `control_ids: Sequence[str] | None = None`. When it is `None`, the output is **byte-identical** to `main`; scenario 2 checks this against the Step 0 fingerprints. When it is given, it is a subset of the framework's control IDs, and the builder renders them in **framework-definition order**, whatever order they were passed in.

- **`_build_controls_text(fw, control_ids=None)`** renders only the listed controls.
- **`build_framework_system_prompt(framework_id, *, control_ids=None)`** (judge). Only these parts change:
  - the controls block is scoped
  - the example `requirement_id` is the first scoped control
  - `ctrl_count` is the scoped count, so the line reads "exactly one entry for every control ID listed above (k total)"

  The persona, instructions, output schema, 11 fields and red-flag section stay identical. No new sentence is added.
- **`build_framework_user_prompt(..., control_ids=None)`**. With `scope = set(control_ids)`:
  - `_expand_cluster_responses` still expands against the **framework's** IDs, and the result is then filtered to `scope`.
  - "Scope — Controls Excluded" lists only excluded IDs in `scope`, and the section is omitted when there are none, as today.
  - Desk-review coverage lines are filtered to `scope`. Red flags are included when their `requirement_ids` intersect `scope`, or when they carry no IDs and belong to this framework (today's framework-level rule), so a framework-level flag appears in every batch.
  - Questionnaire responses are filtered to `scope`.
  - **Evidence vs documents is decided at framework level, as today.** If `evidence` has any quote for any of the framework's controls, the prompt is in evidence mode. It renders only the quotes for `scope`. If `scope` has none, it renders the `## Extracted Document Evidence` header followed by the single line `_No extracted quotes for the controls in this batch._`. Otherwise it renders `_documents_section(documents)` as today. This keeps v1's evidence-visibility behaviour (plan A3) the same as unbatched instead of changing it batch by batch.
  - The closing line becomes `Assess this organization against the {k} {fw.name} controls listed in the Controls Reference and provide the structured JSON output.`
- **`build_framework_desk_review_system_prompt(framework_id, *, control_ids=None)`**:
  - the controls block is scoped
  - `n` becomes the scoped count, which covers both "For each control ({n} total)" and "Include ALL {n} control IDs"
  - `id0`/`id1` are the first two scoped controls

  "Assess against {fw.name} only.", the four analysis levels, and the **full** red-flag signal block stay unchanged, so every batch detects signals (merged in D-P6-1b-H).
- `build_framework_evidence_extraction_prompt`, `build_synthesis_prompt` and everything in `app/dpdpa/**` are **not** changed.

### D-P6-1b-D: Judge orchestration (`claude_analyzer._run_multi_framework_analysis`)

**Work units, flattened under one concurrency bound.**

- Build the unit list in `framework_ids` order.
  - An unbatched framework contributes one unit `(fw_id, None)`.
  - A batched framework contributes `(fw_id, batch)` for each batch in index order.
- Run **all** units through a single `run_bounded(..., max_workers=settings.llm_max_concurrency)`. Do not nest `run_bounded` calls: `llm_max_concurrency` stays the true upper bound on concurrent LLM requests.

**Unbatched unit.** Exactly today's `run_framework(fw_id)` body: the same prompts, the same `_call_llm` kwargs, the same `validate_and_filter` (still resolved through the `claude_analyzer` module name, so `tests/test_p6_1_llm_plumbing.py`'s monkeypatch keeps working), `_flag_unsupported_compliant_items`, the same result dict, **no retry**. Its tags are `call_tag(stage="judge", framework_id=fw_id)`.

**Batched unit**, under `call_tag(stage="judge", framework_id=fw_id, batch=batch.label)`:

1. Build `build_framework_system_prompt(fw_id, control_ids=batch.control_ids)` and `build_framework_user_prompt(..., control_ids=batch.control_ids)`, with every other argument exactly as the unbatched call passes it.
2. Call `_call_llm(tier="judge", stream=True, max_tokens=16384, temperature=0, system=..., messages=[...])`. These are the same kwargs as today apart from prompt content.
3. Parse the response with `_parse_json_response`. A parse failure counts as **all of the batch's IDs missing**. It is not an exception.
4. Validate with a new non-raising helper in `app/schemas/llm_output.py`:
   ```python
   def validate_partial(parsed: dict, known_requirement_ids: set[str]) -> tuple[dict, frozenset[str]]:
       """Same per-item filtering, logging and first-wins dedupe as validate_and_filter;
       returns (validated dict, missing ids) instead of raising."""
   ```
   `validate_and_filter` is refactored to call `validate_partial` and raise `IncompleteAssessmentError` with the **same message** when the returned missing set is non-empty. Its behaviour does not change. `known_requirement_ids` is the **batch's** IDs, so an item for a control outside the batch is dropped as unknown, the same way an invented ID is today.
5. The unit returns `(validated, missing, raw_text, usage)`. Exceptions from `_call_llm` (transport failures after the SDK's own retries, or `_require_content`'s empty-content error) propagate unchanged. No retry is added for them (P6-1 D-P6-1-A).

**Merge (per batched framework, in the caller thread, after the retry pass in D-P6-1b-E).**

- `assessments` holds all surviving items from every batch and every retry, **sorted by the control's index in `fw.all_controls()`**. Then `_flag_unsupported_compliant_items` runs over the merged list.
- `executive_summary` follows D-P6-1b-G.
- `raw` is the batch raw texts, then any retry raw texts, each in batch index order, joined with `"\n\n---\n\n"` (the separator the router already uses for `GapReport.raw_ai_response`).
- `usage` is the four token counters summed over every batch and retry call.
- The framework result dict has the same keys as today (`parsed`, `raw`, `usage`). `total_usage` and the synthesis step are unchanged. Synthesis receives the merged `parsed`.

### D-P6-1b-E: One retry, for missing IDs only

- After the first `run_bounded` pass, every batched unit with a non-empty `missing` set (including a whole batch that failed to parse) gets **exactly one** retry unit covering **only the missing IDs**, in framework order. That means `control_ids=tuple(sorted(missing, key=control_index))` through the same builders, with the same kwargs and tags `call_tag(stage="judge", framework_id=fw_id, batch=f"{batch.label}+retry")`.
- All retry units from all frameworks run in **one** second `run_bounded` pass under the same bound. A retry with only 1 missing ID is valid for the judge prompt, which needs only `controls[0]`.
- Retry results are validated against the missing set with `validate_partial`, and survivors join the merge. Only the retry's `assessments` are used. Its `executive_summary` is ignored.
- Unbatched frameworks never retry. That keeps DPDPA's call count and behaviour identical, including when its single response is incomplete: it still fails exactly as on `main`.

### D-P6-1b-F: Failure semantics: the whole framework fails closed

If a batched framework has any control still missing after its retry, **or** any of its units (first pass or retry) raised, **the whole framework fails**. It goes through today's error dict, with the same four keys and shape (fact 2). `error` is the first failure in batch index order, formatted as:

- missing: `f"Gap analysis for {fw.name} is incomplete after one retry: batch {label} is missing {n} control(s): {sorted(ids)[:10]}"`, with `…` appended when there are more than 10
- exception: `f"Gap analysis for {fw.name} failed in batch {label}: {exc}"`

**What the consultant sees** is exactly what they see today for a failed framework:
- The framework's `AnalysisRun` is `failed` with `error_type="FrameworkAnalysisError"`, and its envelope still carries all its `llm_calls`, batch-tagged, so the failure can be diagnosed.
- The framework is scored `failed_framework_scores()` (P5-1).
- If other frameworks succeeded, the response and assessment show "Analysis failed for ISO 27001. Results for the other frameworks were saved. Run analysis again to complete the assessment." (`app/routers/analysis.py:833-838`).
- If every framework failed, the assessment is `error`.

**Why not mark only the missing controls `not_assessed` + `analysis_incomplete`.**
- v1 has no "analysis incomplete" state anywhere downstream.
- `not_assessed` maps to the `insufficient_evidence` outcome (`analysis_pipeline.OUTCOME_BY_STATUS`), which scoring excludes from the denominator (`scoring.DENOMINATOR_EXCLUDED_OUTCOMES`). So a report missing a whole batch would score as complete over the survivors. `IncompleteAssessmentError`'s docstring forbids exactly that ("incomplete coverage fails closed rather than yielding a misleading complete report").
- Per-requirement survival with an explicit `analysis_incomplete` flag belongs in v2 (plan Part B Stage 2, P6-4), where `insufficient_evidence` is a first-class outcome that consultants see and review.
- The cost is some wasted tokens when one batch fails twice. The retry makes that rare.

### D-P6-1b-G: Executive summary for a batched framework: deterministic, no extra call

The per-batch `executive_summary` strings are discarded (they stay in `raw`). The framework's `parsed["executive_summary"]` is built in code:

```
"{fw.name} ({fw.version}): AI-proposed outcomes for {total} controls, assessed in {b} batches: "
"{c} compliant, {p} partially compliant, {nc} non-compliant, {na} not assessed, {nap} not applicable. "
"All outcomes are proposals pending consultant review."
```

- The counts come from the merged assessments after applying the router's scope rule. When `applicable_controls` is truthy, any control not in it counts as `not_applicable` (the same truthiness test as `app/routers/analysis.py`'s server-side scope enforcement). This way the sentence matches what gets persisted.
- The analyzer does **not** mutate the items. The router still enforces scope.
- The text is ASCII only, with no em dashes, because the legacy PDF prints this field through `S()`.

**Why not a follow-up LLM call or joined batch summaries.**
- Client-facing summaries are already deterministic and built from approved Conclusions (`app/services/approved_report.py::_summary_text`). Narrative is P6-10's job, from approved Findings (D-P6-F).
- Multi-framework assessments still get an LLM narrative from the existing synthesis call, which receives this sentence plus its own stats.
- Six joined slice summaries would be long, repetitive and cut off at 600 characters by the legacy PDF.
- An extra `synthesize` call would add a new prompt, a new failure mode and a new cost line for a field that is on its way out. It is also a number-free narrative that nobody reviews.

### D-P6-1b-H: Desk-review batching (`app/services/desk_review.py`)

**When.** Only for a framework where `framework_id != CURATED_PROMPT_FRAMEWORK_ID` **and** `control_batches(framework_id)` is non-empty. DPDPA's curated path is never batched, whatever the threshold (its prompt has no subset support). Neither is any framework at or under the threshold.

**Units.** These mirror D-P6-1b-D: `(framework_id, None)` or `(framework_id, batch)`, in `framework_ids` then batch order, through **one** `run_bounded` with `llm_max_concurrency`.
- Unbatched unit: exactly today's `_normalize_result(framework_id, _desk_review_call(...))`.
- Batched unit, under `call_tag(stage="desk_review", framework_id=..., batch=batch.label)`:
  - It calls `_call_framework_desk_review(framework_id, documents, company_name, industry, control_ids=batch.control_ids)`, which gains `control_ids=None` and passes it to `build_framework_desk_review_system_prompt`. The user prompt (`build_desk_review_user_prompt`, the same documents) is unchanged.
  - It then calls `_normalize_result(framework_id, result, control_ids=batch.control_ids)`, which gains a `control_ids=None` keyword. When given, it is the valid-ID set instead of the whole framework's IDs, so out-of-batch IDs are dropped and counted, like unknown IDs today.
  - Pass `control_ids=` **only** for batched units, so existing test patches with the old signatures keep working for unbatched frameworks.
- Worker threads still never touch `db`.

**No retry in desk review.** Desk review has no completeness contract today: a missing `coverage_summary` entry is not an error. A batched unit that raises, including on a parse failure, **fails that framework's desk review**:
- `errors[framework_id] = f"Desk review for {fw.name} failed in batch {label}: {exc}"`, using the first failure in batch order
- the other batches' results for that framework are discarded

This matches today's per-framework contract. The partial or all-failed messages and statuses are unchanged.

**Merge** (new `_merge_batch_results(results: list[dict]) -> dict`, in batch order). The output has the same five keys `_normalize_result` returns, so `_persist_findings`, `merged_coverage` and `_raw_response` need no change:

| Key | Merge rule |
|---|---|
| `document_catalog` | Merged by filename. The first batch's entry wins for `document_type`/`summary`, and `coverage_areas` is the ordered union. Factor the body of `_merge_document_catalogs` into `_merge_catalog_lists(lists: list[list[dict]]) -> list[dict]` and have `_merge_document_catalogs` call it, so its behaviour is unchanged |
| `evidence_map` | Dict union in batch order. Keys are disjoint because each batch is filtered to its own IDs |
| `absence_findings` | Concatenated in batch order. Entries **without** a `requirement_id` are deduplicated by exact dict equality, keeping the first |
| `signal_flags` | Deduplicated on `(flag_type, document, normalised source_quote)`, where normalised means lowercased with whitespace collapsed. The first occurrence wins for every field except `requirement_ids`, which becomes the ordered union |
| `coverage_summary` | Dict union in batch order |

**Raw response.** `raw_ai_response` keeps `RAW_RESPONSE_SCHEMA_VERSION = 2` and its shape: `frameworks[fid] = {"status": "completed", "result": <merged>}` or `{"status": "error", "error": ...}`, plus the top-level `llm_calls`, whose records now carry `batch` for batched units. No new keys.

**Cost (state this in the PR).** Every batch re-sends the same documents.
- **Input.** ISO and NIST desk-review input is about **6×** today's. Documents are capped at `max_total_document_words = 20,000` words (about 27k tokens), so the worst case is about 6 × (27k + a smaller system prompt) ≈ 170–180k input tokens per framework, against about 30k today.
- **Output.** Output is roughly unchanged in total, about 16k split into six calls of about 4k each.
- **Wall-clock time.** At about 32 tokens/s (15,901 tokens in about 491 s), six batches at concurrency 4 run in two waves of about 130 s. That is roughly **260 s instead of 491 s** per framework.
- **Report the real numbers.** Codex reports the actual before/after input and output tokens from `llm_calls` in `## Results` (Verification step 3).
- **Caching.** Provider prompt caching (`cache_read_input_tokens`) is unverified on OpenRouter, so no saving from it is assumed.
- **Longer term.** v2 (B.3) removes this multiplication: desk review becomes a view over one shared document read.

### D-P6-1b-I: Evidence extraction is not batched

`_run_framework_evidence_extraction` is left as it is:

- **It fails soft.** Any failure, including a truncated `max_tokens=8192` response, returns `None` and the judge falls back to documents (fact 4). It never fails an analysis.
- **Its output is sparse.** The prompt says to omit controls with no relevant language, so output grows with the quotes found, not with the control count.
- **It rarely runs.** `_collect_framework_evidence` reuses desk-review evidence for any framework where desk review found a quote. In the harness flow desk review always runs first, so extraction is skipped for ISO and NIST whenever their (now batched) desk review found anything.

**Cost of the fallback.** When extraction does run and fails, each judge batch gets the full documents, so judge input is about 6 × 27k. That is acceptable for the baseline, and it shows up in `llm_calls`. The live smoke in Verification step 3 must report whether extraction ran and what its `finish_reason` was. If it is `length`, report it and do not fix it here.

### D-P6-1b-J: `max_tokens` per batch call

| Call | max_tokens | Why |
|---|---|---|
| Judge batch and judge retry | `16384` (the existing literal) | About 4.3k expected for 25 controls, so roughly 3.8× headroom. Keeping the same number keeps seam kwargs identical in form to the unbatched call. A lower cap buys nothing: providers bill tokens produced, not the cap |
| Desk-review batch | `16384` (the existing literal in `_call_framework_desk_review`) | Same reasoning, about 4k expected |
| Curated DPDPA desk review, evidence extraction, synthesis | unchanged (`16000`, `8192`, `4096`) | Not in scope |

`llm_batch_max_controls` is the lever if a model is ever more verbose, not `max_tokens`.

### D-P6-1b-K: Observability: an optional `batch` tag

`app/services/llm_client.py`:

- `call_tag(*, stage=None, framework_id=None, batch: str | None = None)`. Nested merge works as today, with inner values winning.
- `_record_call` adds a `"batch"` key **only when a batch tag is set**. Records made without one keep exactly the 11 P6-1 keys, so every DPDPA and unbatched record is byte-identical and `tests/test_p6_1_llm_plumbing.py:180-192` stays valid.
- Readers use `record.get("batch")`.
- Values are `"i/n"` for a first-pass batch and `"i/n+retry"` for its retry.
- Document the optional key in the `_record_call` docstring and the module docstring.
- `_attach_llm_calls` needs no change: batch records carry `framework_id`, so they land in their own framework's `llm_calls`.

### D-P6-1b-L: Existing tests and protected-surface guards

- **Existing tests that mock one call per ISO/NIST framework.** Some existing tests drive ISO or NIST desk review or analysis through a patched seam and assume one call per framework, for example by returning one canned full-framework response keyed on the system prompt. Many will pass unchanged, because each batch filters a full canned response down to its own IDs. For any that fail **only** because of batching, you are authorised to make exactly one change: pin the v1 unbatched shape with
  ```python
  monkeypatch.setattr(settings, "llm_batch_threshold_controls", 10_000)  # P6-1b: pins the unbatched call shape this test characterises (D-P6-1b-L)
  ```
  Put it in that test or its fixture, with **no assertion changes**. List every file and test you pinned in `## Results`. If an existing test fails for any other reason, stop and report.
- **`tests/test_p6_1_llm_plumbing.py::test_multi_framework_analysis_is_ordered_equivalent_and_concurrent`** (scenario 7 of P6-1) and its `_run_multi` helper are pre-authorised for that pin, since they key canned responses on full-framework system prompts.
- **Guards.**
  - `tests/test_p5_3_framework_desk_review.py:806-834` (definitions and `schema.py`) must keep passing. That is why the batch module is new and `schema.py` is untouched.
  - `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_13_structural_guards` already fails on `main`, and also pins `app/frameworks` with a two-dot diff. Leave it untouched and list it as pre-existing.
  - `tests/test_longitudinal_demo.py::test_scenario_13` protects files this task does not touch.
  - `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes` compares the working tree, so it passes once your test edits are committed. Commit before the final full-suite run.
- **Any new guard you add must use the three-dot form** `git diff main...HEAD`, so it does not go stale after merge.

## Key files

| Path | Change |
|---|---|
| `app/config.py`, `.env.example` | Two settings (D-P6-1b-A) |
| `app/frameworks/batching.py` (new) | `ControlBatch`, `control_batches` (D-P6-1b-B) |
| `app/frameworks/prompts.py` | `control_ids` on `_build_controls_text` and the three builders (D-P6-1b-C) |
| `app/schemas/llm_output.py` | `validate_partial`; `validate_and_filter` delegates to it with identical behaviour (D-P6-1b-D) |
| `app/services/claude_analyzer.py` | Unit flattening, batched judge, retry, merge, deterministic summary (D-P6-1b-D to G) |
| `app/services/desk_review.py` | Batched units, `control_ids` on `_call_framework_desk_review`/`_normalize_result`, `_merge_batch_results`, `_merge_catalog_lists` (D-P6-1b-H) |
| `app/services/llm_client.py` | Optional `batch` tag (D-P6-1b-K) |
| `tests/test_p6_1b_framework_batching.py` (new) | All scenarios below |

**Do not touch:**
- `app/dpdpa/**`, `app/frameworks/schema.py`, `app/frameworks/definitions/**`
- `app/services/scoring.py`, `app/services/analysis_pipeline.py`, `app/routers/analysis.py`. The router already handles the error dict and the call records. If you find it must change, stop and report.
- `tests/fixtures/**`, `tests/support/**`
- `validation/**`, `scripts/validation/**`
- any prompt text other than the scoping in D-P6-1b-C

## Non-goals

- Any v2 work: claims, closed-set citation, test criteria, `insufficient_evidence` as an AI outcome, or `response_schema` on any call site.
- Prompt wording changes beyond scoping to a batch.
- Batching evidence extraction (D-P6-1b-I) or the curated DPDPA desk review.
- Retries on transport errors beyond the SDK's own, and retries in desk review.
- Bedrock (P6-13), job queues, or changes to scoring, reports, PDF or templates.
- Changing any DPDPA behaviour.

## Test scenarios (all required; you may add cases, not drop or weaken them)

Patch the seams (`claude_analyzer._call_llm`, `desk_review._call_llm`) with fakes that answer **per prompt**. Work out which controls a call covers by parsing the `**<ID>**` markers in its system prompt, and return JSON for exactly those IDs unless the scenario says otherwise. Run at `llm_max_concurrency=1` unless the scenario says otherwise.

1. **Threshold and call counts.** `run_multi_framework_analysis(["dpdpa", "iso27001", "nist_csf"], ...)` makes 1 DPDPA judge call, 6 ISO and 6 NIST judge calls, and 1 synthesis call. Each framework's merged `assessments` covers exactly its full control-ID set. Setting `llm_batch_threshold_controls=10_000` gives exactly 3 judge calls. Setting it to `40` batches DPDPA too, which shows the setting is honoured by the judge. Desk review never batches DPDPA at any threshold.
2. **Byte-identical when unbatched.** With `control_ids` omitted, the three builders' sha256 fingerprints for `dpdpa`, `iso27001` and `nist_csf` equal the Step 0 values, hard-coded in the test. The DPDPA judge call's seam kwargs, captured in a multi-framework run, are `==` to those produced by the same inputs with `llm_batch_threshold_controls=10_000`.
3. **Deterministic batch table.** `control_batches("iso27001")` and `control_batches("nist_csf")` match the D-P6-1b-B table exactly (labels, domains, section keys, counts, first and last IDs). `control_batches("dpdpa") == ()`. The union of `control_ids` equals `all_controls()` in order, with no duplicates. Calling it twice gives equal tuples. A synthetic framework whose sections are sized `[30]` and `[1]`, in a domain with `M=25`, exercises both the section-split and the singleton-merge rules.
4. **Merge order.** A fake that returns each batch's items **reversed**, and runs batches at concurrency 4 with random `time.sleep` jitter, still yields merged ISO assessments in `all_controls()` order.
5. **One retry, missing IDs only.** For ISO batch 2/6 the fake omits 2 IDs on the first call.
   - Exactly one retry call is made. Its system prompt lists only those 2 IDs (with "(2 total)"), and it is tagged `batch="2/6+retry"`.
   - The framework completes with all 93 controls.
   - A batch whose first response is not valid JSON is retried in full, once.
   - DPDPA with a missing ID raises the same `IncompleteAssessmentError` message as `main`, with no retry call.
6. **Failure semantics (D-P6-1b-F).**
   - The retry also omits an ID: the ISO result is the error dict with exactly the keys `parsed`, `raw`, `usage`, `error`, and `error` starts with `Gap analysis for ISO 27001` and names `batch 2/6`. NIST and DPDPA are unaffected, and synthesis still runs over the survivors.
   - A batch whose seam raises: no retry, ISO fails with the "failed in batch" message.
   - Through the route (the existing analysis-route harness pattern): the ISO `AnalysisRun` is `failed` with `FrameworkAnalysisError`, its envelope `llm_calls` includes the batch-tagged records, the ISO score is `failed_framework_scores()`, and the response message is today's partial-failure text.
7. **Executive summary.** For a batched framework, `parsed["executive_summary"]` equals the D-P6-1b-G sentence, with counts that reflect `applicable_controls` scope. No extra LLM call is made. For DPDPA, the model's own summary passes through unchanged.
8. **Desk-review merge.** A two-framework (`dpdpa`, `iso27001`) desk review:
   - 1 curated DPDPA call and 6 ISO batch calls
   - catalog entries for the same filename across batches merge into one entry with the union of `coverage_areas`
   - duplicate signal flags (same type, document and quote with different whitespace or case) collapse into one with the union of `requirement_ids`
   - out-of-batch IDs are dropped
   - `coverage_summary` covers all IDs returned
   - persisted `DeskReviewFinding` rows match the merged result
   - a single failing ISO batch fails ISO desk review with the batch message while DPDPA's findings persist, and the partial message is today's text
9. **Concurrency equivalence.** The analysis and desk-review results for `["dpdpa", "iso27001", "nist_csf"]` are `==` at `llm_max_concurrency=1` and `4`. At 4, the seam's max in-flight is > 1 and never > 4: one flattened pool, not nested pools.
10. **Call records.**
    - Every batched call's record has `stage`, `framework_id` and `batch`. Every unbatched call's record has exactly the 11 P6-1 keys, with no `batch` key.
    - `call_tag` nesting: an inner `batch` survives an outer `stage`/`framework_id`.
    - Through the route, ISO's envelope `llm_calls` has 6 judge records, plus a retry record where one happened.
11. **Golden and guards.**
    - `tests/test_golden_dpdpa.py` passes unmodified.
    - `git diff --stat main...HEAD -- tests/fixtures tests/support app/dpdpa app/frameworks/schema.py app/frameworks/definitions app/services/scoring.py` is empty (three-dot form).
    - `tests/test_answer_key_isolation.py` passes.

## Verification (before reporting done)

1. Run `.venv/bin/pytest -q` **after committing**. The result must be the Step 0 baseline plus the new tests, with no new failures. Only the three known failures listed in Step 0 are allowed, and the longitudinal one only intermittently. List any D-P6-1b-L pins you made.
2. Run the focused set `.venv/bin/pytest -q tests/test_p6_1b_framework_batching.py tests/test_p6_1_llm_plumbing.py tests/test_p5_3_framework_desk_review.py tests/test_golden_dpdpa.py tests/test_incomplete_assessment_e2e.py` and record the counts.
3. **Live smoke (orchestrator-run; Codex runs it only if `OPENROUTER_KEY` is set and `openrouter.ai` is reachable, and otherwise says so explicitly and does not claim it).** Run from the implementation worktree:
   ```bash
   .venv/bin/python -m scripts.validation.render_evidence c0-example
   .venv/bin/python scripts/validation/run_company.py c0-example --llm live --runs 1 --stop-after analysis
   ```
   - Pass condition: ISO analysis **completes**, with no `FrameworkAnalysisError`, and **every** `llm_calls` record in the desk-review raw response and in the ISO `AnalysisRun` envelope has `finish_reason == "stop"`.
   - Paste into `## Results` a table of every call with stage, batch, input and output tokens, latency and finish reason. Include the totals against the 2026-09-25 single-call numbers in "Why". Say whether evidence extraction ran (D-P6-1b-I).
   - When the orchestrator launches Codex in the background with `codex exec`, it must redirect stdin: `codex exec ... < /dev/null`. Otherwise the process blocks waiting on the terminal.

## Results

_To be filled in by the implementer: Step 0 baseline and prompt fingerprints, files changed, test counts, D-P6-1b-L pins, live smoke table (or an explicit "not run" and why), any deviation stopped on, PR link._

## Done criteria

- Every scenario passes.
- The full suite has no new failures against the baseline.
- The live smoke passes, or is explicitly recorded as not run.
- Results is filled in.
- The PR is opened against `main` from `codex/p6-1b-v1-framework-batching`. **Claude reviews before merge.**

## Report back

Append `## Results` to this file with:
- the Step 0 baseline and fingerprints
- files changed
- test counts
- every test you pinned under D-P6-1b-L
- the live-smoke call table and totals
- any deviation stopped on (per the rule at the top)
- the PR link
