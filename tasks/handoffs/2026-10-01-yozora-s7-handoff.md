# Yozora S7: Analysis, Review, Report, narrative and board inputs

**Rewritten:** 2026-10-03 (replaces the 2026-10-01 template). **Owner:** Codex builds; Claude reviews every diff and screenshot before merge; Saqlain merges. **Depends on:** S1 and S2 merged; S5 (assessment shell) and S6 (workpaper seg row) recommended first.
**Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (work in your own git worktree of it, one branch per slice, named `codex/yozora-s7-...`). Paths below are relative to your worktree root. The specs below exist on `main` once the docs PR for this series has merged; until then branch from `claude/yozora-slice-handoffs`.

**Orchestrator addenda (4 Oct 2026):** `tasks/handoffs/2026-10-04-yozora-s7-orchestration.md` supersedes the Review inbox and "No mockup" notes below (the inbox shipped in S3; the three screens now have mockups) and sets the S5/S6 dependency order. Where they differ, the addenda win.

**Read first, in this order:** `docs/product/yozora-design-system.md` (the design guide), `docs/product/yozora-fidelity-gate.md`, `docs/product/2026-10-01-app-design-mockups/screens/IA-SPEC.md`, `docs/product/yozora-migration-map.md` (rows for this slice), then the mockups listed under Screens (serve them with `python3 -m http.server` from the repo root and open `/docs/product/2026-10-01-app-design-mockups/screens/<file>?state=<name>` and `&dark`). Background if you need it: `tasks/agent-ownership.md`, `CLAUDE.md`.

## Goal

Rebuild the heart of the review workflow: analysis states, the review queue and requirement card, conclusions and their cards, findings and finding cards, the report tab and release panel, report basis and sign-off, and the three screens that have no mockup yet (narrative, board inputs, recommended-action draft). After this slice the Review menu entry is live.

## Definition of done

- Every state under Screens matches its baseline at the thresholds, light and dark, 1440 and 1024.
- Review sub-views use one `.seg` row: Queue, Conclusions, Findings, Workpaper. Report sub-views: Report, Versions, Applicability (ISO 27001 only).
- `/review` exists and lists assessments with decisions waiting (see Notes). Menu entry Review is `available`.
- Exactly one primary action per state; none in states with no real action.
- Neutral score ring, outcome pills with text labels, fixed severity colours. No combined cross-framework report view.
- Queue keyboard behaviour is unchanged: `j` and `k` move between items (`data-queue-nav` script, `data-queue-keys` hint). The mockup's A, E and X keycap hints on Approve, Edit and Reject do not exist in the app today; see Notes.
- Must-keep ids, `hx-*` and `data-*` unchanged; every listed test updated deliberately.

## Screens

Mockups are in `docs/product/2026-10-01-app-design-mockups/screens/`. Match every state listed; the state names are the `?state=` values on the mockup.

| Mockup | States to match |
|---|---|
| `b5-analysis.html` | `running`, `complete`, `error`, `error-all`, `gate`, `gate-no-override`. |
| `b5-review-queue.html` | `default`, `shared`, `done`, `empty`. |
| `b5-requirement-card.html` | `v2`, `v2-draft`, `contradiction`, `v1`, `none`. |
| `b5-conclusion-card.html` | `pending`, `edit`, `approved`, `edited`, `rejected`, `blocked`, `no-citation`, `superseded`, `locked`, `conflict`, `bulk`. |
| `b5-conclusions.html` | `default`, `legacy-bulk`, `empty`. |
| `b5-review-finding-card.html` | `draft`, `needs-review`, `notes`, `accepted`, `rejected`. |
| `b5-findings.html` | `default`, `create`, `empty`. |
| `b5-finding-card.html` | `open`, `in-progress`, `no-evidence`, `verify`, `verified`, `legacy`, `source-changed`, `migrated`, `add-action`. |
| `b5-report.html` | `released`, `not-released`, `loading`. |
| `b5-no-report.html` | the empty report state. |
| `b5-basis.html` | `empty`, `filled`, `invalid`, `locked`, `saved`. |
| `b5-release.html` | `blocked`, `ready`, `confirm`, `released`, `stale`. |
| `b7-dark-dense.html` | dark mode findings page at density: a check that the dense case holds; also used by S9 for the dark pass. Compare at 1440 dark only. |

## Templates, routes and view functions in scope

Routes were found by grepping `app/routers/` for each template (helper functions are traced to their routes). Verify with `grep -rn '<template>' app` before relying on a row; if a row is wrong, fix the migration map in your PR.

