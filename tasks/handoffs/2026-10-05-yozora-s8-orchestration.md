# Yozora: scope and dispatch S8, review it

**Status: NOT DISPATCHED (5 Oct 2026). Waits on S6 (#110) and S7 merging.** **For:** a cloud thread in the Yozora project. **Repo:** `saqlainmmomin/Cyber`. **Merging is Saqlain's.** The builder never merges or enables auto-merge.

## Goal
Build S8 (Requests view, RFI page, report versions, statement of applicability, comparison, and the three client-facing pages) from `tasks/handoffs/2026-10-01-yozora-s8-handoff.md`, review it against the gates, show Saqlain the pixel evidence, and hand back one ready PR. **Done when** the S8 PR is open with Results filled in, reviewed (12-point checklist in `2026-10-03-yozora-codex-orchestration.md`), screenshots shown (gate 4), and the open questions below answered or recorded.

**Out of scope:** S7 (analysis, review, report tab, narrative, board inputs), S9 (system states, toasts, dark and mobile pass), `GET /reports` (S4 built it).

## Who builds, who reviews
Same split as S7 (Saqlain, 5 Oct 2026): a **Sonnet 5.5** cloud thread builds S8 on a branch off `main`, using subagents for the visual fitting (not Codex); a separate **Opus** (`claude-opus-5-5`) cloud thread then does the adversarial review. Commits are authored as Saqlain Momin with no attribution trailers (check merge commits too).

## Read first
1. This file.
2. `tasks/handoffs/2026-10-01-yozora-s8-handoff.md` (the slice brief; its Results section is where the builder writes up).
3. `tasks/handoffs/2026-10-03-yozora-codex-orchestration.md` (standing procedure and the 12-point checklist), then the Results of the S3/S4, S5/S6 and S7 orchestration files. What those slices shipped wins over the brief where they differ.
4. `docs/product/yozora-fidelity-gate.md`, `docs/product/yozora-design-system.md`, `docs/product/2026-10-01-app-design-mockups/screens/NEEDS-b6.md`.

## Preconditions (check on `origin/main` before dispatching)
- S6 and S7 merged. S8 needs from S6 the Evidence inventory page and its seg row (`pages/evidence_inventory.html`), and from S7 the Report seg row (Report, Versions, Applicability, Narrative, Board inputs) and the `assessment_tabs` / `seg` calls. S8 uses those and does not rebuild them.
- Backend #99 is on `main` (`MagicLink.contact_name` / `contact_email`, `FirmSettings.contact_email`, `app/services/request_summary.py`, the comparison context's `current_report_url`). Verified: all present today.
- Record the baseline full suite on a clean `origin/main` after S6 and S7 land. `test_p6_8_board_report_v2::test_scenario_3` is flaky on `main` (about 2 in 8 runs); re-run it before blaming S8.

## Scoping decisions (made here; Saqlain can overrule)
These fix drift in the 3 Oct brief. Tell the builder they override it.

1. **Drop `/reports`.** S4 built `GET /reports`. Remove it from the brief's Goal, Definition of done, Build notes and Stop-and-ask lines. The menu entry is already live.
2. **Requests view lives under Evidence.** S6's inventory page builds the Evidence seg row with `Requests` pointing at the first assessment's `/assessments/{id}/rfi`. S8 adds `GET /engagements/{engagement_id}/requests` (`pages/requests.html`, view in `app/routers/magic.py`, counts from `request_summary.engagement_summaries`) and re-points that seg item and the "Ask the client" menu item in `pages/evidence_inventory.html` to it. That is a one-line edit in an S6 file; allowed. The page follows `b6-magic_links`: seg row Inventory / Requests, a "Requests by assessment" table linking to each RFI page, then the request cards.
3. **Remove the magic links from the assessment Overview.** S4 left `partials/magic_links.html` in `pages/assessment.html` (the `data-visual-mask` block) and in `engagement_detail.html`'s `engagement_records` macro, "until S8". S8 removes both includes. `_render_consultant` still returns the partial after create and revoke, now rendered into the Requests page's `#magic-links`.
4. **Overview AWS link.** The Overview keeps `data-aws-evidence-link` today. Recommendation: remove it from the Overview, since S6 put "Pull from AWS" in the Evidence menu. Keep the retention block. If Saqlain prefers to keep the link, leave it and record it.
5. **Scope's "Prepare RFI" link keeps its target.** S5's Results deferred a re-point to "the Evidence Requests view". The approved mockup (`b3-scope-complete`) links straight to `b6-rfi`, the one assessment's request, and the RFI page's breadcrumb leads back to Requests. So `data-rfi-link` stays `/assessments/{id}/rfi`. Mockup wins.
6. **Free-text requested items stay.** Decision 8 (3 Oct): no tick-box picker (`.req-pick`) in the new-link form. Build the cards and the checklist; keep the `requested-items` input.
7. **Statement of applicability saves in one action, no backend change.** Today each row posts alone to `POST /api/assessments/{id}/soa/justifications` (`requirement_id`, `justification`). The builder drives one "Save" button that posts only the changed rows one after another with the existing route, the same pattern as the evidence-reuse decision (5). It does not add a bulk route (that would be a backend change). Replace the brief's test line "SoA saves with one POST" with: one button, changed rows only, each row's success or error shown, `saving` and `saved` states. Keep `data-soa-justification-form`, `data-soa-row`, `data-applicability`.
8. **Client pages follow `b6-magic_invalid`.** Decision 11: `b7-link-expired` (different firm name, a named person, "14 days") is matched visually at 390 only; copy comes from the app (firm name from settings, expiry from the link, mailto only when `FirmSettings.contact_email` is set and never containing the token). `.touch` and `.dropzone` already exist in `design/yozora-components.css` and `yozora-patterns.css`; do not add new CSS for them.
9. **Report seg row on Versions, Applicability and Comparison.** Same five items in the same order as S7, Applicability only when ISO 27001 is in scope. Use S7's macro call exactly. Comparison breadcrumb: Report / Versions. Comparison keeps scores per framework, never combined.
10. **Seed.** `design/harness/seed_s8.py`: deterministic throwaway SQLite seed matching the mockups (Meridian Ledger Technologies, Loomwire Labs, Kestrel Advisory), frozen clock. Import the builders from `seed_s4.py` and do not edit it or any other slice's seed. Client pages use a fixed fake token; never put a real token in a baseline. List how each state was produced (loading, error and `uploading` through `PREVIEW_PAGES` fixtures or the mockup's own `?state=`).
11. **Toasts are not pixel-checked here** (S9). Test the `X-Toast-Type` and non-empty `X-Toast-Message` on the new-link, revoke, issue and withdraw responses; leave the pixel compare to S9.
12. **Tests that pin Tailwind classes** (`font-weight: 600`, `text-amber-700` and similar, listed in the brief) are rewritten to assert the `data-*` attribute or visible text. List every changed string in the PR (old, new, reason).

