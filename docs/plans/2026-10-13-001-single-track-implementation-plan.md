# CyberAssess: single implementation track

Date: 13 Oct 2026. Revision 3, after two independent Opus reviews (revision 1 and revision 2). Implementation branches start from `origin/main`, not from the working branch, which lacks the merged E4 RFI code. Status: approved by Saqlain on 13 Oct 2026 with the answers recorded in section 13. Nothing here has been built.

This plan merges five streams of work into one ordered track: the Next.js migration (PR 141), the content audit (150 findings, decisions D1 to D11), the unified control framework (UCF, new), the document-reads plan (revision 5) and the flow rework plan (S3 to S9). Once approved it is the plan of record. Older plans stay as the detail behind each work package.

Companion file: `2026-10-13-001-appendix-finding-trace.md` maps every one of the 150 audit findings to a work package.

## 1. What is decided

These come from Saqlain's review of the content audit, the UI thread record on PR 141, and his messages of 13 Oct. They are inputs, not proposals.

| # | Decision | Source |
|---|---|---|
| 1 | Content is fixed first. Then the design system is written as one text. Then **mockups of the final screens are reviewed once**. Then screen code. | Content audit review; message 13 Oct (supersedes "no prototype round") |
| 2 | Migration and this content work come before any new feature. | Content audit review |
| 3 | Three frameworks in the MVP: ISO 27001, NIST CSF 2.0, DPDPA. GDPR, HIPAA and PCI DSS stay in the registry and are parked. | T6, T10 |
| 4 | Vocabularies: the audit's recommended lists. The score band is decided here (§5.3). | D1 |
| 5 | The gap title comes from the model. | D2 |
| 6 | ISO 27001 clauses 4 to 10 are added. | D3 |
| 7 | One UCF, built once. ISO 27001 (clauses and Annex A) is the base. NIST CSF is layered on it. DPDPA is layered on top with its own privacy slots. Common controls are represented once. A control only partly covered by ISO gets its own slot. Taking a framework out of scope must still work. | D4, T6 |
| 8 | The UCF follows the standard method (one master list, each source mapped to it once, single requirements, each control written once). It is static authored data. | D4, T6 |
| 9 | An issued file shows its real state. Issue is blocked while there are open items. | D5 |
| 10 | The legacy gap report PDF and the separate evidence checklist are retired. | D6 |
| 11 | Client vocabulary: documents, upload link, information request. | D7 |
| 12 | American spelling. | D8 |
| 13 | Legal verification of DPDPA ids and citations is Saqlain's. | D9 |
| 14 | A decided item leaves the review queue at once. Review is two screens: Queue and Gaps. Report and Applicability layouts are approved. | UI thread record |
| 15 | Finding anatomy: no timeline field. Risk basis can come later. Owner role is the domain owner and priority is a marked label. Both are included now because they come from the library and the existing rating at no extra generation cost. What is best to show with a finding is argued in §5.1, not dictated. | T2 comment |
| 16 | Work runs across three accounts with this session as orchestrator. No unnecessary tests. | Message 13 Oct |

## 2. Decisions this plan asks you to take

The review found that these were open and everything downstream depends on them. Each has a recommendation.

| # | Question | Recommendation |
|---|---|---|
| Q1 | **Unit of judgment.** Does the AI judge, and the reviewer approve, per unified control or per source requirement? And which "source requirement"? | The judged unit is the framework record as today (93 ISO controls plus clauses 4 to 10, 106 NIST subcategories, 41 DPDPA requirements). The split single asks (about 550 to 650) exist only as mapping atoms. Questions are asked per unified control. Each answer fans out to the records mapped to it and carries its unified control id, its question text and its mapping coverage. Each record has one primary unified control. Scoring stays per record. Rejected alternative: judge per unified control and derive record outcomes. It needs a new aggregation rule and breaks per-record reviewer approval. |
| Q2 | **Score band wording.** | Option 1, "Readiness" (§5.3). |
| Q3 | **DPDPA-only assessments.** UCF questions, or the legacy DPDPA question bank? **This reverses part of your 12 Oct ruling** to keep the DPDPA-only questionnaire. | UCF questions. The DPDPA layer reuses the curated DPDPA question text and guidance, which the audit rates good on substance. The legacy builder is retired only after a one-off parity script (question text and ids compared). The curated judge and screening key on legacy ids today, so both are kept and re-pointed through an id map, not rewritten. |
| Q4 | **Flow-plan items S3, S4, S5, S8, S9.** | Table in §4.3. Recommended: delete the context wizard and move the approved S3 scope changes into Phase 5, keep RFI inside Evidence (no seventh stage), move the rest to Phase 8. |
| Q5 | **Document reads stages 3 to 6 wait until after the migration.** The silent 20,000-word cap then stays for months. | Accept, with stage 1 making every cut visible. Or pull stages 3 to 6 forward and the build starts later. Your call. |
| Q6 | **Board and auditor field sets (D10).** | The audit's proposal (§5.1, per-reader views). |
| Q8 | **Questionnaire size.** Today ISO, NIST and DPDPA together give 48 questions (ISO alone 93, ISO and NIST 37). The first estimate of 150 to 250 unified controls would grow a three-framework questionnaire three to five times. | Keep the grain rule (one goal, one owner, one test) and the depth tiers (deep, standard, light, skip). **Saqlain's answer: expect fewer, because ISO and NIST overlap heavily.** No preset target. The count per framework subset is reported at each sign-off, and the number is an output of the mapping. |
| Q7 | **Workpaper order and the noun.** | Audit order: control, requirement, procedure, evidence examined, result, conclusion, sign-off. The record is a "gap" when the outcome is a gap. "Finding" is retired from the UI. |

## 3. Assumptions to confirm

| # | Assumption |
|---|---|
| A1 | "Track B PRs are merged" (D11) means Track B is folded into this plan. PR 141 is still open and none of B1 to B10 is built. |
| A2 | The DPDPA clean-up session never produced code (confirmed 13 Oct: "maybe it never ran"). Reads stage 2 is built from the approved plan in WP 1.4. |
| A3 | UI-only text defects in Jinja pages are not fixed in Jinja. The port fixes them. Backend, data, prompts, exports and Jinja label imports are fixed first. |
| A4 | Priority labels stay Immediate, Short-term, Medium-term, Long-term. They are an order label. No dates are stored on the gap. Target dates stay on remediation actions. |
| A5 | The UCF's static part (requirement, why asked, how to ask, expected evidence, test, baseline risk) is written once. Per-assessment text (gap title, condition, impact, recommendation) is generated and grounded in evidence. A static baseline risk statement does not replace a per-assessment impact. This is the answer to your "let me know if that is otherwise". |
| A6 | Evidence reads are not in the MVP critical path (Q5). |
| A7 | Backend work packages keep the live Jinja screens working with the smallest edit (an optional field, or a default such as reject reason "Not stated") until the port replaces them. These edits are allowed under E9. |
| A8 | Pinning a library version means an assessment records the version it used. Loading older versions is not built (Phase 8). Existing assessments keep the questions they were generated with. |

