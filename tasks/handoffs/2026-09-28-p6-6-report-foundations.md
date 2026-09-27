# P6-6: Report foundations (period, cut-off, approval gate, D0 defects, sign-off) `[AR: report correctness]`

This task lays the foundations every later deliverable (P6-8 board report v2, P6-9, P6-10) builds on:

- **Assessment period and evidence cut-off** are recorded per Assessment, printed on every conclusion-bearing deliverable, and **required before any Conclusion can be approved** (D-P6-G).
- **A free-text sign-off block** (prepared by / reviewed by) until Track 4 brings real identities.
- **The D0 report defects** #1, #2, #4, #5, #6, #7, #9, #10 and #11 are fixed. #3 gets a cheap interim fix (₹); #8 is P6-0d.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`, Part D (D0 table) and Track 2 task P6-6. Relevant decisions: **D-P6-G** (period and cut-off required before approval, printed on every deliverable), **D-P6-H** (fpdf2 reports are frozen and retired at parity; so fixes here are minimal and additive), **D-P6-I** (no auth until Track 4, so sign-off names are free text). PRD invariant 4 and PR-012 / PR-050 / PR-053 (`docs/product/2026-09-21-cyberassess-product-requirements.md`). House rules: framework-specific copy is conditional, never a default; PDF sections are additive-only; all PDF text goes through `S()`; snapshots are write-once; scoring is deterministic and untouched; JSON lives in TEXT columns.
**Owner:** Claude designs (this file + contract tests) → Codex implements → Claude runs an adversarial review (`[AR: report correctness]`, checkpoints below) → PR. Per `tasks/agent-ownership.md`, Phase 6 row "P6-6..P6-10 Deliverables".
**Branch / worktree:** `claude/p6-6-report-foundations` in `/Users/saqlainmomin/dpdpa-gap-tool-p6-6`, from `origin/main` @ `f2e8284`. Local `main` == `origin/main` == `f2e8284`.
**Depends on:** P5-6 (snapshots, merged), P3-3 (findings in the PDF, merged). **Blocks:** P6-8 (board report v2 reuses the basis, the methodology text and the gate). **Runs in parallel with:** P6-4 (v2 judge). No shared files (D-P6-6-K).

> **The contract tests are already written. They are the contract.** `tests/test_p6_6_report_foundations.py` (18 tests) was written by the designer before implementation. On `f2e8284` 17 fail and 1 passes (scenario 17, the file-set guard, which must stay green). The 17 fail only for missing-code reasons: `ModuleNotFoundError` for `app.services.report_basis` / `app.utils.http_headers`, `AttributeError` for new `pdf_export` names, a 404 for the missing route, 200-instead-of-400 for the missing gate, and `'?250 Cr' == 'Rs.250 Cr'`. Make all 18 pass **without editing that file**. Do not weaken, skip, `xfail`, re-parametrize or delete any test. If you believe a test is wrong, leave it failing and explain in `## Results` which assertion, why, and what it should be. Extra tests go in `tests/test_p6_6_extra.py`.
>
> The designer checked the file against a throwaway reference implementation of this spec (not in the repo; implement from this spec, not from memory of it): all 18 passed four runs in a row; 13 targeted mutations each made at least one contract test fail (gate removed; coverage lines not wrapped; old appendix gaps count; period lock disabled; ISO treated as a legal regime; integrated methodology page dropped; ₹ mapping removed; one raw `Content-Disposition` left; heatmap never paginates; Workpaper basis line removed; all cover area bars drawn; sign-off page dropped; unlabelled render date). With the reference plus the existing-test edits in D-P6-6-L, the full suite was **943 passed, 10 skipped, 0 failed, 13 errors**; the 13 errors are all `tests/test_longitudinal_demo.py` and are caused only by the approval gate meeting a seed script you may not open (Open question 1). With the gate temporarily disabled those 13 pass.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, name, signature, message constant, audit action, route, form field and rendered string below.

> **Answer-key independence (D-P5-9-C).** This is report work, but the parallel P6-4 is analyzer work, so the rule applies in full. Do not open, grep, glob, list or read: anything under `validation/`; `tasks/handoffs/*p5-9*`; `docs/plans/2026-09-24-002-*`; `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`; `scripts/validation/**`; `tests/test_validation_harness.py`; any `answer_key.json`; `~/cyberassess-runs/**`. Scope every search to explicit paths (`grep -rn ... app/ tests/test_p6_6_*.py`), never a bare repo-root search.

> **Codex cannot write `.git`.** No `git add`, `commit`, `branch`, `stash`. Read-only git is fine and the guards use it. The orchestrator commits.

## Goal

1. A consultant records the assessment period (start, end) and the evidence cut-off, plus free-text "prepared by" / "reviewed by", on the Conclusions page. Every change is an append-only audit event.
2. Approve and edit-and-approve are refused until the period and cut-off are recorded. While any Conclusion is approved, the period and cut-off are locked.
3. The board PDF, the integrated PDF and the Workpaper print the period and cut-off (or "not recorded" for legacy data). The render date is always labelled "Report generated".
4. The listed D0 defects are fixed, each with the smallest change to the frozen fpdf2 layout.
5. Nothing changes in the analyzer, grounding, LLM, scoring, framework packs, schema or scripts.

## Step 0 (before writing code)