## Collision rules
| Shared piece | Rule |
|---|---|
| `pages/evidence_inventory.html` (S6) | Edit only the Requests seg item and the "Ask the client" menu href. |
| `pages/assessment.html`, `pages/engagement_detail.html` | Remove the magic-links include and (if Saqlain agrees) the AWS link, nothing else. Keep `data-assessment-identity` and the retention block. |
| Report seg row (S7) | Same macro call, items and order. |
| `app/routers/web.py`, `tests/yozora_paths.py`, file-set guards, `PREVIEW_PAGES` | Mechanical; keep both sides. Add `YOZORA_S8_PATHS` (add only; never delete or weaken a guard). |
| `layout.html` tab macros | Do not edit. |

## Dispatch
One Sonnet 5.5 cloud thread, branch `claude/yozora-s8` off `origin/main`. Prompt:

> Read tasks/handoffs/2026-10-01-yozora-s8-handoff.md and tasks/handoffs/2026-10-05-yozora-s8-orchestration.md (Scoping decisions and Collision rules override the brief where they differ) and build S8. Use subagents for the visual fitting, one per page group (Requests and RFI; versions, applicability and comparison; client pages), merge their work, then run the full suite and the pixel gate (`design/harness/screenshot.py --full-page`, mockups served with `/static/` mapped to `app/static/`, thresholds 0.4% and no changed region over 40x40, 390 for the client pages). Record failing states as real-data exceptions with the reason, as S5 and S6 did. Write your results to the Results section of the slice brief. Allowances for stale guards go in `tests/yozora_paths.py` (`YOZORA_S8_PATHS`). Commits authored as Saqlain Momin, no attribution trailers. Open a draft PR and message the channel session with its number so the Opus review thread can start.

## Review (Opus thread, all 12 checklist points; do not trust the builder's Results)
- Run the suite yourself and commit before the final run (three-dot guards only see commits).
- **Must-keep extraction diff** on every template in the brief's list. The RFI page is the most heavily asserted page in the app.
- **Round trips over HTTP:** create and revoke a link, RFI generate / issue / withdraw, add to RFI, snapshot issue, SoA save (changed rows only), client upload (item chosen, no file, over the item limit, duplicate file, total size), then `GET /magic/{token}` for expired, revoked and unknown tokens.
- **Privacy:** the token never appears in a mailto, a log line, a non-path URL or a baseline; the invalid page reveals no client or engagement name; the mailto appears only when the firm contact email is set; the greeting uses the first name only when present.
- **Magic links gone from the Overview** and `engagement_detail`; the Requests page renders the cards; `?tab=` links and the Scope link still resolve.
- **Adversarial pass:** unconditional framework copy (DPDPA, ISO 27001), numeric priorities, more than one visible primary per state, a disabled primary, a combined cross-framework score, anything invented, and any backend, model, prompt, scoring or PDF change.
- **Gate 4:** baseline, candidate and diff images with percentages for each screen and state go to Saqlain before the slice is called ready; list the exceptions separately.

## Hand Saqlain
The builder's PR (draft) and the Opus review verdict; then S9.

## Decisions from Saqlain (5 Oct 2026, do not reopen)
Saqlain accepted the recommended answer to all six questions below.

## Questions asked (recommended answer first, all accepted)
1. **Overview AWS link:** remove it, since Evidence has "Pull from AWS"? Recommend yes.
2. **Scope's "Prepare RFI" link:** keep going straight to the assessment's RFI page, as the approved mockup draws it, rather than the Requests list? Recommend yes.
3. **SoA one-click save:** post the changed rows one after another over the existing route, with no new bulk route? Recommend yes (a bulk route is a backend change).
4. **Request cards:** keep free-text requested items (decision 8) and show no tick-box picker, though `b6-magic_links` draws one? Recommend yes.
5. **Mockup copy gap:** `b7-link-expired` says "14 days" and names a person; the app has neither. Build to `b6-magic_invalid` with app-driven copy (decision 11). Recommend yes.
6. **Start order:** dispatch S8 only after both S6 and S7 have merged, as with S7. Recommend yes.

## Results
(Filled in by the orchestrating thread after the PR is open.)
