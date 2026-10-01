# Re-evaluate the board report deliverables and finalize the target format

## Goal

Saqlain is **not convinced by how the client board report looks or by the data it contains**. That covers the PDF and its two derived exports, DOCX and XLSX. Before anything further is built on it, re-evaluate:
- **what** data the board report presents;
- **how** it presents that data, in each of the three formats.

Then agree on one **target format** with Saqlain.

This is a design and decision session, not an implementation session. It is the "one design pass before exposure" from Saqlain's two-pass rule (`~/.claude/CLAUDE.md`).

**Done when** all three exist:
1. **The decision doc.** `docs/product/2026-10-01-board-report-format.md` (or a name Saqlain picks) is written and **Saqlain has approved it in chat**. It defines, per format (PDF, DOCX, XLSX):
   - the audience and the job each reader does with it;
   - each section or sheet in order: keep, change, cut or add, with the reason and the exact document field it comes from (or "new data needed");
   - layout and visual rules: length target, tables vs prose, charts if any, what goes on page 1.
2. **A rendered mockup of the agreed format.** HTML is fine; it is not wired into the app. It must use realistic synthetic data from the existing test fixture, and Saqlain must have looked at it. Put it in the session scratchpad, or publish it as a private Artifact for review.
3. **A short implementation plan**, appended to the decision doc:
   - what changes in `board_report.build_document` (a schema bump?), the template, and `board_exports.py`;
   - which existing contract tests and the golden must change;
   - the decisions on PR #92 and P6-10 (see Constraints).

## Current state (as of 2026-10-01)

### The board report pipeline (on `main`)

- **Generation.** `board_report.build_document(...)` builds a canonical JSON "document" from **approved** Conclusions, Findings and Actions only.
  - It is rendered to PDF via Jinja2 → WeasyPrint (Noto fonts; Devanagari and ₹ work).
  - It is stored write-once as `{sid}.pdf` + `{sid}.json`, with the JSON's SHA-256 in an audit event.
  - The PDF and the JSON sidecar are the immutable record.
