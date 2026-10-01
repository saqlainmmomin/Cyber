# Board report: target format (PDF deck, PPTX, XLSX)

**Status:** APPROVED by Saqlain in chat, 2026-10-01 ("this looks good for now"). **Date:** 2026-10-01. **Branch:** `claude/report-format-review`.
**Supersedes:** the layout parts of plan Part D2/D3 (`docs/plans/2026-09-25-001-...`). The data contract and house rules there still apply.

**Mockups and prototypes:** `docs/product/2026-10-01-board-report-mockup/`.
- `board-deck-PROPOSED.pdf`: 25 slides, 16:9.
- `board-workbook-PROPOSED.xlsx`
- `board-deck-sample.pptx`: 4 editable slides.
- `board-report-CURRENT-rich-data.pdf`: the current v2 template on the same data, for comparison.
- Generator prototypes: `gen_doc.py` → `enrich.py` → `render_deck.py` + `deck_template.html`, `render_xlsx2.py`, `render_pptx.py`, plus the synthetic `deck_document.json`.

These are design references, not app code. They use absolute paths. Barlow Condensed was fetched into the session scratchpad and is not committed; it gets vendored during implementation.

All three are rendered from a synthetic v3 document:
- the fixture's people, firm, company and basis;
- real DPDPA and ISO requirement IDs;
- 120 requirements, 10 findings, 11 actions, 8 initiatives, prior period compared.

## 0. How we got here

1. **First pass:** a portrait A4 report with charts. Saqlain rejected it: readable, but too much empty space, too little colour, and no consultant-grade finish.
2. **Reference set:** photos Saqlain supplied of three Big-4 deliverables:
   - a regulatory IS compliance audit deck;
   - a cybersecurity gap assessment deck (HIPAA / ISO 27001 / NIST CSF);
   - the gap assessment's Excel workbook.
3. **What the references show:** both reports are **16:9 PowerPoint decks**, not documents. That is the main reason they feel finished:
   - one idea per slide;
   - a heavy title frame on every slide;
   - colour blocks and KPI tiles fill the page;
   - findings in a fixed 7-column grammar (No. / Domain / Observation / Risk / Rating / Recommendation / Reference);
   - remediation as initiatives on Short / Medium / Long horizons, rated on Priority, Complexity and Benefit, with responsibility markers;
   - a workbook that mirrors the deck: Executive Summary, Detailed Assessment, Observation Register, Remediation Tracker with initiative banner rows, Definitions.
4. **What we take:** structure and conventions only. No branding, wording, illustrations or client content.
5. **The photos stay local.** They show identifiable clients, and they are not committed.
6. **Where we beat them:** the reference drafts contradict themselves (requirement totals that differ between slides, a risk cell pasted from another row). Every number in ours comes from one document produced by the deterministic engine.

## 1. Decisions (Saqlain, 2026-10-01)

| # | Decision |
|---|---|
| F1 | **PDF = 16:9 landscape deck**, rendered by WeasyPrint (`@page 338.67mm × 190.5mm`). Replaces the portrait layout. |
| F2 | **PPTX replaces DOCX** as the editable format. It mirrors the PDF slide for slide, with native tables and charts (`python-pptx`, new dependency). DOCX from PR #92 stays only for v1/v2 sidecars. |
| F3 | **XLSX = client workbook** in the reference idiom (section 4). |
| F4 | **New consultant-entered data:** `Finding.business_impact` (the "Risk" column), `Finding.recommendation`, `Action.responsibility` (client / consultant / shared), initiative `complexity` and `benefit` (High/Medium/Low), optional board asks (≤3). |
| F5 | **Branding is the consulting firm's and configurable:** firm name, logo, primary, secondary and accent colours. Ships with a strong default theme, the indigo/royal/teal of the mockup. Severity and outcome colours are fixed and not themeable. |
| F6 | **PR #92: merge as-is, iterate after.** Its plumbing stays (routes, derive-from-sidecar, sanitiser, tests). Its DOCX/XLSX renderers become the frozen v2 path. |
| F7 | **P6-10 narrative** becomes the executive-summary verdict panel (exec sentences) and the per-framework narrative. It **folds into the same schema bump (v3)**. Its Finding refs render as R-xx. |
| F8 | **v1/v2 sidecars stay write-once.** Stored PDFs are never re-rendered. Exports branch on `schema_version`. |
| F9 | **SoA:** summary in the PDF (theme × implementation, plus excluded controls); all 93 rows in the XLSX. |
| F10 | **Numeric priority is gone from client output.** Initiative Priority (High/Medium/Low) is **derived** from the highest approved risk the initiative closes; it is never typed. |

## 2. Audience and job

