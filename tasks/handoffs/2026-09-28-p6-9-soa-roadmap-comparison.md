# P6-9: Statement of Applicability, cross-framework roadmap, prior-period comparison in the board report `[AR: report correctness + write-once]`

P6-9 adds three sections to the board report v2 document and PDF shipped by P6-8 B1:

- an **ISO 27001 Statement of Applicability** (Appendix D), when ISO is in scope, with a consultant-editable justification per Annex A control;
- a **cross-framework remediation roadmap**: Actions grouped by UCC cluster, so one remediation shows every Finding it addresses across frameworks;
- a **prior-period comparison** against the previous issued board report in the same engagement, read from its stored, hash-checked JSON sidecar.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`: Track 2 P6-9, Part C item 4 (cross-framework remediation view) and item 6 (SoA justification as an auditor check), Part D D2 items 4, 7 and 9, and "Out of scope" (the ISO clauses 4-10 pack stays deferred; the SoA covers the most-requested ISO artefact). Related decisions: **D-P6-D** (criteria changes bump the pack version), **D-P6-G** (period and cut-off on every deliverable), **D-P6-H** (WeasyPrint report; fpdf2 frozen). P6-8 B1 handoff: `tasks/handoffs/2026-09-28-p6-8-board-report-v2.md` (D-P6-8-D document schema, D-P6-8-F "what of D2 lands in P6-9", D-P6-8-J golden re-record rule). House rules: only approved Conclusions feed client outputs; risk, priority, scores and ordering are deterministic, never an LLM; framework-specific copy is conditional; report sections are additive; snapshots are write-once.
**Owner:** Claude designs (this file + contract tests) → Codex implements → Claude runs an adversarial review (`[AR]`, checkpoints below) → PR. Per `tasks/agent-ownership.md`, Phase 6 row "P6-6..P6-10 Deliverables".
**Branch:** `claude/p6-9-soa-roadmap`, from `origin/main` @ `4f5309d` (after #78, #79, #80, #81). The designer's commit sits on top of it. **Implementation:** branch `claude/p6-9-impl`, the design branch with `origin/main` @ `879c174` (#83) merged in.
**Depends on:** P6-8 B1 (merged #80), P6-6 (merged #73), P3-4 Findings/Actions (merged). **Runs in parallel with the designs of:** P6-8 B2 (DOCX/XLSX), P6-7b (add to RFI), P6-10 (narrative). See "Files touched and overlap".

> **The contract tests are already written. They are the contract.** 17 tests in four files:
> - `tests/test_p6_9_soa.py` (5), `tests/test_p6_9_roadmap.py` (5), `tests/test_p6_9_prior_period.py` (6), `tests/test_p6_9_file_set.py` (1, the scope guard)
> - shared fixtures in `tests/p6_9_support.py` (kept at `tests/` root, like `tests/report_period_helper.py`, so the `tests/support` and `tests/fixtures` guards stay untouched)
>
> On `4f5309d` plus the designer's commit, **16 fail and 1 passes** (the scope guard). The 16 fail only because code is missing: `ModuleNotFoundError` for `app.services.soa`, `app.services.remediation_groups` or `app.services.prior_period`, or, in the document tests, a `KeyError` or an assertion on the schema-v2 keys (`soa`, `prior_period`, `roadmap.groups`, `DOCUMENT_SCHEMA_VERSION == 2`). Make all 17 pass **without editing those files**. Do not weaken, skip, `xfail`, re-parametrize or delete any test. If you believe a test is wrong, leave it failing and explain in `## Results` which assertion, why, and what it should be. Put extra tests in `tests/test_p6_9_extra.py`.
>
> The designer checked the tests against a throwaway reference implementation of this spec (not in the repo; implement from this spec, not from memory of it). With the reference, the P6-8 test edits in D-P6-9-L and the golden re-recorded: all 17 passed, the P6-8 suite passed (14), and the full suite was **1135 passed, 10 skipped, 0 failed** once committed.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, and to every name, signature, constant, route, audit action, document key and rendered string below.

> **Answer-key independence (D-P5-9-C).** Do not open, grep, glob, list or read: anything under `validation/`; `tasks/handoffs/*p5-9*`; `docs/plans/2026-09-24-002-*`; `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`, `scripts/validation/**`; `tests/test_validation_harness.py`; any `answer_key.json`. Scope every search to explicit paths (`grep -rn ... app/ tests/test_p6_9_*.py`), never a bare repo-root search.

> **Codex cannot write `.git` and has no network.** No `git add`, `commit`, `branch`, `stash`. Read-only git is fine and the guards use it. Nothing needs installing: WeasyPrint 70.0 and the Noto fonts are already in place from P6-8 B1. The P6-9 tests stub the PDF renderer where they generate versions, so they do not need WeasyPrint.

## Goal

1. **SoA.** When ISO 27001 is in scope, the board report document carries `soa` and the PDF ends with "Appendix D: Statement of Applicability": one row per Annex A control (93), its applicability, its implementation status derived from the approved Conclusion, and the consultant's justification. A consultant records justifications on a new page; every change is an append-only audit event.
2. **Roadmap.** `roadmap.groups` groups the Actions of approved Findings by UCC cluster. Each group names the Findings it addresses across frameworks ("Addresses 3 findings across India DPDPA, ISO 27001 and NIST CSF"). The PDF roadmap renders the groups.
3. **Prior period.** `prior_period` compares this report with the last issued board report of the previous assessment period in the same engagement, read only from that version's stored sidecar. Per framework only; no combined score.
4. **No migration, no model change, no LLM, no change to `report_snapshots.py` or the snapshots router.** Alembic head stays `8b2d5f7e1c34`.

## Split decision (D-P6-9-A): one PR

All three pieces write into the same four places: `board_report.build_document`, `reports/board_report.html`, `DOCUMENT_SCHEMA_VERSION` and the P6-8 golden `tests/golden/p6_8_board_document.json`. Three PRs would mean three schema bumps, three golden re-records reviewed hunk by hunk, and three rounds of the same text conflicts, for about 700 lines of code in total. So P6-9 is **one PR**. The pieces are still separated by module (`soa.py`, `remediation_groups.py`, `prior_period.py`), so a reviewer can read them independently.

## Step 0 (before writing code)

1. `git branch -f main origin/main` (the guards diff `main...HEAD`), then run `.venv/bin/pytest -q -p no:cacheprovider` and record the counts in `## Results`. Expect exactly the 16 P6-9 contract failures above; everything else green.
2. Confirm these facts. **If any is false, stop and report.** Line numbers are from `4f5309d`.
   1. `app/services/board_report.py`: `DOCUMENT_SCHEMA_VERSION = 1`; `build_document(db, assessment, *, snapshot_id, version_label, generated_at)` builds `approved = approved_report.build_approved_report(...)` and `findings = report_content.assessment_findings(...).findings`; the `roadmap` dict has exactly `actions` and `unplanned_gap_count`; `frameworks[]` entries have `framework_id, name, version, legal`.
   2. `app/services/report_snapshots.py`: `read_board_report_document(db, snapshot)` hash-checks the sidecar and raises `SnapshotIntegrityError`; `generated_event(db, snapshot_id)` returns the generated metadata with `document_sha256`; `rfi_document_path(snapshot)` is the sidecar path; `BOARD_REPORT_SNAPSHOT_TYPE == "board_report"`; `create_board_report_snapshot(...)` and `issue_snapshot(...)` exist. P6-9 **reads** these and changes nothing in the module.
   3. `app/frameworks/mappings/clusters.py` `CONTROL_CLUSTERS`: 52 clusters, 409 member controls, **no control in two clusters** (roadmap scenario 1 pins this). `CLUSTER_006` "Access Control Baseline" contains `dpdpa:CH2.SECURITY.1`, `iso27001:ISO.A5.15`, `nist_csf:NIST.PR.AA.05`.
   4. `app/models/action.py`: an `Action` belongs to exactly one `Finding` (`finding_id`). A Finding is created with its first Action (`findings.create_finding` requires `action_title`).
   5. ISO 27001 in the registry: `name "ISO 27001"`, `version "2022"`, 93 controls, domains titled "Organizational Controls", "People Controls", "Physical Controls", "Technological Controls". `Control.reference` is "Annex A.5.1" style.
   6. `app/models/assessment_pack.py` `AssessmentPack(assessment_id, framework_id, pack_version)` is the recorded pack version (written by `engagement_factory`); `FrameworkDefinition.pack_version` is `version` or `version+criteria_version` (DPDPA is `2023+criteria-v1` after P6-2b).
   7. `app/routers/web.py` `/assessments/{id}/compare/{other}` is the live, web-only comparison (`scoring.compute_delta`). P6-9 does not use or change it: the board report compares frozen documents.
   8. `app/templates/pages/report_snapshots.html` has the `{% if type == 'board_report' %}` preview block (B1).

