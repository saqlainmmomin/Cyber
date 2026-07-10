---
title: "CyberAssess: Trusted Platform — 4 Priorities"
type: feat
status: active
date: 2026-05-08
---

# CyberAssess: Trusted Platform — 4 Priorities

## Strategic Context

CyberAssess is positioned as an **AI-assisted compliance assessment copilot for consultants/analysts** — not an autonomous engine, not an enterprise GRC platform. The architecture is strong, but the platform is not yet ready for fully trusted client-facing use.

This plan closes the gap between a technically impressive solo-operated tool and a reliable, team-safe, pilot-ready platform. The changes are about making the current system **trustworthy, operable, and defensible** — not adding AI for its own sake.

**Operating principle:** Trust before workflow, workflow before packaging.

---

## Sequencing & Phase Gates

```
Priority 1 (Calibration)
    → Gate: prompt frozen, boundary accuracy stable
Priority 2 (E2E Validation)
    → Gate: both seeded runs complete, scorecards pass
Priority 3 (Manager Review Workflow)
    → Gate: review states live, gating enforced
Priority 4 (Multi-Framework Report/Export)
```

**Gate P1 → P2:** Calibration set shows <2 boundary misclassifications on `partial` vs `non` cases across 2 consecutive runs. Prompt version frozen.

**Gate P2 → P3:** Both Helix (`DPDPA+ISO`) and Vantara (`DPDPA+ISO+GDPR`) complete without errors, framework score counts match selection, no cluster-related control loss detected.

**Gate P3 → P4:** Review states implemented in DB, review UI live, report generation gated on assessment-level approval.

---

## Pre-work: Scaffolding & Seed Verification (Before P1)

**Effort: S**

These two tasks are prerequisites that unblock P1 and P2 respectively.

### A. Calibration Test Harness

**Design decision:** Calibration cases live as JSON fixtures in `tests/calibration/cases/`. A standalone Python runner script (`tests/calibration/run_calibration.py`) loads fixtures and runs them through the **production code path** — same prompt builder (`app/dpdpa/prompts.py`), same evidence assembly shape as `claude_analyzer.py` produces, same model and params (`claude-sonnet-4-6`, `max_tokens=16384`). The runner must not shortcut or simplify the prompt assembly — calibration results that differ from production behavior are worthless. No pytest needed — it's a script, not a test suite.

**Fixture schema (one file per case):**
```json
{
  "id": "CALIB-001",
  "label": "partial vs non — documented policy, no operating evidence",
  "framework": "DPDPA",
  "requirement_id": "CH2.CONSENT.1",
  "evidence": {
    "CH2.CONSENT.1": ["Policy document states consent is required.", "No operational logs or consent receipts found."]
  },
  "questionnaire_answers": {"CH2.CONSENT.1": "partially_compliant"},
  "expected_status": "non_compliant",
  "boundary_case": true
}
```

The `evidence` field must match the dict shape that `claude_analyzer.py:_run_evidence_extraction` produces. The `questionnaire_answers` field must match the response format that Call 2 receives in production.

**Files to create:**
- `tests/calibration/cases/` — 25–40 JSON fixtures
- `tests/calibration/run_calibration.py` — runner: loads fixtures → assembles prompt via `app/dpdpa/prompts.py` builder with production params → sends to Claude → compares output → prints scorecard
- `tests/calibration/baseline_results.json` — snapshot of pre-change results (auto-generated on first run)

**Deliverable:** Running `python tests/calibration/run_calibration.py` prints a table of case ID / expected / actual / pass/fail, plus boundary-case accuracy %. A baseline run before any prompt changes is mandatory.

### B. Seed Data Verification

**Task:** Before P2 re-runs, verify that `scripts/seed_test_companies.py` covers Helix (`DPDPA+ISO`) and Vantara (`DPDPA+ISO+GDPR`) with questionnaire responses, documents, and multi-framework selection populated.

- Grep `scripts/seed_test_companies.py` for Helix / Vantara and check framework arrays
- If missing: extend seed script to add multi-framework seeded data; do not create new companies
- Document framework_ids used in each seeded engagement in `docs/plans/` or a comment in the seed script

