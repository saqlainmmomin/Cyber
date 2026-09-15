# WS #4 — Framework-agnostic scoring + the multi-framework scope-exclusion gap

**Date:** 2026-09-15
**Branch:** `ws/4-framework-agnostic-scoring`, off `main` at `bbe08f8`
**Owner:** Codex (mechanical refactor, spec below is unambiguous — do not redesign)
**Context:** `tasks/multi-framework-demo-plan.md` §2 (original WS #4) and §9 (2026-09-15
status audit + reprioritization). This is now the highest-priority workstream: it's
the direct unblock for multi-framework assessments getting real cluster-based scoring
instead of a hardcoded `NotImplementedError`.

---

## Goal

Two independent fixes, same PR, both protected by the existing golden-test suite:

1. **Generalize the cluster-verdict scoring engine** in `app/services/scoring.py` so
   `score()` works for any single registered framework (DPDPA, ISO 27001, or NIST CSF),
   not only `["dpdpa"]` — while still correctly rejecting `len(framework_ids) > 1`,
   because combining cluster verdicts *across* frameworks into one number is WS #7's
   problem (the per-cluster analyzer), not this workstream's.
2. **Fix the scope-exclusion no-op** in `app/services/question_engine.py` so that a
   multi-framework assessment's scope answers (`Assessment.applicable_requirements`)
   actually exclude out-of-scope controls from the questionnaire, instead of every
   control from every selected framework always appearing regardless of scope.

Both fixes must produce **byte-identical output for DPDPA-only assessments** — that's
what the golden tests exist to prove.

---

## Files in scope

- `app/services/scoring.py` — `compute_scores()` (lines 308-385), `_build_cluster_verdicts()`
  (54-110), `_derive_dpdpa_score()` (113-155), `score()` (158-215).
- `app/services/question_engine.py` — `_build_multi_framework_questionnaire()` (54-139),
  specifically the `excluded` computation at lines 61-65.
- `tests/test_picker_and_scoring_contract.py` — three tests listed under "Tests you must
  update, not just satisfy" below. This is expected, not incidental — read that section
  before touching source.
- Do not touch `app/services/screening.py`, `app/routers/analysis.py`, or
  `app/routers/reports.py` — see Non-goals.

---

## Part 1 — Generalize `scoring.py`

### 1a. Collapse `compute_scores()` into a thin wrapper over `compute_framework_scores()`

`compute_scores()` (lines 308-385) and `compute_framework_scores()` (lines 573-633) are
near-duplicate implementations of the same weighted-average algorithm — the only real
difference is `compute_scores()` reads the hardcoded `DPDPA_FRAMEWORK` dict
(`from app.dpdpa.framework import DPDPA_FRAMEWORK`, line 12) and returns a
`chapter_scores` key, while `compute_framework_scores()` reads from
`FrameworkRegistry.get(framework_id).as_legacy_framework_dict()` and returns a
`domain_scores` key. `as_legacy_framework_dict()` (`app/frameworks/schema.py:136-166`) was
purpose-built to produce the identical nested shape `DPDPA_FRAMEWORK` has, so the two
functions are provably interchangeable for `framework_id="dpdpa"`.

Replace the body of `compute_scores()` with:

```python
def compute_scores(assessments: list[dict]) -> dict:
    """Weighted DPDPA compliance score. Thin wrapper — see compute_framework_scores()."""
    result = compute_framework_scores(assessments, "dpdpa")
    return {
        "overall_score": result["overall_score"],
        "overall_rating": result["overall_rating"],
        "chapter_scores": result["domain_scores"],
    }
```

