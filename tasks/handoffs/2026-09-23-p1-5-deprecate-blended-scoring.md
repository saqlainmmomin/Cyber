# P1-5: Deprecate blended scoring — per-framework scores everywhere

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 1, task P1-5, plus the "What breaks and how we handle it" table (rows `compute_unified_maturity() removed` and `GapReport.overall_score removed from templates`).
**Owner:** Codex, from a Claude handoff (per `tasks/agent-ownership.md`). Note the ownership doc lists "no blended cross-framework score" under **product invariants** — the class of decision Claude owns. That is why every replacement shape below is pinned down here rather than left to implementation: the failure mode for this task is not a crash, it is a plausible-looking number that silently averages two incomparable frameworks.
**Depends on:** P1-2 (merged). Independent of P1-3 and P1-4 — it reads `GapReport.framework_scores`, a column that already exists and is already populated.
**Blocks:** Phase 1 exit ("Per-framework scoring, no blended score"), and P3-3 (PDF updates), which must not be written against a single-ring layout that P1-5 is about to delete.

## Goal

Delete the cross-framework average. After this task, every score the system computes, stores, displays, exports or returns over HTTP is attached to exactly one framework id. `compute_unified_maturity()` is gone; `GapReport.framework_scores` is the single source of truth for scores on every report, single- and multi-framework alike; `scoring.score()` accepts N frameworks and returns N scores with no scalar roll-up.

## Current state

Grounded against `main` at `a6d906d`. Re-locate everything by symbol name — the line numbers in the plan doc's P1-5 bullet (`web.py:1449-1510`) predate P1-1/P1-2 and have drifted.

### The blend is computed and persisted in `analysis.py`, which the plan bullet does not mention

**Flag this first: the plan's P1-5 bullet names only the comparison page, report summary and PDF export — all of which merely *display* the number. It omits the one place the blend is actually produced.** That is `app/routers/analysis.py`, in the multi-framework analysis path (search for `unified = compute_unified_maturity(`, currently ~line 491):

```python
unified = compute_unified_maturity(
    {fw_id: {"assessments": assmts} for fw_id, assmts in per_fw_assessments.items()},
    per_fw_scores,
)
...
report = GapReport(
    assessment_id=assessment_id,
    overall_score=unified["overall_score"],                       # ← the blend, persisted
    chapter_scores=json.dumps(unified.get("framework_scores", {})),  # ← see below
    framework_scores=json.dumps(per_fw_scores),
    ...
)
```

This is the only production caller of `compute_unified_maturity` in the codebase (`grep -rn compute_unified_maturity app/` returns its definition in `scoring.py`, its import at `analysis.py:19`, and this call). Fixing the display layers without fixing this leaves a blended number sitting in the database for every future consumer to rediscover.

### `chapter_scores` vs `framework_scores` — two columns, confusable names, different shapes

`app/models/report.py`:
```python
overall_score:    Mapped[float] = mapped_column(Float)              # NOT NULL
chapter_scores:   Mapped[str]   = mapped_column(Text)               # NOT NULL, JSON string
framework_scores: Mapped[str|None] = mapped_column(Text, nullable=True)
```

They are written differently by the two analysis paths, and **`chapter_scores` currently means two incompatible things**:

| | single-framework path (`analysis.py`, `scores = compute_scores(assessments)`) | multi-framework path (`analysis.py`, `unified`/`per_fw_scores`) |
|---|---|---|
| `overall_score` | `scores["overall_score"]` — the one framework's real score, 0–100 | `unified["overall_score"]` — **the blend**, mean of the frameworks' overall scores |
| `chapter_scores` | `scores["chapter_scores"]` = `compute_framework_scores(...)["domain_scores"]`, i.e. `{domain_key: {"score", "rating", "title", "applicable"}}` | `unified["framework_scores"]` = `per_fw_scores`, i.e. `{fw_id: {"overall_score", "overall_rating", "domain_scores"}}` — **a completely different shape wearing the same column** |
| `framework_scores` | **never written** (stays NULL) | `per_fw_scores` — the same dict as above, written a second time |

