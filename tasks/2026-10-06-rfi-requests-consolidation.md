# RFI and Requests consolidation: implementation spec (6 Oct 2026)

Source: Saqlain's walkthrough of a Prestige assessment on 6 Oct. Nothing here is built yet. This file is the spec for one PR. It was verified against `main` at `9cf6977`.

Implementers: read the root `CLAUDE.md` first. No LLM calls are involved. Never open `validation/companies/*/answer_key.json`. PDF code (`S()`) is not touched.

## 0. Status and coordination

- **Questions in section 8 are answered: both defaults apply** (Saqlain, 6 Oct). No Unarchive or purge buttons on the archived Overview; Settings shows one flat list, archived last.
- **Parallel session.** Saqlain has a separate local session working on the final report and converting the mockups to the final version. It edits `app/routers/web.py`, `app/routers/questionnaire.py`, `app/services/context_profiler.py`, the framework definitions, `tests/yozora_paths.py` and adds `tests/test_context_blocks_by_framework.py`. That work is not on `main` yet. Branch from `main`, never from a local checkout. When it lands, expect textual conflicts in `app/routers/web.py` and `tests/yozora_paths.py` (add-only lists: keep both sides). This PR touches `web.py` only if a package needs it; none is planned.
- Review flow: cloud session implements and opens one PR, Claude (local) does the adversarial review, Saqlain reviews and approves, then merges.

## 1. Decisions

| # | Decision | Why (what the code supports) |
|---|---|---|
| D1 | Keep `/assessments/{id}/rfi` (`pages/rfi.html`) as the per-assessment sub-view of Evidence > Requests. Do not fold it into `requests.html`. | Requests is engagement-scoped; the RFI page is assessment-scoped (`rfi_requests.page_context(db, assessment)`). Six entry points and three `HX-Redirect`s point at `/assessments/{id}/rfi` (list in section 3), and about 30 tests GET it. Folding would rewrite all of them for no user gain. The page already sits under Engagement / Evidence / Requests in its crumbs. |
| D2 | Requests becomes the hub: each assessment row gets a "Next step" action that deep-links to the right RFI tab. The RFI page gets an explicit "All requests" back button. Generate and Issue redirect to the next tab. | Gives one home with a visible path down and back up, without moving routes. |
| D3 | The RFI-item link picker is the primary link flow (Client links tab). Unassigned items first; covered items in a collapsed group showing the covering contact; the contact/expiry/limits block is `hidden` until at least one item is checked. | Decision 2 from Saqlain. Uses the existing `.req-picks` / `.req-pick` picker pattern (`yozora-patterns.css:182-197`). |
| D4 | The free-text link form (`#new-link-form`) stays on Requests, moved below the link cards into a collapsed `<details>` "Request something else". | Decision 3. Route `POST /engagements/{id}/magic-links` unchanged. |
| D5 | Scope readability: template-only spacing changes using existing tokens and classes. No CSS file changes. | Decision 4. Avoids `design/tokens.json` sync test and global pixel drift. |
| D6 | Archive, unarchive and purge-preview live only in Settings > Data housekeeping, in a new "Archive and purge" card listing every active, closed and archived engagement. Both Overviews lose the Retention card; the engagement Overview header loses Archive / Unarchive / Review purge. Archived banners stay on both Overviews and gain a link to Settings. | Decision 5. One home, same as D1-D4. Note: an engagement with exactly one assessment never shows the engagement Overview (`web.engagement_detail` 303s to the assessment), so for most engagements the assessment Overview card was the only archive UI. Settings must therefore carry every archivable engagement, not just archived ones. |
| D7 | Archive/unarchive APIs get one optional form field `return_to`. Only the exact value `/settings` changes `HX-Redirect` to `/settings`; anything else keeps `/engagements/{id}`. | Lets Settings stay on Settings after an action. Exact-match allowlist, so no open redirect. Existing callers and tests are unaffected. |

Out of scope: domain grouping; link regenerate. Known limit: links store only `token_digest`, so a link URL is shown once (at creation) and never again. Revoke already exists on Requests cards and is unchanged.

## 2. What the draft got wrong or missed

- "The RFI page has no path back up": wrong. `rfi.html:9` crumbs already link Engagement / Evidence / Requests. The real gap is that nothing on the page looks like Requests (no back control, no link to the monitor).
- Missed: the engagement Overview only renders for multi-assessment or archived engagements (single-assessment engagements redirect).
- Missed: the engagement Overview archive/unarchive modals take `#reviewer-name` from the Retention partial. Removing the partial without removing the modals would silently drop the actor name from the audit event.
- Missed: tests require `pages/rfi.html` and `partials/rfi_links.html` to contain no `'` character, no `|safe` and no `CyberAssess` (`test_p5_6_rfi_rebuild.py::test_scenario_20`, `test_p6_7b_add_to_rfi.py::test_scenario_8`). New copy cannot use contractions. Jinja strings and CSS selectors must use double quotes.
- Missed: RFI link coverage shows an 8-character link id (`coverage[item_id]` holds `id_prefix`), not a contact. Showing "which link covers them" needs a service change.
- Missed: after a link-form validation error the partial re-renders with nothing selected. Once the form is hidden until selection, that would hide the error form. The selection and typed values must survive the error.
- Missed: the settings page is one `<form id="settings-form">`. The new archive forms cannot be nested inside it.

