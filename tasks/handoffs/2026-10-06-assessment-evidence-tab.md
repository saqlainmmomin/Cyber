# Handoff: assessment Evidence tab (Evidence + Requests inside the assessment)

Owner: Codex implements, Claude reviews adversarially, Saqlain approves and merges (`tasks/agent-ownership.md`).
**Branch off `main` only after PR 117 (RFI and Requests consolidation) is merged.** This work edits `rfi.html`, `document_list.html` and `tests/yozora_paths.py`, which 117 also edits. Branch name: `codex/assessment-evidence-tab`. One PR. No Claude/Codex attribution lines in commits or the PR body. Do not merge. Never open `validation/companies/*/answer_key.json`. No LLM calls, no PDF code.

## 1. Problem (from Saqlain's walkthrough, 6 Oct)

Inside an assessment there is no direct way to reach evidence or requests. The assessment tab bar is Overview, Scope, Questionnaire, Review, Report. Evidence is a stepper step that 303-redirects to the **engagement-level** page, which switches the header and tabs from assessment to engagement and loses the context. Requests is only reachable via Scope "Prepare RFI", a buried dropdown item, or top-level Evidence.

## 2. Decision (approved by Saqlain)

Add a sixth assessment tab, **Evidence**, placed after Scope: **Overview · Scope · Evidence · Questionnaire · Review · Report**. This deliberately reverses the "Evidence lives on the engagement only" line in `flow-map.html`, `IA-SPEC.md` and `yozora-design-system.md:28`. The stepper keeps its 5 stages.

- Evidence tab = new page `GET /assessments/{id}/evidence`: the inventory, scoped to the assessment, under the **assessment** header and tab bar (Evidence highlighted).
- Under the tab bar, an **Inventory | Requests** toggle (`seg`). Requests = the existing `/assessments/{id}/rfi` page, which also moves under the assessment header and tab bar (Evidence highlighted).
- The engagement-level `/engagements/{id}/evidence` (incl. `?assessment=`), `/engagements/{id}/requests` and the sidebar Evidence nav are **unchanged and stay valid**. Tests use them.
- No mockup redraw. Pixel gates for the touched pages diverge on purpose; list them in the PR for Saqlain's human gate. Do not tune to pass them.

## 3. Findings from research (do not re-derive)

- Tab bar is one macro: `app/templates/components/layout.html:26` `assessment_tabs(assessment, current, framework)`. 14 callers pass `current` of overview, scope, questionnaire, review or report (`assessment_header.html`, `workpaper*.html`, `review_queue.html`, `conclusions.html`, `findings.html`, `soa.html`, `narrative.html`, `board_inputs.html`, `comparison.html`, `desk_review.html`, `report_snapshots.html`). One edit in the macro covers all of them.
- `assessment_header.html:23` passes `tab`; the assessment page 303s `?tab=documents` to the engagement page at `web.py:1824`. That is the only redirect to change.
- `?tab=documents` is used as an internal link in `web.py:187`, `assessment_stage.py:108,117`, `desk_review_ready.html:10,36`, `scope_complete.html:56` and tests. **Leave those hrefs alone**: they redirect, so they follow the new target for free. Do not rewrite them.
- `evidence_inventory.html` builds its forms from `request.url.path` (lines 54, 78, 95) so a new route works for filters. Two places do not: `document_list.html:77` "Clear filters" uses `inventory_path` (set in `_inventory_fragment_context`, `web.py:1639`, hard-coded to the engagement URL), and the Inventory/Requests `seg` at `evidence_inventory.html:42-45` links to engagement URLs. Document archive/new-version HTMX posts go to `/assessments/{id}/documents/...` with `?{{ fragment_query }}`, which carries `assessment=`; verify they still re-render the list correctly on the new page.
- **Empty-state bug**: with `?assessment=` the page sets `inventory_filtered = True` (`web.py:1771`), so an assessment with zero evidence reads "No evidence matches the filters", while the unfiltered page reads "No evidence yet". The assessment scope is not a user filter.
- `rfi.html` renders `engagement_tabs(engagement, "evidence")` only `{% if engagement %}`; `engagement` can be None for legacy assessments.
- `assessment_tabs` does not set `overflow-x:auto`; engagement tabs do (`style="overflow-x:auto"`). Six tabs must not overflow at 390px.
- Tests that pin the old shape: `test_yozora_s5.py:~46` (exact 5 labels, no "Documents"), `:86-89` and `test_yozora_s6.py:51-53` (redirect Location), `test_longitudinal_demo.py:323-325` (redirect Location). `test_yozora_s6.py:151` and `test_yozora_read_models.py:295,301` use `?tab=documents` as an href or URL and should stay green unchanged. Check `:151` after the change.