## 4. Where every stream goes

### §4.1 Streams

| Stream | What happens |
|---|---|
| PR 141 Track A (26 presentation PRs, P0 to P7) | Phase 7. Order unchanged. Each screen has its own start gate (section 8). |
| PR 141 Track B (B1 to B10) | Backend work packages in Phases 2 to 5. Mapping in §4.2. |
| PR 141 Track C (C1 to C6) | Phases 3 to 5. C1, C3, C5, C6 are the UCF and its wiring. C2, C4 are Phase 4. |
| Content audit (12 themes, 150 findings) | Appendix trace. Theme map in §9.1. |
| Reads stages 1 and 2 | WP 1.3 and 1.4. |
| Reads stages 3 to 6 | Phase 8 (Q5). |
| Flow rework | Table 4.3. |
| Evidence fixes A to C, E4 | Merged. E4 RFI content is reused in WP 5.3. |

### §4.2 Track B rows

| PR 141 row | Work package | Change |
|---|---|---|
| B1 drafts autosave | WP 5.1 (endpoint), 7.4 (port consumes it) | Backend in Phase 5, not in a port. Also the explicit "confirm pre-filled answers" act (F-A19). |
| B2 domain navigation | WP 5.1 | Rebuilt on the UCF domain tree. `domain_group` is not used (F-D2). |
| B3 why asked, how to ask | WP 3.1 to 3.3 (authored), 5.1 (served) | Fields come from the UCF, not `QuestionDef`. |
| B4 gap title, impact, reason | WP 3.5, 4.2 | Wider fields; see §5.1. |
| B5 interview records | Phase 8 | Provenance narrative first from citations and answer sources (WP 3.6). |
| B6 `FindingDetail` read model | WP 3.5 (service), P0 step 0e (DTO) | The DTO is built with the `/api/ui` conventions, not before. |
| B7 RFI identity | WP 5.3 | Unchanged. |
| B8 SoA exclusions | WP 5.4 | Unchanged. |
| B9 report JSON | WP 4.3, 7.5 | Executive summary from slots, not counts. |
| B10 approving a gap creates its record | WP 5.6 | Lands after the Phase 4 gate. Needs a decision record. |

### §4.3 Flow-plan items

Every item has a home or an explicit "dropped, you confirm".

| Flow item | Recommendation | Where |
|---|---|---|
| S3 delete context wizard, context-profiler call, `context_gathered`, questionnaire gate, `risk_tier` as input | Do. It removes DPDPA-worded prompts and a gate. | WP 5.5 |
| S3 scope question types single, multi, text; pending allowed (P13) | Do. Content of the Scope screen. | WP 5.5 |
| S3 note per scope question (P14) | Do. | WP 5.5 |
| S3 custom questions (P16), Common information block | Common block: do. Custom questions: Phase 8. | WP 5.5, Phase 8 |
| S3 XLSX export of scope for the client (P15) | Phase 8. | Phase 8 |
| S3 "likely not applicable" confirm or reject at scope time | Do, for ISO, NIST, DPDPA. | WP 5.5 |
| S3 every scope question shows what it drives | Do. | WP 5.5 |
| S3 period and cut-off move into Scope | Do. | WP 5.5 |
| S4 RFI as a stage between Scope and Evidence | **No seventh stage.** RFI stays under Evidence. Confirm. | Stepper stays six stages (WP 1.2) |
| S4 `rfi_item_status`, evidence to item link tables, "Send RFI", "Waiting on client", "scope changed after send" | Identity and included state: WP 5.3. Status tables and ball-with-whom: Phase 8. | WP 5.3, Phase 8 |
| S5 questionnaire layout | Presentation, in the port. | WP 7.4 |
| S5 side-by-side design and operating view | Dropped (Saqlain, 13 Oct). | |
| S6 F1 XLSX and OCR | Done. | |
| S6 F2 as-of date, F3 re-map evidence | Phase 8. | Phase 8 |
| S7 meeting notes to questionnaire | Phase 8. | Phase 8 |
| S8 merge Queue and Conclusions; workpaper as link | Done by the Queue and Gaps structure. | WP 7.6 |
| S8 auto-draft findings | WP 5.6. | WP 5.6 |
| S8 reviewer name default from Settings | Do. | WP 2.8 |
| S8 comparison matched by engagement; "Re-assess" entry | Matching: do. Entry: Phase 8. | WP 2.4, Phase 8 |
| S8 framework-conditional section refs | Reads 2c. | WP 1.4 |
| S9 scope wording and P17 seed mapping | Authored with the UCF scope content. | WP 3.1 to 3.3, 5.5 |

## 5. Design inputs settled here so the design system can be written

### §5.1 Finding anatomy and per-reader views

One record per source requirement result. The fields, from the 5 Cs of audit practice and your order (gap, status, risk and impact, recommendation with reasoning, where it came from):

| # | Field | Source | MVP | Note |
|---|---|---|---|---|
| 1 | Gap title | Model, editable | Yes, for a gap | 15 words or fewer. States the condition. |
| 2 | Condition | Model | Yes | What was found. Separate from outcome reasoning. |
| 3 | Criteria | UCF | Yes | Requirement statement and the reference per in-scope framework. Static. |
| 4 | Outcome | Reviewer | Yes | 5.2. |
| 5 | Risk rating | Model, editable | Yes | 5.2. |
| 6 | Impact | Model | Yes, for a gap | 1 to 2 sentences, grounded, no invented incidents. |
| 7 | Recommendation | Model | Yes, for a gap | Starts with a verb. |
| 8 | Why this recommendation | Model | Yes, for a gap | Links the action to the condition. |
| 9 | Owner role | UCF domain owner | Yes | A role from the library. Not the person on the remediation action. |
| 10 | Priority | Derived, editable | Yes | 5.2. |
| 11 | Provenance | Citations, answer source, document dates | Yes | What was reviewed, who answered, when. Passage one click away. |
| 12 | Cause category | Model | Stored, not shown | Used later. |
| 13 | Risk basis | Model | Stored if returned, not shown | Later. |
| 14 | Reject or edit reason | Reviewer | Required on reject | Stored. |

Dropped from the request to the model: timeline in weeks, effort.

**Per-reader views (D10 default).** The same record, different fields, never the same sentences twice.

| View | Fields, in order |
|---|---|
| Queue detail (reviewer deciding) | 1, 4, 5, 2, 6, 7, 8, 11, with the decision bar always visible. Criteria on demand. |
| Gap detail (auditor) | 1, 4, 5, 2, 3, 6, 7, 8, 9, 10, 11, remediation, workpaper trail |
| Report, auditor detail | Same as Gap detail, grouped by domain, weakest first |
| Report, board summary | Domain table, then for high and medium gaps only: 1, 6, 5, 7, 8. No control codes in the headline text. |
| Client RFI | None of these. Item fields in WP 5.3 only. |