| Format | Reader | Job |
|---|---|---|
| PDF deck, sections 01-04 | Board / CXO, and the consultant presenting | See posture per framework, the risks, the asks and the plan; approve the asks |
| PDF deck, 05 Annexure | Compliance lead, internal audit | Check every outcome, its evidence, and the SoA status |
| PPTX | Consultant | Edit wording and layout before presenting. Derived from the sidecar and labelled as such. |
| XLSX | Compliance lead and action owners | Track remediation, complete SoA justifications, filter registers. Returned to the consultant. |

## 3. PDF deck: slide by slide

**Frame on every content slide**
- A title banner (section-number wedge in primary, then secondary and accent slants), the title in a condensed display face, and a rule.
- A one-line **takeaway** under the title. It is computed in code or comes from the accepted narrative, never free LLM text.
- A footer with the firm wordmark, company, version, **assessment period, evidence cut-off**, "Confidential", and the page number.

**Fonts**
- Display: Barlow Condensed (OFL), to be vendored like Noto.
- Body: Noto Sans plus Devanagari.

**Colours**
- Severity: Critical `#9B1C1C`, High `#D9481E`, Medium `#F0A030`, Low `#3C9D6B`.
- Outcome: green, amber, red, grey, light grey.

**Charts:** SVG and CSS, from a pure presenter (`board_view.py`). No JavaScript, no images. **Length:** 25 slides at 120 requirements. The requirement register scales at about 21 rows per slide.

| # | Slide | Content and source (**new** = new data, *derived* = computed from the document) |
|---|---|---|
| 1 | Cover | <ul><li>Firm, "Draft until issued", engagement.</li><li>`company_name` in large type.</li><li>**Framework-conditional title**: "Privacy and information security…" only when `frameworks[].legal`.</li><li>Framework chips; period, cut-off, version, snapshot.</li><li>Abstract geometric art in theme colours (no photos).</li></ul> |
| 2 | Contents | 01-05 with descriptions and slide numbers |
| 3 | Assessment overview | <ul><li>Scope cards per framework (`summary.scope`, `coverage.in_scope`).</li><li>Period and cut-off tiles.</li><li>KPI strip: documents reviewed, requirements, key observations, initiatives, open RFIs.</li><li>3-step approach (static copy).</li><li>`basis_of_assessment`.</li></ul> |
| 4 | How to read the ratings | <ul><li>Outcome bands (pill and definition).</li><li>Risk-level boxes.</li><li>Remediation dimensions table (Priority derived; Complexity and Benefit with thresholds).</li><li>Horizons; responsibility markers.</li></ul> |
| 5 | Executive summary | <ul><li>**Verdict panel**: P6-10 `summary.narrative.executive` with R-refs.</li><li>Outcome donut (total requirements).</li><li>5 solid KPI tiles.</li><li>Black "Total requirements assessed" bar with the never-combined note.</li><li>One 100%-stacked outcome bar per framework, with that framework's score, rating and Δ (`prior_period`).</li><li>"Top three risks" strip.</li></ul> |
| 6 | Compliance status by domain | <ul><li>**Status board**: one column per framework with a dark header (score, rating, requirement count).</li><li>Domain rows: score bar, %, and a pill ("No gaps" / "n gaps · k crit/high"), or "Out of scope".</li><li>*Derived* `status_board` from the register.</li></ul> |
| 7 | Risk profile | <ul><li>2×2 severity panels: colour label, ring with count, "where they sit" bars by domain (*derived* `severity_dashboard`).</li><li>Donut of all gaps by risk.</li><li>Framework × risk table (*derived* `risk_matrix`).</li></ul> |
| 8 | Decisions for the board | <ul><li>Up to 3 large ask cards (**new** `board_asks.consultant`).</li><li>"Needs attention" panel: overdue / unowned / not-concluded tiles and *derived* asks.</li></ul> |
| 9-11 | Key observations (n/N) | <ul><li>The 7-column table, 4 rows per slide.</li><li>Columns: R-xx; domain with framework tag and responsibility marker; title and `description`; **new** `business_impact`; severity pill; **new** `recommendation`; Reference.</li><li>Reference is *derived*: own clause plus same-UCC-cluster clauses in in-scope frameworks.</li><li>Responsibility legend.</li></ul> |
| 12 | Remediation roadmap | <ul><li>Short (≤90 d) / Medium (91-180 d) / Long (>180 d) columns.</li><li>Current-state to target-state path.</li><li>Initiative callouts: I-n, title, R-refs, owner, date, responsibility marker, OVERDUE tag, "fixes once across X + Y".</li><li>The horizon is *derived* from target date vs `generated_at`.</li></ul> |
| 13 | Initiatives at a glance | <ul><li>Columns: ref, initiative (+ UCC topic), closes, horizon and date, owner, Priority / Complexity / Benefit glyphs, action status.</li><li>Initiative = today's `roadmap.groups` plus a **new** consultant title, complexity and benefit.</li></ul> |
| 14 | Since the last report | <ul><li>Per framework: prior vs current bars, a large Δ, and improved / regressed / new / unchanged tiles.</li><li>Changed-requirements table (`prior_period`).</li><li>Hidden when there is no prior.</li></ul> |
| 15 | What we could not assess | RFI table, not-concluded counts per framework, limitations (framework-conditional) |
| 16 | Sign-off | Prepared, reviewed, released, issue record (version history); version, snapshot, names note, confidentiality |
| 17 | Annexure divider | A1-A4 |
| 18 | A1 Methodology | `appendices.methodology`, two columns |
| 19-24 | A2 Requirement register (n/N) | Every requirement: outcome dot, risk, decision, evidence |
| 25 | A3 Evidence register + A4 SoA summary | Evidence table; theme × implementation counts and excluded controls (ISO only) |