## 4. Work

Order: A, B, C, D, then E.

### A. Tab macro and docs
- `layout.html` `assessment_tabs`: insert `{"label": "Evidence", "href": base ~ "/evidence" ~ framework_query, "current": current == "evidence"}` after Scope. Make the 6-tab row scroll instead of overflow on small screens (match the engagement tab style: wrap the `nav` call with `style="overflow-x:auto"` the way `engagement_tabs` callers do, or pass it through `tabs()`; pick the least invasive and keep other pages' markup identical except the new link).
- Docs (add-only wording): `yozora-design-system.md:28` list becomes the 6 tabs; `IA-SPEC.md` and `flow-map.html` lines naming the assessment tabs and "Evidence lives on the engagement only" get a dated revision note (do not redraw screens); `yozora-migration-map.md` rows for `evidence_inventory.html`, `rfi.html`, `layout.html`.

### B. Assessment-scoped Evidence page
- Extract the body of `engagement_evidence_inventory_page` (`web.py:1705`) into a helper that both routes call, so the engagement route's behaviour and every existing test stay identical.
- New `@router.get("/assessments/{assessment_id}/evidence")`:
  - 404 for unknown assessment. If `assessment.engagement_id` is None, 303 to `/assessments/{id}` (same as today's `?tab=documents` fallback).
  - Renders `pages/evidence_inventory.html` with `selected_assessment = assessment` plus a new context flag `assessment_chrome=True`, and `inventory_path=/assessments/{id}/evidence`.
  - Archived engagement: renders read-only like today (no new write path).
- `web.py:1824`: redirect target becomes `/assessments/{assessment.id}/evidence`.
- `evidence_inventory.html`, when `assessment_chrome`:
  - Crumbs: Client / Engagement / Assessment / Evidence.
  - Header h1 is the assessment display name with the same meta line; keep the Add from and Upload evidence actions.
  - Replace the `engagement_tabs` row with `assessment_tabs(assessment, "evidence")`.
  - `seg`: Inventory (`/assessments/{id}/evidence`, current) | Requests (`/assessments/{id}/rfi`). Show Requests always (today it needs `tab_assessment`).
  - Hide the "Assessment" filter select (`name="assessment"`, line ~85) and the "Showing [assessment] ×" chip (line ~95); the scope is the page.
  - Keep `.empty` copy rules below.
- **Empty-state fix** (applies to both routes): `inventory_filtered` must be true only when `source`, `status` or `search` is set. If the scoped result is empty and none of those are set, render "No evidence yet" with Upload evidence and Ask the client, never "No evidence matches the filters". On the engagement route, `?assessment=` alone also uses the "No evidence yet" copy. "Clear filters" links to `inventory_path`, which stays on the same page.
- The engagement route with `?assessment=` keeps working and keeps its engagement chrome.

### C. RFI page under the assessment
- `rfi.html`: replace the `engagement_tabs` block with `assessment_tabs(assessment, "evidence")` (always, even when `engagement` is None), then the same Inventory | Requests `seg` with Requests current. Import `assessment_tabs` from `layout.html`.
- Crumbs: Client / Engagement / Assessment / Requests (assessment crumb links to `/assessments/{id}`); keep the "All requests" back button and every hook from 117 (`data-rfi-back-link`, `data-rfi-links`, `#rfi-links`, `#reviewer-name` once only).
- **No `'` character in `rfi.html`** (tests `test_p5_6_rfi_rebuild.py::test_scenario_20`, `test_p6_7b_add_to_rfi.py::test_scenario_8`). No contractions in new copy, double quotes in Jinja strings.
- Engagement `requests.html` (hub) is not touched.

### D. Entry points and copy
- Assessment Overview header gets no extra button. The new tab is the entry.
- Stepper Evidence step and `?tab=documents` hrefs: unchanged (they redirect).
- `evidence_reuse.html` stays on engagement chrome: unchanged this PR (note as follow-up).
- Mobile: at 390px the 6-tab row scrolls horizontally inside its own container; the page itself must not.

### E. Integration
1. `tests/yozora_paths.py`: add `ASSESSMENT_EVIDENCE_TAB_PATHS` (every file touched or created) to `YOZORA_ALL_PATHS`, and add it beside `RFI_REQUESTS_PATHS` in each guard that enumerates tuples (the 10 listed in the 117 handoff). Add only. Re-run until no guard fails.
2. Status log entry in the current `tasks/*-status-log.md`.
3. Full `pytest -q` on Python 3.13 green.
4. **Screenshot sweep for Saqlain** (Chromium via `design/harness/screenshot.py` or Playwright, 1440 and 390, light and dark): every page that renders `assessment_tabs` (overview, scope, questionnaire, review queue, conclusions, findings, report, soa, narrative, board inputs, comparison, desk review, report snapshots, workpaper) before and after, so nothing else moved except the added tab; plus the new Evidence page (with and without evidence, with a filter) and the RFI page under the new chrome. List them in the PR.
5. Smoke test: output pasted in the PR (table below).

## 5. Tests

Changed:
- `test_yozora_s5.py`: rename the five-tabs test; expect `Overview, Scope, Evidence, Questionnaire, Review, Report`; keep `"Documents" not in nav` and the 5 `class="stp`; `:57` href still `?tab=documents` (unchanged); `:86-89` Location becomes `/assessments/{id}/evidence`.
- `test_yozora_s6.py:51-53` and `test_longitudinal_demo.py:323-325`: Location becomes `/assessments/{id}/evidence`. Check `test_yozora_s6.py:151`.
New `tests/test_assessment_evidence_tab.py`:
1. Every `assessment_tabs` caller page lists 6 tabs in order; only the right one has `aria-selected` (spot-check overview, scope, evidence, rfi, review, report).
2. `GET /assessments/{id}/evidence` 200: has `aria-label="Assessment"` nav with Evidence selected, no `aria-label="Engagement"` nav, a seg with Inventory current and Requests linking `/assessments/{id}/rfi`, no assessment filter select, no "Showing" chip.
3. Empty scoped page says "No evidence yet" and not "No evidence matches"; with `?source=upload` and no match it says the filter text and Clear filters goes to `/assessments/{id}/evidence`.
4. Seeded evidence for assessment A shows on A's page and not on sibling B's page; the engagement page still shows both.
5. Assessment with no engagement 303s to `/assessments/{id}`; unknown id 404; archived engagement renders (read-only banner behaviour unchanged).
6. `GET /assessments/{id}/rfi` has the assessment nav with Evidence selected, the seg with Requests current, and still passes the no-`'` rule.
7. `?tab=documents` 303s to the new URL; the engagement `?assessment=` URL still 200.
8. Archive and new-version HTMX on the new page re-render `#document-list` with the scope kept.
Also run: `pytest tests/test_yozora_s5.py tests/test_yozora_s6.py tests/test_yozora_s8_requests.py tests/test_p5_6_rfi_rebuild.py tests/test_p6_7b_add_to_rfi.py tests/test_rfi_link_picker.py tests/test_requests_hub.py tests/test_yozora_read_models.py tests/test_longitudinal_demo.py tests/test_design_lint.py -q`.

## 6. Smoke test (paste output in the PR)

Seed: `python design/harness/seed_s8.py --output /tmp/ev-smoke/db.sqlite3 --screen b6-rfi --state default`, then run uvicorn on 8001 with that DB (same pattern as `tasks/2026-10-06-rfi-requests-consolidation.md` section 6). Variables A (assessment) and E (engagement) from the DB.

| # | Command | Expect |
|---|---|---|
| 1 | `curl -s "$B/assessments/$A" \| grep -o 'aria-label="Assessment".*</nav>' \| grep -o '>[A-Za-z]*</a>'` | 6 labels in order |
| 2 | `curl -si "$B/assessments/$A?tab=documents" \| grep -i '^location'` | `/assessments/$A/evidence` |
| 3 | `curl -s "$B/assessments/$A/evidence" \| grep -c 'aria-label="Engagement"'` | 0 |
| 4 | same page `grep -c 'href="/assessments/'$A'/rfi"'` | at least 1 |
| 5 | `curl -s "$B/assessments/$A/rfi" \| grep -c 'aria-label="Assessment"'` | 1 |
| 6 | `curl -s "$B/engagements/$E/evidence?assessment=$A" -o /dev/null -w '%{http_code}'` | 200 |
| 7 | empty-assessment page: `grep -c 'No evidence matches'` | 0 |
Browser steps at 1440 and 390: Overview, then Evidence tab, then Requests toggle, then Inventory, then back to Overview, with the assessment header staying put; Evidence tab highlighted on both; no horizontal page scroll at 390.

## 7. Adversarial review checklist
- Orphaned links: grep templates, JS, Python for `evidence?assessment`, `tab=documents`, `engagement_tabs(` on `rfi.html`; each resolves.
- Context loss: no page reachable from the new tab switches to engagement chrome except via the explicit "All requests" button.
- Legacy assessments with no engagement: tab bar shows Evidence, route 303s, RFI page renders without engagement.
- Archived engagement: new pages read-only; writes still 409.
- Scope isolation: assessment page never shows a sibling assessment's evidence (test 4).
- `#reviewer-name` appears once per page on rfi; filter forms on the new page keep `assessment` scope via path, not stray params.
- Six tabs at 390px; keyboard order unchanged.
- Guards: allowance added once, nothing deleted.
- Mockups and `design/baselines` untouched; divergence listed in the PR.

## 8. Out of scope
Regrouping the tab bar, redrawing mockups, `evidence_reuse.html` chrome, the engagement hub, any change to the Requests hub or RFI link logic.

## Results

Implemented work packages A through E on `codex/assessment-evidence-tab`.

- WP-A: Added the Evidence assessment tab after Scope, made the six-tab row horizontally scrollable, and updated the dated Yozora documentation notes and migration map.
- WP-B: Added `GET /assessments/{assessment_id}/evidence` with assessment-scoped inventory rendering, preserved engagement inventory behavior, fixed scoped empty-state copy, and preserved assessment scope through archive/version HTMX fragments.
- WP-C: Moved the assessment RFI page under assessment chrome with the Inventory | Requests toggle while preserving existing RFI hooks. `app/templates/pages/rfi.html` contains no apostrophe characters.
- WP-D: Verified the entry points, legacy redirects, archive read-only behavior, scope isolation, unchanged stepper and `?tab=documents` hrefs, and the assessment tab contract across the relevant pages.
- WP-E: Added `ASSESSMENT_EVIDENCE_TAB_PATHS` only to the Yozora path allowances and tuple guards, updated the status log and task tracker, and added focused regression coverage.

Verification:

- Focused regression suite: `128 passed`.
- Full suite: `1583 passed, 30 skipped`.
- Smoke seed completed with `.venv/bin/python design/harness/seed_s8.py --output /tmp/ev-smoke/db.sqlite3 --screen b6-rfi --state default`. The in-process smoke check reported six labels in order, the Documents redirect to `/assessments/assessment-s5/evidence`, zero Engagement navs on the assessment Evidence page, assessment RFI links present, one Assessment nav on RFI, engagement-scoped status `200`, and zero filter-copy matches for an empty scoped assessment.
- Uvicorn could not bind to `127.0.0.1:8001` in this sandbox (`Operation not permitted`), so the smoke assertions used FastAPI `TestClient` against the same seeded database.
- Chromium executable and Playwright were present, but Chromium launch was blocked by the environment with a macOS Mach rendezvous permission error. No screenshot files were produced; the requested 1440/390 light/dark sweep is therefore recorded as environment-blocked rather than passed.
- Mockups and `design/baselines` were not changed. The intentional pixel-gate divergence is limited to the new assessment Evidence and Requests chrome and the added responsive tab overflow behavior.

Commit note: the requested one commit per work package could not be created because this worktree's Git metadata is outside the writable workspace. Git failed while creating `/Users/saqlainmomin/dpdpa-gap-tool/.git/worktrees/cyberassess-evidence-tab/index.lock` with `Operation not permitted`. No push or PR was made.
