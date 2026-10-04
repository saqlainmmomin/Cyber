# Yozora S5: Assessment Overview, Scope, Questionnaire, pre-fill from documents

**Rewritten:** 2026-10-03 (replaces the 2026-10-01 template). **Owner:** Codex builds; Claude reviews every diff and screenshot before merge; Saqlain merges. **Depends on:** S1 and S2 merged; S4 recommended (engagement tabs). PR #99 for assessment stage and pre-fill freshness.
**Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (work in your own git worktree of it, one branch per slice, named `codex/yozora-s5-...`). Paths below are relative to your worktree root. The specs below exist on `main` once the docs PR for this series has merged; until then branch from `claude/yozora-slice-handoffs`.

**Read first, in this order:** `docs/product/yozora-design-system.md` (the design guide), `docs/product/yozora-fidelity-gate.md`, `docs/product/2026-10-01-app-design-mockups/screens/IA-SPEC.md`, `docs/product/yozora-migration-map.md` (rows for this slice), then the mockups listed under Screens (serve them with `python3 -m http.server` from the repo root and open `/docs/product/2026-10-01-app-design-mockups/screens/<file>?state=<name>` and `&dark`). Background if you need it: `tasks/agent-ownership.md`, `CLAUDE.md`.

## Goal

Rebuild the assessment shell and the three tabs that collect information: Overview (the stepper and framework cards), Scope, and Questionnaire including the context steps, screening, follow-ups, section questions and the pre-fill from documents (desk review) that now starts from the Questionnaire tab. After this slice the assessment tab row is the five-tab row of the IA.

## Definition of done

- Every state under Screens matches its baseline at the thresholds, light and dark, 1440 and 1024.
- The tab row is Overview, Scope, Questionnaire, Review, Report (macro from S2). There is no Documents tab in the row; the old `?tab=documents` URL keeps rendering the old documents content until S6 turns it into a redirect (see Notes).
- The Overview shows the five-stage stepper (Scope, Evidence, Questionnaire, Review, Report) driven by the stage service, and the Evidence stage links to `/engagements/{engagement_id}/evidence?assessment={assessment_id}` once S6 has landed.
- Pre-fill runs from the Questionnaire tab and its results feed the pre-filled answers; the `desk-review-area` target and every `hx-*` of the desk review partials still work.
- Screening copy only appears when DPDPA is in scope.
- Must-keep ids, `hx-*` and `data-*` unchanged; tests updated deliberately.

## Screens

Mockups are in `docs/product/2026-10-01-app-design-mockups/screens/`. Match every state listed; the state names are the `?state=` values on the mockup.

| Mockup | States to match |
|---|---|
| `b3-hub.html` | `default`, `empty`, `evidence`, `questionnaire`, `report` (next-step variants), `loading`, `error`, `archived`; plus `?state=prefill`. |
| `b3-scope.html` | `default`, `error`, `saving`, `edit`. |
| `b3-scope-complete.html` | `default`, `iso` (ISO 27001 scope), `loading`, `error`. |
| `b3-questionnaire.html` | `prefill`, `prefilling`, `default`, `context`, `screened`, `noscreen`, `error`, `running`, `complete`; also `?state=findings`. |
| `b3-screening-form.html` | `default`, `loading`, `error`, `complete`; also `?state=screened`. |
| `b3-context-complete.html` | `default`, `generating`, `error`. |
| `b3-question-step.html` | `org`, `data`, `data-yes`, `last`, `saving`, `error`. |
| `b3-followups.html` | `loaded`, `loading`, `error`, `none`. |
| `b3-sections.html` | `default`, `saved`, `loading`, `empty`, `error`. |
| `b3-section-questions.html` | `default`, `errors`, `saved`, `loading`. |
| `b4-desk_review.html` | `ready`, `running`, `findings`, `rerun`, `error`: pre-fill from documents, Assessment / Questionnaire / Pre-fill from documents. |

## Templates, routes and view functions in scope

Routes were found by grepping `app/routers/` for each template (helper functions are traced to their routes). Verify with `grep -rn '<template>' app` before relying on a row; if a row is wrong, fix the migration map in your PR.

