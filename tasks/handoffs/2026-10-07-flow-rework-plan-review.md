# Flow rework: plan review and slice order (handoff)

Read-only review by an Opus subagent, 2026-10-07, against main at ebc34a9. Everything comes from reading code; the app and tests were not run. No `answer_key.json` was opened.

## Owner direction (read this first; it overrides anything below that conflicts)
- **Next session is PLANNING only; implementation follows in later sessions.** The plan should cover all the slices below (S0-S9), with the owner approving the plan before any code.
- **Design vs operating-effectiveness split is OPEN FOR DISCUSSION, and it may not be required at all.** The owner's only reason for it is to have that *view*. Because the data-model split touches scoring, prompts, pre-fill, tiers, exports and snapshots (see section b), the planning session must first ask whether it is needed, and if so, find the least intrusive way to get the view. Candidate paths to weigh, from least to most intrusive:
  1. No split. Keep one result per control. Show the desk-review design coverage and the confirmed questionnaire answer side by side on the control card, as a display only (the data already exists: `DeskReviewSummary.coverage_summary` and findings vs the questionnaire answer).
  2. A derived view: label each requirement as design-type or operating-type in the framework definitions, and group or filter the existing results by that label in the UI and report. No new columns, no scoring change.
  3. A real split in the data model (two stored results per control). Only if 1 and 2 cannot give the owner the view they need. Needs the pre-fill decision (open question 1) first.
  Do not build path 3 by default. Slice S5 in the plan below should be re-scoped accordingly.
- **Owner is the final validator.** The owner reviews and approves every PR before it goes out, after the normal test run. Do not add new pixel gates, per-PR guard allowances beyond what the existing suite forces, or new test scaffolding for its own sake. Keep tests to what protects real behaviour (scoring determinism, data loss, the existing suite). Each slice ends with the owner's manual walkthrough.
- **Goal of the whole effort: simplify.** Make the code smaller and the app more intuitive. Prefer deleting and merging over adding (see section d).
- Decisions already made: demo company and the revised slice order are agreed. Follow-ups stay inline (decision B), so the flow doc's Follow-ups rows that say "generated after analysis" are stale and should be rewritten to match B.

Inputs: `docs/product/2026-10-06-consultant-journey-flow.html`, `docs/product/2026-10-07-consultant-journey-comments.md` (owner decisions are fixed), `tasks/2026-10-06-status-log.md`.

## Headline findings
1. **Follow-ups probably can't be saved today.** Free-text follow-up answers go into an `answer` column that only accepts the five answer values; the DB CHECK should fail and return a 500. Fix before the owner tests follow-ups.
2. **Hold PR #121; don't merge it.** It extends the context wizard the plan is about to delete. Three of its five NIST questions repeat the NIST scope questions (CTX.NIST.1/2/3 vs NIST.SCP.4/2/1, `nist_csf.py:1229-1264`). Carry CTX.ISO.1-5 forward as candidate ISO scope items.
3. **"RFI as a stage" needs a new data model:** a status per RFI item, and a link from each piece of evidence to the item it answers. Neither exists.
4. **Period and evidence cut-off are captured too late.** Today they are a hidden gate on Conclusions (`report_basis_panel.html:117`). Stale-evidence detection can't work until they move to setup or Scope.

