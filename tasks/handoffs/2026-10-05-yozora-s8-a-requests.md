# Yozora S8 group A: Requests page, RFI page, request links

**Status: NOT DISPATCHED.** **Worktree:** `../cyberassess-yozora-s8-a`, branch `codex/yozora-s8-requests` (off `codex/yozora-s8` after the scaffold). One of three parallel Codex builds; B (versions) and C (client) run beside you.

## Goal
Build the engagement Requests view and the RFI page, and take request links out of the Overview. Client links render as request cards (requested items, "N of M received", expiry, per-item checklist, contact name and email when set) using the `.req*` and `.mk` components.

## You own
`app/templates/pages/requests.html` (new), `partials/magic_links.html`, `partials/rfi_links.html`, `pages/rfi.html`; in `app/routers/magic.py` only the consultant side (`_consultant_context`, `_render_consultant`, `create_magic_link`, `revoke_magic_link`, `create_rfi_magic_link`, and the new `GET /engagements/{engagement_id}/requests`); `rfi_page` in `web.py`. One-line edits allowed outside your files: the Requests seg item and "Ask the client" href in `pages/evidence_inventory.html` (re-point to the new page); remove the magic-links include from `pages/assessment.html` (the `data-visual-mask` block) and from `engagement_detail.html`'s `engagement_records` macro; remove the Overview `data-aws-evidence-link` (decision 4, accepted). Keep `data-assessment-identity` and the retention block. Do **not** touch `magic/upload.html`, `magic/invalid.html` or the client side of `magic.py` (group C).

## Mockups and states
`b6-magic_links`: default, empty, error, loading, newlink (shown once at creation), revoke. `b6-rfi`: default, error, issue, loading, noscope, versions. Requests page: seg row Inventory / Requests, a "Requests by assessment" table linking to each RFI page, then the request cards (counts from `app/services/request_summary.py`). RFI: only its own seg (Items, Versions, Client links); breadcrumb leads back to Evidence and Requests. Scope's "Prepare RFI" link keeps its target (`/assessments/{id}/rfi`, decision 5). Free-text requested items stay (decision 6): keep the `requested-items` input, no tick-box picker.

## Group specifics
- `_render_consultant` still returns the partial after create and revoke, now into the Requests page's `#magic-links`; keep `hx-target`/`hx-swap` exactly.
- The RFI page is the most heavily asserted page in the app (`tests/test_p5_6_rfi_rebuild.py`, `test_p6_7b_add_to_rfi.py`, `test_magic_links.py`): run them after every template change.
- Check `?tab=` links and the Scope link still resolve after the Overview edits.
- Toasts: assert `X-Toast-Type` and a non-empty `X-Toast-Message` on new-link, revoke, issue, withdraw; no pixel compare.
- Token never in a URL other than the existing path, a mailto or a log line; fixtures use a fixed fake token.

## Read first
1. `tasks/handoffs/2026-10-05-yozora-s8-codex-orchestration.md` (phases, S7 lessons, constraints) and `tasks/handoffs/2026-10-05-yozora-s8-orchestration.md` (decisions 1 to 12 and collision rules; they override the slice brief).
2. `tasks/handoffs/2026-10-01-yozora-s8-handoff.md`: use only the rows, must-keep list, build notes and asserted strings for your templates below.
3. `docs/product/yozora-design-system.md`, `docs/product/yozora-fidelity-gate.md`, `docs/product/2026-10-01-app-design-mockups/screens/NEEDS-b6.md`, and your mockups in `docs/product/2026-10-01-app-design-mockups/screens/`.
4. Sibling conventions: S5/S6/S7 pages, `design/harness/seed_s7.py`, `design/harness/gate_s8.py` (from the scaffold), `tests/test_yozora_s7_*.py`.

## Rules that bite
Keep every must-keep id, `hx-*`, `data-*`. One visible `.btn.primary` per state, never a disabled primary. Sentence case, no uppercase, no hex or arbitrary Tailwind values (`tests/test_design_lint.py`). Framework names only where in scope. Keep the temporary `reviewer-name` input. New CSS: append a delimited block for your group to `design/yozora-patterns.css`, then `python design/tokens_tool.py build` (both files must stay identical). Do not edit files owned by another group, `layout.html` tab macros, or any other slice seed. Stale guards get add-only allowances (`tests/yozora_paths.py`, `YOZORA_S8_PATHS`); never delete or weaken a guard. Never touch scoring, analyzer, prompts, v2 flag, PDF code, models or migrations (stop and ask). Never read `validation/companies/*/answer_key.json`. No attribution lines in commits. Commit in logical steps; do not push or merge.

## How to work and gate
Seed your states in `design/harness/seed_s8_<group>.py` (`SCREEN_STATES`, `apply`, `route`; list how each non-database state is produced). Gate only your screens: `OPENROUTER_KEY="" .venv/bin/python design/harness/gate_s8.py <screen>[:state] [--content] --out <dir>`; threshold 0.4% and no changed region over 40x40. Run screens in parallel with separate `--out` dirs. **Record misses as exceptions as you go** (cause + evidence) when they are required controls the mockup omits, copy a test pins, shared shell, or real data vs mockup text; fix the rest. Never pad, hard-code mockup copy or loosen a threshold. Tests that pin Tailwind classes are rewritten to assert `data-*` or visible text; list every changed assertion (old, new, reason).

## Done when
Every state of your mockups passes or is a recorded exception, light and dark at 1440 and 1024; your tests and `tests/test_design_lint.py` pass; the full suite passes in your worktree; Results below is filled in.

## Stop and ask
Write the question in Results and stop if: a visual detail is in neither the guide nor the mockup; two mockups disagree; a must-keep cannot be kept; a mockup shows an action with no route and the brief does not cover it; the work needs a model, migration, prompt, scoring or PDF change.

## Results
(Codex fills in: what was built, per-state gate table with percentages, exceptions with causes, tests changed old to new, guards touched, decisions, open questions, full-suite summary line.)

