# Yozora S4: Engagements: list, new, Overview, Findings and actions, Reports, archive and purge

**Rewritten:** 2026-10-03 (replaces the 2026-10-01 template). **Owner:** Codex builds; Claude reviews every diff and screenshot before merge; Saqlain merges. **Depends on:** S1 and S2 merged; S3 recommended first (Clients list). PR #99 for Add assessment, the actions export and assessment stage.
**Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (work in your own git worktree of it, one branch per slice, named `codex/yozora-s4-...`). Paths below are relative to your worktree root. The specs below exist on `main` once the docs PR for this series has merged; until then branch from `claude/yozora-slice-handoffs`.

**Read first, in this order:** `docs/product/yozora-design-system.md` (the design guide), `docs/product/yozora-fidelity-gate.md`, `docs/product/2026-10-01-app-design-mockups/screens/IA-SPEC.md`, `docs/product/yozora-migration-map.md` (rows for this slice), then the mockups listed under Screens (serve them with `python3 -m http.server` from the repo root and open `/docs/product/2026-10-01-app-design-mockups/screens/<file>?state=<name>` and `&dark`). Background if you need it: `tasks/agent-ownership.md`, `CLAUDE.md`.

## Goal

Rebuild the engagement level: the Engagements list, the new-engagement flow, the engagement Overview (assessments table with Stage and Next step, Add assessment, Archive), the Findings and actions tab (the remediation tracker), the integrated Reports tab, and the destructive purge flow. After this slice the Engagements menu entry is live and engagement tabs work from the macros.

## Definition of done

- Every state under Screens matches its baseline at the thresholds, light and dark, 1440 and 1024.
- An engagement with exactly one assessment opens straight on that assessment's Overview (`/assessments/{id}`); engagements with several show the Overview table.
- `/engagements` lists engagements (new route and template, see Notes). Menu entry Engagements is `available`.
- Engagement Overview shows Stage and Next step per assessment from the stage service, an Add assessment primary, and Archive as a ghost button. No stepper on this page.
- Findings and actions has an Export actions link; the tab is titled Findings and actions.
- Retention text on the engagement reads the firm value; the engagement keeps only Archive and Unarchive.
- Must-keep ids, `hx-*` and `data-*` unchanged; tests updated deliberately.

## Screens

Mockups are in `docs/product/2026-10-01-app-design-mockups/screens/`. Match every state listed; the state names are the `?state=` values on the mockup.

| Mockup | States to match |
|---|---|
| `b2-engagement_list.html` | `default`, `empty`, `loading`, `error`. |
| `b2-new_engagement.html` | `default`, `new-client`, `empty`, `error`. |
| `b2-engagement_detail.html` | `default`, `archived`, `archiving`, `empty`, `loading`, `error`; the blocked-archive variant is `?state=blocked` on the mockup. |
| `b2-remediation_tracker.html` | `default`, `empty`, `loading`, `error`, `embedded` (the tracker table embedded in the assessment report). |
| `b2-integrated_reports.html` | `default`, `issue`, `empty`, `none-approved`, `loading`, `error`. |
| `b2-engagement_purge.html` | `default`, `blocked`, `confirm` (typed-name confirm), `error`. |

## Templates, routes and view functions in scope