1. The worktree exists with `.venv` symlinked and `.env` present; `main` == `origin/main` == `f2e8284`.
2. Run `.venv/bin/pytest -q -p no:cacheprovider` and record counts in `## Results`. Before the designer's edits: **938 passed, 10 skipped, 0 failed**. With the designer's files in place (uncommitted): **938 passed, 10 skipped, 18 failed**: the 17 contract tests above plus `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes`, which fails whenever anything under `tests/` is uncommitted and goes green after the orchestrator commits.
3. Confirm these facts. **If any is false, stop and report.** Line numbers are from `f2e8284`.
   1. **D0 #1.** Nothing models a period or cut-off (`grep -rn "cut.off\|period_start" app/` finds only prose). `app/utils/pdf_export.py:1536` prints the literal `"Assessment period and evidence cut-off: not recorded"` in each integrated section; `app/services/report_content.py:40` defines `PERIOD_NOT_RECORDED = "not recorded"`.
   2. **D0 #2.** `pdf_export.py:793-797` prints `datetime.now()` unlabelled on the cover (`%B %d, %Y`); `:1264-1265` and `:1324` print it as `Assessment Date:` on the Scope & Limitations page; `:1482-1483` prints it unlabelled on the integrated cover.
   3. **D0 #3.** `pdf_export.py:78-82` `_UNICODE_MAP` and `:90-94` `S()` encode to Latin-1 with `errors="replace"`, so `₹` (U+20B9) and Devanagari become `?`.
   4. **D0 #4.** Cover `:842-848` prints `critical_count + high_count` as "gaps identified"; the appendix divider `:1180` prints `len(gap_items) - compliant` (which counts insufficient evidence and not applicable as gaps). Two different numbers for the same label.
   5. **D0 #5.** Methodology `:1363-1456`: "GRC Response Scale" / five-option questionnaire scale `:1425-1431`, "Maturity Model (CMMI-Aligned)" `:1445-1453`. Approved reports are scored only from approved Conclusions (`app/services/scoring.py:84` `approved_framework_scores`; `APPROVED_OUTCOME_POINTS`, `DENOMINATOR_EXCLUDED_OUTCOMES`; weights via `compute_framework_scores` `:616-676`; `RATING_THRESHOLDS` `:33-38`). Row priority is derived from the approved risk level (`app/services/approved_report.py:264-300`, `PRIORITY_BY_RISK`).
   6. **D0 #6.** `:1455-1456` disclaimer "consult qualified legal counsel" and `:1452` "best-in-class privacy practice" print for every framework set, including ISO/NIST-only.
   7. **D0 #7.** KPI card `:875-884` "Remediation Timeline (not estimated)" / "n/a" (approved rows always have `timeline_weeks=None`, `approved_report.py:296`). Roadmap `:1003-1050` draws fixed `PRIORITY_CONFIG` windows (`:69-75`: "0-4 weeks", "1-3 months", "3-6 months", "6-12 months") via `_draw_timeline_block` `:288-328`. Web: `app/routers/web.py:2041` `root_cause_counts = {}` (always empty), `:1956-1975` `_compute_root_cause_counts` and `:1894-1900` `_ROOT_CAUSE_LABELS` are dead, and `app/templates/partials/report_summary.html:374-393` is the permanently hidden "Why These Gaps Exist" block.
   8. **D0 #9.** `generate_integrated_pdf` `:1466-1600` has no Scope & Limitations, Methodology or Disclaimer page.
   9. **D0 #10.** `set_auto_page_break(auto=False)` (`:760`, `:1470`). Cover area bars `:850-858` start at y=202 and add 11 mm per domain (DPDPA+ISO+NIST = 16 domains runs to y≈378 on a 297 mm page). Heatmap `:952-956` adds 14 mm per domain with no page break, and `_draw_heatmap_row` `:456-464` draws one square per requirement in a single line (ISO "Organizational" has 37 → 265 mm wide). The per-framework coverage lines `:916-932` use `pdf.text` without wrapping and run past the right edge on **every** approved report (found while writing the tests).
   10. **D0 #11.** `app/routers/reports.py:222-228`, `app/routers/web.py:1118-1123` and `:1150-1155` build `Content-Disposition` as `f'attachment; filename="{filename}"'` from the raw company name (`"`, `;`, CR/LF and non-Latin-1 all pass through). `app/routers/snapshots.py:237-247, :324-331` and `integrated_reports.py:176-182` already sanitise; leave them.
   11. **Approval path.** The only code that writes a human decision is `app/services/conclusion_review.py:204` `decide(...)` (`ConclusionRevision(` appears only at `:253` and in `analysis_pipeline.py:421` for proposals). `analysis_pipeline.LOCKING_ACTIONS == ("approved", "edited")`. Routes: `app/routers/conclusions.py:71-150` (`approve`, `edit`, `reject`, `reopen`); `InvalidDecision` → 400 JSON `{"detail": message}` with an encoded toast. Cards: `conclusion_cards` `:361`, per-card blocker `:433`; `components/conclusion_card.html:127-129` disables Approve and shows `card.approval_blocker`.
   12. **Release** is stored as an `AuditEvent` (`action` release, `entity_type "assessment"`) and read as the latest event (`approved_report.py:189-202`). P6-6 stores the basis the same way (D-P6-6-A).
   13. **Snapshots** freeze rendered bytes and a sha256 (`report_snapshots.py:159-217`, `read_snapshot_bytes`). The gap-report snapshot renders through `reports._download_pdf_response` (`app/routers/snapshots.py:64-77`), the Workpaper snapshot renders `pages/workpaper.html` with `(assessment, wp)`.
   14. **`generate_pdf`'s signature is pinned** by `tests/test_p5_2_reader_migration.py:555-558` (`report, gap_items, company_name, initiatives, answer_source_map, selected_frameworks, assessment, report_findings`). Do not add parameters.
   15. `tests/test_pdf_updates.py:1068` forbids the case-sensitive tokens `Conclusion`, `AnalysisRun` and `analysis_pipeline` anywhere in `pdf_export.py` or `reports.py`. Lowercase "conclusion" is fine. `tests/test_pdf_updates.py:867` asserts the literal `not recorded` integrated line (edited under D-P6-6-L).
   16. `pdfplumber==0.11.6` is in `requirements.txt` (no `pypdf`); the tests read PDFs back with it.
   17. Alembic head is `8b2d5f7e1c34`, pinned in ten existing test files. P6-6 adds no migration (D-P6-6-A).

## Decisions (made here so they are not relitigated)

### D-P6-6-A: Storage is an append-only audit trail, not new columns (no migration)

The basis lives in `audit_events` rows with `action="assessment.report_basis_updated"`, `entity_type="assessment"`, `entity_id=<assessment id>`, `metadata_json={"before": {...}, "after": {...}}` (`sort_keys=True`). The current basis is the latest event's `"after"`, ordered by `created_at DESC, rowid DESC` (the release-event pattern, fact 12). Why: no migration (the head is pinned in ten test files and P6-4 may add one), full change history for free, and no `Assessment` model change (which breaks the suites that build pinned-revision databases). No change to `app/models/**`, `alembic/**` or `report_snapshots.py`; scenario 17 enforces this.

### D-P6-6-B: `app/services/report_basis.py` (new)

```python
PERIOD_REQUIRED_MESSAGE = "Record the assessment period and evidence cut-off before approving conclusions."
PERIOD_LOCKED_MESSAGE = ("The assessment period and evidence cut-off are locked while any conclusion is "
                         "approved. Reopen the approved conclusions to change them.")
PERIOD_INCOMPLETE_MESSAGE = "Enter the period start, period end and evidence cut-off together, or leave all three blank."
PERIOD_ORDER_MESSAGE = "The assessment period must end on or after its start date."
CUTOFF_ORDER_MESSAGE = "The evidence cut-off must be on or after the start of the assessment period."
DATE_FORMAT_MESSAGE = "Dates must be in YYYY-MM-DD format."
NOT_RECORDED = "not recorded"
SIGN_OFF_MAX_CHARS = 200
DISPLAY_DATE_FORMAT = "%d %b %Y"            # "01 Apr 2026"
AUDIT_ENTITY_TYPE = "assessment"
AUDIT_ACTION = "assessment.report_basis_updated"

class ReportBasisError(Exception):          # status_code = 400; .message
@dataclass(frozen=True)
class ReportBasis:
    period_start: date | None; period_end: date | None; evidence_cutoff: date | None
    prepared_by: str | None; reviewed_by: str | None
    period_recorded -> bool                 # property: all three dates set
    period_label -> str                     # "01 Apr 2026 to 30 Jun 2026" or "not recorded"
    cutoff_label -> str                     # "15 Jul 2026" or "not recorded"
    to_metadata() -> dict                   # ISO dates / None, names / None; exactly these five keys
EMPTY_BASIS = ReportBasis(None, None, None, None, None)

def current_basis(db: Session | None, assessment) -> ReportBasis
def basis_for(assessment) -> ReportBasis
def approval_blocker(db: Session, assessment) -> str | None
def period_locked(db: Session, assessment) -> bool
def parse_date(value: str | None) -> date | None
def update_report_basis(db, assessment, *, period_start, period_end, evidence_cutoff,
                        prepared_by, reviewed_by, actor: str) -> ReportBasis
```

