# Multi-Framework Contract Repair & Completion Plan

**Date:** 2026-04-25  
**Branch:** `feat/web-portal`  
**Status:** In progress

---

## Background

The 2026-04-24 session built a complete multi-framework scaffold across 31 files (commit `81c21a8`): 6 frameworks, 400 controls, unified scoring, per-framework Claude calls. However, a post-implementation audit by Codex found that the questionnaire → response → analysis contract is broken. The multi-framework path cannot reliably submit or consume responses. This plan fixes that contract first, then completes the remaining features.

---

## Root Cause

The questionnaire builder emits `cluster_id` as the question ID (e.g., `SINGLE.ISO.A5.24`). Three layers reject or ignore these IDs:

1. **Schema** (`app/schemas/questionnaire.py:14`) — `QUESTION_ID_PATTERN` only matches DPDPA patterns. Any non-DPDPA cluster ID returns 422.
2. **Analysis prompt filter** (`app/frameworks/prompts.py:241`) — filters responses by `fw_control_ids` (real control IDs like `ISO.A5.24`). Cluster-ID-keyed responses are silently dropped → `_No questionnaire responses for this framework._`
3. **Completion gate** (`app/routers/analysis.py:79`) — always calls `build_questionnaire()` (DPDPA-only) to compute the 80% threshold. Multi-framework assessments measure against the wrong baseline.

## Canonical Data Model Decision

- The submitted `question_id` equals the `cluster_id` emitted by the questionnaire builder.
- Server-side expansion from `cluster_id → [(framework_id, control_id)]` happens in the analysis layer using the cluster engine, before the per-framework prompt filter applies.
- This keeps the client simple (one ID per question) and the server authoritative about cross-framework mappings.

---

## Phase A — Fix the Broken Contract

**Owner: Claude** (A1–A4) | **Owner: Codex** (A5, can start immediately in parallel)

### A1. Fix response schema (`app/schemas/questionnaire.py`)

**What:** Widen `QUESTION_ID_PATTERN` to accept cluster ID formats in addition to DPDPA IDs.

**Cluster ID patterns to accept:**
- `SINGLE.<FRAMEWORK>.<CONTROL>` — singleton cluster (e.g., `SINGLE.ISO.A5.24`, `SINGLE.GDPR.ART5.1`)
- `CLUSTER_<N>` — real multi-framework cluster (e.g., `CLUSTER_001`)
- Existing DPDPA patterns unchanged

**Changes:**
- Update `QUESTION_ID_PATTERN` regex (or replace the validator logic entirely with an allowlist approach that also accepts any string matching `SINGLE\.` or `CLUSTER_\d+`)
- Add `cluster_id: str | None = None` field to `ResponseSubmit` as an explicit alias (the submitted `question_id` IS the cluster_id; this field makes it explicit for future use)

**Verify:** `POST /api/assessments/{id}/responses` with `[{"question_id": "SINGLE.ISO.A5.24", "answer": "partially_implemented"}]` returns 201, not 422.

---

### A2. Fix analysis prompt filter (`app/frameworks/prompts.py`)

**What:** Before filtering responses for a framework, expand cluster IDs to their underlying control IDs.

**Current code (line 241):**
```python
fw_responses = [r for r in responses if r["question_id"] in fw_control_ids]
```

**Required logic:**
1. Import `ClusterEngine` from `app.frameworks.cluster_engine`
2. For each response, check if `question_id` is a cluster ID (starts with `SINGLE.` or `CLUSTER_`)
3. If yes, resolve `cluster_id → [(framework_id, control_id)]` via cluster engine
4. Keep the response if any resolved `(framework_id, control_id)` pair belongs to this framework's `fw_control_ids`
5. When passing the response to the prompt, key it by the resolved `control_id` (not the cluster ID), so Claude sees real control references

**Verify:** Call `build_framework_user_prompt(framework_id="iso27001", responses=[{"question_id": "SINGLE.ISO.A5.24", "answer": "partially_implemented"}], ...)` — confirm the output contains `ISO.A5.24` in the Questionnaire Responses section, not `_No questionnaire responses._`

---

### A3. Fix analysis completion gate (`app/routers/analysis.py:78-91`)