---

## Priority 1 — Call 2 Calibration

**Effort: M**

### Goal

Fix systematic `partially_compliant` vs `non_compliant` misclassification in `app/dpdpa/prompts.py` Call 2 prompt. This is the most credibility-sensitive failure mode — a wrong status is more damaging than imprecise reasoning text.

### Design Decisions

**Status taxonomy (canonical, lives in one place):**

| Status | Rule |
|---|---|
| `compliant` | Evidence shows control implemented and operating. Both policy AND operational evidence present. |
| `partially_compliant` | Control exists but is incomplete, inconsistent, limited in scope, or applies only to some systems/BUs. |
| `non_compliant` | Control absent, contradicted by evidence, or materially ineffective. "Documented policy with no operations" defaults here, not `partially_compliant`. |
| `not_applicable` | Requirement out of scope per explicit scope rules — never assigned by model judgment alone. |

**Note on `planned`:** P1 deliberately does not introduce `planned` as a new status. The current four-value taxonomy is sufficient to fix the known misclassification. If calibration reveals a systematic pattern where neither `partially_compliant` nor `non_compliant` is the right call — e.g., intent-only evidence is being forced into one of those buckets at scale — `planned` can be added as a follow-on. It should not be introduced speculatively; adding a status has downstream costs in scoring, reporting, and review UI.

**Critical boundary rules:**
- "Documented policy + no operating evidence" → `non_compliant`, not `partially_compliant`
- "One-time practice, no repeatable control" → `non_compliant`
- "Partial rollout across some BUs" → `partially_compliant`
- "Compensating control only" → `partially_compliant`
- Contradictory evidence is high-weight; treat negative signals as dominant unless clearly outweighed
- `not_applicable` requires explicit scope justification string — never inferred

**Prompt versioning:**
- Add `CALL2_PROMPT_VERSION = "v1.1.0"` constant at top of `app/dpdpa/prompts.py`
- Add `prompt_version` TEXT column to `gap_reports` table via migration
- Populate from constant in `app/services/claude_analyzer.py` when creating `GapReport`

### Files Touched
- `app/dpdpa/prompts.py` — add version constant, revise Call 2 system/user prompt
- `app/main.py` — add `prompt_version` column to gap_reports migration
- `tests/calibration/cases/` — 25–40 JSON fixtures (new)
- `tests/calibration/run_calibration.py` — calibration runner (new)

### Calibration Case Targets

- 25–40 hand-labeled cases total
- At minimum: DPDPA and ISO examples
- At least 8 cases specifically targeting `partial` vs `non` boundary
- At least 4 cases targeting `not_applicable` (scope justification required vs inferred)
- Mix of: single-document, multi-document, contradictory-evidence, stale-policy, compensating-control-only scenarios

### Prompt Revision Principles

Revise minimally — do not rewrite the full analysis flow. Target changes:
- Add explicit decision ladder before status output
- State clearly: "absence of operating evidence is not partial compliance"
- Add contradiction handling: "when evidence conflicts, treat negative signals as dominant unless clearly outweighed"
- Add compact examples (1 sentence each) for each boundary case

### Calibration Loop

1. Run `python tests/calibration/run_calibration.py` → baseline snapshot
2. Revise prompt
3. Re-run → compare to baseline
4. Inspect misclassifications — classify as: prompt ambiguity / evidence structure / flawed expectation
5. Revise once
6. Re-run
7. Stop when: boundary-case accuracy ≥ 85% AND <2 systematic misclassifications across 2 consecutive runs

### Success Criteria
- `partial` vs `non` boundary shows no repeated systematic drift
- Calibration set stable across 2 consecutive runs at threshold
- Runner uses production prompt builder and evidence shape — no simplifications
- Prompt version constant frozen and recorded

### Definition of Done
- [ ] Status taxonomy written and referenced in prompt
- [ ] `prompt_version` column added to gap_reports
- [ ] Calibration harness created, uses production code path, baseline captured
- [ ] Revised prompt passes calibration threshold
- [ ] Prompt version string frozen at new value
- [ ] Calibration run confirms no regression on `not_applicable` cases