| Template | Served by (method path, function) |
|---|---|
| `components/conclusion_card.html` | `POST /api/assessments/{assessment_id}/conclusions/{conclusion_id}/approve` `app/routers/conclusions.py::approve_conclusion`<br>`POST /api/assessments/{assessment_id}/conclusions/{conclusion_id}/edit` `app/routers/conclusions.py::edit_conclusion`<br>`POST /api/assessments/{assessment_id}/conclusions/{conclusion_id}/reject` `app/routers/conclusions.py::reject_conclusion`<br>`POST /api/assessments/{assessment_id}/conclusions/{conclusion_id}/reopen` `app/routers/conclusions.py::reopen_conclusion`<br>`POST /api/assessments/{assessment_id}/divergence-notes/{conclusion_id}/acknowledge` `app/routers/requirement_review.py::acknowledge_divergence`<br>`POST /api/assessments/{assessment_id}/rfi-requests/{conclusion_id}` `app/routers/requirement_review.py::add_rfi_request`<br>`POST /api/assessments/{assessment_id}/rfi-requests/{conclusion_id}/withdraw` `app/routers/requirement_review.py::withdraw_rfi_request` |
| `components/finding_card.html` | `POST /api/assessments/{assessment_id}/findings/{finding_id}/actions` `app/routers/findings.py::add_action_route`<br>`POST /api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/close` `app/routers/findings.py::close_action_route`<br>`POST /api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/reopen` `app/routers/findings.py::reopen_action_route`<br>`POST /api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/status` `app/routers/findings.py::change_action_status_route`<br>`POST /api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/update` `app/routers/findings.py::update_action_route`<br>`POST /api/assessments/{assessment_id}/findings/{finding_id}/actions/{action_id}/verify` `app/routers/findings.py::verify_action_route` |
| `components/requirement_card_body.html` | included by `components/conclusion_card.html` |
| `pages/conclusions.html` | `GET /assessments/{assessment_id}/conclusions` `app/routers/web.py::conclusions_page` |
| `pages/findings.html` | `GET /assessments/{assessment_id}/findings` `app/routers/web.py::findings_page` |
| `pages/review_queue.html` | `GET /assessments/{assessment_id}/review-queue` `app/routers/requirement_review.py::review_queue_page` |
| `pages/board_inputs.html` | `GET /assessments/{assessment_id}/board-inputs` `app/routers/board_inputs.py::board_inputs_page` |
| `pages/narrative.html` | `GET /assessments/{assessment_id}/narrative` `app/routers/drafting.py::narrative_page` |
| `partials/analysis_complete.html` | `GET /assessments/{assessment_id}/analysis-status` `app/routers/web.py::analysis_status` |
| `partials/analysis_error.html` | `GET /assessments/{assessment_id}/analysis-status` `app/routers/web.py::analysis_status` |
| `partials/analysis_gate_blocked.html` | `POST /assessments/{assessment_id}/run-analysis` `app/routers/web.py::run_analysis_web` |
| `partials/analysis_running.html` | `GET /assessments/{assessment_id}/analysis-status` `app/routers/web.py::analysis_status`<br>`POST /assessments/{assessment_id}/run-analysis` `app/routers/web.py::run_analysis_web` |
| `partials/framework_panel.html` | `GET /assessments/{assessment_id}/tab/{framework_id}` `app/routers/web.py::framework_tab` |
| `partials/no_report.html` | `GET /assessments/{assessment_id}/report-summary` `app/routers/web.py::report_summary` |
| `partials/release_panel.html` | included by `pages/conclusions.html` |
| `partials/remediation_draft.html` | `POST /api/assessments/{assessment_id}/recommended-action-drafts/{conclusion_id}` `app/routers/drafting.py::draft_recommended_action` |
| `partials/remediation_panel.html` | included by `partials/report_summary.html` |
| `partials/remediation_summary.html` | included by `partials/report_summary.html` |
| `partials/report_basis_panel.html` | included by `pages/conclusions.html` |
| `partials/report_summary.html` | `GET /assessments/{assessment_id}/report-summary` `app/routers/web.py::report_summary` |
| `partials/report_tab.html` | included by `pages/assessment.html` |
| `partials/review_finding_card.html` | include or macro only, see including template |

## Must-keep ids, `hx-*` and `data-*`

Copied from the templates as they are today (checked against `docs/product/yozora-migration-map.md`). A migration may restyle and move these but not rename, drop or re-target them. If markup must change so that one cannot stay, stop and ask.

