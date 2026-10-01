# Next session: P6-10 revision and implementation, v3 board-deck handoff to Codex, P6-7b check, then app design

## Goal

Finish Phase 6 Track 2 deliverables work and set up the next phase. There are four workstreams, in this order.

1. **P6-10 design revision (subagent).** A subagent revises the existing P6-10 narrative design so it fits the approved v3 board-deck format.
2. **P6-10 implementation (this session).** You implement P6-10 against the revised design, using the usual Codex flow (see Constraints).
3. **v3 board-deck handoff (the same subagent).** After the P6-10 revision, the subagent writes the v3 deck implementation handoff with failing contract tests, and dispatches **only the part that doesn't conflict with P6-10** to Codex. Sequencing is set out in workstream B.
4. **P6-7b.** Find out what is actually left (see workstream C) and finish it.

After all four are done, the next phase is **app (UI/UX) design work**, before Track 4. Do not start it in this session. Write its kickoff (workstream D).

**Done when:**
- P6-10 is implemented, independently verified, adversarially reviewed and opened as a PR.
- The v3 deck handoff and its contract tests are committed on their branch.
- Part V3-A is dispatched to Codex: running, or finished and verified.
- The P6-7b question is resolved with Saqlain.
- An app-design kickoff file exists.
- The Results section below is filled in.

## Current state (as of 2026-10-01)

**On `main` (`origin/main`):**
- **#92 (P6-8 B2: DOCX + XLSX from the board-report sidecar) is MERGED** (`8136bec`). Its renderers support schema v2.
- **P6-7b was merged as #84** ("one-click add-to-RFI from v2 requirement cards"), although `tasks/todo.md` line ~98 still says "P6-7b deferred". The todo line is stale.
- v1 analysis is live. The v2 pipeline is **parked** (P6-5c decision, `tasks/2026-09-30-p6-5c-decision-park-v2.md`).

