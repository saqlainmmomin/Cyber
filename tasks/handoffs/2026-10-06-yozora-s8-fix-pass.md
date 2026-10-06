# Yozora S8 fix pass (6 Oct 2026)

Branch `codex/yozora-s8` (merged A+B+C). Scope: fix the review findings below. Do not touch models, services, prompts, scoring, PDF, migrations. Do not read `validation/companies/*/answer_key.json`. No attribution. Leave changes uncommitted if staging is blocked. Keep must-keep ids, `hx-*`, `data-*`. Never weaken a guard. Fill Results at the bottom.

## Must fix
1. **Board report cannot be generated** (`pages/report_snapshots.html` ~62-90). The old page had a Generate form per type (`hx-post /api/assessments/{id}/snapshots`, `type=` gap_report / board_report / workpaper). The new page hard-codes `type=gap_report`. Make the Generate button follow the active report tab (label "Generate board report" on the Board tab, sending `type=board_report`), as `b6-report_snapshots.html` does. Workpaper versions are hidden by CSS (`.s8-workpaper-group{display:none}`) with no way to view or generate them: restore access (the old "Workpaper (live)" link and the workpaper group) without breaking the mockup's default state; if the mockup truly has no place for it, stop and write the question in Results.
2. **RFI Issue has lost its `hx-confirm`** (`pages/rfi.html` ~122). Restore the original text: "Issue this RFI version? Issued versions are permanent and cannot be changed or withdrawn."
3. **Two visible primaries on RFI Client links tab**: demote the header "Generate new RFI version" to secondary when `rfi_tab == "links"`.
4. **Dropped must-keeps in `partials/rfi_links.html`**: restore `data-rfi-link-error` on the error alert and `data-rfi-received` beside the per-item list; fix the duplicated `data-rfi-item` emission so an issued page does not carry it twice (test_p5_6 count assertion runs before issue; add an after-issue assertion).
5. **Client upload must not depend on JavaScript** (`magic/upload.html`). Each "Choose file" must work as a real form submission with `file-upload` and `item-key` (one form per item or a named select/radio fallback; the brief said per-item upload forms). Keep the dropzone styling. Move the inline script to a same-origin static file and tighten the client CSP to `script-src 'self'` (no `'unsafe-inline'` for scripts); add `font-src 'self'` (the vendored fonts are likely blocked; verify the font loads in a screenshot). Update `tests/test_magic_links.py` CSP assertion to the new exact string and **restore the no-external `<script` / `<link` check** that was dropped (assert only same-origin `/static/` sources).
6. **SoA Save**: do not leave a disabled primary during saving (keep it enabled but ignore clicks, or swap label with `aria-busy`); show a page-level result (count saved / first error with scroll-to-first-error); say "No changes to save" when nothing changed; map network failure to a readable message; remove or wire the dead All/Applicable/Excluded filter (wire to `data-applicability`; no new routes). Fix the "over 600 characters" preview copy to 1000.
7. **Compare link targets the same assessment** (`report_snapshots.html:19`): drop the per-row Compare link unless a real previous assessment exists in context; do not invent one.
8. **Comparison status labels**: use the design vocabulary (sentence case, no Title Case), e.g. "Partially compliant".
9. **Revoke error title**: an already-revoked link must not say "The link was not created".
10. **Request-card receipts** (`magic.py::_consultant_link_cards`): a later rejected upload must not hide an earlier accepted one; count received from accepted events.

## Layout misses worth fixing (from the pixel gate; diffs in `/private/tmp/claude-501/gate-<screen>/`)
- `b6-report_snapshots`: mockup shows Gap report and Board report as side-by-side groups; the candidate stacks them. Match the mockup.
- `b6-magic_invalid` / `b7-link-expired`: heading and card sit ~8px lower/different than the mockup; compare rects and fix real layout offsets (copy differences are exceptions: firm name and dates come from the app).
- `b6-magic_links`, `b6-comparison`, `b6-magic_upload` page heights differ from the mockup; fix only where it is a real structure difference, record the rest as exceptions with cause.
- `b6-rfi` and `b6-soa` fail on height only because the seeded `database` state uses the full real item catalogue; record as exception (do not trim real data to match).

## Do not
Game the gate (no magic padding or hard-coded mockup copy). The orchestrator re-runs the pixel gate (sandbox cannot bind localhost); you run the suite and design lint.

## Results
(Codex fills in.)