- `components/conclusion_card.html`: ids `conclusion-card-{{ card.conclusion.id }}`; hx-target `#conclusion-card-{{ card.conclusion.id }}`; hx-swap `outerHTML`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/conclusions/{{ card.conclusion.id }}/approve`, `hx-post /api/assessments/{{ assessment.id }}/conclusions/{{ card.conclusion.id }}/edit`, `hx-post /api/assessments/{{ assessment.id }}/conclusions/{{ card.conclusion.id }}/reject`, `hx-post /api/assessments/{{ assessment.id }}/conclusions/{{ card.conclusion.id }}/reopen`; data-* `data-conclusion-card`, `data-state`, `data-version`
- `components/finding_card.html`: ids `action-{{ row.action.id }}`, `finding-{{ view.finding.id }}`; hx-target `#finding-{{ view.finding.id }}`; hx-swap `outerHTML`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/findings/{{ view.finding.id }}/actions`, `hx-post /api/assessments/{{ assessment.id }}/findings/{{ view.finding.id }}/actions/{{ row.action.id }}/close`, `hx-post /api/assessments/{{ assessment.id }}/findings/{{ view.finding.id }}/actions/{{ row.action.id }}/reopen`, `hx-post /api/assessments/{{ assessment.id }}/findings/{{ view.finding.id }}/actions/{{ row.action.id }}/status`, `hx-post /api/assessments/{{ assessment.id }}/findings/{{ view.finding.id }}/actions/{{ row.action.id }}/update`, `hx-post /api/assessments/{{ assessment.id }}/findings/{{ view.finding.id }}/actions/{{ row.action.id }}/verify`; data-* `data-action-history`, `data-action-row`, `data-action-status`, `data-close-control`, `data-finding-card`, `data-finding-origin`, `data-history-action`, `data-reopen-control`, `data-source-approved`, `data-verify-control`
- `components/requirement_card_body.html`: hx-target `#conclusion-card-{{ card.conclusion.id }}`; hx-swap `outerHTML`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/divergence-notes/{{ card.conclusion.id }}/acknowledge`, `hx-post /api/assessments/{{ assessment.id }}/rfi-requests/{{ card.conclusion.id }}`, `hx-post /api/assessments/{{ assessment.id }}/rfi-requests/{{ card.conclusion.id }}/withdraw`; data-* `data-acknowledged`, `data-claim`, `data-claim-link`, `data-client-said`, `data-contradiction`, `data-criteria-source`, `data-criterion`, `data-criterion-result`, `data-divergence-ack-form`, `data-divergence-note`, `data-evidence-shared`, `data-evidence-shows`, `data-missing-evidence`, `data-proposal-reason`, `data-quality-chip`, `data-requirement-card`, `data-requirement-source`, `data-rfi-add-form`, `data-rfi-request`, `data-rfi-request-key`, `data-rfi-request-preview`, `data-rfi-request-status`, `data-rfi-state`, `data-rfi-withdraw-form`, `data-tone`, `data-unsupported-assertion`
- `pages/conclusions.html`: ids `reviewer-name`; data-* `data-count`
- `pages/findings.html`: ids `eligible-{{ row.card.conclusion.id }}`, `reviewer-name`; hx-swap `none`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/findings`; data-* `data-board-inputs-link`, `data-eligible-conclusion`
- `pages/review_queue.html`: ids `reviewer-name`, `{{ entry.card.conclusion.id }}`; data-* `data-conclusion-id`, `data-flags`, `data-queue-group`, `data-queue-index`, `data-queue-item`, `data-queue-keys`, `data-queue-nav`, `data-risk`, `data-shared`, `data-shared-claim`, `data-state`
- `pages/board_inputs.html`: ids `reviewer-name`; hx-swap `none`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/board-inputs/actions/{{ action_view.action.id }}/responsibility`, `hx-post /api/assessments/{{ assessment.id }}/board-inputs/asks`, `hx-post /api/assessments/{{ assessment.id }}/board-inputs/initiatives`, `hx-post /api/assessments/{{ assessment.id }}/board-inputs/observations/{{ view.finding.id }}`; data-* `data-board-action`, `data-board-asks`, `data-board-finding`, `data-board-initiative`
- `pages/narrative.html`: ids `reviewer-name`; hx-swap `none`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/narrative/generate`, `hx-post /api/assessments/{{ assessment.id }}/narrative/{{ section.section_id }}/accept`, `hx-post /api/assessments/{{ assessment.id }}/narrative/{{ section.section_id }}/discard`; data-* `data-finding-ref`, `data-narrative-accept-form`, `data-narrative-blocker`, `data-narrative-dropped`, `data-narrative-section`, `data-narrative-unreleased`
- `partials/analysis_complete.html`: data-* `data-review-conclusions-link`
- `partials/analysis_error.html`: hx-target `#analysis-area`; hx-swap `innerHTML`; hx-verbs `hx-post /assessments/{{ assessment_id }}/run-analysis`; data-* `data-analysis-failed-frameworks`
- `partials/analysis_gate_blocked.html`: ids `override_reason`; hx-target `#analysis-area`; hx-swap `innerHTML`; hx-verbs `hx-post /assessments/{{ assessment_id }}/run-analysis`; data-* `data-completion-gate-blocked`, `data-completion-override-form`
- `partials/analysis_running.html`: hx-swap `outerHTML`; hx-verbs `hx-get /assessments/{{ assessment_id }}/analysis-status`
- `partials/framework_panel.html`: none.
- `partials/no_report.html`: none.
- `partials/release_panel.html`: hx-swap `none`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/release`; data-* `data-release-blockers`, `data-release-form`, `data-release-panel`, `data-release-state`
- `partials/remediation_draft.html`: ids `recommended-action-{{ conclusion_id }}`; hx-target `#recommended-action-{{ conclusion_id }}`; hx-swap `outerHTML`; hx-verbs `hx-post /api/assessments/{{ assessment_id }}/recommended-action-drafts/{{ conclusion_id }}`; data-* `data-recommended-action-field`, `data-remediation-draft`, `data-remediation-draft-button`, `data-remediation-draft-error`, `data-suggested-owner-role`
- `partials/remediation_panel.html`: data-* `data-legacy-remediation`
- `partials/remediation_summary.html`: none.
- `partials/report_basis_panel.html`: hx-swap `none`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/report-basis`; data-* `data-period-locked`, `data-period-recorded`, `data-report-basis-form`, `data-report-basis-panel`
- `partials/report_summary.html`: ids `remediation-summary-area`, `remediation-{{ item.id }}`, `review-banner`, `rfi-section`; data-* `data-analysis-incomplete-banner`, `data-copy-target`, `data-copy-trigger`, `data-dpdpa-readiness-note`, `data-framework-coverage`, `data-framework-failed`, `data-framework-not-scored`, `data-framework-pending`, `data-legacy-remediation`, `data-release-blockers`, `data-release-state`, `data-rfi-link`, `data-view-mode`
- `partials/report_tab.html`: ids `report-content`; hx-swap `innerHTML`; hx-verbs `hx-get /assessments/{{ assessment.id }}/report-summary?view={{ report_view_mode }}&amp;framework={{ active_framework }}`
- `partials/review_finding_card.html`: ids `review-card-{{ item.id }}`; hx-target `#review-card-{{ item.id }}`; hx-swap `outerHTML`; hx-verbs `hx-patch /api/assessments/{{ assessment.id }}/review/items/{{ item.id }}`; data-* `data-review-card`, `data-review-status`, `data-risk-level`