### §5.2 Controlled vocabularies

| Dimension | Values |
|---|---|
| Outcome | Compliant, Partially compliant, Non-compliant, Insufficient evidence, Not applicable |
| Risk rating | Critical, High, Medium, Low |
| Priority | Immediate, Short-term, Medium-term, Long-term |
| Review state | Pending, Approved, Edited and approved, Rejected |
| Release state | Draft, Released, Issued |
| Remediation status | Open, In progress, Closed and awaiting verification, Verified |
| Control importance | Internal only. Never shown as "Critical". |
| Score band | 5.3 |

"Approved" belongs to the review state only. Release states never use it.

### §5.3 Score band

The band names a framework score. It must not reuse an outcome word and must not read as a certification claim.

| Option | Bands (thresholds stay 0, 40, 60, 80) | For | Against |
|---|---|---|---|
| 1 Readiness | Not ready, Partly ready, Mostly ready, Ready | Fits "readiness, not certification". No outcome word. | "Ready" needs its target on the line. |
| 2 Maturity | Initial, Developing, Established, Optimized | Familiar. | Collides with the M0 to M5 levels already in the model and with NIST tiers. |
| 3 Gap profile | No score word. Bands from gap counts by risk. | Ties to what a board cares about. | Changes scoring semantics. Two metrics. |

**Recommendation: Option 1.** Target phrase per framework: "Readiness for ISO 27001 certification", "Readiness against NIST CSF 2.0 target profile", "Readiness for DPDP Act obligations". The band always prints next to the count of critical and high gaps, so a high score with open critical gaps is never shown alone. Thresholds and scoring do not change. The rounding mismatch (79.6 printed as 80) is fixed by banding the unrounded score.

## 6. The track

Sizes are working sessions, my estimates, not measured. S is one or less, M is two to three, L is four to six, XL is more. Every "done" has one verify command, not a new test suite (§6C).

### Phase 0. Lock the inputs (docs only)

| WP | What | Depends on | Size |
|---|---|---|---|
| 0.1 | Your answers to section 2, assumptions in section 3, and the score band | This plan | S |
| 0.2 | Finding anatomy, per-reader views, vocabularies signed (5.1, 5.2) | 0.1 | S |
| 0.3 | UCF method, unit of judgment, layer rules, master domains, grain, questionnaire size reported per subset (Q8), field list (section 7) signed | 0.1 | S |
| 0.4 | Flow-plan item table (§4.3) confirmed | 0.1 | S |
| 0.5 | Spend cap for the three gates (WP 1.4, 4.6, and the gate after 5.1) and the one demo-company run for the mockup pack (6.3b). **Approved cap: $7 in total (Saqlain, 13 Oct).** Gates run on a reduced company set (2 to 3 companies, 2 stability runs, both settings), about $1.50 a gate. An expanded run comes later under a new approval. | You | S |
| 0.6 | Decision record DR-1. Records 0.1 to 0.5. Edits path rules 2 (lanes), 3 (click-through for backend PRs) and 5 (sequence). Absorbs migration decision E9. Amendable. | 0.1 to 0.5 | S |

### Phase 1. Foundations (code, first)

| WP | What | Depends on | Size | Done when |
|---|---|---|---|---|
| 1.1 | Vocabulary module. Outcome, risk, priority, review, release and remediation words, score band, display labels, `display_reference`, framework display names. Jinja templates import it (a data change, not a new screen). Spelling pass excludes prompts and prompt-embedded text; those change in WP 4.2. | 0.2 | M | Label guard passes except in files WP 7 will delete. Exports and API read from the module. |
| 1.2 | One stage and status rollup for engagement and assessment, used by every list, header and export. Stepper stays six stages. "Released" and "Issued" defined once. Unnamed assessment gets a distinct display name. The home engagements table query and its count column are fixed (it shows 3 rows, one per client; F-C4). | 0.4, 1.1 | M | Same engagement shows the same stage on every screen and export. |
| 1.3 | Reads stage 1: truthful cut (already approved, E7 and E8). | None | S | Manifest matches what prompts contained. |
| 1.4 | Reads stage 2, in its three parts: 2a explicit frameworks, 2b follow-up engine (narrow non-DPDPA prompt changes; the follow-up engine stays even when the context wizard goes), 2c upload categories, initiative text, section refs. Not yet built: the clean-up session never produced code. Lane O does the prompt part and runs the live gate on the reduced company set. | 1.3 | M | DPDPA goldens pass byte for byte at the point the gate runs, with WP 2.3 and 2.5 not yet merged. Gate passes. |

### Phase 2. Durable defects (backend and exports; no new screens)

Theme T1. Most are independent of the UCF and the port.

| WP | What | Findings | Depends on | Size |
|---|---|---|---|---|
| 2.1 | Issue-time state. An issued version renders its true state (Draft until issued, then Issued by X on date) and issue is blocked while open items exist. Open items, with data sources: executive narrative missing and not marked "none"; board decisions missing and not marked "No decision requested"; recommendation or risk cells that would print "Not recorded"; unowned actions once WP 4.4 supplies the owner role from the library. Already-issued files are not touched. New versions only. Needs a decision record on issue-time rendering. | F-F1, F-F3, F-F24 | 1.1 | L |
| 2.2 | Statute citations built from the framework pack `section_ref`. A regression check that cited sections equal the pack. The pack itself says "Section 8(4)-(6)" (`framework.py:434`), so correct the pack text after your verification (D9). | F-F2, F-D13 | None | S |
| 2.3 | Score band separated from outcome words; band uses the unrounded score; one description of thresholds in PDF, PPTX, XLSX. Moves a golden; re-record deliberately. | F-B4, F-F6, F-F25 | 1.1, 0.1 | S |
| 2.4 | Business impact and comparison tell the truth: penalty ceiling with its commencement date; same-scope change shown separately; comparison matched by engagement. | F-B9, F-B20 | 1.1 | S |
| 2.5 | Out-of-scope conclusions blank gap, risk and recommendation and store a reason. A missing risk rating is flagged, not defaulted to Medium. Moves a golden. | F-E13, F-F22 | 1.1 | S |
| 2.6 | Retire the gap report and evidence checklist as selectable exports. Keep stored `gap_report` snapshots downloadable and keep `generate_pdf` (the DPDPA golden renders it). Remove hard-coded DPDPA counts and the DPDPA paragraph from Scope and Limitations when DPDPA is out of scope. | F-F10, F-F11, F-F18, F-F21 | 1.1 | S |
| 2.7 | Export hygiene: placeholders, hidden duplicate text, truncation without ellipsis, workpaper dead link and UUID, raw ids and "Snapshot" wording in board text, limits and sign-off section order, accepted framework narratives made visible, PPTX and XLSX aligned to the PDF (board asks moved off the Definitions sheet, rationale and citation text back in, one decimal rule). The severity legend and the cover subtitle become framework-conditional. | F-F12 to F-F16, F-F19, F-F23, F-F26 to F-F30 | 1.1, 2.3 | M |
| 2.8 | Reject requires a stored reason (the Jinja Reject form sends "Not stated" until the port; A7); undo added to the API (reopen already exists); reviewer name defaults from Settings. | F-A16 | 1.1 | S |

