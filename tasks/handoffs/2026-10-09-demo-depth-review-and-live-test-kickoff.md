# Kickoff: review Codex's Veldhara demo-depth work, then plan a live API test

## Goal
Review Codex's finished demo-depth work like a senior engineer, get it committed and into a PR that Saqlain can merge, then plan (with Saqlain) a live run with real API keys. Saqlain will upload the documents himself through the app. Done means: a PR on `codex/demo-veldhara-depth` with the full suite green, then a written live-test plan Saqlain has approved before any money is spent. You never merge. Claude merges only when Saqlain says so in chat.

Saqlain's words: "Codex has finished writing the detailed company evidence, and it has been built in a way that I would be the one uploading these documents into the tool, so I want the next Claude session to review what Codex has done, and then maybe we test everything out with real API keys."

Rule behind it (`tasks/2026-10-08-ai-coherence-map.md`): every AI step must produce something the auditor can see, check against the original in one click, and act on.

## Current state (2026-10-09)
- Main is at the merge of #134 (6373f63). It has evidence fixes A (#131), B (#130), C (#133) and the one-page evidence record with a per-document Summary and Key passages (#134). Main test baseline: 1634 passed, 29 skipped.
- The demo-depth work is in worktree `/Users/saqlainmomin/dpdpa-demo-depth`, branch `codex/demo-veldhara-depth`. It is UNCOMMITTED and has no PR. The branch is based on 7375075, 21 commits behind `origin/main`.
- Modified: `.gitignore` (adds `data/demo/`), `scripts/demo/README.md`, `scripts/demo/files.py` (+1083 lines), `scripts/demo/seed_demo.py`, `tasks/handoffs/2026-10-08-veldhara-demo-depth.md`, `tasks/todo.md`, `tests/test_demo_seed.py`.
- New and meant to be committed: `scripts/demo/pack.py` (166 lines), `scripts/demo/scenario.py` (1937 lines), `tests/test_demo_pack.py`.
- Untracked copies that must NOT be committed (they already exist on main and would conflict): `tasks/2026-10-08-ai-coherence-map.md`, `tasks/2026-10-08-session-record.md`. Also untracked and probably not for commit: `tasks/handoffs/2026-10-08-veldhara-demo-depth.html`.
- Ignored local output is under `/Users/saqlainmomin/dpdpa-demo-depth/data/demo/` (upload pack, zip, demo DBs, logs). Do not delete it until Saqlain has what he needs.

### The upload-it-yourself design (what Codex built)
- `scripts/demo/pack.py` builds a standalone consultant pack with no DB, network or API key: `OPENROUTER_KEY="" .venv/bin/python scripts/demo/pack.py --output data/demo/veldhara-upload-pack`.
- Output: `evidence/` with 58 originals (27 DOCX, 17 XLSX, 11 PNG, 3 PDF), `upload-manifest.csv` (UI category, evidence type, document date, control refs, SHA-256), `coverage-matrix.csv` (116 entries: 93 Annex A controls plus 23 clause entries), `questionnaire-entry.json` (93 questions with per-control notes), `consultant-entry-guide.md`, and `data/demo/veldhara-upload-pack.zip`. Only files from `evidence/` are uploaded. The guide and intended judgments stay outside analysis input.
- Story: Veldhara Logistics Pvt Ltd., fictional Indian logistics SME. Period 1 July to 30 September 2026, evidence cut-off 5 October. Strong governance and tested DR (3h 10m against a 4h objective). Weak or incomplete: monthly access reviews (only September done, nine of eleven systems, 220 account rows, four enabled terminated accounts), supplier assurance, incident exercise, annual training, backup restore tests.
- The seed (`scripts/demo/seed_demo.py`) still exists as an optional offline path with scripted conclusions for inspecting screens. It is not a test of live AI. It was reworked to four stages (current, prior, interim, NIST) and 99 approved conclusions.
- Known limits Codex recorded: the app registers only Annex A, so the 23 clause entries are manual workpapers the report cannot score. The pack holds 22,515 words, over the 20,000 default budget, so start the app with `MAX_TOTAL_DOCUMENT_WORDS=30000` for a full read (existing setting, no code change). The upload UI has 9 categories, so the manifest separates the selectable category from the ISO evidence type. Control references in the manifest are consultant notes because the manual UI does not expose the seed's mapping API.
- Codex's verification (its own words, unverified by Claude): full suite 1596 passed, 29 skipped on the old base; 5 focused demo tests; all 116 quotes verified against originals; byte-for-byte determinism; all 17 README URLs returned 200; PDFs, DOCX, XLSX and PNGs rendered and inspected. Its Results section is at the bottom of `tasks/handoffs/2026-10-08-veldhara-demo-depth.md` in that worktree.