---

## Priority 2 — Multi-Framework E2E Validation

**Effort: M**

### Goal

Prove the full multi-framework pipeline (UCC clustering, adaptive engine, framework attribution, synthesis) works reliably on real seeded assessments before building workflow or packaging on top of it.

**Gate into P2:** P1 complete (prompt frozen, calibration passed).

### Design Decisions

**Scorecard location:** `docs/validation/` directory, one markdown file per run:
- `docs/validation/2026-05-XX-helix-dpdpa-iso.md`
- `docs/validation/2026-05-XX-vantara-dpdpa-iso-gdpr.md`

**DPDPA-only assumption audit (do this before re-runs):**
Run a targeted grep to find hardcoded DPDPA assumptions before executing validation:
```bash
grep -rn "DPDPA\|dpdpa\|chapter\|CH2\|CH3" app/routers/ app/services/ app/utils/pdf_export.py \
  --include="*.py" | grep -v "framework\|frameworks\|prompt" | head -60
```
Review results. File any hardcoded DPDPA chapter references outside of `app/dpdpa/` as bugs with root-cause label before running validation.

**Readiness calls:** Separate pass/fail for each framework combination — `DPDPA+ISO` and `DPDPA+ISO+GDPR` are not bundled into one verdict.

### Files Touched
- `scripts/seed_test_companies.py` — extend if Helix/Vantara lack multi-framework data
- `docs/validation/` — scorecard files (new directory)
- Any bug fixes surfaced during validation (per-file, case-by-case)

### Validation Scorecard Schema

For each seeded engagement, document:

```markdown
## Run: Helix Technologies — DPDPA + ISO
**Date:** YYYY-MM-DD
**Prompt version:** v1.1.0

### Execution
- [ ] Questionnaire completion gate passed
- [ ] Analysis completed without disconnect
- [ ] Synthesis completed
- [ ] Report objects persisted
- [ ] Framework score count = 2

### Cluster Expansion
- [ ] Cluster responses accepted by schema
- [ ] Prompt expansion includes correct underlying controls
- [ ] No controls silently dropped

### Output Quality (sampled, 10 items per framework)
| Framework | Req ID | Expected Status | Actual Status | Expected Severity | Actual Severity | Correct? | Notes |
|---|---|---|---|---|---|---|---|

### Issue Log
| Issue | Root Cause Label | Priority |
|---|---|---|

Root cause labels: `prompt/calibration` | `framework-mapping` | `cluster-expansion` | `scope-logic` | `scoring-logic` | `persistence/API` | `reporting/view-layer`

### Verdict
- DPDPA+ISO: PASS / FAIL / CONDITIONAL
- DPDPA+ISO+GDPR: PASS / FAIL / CONDITIONAL
```

### Detailed Work

1. **DPDPA-only assumption audit** — grep + review, file bugs, assign root-cause labels
2. **Seed verification** — confirm Helix and Vantara data in seed script (from Pre-work B)
3. **Helix re-run** — execute full pipeline, complete scorecard
4. **Cluster expansion spot-check** — sample 5 clustered questions, verify expansion behavior in prompt
5. **Vantara re-run** — execute full pipeline, complete scorecard
6. **Classify all issues** — every finding gets a root-cause label
7. **Make readiness call** — separate verdict per framework combination

### Success Criteria
- Both runs complete without errors
- Framework score array length matches framework selection count
- No cluster-related control loss in sampled spot-check
- Output quality sufficient to proceed without major trust caveats
- All issues classified by root cause

### Definition of Done
- [ ] DPDPA-only assumption audit complete
- [ ] Helix scorecard written and filed
- [ ] Vantara scorecard written and filed
- [ ] All issues classified
- [ ] Readiness verdict recorded for each framework combination

---

## Priority 3 — Manager Review Workflow

**Effort: L**

### Goal

Convert CyberAssess from a founder-operated tool into a controlled team workflow. AI findings are explicitly reviewed before becoming client-facing output.