## Build notes

**Review queue and cards.** `GET /assessments/{assessment_id}/review-queue` (`requirement_review.py`) with `components/requirement_card_body.html` and `components/conclusion_card.html` (HTMX `#conclusion-card-{{ card.conclusion.id }}`, swap `outerHTML`; approve, edit, reject, reopen in `app/routers/conclusions.py`; RFI add, withdraw and divergence acknowledge in `requirement_review.py`). These carry the most `data-*` attributes and the most test assertions in the app; change markup and classes only, never attribute names or the swap targets. `GET /assessments/{assessment_id}/conclusions` renders the Conclusions list; `GET /assessments/{assessment_id}/review` only redirects to it.

**Findings.** `GET /assessments/{assessment_id}/findings` with `components/finding_card.html` (HTMX `#finding-{{ view.finding.id }}`, swap `outerHTML`, routes in `app/routers/findings.py`). The IA also reaches individual findings from engagement Findings and actions (S4); both use this one component. Priority is words (Do first, Next, Planned, Backlog), never numeric. `partials/review_finding_card.html` is the legacy finding review card (`data-review-card`, `data-review-status`, `data-risk-level`).

**Keycap hints.** The mockup draws `A`, `E`, `X` keycaps on Approve, Edit and Reject. Only `j` and `k` are implemented (`review_queue.html` script); `app/static/js/app.js` `Shortcuts` has no review scope. Do not draw hints for shortcuts that do nothing. Either leave the keycaps out, or, if Saqlain confirms, add the three handlers (they must submit the same forms as the buttons and ignore input fields). Default: leave them out and report it.

**Analysis.** `POST /assessments/{assessment_id}/run-analysis` and `GET /assessments/{assessment_id}/analysis-status` render the four analysis partials into `#analysis-area` (running swaps `outerHTML`). `analysis_gate_blocked.html` keeps the `override_reason` field and `data-completion-override-form`. The analysis partials sit inside the Questionnaire tab (S5) but are restyled here.

