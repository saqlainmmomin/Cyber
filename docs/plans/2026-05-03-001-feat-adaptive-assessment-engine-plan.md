# Adaptive Multi-Framework Assessment Engine

**Date:** 2026-05-03  
**Branch:** `feat/web-portal`  
**Status:** Phase 1 ✅ complete | Phase 2 ✅ complete | Phase 3 ✅ complete  
**Depends on:** [Multi-Framework Contract Repair](2026-04-25-001-multi-framework-contract-repair-plan.md) (Phase A complete), [Intelligent Audit Assistant](2026-04-04-001-feat-intelligent-audit-assistant-plan.md) (Phase 2 desk review complete)

---

## Problem Statement

CyberAssess's multi-framework assessment is operationally unusable at scale. When a client selects 4 frameworks (DPDPA + ISO 27001 + GDPR + HIPAA), the system generates **157 individual questions** — totalling **5+ hours of questionnaire time**. Even single-framework DPDPA requires 41 questions (~1.5 hours).

### The numbers

| Scenario | Raw Controls | After UCC Clustering | Human Time @ 2 min/q |
|---|---|---|---|
| DPDPA only | 41 | 41 | ~1.5 hrs |
| DPDPA + ISO 27001 | 134 | 90 | ~3 hrs |
| DPDPA + ISO + GDPR | 188 | 103 | ~3.5 hrs |
| DPDPA + ISO + GDPR + HIPAA | 242 | **157** | **~5.2 hrs** |
| All 6 frameworks | 400 | **315** | **~10.5 hrs** |

### Root cause

The 1:1 assumption baked into the pipeline: `1 control → 1 question → 1 human answer`. The UCC cluster engine has only 34 pre-defined clusters (concentrated on DPDPA + ISO + GDPR). HIPAA, NIST CSF, PCI DSS have zero cluster coverage. Even perfect clustering would still yield ~100 questions for 4 frameworks.

### Target state

A 4-framework, 242-control assessment: **~90 minutes** of human time, **~30-40 questions** asked, all 242 controls assessed with full audit trail.

---

## Decisions Made

| Decision | Resolution | Date |
|---|---|---|
| Auto-answer mode | Pre-fill only. Always requires human confirmation. Never auto-submit. | 2026-05-03 |
| Audit trail in PDF | Subtle visual distinction. Always show answer source but keep it muted. | 2026-05-03 |
| Screening flow | Replace current Step 6 (questionnaire) entirely. Not a separate mode. | 2026-05-03 |
| Scoring engine | Untouched. `compliance_status` inputs change source, not the formula. | 2026-05-03 |

---

## Pipeline Integration

Steps 1-5 of the current pipeline are **unchanged**:

```
Step 1: Create Assessment           → Unchanged
Step 2: Scope (SOA)                  → Unchanged
Step 3: Document Upload              → Unchanged
Step 4: Desk Review (Call 0)         → Unchanged
Step 5: Context Gathering (Phase 1)  → Unchanged

Step 6: Compliance Questionnaire     → REPLACED:
  6a. Auto-fill from desk review     (Phase 1 of this plan)
  6b. Tiered question presentation   (Phase 2 of this plan)
  6c. Domain-level screening pass    (Phase 3 of this plan)

Step 7: Analysis (Call 1 + Call 2)   → Unchanged (receives answer_source metadata)
```

---

## Phase 1: Document-Driven Pre-Fill (~3-4 days)

### What it does

The existing `question_engine.py` already modulates questions based on desk review — it marks `adequate` coverage controls as `status: "skipped"` (L216-222). Phase 1 converts this to `status: "pre_filled"` and creates `QuestionnaireResponse` records with `answer_source="document"`, so the answer appears pre-selected in the UI for human confirmation.

### Answer source tracking

| Value | Meaning |
|---|---|
| `human` | Human entered from scratch (default, current behavior) |
| `document` | Pre-filled from desk review evidence, awaiting confirmation |
| `document_confirmed` | Human confirmed the pre-filled answer without changing it |
| `human_override` | Human changed the pre-filled answer to something different |
| `inferred` | Inferred from screening pass (Phase 3, future) |

### Files changed

| File | Change | Status |
|---|---|---|
| `app/models/questionnaire.py` | Added `answer_source` column | ✅ Done |
| `app/main.py` | Added `answer_source` to migration runner | ✅ Done |
| `app/schemas/questionnaire.py` | Added `answer_source` to `ResponseOut` | ✅ Done |
| `app/services/question_engine.py` | `_modulate_question()`: adequate/partial → `pre_filled` instead of `skipped`. Added `_summarize_evidence()`. Added `pre_filled_count` to stats. | ✅ Done |
| `app/services/auto_answer.py` | **NEW** — persists document-based pre-fills after desk review | ✅ Done |
| `app/services/desk_review.py` | Calls `persist_document_answers()` after completion | ✅ Done |
| `app/routers/web.py` | `save_questionnaire_responses()`: tracks confirm vs override. Response loading includes `answer_source`. | ✅ Done |
| `app/templates/partials/section_questions.html` | New `pre_filled` card with blue-gray left border, 📄 pill, evidence summary, pre-selected radio | ✅ Done |
| `app/templates/partials/questionnaire_sections.html` | Stats bar and sidebar show pre-fill counts with 📄 icon | ✅ Done |
| `app/utils/pdf_export.py` | Subtle answer source indicators in PDF gap cards | ✅ Done |

