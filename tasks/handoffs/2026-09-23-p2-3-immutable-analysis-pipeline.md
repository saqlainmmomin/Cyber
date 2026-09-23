# P2-3: Immutable analysis pipeline: append-only runs, conclusions and proposals, dual-written beside the legacy report

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 2, task P2-3; the Target Schema rows `analysis_runs`, `conclusions` and `conclusion_revisions`; Architecture Boundaries "Scoring boundary" and "LLM boundary" ("Failed/incomplete runs produce no draft Conclusions"); the "What breaks" row "Analysis re-run creates new rows instead of replacing | P2-3". Decisions **D2** (JSON for claims), **D3** (individual-only approval) and **D6** (optimistic locking on `Conclusion.version`) in `tasks/2026-09-21-adversarial-review.md`. PRD PR-040, PR-041, PR-042, PR-043, PR-044, PR-045 and PR-055. P2-2 handoff D-P2-2-D and D-P2-2-E.
**Owner:** Claude designs → Codex implements → **Claude reviews** (per `tasks/agent-ownership.md`: this task is foundational, since P2-4 and P2-6 build on its rows; it enforces a product invariant, "no destructive re-runs, never overwrite a human decision"; and it's architecture, because it decides how the new model coexists with the live `GapItem` model). Every architectural fork is closed below. **If the code forces a deviation from any decision, stop and report it in `## Results`. Do not pick an alternative.** Merge gate: the standard `[AR]` adversarial review **plus** a Claude review of the diff.
**Depends on:** P2-1 (Evidence, `active_versions_in_scope`) and P2-2 (`app/services/citations.py`, head `3d8b6f0a2c51`). Both are **merged** (PRs #24 and #25). P2-5 (PR #26) is merged and doesn't interact with this task.
**Blocks:** P2-4 (the approval workflow acts on the `Conclusion`/`ConclusionRevision` rows and the lock rule defined here) and P2-6 (the workpaper walks run → claim → revision → citation).
**Failing contract suite (already written, run it first):** `tests/test_analysis_pipeline.py` has 29 cases. At `c5dee85`, 27 are red for the intended reasons only: 25 fail on `ModuleNotFoundError: No module named 'app.services.analysis_pipeline'`, 1 fails on the missing head (`assert '3d8b6f0a2c51' == '4e8c1a9d2b57'`), and 1 upgrade-refusal test fails with `DID NOT RAISE RuntimeError` (there is no revision yet to refuse). The other 2 are standing guards that pass today and must keep passing. I validated the suite against a throwaway prototype of this spec: it turned all 29 green, and the full suite reached **392 passed** (363 + 29), with the four lockstep test edits in step 2 as the only changes to existing tests. The prototype was then discarded. Turn the suite green **without editing its assertions**.

## Goal

Every analysis trigger leaves a permanent, queryable record. Nothing an earlier trigger or a consultant wrote is deleted or silently overwritten.

- One `AnalysisRun` per framework per trigger. Each run is committed as `running` **before** the LLM is called and finishes as `completed` or `failed`. It holds a JSON envelope in `claims_json` that records what the run was given (inputs, model tiers) and what it claimed (one claim per requirement, with quality flags).
- One `Conclusion` per (assessment, framework, requirement). The pipeline creates it on first sight. On later runs it applies the new AI proposal, **unless a consultant has approved or edited it**. In that case the proposal is recorded but withheld, and the Conclusion row is not touched.
- Every proposal, applied or withheld, appends one `ConclusionRevision`. The revision is linked to its run and carries the claim's P2-2 citations.
- The legacy `GapReport`/`GapItem` write stays exactly as it is today, in the same transaction. Scoring, PDF export, reports, remediation and the live review flow keep working unchanged.

## Current state

Grounded against `c5dee85` on `main`. Re-locate everything by symbol name.

- **`app/routers/analysis.py`**: `trigger_analysis` (single-framework DPDPA path, used when `selected_frameworks` is NULL or `["dpdpa"]`) and `_run_multi_framework_analysis` (every other selection). Both work like this:
  1. Gate on questionnaire completion (400).
  2. Set `assessment.status = "analyzing"` and commit.
  3. Build `desk_review_data` from `DeskReviewSummary`/`DeskReviewFinding`, but only when the summary status is `completed`.
  4. Call the analyzer.
  5. On an exception, set status `error`, commit, and return HTTP 500 `Analysis failed: …` or `Multi-framework analysis failed: …`. On an empty single-path result, return 500 as well.
  6. Otherwise, apply server-side scope enforcement: when `assessment.applicable_requirements` is set, it mutates any out-of-scope item's `compliance_status` to `not_applicable` **in place**.
  7. Snapshot the existing `GapReport` + items into `legacy_history` (the PW-2 pattern), bulk-delete the old `GapItem`/`Initiative` rows, `db.delete(existing)`, add a new `GapReport`, then `GapItem`s and `Initiative`s, set status `completed`, and commit once.

  `_run_multi_framework_analysis` is **called directly** by `tests/test_no_blended_scoring.py` with keyword arguments, so its signature is frozen. Existing tests patch `app.routers.analysis.run_gap_analysis` / `run_multi_framework_analysis` with results that carry only `parsed` and `raw`, often with minimal items (sometimes an unknown status such as `fully_compliant`).
- **Pre-existing bug, verified by reproduction:** a **second** analysis of the same assessment fails with `sqlite3.IntegrityError: UNIQUE constraint failed: gap_reports.assessment_id` on any Alembic-built or `create_all` database. SQLAlchemy's unit of work runs the new `GapReport` INSERT before the `db.delete(existing)` DELETE within one flush. No existing test re-runs through `trigger_analysis` (`test_history_preservation.py` and `test_data_integrity.py` only simulate the snapshot logic), so the suite never caught it. On the web path, `run_analysis_web` swallows the exception and sets status `error`, so **re-running analysis is broken in the live app today**. The plan's own P2-3 test ("run analysis twice") cannot pass until this is fixed, so this task fixes it (step 5).
- **`app/services/claude_analyzer.py`**: `run_gap_analysis` returns `{"parsed", "raw", "usage"}`. Its Call-1 evidence dict (candidate quotes per requirement, from Call 1 or reused from desk review) is used only inside the prompt and **not returned**. `tests/test_golden_dpdpa.py::test_analyzer_output_matches_golden` asserts `run_gap_analysis(...) == expected` **as a whole dict**, so any new key breaks the golden. On a caught per-framework failure, `run_multi_framework_analysis` returns `{"parsed": {..., "assessments": []}, "raw", "usage": {}, "error": str(e)}`. Each validated item has the `GapAssessmentItem` fields (`app/schemas/llm_output.py`), including `evidence_quote` (the model's verbatim supporting quote, which may be fabricated) and `needs_review` (set by `_flag_unsupported_compliant_items`). Statuses outside `KNOWN_STATUSES` are coerced to `not_assessed`.
- **`app/models/analysis_run.py`, `AnalysisRun`** (P1-2): `id`, `assessment_id` FK (indexed), `framework_id`, `status`, `claims_json` (Text, **NOT NULL**), `model_id` (**NOT NULL**), `started_at` (NOT NULL), `completed_at` (nullable). **Zero application code writes it.**
- **`app/models/conclusion.py`**: `Conclusion` has `outcome`, `rationale`, `evidence_summary`, `gaps_identified`, `risk_level` and `recommended_action` (all NOT NULL), `cluster_id` (nullable), `ai_proposed`, `version` (default 1, D6) and `updated_at` (`onupdate`). **There is no uniqueness on (assessment_id, framework_id, requirement_id).** `ConclusionRevision` has `actor`, `action`, `previous_outcome`, `previous_rationale` and `citations_json`, **and no link to an `AnalysisRun`**. The revision stores the values *before* its action (its `previous_*` fields), not the proposed content. Its only writer today is `scripts/migrate_legacy.py`: it writes one `proposed` revision per migrated `GapItem` (`previous_*` NULL, `citations_json` NULL), plus an `approved` revision when `GapItem.reviewed_at` is set. **The bulk approve in `app/routers/review.py` sets `reviewed_at` on every item**, so every bulk-approved legacy report migrated as individually "approved" Conclusions.
- **`scripts/migrate_legacy.py` is re-runnable** (idempotent, human-invoked). For every `GapItem` it looks up the Conclusion by natural key, then the `proposed` revision with **`scalar_one_or_none()`**. As soon as P2-3 has appended a second `proposed` revision, a later run of this script raises `MultipleResultsFound`. It would also create one `Finding` + `Action` per `GapItem` with `remediation_status` set. That column defaults to `"open"`, so every GapItem the pipeline writes qualifies. Step 7 closes this.
- **`app/routers/review.py`** (the live approval flow): `disposition_item` edits single `GapItem`s. `approve_assessment` refuses while any item is `draft`, then stamps `reviewed_by`/`reviewed_at` on **every** item in one loop. This is a bulk accept that contradicts D3. Replacing it is **P2-4**, not this task. This task must not touch it.
- **Readers of `GapItem`/`GapReport`** (all unchanged by this task): `app/services/scoring.py::score` → `_build_cluster_verdicts`, `app/utils/pdf_export.py`, `app/routers/reports.py`, `app/routers/remediation.py`, `app/routers/review.py`, and `app/routers/web.py` (report pages, `analysis_status`). **None of them references `Conclusion` or `AnalysisRun`.** Scenario 12's standing guard pins that.
- **`app/services/citations.py`** (P2-2): `citable_sources(db, assessment_id)` returns the active versions of in-scope active Evidence. `cite_quotes(sources, quotes)` returns verified `text_span` citations and drops ungrounded quotes. `attach_citations(db, revision=, citations=)` re-validates (≤ 3 statements), refuses a revision whose `citations_json` is already set, and flushes. **Cost:** `locate_excerpt` re-normalizes the whole source text for every call. That measures ~0.08 s per 315k-character document. With ~40–90 requirements × N sources per framework, that adds seconds to tens of seconds to a synchronous request. Step 6 memoizes it.
- **Baseline:** `.venv/bin/pytest -q` → **363 passed** (in the main checkout). In a fresh `git worktree`, the suite also reports **1 teardown error** from `tests/conftest.py::_guard_dev_database_untouched`, because `data/dpdpa.db` doesn't exist there and gets created. The P2-2 and P2-5 Results report the same thing. I reproduced it on an untouched `HEAD` worktree (363 passed, 1 error). It is not a regression.

## Decisions (made here so they are not relitigated)

### D-P2-3-A. Dual-write. `GapItem`/`GapReport` are **not** replaced in this task.

**Decision:** `trigger_analysis` keeps writing `GapReport`/`GapItem`/`Initiative` exactly as today, including the `legacy_history` snapshot, and **additionally** writes `AnalysisRun`/`Conclusion`/`ConclusionRevision` from the **same analyzer output, in the same transaction**. They are two views of one analyzer result:

| | Legacy view (`GapReport`/`GapItem`) | New record (`AnalysisRun`/`Conclusion`/`ConclusionRevision`) |
|---|---|---|
| Written by | `trigger_analysis`, unchanged except step 5's flush | `app/services/analysis_pipeline.py`, called by `trigger_analysis` |
| On re-run | replaced (old rows in `legacy_history`), as today | appended. Nothing is deleted. Human decisions are never overwritten (D-P2-3-C) |
| Read by after P2-3 | scoring, PDF, reports JSON, remediation, review (bulk approve), web report pages | **nothing in the app yet**, except the pipeline's own lock check. P2-4 and P2-6 are the first readers |
| Link between them | natural key **(assessment_id, framework_id, requirement_id)**. GapItem rows are deleted on every re-run, so an FK is impossible. Each run's envelope also records the `gap_report_id` written in the same transaction | |

**Why not replace:**
1. The plan bullet says "create/update Conclusion rows", not "replace GapItem".
2. Replacing would rewrite deterministic scoring (`_build_cluster_verdicts` reads `GapItem`), the board PDF, the reports JSON API, remediation tracking and the live review flow in one task. That's five-plus files, including the scoring boundary P1-5 just stabilised.
3. PR-045 says scoring must operate on **consultant-approved** Conclusions. Until P2-4 gives Conclusions an individual approval path, there is nothing correct for scoring to read. Migrating readers off `GapItem` is therefore a later, separate task (open question 1), done once `Conclusion` has proven itself.

**Why the same transaction:** so the invariant "the live `GapReport`'s items and the latest completed runs' claims come from the same analyzer output" is always true. If the new write fails, the legacy write rolls back with it, the previous report survives, and the run is marked `failed` (D-P2-3-B). The alternative, committing the legacy report first, would keep analysis working through bugs in the new code, but would let the two views drift silently. Failing closed is the ownership contract's default for a product invariant.

**Accepted consequences, named:**
- The bulk approve in `review.py` stamps `GapItem`s only and writes **no** `ConclusionRevision`. That is deliberate. Under D3 a bulk stamp is not an individual approval, so it must never appear as one in the new model. So until P2-4, Conclusions written by the pipeline are never locked by the live UI.
- The legacy view keeps today's re-run semantics: a re-run resets `GapItem`s to `draft` with the new AI verdict, even where the matching Conclusion is locked and keeps its human content. After P2-4, the two views will disagree for locked requirements until the reader migration (open question 1). P2-4's designer must decide what the report shows in the meantime.

### D-P2-3-B. Run lifecycle, transaction boundaries and failure

- **One run per framework per trigger.** The single path writes one `dpdpa` run. The multi path writes one run per `selected_frameworks` entry, in that order. All runs from one trigger share an envelope `trigger_id` (a UUID4), so "the runs from one click" is queryable without a new column.
- **Status set:** `RUN_STATUSES = ("running", "completed", "failed")`. The only transitions are `running → completed` and `running → failed`. `fail_runs` never touches a run that isn't `running`.
- **Commit points (exact):**
  1. After every existing gate and the desk-review load, and **immediately before** the analyzer call, run `start_runs(...)` and then `db.commit()`. The `running` row is visible to other sessions while the LLM works (scenario 1 checks this from a second session). A trigger refused by a 400 gate creates **no** run.
  2. **Analyzer exception** (either path): `fail_runs(error_type=type(e).__name__)`, set `assessment.status = "error"`, commit, and raise the existing 500 with its existing message.
  3. **Empty single-path result:** `fail_runs(error_type="EmptyAssessment")`, then as above.
  4. **Multi path, after the analyzer returns:** each framework whose result is missing or has an `"error"` key gets `fail_runs(error_type="FrameworkAnalysisError", framework_ids=[...])`, then `db.commit()` **before** persistence starts. Those frameworks get no Conclusions. The others continue. (The legacy report for a failed framework keeps today's behaviour: no items, and a zero score entry.)
  5. **Persistence phase:** the legacy report rewrite plus one `record_framework_run` per non-failed framework, ending in the existing single commit. On **any** exception in this phase: `db.rollback()`, then `fail_runs(error_type=type(exc).__name__)` for every still-`running` run, `assessment.status = "error"`, commit, and `raise HTTPException(500, f"Analysis results could not be saved ({type(exc).__name__}). Run analysis again.")`. After a rollback, the previous `GapReport`, `Conclusion` rows and revisions are exactly as they were (scenarios 7, 8 and 10).
- **The error record is `{"type": <exception class name>}` only. No message.** Analyzer and parse errors can embed model output, which is client content (`_parse_json_response` includes up to 500 characters of the response). The HTTP detail keeps today's text. The durable row does not. Scenario 8 asserts that the exception message is absent from `claims_json`.
- **Known residual:** if the process dies during the LLM call (a crash, not an exception), the run stays `running` forever. No sweeper is added. Consumers (P2-6) must treat a `running` run whose `started_at` is older than the request timeout as stale (open question 5).

### D-P2-3-C. Re-running must never overwrite a human decision. The exact rule.

For each claim, keyed by (assessment, framework, requirement), there are exactly three dispositions:

| Existing Conclusion | Disposition | Conclusion row | Revision appended (`actor = "system:analysis"`) |
|---|---|---|---|
| none | `created` | inserted with the claim's content, `ai_proposed=True`, `version=1` | `action="proposed"`, `previous_*` = NULL |
| exists, **unlocked** | `applied` | content replaced by the claim's content, `ai_proposed=True`, `version = expected_version + 1`, via **compare-and-swap** (below) | `action="proposed"`, `previous_*` = the row's outcome/rationale **before** this update |
| exists, **locked** | `withheld` | **not touched at all**: content, `version`, `updated_at` and `ai_proposed` unchanged | `action="proposal_withheld"`, `previous_*` = the row's current (unchanged) outcome/rationale |

Every revision, in all three cases, gets `analysis_run_id = run.id` and its claim's citations. So the history shows every proposal, and P2-4 can surface "a newer AI proposal was withheld".

**Lock rule (exact):** `HUMAN_DECISION_ACTIONS = ("approved", "edited", "rejected", "reopened")` and `LOCKING_ACTIONS = ("approved", "edited")`. A Conclusion is **locked** iff its most recent revision whose action is in `HUMAN_DECISION_ACTIONS` has an action in `LOCKING_ACTIONS`. Recency is ordered by `(created_at, rowid)`. System revisions (`proposed`, `proposal_withheld`) never lock or unlock.
- `approved`/`edited` lock: a human has vouched for, or authored, the content.
- `rejected` does **not** lock. A rejection is a verdict on one AI proposal, not human-authored content, so there's nothing human to protect. A fresh proposal replacing a rejected one is what the consultant needs. The rejection revision stays in history.
- `reopened` (P2-4's action) unlocks. It is the **only** way a new AI proposal can reach a locked Conclusion.
- Scenario 4 pins ten sequences, including `approved → reopened → approved` (locked) and `edited → rejected` (unlocked).
- **Legacy migrated approvals lock.** `migrate_legacy.py` wrote `approved` revisions for every bulk-approved legacy report, and those Conclusions are withheld on re-run. That's the conservative reading of "never overwrite a human decision". Whether a migrated bulk approval counts as a D3 approval is P2-4's call (handed forward).

**Compare-and-swap (D6):** an `applied` update is a single `UPDATE conclusions SET … WHERE id = :id AND version = :expected_version`. `expected_version` is what `load_conclusion_state` read. If `rowcount != 1`, raise `ConclusionConflict`, and the persistence phase fails closed (D-P2-3-B step 5). This closes the window in which a consultant commits a decision between the pipeline's read and its write. Scenario 10 injects that race through the `load_conclusion_state` seam. **Handed forward, and load-bearing:** P2-4 must increment `Conclusion.version` on **every** revision it writes (approve, edit, reject, reopen). Otherwise this check can't detect a concurrent human decision.

**Other rules:**
- Requirements missing from a run's output are left alone. Their Conclusions are never deleted or marked. Rows the pipeline writes are never deleted.
- A duplicate `requirement_id` in one framework's items: the first occurrence wins. Later ones are ignored with a warning, and get no claim, Conclusion or revision. (The legacy `GapItem` write keeps its existing behaviour.)

### D-P2-3-D. Citations: a claim cites its own `evidence_quote`, snapshotted sources, through `attach_citations`, failing closed

- **What is cited:** exactly the item's `evidence_quote`, via `cite_quotes(context.sources, [evidence_quote])` when it's non-blank, else `[]`. **This deliberately narrows the P2-2 hand-off (D-P2-2-E), which anticipated `[evidence_quote, *call1_quotes]`**, for two reasons:
  1. *Semantics.* A citation supports a claim. Call-1 and desk-review quotes are pre-verdict **candidates** for a requirement. Attaching them to, say, a `non_compliant` claim would present quotes the verdict rejected as its support.
  2. *Blast radius.* Returning the evidence dict from `run_gap_analysis` changes its return value, and `test_analyzer_output_matches_golden` compares that dict for exact equality. That would force a golden-fixture change for no semantic gain.

  The candidates aren't lost. Desk-review findings already carry their own citations (`desk_review_findings.citations_json`, P2-2) for P2-6 to show. **`claude_analyzer.py` is not modified by this task**, even though the plan's file list names it.
- **Only `text_span` citations.** An analysis claim is never attributed to a document without a quote, so `whole_item` is never produced here. `"[]"` on a revision means "captured, no source-grounded support" (D-P2-2-D), and every revision this task writes stores an array, never NULL.
- **Sources are snapshotted by `start_runs`**, before the LLM call, and the same `CitableSource` tuple is used at persistence. Citations therefore point at the versions analysis was actually offered, and `inputs.evidence_versions` records exactly that set.
- **Written through `attach_citations`**, the single validated write path from P2-2. It re-validates that every cited version is still active. **If a cited version stopped being active during the run** (a new version was released, or the Evidence was invalidated or archived), the run **fails closed**: `CitationError` → rollback → the run is `failed` (scenario 7). The consultant re-runs. The alternative, writing the stale citation around `attach_citations`, would create a second write path. That's the trap P2-2 closed. The window is one LLM call in a single-user app.
- **Grounding drives two content rules.** `Conclusion.evidence_summary` is the `evidence_quote` **only if it grounded**, else `""`, so an ungrounded quote is never presented as evidence (PR-041). The quality flag `unsupported_assertion` is true when the outcome is `compliant` or `partially_compliant` and there are no citations.

### D-P2-3-E. `claims_json`: a versioned envelope (D2: JSON, not a table)

`claims_json` is `json.dumps(envelope, sort_keys=True)`. It is an **object**, not the bare array in the plan's annotation, because the run must also record its inputs and error (PR-040, and the P2-1 promise that "P2-3 analysis runs record their evidence inputs"). A `schema_version` field lets later shapes be told apart (the precedent is P2-5's `scope_json`). It is written at `start_runs` and replaced wholesale at completion or failure. Key sets are exact (the suite asserts equality):

```jsonc
{
  "schema_version": 1,
  "trigger_id": "<uuid4 shared by every run of one trigger>",
  "framework_id": "dpdpa",
  "model_tiers": {"extract": "<settings.llm_model_extract>", "judge": "<…judge>", "synthesize": "<…synthesize>"},
  "inputs": {
    "evidence_versions": [{"evidence_id": "…", "version_id": "…", "filename": "<the version's original_filename>"}],  // = the snapshotted citable_sources, in order
    "legacy_document_ids": ["…"],              // analysis_documents() rows with source == "legacy", in order
    "questionnaire_response_count": 12,        // COUNT of this assessment's questionnaire_responses
    "applicable_requirements": ["…"] | null    // json.loads(assessment.applicable_requirements), or null (also null if it's unparseable)
  },
  "gap_report_id": null | "<GapReport.id written in the same transaction>",   // null until completed
  "desk_review_used": null | true | false,      // null until completed; else `desk_review_data is not None`
  "claims": [ /* one per unique requirement, in analyzer item order; [] while running and when failed */ ],
  "error": null | {"type": "<exception class name | EmptyAssessment | FrameworkAnalysisError>"}
}
```

Each claim:

```jsonc
{
  "requirement_id": "CH2.CONSENT.1",
  "cluster_id": "CLUSTER_029" | null,          // CONTROL_CLUSTERS lookup for this framework (step 4)
  "outcome": "compliant",                       // OUTCOME_BY_STATUS mapping (step 4)
  "scope_enforced": false,                      // applicable_requirements non-empty AND requirement not in it
  "item": { /* the analyzer item dict exactly as the router passed it, after scope enforcement */ },
  "quality": {
    "citation_count": 1,
    "evidence_quote_grounded": true | false | null,   // null = no quote offered
    "unsupported_assertion": false,
    "needs_review": false,                            // bool(item.get("needs_review", False))
    "desk_review_red_flags": 0,                       // desk_review_data findings: type == "signal" and requirement_id == this one
    "desk_review_absence": false,                     // any type == "absence" finding for this requirement
    "contradictions": null                            // NOT ASSESSED by pipeline v1 (open question 2); null, never []
  },
  "conclusion_id": "…",
  "revision_id": "…",                                 // the revision that holds this claim's citations
  "disposition": "created" | "applied" | "withheld"
}
```

- **Citations live only on the revision.** The claim links to it by `revision_id` and doesn't copy it. That's P2-2's one-representation rule. Navigation is revision → `analysis_run_id` → run → the claim whose `revision_id` matches (PR-055's "Conclusion revision → claim/Citation").
- **`item` is the model's full output for that requirement.** `GapReport.raw_ai_response` is replaced on re-run, so this is the durable record of what the model said.
- **Quality dimensions (PR-041/PR-022) are kept separate**, not collapsed into one score. The legacy `evidence_confidence` heuristic is deliberately **not** recorded.
- **Desk-review finding ids are not recorded, only counts.** A desk-review re-run deletes and replaces its findings, so stored ids would dangle.

### D-P2-3-F. Schema: one link column plus one uniqueness guarantee (revision `4e8c1a9d2b57`)

- **`conclusion_revisions.analysis_run_id`**: nullable FK → `analysis_runs.id`, indexed. Without it, the only way to tie a proposal to its run is by timestamp. PR-055's navigation needs a real link. It's NULL for human revisions and for `migrate_legacy`'s backfilled revisions.
- **Unique index `uq_conclusions_assessment_framework_requirement`** on `(assessment_id, framework_id, requirement_id)`. "Create or update the Conclusion for this requirement" is only well-defined if there is at most one. Today that rests on `migrate_legacy.py`'s lookup-before-insert alone. It's an index, not a table constraint, so SQLite needs no table rebuild. The upgrade refuses if duplicates exist rather than choosing which row to drop.
- No other schema change. `proposal_withheld` is a new **value** of the free-text `action` column, not a schema change. The plan's vocabulary (`proposed | edited | approved | rejected | reopened`) is extended by exactly this one value.

### D-P2-3-G. The P1-5/PW-2 `legacy_history` pattern: kept for the legacy tables, not copied for the new ones

`legacy_history` exists because `GapReport`/`GapItem` are *replaced* on re-run: the snapshot-into-JSON is how PW-2 made a destructive write non-destructive. The new tables are append-only **by construction** (a new run row, a new revision row, a compare-and-swap update that is itself recorded as a revision), so the history is the rows themselves. Snapshotting them into JSON would duplicate facts the rows already hold. The legacy pattern stays exactly as it is for `GapReport`. Step 5's `db.flush()` is the only change to it, and it fixes the pre-existing re-run crash without changing what the snapshot contains.

### D-P2-3-H. `scripts/migrate_legacy.py` does not touch pipeline-owned assessments

In `run_migration`, after the `AssessmentPack` block and before the `GapReport` lookup: if **any** `AnalysisRun` exists for the assessment, append the warning `f"Assessment {assessment.id}: conclusions are owned by the analysis pipeline (P2-3); legacy GapItem mapping skipped."` and `continue`. Its Conclusions are already maintained by the pipeline. Its `GapItem`s were written by the pipeline's own trigger, not by legacy history. Mapping them would crash (`MultipleResultsFound`) or mint one `Finding` per `open` item. Findings are P3-1's to design. Client, Engagement and AssessmentPack creation for that assessment still run.

## Required approach

### 1. Models

- `app/models/conclusion.py`, `Conclusion`: add
  ```python
  __table_args__ = (
      Index("uq_conclusions_assessment_framework_requirement",
            "assessment_id", "framework_id", "requirement_id", unique=True),
  )
  ```
- `ConclusionRevision`: add, directly after `citations_json`:
  ```python
  analysis_run_id: Mapped[str | None] = mapped_column(
      String(36), ForeignKey("analysis_runs.id"), nullable=True, index=True
  )
  ```
  `index=True` yields `ix_conclusion_revisions_analysis_run_id`. That name must match the migration, because `tests/test_data_integrity.py::test_tables_columns_fks_indexes_match_orm_metadata` compares the ORM and Alembic schemas.
- No `relationship()` (house rule). `AnalysisRun` is unchanged.

### 2. Alembic revision: pinned id `4e8c1a9d2b57`

File `alembic/versions/4e8c1a9d2b57_p2_3_immutable_analysis_pipeline.py`, `revision = "4e8c1a9d2b57"`, `down_revision = "3d8b6f0a2c51"`. Hand-written.

`upgrade()`:
1. Guard: `SELECT COUNT(*) FROM (SELECT 1 FROM conclusions GROUP BY assessment_id, framework_id, requirement_id HAVING COUNT(*) > 1)`. If it's greater than 0, raise `RuntimeError("Refusing to add uq_conclusions_assessment_framework_requirement: N (assessment_id, framework_id, requirement_id) groups in conclusions hold more than one row. Resolve them first -- restore a verified backup or merge the duplicates by hand.")`. It must run **before any DDL**. The suite checks the version stays at `3d8b6f0a2c51` and both rows survive.
2. `batch_alter_table("conclusion_revisions")`: `add_column(sa.Column("analysis_run_id", sa.String(length=36), nullable=True))`; `create_foreign_key("fk_conclusion_revisions_analysis_run_id_analysis_runs", "analysis_runs", ["analysis_run_id"], ["id"])`; `create_index("ix_conclusion_revisions_analysis_run_id", ["analysis_run_id"], unique=False)`.
3. `batch_alter_table("conclusions")`: `create_index("uq_conclusions_assessment_framework_requirement", ["assessment_id", "framework_id", "requirement_id"], unique=True)`.

`downgrade()`:
1. Guard: `SELECT COUNT(*) FROM conclusion_revisions WHERE analysis_run_id IS NOT NULL`. If it's greater than 0, raise `RuntimeError("Refusing to downgrade past P2-3 revision 4e8c1a9d2b57: N conclusion_revisions rows are linked to analysis runs. Downgrading would drop that link -- restore a verified backup instead.")`.
2. Drop the unique index. Then drop the revision index, the FK (by its name) and the column.

**Existing tests to update in lockstep.** This is the complete list: the prototype run of this spec produced exactly these 9 failures and no others. Change only what is listed.

| File | Change |
|---|---|
| `tests/test_alembic_baseline_immutable.py` | both probe templates: `down_revision = "3d8b6f0a2c51"` → `"4e8c1a9d2b57"` |
| `tests/test_data_integrity.py` | the three `"3d8b6f0a2c51"` head assertions (in `test_fresh_upgrade_downgrade_upgrade_round_trip`, `test_downgrade_refuses_when_data_present`, `test_data_bearing_adopted_db_refuses_then_recovers_to_head`) → `"4e8c1a9d2b57"` |
| `tests/test_startup_invariants.py` | both `assert version == "3d8b6f0a2c51"` → `"4e8c1a9d2b57"` |
| `tests/test_citations.py` | `test_p2_2_revision_is_head_and_reshapes_schema`: replace `assert script.get_current_head() == P2_2_REVISION` with `assert script.get_revision("4e8c1a9d2b57").down_revision == P2_2_REVISION`. `test_p2_2_downgrade_restores_citations_table_and_refuses_with_data`: replace `assert ScriptDirectory.from_config(config).get_current_head() == P2_2_REVISION` with `assert ScriptDirectory.from_config(config).get_revision("4e8c1a9d2b57").down_revision == P2_2_REVISION`. P2-2 is no longer head, and its contract is otherwise unchanged. No other edits. |

### 3. `app/services/analysis_pipeline.py`: public API, exact

The module docstring states D-P2-3-A through H in one short paragraph each. `logger = logging.getLogger(__name__)`. The module **never commits**; the router owns every transaction (the P2-1 rule). It contains **no `delete`** (the standing guard greps the file for the word).

```python
CLAIMS_SCHEMA_VERSION = 1
PIPELINE_ACTOR = "system:analysis"
RUN_STATUSES = ("running", "completed", "failed")
OUTCOME_BY_STATUS = {"compliant": "compliant", "partially_compliant": "partially_compliant",
                     "non_compliant": "non_compliant", "not_applicable": "not_applicable",
                     "not_assessed": "insufficient_evidence"}   # must equal scripts.migrate_legacy.OUTCOME_MAP (asserted)
UNKNOWN_STATUS_OUTCOME = "insufficient_evidence"                 # any other status; log a warning (no item content)
HUMAN_DECISION_ACTIONS = ("approved", "edited", "rejected", "reopened")
LOCKING_ACTIONS = ("approved", "edited")
SUPPORTING_OUTCOMES = ("compliant", "partially_compliant")

class AnalysisPipelineError(Exception): ...
class ConclusionConflict(AnalysisPipelineError): ...    # message: f"Conclusion {id} changed while analysis was running."

@dataclass(frozen=True)
class RunContext:
    trigger_id: str
    run_ids: dict[str, str]                 # framework_id -> AnalysisRun.id, in framework order
    sources: tuple[CitableSource, ...]      # snapshot from citable_sources at start

@dataclass(frozen=True)
class ConclusionState:
    conclusion: Conclusion
    locked: bool
    expected_version: int                   # conclusion.version as read
```

`RunContext` holds ids, not ORM objects, because the persistence-failure path runs after a `rollback()`.

- `start_runs(db, *, assessment_id: str, framework_ids: list[str]) -> RunContext`: snapshot `sources = tuple(citable_sources(db, assessment_id))`. Take `legacy_document_ids` from `analysis_documents(db, assessment_id)` rows with `source == "legacy"`. Count questionnaire responses, and parse `applicable_requirements` from the `Assessment` row. Build the envelope (D-P2-3-E) with `claims=[]`, `gap_report_id=None`, `desk_review_used=None` and `error=None`. For each framework, add an `AnalysisRun(status="running", model_id=settings.llm_model_judge, started_at=<now UTC>, completed_at=None, claims_json=json.dumps(envelope, sort_keys=True))`. The runs share one `trigger_id`. Flush, and return the context.
- `fail_runs(db, context, *, error_type: str, framework_ids: list[str] | None = None) -> None`: for each targeted run (all of them when `None`) whose status is `running`, set `status="failed"`, `completed_at=<now>` and envelope `error={"type": error_type}`, keeping `claims=[]`. Flush.
- `load_conclusion_state(db, *, assessment_id: str, framework_id: str) -> dict[str, ConclusionState]`, keyed by `requirement_id`, using ≤ 2 statements: the Conclusions, then their revisions with `action IN HUMAN_DECISION_ACTIONS` ordered by `created_at, rowid` (`literal_column("conclusion_revisions.rowid")`). The last one per Conclusion decides `locked` (D-P2-3-C). No Conclusions → `{}`.
- `record_framework_run(db, context, *, framework_id: str, assessments: list[dict], desk_review_data: dict | None, gap_report_id: str) -> AnalysisRun`. Called **after** the router has applied scope enforcement and flushed the new `GapReport`:
  1. Load the run and its envelope. `applicable = envelope["inputs"]["applicable_requirements"]`.
  2. `state = load_conclusion_state(db, assessment_id=run.assessment_id, framework_id=framework_id)`, called **through the module global** (scenario 10 patches it), **once**, before any write.
  3. For each item in order, skipping duplicate `requirement_id`s (D-P2-3-C):
     - `outcome` from `OUTCOME_BY_STATUS`, or else `UNKNOWN_STATUS_OUTCOME`.
     - `quote = item.get("evidence_quote") or ""`.
     - `citations = cite_quotes(list(context.sources), [quote]) if quote.strip() else []`.
     - `grounded = None if not quote.strip() else bool(citations)`.
     - Content: `outcome`; `rationale = item.get("current_state") or ""`; `evidence_summary = quote if grounded else ""`; `gaps_identified = item.get("gap_description") or ""`; `risk_level = item.get("risk_level") or "medium"`; `recommended_action = item.get("remediation_action") or ""`; `cluster_id` from step 4. **Mapping note:** `rationale` is `current_state`, not `gap_description` as `migrate_legacy.py` used. PR-043 needs rationale and identified gaps as separate fields, and for a compliant item `gap_description` is typically "No gap".
     - Apply D-P2-3-C. **created:** add, then flush. **applied:** `db.execute(update(Conclusion).where(Conclusion.id == c.id, Conclusion.version == st.expected_version).values(**content, ai_proposed=True, version=st.expected_version + 1).execution_options(synchronize_session=False))`; if `rowcount != 1`, raise `ConclusionConflict`; then `db.expire(c)`. **withheld:** no write to the row.
     - Add the revision (actor `PIPELINE_ACTOR`, action and `previous_*` per D-P2-3-C, `analysis_run_id=run.id`), flush, then `attach_citations(db, revision=revision, citations=citations)`.
     - Append the claim (D-P2-3-E).
  4. Set the envelope's `claims`, `gap_report_id` and `desk_review_used = desk_review_data is not None`. Set `run.status="completed"`, `completed_at=<now>` and `claims_json`. Flush, and return the run.

  Never log quote text or item content. Requirement ids and counts only.

### 4. Cluster lookup

`{m["control"]: c["cluster_id"] for c in CONTROL_CLUSTERS for m in c["controls"] if m["framework"] == framework_id}.get(requirement_id)`, from `app.frameworks.mappings.clusters`. This is the same comprehension `scoring._validated_cluster_mapping` uses, without its coverage check (scoring owns that). **Do not import the private scoring function.**

### 5. `app/routers/analysis.py`: the dual-write wiring

- Add `from app.services import analysis_pipeline` (import the module, so the suite's patches are visible).
- **Single path:** `run_context = analysis_pipeline.start_runs(db, assessment_id=assessment_id, framework_ids=["dpdpa"])` then `db.commit()`, placed right before `run_gap_analysis(...)`. Wire the failure branches exactly as D-P2-3-B describes.
- **Multi path:** the same, at the top of `_run_multi_framework_analysis`, before `run_multi_framework_analysis(...)`, with `framework_ids=list(selected_frameworks)`. **Its signature stays exactly as it is.** Then add the post-analyzer failed-framework commit (D-P2-3-B step 4).
- **Persistence (both paths):** wrap everything from scope enforcement to the final commit in the D-P2-3-B step 5 `try/except`. You may move that block into private helpers, as the prototype did, as long as the behaviour is identical. Inside it, **immediately after `db.add(report); db.flush()`**, call `analysis_pipeline.record_framework_run(db, run_context, framework_id=..., assessments=..., desk_review_data=desk_review_data, gap_report_id=report.id)`. On the single path that's once with `"dpdpa"` and the scope-enforced `assessments`. On the multi path it's once per non-failed framework, in `selected_frameworks` order, with `per_fw_assessments[fw_id]`.
- **Bug fix (both paths):** directly after `db.delete(existing)`, add `db.flush()  # delete before the replacement INSERT: gap_reports.assessment_id is unique`. Change nothing else about the snapshot and delete block.
- **Response:** add `"analysis_run_ids": dict(run_context.run_ids)` to both success dicts. Every other key is unchanged.
- **Do not** change the gates, their messages, the desk-review loading, the `GapItem`/`Initiative` field mapping, `evidence_confidence`, scoring calls, or the existing 500 messages.

### 6. `app/services/citations.py`: memoize the text side of `locate_excerpt`

```python
@functools.lru_cache(maxsize=16)
def _normalized_source(text: str) -> tuple[str, array]:
    normalized, offsets = normalize_with_offsets(text)   # module-global lookup (the suite spies on it)
    return normalized, array("l", offsets)
```

`locate_excerpt` uses `_normalized_source(text)` for the text and keeps calling `normalize_with_offsets(excerpt)` for the excerpt. Behaviour is identical, and `tests/test_citations.py` must stay green unmodified apart from its step 2 lockstep edits. `array("l")` bounds the cache at about 4–8 bytes per offset rather than about 36 for a list of ints, which is roughly 25 MB worst case at 16 × 300k-character sources. `normalize_with_offsets`'s public contract (it returns a fresh `list`) is unchanged.

### 7. `scripts/migrate_legacy.py`

Apply D-P2-3-H exactly. `from app.models.analysis_run import AnalysisRun`, and use `select(AnalysisRun.id).where(AnalysisRun.assessment_id == assessment.id).limit(1)`. No other change. `tests/test_migrate_legacy.py` must stay green unmodified.

## Key files

| File | Why it matters |
|---|---|
| `app/services/analysis_pipeline.py` (new) | The whole contract (step 3). |
| `app/routers/analysis.py` | Dual-write wiring, failure semantics, the re-run flush fix (step 5). |
| `app/models/conclusion.py` | Unique index; `ConclusionRevision.analysis_run_id` (step 1). |
| `alembic/versions/4e8c1a9d2b57_p2_3_immutable_analysis_pipeline.py` (new) | Step 2: pinned id and both guards. |
| `app/services/citations.py` | `_normalized_source` memo (step 6). Nothing else. |
| `scripts/migrate_legacy.py` | The pipeline-owned skip (step 7). |
| `app/services/claude_analyzer.py` | **Not modified** (D-P2-3-D). |
| `app/routers/review.py`, `app/services/scoring.py`, `app/utils/pdf_export.py`, `app/routers/reports.py`, `app/routers/remediation.py` | **Not modified.** Guarded by scenario 12. |
| `tests/test_analysis_pipeline.py` | The contract, plus the four lockstep files in step 2. |

## Non-goals

- Do **not** replace, stop writing, or change the shape of `GapReport`/`GapItem`/`Initiative`, or move any reader onto `Conclusion` (D-P2-3-A; open question 1).
- Do **not** touch `review.py`, or add any approval, reject, edit or reopen route or UI (**P2-4**). No template changes at all. **No read API or page** for runs or conclusions (**P2-4/P2-6**). The plan's "UI shows latest run" belongs there.
- Do **not** modify `claude_analyzer.py`, any prompt, or any golden fixture. Don't cite Call-1 or desk-review candidate quotes (D-P2-3-D).
- Do **not** produce `contradictions`. Leave it `null` (open question 2).
- Do **not** create `AnalysisRun`s for desk review, screening, RFI or vision calls (open question 3).
- Do **not** add a `running`-run sweeper or timeout (open question 5), audit_events rows (the run and revision rows are this domain's append-only trail, per D2), Findings/Actions (**P3-1**), or a `relationship()`.
- Do **not** mirror bulk-approve stamps into `ConclusionRevision` (D-P2-3-A).

## Test scenarios

All in `tests/test_analysis_pipeline.py` (already written). The numbers match the test docstrings.

1. **First run.** The `running` row is visible from a second session **during** the analyzer call. The run completes with the exact envelope key set, `schema_version` 1, `model_id == settings.llm_model_judge`, `model_tiers`, `gap_report_id` and `claims_json == json.dumps(env, sort_keys=True)`. There's one Conclusion per item, with the mapped outcome (`not_assessed → insufficient_evidence`), the content mapping, `cluster_id`, `ai_proposed` and version 1. There's one `proposed` revision per Conclusion (actor `system:analysis`, `previous_*` NULL, run link, `"[]"`). Claims equal the items verbatim. The GapItem and Conclusion natural keys are equal. The response carries `analysis_run_ids`.
2. **Re-run (the plan's test).** Two completed runs with distinct trigger ids. Conclusion ids are unchanged. The second revision is linked to run 2 with `previous_*` equal to run 1's proposal. Content comes from run 2 at version 2. An identical proposal is still recorded and still bumps the version.
3. **Human decisions.** Approved and edited Conclusions are byte-for-byte unchanged (including `updated_at`, `version` and `ai_proposed`) and get a `proposal_withheld` revision with the run link and citations, and disposition `withheld`. A reopened Conclusion is applied again. The legacy GapItem shows the new AI verdict.
4. **Lock rule.** Ten revision sequences produce the specified `locked` values. `expected_version` is correct. An unknown framework returns `{}`. The constants are exact.
5. **Citations.** A grounded quote gets one `text_span` citation to the right version, whose excerpt is the raw slice. A fabricated quote gets `"[]"`, `evidence_quote_grounded` False, `unsupported_assertion` True, and an empty `evidence_summary`. No quote gives `null`. Every revision stores an array that re-validates.
6. **Inputs.** Only the active v2 of kept Evidence is listed: not v1, and not archived Evidence. The legacy document id, response count and applicable list are recorded. A legacy-only quote is not citable.
7. **Evidence changes mid-run.** Another connection supersedes the cited version during the analyzer call. The result is 500, the run `failed` with `CitationError`, no new revision, the previous GapReport intact, and assessment `error`.
8. **Failures.** An analyzer exception gives `failed` with the class name only (the message is not stored). An empty result gives `EmptyAssessment`. Earlier rows are untouched. A 400-refused trigger creates no run. Across success, failure and success, no run, Conclusion or revision is ever deleted, and a requirement absent from a later run is left alone.
9. **Multi-framework.** Three runs share one trigger id. A framework error gives `FrameworkAnalysisError` and no Conclusions for that framework. The others complete with correctly scoped Conclusions and `gap_report_id`. A whole-call exception fails all three runs.
10. **Compare-and-swap.** A version bump between `load_conclusion_state` and the write gives 500 and `ConclusionConflict`, with nothing written.
11. **Quality, scope and dedupe.** Scope enforcement is recorded and gives `not_applicable`. Red-flag and absence counts and `desk_review_used` are recorded. `needs_review` is propagated. `contradictions` is `null`. A duplicate requirement produces one claim and one Conclusion. An unknown status maps to `insufficient_evidence`. `OUTCOME_BY_STATUS == migrate_legacy.OUTCOME_MAP`.
12. **Legacy path unchanged.** The response key set, the GapItems (draft, AI fields) and `scoring.score` all still work. The standing guards: no `Conclusion`/`AnalysisRun`/`analysis_pipeline` reference in scoring, review, reports, remediation or the PDF export; no `delete` in the pipeline module; no delete of the new tables in the router.
13. **Alembic.** The head is `4e8c1a9d2b57` on top of `3d8b6f0a2c51`, with the nullable FK column and its index, and the unique index (column order checked) enforced. The upgrade refuses on duplicate Conclusions and leaves the DB at `3d8b6f0a2c51`. The downgrade refuses while revisions link runs. Once cleared, it removes both and re-upgrades cleanly.
14. **`migrate_legacy` coexistence.** After two pipeline runs, `run_migration` doesn't crash, creates no Conclusions, revisions, Findings or Actions for that assessment, and emits the skip warning.
15. **Citation cost.** Each source text is normalized at most once across a run with six quotes over three sources, and every quote still gets its one citation.

## Done criteria

- `tests/test_analysis_pipeline.py` passes unmodified. `.venv/bin/pytest -q` passes in full, **392 = 363 + 29**, with the step 2 lockstep edits as the only changes to existing tests. (In a fresh worktree, also expect the pre-existing dev-DB guard teardown error described in Current state; nothing else.)
- `alembic heads` shows exactly `4e8c1a9d2b57`. The downgrade to `3d8b6f0a2c51` succeeds on an empty DB and refuses once a run has written revisions.
- `grep -rn "relationship(" app/models/` is empty. `git diff --stat` shows no change to `app/services/claude_analyzer.py`, `app/routers/review.py`, `app/services/scoring.py`, `app/utils/pdf_export.py`, `app/routers/reports.py`, `app/routers/remediation.py`, or any template or golden fixture.
- **Smoke test** (per the project rule; record the outputs). Use a **copy** of the dev DB, and the in-process ASGI fallback if the sandbox refuses a socket bind. Patch `app.routers.analysis.run_gap_analysis` to return two fixed items, one of them quoting text from an uploaded PDF. Then:
  1. `POST /assessments/{id}/run-analysis` twice. **Both** must succeed. The second one proves the re-run crash is fixed. On `main` today it ends in status `error`.
  2. `SELECT framework_id, status FROM analysis_runs WHERE assessment_id = ?` → two `completed` rows.
  3. `SELECT c.requirement_id, c.version, r.action, r.analysis_run_id IS NOT NULL, r.citations_json FROM conclusions c JOIN conclusion_revisions r ON r.conclusion_id = c.id WHERE c.assessment_id = ? ORDER BY c.requirement_id, r.created_at` → two `proposed` rows per requirement, version 2, and a `text_span` citation on the quoting requirement.
  4. Insert an `approved` revision for one Conclusion by hand, run a third time, and show that its row is unchanged and its newest revision is `proposal_withheld`.
  5. Show `GET /assessments/{id}?tab=report` still rendering, and the PDF export still downloading.

## Rollback

- **Code:** `git revert`. The reverted app never writes the new tables and ignores `conclusion_revisions.analysis_run_id` (SQLAlchemy doesn't select a column it doesn't map). The unique index stays but is harmless. Existing `analysis_runs`/`conclusions`/`conclusion_revisions` rows stay as inert history. **A revert also reverts step 5's flush, which re-breaks analysis re-runs.** If only the pipeline has to go, keep that one line.
- **Schema:** `alembic downgrade 3d8b6f0a2c51` refuses once any revision links a run. Either restore the P1-6 backup (`scripts/restore.py`), or `UPDATE conclusion_revisions SET analysis_run_id = NULL` (which loses the run ↔ revision link; the runs and revisions themselves survive) and then downgrade.
- **Data:** nothing in this task deletes or rewrites history. The only in-place writes are `applied` Conclusion updates, and each one is preceded by a revision carrying the prior outcome and rationale.

## Open questions (deliberately flagged, not resolved here)

1. **Moving readers off `GapItem`.** Scoring (PR-045: only approved Conclusions), the PDF and reports (PR-052: approved Conclusions only), and remediation should read Conclusions **after** P2-4 gives them individual approvals. This needs its own task, with its own `[AR: scoring semantics]` gate. Until then, the legacy report shows the latest AI verdict even for requirements whose Conclusion is locked.
2. **`contradictions` from the model.** Producing contradictions needs a prompt/output-schema change, and with it a re-recorded golden fixture. Until that task exists, the envelope says `null` (not assessed), never `[]`.
3. **Other LLM call sites.** The plan's LLM boundary says "all LLM calls produce AnalysisRun records". This task covers gap analysis only. Desk review, screening, RFI and vision are out of scope and would need a run type column to share the table.
4. **Mid-run evidence changes fail the run closed** (D-P2-3-D). Revisit if it turns out to be noisy in practice.
5. **Stale `running` runs after a process crash.** There is no sweeper. P2-6 should display runs older than the request timeout as stale.

## Handed forward to P2-4 (must be honoured there)

- Increment `Conclusion.version` on **every** human revision (approve, edit, reject, reopen). The pipeline's compare-and-swap relies on it (D-P2-3-C).
- `reopened` is the only way a new AI proposal reaches a locked Conclusion. Surface "newer AI proposal withheld" when the latest `proposal_withheld` revision is newer than the latest locking human revision. Its proposal is `claims[revision_id == that revision].item` in that run's envelope.
- The PR-043 approval guard reads the latest proposal revision's `citations_json`. `"[]"` means explicit absence of grounded support, `NULL` means not captured (legacy only).
- Decide whether a `migrate_legacy` `approved` revision (the product of a legacy bulk approve) counts as a D3 individual approval, or should be presented for re-approval.

## Results

### Shipped API

```python
CLAIMS_SCHEMA_VERSION = 1
PIPELINE_ACTOR = "system:analysis"
RUN_STATUSES = ("running", "completed", "failed")
OUTCOME_BY_STATUS = {
    "compliant": "compliant",
    "partially_compliant": "partially_compliant",
    "non_compliant": "non_compliant",
    "not_applicable": "not_applicable",
    "not_assessed": "insufficient_evidence",
}
UNKNOWN_STATUS_OUTCOME = "insufficient_evidence"
HUMAN_DECISION_ACTIONS = ("approved", "edited", "rejected", "reopened")
LOCKING_ACTIONS = ("approved", "edited")
SUPPORTING_OUTCOMES = ("compliant", "partially_compliant")

class AnalysisPipelineError(Exception): ...
class ConclusionConflict(AnalysisPipelineError):
    def __init__(self, conclusion_id: str): ...

@dataclass(frozen=True)
class RunContext:
    trigger_id: str
    run_ids: dict[str, str]
    sources: tuple[CitableSource, ...]

@dataclass(frozen=True)
class ConclusionState:
    conclusion: Conclusion
    locked: bool
    expected_version: int

def start_runs(db: Session, *, assessment_id: str, framework_ids: list[str]) -> RunContext: ...
def fail_runs(
    db: Session,
    context: RunContext,
    *,
    error_type: str,
    framework_ids: list[str] | None = None,
) -> None: ...
def load_conclusion_state(
    db: Session,
    *,
    assessment_id: str,
    framework_id: str,
) -> dict[str, ConclusionState]: ...
def record_framework_run(
    db: Session,
    context: RunContext,
    *,
    framework_id: str,
    assessments: list[dict],
    desk_review_data: dict | None,
    gap_report_id: str,
) -> AnalysisRun: ...
```

The citation memo signature is:

```python
def _normalized_source(text: str) -> tuple[str, array]: ...
```

The Alembic revision shipped as `4e8c1a9d2b57`, revising `3d8b6f0a2c51`. It
adds the nullable indexed `conclusion_revisions.analysis_run_id` foreign key,
the natural-key unique index on `conclusions`, and upgrade/downgrade guards.
`alembic heads` reports exactly `4e8c1a9d2b57 (head)`.

The existing-test edits match the step 2 table exactly: both probe templates
in `test_alembic_baseline_immutable.py`, three head assertions in
`test_data_integrity.py`, two startup assertions in `test_startup_invariants.py`,
and the two P2-2 head checks in `test_citations.py`. `tests/test_analysis_pipeline.py`
was not edited.

Other touched files:

- `app/models/conclusion.py`: ORM unique index and nullable run link.
- `app/services/analysis_pipeline.py`: immutable run/conclusion/revision service.
- `app/routers/analysis.py`: dual-write lifecycle, failure handling, response ids,
  and the two required delete-before-insert flushes.
- `app/services/citations.py`: bounded source normalization memoization.
- `scripts/migrate_legacy.py`: skip for assessments already owned by the pipeline.
- This handoff and `tasks/todo.md`: implementation tracking and results.

No protected legacy consumer, analyzer, template, or golden fixture changed.

### Verification

Focused contract suite:

```text
29 passed in 3.25s
```

Final full suite rerun:

```text
392 passed, 112 warnings in 23.52s
```

The first full-suite run in this fresh worktree produced the documented
one-time developer-database guard teardown error because `data/dpdpa.db` did
not yet exist; the immediate rerun stabilized that pre-existing artifact and
was fully green.

### ASGI smoke output

The smoke used an isolated Alembic-built SQLite database and an in-process
`TestClient`, with `run_gap_analysis` patched to two fixed items. The quoting
item cited an uploaded policy text span.

```text
POST_STATUS 200 200 200
RUNS_AFTER_TWO [('dpdpa', 'completed'), ('dpdpa', 'completed')]
REVISIONS_AFTER_TWO [
  ('CH2.CONSENT.1', 2, 'proposed', 1, '[{"evidence_version_id": "68486d0a-aeca-448b-8fb3-2e94301ba7eb", "excerpt": "obtains consent before processing", "location_ref": "chars:23-56", "location_type": "text_span"}]'),
  ('CH2.CONSENT.1', 2, 'proposed', 1, '[{"evidence_version_id": "68486d0a-aeca-448b-8fb3-2e94301ba7eb", "excerpt": "obtains consent before processing", "location_ref": "chars:23-56", "location_type": "text_span"}]'),
  ('CH2.CONSENT.2', 2, 'proposed', 1, '[]'),
  ('CH2.CONSENT.2', 2, 'proposed', 1, '[]')
]
LOCKED_CONCLUSION_BEFORE_THIRD {'id': 'dfc896e3-6d93-4e28-9ba4-74665d23c864', 'outcome': 'compliant', 'rationale': '[client text elided] consent process is documented', 'version': 2, 'updated_at': '2026-09-23 09:31:08.352746'}
LOCKED_CONCLUSION_AFTER_THIRD {'outcome': 'compliant', 'rationale': '[client text elided] consent process is documented', 'version': 2, 'updated_at': '2026-09-23 09:31:08.352746'}
LOCKED_NEWEST_ACTION proposal_withheld
RUNS_AFTER_THIRD [('dpdpa', 'completed'), ('dpdpa', 'completed'), ('dpdpa', 'completed')]
REPORT_PAGE 200 True
PDF 200 application/pdf 13068 attachment; filename="Compliance_Assessment_DPDPA_Smoke_Client.pdf"
```

The SQL used for the two-run history was:

```sql
SELECT framework_id, status FROM analysis_runs
WHERE assessment_id = ? ORDER BY started_at;

SELECT c.requirement_id, c.version, r.action,
       r.analysis_run_id IS NOT NULL, r.citations_json
FROM conclusions c
JOIN conclusion_revisions r ON r.conclusion_id = c.id
WHERE c.assessment_id = ?
ORDER BY c.requirement_id, r.created_at, r.rowid;
```

The result is pasted above: both triggers succeeded, both runs completed, and
the quoting requirement has a validated `text_span` citation. After inserting
an `approved` revision and triggering a third time, the locked row's outcome,
rationale, version, and `updated_at` stayed identical while its newest action
was `proposal_withheld`.

Sample `claims_json` (client text elided):

```json
{
  "claims": [
    {
      "cluster_id": "CLUSTER_029",
      "conclusion_id": "dfc896e3-6d93-4e28-9ba4-74665d23c864",
      "disposition": "created",
      "item": {
        "compliance_status": "compliant",
        "current_state": "[client text elided] consent process is documented",
        "evidence_quote": "obtains consent before processing",
        "gap_description": "No gap",
        "maturity_level": 4,
        "needs_review": false,
        "remediation_action": "None needed",
        "remediation_effort": "minimal",
        "remediation_priority": 1,
        "requirement_id": "CH2.CONSENT.1",
        "risk_level": "low",
        "root_cause_category": "process",
        "timeline_weeks": 0
      },
      "outcome": "compliant",
      "quality": {
        "citation_count": 1,
        "contradictions": null,
        "desk_review_absence": false,
        "desk_review_red_flags": 0,
        "evidence_quote_grounded": true,
        "needs_review": false,
        "unsupported_assertion": false
      },
      "requirement_id": "CH2.CONSENT.1",
      "revision_id": "61603dae-afed-43dc-9bae-26edf20c9dd5",
      "scope_enforced": false
    },
    {
      "cluster_id": "CLUSTER_029",
      "conclusion_id": "ab6a92db-b1b8-4262-a814-7d43d4bdf9d5",
      "disposition": "created",
      "item": {
        "compliance_status": "non_compliant",
        "current_state": "[client text elided] control is missing",
        "evidence_quote": "",
        "gap_description": "Policy gap",
        "maturity_level": 1,
        "needs_review": true,
        "remediation_action": "Create the control",
        "remediation_effort": "medium",
        "remediation_priority": 1,
        "requirement_id": "CH2.CONSENT.2",
        "risk_level": "high",
        "root_cause_category": "process",
        "timeline_weeks": 4
      },
      "outcome": "non_compliant",
      "quality": {
        "citation_count": 0,
        "contradictions": null,
        "desk_review_absence": false,
        "desk_review_red_flags": 0,
        "evidence_quote_grounded": null,
        "needs_review": true,
        "unsupported_assertion": false
      },
      "requirement_id": "CH2.CONSENT.2",
      "revision_id": "1fc94490-68d2-438f-9968-1f9b87025023",
      "scope_enforced": false
    }
  ],
  "desk_review_used": false,
  "error": null,
  "framework_id": "dpdpa",
  "gap_report_id": "a0c64c30-8a78-4d41-98f9-75767ba943e6",
  "inputs": {
    "applicable_requirements": null,
    "evidence_versions": [
      {
        "evidence_id": "92d06c46-ee13-456f-b059-eac24836cb19",
        "filename": "smoke-policy.pdf",
        "version_id": "68486d0a-aeca-448b-8fb3-2e94301ba7eb"
      }
    ],
    "legacy_document_ids": [],
    "questionnaire_response_count": 1
  },
  "model_tiers": {
    "extract": "deepseek/deepseek-v4-flash",
    "judge": "deepseek/deepseek-v4-flash",
    "synthesize": "deepseek/deepseek-v4-flash"
  },
  "schema_version": 1,
  "trigger_id": "0cba3637-d475-4c7a-a1c1-118763b30601"
}
```

No discrepancy was found between this document and the current code that
required an architectural deviation. Operationally, this fresh worktree had
no usable developer database to copy: the documented guard created a zero-byte
`data/dpdpa.db` artifact. The smoke therefore used a fresh isolated
Alembic-built SQLite database with the same schema, and did not touch the
developer database contents.

The requested local commit could not be created in this managed sandbox:
Git was denied permission to create
`.git/worktrees/p2-3-analysis-pipeline/index.lock` (`Operation not permitted`).
No push was attempted.