**Report tab.** `GET /assessments/{assessment_id}/report` renders `assessment_detail` with tab report; `GET /assessments/{assessment_id}/report-summary` returns `partials/report_summary.html` (the biggest template: framework cards, remediation, RFI section, release panel, report basis). `partials/report_tab.html` hosts `#report-content`. `partials/remediation_summary.html` and `partials/remediation_panel.html` are included by report_summary and belong here. `partials/framework_panel.html` is the per-framework body (the strip is S5). One Generate button follows the selected report tab. No combined view.

**Release and basis.** `partials/release_panel.html` (`data-release-form`, swap `none`) and `partials/report_basis_panel.html` (`data-report-basis-form`, `data-period-locked`, `data-period-recorded`) post to `app/routers/review.py` (`POST /api/assessments/{id}/release`, `.../report-basis`). The sign-off name input is the temporary reviewer-name field.

**Review inbox.** The side-menu Review entry has no destination today and the mockups do not draw one: `b5-review-queue.html` is the per-assessment queue. Proposed minimal page, to confirm with Saqlain before building: `GET /review` lists non-archived assessments that have conclusions awaiting a decision (assessment, engagement, client, count), each linking to its queue; empty state "Nothing waiting for review". If Saqlain declines, remove Review from the menu instead. Until confirmed, do not build it; flip the `NAV_ITEMS` entry only when it exists.

**No mockup: narrative, board inputs, recommended-action draft.** `pages/narrative.html` (`GET /assessments/{assessment_id}/narrative`, `app/routers/drafting.py`), `pages/board_inputs.html` (`GET /assessments/{assessment_id}/board-inputs`, `app/routers/board_inputs.py`) and `partials/remediation_draft.html` (button and field inside the requirement card, HTMX `#recommended-action-{{ conclusion_id }}`) were added after the mockups were drawn and have none. They are reached only by URL today. Build them from existing components only (page header, card, field, button, alert, `.seg`), keep every `data-*`, and put them under Assessment / Report as sub-pages. Do not invent a new component. Record in Results that they are unreviewed by design and list their screenshots separately for Saqlain. Open question: whether they need their own mockups first.

## Backend dependency

PR #99, https://github.com/saqlainmmomin/Cyber/pull/99, carries the server-side work for the redesign; its spec is `tasks/handoffs/2026-10-03-yozora-backend-features.md` on branch `claude/yozora-backend-features`. **Do not re-specify or re-implement it here.** At the time this handoff was written #99 held only its spec (no code), so this file names the planned modules from that spec: if #99 has merged by the time you start, read the real function names from the code and use those; if it has not, follow the 'if not merged' instruction in the Build notes.

None required. PR #99's `assessment_stage` supplies the Overview stage that links here; the review inbox (`GET /review`) is a small read-only query inside this slice if Saqlain approves it.

## Tests