## 4. XLSX: client workbook

**Sheets:** Executive Summary, Detailed Assessment, Observation Register, Remediation Tracker, Statement of Applicability, Evidence Register, Definitions.

**Workbook-wide formatting:**
- Coloured tabs by function, matching the reference.
- Every sheet has a title block: title, purpose, then firm | company | period | cut-off | version | draft.
- Navy headers with autofilter and frozen ID columns.
- Pastel fills: risk (Critical, High, Medium, Low), outcome, complexity and benefit.
- Teal headers with pale-yellow cells mark columns the client edits.
- The formula-injection guard stays.

**Sheet contents:**
- **Executive Summary:**
  - key-value block;
  - Section A: a per-framework posture table (score, rating, Δ pts, counts);
  - a KPI tile row;
  - Section B: native stacked bar chart of gaps by domain × risk;
  - Section C: outcome counts and % with a native pie.
- **Detailed Assessment:** every requirement, with outcome, risk rating, evidence cited, decision and **linked observation (R-xx)**.
- **Observation Register:** R-xx, domain, framework, observation, associated risk, rating, recommendation, reference, responsibility.
- **Remediation Tracker:**
  - a **navy banner row per initiative** (I-n, title, R-refs, horizon, Priority, Complexity, Benefit, cross-framework note);
  - one row per action (A-xx): source obs, domain, action, owner, responsibility, priority, horizon, target date, complexity, benefit;
  - a **Status** dropdown, plus Client update and Evidence of closure columns;
  - overdue dates and "Unassigned" turn red.
- **Statement of Applicability:** all 93 controls, an applicability dropdown, Justification as the editable column.
- **Evidence Register.**
- **Definitions:** every scale used.

**Traceability:** requirement → R-xx → I-n → A-xx, the same IDs in the deck and the workbook.

## 5. PPTX: editable deck

- The same slides and frame as the PDF, built from native shapes, native tables and native charts (doughnut, 100%-stacked bar), so consultants can edit everything.
- The theme colours come from firm settings. Title font is the theme display font, falling back to Arial Narrow; body is Calibri.
- The sample covers the cover, executive summary, key observations and initiatives. The full set mirrors section 3.
- It is derived from the sidecar on download, with the provenance in the slide notes: "derived from snapshot X, vN; edits do not change the report".

## 6. House rules: how the format keeps them

- **Approved only.** Every slide reads `build_document` output: approved Conclusions, Findings and Actions. The new inputs are consultant-entered, and none is LLM output.
- **Deterministic.**
  - Computed in code: scores, counts, risk matrix, status board, severity dashboard, horizons, Priority, overdue flags, derived asks, Reference clauses (UCC) and takeaways.
  - The only LLM text is the consultant-accepted P6-10 narrative, which cites closed-set refs.
- **No blended score.** Scores appear only per framework (status-board headers, per-framework bars, workbook Section A). Cross-framework totals are counts, labelled as such, with the "never combined" note on slide 5 and in the workbook.
- **Framework-conditional copy.** The cover title, limitations and SoA depend on `frameworks[].legal` and ISO in scope. The Reference column lists only in-scope frameworks.
- **Period and cut-off** are on the cover, in every slide footer, and in every sheet's title block.
- **Write-once:** see F8.

## 7. Implementation plan

**Owner split:**
1. A Claude design handoff (contract tests + golden first).
2. Codex implementation.
3. Adversarial review.

It runs as one feature, after #92 and P6-10 merge. Optionally split into two PRs: data, then presentation.

