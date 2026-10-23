# Static prototype review

> Second design pass, 13 Oct 2026. After Saqlain's review, `prototype.css` was rewritten around seven fixed type roles, all six screens were redrawn on it, and both navigation options were replaced by a stepper with a hideable sidebar (`review-queue-sidebar.html` is removed). `tools/build_prototypes.py` regenerates every screen from the JSON files in this folder (`findings.json`, `conclusions.json`, `rfi.json`, `report.json`). The per-screen notes below describe the first pass where they differ.

Placeholders added in the second pass (questionnaire.html): `q-rail-counts`, `q-section-progress`, `q-row-states`, `q2-response`. All depend on saved draft responses (Backend).

Open the seven HTML files directly from disk. No server, browser build or CDN is needed. Inter loads from ../../../app/static/fonts/. All seven share prototype.css. Citation and Findings/Workpaper destinations need the existing app; these views are not static prototypes. Sorts, disclosures and state changes are local demonstrations with no production writes or AI calls.

questionnaire.html: one stage bar and the Option A Section select frame the four ISO domain links. Full-width unanswered and answered question surfaces preserve requirement, why and client hint hierarchy. Prose, bold requirements and guidance cap at 56ch in their own font size; Inter’s zero glyph made the previous 72ch cap wider than 80 average characters. Applicability now lives in Scope. The unanswered example is a reset local state; typing shows unsaved changes without pretending a network save occurred. Other domain panels contain navigation placeholders, not a complete questionnaire.

review-queue.html: six real interim candidates form a compact unbordered list. Pending decisions come first; Order also offers evidence issues, risk and control order. Evidence sorting is a representative priority based on the reviewed missing exercise, removal and training support. Plain counts read 3 pending, 3 decided. Titles take at most two lines; control/name and outcome/risk each take one. Decided items are quieter. Outcome and risk join the finding heading. The sticky decision bar stays attached. Gap, impact, a strong recommendation, Why this recommendation and one provenance narrative follow. No interviews are invented. Local decision previews do not persist.

gaps.html (third pass, 13 Oct 2026; replaces conclusions.html): Review is now Queue and Gaps. 32 real ISO conclusions sit in a six-column register that opens on the 11 with a gap; All controls shows the rest. A row opens the remediation block and a four-step account of how the conclusion was reached, built from the demo app's workpaper and findings pages (`tools/extract_workpaper.py`, GET only, stored in workpaper.json). Three gaps have a real remediation record; the other eight show an unassigned record marked illustrative, because today the record is created by hand. The client note is omitted where it only repeats the reasoning. Final conclusions omit review mechanics. Missing fields are stated honestly; this is a subset of the 93 source controls.

rfi.html: 40 real request artifacts are collapsed to one-line rows: title, requirement, state, mapped evidence and action. Chevron expansion shows what to send as document names only (third pass): the controls each document supports appear when Show controls supported is pressed, and What good looks like renders only when it adds to the title. The Example slot is removed. The document list is still split mechanically from one stored paragraph on closing brackets, so some names split wrongly until the content track supplies structured items. Column headers sort, defaulting to title ascending. The two illustrative draft items begin under In this RFI with no add control. Only the other 38 items are candidates. Adding moves an item into that group once and removes its add control. The backend must reconcile requested, issued and received identity; only Not requested and In draft RFI are demonstrated because the source has no verified issued/received state for these rows. Long titles use ellipsis, with the full title in the expansion and title attribute. Versions and client links are empty-state local panels.

report.html: Board summary and Auditor detail are a top-right two-option toggle, separate from Section. Board opens with written engagement context, posture and a weakest-to-strongest domain table with score and risk counts. It then shows the gaps with impact, risk, recommendation and logic in two columns (third pass: two high-risk gaps per domain open, the rest behind Show N more, which brings the board view from 5,930px to 3,406px at 1440); low gaps remain in Auditor detail. The detailed view holds all 93 controls and domain/outcome/risk filters. Scores stay separate by framework. The board height target is about three 1440 screens; 25 open findings may exceed it, and no new rendered height is claimed. Primary deliverables remain visible. Executive prose and posture are illustrative, not accepted report text.