## Decisions (made here so they are not relitigated)

### D-P6-9-A: One PR (see "Split decision")

### D-P6-9-B: SoA content: every Annex A control, status derived only from approved Conclusions

New module `app/services/soa.py` (no LLM, no writes except `record_justification`):

```python
FRAMEWORK_ID = "iso27001"
AUDIT_ENTITY_TYPE = "assessment"
AUDIT_ACTION = "assessment.soa_justification_updated"
JUSTIFICATION_MAX_CHARS = 1000
APPLICABILITY_LABELS = {"applicable": "Applicable", "excluded": "Excluded",
                        "not_assessed": "Not determined", "pending": "Awaiting decision"}
IMPLEMENTATION_LABELS = {"compliant": "Implemented", "partially_compliant": "Partially implemented",
                         "non_compliant": "Not implemented",
                         "insufficient_evidence": "Not determined: insufficient evidence",
                         "not_applicable": "Not applicable"}
NOT_ASSESSED_LABEL = "Not assessed: outside the assessment scope"
PENDING_LABEL = "Not determined: awaiting consultant decision"
INTRO_TEXT = ("Every Annex A control of {framework}, with its applicability, implementation status and "
              "justification. Applicability and implementation status are derived from the consultant-approved "
              "conclusion for each control; justifications are recorded by the consultant.")
RELIANCE_TEXT = ("This statement records the assessor's view at the evidence cut-off. It does not replace the "
                 "organization's own Statement of Applicability.")
NOT_ASSESSED_NOTE = ("{count} Annex A control(s) were outside the scope of this assessment. Their applicability has "
                     "not been determined; the organization must decide it before relying on this statement.")
MISSING_JUSTIFICATION_NOTE = "{count} control(s) have no recorded justification."
NOT_IN_SCOPE_MESSAGE = "ISO 27001 is not in scope for this assessment."
UNKNOWN_CONTROL_MESSAGE = "That control is not an ISO 27001 Annex A control."
TOO_LONG_MESSAGE = f"Keep the justification to {JUSTIFICATION_MAX_CHARS} characters or fewer."
SAVED_MESSAGE = "Justification saved"
TOTAL_KEYS = ("controls", "applicable", "excluded", "not_assessed", "pending", "implemented",
              "partially_implemented", "not_implemented", "not_determined", "justification_missing")

class SoAError(Exception)                 # __init__(message, status_code=400); .message, .status_code
@dataclass(frozen=True)
class Justification: text: str; recorded_by: str; recorded_at: datetime

def applies(framework_ids) -> bool        # "iso27001" in framework_ids
def current_justifications(db, assessment) -> dict[str, Justification]
def record_justification(db, assessment, *, requirement_id: str, justification: str | None, actor: str) -> str | None
def build_soa(db, assessment, approved) -> dict | None   # approved: approved_report.ApprovedReport
```

**Rows.** One per ISO control in pack order (domains → sections → controls), 93 in total. Per control, using `approved.framework_reviews["iso27001"]` (`in_scope_ids`, `rows`):

| Case | `applicability` | `outcome` | `implementation_label` |
|---|---|---|---|
| not in `in_scope_ids` | `not_assessed` | `None` | `NOT_ASSESSED_LABEL` |
| in scope, no approved row | `pending` | `None` | `PENDING_LABEL` |
| approved `not_applicable` | `excluded` | `not_applicable` | `"Not applicable"` |
| approved anything else | `applicable` | the approved outcome | `IMPLEMENTATION_LABELS[outcome]` |

- An unapproved AI proposal never supplies an outcome (scenario 5). An edited decision uses the edited outcome.
- Why "not_assessed" rather than "excluded" for out-of-scope controls: an SoA exclusion is a decision about the organization; an assessment that did not look at a control cannot make it. Non-ISO scope profiling is not implemented (CLAUDE.md gotcha), so in production ISO normally has every control in scope and this case is rare; the P6-8 fixture has only two ISO controls in scope, so its golden shows 91 of them.
- Row keys (exact, scenario 1): `control_id, reference, title, theme` (domain title), `applicability, applicability_label, outcome, implementation_label, justification, justification_by, justification_on` (ISO date of the event, or None).
- `totals` (exact keys `TOTAL_KEYS`): `controls` = rows; one count per applicability; for `applicable` rows `implemented` / `partially_implemented` / `not_implemented` / `not_determined` from compliant / partially / non / insufficient_evidence; `justification_missing` = rows with no current justification (inclusion needs a justification in an ISO SoA as much as exclusion does).
- `notes`: `NOT_ASSESSED_NOTE` when `not_assessed > 0`, then `MISSING_JUSTIFICATION_NOTE` when `justification_missing > 0`, in that order.
- `soa` keys (exact): `framework_id, framework_name, framework_version, intro` (`INTRO_TEXT.format(framework=f"{name}:{version}")`, i.e. "ISO 27001:2022"), `reliance, notes, totals, rows`.
- `build_soa` returns `None` when ISO is not in `assessment.frameworks`. It never flushes or writes.
- The approved Conclusion's rationale is **not** copied into the SoA. It is shown only as a read-only hint on the editor page (D-P6-9-D). Justification text reaches the client only after a consultant saves it.

### D-P6-9-C: Justification storage: append-only audit events (no migration)

- One `AuditEvent(actor=actor, action=AUDIT_ACTION, entity_type="assessment", entity_id=assessment.id, metadata_json=json.dumps({"framework_id": "iso27001", "requirement_id": ..., "before": str|None, "after": str|None}, sort_keys=True))` per change, then `db.flush()`. The caller commits.
- **Current** justification per control = the latest event for that `requirement_id` ordered by `created_at, rowid`. `after` of `None` clears it. Events with unparseable metadata or another `framework_id` are ignored (never raise).
- `record_justification`, in order:
  1. ISO not in `assessment.frameworks` → `SoAError(NOT_IN_SCOPE_MESSAGE, status_code=404)`.
  2. `requirement_id` not an ISO control (`FrameworkRegistry.get("iso27001").get_control(...) is None`) → `SoAError(UNKNOWN_CONTROL_MESSAGE)` (400). A DPDPA id is unknown too.
  3. Clean: collapse every whitespace run (including newlines) to one space, strip; empty → `None`.
  4. Longer than `JUSTIFICATION_MAX_CHARS` after cleaning → `SoAError(TOO_LONG_MESSAGE)` (400). Never truncate: a silently cut justification is worse than a refusal.
  5. Equal to the current text → return it and write nothing.
  6. Otherwise add the event, flush, return the cleaned text.
