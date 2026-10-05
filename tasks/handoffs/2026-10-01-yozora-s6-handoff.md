# Yozora S6: Evidence: inventory, upload, AWS, reuse, detail, citation span, workpaper

**Rewritten:** 2026-10-03 (replaces the 2026-10-01 template). **Owner:** Codex builds; Claude reviews every diff and screenshot before merge; Saqlain merges. **Depends on:** S1 and S2 merged; S4 recommended (engagement tabs). PR #99 for the inventory read model.
**Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (work in your own git worktree of it, one branch per slice, named `codex/yozora-s6-...`). Paths below are relative to your worktree root. The specs below exist on `main` once the docs PR for this series has merged; until then branch from `claude/yozora-slice-handoffs`.

**Read first, in this order:** `docs/product/yozora-design-system.md` (the design guide), `docs/product/yozora-fidelity-gate.md`, `docs/product/2026-10-01-app-design-mockups/screens/IA-SPEC.md`, `docs/product/yozora-migration-map.md` (rows for this slice), then the mockups listed under Screens (serve them with `python3 -m http.server` from the repo root and open `/docs/product/2026-10-01-app-design-mockups/screens/<file>?state=<name>` and `&dark`). Background if you need it: `tasks/agent-ownership.md`, `CLAUDE.md`.

## Goal

Replace the Documents tab, the AWS evidence tab and the client-links page with one Evidence inventory per engagement, and rebuild the evidence sub-pages: Pull from AWS, Reuse from another assessment, evidence detail, the cited-span view, and the workpaper (an assessment Review sub-view). After this slice the Evidence menu entry (the cross-engagement inventory) is live.

## Definition of done

- Every state under Screens matches its baseline at the thresholds, light and dark, 1440 and 1024.
- `/engagements/{engagement_id}/evidence` renders the inventory from `evidence_inventory.inventory_rows` with filters for source, status and assessment, an Upload evidence primary, and menu entries for Pull from AWS and Reuse. `GET /evidence` renders the cross-engagement view (`?state=all` in the mockup) with an Engagement column and no engagement tabs.
- Status words are Scanning, Available, Rejected, Out of date; sources are Upload, AWS, Client link, Reused.
- Upload and delete still work through the existing HTMX routes into `#document-list`; all upload ids are kept.
- A note under the table links to the questionnaire when documents arrived after the last pre-fill.
- Must-keep ids, `hx-*` and `data-*` unchanged; tests updated deliberately.

## Screens

Mockups are in `docs/product/2026-10-01-app-design-mockups/screens/`. Match every state listed; the state names are the `?state=` values on the mockup.

| Mockup | States to match |
|---|---|
| `b4-evidence.html` | `default`, `upload`, `filtered`, `empty`, `loading`, `error`, `all` (cross-engagement); also `?state=prefill` (note under the table). |
| `b4-aws_evidence.html` | `ready`, `pulling`, `result`, `error`, `notconfigured`. |
| `b4-evidence_reuse.html` | `list`, `error`, `empty`, `unlinked`: tick boxes plus one confirm button. |
| `b4-evidence_detail.html` | `current`, `quarantined`, `unused`. |
| `b4-evidence_span.html` | `span`, `whole`, `superseded`, `unavailable`. |
| `b4-workpaper.html` | `list`, `empty`. |
| `b4-workpaper_entry.html` | `default`, `legacy`, `excluded`. |

## Templates, routes and view functions in scope

**New templates this slice creates:** `pages/evidence_inventory.html`. Add a row for each to `docs/product/yozora-migration-map.md`.

Routes were found by grepping `app/routers/` for each template (helper functions are traced to their routes). Verify with `grep -rn '<template>' app` before relying on a row; if a row is wrong, fix the migration map in your PR.

| Template | Served by (method path, function) |
|---|---|
| `pages/aws_evidence.html` | `GET /engagements/{engagement_id}/aws-evidence` `app/routers/aws.py::aws_evidence_page` |
| `pages/evidence_detail.html` | `GET /evidence/{evidence_id}` `app/routers/web.py::evidence_detail_page` |
| `pages/evidence_reuse.html` | `GET /assessments/{assessment_id}/evidence-reuse` `app/routers/evidence_reuse.py::evidence_reuse_page`<br>`POST /assessments/{assessment_id}/evidence-reuse/{source_use_id}/confirm` `app/routers/evidence_reuse.py::confirm_evidence_reuse` |
| `pages/evidence_span.html` | `GET /evidence-versions/{version_id}/span` `app/routers/requirement_review.py::evidence_span` |
| `pages/workpaper.html` | `GET /assessments/{assessment_id}/workpaper` `app/routers/web.py::workpaper_page` |
| `components/workpaper_entry.html` | included by `pages/workpaper.html` |
| `partials/aws_evidence_panel.html` | `POST /engagements/{engagement_id}/aws-evidence/pull` `app/routers/aws.py::aws_evidence_pull` |
| `partials/document_list.html` | `DELETE /assessments/{assessment_id}/documents/{document_id}` `app/routers/web.py::delete_document_web`<br>`POST /assessments/{assessment_id}/evidence/{evidence_id}/versions` `app/routers/web.py::upload_document_version_web`<br>`POST /assessments/{assessment_id}/upload` `app/routers/web.py::upload_document_web` |
| `partials/documents_tab.html` | included by `pages/assessment.html` |
| `partials/upload_status.html` | `POST /assessments/{assessment_id}/evidence/{evidence_id}/versions` `app/routers/web.py::upload_document_version_web`<br>`POST /assessments/{assessment_id}/upload` `app/routers/web.py::upload_document_web` |