- `current_basis`: `EMPTY_BASIS` when `db` or `assessment` is `None` or has no id, when there is no event, or when the latest event's metadata is not JSON, has no dict `"after"`, or holds an unparseable date. Never raises for bad data.
- `basis_for(assessment)`: `current_basis(sqlalchemy.orm.object_session(assessment), assessment)`; `EMPTY_BASIS` for `None` or an unmapped object (`UnmappedInstanceError`). Renderers use this because `generate_pdf`'s signature is pinned (fact 14) and templates only get `assessment`.
- `approval_blocker`: `None` when `current_basis(...).period_recorded`, else `PERIOD_REQUIRED_MESSAGE`.
- `period_locked`: `True` when any Conclusion of the assessment is locked per `analysis_pipeline.load_conclusion_state(...)` (latest human action in `LOCKING_ACTIONS`), across every `framework_id` present on its Conclusions. Import `analysis_pipeline` inside the function (avoids an import cycle).
- `parse_date`: blank/whitespace → `None`; otherwise `date.fromisoformat`; failure → `ReportBasisError(DATE_FORMAT_MESSAGE)`.
- `update_report_basis`, in this order:
  1. Some but not all three dates → `PERIOD_INCOMPLETE_MESSAGE`. `period_end < period_start` → `PERIOD_ORDER_MESSAGE`. `evidence_cutoff < period_start` → `CUTOFF_ORDER_MESSAGE`. (A cut-off after the period end is normal; one inside the period is allowed.)
  2. Names are cleaned: whitespace runs collapsed to one space, stripped, truncated to 200 characters, empty → `None`.
  3. If the new basis equals `current_basis`, return it and write nothing.
  4. If any of the three dates differs from the current basis and `period_locked(...)`, raise `PERIOD_LOCKED_MESSAGE`. Sign-off-only changes are always allowed.
  5. Add one `AuditEvent(actor=actor, action=AUDIT_ACTION, entity_type="assessment", entity_id=assessment.id, metadata_json=json.dumps({"before": before.to_metadata(), "after": after.to_metadata()}, sort_keys=True))`, `db.flush()`, return `after`. The caller commits.

Clearing (all three blank) is allowed while unlocked.

### D-P6-6-C: The approval gate (D-P6-G) and its state model

States are derived, never stored:

| Basis state | How | Approve / Edit | Reject / Reopen | Change dates | Change sign-off |
|---|---|---|---|---|---|
| not recorded | no event, or latest event has a blank date | **refused** (`PERIOD_REQUIRED_MESSAGE`) | allowed | allowed | allowed |
| recorded, unlocked | dates set, no locked Conclusion | allowed | allowed | allowed | allowed |
| recorded, locked | dates set, ≥1 Conclusion approved/edited | allowed | allowed | **refused** (`PERIOD_LOCKED_MESSAGE`) | allowed |

To change a locked period: reopen every approved Conclusion (release goes stale, as today), change the dates, re-approve, re-release.

Code in `conclusion_review.py`, nothing else:
- In `decide`, immediately after the `ALLOWED_ACTIONS` check and before `latest_proposal = _latest_proposal(revisions)`:
  ```python
  if action in analysis_pipeline.LOCKING_ACTIONS:
      period_blocker = report_basis.approval_blocker(db, db.get(Assessment, conclusion.assessment_id))
      if period_blocker:
          raise InvalidDecision(period_blocker)
  ```
  No revision is written and the version does not change (the existing route rolls back on `InvalidDecision`).
- In `conclusion_cards`, compute `period_blocker = report_basis.approval_blocker(db, assessment)` once (after `titles = ...`) and use `blocker = period_blocker or _approval_blocker(_content(conclusion), latest_proposal)`. The card template already disables Approve and shows the message; do not edit `conclusion_card.html`.
- Import: `from app.services import analysis_pipeline, report_basis`.

Release gets **no** new blocker: new approvals cannot happen without a period, and legacy assessments approved before P6-6 still release and print "not recorded" (D-P6-6-E). Scoring, release, findings and snapshot semantics are unchanged.

### D-P6-6-D: Route and UI

`app/routers/review.py` gains `POST /api/assessments/{assessment_id}/report-basis` (form fields, all `Form("")`): `period_start`, `period_end`, `evidence_cutoff` (ISO `YYYY-MM-DD`), `prepared_by`, `reviewed_by`, `reviewer_name`. Actor is `conclusion_review.reviewer_actor(reviewer_name)`.
- Unknown assessment → `db.rollback()`, 404 `{"detail": "Assessment not found"}`.
- `ReportBasisError` (including `parse_date`) → `db.rollback()`, 400 `{"detail": message}`, headers `X-Toast-Message: quote(message)`, `X-Toast-Type: error`.
- Success → `db.commit()`, 200 `{"status": "saved", **basis.to_metadata()}`, headers `HX-Redirect: /assessments/{id}/conclusions`, `X-Toast-Message: Assessment period and sign-off saved`, `X-Toast-Type: success`.

New partial `app/templates/partials/report_basis_panel.html`, included in `pages/conclusions.html` directly above `{% include "partials/release_panel.html" %}`:
- `<section data-report-basis-panel data-period-recorded="yes|no" data-period-locked="yes|no" ...>` with heading "Assessment period and sign-off" and the sentence "The period and evidence cut-off are required before any conclusion can be approved, and are printed on every report." plus, when locked, " They are locked while any conclusion is approved; reopen approved conclusions to change them."
- `<form data-report-basis-form hx-post="/api/assessments/{{ assessment.id }}/report-basis" hx-include="#reviewer-name" hx-swap="none">` with three `type="date"` inputs (named as the form fields, `readonly` when locked, values `isoformat()` or empty), two text inputs (`maxlength="200"`) and a Save button. Same Tailwind classes as `release_panel.html`.
- `conclusions_page` in `web.py` adds `"report_basis": report_basis.current_basis(db, assessment)` and `"period_locked": report_basis.period_locked(db, assessment)` to its context (the context that already holds `"reviewer_name"`), and imports `report_basis` in the existing `from app.services import approved_report, conclusion_review` line.

### D-P6-6-E: Where the basis renders, page by page (board PDF, `generate_pdf`)

`basis = basis_for(assessment)` and `generated = datetime.now(timezone.utc)` once, near the top (replacing the `max_weeks` computation). Legacy or unrecorded data prints "not recorded", never a guessed date. Page order is unchanged except one new last page.

