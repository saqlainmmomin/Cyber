# Session Log — Adaptive Assessment Engine

**Plan:** [2026-05-03-001-feat-adaptive-assessment-engine-plan.md](plans/2026-05-03-001-feat-adaptive-assessment-engine-plan.md)

---

## Session 1 — 2026-05-03 (Analysis + Phase 1 Implementation)

**Agent:** Antigravity (Gemini)  
**Duration:** ~30 minutes  
**Scope:** Problem analysis, plan creation, Phase 1 backend+frontend implementation

### Context & Decisions

The user raised a core usability concern: multi-framework assessments are "a pain in the ass" because 4 frameworks generate 157 questions (~5 hours). We quantified the problem by running the cluster engine against all framework combinations, then designed three compounding strategies to reduce human input from 157 to ~34 questions.

**Key discovery:** `question_engine.py` already modulates questions based on desk review — it silently skips controls with `adequate` evidence. Phase 1 is surgically converting `skipped` → `pre_filled` and creating response records. The infrastructure was 90% built.

**User decisions locked in:**
- Auto-answers = pre-fill only, always requires confirmation
- Audit trail = subtle visual distinction, always shown
- Screening = replaces Step 6 entirely, not a new mode
- Scoring engine = untouched

### Work Completed

#### Backend (7 files modified, 1 created)

1. **`app/models/questionnaire.py`** — Added `answer_source` column  
   Values: `human | document | document_confirmed | human_override | inferred`

2. **`app/main.py`** — Added migration for `answer_source`

3. **`app/schemas/questionnaire.py`** — Exposed `answer_source` in `ResponseOut`

4. **`app/services/question_engine.py`** — Core change:
   - `_modulate_question()`: adequate/partial coverage → `status: "pre_filled"` with `pre_fill_answer`, `pre_fill_confidence`, `pre_fill_source`, `pre_fill_evidence_summary`
   - Previously: `status: "skipped"` (question hidden entirely)
   - Added `_summarize_evidence()` helper
   - Added `pre_filled_count` to stats return dict
   - Coverage check updated: pre-filled questions count as covered

5. **`app/services/auto_answer.py`** — NEW file:
   - `persist_document_answers()`: creates `QuestionnaireResponse` records from desk review coverage
   - Respects existing human answers (never overwrites)
   - Called from `desk_review.py` after successful completion

6. **`app/services/desk_review.py`** — Added auto-answer call at L121-131:
   - After `summary.status = "completed"`, calls `persist_document_answers()`
   - Wrapped in try/except so pre-fill failure doesn't block desk review

7. **`app/routers/web.py`** — Two changes:
   - `save_questionnaire_responses()`: detects confirm vs override of pre-fills
   - Response loading: includes `answer_source` in template context

#### Frontend (2 templates modified)

8. **`section_questions.html`** — New `pre_filled` question card:
   - Blue-gray left border (`#8b9dc3`)
   - `📄 Document evidence` pill badge with confidence indicator
   - Collapsible evidence summary
   - Answer radio pre-selected from `pre_fill_answer`
   - Full follow-up and notes support (same as active questions)

9. **`questionnaire_sections.html`** — Stats and sidebar:
   - Stats bar: `"📄 N pre-filled from documents"`
   - Section sidebar: per-section pre-fill count with 📄 icon

### Verification

| Test | Result |
|---|---|
| All imports clean | ✅ |
| adequate → pre_filled, fully_implemented, confidence=high | ✅ |
| partial → pre_filled, partially_implemented, confidence=medium | ✅ |
| absent → active, no pre-fill | ✅ |
| Evidence summarizer | ✅ |
| Server startup + migration | ✅ |

### Not Completed (carry to next session)

- [x] PDF report: subtle answer source indicators in gap cards
- [x] End-to-end test: auto-answer signal suppression, question engine override, confirm/override tracking, hidden gap protection (32/32 passed)
- [ ] Phase 2: Tiered assessment depth (`tier_engine.py`, template variants)
- [ ] Phase 3: Domain-level screening (`screening.py`, screening prompts)

### Notes for Next Agent