## Must-keep ids, `hx-*` and `data-*`

Copied from the templates as they are today (checked against `docs/product/yozora-migration-map.md`). A migration may restyle and move these but not rename, drop or re-target them. If markup must change so that one cannot stay, stop and ask.

- `pages/aws_evidence.html`: ids `aws-external-id`; data-* `data-aws-not-configured`, `data-consultant-policy`, `data-external-id`, `data-permissions-policy`, `data-trust-policy`
- `pages/evidence_detail.html`: none.
- `pages/evidence_reuse.html`: ids `reuse-{{ c.source_use_id }}`; data-* `data-reuse-candidate`, `data-reuse-confirm`, `data-reuse-error`, `data-reuse-warning`, `data-warnings`
- `pages/evidence_span.html`: ids `cited-span`; data-* `data-cited-span`, `data-evidence-span-text`, `data-span-unavailable`
- `pages/workpaper.html`: ids `{{ row.anchor }}`; data-* `data-count`, `data-report-basis`, `data-run-stale`, `data-run-status`, `data-workpaper-section`, `data-workpaper-unconcluded`
- `components/workpaper_entry.html`: ids `{{ entry.anchor }}`; data-* `data-decision-state`, `data-in-scope`, `data-revision-action`, `data-revision-history`, `data-workpaper-entry`, `data-workpaper-finding`
- `partials/aws_evidence_panel.html`: ids `aws-evidence-panel`; hx-target `#aws-evidence-panel`; hx-swap `outerHTML`; hx-verbs `hx-post /engagements/{{ engagement_id }}/aws-evidence/pull`; data-* `data-aws-error`, `data-aws-evidence-row`, `data-aws-pull-form`, `data-aws-result`, `data-aws-source-row`
- `partials/document_list.html`: hx-target `#document-list`; hx-swap `innerHTML`; hx-verbs `hx-delete /assessments/{{ assessment_id }}/documents/{{ row.id }}`, `hx-post /assessments/{{ assessment_id }}/evidence/{{ row.id }}/versions`
- `partials/documents_tab.html`: ids `desk-review-area`, `document-list`, `drop-zone`, `file-input`, `file-name-display`, `upload-progress`, `upload-progress-bar`; hx-target `#document-list`; hx-swap `innerHTML`; hx-verbs `hx-get /assessments/{{ assessment.id }}/desk-review-status`, `hx-post /assessments/{{ assessment.id }}/upload`; data-* `data-evidence-reuse-link`
- `partials/upload_status.html`: none.

## Build notes

