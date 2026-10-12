# Handoff: prototype fix pass after Claude's review (Codex)

Docs only. Same rules as `tasks/handoffs/2026-10-12-ui-audit-second-run.md` (read its "Fixed inputs", "Saqlain's per-screen requirements" and "Rules" first). Do not commit, do not launch a browser, do not start a server. GET only against port 8011.

Claude screenshotted the five prototypes on the host at 1440 and 1280 (`docs/ui-audit/prototypes/screenshots/`, measurements in `docs/ui-audit/prototypes/measurements.json`). Look at the screenshots before changing anything. The structure is right. These are the defects to fix.

## Fixes

1. **Prose is too wide.** Measured longest rendered lines at 1440: report 98 characters, questionnaire 94, review queue 87, RFI 84. The rule is 60 to 80. The cause: `--prose:72ch`, and a `ch` is the width of the digit 0, which is wider than the average Inter letter, so 72ch holds about 95 characters. Set the prose measure to about 56ch (and apply it to the bold requirement statement in the questionnaire and to `.guidance`, scaled for 14px text) so no prose line exceeds 80 characters at 1440 or 1280. Correct the same number in `DESIGN_SYSTEM.md` and the spec (they say 72ch), and say why.

2. (Withdrawn. The sidebar is already sticky at full viewport height; the gap was an artefact of full-page screenshots.)

3. **Prototype commentary is written into the UI.** Remove it from the screens; a screen shows only what a real user would see. Explanations belong in `prototypes/README.md`. Examples to remove or replace with real UI copy: "Included; no add form", "The live engagement includes DPDPA and ISO requests. The first two rows demonstrate inclusion state with illustrative markers. Add forms contain candidates only.", "Guidance closed by default", "Switch any time", "Draft ready. Completion is a separate action.", the "Assessment workspace" chip, "Final ISO conclusions. Expand a gap to inspect the finding; review decisions are removed.", "Scope panel: applicability exceptions", "ISO 27001 focus". Check all five files for more of the same.

4. **RFI list is not tight enough.** Each row is three lines (about 109px); 40 items is 4,936px. Make it a dense table-like list, one line per collapsed row (48px or less): title, required or optional, state (Not requested, In draft RFI, Issued, Received), evidence already mapped (for example 2 of 5), and the row action. A chevron expands "what to send", example and "good looks like". Column headers sort on click; keep one default sort. Items already in the RFI have no add control and are grouped under an "In this RFI" heading at the top, so they are not shown again in the add form.

5. **Review queue list is heavy and wraps.** Each queue item is a bordered card and the Pending chip wraps to its own line. Make it a compact list: gap title (two lines at most), control code and name on one line, then outcome and risk in words on one line. Decided items are visually quieter than pending ones. No card per item.

6. **Review finding detail has a flat hierarchy.** Labels, badges and body text float as separate equal blocks. Put outcome and risk on the same line as the finding title block. Order stays: gap statement, risk and impact, recommendation, why this recommendation, where this finding came from. The recommendation must read as the strongest block after the gap statement (it is a primary deliverable), never smaller or quieter than the text around it. Label the reasoning "Why this recommendation". Keep the decision bar where it is.

7. **The statement of applicability pattern is not visible.** It is a collapsed disclosure at the bottom of `questionnaire.html`, so no screenshot shows it. It belongs to Scope, not the questionnaire. Remove it from `questionnaire.html` and add a sixth file, `scope-applicability.html`, in the same frame with the Scope stage active: a short list "Controls that do not apply" with a reason per excluded control (use two plausible Veldhara exclusions, marked `data-illustrative`), an "Add a control that does not apply" picker, and one line stating that the other controls are applicable with the standard justification, shown once. No per-control justification boxes.

8. **Report board view is too long and the view switch is hidden in a dropdown.** `report.html` is 9,353px tall. Board summary and auditor detail are two views of the same report: use a two-option toggle labelled "Board summary" and "Auditor detail" at the top right of the report, not entries in the Section select. Board summary fits in about three screens at 1440: executive summary prose; posture line; a domain table ordered weakest to strongest (domain, score, gaps by risk); then for each domain only its high and medium gaps, each with the non-compliance, impact if unresolved, risk, and the recommendation with its logic. Auditor detail holds all 93 controls with filters.