**What:** Branch on `selected_frameworks` before computing the 80% completion threshold.

**Current code:** Always calls `build_questionnaire(context_profile=context_profile)` which builds the DPDPA-only questionnaire.

**Required logic:**
```python
selected_frameworks = _get_selected_frameworks(assessment)  # already exists as helper in questionnaire.py
if selected_frameworks == ["dpdpa"] or not selected_frameworks:
    # existing path unchanged
    expected_question_ids = {q["id"] for q in build_questionnaire(...) if not q["id"].startswith(("IND.", "FU."))}
else:
    # multi-framework path: use cluster-based builder
    from app.frameworks.questionnaire_builder import build_multi_framework_questionnaire
    cluster_questions = build_multi_framework_questionnaire(selected_frameworks, context_profile=context_profile)
    expected_question_ids = {q["cluster_id"] for q in cluster_questions}
```

Also move `_get_selected_frameworks` helper to a shared location or import it from `routers/questionnaire.py` — avoid duplicating it.

**Verify:** `POST /analyze` for a multi-framework assessment with >80% cluster questions answered does not raise 400.

---

### A4. Fix `GET /questionnaire/sections/{section_id}` (`app/routers/questionnaire.py:205`)

**What:** The endpoint currently always rebuilds the DPDPA questionnaire regardless of `selected_frameworks`.

**Required logic:** Read `selected_frameworks` from the assessment. If multi-framework, call `build_multi_framework_questionnaire()` and group results via `_group_multi_into_sections()` (already implemented at line 316). The `section_id` path param should then match the `domain_group` used as the section key.

**Verify:** `GET /api/assessments/{id}/questionnaire/sections/governance` for an ISO+DPDPA assessment returns ISO and DPDPA governance questions, not DPDPA chapters.

---

### A5. Multi-framework seed data (Codex task — start immediately)

**File:** `scripts/seed_test_companies.py`

**What:** Add at least 2 companies with `selected_frameworks` populated. This is independent of the contract fix and can be seeded now; responses will fail to persist until A1 is merged, but the assessment creation and framework selection steps can be validated immediately.

**Company A — mid-size tech company (DPDPA + ISO 27001):**
```python
{
    "company_name": "Helix Technologies Pvt Ltd",
    "industry": "technology",
    "company_size": "sme",
    "description": "B2B SaaS platform processing employee and customer personal data",
    "selected_frameworks": ["dpdpa", "iso27001"],
}
```

**Company B — large fintech with EU operations (DPDPA + ISO 27001 + GDPR):**
```python
{
    "company_name": "Vantara Financial Services",
    "industry": "financial_services",
    "company_size": "large",
    "description": "Digital lending and payments platform operating across India and EU",
    "selected_frameworks": ["dpdpa", "iso27001", "gdpr"],
}
```

**Steps per company:**
1. `POST /api/assessments` — create assessment
2. `POST /api/assessments/{id}/frameworks` — set `selected_frameworks`
3. `POST /api/assessments/{id}/context` — submit 16 context answers (reuse existing seed patterns)
4. Attempt `POST /api/assessments/{id}/responses` — for ISO questions, use the cluster IDs returned by `GET /api/assessments/{id}/questionnaire` (these will return 422 until A1 is merged; note this in the seed script output)
5. Upload at least 1 document per assessment (reuse existing seed docs)

**CLI flag:** `python scripts/seed_test_companies.py --multi` runs only multi-framework seeds without touching existing DPDPA-only companies.

**Verify:**
```bash
python scripts/seed_test_companies.py --multi
# Should print: "Seeded 2 multi-framework companies"
# Check DB:
python -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as c:
    rows = c.execute(text('SELECT company_name, selected_frameworks FROM assessments WHERE selected_frameworks IS NOT NULL')).fetchall()
    for r in rows: print(r)
"
```

---

## Phase B — End-to-End Validation + UCC Cluster Mappings

**Owner: Claude** (B1–B2) | **Owner: Codex** (B3 — parallel, start after A1 is merged)

### B1. Run end-to-end multi-framework analysis (Claude)

Using the seeded Company A (DPDPA + ISO 27001):