### Key implementation details

**Signal-override pre-fill logic** (`question_engine.py _modulate_question()`):
```python
# Priority: signals/absences FIRST → pre-fills only for clean requirements
# Rationale: documents describe intent; signals reveal operational gaps
if req_id in desk_data["absence_req_ids"] or has_signal_for(req_id):
    q["status"] = "deepened"       # Force human scrutiny
    q["follow_up_enabled"] = True  # Enable probing
    return q                        # Never pre-fill

if coverage.get(req_id) in ("adequate", "partial") and evidence_items:
    q["status"] = "pre_filled"     # Only when no signals exist
    q["pre_fill_answer"] = "fully_implemented" if is_adequate else "partially_implemented"
```

**Confirm vs override tracking** (`web.py save_questionnaire_responses()`):
```python
if existing.answer_source == "document":
    existing.answer_source = (
        "document_confirmed" if answer == existing.answer
        else "human_override"
    )
```

**Auto-answer persistence** (`auto_answer.py`): Called from `desk_review.py` after completion. Creates `QuestionnaireResponse` records with `answer_source="document"`. Never overwrites existing human responses. **Suppresses pre-fills for requirements with signals/absences** — same logic as the question engine.

**Completion gate**: No code change needed — pre-fills create real `QuestionnaireResponse` records that the existing gate at `analysis.py L99-105` counts automatically.

### Verification results

| Test | Result |
|---|---|
| All imports | ✅ Clean |
| adequate → pre_filled, fully_implemented, confidence=high | ✅ |
| partial → pre_filled, partially_implemented, confidence=medium | ✅ |
| absent → active, no pre-fill | ✅ |
| Evidence summarizer | ✅ Produces truncated readable quotes |
| Server startup + migration | ✅ |
| **E2E: Auto-answer signal suppression** | ✅ 7/7 — signals block pre-fills |
| **E2E: Question engine override** | ✅ 12/12 — signals → deepen, clean → pre-fill |
| **E2E: Confirm/override tracking** | ✅ 4/4 — answer_source transitions |
| **E2E: Hidden gap protection** | ✅ 9/9 — signaled gaps never pre-filled |

---

## Phase 2: Tiered Assessment Depth (~3-4 days)

### What it does

Assigns an assessment tier to each control based on criticality, risk profile, and desk review coverage. Different tiers get different UI treatment.

| Tier | Trigger | UI Treatment | Time per question |
|---|---|---|---|
| **Deep** | Critical controls, deepened by desk review | Full question + follow-ups + evidence request | ~5 min |
| **Standard** | Default | Single question with notes | ~2 min |
| **Light** | Pre-filled + non-critical | Compact confirmation card | ~30 sec |
| **Skip** | Excluded by scope | Hidden / auto-marked N/A | 0 |

### Files to change

| File | Change | Status |
|---|---|---|
| `app/services/tier_engine.py` | **NEW** — tier assignment rules | ✅ Done |
| `app/services/question_engine.py` | Integrate tier assignment after modulation | ✅ Done |
| Questionnaire templates | Three card styles (deep amber / standard / light gray) | ✅ Done |

### Tier assignment rules (evaluated in order)

1. `status == "skipped"` (scope exclusion) → **SKIP**
2. `status == "pre_filled"` AND `criticality != "critical"` → **LIGHT**
3. `status == "pre_filled"` AND `criticality == "critical"` → **STANDARD** (critical controls always need attention)
4. `status == "deepened"` OR `criticality == "critical"` → **DEEP**
5. `risk_tier == "HIGH"` AND `criticality == "high"` → **DEEP**
6. Default → **STANDARD**

---

## Phase 3: Domain-Level Screening Pass (~5-7 days)

### What it does

Adds a screening step before the detailed questionnaire. 9 domain-level questions (one per domain group) → Claude infers preliminary status for all controls → only low-confidence controls need detailed human input.

### Files to create/change

| File | Change | Status |
|---|---|---|
| `app/services/screening.py` | **NEW** — screening pass orchestration | ✅ Done |
| `app/dpdpa/prompts.py` | Screening prompt builders | ✅ Done |
| `app/models/assessment.py` | Add `screening_status`, `screening_results` columns | ✅ Done |
| `app/main.py` | Add screening column migrations | ✅ Done |
| `app/routers/web.py` | Screening endpoints + UI flow | ✅ Done |
| `app/services/question_engine.py` | Integrate screening results into modulation | ✅ Done |
| Questionnaire templates | Screening UI + inferred badge | ✅ Done |

### Expected flow

```
Screening step (9 questions, ~5 min)
    → Claude infers preliminary status for all controls
    → Each control marked high/medium/low confidence
    → Low-confidence controls → deep tier
    → High-confidence controls → pre-filled (inferred)
    → User sees preliminary report immediately
    → Then fills in only the 25-30 targeted questions
```

---

## Impact Summary

| Metric | Current (4-fw) | After Phase 1 | After Phase 2 | After Phase 3 |
|---|---|---|---|---|
| Questions requiring human input | 157 | **~70-90** | **~50-60** | **~30-40** |
| Human time | ~5.2 hrs | **~2.5 hrs** | **~2 hrs** | **~1.5 hrs** |
| Controls assessed | 242 | 242 | 242 | 242 |
| Scoring engine changes | — | None | None | None |
| New Claude calls | — | 0 | 0 | +1 (screening) |