9. **Sub-section navigation needs a second option for Saqlain to choose from.** Today the spec says one "Section" select replaces the stacked bars. A select hides the destinations and costs two clicks for views the auditor switches between all day. Keep the five screens on the select (option A). Add `review-queue-sidebar.html` (option B): identical to `review-queue.html` except there is no Section select; instead, when the user is inside an assessment, the sidebar shows the assessment under Engagements with its sections as nested links (Review: Queue, Conclusions, Findings, Workpaper), the current one marked with `aria-current`. The horizontal stage bar stays. In `DESIGN_SYSTEM.md` "Navigation model" and in the spec, describe both options, say which you recommend and why, and mark the choice as pending Saqlain. Do not rewrite the rest of the spec around either option.

10. **Queue toolbar.** Keep the "Order" control (pending decisions first, then missing or contradictory evidence, plus risk and control order). Show the counts as plain text: "3 pending, 3 decided".

## Keep

Do not change the tokens, the status families, the conclusions table, the content, the `data-illustrative` ids or the illustrative manifest except where a fix above adds or removes elements. Update `prototypes/README.md`, `illustrative-content.json`, `requirements.json`, the README coverage table and `tools/verify_audit.py` so they match (seven prototype files now: the five, `scope-applicability.html`, `review-queue-sidebar.html`).

## Verification

- `python docs/ui-audit/tools/verify_audit.py` passes.
- No em dashes. Changes only under `docs/ui-audit/` and this file.
- In `prototype.css`, every prose role has a `max-width` in `ch` of 58 or less.

## Report back

Append `## Results` here: what changed per fix number, in one line each, and anything you could not do.

## Results

1. Changed prose to 56ch, including bold requirements, 14px guidance, expanded findings and recommendation roles; design system and spec explain why Inter’s zero glyph made 72ch hold too many characters.
2. Withdrawn fix left unchanged: sidebar remains sticky at full viewport height.
3. Removed prototype commentary from all five screens, replaced state text with user-facing copy, and moved source/demo limitations into prototypes/README.md.
4. RFI now has 40 one-line collapsed rows, a 45px static row-height calculation, sortable column headers, chevron guidance, and a separate In this RFI group with no add controls or duplicate candidates.
5. Queue now uses an unbordered divided list with a two-line gap title, one-line control/name, one-line outcome/risk, and quieter decided rows.
6. Finding outcome/risk join the title block; gap, impact, strong Recommendation, Why this recommendation and provenance follow in order, with the sticky decision bar retained.
7. Removed questionnaire applicability and added scope-applicability.html with Scope active, two illustrative exclusion reasons, an exclusion picker, and the standard justification shown once.
8. Added the top-right Board summary/Auditor detail toggle, executive summary/posture/domain risk table, 25 visible high/medium board gaps in two columns, and filters over all 93 auditor controls; the three-screen height target remains unverified and may be exceeded with all primary content visible.
9. Added review-queue-sidebar.html with nested assessment links and aria-current; design system and spec describe both options, recommend B for visible one-click destinations, and mark the choice pending Saqlain without changing the five original screens to B.
10. Retained Order choices for pending, evidence issues, risk and control order; counts are plain text: 3 pending, 3 decided.

Updated requirements.json, README coverage, component/archetype guidance, prototypes/README.md, illustrative-content.json and tools/verify_audit.py. The manifest now matches 208 screen/ID pairs across seven prototypes; existing IDs stay intact except the moved Scope element and the eight removed low-risk board elements, with new Scope exclusions, posture and sidebar copies registered.

Verification: python docs/ui-audit/tools/verify_audit.py passes; all interactive inline scripts pass node --check; static document fixtures exercised report toggle/filter and both queue sort functions, and RFI sort/add movement checks passed. git diff --check passes. Existing tokens are unchanged except the requested prose measure. All prose role caps are 56ch, audit text remains at least 14px, and changed paths are confined to docs/ui-audit/ and this handoff with no em dashes.

Limits: inspected all ten supplied pre-fix host captures at 1440 and 1280. No browser, server, commit, application mutation, AI spend or answer-key read occurred. Fresh rendered line lengths, overflow, sticky behavior and report height cannot be proved by this static-only pass; screenshots and measurements.json remain the original evidence. The board keeps all 25 high/medium impacts and recommendations visible, so fitting about three screens is not claimed. Issued/Received RFI state labels are specified but not fabricated as live row states; this prototype demonstrates Not requested and In draft RFI.
