# WS #2 — Framework picker + individual/combined UX (handoff for Codex)

**Plan reference:** `tasks/multi-framework-demo-plan.md` §3 WS #2.
**Branch:** open `ws/2-framework-picker` off `main`.
**Effort:** 2 days.
**Precondition:** none for the picker UI. Scoring changes in this WS stop at the *contract* level; §5 of this doc defines the return shapes every downstream workstream (#4, #7, #8) will code against.

## 1. Goal

1. On the new-assessment screen, the user selects any non-empty subset of `{dpdpa, iso27001, nist_csf}`. GDPR / HIPAA / PCI stay visible but are disabled with a "roadmap — data present, pipeline coming" tag.
2. The assessment view renders per-framework tabs when >1 framework is selected, and a single unified view when exactly 1 is selected.
3. The report view accepts `?view=per_framework|combined` and switches between per-framework score sections and a single combined aggregation.
4. The scoring data model is contract-locked (see §5) so #4, #7, #8 build against a stable shape.

## 2. Load-bearing invariant (Saqlain sign-off, 2026-09-08)

**Score the cluster once, propagate to each framework.**

- The analyzer produces one verdict per **UCC cluster**, not per (framework, control).
- Each framework's overall score is *derived* by walking its control-to-cluster mappings and averaging (weighted by the framework's own control weights).
- The "combined" view is a further derivation — a weighted average across every cluster touched by any selected framework.
- Consequences downstream:
  - Per-framework scoring never re-runs Claude; it's a pure function of cluster verdicts + framework weight tables.
  - Shared controls score identically across frameworks by construction. No reconciliation logic.
  - Combined score is not stored; it's computed on read.
  - Cluster verdicts ARE stored (they're the expensive artefact).

This invariant is what makes the "answer once, applied everywhere" pitch honest. Do NOT design around it — if a requirement seems to conflict, stop and escalate.

## 3. Files in scope

| File | Change |
|---|---|
| `app/models/assessment.py` | Validate `frameworks: list[str]` non-empty on create; add `is_multi_framework` property. |
| `app/routers/web.py` | `POST /assessments` rejects empty `selected_frameworks`. `GET /assessments/{id}` chooses tabs template if multi. `GET /assessments/{id}/report` reads `?view=` query param, defaults to `combined` if multi, `per_framework` (single-tab) if solo. |
| `app/templates/pages/new_assessment.html` | Framework picker: three enabled checkboxes (DPDPA/ISO/NIST), three disabled with `title="Roadmap — control data present, analysis pipeline coming"`. Submit disabled while zero selected. |
| `app/templates/pages/assessment.html` | Add tabs partial when multi; keep current layout when solo. |
| `app/templates/partials/framework_tabs.html` (new) | HTMX-swapping tabs; `hx-get="/assessments/{id}/tab/{framework_id}"`. |
| `app/routers/web.py` | Add `GET /assessments/{id}/tab/{framework_id}` returning the per-framework partial. |
| `app/templates/partials/report_summary.html` | Read a `view_mode` context var; render per-framework sections when `per_framework`, single aggregation when `combined`. |
| `app/services/scoring.py` | Add typed return shapes described in §5. **Do not** rewire analyzer logic; that's #4/#7. |
| `app/schemas/scoring.py` (new) | Pydantic models for the return shapes. |
| `tests/test_picker_and_scoring_contract.py` (new) | See §6. |

**Do NOT touch:**
- `app/services/claude_analyzer.py` (that's #7).
- `app/services/screening.py` (that's #4).
- Any file under `app/frameworks/` (registry is read-only from this WS).
- Any UCC cluster content (that's #6).

## 4. Interfaces — UI

### Framework picker

```html
<fieldset class="picker" name="selected_frameworks">
  <label><input type="checkbox" name="selected_frameworks" value="dpdpa"> DPDPA</label>
  <label><input type="checkbox" name="selected_frameworks" value="iso27001"> ISO 27001</label>
  <label><input type="checkbox" name="selected_frameworks" value="nist_csf"> NIST CSF</label>
  <label class="roadmap"><input type="checkbox" disabled> GDPR <span class="tag">roadmap</span></label>
  <label class="roadmap"><input type="checkbox" disabled> HIPAA <span class="tag">roadmap</span></label>
  <label class="roadmap"><input type="checkbox" disabled> PCI-DSS <span class="tag">roadmap</span></label>
</fieldset>
```

Submit button `disabled` unless ≥1 checkbox in the enabled group is ticked (small `app.js` handler or HTMX `hx-vals` gate).

### Assessment page — tabs

When `len(assessment.frameworks) > 1`:

```html
<nav class="framework-tabs">
  {% for fid in assessment.frameworks %}
    <a hx-get="/assessments/{{ assessment.id }}/tab/{{ fid }}"
       hx-target="#framework-panel"
       hx-push-url="?tab={{ fid }}"
       class="tab {% if fid == active_tab %}active{% endif %}">
      {{ framework_label(fid) }}
    </a>
  {% endfor %}
</nav>
<div id="framework-panel">
  {% include "partials/framework_panel.html" %}
</div>
```

Single-framework assessments render the current layout, no tabs.

## 5. Interfaces — scoring contract (Pydantic)

`app/schemas/scoring.py`:

```python
from pydantic import BaseModel
from typing import Literal

Status = Literal["not_implemented", "partial", "implemented", "not_applicable", "unknown"]

class ClusterVerdict(BaseModel):
    cluster_id: str
    status: Status
    score: float                         # deterministic map from status (see scoring.py)
    reasoning: str                       # analyzer output, one paragraph
    evidence_ids: list[str]              # doc ids cited (empty until WS #8 lands)

class FrameworkScore(BaseModel):
    framework_id: str                    # "dpdpa" | "iso27001" | "nist_csf"
    overall_score: float                 # 0.0–5.0 (M0–M5)
    overall_rating: Literal["M0", "M1", "M2", "M3", "M4", "M5"]
    by_domain: dict[str, float]          # domain → weighted average
    control_count: int
    covered_control_count: int           # controls whose cluster has a verdict
    contributing_clusters: list[str]

class CombinedScore(BaseModel):
    overall_score: float
    overall_rating: Literal["M0", "M1", "M2", "M3", "M4", "M5"]
    by_framework: dict[str, FrameworkScore]
    unique_clusters: int
    total_controls_evaluated: int

class ScoringResult(BaseModel):
    """Top-level return of scoring.score() for a multi-framework assessment."""
    per_framework: dict[str, FrameworkScore]
    combined: CombinedScore
    cluster_verdicts: dict[str, ClusterVerdict]
```

`scoring.score(assessment_id: int, framework_ids: list[str]) -> ScoringResult`:

- If `len(framework_ids) == 1`: `combined` is populated but its values equal the sole framework's.
- `cluster_verdicts` is the raw material; both per-framework and combined derive from it.
- Weighting: use the *framework's own* control weights when aggregating clusters into a `FrameworkScore`. If a control has no assigned weight, treat as 1.0.

**This WS ships the schemas + a thin scoring wrapper that still calls the existing DPDPA path underneath.** The plumbing to produce `cluster_verdicts` from anything other than DPDPA lands in #4/#7. All that's required here is the shapes plus a working DPDPA-only call.

## 6. Test to pass

Add `tests/test_picker_and_scoring_contract.py`:

```python
def test_new_assessment_requires_at_least_one_framework(client):
    r = client.post("/assessments", data={"name": "x", "selected_frameworks": []})
    assert r.status_code == 400

def test_new_assessment_accepts_single_framework(client):
    r = client.post("/assessments", data={"name": "x", "selected_frameworks": ["dpdpa"]})
    assert r.status_code in (200, 302)

def test_new_assessment_accepts_multi(client):
    r = client.post("/assessments", data={"name": "x",
        "selected_frameworks": ["dpdpa", "iso27001", "nist_csf"]})
    assert r.status_code in (200, 302)

def test_assessment_page_renders_tabs_when_multi(client, seeded_multi_assessment):
    r = client.get(f"/assessments/{seeded_multi_assessment.id}")
    assert 'class="framework-tabs"' in r.text
    assert "hx-get=" in r.text

def test_assessment_page_no_tabs_when_solo(client, seeded_dpdpa_assessment):
    r = client.get(f"/assessments/{seeded_dpdpa_assessment.id}")
    assert 'class="framework-tabs"' not in r.text

def test_scoring_contract_shape(seeded_dpdpa_assessment):
    from app.services.scoring import score
    result = score(seeded_dpdpa_assessment.id, ["dpdpa"])
    assert set(result.per_framework.keys()) == {"dpdpa"}
    assert result.combined.overall_score == result.per_framework["dpdpa"].overall_score
    # cluster_verdicts is a dict, values pass ClusterVerdict validation
    from app.schemas.scoring import ClusterVerdict
    for v in result.cluster_verdicts.values():
        ClusterVerdict.model_validate(v.model_dump())

def test_report_view_query_param(client, seeded_multi_assessment):
    r_combined = client.get(f"/assessments/{seeded_multi_assessment.id}/report?view=combined")
    r_per = client.get(f"/assessments/{seeded_multi_assessment.id}/report?view=per_framework")
    assert r_combined.status_code == 200
    assert r_per.status_code == 200
    # per_framework view mentions each selected framework label
    for fid in seeded_multi_assessment.frameworks:
        assert fid.upper().replace("_", " ") in r_per.text or fid in r_per.text
```

`seeded_dpdpa_assessment` and `seeded_multi_assessment` are pytest fixtures — reuse WS #3's `conftest.py` once merged; if #3 hasn't landed, add minimal factories inline in this test file.

## 7. Non-goals

- Actual multi-framework scoring math (DPDPA-only under the hood; the shape is what ships).
- Adaptive tiering / screening across frameworks (#4).
- Any change to `claude_analyzer.py` (#7).
- Populating `cluster_verdicts` from ISO/NIST data (needs #4 + #6 + #7).
- Evidence citation storage (#8).
- Any GDPR/HIPAA/PCI logic beyond the disabled checkboxes.

## 8. Done criteria

1. `pytest -q` green.
2. `uvicorn app.main:app --reload` boots.
3. Create three assessments manually: DPDPA-only, ISO+NIST, all three. Each renders scope, questionnaire, and report without crashing.
4. Multi-framework assessment shows tabs; solo does not.
5. `?view=combined` and `?view=per_framework` both render on a multi assessment.
6. `app/schemas/scoring.py` defines the four models exactly as in §5.
7. `scoring.score()` for a DPDPA-only assessment returns a valid `ScoringResult` where `combined.overall_score == per_framework["dpdpa"].overall_score`.

## 9. Rollback

```bash
git revert <commit-sha-of-ws2-merge>
```

No DB migration. `Assessment.frameworks` is already a column (audit confirmed) — this WS adds validation, not schema.

## 10. Adversarial review

Reviewer: Claude (browser tools).

Prompt:
```
Adversarial review of ws/2-framework-picker. Verify:
1. All done criteria in §8 hold; drive the app and confirm each.
2. Contract in §5: try to construct a ScoringResult where per_framework and
   combined disagree for a single-framework case. If validators allow it,
   FAIL.
3. Roadmap checkboxes are actually disabled at HTML level (not just CSS).
4. GET /assessments/{id}/tab/{framework_id} returns 404 for a framework not
   in the assessment's list — otherwise you can leak the wrong panel.
5. Single most likely production failure mode.

Output: PASS / FAIL with numbered failures. No hedging.
```
