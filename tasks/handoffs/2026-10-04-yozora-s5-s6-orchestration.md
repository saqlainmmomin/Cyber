
## Results

**Status: both slice PRs open as drafts (4 Oct 2026).** S5 is the PR from `claude/finish-s5-s6-yyd2vz`; S6 is [#110](https://github.com/saqlainmmomin/Cyber/pull/110) from `claude/finish-s5-s6-yyd2vz-s6`. Merge S5 first, then merge `main` into S6 and re-run its suite and gate.

**What changed from this plan**
- Codex did rounds one to three on Saqlain's Mac. On 4 Oct Saqlain decided that subagents, not Codex, do the visual fitting. His session limit then stopped the Mac fitters, so the work moved to a cloud session from the round-three commits (`2ecefdd`, `c17c01d`); the Mac fitters' unpushed edits were lost and fitting restarted.
- In the cloud: ten fitter subagents (one per page group), a merge per slice, an adversarial review per slice, and a fix round per slice.
- Saqlain approved a new read-only page, `GET /assessments/{id}/desk-review` ("Pre-fill from documents", the b4 mockup), so the Questionnaire tab shows only the pre-fill summary as the b3 mockup does.
- Framework names follow the house labels from `framework_label()` ("DPDPA 2023", "ISO 27001:2022"), the same as S4, instead of registry names.
- Commits are authored as Saqlain, with no attribution trailers.

**Gate** (pixelmatch 0.1, fail above 0.4% or any changed region over 40x40, full page, light/dark at 1440/1024, mockups served with `/static/` mapped and the state switcher hidden):
- S5: 60 of 188 shots pass. Overview, pre-fill ready/running/error, screening complete, context complete and section saved pass everywhere.
- S6: 61 of 116 pass. Inventory (outside the filtered state) and AWS (outside not configured) pass everywhere.
- Most failing states differ because of real data the mockups simplify: the real DPDPA questionnaire (20+ sections against 6), the real scope questions (10 with help text against 7) and evidence request (39 items against 8), real requirement titles that wrap at 1024, and states the data model can't produce. Each slice handoff's Results lists them per state.

**Checklist (this file's Review section)**
- S5: five tabs; `?tab=documents` still renders; `#desk-review-area` on the Questionnaire tab and not on the Overview; screening copy absent without DPDPA; the stepper comes from `assessment_stage.stage`. Stage outcomes without an exact mockup state reuse the nearest one, recorded as an open question in the S5 Results.
- S6: 303 tested over HTTP; `#document-list` round trips tested over HTTP; `documents_tab.html` deleted with a `deleted` map row; status words limited to Scanning, Available, Rejected, Out of date; no quarantine, scanning or versioning logic changed.
- Suite: S5 1472 passed, 30 skipped; S6 1464 passed, 30 skipped. `test_p6_8_board_report_v2::test_scenario_3` (byte-for-byte PDF) fails intermittently on a clean `main` too.

**Open questions for Saqlain** (details in the slice Results)
- S5: is the nearest-state mapping fine for "Continue questionnaire", "Run analysis", running and board-report stages? Should the live context wizard narrow to 720 px? Should partial scope saves from scripts stay allowed (the form now validates)?
- S6: inventory rows keep their actions hidden (the mockup has none; archive and new version are on the detail page). Unlinked assessments lose their documents view (deferred). AWS not configured keeps the accurate operator message.

**Follow-ups**
- S8: re-point the Scope RFI link to the Evidence Requests view; reconcile the Overview AWS link with Evidence navigation.
- S9: shell account tile (firm name instead of a user), and new S1 shell visual baselines now that the clip reaches Reports.
- The global breadcrumb slash glyph now matches the mockups, which shifts S3/S4 breadcrumbs by a pixel or two.