| Page | Change |
|---|---|
| 1 Cover | Replace the unlabelled date (`:793-797`) with two lines in the navy band: y=46.5, font 9: `Assessment period: {period_label}  \|  Evidence cut-off: {cutoff_label}`; y=52, font 8: `Report generated: {generated:%d %b %Y}`. Summary line (`:839-848`, D0 #4/#7): `{total} requirements assessed  \|  {gap_count} gaps identified ({critical_count + high_count} critical or high)` (no weeks). Area bars (D0 #10): if `len(chapter_scores) <= COVER_AREA_ROWS` draw all; else draw the first `COVER_AREA_ROWS - 1` and then, italic 8 at `bar_y + 4`, `+{n} more assessment areas on the Executive Dashboard`. |
| 2 Executive Dashboard | Third KPI card (D0 #7): value `str(counts.get("insufficient_evidence", 0))`, label `Insufficient Evidence`, accent `STATUS_COLORS["insufficient_evidence"]`. Coverage lines (D0 #10): `multi_cell(CW, 4, ...)` from `(PM, framework_bar_y - 3)`, then `framework_bar_y = pdf.get_y() + 4` (both the scored and not-scored variants). Heatmap (D0 #10): before each row, if `hm_y + heatmap_row_height(len(items)) > CONTENT_BOTTOM`, footer + new page with header `Executive Dashboard (continued)`; `hm_y += _draw_heatmap_row(...)` (it now returns its height). Before "Key Findings", if `hm_y + 8 > CONTENT_BOTTOM - 45`, same page break. |
| 3 Critical & High | Unchanged. |
| 4 Remediation Roadmap | D0 #7: keep the page header "Remediation Roadmap"; section title becomes `Remediation Actions`; the P1-P4 timeline is removed. See D-P6-6-H. |
| Initiatives | Unchanged (never rendered: `initiatives=None`). |
| Appendix divider | D0 #4: `{total} requirements  \|  {gap_count} gaps identified`. |
| Appendix, findings | Unchanged. |
| Scope & Limitations | D0 #2/#5/#6: the first block becomes three lines `Assessment period: …`, `Evidence cut-off: …`, `Report generated: …` (`_basis_lines`), replacing `Assessment Date:`. "Nature of Assessment" body becomes `_nature_text(selected_frameworks)`; "Recommended Follow-On Actions" becomes `_follow_on_text(selected_frameworks)`. Scope of coverage, what is not covered, reliance, confidentiality and the readiness note are unchanged (the readiness note keeps using the render date: it is about commencement relative to today). |
| Methodology | D0 #5/#6: the whole body becomes `methodology_text(selected_frameworks, len(gap_items))`. |
| **Report Sign-off (new, last page)** | `_render_sign_off_page(pdf, company_name, basis, generated)`: header and title `Report Sign-off`; lines `Prepared by: {prepared_by or 'not recorded'}`, `Reviewed by: {reviewed_by or 'not recorded'}`, the three `_basis_lines`, a blank line, `This version is a draft until it is issued. The issued version, and who issued it, are recorded in the report version history.`, `Names are recorded as entered by the consultant; they are not verified sign-ins.` Font 9, `multi_cell(CW, 5, text=S(line))`. |

Workpaper (`pages/workpaper.html`), after the "Read-only. …" paragraph:
```html
{% set basis = report_basis_for(assessment) %}
<p data-report-basis class="mt-1 text-sm text-gray-600 dark:text-gray-300">Assessment period: {{ basis.period_label }} · Evidence cut-off: {{ basis.cutoff_label }}</p>
```
`app/template_config.py` `configure_templates` registers `templates.env.globals["report_basis_for"] = basis_for` (import inside the function). This also reaches Workpaper snapshots, because `snapshots.py` configures its templates the same way.

RFI and evidence-checklist exports are evidence requests, not conclusion-bearing deliverables; they do not print the basis in P6-6 (P6-8 may add it).

### D-P6-6-F: New module-level names and text helpers in `pdf_export.py`

```python
from app.services.report_basis import EMPTY_BASIS, basis_for
from app.services.scoring import RATING_THRESHOLDS, is_failed_framework_score, report_framework_scores

"₹": "Rs.",                         # added to _UNICODE_MAP (D-P6-6-J)
GAP_STATUSES = ("non_compliant", "partially_compliant")
LEGAL_FRAMEWORK_IDS = frozenset({"dpdpa", "gdpr", "hipaa"})   # statutes/regulations; everything else is a standard
COVER_AREA_ROWS = 7
HEATMAP_SQUARES_PER_LINE = 17
CONTENT_BOTTOM = 270

def heatmap_row_height(item_count: int) -> float:   # max(14.0, ceil(n / 17) * 5.5 + 3); 1 line min
def count_gaps(gap_items) -> int:                   # rows whose compliance_status is in GAP_STATUSES
def _framework_label(framework_ids) -> str          # registry names joined by ", " (unknown id → upper())
def _regimes(framework_ids) -> tuple[list[str], list[str]]   # (legal, standards), order kept, de-duplicated
def _basis_lines(basis, generated) -> list[str]     # the three "Assessment period / Evidence cut-off / Report generated" lines
def _render_sign_off_page(pdf, company_name, basis, generated)
```

`_draw_heatmap_row` wraps squares: square `i` at `x + 62 + (i % 17) * 5.5`, `y + (i // 17) * 5.5` (4.5 mm squares, 1 mm gap), and returns `heatmap_row_height(len(items))`. Label, score and rating positions are unchanged. `_draw_timeline_block` is deleted (orphaned by D-P6-6-H); `PRIORITY_CONFIG` stays (the initiatives block uses it).

The copy helpers, verbatim (the tests pin phrases from them; the golden hash is re-recorded from your output):

```python
def _nature_text(framework_ids) -> str:
    legal, _standards = _regimes(framework_ids)
    status = (
        "It is not a formal compliance audit and does not constitute legal advice."
        if legal
        else "It is not a formal compliance or certification audit."
    )
    return (
        "This document constitutes an evidence-based compliance gap assessment. "
        f"{status} Findings are based on documents submitted for review and information "
        "disclosed by the organization's representatives, and every conclusion was "
        "individually approved by a consultant. These conclusions reflect the evidence considered "
        "up to the evidence cut-off stated above."
    )


def _follow_on_text(framework_ids) -> str:
    legal, standards = _regimes(framework_ids)
    lead = (
        "For requirements rated as Non-Compliant or Partially Compliant at a Critical or High "
        "risk level, independent verification by "
    )
    if legal and standards:
        return (
            f"{lead}qualified legal counsel or a certified privacy professional (for "
            f"{_framework_label(legal)} requirements), or by a qualified information security "
            f"auditor (for {_framework_label(standards)}), is strongly recommended before relying "
            "on those findings for regulatory submissions, board reporting, or contractual "
            "representations."
        )
    if legal:
        return (
            f"{lead}qualified legal counsel or a certified privacy professional is strongly "
            "recommended before relying on those findings for regulatory submissions, board "
            "reporting, or contractual representations."
        )
    return (
        f"{lead}a qualified information security auditor is strongly recommended before "
        "relying on those findings for certification, board reporting, or contractual "
        "representations."
    )


def _risk_basis(framework_ids) -> str:
    legal, standards = _regimes(framework_ids)
    legal_basis = (
        f"regulatory exposure, potential penalties under {_framework_label(legal)} and impact "
        "on affected individuals"
    )
    security_basis = (
        "likely impact on the confidentiality, integrity and availability of information"
    )
    if legal and standards:
        return (
            f"{legal_basis} (for {_framework_label(legal)}), and {security_basis} "
            f"(for {_framework_label(standards)})"
        )
    return legal_basis if legal else security_basis


def _disclaimer_text(framework_ids) -> str:
    legal, standards = _regimes(framework_ids)
    parts = []
    if legal:
        parts.append(
            "This assessment provides guidance based on the information and evidence provided "
            "and is not legal advice. Consult qualified legal counsel for definitive compliance "
            f"determinations under {_framework_label(legal)}."
        )
    if standards:
        parts.append(
            ("For " if legal else "This assessment provides guidance based on the information "
             "and evidence provided. For ")
            + f"{_framework_label(standards)}, it is not a certification audit; certification "
            "decisions rest with an accredited certification body or qualified assessor."
        )
    return " ".join(parts)


def _framework_structure_text(framework_ids) -> str:
    lines = []
    for framework_id in dict.fromkeys(framework_ids):
        framework = FrameworkRegistry.get_or_none(framework_id)
        if framework is None:
            continue
        domains = framework.as_legacy_framework_dict()
        weights = ", ".join(
            f"{domain['title']} {round(domain['weight'] * 100)}%"
            for domain in domains.values()
        )
        lines.append(
            f"- {framework.name} ({framework.version}): {framework.control_count()} "
            f"requirements in {len(domains)} domains. Domain weights: {weights}."
        )
    return "\n".join(lines)


def methodology_text(framework_ids, requirement_count: int | None) -> str:
    """Framework-correct methodology for approved-conclusion reports (P6-6, D0 #5/#6)."""
    count_clause = (
        f", across {requirement_count} in-scope requirements"
        if requirement_count is not None
        else ""
    )
    thresholds = []
    upper = 100
    for threshold, rating in RATING_THRESHOLDS:
        thresholds.append(f"- {threshold}-{upper}%: {rating}")
        upper = threshold - 1
    return f"""This assessment evaluates compliance against the following framework(s): {_framework_label(framework_ids)}{count_clause}.

Basis of Assessment:
Each in-scope requirement receives one conclusion. The analysis engine reviews the submitted documents and questionnaire responses and proposes an outcome with cited evidence. A consultant reviews the evidence and individually approves, edits or rejects every proposal. Only individually approved conclusions appear in this report; no outcome, score or finding is produced by the AI on its own.

Outcome Definitions:
- Compliant: the requirement is met and supported by evidence
- Partially Compliant: the requirement is met in part
- Non-Compliant: the requirement is not met
- Insufficient Evidence: the evidence provided does not support a conclusion either way
- Not Applicable: the requirement does not apply within the assessed scope

Scoring Basis:
Scores are computed only from conclusions a consultant has individually approved. Each approved outcome counts as follows: Compliant 100 points, Partially Compliant 50 points, Non-Compliant 0 points. Not Applicable and Insufficient Evidence are excluded from the scoring denominator. Insufficient Evidence is not treated as Non-Compliant; the number of requirements with insufficient evidence is reported next to each framework score. Requirements excluded at scoping are not scored. A framework is scored only when every in-scope requirement has an approved conclusion. Section scores are the average of their requirement points; domain and framework scores are weighted averages using the published weights below.

Framework Structure and Weights:
{_framework_structure_text(framework_ids)}
Requirements are referenced by clause or control identifier for each selected framework; requirement descriptions are summarised for assessment purposes and do not reproduce the source standard. Scores are computed and reported independently for each framework; no score is combined across frameworks.

Rating Thresholds:
{chr(10).join(thresholds)}

Risk Classification:
Each gap carries the risk level (Critical, High, Medium, Low) approved by the consultant, reflecting {_risk_basis(framework_ids)}. Remediation priority on each gap is derived from its approved risk level.

Disclaimer:
{_disclaimer_text(framework_ids)}"""
```

`methodology_text` must never contain the case-sensitive token `Conclusion` (fact 15); "Outcome Definitions" is deliberate.

### D-P6-6-G: Framework-conditional copy (D0 #6)

`LEGAL_FRAMEWORK_IDS` decides every legal-vs-standard sentence: DPDPA, GDPR and HIPAA get legal-counsel wording; ISO 27001, NIST CSF and PCI-DSS get auditor/certification wording; mixed sets get both, each naming its frameworks. An all-standards report must contain none of: `dpdpa`, `digital personal data protection`, `data principal`, `data fiduciary`, `schedule to the`, `legal counsel`, `legal advice`, `privacy practice`, `privacy professional`, `cmmi`, `maturity model` (case-insensitive; scenarios 8, 9, 11b). Existing conditional copy (`dpdpa_only` scope text, the DPDPA readiness note) is unchanged.

### D-P6-6-H: Roadmap from real Actions (D0 #7)

- Rows: every `(finding, action)` for `finding in report_findings.findings` (empty when `report_findings is None`), sorted by `(target_date is None, target_date, severity rank critical<high<medium<low)`.
- Intro (8.5 pt, `MID_TEXT`): `Actions recorded against approved findings, ordered by target date. Owners and dates are set by the consultant; nothing on this page is estimated.`
- Per row: bold 8.5 pt `action.title`; then `Owner: {owner or 'Unassigned'}  |  Target: {target_date:%d %b %Y or 'No target date'}  |  {status_label}`; then `Closes: {finding.framework_name} {finding.requirement_id} - {finding.title}`; `ln(2)`. Page break with header `Remediation Roadmap (continued)` when `get_y() > CONTENT_BOTTOM - 16`.
- No rows: `No remediation actions are recorded for the approved findings yet.`
- Then, if `unplanned > 0` (gap rows, per `GAP_STATUSES`, whose `(framework_id or "dpdpa", requirement_id)` has no finding in `report_findings`), italic: `{unplanned} identified gap(s) have no approved finding with an action yet.`
- Cross-framework "closes N findings" grouping is P6-9 (an Action belongs to one Finding today).
- Web: delete `_ROOT_CAUSE_LABELS`, `_compute_root_cause_counts`, the `root_cause_counts = {}` line and its context key in `web.py`, and the "F. Root Cause Breakdown" block (from its comment to just before "G. Detailed Findings") in `report_summary.html`. The API `remediation_roadmap` priority buckets in `reports.get_report` are out of scope.

### D-P6-6-I: Integrated PDF (D0 #1, #2, #9)

- Cover: `Report generated: {report_as_of:%d %b %Y}` replaces the bare date.
- **New page right after the cover** (before the sections, so each section's label stays last-mentioned in its own section, which `tests/test_pdf_updates.py` scenario 5 relies on): header/title `Scope & Limitations`; one line per section `{label}: {framework names}; assessment period {period_label}; evidence cut-off {cutoff_label}; {scope_label}.`; then `Report generated: …`, `Nature of Assessment:` + `_nature_text(ids)`, `What Is Not Covered:` (the board PDF's non-DPDPA-only sentence without the physical-controls clause), `Recommended Follow-On Actions:` + `_follow_on_text(ids)`, `Confidentiality:` (first two sentences of the board text). `ids` = union of section framework ids in order.
- Each section's scope lines: when `basis.period_recorded`, `Assessment period: …` and `Evidence cut-off: …`; otherwise keep the exact legacy line `Assessment period and evidence cut-off: not recorded`. Then always `Prepared by: {… or 'not recorded'}  |  Reviewed by: {… or 'not recorded'}`.
- **New last page** (after "Assessments Not Included"): header `Methodology`, title `Assessment Methodology`, body `methodology_text(ids, None)` (the integrated report has no single in-scope count).
- `report_content.IntegratedSection` gains two trailing defaulted fields: `framework_ids: tuple[str, ...] = ()` and `basis: ReportBasis | None = None`, filled with `tuple(assessment.frameworks)` and `current_basis(db, assessment)`. The renderer reads them with `getattr(section, "framework_ids", ())` / `getattr(section, "basis", None) or EMPTY_BASIS`, because `tests/test_p6_0e_dpdpa_pack_correctness.py` renders a `SimpleNamespace` section.

### D-P6-6-J: D0 #3 (Latin-1): interim `₹ → Rs.`, Devanagari deferred to P6-8

Add `"₹": "Rs."` to `_UNICODE_MAP`. Devanagari needs a Unicode TTF, which is exactly what P6-8's WeasyPrint + Noto move provides (D-P6-H); bundling a font into the frozen fpdf2 reports is not worth it. Devanagari still renders as `?` until P6-8, and no code path crashes on it (scenario 14).

### D-P6-6-K: File set; P6-4 shares nothing

P6-6 touches exactly:

| Path | Change |
|---|---|
| `app/services/report_basis.py` (new) | B |
| `app/services/conclusion_review.py` | C (gate in `decide`, blocker in `conclusion_cards`, import) |
| `app/services/report_content.py` | I (two section fields + import) |
| `app/routers/review.py` | D (route + import) |
| `app/routers/reports.py` | `attachment_disposition` (M) |
| `app/routers/web.py` | D (context), H (dead code), M (two headers) |
| `app/utils/pdf_export.py` | E, F, G, H, I, J |
| `app/utils/http_headers.py` (new) | M |
| `app/template_config.py` | E (`report_basis_for` global) |
| `app/templates/pages/conclusions.html`, `pages/workpaper.html` | D, E |
| `app/templates/partials/report_basis_panel.html` (new), `partials/report_summary.html` | D, H |
| `tests/fixtures/canonical_dpdpa/expected/pdf_text.sha256`, `pdf_meta.json` | L (re-record) |
| seven existing test files + two assertions | L |
| `tasks/handoffs/2026-09-28-p6-6-report-foundations.md` | append `## Results` only |

P6-4 touches `claude_analyzer.py`, `app/services/grounding/`, `desk_review_v2.py`, `llm_client.py`, `app/config.py` and possibly upload limits (`routers/documents.py`, `document_processor.py`). None overlap; scenario 17 fails if P6-6 touches any of them or `desk_review.py`, `scoring.py`, `analysis_pipeline.py`, `app/dpdpa`, `app/frameworks`, `report_snapshots.py`, `app/models`, `alembic` or `scripts`. **No migration, no model change**, so no merge-order rule with P6-4 is needed for schema. The only shared surface is test guards: both PRs may add `:(exclude)` lines to `tests/test_p6_3a_grounding.py` and `tests/test_p6_nist_csf2_alignment.py`; whichever merges second merges `origin/main` into its branch and keeps both sides (text conflict only; the repo rejects force-pushes, never rebase).

### D-P6-6-L: Existing tests that must change (the complete list)

The designer already applied the guard excludes (bottom of this section). Codex applies the rest, exactly as described, and nothing else in existing tests:

1. **Seed a period where suites approve Conclusions.** In each of these files, in the module-level `_seed(...)` only, directly after the `db.add(assessment)` + `db.flush()` that creates the assessment, add `record_test_period(db, assessment)  # P6-6: D-P6-G approval gate`, and add `from tests.report_period_helper import record_test_period` just above `import app.models`:
   `tests/test_conclusion_approval.py`, `tests/test_findings.py`, `tests/test_remediation_tracking.py`, `tests/test_workpaper.py`, `tests/test_pdf_updates.py`, `tests/test_report_snapshots.py`, `tests/test_p5_6_rfi_rebuild.py`. In `test_p5_6_rfi_rebuild.py` `_seed` ends `db.add(assessment); db.commit()`: insert `db.flush()` and the call between them. The helper (`tests/report_period_helper.py`, already written; kept out of `tests/support/` so the fixture guards stay untouched) goes through the real service, so the gate is never bypassed.
2. `tests/test_pdf_updates.py:867`: replace the `not recorded` assertion with `assert "Assessment period: 01 Jan 2026 to 31 Mar 2026" in text_value` and `assert "Evidence cut-off: 15 Apr 2026" in text_value`, with a one-line `# P6-6 (D0 #1)` comment.
3. `tests/test_p5_2_reader_migration.py:551`: `assert "Remediation Timeline" not in text_value  # P6-6 (D0 #7): card replaced by Insufficient Evidence`.
4. Re-record the golden PDF: run `tests/test_golden_dpdpa.py`'s `_pdf_bytes` / `_extract_pdf` and write the new text sha256 to `tests/fixtures/canonical_dpdpa/expected/pdf_text.sha256` and `"page_count": 17` (one new sign-off page) to `pdf_meta.json`; keep `byte_length_lower_bound`. The designer's reference produced `143a321b086129062edd70c199abadcf59bab17cd1dbb66f0f7eb717681ada9d` / 46,311 bytes; yours matches only if every string is identical. Report old → new in `## Results`. No other fixture changes.
5. `tests/test_longitudinal_demo.py`: see Open question 1. Do not edit it and do not open the seed script.

Guard excludes already applied by the designer (per-PR `:(exclude)` lines naming P6-6; nothing deleted or broadened):
- `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_13_structural_guards`: `app/routers/reports.py`, `app/utils/pdf_export.py`, `app/routers/review.py`.
- `tests/test_p6_3a_grounding.py` `PROTECTED_PATHS`: `app/routers/{reports,review,web}.py`, `app/templates/pages/{conclusions,workpaper}.html`, `app/templates/partials/{report_basis_panel,report_summary}.html`, the two golden files.
- `tests/test_p6_nist_csf2_alignment.py::test_protected_surface_guard_uses_three_dot_diff`: `app/services/{report_basis,conclusion_review,report_content}.py`, `app/routers/{reports,review,web}.py`, the two golden files.
- `tests/test_p6_1_llm_plumbing.py::test_golden_surfaces_and_harness_wrapper` and `tests/test_p6_1b_framework_batching.py::test_protected_surface_guard_uses_three_dot_diff`: the two golden files.

### D-P6-6-M: `Content-Disposition` (D0 #11)

New `app/utils/http_headers.py`:
```python
def attachment_disposition(filename: str) -> str:
    cleaned = "".join(ch for ch in filename if ch.isprintable())            # drops CR, LF, other controls
    fallback = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned).strip("_") or "download"
    encoded = urllib.parse.quote(cleaned or fallback, safe="")
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{encoded}"
```
Use it in `reports.py` (`_download_pdf_response`) and both evidence-checklist routes in `web.py`, keeping the existing `filename` expressions. The already-sanitised snapshot/integrated/RFI downloads are unchanged.

### D-P6-6-N: Snapshot immutability

Snapshots already freeze the rendered bytes and hash; the basis is inside the bytes (cover, scope page, sign-off page; Workpaper header). Changing the basis later requires reopening (D-P6-6-C), and the old version's bytes, hash and text stay exactly as generated (scenario 15). No new snapshot metadata key: `generated_event` metadata keys are pinned by `tests/test_report_snapshots.py`, and the audit trail (D-P6-6-A) already records every basis change with timestamps.

## Do not touch

- The contract test file `tests/test_p6_6_report_foundations.py`, the helper `tests/report_period_helper.py`, and the five designer-edited guard files beyond what is already there.
- `app/services/{claude_analyzer,desk_review,desk_review_v2,llm_client,analysis_pipeline,scoring,report_snapshots,document_processor,evidence,citations}.py`, `app/services/grounding/**`, `app/config.py`, `app/dpdpa/**`, `app/frameworks/**`, `app/models/**`, `app/schemas/**`, `alembic/**`, `scripts/**` (including `scripts/validation/**`), `app/routers/{snapshots,integrated_reports,conclusions,documents,analysis}.py`, `app/templates/components/**`.
- Existing PDF page layouts beyond the changes listed in D-P6-6-E/H/I. Do not reorder pages, rename existing section titles other than "Implementation Timeline" → "Remediation Actions", or restyle anything.
- Every other existing test file and fixture.
- `validation/**` and everything in the independence list.

If you find you need to change any of these, stop and report.

## Non-goals

- The D0 #8 penalty table (P6-0d). Devanagari fonts, WeasyPrint, DOCX/XLSX, standalone Workpaper (P6-8). Statement of Applicability, cross-framework roadmap, prior-period comparison (P6-9). Real user identities in sign-off (Track 4 / P6-11).
- Basis on the RFI or evidence checklist. A release blocker for missing periods. Filtering evidence by cut-off date (the cut-off is the consultant's recorded basis; the tool does not check document dates against it).
- Fixing other unwrapped fpdf2 lines not named here.

## Test scenarios (all in `tests/test_p6_6_report_foundations.py`)

The suite uses an Alembic-`head` SQLite database per test, the real FastAPI app through `TestClient`, and the real analysis route with both analyzer seams faked; an autouse fixture makes any `llm_client.call_llm` call fail. PDFs are read back with `pdfplumber`.

| # | Test | Covers |
|---|---|---|
| 1 | `test_scenario_1_basis_is_an_append_only_audit_trail` | A: no new columns, alembic head unchanged, two updates = two events with before/after, latest wins, `basis_for` uses the object's session, malformed latest event → `EMPTY_BASIS` |
| 2 | `test_scenario_2_report_basis_service_rules` | B: three validation messages (exact text), nothing written on error, name cleaning and 200 cap, labels, audit metadata shape, no-op save writes nothing, clearing |
| 3 | `test_scenario_3_route_saves_and_rejects` | D: bad date 400 + error toast, unknown assessment 404, success JSON / HX-Redirect / success toast, actor from `reviewer_name` |
| 4 | `test_scenario_4_approval_gate_blocks_approve_and_edit` | C: approve and edit → 400 `PERIOD_REQUIRED_MESSAGE`, no revision, version unchanged; service raises `InvalidDecision`; reject allowed; card blocker; panel rendered on the Conclusions page; after saving the period approval succeeds |
| 5 | `test_scenario_5_period_locks_while_any_conclusion_is_approved` | C: date change and clearing refused while approved; sign-off change allowed; `data-period-locked="yes"`; reopen unlocks |
| 6 | `test_scenario_6_board_pdf_prints_period_cutoff_and_labelled_render_date` | D0 #1/#2: cover and scope page carry period, cut-off and `Report generated`; no `Assessment Date`, no bare `%B %d, %Y`; legacy report prints `not recorded` |
| 7 | `test_scenario_7_single_consistent_gaps_count` | D0 #4: non + partial + compliant + insufficient + N/A → every "N gaps identified" is 2; `count_gaps`, `GAP_STATUSES` |
| 8 | `test_scenario_8_methodology_is_framework_correct` | D0 #5: no questionnaire scale / CMMI / maturity / "questionnaire-based"; approved basis, outcome definitions, real domain weights |
| 9 | `test_scenario_9_framework_conditional_copy` | D0 #6: ISO-only board PDF has none of the forbidden phrases and has the auditor/certification wording; DPDPA+ISO has both; methodology for NIST, PCI, ISO+NIST is clean |
| 10 | `test_scenario_10_kpi_roadmap_and_dead_web_section` | D0 #7: no timeline KPI or P1-P4 windows; "Insufficient Evidence" KPI; roadmap lists the real action, owner, date and closes-line before the appendix, plus the unplanned count; dead root-cause helper and template block removed |
| 11 | `test_scenario_11_integrated_pdf_period_scope_methodology_disclaimer` | D0 #1/#2/#9: integrated cover date label; section period, cut-off, sign-off; Scope & Limitations and Methodology/Disclaimer pages |
| 11b | `test_scenario_11b_iso_only_integrated_pdf_has_no_legal_copy` | D0 #6/#9 on the integrated report |
| 12 | `test_scenario_12_many_domains_stay_on_the_page` | D0 #10: DPDPA+ISO+NIST (16 domains, a 37-square ISO row): every char and rect inside the page, no body text over the footer, cover "+N more" note |
| 13 | `test_scenario_13_content_disposition_is_escaped` | D0 #11: helper output shape and round-trip; the three routes with a hostile company name (quote, `;`, CR/LF, non-Latin-1) |
| 14 | `test_scenario_14_sign_off_block_through_sanitiser` | Sign-off page content, `S()` maps em dash and ₹, Devanagari does not crash, the renderer uses `text=S(` |
| 15 | `test_scenario_15_snapshot_captures_basis_immutably` | N: gap-report and Workpaper snapshots contain the basis; after reopen → change → re-approve → re-release, the old version's bytes/hash/text are unchanged and the new version shows the new basis; no snapshot metadata key |
| 16 | `test_scenario_16_workpaper_page_shows_basis` | E: live Workpaper header, recorded and not recorded |
| 17 | `test_scenario_17_p6_6_shares_no_files_with_p6_4` | K: committed and working-tree diffs over the P6-4 / protected paths are empty (green before and after) |

## Verification (before reporting done)

1. `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_6_report_foundations.py` → **18 passed**, file unmodified.
2. Parity and neighbours, all green: `.venv/bin/pytest -q -p no:cacheprovider tests/test_pdf_updates.py tests/test_p5_2_reader_migration.py tests/test_conclusion_approval.py tests/test_findings.py tests/test_remediation_tracking.py tests/test_workpaper.py tests/test_report_snapshots.py tests/test_p5_6_rfi_rebuild.py tests/test_golden_dpdpa.py tests/test_p6_0e_dpdpa_pack_correctness.py tests/test_no_blended_scoring.py tests/test_white_label.py`.
3. `git diff --stat main -- app/models alembic app/services/scoring.py app/services/report_snapshots.py app/services/claude_analyzer.py app/services/grounding app/services/llm_client.py app/config.py scripts app/dpdpa app/frameworks` is empty. `grep -n "Conclusion\|AnalysisRun\|analysis_pipeline" app/utils/pdf_export.py app/routers/reports.py` finds nothing.
4. Full suite `.venv/bin/pytest -q -p no:cacheprovider`. Expected: everything green except `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes` (uncommitted `tests/`) and, until Open question 1 is resolved, the 13 `tests/test_longitudinal_demo.py` errors (`RuntimeError: approve …: expected 200, got 400: {"detail":"Record the assessment period…"}`). Any other failure: list it and why.
5. **Smoke (read the PDFs back).** Run `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_6_report_foundations.py -k "scenario_6 or scenario_7 or scenario_9 or scenario_11 or scenario_12" -v`. These generate, through the real routes and with no LLM, a DPDPA board PDF, a DPDPA+ISO board PDF, an ISO-only board PDF, a DPDPA+ISO integrated snapshot, an ISO-only integrated snapshot and a 16-domain board PDF, and assert on the `pdfplumber` text: period and cut-off on the cover and scope page, one gaps count, no DPDPA or legal copy in the ISO-only reports, nothing off-page. Paste the pass lines into `## Results`. The orchestrator may additionally download a real board and integrated PDF from the running app for an already-analysed assessment and read them back with `pdfplumber` (`"\n".join(page.extract_text() or "" for page in pdfplumber.open(path).pages)`); Codex does not run analysis against a live LLM.
6. When the orchestrator launches Codex with `codex exec`, stdin must be redirected: `codex exec ... < /dev/null`.

## Adversarial review checkpoints `[AR: report correctness]` (after Codex, before the PR)

1. **Gate completeness.** Is `decide` the only path that can create an approved/edited revision? Can a Conclusion be approved with no period by any route, including edit-and-approve, a stale form, or a race between clearing the period and approving (both in one transaction? what does the lock check see)?
2. **Lock.** Can the period change while any Conclusion is locked, via the route or the service? Does reopening the last approved Conclusion unlock it and nothing earlier?
3. **Audit trail.** Is every change one event with correct before/after? Does a malformed or foreign event ever render a guessed date? Is ordering deterministic for same-timestamp events?
4. **Rendering.** Every new string through `S()`; no `pdf.text` without `S()` on user data; no text off-page or over the footer at 16 domains; page order unchanged except the new last page and the integrated scope/methodology pages.
5. **Conditional copy.** Walk each framework set (each single framework, DPDPA+ISO, ISO+NIST, all six): any legal wording for standards-only, any standards wording missing, any DPDPA name outside a DPDPA report?
6. **One gaps number.** Cover, appendix and roadmap unplanned count use `GAP_STATUSES`.
7. **Immutability.** Old snapshot bytes never re-render; no snapshot metadata changed.
8. **Headers.** Any remaining download that builds `Content-Disposition` from raw user text.
9. **File set and independence.** Diff matches D-P6-6-K exactly; nothing under `validation/`, `scripts/`, grounding, analyzer, LLM, scoring, models or alembic.

## Open questions for Saqlain

1. **Blocking: the longitudinal demo seed approves without a period.** `tests/test_longitudinal_demo.py` (13 tests) seeds through `scripts/seed_test_companies.py`, which approves Conclusions over HTTP and now gets the gate's 400. The designer could not look inside that file (independence list). With the gate temporarily disabled all 13 pass, so the gate is the only cause. The fix is a few lines in the seed's longitudinal-demo path: record a period (`POST /api/assessments/{id}/report-basis`, or `report_basis.update_report_basis`) for each demo assessment before its first approval. **Recommended:** authorise that one narrow edit, made by the P6-6 Codex run (whose context never feeds P6-4) or by you, limited to the longitudinal-demo function. Alternative: have `tests/test_longitudinal_demo.py` monkeypatch the gate off for the demo only; not recommended, because it hides the invariant in the one end-to-end demo.
2. **Cut-off rule.** The cut-off must be on or after the period start, and may fall inside the period or after it. Say if you want "on or after the period end".

### Answers (Saqlain, 2026-09-27)

1. **Authorised:** the P6-6 Codex run makes the one narrow edit in `scripts/seed_test_companies.py`. In the longitudinal-demo path only, it records a report basis for each demo assessment before that assessment's first approval, using the real service or route. Nothing else in that file changes. Scenario 17 now excludes exactly that file. The P6-6 Codex run may open `scripts/seed_test_companies.py`, but still no other file on the independence list.
2. **Cut-off rule:** keep "on or after the period start".

## Self-review (designer, before dispatch)

1. **Columns vs audit events.** The first reference added five `Assessment` columns and a migration; the full suite then broke in ten files that pin the Alembic head or build pinned-revision databases, and P6-4 could add a competing head. The audit-event design (release already uses it) removed all of that and adds history.
2. **Snapshot metadata.** A `report_basis` key in generated-event metadata broke the exact-keys assertion in `test_report_snapshots.py` and added nothing the frozen bytes and the audit trail do not already give. Dropped.
3. **Integrated page placement.** Scope & Limitations at the end broke `test_pdf_updates` scenario 5's section-label ordering; it now sits after the cover, which is also where D2 puts scope.
4. **`Conclusion` token.** `test_pdf_updates.py:1068` bans it in `pdf_export.py`; the methodology heading is "Outcome Definitions" and the nature text uses lowercase.
5. **Helper location.** `tests/support/` is guarded by three suites; the helper lives at `tests/report_period_helper.py`.
6. **A pre-existing overflow found by the tests.** The dashboard coverage lines ran off the right edge on every report, not only wide ones. Fixed under D0 #10.
7. **Test speed and network.** The first draft stubbed only one analyzer seam and made real calls on ISO-only runs; the suite now fakes both seams and refuses any `call_llm`. It runs in about 7 s.

## Results

- Implemented P6-6 within D-P6-6-K, plus the authorised longitudinal-demo-only seed edit and D-P6-6-L test/fixture updates. No commits or `.git` writes were made.
- Contract tests: `18 passed`. Golden DPDPA tests: `8 passed`. P6-6 smoke subset: `6 passed`. Required parity suite: `181 passed`.
- Longitudinal demo: `12 passed, 1 failed`; all functional scenarios pass. Scenario 13 reports the two allowlisted modified files (`app/routers/web.py`, `app/services/report_content.py`) as uncommitted, which cannot be resolved without committing or changing the protected test.
- Full suite: `954 passed, 10 skipped, 2 failed`. The second failure is the expected retention guard while the authorised existing test/fixture edits are uncommitted; the longitudinal protected-surface failure is described above.
- Canonical DPDPA PDF fixture re-recorded: page count `16 -> 17`, text SHA-256 `b0420ce4697a6859c0a3b86794cd66f0905afae3b65208a43745451c599c8ac2 -> c6b1139b70029aecde63b3c2e419737e27c413d9c24e3b20026a6bb9cdf16e02`.
- Baseline before implementation was `939 passed, 10 skipped, 17 failed`; the count differs from the historical handoff estimate because the committed designer files keep the retention guard clean.
