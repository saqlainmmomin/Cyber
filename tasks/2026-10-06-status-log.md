# Status log: 2026-10-06

Supersedes `tasks/2026-10-04-status-log.md`.

## Current phase
Phase 6 deliverables done. **Yozora UI redesign complete (S1-S9 merged).** v1 pipeline live, v2 parked (P6-5c). Local-only until Track 4.

## Merged since 4 Oct
- P6-8 V3-B 16:9 board deck (#101); V3-C prior domain scores on `main`.
- Yozora S3 to S7 (Home, clients, settings, engagements, reports list, scope, questionnaire, desk review, evidence, review, findings, report, narrative, board inputs).
- **S8 (#114):** engagement Requests page, RFI page, report versions, statement of applicability (one Save, changed rows posted sequentially), comparison, client upload and invalid-link pages (no-JS upload, same-origin script and font CSP).
- **S9 (#115):** 404/500 pages with a reference code, global toasts/skeletons/failed-swap alerts/menus/modals, lint allow-list deleted, Tailwind retired (`style.css` kept for the HTMX indicator and the Evidence drop-zone).
- Suite on `main` after S9: 1551+ passed, 30 skipped (`test_p6_8_board_report_v2::test_scenario_3` is flaky on `main`).

## Pixel gate state (exceptions, not fitted)
S8 and S9 gates were run once, not iterated. Misses are content-driven (full real RFI/SoA catalogues against short mockups, app-sourced names and dates) or mockup-scaffold layout on component specimens. `b7-dark-dense` has no registered preview state and did not run. The dark and mobile sweep of every earlier screen was not run.

## Known follow-ups
- `app.js` injects Tailwind-only classes (the `?` shortcut modal, dashboard filter, save-indicator colours, review highlights); unstyled since before S9.
- 403/405 return bare JSON to a browser; S9 handlers cover 404/500/catch-all.
- Account menu popover compare and the 1024 side-panel offset (from S1/S2).
- Temporary `reviewer-name` inputs stay until Track 4 (auth).
- S8 changed an invalid-link assertion by decision: expired, revoked and unknown links now have distinct copy (reachable only with the exact token).

## Next
Track 4: auth and hosting. A scope draft was started in Saqlain's checkout (`tasks/2026-10-04-track4-scope.md`, not yet committed).

## Workflow notes
Codex builds in worktrees, Claude commits and reviews (Codex cannot stage, bind localhost, or import `boto3`); the orchestrator runs the suite and the gate. Claude pushes branches and opens PRs; Saqlain merges.
