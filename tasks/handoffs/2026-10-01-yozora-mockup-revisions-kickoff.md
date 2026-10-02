# Yozora mockup revisions: apply Saqlain's approval answers, fix the engagement flow, then start the build

**Written:** 2026-10-02. **Branch/worktree:** `claude/app-design-kickoff` in `/Users/saqlainmomin/cyberassess-docs`, PR https://github.com/saqlainmmomin/Cyber/pull/97 (open; merging is Saqlain's). No Claude attribution beyond the standard commit trailer; do not touch `validation/companies/*/answer_key.json`.
**Read first:** `tasks/handoffs/2026-10-01-yozora-mockup-approvals.md` (Saqlain's exported answers, verbatim), `docs/product/yozora-design-system.md`, `docs/product/yozora-fidelity-gate.md`, `docs/product/yozora-migration-map.md`, `tasks/handoffs/2026-10-01-app-design-system-handoff.md` (Results section), and the `NEEDS-b*.md` files in `docs/product/2026-10-01-app-design-mockups/screens/`.

## Where things stand
62 mockup screens (batches b1 to b7) exist in `docs/product/2026-10-01-app-design-mockups/screens/`, built on shared CSS in `design/` (`yozora-tokens.css`, `yozora-components.css`, `yozora-patterns.css`; `mockup-chrome.css` is mockup-only; `tokens_tool.py check` must pass). Saqlain has answered the approval page: **every proposed decision was ticked as agreed**. Batches 3, 4, 5 and 7 are approved outright; batches 1, 2 and 6 are approved with the changes below.

## What is settled (apply to every screen)
Signed-in user assumed; reviewer-name inputs stay removed until after auth (Track 4). Score circle stays neutral. Firm accent must pass contrast at upload. **States with no real primary action show no primary** (remove the disabled and invented primaries in b3, b5, b6 and anywhere else). Design doc approved as the build reference. Also agreed, apply as written in the walkthrough: delete screen has no primary (red destructive button in the dialog only); remove the invented details on the new-engagement form (control counts, Roadmap tags); review period and cut-off shown in headers; Progress column hides on medium screens; answer scale wording; screening is DPDPA-only; evidence reuse becomes tick boxes plus one confirm button; combined report view removed; priority shown as words (Do first, Next, Planned, Backlog); statement of applicability saves in one action; **show the control code (e.g. A.5.15) in small muted text in lists**; one Generate button following the selected report tab; toasts last 4 s with errors persistent; typed-name delete confirm; error page reference code; fix the two known glitches (kebab menu overflow at 390 in `b7-menus-popovers`, clipped button in `b7-mobile-shell-sheet`).
**Ambiguous, ask Saqlain one short question before building them:** the "Add assessment" button on engagement detail, "Export actions" on remediation, "Open current report" on comparison, and the email-the-firm button (needs a firm contact field). The walkthrough said "keep only if you want those features"; they ticked agree without saying which. Default if unanswered: leave them out.

## Changes Saqlain asked for (do these first)
1. **Retention does not belong on client or engagement pages.** The retention-period box on client detail (`b1-client_detail`) and the retention/archive details on engagement detail (`b2-engagement_detail`) break the flow. Move retention into firm Settings (`b1-firm_settings`, under data housekeeping) as a firm-level value changed rarely. Engagement pages keep only what the user must act on (e.g. an Archive action if still needed). Update the migration map rows for `engagement_retention` and `client_detail`.
2. **One central Evidence inventory instead of fragmented evidence tabs.** Remediation tracker should not sit next to AWS evidence, and AWS evidence should not be its own tab. Design a single Evidence screen per engagement (and the top-level Evidence nav item) listing everything collected and reviewed: uploaded documents, AWS pulls, client-sent files from magic links, reused evidence, with source, status (received, in review, accepted, quarantined) and the requirements it supports. Documents, desk review, evidence detail and reuse hang off it. Remediation tracker moves to its own place (decide: Findings and actions area). Redo the affected b2/b4 screens and update the nav.
3. **The engagement flow is not understandable from fragmented screens.** Before more mockups, produce a one-page flow map (a diagram plus a short walk-through, as an HTML page in the mockups folder) showing the engagement journey end to end: create, scope, questionnaire, evidence, analysis, review, report, RFI and versions, with where each screen lives, what the tabs are, and what the user's next action is at each stage. Show Saqlain this first. Rework tab structure and the stepper to match whatever they approve.
4. **Client magic-link screens look poor.** `b6-magic_links` (staff side) and the client upload page `b6-magic_upload` need a visual pass: show what each link was provisioned for (the requested evidence items, which are received, expiry) so it reads as a purposeful request, not a bare list. Client-facing, mobile-first, firm accent only.

## Method and constraints
- Edit the HTML directly in `screens/`; use shared classes only, no new local `<style>` blocks (add any new component to `design/yozora-components.css` or `yozora-patterns.css` and the gallery first, then run `python3 design/tokens_tool.py check`). Hard rules in the design doc still apply (sentence case, no numbered labels, one primary per state, severity colours fixed).
- Subagents: use Sonnet subagents for screen edits in parallel (one per area), each told the rules above; review their output with screenshots yourself. Playwright for checks: recreate a scratch venv (`python3.13 -m venv /tmp/pw && /tmp/pw/bin/pip install playwright pillow`, launch with `executable_path` set to the cached Chromium under `~/Library/Caches/ms-playwright/chromium-*/`). Check each edited screen at 1440, 1024 and 390, light and dark: no horizontal overflow, no uppercase, at most one visible primary per state.
- Serve: `cd /Users/saqlainmomin/cyberassess-docs && python3 -m http.server 8010`; the review page is `docs/product/2026-10-01-app-design-mockups/approval-walkthrough.html` (update its screen list and decisions if screens are added or removed; its saved answers live only in Saqlain's browser and exported to the file above).
- CI: the file-set guard in `tests/test_p6_2b_dpdpa_criteria.py` allow-lists files; any new top-level file outside `design/`, `docs/product/2026-10-01-app-design-*`, `docs/product/yozora-*` or `tasks/handoffs/2026-10-01-yozora-*` needs an `:(exclude)`-style allowance there. Auto-fix watches the PR for CI.
- Commit to the same branch; merging is Saqlain's.

## Then
After Saqlain approves the flow map and the revised screens: update `docs/product/yozora-migration-map.md` and `docs/product/yozora-design-system.md`, regenerate the S1 to S9 handoffs (`tasks/handoffs/2026-10-01-yozora-s*-handoff.md`) so the evidence screens and retention move are reflected, and hand S1 to Codex. Trademark search for Yozora is still Saqlain's and gates Track 4, not this work.

## Report back
Append a `## Results` section here: what changed, screens added or removed, the approved flow map, open questions, and what Saqlain still has to decide.

## Results

**Status (2026-10-02): all four requested changes and the settled fixes are applied. The flow map is approved. The revised screens still need Saqlain's look before the build "Then" steps start.**

### Flow map (approved)
- `docs/product/2026-10-01-app-design-mockups/flow-map.html` contains the level diagram, the journey diagram with the client-request loop and the findings branch, a stage-by-stage table (where each stage lives, what happens, the main button, the screens), and the list of changes.
- Saqlain approved it on 2 Oct and chose the recommended option on every question:
  - **Tabs:** engagement tabs are Overview, Evidence, Findings and actions, Reports. Assessment tabs are Overview, Scope, Questionnaire, Review, Report.
  - **Stepper:** one stepper (Scope, Evidence, Questionnaire, Review, Report), on the assessment Overview only. Analysis runs inside Review.
  - **Evidence:** lives on the engagement only. The assessment's Evidence step opens it filtered to that assessment.
  - **Single assessment:** an engagement with one assessment opens straight on that assessment.
  - **Extra features:** all four stay (Add assessment, Export actions, Open current report, Email the firm). Saqlain called them "all good features".
- `screens/IA-SPEC.md` is the binding spec the screens follow: the side menu, tab rows, full breadcrumbs, sub-view `.seg` groups, and where every screen lives.

### What changed
1. **Retention.**
   - Removed from `b1-client_detail` (and its save and error states) and from `b2-engagement_detail`.
   - Added as "Keep archived engagements for" in `b1-firm_settings`, under data housekeeping. The page's one Save changes button moved to the page header.
   - The engagement keeps only Archive, as a ghost button.
2. **Evidence.**
   - New `b4-evidence.html` (Engagement / Evidence / Inventory). Every item shows source (Upload, AWS, Client link, Reused), assessment, supported control codes and status.
   - States: default, upload, filtered, empty, loading, error, and all (the cross-engagement view from the side menu).
   - Status labels follow the real states: Scanning (quarantined), Available, Rejected, Out of date. The app has no "in review" or "accepted" state for evidence.
   - Desk review, AWS, reuse, detail and cited-text pages are now sub-pages of Evidence. Desk review is retitled "Pre-fill questionnaire" and AWS "Pull from AWS".
   - `b6-magic_links` is the Requests view. `b6-rfi` is one assessment's request.
   - Remediation moved to its own tab: `b2-remediation_tracker`, retitled "Findings and actions".
3. **Flow.**
   - Every staff screen now has the complete side menu (Home, Clients, Engagements, Review, Evidence, Reports, Settings), the right tab row and full breadcrumbs.
   - Review pages (queue, conclusions, findings, workpaper) and Report pages (report, versions, applicability, basis, release, compare) sit under assessment tabs instead of floating.
   - `b3-hub` (assessment Overview) has stage states (Not started, Evidence, Questionnaire, Review, Report), and its primary button follows the stage.
   - `b2-engagement_detail` has no stepper. It shows assessments with Stage and Next step, plus three summary cards.
4. **Client links.** Each link is now a request card showing:
   - the contact
   - "From RFI version N"
   - status
   - an "N of M received" progress bar
   - a per-item checklist with files and times
   - the expiry

   The new-link form picks items with tick boxes. The client upload page is a mobile-first checklist, with a choose-file control per item, firm accent only, and "Powered by Yozora". New components (`.req*`, `.mk`) are in `yozora-patterns.css` and the gallery.
5. **Settled fixes.**
   - Disabled and invented primaries were removed in about 30 states across b1 to b6. The full list is in the agent report, summarised in the commit.
   - Control codes now show in small muted text in lists (SoA, conclusions, review queue, report, workpaper, desk review, comparison, evidence).
   - Invented control counts and "Roadmap" tags were removed from the new-engagement form.
   - The kebab menu overflow in `b7-menus-popovers` at 390 is fixed.
   - Firm Settings has a new "Contact email for clients" field, which backs the kept "Email the firm" button.
   - The b7 screens got the current side menu.
6. **Docs.**
   - `yozora-migration-map.md` has a revision note, and the rows for assessment, client_detail, engagement_detail, engagement_retention, remediation_tracker, integrated_reports, aws_evidence, documents_tab, document_list, magic_links, magic/upload and rfi are updated.
   - `approval-walkthrough.html` now has a revision note linking the flow map, the new Evidence tile, and regenerated thumbnails.

### Screens added and removed
- **Added:** `screens/b4-evidence.html`, `flow-map.html` (with a screenshot, `flow-map-1440.png`) and `screens/IA-SPEC.md`.
- **Removed (moved to `superseded/`):** `b4-documents_tab.html` and `b4-document_list.html`, both folded into the evidence inventory.
- There are now 61 screens.

### Checks
- **Playwright:** 984 loads, covering every b1 to b7 screen and every state-bar state at 1440, 1024 and 390, light and dark. Results: no horizontal overflow, no uppercase, no disabled primaries, at most one visible primary, no console errors apart from the favicon 404, and every app-shell page has the full side menu.
  - The b5 files stack their states on one page, so a whole-page count shows several primaries. Their per-state counts were checked by the agent that edited them (420 loads, `?state=` per state).
- **Other checks:** `tokens_tool.py check` passes. `tests/test_p6_2b_dpdpa_criteria.py` passes (31, including the file-set guard).
- **Visual review:** I looked at the flow map in light, dark and 390, and at evidence, engagement overview, assessment overview, review queue and client links at full size. I did not look at every other screen at full size.

### Corrections and deviations
- **Evidence reuse wording:** my first spec said evidence is reused "from an earlier engagement". The app (`app/services/evidence_reuse.py`) reuses evidence between assessments of one engagement, so the copy now says "Reuse from another assessment".
- **Client links:**
  - The real app has no client contact name or email on a link. The cards show both, which needs backend support.
  - Items are tick boxes from the RFI, so free-text items are dropped. The link token is shown once, at creation only.
- **Small screens:** at 390 the breadcrumb hides the client and engagement levels on deep pages. A proper breadcrumb overflow component is still missing from the CSS (already listed in the design doc).
- **b2-engagement_purge:** no tab row; it is a destructive flow reached from Archive.
- **b7-mobile-shell-sheet:** the clipped button could not be reproduced, so the file is unchanged.

### Open questions / Saqlain still has to decide
1. **Approve the revised screens:**
   - Start at `approval-walkthrough.html` or `flow-map.html` (served on :8010).
   - Then: update `yozora-design-system.md` (tabs, sub-view `.seg`, stepper placement, `.req` components), regenerate the S1 to S9 handoffs, and hand S1 to Codex.
2. **Backend changes the kept features need:** a client contact on magic links, a firm contact email, Add assessment, and Export actions.
3. **Design choices:**
   - `b6-rfi` stacks two `.seg` rows (Inventory/Requests, then Items/Versions/Client links). Merge them?
   - Should "Pre-fill questionnaire" be a ghost button on the inventory (current) or go in the "Add from" menu?
   - Framework tabs inside Report, SoA and Compare are still a `.tabs` row under the assessment tabs. Keep, or switch to a `.seg`?
4. Trademark search for Yozora (gates Track 4).
