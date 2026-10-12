# Static prototype review

Open the five HTML files directly from disk. No server, browser build or CDN is needed. Inter loads from ../../../app/static/fonts/. All five share prototype.css tokens, layout and component classes. No production writes or AI calls occur. External citation links point to the existing app and need that app to read source files; rendering the screens itself works offline. Navigation destinations without a dedicated prototype use clearly named local panels. This is not a complete application.

questionnaire.html: the full staff frame exposes one stage bar and one labelled Section select. The ISO-domain rail uses the four Annex A themes. Two full-width work surfaces show an unanswered-state example and the real approved access-rights conclusion. Requirement, why and client hint have distinct roles. Draft state and completion remain separate. The marked Scope panel asks only for exclusions and shows the standard default justification. The unanswered question is a local state demonstration reset from the released source, not a claim that live data is incomplete.

review-queue.html: the six real interim candidates appear with gap titles, outcome, risk and review state in words. Pending entries come first. Sort and selection work locally. The selected finding keeps decisions at the top while gap, outcome, impact, full-weight recommendation and reasoning, and one provenance narrative follow in order. File links are one click away. No interviews are invented. Local decision previews do not persist or authorize production actions.

conclusions.html:32 real ISO conclusions across all four domains fill a deterministic five-column sheet. Rows expand across the full table width to gap, status, risk/impact, recommendation/logic and one provenance narrative. The final view removes review mechanics. Missing impact and reasoning are stated honestly. It is a populated subset of the93 source ISO controls, not a claim of completeness for the detailed inventory.

rfi.html:40 real request artifacts form a tight sortable list. Guidance is closed by default and retains what to send, example and good looks like. The first two artifacts demonstrate illustrative draft inclusion instead of an add form; source mapping counts remain real. The target backend must reconcile received, requested and issued identity. Candidate buttons turn into included state locally. Versions and links are flattened Section choices pointing to marked explanatory panels. No live issued-version or client-link records are fabricated.

report.html: the board view starts with written engagement context, then all four ISO domains from weakest organizational to strongest physical, with each real non-compliant or partial conclusion, impact, recommendation and logic. The Section selector switches to auditor detail with all 93 controls and source trace. Framework scores are not combined. The mixed source assessment is explicitly ISO-focused; DPDPA results remain separate. Board narrative is illustrative content, not accepted report prose.

## Source and state limits

GET curl responses from current assessment d491ee73-0925-43bd-8cb2-3b5fff2cc8ac and interim 506d1f04-9c19-44e4-9fdd-fa286f2b4eb6 supply the runtime content. The current assessment actually contains DPDPA and ISO, not ISO alone. source-data.json retains the extracted source and field names. The questionnaire demonstrates the target single-framework ISO grouping; multi-framework UCC grouping is specified, not prototyped. Form, sort, disclosure and view switches are local demonstrations. Autosave network behavior, review blockers/conflict handling and inclusion identity require implementation verification. No browser was launched and no runtime layout screenshots of these prototypes were taken in this run. Host QA must measure horizontal overflow at 1440/1280, font sizes and full prose lines, sticky decision visibility and keyboard focus.

## Every illustrative element

Each row is an exact HTML id with data-illustrative=true. Paired backend/content dependencies are explicit.