- `Justification.recorded_by` is the actor without `conclusion_review.REVIEWER_ACTOR_PREFIX`.
- **Why an audit event, not a table:** no migration (the head is pinned in ten test files), full history for free, and the same pattern as the report basis (P6-6), release and the divergence acknowledgement (P6-7a).
- **No lock.** Justifications stay editable after release and after a version is issued; a version captures what was current when it was generated (the sidecar), and that is the record. Whether an edit should mark existing versions "Source data changed" is Open question 2 (default: no, because it would mean changing `source_manifest`, which flips every existing version of every type to "changed").

### D-P6-9-D: SoA editor: new router and page, one-line link from the versions page

New `app/routers/soa.py` with `router = APIRouter(tags=["soa"])` and its own `Jinja2Templates` configured by `configure_templates` (the pattern of `snapshots.py`/`board_report.py`), included in `app/main.py` directly after the snapshots router: `from app.routers import (... soa as soa_router, ...)` and `app.include_router(soa_router.router, dependencies=_ARCHIVE_GUARD)`. A new router avoids `review.py`/`web.py` (P6-7 and P6-7b territory) and `snapshots.py` (B2 adds its DOCX/XLSX routes there).

- `GET /assessments/{assessment_id}/soa` → HTML (`pages/soa.html`, extends `base.html`).
  - 404 for an unknown assessment or when ISO is not in scope.
  - Context: `assessment`, `soa` (= `build_soa(db, assessment, build_approved_report(db, assessment))`, works before release), `rationale` (dict of the approved `current_state` for ISO rows whose approved outcome is `not_applicable`), `max_chars`, `reviewer_name`.
  - One `<tr data-soa-row="{control_id}" data-applicability="{applicability}">` per row, with the two attributes adjacent in that order (scenario 3 matches `data-soa-row="ISO.A5.5" data-applicability="excluded"`).
  - Per row a `<form data-soa-justification-form hx-post="/api/assessments/{{ assessment.id }}/soa/justifications" hx-include="#reviewer-name" hx-swap="none">` with a hidden `requirement_id`, a `<textarea name="justification" maxlength="{{ max_chars }}">` holding the current justification, and a Save button. One `<input id="reviewer-name" name="reviewer_name">` on the page.
  - For excluded rows with an approved rationale: `<p data-approved-rationale>Approved rationale: {{ ... }}</p>` above the form (a hint; it is never saved unless the consultant types or pastes it).
  - Tailwind classes as on `report_snapshots.html`. No `|safe`.
- `POST /api/assessments/{assessment_id}/soa/justifications` (form fields `requirement_id`, `justification`, `reviewer_name`, all `Form("")`), actor `reviewer_actor(reviewer_name)`:
  - unknown assessment → `db.rollback()`, 404 `{"detail": "Assessment not found"}` with the error toast headers;
  - `SoAError` → `db.rollback()`, `exc.status_code` `{"detail": exc.message}`, headers `X-Toast-Message: quote(message)`, `X-Toast-Type: error`;
  - success → `db.commit()`, 200 `{"status": "saved", "requirement_id": ..., "justification": <cleaned or None>}`, headers `X-Toast-Message: Justification saved`, `X-Toast-Type: success`. No `HX-Redirect` (the page stays put).
- `pages/report_snapshots.html`: inside the existing `{% if type == 'board_report' %}` block, after the preview paragraph, add
  ```html
  {% if 'iso27001' in assessment.frameworks %}<p class="mt-1 text-xs text-gray-500 dark:text-gray-400"><a data-soa-link href="/assessments/{{ assessment.id }}/soa" class="font-medium text-brand dark:text-navy-300 hover:underline">Statement of Applicability justifications →</a></p>{% endif %}
  ```
  Nothing else on that page changes; no `web.py` change is needed (`assessment` is already in the context).

### D-P6-9-E: Document schema v2 (additive only)

`DOCUMENT_SCHEMA_VERSION = 2`. Every B1 key keeps its name, shape and value; three things are added:

| Where | Added | Source |
|---|---|---|
| top level | `soa` (dict or `None`) | D-P6-9-B |
| top level | `prior_period` (dict, always present) | D-P6-9-H |
| `frameworks[]` | `pack_version` (str or `None`) | the assessment's `AssessmentPack` rows, latest per framework by `created_at, rowid`; `None` when none is recorded. **Never** the registry's current value: that is code, not a record of what was judged. |
| `roadmap` | `groups` (list) | D-P6-9-F |

- `roadmap.actions` and `roadmap.unplanned_gap_count` are unchanged, including `actions[].closes` with its single entry. B2's "Action tracker" can keep reading them.
- `prior_period` is computed last, from the otherwise complete document: `document["prior_period"] = prior_period.build_comparison(db, assessment, document)`.
- The sidecar metadata key `document_schema_version` follows automatically (B1 writes the constant).
- `build_document` still never writes: `build_soa`, `build_groups` and `build_comparison` only read.

### D-P6-9-F: Cross-framework roadmap groups (UCC clusters, deterministic)

New module `app/services/remediation_groups.py` (pure functions; the only DB-free module):

```python
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SINGLE_PREFIX = "SINGLE."
@lru_cache(maxsize=1)
def cluster_index() -> dict[tuple[str, str], tuple[str, str]]   # (framework_id, control_id) -> (cluster_id, topic)
def join_names(names) -> str                                      # "A" | "A and B" | "A, B and C"
def build_groups(findings: Sequence[ReportFinding], framework_ids: Sequence[str]) -> list[dict]
```

- **Cluster source.** `cluster_index` reads `app.frameworks.mappings.clusters.CONTROL_CLUSTERS` (import inside the function) and raises `ValueError` if a control appears in two clusters. It uses the static mapping, not `Conclusion.cluster_id`: that column is analysis-time and holds `SINGLE.*` ids for single-framework runs, so it would depend on how the analysis happened to run.
- **Group key.** A Finding's `(framework_id, requirement_id)` → its cluster id and topic; a requirement in no cluster → group id `f"SINGLE.{framework_id}:{requirement_id}"`, topic = the requirement title. Two Findings of the **same** framework in one cluster share a group too (e.g. ISO.A5.1 and ISO.A5.4 in CLUSTER_001).
- **Membership.** A group holds every approved Finding in its cluster. A group with no Action at all is omitted (with `create_finding` requiring an Action this only happens for legacy rows).
- **Group dict** (exact keys): `group_id, topic, headline, frameworks` (distinct framework names in `closes` order), `cross_framework` (`len(frameworks) > 1`), `finding_count, target_date` (earliest Action target as ISO date, or `None`), `actions, closes`.
  - `actions[]`: `title, owner, target_date` (ISO), `status_label, framework_name, requirement_id, finding_title`.
  - `closes[]`: `framework_id, framework_name, requirement_id, requirement_title, finding_title, severity`.
- **Headline:**
  - more than one framework: `f"Addresses {n} findings across {join_names(frameworks)}"`
  - one framework, `n > 1`: `f"Addresses {n} findings in {name}"`
  - `n == 1`: `f"Addresses 1 finding in {name}"`

  "Addresses", not the plan's "closes": a Finding is closed by verification of its own Action (P3-4), not by sharing a cluster. The cluster says the requirements cover the same control concern, which is what the reader needs.
- **Ordering (deterministic, never an LLM; scenario 3 shuffles the input):**
  - framework rank = position in `framework_ids` (then any other framework in first-seen order); requirement rank = position in the pack (`FrameworkRegistry.get(...).all_controls()`), unknown ids last.
  - groups: `(earliest target is None, earliest target, best severity rank in the group, -finding_count, topic.lower(), group_id)`
  - actions in a group: `(target is None, target, finding severity rank, framework rank, requirement rank, action title)`
  - closes in a group: `(framework rank, requirement rank, finding title)`