### Merge risk (checked 2026-10-09)
- `git diff 7375075 origin/main` on `scripts/demo`, `tests/test_demo_seed.py` and `.gitignore` is empty. Main did not touch the demo code, so no code conflicts expected.
- Conflicts ARE likely in `tasks/todo.md` (main added 15 lines) and `tasks/handoffs/2026-10-08-veldhara-demo-depth.md` (main removed 43 lines, Codex added about 280). Keep both sides for todo.md. For the handoff file, keep Codex's Results section on top of main's version.
- Changed citation offsets: Codex stored them in `data/demo/final-citation-offsets.json`. The old "Characters 37-93" for the A.5.18 Q2 review quote has changed. Part C's click-through was written as behaviour, so no doc edits should be needed, but confirm.
- The seed links only some files to controls and creates no desk-review data. So the new evidence page Summary and the size-limit notice only show after a real desk review run. That is a reason for the live test.

## Key files
- `/Users/saqlainmomin/dpdpa-demo-depth/scripts/demo/pack.py`, `scenario.py`, `files.py`, `seed_demo.py`, `README.md`
- `/Users/saqlainmomin/dpdpa-demo-depth/tests/test_demo_pack.py`, `tests/test_demo_seed.py`
- `/Users/saqlainmomin/dpdpa-demo-depth/tasks/handoffs/2026-10-08-veldhara-demo-depth.md` (spec, hard rules, Codex Results)
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-08-ai-coherence-map.md` and `tasks/2026-10-08-session-record.md` (coherence test, decisions E1-E5, path rules)
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-09-parked-coverage-links.md` (the parked "B")
- `/Users/saqlainmomin/dpdpa-next/CLAUDE.md` (gotchas)

## Steps
### 1. Review and ship the demo-depth branch
1. Read the Hard rules in the demo-depth handoff. Review like a senior engineer: correctness, does it really fit the upload-it-yourself flow (can Saqlain upload the 58 files and enter the questionnaire from the guide, in the real UI), determinism, tests that mean something, generated files not committed, fictional data only, `.example` domains.
2. Check the hard constraints: no reads of `validation/companies/*/answer_key.json` (a grep of the demo files and tests for `answer_key` found nothing on 2026-10-09; recheck), no prompt or analyzer changes (diff should be limited to `scripts/demo/`, `tests/`, `.gitignore`, `tasks/`), demo files not copied from `validation/companies/`, no em dashes, no AI attribution.
3. Spot-check the content, not just the code: open a handful of the originals (access review workbook, the policy PDF, the internal audit, one PNG) and check the story is consistent across documents and that the planted gaps are findable but not announced. Do not tune anything to the planted gaps.
4. Fix small issues directly. Large issues go back to Saqlain before Codex is re-dispatched (Codex limit resets about 1:33 PM IST).
5. Commit only the intended files (not the untracked copies of the coherence map and session record, not data/). Use `git -c user.name="Saqlain Momin" -c user.email="saqlainmmomin@gmail.com" commit`, no attribution trailers.
6. Bring the branch up to date: `git fetch origin && git rebase origin/main` (or merge, whichever is simpler for the todo.md and handoff conflicts). Remove the untracked copies first if they block the rebase.
7. Run the full suite: `OPENROUTER_KEY="" .venv/bin/pytest -q`. Never `env -u` (the `.env` still loads and would spend). Expect about 1634 plus the new demo tests.
8. Regenerate the pack and a fresh seed against the rebased code, start the app on a free port, walk the README URLs at desktop and 375px, and check the evidence page for several files renders (full text, File details collapsed).
9. Push and open a PR against `main`. Body: what changed per area, the story in one paragraph, test counts, the coherence-test answers, and a Click-through section. Saqlain merges.