Two live consequences of that shape collision, both of which this task fixes as a side effect:
- `app/routers/reports.py` (`get_report`, `get_report_summary`) does `ChapterScore(**v)` for each value of `chapter_scores`. `ChapterScore` (`app/schemas/report.py`) requires `score: float, rating: str, title: str`. For a multi-framework report the values are `{"overall_score", "overall_rating", "domain_scores"}` → **pydantic `ValidationError`, HTTP 500.**
- `app/utils/pdf_export.py` reads `scores["score"]`, `scores["title"]`, `scores["rating"]` off each `chapter_scores` value (in the cover "Assessment Areas" bars and the page-2 heatmap) → **`KeyError` for a multi-framework report.**

### `scoring.score()` refuses multi-framework and has no production callers

`app/services/scoring.py`, `def score(assessment_id, framework_ids, *, _session=None) -> ScoringResult`:
```python
if len(framework_ids) != 1:
    raise NotImplementedError(
        "Cluster-backed scoring supports exactly one framework at a time; "
        "combining cluster verdicts across frameworks is WS #7's job"
    )
```
It resolves the framework's UCC control→cluster map via `_validated_cluster_mapping(framework_id)`, loads the assessment's `GapItem`s, collapses them to one verdict per cluster with `_build_cluster_verdicts(items, control_clusters)` (which **mutates** the map it is handed, recording each `requirement_id`'s cluster), derives a `FrameworkScore` with `_derive_framework_score(...)`, and wraps it in `CombinedScore` + `ScoringResult`. Note it also enforces `assessment.frameworks != framework_ids` by list equality, so argument order matters today.

`grep -rn "scoring.score\|import score" app/ scripts/` finds **no caller in `app/` or `scripts/`**. The only callers are `tests/test_golden_dpdpa.py`, `tests/test_picker_and_scoring_contract.py`, and `tests/support/fixture_capture.py`. So fixing `score()` is a contract fix, not a behaviour change to any live route — but its test suite is the contract and must be updated in lockstep.

`app/schemas/scoring.py` defines `CombinedScore` with its own `overall_score: float = Field(ge=0.0, le=5.0)` and `overall_rating` — i.e. the blended-scalar shape is baked into the schema, and `ScoringResult.validate_derived_views` asserts `combined.by_framework == per_framework` plus, for the single-framework case, that `combined.overall_score` equals the one framework's score.

### Every other reference (full grep, `app/` + `scripts/`, templates included)

| Location | Reference | Disposition |
|---|---|---|
| `app/services/scoring.py` `compute_unified_maturity` | definition | **delete** |
| `app/routers/analysis.py:19` | import | **delete** |
| `app/routers/analysis.py` multi-fw `GapReport(...)` | `overall_score=unified[...]`, `chapter_scores=json.dumps(unified.get("framework_scores"))` | **rewrite** (step 2) |
| `app/routers/analysis.py` single-fw `GapReport(...)` | `overall_score=scores["overall_score"]`, `chapter_scores=json.dumps(scores["chapter_scores"])` | **rewrite** (step 2) — also gains `framework_scores` |
| `app/routers/analysis.py` two `return {...}` dicts | `"overall_score": report.overall_score` | **remove the key**; multi-fw path already returns `per_framework_scores`, single-fw path gains it |
| `app/routers/web.py` `comparison_page` | `current_score`, `previous_score`, `score_delta = current - previous` | **rewrite** (step 4) |
| `app/routers/web.py` `report_summary` | `chapter_scores`, `framework_scores`, `framework_display` | **rewrite** (step 5) — already per-framework-aware, needs to become unconditional |
| `app/routers/reports.py` `get_report`, `get_report_summary`, `get_full_report` | `overall_score=report.overall_score`, `overall_rating=get_rating(report.overall_score)`, `ChapterScore(**v)` | **rewrite** (step 6) |
| `app/schemas/report.py` `ReportOut`, `ReportSummary` | `overall_score`, `overall_rating` fields | **replace** with `framework_scores` (step 6) |
| `app/schemas/scoring.py` `CombinedScore`, `ScoringResult` | blended scalar | **remove `CombinedScore`** (step 3) |
| `app/utils/pdf_export.py` | `get_rating(report.overall_score)`, `_draw_score_ring(..., report.overall_score, ...)`, `_draw_kpi_card(..., f"{report.overall_score:.0f}%", "Overall Score", ...)` | **rewrite** (step 7) |
| `app/templates/partials/report_summary.html:1` | `{% set score = report.overall_score %}` + the hero "Overall Score" gauge | **rewrite** (step 5) |
| `app/templates/pages/assessment.html` (tab pill) | `{{ report.overall_score \| round(1) }}%` | **rewrite** (step 5) |
| `app/templates/partials/analysis_complete.html` | `Overall compliance score: {{ report.overall_score \| round(1) }}%` | **rewrite** (step 5) |
| `app/templates/pages/comparison.html` | `score_delta`, `previous_score`, `current_score` | **rewrite** (step 4) |
| `app/models/report.py` | column definitions | **keep, annotate as deprecated** (step 1) |
| `app/legacy_migrations.py`, `app/legacy_migrations_schema.py` | historical DDL for the pre-Alembic path | **do not touch** — frozen history |

## Required approach

### 1. `overall_score` / `chapter_scores` — deprecated-but-kept, matching the project's "retired not deleted" convention

Both columns are `NOT NULL` in the live schema (`overall_score: Mapped[float]`, `chapter_scores: Mapped[str]`). Dropping or nulling them needs an Alembic migration, which **is explicitly out of scope for P1-5** — this task writes no migration. So:

- **`overall_score`: retired. Every write becomes the literal `0.0`; every read is deleted.** Add a comment on the column in `app/models/report.py`: `# DEPRECATED (P1-5): blended cross-framework score. Always written as 0.0. Never read, never displayed. Per-framework scores live in framework_scores. Column retained because dropping it needs a migration (out of scope for P1-5).` `0.0` rather than a `-1.0` sentinel because the column is a plain non-null `Float` with no range constraint to satisfy, and `0.0` needs no schema or pydantic change anywhere.
- **`chapter_scores`: kept, and its meaning is *fixed* to one shape.** It becomes, on both analysis paths, a `ChapterScore`-compatible dict namespaced by framework:
  ```
  {f"{fw_id}:{domain_key}": {"score": float, "rating": str,
                             "title": f"{framework_display_name} — {domain_title}",
                             "applicable": bool}}
  ```
  For a single-framework assessment this is the same data as today with a `dpdpa:` prefix on the keys and the framework name prepended to each title. This is what repairs the `ChapterScore(**v)` 500 and the PDF `KeyError` described above. Nothing else changes about how chapter scores are consumed.

### 2. `analysis.py` — stop producing the blend

Delete the `compute_unified_maturity` import and the `unified = compute_unified_maturity(...)` call. `unified["maturity_by_topic"]`, the only part of that function's output that is not a blend, has **zero consumers** (`grep -rn maturity_by_topic app/ tests/` finds only the three lines inside `compute_unified_maturity` itself) — do **not** extract or preserve it; delete it with the function and note the deliberate deletion in `## Results`.

Add one shared helper in `app/services/scoring.py`:
```python
def namespaced_domain_scores(per_framework_scores: dict[str, dict]) -> dict:
    """Flatten {fw_id: compute_framework_scores() output} into the single
    {f'{fw_id}:{domain_key}': ChapterScore-shaped dict} form stored in
    GapReport.chapter_scores. Never averages across frameworks."""
```
It resolves each framework's display name through `FrameworkRegistry.get_or_none(fw_id)`, falling back to `fw_id.upper()` — the pattern already used in `web.py` and `pdf_export.py`.

Both `GapReport(...)` constructions in `analysis.py` then become:
```python
report = GapReport(
    assessment_id=assessment_id,
    overall_score=0.0,                                        # DEPRECATED — see app/models/report.py
    chapter_scores=json.dumps(namespaced_domain_scores(per_fw_scores)),
    framework_scores=json.dumps(per_fw_scores),
    ...
)
```
For the single-framework path that means building `per_fw_scores = {fw_id: compute_framework_scores(assessments, fw_id)}` where `fw_id = assessment.frameworks[0]`, so **every report now has a populated `framework_scores`** — the whole point of the task. `compute_scores()` (the thin DPDPA wrapper at `scoring.py` ~line 356) stays for its other callers but is no longer what feeds the report row.

Both route return dicts drop `"overall_score"` and carry `"per_framework_scores": {fw_id: s["overall_score"] for fw_id, s in per_fw_scores.items()}` (the multi-framework path already builds exactly this; the single-framework path gains it).

### 3. `scoring.score()` — N frameworks, N scores, no roll-up

Replace the `NotImplementedError` guard with real multi-framework support. The UCC design already makes this straightforward: clusters are shared across frameworks by construction, so build the verdicts **once** from all of the assessment's gap items against the union of the frameworks' cluster maps, then project those verdicts onto each framework's own controls.

```python
def score(assessment_id, framework_ids, *, _session=None) -> ScoringResult:
    framework_ids = list(dict.fromkeys(framework_ids))          # dedupe, preserve order
    if not framework_ids:
        raise ValueError("score() requires at least one framework id")
    merged_clusters: dict[str, str] = {}
    for fw_id in framework_ids:
        merged_clusters.update(_validated_cluster_mapping(fw_id))   # keeps the per-framework coverage gate
    # ... load assessment + report + items exactly as today, except:
    if set(assessment.frameworks) != set(framework_ids):            # was list equality — order must stop mattering
        raise ValueError(f"Assessment is not configured for exactly {framework_ids}")
    cluster_verdicts, merged_clusters = _build_cluster_verdicts(items, merged_clusters)
    per_framework = {
        fw_id: _derive_framework_score(fw_id, cluster_verdicts, merged_clusters)
        for fw_id in framework_ids
    }
    return ScoringResult(
        per_framework=per_framework,
        cluster_verdicts=cluster_verdicts,
        unique_clusters=len(cluster_verdicts),
        total_controls_evaluated=sum(s.covered_control_count for s in per_framework.values()),
    )
```
`_derive_framework_score` already walks only its own framework's `all_controls()` and ignores clusters it has no control for, so no filtering of `items` by `framework_id` is needed or wanted — a gap item raised under ISO that maps to a shared cluster is *supposed* to inform the DPDPA projection of that cluster. That is the de-duplication the UCC exists for. Summing `covered_control_count` across frameworks does not double-count, because each framework contributes its own distinct control ids.

`app/schemas/scoring.py`: **delete `CombinedScore` entirely** — it is the blended-scalar shape in type form. `ScoringResult` becomes `{per_framework: dict[str, FrameworkScore], cluster_verdicts: dict[str, ClusterVerdict], unique_clusters: int (ge=0), total_controls_evaluated: int (ge=0)}`. Its `validate_derived_views` keeps the `unique_clusters == len(cluster_verdicts)` and per-framework-key checks and drops every `combined.*` assertion. `FrameworkScore` is unchanged (its `overall_score` is one framework's score — legitimate).

Update the three existing callers in lockstep: `tests/test_golden_dpdpa.py`, `tests/test_picker_and_scoring_contract.py` (which contains an explicit `pytest.raises(NotImplementedError)` on the two-framework call — that test inverts into a positive assertion that two frameworks yield two `per_framework` entries), and `tests/support/fixture_capture.py`.

### 4. Comparison page — a per-framework delta dict, not a scalar

`app/routers/web.py`, `def comparison_page`. Replace the three context keys `current_score` / `previous_score` / `score_delta` with one:

```python
"framework_deltas": [
    {"framework_id": fw_id,
     "name": <registry display name, fallback fw_id.upper()>,
     "current": float, "previous": float, "delta": round(current - previous, 1)}
    for fw_id in <ordered framework ids>
]
```
Ordered framework ids = the *current* assessment's `assessment.frameworks` order. Scores come from a new shared reader (step 8) applied to `current_report` and `previous_report`. A framework present in one report and not the other gets `None` for the missing side and `None` for `delta`; the template renders `—` for those. Never fall back to `report.overall_score`.

`app/templates/pages/comparison.html` replaces the single delta block (the `{% if score_delta > 0 %}` colouring and the `{{ previous_score }}% → {{ current_score }}%` line) with one row per entry in `framework_deltas`, each carrying the same green/red/grey colouring logic keyed off that row's own `delta`. Keep `deltas` / `delta_summary` (the per-requirement `compute_delta` output) untouched — that is already framework-agnostic and is not a score.

### 5. Report summary and the other HTML surfaces — one visual element per framework

`app/routers/web.py`, `def report_summary`: it already builds `framework_display` from `report.framework_scores`. Two changes: (a) build it through the step-8 reader so a legacy NULL-`framework_scores` row still resolves; (b) make it unconditional — drop the `if scores or view_mode == "per_framework"` gate so a single-framework assessment gets an entry too. Keep the `combined` / `per_framework` view toggle: `combined` now means "all frameworks' domain bars in one list" (which is what the namespaced `chapter_scores` already gives), **not** "one blended number".

`app/templates/partials/report_summary.html`:
- Delete `{% set score = report.overall_score %}` and the hero "Overall Score" gauge card (the first card in the `A. Hero Metrics Row` grid).
- Replace it with the existing per-framework ring markup from the `C2. Per-Framework Scores` block, promoted into the hero row: one ring per entry in `framework_display`, each labelled with the framework name and its own `overall_rating`. Keep the existing `fw_color` / `fw_circ` / `fw_offset` computations verbatim — they are already per-framework and correct.
- The hero grid's column count becomes `grid-cols-2 md:grid-cols-{{ [framework_display | length + 3, 4] | min }}` so a 1-framework report keeps today's 4-card row and a 3-framework report wraps instead of squashing.
- Remove the now-duplicated `C2` block (its content moved up), keeping the view-mode toggle links above it.

`app/templates/pages/assessment.html`: the report tab pill `{{ report.overall_score | round(1) }}%` becomes the count of frameworks scored, e.g. `{{ framework_display | length }} framework{{ 's' if framework_display | length != 1 }}` — a pill is too small for N numbers, and any single number there would be a blend by another name.

`app/templates/partials/analysis_complete.html`: `Overall compliance score: <strong>{{ report.overall_score }}%</strong>` becomes one `<span>` per framework: `{{ name }} {{ score | round(0) | int }}%`, comma-separated. This partial is rendered from the analysis-complete HTMX swap, so the route that renders it must pass the per-framework dict — thread it through from wherever the partial is rendered (`grep -rn analysis_complete.html app/routers/`).

### 6. JSON API — no blended field in any response

`app/schemas/report.py`: on both `ReportOut` and `ReportSummary`, delete `overall_score: float` and `overall_rating: str`, and add
`framework_scores: dict[str, FrameworkScoreOut]` where `FrameworkScoreOut` is a new model `{overall_score: float, overall_rating: str, domain_scores: dict[str, ChapterScore]}`. `ChapterScore` is unchanged. `chapter_scores: dict[str, ChapterScore]` stays and now parses cleanly for multi-framework reports thanks to step 1's namespacing.

`app/routers/reports.py`: `get_report` and `get_report_summary` stop passing `overall_score`/`overall_rating` and pass `framework_scores` from the step-8 reader. `get_full_report` drops its `"overall_score"` and `"overall_rating"` keys; its `"frameworks"` key already carries the per-framework breakdown and is unchanged.

This is a breaking API change to three endpoints. It is intended and is the plan's own stated acceptance criterion ("No blended score in UI, PDF, or **API responses**"). There are no external consumers — the app is single-user with no auth — so no deprecation window is warranted; just make the change and list the three endpoints in `## Results`.

### 7. PDF export — one score element per framework, no total anywhere

`app/utils/pdf_export.py`. Remove `overall_rating = get_rating(report.overall_score)` and read `framework_scores` via the step-8 reader into an ordered list of `(fw_id, display_name, overall_score, overall_rating)`.

- **Cover page.** Replace the single centred `_draw_score_ring(pdf, PW/2, 130, 30, report.overall_score, overall_rating)` with one ring per framework, evenly spaced across `CW` and vertically centred at `cy = 130`. Deterministic sizing so there is nothing to judge: radius `30` for N == 1, `22` for N in {2, 3}, `18` for N ≥ 4; ring `i` of `N` is centred at `cx = PM + CW * (i + 0.5) / N`. Below each ring, the framework display name at `Helvetica 8`, centred, passed through `S()` (the latin-1 sanitizer — **every** new PDF string in this task goes through `S()`, per the project gotcha; a missing `S()` crashes fpdf2).
- **Page 2 (Executive Dashboard) KPI row.** The 4-card row loses its "Overall Score" card and becomes a fixed **3**-card row — Critical Gaps, High Risk Gaps, Remediation Timeline — with `card_w = (CW - 6) / 3`. Directly beneath it, add a new `_section_title(pdf, "Framework Scores")` followed by one `_draw_h_bar(pdf, PM, y, CW, 8, fw_score, S(fw_name), fw_rating)` per framework, `y += 11` between bars. Fixed layout, no branching on N — a 1-framework report gets a single-bar section, which reads fine.
- **Cover "Assessment Areas" bars and the page-2 heatmap** iterate `chapter_scores.items()` reading `scores["score"]/["title"]/["rating"]`. They need **no code change** — step 1's namespacing makes those keys present for multi-framework reports for the first time (today it is a `KeyError`). Their titles now read e.g. `ISO 27001 — Organizational Controls`.

### 8. One reader, one legacy fallback

Add to `app/services/scoring.py`:
```python
def report_framework_scores(report, assessment) -> dict[str, dict]:
    """The per-framework scores for a GapReport: {fw_id: compute_framework_scores() output}.

    Parses GapReport.framework_scores. For legacy rows written before P1-5
    (framework_scores NULL) on a single-framework assessment, reconstructs one
    entry from the retired overall_score/chapter_scores columns. This function
    is the ONLY place in app/ permitted to read GapReport.overall_score.
    """
```
Behaviour: parse `report.framework_scores`; on success return it. On NULL/`JSONDecodeError`: if `len(assessment.frameworks) == 1`, return `{assessment.frameworks[0]: {"overall_score": report.overall_score, "overall_rating": get_rating(report.overall_score), "domain_scores": json.loads(report.chapter_scores or "{}")}}`; if multi-framework, return `{}` (there is no honest way to un-blend a legacy multi-framework row — callers render "scores unavailable, re-run analysis").

Every surface in steps 4–7 reads through this one function. After P1-5 no new row ever hits the fallback, since step 2 populates `framework_scores` on both paths.

## Key files

| File | Why it matters |
|---|---|
| `app/services/scoring.py` | `compute_unified_maturity` (delete), `score()` (multi-framework fix), plus the two new helpers `namespaced_domain_scores` and `report_framework_scores`. `compute_framework_scores` is the canonical per-framework shape and is **not** modified. |
| `app/routers/analysis.py` | Where the blend is computed and persisted — the caller the plan's bullet misses. Both `GapReport(...)` constructions and both return dicts. |
| `app/schemas/scoring.py` | `CombinedScore` (delete), `ScoringResult` (reshape), `FrameworkScore` (keep). |
| `app/schemas/report.py` | `ReportOut`/`ReportSummary` field swap; `ChapterScore` is the shape `chapter_scores` must conform to. |
| `app/routers/reports.py` | Three JSON endpoints; also where `ChapterScore(**v)` currently 500s on a multi-framework report. |
| `app/routers/web.py` | `comparison_page` (scalar delta → per-framework list) and `report_summary` (`framework_display` becomes unconditional). |
| `app/utils/pdf_export.py` | Cover ring, page-2 KPI card, and the `chapter_scores` consumers that the namespacing repairs. **All text through `S()`.** |
| `app/templates/partials/report_summary.html` | Hero gauge → per-framework rings; the existing `C2` block is the markup to promote. |
| `app/templates/pages/comparison.html`, `pages/assessment.html`, `partials/analysis_complete.html` | The three remaining `overall_score` Jinja references. |
| `app/models/report.py` | Where the deprecation comment lands; the columns are not dropped. |
| `tests/test_picker_and_scoring_contract.py`, `tests/test_golden_dpdpa.py`, `tests/support/fixture_capture.py` | The only `score()` callers; the contract tests encode the `NotImplementedError` that this task removes. |

## Non-goals

- Do **not** write an Alembic migration. `overall_score` and `chapter_scores` stay in the schema. Dropping `overall_score` is a separate, later task once a release has shipped with nothing reading it.
- Do **not** add per-`AssessmentPack` score storage. P1-3's `## Results` records decision **D-A**: `GapReport.framework_scores` stays authoritative and no score column is added to `AssessmentPack`; a later phase resolves it. P1-5 consumes that decision, it does not revisit it.
- Do **not** touch `app/legacy_migrations.py` / `app/legacy_migrations_schema.py` — frozen pre-Alembic history.
- Do **not** attempt to back-fill `framework_scores` on existing rows. The step-8 fallback covers legacy single-framework rows at read time; legacy multi-framework rows (if any exist) render "re-run analysis".
- Do **not** introduce a weighted cross-framework score as a "better" blend. The product invariant is that no such number exists, not that the current averaging is badly weighted.
- Do **not** fix the pre-existing mismatch between `GapItem.chapter` (which holds `control.reference`) and `chapter_scores`' domain keys in the PDF appendix (`chapter_scores.get(chapter_key, {}).get("title", chapter_key)`). It already misses and already falls back gracefully; namespacing changes nothing about that. Out of scope — note it in `## Results` so it stays visible.
- Do **not** change `compute_framework_scores()`'s algorithm or output shape. It is the fixed point everything else is expressed in.

## Test scenarios

Extend `tests/test_picker_and_scoring_contract.py` for the `score()` contract changes; add `tests/test_no_blended_scoring.py` for the invariant and the persistence/display behaviour.

1. **The blend is never persisted.** Run the multi-framework analysis path (mocked LLM, per the PW-4 harness) on a 2-framework assessment. Assert the resulting `GapReport` has `overall_score == 0.0`, `framework_scores` parsing to a dict with exactly those 2 framework ids, and each entry carrying `overall_score`/`overall_rating`/`domain_scores`. Assert that `0.0` is not coincidentally the mean: seed statuses so both frameworks score well above zero, and assert both per-framework `overall_score`s are `> 0`.
2. **Single-framework analysis now populates `framework_scores` too, and still scores correctly (regression guard).** Run the single-framework path on a `dpdpa` assessment. Assert `framework_scores` is non-NULL with exactly one key `"dpdpa"`, that its `overall_score` equals `compute_framework_scores(assessments, "dpdpa")["overall_score"]` computed independently in the test, and that `overall_score` on the row is `0.0`.
3. **`chapter_scores` has one shape on both paths.** For both the reports from scenarios 1 and 2, assert every key matches `^[a-z0-9_]+:.+$` (framework-namespaced), every value has exactly the keys `score`/`rating`/`title`/`applicable`, and `ChapterScore(**v)` constructs without error for every value. Assert the multi-framework report's keys cover both frameworks' domains.
4. **`compute_unified_maturity` is gone, with no callers.** A grep-based test: `grep -rn "compute_unified_maturity" app/ scripts/` returns nothing, and `from app.services.scoring import compute_unified_maturity` raises `ImportError`. Same grep for `maturity_by_topic`.
5. **No surface in `app/` reads `GapReport.overall_score` except the one permitted reader.** Grep-based: every hit for `overall_score` in `app/**/*.py` and `app/templates/**/*.html` is in the allow-list `{app/models/report.py, app/services/scoring.py, app/schemas/scoring.py, app/legacy_migrations.py, app/legacy_migrations_schema.py, app/routers/analysis.py}` — and within `analysis.py` the only occurrences are the literal `overall_score=0.0` writes and the per-framework dict comprehension. Assert zero hits in `app/templates/`. This test is the standing guard against the blend creeping back.
6. **Comparison page shows a per-framework delta.** Seed two completed assessments for the same `company_name`, both 2-framework, with deliberately different per-framework scores (e.g. framework A improves, framework B regresses). `GET /assessments/{new}/compare/{old}` is 200; the context/HTML contains one delta row per framework with the correct sign per framework, and contains **no** single combined delta. Assert specifically that the two frameworks' deltas have opposite signs and that no rendered number equals their mean.
7. **Comparison handles a framework present in only one report.** Old report has `{dpdpa}`, new has `{dpdpa, iso27001}`. The page renders 200 with `iso27001`'s `previous`/`delta` as `None`, displayed as `—`, and does not raise.
8. **PDF: one score section per framework, no blended total.** Generate the PDF for the 2-framework report from scenario 1. Assert it generates without exception (today this is a `KeyError` on `chapter_scores`), that extracted text contains both framework display names, and contains no "Overall Score" label. Repeat for the single-framework report from scenario 2 — it must still generate and contain that one framework's name (regression guard). Assert every framework's rounded score string appears in the extracted text.
9. **JSON API carries no blended field.** `GET /assessments/{id}/report`, `/report/summary` and `/report/full` (via the HTTP harness, with review approval satisfied — these routes go through `require_review_approval`) for both a single- and a multi-framework assessment: all six responses are 200, none contains an `overall_score` or `overall_rating` key at the top level, and each contains a `framework_scores`/`frameworks` object keyed by framework id. The multi-framework `/report` and `/report/summary` calls are the ones that return 500 today — they are the regression this scenario locks in.
10. **`score()` handles N frameworks without blending.** `score(assessment_id, ["dpdpa", "iso27001"])` on a 2-framework assessment returns a `ScoringResult` with 2 `per_framework` entries, each a `FrameworkScore` whose `framework_id` matches its key, and `unique_clusters == len(cluster_verdicts)`. Assert `ScoringResult` has **no** `combined` attribute and `CombinedScore` no longer exists in `app.schemas.scoring`. Assert the two frameworks' `overall_score`s are independent (seed so they differ) and that no returned field equals their mean.
11. **`score()` argument-order and dedupe.** `score(id, ["iso27001", "dpdpa"])` and `score(id, ["dpdpa", "iso27001"])` on the same assessment return equal `per_framework` dicts (set-based config check, not list equality). `score(id, ["dpdpa", "dpdpa"])` on a single-framework assessment succeeds with one entry. `score(id, [])` raises `ValueError`. `score(id, ["dpdpa"])` on a 2-framework assessment still raises `ValueError` (config mismatch), and the unregistered-framework and missing-assessment cases keep their existing behaviour.
12. **Shared clusters are scored once, not double-counted.** Using a UCC cluster that maps controls in both `dpdpa` and `iso27001`, seed one `GapItem` that resolves to it. Assert the single cluster produces exactly one entry in `cluster_verdicts` while contributing to both frameworks' `covered_control_count` — i.e. `unique_clusters` counts clusters and `total_controls_evaluated` counts controls, and `total_controls_evaluated > unique_clusters` for the multi-framework case.
13. **Legacy-row fallback.** Construct a `GapReport` by hand with `framework_scores=None`, a real `overall_score` and a real single-framework `chapter_scores` (i.e. the pre-P1-5 row shape) on a `dpdpa` assessment. `report_framework_scores(report, assessment)` returns one entry reconstructing that score. The same with a 2-framework assessment returns `{}`, and `GET /assessments/{id}/report-summary` renders 200 with a "scores unavailable" message rather than raising.

## Done criteria

- `grep -rn "compute_unified_maturity" app/ scripts/` is empty; the function and its import are deleted.
- `grep -rn "overall_score" app/templates/` is empty.
- Every `GapReport` written by either analysis path has `overall_score == 0.0` and a non-NULL `framework_scores` containing one entry per selected framework.
- `scoring.score()` accepts any number of registered frameworks; `CombinedScore` no longer exists; `ScoringResult` exposes no cross-framework scalar.
- The three JSON report endpoints, the report summary partial, the comparison page and the PDF all render per-framework scores for a 2-framework assessment, and a 1-framework assessment is byte-for-byte sensible (regression guard, scenarios 2 / 8 / 9).
- `pytest -q` passes in full — including the updated `tests/test_picker_and_scoring_contract.py` and `tests/test_golden_dpdpa.py`, and `tests/support/fixture_capture.py` still produces its fixtures.
- Smoke-tested live per the project's smoke-test rule: run a mocked multi-framework analysis in the running app, open the report tab, open the comparison page against a prior run, and download the PDF — confirm by eye that no single combined percentage appears on any of the three.

## Rollback

Application code and schemas only; no migration, no data transformation of existing rows. `git revert` the commit. Reports written *while* P1-5 is in effect carry `overall_score = 0.0`; a revert would make those rows display `0%` on the old blended surfaces, so if the commit is reverted after any analysis run, re-run the analysis for the affected assessments (the re-run path already preserves prior state in `GapReport.legacy_history`, per PW-2).

## Report back

Append a `## Results` section containing:
- The final disposition table for every `overall_score` / `chapter_scores` / `compute_unified_maturity` / `framework_scores` reference (file → what happened), so the grep-based guard in scenario 5 can be checked against it by eye.
- The exact `chapter_scores` key format as implemented, with one real example key/value pair from a multi-framework run.
- Confirmation that `maturity_by_topic` was deleted rather than preserved, and that no consumer existed.
- The `ScoringResult` / `CombinedScore` schema diff, and the list of test files updated to match.
- The three JSON endpoints whose response shape changed, with a before/after key list for one of them.
- A note on the PDF: number of rings rendered on the cover for the multi-framework smoke test, and confirmation that every new string goes through `S()`.
- Anything this document got wrong about the current code (a drifted symbol, a reference the grep above missed) — name it explicitly rather than silently working around it.
