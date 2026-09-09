---
artifact_contract: "ce-handoff/v1"
created_at: "2026-09-09"
title: "WS1–WS3 implementation results and approval handoff"
summary: "Configurable branding, framework picker and scoring contract, and synthetic DPDPA goldens implemented and verified; publication awaits Saqlain's approval."
keywords: ["white-label", "framework-picker", "golden-tests", "approval"]
cwd: "/Users/saqlainmomin/dpdpa-gap-tool"
branch: "docs/2026-09-08-handoffs"
head: "635291e"
---

# Objective and authorization

Saqlain requested execution of the three September 8 handoffs with a dedicated Sol/medium subagent for each, followed by ONE results handoff and a code PR only after approval. The three workers were dispatched with `gpt-5.6-sol` and `medium`. Saqlain explicitly approved clearly labeled synthetic goldens while retaining the live capture script. No live analyzer calls, commits, pushes, PR creation, or production deployment were performed.

Implementation is uncommitted in the shared checkout above. The starting tree was clean. The existing feature branch was retained for the requested combined PR instead of creating three competing branches in the shared workspace. Original handoffs remain unchanged:

- `tasks/handoffs/2026-09-08-ws1-white-label.md`: branding interfaces and acceptance criteria.
- `tasks/handoffs/2026-09-08-ws2-picker-data-model.md`: picker, report modes, cluster-once contract.
- `tasks/handoffs/2026-09-08-ws3-golden-dpdpa.md`: strict replay and golden comparison contract.

# Implemented results

## WS1 — deployment branding

`app/config.py` and `.env.example` define `FIRM_NAME`, `FIRM_LOGO_PATH`, and `FIRM_PRIMARY_HEX`. `app/main.py` injects shared template settings. Base/login templates and PDF/RFI/evidence-checklist exports use configurable product text; framework identifiers retain their meaning. Page-title suffixes carry the firm name even when child templates override their title.

PDF logos accept absolute or repository-relative paths and fit a 40×20 mm box. PDF accents use the configured primary RGB value. RFI/evidence titles handle long firm names. PDF and DOCX exports contain configured branding. `app/static/img/momin-test.png` is the requested 200×80 placeholder. `tests/test_white_label.py` covers defaults, environment overrides, HTML, PDF/logo, DOCX, and the unexcluded grep gate.

Compatibility decisions: the current MVP has no auth and the login template was orphaned; GET `/login` redirects to the branded dashboard rather than introducing a nonfunctional sign-in form. Navbar color changes only with an explicit override, preserving default navy. Navbar logo serving was not added: the detailed handoff interface specifies PDF embedding, and the operator-provisioned path may be outside static storage. Existing PDF layout gains branding rather than remaining pixel-identical. Remaining product-name matches outside the specified gate are source comments, not rendered branding.

## WS2 — selection, navigation, and scoring contract

`app/models/assessment.py` adds parsed `frameworks` and `is_multi_framework` properties and rejects explicitly empty selections. `app/routers/web.py` preserves `/assessments/new`, accepts the requested checkbox field, and adds `/assessments` compatibility. New assessments permit DPDPA, ISO 27001, and NIST CSF; GDPR/HIPAA/PCI-DSS are disabled roadmap choices and rejected on submission.

The assessment page and new framework partials provide multi-framework tabs with domain/control summaries and finding counts; single-framework assessments retain their layout. Unknown or unselected framework tabs return 404. Framework and workflow query state are separate so changing workflow does not reset the selected framework.

The report supports combined/per-framework modes. `/report` renders the full application shell for normal and HTMX-boosted navigation; non-boosted HTMX and `/report-summary` return the fragment. `app/templates/partials/report_tab.html` also changed as a necessary integration seam to forward view/framework state to its lazy-loaded summary. This one-line scope addition fixes real navigation behavior.

`app/schemas/scoring.py` defines ClusterVerdict, FrameworkScore, CombinedScore, and ScoringResult with deterministic verdict-score and derived-view consistency validation. `scoring.score(id, ['dpdpa'], *, _session=None)` adapts legacy report rows to cluster verdicts, uses existing UCC mappings, propagates each verdict to mapped DPDPA controls, and delegates score arithmetic to unchanged legacy scoring scaled to 0–5. Legacy conflicting cluster members resolve conservatively to their least implemented assessed status. Unknown/N/A do not enter score averages, but do count as covered when their cluster has a verdict. The injected session is for isolated tests/capture. Non-DPDPA calls to the new wrapper explicitly remain unsupported, as scoped; existing analyzer/report paths remain available.

## WS3 — deterministic regression baseline

`tests/fixtures/canonical_dpdpa/` contains synthetic policies, 41 questionnaire answers, all nine screening inputs, branding inputs, replay metadata, and exact expected screening/analyzer/score output plus extracted PDF text SHA-256, page count, and byte floor. Total size at capture: 109,417 bytes. No real client data.