**Data: `board_report.build_document`, `DOCUMENT_SCHEMA_VERSION = 3` (shared with P6-10)**
- **Derived:**
  - `observations[]`: R-xx, domain, references via `remediation_groups.cluster_index`, responsibility;
  - `initiatives[]`: I-n from `roadmap.groups`, horizon, priority, overdue, actions with A-xx and obs refs;
  - `status_board[]`, `severity_dashboard`, `summary.risk_matrix`;
  - `roadmap.status_counts`, `roadmap.overdue_count`;
  - `takeaways{}`, `board_asks.derived`.
- **New stored fields:**
  - migration `findings.business_impact TEXT NULL` and `findings.recommendation TEXT NULL`;
  - `actions.responsibility VARCHAR NULL` (client / consultant / shared);
  - new `initiatives` metadata keyed by `(assessment_id, group_id)`: title, complexity, benefit;
  - `assessments.board_asks_json TEXT`;
  - all edits audited.
- **Removed:** numeric `priority` from `top_risks[]`, gaps and the register.
- **UI:**
  - Finding form: "Why it matters" and "Recommendation" textareas, plus responsibility on actions.
  - Roadmap page: initiative title, complexity and benefit per group.
  - Versions page: board asks.
- **Readiness:** missing new fields never block generation. Empty Risk or Recommendation cells render "Not recorded" in muted text.

**Presentation**
- `app/services/board_view.py`: a pure presenter (the prototype is `render_deck.view`) that does geometry, pagination and labels.
- Rewrite `app/templates/reports/board_report.html` to the deck. One `<section class="slide" data-slide="...">` per slide; `data-slide` names follow section 3.
- **Fonts:** vendor Barlow Condensed Bold and SemiBold with the OFL licence. Pin them by hash like the Noto fonts (`html_pdf.FONT_FILES`).
- **Theme:** `Settings.firm_logo_path`, `firm_color_primary`, `firm_color_secondary`, `firm_color_accent`, validated hex values, frozen into the sidecar as `theme{}` so an issued report keeps its look.
- `app/services/board_exports.py`: dispatch on `schema_version`.
  - v3: new XLSX (prototype `render_xlsx2.py`) and new PPTX (prototype `render_pptx.py`).
  - v≤2: the PR #92 renderers, frozen.
  - The DOCX route returns 410 for v3 documents and points to the PPTX.
- **Dependency:** `python-pptx`.

**Tests that change**
- `tests/test_p6_8_board_report_v2.py`:
  - schema → 3;
  - top-level keys (`observations`, `initiatives`, `status_board`, `severity_dashboard`, `takeaways`, `board_asks`, `theme`);
  - `data-section` → `data-slide` assertions;
  - priority text;
  - the fixture adds `business_impact`, `recommendation`, responsibility, initiative metadata and an ask.
- `tests/test_p6_9_roadmap.py`: the slice uses `data-slide="roadmap"`/`initiatives`.
- `tests/test_p6_9_soa.py`: the PDF asserts the summary and excluded rows, not 93 rows; the 93-row assertion moves to the XLSX test; schema → 3.
- `tests/test_p6_9_prior_period.py`: the legacy v2 fixture stays; the slide-order slice is renamed.
- `tests/test_p6_8_b2_docx_xlsx.py` (#92):
  - the v2 path is unchanged;
  - new v3 tests: sheet names and order, tracker banner rows, Status validation, the SoA's 93 rows, formula injection on the new text fields;
  - PPTX: slide count, native table and chart present, provenance in notes;
  - DOCX returns 410 for v3.
- P6-10b tests: verdict panel location; schema version.
- **Golden:** re-record `tests/golden/p6_8_board_document.json`.
- **New contract tests:**
  - framework-conditional cover title;
  - period and cut-off in every slide footer;
  - no combined score;
  - status-board and risk-matrix counts equal the register;
  - horizon boundaries (90/180 days; overdue only when not Done);
  - Priority is derived from max risk;
  - Reference lists only in-scope frameworks;
  - takeaways are deterministic;
  - theme colours are validated and frozen;
  - empty new fields render "Not recorded".

**Next handoff:** `tasks/handoffs/2026-10-0x-board-report-v3-deck.md`. It pins the v3 schema, the migrations, the contract tests above and the `D-P6-8-V3-*` decisions (F1-F10). Write it after #92 and P6-10 merge.

## 8. Open items for review

- **Tune the default theme against the reference** if Saqlain wants it closer. The status board and KPI tiles use the reference's dark-header and solid-tile treatment. The palette is our own.
- **Slide budget:** 25 slides at 120 requirements. The register is 6 of them. If that is too long, the alternative is to keep the full register in the XLSX only and show only gaps in the PDF annex.