### Phase 3. Unified control framework and data model

Lane T for 3.1 to 3.4. Sign-off per domain. Each part ends usable: ISO alone after 3.1, ISO and DPDPA after 3.2, all three after 3.3.

| WP | What | Depends on | Size | Done when |
|---|---|---|---|---|
| 3.1 | UCF part 1, ISO base: clauses 4 to 10 and Annex A 93, master domains, unified controls with the fields in §7.4, mappings, scope question content for ISO. Lane T owns the files it must touch here (framework definitions for ISO scope content). Source atomizing can start before 0.3 is signed; mapping waits for it. | 0.3 | XL | Signed by you per domain. ISO-only subset passes 3.4. |
| 3.2 | UCF part 2, DPDPA layer: 41 requirements split, overlap mapped to the base, privacy domains, curated question text reused, stale screening ids fixed (touches `app/dpdpa/` and screening; Lane T owns these files for this WP) | 3.1 | L | Signed. ISO and DPDPA subset passes 3.4. |
| 3.3 | UCF part 3, NIST layer: 106 subcategories split, mapped to the base, NIST-only slots | 3.1 | XL | Signed. All seven subsets pass 3.4. |
| 3.4 | UCF validation script (the checks in §7.6), a library version number, and `ucf_version` recorded on each assessment (A8: recorded, not a multi-version loader). Small model change and migration; Lane T owns them for this WP. | 3.1 | S | One script, run on load. |
| 3.5 | Finding anatomy storage and read model service: migration adding fields in §5.1; stop discarding priority and cause; the library's test text carried to the workpaper as "procedure" (F-A14); new tables added to `PURGE_ORDER` and the FK-order check; missing states for existing conclusions. | 0.2 | L | Existing conclusions render with explicit missing states. |
| 3.6 | Provenance narrative built deterministically from citations, answer source and document dates. | 3.5 | M | Present for every conclusion with a citation or answer. |

### Phase 4. Generation (prompts)

One decision record for the phase. It names which freezes it lifts: P6-5c, E6 Q1 and the N6 note, for the named output fields only, on both the registry path and the DPDPA curated path. The parked v2 path does not get the new fields. Phase 4 changes sit behind a setting (`finding_anatomy_mode`, off or on) so the gate is a same-commit comparison and rollback is a setting.

| WP | What | Depends on | Size |
|---|---|---|---|
| 4.1 | Decision record and the setting | 0.2, 3.5 | S |
| 4.2 | Judge output: gap title, condition, impact, recommendation, reason, cause. One shared status definition for all frameworks, including insufficient evidence (F-E7, F-E15). A questionnaire answer with no quote is null, not an ungrounded quote (F-E6). Strict validation: one retry, then the item is marked "needs attention" and counted, never defaulted. Compliant results get a positive conclusion sentence. DPDPA goldens re-recorded when the setting is switched on (4.7). Prompt-embedded spelling changes here. | 4.1 | L |
| 4.3 | Narrative and executive summary slots (context, scope, posture, key gaps, recommendations, decisions), each with its own grounding rule. Use the batched summary instead of discarding it. Integrated engagement report gets an executive layer. Unplanned gaps are rendered. | 4.2 | M |
| 4.4 | Remediation draft carries the reason and the domain owner role. Board inputs prefilled from it. | 4.2 | S |
| 4.5 | Cross-framework synthesis deleted or fed approved gaps. OCR commentary separated from citable text. Pre-fill basis stored as one line and passed to the judge with its answer source. | 4.2 | M |
| 4.6 | Same-commit gate, setting off versus on, on all validation companies, aggregate only: catch not lower, false positives not higher, stability not lower, cost reported. Runs on the question packs as they are today, **before WP 5.1 merges**. Held-out answer keys never read. Lane O runs it (it needs network and spends). | 4.2 to 4.5, 0.5 | M |
| 4.7 | Switch `finding_anatomy_mode` on by default after 4.6 passes. Goldens for both paths re-recorded in this PR. | 4.6 | S |

### Phase 5. Content wired into the product

| WP | What | Depends on | Size |
|---|---|---|---|
| 5.1 | Questionnaire builder reads the UCF. One question per unified control with why asked, how to ask and each in-scope framework's reference. **One shared fan-out function** (used by the judge prompt input, persistence, follow-ups and the completion gate) expands an answer to the framework records mapped to it and carries the unified control id, the question text and the mapping coverage, so the judge sees "answered via UC-x (partial: covers A, not B)". Each record has one primary unified control stored in place of `cluster_id`. The persistence check that today misses clustered responses (`routers/analysis.py:766-769`) is fixed. The drafts endpoint (B1) and the explicit confirm of pre-filled answers (F-A19) are built here. Cluster ids are replaced across the 28 files that use them. Existing multi-framework assessments are frozen read-only (default) or migrated; validation question packs are re-exported by someone other than the prompt author. Lane T, with an Opus review. | 3.4, 3.2, 3.3, 4.6, 1.1 | XL |
| 5.1g | Gate after 5.1, because judge input changed: an absolute floor against 4.6's "on" numbers, on the re-exported packs. Nothing in 5.2, 5.6, 5.7 or 6.3b starts before it passes. | 5.1, 0.5 | S |
| 5.2 | Scoring: cluster lookups removed. Per-requirement scoring is unchanged. `score()` and its cluster verdicts, which no app code calls, are deleted. Existing goldens re-recorded deliberately. | 5.1g | M |
| 5.3 | RFI from UCF expected evidence: one item per artifact in client words, a plain why, what good looks like, formats, one due date (owned here), item identity (B7). The client upload page gets the same fields snapshotted into the link scope. Control codes and auditor blanks removed from client documents. Link expiry defaults to the due date plus a grace period, and a closed link says why (F-B18). | 3.1, 1.1 | L |
| 5.4 | Statement of applicability: exclusions with reasons, standard justification for the rest, ISO only. Clauses 4 to 10 are never excludable. Applicability lists already stored on assessments are migrated for the new ids. | 3.1 | M |
| 5.5 | Scope content from §4.3: context wizard removed (its DPDPA-worded prompts go with it, F-A18), question types, pending answers, notes, common information, proposals confirmed at scope time, period and cut-off. | 0.4, 3.1 | L |
| 5.6 | Approving a gap creates its remediation record (B10). Backfill writes "Gap title not recorded" with the control name as a secondary line, never as the title. Decision record on new report versions and prior-period comparison. | 4.7 | M |
| 5.7 | Demo company (Veldhara) reseeded with cluster-free answers and the new fields. Needed for mockup content and every later capture. | 3.5, 4.7, 5.1g | M |

