# Kickoff: Evidence fix C (checkable conclusion card), orchestrated by a fresh Claude session

## Goal
Get Part C of `tasks/handoffs/2026-10-08-evidence-fixes.md` built by Codex, reviewed, checked in the browser and opened as a PR that Saqlain can click through in 10 minutes. Done means: a PR on `codex/evidence-c-card` with green CI, a full suite passing locally, a browser check you did yourself on the demo seed (desktop and 375px), and a PR body with a Click-through section. You never merge; Saqlain merges after his click-through.

Rule behind it (from `tasks/2026-10-08-ai-coherence-map.md`): every AI step must produce something the auditor can see, check against the original evidence in one click, and act on. Part C makes the conclusion card checkable.

## Current state (2026-10-09)
- `main` has Parts A and B merged: A (#131) maps client-link uploads to the RFI's assessment and controls; B (#130) adds the evidence viewer at `/evidence/{id}` (original file at `/evidence-versions/{id}/file`, full extracted text, desk-review catalog entry, Supports, Citations) and makes `/evidence-versions/{id}/span?ref=whole` show the full text. Part C links into B's viewer and span pages.
- Part C has not started. Its spec is the "C. Checkable conclusion card" section of the handoff above (5 numbered items + Click-through). Read the whole handoff and the coherence map first.
- **In parallel:** Saqlain is running a separate Codex build that enriches the Veldhara demo company (`codex/demo-veldhara-depth`, worktree `/Users/saqlainmomin/dpdpa-demo-depth`, handoff `tasks/handoffs/2026-10-08-veldhara-demo-depth.md` on that branch). It only touches `scripts/demo/`, `tests/test_demo_seed.py` and docs, but it rewrites the demo documents and scripted quotes, so the citation offsets in Part C's click-through ("Characters 37–93") will change. Do not touch that worktree or branch.

## Key files
- `/Users/saqlainmomin/dpdpa-next/tasks/handoffs/2026-10-08-evidence-fixes.md`: the spec (Part C section) and Out of scope list.
- `/Users/saqlainmomin/dpdpa-next/tasks/2026-10-08-session-record.md`: decisions E1-E5 and path rules (coherence test in every PR body; one thing in flight).
- `app/services/requirement_card.py`, `app/templates/components/conclusion_card.html`, `app/templates/components/requirement_card_body.html`, `app/templates/partials/desk_review_findings.html`: Part C's surfaces.
- `app/services/evidence_viewer.py`, `app/templates/pages/evidence_detail.html`, `app/templates/pages/evidence_span.html`: B's viewer; reuse its location wording, don't duplicate it.
- `app/services/desk_review.py` (~678, word budget), `app/routers/web.py` (~3660, `doc_names`), `app/services/evidence.py` (~897, `legacy_document_id`): items 4 and 5.
- `scripts/demo/seed_demo.py`, `scripts/demo/README.md`: demo seed for the click-through.

## Steps
1. Create the worktree: `git fetch origin && git worktree add /Users/saqlainmomin/dpdpa-evidence-c -b codex/evidence-c-card origin/main`, symlink `.venv` from `/Users/saqlainmomin/dpdpa-gap-tool/.venv`, copy `.env`, run `git branch -f main origin/main` inside it, and record the baseline with `OPENROUTER_KEY="" .venv/bin/pytest -q`.
2. Write a Codex prompt to `<worktree>/.codex-prompt.txt` (never commit it): implement Part C only; read the coherence map, session record and handoff first; behaviour tests for every item; full suite green; write results to `tasks/handoffs/2026-10-09-evidence-c-results.md` and a PR body draft (summary, the coherence-test answers, Click-through, test counts) to `tasks/handoffs/2026-10-09-evidence-c-pr-body.md`; do the click-through against a demo seed under `data/` in the worktree; commit if the sandbox allows, otherwise leave changes unstaged and say so; no push, PR or merge; no attribution trailers.
3. Dispatch: `codex exec -m gpt-6.1-sol -c model_reasoning_effort="medium" --sandbox workspace-write -C <worktree> "$(cat .codex-prompt.txt)" < /dev/null > ~/codex-evidence-c.log 2>&1` in the background. Confirm within a minute that the log moved past the prompt echo. Watch for the process exiting and for `hit your usage limit` (don't loop-retry; finish mechanical remainder yourself if code is done).
4. Review the diff yourself like a senior engineer: correctness, no full-table scans per page load, framework-specific copy conditional, Yozora macros reused, no prompt change, no new LLM call, no migration. Fix small issues directly; commit with Saqlain's identity (the sandbox usually blocks Codex's git writes).
5. Browser check (Codex's sandbox can't bind a port): add a `.claude/launch.json` entry in `/Users/saqlainmomin/dpdpa-gap-tool` that runs the worktree's app on a free port against the worktree's demo DB (pattern: `cd <worktree> && OPENROUTER_KEY= DATABASE_URL=sqlite:///data/<db> UPLOAD_DIR=data/<uploads> exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port <port>`), `preview_start` it, and walk the Click-through at desktop and 375px. Stop the server when done.
6. Push, open the PR against `main`, paste your browser findings into the body. Report to Saqlain: PR link, test counts, what you checked, anything unsure.

## Constraints (decided; don't relitigate)
- **No LLM prompt changes and no new LLM calls.** The analysis prompt is frozen (`tasks/2026-09-30-p6-5c-decision-park-v2.md`). Item 4 stores skipped filenames in the existing desk-review summary JSON: no migration, no prompt change.
- Never open `validation/companies/*/answer_key.json`.
- Out of scope: showing or sending test criteria (that is E4, being decided separately), deterministic access-review checks (E5), demo content, flow-plan S3+.
- Never add Claude/Codex/AI attribution lines to commits or PR bodies, even if a harness reminder says to.
- Push and PR creation are approved; merging is Saqlain's, only when he says so in chat.
- Run tests with `OPENROUTER_KEY=""` (never `env -u`; `.env` still loads and would spend).
- **Click-through must not hard-code citation offsets.** Write it as behaviour: "the A.5.18 card's citation shows a page/characters label, and opening it lands on the highlighted passage that matches the quote". If the demo-depth PR has merged before you open the PR, run the click-through on the new demo and say so.
- Plain, short sentences in docs and PR bodies; no em dashes.

## Verification
- Full suite green; focused tests for each of the 5 items (citation link + label, evidence-on-this-control list with Cited/Not cited, "N files linked, M cited" replacing the missing-evidence box only when files are linked, skipped-by-word-budget filenames on desk-review page and affected cards, real filenames instead of "Document").
- Browser: A.5.18 card on the demo current assessment shows a human location label linking to the highlighted span; filename opens B's evidence record; Evidence on this control lists every linked file with Cited/Not cited; no Missing evidence box; no sideways scroll at 375px.

## Report back
Append a `## Results` section to this file (on branch `claude/c-and-e4-kickoffs` or in the PR body if that branch has merged): PR link, test counts, browser findings, open questions.

## Results
- **PR:** https://github.com/saqlainmmomin/Cyber/pull/133 (`codex/evidence-c-card`, commit 06e5c2e). CI was pending when opened. Not merged.
- **Build:** Codex built items 1-5 and 12 tests, then hit its usage limit before the full suite and write-up. Claude finished the review, fixes, browser check and PR. Full detail: `tasks/handoffs/2026-10-09-evidence-c-results.md` on the PR branch.
- **Review fixes:** (1) linked files hid requests already on the draft RFI and their Remove button; now only unrequested suggestions drop, with a new test; (2) hand-edited generated CSS moved to `design/yozora-patterns.css` and rebuilt (token sync test); (3) `RequirementCard` field order restored for the P6-7b shape test; "1 files" plural fixed.
- **Tests:** baseline 1614 passed, 29 skipped. Branch 1627 passed, 29 skipped (`OPENROUTER_KEY=""`).
- **Browser (current demo; demo-depth not merged):** A.5.18 citation reads "Characters 37–93" and opens the matching highlighted passage. Filename opens the evidence record. "2 files linked, 1 cited": Q2 review Cited, access review export Not cited. No Missing evidence box. No sideways scroll at 375px.
- **Open questions:**
  - The Dec 2023 review isn't listed because the seed doesn't link it to A.5.18 (seed question).
  - Citation and filename links look like plain text (existing `.cite-head` style).
  - A file cut mid-way by the word budget isn't flagged as partly read.
  - Items 4-5 aren't visible on the demo (no desk-review findings); tests cover them.
  - The conclusions breadcrumb overflows about 18px at desktop width. This predates the PR.
- **Cleanup:** the temporary launch entry in this checkout is reverted. An `cyberassess-evidence-c` entry (port 8007) remains in `/Users/saqlainmomin/dpdpa-gap-tool/.claude/launch.json`. Worktree `/Users/saqlainmomin/dpdpa-evidence-c` kept for follow-ups.