## 3. Route and entry-point map (all stay valid)

| Entry point | Target | Change |
|---|---|---|
| `partials/scope_complete.html:36` "Prepare RFI" (`data-rfi-link`) | `/assessments/{id}/rfi` | none (Items tab is right for this step) |
| `partials/report_summary.html:159` (`data-rfi-link`) | `/assessments/{id}/rfi` | none |
| `components/requirement_card_body.html:104` "Open the RFI" | `/assessments/{id}/rfi` | none |
| `partials/document_list.html:81` "Ask the client" | `/assessments/{id}/rfi` | WP-A: `?tab=links` |
| `pages/requests.html:39,41,46` rows | `/assessments/{id}/rfi` | WP-B: keep row link; add Next step link |
| `pages/evidence_inventory.html:31,44` | `/engagements/{id}/requests` | none |
| `snapshots._rfi_success` (generate, issue) | `HX-Redirect /assessments/{id}/rfi` | WP-A: `?tab=versions` after generate, `?tab=links` after issue |
| `requirement_review.withdraw_rfi_request` origin=rfi | `HX-Redirect /assessments/{id}/rfi` | none (asserted exactly by `test_p6_7b...:697`) |
| `retention` archive/unarchive | `HX-Redirect /engagements/{id}` | WP-C: `/settings` when `return_to=/settings` |
| `/design/pages/b6-rfi`, `b6-magic_links` previews (`design_s8_requests.py`) | render `rfi.html`, `requests.html` | none; must still render (`test_yozora_s8_requests.py`) |

HTMX targets that must keep their ids and swap mode: `#rfi-links` (outerHTML, from `rfi_links.html`), `#magic-links` (outerHTML, from `magic_links.html`). Every `data-*` hook listed in `docs/product/yozora-migration-map.md` for the touched templates stays, except the ones WP-C removes on purpose (listed there).

## 4. Work packages

Five packages. A-D touch disjoint files and can run in parallel worktrees branched from `main`. E runs last on the merged branch. Branch name: `claude/rfi-requests-consolidation`. One PR.

During A-D, run only the tests named in your package. File-set guard tests will fail until E adds the allowance; that is expected.

| WP | Owner files (only these) | Depends on |
|---|---|---|
| A. RFI sub-view and link picker | `app/templates/pages/rfi.html`, `app/templates/partials/rfi_links.html`, `app/services/rfi_requests.py`, `app/routers/magic.py`, `app/routers/snapshots.py`, `app/static/js/app.js`, `app/templates/partials/document_list.html`, new `tests/test_rfi_link_picker.py` | none |
| B. Requests hub | `app/templates/pages/requests.html`, `app/templates/partials/magic_links.html`, new `tests/test_requests_hub.py` | A's `adhoc_open` context key (contract below); B can merge first |
| C. Retention to Settings | `app/templates/pages/assessment.html`, `app/templates/pages/engagement_detail.html`, `app/templates/pages/firm_settings.html`, `app/templates/pages/engagement_purge.html`, `app/routers/firm_settings.py`, `app/routers/retention.py`, delete `app/templates/partials/engagement_retention.html`; tests `tests/test_retention.py`, `tests/test_yozora_firm_settings.py`, `tests/test_yozora_s4.py`, `tests/test_yozora_s5.py`, `tests/test_magic_links.py`, new `tests/test_settings_archive.py` | none |
| D. Scope readability | `app/templates/partials/scope_complete.html`, new `tests/test_scope_complete_layout.py` | none |
| E. Integration | `tests/yozora_paths.py`, the file-set guard tests listed in E, `docs/product/yozora-migration-map.md`, `docs/product/yozora-design-system.md`, `tasks/2026-10-06-status-log.md`, this plan file | A-D merged |

Merge order: A, B, C, D (any order, no textual overlap), then E.

### WP-A. RFI sub-view and link picker

**`app/services/rfi_requests.py` → `page_context`**
- Next to `coverage`, build `coverage_labels: dict[str, list[str]]` in the same loop (same filters: current issue, `status == "active"`). Label per link: `f"{row.contact_name or row.contact_email or 'Client contact'}, expires {row.expires_at.strftime('%d %b %Y')}"`.
- Return it as `"coverage_labels"`. Leave `coverage` unchanged (tests count it).

**`app/routers/magic.py`**
- `_render_rfi_links(...)`: add kwargs `selected_item_ids: Sequence[str] = ()` and `link_form: dict | None = None`. Put into context `selected_item_ids` (list) and `link_form` (defaults `{"contact_name": "", "contact_email": "", "expires_in_days": 7, "max_uploads": 20, "max_total_mb": 100}` overlaid with the given dict). Add `"coverage_labels": {}` to the `SnapshotError` fallback dict.
- `create_rfi_magic_link`: after parsing the form, build `link_form` from the raw form strings and pass `selected_item_ids=item_ids, link_form=link_form` on every error return (`RfiError`, `MagicLinkNotFound`, `SnapshotIntegrityError`, `MagicLinkError`, `Exception`). Success path passes neither (a fresh form).
- `_consultant_context` and `_render_consultant`: add kwarg `adhoc_open: bool = False` → context key `adhoc_open`. In `create_magic_link` (free-text), pass `adhoc_open=True` on both error returns. Revoke paths leave it `False`. This is the contract WP-B reads.

