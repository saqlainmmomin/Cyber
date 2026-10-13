# UI thread record, for the content session to pick up

Date: 13 Oct 2026. Branch `codex/ui-audit`, PR #141 (docs and static prototypes only, open, not merged). Worktree `/Users/saqlainmomin/dpdpa-ui-audit`.

Written at Saqlain's request after he read the third-pass review page. It records what this thread did, what was decided, what the decisions rest on, what was not checked, how this work overlaps with the content audit, and what it will cost to redraw the screens once the content is settled.

## 1. Where things stand

**Decision by Saqlain, 13 Oct 2026: the migration does not start yet.** The content session found problems that a port would carry across unchanged. Content is fixed first; then the screens are regenerated against the settled content, the plan is finalised, and only then does the build start. His words: "the content remap will be done first and then we can just port or migrate the UI."

- Final approval on the review page: **Changes needed first.**
- His view of the current prototypes: "these screens look good for now, they are going to be changed again once the content gets finalized."
- Step 0a of the plan is on hold. No build kickoff prompt was written.
- PR #141 stays open. Whether to merge it as a record before the content work is his call; nobody has asked him since the hold.

**Answered by Saqlain later on 13 Oct 2026 (in chat). These override anything below that says otherwise.**

1. **No more prototypes.** "We won't be doing prototypes this time. We will define the design system, the content and get straight to building." The static prototypes in `docs/ui-audit/prototypes/` are a record of approved layout decisions, not something to regenerate. Section 6 below (effort to regenerate the UI) no longer applies as written; what remains of it is the design system and plan work.
2. **A decided item leaves the queue at once.** The queue shows only what is pending. The "Decided" group in `review-queue.html` and in the amendment's Review queue line is superseded. Undo and reopen need a home (my suggestion, not his: a short undo message after the decision, and "Reopen decision" on the gap).
3. **Board summary length is the other session's.** The content session owns what the board view contains. The two-per-domain shortening in `report.html` is not a decision.
4. **Report and Applicability are approved.**

So the order is now: design system defined, content defined, then build. No prototype round in between.

## 2. What this thread did

Three commits on `codex/ui-audit`: `6d895b5`, `9cb8954`, and the one that adds this file. Detail is in the Results section of `tasks/handoffs/2026-10-13-review-structure-and-rfi-kickoff.md`.

| Work | Where |
| --- | --- |
| Read the four Review screens and answered "is this what my workpaper does" and "why four screens" | Results section 1 of the kickoff file |
| Review redrawn as two screens. `conclusions.html` replaced by `gaps.html`; stepper shows Queue and Gaps | `docs/ui-audit/prototypes/gaps.html`, `tools/build_prototypes.py` (`gaps`, `trail`, `remediation`) |
| Real workpaper and remediation data pulled from the demo app for the 32 sample controls | `tools/extract_workpaper.py`, `prototypes/workpaper.json` |
| Evidence request detail: document names only, controls behind one button, Example slot removed | `rfi()` in `build_prototypes.py` |
| Board summary shortened from 5,930px to 3,406px at 1440 | `report()` in `build_prototypes.py` |
| Decision written into the design system amendment, the spec, requirements R11, C01 to C03, F03, and plan sections 4.4, 6.1, 6.2 (new B10), 6.3, 7 | `docs/ui-audit/*.md`, `requirements.json`, `docs/plans/2026-10-12-001-nextjs-frontend-migration-plan.md` |
| Verifier and capture tool follow the new structure | `tools/verify_audit.py`, `tools/capture_prototypes.py` |
| Review page for Saqlain (private) | https://claude.ai/artifact/9uj6BYMdsm9NKuiedj4evk |

## 3. Decisions, and who made them

### Saqlain's (in chat, 13 Oct 2026)

| Decision | Note |
| --- | --- |
| Review is two screens: Queue and Gaps | Conclusions, Findings and Workpaper stop being screens |
| Compliant controls are an "All controls" filter on Gaps | Gaps opens on controls with a gap |
| Remediation lives on the gap; approving a gap creates the record | Removes the manual "Create finding" step. Backend change, B10 in the plan |
| Workpaper is a section of each control, plus one whole-assessment export | No Workpaper screen |
| Analysis runs go to Overview; excluded and unconcluded requirements go to the report's auditor detail and the exported workpaper | Not drawn |
| Content is fixed before the migration | Section 1 above |

