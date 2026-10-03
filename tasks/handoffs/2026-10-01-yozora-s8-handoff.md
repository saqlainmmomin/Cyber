# Yozora S8: Requests, report versions, applicability, compare, client-facing pages

**Rewritten:** 2026-10-03 (replaces the 2026-10-01 template). **Owner:** Codex builds; Claude reviews every diff and screenshot before merge; Saqlain merges. **Depends on:** S1 and S2 merged; S6 (Evidence inventory and its seg row) and S7 recommended first. PR #99 for client contacts, Email the firm and Open current report.
**Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (work in your own git worktree of it, one branch per slice, named `codex/yozora-s8-...`). Paths below are relative to your worktree root. The specs below exist on `main` once the docs PR for this series has merged; until then branch from `claude/yozora-slice-handoffs`.

**Read first, in this order:** `docs/product/yozora-design-system.md` (the design guide), `docs/product/yozora-fidelity-gate.md`, `docs/product/2026-10-01-app-design-mockups/screens/IA-SPEC.md`, `docs/product/yozora-migration-map.md` (rows for this slice), then the mockups listed under Screens (serve them with `python3 -m http.server` from the repo root and open `/docs/product/2026-10-01-app-design-mockups/screens/<file>?state=<name>` and `&dark`). Background if you need it: `tasks/agent-ownership.md`, `CLAUDE.md`.

## Goal

Rebuild everything that leaves or re-enters through the client: the engagement Requests view (client links as request cards), the RFI page, report versions, the statement of applicability, report comparison, and the three client-facing pages (upload, expired/invalid link). After this slice the Reports menu entry is live.

## Definition of done

- Every state under Screens matches its baseline at the thresholds, light and dark; client-facing pages also at 390 (touch size 44px).
- Client links render as request cards (requested items, 'N of M received', expiry, per-item checklist) using the `.req*` and `.mk` components.
- The upload page greets the contact's first name when present; the invalid, expired and revoked pages show 'Email <firm>' only when the firm contact email is set, and never put the token in the mailto.
- Comparison has an Open current report link; the statement of applicability saves in one action; one Generate button follows the report tab.
- `/reports` exists (see Notes) or Reports is not in the menu. Menu entry is flipped only when the page exists.
- Must-keep ids, `hx-*` and `data-*` unchanged; tests updated deliberately.

## Screens

Mockups are in `docs/product/2026-10-01-app-design-mockups/screens/`. Match every state listed; the state names are the `?state=` values on the mockup.

| Mockup | States to match |
|---|---|
| `b6-magic_links.html` | `default`, `empty`, `error`, `loading`, `newlink` (shown once at creation), `revoke`. Engagement / Evidence / Requests. |
| `b6-rfi.html` | `default`, `error`, `issue`, `loading`, `noscope`, `versions`. Engagement / Evidence / Requests / one assessment request. |
| `b6-report_snapshots.html` | `default`, `empty`, `error`, `issue`, `loading`, `board`, `unreleased`. Assessment / Report / Versions. |
| `b6-soa.html` | `default`, `empty`, `error`, `loading`, `saving`, `saved`. |
| `b6-comparison.html` | `default`, `empty`, `error`, `iso`, `loading`. |
| `b6-magic_upload.html` | `default`, `uploading`, `done`, `error`. Client page, no side menu, 390 and 1440. |
| `b6-magic_invalid.html` | `expired`, `revoked`, `unknown`. |
| `b7-link-expired.html` | the expired-link page at 390 with Email the firm; same template as b6-magic_invalid (`magic/invalid.html`). The two mockups use different sample firm names and expiry copy ('14 days'); see Open questions in the orchestration file; build to `b6-magic_invalid` and match b7-link-expired visually. |

## Templates, routes and view functions in scope

**New templates this slice creates:** `pages/requests.html`. Add a row for each to `docs/product/yozora-migration-map.md`.

Routes were found by grepping `app/routers/` for each template (helper functions are traced to their routes). Verify with `grep -rn '<template>' app` before relying on a row; if a row is wrong, fix the migration map in your PR.

