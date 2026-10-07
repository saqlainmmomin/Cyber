# Flow rework plan (S0-S9)

Status: **draft for owner approval. No code until approved.** Date: 2026-10-07. Base: main at 00f3300, plus the flow doc, owner comments and the review handoff on `claude/stress-test-demo-company-yx20b1`.

Inputs: `docs/product/2026-10-06-consultant-journey-flow.html`, `docs/product/2026-10-07-consultant-journey-comments.md`, `tasks/handoffs/2026-10-07-flow-rework-plan-review.md`. If a line reference in the handoff conflicts with this plan, this plan wins. Each slice re-checks its line refs before starting, because main moves.

**Goal: simplify.** A smaller codebase and an app where the consultant never has to guess the next step. Each slice should delete at least as much as it adds where it can. The owner approves every PR after the normal test run and a manual click-through against the flow doc.

## Decisions settled in this session (2026-10-07)
| # | Decision | Effect on the plan |
|---|---|---|
| P1 | **No design/operating data split.** Show design (desk-review coverage per control) and operating (the confirmed questionnaire answer) side by side on the control card, as a display only. Supersedes comment decision A. | S5 is display-only. No migration, no scoring/pre-fill/tier/snapshot change. S7 (meeting notes) no longer waits on a split. |
| P2 | **The old held-out validation set doesn't matter to the owner;** a new company and dataset will be used. | S3 drops the `LEGACY_CONTEXT_IDS` mapping work. See "Validation" below for what this costs. |
| P3 | **First RFI: export (PDF/DOCX, sent by the consultant) or client upload link. The consultant picks one; both are available.** | S4 "Send RFI" = generate + issue a version, then choose Download or Create link. |
| P4 | **Merge Queue + Conclusions** into one review screen. | S8 |
| P5 | **Auto-draft findings** from approved gaps (draft, editable, deletable). | S8 |
| P6 | **Retire the per-PR file-path guards** (explained below). Behaviour tests stay. | S0 |
| P7 | Follow-ups stay inline (comment decision B). The flow doc's "generated after analysis" rows get rewritten to match. | S2 |
| P8 | Only DPDPA, ISO 27001 and NIST CSF. GDPR/HIPAA/PCI are hidden, not greyed out. | S0 |

### P6 explained: which tests get retired
Two kinds of tests live in `tests/`:
1. **Behaviour tests:** scoring determinism, golden scores, data retention/purge, routes return the right page, the LLM never reads an answer key, and so on. **These stay.** When a slice intentionally changes behaviour (e.g. the stepper gets a sixth "RFI" stage), the test is updated in the same PR to state the new behaviour. That is normal and expected.
2. **File-path guards:** about 16 test files (e.g. `test_p6_9_file_set.py`, `p6_10_support.py`, `tests/yozora_paths.py`, 540 lines) run `git diff main...HEAD` and fail if the branch touches any file outside a frozen allow-list. They were written to stop one past PR (P6-9, Yozora S1, ...) from straying into another's files. They say nothing about whether the app works, and every new slice has to add its file paths to them. **These are the ones retired:** delete the `git diff` checks and `yozora_paths.py`; keep any real behaviour assertions in the same files.

Two guards are not path guards and stay: `test_answer_key_isolation.py` (code never reads `answer_key.json`) and the "every LLM call site is registered" check (`test_remaining_llm_call_sites.py`).

### P2 correction: what the old validation set still does
The owner is right that the old companies don't matter as product data. One thing they still do: they are the only check that **analysis quality didn't get worse** when the text sent to the LLM changes. Two slices change that text: S3 (the context-profile header leaves the analysis prompt) and S6-F2 (the as-of date enters desk-review prompts). The demo company in S1 can't do this job, because it runs on a stubbed LLM.

Plan: no mapping work. Gaps that trace only to context answers stop being detectable, and that's accepted. The validation scripts only get fixed where they would crash. Run the remaining set once before and once after S3 and S6-F2 as a smoke check, never to tune against it. A new held-out company (written by someone other than whoever changes the prompts) is a **separate item, not in this plan**, and replaces the old set when it exists.