He chose the first four from options I wrote, each time picking the one I marked as recommended. He had the evidence summary in front of him but not the content audit's findings on the same screens. Treat them as decided on the structure and open on the detail.

### Mine, not confirmed by him

- Period, sign-off and release panels move from Conclusions to Report.
- The open gap leads with Remediation and does not repeat the gap statement, because the row states it.
- The workpaper is drawn as four steps: the client answered, the evidence showed, the AI proposed, the reviewer decided.
- One "Show controls supported" button per evidence request, instead of the hover per line that he suggested. Reason: hover does not work by keyboard or touch.
- The Example slot is removed from evidence requests. "What good looks like" renders only when most of its words are not in the title. That rule is a word-overlap test and is crude.
- The client's note is left out of the workpaper where it only repeats the reasoning. In the demo data that is every control, so the slot never renders.
- The screen is named "Gaps". This choice touches the content audit's vocabulary decision (D1) and its finding about the word "finding" (F-B8).
- Decided items stay in the queue's "Decided" group (unchanged from the queue he approved).
- Board summary shows two high-risk gaps per domain.

## 4. What the decisions rest on

### What I read

| Source | How much |
| --- | --- |
| `pages/review_queue.html`, `conclusions.html`, `findings.html`, `workpaper.html` | In full |
| `components/workpaper_entry.html` | The body in full |
| `components/conclusion_card.html`, `finding_card.html` | Headings and the read-only parts; not the forms |
| `web.py` routes for review, conclusions, workpaper, findings | In full |
| `models/finding.py`, `conclusion.py`, `action.py` | In full |
| `services/workpaper.py` | Data classes and `build_workpaper` in full |
| `services/findings.py` | `create_finding`, `findings_page` and the constants; not the action state machine |
| `services/report_content.py` | `assessment_findings` only |
| Callers of the finding record | Found by grep: `routers/reports.py`, `board_report.py`, `narrative.py`, `board_inputs.py`, `remediation_rollup.py`, `actions_export.py`, `retention.py`. I read the call lines, not the functions |
| Live demo, assessment `d491ee73` | The four Review pages fetched over HTTP and counted; record counts from the demo database, read-only |
| Content audit (`dpdpa-next/tasks/2026-10-13-content-audit.html`) | Summary, the twelve themes, the eleven decisions and the "PR 141 gaps" table. About an eighth of the text |

### Numbers, and one correction

Assessment `d491ee73` is **DPDPA plus ISO 27001**, not ISO alone: 99 conclusions, of which 93 are ISO (64 compliant, 28 partially compliant, 1 non-compliant) and 6 are DPDPA (4 partially compliant, 1 non-compliant, 1 not applicable). All 99 are approved. 34 have a gap outcome; 6 have a finding record; 28 do not. My chat summary and the review page call it "the ISO assessment with 99 controls". The counts are right; the label is loose.

### What I did not check

- **The approval code path.** B10 says "approving a gap creates its remediation record". The place to do that is `conclusion_review.decide`. I did not read it. I do not know how reopen, reject after approve, edit-and-approve or the legacy bulk approvals should treat a finding that already exists, beyond the `source_approved` flag I saw being read.
- **What the automatic record would say.** A finding's title is prefilled with the control name and its description with the gap text. Creating records automatically today would file 28 more findings titled "Access rights" and the like. The content audit reports the same prefill (its T2). B10 is only worth doing after the gap title exists.
- **The effect on issued reports.** After B10 the PDF, board deck and tracker of an existing assessment would list every approved gap. I did not look at how report snapshots freeze content, so I do not know whether issued versions are safe.
- **Tests.** I did not read or run the test suite. I do not know what pins the current four screens.
- **Other frameworks.** Only this one demo assessment. Nothing checked for a DPDPA-only, NIST or three-framework assessment, where the queue groups shared evidence across frameworks.
- **The interim assessment** (`506d1f04`, pending items). Counts only. I did not watch an item being decided.
- **The engagement-level "Findings and actions" page.** Not opened. It shows the same finding records and would need to agree with the Remediation block.
- **The release and sign-off logic** that I moved to Report.
- **The screens as a person sees them.** I read rendered HTML and counted elements. I did not look at the four live Review screens in a browser in this session; the screenshots are from earlier sessions.
- **The client's side of an evidence request.** The prototype is the consultant's request list. The client upload page is not drawn anywhere in the audit.
- **Most of the content audit.** I did not read the 150 findings, the reference tables or the proposed vocabularies.
- **Accessibility beyond one pass.** Tab order, focus rings and `aria-expanded` were checked by script on Gaps, evidence requests, report and queue. No screen reader. Greyscale was inspected by eye on Gaps only. Questionnaire and Applicability were not rechecked.
- **Dark theme, and widths under 1280** apart from one 390px check of the evidence request.