**`app/routers/snapshots.py`**
- `_rfi_success(snapshot, assessment_id, message, tab: str | None = None)`: `HX-Redirect` is `/assessments/{id}/rfi` plus `?tab={tab}` when given. `generate_rfi_version` passes `tab="versions"`; `issue_rfi_version` passes `tab="links"`.

**`app/templates/pages/rfi.html`** (no `'` anywhere)
- Header `.acts`: when `engagement` is set, add first `<a class="btn ghost" href="/engagements/{{ engagement.id }}/requests" data-rfi-back-link>All requests</a>`. Keep the Generate form after it.
- Client links panel, no-issue empty state: keep text; add `<a class="btn secondary sm" href="/assessments/{{ assessment.id }}/rfi?tab=versions">Go to versions</a>` inside the `.empty` div.
- Nothing else changes. Do not add `data-rfi-links` anywhere outside the include (scenario 20 asserts its absence before issue).

**`app/templates/partials/rfi_links.html`** (rewrite; no `'` anywhere)

```
<section id="rfi-links" data-rfi-links class="stack">
  error alert (unchanged markup and hooks)
  new-link alert (unchanged) + after the input:
    {{ button("Copy link", "secondary", "", "copy", false, copy_trigger="input[data-rfi-new-link]") }}
  <form class="solid card" data-rfi-link-form hx-post=(unchanged) hx-target="#rfi-links" hx-swap="outerHTML" hx-include="#reviewer-name">
    header .between: h2 "Send items to the client"; p.help "Select the items for one client contact. A link can include up to 20 items."
      right side: <span class="sub num" data-rfi-selected-count aria-live="polite">No items selected</span>
    split current_items with a namespace: covered = coverage.get(item_id) non-empty; else unassigned (keep RFI order)
    if any active link in `links` has snapshot_id != current_issue.id:
      <p class="help" data-rfi-older-links>Active links from earlier RFI versions are not counted here.</p>
    <h3 style="margin-top:var(--s-6)">Not yet sent <span class="sub num">{{ n }}</span></h3>
    <div class="req-picks" data-rfi-unassigned-items style="margin-top:var(--s-3)"> one picker row per unassigned item
      or, when none: <p class="sub" data-rfi-all-covered>Every item is in an active client link.</p>
    if covered:
      <details class="disclose" data-rfi-covered-items style="margin-top:var(--s-6)"{% if a selected id is covered %} open{% endif %}>
        <summary>{{ n }} items already in an active link</summary>
        <div class="req-picks" style="margin-top:var(--s-3)"> one picker row per covered item </div>
      </details>
    <div data-rfi-link-details style="margin-top:var(--s-6)"{% if not selected_item_ids %} hidden{% endif %}>
      form-grid: contact name, contact email, expires in (days)   (same ids/names as today; values from link_form)
      <details class="disclose"><summary>Upload limits</summary> form-grid: max uploads, max total MB </details>
      <div style="margin-top:var(--s-5)">{{ button("Create client link", "primary", "", "link", true, button_type="submit") }}</div>
    </div>
  </form>
  <div class="sec"><h2>Links for this RFI</h2><a class="btn ghost sm" href="/engagements/{{ assessment.engagement_id }}/requests" data-rfi-requests-link>Track receipts in Requests</a></div>
  existing links list (unchanged, keeps data-rfi-link-row and data-link-contact) or empty state (unchanged)
</section>
```

Picker row (both groups):
```
<label class="choice req-pick">
  <input type="checkbox" name="item_ids" value="{{ item.item_id }}"{% if item.item_id in selected_item_ids %} checked{% endif %}>
  <span class="grow">
    <b>{{ item.title }}</b>
    <span class="help"><span class="num">{{ item.item_id }}</span> · <span data-rfi-coverage="{{ item.item_id }}">
      unassigned: <span data-rfi-unsent>Not yet in an active client link</span>
      covered:    In a link to {{ coverage_labels.get(item.item_id, []) | join("; ") }}
    </span></span>
    received spans: unchanged markup (data-rfi-received, class sub, display:block)
  </span>
</label>
```
- Use `{% set labels = coverage_labels if coverage_labels is defined else {} %}` and `{% set selected = selected_item_ids if selected_item_ids is defined else [] %}`, `{% set form = link_form if link_form is defined else {...defaults} %}`; the design previews and fallback contexts may not pass them.
- Exactly one `data-rfi-coverage="..."` per item and one `data-rfi-unsent` per unassigned item. Do not put either string in summaries, counts or JS.
- The context has no `engagement`; use `assessment.engagement_id`.

**`app/static/js/app.js`** (append one block; no other edits)
- `syncRfiLinkForm(form)`: `n` = checked `input[name="item_ids"]` in the form. Set `[data-rfi-link-details].hidden = n === 0`. Set `[data-rfi-selected-count]` text: `No items selected` / `1 item selected` / `${n} items selected`; when `n > 20` append ` · A link can include up to 20 items` and set the submit button `disabled`; otherwise remove `disabled`.
- Wire: `document.addEventListener('change', ...)` delegating to `closest('[data-rfi-link-form]')`; on `htmx:load` run it for every `[data-rfi-link-form]` under `event.detail.elt`; also once at load for `document.querySelectorAll('[data-rfi-link-form]')`.
- Do not move focus. Revealing the block must not scroll.