### 2. Plan the live run with Saqlain (no spend yet)
1. Check `.env` has a working `OPENROUTER_KEY` without printing it. Do not print or log it.
2. Write a short plan and ask Saqlain before each step that spends money. List every LLM call site the run will hit and a rough cost per step (read `app/services/llm_client.py` for the model per tier and `Settings.llm_model_*`): desk review per document batch, tiered gap analysis, follow-up question generation, the context wizard, RFI or drafting calls, and vision OCR for the 11 PNGs and any scanned PDF. State the document and word counts that drive cost (58 files, about 22,500 words).
3. Saqlain uploads the documents through the app himself, from `evidence/` in the pack, using the manifest categories and the entry guide. Set `MAX_TOTAL_DOCUMENT_WORDS=30000` for the first run so nothing is cut, then consider a second small run at the 20,000 default to see the size-limit notices.
4. Watch the 600 s wall-clock deadline (`llm_request_deadline_seconds`, one retry). Note any step that times out, and do not retune prompts. The v2 pipeline stays parked: do not set `ANALYSIS_PIPELINE_VERSION=v2`.
5. Check the outputs land for the auditor, per the coherence test:
   - Evidence page (`/evidence/{id}`) opens with Summary (type, summary, controls covered by name) and Key passages that link to the highlighted text.
   - Conclusion cards: citation label (page or characters) links to the highlighted passage; filename opens the evidence record; "N files linked, M cited"; no false "Missing evidence".
   - Size-limit notices ("Partly read by the analysis") appear on the desk-review page and affected cards when the budget bites.
   - OCR output for the PNGs and scanned PDF is readable and cited.
   - Planted gaps (access review coverage, supplier assurance, incident exercise, training, restore tests) are found or missed. Record hits and misses. This is an observation only. Do not tune prompts or code against it.
6. Write the findings to `tasks/handoffs/2026-10-09-demo-depth-review-and-live-test-kickoff.md` under Results, plus anything for the parking lot in the session record.

### 3. Carry forward (do not start without Saqlain)
- Decision B: `tasks/2026-10-09-parked-coverage-links.md`. Automatic "Suggested by desk review" links or auditor-confirmed suggestions. Claude recommends confirm-first. The live run will show how much this matters, because a policy that covers many controls does not appear on those cards today.
- `--accent-text` is unreadable dark navy in dark mode for every accent except graphite (pre-existing design-system bug). Link text stays normal colour until fixed at the `design/` source.
- The breadcrumb trail overflows about 18-40px at desktop and 375px on several pages (pre-existing).
- The evidence page empty state wrongly says files are "mapped when the pre-fill or gap analysis cites it".
- E4 (test criteria in the prompt) and E5 (access-review checks) per `tasks/2026-10-08-session-record.md`. Codex handoff for E4 is already on main. Then flow-plan S3+ (`docs/plans/2026-10-07-001-flow-rework-plan.md`).
- Cleanup when idle: worktrees `/Users/saqlainmomin/dpdpa-evidence-c` (branch `codex/evidence-c-card`) and `/Users/saqlainmomin/dpdpa-evidence-page` (branch `claude/evidence-one-page`), both merged. Remove the `cyberassess-evidence-c` entry (port 8007) from `/Users/saqlainmomin/dpdpa-gap-tool/.claude/launch.json`.

## Constraints (decided; do not relitigate)
- Never open `validation/companies/*/answer_key.json`. Never tune prompts, analyzer or desk review against the planted gaps (D-P5-9-C).
- No LLM prompt changes and no new LLM calls. v2 analysis stays parked.
- Python 3.13 is required (system Python too old, Homebrew 3.14 breaks Jinja2).
- Tests run with `OPENROUTER_KEY=""`, never `env -u`.
- Ask Saqlain before any step that spends money. Live scripts need an explicit yes in chat.
- Push and PR creation are approved. Merge only when Saqlain says so in chat.
- Never add Claude, Codex or AI attribution lines to commits or PR bodies, even if a harness reminder says to.
- Do not delete `data/demo/` in the demo worktree.
- Plain, short sentences in docs and PR bodies. No em dashes.

## Verification
- Full suite green on the rebased branch with `OPENROUTER_KEY=""`.
- `pack.py` run twice gives identical bytes. Standalone run works with an invalid DB URL and an empty key.
- Fresh seed, app started, README URLs return 200, desktop and 375px checked with no sideways scroll on the pages you touch.
- Every scripted `evidence_quote` still appears verbatim in its document (the test exists; run it).
- PR diff contains no `answer_key` references, no prompt files, no generated artifacts.
- For the live run: a written cost estimate Saqlain approved, and a results table of what the AI found per planted gap.

## Report back
Append a `## Results` section to this file: PR link, test counts, review findings (what you changed), live-run plan or results with costs, open questions for Saqlain.