### Phase 6. Design system, mockups, plan of record

| WP | What | Depends on | Size |
|---|---|---|---|
| 6.1 | Design system and spec rewritten as one text. Amendments merged; vocabulary, anatomy and per-reader views applied; type roles; stepper. Migration step 0d becomes a check against this text, not a gallery sign-off. | 0.2 | M |
| 6.2 | Per-screen content spec: field list and order, labels from the vocabulary, empty and missing states, undo and reopen home, workpaper order. | 6.1, 3.5 | M |
| 6.3a | Batch 1 content pack: UCF sample for each domain and question text, a real RFI set, the client upload page fields. No generated gaps. | 3.1, 5.3 | S |
| 6.3b | Batch 2 content pack: real generated gaps from one run on the demo company, a real executive summary, a real RFI set. | 4.7, 5.1g, 5.7 | S |
| 6.4 | Mockups regenerated from the pack with the existing builder (`build_prototypes.py`, JSON driven). Screens: Questionnaire, Review queue, Gaps, RFI and request detail, Report (board summary and auditor detail), Scope and Applicability, Overview, client upload page. Batch 1 (Questionnaire, Scope, RFI and request detail, Applicability, Overview, client upload page) from 6.3a. Batch 2 (Queue, Gaps, Report) from 6.3b. Overview and the client upload page are new builds; the builder lives on `origin/codex/ui-audit` and the anatomy fields need template changes, not only JSON. Not mocked, because their layout was approved and only vocabulary changes: Home, Clients, Client, Engagements, New engagement, Engagement, Remediation, Integrated reports, Requests, AWS evidence, Purge, Settings, Evidence screens, Versions, Comparison, Narrative, Board inputs. You confirm this list in WP 0.1. | 6.2, 6.3a / 6.3b | L |
| 6.5 | **Your review of the mockups.** One round per batch. Your changes applied once. | 6.4 | S |
| 6.6 | Plan of record finalized: Track A order, PR counts, per-screen gates. Independent review. Runs after batch 1 is reviewed; batch 2 only gates the Review and Report ports. | 6.5 (batch 1) | S |

### Phase 7. Migration build (Track A, P0 to P7)

Nothing starts before the first mockup batch is approved. Order and PR counts as in the migration plan, with the verification in §6C overriding that plan's section 8. Differences:

| WP | Note | Start gate |
|---|---|---|
| 7.1 P0 foundations | Includes `/api/ui` conventions, shell endpoint (uses 1.2) and the `FindingDetail` DTO. | 6.1, 6.5 batch 1, 6.6, 1.1, 1.2 |
| 7.2 P1 Portfolio, P2 Engagement and firm | Unchanged. Remediation port follows 5.6. | 7.1 |
| 7.3 P3 Evidence | Unchanged. | 7.1 |
| 7.4 P4 Scope, Questionnaire | Consumes the drafts endpoint (B1, built in 5.1), unified domains, why and how slots, exclusions (5.4, 5.5). | 7.1, 5.1g, 5.4, 5.5 |
| 7.5 P4 Report | Board summary and auditor detail from WP 4.3 and the §5.1 views. | 7.1, 4.3, 2.3, 6.5 batch 2 |
| 7.6 P5 Review | Queue and Gaps on §5.1. Decided items leave the queue. | 7.1, 3.5, 4.7, 6.5 batch 2 |
| 7.7 P6 Reporting | Versions, Comparison, Narrative, Board inputs, RFI on 5.3. | 7.1, 5.3 |
| 7.8 P7 Decommission | Remove Jinja UI. Restyle the client upload page and fix its keyboard path. | All |

### Phase 8. After the migration (held until you release it)

Reads stages 3 to 6. Interview records (B5). Meeting notes (S7). Evidence as-of date and re-map (S6 F2, F3). Client scope export and custom scope questions. RFI status tables and "waiting on client". "Re-assess" entry. DPDPA industry question bank (F-D14). A first-level and second-level RFI idea. GDPR, HIPAA, PCI DSS. Deterministic access-review checks (E5). Control type, frequency and key settings display.

## 6A. How the three accounts work together

This session (desktop Claude) is the orchestrator. It plans, writes the handoffs, dispatches Codex, verifies everything that comes back, opens PRs and keeps the board. It does not merge. Saqlain merges.

### Lanes

| Lane | Account | Model and mode | Takes | Does not take |
|---|---|---|---|---|
| O | Desktop Claude (this session) | Opus for design calls, Sonnet subagents for scoped reviews and screenshots | Decision records, plan and board, anatomy, prompts (Phase 4), the prompt part of WP 1.4 and every live evaluation gate (they need network and spend; the Codex sandbox has none by default), design system text, mockup content direction, verification, PRs | Long mechanical builds |
| T | Terminal Claude (Ghostty), fresh session per kickoff | Opus for decisions, Sonnet subagents for simple tasks | UCF authoring and assembly (3.1 to 3.4), questionnaire wiring and stored-data migration (5.1, 5.2), the judgment-heavy ports (Questionnaire, Review, Report), and the framework, screening and model files those WPs touch | Anything Codex can do from a plain spec |
| C | Codex | `gpt-6.1-sol`, medium effort, `workspace-write`, one worktree per run | Phase 1 and 2 code, migrations and read models from a written spec (3.5), RFI and SoA builders (5.3, 5.4), mockup builds from JSON, mechanical ports | Design calls, prompts, anything with an open question |

This follows `tasks/agent-ownership.md`: Claude owns gating, security, irreversible, invariant and judgment work; Codex owns mechanical, fully specified, contained work. WP 2.1 (issue-time rendering, an immutability change) and WP 5.6 are Claude-designed and Codex-implemented, with an Opus review. WP 5.1 is built by lane T, with an Opus review. It has one owner.

### How work moves

1. The orchestrator writes a handoff per work package: `tasks/handoffs/2026-10-DD-<wp>.md`. Fixed shape: goal, inputs, files owned, files not to touch, rules, one verify command, a Results section.
2. Codex runs are dispatched from this session, one worktree each: `codex exec -m gpt-6.1-sol -c model_reasoning_effort="medium" --sandbox workspace-write -C <worktree> "<prompt>" < /dev/null`.
3. Terminal Claude runs are started by Saqlain. The orchestrator writes the kickoff file and gives one line to paste in Ghostty. The session works in its own worktree and writes Results into the file. The two Claude sessions cannot message each other reliably, so the file is the channel. The orchestrator learns a run finished when you say so, or when it checks the branch and the Results section at each check-in. It does not poll.
4. The orchestrator verifies each result independently: reads the diff, runs the verify command, checks changed paths against the lane's file set. It never trusts a self-reported pass.
5. The orchestrator pushes and opens the PR. No Claude or Codex attribution on any commit or PR. Saqlain clicks through and merges.
6. The board is `tasks/todo.md`. Only the orchestrator edits it. One line per work package: lane, status, PR, blocker.

