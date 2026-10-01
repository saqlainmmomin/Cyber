# P6-8 v3: the board report as a 16:9 deck (PDF), an editable PPTX and a client XLSX `[AR: no blended score + approved-only + write-once versions]`

Implements the approved format `docs/product/2026-10-01-board-report-format.md` (decisions **F1-F10**, section 7 plan; mockups in `docs/product/2026-10-01-board-report-mockup/`, which are design references, not app code). The format is **approved and not reopened here**. If the code reveals a real problem with one of F1-F10, stop and report it with 2-3 options; do not choose.

**Owner:** Claude designs (this file + failing contract tests) -> Codex implements -> Claude reviews adversarially (`[AR]` below) -> PR. Per `tasks/agent-ownership.md`, Phase 6 row "P6-6..P6-10 Deliverables"; the migration, the retention purge scope and the write-once sidecar are Claude-reviewed.
**Depends on:** P6-8 B1 (#80) and B2 (#92), P6-9 (merged), P6-7b (#84), the format decision (#93), **P6-10** (the narrative; it claims document schema **v3** and the finding-id contract, `tasks/handoffs/2026-09-28-p6-10-remediation-and-narrative.md`, revision 2026-10-01).

## Two parts, two Codex runs, two PRs

The deck rewrites `board_report.build_document`, the template, the schema and the exporters, which is exactly where P6-10 works. So the work is split (decision doc section 7 allows it):

| Part | Scope | Branch (from `origin/main` @ `1df2b68`) | Runs |
|---|---|---|---|
| **V3-A data capture** | Migration, models, validation, audit, the board-inputs page, firm theme settings, the display font, the retention purge scope. **No** `build_document`, schema, report template or exporter change. | `claude/p6-8-v3a-data-capture`, worktree `/Users/saqlainmomin/cyberassess-v3a` | **Now**, in parallel with P6-10 (disjoint files) |
| **V3-B document and presentation** | The derived v3 document, `board_derive.py`, `board_view.py`, the 16:9 template, v3 XLSX and PPTX, DOCX retired for v3, golden re-record. | `claude/p6-8-v3b-deck`, worktree `/Users/saqlainmomin/cyberassess-v3b` (tests only today) | **Dispatch trigger: after the P6-10 PR and the V3-A PR are merged.** Merge `origin/main` into the branch first (never rebase), then dispatch. |

Both branches carry this file. The V3-A branch holds the V3-A tests, the guard allowances and the existing-test edits; the V3-B branch holds the V3-B tests and the synthetic v3 document. Whichever merges second merges `origin/main` into its branch and keeps both sides of every guard list (`tests/test_p6_2b_dpdpa_criteria.py` is the usual conflict).

> **The contract tests are already written. They are the contract.** Make them pass **without editing them**. Do not weaken, skip, `xfail`, re-parametrize or delete a test; if you believe a test is wrong, leave it failing and say which assertion, why, and what it should be in `## Results`. Extra tests go in `tests/test_p6_8_v3a_extra.py` / `tests/test_p6_8_v3b_extra.py`.
> **If the code forces a deviation from a decision, stop and report it in `## Results`; do not pick an alternative.** That covers every name, signature, constant, route, audit action, key, `data-*` attribute and rendered string below.
> **Answer-key independence (D-P5-9-C).** Never open, grep, glob or read anything under `validation/`, `scripts/validation/`, `tasks/handoffs/*p5-9*`, `docs/plans/2026-09-24-002-*`, `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`, `tests/test_validation_harness.py` or any `answer_key.json`. Scope every search to explicit paths (`app/`, the v3 test files).
> **Codex cannot write `.git` and has no network.** No `git add`/`commit`/`branch`/`stash`; read-only git is fine (the file-set guards use it). No `pip install`, no live LLM call (none is needed). The orchestrator commits.

## House rules the deck must keep (all already decided)

Only approved Conclusions, Findings and Actions reach client output. Scores, risk, priority and every count are deterministic, never an LLM. **No score is combined across frameworks.** Framework-specific copy is conditional. Report versions are write-once and the JSON sidecar is the record. Assessment period and evidence cut-off are on every deliverable. The only LLM text in a report is the consultant-accepted P6-10 narrative.

## Decisions (V3-A: A-F; V3-B: G-R; both: S)

Mapping to the approved format: **F1** (16:9 PDF) -> G, H, I; **F2** (PPTX replaces DOCX) -> N; **F3** (XLSX) -> M; **F4** (new consultant data) -> A-D, I, Q; **F5** (firm theme) -> E, F, L, R; **F6** (#92 merged as-is) -> N; **F7** (narrative into schema v3, refs as R-xx) -> J; **F8** (old sidecars frozen) -> N, R; **F9** (SoA) -> M, H; **F10** (priority derived) -> K, O.

### D-P6-8-V3-A (V3-A): capture only, and what V3-A may not touch

V3-A stores, validates, audits and edits the new consultant inputs. It changes **nothing** a report reads: the document, `DOCUMENT_SCHEMA_VERSION`, `board_report.py`, the report templates, the exporters, the golden and `report_content.py` stay as they are (the contract test greps `board_report.py` for the new field names). The v3 document **shape** is pinned below so V3-B and V3-A agree, but V3-A does not emit it. Allowed file set: the paths in `tests/p6_8_v3a_paths.py` (`V3A_APP_PATHS`, which includes `app/services/retention.py`, D-P6-8-V3-B). Forbidden: `tests/test_p6_8_v3a_data_capture.py::V3A_FORBIDDEN_PATHS` (the guard is scenario 12).

### D-P6-8-V3-B (V3-A): migration `5e9a2c7d4b18`, models, retention

New revision `alembic/versions/5e9a2c7d4b18_p6_8_v3a_board_inputs.py`, `down_revision = "8b2d5f7e1c34"` (the current head). Use `op.batch_alter_table` (SQLite). Upgrade:

| Change | Type |
|---|---|
| `findings.business_impact` | `Text`, nullable ("Why it matters", the deck's Risk column) |
| `findings.recommendation` | `Text`, nullable |
| `actions.responsibility` | `String(20)`, nullable (`client` / `consultant` / `shared`) |
| `assessments.board_asks_json` | `Text`, nullable |
| new table `initiative_metadata` | `id String(36) PK`, `assessment_id String(36) NOT NULL FK assessments.id ON DELETE RESTRICT` (indexed `ix_initiative_metadata_assessment_id`), `group_id String(255) NOT NULL`, `title String(255)`, `complexity String(10)`, `benefit String(10)` (all three nullable), `created_at`, `updated_at` (`DateTime(timezone=True)`, NOT NULL), `UniqueConstraint("assessment_id", "group_id", name="uq_initiative_metadata_assessment_group")` |

The table is not called `initiatives`: that name is the legacy gap-report table. `group_id` is a `remediation_groups` group id (a UCC cluster id or `SINGLE.<framework>:<requirement>`).

**Downgrade** drops the new objects, **but refuses** (`RuntimeError("Refusing to downgrade past P6-8 V3-A revision 5e9a2c7d4b18: ...")`, before any DDL) when any of the five holds consultant-entered data, exactly like P5-3's guarded downgrade ("restore a verified backup instead"). `tests/test_data_integrity.py` round-trips `downgrade -1` then `upgrade head` and compares the **full schema snapshot**: the migration and the models must declare identical constraint and index names, or that test fails.

Models: `Finding.business_impact`, `Finding.recommendation`, `Action.responsibility`, `Assessment.board_asks_json`, and `app/models/initiative_metadata.py::InitiativeMetadata` registered in `app/models/__init__.py` (and its `__all__`). No `relationship()` (a retention test forbids them).

**Retention (the destructive path; this part is Claude-reviewed line by line).** Add `"initiative_metadata"` to `retention.PURGE_ORDER` directly after `"findings"` (any position before `"assessments"` satisfies the FK-order test; the order is pinned by `tests/test_retention.py` scenario 1) and a scope `("initiative_metadata", InitiativeMetadata, InitiativeMetadata.assessment_id.in_(assessment_ids))` in `_purge_scopes`. The four new columns are on rows the purge already deletes. `tests/test_p6_8_v3a_purge.py` proves the target's rows go and a control engagement's stay.

### D-P6-8-V3-C (V3-A): `app/services/board_inputs.py`

Pure service, **never commits** (the routes do), no LLM. Constants, messages, audit actions and signatures are pinned by `test_scenario_3`; behaviour by scenarios 4-7. Summary:

```python
RESPONSIBILITIES = ("client", "consultant", "shared"); LEVELS = ("high", "medium", "low")
MAX_BUSINESS_IMPACT = 1200; MAX_RECOMMENDATION = 1500; MAX_INITIATIVE_TITLE = 120; MAX_ASKS = 3; MAX_ASK_CHARS = 400
FINDING_NOT_FOUND, ACTION_NOT_FOUND, GROUP_NOT_FOUND, ASSESSMENT_NOT_FOUND, INVALID_RESPONSIBILITY, INVALID_LEVEL,
TOO_MANY_ASKS, TEXT_TOO_LONG ("{label} must be {limit} characters or fewer."), NO_CHANGES   # exact strings in the test
AUDIT_FINDING = "finding.board_fields_updated"; AUDIT_ACTION = "action.responsibility_updated"
AUDIT_INITIATIVE = "initiative.metadata_updated"; AUDIT_ASKS = "assessment.board_asks_updated"
class BoardInputError(Exception)  # .message, .status_code; BoardInputNotFound (404); InvalidBoardInput (400)
update_finding_fields(db, assessment_id, finding_id, business_impact, recommendation, actor) -> Finding
update_action_responsibility(db, assessment_id, action_id, responsibility, actor) -> Action
update_initiative(db, assessment_id, group_id, title, complexity, benefit, actor) -> InitiativeMetadata
update_board_asks(db, assessment_id, asks, actor) -> {"consultant": [...], "consultant_by": str | None}
board_asks(assessment) -> {"consultant": [...], "consultant_by": ...}; initiative_metadata(db, assessment_id) -> {group_id: {...}}
```

Rules: text is trimmed, CRLF becomes LF, blank becomes `NULL` (it clears the field); levels and responsibility are trimmed and lower-cased then checked against the closed set; all validation runs before any write; a **no-op writes no audit event**; an edit writes exactly one event whose `metadata_json` is pinned in the test (`changes: {field: {from, to}}` for finding and initiative edits; `from`/`to` for responsibility and asks). `update_initiative` accepts only a `group_id` that is a **current** roadmap group of the assessment (`remediation_groups.build_groups(report_content.assessment_findings(...).findings, assessment.frameworks)`), so unapproved or invented groups cannot be annotated; the row is kept with `NULL`s when everything is blanked (history stays simple). `update_board_asks` keeps at most 3 non-empty asks and stores `{"asks": [...], "by": "<reviewer>"}` (the actor without its `consultant:` prefix) in `assessments.board_asks_json`, or `NULL` when none. There is no optimistic locking: single-consultant MVP, last write wins, every change audited with its before value.

**Action responsibility is not workflow.** It never touches `history_json`, status, owner, title or date, so P3-1's append-only history contract is unchanged.

### D-P6-8-V3-D (V3-A): routes and the board-inputs page

One new router `app/routers/board_inputs.py` (`APIRouter(tags=["board-inputs"])`, no prefix), registered in `app/main.py` with `dependencies=_ARCHIVE_GUARD` (one import and one `include_router` line, next to the SoA router). Exactly five routes (`test_scenario_8`); none contains `/findings`, `/conclusions`, `/remediation`, `/snapshots` or `/workpaper`, because other suites pin every route containing those substrings:

| Route | Form fields | Success | Refusal |
|---|---|---|---|
| `GET /assessments/{assessment_id}/board-inputs` | | `pages/board_inputs.html` | 404 unknown assessment |
| `POST /api/assessments/{assessment_id}/board-inputs/observations/{finding_id}` | `business_impact`, `recommendation`, `reviewer_name` | commit; 200 `{"status": "saved", "changed": bool}` | rollback; `{"detail": message}` with the error's status |
| `POST .../board-inputs/actions/{action_id}/responsibility` | `responsibility`, `reviewer_name` | same | same |
| `POST .../board-inputs/initiatives` | `group_id`, `title`, `complexity`, `benefit`, `reviewer_name` | same | same |
| `POST .../board-inputs/asks` | `ask_1`, `ask_2`, `ask_3`, `reviewer_name` | same | same |

Every response carries `X-Toast-Message` (URL-quoted) and `X-Toast-Type` (`success`, or `error` on a refusal; "No changes to save." is a success toast). Actor: `conclusion_review.reviewer_actor(reviewer_name)`.

**Page** (`pages/board_inputs.html`, extends `base.html`, no `|safe`, nothing numeric-priority): a reviewer-name input `id="reviewer-name"` included by every form (`hx-include`, `hx-swap="none"`); one `<form data-board-finding="<finding id>">` per Finding with textareas `business_impact` and `recommendation`; one `<form data-board-action="<action id>">` per Action with a `responsibility` select (blank, `client`, `consultant`, `shared`); one `<form data-board-initiative="<group id>">` per current roadmap group with `title`, `complexity`, `benefit`; one `<form data-board-asks>` with exactly `ask_1`..`ask_3`. The findings page gets one link `<a data-board-inputs-link href="/assessments/{id}/board-inputs">`.

**Deviation from the decision doc's section 7 UI bullets (flagged for Saqlain, see Open questions):** the doc places the fields on the Finding form, "the Roadmap page" and the versions page. There is no roadmap page, the finding card and findings routes are pinned by older suites, and the versions page is P6-10's file. So all four inputs live on **one** board-inputs page, linked from the findings page. The stored data and audit are exactly F4's; only the placement differs.

### D-P6-8-V3-E (V3-A): firm theme settings (F5)

`app/config.py::Settings` gains `firm_color_primary: str = "#161A5C"`, `firm_color_secondary: str = "#2D3FD3"`, `firm_color_accent: str = "#12B3A6"` (the mockup's indigo / royal / teal), each validated with `re.fullmatch(r"#[0-9a-fA-F]{6}", v)` (**fullmatch**: the existing `firm_primary_hex` validator uses `re.match(...$)`, which accepts a trailing newline; the test rejects `"#161A5C\n"`). The existing `firm_name`, `firm_logo_path` and **`firm_primary_hex` (default `#2563eb`) are unchanged**: `firm_primary_hex` is the legacy fpdf2 and navigation colour, and the approved doc names the deck colours `firm_color_*`, so there are two "primary" settings by design (see Open questions). New `app/services/firm_theme.py::resolve_theme(config=None) -> {"firm_name", "logo_path", "primary", "secondary", "accent"}` reads settings only: it does **not** open the logo file (V3-B embeds and hashes it into the sidecar, D-P6-8-V3-R).

### D-P6-8-V3-F (V3-A): the display font (F5)

Barlow Condensed Bold and SemiBold (SIL OFL 1.1) are already vendored by the designer in `app/assets/fonts/noto/` (next to the Noto files, so the offline fetcher's single font directory keeps working), because Codex has no network. Hashes: `BarlowCondensed-Bold.ttf` `e476562e...5b65`, `BarlowCondensed-SemiBold.ttf` `7b619d14...d2d9` (full values in the test); licence `OFL-BarlowCondensed.txt` (the OFL text under the font's own copyright line, "Copyright 2017 The Barlow Project Authors"; Saqlain: please compare it with upstream's `OFL.txt` before release). You add, **additively** in `app/utils/html_pdf.py`: `DISPLAY_FONT_FILES` (name -> sha256), `DISPLAY_LICENSE_FILES = ("OFL-BarlowCondensed.txt",)`, `display_font_face_css()` (two `@font-face` rules, family `'Display'`, weight 700 -> Bold, 600 -> SemiBold), and let `_OfflineFetcher` allow the display files too. `FONT_FILES`, `LICENSE_FILES` and `font_face_css()` stay byte-identical (B1's test pins them). V3-A does not use the font in any report; V3-B composes the CSS.

### The pinned v3 document (V3-B emits it; V3-A must not)

Document **schema v3** is P6-10's bump (`summary.narrative`, and sentences `{"text", "finding_ids", "finding_refs", "citations"}`). V3-B adds the keys below **under the same version number** (P6-10 merges first; the deck has never shipped), and re-records the golden once. Reference derivations: `docs/product/2026-10-01-board-report-mockup/enrich.py` (read it; where this file pins differently, this file wins). The synthetic document `tests/golden/p6_8_v3_deck_document.json` (120 requirements, 10 observations, 8 initiatives, a prior period) follows exactly this shape and is the input of the presentation tests.

* **New top-level keys:** `observations`, `initiatives`, `status_board`, `severity_dashboard`, `takeaways`, `board_asks`, `theme`. `summary.risk_matrix`, `roadmap.status_counts`, `roadmap.overdue_count` are new.
* **`observations[]`**: **all** approved Findings (not just the top ten), in `top_risks` order: `{"ref": "R-01", "rank", "finding_id", "framework_id", "framework_name", "requirement_id", "domain", "title", "observation" (= Finding.description), "risk" (= business_impact or `null`), "rating" (= severity), "recommendation" (or `null`), "responsibility" (derived, below, or `null`), "references": [{"framework_id", "framework_name", "clauses": [str, <=4]}]}`. `ref` is `R-%02d` of the rank, which is **the same number as P6-10's `F<n>` alias**; `finding_id` is the join key for narrative sentences.
* **`references`**: the control's own clause plus the clauses of the other controls in its UCC cluster (`remediation_groups.cluster_index`), **only for frameworks in scope**, in in-scope framework order; clause text is `section_ref or id` from the framework definition. A control in no cluster lists only itself. (An ISO-only assessment never lists a DPDPA clause.)
* **`top_risks[]`**: gains `business_impact`, `recommendation`, `action_status_label`; **loses `priority`**. `framework_sections[].gaps[]` and `appendices.requirement_register[]` also lose `priority` (**F10**: no numeric priority in client output; `Finding.priority` stays in the database and keeps ordering `top_risks`).
* **`roadmap.groups[].actions[]`** gain `finding_id` and `responsibility` (so initiatives can map actions to observations without a database read). `roadmap.status_counts` is `{"Open": n, "In progress": n, "Closed, awaiting verification": n, "Closed and verified": n}` in that order (the real `ACTION_STATUS_LABELS`; zeros kept). `roadmap.overdue_count` is the number of overdue actions.
* **`initiatives[]`**, one per `roadmap.groups` entry in group order: `{"ref": "I-1", "group_id", "title" (consultant title, else the group topic), "topic", "obs_refs": [sorted R-xx], "frameworks": [names], "cross_framework", "horizon" ("short" <= 90 days from `generated_on`, "medium" <= 180, "long" beyond, "unscheduled" without a date), "target_date", "overdue", "priority" ("high"/"medium"/"low", **derived**), "complexity", "benefit" (consultant levels or `null`), "responsibility" (derived), "owner" (first recorded owner), "actions": [{...group action..., "ref": "A-01", "obs_ref", "overdue"}]}`. Action refs `A-%02d` run across initiatives in order.
* **`status_board[]`**: `{"framework_id", "name", "version", "score", "rating", "in_scope", "domains": [{"title", "in_scope", "gaps", "crit_high", "ie", "score", "rating"}]}`, a domain matched to register rows by `f"{section.name} — {domain.title}"`.
* **`summary.risk_matrix`** `{framework_id: {critical, high, medium, low}}` and **`severity_dashboard`** `{severity: {"total", "distinct", "top": [{"label": "<framework name> · <domain>", "count"}]}}` (top four, ties broken by label), both counting register gaps (`partially_compliant` + `non_compliant`).
* **`takeaways`** `{status_board, dashboard, roadmap}`, deterministic sentences with the exact formats in `board_derive` (D-P6-8-V3-P). **`board_asks`** `{"derived": [...], "consultant": [...], "consultant_by": str | None}`.
* **`theme`** `{"firm_name", "primary", "secondary", "accent", "logo": null | {"media_type", "data_base64", "sha256"}}` (D-P6-8-V3-R).

### D-P6-8-V3-G (V3-B): the deck structure and frame (F1)

`board_report.render_html(document, embed_fonts)` keeps its signature and renders **one `<section class="slide" data-slide="<name>">` per slide** (A4 landscape replaced by `@page { size: 338.67mm 190.5mm; margin: 0 }`), in this order: `cover`, `contents`, `overview`, `ratings`, `executive-summary`, `status-board`, `risk-dashboard`, `board-asks`, `observations` (4 rows per slide), `roadmap`, `initiatives`, `comparison` (only when `prior_period.status == "compared"`), `limits`, `sign-off`, `annexure` (divider), `methodology`, `requirement-register` (21 rows per slide), `evidence-and-soa`. 25 slides for the synthetic document. Sections: `overview`, `ratings` are 01; `executive-summary`..`board-asks` 02; `observations` 03; `roadmap`..`sign-off` 04; the annexure slides 05 (`SECTION_OF` in the test). Every non-cover slide has a `<footer data-slide-footer>` with the firm, "Confidential", period, cut-off, version and the page number; the cover carries the same labels. The cover title is **framework-conditional**: "Privacy and information security compliance assessment" when any `frameworks[].legal`, else "Information security compliance assessment". A pure presenter `app/services/board_view.py::view(document) -> dict` does geometry, pagination and labels (prototype: `render_deck.view` in the mockup directory); `view(document)["slides"]` is the ordered list `{"slide", "number", "section", "title"}` that the template, the PPTX and the contents page all use. No JavaScript, no remote URL, no images except the optional logo; charts are inline SVG/CSS from the presenter. The SoA is a summary slide (theme x implementation, excluded controls), the 93 rows are in the XLSX (**F9**).

### D-P6-8-V3-H (V3-B): executive summary, status board, risk dashboard (F1, F9)

Selectors pinned by the tests: `data-framework-score="<id>"`, `data-outcome-bar="<id>"`, `data-total-requirements`, `data-top-risk="R-xx"` (first three observations) and the constant `board_view.NEVER_COMBINED_NOTE = "Scores are per framework and are never combined; the totals above are counts."`, rendered on the executive summary; no `data-combined-score` anywhere. Status board: `data-status-framework="<id>"` containing `data-status-domain="<title>"` rows with the pill "No gaps", "<n> gaps · <k> crit/high" or "Out of scope"; takeaway in `data-takeaway="status-board"`. Risk dashboard: `data-severity-panel="critical|high|medium|low"` (ring count and "where they sit" labels), a framework x risk table `tr[data-risk-matrix="<id>"]` whose last four cells are critical, high, medium, low, takeaway `data-takeaway="dashboard"`.

### D-P6-8-V3-I (V3-B): observations, roadmap, initiatives, board asks (F1, F4, F10)

* **Observations:** `tr[data-observation="R-xx"]` with exactly seven `td`: ref; domain + framework + responsibility marker (`data-responsibility="client|consultant|shared"`); title + observation; risk; rating pill; recommendation; reference (`<framework name>: <clauses>`). A `null` risk or recommendation renders **"Not recorded"** in an element with class `not-recorded` (never blank, never invented). A `data-responsibility-legend` is on each slide.
* **Roadmap:** three columns `data-horizon-column="short|medium|long"`; each initiative a `data-initiative="I-n"` callout with title, its `R-xx` refs and, when overdue, "OVERDUE"; `unscheduled` initiatives sit in the long column labelled "Not scheduled"; takeaway `data-takeaway="roadmap"`.
* **Initiatives:** `tr[data-initiative-row="I-n"]` with `data-priority`, `data-complexity`, `data-benefit` glyph elements and the owner. Priority is derived (K).
* **Board asks:** consultant asks as `data-board-ask` cards (at most three shown), the derived "needs attention" list as `data-derived-ask` items, "by <consultant_by>"; the derived panel renders even with no consultant asks.

### D-P6-8-V3-J (V3-B): narrative placement (F7)

P6-10's narrative moves out of the portrait summary into the deck: the **executive** narrative is the verdict panel `data-narrative="executive"` **inside** `data-slide="executive-summary"`; each framework's narrative is `data-narrative="framework-<id>"` under that framework's outcome bar on the same slide; the cross-framework narrative is `data-narrative="cross-framework"` on `risk-dashboard` (my choice, see Open questions). Sentences are `data-narrative-sentence`; their references render as `<span class="ref">R-xx</span>` **through the `finding_ids` join to `observations[].finding_id`**, never as `F`-aliases and never as requirement ids. A cited finding that is not an observation drops its ref and keeps the sentence. With no accepted narrative nothing renders (no `data-narrative` attribute at all). `narrative.NARRATIVE_NOTE` moves with the panel and says "R-xx" (update P6-10's constant and its test in the list below).

### D-P6-8-V3-K (V3-B): numeric priority is gone (F10)

No client slide, sheet or PPTX text shows a typed 1-4 priority (`test_scenario_11` greps for `Priority [1-4]` and `P[1-4]`). Initiative Priority is **derived** from the highest approved severity it closes (`board_derive.priority_for`) and shown as High / Medium / Low; there is no input for it anywhere.

### D-P6-8-V3-L (V3-B): theme and fonts in the template (F5)

`:root` defines `--p1` (primary), `--p2` (secondary), `--acc` (accent) **from `document.theme`** (and may derive a lighter tint); severity colours `#9B1C1C #D9481E #F0A030 #3C9D6B` and the outcome colours are constants, not themed. With `embed_fonts=True` the page includes `font_face_css()` and `display_font_face_css()` and uses `font-family: 'Display'` for titles; with `embed_fonts=False` (preview) no font is embedded and `BarlowCondensed` does not appear. A logo renders as one `<img src="data:<media_type>;base64,...">` on the cover only. User text is always autoescaped.

### D-P6-8-V3-M (V3-B): the client XLSX (F3, F9)

`board_exports.render_xlsx` dispatches on `schema_version`: v1/v2 -> the B2 workbook, unchanged (`XLSX_SHEETS`); **v3 -> `XLSX_SHEETS_V3 = ("Executive Summary", "Detailed Assessment", "Observation Register", "Remediation Tracker", "Statement of Applicability", "Evidence Register", "Definitions")`** (SoA only when `soa` is present). Layout follows the reference workbook `board-workbook-PROPOSED.xlsx` (prototype `render_xlsx2.py`): coloured tabs; `A1` title, `A2` purpose, `A3` `firm  |  company  |  Assessment period ...  |  Evidence cut-off ...  |  Board report vN (snapshot xxxxxxxx)  |  Draft until issued`; header row 6; frozen panes and autofilter on the registers; headers exactly as asserted in `test_scenario_14*`; Executive Summary with a per-framework posture table (never combined), a native stacked bar and a native pie, and the `NEVER_COMBINED_NOTE`; Detailed Assessment with a **Linked observation** `R-xx` per requirement; Remediation Tracker with one banner row per initiative (one cell: `I-1  <title>   |   R-03 / R-05   |   Short term   |   Priority: High   |   Complexity: High   |   Benefit: High   |   ...`), `A-xx` action rows, a Status dropdown (`Open,In progress,Done,Blocked`), "Unassigned" for a missing owner, conditional formats turning overdue dates and "Unassigned" red; SoA with all 93 rows and an Applicability dropdown (`Applicable,Excluded,Not determined`), Justification the editable column; Definitions for every scale (outcomes, risk, complexity, benefit, horizons, responsibility). The formula-injection guard (`FORMULA_PREFIXES`, `quotePrefix`) covers every new text field.

### D-P6-8-V3-N (V3-B): PPTX, DOCX and the dispatch (F2, F6, F8)

New dependency **`python-pptx==1.0.2`** in `requirements.txt` (the orchestrator installs it into `.venv` **before** dispatching V3-B; Codex cannot). `board_exports` gains `PPTX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"`, `render_pptx(document, *, document_sha256) -> bytes` (prototype `render_pptx.py`): 25 slides of 338.67 x 190.5 mm mirroring the PDF one for one, native tables and native charts (doughnut, 100%-stacked bar), theme colours from `document.theme`, title font Arial Narrow (fallback for Barlow), body Calibri, and **every slide's notes contain `derivation_label(document, document_sha256)`** (edits do not change the report). Dispatch by `schema_version`: v3 -> new XLSX + PPTX; v<=2 -> the B2 renderers, frozen; **`render_docx` raises `DocumentSuperseded` (`status_code = 410`, `DOCX_SUPERSEDED_MESSAGE` mentioning PPTX) for v3**; `render_pptx` raises `UnsupportedDocument` for v<3; unknown versions still raise `UnsupportedDocument` (409). `SUPPORTED_SCHEMA_VERSIONS` stays `(1, 2, 3)` (P6-10 adds the 3). New route `GET /api/assessments/{assessment_id}/snapshots/{snapshot_id}/pptx` next to the docx/xlsx routes (same headers, `X-Board-Export-Format-Version` unchanged); the docx route returns 410 for v3 with the toast. The versions page offers PPTX and XLSX for v3 versions and DOCX/XLSX for older ones. Stored PDFs and old sidecars are never re-rendered (F8).

### D-P6-8-V3-O (V3-B): `app/services/board_derive.py`, the pure derivations

No database, no LLM, no clock (the caller passes `generated_on`). Pinned by `test_p6_8_v3b_document.py` scenarios 1-6, each against the synthetic document:

```python
HORIZON_SHORT_DAYS = 90; HORIZON_MEDIUM_DAYS = 180; HORIZONS = ("short", "medium", "long", "unscheduled")
OPEN_STATUS_LABELS = ("Open", "In progress")
horizon_for(target_date: date | None, generated_on: date) -> str        # <=90 short, <=180 medium, else long, None -> unscheduled
is_overdue(target_date, generated_on, status_label) -> bool              # target < generated_on and status in OPEN_STATUS_LABELS
priority_for(severities) -> "high" | "medium" | "low"                    # any critical/high -> high; else any medium -> medium; else low
responsibility_for(values) -> str | None                                 # all equal -> it; mixed -> "shared"; none recorded -> None
observation_ref(rank) "R-%02d"; initiative_ref(i) "I-%d"; action_ref(n) "A-%02d"
reference_clauses(framework_id, requirement_id, in_scope_framework_ids) -> [{"framework_id", "framework_name", "clauses"}]
build_status_board(framework_sections, register); build_risk_matrix(...); build_severity_dashboard(...)
build_initiatives(groups, metadata, observations, generated_on)           # metadata: {group_id: {"title", "complexity", "benefit"}}
build_takeaways(status_board, severity_dashboard, totals, initiatives, observations)
derived_asks(initiatives, observations, *, insufficient_evidence, rfi_open) -> [str]
```

### D-P6-8-V3-P (V3-B): the derived blocks and their exact text

Takeaways: `status_board` = `"{clean} of {scoped} in-scope domain(s) have no approved gaps; the weakest are {A} ({a:.0f}%) and {B} ({b:.0f}%)."` (one weakest: `"; the weakest is {A} ({a:.0f}%)"`; none: no clause); `dashboard` = `"{gaps} approved gap(s), {ch} of them critical or high; {n} critical gap(s) in {k} domain(s)."`; `roadmap` = `"{n} initiative(s) cover {c} of {N} key observations; {x} close a weakness once across more than one framework."`. Derived asks, in this order and only when non-zero: `"{n} remediation action(s) past their target date."`, `"{n} action(s) on critical or high findings have no owner."`, `"{n} action(s) have no target date."`, and `"{ie} requirement(s) could not be concluded; {rfi} evidence request(s) are open."` (shown when either is non-zero). Counts and the matrix always equal the register (the tests prove it).

### D-P6-8-V3-Q (V3-B): `build_document` (schema v3)

`board_report.build_document` emits the pinned document above. Inputs: `report_content` carries `business_impact`, `recommendation` and `responsibility` through `ReportFinding`/`ReportAction`; initiative metadata via `board_inputs.initiative_metadata`; asks via `board_inputs.board_asks`. **Missing inputs never block generation** (section 7 "Readiness"); they stay `null` and render "Not recorded". The document is deterministic (two builds with the same `generated_at` are equal). `DOCUMENT_SCHEMA_VERSION` stays `3`. The golden `tests/golden/p6_8_board_document.json` is re-recorded **once** with `P6_8_RECORD_GOLDEN=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_p6_8_board_report_v2.py -k golden` and then the file is run without the variable; its diff must be explained by this section (new keys, removed `priority`, `theme` default colours).

### D-P6-8-V3-R (V3-B): the theme is frozen in the sidecar (F5, F8)

`theme` is built at generation from `firm_theme.resolve_theme()`; a configured `firm_logo_path` is read **once** (at most 2 MB; a missing, unreadable or oversized file is `logo: null`, never an error) and stored as `{"media_type", "data_base64", "sha256"}`. After the version is generated, changing settings must not change it: `test_scenario_15` reads the stored sidecar after changing the primary colour. The golden uses the default theme.

### D-P6-8-V3-S (both): existing tests that change

**V3-A, already applied by the designer** (nothing deleted; scoped allowances): the Alembic head literal `8b2d5f7e1c34` -> `5e9a2c7d4b18` in `tests/test_p6_6_report_foundations.py`, `test_retention.py` (also `PURGE_ORDER`), `test_p5_6_rfi_rebuild.py`, `test_startup_invariants.py`, `test_p5_3_framework_desk_review.py`, `test_p5_4_adaptive_ucc_questionnaire.py` (also `upgrade` to `"head"`), `test_alembic_baseline_immutable.py`, `test_data_integrity.py`, `test_correctness_bundle.py`, `test_p5_2_reader_migration.py`; and per-PR file-set allowances (`tests/p6_8_v3a_paths.py`, `V3A_EXCLUDES`) in the guard tests of P6-2b, P6-3a, P6-4 (cap, judge, what's-missing), P6-5/P5-2/P5-4/P5-6/nist-csf2, P6-6, P6-7, P6-7b, B1, B2 and P6-9. If another existing test fails because of the migration, **stop and report the file and line**; do not edit it.

**V3-B, applied by Codex in its run, and nothing else** (from the decision doc section 7, adjusted to the code now on main): `tests/test_p6_8_board_report_v2.py` (`DOCUMENT_KEYS` + the seven keys; `data-section` assertions -> `data-slide`; priority text; its fixture also fills the V3-A inputs; the golden); `tests/test_p6_9_roadmap.py` (the slice uses `data-slide="roadmap"`/`initiatives`); `tests/test_p6_9_soa.py` (the PDF asserts the SoA summary and excluded rows, not 93 rows; the 93-row assertion moves to the XLSX test); `tests/test_p6_9_prior_period.py` (the legacy v2 fixture stays; the slide-order slice is renamed); `tests/test_p6_8_b2_docx_xlsx.py` (the v2 path is unchanged; the live-builder assertions already read 3 after P6-10); `tests/test_p6_10b_narrative.py` (scenarios 4 and 9: references `[requirement id]` -> `R-xx`, the note text, the verdict-panel location) and `narrative.NARRATIVE_NOTE`. Plus per-PR guard allowances for the V3-B file set. Anything else that breaks: stop and report.

## Files touched

**V3-A:** `alembic/versions/5e9a2c7d4b18_p6_8_v3a_board_inputs.py` (new), `app/models/{finding,action,assessment,initiative_metadata (new),__init__}.py`, `app/services/{board_inputs (new),firm_theme (new),retention}.py`, `app/routers/board_inputs.py` (new), `app/main.py` (2 lines), `app/config.py`, `app/templates/pages/{board_inputs (new),findings}.html` (the findings page: one link), `app/utils/html_pdf.py` (additive), the three Barlow files (already in the branch). The tests, support and guard edits are the designer's.

**V3-B (indicative; the guard test the designer adds at dispatch is authoritative):** `app/services/{board_derive (new),board_view (new),board_report,board_exports,report_content,remediation_groups,narrative}.py`, `app/routers/snapshots.py`, `app/templates/reports/board_report.html` (rewritten, with partials as needed), `app/templates/pages/report_snapshots.html`, `requirements.txt`.

## Verification (Codex reports these in `## Results`; the orchestrator re-runs them)

**V3-A:** (1) `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_8_v3a_data_capture.py tests/test_p6_8_v3a_purge.py` -> **21 passed**, files unmodified, run twice. (2) Full suite: baseline on this branch's base (`origin/main` @ `1df2b68`) is **1224 passed, 10 skipped**. On this branch before your work it is **34 failed, 1211 passed, 10 skipped**: 21 new V3-A tests plus 13 existing tests (the "Alembic head" pins and `PURGE_ORDER`) that go green only once the migration and the purge scope exist. Expected after V3-A: **1245 passed, 10 skipped**, plus only the known transient `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes` while files are uncommitted. (3) `git diff --stat main -- app/services/board_report.py app/services/board_exports.py app/templates/reports app/services/report_snapshots.py tests/golden` is empty. (4) Migration: upgrade then downgrade on a scratch DB (the tests do it), `alembic heads` prints `5e9a2c7d4b18 (head)`. (5) Orchestrator, in the browser: the board-inputs page saves each form and the audit rows appear; screenshot.

**V3-B:** both V3-B test files green and untouched; full suite green with counts recorded; a generated version's PDF is 25 landscape pages (open it); `python-pptx` opens the PPTX; the XLSX opens in LibreOffice or Numbers without repair; the v2 sidecar of an old version still exports through the B2 path.

## Adversarial review checkpoints `[AR]`

1. **No blended score.** Any total, average or ranking across frameworks in the deck, XLSX or PPTX other than counts?
2. **Approved only.** Does any new field reach output for an unapproved Finding or Action? Can an invented `group_id` get a title?
3. **No unreviewed text.** Is any derived sentence free text? Does a `null` input ever render as filler instead of "Not recorded"?
4. **Write-once.** Does anything re-render or rewrite an existing version? Is the theme (and logo) frozen at generation? Are v1/v2 sidecars still exportable through the frozen path?
5. **Retention.** Is `initiative_metadata` purged with its assessment and only then? Does the downgrade refuse to drop consultant text?
6. **Injection.** Are consultant fields autoescaped on the page and in the HTML deck, quote-prefixed in the XLSX, and plain runs in the PPTX? Any `|safe`?
7. **Conditional copy.** ISO-only: no legal wording on the cover, in references or in definitions.
8. **Period and cut-off** on every slide, sheet and PPTX slide.
9. **Priority** appears nowhere as a typed number; the derived one matches the highest approved severity.
10. **Scope.** The diff matches "Files touched"; the V3-A diff does not touch `board_report.py`.

## Ready-to-paste Codex prompts

**V3-A:**
```
You are implementing P6-8 V3-A (consultant-entered data for the v3 board deck) in /Users/saqlainmomin/cyberassess-v3a on branch claude/p6-8-v3a-data-capture.

Read fully first: tasks/handoffs/2026-10-01-board-report-v3-deck.md (decisions D-P6-8-V3-A..F and S; skip G..R, they are V3-B), tests/test_p6_8_v3a_data_capture.py, tests/test_p6_8_v3a_purge.py, tests/p6_8_v3_support.py, tests/p6_8_v3a_paths.py, CLAUDE.md and AGENTS.md.

Rules:
- Make every test in tests/test_p6_8_v3a_data_capture.py and tests/test_p6_8_v3a_purge.py pass WITHOUT editing them (or the support/paths/guard files). Do not skip, xfail, weaken or delete tests. If a test looks wrong, leave it failing and explain in the handoff's ## Results.
- Implement exactly D-P6-8-V3-A..F. Names, signatures, constants, messages, routes, audit actions, metadata keys, form field names and data-* attributes are fixed. If the code forces a deviation, stop and report it.
- Touch only the V3-A file set (the paths in tests/p6_8_v3a_paths.py, which includes app/services/retention.py). Do NOT touch board_report.py, board_exports.py, any report template, the document schema version, the golden, or the exporters. Do not edit existing tests; if one fails because of the migration, stop and report it.
- No network, no .git writes, no pip install, no live LLM call. The Barlow font files are already in app/assets/fonts/noto/; do not replace them.
- Answer-key independence: never open validation/**, scripts/validation/**, tasks/handoffs/*p5-9*, docs/plans/2026-09-24-002-*, scripts/seed_test_companies.py, scripts/test_ground_truth.json, scripts/seed-v2-prompt.md, tests/test_validation_harness.py or any answer_key.json.

Steps: 1) run the full suite, record the counts (expect 34 failed, 1211 passed, 10 skipped before your work: 21 new tests and 13 existing head-pin tests); 2) implement; 3) run the two V3-A test files (21 passed, twice), then the full suite; 4) append "## Results (V3-A)" to the handoff: counts, deviations, doubts. Change nothing else in the handoff.
```

**V3-B (do not dispatch until the P6-10 and V3-A PRs are merged; then merge `origin/main` into `claude/p6-8-v3b-deck`, install `python-pptx==1.0.2` into `.venv`, add the V3-B file-set guard, and adapt this prompt):**
```
You are implementing P6-8 V3-B (the v3 board document, 16:9 deck, XLSX and PPTX) in <worktree> on branch claude/p6-8-v3b-deck.
Read fully first: tasks/handoffs/2026-10-01-board-report-v3-deck.md (all decisions; the pinned v3 document), docs/product/2026-10-01-board-report-format.md, tests/test_p6_8_v3b_document.py, tests/test_p6_8_v3b_deck.py, tests/p6_8_v3_support.py, and the prototypes in docs/product/2026-10-01-board-report-mockup/ (read-only references, absolute paths inside them are not for you).
Rules as for V3-A, for the two V3-B test files. Apply exactly the V3-B edits of D-P6-8-V3-S and re-record the golden once.
```

## Open questions for Saqlain (each has a default; none blocks V3-A)

1. **Where the inputs live (V3-A).** Default: one board-inputs page linked from the findings page. The decision doc's section 7 puts the fields on the finding form, "the roadmap page" and the versions page. Alternative: add "Why it matters" and "Recommendation" to the create-finding form too (a bigger change to pinned finding routes and `finding_card.html`).
2. **Two primary colours.** Default: new `firm_color_primary/secondary/accent` as the approved doc names them, and the legacy `firm_primary_hex` (fpdf2, navigation) untouched. Alternative: one setting, which would change the app's navigation colour and the fpdf2 PDFs' default.
3. **Where the framework and cross-framework narratives sit (V3-B).** Default: framework narrative under each framework's bar on the executive-summary slide, cross-framework narrative on the risk-dashboard slide. The decision doc only fixes the executive verdict panel.
4. **Observations: all findings or the top ten (V3-B).** Default: all approved findings, so every narrative reference maps to an R-xx and the register is complete; the deck grows by one slide per four findings. Alternative: cap at ten like `top_risks`, and drop narrative refs beyond rank ten.
5. **Barlow licence file.** Written from the OFL text with the font's own copyright line; please compare with upstream before release.

## Self-review (designer)

1. **V3-A was proven against a throwaway reference implementation** (not committed): all 21 V3-A tests passed, and the **full suite with the reference was 1244 passed, 10 skipped, plus only the uncommitted-tests transient** (the guard allowances were verified against committed changes in a scratch worktree). Writing it exposed three things this file now pins: the retention purge scope (`test_retention` fails without it), the downgrade round-trip schema comparison, and `re.match(...$)` accepting a trailing newline.
2. **V3-B is less verified.** `test_p6_8_v3b_document.py` scenarios 1-6 (pure derivations) pass against a throwaway `board_derive`; the XLSX assertions were checked against the approved reference workbook (the new pins, such as the never-combined note and the responsibility definitions, are not in the prototype and will fail until implemented); PPTX mechanics were checked against the sample deck. The HTML selectors, `build_document`, route and PDF tests have **not** been run against an implementation. Expect Codex to report a few test bugs; fix them in a designer pass, not in the run.
3. **Red state.** V3-A: the two V3-A files are 20 failed, 1 passed (the file-set guard, scenario 12) and no collection errors; with the 13 existing head-pin tests the branch is 34 failed. V3-B: 36 failed, 1 passed (the no-priority test passes trivially on the old template), no collection errors; the failures are `ModuleNotFoundError` for `board_view`, `board_derive`, `pptx`, missing keys, and assertions. The V3-B document tests need P6-10 and V3-A merged to reach their real assertions; on main today they fail on missing modules and keys.
4. **Not verified:** the page in a browser, the PDF look (the mockup PDF is the reference), live LLM anything (none is used), and the merge of this branch with P6-10 (disjoint files except `tests/test_p6_2b_dpdpa_criteria.py` and possibly `pages/report_snapshots.html`).

## Results

## Results (V3-A)

- Baseline: 34 failed, 1211 passed, 10 skipped.
- Focused V3-A tests: 21 passed on the first run and 21 passed on the required second run.
- Full suite: 1245 passed, 10 skipped, 290 warnings.
- Deviations: None. The V3-A contract tests, support/paths/guard files, and existing tests were not edited. Changes stayed within the V3-A file set.
- Doubts: No blocking doubts. Browser-level screenshot verification and upstream font-license comparison were not performed; the offline font rendering contract passed.
- Review fix: responsibility forms now submit on `change`; targeted command: 21 passed, 1 failed (the V3-A file-set guard requires an allowance for `tests/test_p6_8_v3a_extra.py`); full suite not run.
