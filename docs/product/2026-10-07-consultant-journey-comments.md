# Consultant journey: owner comments (verbatim export, 2026-10-07)

Source: `2026-10-06-consultant-journey-flow.html`. Marks are the owner's; quoted text is the owner's words, lightly unedited.

## Principles
- **[CHANGE]** One primary action per screen. Owner: a more lenient version is that at any point the user should not have to guess what to do next.
- **[OK]** A screen never asks something we won't use. "No need to collect information we won't be using."
- **[OK]** Framework-specific wording only when that framework is in the assessment.
- **[OK]** Always see where you are and who the ball is with. "This is my home screen, my central dashboard for tracking all engagements at once."
- **[OK]** No hidden gates.
- **[OK]** Everything the consultant enters is editable later.

## 0. Engagement setup
- **[CHANGE]** All six frameworks selectable: "not yet. Let's perfect the first three (DPDPA, ISO 27001, NIST CSF) and then strategically add more standards."
- **[OK]** After 'Start assessment' land on Scoping. Rationale: scope of the engagement comes first (e.g. a company may certify ISMS for one room in one building; we need to know which systems and domains are in scope). Scoping answers drive a standard RFI. The RFI collects information that makes the questionnaire easier: evidence showing how controls are established and defined in the org, which the consultant then probes.
- **[no mark]** Add/remove frameworks later with a warning: "if it's not too complicated, but not my priority."
- **[OK]** Re-assessment with comparison to the last one is first-class.

## 1. Scoping
All rows OK: one flow not two wizards; ISO-only has ISMS scoping and zero privacy; multi-framework shows shared facts once; remediation budget removed (timeline and driver stay in one short block); confirm/reject "likely not applicable" for every framework; human labels; scope editable later and the RFI shows what changed.

**Notes:**
- The scoping questions are not good enough, and the owner is unsure what influence they currently have on the rest of the flow.
- Owner will share sample scope questions and RFIs sent to clients before engagements at KPMG, to optimise ours.
- Presentation is overbearing: the RFI list and out-of-scope controls look like one big blob of text. Signal over noise; users know cyber.
- Close to zero feedback on completing any part of the process. A user should be absolutely sure about what they have already done. (Owner invited clarifying questions.)

## 2. RFI
All rows OK: RFI is a visible stage; button says 'Send RFI' until sent, then 'Upload evidence'; a document requested under two frameworks appears once; items can be marked received / insufficient / waived and later steps use that status.

**Notes:**
- Overview tab should direct the user after an engagement is created: fill the scope so an RFI can be generated and the initial request sent. This is the real step order: define scope, then send an RFI.
- The evidence list (e.g. policy definition, risk assessment and treatment) is hard to read and looks like useless information. It should say clearly what each evidence item is and why it is requested.
- On the post-scope page it is unclear what to do next. The 'Prepare RFI' button must be highlighted, especially the first time. PDF and Docs download buttons move below it.
- The user should be able to select which items go into the first RFI, and see the tool's suggestion and agree or not.
- 'Request' only appears when entering the request section of the Evidence tab. Once evidence is assigned and linked, the next visit to Evidence should show what has been received, what is pending, and an option to request additional evidence.

## 3. Evidence in + desk review
All rows OK (Excel/CSV, images and scanned PDFs, dates vs assessment period with plain 'stale', one-click re-map, design findings separate).

## 4. Questionnaire
All rows OK (opens straight after desk review; source + quote on pre-fills; separate design and operating fields; consultant comment per question).

**Notes:**
- NEW FEATURE: consultant pastes meeting notes / MoMs from domain-owner discussions and the questionnaire auto-fills from them.
- Layout is bad: side nav and domain picker eat space and squeeze questions and answers to the left. Make questions the highlight; allow hiding the nav/picker or show them better.

## 5. Follow-ups / 6. Analysis
Rows OK, but the owner has not tested these. Layout and spacing opinions must be respected. Needs dummy filled-in data to judge.

## 7. Report
All rows OK.

## Open decisions
- **A.** Yes, split design vs operating effectiveness in the data model. "Not too difficult to determine which pertains to which, but don't over-complicate."
- **B.** Follow-ups stay inline, as now.
- **C.** Do not add GDPR, HIPAA, PCI-DSS now. The RFI points are in the RFI notes.
- **D.** Yes, scoping always precedes RFI.
- **E.** Real engagement flow, in the owner's words:
  1. On getting a request, send scope questions to the org (headcount, cloud, etc., depending on the engagement).
  2. After scope, ask for design-level documents (policies, procedures), plus some known operational evidence such as access review lists.
  3. Read them to understand which controls the company has defined and compare documentation against the control being assessed. This is the first anchor for judging domain owners' responses.
  4. Learn the specifics (e.g. access review uses tool X, requests raised in ServiceNow, defined workflow).
  5. Set up discussions with individual domain owners using the framework and questionnaire. Answers lead to follow-up questions, or additional evidence, shown in the session or sent as files.
  6. After all domain-owner discussions, produce the final report.
  7. A board meeting happens in between, and status-update decks are needed. Later, not now.

## Anything else
- Text hierarchy is poor across the app; the design effort went into looks, not hierarchy. Evidence step is the prime example: show what the item is, why the tool suggests it, and let the user select what goes into the first RFI. The person will do a lot of reading, so make it as light as possible.
- Gradient bug: on a small screen the full gradient shows; on a taller or larger screen the page looks different, like two colours.
