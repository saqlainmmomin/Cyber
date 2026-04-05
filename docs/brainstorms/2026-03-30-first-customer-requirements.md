---
date: 2026-03-30
topic: first-customer-onboarding
---

# CyberAssess — First Customer by 2026-04-05

## Problem Frame

Backend and report pipeline are complete. The gap is GTM: no target company identified, no outreach sent, no facilitation process documented. The binding constraint is calendar — 6 days to identify a company, get a response, conduct an interview, run the assessment, and deliver the report. Cold outreach response rates make this tight. Everything that isn't on the critical path to "report in their hands" is deferred.

**Quality standard**: Audit-grade reliability. Every output must be defensible to a CISO, Board Risk Committee, or external certification body. The bar is Big 4 engagement quality. Every design decision is evaluated against: *Would a Lead Auditor sign off on this?*

**Approach**: White-glove consulting. Saqlain conducts a structured interview, fills the questionnaire, runs the backend, delivers the report. No frontend needed. First engagements are free gap reports → paid remediation consulting.

---

## Requirements

### Outreach & Targeting (Day 1 — Critical Path)

- R1. **Sanitized sample report**: Take the existing Meridian Retail test output, strip any internal artifacts, and produce a clean PDF that can be attached to outreach. This is the single highest-leverage collateral — prospects see the deliverable before committing to a meeting.
- R2. **Target list**: 5 vendor companies from Flipkart / Morgan Stanley / CRED ecosystems. Prioritise: public privacy policy available (pre-research is easier), 100–2000 employees, known enterprise audit exposure.
- R3. **Outreach message**: Leads with the audit-prep hook, not the tool. "Your enterprise clients will audit you on DPDPA. Let me show you where you'll fail before they do." One variant for LinkedIn DM, one for email. Attach or link the sample report.

### Interview Facilitation (Day 2 — Parallel with Outreach Follow-up)

- R4. **Pre-research workflow**: Before the interview, research the target company — public privacy policy, website privacy notice, app store listings, LinkedIn company page, news/regulatory mentions. This pre-research is what makes the interview feel expert-led and the report company-specific.
- R5. **Facilitator's guide**: All questionnaire questions (context block + all sections) in a printable format with space for notes and follow-up probes. Formatted for in-person or Zoom.
- R6. **Interview protocol**: Who should be in the room from the client side (recommend: DPO or privacy lead + IT/security head + someone from legal). How to open (frame as collaborative assessment, not audit). How to handle "I don't know" (mark as gap, note for follow-up). How to probe for evidence vs. intent. How to close (set report delivery timeline — 48 hours).

### Report Hardening (Day 2–3 — Parallel Track)

- R7. **Scope and limitations section**: Report must state it is a questionnaire-based gap assessment, not a formal audit. Findings based on disclosed information. Recommend independent verification for high-risk gaps.
- R8. **Methodology section**: Explain the 41-requirement DPDPA framework, 5-option GRC scale, weighted scoring model per chapter, and CMMI maturity criteria (M0–M5 with explicit definitions). An auditor should be able to reproduce a score from the methodology description alone.
- R9. **Evidence log section**: List what was reviewed — documents provided, questions answered, public sources referenced. Distinguish "disclosed" evidence from "inferred" findings.
- R10. **Company-specific gap descriptions**: Claude-generated gap narratives must reference the company's disclosed context (sector, data volumes, processing activities). Generic boilerplate is not audit-grade.
- R11. **CMMI rating criteria**: Each maturity level (M0–M5) must have explicit, documented criteria so ratings are consistent and defensible. Check existing implementation first — may already be adequate from live test.

### Delivery (Day 4–6)

- R12. **Conduct interview**: Run the structured interview, capture responses, note evidence provided.
- R13. **Run assessment + deliver report**: Process through backend, generate HTML dashboard + PDF. Review output for accuracy before sending. Deliver via email with a brief cover note framing next steps (remediation consulting).
- R14. **Schedule follow-up**: Book a 30-minute remediation pitch call within 1 week of report delivery.

---

## Scope Boundaries (Explicitly Deferred)

- **Frontend** — not on critical path; white-glove model makes it unnecessary for first 5 engagements
- **Self-serve client access** — no portal, login, or invite flow
- **Hosting / deployment** — backend runs locally; report delivered as PDF/HTML file
- **Payment / invoicing** — first report is free
- **Multi-framework** (ISO 27001, SOC 2, GDPR) — DPDPA only
- **Assessment logic edge cases** (NA-heavy scoring, all-compliant edge cases, API failure handling) — in white-glove mode, Saqlain controls the input; harden these for scale, not week 1
- **Workflow log template** — just take notes for the first engagement; formalise after

---

## Success Criteria

1. A named, real company has received a CyberAssess DPDPA gap report by 2026-04-05
2. The report passes the Lead Auditor test: every finding, score, and recommendation is defensible if challenged
3. At least one follow-up conversation (remediation pitch) is scheduled
4. Saqlain has enough notes from the first engagement to run the second one without inventing process

---

## Schedule Risk & Mitigation

**Risk**: Cold outreach → response → meeting → interview → report in 6 days is aggressive.

**Mitigations** (escalate in order):
1. Send outreach to all 5 targets on Day 1, not sequentially
2. Tap warm connections — even a friend's company or former colleague's employer counts for the first engagement
3. **Backup (Day 3 trigger)**: If no meeting is booked by end of Day 3, pick the most promising target with a public privacy policy, produce a complimentary assessment from public information alone, and send the report unsolicited as a door-opener. "I assessed your DPDPA exposure based on public information — here's what I found."

---

## Outstanding Questions

### Deferred to Planning

- **[Affects R8][Technical]** What are the current CMMI M0–M5 assignment criteria in the codebase? Check `scoring.py` and `prompts.py` — may already be explicit enough.
- **[Affects R10][Technical]** How much company-specific context does the current Claude prompt inject into gap descriptions? Check against Prestige Estates test output.
- **[Affects R5][Technical]** Best format for facilitator's guide — generate from `questionnaire.py` + `context_questions.py` into printable Markdown/PDF?
- **[Affects R9][Needs research]** What does the current evidence extraction call return for uploaded documents? Check `claude_analyzer.py`.
- **[Affects R7, R8][Technical]** Where in the HTML/PDF template do methodology and limitations sections get inserted? Check `pdf_export.py` and dashboard template.

---

## Next Steps

→ `/ce:plan` for structured implementation planning.

**Day-by-day critical path:**

| Day | Priority | Parallel |
|-----|----------|----------|
| **1 (Mar 30)** | R1: Sanitize sample report. R2: Target list. R3: Outreach. Send. | — |
| **2 (Mar 31)** | R4: Pre-research top targets. R5: Facilitator's guide. | R7–R8: Start report hardening |
| **3 (Apr 1)** | Follow up outreach. Book interview. | R9–R11: Finish report hardening |
| **4–5 (Apr 2–3)** | R12: Conduct interview. R13: Run assessment + deliver. | — |
| **6 (Apr 4–5)** | R13: Deliver report. R14: Schedule follow-up. | Backup: unsolicited report if no meeting |