**Open: [saqlainmmomin/Cyber#93](https://github.com/saqlainmmomin/Cyber/pull/93)**, branch `claude/report-format-review`. It holds the **approved** board-report target format:
- Decision doc: `docs/product/2026-10-01-board-report-format.md`. Read all of it: decisions F1-F10 and the section 7 implementation plan.
- Mockups and generator prototypes: `docs/product/2026-10-01-board-report-mockup/`. They contain:
  - `board-deck-PROPOSED.pdf` (25 slides, 16:9);
  - `board-workbook-PROPOSED.xlsx`;
  - `board-deck-sample.pptx`;
  - `render_deck.py` (its `view()` is the presenter prototype) + `deck_template.html`;
  - `render_xlsx2.py`, `render_pptx.py`, `enrich.py`, `gen_doc.py`;
  - `deck_document.json`, a synthetic v3 document.
- Results: `tasks/handoffs/2026-10-01-report-format-reevaluation.md`.
- **Before starting, check whether #93 is merged** (`gh pr view 93 --repo saqlainmmomin/Cyber`). Merging is Saqlain's. If it isn't merged, read these files from the `claude/report-format-review` branch, and ask Saqlain to merge it before any branch that cites the doc is opened as a PR.

**The approved format in one paragraph:**
- **PDF:** becomes a 16:9 landscape deck (WeasyPrint): cover, contents, assessment overview, rating definitions, executive summary, domain status board, risk profile, board asks, key observations (n/N), roadmap, initiatives, since last report, limits, sign-off, annexure.
- **PPTX:** replaces DOCX as the editable format for v3. DOCX stays for v1/v2 sidecars.
- **XLSX:** becomes a client workbook in a Big-4 idiom.
- **New consultant-entered fields:** `Finding.business_impact`, `Finding.recommendation`, `Action.responsibility`, initiative complexity/benefit, board asks.
- **Theme:** firm-configurable.
- **Schema:** document schema **v3 is shared with P6-10** (F7).
- **Priority:** numeric priority is removed from client output, and initiative Priority is derived.

**P6-10 existing design:**
- Branch `claude/p6-10-narrative`, one commit `4cf0da0`, **47 commits behind `origin/main`**. Remote branch exists.
- Worktree: `/Users/saqlainmomin/dpdpa-gap-tool/.claude/worktrees/agent-a73abd9fbc84263ef`.
- Contents: `tasks/handoffs/2026-09-28-p6-10-remediation-and-narrative.md` (decisions D-P6-10-A..P), `tests/test_p6_10a_remediation_draft.py`, `tests/test_p6_10b_narrative.py`, `tests/p6_10_support.py`.
- **Known staleness:**
  - It assumes `DOCUMENT_SCHEMA_VERSION = 1 → 2`. Main is already v2 (P6-9), so P6-10 must claim **v3**.
  - It renders the narrative into the old portrait template.
  - It must add v3 to B2's supported schema versions, since #92 is merged.

## Workstreams

### A. P6-10: revise the design (subagent), then implement (you)

**A1. Subagent revision.** Spawn one subagent (local, `model: sonnet`; see Constraints). In the P6-10 worktree it must do the following.
1. **Update the branch:** `git fetch`, then **merge** `origin/main` into `claude/p6-10-narrative` (never rebase). Resolve guard-test conflicts by keeping both sides.
2. **Revise the handoff in place**, with a dated "Revision 2026-10-0x" note at the top that cites the decision doc. Required changes:
   - **Schema:** P6-10 bumps `DOCUMENT_SCHEMA_VERSION` 2 → **3**. Update D-P6-10-K/P and the B1 scenario-4 version line.
   - **Exports:** add 3 to the B2 exporters' supported schema versions (`app/services/board_exports.py`), so v3 sidecars still export with the v2 layout until the deck work replaces it. Add a contract test for this.
   - **Stable finding references:** store **stable finding IDs** next to the per-section aliases in the sidecar narrative (e.g. `finding_refs` aliases plus `finding_ids`). The deck renders refs as `R-xx` (top-risk rank). The design must let a later presenter map a sentence's refs to `R-xx` without re-reading the DB.
   - **Placement for now:** keep rendering in the *current* portrait template. Say explicitly that the v3 deck work (workstream B) moves it into the executive-summary verdict panel (`data-narrative="executive"` inside `data-slide="executive-summary"`) and the per-framework narrative.
   - **Tests:** update any contract test whose expectations change, in the three P6-10 test files only. Re-verify the red state: failures must be clean `ModuleNotFoundError` or assertion failures, not collection errors.
   - **Guards:** add per-PR file-set guard allowances for P6-10's files where existing guards block it. Use the pattern of the `REPORT_FORMAT_FILES` / `P6_5C_RECORD_FILES` tuples in `tests/test_p6_2b_dpdpa_criteria.py`. Never delete a guard.
3. **Commit** on `claude/p6-10-narrative` and push. No Claude attribution.

**A2. You review the revision**, then implement P6-10 the usual way:
1. Dispatch Codex for 10a, then 10b, as the handoff's D-P6-10-A describes.
2. Verify independently: re-run tests, read the diff, check its scope.
3. Run an adversarial review: the `code-review` skill at `high`, plus manual reading.
4. Send scoped fixes back to Codex.
5. Open the PR.

Live LLM spend is allowed only for P6-10's own smoke checks, after asking Saqlain. The expected cost is cents (DeepSeek pricing).

### B. v3 board deck: handoff and Codex dispatch (the same subagent, after A1)

**Sequencing problem:** the deck's document, template and exporter changes touch the same files as P6-10 (`board_report.py`, the schema version, the template, the golden). Running both at once would collide. So split the deck work, as the decision doc section 7 allows:

- **V3-A, data capture.** No `build_document`, schema, template or exporter changes. Covers:
  - migrations: `findings.business_impact`, `findings.recommendation`, `actions.responsibility`, initiative metadata keyed by `(assessment_id, cluster/group id)` (title, complexity, benefit), `assessments.board_asks_json`;
  - model fields and validation;
  - Finding, Action, roadmap-group and versions-page form fields;
  - audit events;
  - firm theme settings (`firm_logo_path`, primary/secondary/accent colours, validated hex);
  - vendoring Barlow Condensed (OFL) next to the Noto fonts, pinned by hash.

  **It can run in parallel with P6-10. Dispatch it to Codex now.**
- **V3-B, document v3 content and presentation.** Covers:
  - the derived fields (`observations`, `initiatives`, `status_board`, `severity_dashboard`, `risk_matrix`, `takeaways`, `board_asks`, `theme`, removing numeric priority);
  - the `app/services/board_view.py` presenter;
  - the 16:9 deck template;
  - the v3 XLSX and PPTX renderers (`python-pptx`); DOCX returns 410 for v3;
  - golden re-record and tests.

  **Write it and commit it now, but dispatch it to Codex only after the P6-10 PR and the V3-A PR are merged.** Branch it from the `main` that has both.

**What the subagent does:**
1. Write `tasks/handoffs/2026-10-0x-board-report-v3-deck.md` covering both parts. Use decision IDs `D-P6-8-V3-*` that map to F1-F10, and pin the exact v3 schema delta on top of P6-10's v3.
2. Write **failing contract tests first**, in separate files per part: `tests/test_p6_8_v3a_data_capture.py` and `tests/test_p6_8_v3b_deck.py`, plus shared support if needed. The list of contract tests is in section 7 of the decision doc. Verify the red state.
3. Base V3-A on `origin/main`, on branch `claude/p6-8-v3a-data-capture`, using a git worktree. Commit the handoff and tests there.
4. Put V3-B's tests on `claude/p6-8-v3b-deck`, from the same base, to be merged forward later.
5. **Dispatch V3-A to Codex** from its own worktree:
   - Set the worktree up first: `git worktree add ../cyberassess-v3a -b ... origin/main`, symlink `.venv`, copy `.env`, record the baseline test count.
   - Run: `codex exec -C <worktree> -s workspace-write -m gpt-5.6-luna -c model_reasoning_effort="xhigh" "<prompt>" < /dev/null > <log> 2>&1 &` (backgrounded with `nohup`).
   - Confirm the log moves past the prompt echo within two minutes.
   - The prompt points Codex at the handoff, the exact file set, and "make the V3-A tests pass without editing them".
6. Report back the branch, the log path and the PID.

**You then verify and review V3-A when Codex finishes:**
- independent test run, diff scope, adversarial review, scoped fixes, PR;
- re-run the full suite with `git branch -f main origin/main` in the worktree first;
- a migration must be reversible and tested.

### C. P6-7b: find out what is actually left

P6-7b ("one-click add-to-RFI") merged as #84, but only for **v2** requirement cards, and v2 is parked.
1. Check whether the add-to-RFI action is reachable from the **v1** review flow. Read `tasks/handoffs/2026-09-28-p6-7-requirement-card.md` and the P6-7b handoff on `claude/p6-7b-add-to-rfi`, and run the app with the `run` skill.
2. Ask Saqlain one focused question with 2-3 options. For example:
   - (a) extend add-to-RFI to v1 cards;
   - (b) it's done, just correct `tasks/todo.md`;
   - (c) something else he means by P6-7b.
3. Do what he picks. If it's (a), use the same design → Codex → review flow, kept small. It doesn't touch the board-report files, so it can run in parallel.

### D. Then: write the app-design kickoff (do not start the design)

Saqlain wants to work on **the design of the app (UI/UX)** before Track 4 (P6-11 to P6-14: identity/auth, CSRF, encryption, upload hardening, Bedrock `ap-south-1`, deploy).
1. Write `tasks/handoffs/<date>-app-design-kickoff.md`. Inventory the current Jinja2 + HTMX + Tailwind pages and the core flows: engagement, assessment, questionnaire/desk review, requirement cards and review queue, RFI, reports and versions.
2. Write down the **visual system the board deck established**, so the app can share it: indigo/royal/teal palette, condensed display face, severity/outcome colours, status board, KPI tiles.
3. List open questions for Saqlain.
4. Update `tasks/todo.md` to record the order: Track 2 done, then app design, then Track 4.

## Key files

| Path | What it is |
|---|---|
| `/Users/saqlainmomin/dpdpa-gap-tool` | Primary checkout, on `main`. **Never switch its branch while another process uses it.** Use worktrees. |
| `docs/product/2026-10-01-board-report-format.md` (PR #93 / main) | Approved format: F1-F10, the slide and sheet spec, the v3 plan, the tests to change |
| `docs/product/2026-10-01-board-report-mockup/` | Mockups and prototypes for workstream B |
| `/Users/saqlainmomin/dpdpa-gap-tool/.claude/worktrees/agent-a73abd9fbc84263ef` | P6-10 worktree (`claude/p6-10-narrative`) |
| `tasks/handoffs/2026-09-28-p6-10-remediation-and-narrative.md` (P6-10 branch) | P6-10 design to revise |
| `app/services/board_report.py` | `build_document`, `DOCUMENT_SCHEMA_VERSION` (2 on main) |
| `app/services/board_exports.py` | B2 DOCX/XLSX renderers (#92) |
| `app/templates/reports/board_report.html` | Current portrait template |
| `app/services/remediation_groups.py` | UCC clusters (`cluster_index`), the basis for initiatives and the Reference column |
| `tests/golden/p6_8_board_document.json` | Golden v2 document |
| `tests/test_p6_8_board_report_v2.py` | B1 contract and `_engagement_fixture` |
| `tests/test_p6_2b_dpdpa_criteria.py` | File-set guard with per-PR allowance tuples |
| `tasks/agent-ownership.md` | Claude/Codex split; check it before scoping a handoff |
| `tasks/todo.md` | Plan tracker (the P6-7b line is stale) |

## Constraints (decided; do not relitigate)

- **House rules:**
  - only approved Conclusions, Findings and Actions reach client outputs;
  - scores, risk and priority are deterministic, never an LLM;
  - no score is combined across frameworks;
  - framework-specific copy is conditional;
  - report versions are write-once, and the sidecar is the record;
  - assessment period and evidence cut-off are on every deliverable.
- **The format decisions F1-F10 are approved.** Don't reopen them. If implementation reveals a real problem, raise it with Saqlain with 2-3 options.
- **Answer-key isolation:** never open `validation/**`, `answer_key.json` or `scripts/validation/**`.
- **Subagents:** local subagents run on `model: sonnet`. Opus-level work goes to a remote subagent only if it truly needs it.
- **Codex:** `gpt-5.6-luna` at `xhigh` by default. Always `< /dev/null` when backgrounded. One worktree per parallel Codex run. If you hit a quota error, don't loop-retry; report it.
- **Never trust Codex's self-report.** Re-run tests, read the diff, review adversarially before any PR.
- **Guards:** when an old file-set guard blocks a legitimate PR, add a scoped per-PR allowance with a comment. Never delete it.
- **Commits:** no Claude attribution in this repo (no `Co-Authored-By`, no "Generated with Claude Code").
- **Merging is Saqlain's.** Don't merge. Pushing branches and opening PRs is fine.
- **LLM spend:** ask Saqlain before any live run.
- **Untracked handoff files:** before `git pull` on the primary checkout, check `git status`. Remove local untracked handoff copies that a merge is about to bring in (diff them first).

## Verification

- **P6-10:**
  - the P6-10 contract files are green, untouched except by the A1 revision;
  - the full suite is green, apart from known transient guards, with the counts recorded;
  - a generated board-report version freezes the accepted narrative in its sidecar;
  - a v3 sidecar exports via the B2 DOCX/XLSX;
  - an adversarial review is done.
- **V3-A:**
  - the V3-A contract tests are green;
  - the migrations upgrade and downgrade on a scratch DB;
  - forms save and audit the new fields, checked in the browser with the `run` skill (screenshot);
  - the theme settings reject bad hex values;
  - the full suite is green.
- **V3-B:** the handoff and red tests are committed, and dispatch is explicitly deferred. Note the trigger: "after P6-10 and V3-A merge".
- **P6-7b:** Saqlain's choice is recorded and done.
- **App-design kickoff:** the file is written, and `tasks/todo.md` is updated.

## Report back

Append to the `## Results

Session of 2026-10-01. Workstream status: A (P6-10) implemented, reviewed, PR #95; B (v3 deck) V3-A PR #94, V3-B committed and held; C (P6-7b) resolved; D (app-design kickoff) written and pushed.

### Branches, PRs and commits

| Item | Branch | Commits | PR |
|---|---|---|---|
| P6-10 revision (A1) | `claude/p6-10-narrative` | merge `3a91bb1` (origin/main 1df2b68, no rebase), revision `5723ea5` | |
| P6-10a (Stage 3) | same | `5861dd9` | |
| P6-10b (Stage 4, schema v3) | same | `f9c2f98`, guard allowance `0ac3a83`, review fix `3769617` | [#95](https://github.com/saqlainmmomin/Cyber/pull/95) (Saqlain pushed and opened it; push and `gh pr create` were denied to Claude) |
| V3-A (data capture) | `claude/p6-8-v3a-data-capture` | `7d12576` (handoff + tests), `8aa50a2` (Codex), `d42e055` (review fix) | [#94](https://github.com/saqlainmmomin/Cyber/pull/94) |
| V3-B (deck, held) | `claude/p6-8-v3b-deck` | `37386ad` (handoff + red tests only) | none; **not dispatched** |
| App-design kickoff | `claude/app-design-kickoff` | `4974097` | none (docs only) |

### Test counts

- Baseline on origin/main: 1224 passed, 10 skipped.
- P6-10 red state after revision: 26 failed, 2 passed (the two P6-10 files), no collection errors. Verified independently.
- P6-10a (Codex): 16 passed; full suite 1241 passed, 11 failed (the expected 10b tests).
- P6-10b committed tree after my guard fixes: 1253 passed then, 1257 passed, 10 skipped, 0 failed after the review fix (retention scenario 13 is a transient that fails only while test files are uncommitted; it passed once committed).
- V3-A red state: 34 failed, 1211 passed. Codex: 21 V3-A tests passed twice; full suite 1245 passed, 10 skipped. After the review fix: 22 V3-A tests pass; the only failure before the guard allowance was the file-set guard.
- V3-B red state (committed tests, not dispatched): 36 failed, 1225 passed, 10 skipped.

### Review findings and how they were resolved

- **V3-A (code-review high + manual):** the per-action Responsibility form had no submit button or `hx-trigger`, so Responsibility could not be saved from the UI. Fixed by Codex (`hx-trigger="change"`) with a regression test; the guard allowance for the new test file was added by Claude. Noted, not fixed: routes re-query rows the service already loads; `_toast` helper duplicated; reviewer-name prefill reads only board-asks events; initiative metadata not reconciled when a roadmap group disappears (V3-B must ignore unknown group ids); `firm_logo_path` is unvalidated (V3-B must confine it).
- **P6-10a:** non-integer `expected_version` returned HTTP 500. Fixed in the 10b run with a regression test.
- **P6-10b:** the framework-conditional copy filter (spec D-P6-10-H rule 7) was skipped for the executive and cross-framework sections. Fixed by Codex with regression tests. Design note, not fixed: the specified measured-value filter lets counts, dates and timelines through; the consultant reviews every sentence.
- **Designer omissions fixed by Claude:** two guards (`test_p6_4_cap_upload_limit`, `test_p6_nist_csf2_alignment`) and the P6-2b guard needed P6-10 allowances; `test_p6_9_prior_period` needed one integer (prior sidecar is built by the live builder, now v3). Codex also wrongly marked P6-10 done in `tasks/todo.md`; reverted.
- Not verified: V3-A page in a real browser (the preview server is bound to the primary checkout, which is on `main`); no live LLM smoke for P6-10 (needs Saqlain's OK to spend).

### Codex run logs

- V3-A: `/Users/saqlainmomin/cyberassess-v3a-codex.log`; V3-A review fix: `/Users/saqlainmomin/cyberassess-v3a-fix-codex.log`
- P6-10a: `/Users/saqlainmomin/cyberassess-p610a-codex.log`
- P6-10b: `/Users/saqlainmomin/cyberassess-p610b-codex.log`; P6-10b review fix: `/Users/saqlainmomin/cyberassess-p610b-fix-codex.log`
- All with `gpt-5.6-luna` at `xhigh`; no quota errors.

### V3-B dispatch trigger

Dispatch V3-B only **after the P6-10 PR and #94 (V3-A) are merged**. Before dispatching: branch from the `main` that has both; add `python-pptx` (pinned) to `requirements.txt` and install it in the shared `.venv` (Saqlain approved this on 2026-10-01; Codex cannot install packages); merge `claude/p6-8-v3b-deck` (handoff + red tests) forward; expect a keep-both merge in `tests/test_p6_2b_dpdpa_criteria.py`. V3-B tests were proven only for the pure derivations and XLSX; expect a few test bugs in the HTML selector, `build_document`, route and PDF tests when Codex first runs them. Accepted defaults: observations include all approved findings; framework narrative under each framework's bar on the executive-summary slide; cross-framework narrative on the risk-dashboard slide.

### Decisions by Saqlain this session

- **P6-7b:** "Done, fix todo (Recommended)". `tasks/todo.md` now says P6-7b shipped as #84 on v2 cards only (D-P6-7b-J). Nothing more to build.
- V3-A fields live on one board-inputs page (`/assessments/{id}/board-inputs`); keep both `firm_primary_hex` and the new `firm_color_*` settings; add and install python-pptx before V3-B; accept the three V3-B layout defaults.
- Saqlain pushed V3-A's last commit and the P6-10 branch and opened #94 and #95 himself because push and `gh pr create` were denied to Claude.

### Review items for Saqlain (V3-A)

- `app/services/retention.py`: `initiative_metadata` purge scope and `PURGE_ORDER` position (destructive path).
- `app/assets/fonts/noto/OFL-BarlowCondensed.txt` was reconstructed from Noto's OFL text under Barlow's copyright line; compare with upstream before release. The Barlow TTFs came from an earlier scratchpad (no network for Codex) and are pinned by SHA-256.

### App-design kickoff

`tasks/handoffs/2026-10-01-app-design-kickoff.md` (inventory of pages and flows, the deck's visual system, eight open questions). `tasks/todo.md` records the order: Track 2 done, then app design, then Track 4. Saqlain may start design in a separate session now; template implementation should wait for #94 and the P6-10 PR to merge.