`app/services/claude_analyzer.py` routes SDK requests through a single plain-dict seam, including streaming requests. `tests/support/analyzer_mock.py` hashes normalized full requests and fails on missing/unmatched recordings, including errors swallowed by optional production fallbacks. `tests/support/fixture_capture.py` regenerates offline by default; a genuine analyzer recording needs `--live` and `USE_LIVE_ANALYZER=1`.

The fixture uses the actual screening prompt/parse/persistence path with a synthetic provider response. Desk-review findings are seeded; the desk-review provider itself is not covered. Analyzer recording provenance is explicitly `synthetic_offline_characterization`, not a genuine model response. PDF time is fixed only in the harness. See the fixture README for capture commands and limits.

`tests/conftest.py` supplies isolated canonical and legacy prefill fixtures. This resolves the four missing-fixture baseline errors without suppressing tests; accumulated legacy test failures assert at teardown. White-label tests isolate both app lifespan migrations and request sessions from the user's database.

# Verification evidence

- Starting full suite: **25 passed, 4 setup errors**, all four due to missing fixtures in the legacy prefill script.
- Final combined suite: **53 passed** using `.venv/bin/python -m pytest -q`, with a separate `/tmp` database and upload directory. Existing collection/return-value and framework deprecation warnings remain.
- WS1 test-first evidence: 4 initial failures, then 4 passed; plain and ambient-branding runs also pass after database isolation correction.
- WS2 test-first evidence: 9 initial failures, then 13 passed. Follow-up regressions cover HTML shell, normal/boosted HTMX, framework persistence, and unknown/N/A coverage.
- WS3 focused golden plus legacy compatibility run: 11 passed. Parent reran offline capture successfully: 41 findings, 46,515-byte report, 109,417-byte fixture tree.
- WS3 worker ran three captures with identical fixture digest `873d0d397aa788ad8e6d2bc197f47832669903b3`.
- WS3 isolated adversarial evidence: changing a status-score mapping failed score and PDF-text tests; semantic private-variable rename passed all seven golden/mock tests; deleting recording failed all four pipeline goldens with explicit live-disabled guidance. Live capture without its opt-in refused provider transport.
- Python compilation of touched Python files passed in worker checks; `git diff --check` passed. No project lint/typecheck command is configured.
- Product-name grep across specified templates/export files: zero matches, without exclusions.
- Uvicorn with reload booted on port 8018 using Python 3.13.13 and a separate temporary database.
- Real browser: created DPDPA-only, ISO+NIST, and all-three assessments; scope, questionnaire entry, and report states rendered. Single assessment has no framework tab group; multi-framework tabs switch and survive reload. Roadmap choices and zero-selection submit are disabled.
- Real browser after fixes: on the all-three synthetic report, clicking Per framework retains branded navigation, the selected NIST tab, and displays all framework scores. Direct report URLs render the full shell. Synthetic smoke report rows were seeded only in `/tmp/cyberassess-ws123-browser.db`; no live analysis was invoked.
- Desktop report and 390px mobile picker inspected; temporary viewport override reset. Existing dark-theme contrast limitations in the pre-existing assessment/picker remain outside this work's scope.

# Review and remaining limits

A separate reviewer found the report-fragment navigation and coverage-count defects; both were fixed with regressions. Parent browser testing then found HTMX-boosted navigation needed a distinct branch; that was also fixed and verified in the browser. Parent inspected integration changes and retained existing scoring functions and report sections.

The additional full CE review attempt was interrupted by an account usage limit before producing a completed receipt; do not describe it as a completed independent review pipeline. Code review: skipped (ce-code-review unavailable) — that top-level attempt terminated under the usage limit; bounded reviewer findings and parent diff/browser verification were used. No independent cross-model completion is claimed.

No implementation blocker remains. Deliberate limits are the synthetic rather than live-captured baseline, seeded desk-review provider output, DPDPA-only new scoring wrapper, and PDF-only filesystem logo embedding. Later workstreams own multi-framework cluster analysis and persistence; this change does not claim those are implemented.

# Publication handoff

Pending action is **Saqlain's approval to commit, push, and open the combined code PR**. Nothing has been staged or committed by this run. Recheck the diff and branch before publication because the work is currently uncommitted. Include this results file and `tasks/todo.md`; include all new schema, partial, fixture, support, test, and placeholder files. Do not include temporary databases, uploads, or ignored build artifacts. Source docs are already in baseline commit 635291e.

Suggested PR title: `feat: add deployment branding, framework picker, and DPDPA golden tests`.

Post-deploy validation: owner is the deploying maintainer. During the first deployment smoke and first generated report, check logs for TemplateResponse/UndefinedError, invalid color/image errors, unknown framework IDs, and HTTP 500s; verify one branded PDF and report-mode navigation. Healthy signals are correct brand, retained page shell, selected framework, and expected report scores. Roll back the feature commit(s) if creation/export fails or score regression is observed. No database migration is introduced.
