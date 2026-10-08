# AI coherence map (2026-10-08)

Question asked: at each point where AI touches evidence, does the auditor see what it did, can they check it against the source in one click, and does it change anything downstream?

How this was checked: walked the Veldhara demo on PR #127 (:8002) in the browser (evidence tab, evidence record, A.5.18 conclusion, citation view, NIST questionnaire, RFI), plus a code trace of every LLM call site. Limits: demo documents are short stubs and the analysis is scripted, so no live AI run was done. The magic-link finding was confirmed in code, not by uploading.

## Verdict

**Rebuild trigger not hit.** The data model can carry what an auditor needs: evidence versions, evidence-to-control links, citations to the exact passage, and signed test criteria per control (design vs operating, with an evidence hint) already exist. What's broken is wiring and surfacing, plus one missing capability (testing tabular evidence). That's fixable in place, but it's the core of the product, not polish.

## The loop, step by step

| # | Step | What the AI does | Auditor sees it? | Verdict |
|---|---|---|---|---|
| 1 | Request evidence (RFI) | Nothing. One line per document type ("Access control policy and recent user access review records" covers 7 controls). No period, cycles, samples or proof of action. | Yes, but it says too little | **Half** |
| 2 | Client uploads via magic link | Nothing, ever. The upload is stored against the engagement with no assessment and no control link, so it's out of analysis scope. The only UI that links evidence to an assessment is "Reuse". | Listed in the inventory; can't open it | **Invisible** (worst one) |
| 3 | Extraction (PDF/DOCX text, XLSX sampled to 200 rows, OCR for images) | Turns the file into text | Only through a citation view that is linked from almost nowhere. No original file, no download. | **Half** |
| 4 | Desk review: what each document is | Writes a per-document summary, type and coverage areas | Stored, never rendered (only the count shows) | **Invisible** |
| 5 | Desk review: what got read | Reads all in-scope documents up to 20,000 words in total; later documents are silently dropped | Not shown; the auditor can't tell which files were skipped | **Invisible** |
| 6 | Desk review → pre-fill answers | Picks an answer with up to 3 quotes; unconfirmed until the consultant confirms | Yes, on the question | **Lands**, except quotes from new uploads show the label "Document" instead of the filename (bug) |
| 7 | Absence findings and red flags | Lists what's missing or contradictory | On the desk-review page; flag type not shown | **Half** |
| 8 | Gap judgement → conclusion card | Status, rationale, risk, quote | Yes. The A.5.18 card cites the Q2 review "9 of 11 systems" correctly. But: | **Half** |
| | | (a) no test criteria: "no criteria checklist available", although signed criteria exist and v1 never sends them | | |
| | | (b) doesn't say which linked evidence it used: the access review spreadsheet is linked to A.5.18 and never mentioned | | |
| | | (c) "Missing evidence: recent user access review records" while three access review files are linked | | |
| | | (d) the location shows as `chars:37-93` with no link to the highlighted passage; the filename goes to a record with no contents | | |
| 9 | Testing the data itself | **Doesn't exist.** The access review table (user, system, role, last login, retain/remove) is quoted as text, never tested: were removals done, were admins reviewed, which systems are covered, who reviewed and when | No | **Missing** |
| 10 | Follow-ups, narrative, remediation drafts | Generated from answers and findings | Yes | **Lands** |

Also seen, not AI: NIST questions are all "Has your organization implemented ⟨subcategory title⟩?", which reads as a client self-assessment, not a consultant's interview. The NIST assessment shows DPDPA-sounding section names ("Governance & Accountability", "Incident Response & Breach Notification"). The evidence record labels the access review export as "Other".

## What to fix, in order

1. **Client-link uploads reach the assessment.** Link them to the assessment the RFI was issued from, and to the requested item's controls. Small, bug-sized. Without it, the magic link is a dead end.
2. **Evidence viewer, in four parts:** the original file (inline PDF/image, table for XLSX/CSV, download, access guard); what the AI read (extracted text, "sampled 200 of N rows" note); what the AI made of it (the stored per-document summary from step 4); where it's cited. This one screen turns steps 3, 4 and 5 visible.
3. **Make the conclusion card checkable.** Every citation opens the highlighted passage. List the evidence linked to the control and whether the AI used it. Drop "missing evidence" when matching evidence is linked. Name any documents dropped by the 20,000-word limit.
4. **Test criteria in the loop.** Show each control's signed criteria (design and operating) on the card, write RFI items from their evidence hints, and send them to the v1 judge. **Needs your decision:** this changes the analysis prompt, which is the area parked by P6-5c.
5. **Test tabular evidence, starting with access reviews only.** Map the columns (AI), then deterministic checks: coverage against the system list, removals actioned, privileged accounts reviewed, reviewer and date present, number of cycles in the period. The results show on the card as findings the auditor confirms. **Needs your auditor input** on what the checks are.

Items 1–3 are small, need no prompt changes, and make every existing AI step visible. Items 4–5 are where the AI starts doing the auditor's real work, and they need you to decide or design.

## Follow-ups noted 2026-10-08

- #127 sampling dropped 6 of 35 exceptions in Saqlain's 220-row access review test file (incl. E131: terminated, Admin, access still enabled). Sent back to Codex: store every row (`tasks/handoffs/2026-10-08-flow-s6-f1-keep-every-row.md` on `codex/flow-s6-f1-fix`).
- Saqlain wants the Veldhara demo company (#128, merged) fleshed out later: it's bare-bones (130-300 character stub documents).
- Fresh context update (CLAUDE.md, status log) after the evidence fixes land; #116 was closed as stale.

## Fit with the flow-rework plan

- S6-F1 (#127, XLSX/OCR) is a prerequisite for item 5. Keep it.
- Item 1 overlaps S4 (RFI as a stage). Items 2–3 don't overlap anything.
- Suggestion: do 1–3 before S3; scope 4–5 once you've decided on them.