| Template | Served by (method path, function) |
|---|---|
| `magic/invalid.html` | `GET /magic/{token}` `app/routers/magic.py::get_magic_link`<br>`POST /magic/{token}` `app/routers/magic.py::post_magic_link` |
| `magic/upload.html` | `GET /magic/{token}` `app/routers/magic.py::get_magic_link`<br>`POST /magic/{token}` `app/routers/magic.py::post_magic_link` |
| `pages/comparison.html` | `GET /assessments/{assessment_id}/compare/{other_id}` `app/routers/web.py::comparison_page` |
| `pages/report_snapshots.html` | `GET /assessments/{assessment_id}/snapshots` `app/routers/web.py::snapshots_page` |
| `pages/rfi.html` | `GET /assessments/{assessment_id}/rfi` `app/routers/web.py::rfi_page` |
| `pages/soa.html` | `GET /assessments/{assessment_id}/soa` `app/routers/soa.py::soa_page` |
| `partials/magic_links.html` | `POST /engagements/{engagement_id}/magic-links` `app/routers/magic.py::create_magic_link`<br>`POST /engagements/{engagement_id}/magic-links/{link_id}/revoke` `app/routers/magic.py::revoke_magic_link` |
| `partials/rfi_links.html` | `POST /assessments/{assessment_id}/rfi/versions/{snapshot_id}/magic-links` `app/routers/magic.py::create_rfi_magic_link` |

## Must-keep ids, `hx-*` and `data-*`

Copied from the templates as they are today (checked against `docs/product/yozora-migration-map.md`). A migration may restyle and move these but not rename, drop or re-target them. If markup must change so that one cannot stay, stop and ask.

- `magic/invalid.html`: none.
- `magic/upload.html`: ids `file-upload`, `item-key`
- `pages/comparison.html`: none.
- `pages/report_snapshots.html`: ids `reviewer-name`, `{{ row.snapshot.id }}`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/snapshots`, `hx-post /api/assessments/{{ assessment.id }}/snapshots/{{ row.snapshot.id }}/issue`; data-* `data-board-export`, `data-board-report-preview`, `data-issue-control`, `data-narrative-link`, `data-snapshot-id`, `data-snapshot-row`, `data-snapshot-state`, `data-snapshot-type`, `data-soa-link`
- `pages/rfi.html`: ids `reviewer-name`, `{{ evidence_request.conclusion_id }}`, `{{ row.snapshot.id }}`; hx-swap `none`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/rfi-requests/{{ evidence_request.conclusion_id }}/withdraw`, `hx-post /api/assessments/{{ assessment.id }}/rfi/versions`, `hx-post /api/assessments/{{ assessment.id }}/rfi/versions/{{ row.snapshot.id }}/issue`; data-* `data-conclusion-id`, `data-rfi-generate-form`, `data-rfi-issue-control`, `data-rfi-item`, `data-rfi-kind`, `data-rfi-mapped`, `data-rfi-omit`, `data-rfi-preview`, `data-rfi-request`, `data-rfi-requests`, `data-rfi-requests-note`, `data-rfi-scope-required`, `data-rfi-version-row`, `data-rfi-versions`, `data-rfi-withdraw-form`, `data-snapshot-id`, `data-snapshot-state`
- `pages/soa.html`: ids `reviewer-name`; hx-swap `none`; hx-verbs `hx-post /api/assessments/{{ assessment.id }}/soa/justifications`; data-* `data-applicability`, `data-approved-rationale`, `data-soa-justification-form`, `data-soa-row`
- `partials/magic_links.html`: ids `magic-links`, `requested-items`; hx-target `#magic-links`; hx-swap `outerHTML`; hx-verbs `hx-post /engagements/{{ engagement_id }}/magic-links`, `hx-post /engagements/{{ engagement_id }}/magic-links/{{ link.id }}/revoke`
- `partials/rfi_links.html`: ids `rfi-links`; hx-target `#rfi-links`; hx-swap `outerHTML`; hx-verbs `hx-post /assessments/{{ assessment.id }}/rfi/versions/{{ current_issue.id }}/magic-links`; data-* `data-rfi-coverage`, `data-rfi-link-error`, `data-rfi-link-form`, `data-rfi-link-row`, `data-rfi-links`, `data-rfi-new-link`, `data-rfi-received`, `data-rfi-unsent`

