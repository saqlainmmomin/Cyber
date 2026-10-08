# Evidence fixes — Part A results

## Changed files

- `app/services/magic_links.py`: resolve requested controls from the link's hash-verified RFI snapshot; validate assessment/engagement scope; assign the source assessment, including items without controls; create supporting EvidenceUse rows; save receipt, scope, mappings and audit together, rolling back and removing the blob on failure.
- `app/services/evidence.py`: optional deferred commit on successful engagement ingestion; existing callers retain their default commit behavior and scan rejection remains recorded.
- `app/templates/pages/evidence_detail.html`: three-line unmapped-engagement note and link to the existing inventory. This is the only overlap with Part B's template; preserve it when integrating B.
- `tests/test_p5_6_rfi_rebuild.py`: strengthen existing upload contract and cover single/multiple frameworks, empty control lists, exact snapshot/control selection, isolation, old issued links, scan rejection, snapshot integrity, removed frameworks and mapping-failure rollback/retry.
- `tests/test_magic_links.py`: engagement uploads remain excluded from assessment analysis; unmapped note is shown and disappears after mapping; existing inventory reuse action remains available.
- `tasks/todo.md`: Part A progress.
- This results file and `tasks/handoffs/2026-10-08-evidence-fixes-a-pr-body.md`.

The three supplied untracked input documents and `.codex-prompt.txt` are untouched and excluded from staging. No LLM prompts, calls, migrations, backfills, Part B viewer routes or answer keys were changed/read. All demo data and uploaded workbooks stay under ignored `data/` paths.

## Behavior verification

- Before implementation, the updated upload test failed because no EvidenceUse rows existed. The unmapped-note test failed before the template change. Empty-control/source-assessment tests and mapping-failure test failed before the atomic change.
- Focused final command: `OPENROUTER_KEY="" .venv/bin/pytest -q tests/test_p5_6_rfi_rebuild.py tests/test_magic_links.py tests/test_assessment_evidence_tab.py tests/test_evidence_service.py` — **113 passed** (23.30 seconds).
- Full required command: `OPENROUTER_KEY="" .venv/bin/pytest -q` — **1600 passed, 29 skipped** (290.95 seconds); baseline 1592 passed, 29 skipped. Eight additional parametrized/regression cases; all existing tests pass.
- `git diff --check`: passed.
- No stale protected-surface guard blocked verification. `tests/yozora_paths.py` was already removed on the starting branch; no allowances added.
- Read-only `git diff main...HEAD` was checked as requested. Local `main` is stale at `00f3300`; starting HEAD and `origin/main` are both `9b651fb`. Its three-dot diff includes inherited mainline work, including old prompt changes, not edits from Part A. The Part A working diff is limited to the files above.

## Demo receipt flow — observed against real routes

Setup: `OPENROUTER_KEY="" UPLOAD_DIR=data/uploads/evidence-a-demo .venv/bin/python scripts/demo/seed_demo.py --db data/evidence-a-demo.db`. No extraction, ingestion, snapshot, RFI or mapping services were mocked in this flow. All LLM calls were disabled.

The sandbox denied uvicorn binding `127.0.0.1:8011` with `Operation not permitted`. Computer Use denied Arc access, and the in-app browser was unavailable. Therefore this is an in-process HTTP/template click-through using FastAPI TestClient against the seeded DB, **not a completed browser click-through or visual/responsive verification**. Saqlain's browser review is still required.

On the final implementation:

1. Opened current demo ISO assessment `3ce69a86-c416-41f3-86ba-fa8af734de45` RFI page (200), generated and issued snapshot `439d020e-237a-4ce3-bfae-6f92086fa675` through the real HTTP routes (200).
2. Created an RFI client link for `RFI-019`, “Access control policy and recent user access review records,” through the HTTP route; opened its client page (200), which displayed the requested title.
3. Uploaded Saqlain's supplied synthetic workbook as `Part_A_Final_Access_Review_220.xlsx` through `/magic/{token}` (200). Client HTML showed “File received”. Stored extraction contains E131. No workbook bytes are committed.
4. Assessment Evidence tab (200) contains that filename. Evidence record `4f9a210b-ee76-4450-ac80-dca4becef58b` (200) lists all seven requested controls under Supports: ISO.A5.15, ISO.A5.16, ISO.A5.17, ISO.A5.18, ISO.A8.2, ISO.A8.3, ISO.A8.5. All uses have relevance `supporting`, and the Evidence's source assessment is the current assessment.
5. RFI page (200) lists the filename with its received marker; real page context reports 7 of 7 requirements mapped and the correct snapshot/item receipt. The version is in `active_versions_in_scope` for the current assessment.

Supplementary final CSV upload also passed source-assessment, seven-control Supports, assessment inventory and RFI receipt checks.

Logs: `/tmp/evidence-a-demo-final-smoke.log`, `/tmp/evidence-a-focused-tests.log`, `/tmp/evidence-a-full-tests.log` (local, uncommitted).

## Review and remaining limits

- Independent read-only review found the post-ingest commit gap and empty-control scope gap; both were fixed with regression tests. Final re-review confirmed both P1s closed and found no new correctness defects.
- **Handoff mismatch:** the existing “Reuse from another assessment” screen only offers Evidence with an existing use in another assessment. An unscoped engagement receipt cannot itself appear there (`evidence_reuse.reuse_candidates` joins EvidenceUse). The record shows the requested plain note and links to inventory, where the existing reuse action remains. Adding a new unscoped linking flow or extending reuse was left outside Part A; the note does not claim that this file can already be reused. This limitation needs owner resolution.
- **Part B integration:** preserve the small note near `data-evidence-status` when merging its `evidence_detail.html` changes. No Part B functionality was implemented.
- **No-auth note for Part B:** no auth exists yet; Track 4 adds it. Part B's original-file route must apply its specified version/status/path/MIME guards, but does not acquire auth through Part A.
- Browser click-through, screenshots and responsive verification remain blocked by the environment, as detailed above.

## Git delivery

Staging was attempted with an explicit list containing only the eight Part A implementation/test/tracker/results/PR-body files. Git failed creating `/Users/saqlainmomin/dpdpa-gap-tool/.git/worktrees/dpdpa-evidence-a/index.lock`: `Operation not permitted`. The external worktree Git metadata is outside this sandbox's writable roots. **Even staging is blocked**, so the changes remain unstaged in this checkout rather than staged. After the full suite passed, attempted `git commit -F /tmp/evidence-a-commit-message.txt -- <explicit eight owned files>` with message `fix(evidence): scope RFI client uploads to their requested assessment`. It failed because the two new results/PR-body paths were unknown to the index, which the failed staging step could not update. No commit was created; starting HEAD remains `9b651fb`. No push, PR creation or merge.