### Keeping lanes from colliding

- One worktree and branch per run. Never two runs in one directory.
- Each handoff names the files its lane owns. Hot shared files are `app/routers/web.py`, `app/routers/analysis.py`, `app/main.py`, `app/config.py` (settings), `app/services/retention.py`, the Alembic revisions and `tasks/todo.md`. Edits to them are serialized by the orchestrator, and the orchestrator assigns each Alembic `down_revision`.
- The UCF lane writes under `app/frameworks/ucf/` and `docs/ucf/`, plus the specific files named in WP 3.1, 3.2 and 3.4. Nothing outside the UCF package reads the library until WP 5.1.
- A usage-limit error from Codex is reported, not retried in a loop.
- Up to three runs at a time, on disjoint file sets. The session record's "one in flight" rule is edited in DR-1 to say this.

### Waves

| Wave | O | T | C |
|---|---|---|---|
| 1 | Phase 0, DR-1; handoffs; 1.4 prompt part | UCF part 1 kickoff: source atoms for ISO clauses and Annex A, started while 0.3 is being signed (mapping waits for the signature). Drafting subagents run inside this terminal session on its own budget | 1.1, 1.3, 2.2 |
| 2 | 3.5 spec, 2.1 design and decision record, 4.1 decision record, 1.4 gate | UCF mapping and master list; first domains for your sign-off | 1.2, 1.4 (non-prompt parts), 2.4, 2.6 |
| 3 | Phase 4 prompt work; verification | 3.2 DPDPA layer; 3.4 | 3.5, 2.1, 2.3, 2.5, 2.7, 2.8 |
| 4 | 4.6 gate (before 5.1 merges); 6.2 spec | 3.3 NIST layer; 5.1 | 5.3, 5.4, 5.5, 3.6 |
| 5 | 4.7, 5.1g gate; 5.6 decision record; 6.3a and 6.3b content packs; mockup captures and your review | 5.1 finishes; 5.7 reseed | 6.4 mockups from JSON; 5.6 |
| 6 | Verification, PRs, board | Questionnaire, Review, Report ports | Remaining ports, decommission; 5.3, 5.4, 5.5 if not yet done |

A wave starts when its inputs are signed, not when the previous wave ends.

### Review depth

- Routine PR: the orchestrator reads the diff and runs the verify command.
- Risky or gating work (2.1, 3.5, 4.2, 5.1, 5.6, the UCF mapping): one adversarial Opus review before the PR.
- Phase boundary: one review of the phase against this plan.

## 6B. Mockups before code

You asked on 13 Oct to see mockups of the final screens once the content is settled, before any code. This replaces "no prototype round" and the D11 "no mock-up phase". Work packages 6.3a, 6.3b, 6.4 and 6.5. One round per batch. Batch 1 does not wait for the generation work. Everything on the mockups is real settled content, not illustrative text. Nothing in Phase 7 starts before the first batch is approved.

## 6C. Verification policy (no unnecessary tests)

A check exists only to catch a failure that would be wrong and hard to notice. **This section overrides section 8 of the migration plan and the test lists in the reads plan.** From the migration plan, each screen keeps one browser smoke (the click-through), and a JSON test only where a route returns data; pixel baselines, per-width and per-theme screenshot gates and component unit tests are not added unless a component holds logic that is not display. From the reads plan, stage 2 keeps its A/B gate and the DPDPA goldens; the extra all-framework characterization checks are replaced by the one smoke in item 6. The Q3 parity check is a one-off script.

Allowed:
1. **UCF data validation.** One script, run on load and in CI, for tests 1 to 6 in §7.6. It checks data, not behavior.
2. **Scoring invariants.** Per-requirement scoring is a product invariant and its tests already exist. They are re-recorded where a golden moves, not extended.
3. **One regression check per defect that already shipped wrong:** statute citations equal the pack; an issued file never carries a draft marker.
4. **One label guard**, lint style.
5. **One smoke script per work package** (curl, script or browser step) that the orchestrator runs and reports. This replaces new test files.
6. **One app-level smoke across the seven framework subsets**: build the questionnaire, score a fixture, build the RFI. One script, run at the end of Phase 5.
7. **Three evaluation gates:** reads stage 2 (WP 1.4), Phase 4 (WP 4.6) and after WP 5.1 (5.1g) because judge input changed. Aggregate numbers only, under the cap in WP 0.5.

Not added: per-screen measurement or screenshot harnesses, pixel gates, per-PR A/B runs, case matrices for display code, tests that only restate a template. The existing suite keeps running: the affected subset per PR, the full suite at phase boundaries.

## 7. The unified control framework

### §7.1 Method

From the control-library method in your interview prep, applied to three sources.

1. **List the sources and versions.** ISO/IEC 27001:2022 with Amd 1:2024 (clauses 4 to 10, Annex A 93 controls). NIST CSF 2.0 (6 functions, 22 categories, 106 subcategories). DPDP Act 2023 and Rules 2025 (the 41 requirements in the repo pack).
2. **Break each source into single requirements.** One "must" per row with its reference. NIST subcategories hold 3 to 6 asks. Compound ISO and DPDPA items are split. For ISO the stored text is a reference and a short paraphrase, not the standard's wording.
3. **One master list.** Every source is mapped to the master once. Sources are never mapped to each other.
4. **Map each source requirement to unified controls** with a match type (equal, requirement smaller, requirement bigger, overlap, none), a coverage (full, partial, none) and a one-line reason.
5. **Clean the list.** Merge duplicates, split controls that do two jobs, remove controls that serve no source. Where sources give different numbers, the number lives in the layer that sets it. A framework's number applies only when that framework is selected.
6. **Write each control once** as who, does what, when, how, why, proof.
7. **Prove traceability both ways** by script (§7.6).
8. **Version it.** An assessment records and pins the library version (WP 3.4).

The method's gap register and roadmap are what an assessment produces. They are not library content.

### §7.2 Unit of judgment, grain and layers

**Unit of judgment (Q1).** The judged unit is the framework record: an ISO control or clause, a NIST subcategory, a DPDPA requirement. The single asks inside a record exist only as mapping atoms. Questions are asked per unified control. The AI judges, and the reviewer approves, per framework record. An answer to a unified control's question fans out to every record mapped to it, through one shared function. The expanded answer carries the unified control id, the question text and the mapping coverage, so the judge sees which part of the record the answer covers. Each record has one primary unified control, stored in place of `cluster_id`. Scoring is per record and per framework, never combined across frameworks. This is how the product already works for clusters; the UCF replaces clusters at a finer grain.

