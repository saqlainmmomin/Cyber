# Flow rework plan (S0-S9)

Status: **approved in principle by the owner 2026-10-07; final copy.** Implementation starts with wave 1. Date: 2026-10-07. Base: main at 00f3300, plus the flow doc, owner comments and the review handoff on `claude/stress-test-demo-company-yx20b1`.

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
| P9 | **Remove budget from the report.** The remediation budget band ("under 10k" ... "above 150k") leaves the PDF and is no longer computed. Effort and timeline stay. | S0 |
| P10 | **The RFI stage is skippable** ("Skip RFI, go to evidence"). | S4 |
| P11 | **Meeting notes are per domain: one meeting per domain.** The consultant uploads or pastes the notes for a domain, and suggested answers map onto that domain's questions only. | S7 |
| P12 | **PR #121 closed** as superseded (closed 2026-10-07). | S0, S3 |

### P6 explained: which tests get retired
Two kinds of tests live in `tests/`:
1. **Behaviour tests:** scoring determinism, golden scores, data retention/purge, routes return the right page, the LLM never reads an answer key, and so on. **These stay.** When a slice intentionally changes behaviour (e.g. the stepper gets a sixth "RFI" stage), the test is updated in the same PR to state the new behaviour. That is normal and expected.
2. **File-path guards:** about 16 test files (e.g. `test_p6_9_file_set.py`, `p6_10_support.py`, `tests/yozora_paths.py`, 540 lines) run `git diff main...HEAD` and fail if the branch touches any file outside a frozen allow-list. They were written to stop one past PR (P6-9, Yozora S1, ...) from straying into another's files. They say nothing about whether the app works, and every new slice has to add its file paths to them. **These are the ones retired:** delete the `git diff` checks and `yozora_paths.py`; keep any real behaviour assertions in the same files.

Two guards are not path guards and stay: `test_answer_key_isolation.py` (code never reads `answer_key.json`) and the "every LLM call site is registered" check (`test_remaining_llm_call_sites.py`).

### P2 correction: what the old validation set still does
The owner is right that the old companies don't matter as product data. One thing they still do: they are the only check that **analysis quality didn't get worse** when the text sent to the LLM changes. Two slices change that text: S3 (the context-profile header leaves the analysis prompt) and S6-F2 (the as-of date enters desk-review prompts). The demo company in S1 can't do this job, because it runs on a stubbed LLM.

Plan: no mapping work. Gaps that trace only to context answers stop being detectable, and that's accepted. The validation scripts only get fixed where they would crash. Run the remaining set once before and once after S3 and S6-F2 as a smoke check, never to tune against it. A new held-out company (written by someone other than whoever changes the prompts) is a **separate item, not in this plan**, and replaces the old set when it exists.

### KPMG samples (received 2026-10-07): what they change
Three real pre-engagement sheets (photos; client names withheld, not stored in the repo): one multi-standard sheet (ISO 27001, ISO 42001, ISO 20000, ISO 9001, CMMI, privacy) and two shorter ones (a cyber assessment, and ISO 27001 + 9001), about 75 questions in all.

What they show:
1. **KPMG's "RFI" is our Scope, not our evidence request.** Every row is a question for the client to answer in words ("~1,000", "Yes", "TBD", a cloud provider name, a list of departments). Documents come later. So the flow is: scope questionnaire **sent to the client**, then the evidence RFI. Today our scope is filled in-app by the consultant only.
2. **The shape fits the plan:** a "Common Information" block asked once, then one block per standard. Privacy is one block across GDPR/DPDPA/CCPA, not one per law. This removes the plan's riskiest assumption.
3. **Columns: No. / Track / Question / Client response / Notes from the kickoff meeting (dated).** So each scope answer needs a consultant note beside it.
4. **Answers are often partial:** "TBD", "WIP", "As per scope", approximations like "~10". Scope must allow unanswered/pending items and must not block on them.
5. **Almost everything is free text.** Strict number or structured fields wouldn't survive "~1,000 across sites". This simplifies S3: single-select, multi-select and text only, no `number` type.
6. **About a third of the questions are about the engagement, not the client's controls:** will the consultant draft the policies, run training, do VAPT, run a phishing simulation, coordinate the certification body, the UAR sample size, the timeline, who does remediation. Under the principle "never ask what we won't use", these don't belong in the built-in bank. Consultants can add them as **custom questions** (text, exported, not used by the engine).
7. **Some answers should seed the evidence RFI:** "existing certification? share the certificate and its scope", "existing policies? list them", "risk methodology and last assessment date", "tools deployed (PAM, SIEM, EDR, DLP)". A "Yes" there pre-selects the matching RFI item in S4.