- `board_report.build_document` sets `roadmap["groups"] = remediation_groups.build_groups(findings, framework_ids)` with the same `findings` list it already reads (approved Findings only). Every Action in `roadmap.actions` appears in exactly one group (scenario 4).

### D-P6-9-G: Rendering (`app/templates/reports/board_report.html`)

Section order after P6-9: cover, summary, top-risks, roadmap, not-assessed, framework sections, **comparison (new)**, sign-off, methodology, requirement-register, evidence-register, **soa (new, conditional)**. The B1 order of the existing sections is unchanged, so P6-8 scenario 7's heading order still holds.

- **Roadmap (`data-section="roadmap"`).** This is the one existing section whose body changes; B1 (D-P6-8-F) reserved it for P6-9. The heading stays "Remediation roadmap". The intro becomes exactly:
  > Actions recorded against approved findings, grouped by shared control: findings in different frameworks that cover the same control concern are listed together, so one remediation is tracked once. Groups are ordered by their earliest target date. Owners and dates are set by the consultant; nothing on this page is estimated.

  Per group, `<article class="risk" data-roadmap-group="{{ group.group_id }}">`: the topic (bold), the headline (small), a table `Action | Owner | Target date | Status | Finding` (owner `or 'Unassigned'`, date through `display_date` or `No target date`, finding as `{framework_name}: {requirement_id} ({finding_title})`), then `Findings addressed: {framework_name}: {requirement_id} ({finding_title}); ...`. Each Action title appears exactly once in the section (scenario 4). Empty state unchanged: `No remediation actions are recorded for the approved findings yet.`
- **Comparison (`data-section="comparison"`, always rendered, `<h2>Prior-period comparison</h2>`).**
  - `status == "compared"`: the intro; `Compared with version {version_label} (snapshot {snapshot_id[:8]}) for the assessment period {period_label}, evidence cut-off {cutoff_label}, generated {generated_on}.`; each note as a small paragraph; a table `Framework | Prior score | Current score | Change | Improved | Regressed | Changed | Newly assessed | No longer assessed` with one `<tr data-comparison-framework="{framework_id}">` per framework (scores or `Not scored`; change as `'%+.1f'|format(score_delta)` + ` points`, or `Not compared`; a not-compared framework gets one `Not compared` cell spanning the rest); `Gaps identified: {prior.gaps} in the prior period, {current.gaps} in this period.`; then the changes table `Requirement | Prior outcome | Current outcome | Change` (`{framework_name}: {requirement_id} - {requirement_title}`, labels or `Not assessed`, `direction_label`), or `No requirement outcome changed between the two periods.`
  - otherwise: each note as `<p class="empty">`.
  - No text in the section says "combined" or "overall" (scenario 6).
- **SoA (`data-section="soa"`, only `{% if doc.soa %}`, after the evidence register), `<h2>Appendix D: Statement of Applicability</h2>`:** intro, reliance (small), notes (small), then a table `Control | Theme | Applicability | Implementation | Justification` with one `<tr data-soa-control="{control_id}">` per row: `{reference} {title}`, theme, `applicability_label`, `implementation_label`, the justification or `<span class="muted">Justification not recorded</span>`.
- Rules from B1 still apply: no `|safe`; no user data in `<style>`; only glyphs Noto has (no `→`, `✓`, arrows or emoji in this template; words such as "Improved"/"Regressed" instead of ▲/▼); every date through `display_date`.
- An ISO-only report stays free of DPDPA/legal wording (P6-8 scenario 6 still runs); the SoA copy says nothing about law.

### D-P6-9-H: Prior-period selection (issued sidecars only)

New module `app/services/prior_period.py`:

```python
STATUSES = ("compared", "no_prior", "unavailable")
DIRECTIONS = ("regressed", "improved", "changed", "new", "no_longer_assessed")   # also the sort order
DIRECTION_LABELS = {"regressed": "Regressed", "improved": "Improved", "changed": "Changed",
                    "new": "Newly assessed", "no_longer_assessed": "No longer assessed", "unchanged": "Unchanged"}
COUNT_KEYS = ("improved", "regressed", "unchanged", "changed", "new", "no_longer_assessed")
OUTCOME_RANK = {"non_compliant": 0, "partially_compliant": 1, "compliant": 2}
OUTCOME_LABELS = board_report.OUTCOME_LABELS values (copy the dict; do not import board_report, it imports this module)
TOTAL_KEYS = ("requirements", "gaps", "critical_high_gaps", "insufficient_evidence", "not_applicable")
REQUIREMENT_ID_ALIASES: dict[tuple[str, str], str] = {}   # (framework_id, id in an earlier pack) -> current id
INTRO_TEXT = ("Compared with the last issued board report for the previous assessment period in this "
              "engagement. The earlier report is read from its stored, hash-checked document and is never "
              "regenerated. Scores are compared within each framework only.")
NO_PRIOR_TEXT = ("No earlier issued board report for a previous assessment period exists in this engagement, "
                 "so there is nothing to compare.")
UNAVAILABLE_TEXT = "The earlier issued board report {snapshot} failed its integrity check, so no comparison is shown."
SKIPPED_TEXT = ("{count} other issued board report(s) in this engagement failed their integrity check and "
                "were not considered.")
NOT_IN_PRIOR_TEXT = "{name} was not assessed in the earlier report."
EDITION_CHANGED_TEXT = ("{name}: the earlier report assessed version {prior}; this report assesses version {current}. "
                        "Outcomes are not compared across versions.")
CRITERIA_CHANGED_TEXT = ("{name}: the test criteria changed between periods ({prior} to {current}). Some changes may "
                         "reflect the revised criteria rather than a change in the control.")
CRITERIA_UNKNOWN_TEXT = ("{name}: the pack version of one of the two reports was not recorded, so a change in test "
                         "criteria cannot be ruled out.")

@dataclass
class PriorSelection: snapshot: ReportSnapshot | None; document: dict | None; document_sha256: str | None; failed: list[ReportSnapshot]
def find_prior(db, assessment, *, period_start: date | None) -> PriorSelection
def classify(prior: str | None, current: str | None) -> str
def build_comparison(db, assessment, current: dict) -> dict
```