**Grain.** A unified control has one goal, one owner and one test. It is close to an Annex A control and is split where the test differs. The count is an output of the mapping. The first estimate was 150 to 250; heavy ISO and NIST overlap should bring it lower. Compare the 52 clusters today (up to 24 controls per question).

**Partial coverage.** If a source requirement is only partly covered by a base control, it maps to that control (partial) and to a remainder slot control. The record's conclusion is judged on the answers to both, each labeled with what it covers. There is no capping rule. The conclusion is the reviewer's. A remainder slot is always created when coverage is partial, unless the mapping row records "remainder immaterial" with a reason.

| Layer | Content | Rule |
|---|---|---|
| Base: ISO 27001 | Clauses 4 to 10 as ISMS requirements. Annex A 93 controls. | Every ISO requirement has a unified control. |
| NIST | 106 subcategories split into asks, mapped to base controls | Fully covered: mapped, no new control. Partly covered: mapped partial plus a remainder slot, or a recorded "remainder immaterial" reason. NIST only: own slot in the matching domain. |
| DPDPA | 41 requirements split into asks | Overlap with ISO (security safeguards, breach, processors, retention): mapped to the base, with the DPDPA remainder as its own slot. Privacy only: own privacy domains. |

A unified control is shown if any selected framework maps to it. Drop a framework and its exclusive controls disappear. Shared controls stay. Text and numbers shown never name a framework that is out of scope.

### §7.3 Master domains (recommendation, signed in WP 0.3)

ISMS and governance (clauses 4 to 10), Risk and compliance, Assets and information, Identity and access, Cryptography, Network and infrastructure, Operations, logging and monitoring, Secure development and change, Physical and environmental, People, Suppliers and third parties, Incident and breach management, Resilience and continuity, Privacy: notice and consent, Privacy: principal rights and grievance, Privacy: purpose, minimization and accuracy, Privacy: fiduciary governance (nomination, significant data fiduciary, data protection officer), Privacy: special categories and transfers. Privacy domains appear only when DPDPA is in scope. ISO themes remain an attribute for ISO reporting.

### §7.4 Fields per unified control

| Field | Reader | Static or generated |
|---|---|---|
| Statement (who, does what, when, how, why, proof) | Auditor | Static |
| Why asked | Consultant | Static |
| How to ask | Consultant | Static |
| Expected evidence (artifact names in client words, period) | Consultant, client | Static |
| Good looks like | Consultant, client | Static |
| Test (what to sample, what pass looks like) | Auditor | Static |
| Baseline risk if absent | Board, consultant | Static |
| Importance (internal) | Engine | Static |
| Control type, frequency, key settings and their source | Auditor | Static, shown in Phase 8 |
| Domain owner role | Report, remediation | Static |
| Master domain, ISO theme | Navigation, reporting | Static |
| Source mappings (framework, reference, match type, coverage, reason) | Auditor | Static |
| Applicability rule | Scope | Static |
| Answers, outcome, gap title, condition, impact, recommendation | All | Generated per assessment |

Existing signed test criteria (728) seed the test and good-looks-like fields. Existing RFI evidence requests (ISO 30, NIST 25, DPDPA 15) seed expected evidence. The answer scale stays five values (fully, partially, planned, not, not applicable); the stored values are under a database constraint and do not change.

### §7.5 Authoring workflow

1. One Opus drafting subagent per framework drafts single requirements and proposed mappings into reviewable tables, not code.
2. Lane T assembles the master list and mapping table and runs the validation script.
3. You review and sign per domain. You have done this method before; your signature is the gate.
4. Only signed rows are loaded into the app.

Size, from the review: about 550 to 650 mapping rows (ISO clauses and Annex A about 230, NIST 350 to 500, DPDPA about 80) and 150 to 250 unified controls with the fields above, plus re-keying 728 criteria. This is the longest item on the critical path, which is why it is staged so the ISO-only subset becomes usable first.

### §7.6 Checks that define done (one script)

1. Every framework record maps to at least one unified control with full coverage, or to a base plus a remainder slot, or has a recorded "remainder immaterial" reason, or is marked no match with a reason. Every record has exactly one primary unified control.
2. Every unified control has at least one source reference, a statement, a test and a domain owner role.
3. No unified control is in two domains. No source requirement maps to the same control twice.
4. For each of the seven framework subsets, no text or number shown names an out-of-scope framework, and no remainder slot of an out-of-scope framework appears.
5. Both directions answer: which controls cover requirement X, and which requirements lose coverage if control Y is retired.
6. Every question is a single obligation, answerable on the five-value scale, and contains no control code.
7. Ids are stable. A change makes a new library version.

### §7.7 What changes in code

The per-framework definitions stay as source requirement records. A new UCF data package holds unified controls and mappings. The 52 hand-written clusters and the cluster engine are replaced by the mapping table. The questionnaire builder and the RFI builder read the UCF. The judge prompt input and the review queue grouping move from `cluster_id` to unified control id. Per-requirement scoring is unchanged. The DPDPA legacy question builder is retired only after a parity check (Q3).

## 8. Dependencies

```
0.1 -> 0.2 -> 1.1 -> 1.2, 2.1, 2.3 to 2.8 (2.2 is independent), 5.1
0.1 -> 0.3 -> 3.1 -> 3.2, 3.3, 3.4, 5.3, 5.4, 5.5
3.2 + 3.3 + 3.4 + 4.6 -> 5.1 -> 5.1g -> 5.2, 5.7
0.2 -> 3.5 -> 3.6, 4.1 -> 4.2 -> 4.3, 4.4, 4.5 -> 4.6 -> 4.7 -> 5.6
1.3 -> 1.4 (gate)
4.7 + 5.1g -> 5.7
3.1 + 5.3 -> 6.3a -> 6.4 batch 1 -> 6.5 batch 1 -> 6.6 -> 7.1 (P0)
4.7 + 5.1g + 5.7 -> 6.3b -> 6.4 batch 2 -> 6.5 batch 2 -> 7.5, 7.6
6.1 needs 0.2; 6.2 needs 6.1, 3.5
```

The critical path for the whole product is 0.1, 0.3, 3.1, 3.3, 3.4, 5.1, 5.1g, 5.7, 6.3b, 6.4, 6.5 batch 2, then the Review and Report ports. The path to starting any screen code is shorter: 0.3, 3.1, 5.3, 6.3a, 6.4 batch 1, 6.5 batch 1, 6.6, then P0. Phase 4 (3.5 to 4.7) runs beside the UCF and joins at 5.7 and 6.3b. Beside both of them, you signing about 19 master domains is the real constraint; each is prepared as one table.