scope-applicability.html: the Scope stage is active. Controls that do not apply shows two plausible exclusions, marked illustrative, with a reason each. A picker asks only for a new exclusion and its reason. All remaining controls use the standard applicability justification shown once. No per-applicable-control justification boxes appear. Neither exclusion is claimed as stored in the real Veldhara assessment.

review-queue-sidebar.html: Option B uses identical queue content and behavior, but replaces Section with nested assessment links beneath Engagements. Queue has aria-current. The horizontal stage bar stays. Option B is recommended for visible destinations and one-click frequent switching; the choice is pending Saqlain. Option A remains on the five original screens and Scope for comparison.

## Source and state limits

Existing GET responses from assessments d491ee73-0925-43bd-8cb2-3b5fff2cc8ac and 506d1f04-9c19-44e4-9fdd-fa286f2b4eb6 supply the content in source-data.json. The source assessment contains DPDPA and ISO; questionnaire/report demonstrate the ISO view, while multi-framework UCC grouping stays specified. No new GET was necessary for this fix pass. The supplied screenshots and measurements.json record the pre-fix host captures at 1440 and 1280; they have not been replaced with invented evidence. This pass launches no browser or server. Host QA must remeasure height, horizontal overflow, full prose lines, font sizes, focus order and sticky decisions. Static CSS bounds and interaction fixtures cannot prove rendered geometry. Autosave, review blockers/conflicts and inclusion identity remain implementation dependencies.

## Every illustrative element

Each row identifies a screen and exact HTML id carrying data-illustrative=true. Option B repeats Option A dependencies without changing their IDs. Paired backend/content dependencies remain explicit.