1. Submit questionnaire responses via cluster IDs (now accepted after A1)
2. `POST /analyze` — trigger analysis
3. Check:
   - Evidence extraction call runs (if documents present)
   - ISO 27001 Claude call receives non-empty questionnaire responses
   - DPDPA Claude call receives non-empty questionnaire responses
   - Per-framework gap items persisted with correct `framework_id`
   - `GET /api/assessments/{id}/report` returns `framework_scores` dict with 2 entries
4. Document any defects found; fix inline

### B2. Validate synthesis call (Claude)

- Cross-framework synthesis prompt receives per-framework summaries
- `GET /api/assessments/{id}/report/full` returns `per_framework` breakdown and unified initiatives
- Scores are internally consistent (no NaN, no division by zero from empty framework)

### B3. Populate UCC cluster mappings (Codex task)

**File:** `app/frameworks/mappings/clusters.py`

**Target:** ~80–100 real clusters for DPDPA + ISO 27001 + GDPR (the three highest-overlap frameworks). HIPAA / NIST / PCI-DSS in a second pass.

**Priority topic areas (start here — highest overlap, highest ROI):**

| Topic area | DPDPA | ISO 27001 | GDPR |
|---|---|---|---|
| Governance & policy | CH2.CONSENT.1, CH4.DP.1 | ISO.A5.1, ISO.A5.2 | GDPR.ART5.1, GDPR.ART24 |
| Access control | CH3.RIGHTS.1 | ISO.A5.15, ISO.A5.18, ISO.A8.2 | GDPR.ART25, GDPR.ART32 |
| Incident response | BN.NOTIF.1, BN.NOTIF.2 | ISO.A5.24, ISO.A5.26 | GDPR.ART33, GDPR.ART34 |
| Third-party risk | CH4.DP.3, CH4.DP.4 | ISO.A5.19, ISO.A5.20 | GDPR.ART28, GDPR.ART29 |
| Notices & rights | CH2.NOTICE.1, CH3.RIGHTS.2 | ISO.A5.34 | GDPR.ART13, GDPR.ART14, GDPR.ART15–22 |

**Cluster dict schema** (each entry in `CONTROL_CLUSTERS`):
```python
"CLUSTER_001": {
    "topic": "Governance Policy",
    "primary_question": "Does your organization have a formally documented and board-approved data protection / information security policy?",
    "primary_guidance": "Look for: written policy, approval date, owner, annual review cycle, distribution evidence.",
    "controls": [
        {"framework": "dpdpa",   "control_id": "CH4.DP.1",   "coverage": "full"},
        {"framework": "iso27001","control_id": "ISO.A5.1",   "coverage": "full"},
        {"framework": "gdpr",    "control_id": "GDPR.ART24", "coverage": "partial"},
    ],
    "criticality": "high",
    "domain_group": "governance",
    "follow_up_triggers": {
        "partially_implemented": "FOLLOWUP_CLUSTER_001_A",
        "not_implemented": "FOLLOWUP_CLUSTER_001_B",
    },
}
```

**Verify after populating:**
```bash
# Cluster count
python -c "from app.frameworks.mappings.clusters import CONTROL_CLUSTERS; print(len(CONTROL_CLUSTERS), 'clusters defined')"

# Questionnaire length reduction
python -c "
from app.frameworks.cluster_engine import ClusterEngine
e = ClusterEngine()
q3 = e.build_questionnaire(['dpdpa','iso27001','gdpr'])
q2 = e.build_questionnaire(['dpdpa','iso27001'])
print(f'3-fw: {len(q3)} questions (target ≤120)')
print(f'2-fw: {len(q2)} questions (target ≤90)')
"

# Coverage check — no control should be lost
python -c "
from app.frameworks.cluster_engine import ClusterEngine
from app.frameworks.registry import FrameworkRegistry
e = ClusterEngine()
for fw_id in ['dpdpa','iso27001','gdpr']:
    fw = FrameworkRegistry.get(fw_id)
    all_ids = {c.id for c in fw.all_controls()}
    covered = e.get_covered_control_ids(fw_id)
    missing = all_ids - covered
    print(f'{fw_id}: {len(covered)}/{len(all_ids)} controls covered, {len(missing)} missing')
"
```