**Gate into P3:** P2 complete, both scorecards pass (or conditional with known caveats).

**Design principle:** Analysis can be AI-assisted. Release must be human-controlled.

### Design Decisions

**Reviewer identity (MVP):** Simple `reviewer_name` TEXT field — free text string entered by the user. No User model, no auth. This is consistent with the "No auth — MVP single-user" constraint. For MVP, this can be pre-filled from an env var `REVIEWER_NAME` or entered in the UI at review time. Do not build a User model for this phase.

**Review states — separate fields, not extending existing status enum:**
The existing assessment status flow (`created → context_gathered → ... → completed / error`) is not touched. Review state is a separate concern stored in separate columns:

```
Assessment.review_status: TEXT  — null | under_review | approved | rejected
GapItem.review_status: TEXT     — draft | accepted | edited | rejected | needs_follow_up
```

This avoids conflating analysis state with review state.

**AI text preservation:** Add parallel `ai_*` columns to preserve original AI output before reviewer edits:
```
GapItem:
  ai_compliance_status TEXT    -- original AI value, never overwritten
  ai_gap_description   TEXT    -- original AI text, never overwritten  
  ai_risk_level        TEXT    -- original AI value, never overwritten
  compliance_status    TEXT    -- reviewer-editable (was already present)
  gap_description      TEXT    -- reviewer-editable (was already present)
  risk_level           TEXT    -- reviewer-editable (was already present)
  reviewer_notes       TEXT    -- new
  reviewed_by          TEXT    -- new
  reviewed_at          DATETIME -- new
```
Migration: copy current `compliance_status`, `gap_description`, `risk_level` → `ai_*` columns at migration time for existing records.

**Review UI location:** New route `/review/{assessment_id}` accessible from the report view (button: "Open Review Queue"). Separate page, not inline with report. Manager navigates to review queue, dispositions each gap item, then approves the assessment for report generation.

**Final output gating — applies to all client-facing surfaces, not just PDF:**
- `GET /api/assessments/{id}/report/pdf` — gated: requires `review_status == 'approved'`
- `GET /assessments/{id}/report` (HTML summary page in web portal) — gated in final mode: shows watermark and disabled export controls until approved
- Any future export/download route (DOCX, XLSX, etc.) must check the same gate before adding a new endpoint

Draft access (before approval) is always available for the analyst operating the tool. The gate applies only to surfaces that a client would receive. Implement gating as a shared helper so new export routes inherit it automatically rather than each needing their own check.

**Final output content:**
- Draft mode: all findings, watermark "DRAFT — Under Review", export controls disabled or watermarked
- Final mode: only `accepted` + `edited` gap items; shows "Manager Reviewed" badge with reviewer name + timestamp

### Files Touched
- `app/models/assessment.py` — add `review_status` column
- `app/models/report.py` — add `review_status`, `reviewed_by`, `reviewed_at`, `reviewer_notes`, `ai_*` columns to GapItem
- `app/main.py` — migrations for all new columns
- `app/routers/reports.py` — add review gating to PDF endpoint
- `app/routers/web.py` — add `/review/{assessment_id}` route
- `app/templates/partials/` — review queue UI template (new)
- `app/schemas/questionnaire.py` or new `app/schemas/review.py` — review action schemas
- New router: `app/routers/review.py` — PATCH endpoints for gap item disposition, assessment approval

### Assessment-Level Review States

```
null               → analysis not yet complete (no review state)
under_review       → manager has opened review queue
approved           → manager has approved for report release
rejected           → manager has rejected (requires re-analysis or manual correction)
```

### Gap Item Review States

```
draft              → AI output, not yet reviewed
accepted           → reviewer confirmed AI finding as-is
edited             → reviewer modified status/description (ai_* columns preserve original)
rejected           → reviewer dismissed (excluded from final report)
needs_follow_up    → requires additional evidence before disposition
```

### Review UI — Key Elements per Finding Card