**Existing tests that exercise this slice** (route calls matched against this slice's routes, plus tests that name its templates). Run them first and again after each template change.

| Test file | Calls to this slice's routes | Mentions its templates |
|---|---|---|
| `tests/test_findings.py` | 22 | 2 |
| `tests/test_remediation_tracking.py` | 14 | 3 |
| `tests/test_p6_7_requirement_card.py` | 8 | 6 |
| `tests/test_conclusion_approval.py` | 10 | 2 |
| `tests/test_p5_2_reader_migration.py` | 10 | 2 |
| `tests/test_correctness_bundle.py` | 6 | 3 |
| `tests/test_p6_3a_grounding.py` | 0 | 8 |
| `tests/test_p6_4_whats_missing.py` | 0 | 6 |
| `tests/test_p6_7b_add_to_rfi.py` | 1 | 4 |
| `tests/test_p6_2b_dpdpa_criteria.py` | 0 | 4 |
| `tests/test_p6_4_cap_upload_limit.py` | 0 | 4 |
| `tests/test_p6_6_report_foundations.py` | 3 | 1 |
| `tests/test_p6_8_board_report_v2.py` | 0 | 4 |
| `tests/test_workpaper.py` | 4 | 0 |
| `tests/test_p6_10a_remediation_draft.py` | 3 | 0 |
| `tests/test_p6_8_b2_docx_xlsx.py` | 0 | 3 |
| `tests/test_p6_8_v3a_data_capture.py` | 3 | 0 |
| `tests/test_p6_9_file_set.py` | 0 | 3 |
| `tests/test_picker_and_scoring_contract.py` | 3 | 0 |
| `tests/test_report_snapshots.py` | 1 | 2 |
| `tests/test_p6_0e_dpdpa_pack_correctness.py` | 1 | 1 |
| `tests/test_p6_10b_narrative.py` | 2 | 0 |
| `tests/test_needs_review_ui.py` | 0 | 1 |
| `tests/test_no_blended_scoring.py` | 1 | 0 |

(+4 more files with fewer matches; list them with `grep -ln` on the routes above.)

Strings such as `text-amber-700` are Tailwind classes that a test pins; the redesign removes Tailwind from the page, so those tests must be rewritten to assert the `data-*` attribute or the visible text instead, and the change listed in the PR.

**Asserted strings likely to change.** These literals appear in `assert ... in ...` lines of the tests above and also verbatim in this slice's templates today; if a restyle changes or removes one, edit the test deliberately and list the change in the PR description (old string, new string, reason).

- "Live PDF": test_correctness_bundle.py:844, test_p5_6_rfi_rebuild.py:909, test_report_snapshots.py:800
- "A newer AI proposal was withheld": test_conclusion_approval.py:378, test_conclusion_approval.py:391
- "Closed without closure evidence (legacy)": test_remediation_tracking.py:1069, test_remediation_tracking.py:721
- "History could not be read.": test_findings.py:727, test_remediation_tracking.py:811
- "Legacy bulk approval, not individually reviewed": test_conclusion_approval.py:583, test_findings.py:1111
- "Needs review": test_needs_review_ui.py:325, test_needs_review_ui.py:333
- "No conclusions yet. Run the gap analysis first.": test_conclusion_approval.py:825, test_workpaper.py:756
- "Scores unavailable": test_no_blended_scoring.py:578, test_p5_2_reader_migration.py:765
- "Add to draft RFI": test_p6_7b_add_to_rfi.py:297
- "Closed and verified actions cannot be changed here.": test_findings.py:664
- "Compliant": test_conclusion_approval.py:378
- "Evidence support not captured (legacy)": test_workpaper.py:741
- "Legacy remediation record (read-only)": test_remediation_tracking.py:837
- "No approved conclusions are waiting for a finding.": test_findings.py:938
- "No findings yet.": test_findings.py:939
- "No remediation actions yet.": test_remediation_tracking.py:855
- "No supporting citation (explicit evidence absence)": test_workpaper.py:742
- "Non-Compliant": test_p6_10a_remediation_draft.py:188
- "Remediation Progress": test_remediation_tracking.py:849
- "Report view differs": test_conclusion_approval.py:817
- "This conclusion changed since you loaded it": test_conclusion_approval.py:325
- "Workpaper trace →": test_findings.py:923
- "Your unsaved value": test_conclusion_approval.py:610
- "analysis failed": test_correctness_bundle.py:665
- "awaiting consultant review": test_p5_2_reader_migration.py:733
- "individually approved": test_p6_6_report_foundations.py:755
- "insufficient evidence": test_p5_2_reader_migration.py:551
- "model flagged this verdict": test_needs_review_ui.py:326
- "not captured": test_conclusion_approval.py:544
- "supporting outcome has no grounded citation": test_conclusion_approval.py:560
- "text-amber-700 dark:text-amber-300": test_needs_review_ui.py:327

**Page text asserted by tests that fetch this slice's routes** (not necessarily from this slice's own templates; the test may be reading text that comes from an included partial or the shell). Check each one when you restyle the page it comes from.

- "ISO 27001": test_picker_and_scoring_contract.py:259, test_picker_and_scoring_contract.py:300
- "Why These Gaps Exist": test_p6_6_report_foundations.py:847, test_p6_6_report_foundations.py:850
- "Acknowledged by Priya": test_p6_7_requirement_card.py:674
- "Build a consent ledger": test_p6_6_report_foundations.py:837
- "Closed with evidence": test_remediation_tracking.py:459
- "Closed, awaiting verification": test_remediation_tracking.py:425
- "Closure verified": test_remediation_tracking.py:458
- "Created by Priya": test_findings.py:922
- "Data Protection Officer": test_p6_10a_remediation_draft.py:136
- "Evidence support was not captured": test_conclusion_approval.py:547
- "Fix the gap": test_p6_10a_remediation_draft.py:345
- "Grounded quote": test_conclusion_approval.py:815
- "ISO A.5.2 needs a documented allocation; DPDPA does not.": test_p6_7_requirement_card.py:675
- "Insufficient Evidence": test_p6_6_report_foundations.py:835
- "Legacy note": test_remediation_tracking.py:839
- "No actions in this engagement yet.": test_remediation_tracking.py:1009
- "Owner: Anita Rao": test_p6_6_report_foundations.py:838
- "Prefilled action": test_findings.py:906
- "Released by Priya": test_p5_2_reader_migration.py:617
- "Repeat violations": test_correctness_bundle.py:798
- "Replace the pre-ticked consent box with an unticked, specific opt-in.": test_p6_10a_remediation_draft.py:134
- "Source conclusion is no longer approved (now pending)": test_findings.py:933
- "Status: Accepted risk": test_remediation_tracking.py:700
- "Target: 30 Nov 2026": test_p6_6_report_foundations.py:838
- "This summary is generated from consultant-approved conclusions only.": test_p5_2_reader_migration.py:599