**Success criteria:**
- 3-framework questionnaire: ≤120 questions (down from 188)
- 2-framework (DPDPA + ISO): ≤90 questions (down from 134)
- 0 controls dropped from any framework

---

## Phase C — Reporting Hardening

**Owner: Claude** (after Phase B)

### C1. Fix JSON report endpoints (`app/routers/reports.py`)

- `GET /report/summary` (line ~139): replace `get_requirement_count()` (DPDPA-only) with framework-aware count — use `FrameworkRegistry.get(fw_id).control_count()` summed across selected frameworks
- `GET /report`: ensure `framework_scores` dict and `unified_maturity` are returned for multi-framework assessments
- `GET /report/full`: confirm per-framework breakdown and cross-framework initiatives serialize correctly

**Verify:** All three endpoints return correct, non-DPDPA-specific data for the Phase B validation assessment.

### C2. Per-framework scope UI

The web portal scope page currently shows only DPDPA scope questions (`GET /api/assessments/{id}/questionnaire/sections` filtered to scope). Each framework definition already has `scope_questions`.

- For multi-framework assessments, render a scope question block per selected framework (collapsible per framework)
- Pass `framework_id` alongside each scope answer so applicability filtering updates the correct controls
- Existing DPDPA-only behavior unchanged

**Verify:** Selecting DPDPA + ISO 27001 in the web portal and advancing to scope shows question blocks for both frameworks.

---

## Phase D — Multi-Framework PDF Export

**Owner: Claude** (after Phase C)

### D1. Build `app/utils/multi_pdf_export.py`

New file — do not modify `pdf_export.py` (existing single-framework PDF stays intact).

**Pages:**
1. Cover page (reuse `_page_header` / `_page_footer` patterns)
2. Executive Dashboard — unified maturity score + per-framework score row
3. Per-framework summary page (one per selected framework): score gauge + top 3 gaps + recommended initiatives
4. Cross-framework heatmap: frameworks × domain areas, cells colored by score
5. Radar chart: unified maturity across 5–6 topic areas
6. Cross-framework initiative table: grouped by root cause, showing which frameworks each initiative addresses
7. Appendix: detailed findings (existing appendix format, with `framework_id` column)

**Hard rules (from CLAUDE.md):**
- All text through `S()` sanitizer — no exceptions
- Dispatch: `GET /report/pdf` routes to `multi_pdf_export.py` when `len(selected_frameworks) > 1`

**Verify:** PDF downloads without error for the Phase B validation assessment. All pages render. Single-framework DPDPA PDF is unchanged.

---

## Validation Criteria — Definition of Done

The multi-framework path is operational when all pass:

| # | Check | How to verify |
|---|---|---|
| 1 | Schema accepts cluster IDs | `POST /responses` with `SINGLE.ISO.A5.24` → 201 |
| 2 | Analysis receives responses | `build_framework_user_prompt()` for ISO shows non-empty responses |
| 3 | Full 3-framework analysis runs | Evidence + 3 fw calls + synthesis complete without error |
| 4 | Report has 3 framework scores | `GET /report` returns `framework_scores` with 3 keys |
| 5 | UCC reduces questionnaire length | 3-fw: ≤120 questions |
| 6 | Multi-fw PDF downloads | `GET /report/pdf` returns PDF with per-framework pages |

---

## File Index

| File | Phase | Owner | Change type |
|---|---|---|---|
| `app/schemas/questionnaire.py` | A1 | Claude | Widen ID pattern |
| `app/frameworks/prompts.py` | A2 | Claude | Expand cluster IDs before filter |
| `app/routers/analysis.py` | A3 | Claude | Framework-aware completion gate |
| `app/routers/questionnaire.py` | A4 | Claude | Multi-fw section dispatch |
| `scripts/seed_test_companies.py` | A5 | Codex | Add 2 multi-fw companies |
| `app/frameworks/mappings/clusters.py` | B3 | Codex | Populate 80–100 cluster entries |
| `app/routers/reports.py` | C1 | Claude | Framework-aware counts |
| Web portal templates | C2 | Claude | Per-fw scope UI |
| `app/utils/multi_pdf_export.py` | D1 | Claude | New multi-fw PDF exporter |