| Screen | Element ID | Classification | Dependency |
| --- | --- | --- | --- |
| questionnaire.html | q1-why | Content | Static per-control why_asked field |
| questionnaire.html | q1-hint | Content | Static per-control client_prompt_hint field |
| questionnaire.html | q2-why | Content | Static per-control why_asked field |
| questionnaire.html | q2-hint | Content | Static per-control client_prompt_hint field |
| questionnaire.html | soa-standard | Content | Authored standard justification plus Backend default applicability source marker |
| review-queue.html | queue-title-0 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue.html | finding-title-0 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue.html | finding-impact-0 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue.html | finding-reason-0 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue.html | finding-provenance-0 | Content | Reviewed provenance narrative with Backend method/interview source records |
| review-queue.html | queue-title-1 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue.html | finding-title-1 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue.html | finding-impact-1 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue.html | finding-reason-1 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue.html | finding-provenance-1 | Content | Reviewed provenance narrative with Backend method/interview source records |
| review-queue.html | queue-title-2 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue.html | finding-title-2 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue.html | finding-impact-2 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue.html | finding-reason-2 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue.html | finding-provenance-2 | Content | Reviewed provenance narrative with Backend method/interview source records |
| review-queue.html | queue-title-3 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue.html | finding-title-3 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue.html | finding-impact-3 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue.html | finding-reason-3 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue.html | finding-provenance-3 | Content | Reviewed provenance narrative with Backend method/interview source records |
| review-queue.html | queue-title-4 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue.html | finding-title-4 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue.html | finding-impact-4 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue.html | finding-reason-4 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue.html | finding-provenance-4 | Content | Reviewed provenance narrative with Backend method/interview source records |
| review-queue.html | queue-title-5 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue.html | finding-title-5 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue.html | finding-impact-5 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue.html | finding-reason-5 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue.html | finding-provenance-5 | Content | Reviewed provenance narrative with Backend method/interview source records |
| conclusions.html | conclusion-title-0 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-1 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-2 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-3 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-4 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-5 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-6 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-7 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-8 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-9 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-10 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-11 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-12 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-13 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-14 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-15 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-16 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-17 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-18 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-19 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-20 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-21 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-22 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-23 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-24 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-25 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-26 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-27 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-28 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-29 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-30 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| conclusions.html | conclusion-title-31 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| rfi.html | rfi-included-0 | Backend | Illustrative inclusion state; stable cross-source request identity/state contract, not live receipt or issuance |
| rfi.html | rfi-included-1 | Backend | Illustrative inclusion state; stable cross-source request identity/state contract, not live receipt or issuance |
| report.html | report-executive | Content | Accepted per-assessment executive narrative, exposed by existing narrative/board read model |
| report.html | report-organizational-impact-0 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-0 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-1 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-1 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-2 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-2 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-3 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-3 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-4 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-4 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-5 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-5 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-6 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-6 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-7 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-7 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-8 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-8 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-9 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-9 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-10 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-10 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-11 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-11 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-12 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-12 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-13 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-13 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-14 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-14 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-15 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-15 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-16 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-16 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-17 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-17 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-18 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-18 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-19 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-19 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-20 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-20 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-people-impact-0 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-people-reason-0 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-people-impact-1 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-people-reason-1 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-people-impact-2 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-people-reason-2 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-technological-impact-0 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-technological-reason-0 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-technological-impact-1 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-technological-reason-1 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-technological-impact-2 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-technological-reason-2 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-technological-impact-3 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-technological-reason-3 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-technological-impact-4 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-technological-reason-4 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-physical-strength | Content | Board domain narrative generated per assessment |
| conclusions.html | conclusion-impact-0 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-0 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-0 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-1 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-2 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-3 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-impact-4 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-4 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-4 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-impact-5 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-5 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-5 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-6 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-7 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-8 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-9 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-impact-10 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-10 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-10 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-impact-11 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-11 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-11 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-impact-12 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-12 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-12 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-13 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-14 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-15 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-impact-16 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-16 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-16 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-impact-17 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-17 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-17 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-impact-18 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-18 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-18 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-19 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-20 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-21 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-22 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-23 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-24 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-25 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-impact-26 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-26 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-26 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-impact-27 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| conclusions.html | conclusion-reason-27 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| conclusions.html | conclusion-provenance-27 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-28 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-29 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-30 | Content | Reviewed provenance narrative with method/interview source records |
| conclusions.html | conclusion-provenance-31 | Content | Reviewed provenance narrative with method/interview source records |