## (a) Main vs owner comments
| Row | Status | Evidence |
|---|---|---|
| Only 3 frameworks | Done | `web.py:78`; GDPR/HIPAA/PCI still greyed out at `pages/new_engagement.html:13,25` (noise) |
| Land on Scoping after Start | Missing | `web.py:1339` redirects to the engagement page |
| Re-assessment first-class | Partial | comparison at `web.py:3457-3465` matches on `company_name` string, needs both `completed`; no "Re-assess" entry at setup |
| One scoping flow | Missing | gate at `partials/questionnaire_tab.html:27-40,69`; same facts asked twice: `dpdpa/scope_questions.py` SCP.1/2/3 vs CTX.DATA.4, CTX.RISK.1 |
| Budget removed | Missing | `dpdpa/context_questions.py:165` (CTX.INIT.3); PDF also prints an effort-derived budget band (`scoring.py:540`, `pdf_export.py:1394`) |
| Human labels | Missing (wizard) | `partials/question_step.html:19`; scope form is fine |
| Back-button bug | Present | `question_step.html:50-63` appends instead of replacing |
| Scope edits show in RFI | Partial | only "Source data changed since generation" (`pages/rfi.html:119`) |
| Overview directs the user | Partial | order is Set scope -> Upload evidence (`assessment_stage.py:107`), never Prepare/Send RFI |
| Prepare RFI highlighted | Missing | `partials/scope_complete.html:30-32` small secondary; primary is "Continue to evidence" (`:56`) |
| RFI is a stage | Missing | STAGES has 5 entries (`assessment_stage.py:45`); RFI is the Evidence tab's "Requests" toggle |
| "Send RFI" until sent | Missing | flow is Generate version -> Versions tab -> Issue -> Client links tab (`rfi.html:26,126,138`) |
| User picks first-RFI items | Partial | only inverted "Already received" omit checkbox, documents only (`rfi.html:88`); copy at `:62` is wrong for a first RFI |
| Item says what and why | Partial | `EvidenceRequest.reason` exists in schema; content waits for KPMG |
| Received / insufficient / waived | Missing | no status model; "received" only from magic-link audit events (`services/request_summary.py:26,41-66`) |
| Post-send Evidence view | Missing | no received/pending/request-more |
| Same document once across frameworks | Done | UCC merge by `document_type` (`frameworks/schema.py:96`) |
| XLSX/CSV, scanned-PDF OCR, doc dates | Missing | `services/document_processor.py:227-236`; no date in any prompt |
| Design vs operating fields | Missing | single answer scale (`models/questionnaire.py:13-16`) |
| Questionnaire opens without gate | Missing | `questionnaire_tab.html:69` |
| Comment per question | Done (buried) | collapsed `<details>` in `section_questions.html` |
| Layout cramped | Present | `questionnaire_sections.html:30-70` |
| Gradient bug | Present | `static/css/yozora-components.css:3`: gradient on `html` stretched over document height; try `background-attachment: fixed` or a fixed pseudo-element |

## (b) What each change touches
**Merge context wizard into Scope, drop budget, remove the gate**
- Columns `Assessment.context_answers/context_profile` stay as dead data (no migration). Stop writing status `context_gathered` (`web.py:2490`, `routers/questionnaire.py:92`, `services/portfolio.py:11,26`, `components/status_badge.html`).
- `risk_tier` only changes "Deep review" badges (`tier_engine.py:46-50`); counts and scoring unaffected. DPDPA `relevance_weight`/`context_note`/`skip_if` are display only (`dpdpa/questionnaire.py:135-185`). Profile also adds a header to the analysis prompt (`frameworks/prompts.py:474`, `dpdpa/prompts.py:469-478`): removal is scoring-safe but changes LLM input, so re-run held-out validation after (never tune).
- Touch: `routers/questionnaire.py:39-145`, `schemas/context.py:13`, `web.py:18,1930,2417-2497,3607`, `design.py:13,365,453`, templates `context_complete`, `question_step`, `questionnaire_tab`; tests `test_yozora_s5.py:39,97,113,466`, `test_p5_4...:918,937`, `test_remaining_llm_call_sites.py:107-158`, `test_p6_1d...:255`, `test_phase1_prefill.py:67`; `p6_10_support.py:96`.
- Validation is the biggest risk: `export_question_pack.py:109-146`, `lint_pack.py:237-320` (errors on unknown context ids incl. answer-key trails `context:CTX.*`), `run_company.py:383-389,605`. Option 1: freeze a `LEGACY_CONTEXT_IDS` list in `scripts/validation` and map CTX answers onto new scope fields. Option 2: accept some gaps become undetectable. Check only via `lint_pack` error counts.
- Seeds: `scripts/seed_test_companies.py:31,1292,1409`, `design/harness/seed_s5.py`, five `validation/companies/*/intake_answers.json`.
- Structure gap: `ScopeQuestion.type` is single/multi only (`frameworks/schema.py:78`) and `scope_form.html:19` renders radios even for multi. KPMG-style questions (headcount, sites, cloud providers) need text, number, multi types and a shared-facts block.

**RFI as a stage**
- `assessment_stage.py` gets an `rfi` stage. Consumers: stepper (`web.py:182-209`; tests pin 5 `class="stp`), hub state/`framework_hub_panel.html`, portfolio copy (`web.py:250-268`), dashboard rows (`web.py:345-395`), engagement table (`web.py:564`), Overview action (`web.py:2019-2033`); tests `test_yozora_read_models.py:280-321`, s3, s4, s5.
- New tables (both go in the purge list `retention.py:614` and FK-order test `test_retention.py:548`): `rfi_item_status`; evidence <-> RFI-item link (also needed for one-click re-map; D8 forbids auto-mapping, `schema.py:93`).
- Also `rfi_requests.py` (client text "PDF, DOCX or image" at `:47` must change with XLSX), `request_summary.py`, `rfi_export.py`.
- Issued snapshots are immutable and Claude-owned (`tasks/agent-ownership.md`). "Send" = generate + issue without breaking old versions. Stage must be skippable.