### Decided from the samples (owner confirmed 2026-10-07)
| # | Decision | Slice |
|---|---|---|
| P13 | Scope question types: single, multi, text. No number type. Every scope answer can be left pending ("TBD") without blocking. | S3 |
| P14 | Each scope question has a consultant note field ("notes from kickoff"). | S3 |
| P15 | **Scope can be sent to the client** the same way as the RFI: XLSX export with columns No. / Section / Question / Response / Notes, or the client link. The consultant can also fill it in-app. Importing a filled XLSX back is **not** in this plan; the consultant types the answers in (revisit after S1). | S3 (export), S4 (shares the send mechanism) |
| P16 | Consultants can add custom scope questions (text). They are exported and stored, never fed to scoring or prompts. | S3 |
| P17 | Certain scope answers pre-select RFI items (certificate, policy list, risk methodology, tool list). A mapping table in the framework definitions; no LLM. | S4 |

## Design pass: part of every slice that touches a screen
The owner's top concern: content has to be easy to read, with the important information standing out. Text hierarchy is a deliverable in every slice, not a later polish pass.

- **S2 writes the rules once:** a one-page checklist (below), plus macros. S2 is the only slice that is purely design.
- **Every slice that changes a screen ends with a design pass** on each screen it touches, before the PR opens. The PR includes before/after screenshots (taken on the S1 demo company) and a filled-in checklist for each screen.
- **Checklist (S2 finalises the wording):**
  1. In 3 seconds, can you tell where you are, what's done and what to do next? There's one clearly primary action.
  2. The most important information (status, counts, what's missing) comes first and is the most prominent. Supporting text is smaller and lighter.
  3. No walls of text: lists are scannable, long explanations are collapsed, ids and codes are secondary to human labels.
  4. Completed steps show as done (checkmark / done state). Nothing finishes silently.
  5. Only the frameworks in this assessment appear in the wording.
- This is the "design pass at build" in the two-pass rule. The second pass is the owner's walkthrough before exposure. **No extra polish rounds between them**, and no new pixel-gate tests.
- Screens no slice touches (dashboard, engagement page, settings) get their design pass in S8.

## Who does what (three accounts)
| Lane | Account | Does |
|---|---|---|
| **Orchestrator** | Claude, desktop app (this account) | Writes the handoff for each slice, dispatches Codex, verifies each diff (re-runs tests, reads the change), runs **one** review pass per PR in a Sonnet subagent, opens PRs. Owns the Claude-side design of S3 (wizard deletion, scope model), S4 (stage machine, the two new tables and their purge rules) and S7 (LLM module, unconfirmed-answer gating, prompt safety). |
| **Design + spec** | Claude, second account, run from the terminal | Writes S2 (rules + checklist + macros), the S1 demo company spec (narrative, which documents, which states), and S9 wording. Also reviews Claude-built code, so the builder never reviews their own work. |
| **Builder** | Codex | Implements from handoffs: S0, S1 (seed script + demo files), S6, then S3/S4/S5/S7/S8 builds. Model: `gpt-5.6-luna` at xhigh by default, several runs in parallel in separate worktrees; `gpt-5.6-sol` for S3 and S4 (the riskiest builds) when quota allows. On a usage-limit error: don't retry in a loop. Finish what's done or wait for the reset. |

Demo files (xlsx, a scanned-looking PDF, an image) are generated with plain Python (openpyxl, Pillow), with no image-generation model needed.

## Testing: keep it lean
- Keep: the existing suite, scoring determinism/golden scores, data retention and purge, LLM call-site registration, answer-key isolation, unconfirmed answers never reaching analysis.
- Each slice adds tests only for behaviour that could lose data or change a score silently. No new pixel gates, no file-path guards, no snapshot tests of templates.
- One review pass per PR (Sonnet subagent). A second pass only if the first finds a real bug.
- The owner's click-through is the final gate.

## Slices
Order: **S0a first** (retire the guard tests, a small PR, so later slices don't carry guard allowances). Then S0b, S1, S2 and S6-F1 in parallel (disjoint files). S1's follow-up screens need S0b's follow-up fix merged first; the rest of S1 doesn't wait. Then S3, then S4 (both touch `web.py` and the scope partials, so in sequence). S5 after S2+S4. S7 after S5. S8 after the S1 walkthrough. S9 after S3 (samples received).

### S0 Hotfixes + guard retirement
S0a = guard retirement only (first). S0b = everything else.
- **Follow-up storage (verified bug).** The follow-up textarea posts free text into `QuestionnaireResponse.answer`, which has a CHECK constraint allowing only the 5 answer values (`web.py:2671-2695`, `models/questionnaire.py:13-16`). Every follow-up save fails. Fix: store the free text in `notes` with an empty answer, or a dedicated nullable column; pick whichever needs no CHECK change. Set `cluster_id` for `FU.<cluster>` rows. Follow-ups should survive a reload once answered.
- Gradient: `yozora-components.css:3`, the gradient stretches over document height. Fix with a fixed pseudo-element or `background-attachment: fixed`.
- First-RFI copy (`rfi.html:62`); hide "Live PDF" until released (`assessment_header.html:16-17`); hide greyed-out GDPR/HIPAA/PCI cards (`new_engagement.html`).
- **Remove the budget band (P9):** drop it from the PDF initiative line (`pdf_export.py:1358,1394`) and stop computing it (`_BUDGET_BANDS`, `scoring.py:487-497,540-556,765-777`; `analysis.py:506,821`). The `Initiative.budget_estimate_band` column stays as nullable dead data, with no migration. Old snapshots still render. Check golden/scoring tests for the field and update them in the same PR.
- Retire file-path guards (P6).
- PR #121: closed as superseded (P12). Note CTX.ISO.1-5 as candidate ISO scope items for S3/S9. Its NIST questions repeat NIST.SCP.*.
- **Exit:** one follow-up saves, survives a reload and shows in the workpaper; full suite green.

### S1 Demo company
- `scripts/demo/`: built through the real routes and services with a stubbed LLM, plus seeded conclusions so review/report screens can be walked. Nothing named `answer_key`; this is a walkthrough fixture, not an evaluation set.
- Contents: a prior released assessment (for re-assessment comparison); one DPDPA+ISO assessment and one NIST-only; an image, an xlsx and a stale-dated file (the xlsx is rejected until S6, which shows the gap on purpose).
- **Exit:** the owner walks the unseen screens (follow-ups, analysis, review, conclusions, findings, report, versions, comparison) and leaves comments. Those comments become S8's list.

### S2 Rules (docs + macros only)
- A one-page hierarchy rule: type scale, one obvious next action per screen, a done state for every step (checkmark/toast + stepper tick), how an evidence/RFI item is written (what it is, why it's requested).
- Macros for the done state and the "next step" banner in `app/templates/components/`.
- Rewrite the flow doc's Follow-ups rows to match decision B.
- **Exit:** owner signs off the rule page and checklist. Later slices apply it to the screens they touch (see Design pass), so there's no app-wide restyle pass.

### S3 One scoping flow
- **Delete** the context wizard: `routers/questionnaire.py` context routes, `context_profiler` LLM call, `context_complete`, `question_step`, and status `context_gathered` (stop writing it; old rows still render). `Assessment.context_answers/context_profile` columns stay as dead data, with no migration.
- Remove the questionnaire gate (`questionnaire_tab.html:27-40,69`).
- Scope gets: question types single, multi (rendered as checkboxes; today `scope_form.html:19` renders radios even for multi) and text, with pending allowed (P13); a note per question (P14); custom questions (P16); XLSX export for the client (P15); a **Common information** block asked once (from the samples: legal entity, entities and locations in scope, headcount per site, business functions in scope, existing certifications and their scope, existing documentation status, security tools deployed, cloud providers and hosting locations, data centres and DR sites, outsourced IT/third parties, timeline and driver) followed by per-framework blocks (privacy block = one block for DPDPA); human labels; **assessment period + evidence cut-off** moved here from Conclusions (`report_basis_panel.html:117`).
- Duplicates removed: DPDPA SCP.1/2/3 vs CTX.DATA.4/CTX.RISK.1. Budget question (CTX.INIT.3) goes.
- `risk_tier` stops being an input. Deep-review badges come from desk review "deepened" only.
- After "Start assessment", land on Scoping (`web.py:1339`).
- Validation: per P2, fix scripts only where they crash. Smoke run before/after.
- **Exit:** create → scope → questionnaire opens with no gate; same scope answers drive the RFI; owner walkthrough.

### S4 RFI as a stage
- `assessment_stage.py`: add `rfi` between Scope and Evidence; skippable (P10). Update stepper, hub, dashboard rows, engagement table and Overview action to point at it.
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
- One meeting per domain (P11). On each questionnaire domain: "Add meeting notes" (upload a file or paste text). The notes are stored as an Evidence item, source "interview", tagged with that domain, which gives citations, purge, versioning and workpaper trace for free. A domain can get further notes later (a follow-up meeting) as a new version.
- Suggestions only target that domain's questions.
- New LLM module suggests answers with quotes. Answers land with a new `answer_source` in `UNCONFIRMED_ANSWER_SOURCES`, so nothing reaches analysis until the consultant confirms it (D-P5-F). Registered in the LLM call-site list; covered by the prompt-injection pack.
- **Exit:** upload one domain's demo notes → suggestions with quotes for that domain's questions → confirm → shows as operating answer in S5's view.

### S8 Review, release and report fixes (from the S1 walkthrough)
- Merge Queue + Conclusions (P4); workpaper becomes a link; auto-draft findings (P5).
- Release button lives where the stage says it does (today stage "Release report" goes to a tab with no release button).
- Reviewer name defaults from Settings instead of 13 fields.
- Framework-conditional section refs on conclusions/review queue (today DPDPA refs are hard-coded).
- Report: demote Narrative/Board inputs/Applicability sub-tabs; one primary action per screen.
- Comparison: human labels; match the prior assessment by engagement, not the `company_name` string; add a "Re-assess" entry at setup.
- Design pass on the screens no other slice touched (dashboard, engagement page, settings).
- Exact list comes from the owner's S1 comments.

### S9 KPMG content
- Scope wording from the samples, inside the S3 structure. Content only. Candidate per-framework items (paraphrased):
  - **ISO 27001:** functions, departments, processes, applications and infrastructure in scope; on-prem vs cloud applications, the cloud provider, deployment model; risk methodology, when last reviewed, last risk assessment date and scope; existing ISMS policies and procedures; certification target date. Merge in CTX.ISO.1-5 from closed #121 where they don't duplicate.
  - **DPDPA (privacy block):** functions processing personal data; third parties processing personal data, and how many; countries data is collected from; processing or sharing outside India; transfer mechanisms; where personal data is hosted and backed up; number of applications processing personal data; privacy tooling; data mapping done or not; prior privacy assessments.
  - **NIST CSF:** PAM tool and how many apps are integrated; how user access reviews run (frequency, method, owners, systems covered); SOC tooling and operating model (in-house, hybrid, outsourced); any framework already used to run the security programme; recent SOC/PAM/resilience assessments; third-party risk framework and recent vendor assessments. Check against NIST.SCP.* to avoid repeats.
- Evidence RFI wording: what each item is and why it's asked (S2 rule), plus the P17 seed mapping.

## What gets smaller
Context wizard + profiler LLM call + `context_complete`/`question_step` templates; `context_gathered` status; the questionnaire gate; scope checklist + its PDF/DOCX; ~16 file-path guard tests and `yozora_paths.py`; Queue/Conclusions duplication; 13 reviewer-name fields; greyed roadmap cards. Left alone on purpose: legacy DPDPA-only questionnaire path, the parked v2 pipeline, design preview routers/pixel gates (frozen; no new ones).

## Risks
1. **Sending scope to the client (P15) is new** and widens S3. If S3 gets too big, ship the XLSX export first and the client link in S4 alongside the RFI link. (The earlier risk, that KPMG material wouldn't fit the shape, is retired: the samples match it.)
2. **Removing the context profile changes LLM input** with no held-out set we care about. Mitigation: before/after smoke run on the old set; a new held-out company later.
3. **The stage machine change (S4) touches many consumers.** Done in one slice, with behaviour tests updated in the same PR.