- The `answer_source` column defaults to `"human"` — all existing assessments are backward-compatible
- The completion gate at `analysis.py L99-105` already counts pre-filled answers automatically (they're real `QuestionnaireResponse` records)
- The `_modulate_industry_question()` function in `question_engine.py` was NOT updated for pre-fill yet — industry questions currently use the old skip logic. This should be addressed when starting Phase 2.
- The PDF export change (answer source indicators) requires reading `answer_source` from `QuestionnaireResponse` for each gap item's requirement ID — the gap item model doesn't carry `answer_source`, so it needs a join at render time

---

## Session 2 — 2026-05-03 (PDF Report Completion)

**Agent:** Antigravity (Claude Opus 4.6)  
**Duration:** ~10 minutes  
**Scope:** PDF answer source indicators — completes Phase 1 backend

### Work Completed

#### PDF Report (`app/utils/pdf_export.py` + `app/routers/reports.py`)

1. **`app/routers/reports.py`** — Added `QuestionnaireResponse` import and answer source lookup:
   - Queries all `QuestionnaireResponse` records for the assessment
   - Builds `answer_source_map: dict[str, str]` mapping `question_id → answer_source`
   - Passes map to `generate_pdf()`

2. **`app/utils/pdf_export.py`** — Added answer source indicators:
   - New `ANSWER_SOURCE_CONFIG` constant maps source values to (label, muted color) tuples
   - `_draw_gap_card()` accepts optional `answer_source` parameter
   - Renders a subtle muted pill below the status/risk badges:
     - `document` → "Doc Pre-fill" in muted blue-gray `(120, 140, 180)`
     - `document_confirmed` → "Doc Confirmed" in muted green `(100, 160, 130)`
     - `human_override` → "Doc Override" in muted amber `(180, 140, 100)`
     - `inferred` → "Inferred" in muted purple `(140, 130, 170)`
     - `human` → no indicator (default, clean)
   - Card height adjusts dynamically when indicator is present (+4.5mm offset)
   - Indicators appear in both Critical & High Risk Gaps page and Appendix cards
   - `generate_pdf()` signature updated with `answer_source_map` parameter

### Verification

| Test | Result |
|---|---|
| `pdf_export` import clean | ✅ |
| `reports` router import clean | ✅ |

### Phase 1 Status: ✅ COMPLETE

All 9 files from the Phase 1 plan are now implemented and verified.

---

## Session 3 — 2026-05-03 (Signal Override Fix + E2E Test)

**Agent:** Antigravity (Claude Opus 4.6)  
**Duration:** ~15 minutes  
**Scope:** Critical bug fix — signals must override pre-fills; E2E test

### Problem Identified

**The pre-fill logic had a silent priority inversion:** `_modulate_question()` checked coverage FIRST and returned early with a pre-fill, before signal/absence checks could run. This meant:

- A requirement with adequate document coverage **AND** a critical desk review signal → pre-filled as "fully implemented, high confidence"
- The signal (e.g., "bundled consent") → **silently discarded**
- The follow-up probing that would have caught the gap → **never triggered**

This defeats the core premise: documents describe intent, signals reveal operational gaps. When both exist, signals must win.

The same issue existed in `auto_answer.py` — it created `QuestionnaireResponse` records for ALL adequate/partial coverage without checking for signals.

### Audit Principle

| Layer | What it shows | Reliability |
|---|---|---|
| Policy documents | Intent and stated procedures | Low — often aspirational |
| Signals (red flags) | Policy-practice divergence | High — evidence-based |
| Follow-up probing | Operational reality | Highest — targeted scrutiny |

**Rule: Signals override pre-fills. Always.**

### Work Completed

#### 1. `app/services/question_engine.py` — `_modulate_question()`
- Reordered priority: absences → signals → pre-fills → active
- If ANY signal or absence exists for a requirement → DEEPEN (never pre-fill)
- Deepened questions now also receive evidence context (side-by-side view)
- Added detailed docstring documenting the priority order

#### 2. `app/services/auto_answer.py` — `persist_document_answers()`
- Now loads ALL findings (not just evidence) in a single query
- Indexes signal/absence requirement IDs into `signal_req_ids` set
- Skips pre-fill for any requirement in `signal_req_ids`
- Logs suppression count alongside creation count

#### 3. `tests/test_phase1_prefill.py` — NEW E2E test (32 checks)
Uses the NovaPay fixture (realistic hidden-gap scenario).

**Test 1: Auto-Answer Signal Suppression**
- `persist_document_answers()` creates pre-fills for clean requirements ✅
- No signal requirements get auto-answered ✅
- Specific hidden gap reqs (CH2.CONSENT.2, BN.NOTIFY.1, CH2.NOTICE.1) NOT pre-filled ✅
- Clean requirements (CH2.SECURITY.1) ARE pre-filled ✅

**Test 2: Question Engine Signal Override**
- 9 signal requirements deepened (not pre-filled) ✅
- 5 clean requirements pre-filled ✅
- All deepened questions have `follow_up_enabled=True` ✅
- Signal text visible in `desk_review_note` ✅
- Evidence attached alongside signals for side-by-side review ✅

**Test 3: Confirm vs Override Tracking**
- Confirming pre-fill → `answer_source = "document_confirmed"` ✅
- Overriding pre-fill → `answer_source = "human_override"` ✅
- Unchanged pre-fills retain `answer_source = "document"` ✅

**Test 4: Hidden Gaps with Signals Not Pre-Filled**
- All 8 hidden gaps: signaled requirements NOT pre-filled ✅
- 5 hidden gap reqs without own signals are pre-fillable by design (gap surfaces through follow-up probing, not desk review)

### Key Design Decision

Not all hidden gap requirements have their own signal/absence. Example: `CH2.CONSENT.1` and `CH2.CONSENT.3` share a hidden gap group with `CH2.CONSENT.2`, but only `CH2.CONSENT.2` has the bundled consent signal. The other two are correctly pre-fillable because the documents DO look adequate for those specific controls — the gap only surfaces through follow-up probing.

This is **by design:** Phase 2's follow-up engine is responsible for surfacing gaps that don't have their own desk review signals.

### Results: 32/32 passed ✅

---

## Session 4 — 2026-05-04 (Phase 2: Tiered Assessment Depth)

**Agent:** Antigravity (Claude Opus 4.6 Thinking)  
**Duration:** ~15 minutes  
**Scope:** Phase 2 — tier engine, question engine integration, 3 card styles

### Work Completed

#### 1. `app/services/tier_engine.py` — NEW
Pure-function tier assignment with 7-rule priority cascade:
- Rule 1: `skipped` → SKIP
- Rule 2: `pre_filled` + non-critical → LIGHT
- Rule 3: `pre_filled` + critical → STANDARD
- Rule 4: `deepened` → DEEP
- Rule 5: `critical` + HIGH risk → DEEP
- Rule 6: `high` + HIGH risk → DEEP
- Rule 7: default → STANDARD

Includes `assign_tiers()` batch function and `compute_tier_stats()` helper.

#### 2. `app/services/question_engine.py` — 4 changes
- Import `assign_tiers`, `compute_tier_stats` from tier engine
- Extract `risk_tier` from `context_profile`
- After modulation: call `assign_tiers()` on both base and industry questions
- Stats return dict now includes `tier_counts: {"deep": N, "standard": N, "light": N, "skip": N}`
- **Fixed `_modulate_industry_question()`** to use pre-fill logic instead of the old skip logic, and ensured signals correctly override pre-fills just like the base DPDPA questions.

#### 3. `app/templates/partials/section_questions.html` — 3 card styles
- **LIGHT**: Compact single-row card with inline radio buttons (shortened labels: Full/Partial/Planned/No/N/A), `📄 Confirm` badge, collapsed evidence `<details>`, gray-50 background, 2px left border
- **STANDARD**: Full pre-fill card (unchanged from Phase 1 — evidence summary, guidance, follow-ups)
- **DEEP**: Active/deepened card enhanced with `⚠️ Deep Review` amber badge, evidence `<details>` auto-expanded via `open` attribute

#### 4. `app/templates/partials/questionnaire_sections.html` — stats + sidebar
- Stats bar: tier breakdown `⚠️ N deep review · N standard · ⚡ N quick confirm`
- Sidebar: per-section deep count with `⚠️` icon

### Verification

| Test | Result |
|---|---|
| `tier_engine` import | ✅ |
| `question_engine` import | ✅ |
| Unit tests: 15 tier rules (all 7 rules + batch + edge cases) | ✅ 15/15 |

### Phase 2 Status: ✅ COMPLETE

### Not Completed (carry to next session)

- [ ] Phase 3: Domain-level screening (`screening.py`, screening prompts)

### Notes for Next Agent

- The `tier` key is added to every question dict after modulation — templates can branch on `q.get('tier')`
- Light cards intentionally omit follow-up triggers — non-critical pre-fills shouldn't trigger probing
- The tier engine is a pure function with no DB dependency — easy to unit test
- `risk_tier` defaults to `"MEDIUM"` when no context profile exists (backward-compatible)

---

## Handoff to Claude Code

**Agent:** Antigravity (Gemini 3.1 Pro High)
**Date:** 2026-05-04

Phase 3 (Domain-Level Screening Pass) has been fully planned. The implementation details are in the artifact `phase3_implementation_plan.md`.

A prompt file `phase3_claude_prompt.md` has been created in the project root. Please invoke Claude Code and pass this file to initiate the implementation of Phase 3.

---

## Session 5 — 2026-05-04 (Phase 3: Domain-Level Screening Pass)

**Agent:** Claude Code (claude-sonnet-4-6)
**Duration:** ~20 minutes
**Scope:** Phase 3 — full implementation of domain-level screening pass

### Work Completed

All 7 implementation steps complete. No regressions.

#### 1. `app/models/assessment.py`
Added `screening_status` (VARCHAR 20, nullable) and `screening_results` (TEXT, nullable) columns.

#### 2. `app/main.py`
Added `screening_status` and `screening_results` to the `assessments` migrations dict. Verified migrations apply cleanly.

#### 3. `app/dpdpa/prompts.py`
Added at end of file:
- `SCREENING_DOMAINS`: list of 9 domain dicts, each with `id`, `title`, `question`, and `covers` (list of req IDs). Domains: CONSENT, NOTICE, PURPOSE, ACCURACY, SECURITY, BREACH, RIGHTS, GOVERNANCE, CROSSBORDER.
- `build_screening_system_prompt()`: cacheable system prompt — persona + 41 req reference + inference rules.
- `build_screening_user_prompt()`: user prompt with org profile + 9 domain Q&A blocks.

#### 4. `app/services/screening.py` — NEW
- `run_screening_pass()`: orchestrates Claude call, parses JSON, persists to DB, creates inferred `QuestionnaireResponse` records for high-confidence non-non_compliant inferences.
- `_parse_inferences()`: robust JSON parser with validation; fills missing req IDs as `not_assessed/low`.
- `_persist_inferred_answers()`: creates `QuestionnaireResponse` with `answer_source="inferred"` for high-confidence compliant/partially_compliant inferences. Never overwrites existing answers.
- `get_domain_coverage()`: returns `SCREENING_DOMAINS` for use in templates.

#### 5. `app/routers/web.py`
Added two endpoints before the analysis trigger section:
- `GET /assessments/{id}/screening` → serves `screening_form.html` partial.
- `POST /assessments/{id}/screening/submit` → processes form, calls `run_screening_pass()`, redirects to questionnaire.
Also: added `screening_done` to `assessment_detail` context and passed it to the template.

#### 6. `app/services/question_engine.py`
- Added `_load_screening_data()`: safely loads and parses `assessment.screening_results`.
- `build_adaptive_questionnaire()`: loads screening data; after desk review modulation, applies `_apply_screening()` to still-active questions.
- Added `inferred_count` to stats; stats now return `inferred_questions` key.
- Added `_apply_screening()`: maps screening confidence to UI behaviour:
  - `high` + compliant/partially_compliant → `pre_filled` with `pre_fill_source="inferred"`
  - `low` → `deepened` (force human scrutiny)
  - `medium` → active with a context hint in `desk_review_note`

#### 7. Templates

**`app/templates/partials/screening_form.html`** — NEW
- 9-domain form with HTMX submission.
- Shows requirement ID pills per domain (first 4 + "+N more").
- Purple loading indicator, skip link to questionnaire.
- Shows "complete" banner after successful screening.

**`app/templates/partials/section_questions.html`**
- LIGHT and STANDARD pre-fill cards: branch on `pre_fill_source == "inferred"`:
  - Purple left-border and `bg-purple-50/40` background instead of slate.
  - `✨ Inferred` badge (purple) instead of `📄 Document evidence`.

**`app/templates/partials/questionnaire_sections.html`**
- Stats bar: added `✨ N inferred from screening` count in purple.

**`app/templates/partials/questionnaire_tab.html`**
- Added "Domain Screening" card above the detailed questionnaire.
- "Start screening" button loads `screening_form.html` into `#screening-body` via HTMX.
- Shows completion badge + purple confirmation message after screening is done.

### Verification

| Test | Result |
|---|---|
| All Phase 3 imports clean | ✅ |
| `SCREENING_DOMAINS` has 9 domains | ✅ |
| Migrations: `screening_status` + `screening_results` added to `assessments` | ✅ |
| Phase 1 regression: `test_phase1_prefill.py` | ✅ 32/32 |
| Phase 2 regression: `test_phase2_tiers.py` | ✅ 15/15 |

### Phase 3 Status: ✅ COMPLETE

### Architecture Notes for Next Agent

- `pre_fill_source` field values: `"document"` (Phase 1) | `"inferred"` (Phase 3). Templates branch on this to show the correct badge colour.
- Screening does NOT overwrite desk-review pre-fills (`auto_answer.py` creates those first; `_persist_inferred_answers` skips existing responses).
- `answer_source` column in `questionnaire_responses` already had `"inferred"` as a supported value (added in Phase 1 design).
- Screening results are stored as flat JSON in `assessment.screening_results`. The `_apply_screening()` function in `question_engine.py` reads this at questionnaire render time.
- The 9 screening domains cover all 41 DPDPA requirements. Future work: extend `SCREENING_DOMAINS` in `app/dpdpa/prompts.py` to cover ISO 27001 / GDPR / HIPAA controls for multi-framework screening.