**New templates this slice creates:** `pages/engagements.html`; the Add assessment form page (created by PR #99). Add a row for each to `docs/product/yozora-migration-map.md`.

Routes were found by grepping `app/routers/` for each template (helper functions are traced to their routes). Verify with `grep -rn '<template>' app` before relying on a row; if a row is wrong, fix the migration map in your PR.

| Template | Served by (method path, function) |
|---|---|
| `pages/engagement_detail.html` | `GET /engagements/{engagement_id}` `app/routers/web.py::engagement_detail` |
| `pages/engagement_purge.html` | `GET /engagements/{engagement_id}/purge` `app/routers/retention.py::purge_preview_page` |
| `pages/integrated_reports.html` | `GET /engagements/{engagement_id}/integrated-reports` `app/routers/web.py::integrated_reports_page` |
| `pages/new_engagement.html` | `GET /engagements/new` `app/routers/web.py::new_engagement_page`<br>`POST /assessments/new` `app/routers/web.py::create_assessment`<br>`POST /engagements` `app/routers/web.py::create_engagement` |
| `pages/remediation_tracker.html` | `GET /engagements/{engagement_id}/remediation` `app/routers/web.py::remediation_tracker_page` |
| `partials/engagement_list.html` | `GET /clients/{client_id}/engagements-list` `app/routers/web.py::client_engagement_list` |
| `partials/engagement_retention.html` | included by `pages/engagement_detail.html` |
| `partials/client_picker.html` | `GET /engagements/new/client-fields` `app/routers/web.py::new_engagement_client_fields` |

## Must-keep ids, `hx-*` and `data-*`

Copied from the templates as they are today (checked against `docs/product/yozora-migration-map.md`). A migration may restyle and move these but not rename, drop or re-target them. If markup must change so that one cannot stay, stop and ask.

- `pages/engagement_detail.html`: none.
- `pages/engagement_purge.html`: ids `confirm-name`, `reviewer-name`; hx-verbs `hx-post /api/engagements/{{ engagement.id }}/purge`; data-* `data-purge-count`, `data-purge-dependency`, `data-purge-files`, `data-purge-form`, `data-purge-reason`, `data-purge-reasons`
- `pages/integrated_reports.html`: ids `reviewer-name`, `{{ row.snapshot.id }}`; hx-verbs `hx-post /api/engagements/{{ engagement.id }}/integrated-reports`, `hx-post /api/engagements/{{ engagement.id }}/integrated-reports/{{ row.snapshot.id }}/issue`; data-* `data-excluded-assessment`, `data-included-assessment`, `data-integrated-row`, `data-issue-control`, `data-snapshot-id`, `data-snapshot-state`
- `pages/new_engagement.html`: ids `client-fields`, `create-engagement`, `description`, `engagement_name`, `engagement_type`, `new-engagement-form`; hx-target `#client-fields`; hx-swap `innerHTML`; hx-verbs `hx-get /engagements/new/client-fields?mode=existing`, `hx-get /engagements/new/client-fields?mode=new`
- `pages/remediation_tracker.html`: ids `assessment-{{ row.assessment_id }}`; data-* `data-assessment-row`, `data-awaiting-action`, `data-overdue-action`, `data-owner-row`, `data-rollup-count`, `data-severity-row`
- `partials/engagement_list.html`: none.
- `partials/engagement_retention.html`: ids `reviewer-name`; hx-verbs `hx-post /api/engagements/{{ engagement.id }}/archive`, `hx-post /api/engagements/{{ engagement.id }}/unarchive`; data-* `data-archive-control`, `data-archived-banner`, `data-purge-preview-link`, `data-retention-panel`, `data-unarchive-control`
- `partials/client_picker.html`: ids `client_id`, `company_name`, `company_size`, `industry`

## Build notes

**Engagements list.** No firm-wide list exists today. Add `GET /engagements` and `app/templates/pages/engagements.html` to `b2-engagement_list.html` (columns engagement, client, frameworks, stage, last activity, filters via `.tools`). `partials/engagement_list.html` is the client-scoped list used by client detail; restyle it with the same table component. Add a migration-map row for the new template.

**Single-assessment redirect.** In `engagement_detail` (`GET /engagements/{engagement_id}`), when the engagement has exactly one non-archived assessment, return a 303 to `/assessments/{id}`. Add a test. Archived engagements still show the Overview (read-only) so the archived banner and Unarchive are reachable.

**Add assessment.** Button on the Overview. Route and form come from PR #99 (`GET /engagements/{id}/assessments/new`, `POST /engagements/{id}/assessments`, `Assessment.name`). That PR creates a minimal template; restyle it as a form page using the `.form-narrow` pattern. Display the assessment name with the same fallback as the model.

**Stage and Next step columns.** Call `assessment_stage.stage(db, assessment)` per row in the `engagement_detail` view; pass a list of row view-models to the template. Do not compute stage in the template.

**Findings and actions.** `remediation_tracker_page` (`GET /engagements/{engagement_id}/remediation`). Rename visible copy to Findings and actions (the URL stays). Add the Export actions link to PR #99's `GET /engagements/{id}/remediation/export.xlsx`. `partials/remediation_summary.html` and `partials/remediation_panel.html` are included by the assessment report (S7), not here; do not touch them. The tracker uses priority as words (Do first, Next, Planned, Backlog); never render the numeric priority.

**Purge.** `pages/engagement_purge.html` is a destructive confirm. Typed-name confirmation: the destructive button is disabled until the field equals the engagement name; keep ids `confirm-name` and `reviewer-name` (temporary name field, see the rule) and every `data-purge-*` attribute.

**Archive control.** `partials/engagement_retention.html` is included by `engagement_detail.html`. Under the firm-level retention change it keeps only archive and unarchive, the archived banner and the purge-preview link; its retention text reads `FirmSettings.archived_retention_years` through `app/services/firm_settings.py`. Keep `data-archive-control`, `data-archived-banner`, `data-purge-preview-link`, `data-retention-panel`, `data-unarchive-control`.

**Client links on the Overview, until S8.** `engagement_detail.html` includes `partials/magic_links.html` (line 76), the only place staff can create a client link today. The approved Overview has no such section: client links move to Evidence / Requests, which S8 builds (`GET /engagements/{id}/requests`). Until S8 merges, keep the include on the page, render it with the existing markup inside a wrapper carrying `data-visual-mask`, and say in Results that this region is a temporary exception to the baseline. S8 removes the include. Do not delete the include in S4; that would leave staff with no way to create a link.

**New engagement.** `GET /engagements/new` plus `GET /engagements/new/client-fields` (HTMX, target `#client-fields`, swap `innerHTML`) and `POST /engagements`. `partials/client_picker.html` (ids `client_id`, `company_name`, `company_size`, `industry`) is the swapped fragment. The assessment-creation routes (`POST /assessments`, `POST /assessments/new`) also render this template on error; keep both error paths.

## Backend dependency

PR #99, https://github.com/saqlainmmomin/Cyber/pull/99, carries the server-side work for the redesign; its spec is `tasks/handoffs/2026-10-03-yozora-backend-features.md` on branch `claude/yozora-backend-features`. **Do not re-specify or re-implement it here.** At the time this handoff was written #99 held only its spec (no code), so this file names the planned modules from that spec: if #99 has merged by the time you start, read the real function names from the code and use those; if it has not, follow the 'if not merged' instruction in the Build notes.

PR #99: Add assessment (route, `Assessment.name`), actions export, `assessment_stage.stage`, `firm_settings.get`. **Not covered by #99:** the `/engagements` list page (read-only queries inside this slice).

## Tests

**Existing tests that exercise this slice** (route calls matched against this slice's routes, plus tests that name its templates). Run them first and again after each template change.

| Test file | Calls to this slice's routes | Mentions its templates |
|---|---|---|
| `tests/test_retention.py` | 11 | 0 |
| `tests/test_longitudinal_demo.py` | 8 | 0 |
| `tests/test_pdf_updates.py` | 6 | 1 |
| `tests/test_remediation_tracking.py` | 4 | 0 |
| `tests/test_magic_links.py` | 2 | 0 |
| `tests/test_aws_evidence.py` | 1 | 0 |
| `tests/test_picker_and_scoring_contract.py` | 1 | 0 |
| `tests/test_white_label.py` | 1 | 0 |

Strings such as `text-amber-700` are Tailwind classes that a test pins; the redesign removes Tailwind from the page, so those tests must be rewritten to assert the `data-*` attribute or the visible text instead, and the change listed in the PR.

**Asserted strings likely to change.** These literals appear in `assert ... in ...` lines of the tests above and also verbatim in this slice's templates today; if a restyle changes or removes one, edit the test deliberately and list the change in the PR description (old string, new string, reason).

- "Draft (superseded)": test_pdf_updates.py:993
- "Eligible for permanent purge on or after": test_retention.py:671
- "Issued (current)": test_pdf_updates.py:992
- "No actions in this engagement yet.": test_remediation_tracking.py:1009
- "No versions generated yet.": test_pdf_updates.py:983
- "consultant:": test_remediation_tracking.py:995
- "not compliance scores": test_remediation_tracking.py:994

**Page text asserted by tests that fetch this slice's routes** (not necessarily from this slice's own templates; the test may be reading text that comes from an included partial or the shell). Check each one when you restyle the page it comes from.

- "Add at least one requested item.": test_magic_links.py:409
- "Baseline gap assessment (DPDPA + ISO 27001)": test_longitudinal_demo.py:221
- "File received: ISMS Policy.pdf": test_magic_links.py:540
- "Files removed": test_retention.py:1314
- "ISMS Policy.pdf": test_magic_links.py:587
- "Incident response plan": test_longitudinal_demo.py:226
- "Information security policy": test_longitudinal_demo.py:225
- "Momin &amp; Co": test_white_label.py:102
- "NIST CSF 2.0 baseline gap assessment": test_longitudinal_demo.py:224
- "Not approved for release": test_pdf_updates.py:957
- "Remediation validation (ISO 27001)": test_longitudinal_demo.py:222

**New tests to add:**

- Single-assessment engagement returns 303 to the assessment; two assessments render the Overview table.
- `GET /engagements` lists engagements.
- Overview rows show Stage and Next step from the stage service.
- Findings and actions page links the export and shows priority as words with no numeric priority.

## File-set guard

Many tests are scope guards: they diff the branch against `main` and fail when a file outside an allow-list changes (the P6-2b scenario 11 guard in `tests/test_p6_2b_dpdpa_criteria.py`, the P6-9 file-set guard in `tests/test_p6_9_file_set.py`, and several older `:(exclude)` guards). They were written for earlier PRs and are stale for this one. **Never delete or weaken a guard.** Add a scoped allowance instead, the way `tests/p6_8_v3a_paths.py` does for V3-A:

1. S1 creates `tests/yozora_paths.py` with one tuple per slice (`YOZORA_S1_PATHS`, ...) and `YOZORA_EXCLUDES = [f":(exclude){p}" for p in ...]` over all tuples. Each later slice adds its own tuple (every file it adds or changes outside `docs/product/` and `design/`) to that module.
2. Run the full suite. For each guard that fails on your files, splat `*YOZORA_EXCLUDES` into its pathspec list (or import the tuple into its allow-list), exactly as `V3A_EXCLUDES` is imported by `tests/test_p5_6_rfi_rebuild.py`. Add a comment `# Yozora per-PR allowance`.
3. Keep this slice's handoff file and `YOZORA_DESIGN_FILES` allowed (already done for `tasks/handoffs/2026-10-01-yozora-s*-handoff.md`).
4. List every guard you touched in the PR description.

**This slice's `YOZORA_S4_PATHS` starts as:**

- `app/templates/pages/engagement_detail.html`
- `app/templates/pages/engagement_purge.html`
- `app/templates/pages/integrated_reports.html`
- `app/templates/pages/new_engagement.html`
- `app/templates/pages/remediation_tracker.html`
- `app/templates/partials/engagement_list.html`
- `app/templates/partials/engagement_retention.html`
- `app/templates/partials/client_picker.html`
- `app/templates/pages/engagements.html`
- `app/routers/web.py`
- `app/routers/retention.py`
- plus every test, CSS, JS and fixture file you add or change.

**Guards found today that name this slice's files** (expect these to need the allowance; there may be more):

- `tests/test_longitudinal_demo.py` names `app/routers/web.py`
- `tests/test_p6_3a_grounding.py` names `app/routers/web.py`
- `tests/test_p6_7_requirement_card.py` names `app/routers/web.py`
- `tests/test_p6_7b_add_to_rfi.py` names `app/routers/web.py`
- `tests/test_p6_8_b2_docx_xlsx.py` names `app/routers/web.py`
- `tests/test_p6_8_board_report_v2.py` names `app/routers/web.py`
- `tests/test_p6_9_file_set.py` names `app/routers/web.py`
- `tests/test_p6_nist_csf2_alignment.py` names `app/routers/web.py`
- `tests/test_retention.py` names `app/routers/retention.py`

## Screenshot gate

Use the harness from S1 (`design/harness/README.md`). Render each screen listed above in every state, light and dark, at 1440 and 1024. Baselines are the approved mockups rendered at the same viewport with `?state=<name>` and `?dark`, saved as `design/baselines/<screen>-<state>-<theme>-<width>.png` (S1 defines the exact naming; include the state in the name when the screen has several). Candidates use seeded demo data (the fictional Meridian Ledger Technologies, Loomwire Labs and Kestrel Advisory companies from the mockups) with the clock frozen and fonts vendored.

Thresholds from the fidelity gate: colour tolerance 0.1 (pixelmatch); fail above **0.4%** differing pixels on app screens and **0.2%** on `/design`; fail on any single changed region over 40x40 px regardless of the total. Mask dynamic regions with `data-visual-mask`. Loosening a threshold needs a written reason in the PR.

In the PR, post for each screen and state: the baseline, the candidate and the diff image side by side, plus the differing-pixel percentage. Saqlain sees these before merge (gate 4). CI green is necessary, not sufficient.

## Dependency order

S1 shell, then S2 component layer and `/design`, then S3 to S8 (S3 and S4 first; S5, S6 and S7 can run in parallel worktrees only if they touch no shared template; S8 after S6 and S7), then S9 system states, dark and mobile pass. This is slice **S4**.

## Stop and ask

Stop and write the question in this file's Results section (and tell the orchestrating session) if:

- a visual detail is in neither the design guide nor the approved mockup;
- two mockups disagree;
- a must-keep id, `hx-*` or `data-*` cannot be kept;
- a mockup shows an action with no route behind it that this file does not cover;
- the work needs a model, migration, prompt, scoring or PDF change.
- If the mockup shows an engagement-level action with no route behind it, stop and ask.
- If #99 is not merged, build only the screens that do not need it (list, new engagement, integrated reports, purge), say what is blocked, and stop.

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