- Framework badge + requirement ID + title
- AI status / severity (read-only display of `ai_*` columns)
- Current status / severity (editable if reviewer wants to change)
- Answer source indicators (desk review / questionnaire / document evidence)
- Evidence summary text
- Reviewer notes field
- Action buttons: Accept | Edit | Reject | Flag for Follow-up
- Filter bar: All | Draft only | High severity | Needs follow-up | By framework

### Audit Trail

Log per review action (minimal table `review_audit_log`):
- `assessment_id`, `gap_item_id` (nullable for assessment-level actions)
- `action` (accepted/edited/rejected/approved/etc.)
- `reviewer_name`
- `timestamp`
- `prior_status`, `new_status`
- `notes`

### Success Criteria
- No finalizable output (PDF, HTML summary, any download) can be delivered without explicit review approval
- Gating implemented as a shared helper — not per-route duplication
- All review actions attributed to reviewer name + timestamp
- Managers can process a full finding set without touching the database
- Draft access available to analyst before review; final output gated

### Definition of Done
- [ ] Schema extended with review fields and ai_* columns
- [ ] Migrations written for all new columns
- [ ] Review states enforced in workflow
- [ ] `/review/{assessment_id}` route and UI shipped
- [ ] Shared approval gate helper implemented
- [ ] PDF download gated via shared helper
- [ ] HTML summary page shows watermark + disabled export until approved
- [ ] Draft vs final behavior consistent across all output surfaces

---

## Priority 4 — Multi-Framework Report / Export

**Effort: L**

### Goal

Produce a report that accurately reflects multi-framework assessments — usable for demos, internal review, and early pilot delivery.

**Gate into P4:** P3 complete (review workflow live and gating enforced).

### Design Decisions

**Chart library:** Use **matplotlib** to generate chart PNGs, embed via fpdf2's `image()` method. Add to `requirements.txt` if not already present. Do not attempt SVG-in-fpdf2 or ASCII charts.

**Chart model for first milestone — two views only:**

1. **Framework score comparison** — horizontal bar chart: one bar per selected framework showing overall compliance score. Simple, honest, directly answers "which framework are we weakest on?" No domain normalization, no spider chart — those require control-count normalization that can mislead if frameworks have very different control counts.

2. **Cross-framework initiative clusters** — table or grouped list: initiatives grouped by root cause category (policy / people / process / technology / governance), each showing which frameworks they address. Directly answers "where are our weaknesses repeated across frameworks?" This is more actionable than a heatmap and doesn't require normalization.

**Deferred:** Radar/spider charts (per-domain spoke comparisons) and domain × framework heatmaps require normalizing control counts across frameworks with different granularity — that work belongs in a later iteration once the basic score surfaces are trusted.

Generate chart PNGs to a temp directory, embed in PDF, then delete.

**DPDPA-only assumption cleanup — explicit sub-task (not a throwaway pre-step):**
Before building new report structure, audit and fix `app/utils/pdf_export.py` (942 lines) for hardcoded DPDPA assumptions. Scope this as its own work item:
- Grep for `DPDPA`, `chapter`, `CH2/CH3/CH4`, hardcoded section titles
- Replace with framework-aware parameters passed from report data
- Estimate: ~2–3 hours of careful editing; do not rewrite entire file
- All text still through `S()` — no exceptions
- Test with both single-framework (DPDPA-only) and multi-framework report objects to verify backward compatibility

**Report structure (8 sections):**
1. Cover / engagement summary (frameworks selected, assessment date, reviewer name)
2. Executive summary (narrative, overall maturity)
3. Frameworks + scope summary (per-framework: version, scope, total controls assessed)
4. Overall maturity snapshot (aggregate score, status distribution)
5. Per-framework score pages (one page per framework: scores by domain, top gaps)
6. Cross-framework visual summary (radar chart + initiative rollup by root cause)
7. Detailed findings by framework (gap items, filtered to accepted+edited in final mode)
8. Appendix (methodology, answer-source legend, reviewer attestation if approved)

**Draft vs final alignment (requires P3):**
- Draft: all findings, watermark, no reviewer attestation
- Final: accepted+edited findings only, reviewer name+timestamp in cover, "Manager Reviewed" badge