Earliest start per port: P0 after 6.1, mockup batch 1 and 6.6. P1 to P3 after P0. P4 Scope and Questionnaire after 5.1g, 5.4, 5.5. P4 Report after 4.3, 2.3 and batch 2. P5 after 3.5, 4.7 and batch 2. P6 RFI after 5.3.

## 9. Traceability

### §9.1 Audit themes

| Theme | Work packages |
|---|---|
| T1 Wrong or contradictory | 1.2, 2.1 to 2.5, 4.2 |
| T2 Finding anatomy | 3.5, 3.6, 4.2, 4.4 |
| T3 Report shape | 4.3, 6.2, 7.5 |
| T4 Repetition | 3.5 (one source per fact), 6.2, 7.6, 7.5 |
| T5 Vocabulary | 1.1, 1.2, 2.3 |
| T6 Control and question wording | 3.1 to 3.4, 5.1 |
| T7 Client voice | 5.3, 7.8 |
| T8 Developer text | 2.7, 1.1, port |
| T9 Orientation | 1.2, 6.2, Phase 7 |
| T10 Coverage and framework copy | 3.1, 4.5, 1.4 |
| T11 Working papers, decisions | 2.8, 5.4, 6.2, 7.6 |
| T12 Polish | Port |

The 150-row trace is in the companion appendix.

### §9.2 Your decisions

| Decision | Applied in |
|---|---|
| D1 vocabularies, score band | §5.2, §5.3, WP 1.1, 2.3 |
| D2 gap title from the model | 4.2, 3.5 |
| D3 ISO clauses | §7.2, WP 3.1 |
| D4 UCF | Section 7, WP 3.1 to 3.4 |
| D5 state cover, block issue | 2.1 |
| D6 retire exports | 2.6 |
| D7 client vocabulary | 5.3, 7.8, 5.1 |
| D8 American spelling | 1.1, 4.2 |
| D9 legal verification | 2.2, 3.2 (yours) |
| D10 board and auditor fields | §5.1 views |
| D11 sequencing and mockups | Sections 3, 4, 6, 6B |

### §9.3 Parked

F-D6 (GDPR question form), F-D11 (GDPR, HIPAA, PCI evidence requests and scope), the HIPAA and PCI parts of F-D1, F-D13 and F-D17. They return when those frameworks are scheduled.

## 10. Risks

| Risk | Mitigation |
|---|---|
| UCF authoring gates questions, RFI and report grouping and is the longest item | Staged so ISO-only is usable first. Sign off per domain. Own lane. |
| Moving from clusters to unified controls breaks stored answers and the evaluation set | WP 5.1 freezes or migrates stored data and re-exports packs independently. Gate after 5.1. |
| Prompt changes move goldens and the DPDPA path | One decision record, a setting, same-commit gate, goldens re-recorded in the PR that moves them. |
| WP 2.1 changes how issued files are produced | Decision record, Opus review, new versions only. |
| Auto-creating records changes new report versions | WP 5.6 after the gate; decision record first. |
| Silent 20,000-word cap persists until Phase 8 | Stage 1 makes every cut visible (Q5). |
| Wrong legal citations persist | WP 2.2 and your verification (D9). |
| Codex usage limit mid-run | Report, do not loop; the orchestrator finishes mechanical remainders. |
| Terminal session loses context | Fresh session per kickoff with a handoff file; Results written to the file. |
| Scope creep from Phase 8 | Explicit list and your release. |

## 11. Still needed from you

1. Verify the legal items in P2 (DPDPA `CH4.*` ids and chapter label, the s.8 and s.10 citations, the commencement wording, the editorial notes in signed criteria). Until you do, ids and pack text do not change.
2. Sign each domain's controls as the UCF tables arrive (about 18 domains, one table each).
3. Start the terminal session with the kickoff line.
4. Confirm F10 (section 13): no seventh RFI stage.

## 12. Terms

| Term | Meaning here |
|---|---|
| Golden | A stored expected output that a test compares byte for byte (for example the DPDPA report). Changing wording or scoring moves it and it is re-recorded on purpose in the PR that moves it. |
| Fan out | One answer to a unified control's question is applied to every framework record mapped to that control. |
| Framework record | One ISO control or clause, one NIST subcategory, or one DPDPA requirement. The unit that is judged, approved and scored. |
| Unified control | One goal, one owner, one test in the library. Questions are asked per unified control. |
| Remainder slot | A unified control that holds the part of a record the base control does not cover. |
| Same-commit gate | A run that compares the setting off against on at the same commit, so only the change under test differs. |
| Read model | The service that assembles one record for display from several tables. |
| DTO | The typed JSON shape the API sends to the screen. |

## 13. Answers recorded, 13 Oct 2026

All items in the open-items review were answered. The raw export is in `tasks/2026-10-13-open-items-answers.md`.

| Item | Answer |
|---|---|
| Q1 Unit of judgment | Per framework record. Questions per unified control, answers fan out. |
| Q2 Score band | Option 1, Readiness: Not ready, Partly ready, Mostly ready, Ready. Thresholds 0, 40, 60, 80. |
| Q3 DPDPA-only | UCF questions with curated DPDPA text reused. Legacy builder retired after a one-off parity script. |
| Q5 Reads stages 3 to 6 | After the migration (Phase 8). |
| Q6 Per-reader views | As in section 5.1. |
| Q7 Workpaper order and noun | Audit order. "Gap" when the outcome is a gap. "Finding" retired from the UI. |
| Q8 Questionnaire size | Accepted the grain. Expect fewer than the first estimate. No preset target. |
| S1 to S5 | Approved as written (anatomy, vocabularies, UCF method and layers, 18 master domains, list of unmocked screens). |
| A1 | Track B is folded into this plan. |
| A2 | The clean-up session never ran. Stage 2 is built in WP 1.4. |
| A3, A4, A5, A7, A8 | Agreed. |
| F1 to F9, F11 to F13, F15 to F22 | Agreed with the recommendation in section 4.3. |
| F10 | "Agree" on the card whose recommendation was no seventh stage. Read as: no seventh stage, RFI stays under Evidence. **Confirm.** |
| F14 | Dropped. The side-by-side design and operating view is out of scope. |
| P1 | $7 in total. Fewer companies per gate. An expanded run later. |
| P2 | Saqlain verifies all legal items. |
| P3 | Push and open a docs PR (this PR). |
| P4 | PR 141 stays open. Its migration plan is updated to point here (WP 0.6), then it merges. |
| P5 | Yes, start the first terminal session (UCF part 1). Kickoff: `tasks/handoffs/2026-10-13-ucf-part-1-kickoff.md`. |

Phase 0 status: 0.1 to 0.5 are answered. WP 0.6 (the decision record that edits the session record's rules) is next.