**New tests to add:**

- Review, Conclusions, Findings and Workpaper pages share one `.seg` row; Report pages share theirs; Applicability only when ISO 27001 is in scope.
- No page renders more than one visible `.btn.primary` in the states the harness captures.
- `pages/narrative.html` and `pages/board_inputs.html` render with every `data-*` kept.
- If the review inbox is approved: `GET /review` lists only assessments with decisions waiting.

## File-set guard

Many tests are scope guards: they diff the branch against `main` and fail when a file outside an allow-list changes (the P6-2b scenario 11 guard in `tests/test_p6_2b_dpdpa_criteria.py`, the P6-9 file-set guard in `tests/test_p6_9_file_set.py`, and several older `:(exclude)` guards). They were written for earlier PRs and are stale for this one. **Never delete or weaken a guard.** Add a scoped allowance instead, the way `tests/p6_8_v3a_paths.py` does for V3-A:

1. S1 creates `tests/yozora_paths.py` with one tuple per slice (`YOZORA_S1_PATHS`, ...) and `YOZORA_EXCLUDES = [f":(exclude){p}" for p in ...]` over all tuples. Each later slice adds its own tuple (every file it adds or changes outside `docs/product/` and `design/`) to that module.
2. Run the full suite. For each guard that fails on your files, splat `*YOZORA_EXCLUDES` into its pathspec list (or import the tuple into its allow-list), exactly as `V3A_EXCLUDES` is imported by `tests/test_p5_6_rfi_rebuild.py`. Add a comment `# Yozora per-PR allowance`.
3. Keep this slice's handoff file and `YOZORA_DESIGN_FILES` allowed (already done for `tasks/handoffs/2026-10-01-yozora-s*-handoff.md`).
4. List every guard you touched in the PR description.

**This slice's `YOZORA_S7_PATHS` starts as:**

- `app/templates/components/conclusion_card.html`
- `app/templates/components/finding_card.html`
- `app/templates/components/requirement_card_body.html`
- `app/templates/pages/conclusions.html`
- `app/templates/pages/findings.html`
- `app/templates/pages/review_queue.html`
- `app/templates/pages/board_inputs.html`
- `app/templates/pages/narrative.html`
- `app/templates/partials/analysis_complete.html`
- `app/templates/partials/analysis_error.html`
- `app/templates/partials/analysis_gate_blocked.html`
- `app/templates/partials/analysis_running.html`
- `app/templates/partials/framework_panel.html`
- `app/templates/partials/no_report.html`
- `app/templates/partials/release_panel.html`
- `app/templates/partials/remediation_draft.html`
- `app/templates/partials/remediation_panel.html`
- `app/templates/partials/remediation_summary.html`
- `app/templates/partials/report_basis_panel.html`
- `app/templates/partials/report_summary.html`
- `app/templates/partials/report_tab.html`
- `app/templates/partials/review_finding_card.html`
- `app/routers/requirement_review.py`
- `app/routers/web.py`
- `app/routers/conclusions.py`
- `app/routers/findings.py`
- `app/routers/review.py`
- `app/routers/drafting.py`
- `app/routers/board_inputs.py`
- plus every test, CSS, JS and fixture file you add or change.

**Guards found today that name this slice's files** (expect these to need the allowance; there may be more):