| Template | Served by (method path, function) |
|---|---|
| `pages/assessment.html` | `GET /assessments/{assessment_id}` `app/routers/web.py::assessment_detail` |
| `partials/context_complete.html` | `GET /assessments/{assessment_id}/context/block/{block_index}` `app/routers/web.py::get_context_block` |
| `partials/followup_questions.html` | `POST /assessments/{assessment_id}/questionnaire/followup` `app/routers/web.py::generate_followup_questions` |
| `partials/framework_tabs.html` | included by `pages/assessment.html` |
| `partials/question_step.html` | `GET /assessments/{assessment_id}/context/block/{block_index}` `app/routers/web.py::get_context_block` |
| `partials/questionnaire_sections.html` | `GET /assessments/{assessment_id}/questionnaire/sections` `app/routers/web.py::get_questionnaire_sections_web` |
| `partials/questionnaire_tab.html` | included by `pages/assessment.html` |
| `partials/scope_complete.html` | included by `partials/scope_tab.html` |
| `partials/scope_form.html` | included by `partials/scope_tab.html` |
| `partials/scope_tab.html` | included by `pages/assessment.html` |
| `partials/screening_form.html` | `GET /assessments/{assessment_id}/screening` `app/routers/web.py::screening_form`<br>`POST /assessments/{assessment_id}/screening/submit` `app/routers/web.py::submit_screening` |
| `partials/section_questions.html` | `GET /assessments/{assessment_id}/questionnaire/section/{section_id}` `app/routers/web.py::get_section_questions` |
| `partials/section_saved.html` | `POST /assessments/{assessment_id}/questionnaire/save` `app/routers/web.py::save_questionnaire_responses` |
| `partials/status_timeline.html` | included by `pages/assessment.html` |
| `partials/desk_review_error.html` | `GET /assessments/{assessment_id}/desk-review-status` `app/routers/web.py::desk_review_status_web` |
| `partials/desk_review_findings.html` | `GET /assessments/{assessment_id}/desk-review-status` `app/routers/web.py::desk_review_status_web` |
| `partials/desk_review_ready.html` | `GET /assessments/{assessment_id}/desk-review-status` `app/routers/web.py::desk_review_status_web` |
| `partials/desk_review_running.html` | `GET /assessments/{assessment_id}/desk-review-status` `app/routers/web.py::desk_review_status_web`<br>`POST /assessments/{assessment_id}/run-desk-review` `app/routers/web.py::run_desk_review_web` |

## Must-keep ids, `hx-*` and `data-*`

Copied from the templates as they are today (checked against `docs/product/yozora-migration-map.md`). A migration may restyle and move these but not rename, drop or re-target them. If markup must change so that one cannot stay, stop and ask.

- `pages/assessment.html`: data-* `data-archived-banner`
- `partials/context_complete.html`: none.
- `partials/followup_questions.html`: none.
- `partials/framework_tabs.html`: ids `framework-panel`; hx-target `#framework-panel`; hx-swap `innerHTML`; hx-verbs `hx-get /assessments/{{ assessment.id }}/tab/{{ framework.id }}`
- `partials/question_step.html`: ids `context-form-{{ block_index }}`, `previous-answers`; hx-target `#context-wizard`; hx-swap `innerHTML`; hx-verbs `hx-get /assessments/{{ assessment_id }}/context/block/{{ block_index + 1 }}`, `hx-get /assessments/{{ assessment_id }}/context/block/{{ block_index - 1 }}`, `hx-post /assessments/{{ assessment_id }}/context/save`; data-* `data-depends-on`, `data-depends-value`
- `partials/questionnaire_sections.html`: ids `section-content`; hx-target `#section-content`; hx-swap `innerHTML`; hx-verbs `hx-get /assessments/{{ assessment_id }}/questionnaire/section/{{ section.section_id }}`, `hx-get /assessments/{{ assessment_id }}/questionnaire/section/{{ sections[0].section_id }}`; data-* `data-collapsible-section`, `data-section`, `data-stat-answered`, `data-stat-awaiting-confirmation`
- `partials/questionnaire_tab.html`: ids `analysis-area`, `context-wizard`, `questionnaire-content`, `screening-body`, `screening-section`; hx-target `#analysis-area`, `#screening-body`; hx-swap `innerHTML`; hx-verbs `hx-get /assessments/{{ assessment.id }}/context/block/0`, `hx-get /assessments/{{ assessment.id }}/questionnaire/sections`, `hx-get /assessments/{{ assessment.id }}/screening`, `hx-post /assessments/{{ assessment.id }}/run-analysis`; data-* `data-screening-unavailable`, `data-shortcut-scope`
- `partials/scope_complete.html`: data-* `data-rfi-link`
- `partials/scope_form.html`: data-* `data-scope-group`
- `partials/scope_tab.html`: none.
- `partials/screening_form.html`: ids `screening-indicator`; hx-target `#screening-section`; hx-swap `innerHTML`; hx-verbs `hx-post /assessments/{{ assessment_id }}/screening/submit`
- `partials/section_questions.html`: ids `followup-indicator-{{ q.id }}`, `followup-{{ q.id }}`, `question-{{ q.id }}`; hx-target `#followup-{{ q.id }}`, `#section-content`; hx-swap `innerHTML`; hx-verbs `hx-post /assessments/{{ assessment_id }}/questionnaire/followup`, `hx-post /assessments/{{ assessment_id }}/questionnaire/save`; data-* `data-pre-filled`, `data-prefill-badge`, `data-progress-counter`, `data-question-card`, `data-question-index`, `data-question-name`, `data-questionnaire-form`, `data-required-question`, `data-save-indicator`, `data-section-header`, `data-section-questionnaire`, `data-validation-summary`
- `partials/section_saved.html`: none.
- `partials/status_timeline.html`: none.
- `partials/desk_review_error.html`: hx-target `#desk-review-area`; hx-swap `innerHTML`; hx-verbs `hx-post /assessments/{{ assessment_id }}/run-desk-review`
- `partials/desk_review_findings.html`: hx-target `#desk-review-area`; hx-swap `innerHTML`; hx-verbs `hx-post /assessments/{{ assessment_id }}/run-desk-review`; data-* `data-desk-review-failed-frameworks`
- `partials/desk_review_ready.html`: ids `dr-spinner`; hx-target `#desk-review-area`; hx-swap `innerHTML`; hx-verbs `hx-post /assessments/{{ assessment_id }}/run-desk-review`
- `partials/desk_review_running.html`: hx-swap `outerHTML`; hx-verbs `hx-get /assessments/{{ assessment_id }}/desk-review-status`