## 5. Overlap with the content audit

The content audit's own framing: "The interface is not the main problem. The content has no designed shape for its reader." That matches what Saqlain said on the review page. Below is how each of its themes meets this thread's work, from the part of it I read.

### Where the two agree

| Content audit | This thread |
| --- | --- |
| T4: the same text under different headings; Conclusions re-embeds the queue card (F-A17, F-A27) | Same finding, reached from the templates. Removing Conclusions resolves it structurally |
| T4 direction: "each downstream screen adds what the previous one lacks (owner, target, status, closure evidence)" | That is the Gaps design: the open gap leads with remediation |
| T2: the finding title is the control name (`findings.py:899`) | Same observation; it is why B10 must follow the gap title |
| T3: board and auditor views of one fact set | Already in the report prototype |
| T7: one request lists artifacts that belong to other requests (F-B16); control codes in client text (F-B17) | Saqlain's RFI notes say the same. The codes are now hidden by default |
| T11: the applicability statement should list exclusions only | Already in the applicability prototype |
| T9: crumbs should read Client / Engagement / Assessment / Page | The prototype context line does this |

### Where they pull apart, and need one answer

1. **The anatomy of a finding (T2, decision D2).** The audit wants gap statement, condition, criteria, cause, impact, risk basis, recommendation with reasoning, owner role, priority and timeline, and provenance. The Gaps detail has recommendation, why, impact, owner, target, status and a four-step trail. It has no cause, no risk basis, no criteria and no priority. Plan row B4 adds three fields; the audit says at least four more are generated today and dropped. **The gap detail and the queue detail must be redrawn once the anatomy is fixed.** This is the largest overlap.
2. **The order of a workpaper (T11).** The audit proposes: control, requirement text, procedure, evidence examined, result, conclusion, sign-off, with run details in an appendix. I drew: client answered, evidence showed, AI proposed, reviewer decided. Mine has no requirement text, no procedure and no sign-off, and it gives the AI proposal and its checks a step of their own, which the audit says is engine text that should not lead (T8, F-A14). **Use the audit's order unless Saqlain prefers mine.** The data I pulled into `workpaper.json` serves either.
3. **The word for the thing (T5, D1, F-B8).** I named the screen "Gaps". The queue prototype's heading still says "Findings". The audit counts four meanings of "finding" in the product. The name of this screen, the queue heading, the status words ("Open", "Not assigned") and the outcome and risk words in every prototype should come from the audit's controlled lists once Saqlain picks them.
4. **Remediation fields (T2, T5).** The audit reports three priority maps that disagree and an owner role that is generated and not saved. The Remediation block shows owner, target and status and no priority. Its fields should follow the audit's decision.
5. **Evidence requests (T7).** The audit wants each item split into a plain "why" for the client, what to send, what good looks like and a separate auditor basis, with one "please send by" date. My layout has what to send, what good looks like and the supported controls behind a button, which is the auditor basis. It has no "why" slot and no date. Small redraw. The client upload page needs drawing from nothing.
6. **Reject and edit (T11, F-A16).** The audit reports that reject takes no reason and "Edit" always approves. The queue prototype keeps Approve, Edit and Reject as they are. If that behaviour changes, the decision bar changes.
7. **Stage and status logic (T1, F-C1 to F-C4).** The audit reports four rollups that disagree on whether an engagement is released. The stepper's ticks come from that logic. The stepper should not be built until there is one answer.
8. **Question grain (T6, D4).** 317 of 412 questions are one template; the audit proposes 150 to 250 unified requirements. The questionnaire prototype assumes one row per control inside a domain, and the multi-framework version was never drawn. That screen waits on D4.
9. **Report length (T3, F-B3, D10).** The audit notes "Fix first" is capped at 5 while 17 gaps are critical or high, and asks what the board view contains. My shortening to two per domain is one answer to the same question. D10 should settle it.
10. **B10 is not in the content audit.** Its "PR 141 gaps" table was written against plan rows B1 to B9. The content session should know that B10 now exists and that it changes what the PDF, deck and tracker contain.

### What in this thread survives content changes