## Build notes

**Requests view.** `partials/magic_links.html` is rendered by `_render_consultant` in `app/routers/magic.py` (`#magic-links`, swap `outerHTML`; routes `POST /engagements/{engagement_id}/magic-links`, `POST .../magic-links/{link_id}/revoke`). `partials/rfi_links.html` (`#rfi-links`) is the per-RFI-version link list (`POST /assessments/{assessment_id}/rfi/versions/{snapshot_id}/magic-links`). Both move under the engagement Evidence tab, Requests seg view. Contact name and email on links come from PR #99 (`MagicLink.contact_name`, `contact_email`); render them in the row when present. The mockup's tick-box item picker (`.req-pick`) is a UI change PR #99 deliberately left out: today requested items are free text (engagement route) or RFI items. Keep the current inputs and ids `requested-items`; show the picker only if Saqlain asks for it, and say so in Results.

**New Requests page.** The Requests view page itself (`b6-magic_links`) is the engagement-level list of all request cards. Today `partials/magic_links.html` is only included by `engagement_detail.html` (line 76; S4 keeps that include until now) and returned by `_render_consultant` after create and revoke. Remove the include from the Overview, and add `GET /engagements/{engagement_id}/requests` (view function in `app/routers/magic.py`, reusing `_consultant_context`; template `app/templates/pages/requests.html`, migration-map row) that renders the cards for the engagement using `app/services/request_summary.py` (PR #99) for received counts. Stop and ask if the data it needs is not on the existing link and RFI models.

**RFI page.** `GET /assessments/{assessment_id}/rfi` (`web.py`, `rfi_page`) with the version list and the generate/issue/withdraw controls (`app/routers/snapshots.py`, `POST /assessments/{id}/rfi/versions`, `.../issue`, `.../docx`). A request page shows only its own seg: Items, Versions, Client links. The breadcrumb leads back to Evidence and Requests. It is heavily asserted by tests.

**Report versions and statement of applicability.** `GET /assessments/{assessment_id}/snapshots` (`snapshots_page`, `web.py`) lists versions (`data-snapshot-*`, board export, preview). `GET /assessments/{assessment_id}/soa` (`app/routers/soa.py`) with `POST /api/assessments/{id}/soa/justifications`: one save for the whole page rather than per row; keep `data-soa-justification-form`, `data-soa-row`, `data-applicability`. The Applicability seg item is shown only when ISO 27001 is in scope; framework copy stays conditional.

**Comparison.** `GET /assessments/{assessment_id}/compare/{other_id}` (`comparison_page`). Add the Open current report link from PR #99 (the context carries the current assessment's report URL). Scores are shown per framework, never combined.

**Client pages.** `GET /magic/{token}` and `POST /magic/{token}` (`magic.py`: `_render_upload`, `_render_invalid`). `magic/upload.html` is a request card for the client: keep ids `file-upload` and `item-key`, the per-item upload forms and the token handling. `magic/invalid.html` covers expired, revoked and unknown links with one template; never reveal the engagement or client name beyond what it shows today. Use `.touch` controls and the client page shell (no side menu). Greeting uses the contact's first name only when PR #99's field exists and is set.

**Reports menu.** The side-menu Reports entry has no destination and the mockups draw none (`b6-report_snapshots` is per assessment). Proposed minimal page, to confirm with Saqlain: `GET /reports` lists issued and released report versions across engagements (client, engagement, assessment, version, date), each linking to its assessment's Versions page; empty state "No reports yet". If he declines, drop Reports from the menu. Do not build it unconfirmed.

## Backend dependency

PR #99, https://github.com/saqlainmmomin/Cyber/pull/99, carries the server-side work for the redesign; its spec is `tasks/handoffs/2026-10-03-yozora-backend-features.md` on branch `claude/yozora-backend-features`. **Do not re-specify or re-implement it here.** At the time this handoff was written #99 held only its spec (no code), so this file names the planned modules from that spec: if #99 has merged by the time you start, read the real function names from the code and use those; if it has not, follow the 'if not merged' instruction in the Build notes.

PR #99: `MagicLink.contact_name` and `contact_email`, creation routes accepting them, the invalid-page mailto from `FirmSettings.contact_email`, the comparison context's current-report URL, `app/services/request_summary.py`. **Not covered by #99:** the Requests page route (`/engagements/{id}/requests`) and the optional `/reports` list; both read-only.

## Tests

**Existing tests that exercise this slice** (route calls matched against this slice's routes, plus tests that name its templates). Run them first and again after each template change.

| Test file | Calls to this slice's routes | Mentions its templates |
|---|---|---|
| `tests/test_magic_links.py` | 19 | 0 |
| `tests/test_p5_6_rfi_rebuild.py` | 13 | 2 |
| `tests/test_p6_7b_add_to_rfi.py` | 3 | 4 |
| `tests/test_retention.py` | 6 | 0 |
| `tests/test_p6_9_soa.py` | 5 | 0 |
| `tests/test_p6_8_board_report_v2.py` | 1 | 3 |
| `tests/test_report_snapshots.py` | 4 | 0 |
| `tests/test_p6_2b_dpdpa_criteria.py` | 0 | 3 |
| `tests/test_p6_3a_grounding.py` | 0 | 3 |
| `tests/test_p6_4_cap_upload_limit.py` | 0 | 3 |
| `tests/test_p6_4_whats_missing.py` | 0 | 3 |
| `tests/test_p6_7_requirement_card.py` | 0 | 3 |
| `tests/test_no_blended_scoring.py` | 2 | 0 |
| `tests/test_p6_8_b2_docx_xlsx.py` | 1 | 1 |
| `tests/test_p6_9_file_set.py` | 0 | 2 |
| `tests/test_p6_10b_narrative.py` | 1 | 0 |
| `tests/test_p6_8_v3a_data_capture.py` | 0 | 1 |

Strings such as `text-amber-700` are Tailwind classes that a test pins; the redesign removes Tailwind from the page, so those tests must be rewritten to assert the `data-*` attribute or the visible text instead, and the change listed in the PR.

**Asserted strings likely to change.** These literals appear in `assert ... in ...` lines of the tests above and also verbatim in this slice's templates today; if a restyle changes or removes one, edit the test deliberately and list the change in the PR description (old string, new string, reason).

- ">Issued<": test_report_snapshots.py:757
- "Draft (superseded)": test_report_snapshots.py:758
- "Framework Scores": test_no_blended_scoring.py:490
- "Generating a gap report requires the report to be released.": test_report_snapshots.py:775
- "Issued (current)": test_report_snapshots.py:757
- "Received": test_magic_links.py:587
- "Statement of Applicability": test_p6_9_soa.py:250
- "This link has reached its upload limit.": test_magic_links.py:656
- "font-weight: 600": test_p6_8_v3a_data_capture.py:801
- "font-weight: 700": test_p6_8_v3a_data_capture.py:801

**Page text asserted by tests that fetch this slice's routes** (not necessarily from this slice's own templates; the test may be reading text that comes from an included partial or the shell). Check each one when you restyle the page it comes from.

- "Not in scope: no outsourcing.": test_p6_9_soa.py:204, test_p6_9_soa.py:208
- "Add at least one requested item.": test_magic_links.py:409
- "Choose a file to upload.": test_magic_links.py:608
- "Choose one of the requested items.": test_magic_links.py:604
- "Evidence already mapped for 1 of": test_p5_6_rfi_rebuild.py:938
- "File received: ISMS Policy.pdf": test_magic_links.py:540
- "ISMS Policy.pdf": test_magic_links.py:587
- "ISO 27001": test_no_blended_scoring.py:501
- "Magic link is already revoked.": test_magic_links.py:788
- "Overall Score": test_no_blended_scoring.py:491
- "Rationale for ISO.A5.5": test_p6_9_soa.py:197
- "This link has reached its upload limit. Contact your consultant.": test_magic_links.py:649
- "This upload would exceed the total size limit for this link.": test_magic_links.py:688
- "You have already uploaded this file through this link.": test_magic_links.py:705

**New tests to add:**

- `GET /engagements/{id}/requests` renders the cards; the Overview no longer includes the links partial.
- Request cards: requested items, 'N of M received', expiry and per-item markers render from the link data.
- Invalid page: mailto present only when the firm contact email is set; the token never appears in it; the page does not reveal the engagement or client.
- Upload page greets the contact's first name only when present.
- Comparison page contains the Open current report link; SoA saves with one POST for the page.

## File-set guard

Many tests are scope guards: they diff the branch against `main` and fail when a file outside an allow-list changes (the P6-2b scenario 11 guard in `tests/test_p6_2b_dpdpa_criteria.py`, the P6-9 file-set guard in `tests/test_p6_9_file_set.py`, and several older `:(exclude)` guards). They were written for earlier PRs and are stale for this one. **Never delete or weaken a guard.** Add a scoped allowance instead, the way `tests/p6_8_v3a_paths.py` does for V3-A:

1. S1 creates `tests/yozora_paths.py` with one tuple per slice (`YOZORA_S1_PATHS`, ...) and `YOZORA_EXCLUDES = [f":(exclude){p}" for p in ...]` over all tuples. Each later slice adds its own tuple (every file it adds or changes outside `docs/product/` and `design/`) to that module.
2. Run the full suite. For each guard that fails on your files, splat `*YOZORA_EXCLUDES` into its pathspec list (or import the tuple into its allow-list), exactly as `V3A_EXCLUDES` is imported by `tests/test_p5_6_rfi_rebuild.py`. Add a comment `# Yozora per-PR allowance`.
3. Keep this slice's handoff file and `YOZORA_DESIGN_FILES` allowed (already done for `tasks/handoffs/2026-10-01-yozora-s*-handoff.md`).
4. List every guard you touched in the PR description.

**This slice's `YOZORA_S8_PATHS` starts as:**

- `app/templates/magic/invalid.html`
- `app/templates/magic/upload.html`
- `app/templates/pages/comparison.html`
- `app/templates/pages/report_snapshots.html`
- `app/templates/pages/rfi.html`
- `app/templates/pages/soa.html`
- `app/templates/partials/magic_links.html`
- `app/templates/partials/rfi_links.html`
- `app/templates/pages/requests.html`
- `app/routers/magic.py`
- `app/routers/snapshots.py`
- `app/routers/soa.py`
- `app/routers/web.py`
- plus every test, CSS, JS and fixture file you add or change.

**Guards found today that name this slice's files** (expect these to need the allowance; there may be more):

- `tests/test_longitudinal_demo.py` names `app/routers/magic.py`, `app/routers/web.py`
- `tests/test_p5_6_rfi_rebuild.py` names `app/templates/pages/rfi.html`, `app/templates/partials/rfi_links.html`
- `tests/test_p6_2b_dpdpa_criteria.py` names `app/templates/pages/report_snapshots.html`, `app/templates/pages/rfi.html`, `app/templates/pages/soa.html`, `app/routers/snapshots.py`, `app/routers/soa.py`
- `tests/test_p6_3a_grounding.py` names `app/templates/pages/report_snapshots.html`, `app/templates/pages/rfi.html`, `app/templates/pages/soa.html`, `app/routers/snapshots.py`, `app/routers/soa.py`, `app/routers/web.py`
- `tests/test_p6_4_cap_upload_limit.py` names `app/templates/pages/report_snapshots.html`, `app/templates/pages/rfi.html`, `app/templates/pages/soa.html`, `app/routers/snapshots.py`, `app/routers/soa.py`
- `tests/test_p6_4_whats_missing.py` names `app/templates/pages/report_snapshots.html`, `app/templates/pages/rfi.html`, `app/templates/pages/soa.html`, `app/routers/snapshots.py`, `app/routers/soa.py`
- `tests/test_p6_7_requirement_card.py` names `app/templates/pages/report_snapshots.html`, `app/templates/pages/rfi.html`, `app/templates/pages/soa.html`, `app/routers/snapshots.py`, `app/routers/soa.py`, `app/routers/web.py`
- `tests/test_p6_7b_add_to_rfi.py` names `app/templates/pages/report_snapshots.html`, `app/templates/pages/rfi.html`, `app/templates/pages/soa.html`, `app/templates/partials/rfi_links.html`, `app/routers/magic.py`, `app/routers/snapshots.py` ...
- `tests/test_p6_8_b2_docx_xlsx.py` names `app/templates/pages/report_snapshots.html`, `app/routers/snapshots.py`, `app/routers/soa.py`, `app/routers/web.py`
- `tests/test_p6_8_board_report_v2.py` names `app/templates/pages/report_snapshots.html`, `app/templates/pages/rfi.html`, `app/templates/pages/soa.html`, `app/routers/snapshots.py`, `app/routers/soa.py`, `app/routers/web.py`
- `tests/test_p6_8_v3a_data_capture.py` names `app/templates/pages/report_snapshots.html`, `app/routers/snapshots.py`
- `tests/test_p6_9_file_set.py` names `app/templates/pages/report_snapshots.html`, `app/templates/pages/soa.html`, `app/routers/snapshots.py`, `app/routers/soa.py`, `app/routers/web.py`
- `tests/test_p6_nist_csf2_alignment.py` names `app/routers/snapshots.py`, `app/routers/soa.py`, `app/routers/web.py`

## Screenshot gate

Use the harness from S1 (`design/harness/README.md`). Render each screen listed above in every state, light and dark, at 1440 and 1024, and 390 for the client-facing pages (`b6-magic_upload`, `b6-magic_invalid`, `b7-link-expired`). Baselines are the approved mockups rendered at the same viewport with `?state=<name>` and `?dark`, saved as `design/baselines/<screen>-<state>-<theme>-<width>.png` (S1 defines the exact naming; include the state in the name when the screen has several). Candidates use seeded demo data (the fictional Meridian Ledger Technologies, Loomwire Labs and Kestrel Advisory companies from the mockups) with the clock frozen and fonts vendored.

Thresholds from the fidelity gate: colour tolerance 0.1 (pixelmatch); fail above **0.4%** differing pixels on app screens and **0.2%** on `/design`; fail on any single changed region over 40x40 px regardless of the total. Mask dynamic regions with `data-visual-mask`. Loosening a threshold needs a written reason in the PR.

In the PR, post for each screen and state: the baseline, the candidate and the diff image side by side, plus the differing-pixel percentage. Saqlain sees these before merge (gate 4). CI green is necessary, not sufficient.

## Dependency order

S1 shell, then S2 component layer and `/design`, then S3 to S8 (S3 and S4 first; S5, S6 and S7 can run in parallel worktrees only if they touch no shared template; S8 after S6 and S7), then S9 system states, dark and mobile pass. This is slice **S8**.

## Stop and ask

Stop and write the question in this file's Results section (and tell the orchestrating session) if:

- a visual detail is in neither the design guide nor the approved mockup;
- two mockups disagree;
- a must-keep id, `hx-*` or `data-*` cannot be kept;
- a mockup shows an action with no route behind it that this file does not cover;
- the work needs a model, migration, prompt, scoring or PDF change.
- Never place the token in a URL parameter other than the existing path, in a mailto, in a log line or in a screenshot baseline: use a fixed fake token in fixtures.
- If the Requests page needs a field the models lack, stop and ask.
- If Saqlain has not confirmed `/reports`, skip it.

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