**Inventory.** New route `GET /engagements/{engagement_id}/evidence` and `GET /evidence` (cross-engagement), new template `app/templates/pages/evidence_inventory.html` (add a migration-map row). Rows, filters and counts come from `app/services/evidence_inventory.py` (PR #99): `inventory_rows(db, engagement_id, *, assessment_id=None, source=None, status=None, search=None)`, `cross_engagement_rows(db, ...)`, `status_counts(...)`. Where PR #99 said a source cannot be told apart from stored data, show what the service returns and do not guess. `partials/document_list.html` (target `#document-list`, swap `innerHTML`) becomes the table body fragment returned by upload, delete and version-upload routes (`POST /assessments/{assessment_id}/upload`, `DELETE /assessments/{assessment_id}/documents/{document_id}`, `POST /assessments/{assessment_id}/evidence/{evidence_id}/versions`); `partials/upload_status.html` is the status row those routes return. Keep the upload panel ids (`drop-zone`, `file-input`, `file-name-display`, `upload-progress`, `upload-progress-bar`), `data-evidence-reuse-link`, and the category select.

**Folding away the documents tab.** `partials/documents_tab.html` is deleted once its upload panel is in the inventory page, and `GET /assessments/{id}?tab=documents` becomes a 303 to `/engagements/{engagement_id}/evidence?assessment={id}` (S5 removed the tab from the row and left the URL working; add the redirect test here). Its `desk-review-area` already moved to the Questionnaire tab in S5 (if S5 has not merged, leave a clearly marked include and say so). Remove the file from the lint allow-list by deleting it, and update the migration map row to `deleted`.

**AWS.** `GET /engagements/{engagement_id}/aws-evidence`, `POST .../aws-evidence/pull` (`app/routers/aws.py`). A sub-page of Evidence (Evidence tab stays selected). `partials/aws_evidence_panel.html` is the HTMX panel (`#aws-evidence-panel`, swap `outerHTML`). The trust, permissions and consultant policy blocks use the `.code` component with a copy action. Keep `aws-external-id` and the `data-*` list.

**Reuse.** `GET /assessments/{assessment_id}/evidence-reuse`, `POST .../evidence-reuse/{source_use_id}/confirm` (`app/routers/evidence_reuse.py`). Reuse is between assessments of the same engagement. The mockup uses tick boxes and one confirm button; today each candidate has its own form (`data-reuse-confirm`, `hx-boost="false"`) posting one `source_use_id` with its own fields. A single confirm for several ticked rows needs either a script that submits each ticked row's form in turn, or a new bulk route. That is a product-and-backend decision the mockup does not settle: build the tick boxes and the one confirm button over the existing per-candidate POST (submitted in sequence by a small script, stopping at the first error and showing it), do not add a route, and report the limitation in Results. Keep `data-reuse-candidate`, `data-reuse-confirm`, `data-reuse-error`, `data-reuse-warning`, `data-warnings`.

**Detail and span.** `GET /evidence/{evidence_id}` (`web.py`, `evidence_detail_page`) and `GET /evidence-versions/{version_id}/span` (`requirement_review.py`, also embedded in S7's requirement card). Keep `cited-span`, `data-cited-span`, `data-evidence-span-text`, `data-span-unavailable`; the span page asserts text in `tests/test_p6_3a_grounding.py` and others.

**Workpaper.** `GET /assessments/{assessment_id}/workpaper` with `components/workpaper_entry.html` rows. It is an assessment Review sub-view: the S2 `seg` row (Queue, Conclusions, Findings, Workpaper) sits under the assessment tab row with Review selected. The Review queue, Conclusions and Findings pages are S7 and must use the same seg macro. The standalone workpaper print template (`reports/workpaper_standalone.html`) is out of scope.

## Backend dependency

PR #99, https://github.com/saqlainmmomin/Cyber/pull/99, carries the server-side work for the redesign; its spec is `tasks/handoffs/2026-10-03-yozora-backend-features.md` on branch `claude/yozora-backend-features`. **Do not re-specify or re-implement it here.** At the time this handoff was written #99 held only its spec (no code), so this file names the planned modules from that spec: if #99 has merged by the time you start, read the real function names from the code and use those; if it has not, follow the 'if not merged' instruction in the Build notes.

PR #99: `app/services/evidence_inventory.py`, `app/services/prefill_freshness.py`. **Not covered by #99:** the inventory routes and page (`/engagements/{id}/evidence`, `/evidence`), which this slice adds as read-only views over those services.

## Tests

**Existing tests that exercise this slice** (route calls matched against this slice's routes, plus tests that name its templates). Run them first and again after each template change.

| Test file | Calls to this slice's routes | Mentions its templates |
|---|---|---|
| `tests/test_workpaper.py` | 19 | 2 |
| `tests/test_longitudinal_demo.py` | 8 | 1 |
| `tests/test_aws_evidence.py` | 6 | 2 |
| `tests/test_evidence_service.py` | 6 | 0 |
| `tests/test_p6_7_requirement_card.py` | 3 | 3 |
| `tests/test_p6_3a_grounding.py` | 0 | 2 |
| `tests/test_p6_6_report_foundations.py` | 2 | 0 |
| `tests/test_report_snapshots.py` | 2 | 0 |
| `tests/test_findings.py` | 1 | 0 |
| `tests/test_p6_4_cap_upload_limit.py` | 0 | 1 |
| `tests/test_p6_4_whats_missing.py` | 0 | 1 |
| `tests/test_p6_8_board_report_v2.py` | 1 | 0 |
| `tests/test_p6_nist_csf2_alignment.py` | 1 | 0 |
| `tests/test_performance_benchmarks.py` | 1 | 0 |

Strings such as `text-amber-700` are Tailwind classes that a test pins; the redesign removes Tailwind from the page, so those tests must be rewritten to assert the `data-*` attribute or the visible text instead, and the change listed in the PR.

**Asserted strings likely to change.** These literals appear in `assert ... in ...` lines of the tests above and also verbatim in this slice's templates today; if a restyle changes or removes one, edit the test deliberately and list the change in the PR description (old string, new string, reason).

- "No desk-review findings for this requirement.": test_workpaper.py:428, test_workpaper.py:744
- "No evidence mapped to this requirement.": test_workpaper.py:427, test_workpaper.py:745
- "Applicable requirements with no conclusion": test_workpaper.py:563
- "Confirm reuse": test_longitudinal_demo.py:273
- "Current version": test_p6_7_requirement_card.py:1017
- "Declining records nothing.": test_longitudinal_demo.py:276
- "Evidence support not captured (legacy)": test_workpaper.py:741
- "Legacy bulk approval, not individually reviewed": test_findings.py:1111
- "No analysis runs recorded.": test_workpaper.py:757
- "No conclusions yet. Run the gap analysis first.": test_workpaper.py:756
- "No evidence from earlier assessments is waiting for confirmation.": test_longitudinal_demo.py:306
- "No questionnaire response recorded for this requirement.": test_workpaper.py:426
- "No supporting citation (explicit evidence absence)": test_workpaper.py:742
- "Scope-enforced to not applicable at analysis time": test_workpaper.py:552
- "Shared cluster question": test_workpaper.py:655
- "Superseded": test_evidence_service.py:1234
- "Superseded version": test_p6_7_requirement_card.py:1034
- "Whole document cited": test_p6_7_requirement_card.py:1028
- "not linked to an engagement": test_longitudinal_demo.py:341

**Page text asserted by tests that fetch this slice's routes** (not necessarily from this slice's own templates; the test may be reading text that comes from an included partial or the shell). Check each one when you restyle the page it comes from.

- "Assessment period: 01 Apr 2026 to 30 Jun 2026 · Evidence cut-off: 15 Jul 2026": test_p6_6_report_foundations.py:1127
- "Assessment period: not recorded · Evidence cut-off: not recorded": test_p6_6_report_foundations.py:1130
- "Download PDF": test_report_snapshots.py:801
- "Live PDF": test_report_snapshots.py:800
- "PDF Report": test_report_snapshots.py:802
- "Privacy Policy": test_evidence_service.py:1242
- "Privacy Policy.pdf": test_evidence_service.py:1216
- "Version 1": test_p6_7_requirement_card.py:1016

**New tests to add:**

- Inventory page: rows, filters (source, status, assessment), status words, and the cross-engagement view with an Engagement column.
- `GET /assessments/{id}?tab=documents` responds 303 to the engagement Evidence inventory filtered to the assessment.
- Upload, delete and version-upload round trips still return the `#document-list` fragment.
- Reuse page: tick boxes and one confirm button present; confirm of one candidate still works.

## File-set guard

Many tests are scope guards: they diff the branch against `main` and fail when a file outside an allow-list changes (the P6-2b scenario 11 guard in `tests/test_p6_2b_dpdpa_criteria.py`, the P6-9 file-set guard in `tests/test_p6_9_file_set.py`, and several older `:(exclude)` guards). They were written for earlier PRs and are stale for this one. **Never delete or weaken a guard.** Add a scoped allowance instead, the way `tests/p6_8_v3a_paths.py` does for V3-A:

1. S1 creates `tests/yozora_paths.py` with one tuple per slice (`YOZORA_S1_PATHS`, ...) and `YOZORA_EXCLUDES = [f":(exclude){p}" for p in ...]` over all tuples. Each later slice adds its own tuple (every file it adds or changes outside `docs/product/` and `design/`) to that module.
2. Run the full suite. For each guard that fails on your files, splat `*YOZORA_EXCLUDES` into its pathspec list (or import the tuple into its allow-list), exactly as `V3A_EXCLUDES` is imported by `tests/test_p5_6_rfi_rebuild.py`. Add a comment `# Yozora per-PR allowance`.
3. Keep this slice's handoff file and `YOZORA_DESIGN_FILES` allowed (already done for `tasks/handoffs/2026-10-01-yozora-s*-handoff.md`).
4. List every guard you touched in the PR description.

**This slice's `YOZORA_S6_PATHS` starts as:**

- `app/templates/pages/aws_evidence.html`
- `app/templates/pages/evidence_detail.html`
- `app/templates/pages/evidence_reuse.html`
- `app/templates/pages/evidence_span.html`
- `app/templates/pages/workpaper.html`
- `app/templates/components/workpaper_entry.html`
- `app/templates/partials/aws_evidence_panel.html`
- `app/templates/partials/document_list.html`
- `app/templates/partials/documents_tab.html`
- `app/templates/partials/upload_status.html`
- `app/templates/pages/evidence_inventory.html`
- `app/routers/web.py`
- `app/routers/evidence_reuse.py`
- `app/routers/aws.py`
- plus every test, CSS, JS and fixture file you add or change.

**Guards found today that name this slice's files** (expect these to need the allowance; there may be more):

- `tests/test_longitudinal_demo.py` names `app/templates/pages/evidence_reuse.html`, `app/routers/web.py`, `app/routers/evidence_reuse.py`
- `tests/test_p6_3a_grounding.py` names `app/templates/pages/evidence_span.html`, `app/templates/pages/workpaper.html`, `app/routers/web.py`
- `tests/test_p6_4_cap_upload_limit.py` names `app/templates/pages/evidence_span.html`
- `tests/test_p6_4_whats_missing.py` names `app/templates/pages/evidence_span.html`
- `tests/test_p6_7_requirement_card.py` names `app/templates/pages/evidence_span.html`, `app/templates/pages/workpaper.html`, `app/templates/components/workpaper_entry.html`, `app/routers/web.py`
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

S1 shell, then S2 component layer and `/design`, then S3 to S8 (S3 and S4 first; S5, S6 and S7 can run in parallel worktrees only if they touch no shared template; S8 after S6 and S7), then S9 system states, dark and mobile pass. This is slice **S6**.

## Stop and ask

Stop and write the question in this file's Results section (and tell the orchestrating session) if:

- a visual detail is in neither the design guide nor the approved mockup;
- two mockups disagree;
- a must-keep id, `hx-*` or `data-*` cannot be kept;
- a mockup shows an action with no route behind it that this file does not cover;
- the work needs a model, migration, prompt, scoring or PDF change.
- If a source or status cannot be derived from stored data, show what the service returns and report it; do not add a column.
- Do not change how evidence is quarantined, scanned or versioned.

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

### Review fixes

- B1: documents now redirect linked assessments to inventory and unlinked assessments to their overview; both HTTP cases are covered.
- B2: inventory fragments carry the engagement scope and owner assessment, so Archive and New version never render an empty assessment id and round trips preserve filters.
- B3: the inventory count strip reads the service’s `total`, `Available`, `Scanning`, `Rejected`, and `Out of date` keys.
- B4: the cross-engagement table adds an Engagement header and links each cell to that engagement’s inventory.
- B5: S6 imports the shared `db_path`, `engine`, `upload_root`, framework-registration, `db`, and `http` fixtures, so its tests collect and run.
- S1–S3: freshness comes from the selected assessment’s real pre-fill data; AWS error copy matches the approved preview; upload/archive/version fragments keep scope and filters, with a visible assessment choice for All assessments.
- S4: reuse candidates are independently unchecked, warning acknowledgement remains required, one button submits selected forms sequentially, stops on the first error, reloads after success, and keeps empty errors hidden; warning copy includes framework lists.
- S5–S6: upload categories come from `DocumentCategory` with the origin accept list, and evidence statuses use the shared display macro rather than raw state words.
- S7–S9: legacy documents restore the migration notice; all S6 dates use the app filter, detail links use assessment names and plain provenance labels, and the AWS role name is restored. Policy blocks use the existing `code_block` macro with its additive optional copy binding; the external ID keeps its existing copy action.
- G1–G9: the approved header/table/card structures were rebuilt for inventory, detail/span, AWS, reuse, workpaper, and workpaper-entry states; Meridian now seeds the approved 11-item/4-run dataset with real reuse candidates, and `PREVIEW_PAGES["workpaper_entry"]` renders default, legacy, and excluded component fixtures without adding a production route.

### Review fixes, round 3

- Removed production mockup state switchers from AWS, reuse, detail, span, and workpaper; retained only transient loading/error/pulling/upload preview paths, and kept the workpaper Queue/Conclusions/Findings/Workpaper seg.
- Wired inventory “Ask the client” and “Requests” to the existing `/assessments/{id}/rfi` route. Upload now opens the in-place disclosure; `?state=upload` remains only the open-panel preview.
- Preserved assessment/source/status/search filters and per-row archive/version URLs in inventory fragments. Added HTTP coverage for fragment contracts, freshness and migration notices, non-available counts, filtered empty state, display labels/actions, reuse markup, and AWS preview/copy bindings.
- Added minimal optional copy binding to the shared button/code-block macros; AWS policy blocks use it. Added debug-only `PREVIEW_PAGES["aws_evidence"]` using the real AWS page/panel templates with a fixture pull result; production query states do not fabricate an AWS result.
- Restored the P6-6 `data-report-basis` attribute and exact reporting-basis wording. Workpaper now shows compact conclusions/runs while keeping full entries reachable in collapsed details; the workpaper-entry preview renders inside the real page shell.
- Seeded distinct cited paragraphs and superseded-version text, and aligned the Meridian inventory fixture with real status counts/order/source/assessment/support/size/date data and freshness.
- Verification: full suite passed with 1463 passed and 30 skipped; focused S6/P6/workpaper/AWS checks passed (31). Design lint/S2 checks passed (16). App server binding and Chromium pixel capture remain unavailable in this sandbox, so no pixel percentage is claimed.

### Review fixes, round 4 (adversarial review)

- B2: detail-page Archive and Upload new version keep `hx-target="#detail-action-status"`; when that is the `HX-Target`, both routes answer with an empty body plus `HX-Refresh`, so the page reloads instead of receiving the inventory table (errors from a version upload still render `upload_status` into the status line). The inventory contract is unchanged. Archive/version buttons are hidden once the evidence is archived. The inventory row actions stay in the hidden actions cell: the b4-evidence mockup has no per-row actions (decision for the orchestrator).
- S3: revision history shows `Reason: <rationale after>` on edited rows and the rationale before reopening on reopened rows; earlier and withheld proposals list their own citations under the row (the current proposal's citations are in the AI proposal card). Conclusion id, client-response question id and desk-review finding type are kept as `data-conclusion-id`, `data-question-id` and `data-finding-type` (the mockup has no room for them as text).
- S4/S5: the reuse confirm button counts ticked boxes only, is disabled at 0 and reads "Confirm reuse" / "Confirm reuse of N". After a failure nothing reloads: confirmed cards are removed and the alert says "N reused before this error" with a reload link.
- N12: AWS `pulling`/`error` and the reuse acknowledgement error are reachable only through `PREVIEW_PAGES` (`preview_state`); live routes ignore `?state=`.
- S8: legacy documents render as inventory rows with the "Legacy (not migrated)" status (left out of source/status/search-filtered views); the migration notice stays.
- S9 (deferred, no change): an assessment with no engagement redirects `?tab=documents` to its overview; restoring the old documents branch needs the S5-owned assessment page.
- Also: "Out of date" uses the medium tone everywhere, files under 500 bytes show bytes, `code_block` copies from its `<pre>`, the detail and AWS pages use `engagement_tabs`, and the reuse list is a spaced stack.

### Built

- Added the engagement and cross-engagement Evidence inventory routes, backed by the merged `evidence_inventory.inventory_rows`, `cross_engagement_rows`, `status_counts`, and `prefill_freshness.freshness` read models. The explicit `?tab=documents` assessment URL now returns a 303 to `/engagements/{engagement_id}/evidence?assessment={id}`; the assessment template and stepper were left to S5.
- Moved the live upload panel and `#document-list` HTMX table into the inventory. Upload, delete, and version-upload still use the existing per-assessment routes and evidence service lifecycle; only the returned fragment context changed. The obsolete `partials/documents_tab.html` was deleted and its migration-map row is `deleted`. No `desk-review-area` was added.
- Replaced the S2 evidence badge map with `EVIDENCE_STATUS_LABELS`, populated from `evidence_inventory.STATUS_LABELS`; `Superseded` and `Legacy (not migrated)` remain neutral version-history labels. Evidence is live in the shell navigation. The visual shell clip still ends at Reports, so it now covers the live Evidence row above it; Settings, the account menu and page content stay outside.
- Restyled AWS pull, reuse, evidence detail, citation span, and read-only workpaper surfaces with Yozora components while retaining the required ids, `hx-*` targets/swaps, and `data-*` hooks. Reuse has one visible `Confirm reuse` button and a small sequential script over the existing per-candidate POST forms. It stops at the first error and shows that error; it does not provide atomic bulk confirmation, rollback, or a new route.
- Added `design/harness/seed_s6.py`. It imports S4 builders and `FROZEN_NOW` (30 Sep 2026), seeds Meridian Ledger Technologies, Loomwire Labs, and Kestrel Advisory, creates active/scanning/rejected/out-of-date/AWS/client-link/reused/versioned evidence, a completed desk review plus newer evidence for the pre-fill note, and real workpaper records. It runs `create_all` followed by `alembic stamp head` before closing the database.

### Seed state production

| Screen/state | How it is produced |
|---|---|
| Evidence `default` | `/engagements/eng-meridian/evidence` over seeded rows and real filters. |
| Evidence `upload` | Same stamped DB with `?state=upload`; the real multipart form is open. |
| Evidence `filtered` | Same DB with real `source`, `status`, `assessment`, and `search` query filters. |
| Evidence `empty` | A real no-match search query; `state=empty` no longer hides seeded rows. |
| Evidence `loading` / `error` | Explicit `?state=loading` or `?state=error` state branch; no backend data is fabricated. |
| Evidence `prefill` | `DeskReviewSummary.completed_at` is 27 Sep 2026 and active evidence arrives later; `/engagements/eng-meridian/evidence?assessment=assessment-meridian-head&state=prefill` shows the real freshness note. |
| Evidence `all` | `/evidence?state=all`, using the cross-engagement read model and Engagement column. |
| AWS `ready` / `notconfigured` | Real AWS page context. `pulling`, `error` and `result` are preview-only: `/design/pages/aws_evidence?state=...` sets `preview_state` (and, for `error`, fixture alert copy); the live route ignores `?state=`. |
| Reuse `list` / `empty` / `error` / `unlinked` | Real candidate data, the Payments subsidiary with no candidates, `/design/pages/evidence_reuse?assessment=<id>&state=error` (the confirm route's real acknowledgement error, preview-only), and the seeded `assessment-unlinked` assessment. |
| Detail `current` / `quarantined` / `unused` | Seeded evidence/version status and mapping combinations, rendered by the real detail route. |
| Span `span` / `whole` / `superseded` / `unavailable` | Real citation route data; current, superseded, whole-document, and unavailable-version branches are preserved. |
| Workpaper `list` / `empty` | `_seed_review_stage` creates real conclusions for list; the seeded Payments subsidiary has no conclusions for the empty view. The entry component keeps real response/evidence/decision/revision data rather than mockup literals. |
| Workpaper entry `default` / `legacy` / `excluded` | Existing debug-only `/design/pages/workpaper_entry?state=...` uses `PREVIEW_PAGES` fixtures and renders the component without adding a production route. |

### Tests and verification

- `pytest -q tests/test_design_lint.py tests/test_yozora_shell.py tests/test_design_harness.py tests/test_yozora_s2.py tests/test_p6_9_file_set.py tests/test_p6_8_v3b_file_set.py`: **26 passed, 2 warnings**.
- `python -m compileall -q app design/harness tests`: passed.
- `python design/harness/seed_s6.py --database /tmp/yozora-s6-test.sqlite3 --screen evidence --state prefill`: passed; the database was stamped at Alembic head. Direct read-model verification returned cross-engagement rows and `PrefillFreshness(available=2, new_since_last_prefill=2, ...)` for Meridian Head office.
- A local minimal FastAPI/TestClient smoke (web router only, because importing the full app requires the missing AWS SDK) passed the 303 redirect and HTTP upload, version-upload, and delete round trips.
- Added `tests/test_yozora_s6.py` for HTTP inventory/filter/redirect/fragment round trips and service-backed badge labels. The full fixture collection is blocked here by `ModuleNotFoundError: boto3`; the orchestrator should run it with project dependencies installed. No server, browser, network, or pixel capture is available in this environment, so no screenshot percentages are claimed.
- Existing longitudinal assertion changed from following the Documents page and checking its old reuse link to asserting the new 303 `Location`. The old/new visible reuse and workpaper strings were retained where existing tests pin them.

### Screenshots

| Screen matrix | Result |
|---|---|
| All S6 states, light/dark, 1440/1024 | Not run: browser/server are unavailable in this environment; no percentages claimed. |

### Guards, decisions, and follow-ups

- Added `YOZORA_S6_PATHS` to `tests/yozora_paths.py`, included it in `YOZORA_EXCLUDES`, and added only scoped S6 allowances to the stale file-set guards (`test_p6_9_file_set`, `test_p6_7b_add_to_rfi`, `test_p6_7_requirement_card`, `test_p6_8_b2_docx_xlsx`, `test_p6_8_board_report_v2`, `p6_10_support`, `test_longitudinal_demo`, and the new inventory test/design-lint entries). No guard was removed or weakened.
- The AWS Overview link on the assessment Overview remains unchanged as required; follow-up for S8: reconcile that link with the final Evidence navigation.
- No changes were made to quarantine, scanning, versioning, scoring, analyzer, prompt, PDF, `assessment.html`, the layout tab macros, S5 questionnaire/desk-review surfaces, or the Overview page.
- The worktree is on `codex/yozora-s6`. The requested commits could not be created because the managed workspace denies writes to the linked worktree metadata at `/Users/saqlainmomin/dpdpa-gap-tool/.git/worktrees/cyberassess-yozora-s6/index.lock` (`Operation not permitted`). No push or merge was attempted; the working-tree changes remain available for the orchestrator to commit after permissions are restored.

### Open questions / orchestrator checks

- Run the full suite with `boto3` and the S5 merge applied, then run the complete light/dark 1440/1024 pixel gate. In particular, verify the three standalone `b4-workpaper_entry` preview states and AWS result/pull states against the approved baselines.

### Pixel gate and review, cloud orchestrator (4 Oct 2026)

Visual fitting was done by subagents, not Codex, per Saqlain's decision on 4 Oct 2026. The round-three fitting on the Mac was lost when its session limit hit, so fitting restarted in a cloud session from `c17c01d`: five fitters (inventory, detail, AWS, span/reuse, workpaper), then an adversarial review and a fix round.

Gate: `design/harness/screenshot.py` logic (pixelmatch 0.1, fail above 0.4% or any changed region wider and taller than 40 px), full page, mockups served with `/static/` mapped to `app/static/`, the mockup state switcher hidden, light/dark at 1440/1024. Result: **61 of 116 shots pass**.

| State | Pass | Range |
|---|---|---|
| AWS ready, pulling, result, error | 16/16 | 0.05–0.27% |
| AWS not configured | 1/4 | 0.39–0.54% |
| Detail current / quarantined / unused | 2/4, 0/4, 4/4 | 0.04–5.70% |
| Inventory default, upload, empty, loading, error, all, prefill | 28/28 | 0.04–0.26% |
| Inventory filtered | 0/4 | 2.8–4.4% |
| Span span / whole / superseded / unavailable | 0/4, 2/4, 0/4, 2/4 | 0.21–9.6% |
| Reuse list / error / empty / unlinked | 0/4, 0/4, 4/4, 0/4 | 0.05–7.3% |
| Workpaper list / empty | 0/4, 2/4 | 0.33–15.3% |
| Workpaper entry default / legacy / excluded | 0/12 | 4.4–17.3% |

Real-data exceptions (everything else in those states matches):
- **AWS not configured:** the real operator message ("Set AWS_EXTERNAL_ID_SECRET…") is accurate for this app and wraps one line longer than the mockup's region/role wording.
- **Detail at 1024, span at 1024, workpaper list at 1024, entry default:** real registry requirement titles and ids are longer than the mockup's ("Notice to data principals / s.5") and wrap, shifting the page. Workpaper entry rows show the full stored rationale as the edit reason (no separate edit-reason field exists).
- **Detail quarantined:** the app holds only the new version for scanning (item and v2 stay available), so the mockup's item-level Scanning plus three versions is not reachable.
- **Inventory filtered:** the pre-fill note shows under an assessment filter (required by an earlier review fix and its test); the service returns only the codes mapped into the filtered assessment.
- **Span:** the route has a version id and a character range only, so no "Cited for <requirement>" and "Characters 160–377" instead of "Page 4"; the real context window shifts the first line.
- **Reuse:** real gap between cards (the mockup's cards touch only because its state script clears the flex gap); confirm button starts disabled with nothing ticked; requirement titles, relevance values and scope warnings come from real data; unlinked assessments have no engagement tabs or client crumbs.
- **Workpaper entry legacy / excluded:** real bulk-approval revision gives two history rows; the scope-enforced proposal reads Not applicable, and a never-decided conclusion cannot carry the mockup's withheld-proposal alert.
- **Shell (every page, inside thresholds):** the account tile shows the firm name (no auth until Track 4) and the review count is live.

Review fixes after the gate: detail-page Archive and Upload new version reload the page instead of swapping the inventory table into the status slot; workpaper history shows the edit reason and per-revision citations again; reuse confirm counts ticked boxes, stays disabled at zero and no longer reloads over an error; live AWS and reuse routes ignore `?state=` (transient states only through `/design/pages/...`); legacy documents listed as inventory rows with the Legacy pill; shell clip bottom kept at Reports; "Out of date" tone made consistent; sub-500-byte files no longer show "0 KB".

Decisions recorded:
- Inventory rows keep the hidden actions cell (the mockup has no per-row actions); archive and new version are reached from the detail page.
- Unlinked (unmigrated) assessments: `?tab=documents` redirects to Overview and the inventory fragments return an empty list. Deferred, not changed here.
- `#desk-review-area` is not added back in S6: S5 moves it to the Questionnaire tab and merges first.
- `tests/visual/test_shell_visual.py` clip now reaches Reports; its S1 baseline images are shorter than that clip, so the shell visual test needs new baselines when it is next run (it is skipped in the normal suite).

Suite: 1464 passed, 30 skipped, plus `test_p6_8_board_report_v2::test_scenario_3` (byte-for-byte PDF determinism), which is flaky on `main` too (2 of 8 runs failed on a clean main checkout).

### After S5 merged (5 Oct 2026)
Merged `main` (S5 and V3-C) into this branch. Full suite: 1492 passed, 30 skipped after changing one S5 test: `?tab=documents` now asserts the S6 303 to the inventory instead of the old rendered view. The gate was re-run (fast numpy mode, same matrix): 57 of 116 pass, against 61 before the merge. Four shots moved from just under the 0.4% limit to just over it, all at 1440: AWS result dark (0.27% to 0.45%), AWS not configured dark (0.39% to 0.57%), evidence detail current light and dark (0.36% and 0.35% to 0.64% and 0.63%). The diffs are text rows (account tile and real requirement titles and codes against the mockup's) and the changed regions are one text line high. S5's `.table-scroll` rule was ruled out as the cause. The remaining states are unchanged real-data exceptions.