**`find_prior`:**
1. No `assessment.engagement_id`, or `period_start is None` → empty selection (`no_prior`).
2. Candidates: `ReportSnapshot` rows with `type == "board_report"`, `is_issued`, joined to `Assessment` with the **same `engagement_id`**, `Assessment.id != assessment.id` (an assessment's own versions are never its prior period) and `Assessment.status != "archived"`, ordered by `report_snapshots.rowid`.
3. Per candidate assessment keep only its **current issue** (the last issued row). Newer, unissued drafts are never used.
4. For each: `document = report_snapshots.read_board_report_document(db, snapshot)` and `document_sha256 = report_snapshots.generated_event(db, snapshot.id)["document_sha256"]`. `SnapshotIntegrityError` → append to `failed` and continue.
5. Eligible when the **document's** `basis.period_end` (ISO date) exists and is **before** `period_start`. The period is read from the frozen document, not from the earlier assessment's live basis. Overlapping periods are not prior periods.
6. The prior is the eligible one with the latest `period_end`; ties go to the later issue (rowid order).

The earlier assessment's live data (Conclusions, Findings, basis, `build_approved_report`) is never read, and nothing is rendered or written (scenario 2 patches `build_approved_report` to fail for it and `render_pdf` to raise).

**Status:**
- no prior and nothing failed → `no_prior`, `notes = [NO_PRIOR_TEXT]`
- no prior but something failed → `unavailable`, `notes = [UNAVAILABLE_TEXT.format(snapshot=failed[-1].id[:8])]`
- a prior found → `compared`; if anything failed, `SKIPPED_TEXT.format(count=len(failed))` is the first note. A tampered report is never skipped silently.

### D-P6-9-I: Comparison content

`prior_period` keys (exact): `status, intro, notes, prior, frameworks, changes, totals`. For `no_prior`/`unavailable`: `prior None, frameworks [], changes [], totals None`.

- `prior` (exact keys): `snapshot_id, assessment_id, version_label` (the prior document's `snapshot.version_label`), `generated_on` (the prior document's), `period_label, cutoff_label` (the prior document's `basis`), `document_sha256` (from its generated event, which proves which sidecar was compared), `schema_version` (the prior document's; 1 for a B1 sidecar).
- `frameworks[]`, one per **current** framework in order (exact keys): `framework_id, name, compared, prior_version, current_version, prior_pack_version, current_pack_version, prior_score, current_score, score_delta, prior_rating, current_rating, counts`.
  - `current_score`/`current_rating` from this document's `summary.frameworks[]`; always filled.
  - Framework absent from the prior document → `compared False`, all `prior_*` `None`, `counts None`, note `NOT_IN_PRIOR_TEXT`.
  - Different edition (`frameworks[].version`) → `compared False`, `prior_version` set, `prior_pack_version` set, `prior_score`/`score_delta`/`counts` `None`, note `EDITION_CHANGED_TEXT`. Outcomes are never compared across editions (ISO 27001:2013 vs 2022 ids do not mean the same control).
  - Same edition → `compared True`. If either pack version is `None` → note `CRITERIA_UNKNOWN_TEXT`; if both are set and differ → note `CRITERIA_CHANGED_TEXT` (D-P6-D: criteria bumps keep requirement ids, so outcomes are still comparable, but the reader is told the test changed). `prior_score`/`prior_rating` from the prior `summary.frameworks[]`. `score_delta = round(current - prior, 1)` only when both summaries have `status == "scored"` and both scores are set, else `None`. `counts` (exact `COUNT_KEYS`).
  - Notes are appended in framework order, one per framework at most (plus the leading skip note).
- **Matching.** Requirement key = `(framework_id, requirement_id)`. Prior register ids are first mapped through `REQUIREMENT_ID_ALIASES` (empty today; the place to record a rename when a pack version renames an id). Then per compared framework, over the current register rows and then the prior-only rows:
  - `classify(prior, current)`: prior `None` → `new`; current `None` → `no_longer_assessed`; equal → `unchanged`; both in `OUTCOME_RANK` → `improved` or `regressed` by rank; otherwise (to or from `insufficient_evidence` or `not_applicable`) → `changed`.
  - Every requirement adds to `counts`; every non-`unchanged` one becomes a `changes[]` entry (exact keys): `framework_id, framework_name, requirement_id, requirement_title` (current row, else prior row), `prior_outcome, prior_outcome_label, current_outcome, current_outcome_label` (labels via `OUTCOME_LABELS`, `None` when the outcome is `None`), `direction, direction_label`.
- **Order of `changes`:** `(DIRECTIONS.index(direction), framework rank in this document, requirement pack rank)`; ids no longer in the pack sort after known ones, by id.
- `totals = {"prior": {k: prior summary.totals.get(k)}, "current": {k: current summary.totals[k]}}` for `TOTAL_KEYS`. Totals are counts, never a combined score.
- The prior document is treated as data: missing keys read as empty (`.get`) and never raise.

### D-P6-9-J: Matching across pack versions (the rule, in one place)

1. Same framework id **and** same edition (`version`) → compare requirement by requirement on `(framework_id, requirement_id)` after aliases.
2. Pack version (`version+criteria_version`) differs → still compared, with `CRITERIA_CHANGED_TEXT`. Unknown on either side (B1 sidecars have no `pack_version`; assessments not created through `engagement_factory` have no `AssessmentPack`) → still compared, with `CRITERIA_UNKNOWN_TEXT`.
3. Edition differs → not compared.
4. A requirement renamed between packs is matched only through `REQUIREMENT_ID_ALIASES`; without an alias it shows as `new` + `no_longer_assessed`, which is honest.

### D-P6-9-K: File set, no LLM, disjointness

P6-9 touches exactly:

| Path | Change |
|---|---|
| `app/services/soa.py` (new) | B, C |
| `app/services/remediation_groups.py` (new) | F |
| `app/services/prior_period.py` (new) | H, I, J |
| `app/services/board_report.py` | E (schema 2, `pack_version`, `groups`, `soa`, `prior_period`) |
| `app/routers/soa.py` (new), `app/templates/pages/soa.html` (new) | D |
| `app/main.py` | D (import + one `include_router` line) |
| `app/templates/reports/board_report.html` | G |
| `app/templates/pages/report_snapshots.html` | D (one line inside the board_report block) |
| `tests/golden/p6_8_board_document.json` | re-recorded once (D-P6-9-L) |
| `tests/test_p6_8_board_report_v2.py` | the two exact edits in D-P6-9-L |
| `tasks/handoffs/2026-09-28-p6-9-soa-roadmap-comparison.md` | append `## Results` only |
| designer (already committed) | `tests/p6_9_support.py`, `tests/test_p6_9_{soa,roadmap,prior_period,file_set}.py`, and the per-PR guard excludes listed in D-P6-9-L |

`tests/test_p6_9_file_set.py` enforces the `app/` allowlist (exact paths) and forbids: the fpdf2 reports and fixtures; B1 plumbing and the other in-flight designs' files (`html_pdf.py`, `report_snapshots.py`, `snapshots.py`, `standalone_workpaper.py`, `workpaper_standalone.html`, `rfi_requests.py`, `requirement_card.py`, `review_queue.py`, `requirement_review.py`, `review.py`, `web.py`, `conclusion_review.py`, `templates/components`, `templates/partials`, `base.html`); the report readers and scoring (`approved_report`, `report_content`, `report_basis`, `findings`, `remediation_rollup`, `scoring`); the analyzer, LLM and grounding; `app/frameworks` (the UCC mapping is read, never edited), `app/dpdpa`, models, schemas, alembic, `config.py`, requirements files, `scripts`, `validation`. The new modules contain none of `llm_client`, `claude_analyzer`, `services.grounding`, `call_llm`, `openai`, `anthropic`.

### D-P6-9-L: Existing tests that change (the complete list)

**Already applied by the designer** (per-PR `:(exclude)`/allow entries naming P6-9; nothing deleted or broadened; stale-guard rule):
- `tests/test_p6_2b_dpdpa_criteria.py`: new `P6_9_FILES` prefix tuple, applied in scenario 11.
- `tests/test_p6_3a_grounding.py` `PROTECTED_PATHS`: `app/routers/soa.py`, `app/templates/pages/soa.html`.
- `tests/test_p6_4_cap_upload_limit.py::_changed`: the five new P6-9 app files.
- `tests/test_p6_4_whats_missing.py` scenario 13: a `p6_9` exclude list on both the diff and the untracked listing.
- `tests/test_p6_7_requirement_card.py`: new `P6_9_APP_FILES`, subtracted in scenario 14.
- `tests/test_p6_8_board_report_v2.py` `P6_8_B1_APP_ALLOWLIST` (scenario 14): the five new files and `app/main.py`.
- `tests/test_p6_nist_csf2_alignment.py`: excludes for `soa.py`, `remediation_groups.py`, `prior_period.py`, `routers/soa.py`.

**Codex applies exactly these, and nothing else in existing tests** (they pin the schema this PR changes):
1. `tests/test_p6_8_board_report_v2.py` `DOCUMENT_KEYS`: add the line `    "soa", "prior_period",  # P6-9 (D-P6-9-E): schema v2` before the closing `}`.
2. Same file, scenario 4: `assert document["schema_version"] == board.DOCUMENT_SCHEMA_VERSION == 1` becomes `... == 2  # P6-9 (D-P6-9-E)`.
3. **Golden re-record** (D-P6-8-J allows it because this handoff states the change): `P6_8_RECORD_GOLDEN=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_p6_8_board_report_v2.py -k golden`, once, then run the file without the variable. Expected diff, and nothing else: `schema_version` 1 → 2; `frameworks[].pack_version: null` (the P6-8 fixture has no `AssessmentPack` rows); `roadmap.groups` with two single-Finding groups, `CLUSTER_001` (ISO.A5.1, target 2026-10-31) then `CLUSTER_029` (the DPDPA consent requirement); `prior_period` with `status "no_prior"` and `NO_PRIOR_TEXT`; `soa` with 93 rows (ISO.A5.1 applicable/partially implemented, ISO.A5.2 excluded, 91 `not_assessed`), all justifications `null`. With the reference the file grew from 17,413 to 65,281 bytes, almost all of it the 93 SoA rows. **Any other hunk means an unexplained change: stop and report.**

**Expected transient failures while the tree is uncommitted** (green after the orchestrator commits): `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes` and `tests/test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged`.

## Files touched and overlap with the parallel designs

The parallel designs are P6-8 B2 (DOCX/XLSX from the board-report sidecar), P6-7b (add to RFI from the requirement card) and P6-10 (Finding-grounded narrative). Their designs are not merged yet, so this section states P6-9's side; each later design must do the same for its own.

| File | P6-9 | Likely also touched by | Conflict type |
|---|---|---|---|
| `app/services/board_report.py` | E | P6-10 (fills `summary.frameworks[].narrative`) | text, adjacent lines in `build_document`; both bump `DOCUMENT_SCHEMA_VERSION` |
| `app/templates/reports/board_report.html` | G | P6-10 (summary narrative), maybe B2 (none if B2 only reads the sidecar) | text, different sections |
| `tests/golden/p6_8_board_document.json` | re-record | P6-10, B2 if it changes the document | **re-record after merge, never hand-merge** |
| `tests/test_p6_8_board_report_v2.py` | `DOCUMENT_KEYS`, schema line, allowlist | P6-10, B2 (allowlist) | text; keep both sides |
| `app/templates/pages/report_snapshots.html` | one line in the board_report block | B2 (DOCX/XLSX links on rows) | text, adjacent |
| `app/main.py` | one import + one include | only if another design adds a router | text |
| guard files in D-P6-9-L | excludes | every PR | keep both sides |
| `report_snapshots.py`, `snapshots.py`, `rfi_requests.py`, `requirement_card.py`, `review.py`, `web.py` | **not touched** (forbidden in the P6-9 guard) | B2, P6-7b | none |

**Merge order (recommended): P6-9 → B2 → P6-10.**
- P6-9 before B2: B2's DOCX/XLSX then render schema v2 (SoA sheet, comparison, grouped roadmap) from the start, instead of a follow-up. If B2 merges first, its exporter is designed against v1 and must tolerate the new keys; a small follow-up adds the SoA sheet and the comparison to the DOCX (Open question 3).
- P6-10 last: it needs P6-4/P6-6 and an LLM stage, and it is the slowest. It bumps the schema to 3 and re-records the golden after merging main.
- Whoever merges second: merge `origin/main` into the branch (never rebase; force-push is rejected), keep both sides of every exclude list, take the **higher** `DOCUMENT_SCHEMA_VERSION` plus one if both added keys, and **re-record the golden from the merged code** with the command above, then check every hunk against both handoffs.

## Do not touch

- The P6-9 contract files, `tests/p6_9_support.py`, the designer's guard edits, and `tests/report_period_helper.py`.
- `app/services/{report_snapshots,approved_report,report_content,report_basis,findings,remediation_rollup,scoring,conclusion_review,rfi_requests,standalone_workpaper,requirement_card,review_queue,analysis_pipeline,analysis_v2,claude_analyzer,llm_client}.py`, `app/services/grounding/**`, `app/utils/**`.
- `app/routers/{snapshots,reports,integrated_reports,review,web,requirement_review,conclusions,findings}.py`.
- `app/frameworks/**` (read `CONTROL_CLUSTERS`; do not edit it), `app/dpdpa/**`, `app/models/**`, `app/schemas/**`, `alembic/**`, `app/config.py`, `app/template_config.py`, `app/templates/{base.html,components/**,partials/**}`, `app/templates/pages/*` except `report_snapshots.html` and the new `soa.html`.
- `requirements*.txt`, `.github/**`, `Dockerfile`, `scripts/**`, `tests/fixtures/**`, `tests/support/**`, every other existing test and golden.
- `validation/**` and everything in the independence list.

If you find you need to change any of these, stop and report.

## Non-goals

- **No DPDPA penalty exposure line.** P6-8's Open question 3 suggested P6-9 move `web.py`'s `_PENALTY_MAP` to `app/dpdpa/`; that touches `web.py` (P6-7b territory) and `app/dpdpa`. It stays out (Open question 4).
- No change to the live web comparison (`/compare/{other}`) or `scoring.compute_delta` (its `insufficient_evidence` ranking is a separate issue; see Self-review 5).
- No SoA in the fpdf2 reports, no SoA export file of its own (Open question 3), no structured inclusion reasons (Open question 1).
- No ISO clauses 4-10 (P5-7 stays deferred).
- No migration, no model change, no LLM, no new dependency.

## Test scenarios

| File / # | Test | Covers |
|---|---|---|
| soa 1 | `test_scenario_1_document_schema_v2_and_soa_rows_cover_every_annex_a_control` | E, B: schema 2; exact top-level keys; `pack_version` on frameworks; SoA keys; 93 rows in pack order; the four applicability cases and labels; reference/title/theme; totals; notes |
| soa 2 | `test_scenario_2_justification_is_an_append_only_audit_trail` | C: action, metadata, whitespace cleaning, unchanged = no event, latest wins, clear, too long / unknown / DPDPA id refused with nothing written, document shows text, author, date |
| soa 3 | `test_scenario_3_soa_page_and_save_route` | D: page rows and forms, rationale hint, save JSON and toasts, 400 without an event, 404s (unknown assessment, DPDPA-only page and post), versions-page link only with ISO |
| soa 4 | `test_scenario_4_soa_is_conditional_on_iso_and_rendered_as_appendix_d` | B, G: `soa None` and no SoA text without ISO; Appendix D after the evidence register; 93 rows; empty justification text; no control ids in `<style>` |
| soa 5 | `test_scenario_5_status_comes_only_from_approved_decisions` | B: unreviewed proposal → pending (not its AI outcome), edited → edited outcome, `None` without ISO |
| roadmap 1 | `test_scenario_1_cluster_membership_is_a_function` | F: no control in two clusters; index size; CLUSTER_006 members; `join_names` |
| roadmap 2 | `test_scenario_2_findings_sharing_a_cluster_form_one_cross_framework_group` | F: group keys, topic, frameworks, headline, target, action order and shape, closes order and shape, no-action group omitted |
| roadmap 3 | `test_scenario_3_ordering_is_deterministic_and_input_order_independent` | F: the group key; same output for shuffled input; same-framework group headline |
| roadmap 4 | `test_scenario_4_document_roadmap_keeps_b1_actions_and_adds_groups` | E, F, G: real Findings through the route; `roadmap` keys; B1 `actions` unchanged; groups; each action once; rendered intro, groups, headline, dates |
| roadmap 5 | `test_scenario_5_no_actions_keeps_the_empty_state` | G |
| prior 1 | `test_scenario_1_compares_with_the_previous_issued_period_from_its_sidecar` | H, I: status, intro, `prior` block with the sidecar hash, notes, per-framework keys and counts, score deltas from the two documents, change order and shape, totals, `classify` |
| prior 2 | `test_scenario_2_prior_is_read_from_stored_bytes_never_rerendered_or_live` | H: live edits to the earlier assessment change nothing; its live data is never read; nothing rendered or written |
| prior 3 | `test_scenario_3_selection_rules` | H: issued only, latest period, drafts ignored, overlapping period ignored, other engagement ignored, own versions ignored, archived skipped, no engagement / first period → `no_prior` |
| prior 4 | `test_scenario_4_matching_across_pack_versions_and_editions` | J: `pack_version` from `AssessmentPack`; criteria-changed note; edition change not compared; alias matching; B1 (schema 1) sidecar compared with the unknown-criteria note; framework not in prior |
| prior 5 | `test_scenario_5_tampered_prior_is_reported_not_silently_skipped` | H: `unavailable` with the snapshot id; with a valid older prior, compared plus the skip note |
| prior 6 | `test_scenario_6_comparison_section_renders_between_frameworks_and_sign_off` | G: always rendered; empty text for the first period; position; per-framework rows and signed deltas; directions; no "combined"/"overall" |
| file_set 1 | `test_scenario_1_no_llm_and_p6_9_file_set` | K |

The prior-period tests generate and issue real board-report versions through the real routes, with `board_report.render_pdf` stubbed (`stub_render`): the comparison only ever reads sidecars. P6-8 scenario 7 still renders the full PDF (now including the SoA and comparison) with WeasyPrint and checks every glyph comes from Noto.

## Verification and smoke plan (before reporting done)

1. `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_9_soa.py tests/test_p6_9_roadmap.py tests/test_p6_9_prior_period.py tests/test_p6_9_file_set.py`: **17 passed**, files unmodified. Run it twice.
2. After the D-P6-9-L edits and the golden re-record: `tests/test_p6_8_board_report_v2.py` 14 passed, also with `CYBERASSESS_REQUIRE_WEASYPRINT=1`.
3. Neighbours: `tests/test_report_snapshots.py tests/test_p5_6_rfi_rebuild.py tests/test_workpaper.py tests/test_p6_6_report_foundations.py tests/test_remediation_tracking.py tests/test_findings.py tests/test_p6_7_requirement_card.py`: green.
4. Full suite: green except the two transient uncommitted-tree guards (D-P6-9-L).
5. **Smoke (orchestrator, after commit), real routes, no LLM:**
   1. Engagement with two DPDPA+ISO+NIST assessments, periods Jan-Mar and Apr-Jun 2026. Release the first, generate and issue a board report v2. In the second, add Findings on `CH2.SECURITY.1`, `ISO.A5.15` and `NIST.PR.AA.05`, record two SoA justifications on `/assessments/{id}/soa`, release, generate a version.
   2. Read the PDF back with pdfplumber: "Addresses 3 findings across India DPDPA, ISO 27001 and NIST CSF", "Prior-period comparison" with signed per-framework deltas, "Appendix D: Statement of Applicability" with the two justifications; no `?`, no U+FFFD; all fonts Noto (P6-8 scenario 7 check).
   3. Tamper with the first report's sidecar and regenerate: the comparison says the earlier report failed its integrity check. Restore it.
   4. Paste the pass lines and page count into `## Results`.

## Adversarial review checkpoints `[AR]` (after Codex, before the PR)

1. **Approved-only.** Does any SoA status, group or comparison value come from a proposal, an unreviewed Conclusion, a `GapItem`, or the approved rationale text? Is the rationale only a hint on the editor page?
2. **Write-once and frozen history.** Does the comparison ever read the earlier assessment's live data, re-render it, or write anything? Is a prior read only through `read_board_report_document` (hash-checked)? Is `report_snapshots.py` untouched?
3. **Selection.** Only issued, same engagement, other assessment, not archived, period ended before this one starts, latest wins. Can an unissued draft, an overlapping period or another client's report be picked?
4. **Integrity surfacing.** Is a failed sidecar always reported (`unavailable` or the skip note), never silently skipped?
5. **No blended score.** Is anything summed or averaged across frameworks other than the B1 counts?
6. **Determinism.** Group, action, close and change orders have explicit keys with final tie-breakers; the roadmap is independent of input order.
7. **Conditional copy.** SoA only with ISO; ISO-only reports still carry no DPDPA/legal wording; nothing framework-specific in the comparison copy.
8. **Golden.** Every hunk of the golden diff is one of the D-P6-9-L items.
9. **Injection / glyphs.** No `|safe`, no user text in `<style>`, no non-Noto glyph in the report template; the justification is escaped on the page and in the PDF.
10. **File set.** Diff equals D-P6-9-K; no `report_snapshots.py`, `snapshots.py`, `web.py`, `app/frameworks` change.

## Ready-to-paste Codex prompt (P6-9)

```
You are implementing P6-9 (ISO Statement of Applicability, cross-framework roadmap groups, prior-period comparison in the board report v2) in <worktree> on branch claude/p6-9-soa-roadmap.

Read first, fully: tasks/handoffs/2026-09-28-p6-9-soa-roadmap-comparison.md (the spec), tests/test_p6_9_soa.py, tests/test_p6_9_roadmap.py, tests/test_p6_9_prior_period.py, tests/test_p6_9_file_set.py and tests/p6_9_support.py (the contract). Also CLAUDE.md, AGENTS.md, and D-P6-8-D/E/F/J in tasks/handoffs/2026-09-28-p6-8-board-report-v2.md.

Rules:
- The contract tests are the contract. Make all 17 pass WITHOUT editing those files or tests/p6_9_support.py. Do not skip, xfail, weaken or delete any test. If a test looks wrong, leave it failing and explain in the handoff's ## Results.
- Implement exactly D-P6-9-A..L. Names, signatures, constants, routes, audit action, document keys and rendered strings are fixed. If the code forces a deviation, stop and report it in ## Results; do not pick an alternative.
- Touch only the files in D-P6-9-K. Apply exactly the two existing-test edits in D-P6-9-L and re-record the P6-8 golden once with the stated command; check its diff contains only the listed changes. Everything under "Do not touch" is off limits (report_snapshots.py, snapshots.py, web.py and app/frameworks included).
- You have no network and cannot write .git: no pip install, no git add/commit/branch/stash. Read-only git is fine.
- Answer-key independence: never open, grep, list or glob validation/**, tasks/handoffs/*p5-9*, docs/plans/2026-09-24-002-*, scripts/seed_test_companies.py, scripts/test_ground_truth.json, scripts/seed-v2-prompt.md, scripts/validation/**, tests/test_validation_harness.py or any answer_key.json. Scope every search to explicit paths (app/, tests/test_p6_9_*.py, tests/p6_9_support.py, the files you edit).
- No LLM calls, no migration, no model change, no new dependency.

Steps:
1. git branch -f main origin/main is done by the orchestrator. Run the full suite (.venv/bin/pytest -q -p no:cacheprovider), record counts, confirm the Step 0 facts.
2. Implement soa.py, remediation_groups.py, prior_period.py, the board_report.py changes, routers/soa.py + pages/soa.html + the main.py include, the board_report.html sections and the report_snapshots.html link.
3. Apply the two D-P6-9-L test edits, then re-record the golden once and review its diff.
4. Run the P6-9 files twice, the P6-8 file (also with CYBERASSESS_REQUIRE_WEASYPRINT=1), the neighbours and the full suite (Verification 1-4). The only acceptable failures are the two uncommitted-tree guards.
5. Append ## Results to the handoff: baseline and final counts, golden size and a one-line summary of each diff hunk group, any deviation or doubt. Change nothing else in the handoff.
```

Launch with stdin redirected: `codex exec ... < /dev/null`.

## Open questions for Saqlain (each has a default; nothing here blocks P6-9)

1. **Structured inclusion reasons in the SoA.** Certification SoAs often tick reasons (risk treatment, legal, contractual, business requirement) as well as free text. **Default:** free text only in P6-9; add a reasons field later if clients ask.
2. **Should a justification edit flag existing versions as "Source data changed"?** It would need a new key in `report_snapshots.source_manifest`, which changes the stored `source` of every type and marks every existing version as changed once. **Default:** no; the generated version's sidecar is the record, and the SoA page shows the current text.
3. **SoA as its own file.** **Default:** the SoA lives in the board report (PDF and sidecar) only; B2's XLSX adds an "SoA" sheet derived from the same sidecar (B2 designer to pick up; if B2 merges first, a small follow-up).
4. **DPDPA penalty exposure line** (P6-8 Open question 3 pointed it at P6-9). **Default:** not in P6-9, because it needs `web.py` and `app/dpdpa` edits that collide with P6-7b; do it as a small separate PR after P6-7b, DPDPA-conditional, citing the Schedule.
5. **Should a board report be blocked while ISO controls lack a justification?** **Default:** no; the SoA says how many are missing (`MISSING_JUSTIFICATION_NOTE`) and the consultant decides. A hard gate could be added to issue (not generate) later.
6. **Archived prior assessments** are skipped (their files may be purged by retention). **Default:** keep skipping; say if an archived-but-not-purged prior should still be compared.

## Self-review (designer, before dispatch)

1. **Reference-checked.** A throwaway implementation of this spec passed all 17 tests, the P6-8 suite (14, with the D-P6-9-L edits and the re-recorded golden) and the full suite (1135 passed, 10 skipped) once committed. The reference was not committed; only the tests, guards and this file were.
2. **Guards found by running, not guessed.** With the reference committed on a scratch branch, exactly seven existing scope guards tripped (P6-2b, P6-3a, P6-4-cap, P6-4-missing, P6-7a, P6-8 B1, NIST alignment). Each got a per-PR entry naming P6-9; with those, all guard files pass with the reference.
3. **Why the roadmap keeps `roadmap.actions`.** B1's `closes` comment anticipated P6-9 widening it, but B2 (designed in parallel) reads `roadmap.actions` for its action tracker. Adding `roadmap.groups` and leaving `actions` exactly as B1 made it avoids breaking a design nobody here can see.
4. **An `Action` belongs to one Finding.** So "fix once" cannot be a shared Action row without a migration. Grouping by UCC cluster gives the plan's view without one; each Finding still closes by its own Action's verification.
5. **Not reusing `scoring.compute_delta`.** It ranks `insufficient_evidence` with `non_compliant` (both 0), so "insufficient evidence → non-compliant" would read as "unchanged" and "→ compliant" as "improved". The report's `classify` calls moves to or from insufficient evidence or not applicable "changed". `scoring.py` is not touched; whether the web comparison should follow is a separate question.
6. **Periods come from the frozen document.** Selecting the prior by the earlier assessment's live basis would read live data and could change after issue (dates unlock when conclusions are reopened).
7. **Known pre-existing warning.** `board_report.build_document` calls `db.get(Engagement, None)` for an assessment without an engagement (SQLAlchemy `SAWarning`, B1 code). Prior scenario 3 hits it. Not fixed here (out of scope); Codex may guard it with `if assessment.engagement_id` only if it touches that line anyway.

## Results

- Step 0 baseline: `.venv/bin/pytest -q -p no:cacheprovider` reported **1119 passed, 10 skipped, 16 failed**. The 16 failures were the expected missing P6-9 modules/schema keys. The Step 0 branch, board-report v1 shape, snapshot sidecar helpers, UCC counts/mappings, ISO 27001 catalog, and AssessmentPack facts were confirmed.
- Verification 1: the four P6-9 contract files passed twice: **17 passed** each run. The post-cleanup combined P6-9/P6-8 run also passed (**31 passed**).
- Verification 2: `tests/test_p6_8_board_report_v2.py` passed **14 passed** normally and **14 passed** with `CYBERASSESS_REQUIRE_WEASYPRINT=1`.
- Verification 3: the required neighbor suites passed **113 passed**.
- Verification 4: the final full suite reported **1134 passed, 10 skipped, 1 failed**. The only failure was `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes`, the expected uncommitted-tree guard for the authorized golden and P6-8 test edits; the paired longitudinal guard passed in a targeted run (**1 passed, 1 expected guard failure**).
- Golden: `tests/golden/p6_8_board_document.json` is **65,281 bytes**. Diff hunk groups are: schema version `1` to `2`; recorded `pack_version: null` on the two fixture frameworks; added `roadmap.groups` for `CLUSTER_001` and `CLUSTER_029`; added `prior_period` with `no_prior` and its required note; and added the 93-row `soa` with the expected totals/notes. No other golden changes were present.
- Scope/deviation: no implementation deviation or unresolved doubt. No commit was made, as instructed; the post-commit real-route smoke plan was therefore not run. `git diff --check` passed and no forbidden path changed.

### Orchestrator verification (2026-09-29)

- **Branch:** `claude/p6-9-impl` = the design branch + `origin/main` @ `879c174` (#83) merged in. The `test_p6_3a_grounding.py` guard conflict was resolved by keeping both sides.
- **Saqlain's answers applied:** every open question takes the handoff default (free-text justifications, no source-manifest key, SoA only in the board report, no gate, archived priors skipped, no penalty line).
- **Full suite (committed):** 1135 passed, 10 skipped, 0 failed, matching the designer's reference count.
- **Adversarial review (Sonnet subagent):** all 10 `[AR]` checkpoints PASS and nothing is blocking. Every golden hunk is a D-P6-9-L item; `pack_version: null` is item 3.
  - SHOULD-FIX, fixed by the orchestrator: `prior_period._pack_versions` was dead code, because `board_report` computes the pack versions itself. Deleted, with its orphaned import; the affected suites still pass (136).
  - NITs, not changed:
    - The roadmap sort tuples add final tie-breakers (`finding.title`, `requirement_id`) beyond the listed keys. This only strengthens determinism.
    - `routers/soa.py` hard-codes `"consultant:"` rather than importing `REVIEWER_ACTOR_PREFIX`.
    - `find_prior` also catches `KeyError`/`TypeError` as a failed sidecar. That is broader than specified, but a failure is still surfaced, never skipped.
    - `find_prior` hash-checks one sidecar per other issued assessment in the engagement. It is bounded by the engagement's size.
- **Smoke (real routes, real WeasyPrint render, no LLM).** The script is a scratch pytest module reusing `tests/p6_9_support.py`. It builds one engagement with two DPDPA+ISO+NIST assessments (Jan-Mar and Apr-Jun 2026). The first is released and its board report generated and issued. The second has Findings on `CH2.SECURITY.1`, `ISO.A5.15` and `NIST.PR.AA.05`, two SoA justifications posted through `/api/assessments/{id}/soa/justifications` (`/soa` page 200, posts 200/200), then release and generate:
  - PDF: 21 pages; fonts Noto-Sans, Noto-Sans-Bold, Noto-Sans-Oblique only; no U+FFFD and no `?`.
  - "Addresses 3 findings across India DPDPA, ISO 27001 and NIST CSF": present.
  - "Prior-period comparison": present, status `compared`, with signed per-framework deltas (-16.6, -57.1, -62.4). Counts: DPDPA 1 improved and 1 regressed; ISO and NIST 1 regressed and 1 unchanged each.
  - "Appendix D: Statement of Applicability": present, 93 rows. Both justifications are in the sidecar verbatim (`<by>` and `&` round-trip, not double-escaped) and every word of both is in the PDF text; they wrap across table cells.
  - Tamper: after editing the issued prior's sidecar and regenerating, the comparison status is `unavailable` and the PDF says the earlier report "failed its integrity check". The sidecar was restored byte-identical.
