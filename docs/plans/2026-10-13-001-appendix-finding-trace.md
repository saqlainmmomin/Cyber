# Appendix: finding trace

Companion to `2026-10-13-001-single-track-implementation-plan.md`. Every finding from the content audit and the work package that fixes it. Status: Covered, Port (fixed by the screen port in Phase 7), Parked (framework out of MVP), Phase 8 (after the migration), No change.

| Finding | Sev | Title | Work package | Status |
|---|---|---|---|---|
| F-A1 | P0 | Every unit of work is titled by the control name, never the gap | 3.5, 4.2, 7.6 | Covered |
| F-A2 | P0 | No consequence/impact, no cause, and risk is a bare pill with no basis | 3.5, 4.2, 4.4, 7.6 | Covered |
| F-A3 | P0 | Recommendation is a small unreasoned box; in the v2 path it is empty | 3.5, 4.2, 4.4, 7.6 | Covered |
| F-A4 | P0 | The same sentence appears up to three times on one card; "Evidence" and "Evidence on this control" show the same file | 3.5, 6.2, 7.6 | Covered |
| F-A5 | P0 | The conclusion data passes unchanged through five screens, so each screen repeats rather than re-shapes it | 3.5, 6.2, 7.6 | Covered |
| F-A6 | P0 | The questionnaire question carries no control reference or requirement text, and the guidance field has two jobs | 3.1, 3.2, 3.3, 5.1 | Covered |
| F-A7 | P0 | Section/domain titles come from a single DPDPA-flavored map; the section header repeats itself | 3.1, 5.1 | Covered |
| F-A8 | P1 | Engine tier words leak into the reader's UI and are not explained | 7.x port | Port |
| F-A9 | P1 | One word, two dimensions: control criticality and finding risk share "Critical/High" | 1.1 | Covered |
| F-A10 | P1 | "Finding" means three things; "gap" and "missing provision" are one thing with two names | 1.1 | Covered |
| F-A11 | P1 | A control has at least five reference forms, and some are hard-coded in templates | 1.1 | Covered |
| F-A12 | P1 | Five outcome vocabularies; Relevance has two label sets | 1.1 | Covered |
| F-A13 | P1 | Developer/engine text is shown to the consultant | 2.7 (exports), 7.x port (screens) | Covered |
| F-A14 | P1 | The workpaper is a system log, not an audit working paper | 3.5 (library test text becomes the procedure), 6.2 (order), 7.6 | Covered |
| F-A15 | P1 | Finding/action status vocabulary is inconsistent | 1.1 | Covered |
| F-A16 | P1 | Decisions lack a stated meaning and "Reject" needs a reason | 2.8, 7.6 | Covered |
| F-A17 | P1 | Conclusions page is not shaped as a final sheet | 6.2, 7.6 | Covered |
| F-A18 | P1 | DPDPA-only wording appears in the shared context wizard | 5.5 (context wizard and its prompts removed) | Covered |
| F-A19 | P1 | Pre-filled AI answers are confirmed by the section save, with confidence stated but not the source | 5.1 (explicit confirm and drafts endpoint), 7.4 | Covered |
| F-A20 | P1 | Review card omits "what the client said" for v1 conclusions | 3.6 | Covered |
| F-A21 | P1 | Soa: blank by default, mixed statuses, wrong audience sentence | 5.4, 7.4 | Covered |
| F-A22 | P1 | Desk review is named four ways and its output is uninterpreted | 1.1 | Covered |
| F-A23 | P1 | Evidence screens do not name what the reader needs | 7.x port | Port |
| F-A24 | P1 | The risk/priority fields on the finding form use unrelated labels | 1.1 | Covered |
| F-A25 | P1 | Dead/retired surfaces still carry a competing vocabulary | 7.x port | Port |
| F-A26 | P2 | Microcopy | 7.x port | Port |
| F-A27 | P2 | Breadcrumbs and repeated headers | 7.x port | Port |
| F-A28 | P2 | Positive result copy | 4.2 | Covered |
| F-A29 | P2 | Case and spelling | 1.1 | Covered |
| F-A30 | P2 | Findings page interaction text | 5.6, 7.6 | Covered |
| F-B1 | P0 | The report's "Executive summary" is a string of counts, not an executive summary | 4.3 | Covered |
| F-B2 | P0 | No gap on the report shows impact, risk basis, cause or recommendation | 3.5, 4.2, 7.5 | Covered |
| F-B3 | P0 | Gaps are not grouped by domain, weakest first, and the list is the control register, not findings | 6.2, 4.3, 7.5 | Covered |
| F-B4 | P0 | Overall rating labels are misleading and reuse the outcome vocabulary | 2.3 | Covered |
| F-B5 | P0 | No board view vs auditor view; the board content is not on the report | 6.2, 4.3, 7.5 | Covered |
| F-B6 | P0 | The client upload page cannot tell the client what to send, why, or by when | 5.3 | Covered |
| F-B7 | P0 | The "what to send" and "why" text on RFI items is assessor voice with statute and control codes | 5.3 | Covered |
| F-B8 | P1 | Two incompatible meanings of "finding" on adjacent screens | 1.1 | Covered |
| F-B9 | P1 | "Business impact" shows counts and a statutory maximum penalty, not business impact | 2.4 | Covered |
| F-B10 | P1 | Six empty cards repeat the finding titles a third time | 7.x port | Port |
| F-B11 | P1 | Outcome and risk are conflated; risk is shown on rows that have no gap | 1.1 | Covered |
| F-B12 | P1 | Same text repeated under multiple headings on the report screen | 7.x port | Port |
| F-B13 | P1 | The report summary and the Narrative are two unrelated executive texts; narrative rules forbid posture; reference IDs differ | 4.3 | Covered |
| F-B14 | P1 | Board inputs duplicates the recommendation field and leaves it blank | 4.4, 3.5, 7.7 | Covered |
| F-B15 | P1 | RFI items page: contradictory and mislabeled helper text | 5.3 | Covered |
| F-B16 | P1 | "What to send" groups unrelated artifacts under the item title | 5.3 | Covered |
| F-B17 | P1 | Client-visible request text carries control codes and raw IDs | 5.3 | Covered |
| F-B18 | P1 | "By when" has two answers and the client page shows neither as a deadline | 5.3 (due date, link expiry default, closed-link message) | Covered |
| F-B19 | P1 | Client upload page errors and states | 5.3 | Covered |
| F-B20 | P1 | Comparison overstates change when scope differs | 2.4 | Covered |
| F-B21 | P1 | Workflow vocabulary: release, approve, issue, accept, generate | 1.1 | Covered |
| F-B22 | P2 | Remediation tracker naming and structure | 7.x port | Port |
| F-B23 | P2 | Requests and Reports lists | 7.x port | Port |
| F-B24 | P2 | The signer field has five names | 1.1 | Covered |
| F-B25 | P2 | Analysis complete screen | 7.x port | Port |
| F-B26 | P2 | Misc microcopy | 5.3 (superseded RFI state), 7.x port | Covered |
| F-C1 | P0 | The same engagement gets a different stage on every screen | 1.2 (rollup, display name, home table query) | Covered |
| F-C2 | P0 | "Progress" percentage is not progress through the stages shown beside it | 1.2 (rollup, display name, home table query) | Covered |
| F-C3 | P0 | "Released" and "Issued" describe the same report on one screen and contradict each other | 1.2 (rollup, display name, home table query) | Covered |
| F-C4 | P0 | Home table silently shows 3 rows, one per client, and mislabels its count column | 1.2 (rollup, display name, home table query) | Covered |
| F-C5 | P1 | Breadcrumb says "Home" on ten non-home screens | 7.1 (shell), 7.x port | Port |
| F-C6 | P1 | Client-name crumb links to the dashboard; "Assessments" crumb names a place that does not exist | 7.1 (shell), 7.x port | Port |
| F-C7 | P1 | Unnamed assessments are titled with the client name, so one string appears up to four times and rows cannot be told apart | 1.2 (rollup, display name, home table query) | Covered |
| F-C8 | P1 | Assessment h1 never changes between tabs; the stepper repeats the tab labels | 7.1 (shell), 7.x port | Port |
| F-C9 | P1 | Overview repeats the framework name three times and does not state the result | 7.1 (shell), 7.x port | Port |
| F-C10 | P1 | Shell brand and affordances are wrong or inert | 7.1 (shell), 7.x port | Port |
| F-C11 | P1 | Stage and status vocabulary: five parallel sets for one lifecycle | 1.1 | Covered |
| F-C12 | P1 | Three names for the document-reading step and two for the analysis step | 1.1 | Covered |
| F-C13 | P1 | Report lifecycle verbs and pills are inconsistent | 1.1 | Covered |
| F-C14 | P1 | Purge page exposes database table names and counts the same thing twice | 7.1 (shell), 7.x port | Port |
| F-C15 | P1 | Implementation instructions and internals shown as UI copy | 7.1 (shell), 7.x port | Port |
| F-C16 | P1 | Errors: raw JSON, wrong 404 text, generic failure message | 7.1 (shell), 7.x port | Port |
| F-C17 | P1 | Raw and mismatched label maps show internal values | 1.1 | Covered |
| F-C18 | P1 | Framework names: four spellings and a rendering glitch | 1.1 | Covered |
| F-C19 | P1 | New engagement form: duplicated labels, tripled errors, hidden primary button | 7.1 (shell), 7.x port | Port |
| F-C20 | P1 | Home attention rows: verb mismatch and no object | 1.2 (rollup, display name, home table query) | Covered |
| F-C21 | P1 | Settings copy misdescribes what it does | 7.1 (shell), 7.x port | Port |
| F-C22 | P1 | Same nav word at three scopes | 7.1 (shell), 7.x port | Port |
| F-C23 | P2 | `<title>` format | 7.1 (shell), 7.x port | Port |
| F-C24 | P2 | Loading and error states are previews, and the error copy blames the connection | 7.1 (shell), 7.x port | Port |
| F-C25 | P2 | Duplicate feedback and repeated phrases | 7.1 (shell), 7.x port | Port |
| F-C26 | P2 | Empty states without the one next step | 7.1 (shell), 7.x port | Port |
| F-C27 | P2 | Small content defects | 7.1 (shell), 7.x port | Port |
| F-D1 | P0 | 77% of control questions are one generated template, and the "guidance" repeats the requirement | 3.1, 3.2, 3.3, 5.1 | Covered |
| F-D2 | P0 | Questionnaire section labels for ISO, NIST, PCI and HIPAA are privacy headings or "Other Controls" | 3.1, 5.1 | Covered |
| F-D3 | P0 | In multi-framework assessments the 412 control questions are bypassed, and one question can stand in for up to 24 controls, some of which it does not test | 5.1, 5.2 | Covered |
| F-D4 | P0 | Privacy and DPDPA-flavored wording is hard-wired into security questions and shown to non-privacy assessments | 3.1, 3.2, 3.3, 5.5 | Covered |
| F-D5 | P1 | Cluster "follow-ups" are statements about what each framework expects, not questions | 3.1, 3.2, 3.3 (mapping strength) | Covered |
| F-D6 | P1 | GDPR questions are open-form and compound but are answered on a five-value maturity scale | Parked (GDPR) | Parked |
| F-D7 | P1 | DPDPA questions are good on substance but 5 are compound, and the guidance blends citation, evidence and hint into one paragraph | 3.2 (and your verification, D9) | Covered |
| F-D8 | P1 | ISO 27001 content has Annex A only: no clauses 4 to 10 | 3.1 | Covered |
| F-D9 | P1 | ISO section names under the four themes are invented and several mislead | 3.1 | Covered |
| F-D10 | P1 | The three texts Saqlain asked for do not exist as separate fields | 3.1, 3.2, 3.3, 5.1 | Covered |
| F-D11 | P1 | Scope questions for GDPR, HIPAA and PCI have no effect, and GDPR/HIPAA/PCI produce no client document requests | 5.3 for ISO, NIST, DPDPA; GDPR, HIPAA, PCI parked | Partly parked |
| F-D12 | P1 | DPDPA domain structure is half borrowed from the Act, half invented, and the "chapter" labels look wrong | 3.2 (and your verification, D9) | Covered |
| F-D13 | P1 | Stale or inconsistent identifiers and citations | 2.2 (citations), 3.2 (screening ids), PCI parked | Partly parked |
| F-D14 | P2 | Industry question bank covers one vertical and is DPDPA-only | Phase 8 (decide), industry bank | Phase 8 |
| F-D15 | P2 | "Root cause clusters" are remediation workstreams | 1.4 (2c), 4.4 | Covered |
| F-D16 | P2 | Vocabulary and spelling drift (section 6 has the full list) | 1.1 | Covered |
| F-D17 | P2 | Criticality is uneven across frameworks and cluster values are ignored | 3.1, 3.2, 3.3 (importance re-baselined) | Covered |
| F-D18 | P2 | Description voice follows the source standard and may exceed the D4 reference-only rule | 3.1 | Covered |
| F-D19 | P2 | Cluster naming defects | 5.1, 5.2 | Covered |
| F-E1 | P0 | No field exists for the finding's headline, impact, or recommendation reasoning | 4.2, 3.5 | Covered |
| F-E2 | P0 | "Rationale" is not a rationale; condition is smeared across two overlapping fields shown stacked | 4.2, 3.5 | Covered |
| F-E3 | P0 | The executive summary a reader sees is a string of counts; the model's prose is discarded | 4.3 | Covered |
| F-E4 | P0 | The board narrative prompt structurally cannot produce the exec-summary structure | 4.3 | Covered |
| F-E5 | P0 | Recommendation is a primary deliverable but is a 1-3 sentence blob with no owner, reasoning or priority that survives, and it is stored in three unsynchronized places | 4.4, 3.5 | Covered |
| F-E6 | P1 | Provenance cannot be expressed; evidence is a quote plus character offsets | 3.6, 4.2 (no-quote sentinel becomes null); interview sources Phase 8 | Covered |
| F-E7 | P1 | The DPDPA judge prompt tells the model to assert non-compliance on silence; product semantics say the opposite | 4.2 | Covered |
| F-E8 | P1 | Free-text fields are unconstrained in shape and likely restate the control | 4.2, 3.5 | Covered |
| F-E9 | P1 | Risk/impact is one enum with no basis; v1 and v2 compute it differently | 1.1, 4.2 | Covered |
| F-E10 | P1 | Cross-framework synthesis is asked for themes without being given gap content, and most of its output is discarded | 4.5 (E11 note: changing the OCR prompt stales read fingerprints, a re-read cost in Phase 8) | Covered |
| F-E11 | P1 | AI inference is stored as document text (vision OCR) and desk-review `content` duplicates `source_quote` | 4.5 (E11 note: changing the OCR prompt stales read fingerprints, a re-read cost in Phase 8) | Covered |
| F-E12 | P1 | Outcome label rendering is inconsistent and "not assessed" means three things | 1.1, 4.2 | Covered |
| F-E13 | P1 | Out-of-scope conclusions keep model gap/risk/remediation text | 2.5 | Covered |
| F-E14 | P1 | Shared prompts bake in DPDPA wording | 1.4 (2b, follow-up engine), 5.5 (context prompts removed) | Covered |
| F-E15 | P2 | Shared prompt text diverges between DPDPA and the other five frameworks | 4.2, 3.5 | Covered |
| F-E16 | P2 | Controlled vocabulary is partly free text and partly slugified free text | 1.1, 4.2 | Covered |
| F-E17 | P2 | Pre-fill notes are an evidence dump fed back into the judge | 4.5 (E11 note: changing the OCR prompt stales read fingerprints, a re-read cost in Phase 8) | Covered |
| F-E18 | P2 | v2 (parked) shapes, note only | No change: v2 stays parked and does not get the new fields | No change |
| F-F1 | P0 | The issued board report carries a hard-coded "DRAFT UNTIL ISSUED" marker | 2.1 | Covered |
| F-F2 | P0 | Client-facing RFI text quotes the wrong statutory sections | 2.2 | Covered |
| F-F3 | P0 | The executive summary can ship empty or filled with a disclaimer | 2.1 | Covered |
| F-F4 | P1 | The per-gap block is a 3C, not a 5C | 3.5, 4.2, 7.5 | Covered |
| F-F5 | P1 | 49 of 59 gaps are invisible in the report body | 4.3, 6.2 | Covered |
| F-F6 | P1 | One word, two dimensions (rubric: never reuse a word) | 2.3, 1.1 | Covered |
| F-F7 | P1 | Outcome and rating vocabulary differs between exports (and the app) | 1.1 | Covered |
| F-F8 | P1 | Four priority vocabularies, and priority is colored as severity | 1.1 | Covered |
| F-F9 | P1 | The executive summary is a dashboard with a good brief, not an engagement summary | 4.3, 6.2 | Covered |
| F-F10 | P1 | Gap report (D) mislabels counts as "Key Findings" and buries method | 2.6, 2.7 (conditional legend and subtitle), 1.4 (2c) | Covered |
| F-F11 | P1 | Not-applicable requirements print as full gap cards with a risk badge | 2.6, 2.7 (conditional legend and subtitle), 1.4 (2c) | Covered |
| F-F12 | P1 | Legacy findings and cards truncate silently and omit the "so what" | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |
| F-F13 | P1 | Workbook (C): thin where it should be rich, rich where it should be thin | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |
| F-F14 | P1 | PPTX is not slide-for-slide the PDF (and is the version a presenter edits) | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |
| F-F15 | P1 | Implementation words and raw IDs in the board text | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |
| F-F16 | P1 | Section badges and order are wrong | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |
| F-F17 | P1 | RFI (F): item text is written for the auditor, not the client | 5.3 | Covered |
| F-F18 | P1 | Evidence checklist (G) duplicates RFI with a weaker model | 2.6, 2.7 (conditional legend and subtitle), 1.4 (2c) | Covered |
| F-F19 | P1 | Workpaper (H): right skeleton, unfinished surface | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |
| F-F20 | P1 | Integrated engagement report (E) has no executive layer | 4.3, 6.2 | Covered |
| F-F21 | P1 | Framework-specific copy leaks and hard-coded numbers | 2.6, 2.7 (conditional legend and subtitle), 1.4 (2c) | Covered |
| F-F22 | P1 | Gaps with no `risk_level` become "Medium" | 2.5 | Covered |
| F-F23 | P1 | Narratives the consultant must accept are never shown | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |
| F-F24 | P1 | Placeholders ship in board tables | 2.1 | Covered |
| F-F25 | P2 | Rating thresholds are described three ways | 2.3, 1.1 | Covered |
| F-F26 | P2 | Ordering and tie-breaks | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |
| F-F27 | P2 | Edge cases in the generator | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |
| F-F28 | P2 | Hidden duplicate text | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |
| F-F29 | P2 | Spelling and register | 1.1 | Covered |
| F-F30 | P2 | Actions XLSX uses "Control code" | 2.7 (incl. board asks off the Definitions sheet, rationale and citation text restored) | Covered |

## Counts

- Covered: 119
- No change: 1
- Parked: 1
- Partly parked: 2
- Phase 8: 1
- Port: 26