**Design vs operating split**
- Smallest real split: design result = desk-review coverage per requirement (deterministic, overridable); operating result = confirmed questionnaire answer; final `Conclusion.outcome` and `scoring.py` unchanged. Keeps golden tests safe (`tests/support/canonical_dpdpa.py`, `test_no_blended_scoring.py`, `test_picker_and_scoring_contract.py`).
- Hidden conflict: `auto_answer.py` and `_modulate_question` pre-fill the operating answer from design documents; LIGHT tier = `pre_filled` (`tier_engine.py:34`). After the split, documents can't honestly pre-fill operating answers; counts, tiers and stage progress shift. Owner decision needed.
- Other consumers: `section_questions.html`, `conclusion_card.html`, `requirement_card_body.html`, `workpaper.py`, `approved_report`, `report_content`, `pdf_export`, `board_exports`, `actions_export`, `compute_delta`, snapshot schema version (old snapshots must still render), Alembic, validation `question_pack.questionnaire.json`.

**XLSX/CSV + OCR + as-of dates**
- Extraction: `document_processor.py:29-41,227`, `evidence.py:148`, accept lists at `evidence_inventory.html:79` and magic-link upload; truncation in `desk_review._truncate_documents` (5,000-row access review needs sampling). Citations are character spans (`citations.py:5`) so spreadsheet-as-text works; evidence detail needs a table render.
- OCR: per-page vision fallback (`llm_model_vision`); adds a rasteriser dependency.
- Dates: move period/cut-off capture to Scope; put as-of date into desk-review prompts (`frameworks/prompts.py`, `dpdpa/prompts.py`), which falls under the held-out rule (re-run validation, never tune); store document date on `EvidenceVersion` (migration).

**Meeting notes -> questionnaire auto-fill**
- Store pasted notes as an Evidence item (source "interview"): citations, purge, workpaper trace, versioning come free.
- New LLM module: add to `p6_10_support.py:89-101` and `test_remaining_llm_call_sites.py`; new `answer_source` value added to `UNCONFIRMED_ANSWER_SOURCES` (`auto_answer.py:33`) so machine answers never feed analysis unconfirmed (D-P5-F); prompt-injection pack (`scripts/injection_pack_live.py`). Depends on the split decision.

**Guard tax:** `tests/yozora_paths.py`, `P6_10_FORBIDDEN_PATHS` and guards in 15 other test files mean every slice adds allowances; `yozora_paths.py` is a certain merge-conflict point.

## (c) Unseen screens: predicted problems
- **Follow-ups:** every radio change triggers an LLM call and rebuilds the questionnaire (`web.py:2713-2779`); follow-ups aren't stored until answered and vanish on reload; saving fails on the CHECK (`web.py:2671-2695`, `models/questionnaire.py:13-16`, Alembic `6fc718bb9f09:135`); no test posts `followup_FU`; multi-framework `FU.<cluster>` rows have no `cluster_id`.
- **Analysis:** Run analysis card under the split view (`questionnaire_tab.html:82-108`); 4 actions at `analysis_complete.html:40-45`; "Live PDF" offered before release (`assessment_header.html:16-17`) but route returns 403/409 (`utils/review_gate.py:28-33`).
- **Review queue:** cramped split layout; raw ids (`conclusion_card.html:28`); wall of text (125-line requirement card body); done state points to `/report` (`review_queue.html:53`), report only says "Open conclusions" (`report_summary.html:46,55`), release lives on Conclusions (`conclusions.html:46`): ping-pong; reviewer-name field on 13 pages.
- **Conclusions/release:** hard-coded DPDPA section refs (`conclusions.html:21`, `review_queue.html:18`); hidden period gate; two primaries (`conclusions.html:35`, `release_panel.html:93`); stage "Release report" goes to `?tab=report` (`assessment_stage.py:140`) which has no release button; dashboard calls it "Sign off board report" (`web.py:366`).
- **Findings:** manual "Create finding" per approved conclusion (`findings.html:50-70`).
- **Report:** 5 sub-tabs (`seg_rows.html:16-27`); `report_summary.html` ~9 stacked sections.
- **Versions/board:** 4-5 ghost download buttons per row (`report_snapshots.html`); `board_inputs.html` three Save buttons, no completion state.
- **Comparison:** raw enum labels (`comparison.html:9`); fragile matching (`web.py:3458`); reachable only from the report.