### Still open (owner)
| # | Question | Default if no answer |
|---|---|---|
| O1 | **Budget band in the PDF.** The owner said "we're not talking money, so keep it." It does print money ranges: "under 10k", "10k to 50k", "50k to 150k", "above 150k" (no currency), worked out from effort × timeline (`scoring.py:487-542`, `pdf_export.py:1394`). Keep, or show effort + timeline only? | Keep as is (owner's answer), pending a look at the printed page. |
| O2 | Can the consultant **skip** the RFI stage entirely (e.g. evidence already in hand)? | Yes, skippable ("Skip RFI, go to evidence"). The review said the stage must be skippable. |
| O3 | 5-10 redacted KPMG scope questions and one RFI. | S3 builds the structure only. S9 fills the wording when samples arrive. |
| O4 | Meeting notes: one per domain-owner session, or one per questionnaire section? | Per session: one Evidence item (source "interview") per meeting, which can fill any question. |

## Slices
Order: S0, S1, S2 and S6-F1 in parallel (disjoint files). Then S3, then S4 (both touch `web.py` and the scope partials, so in sequence). S5 after S2+S4. S7 after S5. S8 after the S1 walkthrough. S9 when samples arrive.

### S0 Hotfixes + guard retirement
- **Follow-up storage (verified bug).** The follow-up textarea posts free text into `QuestionnaireResponse.answer`, which has a CHECK constraint allowing only the 5 answer values (`web.py:2671-2695`, `models/questionnaire.py:13-16`). Every follow-up save fails. Fix: store the free text in `notes` with an empty answer, or a dedicated nullable column; pick whichever needs no CHECK change. Set `cluster_id` for `FU.<cluster>` rows. Follow-ups should survive a reload once answered.
- Gradient: `yozora-components.css:3`, the gradient stretches over document height. Fix with a fixed pseudo-element or `background-attachment: fixed`.
- First-RFI copy (`rfi.html:62`); hide "Live PDF" until released (`assessment_header.html:16-17`); hide greyed-out GDPR/HIPAA/PCI cards (`new_engagement.html`).
- Retire file-path guards (P6).
- PR #121: close as superseded. Note CTX.ISO.1-5 as candidate ISO scope items for S3/S9. Its NIST questions repeat NIST.SCP.*.
- **Exit:** one follow-up saves, survives a reload and shows in the workpaper; full suite green.

### S1 Demo company
- `scripts/demo/`: built through the real routes and services with a stubbed LLM, plus seeded conclusions so review/report screens can be walked. Nothing named `answer_key`; this is a walkthrough fixture, not an evaluation set.
- Contents: a prior released assessment (for re-assessment comparison); one DPDPA+ISO assessment and one NIST-only; an image, an xlsx and a stale-dated file (the xlsx is rejected until S6, which shows the gap on purpose).
- **Exit:** the owner walks the unseen screens (follow-ups, analysis, review, conclusions, findings, report, versions, comparison) and leaves comments. Those comments become S8's list.

### S2 Rules (docs + macros only)
- A one-page hierarchy rule: type scale, one obvious next action per screen, a done state for every step (checkmark/toast + stepper tick), how an evidence/RFI item is written (what it is, why it's requested).
- Macros for the done state and the "next step" banner in `app/templates/components/`.
- Rewrite the flow doc's Follow-ups rows to match decision B.
- **Exit:** owner signs off the rule page. Later slices apply it to their own screens only, so there's no app-wide restyle pass.

### S3 One scoping flow
- **Delete** the context wizard: `routers/questionnaire.py` context routes, `context_profiler` LLM call, `context_complete`, `question_step`, and status `context_gathered` (stop writing it; old rows still render). `Assessment.context_answers/context_profile` columns stay as dead data, with no migration.
- Remove the questionnaire gate (`questionnaire_tab.html:27-40,69`).
- Scope gets: question types `text`, `number`, `multi_select` rendered as checkboxes (today `scope_form.html:19` renders radios even for multi); a **shared facts** block asked once (headcount, sites, cloud providers, timeline, driver) followed by per-framework blocks; human labels; **assessment period + evidence cut-off** moved here from Conclusions (`report_basis_panel.html:117`).
- Duplicates removed: DPDPA SCP.1/2/3 vs CTX.DATA.4/CTX.RISK.1. Budget question (CTX.INIT.3) goes.
- `risk_tier` stops being an input. Deep-review badges come from desk review "deepened" only.
- After "Start assessment", land on Scoping (`web.py:1339`).
- Validation: per P2, fix scripts only where they crash. Smoke run before/after.
- **Exit:** create → scope → questionnaire opens with no gate; same scope answers drive the RFI; owner walkthrough.

### S4 RFI as a stage
- `assessment_stage.py`: add `rfi` between Scope and Evidence; skippable (O2). Update stepper, hub, dashboard rows, engagement table and Overview action to point at it.
- Post-scope page: **Prepare RFI** is the primary button; PDF/DOCX downloads sit below it. The scope checklist + checklist exports are replaced by "N items suggested → Prepare RFI".
- Item list: suggested items pre-selected, consultant ticks/unticks; each item shows what it is and why it's requested (`EvidenceRequest.reason`; wording improves in S9).
- **Send RFI** = generate + issue a version, then Download (PDF/DOCX) or Create client link (P3). The button reads "Send RFI" until sent, then "Upload evidence".
- New tables: `rfi_item_status` (requested / received / insufficient / waived) and an evidence ↔ RFI-item link. The consultant links evidence manually; there is no auto-mapping (D8). Both tables go on the purge list (`retention.py`) and the FK-order test.
- Evidence tab after sending: received / pending / "request more". "Run desk review" moves to Evidence.
- Issued snapshots stay immutable; old versions still render.
- **Exit:** scope → send RFI (both ways) → mark items → evidence tab shows status; owner walkthrough.

### S5 Questionnaire layout + side-by-side view
- Layout: questions become the main column; side nav and domain picker collapse or hide (`questionnaire_sections.html:30-70`). Comment per question becomes visible, not buried in `<details>`.
- Side-by-side (P1), on the question and on the control card: **Design (documents):** coverage level from `DeskReviewSummary.coverage_summary`, with the cited document. **Operating (interviews):** the confirmed answer and its source. Display only; scoring, tiers and pre-fill stay unchanged.
- **Exit:** owner walkthrough on the demo company.

### S6 Evidence engine
- **F1 (parallel from S2):** XLSX/CSV extraction (large sheets sampled, not truncated blind); scanned PDF/image OCR via per-page vision fallback (`llm_model_vision`; adds a rasteriser dependency); update accept lists on evidence and magic-link upload, and the client-facing "PDF, DOCX or image" text.
- **F2 (after S3):** document as-of date stored on `EvidenceVersion` (migration); compare with period/cut-off from S3; plain "stale" label; as-of date into desk-review prompts. Smoke run before/after (P2).
- **F3 (after S4):** one-click re-map of an evidence file to another RFI item.
- **Exit:** the demo's xlsx and image are read; the stale file is labelled.

### S7 Meeting notes → questionnaire
- Paste notes = an Evidence item, source "interview" (citations, purge, versioning, workpaper trace for free).
- New LLM module suggests answers with quotes. Answers land with a new `answer_source` in `UNCONFIRMED_ANSWER_SOURCES`, so nothing reaches analysis until the consultant confirms it (D-P5-F). Registered in the LLM call-site list; covered by the prompt-injection pack.
- **Exit:** paste demo notes → suggestions with quotes → confirm → shows as operating answer in S5's view.

### S8 Review, release and report fixes (from the S1 walkthrough)
- Merge Queue + Conclusions (P4); workpaper becomes a link; auto-draft findings (P5).
- Release button lives where the stage says it does (today stage "Release report" goes to a tab with no release button).
- Reviewer name defaults from Settings instead of 13 fields.
- Framework-conditional section refs on conclusions/review queue (today DPDPA refs are hard-coded).
- Report: demote Narrative/Board inputs/Applicability sub-tabs; one primary action per screen.
- Comparison: human labels; match the prior assessment by engagement, not the `company_name` string; add a "Re-assess" entry at setup.
- Exact list comes from the owner's S1 comments.

### S9 KPMG content
- Scope and RFI wording from the owner's samples (O3), inside the S3/S4 structure. Content only.

## What gets smaller
Context wizard + profiler LLM call + `context_complete`/`question_step` templates; `context_gathered` status; the questionnaire gate; scope checklist + its PDF/DOCX; ~16 file-path guard tests and `yozora_paths.py`; Queue/Conclusions duplication; 13 reviewer-name fields; greyed roadmap cards. Left alone on purpose: legacy DPDPA-only questionnaire path, the parked v2 pipeline, design preview routers/pixel gates (frozen; no new ones).

## Risks
1. **KPMG material may not fit** the shared-facts + per-framework-block shape. S3 builds the types generically (text/number/single/multi); S9 is content only. Ask for samples now (O3).
2. **Removing the context profile changes LLM input** with no held-out set we care about. Mitigation: before/after smoke run on the old set; a new held-out company later.
3. **The stage machine change (S4) touches many consumers.** Done in one slice, with behaviour tests updated in the same PR.
