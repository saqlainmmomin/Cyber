---
date: 2026-04-04
topic: intelligent-audit-assistant
---

# CyberAssess: Intelligent Audit Assistant

## Problem Frame

CyberAssess currently operates as a structured-but-static assessment tool. Clients answer a fixed questionnaire, upload documents, and receive a gap report. While the two-phase questionnaire (context gathering → adaptive sections) adds some intelligence, it still feels like a form — not an auditor.

A seasoned auditor works differently: they review documents first, arrive with hypotheses, ask pointed questions based on what they found, probe deeper when answers don't add up, generate targeted evidence requests, and know what signals to look for based on the client's industry. The tool should replicate this workflow.

Additionally, inputs are currently captured via Excel sheets and API calls — this needs to be replaced with a web-based assessment portal.

## Requirements

### Evidence Intelligence (Core — Build First)

- R1. **Desk Review Phase**: When documents are uploaded, the tool automatically analyzes them before the questionnaire begins. It catalogs each document, extracts key provisions, and maps findings to specific DPDPA requirements.
- R2. **Cross-referencing (Level 1)**: The tool detects contradictions between questionnaire answers and uploaded document content. Example: client claims breach notification process exists, but uploaded policy omits the 72-hour DPDPA timeline.
- R3. **Absence Detection (Level 2)**: The tool identifies what's missing from uploaded documents relative to DPDPA requirements. Example: privacy policy has no mention of data principal rights under Chapter 3, no consent withdrawal mechanism, no children's data handling.
- R4. **Signal Detection (Level 3)**: The tool catches red flags that reveal deeper compliance issues. Examples: privacy policy references "legitimate interest" (GDPR concept, not in DPDPA), consent language buried in a 40-page T&C instead of being "clear, specific, and informed," copy-pasted GDPR templates with no DPDPA adaptation.
- R5. **Evidence Cataloging & Mapping**: Uploaded documents are automatically cataloged (document type, coverage area) and mapped to the DPDPA requirements they address. This replaces manual auditor effort.

### Dynamic Questionnaire

- R6. **Evidence-Informed Questioning**: Desk review findings shape the questionnaire. Questions about areas already covered by documents are skipped or shortened. Areas where red flags were detected get deeper, more pointed questions.
- R7. **Industry-Specific Question Banks**: Different industries receive fundamentally different questions beyond relevance weighting. A fintech gets questions about payment data flows and RBI overlap. A healthcare company gets questions about sensitive health data handling. Not the same 41 questions with different weights — different questions entirely.
- R8. **Conversational Follow-ups**: When an answer doesn't add up or reveals a potential gap, the tool asks probing follow-up questions rather than moving to the next fixed question. Example: "You said you have consent mechanisms — how do you handle consent withdrawal for derived/inferred data?"

### RFI Generation

- R9. **Formal RFI Document**: After the assessment, the tool generates a structured Request for Information document listing: specific evidence items needed, the DPDPA requirement each maps to, priority level, and suggested deadline. This is a standalone, client-ready document the auditor can send directly.

### Policy Generation

- R10. **Core DPDPA Policies**: Generate Privacy Policy, Consent Management Policy, Breach Notification Procedure, and Data Retention Policy — the policies every org needs under DPDPA and most lack.
- R11. **Role-Specific Policies**: Based on the assessment findings (SDF status, processing activities, cross-border transfers), generate additional policies: DPIA Template, DPO Appointment Charter, Vendor/Data Processor Agreement template, and others as the org's profile requires.
- R12. **Hybrid Generation Approach**: Policies use a template structure (required sections, mandatory DPDPA clauses, standard legal language) with AI-generated content tailored to the org's actual context (industry, size, data types, processing activities, identified gaps). Human review gate before delivery.

### Assessment Flow (New Three-Phase Design)

- R13. **Phase 1 — Desk Review**: Client uploads broad evidence (privacy policy, public information). AI performs preliminary analysis — flags red flags, missing clauses, signal detection. Generates initial evidence map.
- R14. **Phase 2 — Adaptive Assessment**: Questionnaire dynamically shaped by desk review findings + industry context + org profile. Includes conversational follow-ups when answers need probing.
- R15. **Phase 3 — Outputs**: Gap report (existing, enhanced with evidence intelligence), formal RFI document, and generated policies for identified gaps. All outputs are client-ready.

### Web-Based Assessment Portal

- R16. **Replace Excel Workflow**: A web interface where the auditor (and eventually the client) can upload documents, answer questions in a guided flow, view assessment progress, and access all outputs. Professional, clean experience — not a spreadsheet.

## Success Criteria

- An assessment using the new flow produces demonstrably richer gap analysis than the current static questionnaire — specifically catching contradictions and red flags that the old flow missed.
- The RFI document is professional enough to send to a client without manual editing.
- Generated policies contain correct DPDPA structure and org-specific substance, requiring only legal review — not a rewrite.
- Assessment preparation time for the auditor is meaningfully reduced compared to the current Excel-based workflow.
- A client reviewing the output says "this tool understands our situation" — not "this is a generic checklist."

## Scope Boundaries

- **DPDPA only** — no multi-framework support yet, but architectural decisions should not prevent future extension to ISO 27001, SOC 2, GDPR.
- **No compliance monitoring over time** — this remains a point-in-time assessment tool. No progress tracking between assessments, no ongoing monitoring, no re-assessment scheduling.
- **Contextual inference (Level 4) deferred** — industry-context-based gap inference (e.g., healthcare company + no sensitive data handling = inferred gap) is a future enhancement once the industry-adaptive questionnaire is mature.

## Key Decisions

- **Evidence intelligence before questionnaire**: Documents are analyzed first, findings shape the questionnaire. This mirrors how a seasoned auditor works.
- **Levels 1-3 for evidence intelligence**: Cross-referencing, absence detection, and signal detection. Level 4 (contextual inference) deferred.
- **Formal RFI as standalone output**: Not just a section in the report — a client-ready document.
- **Hybrid policy generation**: Template structure + AI content. Ensures no mandatory clauses are missed while providing org-specific customization.
- **Web portal over Excel**: Professional input experience, guided flow, replaces spreadsheets.

## Outstanding Questions

### Resolved

- [R16] **Frontend: Jinja2 + HTMX + Tailwind CSS** within the FastAPI repo. Server-rendered for minimal attack surface, HTMX for dynamic questionnaire flow, Tailwind for professional styling. Single repo/deployment, server-side auth.
- [R7] **1 industry vertical (IT/SaaS) + generic bank** for v1. Prove the architecture with one deep vertical, add more incrementally.

### Deferred to Planning

- [Affects R1-R5][Technical] How should the desk review pipeline integrate with the existing two-call Claude analysis? Add a pre-analysis call, or restructure into a multi-step agent pipeline?
- [Affects R6-R8][Needs research] What's the right architecture for dynamic question generation? Pre-defined branching trees vs. LLM-generated follow-ups vs. a hybrid?
- [Affects R10-R12][Needs research] What policy template structure ensures DPDPA clause completeness? Needs research into DPDPA mandatory provisions per policy type.
- [Affects R9][Technical] RFI document format — PDF, DOCX, or both?
- [Affects R16][Technical] Authentication and multi-tenancy approach for the web portal.

## Next Steps

→ `/ce:plan` for structured implementation planning.