**Scope for first milestone:** Accurate multi-framework PDF. No remediation tracking, no policy generation, no client portal, no executive slide export.

### Files Touched
- `app/utils/pdf_export.py` — DPDPA assumption cleanup + multi-framework sections
- `app/routers/reports.py` — pass framework-aware data to export
- `app/services/scoring.py` — verify per-framework score output structure is complete
- `requirements.txt` — add `matplotlib` if not present
- New helper: `app/utils/chart_generator.py` — matplotlib chart PNG generation

### DPDPA Assumption Audit (Sub-task)

```bash
grep -n "DPDPA\|Chapter\|chapter\|CH[2-6]\|\"consent\"\|\"breach\"\|\"cross.border\"" \
  app/utils/pdf_export.py
```

For each hit:
- If it's a section heading: parameterize from report data
- If it's a count/scope reference: replace with framework-aware count from report object
- If it's a chapter reference: replace with framework section reference

### Success Criteria
- `DPDPA+ISO` assessment exports with correct framework sections and counts
- `DPDPA+ISO+GDPR` assessment exports without falling back to DPDPA-only headings
- Framework score comparison bar chart renders and embeds correctly
- Cross-framework initiative cluster view is present and accurate
- Draft and final modes produce distinct outputs
- Output is understandable to a reviewing manager without verbal explanation

### Definition of Done
- [ ] DPDPA assumptions cleaned from pdf_export.py
- [ ] Framework-aware export path implemented
- [ ] Per-framework score pages render
- [ ] Framework score comparison bar chart generated and embedded
- [ ] Cross-framework initiative cluster view included
- [ ] Draft/final mode behavior wired to review workflow
- [ ] One full demo export (Helix, DPDPA+ISO) verified end-to-end

---

## Cross-Cutting Decisions

### Prompt Versioning
- Format: `"v{major}.{minor}.{patch}"` — e.g., `v1.1.0`
- Lives as `CALL2_PROMPT_VERSION` constant in `app/dpdpa/prompts.py`
- Stored in `gap_reports.prompt_version` TEXT column
- Increment minor on any calibration-motivated change, patch on editorial fixes
- Record version + rationale in a comment block above the constant

### `planned` Status — Conditional Follow-on
Not introduced in P1. If calibration reveals that intent-only evidence patterns are being systematically misclassified and neither `non_compliant` nor `partially_compliant` fits cleanly, add `planned` as a follow-on after P1 closes. At that point: add to `GapItem.compliance_status` via migration in `_run_migrations()`, score at 10, update scoring map and prompt taxonomy together.

### Testing Strategy
- No pytest for now — calibration runner is a standalone script
- If/when pytest is added, calibration fixtures can be loaded as parametrized test cases
- Validation scorecards in `docs/validation/` serve as the manual E2E record
- Smoke test: after any prompt change, run 1 seeded assessment end-to-end and check report object

### What Not to Build in This Plan
- Policy generation
- Remediation tracking
- Executive dashboard expansion
- RBAC / SSO
- External integrations
- Additional framework screening domains beyond current set

---

## Milestones

| Milestone | Outcome | Key Deliverables |
|---|---|---|
| M1 | Trusted analysis core | Calibration harness live, prompt frozen, Helix re-run complete |
| M2 | Validated multi-framework pipeline | Vantara re-run, scorecards filed, readiness verdicts recorded |
| M3 | Team-safe review process | Review states live, UI shipped, PDF gating enforced |
| M4 | Pilot-grade deliverable | Multi-framework PDF shipped, draft/final modes, one demo export verified |

---

## Effort Summary

| Priority | Effort | Primary Constraint |
|---|---|---|
| Pre-work | S | Scaffolding — 1 session |
| P1: Calibration | M | Fixture creation + iteration loop |
| P2: E2E Validation | M | Seed data + manual scorecard review |
| P3: Review Workflow | L | Schema + UI + gating — largest surface area |
| P4: Report/Export | L | pdf_export.py surgery + chart integration |