- Two screens in Review, and the reasons for it.
- Remediation and workpaper as sections of a gap, not screens.
- The register as the landing view, with compliant controls behind a filter.
- The type roles, stepper, status shapes and layout rules from the second pass.
- No clause codes inline in an evidence request; nothing rendered that only repeats a title.
- The extraction tool and the builder: content is in JSON files, so a redraw is a data and template change, not a rewrite.

### What will not survive

- Every label, heading and status word in the prototypes.
- The field list and order inside the gap detail and the queue detail.
- The four-step trail.
- The hand-written text marked illustrative (190 elements), which stands in for content that does not exist yet.
- Plan rows B4, B6, B9 and B10 as written, and the PR counts in section 6 of the plan.

## 6. Effort to regenerate the UI after the content is settled

**Superseded 13 Oct 2026:** Saqlain decided there will be no further prototype round (section 1). The rows that still stand as work are the design system and spec rewritten as one text, the plan finalised, and the checks not yet done. The other rows describe decisions the build now has to make directly from the design system and the content definitions.

Sizes are my estimates, in working sessions of this kind (one sitting, with captures and the verifier). They assume the content session delivers the inputs named. I have not done this work, so treat them as rough.

| Work | Needs from content | Size |
| --- | --- | --- |
| Relabel all six prototypes from the controlled lists | D1 answered; one list each for outcome, risk, priority, workflow, score band | Half a session |
| Redraw the gap detail and the queue detail to the settled finding anatomy | Field list and order (T2, D2); sample text for two or three real gaps | One session |
| Redraw the workpaper section to the settled order | T11 direction confirmed; what counts as "procedure" | Half a session, done with the row above |
| Evidence request detail with a "why" line and a due date; draw the client upload page | Item schema (T7); D7 client vocabulary | One session. The upload page is new work |
| Report: board and auditor field sets | D10; an executive summary that is real prose | Half to one session |
| Questionnaire, including the multi-framework version | D4 grain; domain list; why-asked and how-to-ask text for a sample | One session; more if the grain changes the navigation |
| Overview with analysis runs; the report's excluded and unconcluded lists | T8 direction on run details | Half a session |
| Rewrite the spec and design system as one text instead of amendments over older text | All of the above | One session |
| Finalise the plan: Track B rows, Track C as its own plan, sequencing (D11), PR counts | The audit's decisions answered | One session, with Saqlain |
| Checks not yet done: screen reader pass, dark theme, widths under 1280, greyscale on every screen | None | Half a session |

Total: roughly six to eight sessions of prototype and plan work after the content decisions land. The backend work is separate and larger: the finding anatomy fields, B10, the vocabulary module, the stage logic and the request item schema are all code in the Python app, and none of it has been estimated in this thread.

## 7. A sequence to consider

This is a proposal. Saqlain has decided only that content comes first.

1. Saqlain answers the content audit's decisions D1 to D11. D1 (vocabulary), D2 (gap title), D4 (question grain), D10 (board and auditor field sets) and D11 (sequencing) are the ones the screens wait on.
2. The content session fixes what is wrong in the Python app now (its T1: the draft marker on issued reports, the statute citations, the score label, the stage logic). These do not depend on the UI.
3. One agreed finding anatomy and one workpaper order, written once, owned by the content session. This thread's sections 5.1 and 5.2 are the input from the UI side.
4. The design system is written as one text (today it is an amendment over older text), using the settled vocabulary and field lists. No prototype round (Saqlain, 13 Oct 2026).
5. The plan is finalised as one document: backend changes, content work and screen ports in order.
6. The build starts.

## 8. For whoever picks this up

- Start from `docs/ui-audit/prototypes/` and `tools/build_prototypes.py`. Edit the builder and the JSON, never the HTML. Run `python3 docs/ui-audit/tools/verify_audit.py` after committing; it checks git status.
- The approved rules are the amendment at the top of `docs/ui-audit/DESIGN_SYSTEM.md` and `NEXTJS_MIGRATION_UI_SPEC.md`. Body text below the amendment is older and loses where they disagree.
- The demo app is at `http://127.0.0.1:8011`. Keep `OPENROUTER_KEY=""`. Never read `validation/companies/*/answer_key.json`.
- The review page's builder was in this session's scratchpad and may be gone. Rebuild from `docs/ui-audit/prototypes/screenshots/`.
- No em dashes in docs. No Claude or Codex attribution on commits or PRs. Claude pushes and opens PRs; Saqlain merges.