## Build notes

**Assessment shell.** `assessment_detail` (`GET /assessments/{assessment_id}`, `app/routers/web.py`) renders `pages/assessment.html` with `tab` in scope, documents, questionnaire, report. Change it to tabs overview, scope, questionnaire, and keep `report` rendering as today (S7 restyles its content); Review links to `/assessments/{id}/review-queue`. Replace the hand-built `timeline_steps` list and `partials/status_timeline.html` with the stepper macro fed by `assessment_stage.stage` (PR #99). Remove Documents from the tab row, but leave `?tab=documents` rendering `partials/documents_tab.html` unchanged by URL until S6, which owns the replacement and turns the URL into a 303 to the engagement Evidence inventory filtered to the assessment. Keep `data-archived-banner` and the `framework` and `view` query parameters; the `view` combined mode is not designed (no combined cross-framework view), so ignore `view=combined` visually and do not offer it.

**Framework cards on the Overview.** `partials/framework_tabs.html` (id `framework-panel`, HTMX `GET /assessments/{assessment_id}/tab/{framework_id}`, swap `innerHTML`) wraps `partials/framework_panel.html`, which S7 owns as the per-framework content. In this slice restyle the tab strip and keep the target; the panel body restyle is S7. Scores are never combined across frameworks; the ring is neutral.

**Pre-fill from documents.** The desk-review partials (`desk_review_ready`, `desk_review_running`, `desk_review_findings`, `desk_review_error`) are returned by `GET /assessments/{assessment_id}/desk-review-status` and `POST /assessments/{assessment_id}/run-desk-review` into `#desk-review-area`. The area now lives on the Questionnaire tab (`b3-questionnaire` pre-fill card). Move the `desk-review-area` container from `partials/documents_tab.html` (S6 deletes that file) to `partials/questionnaire_tab.html`; the old documents content then has no desk-review block. The freshness copy ("5 documents ready to pre-fill", "3 new documents since the last pre-fill") comes from `app/services/prefill_freshness.py` (PR #99). `b4-desk_review.html` is the results page; its route is the same status endpoint rendered as the `findings` state.

**Questionnaire tab.** `questionnaire_tab.html` holds the screening body, context wizard (`#context-wizard`, steps from `GET /assessments/{assessment_id}/context/block/{block_index}`), sections (`#section-content`) and the analysis area (`#analysis-area`; the analysis partials are S7). Answer scale labels: Fully implemented, Partially implemented, Planned, Not implemented, Not applicable; the stored values stay as they are, only labels change. Control codes in small muted text.

**Scope.** `GET /assessments/{assessment_id}/scope` and `POST /assessments/{assessment_id}/scope/save`; `partials/scope_tab.html` includes `scope_form.html`; `scope_complete.html` is the confirmation. Keep `data-scope-group` and `data-rfi-link` (the RFI link now goes to the engagement Evidence Requests view for this assessment).

**Screening.** DPDPA only. `screening_form.html` is rendered into `#screening-section` by `GET /assessments/{assessment_id}/screening` and `POST .../screening/submit`. Keep `screening-indicator`. The `noscreen` state shows when DPDPA is not in scope and must not mention DPDPA.

## Backend dependency

PR #99, https://github.com/saqlainmmomin/Cyber/pull/99, carries the server-side work for the redesign; its spec is `tasks/handoffs/2026-10-03-yozora-backend-features.md` on branch `claude/yozora-backend-features`. **Do not re-specify or re-implement it here.** At the time this handoff was written #99 held only its spec (no code), so this file names the planned modules from that spec: if #99 has merged by the time you start, read the real function names from the code and use those; if it has not, follow the 'if not merged' instruction in the Build notes.

PR #99: `app/services/assessment_stage.py` (`stage(db, assessment)`: stage, progress note, next-step label and target), `app/services/prefill_freshness.py` (available document count and count added since the last completed desk review). No new routes.

## Tests

**Existing tests that exercise this slice** (route calls matched against this slice's routes, plus tests that name its templates). Run them first and again after each template change.

| Test file | Calls to this slice's routes | Mentions its templates |
|---|---|---|
| `tests/test_p5_4_adaptive_ucc_questionnaire.py` | 14 | 3 |
| `tests/test_p5_3_framework_desk_review.py` | 5 | 0 |
| `tests/test_picker_and_scoring_contract.py` | 5 | 0 |
| `tests/test_p5_5_scoping_evidence.py` | 3 | 0 |
| `tests/test_p5_6_rfi_rebuild.py` | 2 | 0 |
| `tests/test_retention.py` | 2 | 0 |
| `tests/test_longitudinal_demo.py` | 1 | 0 |
| `tests/test_p6_0f_dpdpa_followups.py` | 0 | 1 |
| `tests/test_report_snapshots.py` | 0 | 1 |
| `tests/test_white_label.py` | 1 | 0 |

Strings such as `text-amber-700` are Tailwind classes that a test pins; the redesign removes Tailwind from the page, so those tests must be rewritten to assert the `data-*` attribute or the visible text instead, and the change listed in the PR.

**Asserted strings likely to change.** These literals appear in `assert ... in ...` lines of the tests above and also verbatim in this slice's templates today; if a restyle changes or removes one, edit the test deliberately and list the change in the PR description (old string, new string, reason).

- "Cross-border transfers": test_p5_5_scoping_evidence.py:442, test_p5_5_scoping_evidence.py:455, test_p5_5_scoping_evidence.py:462, test_p5_5_scoping_evidence.py:476
- "SDF obligations": test_p5_5_scoping_evidence.py:444, test_p5_5_scoping_evidence.py:455, test_p5_5_scoping_evidence.py:462, test_p5_5_scoping_evidence.py:476
- "Children's data": test_p5_5_scoping_evidence.py:443, test_p5_5_scoping_evidence.py:455, test_p5_5_scoping_evidence.py:462, test_p5_5_scoping_evidence.py:481
- "Third-party processors": test_p5_5_scoping_evidence.py:455, test_p5_5_scoping_evidence.py:462, test_p5_5_scoping_evidence.py:481, test_p5_5_scoping_evidence.py:489
- "ISO 27001": test_picker_and_scoring_contract.py:180, test_picker_and_scoring_contract.py:259, test_picker_and_scoring_contract.py:300
- "Live PDF": test_p5_6_rfi_rebuild.py:909, test_report_snapshots.py:800
- "Statement of Applicability": test_p5_5_scoping_evidence.py:475, test_p5_5_scoping_evidence.py:480
- "proposed as likely not applicable": test_p5_5_scoping_evidence.py:447, test_p5_5_scoping_evidence.py:456
- "Assessment Scope": test_p5_5_scoping_evidence.py:494
- "Evidence Request": test_p5_5_scoping_evidence.py:445
- "Red Flags": test_p5_3_framework_desk_review.py:780
- "Start screening": test_p5_4_adaptive_ucc_questionnaire.py:921
- "out of scope": test_p5_4_adaptive_ucc_questionnaire.py:904

**Page text asserted by tests that fetch this slice's routes** (not necessarily from this slice's own templates; the test may be reading text that comes from an included partial or the shell). Check each one when you restyle the page it comes from.

- "Terms hide the choice": test_p5_3_framework_desk_review.py:480, test_p5_3_framework_desk_review.py:503, test_p5_3_framework_desk_review.py:504
- "(affects CH2.NOTICE.1, CH2.CONSENT.1)": test_p5_3_framework_desk_review.py:501
- "Confirm reuse": test_longitudinal_demo.py:273
- "Declining records nothing.": test_longitudinal_demo.py:276
- "Eligible for permanent purge on or after": test_retention.py:671
- "ISO signal": test_p5_3_framework_desk_review.py:525
- "Momin &amp; Co": test_white_label.py:102
- "No evidence from earlier assessments is waiting for confirmation.": test_longitudinal_demo.py:306
- "Red Flags (1)": test_p5_3_framework_desk_review.py:512
- "Related: CH2.NOTICE.1, CH2.CONSENT.1": test_p5_3_framework_desk_review.py:513
- "Scope answer: fully remote with no premises.": test_p5_5_scoping_evidence.py:449
- "Signal detected": test_p5_3_framework_desk_review.py:493
- "Statement of Applicability (current version)": test_p5_5_scoping_evidence.py:446

**New tests to add:**

- The assessment tab row has exactly Overview, Scope, Questionnaire, Review, Report and no Documents.
- The stepper renders five stages in order; only on the Overview.
- Screening copy absent when DPDPA is not in scope.
- `#desk-review-area` is on the Questionnaire tab and absent from the Overview.

## File-set guard

Many tests are scope guards: they diff the branch against `main` and fail when a file outside an allow-list changes (the P6-2b scenario 11 guard in `tests/test_p6_2b_dpdpa_criteria.py`, the P6-9 file-set guard in `tests/test_p6_9_file_set.py`, and several older `:(exclude)` guards). They were written for earlier PRs and are stale for this one. **Never delete or weaken a guard.** Add a scoped allowance instead, the way `tests/p6_8_v3a_paths.py` does for V3-A:

1. S1 creates `tests/yozora_paths.py` with one tuple per slice (`YOZORA_S1_PATHS`, ...) and `YOZORA_EXCLUDES = [f":(exclude){p}" for p in ...]` over all tuples. Each later slice adds its own tuple (every file it adds or changes outside `docs/product/` and `design/`) to that module.
2. Run the full suite. For each guard that fails on your files, splat `*YOZORA_EXCLUDES` into its pathspec list (or import the tuple into its allow-list), exactly as `V3A_EXCLUDES` is imported by `tests/test_p5_6_rfi_rebuild.py`. Add a comment `# Yozora per-PR allowance`.
3. Keep this slice's handoff file and `YOZORA_DESIGN_FILES` allowed (already done for `tasks/handoffs/2026-10-01-yozora-s*-handoff.md`).
4. List every guard you touched in the PR description.

**This slice's `YOZORA_S5_PATHS` starts as:**

- `app/templates/pages/assessment.html`
- `app/templates/partials/context_complete.html`
- `app/templates/partials/followup_questions.html`
- `app/templates/partials/framework_tabs.html`
- `app/templates/partials/question_step.html`
- `app/templates/partials/questionnaire_sections.html`
- `app/templates/partials/questionnaire_tab.html`
- `app/templates/partials/scope_complete.html`
- `app/templates/partials/scope_form.html`
- `app/templates/partials/scope_tab.html`
- `app/templates/partials/screening_form.html`
- `app/templates/partials/section_questions.html`
- `app/templates/partials/section_saved.html`
- `app/templates/partials/status_timeline.html`
- `app/templates/partials/desk_review_error.html`
- `app/templates/partials/desk_review_findings.html`
- `app/templates/partials/desk_review_ready.html`
- `app/templates/partials/desk_review_running.html`
- `app/routers/web.py`
- plus every test, CSS, JS and fixture file you add or change.

**Guards found today that name this slice's files** (expect these to need the allowance; there may be more):

- `tests/test_longitudinal_demo.py` names `app/routers/web.py`
- `tests/test_p5_4_adaptive_ucc_questionnaire.py` names `app/templates/partials/questionnaire_sections.html`, `app/templates/partials/questionnaire_tab.html`, `app/templates/partials/screening_form.html`
- `tests/test_p6_3a_grounding.py` names `app/routers/web.py`
- `tests/test_p6_7_requirement_card.py` names `app/routers/web.py`
- `tests/test_p6_7b_add_to_rfi.py` names `app/routers/web.py`
- `tests/test_p6_8_b2_docx_xlsx.py` names `app/routers/web.py`
- `tests/test_p6_8_board_report_v2.py` names `app/routers/web.py`
- `tests/test_p6_9_file_set.py` names `app/routers/web.py`
- `tests/test_p6_nist_csf2_alignment.py` names `app/routers/web.py`

## Screenshot gate

Use the harness from S1 (`design/harness/README.md`). Render each screen listed above in every state, light and dark, at 1440 and 1024. Baselines are the approved mockups rendered at the same viewport with `?state=<name>` and `?dark`, saved as `design/baselines/<screen>-<state>-<theme>-<width>.png` (S1 defines the exact naming; include the state in the name when the screen has several). Candidates use seeded demo data (the fictional Meridian Ledger Technologies, Loomwire Labs and Kestrel Advisory companies from the mockups) with the clock frozen and fonts vendored.

Thresholds from the fidelity gate: colour tolerance 0.1 (pixelmatch); fail above **0.4%** differing pixels on app screens and **0.2%** on `/design`; fail on any single changed region over 40x40 px regardless of the total. Mask dynamic regions with `data-visual-mask`. Loosening a threshold needs a written reason in the PR.

In the PR, post for each screen and state: the baseline, the candidate and the diff image side by side, plus the differing-pixel percentage. Saqlain sees these before merge (gate 4). CI green is necessary, not sufficient.

## Dependency order

S1 shell, then S2 component layer and `/design`, then S3 to S8 (S3 and S4 first; S5, S6 and S7 can run in parallel worktrees only if they touch no shared template; S8 after S6 and S7), then S9 system states, dark and mobile pass. This is slice **S5**.

## Stop and ask

Stop and write the question in this file's Results section (and tell the orchestrating session) if:

- a visual detail is in neither the design guide nor the approved mockup;
- two mockups disagree;
- a must-keep id, `hx-*` or `data-*` cannot be kept;
- a mockup shows an action with no route behind it that this file does not cover;
- the work needs a model, migration, prompt, scoring or PDF change.
- If the stage service returns a next step the Overview mockup has no variant for, stop and ask.
- Do not change desk review logic or prompts.

Do not invent. Do not touch `validation/companies/*/answer_key.json`. No attribution in commits.


## Rules that apply to every slice

- **Source of truth.** If this file, the design guide and a mockup disagree, the approved mockup wins for what the screen looks like, the application code wins for what the route does, and you stop and ask when they conflict (see Stop and ask).
- **Reviewer-name rule.** The designs assume a signed-in user and show no name field. The app has no auth until Track 4, so every route that needs a reviewer or consultant name keeps its temporary input (`reviewer-name` and similar ids). Restyle the input; do not remove it, do not pre-fill it with a real person, and do not show it in states where the mockup has no matching action. Track 4 deletes these fields.
- **Framework copy is conditional.** DPDPA, ISO 27001 and other framework names appear only where that framework is in scope for the assessment. Screening is DPDPA only. Scores are never combined across frameworks; the score ring is neutral.
- **One primary per state.** At most one visible `.btn.primary` in any page state, and none in a state with no real action (never a disabled primary).
- **Vocabulary.** Evidence status: Scanning, Available, Rejected, Out of date. Priority: Do first, Next, Planned, Backlog (never numbers). Answers: Fully implemented, Partially implemented, Planned, Not implemented, Not applicable. Control codes in small muted text in lists. Sentence case, no uppercase, no numbered or lettered headings, dates as 15 Oct 2026.
- **Never touch** `validation/companies/*/answer_key.json`, scoring, the analyzer, prompts, or the PDF code paths. All PDF text goes through `S()`. These slices change templates, CSS, small view code and tests.
- **Commits.** One logical change per commit, no attribution lines of any kind, no co-author trailer. Do not merge; Saqlain merges.
- **Python.** Python 3.13 (`python3.13 -m venv .venv`); Homebrew 3.14 breaks Jinja2. Run the full suite before opening the PR and paste the summary line into Results.

## Results

Implemented the S5 assessment shell, Scope, Questionnaire, context/screening/follow-up flows, and desk-review pre-fill surface.

### Built

- Replaced the assessment tab row with Overview, Scope, Questionnaire, Review, and Report. The Review tab uses `/assessments/{id}/review-queue`; `NAV_ITEMS` was not changed.
- Wired the Overview stepper and Overview CTA to `assessment_stage.stage()`. Every stage-service outcome maps to an approved `b3-hub` state: scope → `empty`; evidence/upload → `evidence`; evidence/pre-fill → `questionnaire`; evidence/running → `loading`; questionnaire (continue, run analysis, or running) → `questionnaire`; review → `default`; report (release, board-report generation, or complete) → `report`; assessment error → `error`.
- Kept the Evidence stepper link at `/assessments/{id}?tab=documents`, and kept the `?tab=documents` rendering branch unchanged. The post-scope default is now Overview.
- Moved the live `desk-review-area` HTMX target to `questionnaire_tab.html` while leaving `documents_tab.html` untouched. Its route, controls, indicators, retry, rerun, findings, and target wiring remain live.
- Used `prefill_freshness.freshness()` for document/pre-fill copy and real desk-review findings, coverage, evidence, and framework names. The Scope RFI link remains `/assessments/{id}/rfi`; the engagement Evidence Requests destination is deferred to S8 because that view does not exist yet.
- Restyled the assessment Overview engagement context, retaining the AWS evidence link, retention include, magic links, and `data-assessment-identity`. Only the S7-owned framework panel body is behind `data-visual-mask`; framework tab HTMX contracts remain intact.
- Added `design/harness/seed_s5.py`, importing S4 builders and `FROZEN_NOW` without editing either prior seed. It creates Meridian Ledger Technologies, Loomwire Labs, and Kestrel Advisory fixtures, real legacy documents for the app's `analysis_documents()` reader, real questionnaire responses, and stamps Alembic `head` after `create_all`.

### Seed state production

The harness validated all **59** S5 states. **32** use deterministic database data. **27** are marked `preview-state` for the orchestrator's mockup/state overlay because they represent transient or interaction-only states: `b3-hub` empty/loading/error; `b3-scope` error/saving; `b3-scope-complete` loading/error; `b3-questionnaire` prefilling/error/running; `b3-screening-form` loading/error; `b3-context-complete` generating/error; `b3-question-step` saving/error; `b3-followups` loading/error; `b3-sections` loading/empty/error; `b3-section-questions` errors/saved/loading; and `b4-desk-review` running/rerun/error. This follows the existing S4 harness state-overlay convention; the partial-only screens use the separate `PREVIEW_PAGES` fixtures listed below.

The seed smoke check reported `validated 59 S5 states`, `alembic: head`, and the frozen clock `2026-09-30T12:00:00+00:00`. Stage smoke reached real branches for no-document evidence, pre-fill-ready evidence, partial questionnaire, review, released report, and analysis loading. Partial-only S5 screens also have registered `PREVIEW_PAGES` fixtures for their state URLs below.

### Screenshot gate

| Coverage | Result |
|---|---|
| 59 S5 states × light/dark × 1440/1024 | Not run in this environment; server and browser/Chromium are unavailable. The orchestrator owns the pixel gate and percentage report. |

### Tests and guard changes

- Added `tests/test_yozora_s5.py` for the five-tab row, five-stage stepper, legacy documents URL, live Questionnaire desk-review target, Overview engagement context, and non-DPDPA screening copy.
- Updated the intentional copy assertion from `Evidence Request` to `Evidence request` for sentence case.
- Updated the non-DPDPA page assertion from the DPDPA-specific screening message to `Screening is not available for this assessment.` and asserted that `DPDPA` and `Start screening` are absent. The screening endpoint's existing real message remains covered separately.
- Added `YOZORA_S5_PATHS` to `tests/yozora_paths.py` and `YOZORA_EXCLUDES`, with the required `# Yozora per-PR allowance` comment. Updated only the stale guard allowances in `tests/p6_10_support.py`, `tests/test_longitudinal_demo.py`, `tests/test_p6_7_requirement_card.py`, `tests/test_p6_7b_add_to_rfi.py`, `tests/test_p6_8_b2_docx_xlsx.py`, `tests/test_p6_8_board_report_v2.py`, `tests/test_p6_8_v3a_data_capture.py`, and `tests/test_p6_9_file_set.py`. No guard was removed or weakened.

Available verification:

```text
122 passed — focused S5, adjacent Yozora, longitudinal, and regression tests
validated 59 S5 states; database=32; preview-state=27
Python compile checks passed; git diff --check passed
```

The full pytest collection is blocked in this environment by missing optional dependencies `botocore.stub` and `pptx`; the focused S5 and adjacent regression tests run successfully. The browser pixel gate was not run here; the orchestrator should run it in its provisioned environment.

The requested commit could not be created: this worktree's Git metadata is at `/Users/saqlainmomin/dpdpa-gap-tool/.git/worktrees/cyberassess-yozora-s5`, outside the writable workspace. A named-path `git add` failed with `Unable to create .../index.lock: Operation not permitted`; no files were staged, pushed, or merged.

### Decisions and open questions

- `documents_tab.html` has no diff, as required for the parallel S6 slice. `NAV_ITEMS` was not changed; partial-only S5 states are registered in `PREVIEW_PAGES`.
- The S4 engagement-context block stays on the assessment Overview until the later S8 destination exists; magic links remain masked.
- No stage-service variant lacked an approved `b3-hub` state, so no implementation question is outstanding.
- No visual percentages are claimed because the required server/browser gate could not run in this environment.

### Review fixes

- Restored all S5 fixture imports (`engine`, `db_path`, `upload_root`, and `_register_frameworks`), added the engagement-linked Overview HTTP smoke test, and kept the Overview engagement context variables required by retention, magic links, client uploads, and the AWS evidence link. The single-assessment engagement redirect now lands on `?tab=overview`; non-Overview tabs do not call `assessment_stage.stage()`.
- Moved the 46 S5 pattern rules into `design/yozora-patterns.css` and regenerated `app/static/css/yozora-patterns.css`; `tokens_tool.py check` is clean. The remaining source classes are justified by the approved mockups: `stack-l`, `stack-m`, `cluster-s`, `split-row`, `section-header`, `section-actions`, and `questionnaire-layout` implement the questionnaire two-pane/card spacing; `questionnaire-stats`, `question-*`, `choice-grid`, and `chip-accent`/`chip-warning` implement answer progress, control cards, answer scales, and pre-fill/deep-review markers; `evidence-*` and `quote` implement citations; `alert-error`, `card-muted`, `empty-state*`, and `card-success` implement skipped/error/empty/saved states; `review-row`, `coverage-dist`, and `table-scroll` implement the desk-review findings and coverage views.
- Restored the S4 context block on Overview, kept the S7 framework body behind `data-visual-mask`, rendered hub empty/evidence/questionnaire/loading/error/report/archived states, hid the single-framework empty heading, restored framework and section selection updates, preserved `framework=` across assessment tabs, and aligned sentence-case analysis copy.
- Rendered the no-CTA stage states in the Overview panel (`Pre-fill running`, `Analysis running`, and board-report-generated), carried the approved transient `state=` preview through Scope and Report routes, and kept default routes data-driven.
- Framework chips use the framework registry's real name/version fields; the current definitions therefore render `India DPDPA 2023` and `ISO 27001 2022` in the desk-review ready state, preserving the real names instead of inventing shortened labels from the mockup.
- Moved the pre-fill card before the context branch so it is reachable before and after context; removed the raw “Open status” link; passed freshness into findings; restored coverage rows, evidence `source_location`, section stats, chapter title, and control codes; linked “Upload evidence” to the Documents view; and kept one primary action per live questionnaire state.
- Updated the deterministic seed to “Head office” under Meridian, real five/six-document states, three-of-six review progress, a hub empty assessment, DPDPA-only screening fixtures except `noscreen`, and the mockup filename `b4-desk_review`. Added transient `state=` handling and partial-only preview URLs without replacing default real data.

Intentional test-string changes (old → new — reason):

- `Red Flags (1)` → `Red flags (1)` — sentence case while retaining the visible count.
- `name="answer_CLUSTER_002" value="fully_implemented" class="sr-only" checked` → `name="answer_CLUSTER_002" value="fully_implemented" checked` — the new visible choice markup removed the obsolete `sr-only` class; the saved answer remains checked.
- `name="answer_CH2.CONSENT.1" value="fully_implemented" class="sr-only" checked` → `name="answer_CH2.CONSENT.1" value="fully_implemented" checked` — same intentional markup change for the DPDPA control.
- `assert "DPDPA" not in page.text` for every scenario → an ISO-only branch retaining that assertion plus a mixed-assessment branch asserting `SCREENING_NOT_APPLICABLE_MESSAGE` on the screening fragment — the mixed assessment legitimately includes DPDPA in its framework list.
- Framework-tab request `/assessments/{id}` → `/assessments/{id}?tab=overview` and solo equivalent → `?tab=overview` — framework tabs are an Overview-only mockup element.
- `hx-push-url="/assessments/{id}?tab=questionnaire&amp;framework=iso27001"` → `hx-push-url="/assessments/{id}?tab=overview&amp;framework=iso27001"` — selection is asserted on the Overview where the tabs render.
- `/assessments/{id}?tab=report&amp;framework=iso27001` → `/assessments/{id}/report?framework=iso27001` — the assessment tab row now owns the canonical report route and preserves the framework query.
- `desk-review-status"` → `desk-review-status?surface=questionnaire` — the Questionnaire surface needs its findings action state without changing the b4 desk-review surface.
- `NIST CSF 2.0 baseline gap assessment` → `engagement_b.name` after asserting a `303` Location of `/assessments/{nist_id}?tab=overview` — the single-assessment engagement page intentionally redirects to the assessment Overview, while the test still checks the hierarchy and linked evidence content.

Partial-only preview URLs (each accepts the listed `state` exactly):

- `/design/pages/b3-screening-form?state=default`, `loading`, `error`, `complete`, `screened`.
- `/design/pages/b3-context-complete?state=default`, `generating`, `error`.
- `/design/pages/b3-question-step?state=org`, `data`, `data-yes`, `last`, `saving`, `error`.
- `/design/pages/b3-followups?state=loaded`, `loading`, `error`, `none`.
- `/design/pages/b3-sections?state=default`, `saved`, `loading`, `empty`, `error`.
- `/design/pages/b3-section-questions?state=default`, `errors`, `saved`, `loading`.
- `/design/pages/b4-desk_review?state=ready`, `running`, `findings`, `rerun`, `error`.