- `tests/test_longitudinal_demo.py` names `app/routers/web.py`
- `tests/test_p5_2_reader_migration.py` names `app/templates/partials/release_panel.html`, `app/templates/partials/review_finding_card.html`
- `tests/test_p5_4_adaptive_ucc_questionnaire.py` names `app/routers/review.py`
- `tests/test_p6_2b_dpdpa_criteria.py` names `app/templates/components/conclusion_card.html`, `app/templates/components/requirement_card_body.html`, `app/templates/pages/narrative.html`, `app/templates/partials/remediation_draft.html`, `app/routers/requirement_review.py`, `app/routers/drafting.py`
- `tests/test_p6_3a_grounding.py` names `app/templates/components/conclusion_card.html`, `app/templates/components/requirement_card_body.html`, `app/templates/pages/conclusions.html`, `app/templates/pages/review_queue.html`, `app/templates/pages/narrative.html`, `app/templates/partials/remediation_draft.html` ...
- `tests/test_p6_4_cap_upload_limit.py` names `app/templates/components/conclusion_card.html`, `app/templates/components/requirement_card_body.html`, `app/templates/pages/conclusions.html`, `app/templates/pages/review_queue.html`, `app/routers/requirement_review.py`
- `tests/test_p6_4_whats_missing.py` names `app/templates/components/conclusion_card.html`, `app/templates/components/requirement_card_body.html`, `app/templates/pages/conclusions.html`, `app/templates/pages/review_queue.html`, `app/templates/pages/narrative.html`, `app/templates/partials/remediation_draft.html` ...
- `tests/test_p6_6_report_foundations.py` names `app/templates/partials/report_summary.html`
- `tests/test_p6_7_requirement_card.py` names `app/templates/components/conclusion_card.html`, `app/templates/components/requirement_card_body.html`, `app/templates/pages/conclusions.html`, `app/templates/pages/review_queue.html`, `app/templates/pages/narrative.html`, `app/templates/partials/remediation_draft.html` ...
- `tests/test_p6_7b_add_to_rfi.py` names `app/templates/components/conclusion_card.html`, `app/templates/components/requirement_card_body.html`, `app/templates/pages/narrative.html`, `app/templates/partials/remediation_draft.html`, `app/routers/requirement_review.py`, `app/routers/web.py` ...
- `tests/test_p6_8_b2_docx_xlsx.py` names `app/templates/components/conclusion_card.html`, `app/templates/pages/narrative.html`, `app/templates/partials/remediation_draft.html`, `app/routers/web.py`, `app/routers/drafting.py`
- `tests/test_p6_8_board_report_v2.py` names `app/templates/components/conclusion_card.html`, `app/templates/components/requirement_card_body.html`, `app/templates/pages/narrative.html`, `app/templates/partials/remediation_draft.html`, `app/routers/requirement_review.py`, `app/routers/web.py` ...
- `tests/test_p6_8_v3a_data_capture.py` names `app/routers/findings.py`, `app/routers/drafting.py`, `app/routers/board_inputs.py`
- `tests/test_p6_9_file_set.py` names `app/templates/components/conclusion_card.html`, `app/templates/pages/narrative.html`, `app/templates/partials/remediation_draft.html`, `app/routers/requirement_review.py`, `app/routers/web.py`, `app/routers/review.py` ...
- `tests/test_p6_nist_csf2_alignment.py` names `app/routers/requirement_review.py`, `app/routers/web.py`, `app/routers/review.py`

## Screenshot gate

Use the harness from S1 (`design/harness/README.md`). Render each screen listed above in every state, light and dark, at 1440 and 1024. Baselines are the approved mockups rendered at the same viewport with `?state=<name>` and `?dark`, saved as `design/baselines/<screen>-<state>-<theme>-<width>.png` (S1 defines the exact naming; include the state in the name when the screen has several). Candidates use seeded demo data (the fictional Meridian Ledger Technologies, Loomwire Labs and Kestrel Advisory companies from the mockups) with the clock frozen and fonts vendored.

Thresholds from the fidelity gate: colour tolerance 0.1 (pixelmatch); fail above **0.4%** differing pixels on app screens and **0.2%** on `/design`; fail on any single changed region over 40x40 px regardless of the total. Mask dynamic regions with `data-visual-mask`. Loosening a threshold needs a written reason in the PR.

In the PR, post for each screen and state: the baseline, the candidate and the diff image side by side, plus the differing-pixel percentage. Saqlain sees these before merge (gate 4). CI green is necessary, not sufficient.

## Dependency order

S1 shell, then S2 component layer and `/design`, then S3 to S8 (S3 and S4 first; S5, S6 and S7 can run in parallel worktrees only if they touch no shared template; S8 after S6 and S7), then S9 system states, dark and mobile pass. This is slice **S7**.

## Stop and ask

Stop and write the question in this file's Results section (and tell the orchestrating session) if:

- a visual detail is in neither the design guide nor the approved mockup;
- two mockups disagree;
- a must-keep id, `hx-*` or `data-*` cannot be kept;
- a mockup shows an action with no route behind it that this file does not cover;
- the work needs a model, migration, prompt, scoring or PDF change.
- If Saqlain has not confirmed the review inbox, skip it and say so.
- Never touch scoring, the analyzer, prompts or the report snapshot PDF code. This slice changes templates only (plus the small inbox route).
- If a card state in the mockup needs data the template does not receive today, stop and ask.

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

(Codex fills in: what was built, the screenshots table with percentages, tests changed with old and new strings, guards touched, decisions made, open questions, full-suite summary line.)