**`app/templates/partials/document_list.html`**: line 81 href becomes `/assessments/{{ request_assessment_id }}/rfi?tab=links`.

**Tests (`tests/test_rfi_link_picker.py`, new)** using the `tests/test_p5_6_rfi_rebuild.py` helpers (`_seed`, `_generate`, `_issue`, `_create_rfi_link`, import them):
1. After issue with no links: `data-rfi-unassigned-items` has every item; no `data-rfi-covered-items`; `data-rfi-link-details` carries `hidden`.
2. After a link to the first 3 items with contact "Ananya Rao": those 3 render inside `data-rfi-covered-items` with "In a link to Ananya Rao, expires"; the rest under unassigned; counts of `data-rfi-coverage=` equal item count.
3. POST the RFI link with `item_ids=RFI-002` and `contact_email=nope`: response contains `value="RFI-002" checked`, `data-rfi-link-details` without `hidden`, and the typed email value; no link created.
4. Generate returns `HX-Redirect` `/assessments/{id}/rfi?tab=versions`; issue returns `...?tab=links`.
5. Free-text create with empty items returns a body with `data-request-something-else` and `open` (asserts the `adhoc_open` contract end-to-end once WP-B lands; mark it as WP-E verify if B is not merged yet).
6. A revoked link's items return to unassigned (mirror scenario 16 at small scale).
7. Source of `rfi_links.html` and `rfi.html` has no `'` (already in scenario 20; keep it green).
8. A link from an older issued version, still active, shows `data-rfi-older-links` after a newer version is issued.

Also run: `pytest tests/test_p5_6_rfi_rebuild.py tests/test_p6_7b_add_to_rfi.py tests/test_yozora_magic_link_contacts.py tests/test_yozora_s8_requests.py tests/test_report_snapshots.py tests/test_yozora_s9_system.py -q`.

### WP-B. Requests hub

**`app/templates/pages/requests.html`**
- Keep head, crumbs, engagement tabs, Inventory/Requests seg, the `Requests by assessment` heading text (asserted) and the empty state.
- Table columns: `Assessment | RFI (hide-sm) | Received | Next step (hide-sm) | chevron (hide-sm)`. Row keeps `data-request-summary` and `data-href="/assessments/{id}/rfi"`.
- Next step per summary (compute in template):
  - `latest_version is none` → label `Prepare RFI`, tab `items`
  - `version is none or latest_version > version` → `Review draft version {{ latest_version }}`, tab `versions`
  - `active_links == 0` → `Create client link`, tab `links`
  - else → `View links`, tab `links`
- Render as `<a class="btn ghost sm" href="/assessments/{id}/rfi?tab={tab}" data-request-next-step="{tab}">label</a>`. On mobile, render the same link inside the first cell's `show-sm` sub-line (one link visible per breakpoint).
- Received cell keeps the existing text (`{{ received }} of {{ items }} received` / `No issued requests`; asserted).

**`app/templates/partials/magic_links.html`** (inside `<section id="magic-links">`, non-loading branch)
- Order: error alert, new-link alert (unchanged), then `<div class="sec" style="margin-top:var(--s-8)"><h2>Links</h2></div>` with the cards / empty state (card markup unchanged), then the free-text block.
- Free-text block: `<details class="disclose" id="request-something-else" data-request-something-else style="margin-top:var(--s-8)"{% if adhoc_open is defined and adhoc_open %} open{% endif %}><summary>Request something else</summary><p class="help">For items outside an issued RFI. The client sees each line exactly as you type it.</p>` then the existing `<form id="new-link-form" ...>` with `style="margin-top:var(--s-4)"`. Remove the form's inner `.between` header (h2 "New link" and its help). Keep `#requested-items`, field ids, the Upload limits disclosure and "Create link".
- Empty links state copy: `<h3>No client links yet</h3><p>Issue an RFI for an assessment above, then send its items from the Client links tab.</p>`.
- Loading-state branch: unchanged.

**Tests (`tests/test_requests_hub.py`, new)**
1. Assessment with no RFI → `data-request-next-step="items"`; generated draft only → `"versions"` with "Review draft version 1"; issued, no links → `"links"` "Create client link"; with an active link → "View links".
2. In the page, the index of `data-request-something-else` is after the first `data-link-id` (when a link exists); the `<details>` has no `open` on a plain GET.
3. Free-text form still posts to `/engagements/{id}/magic-links` and is inside `data-request-something-else`.

