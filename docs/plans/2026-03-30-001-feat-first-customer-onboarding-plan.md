---
title: First Customer Onboarding — White-Glove DPDPA Assessment
type: feat
status: active
date: 2026-03-30
origin: docs/brainstorms/2026-03-30-first-customer-requirements.md
---

# First Customer Onboarding — White-Glove DPDPA Assessment

## Overview

Get a finished CyberAssess DPDPA gap report into the hands of a real vendor company by 2026-04-05. The delivery model is consulting-led: Saqlain conducts a structured interview, fills the questionnaire, runs the backend, and delivers the report. No frontend required.

The quality bar is audit-grade — every finding, score, and recommendation must be defensible to a CISO or Board Risk Committee. The three parallel workstreams are: outreach/targeting (Day 1), interview facilitation materials (Day 2), and report hardening (Day 2–3).

---

## Problem Statement

Backend and pipeline are complete. The gap is three things:
1. **No GTM motion** — no target company, no outreach message, no sample collateral
2. **No facilitation process** — no interviewer guide, no protocol for running a structured assessment session
3. **Report is not audit-grade** — PDF/HTML lacks methodology, scope/limitations, and evidence log sections that a compliance buyer would expect

---

## Proposed Solution

Three parallel tracks against a 6-day deadline:

**Track A — GTM (Day 1)**: Sanitize existing test output into a sample report, build a target list of 5 vendor companies, draft and send outreach.

**Track B — Facilitation (Day 2)**: Generate a facilitator's guide from the existing questionnaire code, define the interview protocol, write a pre-research workflow checklist.

**Track C — Report Hardening (Day 2–3)**: Add scope/limitations, methodology, and evidence log sections to the PDF and HTML dashboard.

**Track D — Delivery (Day 4–6)**: Conduct interview, run assessment, deliver report, schedule follow-up.

---

## Technical Considerations

### What's already correct (do not change)

- **CMMI M0–M5 criteria**: Explicitly defined in `prompts.py` lines 68–75. Already audit-defensible. No changes needed.
- **Company-specific context injection**: `build_user_prompt()` in `prompts.py:184` passes company name, industry, size, description, and full risk profile. Claude is instructed to tailor findings to industry and size. Already in place.
- **Evidence extraction pipeline**: Two-call architecture in `claude_analyzer.py` extracts document quotes in Call 1, injects them into Call 2. Already working.
- **Scoring determinism**: `scoring.py` weighted scoring is fully deterministic and reproducible. Not_assessed answers are excluded from the denominator. Acceptable for white-glove mode.

### What needs to be added

- **PDF: Scope & Limitations section** — new page in `pdf_export.py` before gap details. Plain text, no visuals needed.
- **PDF: Methodology section** — brief section explaining scoring model, chapter weights, GRC scale, CMMI criteria. Makes the score reproducible by an auditor.
- **PDF: Evidence Log section** — per-gap column showing `evidence_quote` from the database. This field is already populated by Claude but not rendered in the PDF.
- **Facilitator's guide script** — a new script in `scripts/` that reads `questionnaire.py` + `context_questions.py` and outputs a printable Markdown guide with space for notes per question.
- **Sanitized sample report** — rerun the seed script with "Meridian Retail Ltd" as dummy company, export clean PDF.

---

## System-Wide Impact

- `pdf_export.py` changes are additive (new pages/sections). No existing sections are modified. No API changes.
- Facilitator's guide script is read-only against the codebase — reads question text, produces a Markdown file. No side effects.
- Sample report reuse: the existing `data/` output from the Prestige Estates test can be regenerated using `scripts/seed_prestige_analysis.py` with company name swapped to "Meridian Retail Ltd." No real client data in the deliverable.

---

## Acceptance Criteria

### Track A — Outreach (Day 1)
- [ ] A1. A sanitized PDF sample report exists with "Meridian Retail Ltd" as the company name — no internal test artifacts
- [ ] A2. A target list of 5 vendor companies from Flipkart / Morgan Stanley / CRED ecosystems, each with: company name, contact name/title, LinkedIn URL, public privacy policy URL (if available), and rationale for selection
- [ ] A3. Two outreach message variants exist (LinkedIn DM + email), leading with audit-prep hook, referencing the sample report

### Track B — Facilitation (Day 2)
- [ ] B1. A `scripts/generate_facilitator_guide.py` script outputs `docs/facilitator-guide.md` — all 15 context questions and 41 requirement questions, grouped by block/chapter, each with space for notes and a follow-up probe
- [ ] B2. An interview protocol document (`docs/interview-protocol.md`) covering: recommended attendees from client side, session framing script, how to handle "I don't know," how to probe for evidence vs. intent, how to close and set report delivery expectation
- [ ] B3. A pre-research checklist (`docs/pre-research-checklist.md`) covering: public privacy policy review, website privacy notice, app store listings, LinkedIn company page, news/regulatory mentions

### Track C — Report Hardening (Day 2–3)
- [ ] C1. PDF contains a **Scope & Limitations** section stating: questionnaire-based assessment (not a formal audit), findings based on disclosed information, independent verification recommended for high-risk gaps, assessment date
- [ ] C2. PDF contains a **Methodology** section with: DPDPA 41-requirement framework overview, chapter weights (CH2 30%, CH3 20%, CH4 20%, CB 15%, BN 15%), GRC 5-option scale definitions, CMMI M0–M5 criteria, scoring formula
- [ ] C3. PDF contains an **Evidence Log** section (or per-gap column) showing the `evidence_quote` value for each gap item — distinguishing verbatim document quotes from "No relevant language found"
- [ ] ~~C4. HTML dashboard~~ — deferred. No HTML generation code exists in the current app; PDF is the sole week-1 deliverable.

