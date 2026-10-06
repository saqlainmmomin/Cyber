# Yozora S8 group A: Requests page, RFI page, request links

**Status: IMPLEMENTED; visual gate blocked by the local sandbox.** **Worktree:** `../cyberassess-yozora-s8-a`, branch `codex/yozora-s8-requests` (off `codex/yozora-s8` after the scaffold). One of three parallel Codex builds; B (versions) and C (client) run beside you.

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

### What was built

- Added `GET /engagements/{engagement_id}/requests` with the engagement Evidence > Requests navigation, per-assessment RFI summary rows, and request cards for manual and RFI-scoped client links.
- Rebuilt the consultant request-card, RFI item/version, and RFI client-link surfaces while preserving the existing `id`, `hx-*`, and `data-*` interaction contracts. New-link, revoke, issue, and withdraw flows use toast headers; the existing issue/withdraw endpoints already supplied their headers.
- Removed magic-link and AWS evidence panels from Overview, kept retention and `data-assessment-identity`, and re-pointed Evidence inventory's Requests and Ask the client links to the Requests view.
- Added real-template S8 preview registration and deterministic Requests/RFI fixture seeds. Fixture tokens are fixed digests and are never exposed as usable client capability tokens. No new CSS was needed; the existing `.req*`/`.mk` pattern blocks were reused.

### Preview state gate

The required command was attempted with `OPENROUTER_KEY="" .venv/bin/python design/harness/gate_s8.py ...`. It stopped before seeding/capture at `_free_port()` with `PermissionError: [Errno 1] Operation not permitted`; this environment denies localhost socket binding. Therefore no screenshot percentage exists (`n/a`), and every state is recorded as the same infrastructure exception rather than treated as a visual pass.

| screen | state | themes / widths | diff | verdict |
|---|---|---|---:|---|
| b6-magic_links | default | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-magic_links | empty | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-magic_links | error | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-magic_links | loading | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-magic_links | newlink | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-magic_links | revoke | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-rfi | default | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-rfi | error | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-rfi | issue | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-rfi | loading | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-rfi | noscope | light/dark, 1440/1024 | n/a | blocked before capture |
| b6-rfi | versions | light/dark, 1440/1024 | n/a | blocked before capture |

### Exceptions

- Visual gate: one environment exception applies to all 12 states: localhost socket binding is denied before either the mockup server or app server can start. Evidence: the command exited with the traceback ending at `design/harness/gate_s8.py:48`, `sock.bind(("127.0.0.1", 0))`.
- Required AWS and retention controls remain available at their dedicated routes, but the Overview links were intentionally removed by the S8 decision. Existing assertions were moved to the Requests route or changed to assert absence.
- The live RFI page displays the actual seeded/generated RFI data, so copy/count differences from static mockup text are data-driven rather than hard-coded. The route/seed checks passed for all states.

### Tests changed: old → new

- `tests/test_magic_links.py`: Overview magic-link assertions → `/engagements/{id}/requests`; legacy “0 of 20 uploads” → card “0 of 2 received”; uploaded evidence is asserted on the Requests page. Added card ownership and toast-header contracts.
- `tests/test_aws_evidence.py`: Overview AWS href present → absent, matching the accepted S8 removal decision.
- `tests/test_longitudinal_demo.py`: client-upload labels on the assessment Overview → the engagement Requests page; added S8 guard allowance.
- `tests/test_yozora_magic_link_contacts.py`: contact rendering on Overview → Requests.
- `tests/test_yozora_s4.py`: AWS and magic-link controls on Overview → AWS absent, Evidence remains, and the link form is asserted on Requests.
- `tests/test_yozora_s5.py`: Overview client-link/AWS copy → absence on Overview plus a live Requests-page check.
- Existing RFI assertions were preserved; the RFI template adds the missing `data-rfi-scope-required`, received-evidence links, and evidence-request note markup required by the contracts.

### Guards touched

Added the new Requests/RFI files and affected downstream contract tests to `YOZORA_S8_PATHS`, then made add-only S8 allowances in the stale P6-7/P6-7b/P6-8/P6-9/P6-10/V3-A/retention/longitudinal guards. No guard was deleted or weakened; no models, migrations, scoring, analyzer, prompts, v2 flag, or PDF code was changed.

### Decisions and open questions

- Kept free-text requested items and the exact `/assessments/{id}/rfi` Prepare RFI target.
- Kept all consultant link mutations as HTMX partial responses and used response headers for toasts only.
- No open implementation questions. The only handoff item is environmental: rerun the S8 visual gate in an environment that permits localhost socket binding and Chromium capture.

### Verification

- Focused Requests/RFI regressions: `65 passed` (`test_magic_links`, `test_p5_6_rfi_rebuild`, `test_p6_7b_add_to_rfi`).
- Design lint plus preview route/registry checks: `8 passed`.
- Full suite: `1529 passed, 30 skipped in 197.82s (0:03:17)`.