| Screen | Element ID | Classification | Dependency |
| --- | --- | --- | --- |
| questionnaire.html | q1-why | Content | Static per-control why_asked field |
| questionnaire.html | q1-hint | Content | Static per-control client_prompt_hint field |
| questionnaire.html | q2-why | Content | Static per-control why_asked field |
| questionnaire.html | q2-hint | Content | Static per-control client_prompt_hint field |
| scope-applicability.html | soa-standard | Content | Authored standard justification plus Backend default applicability source marker |
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
| gaps.html | conclusion-title-0 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-1 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-2 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-3 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-4 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-5 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-6 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-7 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-8 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-9 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-10 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-11 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-12 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-13 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-14 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-15 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-16 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-17 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-18 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-19 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-20 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-21 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-22 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-23 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-24 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-25 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-26 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-27 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-28 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-29 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-30 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| gaps.html | conclusion-title-31 | Backend | Reviewed gap_title; title uses real gap text but field is absent |
| rfi.html | rfi-included-0 | Backend | Illustrative inclusion state; stable cross-source request identity/state contract, not live receipt or issuance |
| rfi.html | rfi-included-1 | Backend | Illustrative inclusion state; stable cross-source request identity/state contract, not live receipt or issuance |
| report.html | report-executive | Content | Accepted per-assessment executive narrative, exposed by existing narrative/board read model |
| report.html | report-organizational-impact-1 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-1 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
| report.html | report-organizational-impact-3 | Content | Board impact text; Backend per-conclusion impact slot |
| report.html | report-organizational-reason-3 | Content | Recommendation reasoning generated per assessment; Backend explicit reason slot |
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
| gaps.html | conclusion-impact-0 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-0 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-0 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-1 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-2 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-3 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-impact-4 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-4 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-4 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-impact-5 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-5 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-5 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-6 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-7 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-8 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-9 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-impact-10 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-10 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-10 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-impact-11 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-11 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-11 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-impact-12 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-12 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-12 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-13 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-14 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-15 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-impact-16 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-16 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-16 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-impact-17 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-17 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-17 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-impact-18 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-18 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-18 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-19 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-20 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-21 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-22 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-23 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-24 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-25 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-impact-26 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-26 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-26 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-impact-27 | Content | Assessment-specific impact narrative; Backend impact_statement slot |
| gaps.html | conclusion-reason-27 | Content | Recommendation logic from source action; Backend recommendation_reason slot |
| gaps.html | conclusion-provenance-27 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-28 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-29 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-30 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | conclusion-provenance-31 | Content | Reviewed provenance narrative with method/interview source records |
| gaps.html | gap-remediation-0 | Backend | Remediation record created when a gap is approved (Track B); today a finding is created by hand, so this gap has no owner, target or status on record |
| gaps.html | gap-remediation-4 | Backend | Remediation record created when a gap is approved (Track B); today a finding is created by hand, so this gap has no owner, target or status on record |
| gaps.html | gap-remediation-5 | Backend | Remediation record created when a gap is approved (Track B); today a finding is created by hand, so this gap has no owner, target or status on record |
| gaps.html | gap-remediation-10 | Backend | Remediation record created when a gap is approved (Track B); today a finding is created by hand, so this gap has no owner, target or status on record |
| gaps.html | gap-remediation-17 | Backend | Remediation record created when a gap is approved (Track B); today a finding is created by hand, so this gap has no owner, target or status on record |
| gaps.html | gap-remediation-18 | Backend | Remediation record created when a gap is approved (Track B); today a finding is created by hand, so this gap has no owner, target or status on record |
| gaps.html | gap-remediation-26 | Backend | Remediation record created when a gap is approved (Track B); today a finding is created by hand, so this gap has no owner, target or status on record |
| gaps.html | gap-remediation-27 | Backend | Remediation record created when a gap is approved (Track B); today a finding is created by hand, so this gap has no owner, target or status on record |
| review-queue-sidebar.html | queue-title-0 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue-sidebar.html | finding-title-0 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue-sidebar.html | finding-impact-0 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue-sidebar.html | finding-reason-0 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue-sidebar.html | finding-provenance-0 | Content | Reviewed provenance narrative with Backend method/interview source records |
| review-queue-sidebar.html | queue-title-1 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue-sidebar.html | finding-title-1 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue-sidebar.html | finding-impact-1 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue-sidebar.html | finding-reason-1 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue-sidebar.html | finding-provenance-1 | Content | Reviewed provenance narrative with Backend method/interview source records |
| review-queue-sidebar.html | queue-title-2 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue-sidebar.html | finding-title-2 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue-sidebar.html | finding-impact-2 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue-sidebar.html | finding-reason-2 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue-sidebar.html | finding-provenance-2 | Content | Reviewed provenance narrative with Backend method/interview source records |
| review-queue-sidebar.html | queue-title-3 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue-sidebar.html | finding-title-3 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue-sidebar.html | finding-impact-3 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue-sidebar.html | finding-reason-3 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue-sidebar.html | finding-provenance-3 | Content | Reviewed provenance narrative with Backend method/interview source records |
| review-queue-sidebar.html | queue-title-4 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue-sidebar.html | finding-title-4 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue-sidebar.html | finding-impact-4 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue-sidebar.html | finding-reason-4 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue-sidebar.html | finding-provenance-4 | Content | Reviewed provenance narrative with Backend method/interview source records |
| review-queue-sidebar.html | queue-title-5 | Backend | Reviewed Conclusion.gap_title field; text is illustrative Content per assessment |
| review-queue-sidebar.html | finding-title-5 | Backend | Conclusion.gap_title with reviewed per-assessment Content |
| review-queue-sidebar.html | finding-impact-5 | Backend | Conclusion.impact_statement; generated per assessment Content |
| review-queue-sidebar.html | finding-reason-5 | Content | Generated recommendation reasoning; Backend recommendation_reason slot |
| review-queue-sidebar.html | finding-provenance-5 | Content | Reviewed provenance narrative with Backend method/interview source records |
| scope-applicability.html | soa-exclusion-outsourcing | Content | Illustrative Veldhara scope exclusion; Backend stores exclusion reason/version; Content authored by scope reviewer |
| scope-applicability.html | soa-exclusion-coding | Content | Illustrative Veldhara scope exclusion; Backend stores exclusion reason/version; Content authored by scope reviewer |
| report.html | report-posture | Content | Assessment-specific board posture synthesis from deterministic domain scores and gaps; Backend accepted report read model |