### Track D — Delivery
- [ ] D1. At least one interview is conducted with a real company
- [ ] D2. Assessment is run through the backend and report generated
- [ ] D3. Report is reviewed by Saqlain against the Lead Auditor standard before sending
- [ ] D4. Report is delivered to the company contact
- [ ] D5. A follow-up remediation call is booked within 1 week of delivery

---

## Schedule Risk & Mitigation

**Risk**: Cold outreach in 6 days is aggressive. Mitigation escalation order:
1. Send to all 5 targets on Day 1 simultaneously
2. Prioritize warm connections (former colleagues, known founders) for first engagement
3. **Day 3 trigger**: If no meeting booked, produce a complimentary assessment from the best target's public privacy policy and send the report unsolicited as a door-opener

---

## Day-by-Day Execution Plan

| Day | Date | Critical Path | Parallel |
|-----|------|---------------|----------|
| 1 | Mar 30 | A1: Sanitize sample report · A2: Target list · A3: Outreach messages · **Send outreach** | — |
| 2 | Mar 31 | B1: Facilitator's guide · B2: Interview protocol · B3: Pre-research checklist | C1–C2: Start PDF hardening |
| 3 | Apr 1 | Follow up on outreach · Book interview · Pre-research top target | C3–C4: Finish PDF hardening |
| 4–5 | Apr 2–3 | D1: Conduct interview · D2: Run assessment | — |
| 6 | Apr 4–5 | D3: Review report · D4: Deliver · D5: Book follow-up | Backup: unsolicited report |

---

## Implementation Notes

### A1 — Sanitized Sample Report
Run `scripts/seed_prestige_analysis.py` with `COMPANY_NAME = "Meridian Retail Ltd"` and regenerate the PDF. Verify no internal artifacts (file paths, test IDs) appear in the output. Export to `docs/sample-report-meridian-retail.pdf`.

### B1 — Facilitator's Guide Script
`scripts/generate_facilitator_guide.py` should:
1. Import `CONTEXT_BLOCKS` from `app.dpdpa.context_questions`
2. Import `_QUESTION_TEXT` from `app.dpdpa.questionnaire`
3. Import `DPDPA_FRAMEWORK` from `app.dpdpa.framework` for chapter/section structure
4. Output Markdown with: session header, context block per section, then questionnaire per chapter
5. Each question: ID, full question text, answer options, `**Notes:**` and `**Evidence seen:**` blank fields

### C1–C3 — PDF Report Hardening
New pages are added inside `generate_pdf()` in `app/utils/pdf_export.py`. Insert them after the initiatives section and before the detailed gap cards (or as a final appendix). Use existing `_section_title()` helper and plain `pdf.multi_cell()` for text blocks. The evidence log can be rendered as an extra column in the existing gap card layout or as a separate appendix table.

### C4 — HTML Dashboard (Deferred)
The HTML dashboard (`data/prestige_estates_dashboard*.html`) was a one-off generated file — it was deleted after the live test and no HTML generation code exists in the current app. **C4 is out of scope for week 1.** PDF is the sole deliverable. The HTML dashboard can be built as a separate feature when self-serve frontend work begins.

---

## Dependencies & Assumptions

- `scripts/seed_prestige_analysis.py` was deleted — need to recreate a demo seed script from scratch. The script should: create an assessment in the DB with Meridian Retail Ltd, insert plausible pre-canned gap items (no Claude API call needed), then call `generate_pdf()` directly.
- `evidence_quote` confirmed in `GapItem` model at `app/models/report.py:40`, available in `generate_pdf()` via `items` list — just not rendered yet.
- No HTML template exists — PDF-only delivery for week 1.
- Claude API key available and working for live assessment run.

---

## Files to Create / Modify

| File | Action | Track |
|------|--------|-------|
| `scripts/generate_facilitator_guide.py` | Create | B1 |
| `docs/facilitator-guide.md` | Generated output | B1 |
| `docs/interview-protocol.md` | Create | B2 |
| `docs/pre-research-checklist.md` | Create | B3 |
| `scripts/seed_demo_report.py` | Create (replaces deleted seed script) | A1 |
| `docs/sample-report-meridian-retail.pdf` | Generate via seed script | A1 |
| `app/utils/pdf_export.py` | Modify — add 3 new sections | C1–C3 |
| ~~HTML dashboard~~ | ~~Deferred — no template exists~~ | ~~C4~~ |

---

## Sources & References

**Origin document:** [docs/brainstorms/2026-03-30-first-customer-requirements.md](../brainstorms/2026-03-30-first-customer-requirements.md)

Key decisions carried forward:
- White-glove consulting model (no frontend for week 1) — see origin: Approach
- Audit-grade reliability as quality bar — see origin: Quality Standard
- Free report → paid remediation GTM motion — see origin: R3

**Internal references:**
- Questionnaire questions: `app/dpdpa/questionnaire.py:24`
- Context questions: `app/dpdpa/context_questions.py:8`
- CMMI criteria: `app/dpdpa/prompts.py:68`
- PDF sections: `app/utils/pdf_export.py:419` (`generate_pdf`)
- Scoring engine: `app/services/scoring.py:33`
- Dummy company convention: "Meridian Retail Ltd" (see project memory)