## (d) Cut / merge / demote
| Item | Action | Risk |
|---|---|---|
| Context wizard, profiler LLM call, `context_complete`, `context_gathered` | Remove | Medium |
| `risk_tier` -> Deep review badges | Drop the input; keep desk-review "deepened" | Low |
| DPDPA domain screening (third pre-fill) | Demote, then remove | Medium (17 test files, `run_company` stage) |
| Scope checklist + checklist PDF/DOCX (duplicates RFI) | Replace with count + "Prepare RFI" | Low |
| Review sub-tabs Queue/Conclusions/Findings/Workpaper | Merge Queue+Conclusions; workpaper a link; auto-draft findings | Medium |
| Report sub-tabs Narrative/Board inputs/Applicability | Demote (board work deferred) | Low |
| Reviewer name x13 | Default from Settings | Low |
| Greyed roadmap frameworks | Hide | Low |
| Per-PR protected-surface guards | Retire or rebaseline (owner decision) | Medium |
| Design preview routers `design_s7`-`s9`, pixel gates | Freeze; add no new ones | High if deleted |
| Legacy DPDPA-only questionnaire vs UCC engine | Leave | High |
| Parked v2 pipeline | Leave | Decision record |

## (e) Recommended slice order
Changes to the original order: don't merge #121; follow-up fix first; write feedback/hierarchy rules before building new screens; settle the split's shape (decision only) before any questionnaire/evidence/MoM screen; period capture belongs in the scope slice.

**Riskiest assumption:** KPMG scope/RFI material fits today's single/multi radio Scope shape and per-framework blocks. De-risk: get 5-10 redacted KPMG scope questions and one RFI before building the structure. Second risk: a "simple" split doesn't change counts or scoring; de-risk with a paper mock of one control card on the demo company.

Every exit ends with the owner clicking through against the flow doc.
- **S0 Hotfixes** (parallel, disjoint): follow-up storage; gradient CSS; first-RFI copy (`rfi.html:62`); hide Live PDF until released. Exit: one follow-up saves and shows in the workpaper.
- **S1 Demo company** (parallel from day 0): in `scripts/demo/`, no file named `answer_key`, never tune against it. Built through routes/services with a stubbed LLM plus seeded conclusions so review/report screens can be walked. Prior released assessment; DPDPA+ISO and NIST-only assessments; image, xlsx and stale files (xlsx rejected until S6, which shows the gap). Exit: owner walks the unseen screens in (c).
- **S2 Rules + split decision** (docs and macros only): type scale, done state, one primary action, completion toast/checkmarks; owner signs off split shape.
- **S3 Scope merge + remove gate** (structure only): question types, shared facts, per-framework blocks; delete wizard; human labels; period/cut-off at Scope; land on Scoping after create; validation id mapping. Exit: `lint_pack` clean on counts; held-out validation re-run.
- **S4 RFI stage** (after S3): stage machine (skippable); suggested + selected items; Send = generate + issue; item status + evidence link tables; post-send received/pending/request-more on Evidence; "Run desk review" moves to Evidence.
- **S5 Questionnaire layout + design/operating view** (after S2, S4). Layout is certain. The design/operating view is OPEN (see Owner direction): start from path 1 or 2, not the data-model split.
- **S6 Evidence engine:** F1 XLSX/CSV + OCR (parallel from S2); F2 dates/stale (after S3); F3 re-map (after S4).
- **S7 MoM** (after S5).
- **S8 Unseen-screen fixes** from the S1 walkthrough (review/release/findings consolidation).
- **S9 KPMG content** (scope and RFI wording) once samples arrive.

**Parallelism:** S0, S1, S2 and S6-F1 run together on disjoint files. S3 and S4 both touch `web.py` and scope partials: run in sequence.

## (f) Open questions for the owner
1. Is the split needed at all, or is a side-by-side / derived view enough (see Owner direction)? Only if a real split is chosen: do documents still pre-fill the operating answer, or only the design result?
2. Can you share 5-10 KPMG scope questions and one RFI now, even redacted?
3. Held-out validation: retire gaps that trace to context answers, or map those answers into scope?
4. Can the first RFI be sent as export only (no client link), and can the RFI stage be skipped?
5. Remove the effort-derived budget band from the PDF?
6. Merge Queue and Conclusions; auto-draft findings from approved gaps?
7. Retire the per-PR guard tests?
8. Where do meeting notes live: per domain-owner session or per questionnaire section?
9. The flow doc's Follow-ups rows (generate after analysis) contradict decision B (inline). Rewrite them to match B?