Also run: `pytest tests/test_magic_links.py tests/test_yozora_magic_link_contacts.py tests/test_yozora_s8_requests.py tests/test_yozora_s8_client.py tests/test_longitudinal_demo.py -q` (guard failures in `test_longitudinal_demo.py` are E's).

### WP-C. Retention to Settings

**`app/routers/retention.py`**
- `archive_engagement_route` and `unarchive_engagement_route`: add `return_to: str = Form("")`. `redirect = "/settings" if return_to == "/settings" else f"/engagements/{engagement.id}"`. Nothing else changes.

**`app/routers/firm_settings.py`**
- Add `engagement_archive_rows(db) -> list[dict]`: query `Engagement` joined to `Client` where `Engagement.status.in_(retention.ARCHIVABLE_STATUSES + (retention.ARCHIVED_STATUS,))`, ordered by client name, engagement name. Each row: `{"engagement", "client_name", "archived": status == ARCHIVED_STATUS, "retention": retention.retention_state(db, engagement) if archived else None}`. Return non-archived rows first, then archived, each group keeping the query order.
- `_render` context: `"engagement_archive": [] if preview_state == "nodata" else engagement_archive_rows(db)`.
- Update the module docstring to name the archive list.

**`app/templates/pages/firm_settings.html`**
- Close `</form>` right after the retention card (the `data-retention-form` card). Inside the form stay: Branding, the Data housekeeping heading, the retention card. Rename that card's h3 to `Retention period`; all its ids, names, label and help text stay (asserted).
- Remove the sr-only `#reviewer-name` input from the form.
- After `</form>`, in this order: the new card, then the Unmigrated assessments card (unchanged), then Users and roles (unchanged).
- New card: `<div class="glass card narrow" id="engagement-archive" data-engagement-archive>`
  - `<h3>Archive and purge</h3><p class="sub tight">Archiving makes an engagement read-only and removes it from active views. Purge is available once the retention period has passed and every check passes.</p>`
  - Name field: `<label class="label" for="reviewer-name" style="margin-top:var(--s-4)">Your name</label><label class="field"><input id="reviewer-name" name="reviewer_name" form="settings-form" maxlength="200" autocomplete="name" placeholder="Recorded on settings changes, archive and unarchive"></label>`. The `form` attribute keeps it submitting with Save changes; archive forms read it through `hx-include`.
  - Empty: `<p class="muted tight" style="margin-top:var(--s-4)">No engagements yet.</p>`.
  - Otherwise `<ul class="line-list" style="margin-top:var(--s-4)">`, one `<li data-engagement-archive-row="{{ e.id }}" data-archive-state="{{ 'archived' if row.archived else 'active' }}">`:
    - `<div class="txt"><b><a href="/engagements/{{ e.id }}">{{ e.name }}</a></b><span class="sub" style="display:block">{{ client_name }} · ...</span></div>`
    - Not archived: sub tail `Active` or `Closed`; action `<form data-archive-control hx-post="/api/engagements/{{ e.id }}/archive" hx-include="#reviewer-name" hx-swap="none" hx-confirm="Archive {{ e.name }}? It becomes read-only and leaves active views. You can unarchive it later."><input type="hidden" name="return_to" value="/settings">{{ button("Archive", "secondary", "sm", button_type="submit") }}</form>`
    - Archived: sub tail from `row.retention`: with a record, `Archived {{ archived_at | display_date }} by {{ archived_by_display }} · ` then `Eligible for purge now` (elapsed), `Eligible for purge from {{ eligible_at | display_date }}`, or `Retention setting is not valid` (no eligible_at); without a record, `No archive record was found`. Actions in `<div class="hrow">`: unarchive form (same pattern, `data-unarchive-control`, `/unarchive`, confirm `Unarchive {{ e.name }}? It becomes editable again. Archiving it again starts a new retention period.`) and `<a class="btn ghost sm" data-purge-preview-link href="/engagements/{{ e.id }}/purge">Review purge</a>`.
  - No inline `display:none` anywhere; `hidden` only if needed.

**`app/templates/pages/assessment.html`**
- Delete line 21 (`{% set retention = ... %}`) and lines 48-53 (the comment and the `data-visual-mask` Retention block).
- Archived banner body becomes: `Its engagement is archived. Unarchive it in <a href="/settings#engagement-archive" data-archive-settings-link><u>Settings</u></a> to make changes.` Keep `data-archived-banner`.

**`app/templates/pages/engagement_detail.html`**
- Delete the stale comment (line 25) and the macros `engagement_records`, `archive_modal`, `unarchive_modal`, plus every call to them.
- `title_head`: default branch keeps only Add assessment; the `archived` branch renders no actions; drop the `archiving` branch.
- State whitelist (line 9): remove `archiving`. Line 10 condition becomes `state == 'default'`.
- Archived banner (line 31): keep all text; append ` Unarchive or purge it from <a href="/settings#engagement-archive" data-archive-settings-link><u>Settings</u></a>.` inside the banner `<div>`.

**`app/templates/pages/engagement_purge.html`**: header button becomes `<a class="btn secondary" href="/settings#engagement-archive">Back to Settings</a>`.

**Delete `app/templates/partials/engagement_retention.html`** (no remaining includes; grep to confirm). Leave its entries in `tests/test_design_lint.py` and the path tuples (lists are add-only; a missing file in an allow-list is harmless).

**Test updates (exact)**

| File:line (main) | Now asserts | Change to |
|---|---|---|
| `tests/test_retention.py:673-674` | overview has `data-unarchive-control`, `data-purge-preview-link` | overview has neither and has `data-archive-settings-link`; `GET /settings` has `hx-post="/api/engagements/{id}/unarchive"` and `href="/engagements/{id}/purge"` |
| `tests/test_retention.py:670-672,675-676` | banner, eligible text, no archive control, assessment banner | unchanged |
| `tests/test_retention.py:1003` | engagement page shows `Retention: 10 years after archive (firm setting` | `data-retention-section` not in the engagement page; keep the following archive and metadata asserts |
| `tests/test_yozora_firm_settings.py:287-294` `test_engagement_page_reads_the_firm_retention` | engagement page retention text and `data-archive-control` | rename `test_settings_lists_engagement_with_archive_control`: `/settings` has `data-engagement-archive-row="{id}"` with an archive form (`hx-include="#reviewer-name"`); engagement page has no `data-retention-section` and no `data-archive-control`; after saving 15 years and archiving, the Settings row shows `Eligible for purge from` + `add_years(archived_at, 15)` via `display_date` |
| `tests/test_yozora_s4.py:247-268` `test_engagement_overview_archive_unarchive_and_tools_are_visible` | header archive button, archive form, visible `#reviewer-name`, unarchive modal, purge links on overview | rename `..._links_archive_to_settings`: overview has no `data-archive-engagement`, no `data-archive-control`, no `reviewer-name`; keep the evidence/assessment/requests asserts; `/settings` has a visible `#reviewer-name` and the archive form; after archive, overview has the banner, `data-archive-settings-link`, "by Priya", no `data-modal-open="unarchive-modal"`; `/settings` has the unarchive form and a purge link to `/engagements/{id}/purge`; keep `_assert_no_display_none` on both pages |
| `tests/test_yozora_s5.py:58` | `data-visual-mask` in overview | `data-retention-section` not in overview (the remaining mask lives in the scored hub panel, which this fixture does not reach) |
| `tests/test_yozora_s5.py:75,79` | `Retention` in overview; `New link` on Requests | `data-retention-section` not in overview; `Request something else` on Requests (WP-B copy) |
| `tests/test_magic_links.py:439` | `retention` in overview | `data-retention-section` not in overview |
| `tests/test_yozora_s3.py:116-119` | client page has no retention form; settings has it | unchanged (must stay green) |

**New tests (`tests/test_settings_archive.py`)**
1. Archive with `return_to=/settings` → 200, `HX-Redirect: /settings`; with `return_to=https://evil.example` and with none → `/engagements/{id}`.
2. Settings lists active and closed engagements with Archive, archived ones with Unarchive + purge link, and omits other statuses; archived rows come last.
3. Settings archive then unarchive records `consultant:<name>` from `reviewer_name` in the audit events.
4. `GET /settings` and `POST /settings` (invalid retention) both render with no nested `<form>` inside `#settings-form` (parse and check), and `#reviewer-name` appears exactly once.
5. Archived assessment Overview still shows `data-archived-banner` and the settings link; a write to that engagement still returns 409.

Also run: `pytest tests/test_retention.py tests/test_yozora_firm_settings.py tests/test_yozora_s3.py tests/test_yozora_s4.py tests/test_yozora_s5.py tests/test_magic_links.py -q`.

### WP-D. Scope readability (`app/templates/partials/scope_complete.html` only)

One design pass. Existing tokens and classes only; inline styles use `var(--s-*)` / `var(--line)` like the rest of the templates. Keep every text string the tests read (`Scope confirmed`, `Evidence request`, flag labels, `proposed as likely not applicable`, control ids), `data-rfi-link`, the PDF/DOCX links and `#flags`.

Scope confirmed card:
- Excluded and proposed-not-applicable lists: `<ul class="checks mt">` becomes `<ul class="line-list mt" data-scope-excluded>` / `data-scope-proposed`. Each `<li>` holds `<div class="txt"><b>…</b><span class="sub" style="display:block;margin-top:var(--s-1)">…</span></div>`. This fixes title and detail running together on one line (`.checks li div` is inline).
- Proposed list: the detail line stays `framework · control id · rationale`.
- Flags (`.domains`): unchanged.

Evidence request card (the list):
- Replace the per-group `<h3 class="mt-lg">` and `<div class="mt">` with, per group: `<div class="between" data-checklist-group="{{ 'required' if heading == 'Required' else 'recommended' }}" style="margin-top:{{ 'var(--s-6)' if loop.first else 'var(--s-8)' }};padding-bottom:var(--s-3);border-bottom:1px solid var(--line)"><h3>{{ heading }}</h3><span class="sub num">{{ items|length }} item{{ "s" if items|length != 1 else "" }}</span></div>`.
- Rows: keep `.check-row`; add `style="padding:var(--s-4) 0"` and `data-checklist-item`. Reason: `<span class="sub" style="display:block;margin-top:var(--s-1)">`. Chips: `<div class="chips" style="flex:none;max-width:40%;justify-content:flex-end">`.
- Result: 16px rows with a hairline between, 32px between groups, a ruled group header with a count.

**Tests (`tests/test_scope_complete_layout.py`, new)**: scope tab for a scoped DPDPA + ISO assessment renders `data-checklist-group="required"` before `"recommended"`, each with a count; every `data-checklist-item` reason sits in a `display:block` sub; excluded/proposed lists use `line-list`; `data-rfi-link` still present. Also run `pytest tests/test_p5_5_scoping_evidence.py tests/test_yozora_s5.py tests/test_p6_0f_dpdpa_followups.py tests/test_design_lint.py -q`.

### WP-E. Integration (after A-D merge)

1. **Path allowance.** In `tests/yozora_paths.py` add a tuple `RFI_REQUESTS_PATHS` with every file A-E touched or created (templates, routers, service, `app.js`, new and edited tests, docs, this plan, the status log) and append it to `YOZORA_ALL_PATHS`. Then, for each guard that enumerates tuples instead of using `YOZORA_EXCLUDES`, add `RFI_REQUESTS_PATHS` exactly where `YOZORA_S9_PATHS` appears (import plus the subtraction or `not in` clause): `tests/p6_10_support.py`, `tests/test_longitudinal_demo.py`, `tests/test_p6_2b_dpdpa_criteria.py`, `tests/test_p6_7_requirement_card.py`, `tests/test_p6_7b_add_to_rfi.py`, `tests/test_p6_8_b2_docx_xlsx.py`, `tests/test_p6_8_board_report_v2.py`, `tests/test_p6_8_v3a_data_capture.py`, `tests/test_p6_9_file_set.py`, `tests/test_retention.py`. Add only; never delete a guard or a path. Re-run until no guard fails.
2. **Docs.** `docs/product/yozora-migration-map.md`: update the rows for `rfi.html`, `rfi_links.html`, `requests.html`, `magic_links.html`, `firm_settings.html`, `engagement_detail.html`, `assessment.html`, `scope_complete.html` with the new hooks; mark `engagement_retention.html` removed. `docs/product/yozora-design-system.md:99`: replace "an engagement keeps only Archive" with "Archive, unarchive and purge live in Settings; an archived engagement shows a read-only banner that links there."
3. **Status.** Add an entry to `tasks/2026-10-06-status-log.md`. Commit this plan file in the PR.
4. **Full suite.** `pytest -q` green on Python 3.13.
5. **Smoke test** (section 6). Report the output in the PR.
6. **Visual.** The pixel gates for `b6-rfi`, `b6-magic_links`, `b3-scope-complete`, `engagement_detail` and `b1-firm_settings` will diverge from the approved mockups on purpose. Do not tune to pass them. If Chromium is available, capture candidates with `design/harness/screenshot.py` against the smoke server at 1440 and 390, light and dark: scope tab, RFI Client links (nothing selected, one selected), Requests, Settings, archived Overview. List them in the PR for Saqlain's human gate (fidelity gate 4).
7. **PR.** Push and open one PR to `main`. No Claude attribution lines in commits or the PR body. Do not merge.

## 5. Integration checklist

- [ ] `grep -rn "engagement_retention" app/` returns nothing.
- [ ] `grep -rn "retention_forms\|data-retention-section\|archive-modal" app/templates` returns nothing.
- [ ] `grep -n "'" app/templates/pages/rfi.html app/templates/partials/rfi_links.html` returns nothing.
- [ ] `#rfi-links` and `#magic-links` ids unchanged; `hx-swap="outerHTML"` unchanged.
- [ ] `#reviewer-name` appears once per rendered page on rfi, settings and purge pages.
- [ ] Every `/design/pages/b6-*` state still returns 200 (`tests/test_yozora_s8_requests.py`).
- [ ] At most one `.btn.primary` visible per page state on Settings and Requests.
- [ ] No `display:none` added; no hex colours; no new CSS.
- [ ] Full `pytest -q` green.

## 6. Smoke test (implementer runs and pastes output in the PR)

Prestige is in Saqlain's local database only. Use the S8 seed: one engagement, one assessment, issued RFI version 1, draft version 2, one link (Maya Chen) covering four items with two receipts.

```bash
mkdir -p /tmp/rfi-smoke
python design/harness/seed_s8.py --output /tmp/rfi-smoke/db.sqlite3 --screen b6-rfi --state default
export DATABASE_URL=sqlite:////tmp/rfi-smoke/db.sqlite3 UPLOAD_DIR=/tmp/rfi-smoke/db.uploads
uvicorn app.main:app --host 127.0.0.1 --port 8001 &   # wait until it answers
eval "$(python - <<'PY'
import sqlite3
c = sqlite3.connect("/tmp/rfi-smoke/db.sqlite3")
a, e = c.execute("select id, engagement_id from assessments limit 1").fetchone()
s = c.execute("select id from report_snapshots where assessment_id=? and type='rfi' and is_issued=1", (a,)).fetchone()[0]
print(f"A={a} E={e} S={s}")
PY
)"
B=http://127.0.0.1:8001
```
The seed prints JSON with `assessment_id`. RFI snapshots have `type='rfi'`. The seed freezes some timestamps; if the Maya Chen link reads as expired, rows 4-5 change accordingly. Report the actual values and why, do not edit the seed.

| # | Command | Expect |
|---|---|---|
| 1 | `curl -s "$B/assessments/$A?tab=scope" \| grep -c 'data-checklist-group'` | 2 (or 1 if no recommended items) |
| 2 | `curl -s "$B/engagements/$E/requests" \| grep -o 'data-request-next-step="[a-z]*"'` | `versions` (draft 2 is newer than issued 1) |
| 3 | `curl -s "$B/engagements/$E/requests" \| grep -c 'data-request-something-else'` | 1, and no `open` on it |
| 4 | `curl -s "$B/assessments/$A/rfi?tab=links" \| grep -c 'data-rfi-unsent'` | item count minus 4 |
| 5 | same page: `grep -c 'In a link to Maya Chen'` | 4 |
| 6 | same page: `grep -o 'data-rfi-link-details[^>]*>'` | contains `hidden` |
| 7 | `curl -s -X POST "$B/assessments/$A/rfi/versions/$S/magic-links" -H 'HX-Request: true' -d item_ids=RFI-005 -d contact_email=nope \| grep -c 'value="RFI-005" checked'` | 1 |
| 8 | same POST with `-d contact_name=Smoke -d contact_email=smoke@example.com` then `grep -c data-rfi-new-link` | 2 (alert div and input) |
| 9 | `curl -s "$B/engagements/$E/requests" \| grep -c 'Smoke'` | at least 1 |
| 10 | `curl -sL "$B/engagements/$E" \| grep -c 'data-retention-section\|data-archive-control'` | 0 |
| 11 | `curl -s "$B/settings" \| grep -c "data-engagement-archive-row=\"$E\""` | 1 |
| 12 | `curl -si -X POST "$B/api/engagements/$E/archive" -d reviewer_name=Smoke -d return_to=/settings \| grep -i '^hx-redirect'` | `/settings` |
| 13 | `curl -s "$B/settings" \| grep -c "/api/engagements/$E/unarchive"` and `grep -c "/engagements/$E/purge"` | 1 and 1 |
| 14 | `curl -s "$B/engagements/$E" \| grep -c 'data-archive-settings-link'` | 1 |
| 15 | `curl -s -o /dev/null -w '%{http_code}' -X POST "$B/assessments/$A/rfi/versions/$S/magic-links" -d item_ids=RFI-006` | 409 (archived is read-only) |
| 16 | `curl -si -X POST "$B/api/engagements/$E/unarchive" -d reviewer_name=Smoke -d return_to=/settings \| grep -i '^hx-redirect'` | `/settings` |

Browser steps (Browser pane or Playwright, if available), at 1440 and 390:
1. RFI Client links: tick one item; the contact block appears and the count reads "1 item selected". Untick; it hides. Tick 21; the submit button is disabled and the count names the 20 limit.
2. Expand "4 items already in an active link"; each row names Maya Chen and an expiry.
3. Tab through the picker with the keyboard: checkboxes, the disclosure summary, then the revealed fields, in visual order.
4. Requests: "Request something else" is collapsed; submit it empty; it reopens with the error.
5. Settings: Archive a row; the confirm modal names the engagement; after confirm, the page reloads on Settings with the row in the archived group.
6. Scope tab: rows are visibly separated; Required and Recommended headers carry counts. Check 390px for chip wrapping.

Stop the server and delete `/tmp/rfi-smoke` afterwards.

## 7. Adversarial review checklist

- **Orphaned links.** Grep templates, JS and Python for `/rfi"`, `/rfi?`, `/requests`, `engagement_retention`, `archive-modal`; every hit resolves (section 3).
- **Lost audit actor.** Archive/unarchive from Settings sends `reviewer_name`; no remaining form `hx-include="#reviewer-name"` on a page without that input.
- **Nested forms.** Nothing with `hx-post` inside `#settings-form`; the retention select still saves.
- **Archived read-only.** RFI generate/issue/link and free-text link POSTs on an archived engagement still return 409 via `archive_write_guard`. The forms still render on archived RFI and Requests pages (unchanged behaviour; not fixed here).
- **Unissued RFI.** Client links tab shows the empty state and "Go to versions"; Requests next step is items or versions; no picker renders.
- **Stale or superseded version.** After issuing version 2, version-1 links stop counting toward coverage (existing rule `RFI_LINK_NOT_CURRENT`); `data-rfi-older-links` explains it. Linking from a non-current snapshot still 409s.
- **Coverage after revoke or expiry.** Items return to "Not yet sent" (status is not `active`).
- **Error re-render.** Validation errors keep the selection and typed values; the details block is open; the covered disclosure opens if a selected item is in it.
- **Twenty-item cap.** JS disables submit above 20; the server still rejects it.
- **Empty states.** No engagements in Settings; no links on Requests; every item covered (`data-rfi-all-covered`); no assessments on Requests.
- **Copy rules.** No `'` in `rfi.html` / `rfi_links.html`; framework-specific copy stays conditional (`has_dpdpa` flags untouched).
- **Keyboard and mobile.** Revealing the link fields does not move focus; `.req-picks` collapses to one column under the mobile breakpoint; the Requests next step shows once per breakpoint; Settings rows wrap without horizontal scroll at 390px.
- **Previews.** `/design/pages/b6-rfi` and `b6-magic_links` states render without the new context keys (template defaults).
- **Return-to redirect.** Only the exact string `/settings` changes the redirect.
- **Guards.** Allowance added once in `tests/yozora_paths.py` and in each enumerating guard; nothing deleted.

## 8. Questions for Saqlain (defaults apply if no answer)

1. **Archived engagement header.** Default: no Unarchive or purge buttons on the archived Overview; the banner links to Settings. Alternative: keep an Unarchive button in the banner too. The default keeps one home for the action.
2. **Settings list size.** Default: one flat list of every active, closed and archived engagement, archived last. Alternative: show only archived engagements plus a search, and keep Archive on the engagement header. The default is fine for the current single-firm MVP; revisit with Track 4.