- **Document schema v2** (since P6-9, PR #86) has these top-level keys:
  - `snapshot`, `company_name`, `firm_name`, `engagement_name`, `frameworks[]` (incl. `pack_version`), `basis`, `release`;
  - `summary`: basis of assessment, scope, limitations, confidentiality, per-framework score/rating/headline/coverage/`narrative` (null until P6-10), totals;
  - `top_risks` (max 10);
  - `roadmap` (`actions`, plus `groups` by Unified Control Cluster);
  - `not_assessed` (insufficient evidence, RFI items);
  - `framework_sections` (domains, gaps);
  - `prior_period` (comparison with the last issued report of an earlier period);
  - `sign_off`;
  - `appendices` (methodology text, requirement register, evidence register);
  - `soa` (ISO 27001 Statement of Applicability, 93 Annex A rows, only when ISO is in scope);
  - `source`.
- **PDF section order:** cover → management summary → top risks → remediation roadmap (grouped) → what we could not assess → one section per framework → prior-period comparison → sign-off → Appendix A methodology → B requirement register → C evidence register → D SoA.
- A **web preview** of the same template exists, so you can iterate without generating versions: `GET /api/assessments/{id}/board-report/preview`, linked from the versions page.

### DOCX/XLSX exports: PR #92, open and not merged

[PR #92](https://github.com/saqlainmmomin/Cyber/pull/92), branch `claude/p6-8-b2-docx-xlsx`.
- The DOCX mirrors the PDF section by section.
- The XLSX has these sheets: About, Framework summary, Requirement register, Top risks, Action tracker (with "Client update"/"Evidence of closure" columns), Evidence register, plus conditional "Prior-period changes" and "Statement of Applicability".
- Everything is derived from the sidecar only, rendered on request and never stored.
- 12 contract tests; the full suite was green (1,224 passed).

### Samples Saqlain reviewed and was not convinced by

`~/Downloads/board.pdf`, `~/Downloads/board.docx`, `~/Downloads/board.xlsx`.
- They were generated from the test fixture: a released DPDPA + ISO 27001 assessment, a Devanagari company name, two Findings with Actions, and one SoA justification.
- The fixture is thin (five requirements in scope). Part of the "not convinced" may be thin data rather than format. **Separate those two questions explicitly.**

### What the plan intended

`docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md` (on `main`):
- Part D, section D2, gives the intended board report content (target 10-15 pages + appendices).
- D3 covers the formats; D4 covers the rendering stack.
- Use it as the baseline being re-evaluated, not as settled truth.

### Pending work that depends on this decision

- **P6-10 (Finding-grounded narrative)** is designed on the unmerged branch `claude/p6-10-narrative`. It fills `summary.frameworks[].narrative` and bumps the schema to v3.

## Key files

The primary checkout `/Users/saqlainmomin/dpdpa-gap-tool` is on an old branch (`codex/p5-9a-validation-harness`) with uncommitted files, so **do not switch it**. Work in a fresh worktree from `origin/main`:

```bash
git -C /Users/saqlainmomin/dpdpa-gap-tool worktree add ../cyberassess-report-format -b claude/report-format-review origin/main
```

Symlink `.venv` and copy `.env` from the primary checkout. Paths below are relative to that worktree.

| Path | What it is |
|---|---|
| `app/services/board_report.py` | `build_document`: every field the report can show, and where it comes from |
| `app/templates/reports/board_report.html` | the PDF/preview template (all copy and layout) |
| `app/services/board_exports.py` (PR #92 branch only) | the DOCX/XLSX renderers |
| `app/services/soa.py`, `remediation_groups.py`, `prior_period.py` | P6-9 data for the SoA, grouped roadmap and comparison |
| `tests/golden/p6_8_board_document.json` | a full real example of the v2 document (best quick read of the data) |
| `tests/test_p6_8_board_report_v2.py` | B1 contract and fixture (`_engagement_fixture`) to generate samples |
| `tasks/handoffs/2026-09-28-p6-8-board-report-v2.md` | B1 design (schema, decisions D-P6-8-*) |
| `tasks/handoffs/2026-09-28-p6-9-soa-roadmap-comparison.md` | P6-9 design (schema v2) |
| `tasks/handoffs/2026-09-28-p6-8-b2-docx-xlsx.md` (PR #92 branch) | B2 design, decisions D-P6-8-B2-A..K, results |
| `docs/product/2026-09-21-cyberassess-product-requirements.md` | PRD: invariants and report requirements (PR-0xx ids) |
| `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md` | Phase 6 plan, Part D = deliverables |
| `.claude/launch.json` | dev server config `cyberassess` (port 8001) for the browser preview |

## Constraints (decided; do not relitigate without Saqlain)

- **House rules stay:**
  - only approved Conclusions/Findings reach client outputs;
  - scores, risk and priority are deterministic, never an LLM;
  - no score is combined across frameworks;
  - framework-specific copy is conditional (an ISO-only report has no DPDPA or legal wording);
  - report versions are write-once, and the sidecar is the record;
  - assessment period and evidence cut-off are on every deliverable.
- **Rendering stack:** WeasyPrint HTML→PDF stays. The old fpdf2 PDFs are frozen; do not touch `app/utils/pdf_export.py`.
- **Exports are derived from the stored document only.** They never read live data, and they are re-rendered on download (D-P6-8-B2-K). Formula-injection protection in XLSX stays.
- **Answer-key isolation:** never open `validation/**`, `answer_key.json` or `scripts/validation/**` (see the CLAUDE.md gotcha).
- **No LLM spend** in this session unless Saqlain asks.
- **This session decides; it does not implement in `app/`.** Mockups live in the scratchpad or an Artifact. Implementation goes later to a Claude design handoff plus Codex, the usual flow (`tasks/agent-ownership.md`).
- **Ask Saqlain** with focused questions (2-3 alternatives each) on the open choices below; don't pick silently. Useful framing questions:
  - Who reads each format: the board, the client's compliance lead, or the consultant?
  - What decision does each reader make with it?
  - What does a competitor's or Big-4 deliverable look like that he'd want to match?
  - What specifically felt wrong: look, length, missing data, wrong data, wording?
- **Decide explicitly, as part of the plan:**
  1. **PR #92.** Merge as-is and iterate, hold until the format is final, or close and redesign B2?
  2. **P6-10's narrative.** Where does it sit in the new format, and does it still bump the schema separately or fold into the new format's schema bump?
  3. **Schema v1/v2 sidecars.** Whether already-generated report versions keep their old layout. The default is yes: write-once.
- Don't commit to `main`. Commit the decision doc on `claude/report-format-review`. Saqlain pushes and merges; pushes are blocked for agents in auto mode, so hand him the commands.
- **No Claude attribution** (`Co-Authored-By` or "Generated with Claude Code") in commits or PRs in this repo.

## Verification

Before reporting done:
1. Render the **current** report for review from a richer sample than the thin fixture if possible. Use synthetic data only: generate it via the test fixture pattern, or seed a local assessment through the app. Show Saqlain the current state next to the mockup. Use the browser preview (`preview_start` with name `cyberassess`, then the `/board-report/preview` route) or WeasyPrint output.
2. The mockup renders without errors, uses only fields that exist or are listed as "new data needed", and follows the house rules above. Check: no blended score, conditional framework copy, period and cut-off present.
3. Saqlain has explicitly approved the decision doc and the mockup in chat. Quote his approval in Results.
4. `git status` in the worktree shows only the decision doc (plus this handoff's Results) changed. Nothing in `app/` or `tests/`.

## Report back

Append a `## Results` section to this file (`tasks/handoffs/2026-10-01-report-format-reevaluation.md` in the primary checkout, or copy it into the worktree and commit it there), covering:
- the decision doc path and the mockup location;
- Saqlain's approval (quoted);
- the PR #92 / P6-10 / schema decisions;
- the next handoff to write: the implementation design.

## Results

**Status:** done 2026-10-01. Decision doc and mockups approved.

**Decision doc:** `docs/product/2026-10-01-board-report-format.md`. It records decisions F1-F10, a slide-by-slide and sheet-by-sheet spec with source fields, how the format keeps the house rules, and the implementation plan.

**Mockups and prototypes:** `docs/product/2026-10-01-board-report-mockup/`, all from synthetic data:
- `board-deck-PROPOSED.pdf`: 25-slide 16:9 deck.
- `board-workbook-PROPOSED.xlsx`
- `board-deck-sample.pptx`: 4 editable slides.
- `board-report-CURRENT-rich-data.pdf`: the current template on the same data.
- The generator scripts.

**Saqlain's approval (quoted):** "this looks good for now lets open a pr and get main in sync with local."

**How we got there:**
1. **Round 1:** a portrait A4 redesign with charts. Rejected: "a lot of empty spaces … lacks overall color, feel, and like a finish". The Excel "lacked formatting of any kind".
2. **Reference set:** Saqlain supplied photos of three Big-4 deliverables: a compliance-audit deck, a cyber gap-assessment deck and its Excel workbook. No maturity report was in the set.
3. **What a subagent catalogue of the photos found:** both reports are 16:9 PowerPoint decks. The idiom is:
   - a title-banner frame on every slide;
   - solid KPI tiles and donuts;
   - a per-regulation domain status board;
   - a 7-column observations table with a clause Reference column;
   - Short / Medium / Long initiatives rated on Priority, Complexity and Benefit, with responsibility markers;
   - a workbook with initiative banner rows in the remediation tracker.
4. **Round 2** rebuilt all three formats in that idiom. We took structure only: no branding, wording or imagery. The photos are not committed.

**What round 1 confirmed:** on rich synthetic data (120 requirements), the current v2 template runs to 35 pages and has the same problems as on the thin fixture. Two of them are data defects, not thin-data artefacts:
- numeric priority conflicts between sections;
- out-of-scope domains print "Not applicable".

The rest are format defects.

**Decisions:**
- **PR #92:** merge as-is, iterate after (F6). Its DOCX/XLSX renderers become the frozen path for v1/v2 sidecars.
- **P6-10:** the narrative becomes the executive-summary verdict panel plus the per-framework narrative. It folds into the same schema bump, v3 (F7).
- **Schema v1/v2 sidecars:** write-once. Stored PDFs are never re-rendered, and exports branch on `schema_version` (F8).
- **Also decided:**
  - 16:9 deck PDF (F1);
  - PPTX replaces DOCX (F2);
  - new consultant fields: business impact, recommendation, responsibility, initiative complexity and benefit, board asks (F4);
  - firm-configurable theme (F5);
  - SoA summary in the PDF, all 93 rows in the XLSX (F9);
  - numeric priority dropped, initiative Priority derived (F10).

**Verification:**
- The mockup PDFs render without errors.
- The deck has the assessment period and evidence cut-off in every slide footer, checked on slides 2-25. The cover carries them in its meta strip.
- There is no combined score anywhere.
- The cover title is framework-conditional.
- The XLSX and PPTX could not be previewed (no Office or LibreOffice on this host). Saqlain to open them in Excel and PowerPoint.

**Deviation from the verification checklist:** besides the decision doc and this handoff, the commit adds `docs/product/2026-10-01-board-report-mockup/`, the design references the implementation handoff needs. Nothing changes in `app/` or `tests/`.

**Next handoff:** `tasks/handoffs/2026-10-0x-board-report-v3-deck.md`, the implementation design. It pins the v3 schema, the migrations, theme settings, font vendoring, the `board_view.py` presenter, the PPTX and XLSX renderers, and the contract tests in section 7 of the decision doc. Write it after #92 and P6-10 merge.
