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

(Codex fills in: what was built, the screenshots table with percentages, tests changed with old and new strings, guards touched, decisions made, open questions, full-suite summary line.)