This removes the `DPDPA_FRAMEWORK` import from the scoring logic entirely (line 12
becomes `from app.dpdpa.framework import ROOT_CAUSE_CLUSTERS, get_all_requirements` —
`get_all_requirements` is still used elsewhere in this file if so, check; `ROOT_CAUSE_CLUSTERS`
stays, it's legitimately DPDPA-only and out of scope, see Non-goals).

**Do not change `compute_framework_scores()` itself** — it's already framework-agnostic
and is the thing `compute_scores()` now delegates to.

### 1b. Generalize `_build_cluster_verdicts()` to take a `framework_id`

Current signature (line 54): `_build_cluster_verdicts(items: list) -> tuple[dict, dict[str, str]]`.
Line 71 hardcodes `if member["framework"] == "dpdpa":` when building the `control_clusters`
lookup — meaning for any non-DPDPA item, `control_clusters.get(item.requirement_id)` always
returns `None`, and every control silently falls through to its own `SINGLE.{requirement_id}`
cluster (line 77) instead of the real shared UCC cluster. This is the actual bug: ISO/NIST
items never get real cluster grouping today, they just look like they do because the
fallback silently produces a plausible-looking cluster ID.

Change the signature to `_build_cluster_verdicts(items: list, framework_id: str) -> tuple[dict, dict[str, str]]`
and change line 71 to `if member["framework"] == framework_id:`. Nothing else in the
function needs to change — the rest of the grouping/worst-case-verdict logic (lines 73-110)
is already framework-agnostic (it operates on `item.requirement_id`, `item.compliance_status`,
`item.gap_description`, none of which are DPDPA-specific fields).

### 1c. Generalize `_derive_dpdpa_score()` → `_derive_framework_score()`

Current signature (line 113): `_derive_dpdpa_score(cluster_verdicts, control_clusters)`,
hardcodes `FrameworkRegistry.get("dpdpa")` (line 117) and calls `compute_scores(propagated)`
(line 140, which per 1a now always scores against DPDPA regardless of `propagated`'s actual
controls — this must be fixed as part of this change, not left as a latent bug).

Rename to `_derive_framework_score(framework_id: str, cluster_verdicts, control_clusters)`,
and:
- Replace `FrameworkRegistry.get("dpdpa")` → `FrameworkRegistry.get(framework_id)`.
- Replace `legacy_score = compute_scores(propagated)` → `legacy_score = compute_framework_scores(propagated, framework_id)`,
  and read `legacy_score["domain_scores"]` directly (not `["chapter_scores"]`) — this
  also means the `/20` rescale logic (lines 141-146) stays as-is since
  `compute_framework_scores()` returns 0-100 scores exactly like `compute_scores()` did.
- Replace the hardcoded `framework_id="dpdpa"` in the returned `FrameworkScore` (line 148)
  with the `framework_id` parameter.

### 1d. Generalize `score()` — single-framework only, multi-framework still rejected

Current guard (lines 174-177):
```python
if framework_ids != ["dpdpa"]:
    raise NotImplementedError(
        "Cluster-backed scoring is currently available only for DPDPA-only assessments"
    )
```

Replace with:
```python
if len(framework_ids) != 1:
    raise NotImplementedError(
        "Cluster-backed scoring supports exactly one framework at a time; "
        "combining cluster verdicts across frameworks is WS #7's job"
    )
framework_id = framework_ids[0]
```

Then, in the body (lines 179-215):
- Line 185: `if assessment.frameworks != ["dpdpa"]:` → `if assessment.frameworks != framework_ids:`
  and generalize the error message from `"Assessment is not configured as DPDPA-only"` to
  `f"Assessment is not configured for exactly {framework_ids}"`.
- Line 201: `_build_cluster_verdicts(items)` → `_build_cluster_verdicts(items, framework_id)`.
- Line 202: `_derive_dpdpa_score(cluster_verdicts, control_clusters)` → `_derive_framework_score(framework_id, cluster_verdicts, control_clusters)`.
- Line 203: `per_framework = {"dpdpa": framework_score}` → `per_framework = {framework_id: framework_score}`.

Everything below that (the `CombinedScore`/`ScoringResult` construction, lines 204-215)
is already generic — no change needed.

---

## Part 2 — Fix the scope-exclusion no-op

`app/services/question_engine.py:61-65`:

```python
excluded: set[str] | None = None
if assessment.applicable_requirements:
    try:
        applicable = set(json.loads(assessment.applicable_requirements))
        excluded = None  # UCC engine uses include-list differently — pass None for now
    except (json.JSONDecodeError, TypeError):
        pass
```

`applicable_requirements` is an **include-list** (built by `compute_scope_multi()`,
`app/services/scope_profiler.py:276-313` — a flat list of control IDs that survived scope
filtering, combined across every selected framework). `resolve_clusters()` and
`build_multi_questionnaire()` (`app/frameworks/cluster_engine.py:113`,
`app/frameworks/questionnaire_builder.py:31`) both take `excluded_controls: set[str] | None`
— an **exclude-list**. The fix is a set-difference against the full control universe for
the selected frameworks:

```python
excluded: set[str] | None = None
if assessment.applicable_requirements:
    try:
        applicable = set(json.loads(assessment.applicable_requirements))
        all_controls = {
            control.id
            for fw_id in framework_ids
            for control in FrameworkRegistry.get(fw_id).all_controls()
        }
        excluded = all_controls - applicable
    except (json.JSONDecodeError, TypeError):
        pass
```

You'll need `from app.frameworks.registry import FrameworkRegistry` at the top of
`question_engine.py` (not currently imported there).

**Edge case to verify by test, not by inspection:** if `applicable_requirements` is an
empty list (all scope answers said "no" — legitimately zero controls apply), `excluded`
should equal the full control universe, i.e. every question skipped. Confirm
`resolve_clusters()` degrades gracefully to an empty cluster list rather than erroring
when every control is excluded (read `cluster_engine.py:113-195` — it should, since it
just produces zero clusters, but add a test for it, don't assume).

---

## Interfaces after this change

- `scoring.compute_scores(assessments: list[dict]) -> dict` — **unchanged signature and
  output shape.** Internals now delegate to `compute_framework_scores`.
- `scoring._build_cluster_verdicts(items: list, framework_id: str) -> tuple[dict, dict[str,str]]` —
  **new required parameter.**
- `scoring._derive_framework_score(framework_id: str, cluster_verdicts: dict, control_clusters: dict[str,str]) -> FrameworkScore` —
  **renamed from `_derive_dpdpa_score`, new required first parameter.**
- `scoring.score(assessment_id, framework_ids: list[str], *, _session=None) -> ScoringResult` —
  **same signature.** Now accepts any single registered framework ID, not just `["dpdpa"]`.
  Still raises `NotImplementedError` for `len(framework_ids) != 1`.
- `question_engine._build_multi_framework_questionnaire()` — **no signature change.**
  Internal behavior only: scope exclusion now actually applies.

---

## Non-goals (do not touch, do not redesign)

- **`app/services/screening.py` stays DPDPA-only.** `run_screening_pass()` has no
  `framework_ids` parameter and none should be added in this workstream. Generalizing
  domain screening to ISO 27001/NIST CSF requires *designing new domain-question content*
  for those frameworks (or redesigning screening to be cluster-based instead of
  requirement-based) — that's judgment/content work for Claude or Saqlain first, the
  same way WS #6's cluster mappings were, not a mechanical refactor. If you find yourself
  needing to touch this file to make something else work, stop and flag it instead of
  improvising a domain-question set.
- **`app/routers/analysis.py` and `generate_initiatives()`/`ROOT_CAUSE_CLUSTERS` stay as
  they are.** The legacy single-framework analysis path is *supposed* to be DPDPA-specific
  by design (it's the pre-multi-framework code path, kept for backward compatibility) —
  it is not a bug that it imports `app.dpdpa.framework` directly. Do not "fix" it.
- **`app/routers/reports.py:8`'s direct `app.dpdpa.framework` import** is real cleanup
  debt (tracked as WS #10 in the plan) but is unrelated to scoring or the questionnaire —
  leave it for that separate, smaller PR.
- **Do not attempt cross-framework combined cluster scoring** (i.e. don't try to make
  `score()` accept `["dpdpa", "iso27001"]` and produce one blended verdict). That's WS #7.
- **`GapItem.cluster_id` persistence is not part of this workstream.** `_build_cluster_verdicts`'s
  fallback chain (`item.cluster_id or control_clusters.get(item.requirement_id) or ...`)
  works correctly via the `control_clusters` lookup alone once 1b lands — you do not need
  to make `analysis.py` start populating `GapItem.cluster_id` for multi-framework items to
  satisfy this handoff's done criteria.

---

## Tests you must update, not just satisfy

Three existing tests in `tests/test_picker_and_scoring_contract.py` assert the *old*,
narrower contract. Their assertions must change to reflect the new, intentionally wider
contract — this is expected scope, not an accidental regression:

1. **`test_scoring_wrapper_does_not_fabricate_other_frameworks`** (line 279) currently
   asserts `score(assessment.id, ["iso27001"], ...)` raises `NotImplementedError`. After
   this change it should succeed and return a real `ScoringResult` for the ISO-only
   assessment (build a minimal ISO gap-item fixture the same way
   `test_scoring_collapses_mapped_controls_and_matches_legacy_semantics` does for DPDPA,
   using a real `ISO.*` control ID that exists in a `CONTROL_CLUSTERS` entry). Add a
   *new* test alongside it that still asserts `NotImplementedError` for
   `score(assessment.id, ["dpdpa", "iso27001"])` (multi-framework) — that's the behavior
   the old test's name was actually protecting against fabrication of, and it must not be
   lost.
2. **`test_scoring_rejects_missing_or_mismatched_assessment`** (line 319) — the
   `match="not configured as DPDPA-only"` string must change to match whatever generalized
   message you write in step 1d (e.g. `match="not configured for"`). The test's intent
   (requested `framework_ids` must exactly equal `assessment.frameworks`, not a subset)
   does not change — only the literal string.
3. **`test_scoring_contract_shape_and_single_framework_consistency`** and
   **`test_scoring_collapses_mapped_controls_and_matches_legacy_semantics`** call
   `score(assessment.id, ["dpdpa"], ...)` — these must keep passing **unmodified**. If you
   need to touch their assertions to make them pass, you've broken the DPDPA-only
   contract; stop and re-check 1a-1d instead of editing the test.

Write a new test for question_engine.py's fix — pick any ISO-only or NIST-only assessment,
set `applicable_requirements` to a small subset, call `build_adaptive_questionnaire()` (or
`_build_multi_framework_questionnaire()` directly), and assert that a control ID *not* in
the applicable set does not appear in any returned section's questions.

---

## Done criteria

1. `pytest -q` green, including:
   - The full existing suite (62 tests as of `bbe08f8`) with the three intentionally
     updated tests reflecting the new assertions above.
   - A new passing test proving `score(<iso-only-assessment>, ["iso27001"])` returns a
     real `ScoringResult` (not an exception).
   - A new passing test proving `score(<dpdpa+iso-assessment>, ["dpdpa", "iso27001"])`
     still raises `NotImplementedError`.
   - A new passing test proving scope exclusion actually removes out-of-scope controls
     from a multi-framework questionnaire.
2. `tests/test_golden_dpdpa.py` passes with **zero changes to the golden fixtures** —
   if you find yourself needing to regenerate `tests/fixtures/canonical_dpdpa/expected/*`,
   you've introduced a behavioral change to the DPDPA-only path and must find where 1a/1c
   diverged from the original arithmetic instead of updating the golden.
3. `uvicorn app.main:app` boots clean against a scratch SQLite DB (same smoke check as
   the PR #7 review: startup assertions pass, both credential warnings still fire, and
   `GET /assessments/new` returns 200).
4. Manual smoke: create an ISO-27001-only assessment, answer its ISO scope questions such
   that at least one control is excluded, open its questionnaire, and confirm the excluded
   control's cluster question does not render.

---

## Rollback

```
git revert <merge-commit-sha-of-this-workstream>
```

If the golden tests fail and the cause isn't obvious within the session, do not chase it
by loosening the golden comparison — revert this branch and re-open with a narrower first
attempt (Part 1 only, Part 2 as a separate PR) rather than debugging both changes tangled
together.
