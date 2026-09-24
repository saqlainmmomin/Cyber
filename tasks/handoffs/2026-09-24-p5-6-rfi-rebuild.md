# P5-6: The RFI is rebuilt as a versioned evidence request. It is sourced from the scope-derived evidence request (P5-5) and from consultant-approved Conclusions (P5-2) only, stored through `report_snapshots` as a new write-once `rfi` snapshot type, gated independently of report release, and issuable to the client as magic-link request items that stay bound to the immutable issued version. The GapItem- and LLM-sourced RFI and `rfi_documents` are frozen

**Plan:** `docs/plans/2026-09-24-001-cleanup-and-non-dpdpa-parity-plan.md`, task P5-6 ("RFI rebuilt as a versioned, Conclusion-sourced evidence request"). It closes known gap **#7** as reframed ("RFI regeneration has no version history … sourced from AI `GapItem`s … its download sits behind the full report release gate, which is backwards for a request that precedes conclusions … does not connect to magic links … Rebuild it as a versioned snapshot sourced from approved Conclusions that can be issued as magic-link request items") and plan-level decision **D-P5-E** ("The RFI is rebuilt, not just versioned"). It also closes the decisions handed forward to it: **D-P5-5-J** ("Create magic link from these items: deferred to P5-6"), **P5-5 open question 4** ("Issuing more than 20 items"), **P3-2 open question 2** ("RFI snapshots … An `rfi` type would reuse this lifecycle unchanged"), and **P2-5 open question 3** ("When request deduplication lands, `scope_json` should reference request-item ids. `"version": 1` in the blob exists so that migration can tell the shapes apart").

**Product contract** (`docs/product/2026-09-21-cyberassess-product-requirements.md`):
- **PR-054** "Generated reports **and RFIs** shall be versioned snapshots." Acceptance: "regenerating output creates a new version bound to the exact approved Conclusion set and does not overwrite an issued artifact."
- **PR-023** "Overlapping Evidence requirements shall be requested once." Acceptance: "one request item may map to several Requirements across several frameworks, and each mapping is visible in the Workpaper."
- **PR-024** Acceptance: magic-link tokens are "expiring, revocable, non-enumerable, restricted to named request items, rate-limited, and prevented from reading other Engagement data."
- **PR-052** Acceptance: "exports use approved Conclusions only and remain unavailable until review gates pass."
- **Invariant 7:** "AI output is always a proposal. Only a consultant decision becomes a final Conclusion." **Guardrail:** "No report or downloadable client deliverable is released from unapproved Conclusions."

**Decisions log:** `tasks/2026-09-21-adversarial-review.md` **D3** (individual approval, no bulk accept), **D8** / plan **D-P5-D** (evidence mapping is consultant-driven; requests are suggestions, never routing), **D2** (generic `audit_events`).

**Owner:** Claude designs (the plan: "it touches the magic-link capability scope and snapshot immutability") → Codex implements → Claude reviews. Every fork the plan, P5-2 and P5-5 hand to this task is closed below.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, every constant, message, key name, route, status code and ordering below, and every test scenario. "The existing code makes step N awkward" is not a licence to redesign step N. Write down what you found and what you would need to change, then stop.

> **P5-2 and P5-5 are fixed contracts this task builds on, not open questions.** From P5-2: `app/services/approved_report.py` (`build_approved_report`, `ApprovedRow`'s D-P5-2-K field set, eligibility D-P5-2-B, scope D-P5-2-C), the snapshot stale pattern (D-P5-2-O) and the legacy-review retirement pattern (D-P5-2-I). From P5-5: the merged evidence-request item contract D-P5-5-E (`compute_scope_multi(...)["evidence_checklist"]`, six keys, deduplicated by `document_type`). **Where this task departs from a sentence in P5-2, D-P5-6-A names it and says why; nothing else in P5-2 or P5-5 is weakened.**

**Depends on:** P5-2 (reader migration; **must be merged first**, Step 0) and P5-5 (merged, PR #39). This handoff was written against `main` at `fd428b1` (`fd428b1196dcbd55858ebc7fb3548f94d9e794bc`), on which P5-2 is **written but not yet implemented**. Every P5-2 symbol below is taken from its handoff (`tasks/handoffs/2026-09-24-p5-2-reader-migration.md`) and must be re-verified in Step 0.
**Blocks:** nothing in Phase 5.
**Runs in parallel with:** P5-4 only if it is still in flight. File overlap is limited to `app/routers/web.py`, in disjoint functions (D-P5-6-N).
**No failing contract suite is pre-written.** `grep -rln "rfi_requests\|RFI_SNAPSHOT_TYPE\|create_rfi_link\|create_rfi_snapshot\|LEGACY_RFI_RETIRED" tests/` finds nothing at `fd428b1`. **Codex writes `tests/test_p5_6_rfi_rebuild.py` itself** from `## Test scenarios`. Every scenario is required. You may add cases, but you may not drop or weaken one. Existing tests may be changed **only** under D-P5-6-M.

## Step 0 (dispatching Claude session, before Codex starts)

**The suite baseline was not measured by the author of this handoff.** It was written in a cloud container where PyPI is blocked by the network policy, so `pip install` and `pytest` could not run. The last independently verified numbers are P5-3's merge record (593 passed, 9 skipped) and P5-5's (569 passed, 9 skipped, measured before P5-3 merged). P5-2 will change the count again. **After P5-2 is merged, create the worktree (`git worktree add ../dpdpa-gap-tool-p5-6 -b codex/p5-6-rfi-rebuild main`, symlink `.venv`, copy `.env`), run `.venv/bin/pytest -q` there, and write the measured baseline and the `main` commit into this section.** Do not dispatch on an unmeasured baseline, and do not dispatch before P5-2 is merged.

**Codex, your first action:** run

```bash
grep -n "^def build_approved_report\|^def in_scope_requirement_ids\|^def is_released\|^def release_state\|^class ApprovedRow\|^class ApprovedReport" app/services/approved_report.py
.venv/bin/python -c "import dataclasses; from app.services.approved_report import ApprovedRow; print([f.name for f in dataclasses.fields(ApprovedRow)])"
grep -n "^def generated_after\|^RFI_SNAPSHOT_TYPE\|^def create_rfi_snapshot\|^SNAPSHOT_TYPES\|^ASSESSMENT_SNAPSHOT_TYPES" app/services/report_snapshots.py
grep -n "^MAX_ITEMS\|^def create_link\|^def create_rfi_link\|^def scope_items" app/services/magic_links.py
grep -n '"frameworks": \[' app/services/scope_profiler.py
grep -rn "/rfi/pdf\|/rfi/docx\|generate-rfi\|rfi_generator" tests/
.venv/bin/alembic heads
```

and confirm:
1. `approved_report.py` exists with those four functions and two classes, and `ApprovedRow` has at least `conclusion_id`, `conclusion_version`, `framework_id`, `requirement_id`, `requirement_title`, `chapter_title`, `control_reference`, `compliance_status`, `gap_description` (D-P5-2-K).
2. `report_snapshots.py` has `generated_after` (P5-2), `SNAPSHOT_TYPES == ("gap_report", "workpaper", "integrated_report")`, `ASSESSMENT_SNAPSHOT_TYPES == ("gap_report", "workpaper")`, and **no** `RFI_SNAPSHOT_TYPE` or `create_rfi_snapshot` yet.
3. `magic_links.py` has `MAX_ITEMS = 20`, `create_link` and `scope_items`, and no `create_rfi_link`.
4. P5-5's `frameworks` key is present in `scope_profiler.py`.
5. Record the exact list of test files and lines that reference the legacy RFI routes or `rfi_generator` (expected: `tests/test_remaining_llm_call_sites.py`, `tests/test_correctness_bundle.py` scenario 7, and P5-2's `tests/test_p5_2_reader_migration.py` scenario 8). D-P5-6-M governs each one.
6. Record the Alembic head. **This task adds no revision** (D-P5-6-K); the head must be identical before and after. P5-2 and P5-4 both declare no revision, so it is expected to be `8b2d5f7e1c34`, but record whatever `alembic heads` prints and hold the task to *that* value.

**If 1-4 are not true, stop and report in `## Results`.**

## Goal

1. A consultant can prepare an RFI **as soon as scope is recorded**, before analysis or release. It lists the P5-5 evidence-request items (each once, with every requirement it maps to) and, once analysis has run, one item per **consultant-approved `insufficient_evidence` Conclusion**. Nothing AI-proposed and unapproved, no score, no outcome label and no desk-review output ever reaches it (D-P5-6-B).
2. Every generation writes a **new, write-once `rfi` snapshot**: the rendered PDF the client receives plus a hash-pinned JSON record of exactly what was requested. Issuing is one-way and newest-only (P3-2 lifecycle unchanged), and is refused when the draft no longer matches its sources (PR-054; D-P5-6-D/E).
3. The RFI is **not** behind the report release gate (D-P5-6-A).
4. Items of the **current issued** RFI version can be issued as magic-link request items. The link stays inside every P2-5 limit and security property; it carries references to the immutable RFI version, not copies of mappings (D-P5-6-H).
5. The consultant sees, per request item: its requirement mappings (PR-023), which client links cover it, and what the client has uploaded against it (D-P5-6-I).
6. The legacy RFI (`generate_rfi_web`, `rfi_generator`, `RFIDocument` downloads) is retired with an explicit 410. `rfi_documents` is frozen history (D-P5-6-J). No schema change (D-P5-6-K).

## Current state

Grounded against `fd428b1`. Line numbers were read at that commit; P5-2 will shift some of them in `web.py`, `snapshots.py` and `report_summary.html`. **Relocate everything by symbol name.**

### The legacy RFI (to be retired)

- **`app/models/rfi.py`** (25 lines): `RFIDocument(id, assessment_id, title, introduction, evidence_items (JSON text), response_instructions, appendix, total_items, critical_items, raw_ai_response, generated_at)`. `assessment_id` is `unique=True` (line 16), so one row per assessment. Readers/writers: `web.py` (import line 24; `report_summary` line 1972 and context key `"rfi"` line 2044; `generate_rfi_web`; both downloads), `app/services/retention.py` (import line 35; `"rfi_documents"` in the purge table list line 58 and the purge scope line 642), `app/legacy_migrations.py` (lines 40, 51), `app/legacy_migrations_schema.py` (199-214), `scripts/score_test_results.py` (25, 93), `scripts/seed_test_companies.py` (30, 1276), `scripts/detect_orphans.py` (18). Tests: `test_data_integrity.py`, `test_retention.py`, `test_correctness_bundle.py` build rows or tables of it.
- **`web.generate_rfi_web`** (`POST /assessments/{assessment_id}/generate-rfi`, lines 2319-2406): 400 unless a `GapReport` exists; reads **every `GapItem`** (2337-2352) plus P5-3's `scoped_findings` desk-review absences and signals (2355-2368); calls `rfi_generator.generate_rfi`; on exception returns an inline error HTML; **deletes the existing `RFIDocument` then inserts** (2383-2400). No gate.
- **`web.download_rfi_pdf`** (2409-2437) and **`download_rfi_docx`** (2440-2468): `require_review_approval(assessment_id, db)` first (the full release gate), then render the stored row through `rfi_export`. After P5-2 they pass P5-2's release gate (D-P5-2-T).
- **`app/services/rfi_generator.py`** (301 lines): `_REQ_TITLES`/`_REQ_SECTIONS`/`_REQ_CHAPTERS` are **DPDPA-only** lookups (22-30); `_build_evidence_items` (92-151) takes every `GapItem` whose status is not `compliant`/`not_assessed` plus desk-review absences (signals are passed and ignored, as P5-3 F12 recorded); `_call_claude_rfi` (195-264) is an LLM call on the `synthesize` tier that writes the introduction, response instructions and each item's "evidence_requested" prose. **So the RFI today is AI proposals rendered through AI prose.** Its only callers are `web.generate_rfi_web` and `tests/test_remaining_llm_call_sites.py` (lines 215-258, three tests).
- **`app/utils/rfi_export.py`** (362 lines): `generate_rfi_pdf(title, company_name, introduction, evidence_items, response_instructions, generated_at=None, framework_label="") -> bytes` (34-150) and `generate_rfi_docx(...)` with the same parameters (240-361). Items are dicts read with `.get`: `item_id`, `priority`, `requirement_id`, `section_ref` (or legacy `dpdpa_section`), `requirement_title`, `current_status`, `evidence_requested`, `deadline_weeks`, `chapter` (grouping). `RFI_PRIORITY_COLORS` knows `Critical/High/Medium/Low` (22-27). `_render_evidence_item` (153-214) draws a fixed 40 mm card and prints `f"{requirement_id} | {section_ref}"` on one line. Both generators are called directly by `tests/test_white_label.py` (keyword arguments; the file also forbids the word `CyberAssess` in `rfi_export.py`) and `tests/test_p5_8_mechanical_cleanup.py::test_rfi_docx_includes_framework_label`.
- **Templates:** `partials/report_summary.html` lines 384-389 (`{% if rfi %}` "RFI PDF" / "RFI DOCX" header links) and section **H** lines 537-560 ("Request for Information (RFI)" card, `#rfi-section`, the "Generate RFI" button, `{% include "partials/rfi_generated.html" %}`). `partials/rfi_generated.html` is included only there and returned only by `generate_rfi_web`.

### Report snapshots (`app/services/report_snapshots.py`, 528 lines; `app/routers/snapshots.py`, 187 lines)

- Constants (22-39): `SNAPSHOT_TYPES`, `ASSESSMENT_SNAPSHOT_TYPES`, `FORMAT_BY_TYPE`, `MEDIA_TYPES = {"pdf", "html"}`, `TYPE_LABELS`, `AUDIT_ENTITY_TYPE = "report_snapshot"`, `GENERATED_ACTION`, `ISSUED_ACTION`, `MANIFEST_SCHEMA_VERSION = 1`, `ISSUE_SQL` (newest-only per `type` and assessment, via `rowid`).
- `storage_path_for` (83-94) → `reports/assessments/{assessment_id}/{snapshot_id}.{fmt}`. `_write_file` (118-123) opens with `"xb"` (write-once). `_store` (145-194) writes the file, adds the row and the `report_snapshot.generated` event with **exactly** `schema_version, type, format, storage_path, sha256, size_bytes, assessment_id, engagement_id, review_status, source`, flushes, and unlinks the file on any exception. `create_snapshot` (197-230) accepts only `ASSESSMENT_SNAPSHOT_TYPES` and uses `source_manifest` (101-115).
- `generated_event` (305-323), `read_snapshot_bytes` (326-335, sha256-verified), `issue_snapshot` (342-373: verify file, `ISSUE_SQL`, "already issued" / "A newer version of this report exists…" `SnapshotNotIssuable` 409, `report_snapshot.issued` event).
- `SnapshotRow` (384-396), `_build_rows(snapshots, generated_by_id, issued_by_id, current_source)` (399-445: `sequence` by rowid order, `state` issued/draft/superseded_draft, `issuable = state == "draft"`, `source_changed`), `snapshot_rows` (472-502: **keys are exactly `ASSESSMENT_SNAPSHOT_TYPES`**), `engagement_snapshot_rows(db, engagement, *, current_source)` (505-528).
- Router: `_error` (28-32), `_success` (35-47, `HX-Redirect` to `/snapshots`), `_render` (50-63), `generate_snapshot` (66-111: type must be in `SNAPSHOT_TYPES`, else 400 "Unknown report type."; `integrated_report` → 400; commit failure unlinks the file → 500), `issue_snapshot_route` (114-144: `require_review_approval`, then P5-2 adds the `SNAPSHOT_STALE_MESSAGE` check), `snapshot_file_route` (147-187: **no gate**; for `format == "pdf"` it looks up the sequence with `snapshot_rows(db, assessment)[snapshot.type]`, which would raise `KeyError` for a type outside `ASSESSMENT_SNAPSHOT_TYPES`).
- `tests/test_report_snapshots.py` line 720 asserts the snapshots page has exactly **2** `data-snapshot-type=` sections, and line 541-542 pins the generic route's "Unknown report type." and integrated-report messages.
- Retention: `_blob_roots` (`retention.py` 613-617) includes `reports/assessments/{assessment_id}`; the purge removes each root with `shutil.rmtree` (line 1032). **Any extra file written under that directory is purged with the assessment.** `report_snapshots` rows are purged by `assessment_id` (644), whatever their `type`.
- `ReportSnapshot.type` is `String(30)` and `format` is `String(10)`; the P1-2 migration (`5c7c75960f43`) has **no CHECK constraint** on either. `"rfi"` and `"pdf"` need no schema change.

### Magic links (`app/services/magic_links.py`, 459 lines; `app/routers/magic.py`, 321 lines)

- `MAX_ITEMS = 20`, `MAX_ITEM_TITLE_CHARS = 200` (30-31). `create_link(db, *, engagement_id, item_titles, expires_in_days, max_uploads, max_total_mb, actor="consultant") -> CreatedLink` (146-211), validation in this order: engagement missing → `MagicLinkNotFound`; not `active` → `MagicLinkConflict`; no titles → "Add at least one requested item."; > 20 → "A link can request at most 20 items."; > 200 chars; duplicate (casefold); expiry 1-30; uploads 1-100; total 1-500 MB. Then `scope_json = json.dumps({"items": [{"key": "item-N", "title": …}], "version": 1}, sort_keys=True)` and the `magic_link.created` audit event with **exactly** `{engagement_id, expires_at, item_keys, max_size_bytes, max_uploads}` (`tests/test_magic_links.py` 309-324 pins both).
- `scope_items(link)` (109-110) returns `json.loads(link.scope_json)["items"]`. It is the **only** reader of `scope_json`: `magic.py` uses it for the client page items and the `item_key` check (183-191); `receive_client_upload` (316-375) uses it to bind an upload to its item (`change_reason` "Client upload via magic link for requested item: {title}", audit `magic_link.upload_received` metadata exactly `{evidence_id, item_key, magic_link_id, sha256, size_bytes}`, pinned at `test_magic_links.py` 566-572); `magic_link_rows` (378-402) lists titles.
- The client page `app/templates/magic/upload.html` renders **only** `item.title` (line 52, 63) and `item.key` (option value). P2-5 D-P2-5-C: the client page must not render the client name, engagement/assessment/evidence/link ids, other links' items, or "anything questionnaire- or conclusion-related".
- Consultant route `POST /engagements/{engagement_id}/magic-links` (`magic.py` 239-292) returns `partials/magic_links.html` with `_CONSULTANT_HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}`; the raw URL is shown once.
- Every router in `app/main.py` (131-153) is mounted with `_ARCHIVE_GUARD`; `tests/test_retention.py` (~765-835) enumerates every mutating route with an `{assessment_id}`/`{engagement_id}`/`{evidence_id}` parameter and requires the guard's 409. **New routes carrying `{assessment_id}` are covered automatically.**

### The two inputs P5-6 consumes

- **P5-5 (merged):** `compute_scope_multi(scope_answers, framework_ids)["evidence_checklist"]` → items with exactly `{"document_type", "label", "reason", "required", "maps_to", "frameworks"}`, one per `document_type`, `maps_to` the union across contributing frameworks in first-seen order, control IDs globally unique across the registry (D-P5-5-E). It is a pure function of `(scope_answers, framework_ids)` and the framework definitions. `web.download_evidence_checklist_pdf/docx` (1040-1101) render it live, unversioned. "Scope recorded" in the UI is `assessment.scope_answers is not None` (`web.py` 825).
- **P5-2 (to be merged first):** `approved_report.build_approved_report(db, assessment).rows` → `ApprovedRow`s for every **eligible in-scope** Conclusion (latest human decision `approved`/`edited` by a `consultant:` actor; out-of-scope never rows), in framework selection order then registry order, with `compliance_status` in the five-value vocabulary including `insufficient_evidence`. It is computed on read and is **independent of release state** (release is a separate `release_state`). P5-2 does not define `build_approved_report`'s behaviour when no `GapReport` exists (its blocker 1 stops there), so this task does not call it in that case (D-P5-6-B).
- Approving an `insufficient_evidence` Conclusion already requires non-blank gaps and a recommended action (`conclusion_review.INCOMPLETE_GAPS`, `_approval_blocker`) and captured citations (`EVIDENCE_NOT_CAPTURED`).

## Decisions (made here so they are not relitigated)

### D-P5-6-A. The gating fork: the RFI is a request, not a release surface. It is gated independently, and never on report release. P5-6's word wins over P5-2's D-P5-2-T sentence.

**The conflict.** P5-2 D-P5-2-T says "P5-6 must source from `build_approved_report(...).rows` and **gate on `release_state`**", and P5-2 moves the *legacy* RFI downloads onto the release gate. The plan's P5-6 scope says "The download **no longer** sits behind the full report release gate", and gap #7 calls the release gate "backwards for a request that precedes conclusions."

**Resolution.** The sourcing half of P5-2's sentence is kept exactly (the RFI reads `build_approved_report(...).rows` and nothing else about Conclusions). The gating half is **not** adopted. The RFI (generate, issue, PDF, DOCX, client links) is gated only by:
1. the assessment exists (404);
2. scope is recorded, `assessment.scope_answers is not None` (409 `RFI_SCOPE_REQUIRED_MESSAGE`), because the evidence request is derived from scope;
3. the RFI has at least one item (409 `RFI_EMPTY_MESSAGE`);
4. the P4-4 archive guard (409 on every POST, inherited from the router mounts);
5. for issue: the draft still matches its sources (D-P5-6-D);
6. for a client link: an engagement exists and the version is the current issue (D-P5-6-H).

No RFI code path calls `require_review_approval`, `release_state`, `is_released` or `latest_release_event`, reads `review_status`, or checks for a failed framework. A guard test enforces it (scenario 22).

**Why P5-6 wins here, and why this does not weaken P5-2's invariant:**
1. **Scope ownership.** The plan (the source of truth for task scope) gives the RFI's design to P5-6 and states the gate outcome explicitly. P5-2 itself says "**P5-6 owns the RFI** (D-P5-E); only its download gate changes here." P5-2's gate on the legacy RFI was a holding action for a GapItem-sourced artifact. This task retires that artifact (D-P5-6-J), so the question of gating it disappears.
2. **Purpose.** An RFI exists to collect evidence *before* Conclusions can be reached. P5-2's release requires every in-scope requirement to be individually approved (D-P5-2-F). Gating the RFI on release would make it available only after the evidence it requests has stopped mattering. That is exactly the "backwards" defect gap #7 names.
3. **What the release gate protects is not in the RFI.** Release protects scores, outcome distributions, gap cards, remediation and the executive summary (a statement of results). The RFI carries none of them: no score, no rating, no outcome label, no risk level, no remediation, no AI text (D-P5-6-B/C). Its only Conclusion-derived content is the consultant-approved gap text of Conclusions the consultant individually concluded as `insufficient_evidence`, i.e. the consultant's own written request for evidence.
4. **PR-052 and the guardrail still hold, at item granularity.** "Exports use approved Conclusions only" holds: every Conclusion-derived item comes from an eligible (individually approved, D3) Conclusion. "Until review gates pass" holds per item: the review gate for a request item is that Conclusion's individual approval, not the whole report's release. Unapproved AI proposals never appear (Invariant 7).
5. **PR-041 (fail closed on incomplete coverage) does not apply.** The RFI asserts no coverage and no completeness. A failed framework simply contributes no Conclusion items, and its evidence requests still appear, which is what the consultant needs to re-run it.

### D-P5-6-B. What the RFI contains (exact sources and filters)

Two sources, in this order. Nothing else.

**1. Document items: the P5-5 evidence request, minus consultant omissions.**
- `checklist = scope_profiler.compute_scope_multi(json.loads(assessment.scope_answers), assessment.frameworks)["evidence_checklist"]`, in its order.
- The consultant may **omit** document types at generation time (multi-valued form field `omit`). Each value must be a `document_type` in `checklist`; otherwise 400 `RFI_UNKNOWN_OMISSION_MESSAGE`, nothing written. Omissions are recorded in the version (D-P5-6-C/E).
- Both `required` and recommended items are included (the priority shows which). P5-5's demotion rule has already applied.
- **No automatic fulfilment detection.** An item is never dropped because evidence exists. D-P5-D forbids treating mapped evidence as proof a request is satisfied, and an `EvidenceUse` says a file was mapped, not that it is sufficient. The RFI page shows a **consultant-only hint** per document item (D-P5-6-I: "Evidence already mapped for M of N requirements", from existing `EvidenceUse` rows of this assessment) so the consultant can choose to omit. The hint is never written into the RFI.

**2. Requirement items: approved `insufficient_evidence` Conclusions.**
- Only if a `GapReport` exists for the assessment (`db.query(GapReport.id).filter(GapReport.assessment_id == assessment.id).first()`); otherwise there are none.
- `rows = [r for r in approved_report.build_approved_report(db, assessment).rows if r.compliance_status == "insufficient_evidence"]`, in `rows` order. Take `rows` as P5-2 returns them; do not re-derive eligibility or scope, and do not filter by framework view status.
- **Excluded, with reasons:**
  - `compliant`, `not_applicable`: nothing to request.
  - `partially_compliant`, `non_compliant`: the consultant has concluded. Requesting evidence after a final, locked conclusion is remediation, not an RFI, and disclosing those outcomes before release would disclose results. A consultant who wants evidence first reopens the Conclusion and records `insufficient_evidence`.
  - Pending, rejected, reopened and legacy-bulk-approved Conclusions, and AI proposals of any kind (Invariant 7).
  - **Findings** (the plan's "approved Conclusions and Findings"): every Finding hangs 1:1 off an eligible gap Conclusion (`findings.py`), so an `insufficient_evidence` Finding's Conclusion is already a requirement item. Finding titles, severity and Actions are remediation-tracking content that belongs to the released report, not to a request. Findings add no item and no text.
  - Desk-review absences and signals (P5-3 `DeskReviewFinding`), `GapItem`s, `GapReport` text, `Initiative`s: all AI output that no consultant approved.
- A requirement item and a document item mapping the same requirement are **both kept**. The document item asks for a named document once for many requirements (PR-023). The requirement item carries the consultant's specific gap text for one requirement.

**No LLM.** Every word in the RFI is either framework content (P5-5 labels and reasons, registry titles), consultant-approved Conclusion text, or a fixed constant in D-P5-6-C. `rfi_generator.py` and its `synthesize` call are deleted (D-P5-6-J).

### D-P5-6-C. The RFI document: exact schema, numbering, text constants, canonical bytes

New module **`app/services/rfi_requests.py`**. It never commits and never deletes; its only writes go through `report_snapshots.create_rfi_snapshot`, `report_snapshots.issue_snapshot` and `magic_links.create_rfi_link`. Constants (exact text, all ASCII):

```python
RFI_DOCUMENT_SCHEMA_VERSION = 1
RFI_ITEM_ID_FORMAT = "RFI-{n:03d}"
RFI_DOCUMENTS_GROUP = "Documents requested"
RFI_DOCUMENT_STATUS = "Document requested for this assessment"
RFI_REQUIREMENT_STATUS = "Evidence needed before this requirement can be concluded"
RFI_REQUIREMENT_FALLBACK = "Provide evidence showing how this requirement is met."
DEADLINE_WEEKS = {"Required": 2, "Recommended": 4}
RFI_INTRODUCTION = (
    "This Request for Information has been prepared as part of the {framework_label} compliance "
    "assessment for {company_name}. It lists the documents and evidence needed to complete the "
    "assessment. Items marked Required are needed before the related requirements can be concluded; "
    "items marked Recommended help confirm the assessment where they exist. Where one document is "
    "requested for several requirements, it only needs to be provided once."
)
RFI_RESPONSE_INSTRUCTIONS = (
    "Please provide each item and quote its RFI item number (for example, RFI-001) when you send it. "
    "If your consultant has given you a secure upload link, upload each file against the matching item. "
    "Documents may be provided in PDF, DOCX or image format. If an item does not apply to your "
    "organisation, reply with a short written explanation instead of a document."
)
```

`build_rfi_document(db, assessment, *, omitted: Sequence[str] = ()) -> dict` returns exactly these keys:

```python
{
    "schema_version": 1,
    "assessment_id": assessment.id,
    "company_name": assessment.company_name,
    "framework_ids": list(assessment.frameworks),
    "framework_label": ", ".join(registry names in selection order),   # same names as web._selected_framework_names
    "title": f"{framework_label} Compliance - Request for Information: {company_name}",
    "introduction": RFI_INTRODUCTION.format(framework_label=..., company_name=...),
    "response_instructions": RFI_RESPONSE_INSTRUCTIONS,
    "omitted_document_types": sorted(set(omitted)),
    "items": [...],
    "totals": {"items": n, "documents": d, "requirements": r, "required": q},
    "source": current_source(...)   # D-P5-6-D
}
```

**Items**, document items first (checklist order, omitted ones skipped), then requirement items (row order). `item_id` numbers them contiguously from `RFI-001` across both kinds. Every item has exactly these keys:

| Key | Document item | Requirement item |
|---|---|---|
| `item_id` | `RFI_ITEM_ID_FORMAT.format(n=…)` | same |
| `kind` | `"document"` | `"requirement"` |
| `title` | checklist `label` | `row.requirement_title` |
| `request` | checklist `reason` | `row.gap_description.strip()` or `RFI_REQUIREMENT_FALLBACK` if blank |
| `required` | checklist `required` | `True` |
| `requirements` | `[[framework_id, control_id], …]` for each id in `maps_to`, in order | `[[row.framework_id, row.requirement_id]]` |
| `document_type` | checklist `document_type` | `None` |
| `control_reference` | `None` | `row.control_reference` |
| `conclusion_id`, `conclusion_version` | `None`, `None` | `row.conclusion_id`, `row.conclusion_version` |
| `group` | `RFI_DOCUMENTS_GROUP` | `row.chapter_title` |

- **Framework attribution** of a `maps_to` id: the first framework in the item's `frameworks` whose `FrameworkRegistry.get(fw).get_control(id)` is not `None`. If none matches, raise `ValueError(f"Evidence request {document_type} maps to unknown control {id}")`. P5-5 scenario 2 guarantees it never happens; if it does, that is a content bug to report, not to paper over.
- `totals`: `items = len(items)`, `documents`/`requirements` = counts by kind, `required` = count with `required` True.
- **Canonical bytes:** `canonical_bytes(document) = json.dumps(document, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")`. The document contains **no timestamp and no random value**, so building twice from unchanged state yields byte-identical output (scenario 1).
- Empty (`items == []`) → `RfiError(RFI_EMPTY_MESSAGE, 409)` from `generate_version`; `build_rfi_document` itself returns the empty document (the page preview shows it).

### D-P5-6-D. What a version is bound to, and when it may be issued (PR-054)

`current_source(db, assessment) -> dict`, exact key set and content:

```python
{
    "schema_version": 1,
    "framework_ids": list(assessment.frameworks),
    "checklist_sha256": sha256(json.dumps(checklist, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest(),
    "conclusion_versions": [[row.conclusion_id, row.conclusion_version] for every included requirement row],  # sorted by conclusion_id
}
```

- `checklist` is the **full** checklist, before omissions. **Omission is a generation parameter, not a source**: it is recorded in the document and the event (D-P5-6-E) but does not make a version stale.
- The checklist is bound **by value** (its hash): it is a pure function of scope answers, framework selection *and* the framework definitions, so hashing its output catches a content edit to P5-5's lists that the inputs alone would miss. The raw scope answers are not stored (the hash covers their effect, and audit rows keep identifiers only, P4-4 D-P4-4-B).
- `conclusion_versions` binds exactly the Conclusions the RFI quotes, as `(id, version)` pairs, in the same way P5-2's release manifest binds the released set (D-P5-2-G). `Conclusion.version` increments on every human decision, so a reopen, edit or re-approval of a quoted Conclusion changes it; a newly approved `insufficient_evidence` Conclusion, or a quoted one leaving scope or changing outcome, changes the list.
- **Issue rule (the P5-2 D-P5-2-O pattern, made exact):** a draft may be issued only if its recorded `source` (the generated event's `metadata["source"]`) **equals** `current_source(db, assessment)` computed now; otherwise **409 `RFI_STALE_MESSAGE`**. P5-2 compares audit `rowid`s against a release event because the gap report has a release act to anchor to. The RFI has none (D-P5-6-A), so it compares its own manifest by value, which is strictly stronger.
- **Named, accepted:** a change to `assessment.company_name` alone does not stale a draft (P3-2's manifests don't bind it either; the name is display-only and is not an identifier to put in an audit row).
- After issue, a source change never touches the issued version. The page flags it "Source data changed since generation" (`_build_rows`' existing `source_changed`), and the consultant generates and issues a new version.

### D-P5-6-E. Storage: a new `rfi` snapshot type through `report_snapshots`, P3-2 lifecycle unchanged, rendered PDF plus a hash-pinned JSON record

**One `ReportSnapshot` row per RFI version**, `type = "rfi"`, `format = "pdf"`, `storage_path = reports/assessments/{assessment_id}/{snapshot_id}.pdf` holding the **rendered PDF bytes** (the client deliverable). Alongside it, one **write-once JSON sidecar** at the same path with `.json` instead of `.pdf` holding `canonical_bytes(document)`.

**Why both, and why the PDF is the snapshot.** P3-2 D-P3-2-A decided that a snapshot is the exact rendered bytes, never re-rendered, because renderer changes must not alter what a client received, and fpdf2 output cannot be re-verified by hash. The RFI PDF is what the client receives, so it follows that rule unchanged. But client links (D-P5-6-H) and the tracking page (D-P5-6-I) need the structured items the PDF was rendered from, frozen with it. Parsing a PDF back is not an option, and storing consultant gap text in an audit row is forbidden (D-P4-4-B). So the structured record is a second write-once file, pinned by its own sha256 in the generated event. It lives in the snapshot's directory, so the retention purge (`rmtree` of `reports/assessments/{assessment_id}`) removes it with the PDF, with no retention change.

**Exact changes to `app/services/report_snapshots.py`** (additive; `SNAPSHOT_TYPES`, `ASSESSMENT_SNAPSHOT_TYPES`, `source_manifest`, `snapshot_rows`, `issue_snapshot`, `ISSUE_SQL`, `generated_after` and every existing message are **unchanged**):
1. `RFI_SNAPSHOT_TYPE = "rfi"`; `FORMAT_BY_TYPE["rfi"] = "pdf"`; `TYPE_LABELS["rfi"] = "Request for information (PDF)"`; `RFI_DOCUMENT_SUFFIX = ".json"`. `"rfi"` is **not** added to `SNAPSHOT_TYPES` or `ASSESSMENT_SNAPSHOT_TYPES`, so the generic generate route keeps answering "Unknown report type." for it and the snapshots page keeps exactly two sections.
2. `_store(...)` gains a keyword-only `extra_metadata: dict | None = None`. When given, its keys are merged into the generated-event metadata; a key that collides with an existing key raises `ValueError`. Existing callers pass nothing, so their event key set is unchanged.
3. `rfi_document_path(snapshot) -> Path` = `Path(settings.upload_dir) / (snapshot.storage_path.removesuffix(".pdf") + RFI_DOCUMENT_SUFFIX)`. The path is **derived, never stored**, and is built only from server UUIDs.
4. `create_rfi_snapshot(db, *, assessment, pdf_content: bytes, document_content: bytes, source: dict, omitted_document_types: list[str], actor: str) -> ReportSnapshot`: empty `pdf_content` or `document_content` → `InvalidSnapshot("Rendered report was empty; nothing was saved.")` before any write. Mint `snapshot_id`; compute both paths; `_write_file` the sidecar first; then `_store(..., snapshot_type="rfi", fmt="pdf", review_status=assessment.review_status, source=source, extra_metadata={"document_sha256": sha256(document_content), "document_size_bytes": len(document_content), "omitted_document_types": omitted_document_types})`. On any exception from `_store`, unlink the sidecar and re-raise (`_store` already unlinks the PDF). Generated-event key set for an `rfi` row is therefore exactly the ten P3-2 keys plus those three.
5. `read_rfi_document(db, snapshot) -> dict`: `snapshot.type != "rfi"` → `SnapshotNotFound("RFI version not found.")`; read the generated event; read the sidecar bytes; missing file or sha256 ≠ `metadata["document_sha256"]` → `SnapshotIntegrityError(INTEGRITY_MESSAGE)`; return `json.loads`.
6. `rfi_snapshot_rows(db, assessment, *, current_source: dict | None) -> list[SnapshotRow]`: the `engagement_snapshot_rows` pattern, selecting `assessment_id == assessment.id and type == "rfi"` ordered by `rowid`, then `_build_rows(..., current_source)`.
7. `current_rfi_issue(db, assessment) -> ReportSnapshot | None`: the newest (`rowid`) `rfi` row of the assessment with `is_issued` true.

Issue uses the unchanged `issue_snapshot` (integrity, newest-only `ISSUE_SQL`, "already issued", "A newer version of this report exists…", `report_snapshot.issued` event). Issued bytes and the sidecar are never opened for writing again.

### D-P5-6-F. Routes, gates, messages (exact)

`rfi_requests.py` defines `class RfiError(Exception)` with `(message: str, status_code: int)` and these messages:

```python
RFI_SCOPE_REQUIRED_MESSAGE = "Record the assessment scope before preparing an RFI."
RFI_EMPTY_MESSAGE = "Nothing to request: every evidence request item is omitted and no approved conclusion is marked insufficient evidence."
RFI_UNKNOWN_OMISSION_MESSAGE = "One of the omitted items is not in the current evidence request. Reload the page and try again."
RFI_STALE_MESSAGE = "This RFI version no longer matches the current scope, evidence request or approved conclusions. Generate a new version, then issue it."
RFI_NOT_FOUND_MESSAGE = "RFI version not found."
RFI_WRONG_ROUTE_MESSAGE = "RFI versions are generated and issued from the RFI page."
RFI_LINK_NOT_CURRENT_MESSAGE = "Client links can only be created from the current issued RFI version."
RFI_NO_ENGAGEMENT_MESSAGE = "This assessment is not part of an engagement, so a client link cannot be created."
RFI_UNKNOWN_ITEM_MESSAGE = "Choose requested items from this RFI version."
LEGACY_RFI_RETIRED = "The previous RFI generator has been retired. Prepare a versioned RFI from the RFI page."
```

Service functions (all non-committing):
- `generate_version(db, assessment, *, omitted, actor) -> ReportSnapshot`: scope not recorded → 409 scope message; unknown omission → 400; build; empty → 409; `sequence = count(rfi rows of assessment) + 1`; `pdf = render_pdf(document, generated_at=datetime.now(timezone.utc), version_label=f"v{sequence}")`; `create_rfi_snapshot(...)` with `source=document["source"]`, `omitted_document_types=document["omitted_document_types"]`.
- `issue_version(db, assessment, snapshot_id, *, actor) -> ReportSnapshot`: `report_snapshots.load_snapshot` (404) and `type == "rfi"` (else 404 `RFI_NOT_FOUND_MESSAGE`); `read_rfi_document` (integrity 500); `metadata["source"] != current_source(...)` → 409 `RFI_STALE_MESSAGE`; `report_snapshots.issue_snapshot(...)`.

Routes (**no release gate on any of them**):

| Method, path | Router | Behaviour |
|---|---|---|
| `GET /assessments/{assessment_id}/rfi` | `web.py`, new `rfi_page` | 404 unknown assessment; renders `pages/rfi.html` (D-P5-6-I). Read-only. |
| `POST /api/assessments/{assessment_id}/rfi/versions` | `snapshots.py`, new `generate_rfi_version` | Form `omit: list[str] = Form(default=[])`, `reviewer_name: str = Form("")`. 404 JSON "Assessment not found"; `RfiError` → `_error(status, message)` after `db.rollback()`; `SnapshotError` likewise. Commit; on commit failure `db.rollback()`, unlink the PDF **and** the sidecar, 500 "The report version could not be saved. Try again." Success 200 JSON `{"snapshot_id", "type": "rfi", "is_issued": false}`, `HX-Redirect: /assessments/{assessment_id}/rfi`, toast "Draft RFI version generated". |
| `POST /api/assessments/{assessment_id}/rfi/versions/{snapshot_id}/issue` | `snapshots.py`, new `issue_rfi_version` | Form `reviewer_name`. Errors as above. Success: commit, same JSON shape with `is_issued: true`, `HX-Redirect` to the RFI page, toast "RFI version issued". |
| `GET /api/assessments/{assessment_id}/rfi/versions/{snapshot_id}/docx` | `snapshots.py`, new `rfi_version_docx` | 404s as above; `read_rfi_document` (500 on integrity); `render_docx(document, generated_at=snapshot.generated_at, version_label=f"v{sequence}")`; `Content-Disposition: attachment; filename="{safe_company}_rfi_v{sequence}_{snapshot.id[:8]}.docx"` (the file route's `safe_company` rule), header `X-RFI-Document-Sha256`. |
| `GET /api/assessments/{assessment_id}/snapshots/{snapshot_id}/file` | existing | Serves the RFI PDF, hash-verified. **One fix:** the sequence lookup for `format == "pdf"` uses `report_snapshots.rfi_snapshot_rows(db, assessment, current_source=None)` when `snapshot.type == RFI_SNAPSHOT_TYPE`, else the existing `snapshot_rows(...)[snapshot.type]`. The filename becomes `…_rfi_v{n}_{id8}.pdf` by the existing format string. |
| `POST /api/assessments/{assessment_id}/snapshots/{snapshot_id}/issue` | existing | Immediately after `load_snapshot`, if `snapshot.type == RFI_SNAPSHOT_TYPE`: `db.rollback()`, 400 `RFI_WRONG_ROUTE_MESSAGE`. Nothing else changes. |
| `POST /api/assessments/{assessment_id}/snapshots` with `type=rfi` | existing | Unchanged: 400 "Unknown report type." |
| `POST /assessments/{assessment_id}/rfi/versions/{snapshot_id}/magic-links` | `magic.py`, new `create_rfi_magic_link` | D-P5-6-H. |

The DOCX is **not** a snapshot: it is rendered from the hash-verified sidecar on each download, as the consultant's editable working copy. Its words are exactly the frozen document's; its bytes are not pinned. **The issued artifact is the PDF.** Named and accepted.

### D-P5-6-G. Rendering: `rfi_export.py` gets additive changes only

`rfi_requests.render_items(document) -> list[dict]` adapts each frozen item to the renderer's existing keys:

```python
priority = "Required" if item["required"] else "Recommended"
ids = [rid for _fw, rid in item["requirements"]]
base = {"item_id": item["item_id"], "priority": priority, "requirement_title": item["title"],
        "evidence_requested": item["request"], "deadline_weeks": DEADLINE_WEEKS[priority],
        "chapter": item["group"]}
document:    base | {"requirement_id": "", "section_ref": "", "current_status": RFI_DOCUMENT_STATUS, "requirements": ids}
requirement: base | {"requirement_id": ids[0], "section_ref": item["control_reference"] or "", "current_status": RFI_REQUIREMENT_STATUS, "requirements": []}
```

`render_pdf`/`render_docx` call `generate_rfi_pdf`/`generate_rfi_docx` with `title`, `company_name`, `introduction`, `evidence_items=render_items(document)`, `response_instructions`, `generated_at`, `framework_label` from the document, and `version_label`.

**Exact additive edits to `app/utils/rfi_export.py`** (the existing parameters, their order and defaults are unchanged; every new PDF string through `S()`):
1. Both generators gain a keyword-only `version_label: str = ""`. PDF: after the "Reference:" line, when set, `pdf.ln(6)` and a centred `S(f"Version: {version_label}")`. DOCX: when set, the metadata run text gains `f"\nVersion: {version_label}"`.
2. `RFI_PRIORITY_COLORS` gains `"Required": (230, 126, 34)` and `"Recommended": (39, 174, 96)`.
3. Cover summary (PDF): after the existing Medium part, append `f"{n} Required"` and `f"{n} Recommended"` when non-zero. DOCX summary: after High, append `f"  |  {n} Required"` when non-zero.
4. `_render_evidence_item`: `requirements = item.get("requirements") or []`; both card rects use height `48 if requirements else 40`; the reference line prints `" | ".join(p for p in (requirement_id, section_ref) if p)` (no bare `" | "`); after the "Evidence Requested" block, when `requirements`, a 7-pt `MID_TEXT` `multi_cell` `S(f"Requested for: {_requested_for(requirements)}")`, where `_requested_for(ids)` is `", ".join(ids)` for up to 12 ids, else `", ".join(ids[:12]) + f" and {len(ids) - 12} more"`.
5. DOCX data row: when `item.get("requirements")`, the Requirement cell is `f"{requirement_title}\nRequested for: {', '.join(requirements)}"` (the **full** list: the editable copy carries every mapping); otherwise unchanged.

No other change to `rfi_export.py`. `tests/test_white_label.py` and `tests/test_p5_8_mechanical_cleanup.py` must pass unmodified.

### D-P5-6-H. Magic-link issuance: the answer to D-P5-5-J. `scope_json` is extended by reference only; `MAX_ITEMS` is not raised; the consultant chooses up to 20 items per link and may create as many links per RFI as needed.

**The fork** ("extends `magic_links.scope_json` (a security boundary) or stays a consultant-side template"). **Decision: extend, minimally.** An RFI link's `scope_json` is **version 2**:

```json
{"items": [{"key": "item-1", "rfi_item_id": "RFI-004", "title": "RFI-004: Incident management procedure / incident response plan"}],
 "rfi": {"assessment_id": "<assessment id>", "snapshot_id": "<issued rfi snapshot id>"},
 "version": 2}
```

serialised with `json.dumps(..., sort_keys=True)`. Version 1 links (`create_link`) are **byte-for-byte unchanged**.

**Why extend rather than stay a template.** A template (pre-filled free-text titles into today's form) loses the binding between an upload and the request item, and so between the upload and the requirements it was requested for. PR-023 wants those mappings visible, and the only structured binding an upload has is its `item_key` (`magic_link.upload_received` metadata). With a version-2 scope, `item_key` → `rfi_item_id` → the immutable, hash-pinned RFI sidecar → `requirements`. P2-5 OQ3 anticipated exactly this ("`scope_json` should reference request-item ids").

**Why this does not widen the security boundary** (each point is tested in scenarios 14-17):
1. **Capability is unchanged.** What a token can do is decided by `item.key` (which upload targets exist) and the row's limits. v2 changes neither. `rfi_item_id` and `rfi` are **never read** by `magic.py`, `resolve_token`, `check_upload_allowed` or `receive_client_upload`, and are never used for authorisation. `resolve_token`, the non-enumerability rules, rate limits, size limits, expiry and revocation are untouched.
2. **Nothing new is shown to the client.** `upload.html` renders only `title` and `key`. The title is `"{rfi_item_id}: {item title}"`: the RFI item number and a framework document label or registry requirement title, all of which the client already holds in the RFI PDF. No company name, no engagement/assessment/snapshot/conclusion/evidence id, no gap text, no outcome word. The ids inside `rfi` sit in the server-side row only, like `engagement_id` already does.
3. **Mappings are referenced, not copied.** `scope_json` carries no requirement IDs. The single source of the mapping is the issued sidecar, which is write-once and hash-verified. There is no second copy to drift or to leak through the link row.
4. **Limits are unchanged**, including `MAX_ITEMS = 20`, `MAX_ITEM_TITLE_CHARS = 200` and title uniqueness.

**Why not raise `MAX_ITEMS`, and why not split automatically.** The item list is readable by anyone holding the token, so the per-link cap bounds what one leaked link exposes. It also keeps the client's choice list usable. RFI items naturally go to different client owners (HR for `hr_security`/`training_records`, IT for `logging_monitoring`/`network_security`, legal for `legal_register`), so several narrower links are the right shape, not one wide one. Auto-splitting a 34-item RFI would mint two or more tokens that are each shown only once, for groupings nobody chose. **So the consultant selects which items go into each link (≤ 20) and can create any number of links per RFI version.** The page shows which items are not yet in any active link (D-P5-6-I), so nothing is silently left out.

**Binding rules:**
- A link can be created only from the **current issued** RFI version (`current_rfi_issue`). A draft, a superseded draft, or an older issued version → 409 `RFI_LINK_NOT_CURRENT_MESSAGE`. The client holds an issued version, so links must match what was issued.
- `link.engagement_id = assessment.engagement_id`. `None` → 409 `RFI_NO_ENGAGEMENT_MESSAGE`. `create_link`'s own checks still apply (engagement missing 404, not active 409). A mixed engagement with several assessments gets separate RFIs and separate links; there is no cross-assessment union (D-P5-5-J reason 1, closed).
- Links already created stay valid when a newer RFI version is issued. They stay bound to their own version and are listed under it.

**Exact changes to `app/services/magic_links.py`:**
1. Extract `create_link`'s validation, **unchanged in order and messages**, into `_validated_titles(db, *, engagement_id, item_titles, expires_in_days, max_uploads, max_total_mb) -> list[str]`, and the insert-plus-audit into `_insert_link(db, *, engagement_id, scope: dict, item_keys: list[str], expires_in_days, max_uploads, max_total_mb, actor, extra_audit: dict | None = None) -> CreatedLink`. `create_link` calls both with a version-1 scope. Its behaviour, stored bytes and audit are identical (`tests/test_magic_links.py` unmodified is the proof).
2. `RFI_SCOPE_VERSION = 2` and
   ```python
   def create_rfi_link(db, *, engagement_id: str, assessment_id: str, snapshot_id: str,
                       rfi_items: list[tuple[str, str]], expires_in_days: int, max_uploads: int,
                       max_total_mb: int, actor: str = "consultant") -> CreatedLink:
   ```
   `rfi_items` is `(rfi_item_id, title)` pairs. Titles go through `_validated_titles` (so ≤ 20, ≤ 200 chars, unique, and the expiry/limit ranges apply). Then every `rfi_item_id` must match `^RFI-\d{3,}$` and be unique, else `MagicLinkValidationError(RFI_UNKNOWN_ITEM_TEXT)` with `RFI_UNKNOWN_ITEM_TEXT = "Choose requested items from this RFI version."` (defined in `magic_links.py`, equal to `rfi_requests.RFI_UNKNOWN_ITEM_MESSAGE`, which re-exports it). Items are `{"key": f"item-{n}", "rfi_item_id": id, "title": title}`. Audit `magic_link.created` metadata = the five v1 keys plus exactly `"rfi_assessment_id"`, `"rfi_snapshot_id"`, `"rfi_item_ids"`.
3. Nothing else changes: `scope_items`, `receive_client_upload`, `magic_link_rows`, `resolve_token`, every constant.

**`rfi_requests.create_client_link(db, assessment, snapshot_id, *, item_ids, expires_in_days, max_uploads, max_total_mb, actor) -> CreatedLink`:** no engagement → 409; `load_snapshot` + `type == "rfi"` → 404; not the current issue → 409; `read_rfi_document` (500 on integrity); `item_ids` de-duplicated in given order; any id not in the document → `RfiError(RFI_UNKNOWN_ITEM_MESSAGE, 422)`; titles are `f"{item_id}: {title}"`, and if longer than `MAX_ITEM_TITLE_CHARS` they are cut to 199 characters plus `"…"`; then `magic_links.create_rfi_link(...)`.

**Route `POST /assessments/{assessment_id}/rfi/versions/{snapshot_id}/magic-links`** in `app/routers/magic.py` (so every token-minting route lives in the one router with `_CONSULTANT_HEADERS`). Form: `item_ids` (multi-valued, `form.getlist`), `expires_in_days` (default 7), `max_uploads` (default 20), `max_total_mb` (default 100), parsed with the existing `_form_int` and its messages, and `reviewer_name`. Actor `conclusion_review.reviewer_actor(reviewer_name)`. It renders the new partial `partials/rfi_links.html` with `rfi_requests.page_context(...)` plus `new_link_url` (shown once) or `error`, always with `_CONSULTANT_HEADERS`. Status codes follow the existing consultant route: unknown assessment, `MagicLinkNotFound` and `RfiError` 404 → 404; `SnapshotIntegrityError` → 500; every other `MagicLinkError`/`RfiError` → 200 with the error shown; success → commit, 200. Any error → `db.rollback()` first.

### D-P5-6-I. The RFI page and request tracking (consultant-only)

`rfi_requests.page_context(db, assessment) -> dict` with keys `assessment`, `scope_recorded`, `preview` (`build_rfi_document(db, assessment)` if scope is recorded, else `None`), `mapped_hints` (`{document_type: (mapped, total)}`), `versions` (`rfi_snapshot_rows(db, assessment, current_source=current_source(...))`, or `[]` if scope is not recorded), `current_issue` (the snapshot or `None`), `current_items` (the current issue's document items, from its sidecar), `links` (`RfiLinkRow` list), `coverage` (`{rfi_item_id: [link id_prefix of active links bound to the current issue that include it]}`), `received` (`{(snapshot_id, rfi_item_id): [ {evidence_id, filename, status, uploaded_at} ]}`), `reviewer_name` (the snapshots-page rule: the latest `consultant:` actor on an `rfi` snapshot event, else `""`).

- `mapped_hints`: `keys = {(u.framework_id, u.requirement_id) for u in EvidenceUse rows with assessment_id == assessment.id}`; for each preview document item, `(sum(tuple(r) in keys for r in requirements), len(requirements))`. Read-only. Never written anywhere.
- `RfiLinkRow` (frozen dataclass): `link_id, id_prefix, status, created_at, expires_at, snapshot_id, sequence, items: tuple[tuple[str, str], ...]` (`(rfi_item_id, title)`), `uploads_used, max_uploads`. Rows: `MagicLink` of `assessment.engagement_id` whose parsed `scope_json` has `version == 2` and `rfi.assessment_id == assessment.id`, ordered `created_at` desc then `id` desc; `status`/usage from `magic_links.link_status`/`link_usage`. None if the assessment has no engagement.
- `received`: `AuditEvent` rows with `entity_type == "magic_link"`, `action == "magic_link.upload_received"`, `entity_id` in those link ids, ordered by `rowid`; `item_key` → that link's `rfi_item_id`; `evidence_id` → `db.get(Evidence, …)` (skip if missing), `filename = original_filename`, `status`.

**`app/templates/pages/rfi.html`** (new; extends `base.html`; styled like `pages/report_snapshots.html`; autoescaped; no `|safe`, no `CyberAssess`). Required elements and exact copy:
1. Breadcrumb to the assessment, `<h1>` "Request for information", the consultant-name input `#reviewer-name`.
2. Scope not recorded → `<div data-rfi-scope-required>` "Record the assessment scope before preparing an RFI." with a link to `/assessments/{id}?tab=scope`, and nothing else below.
3. `<section data-rfi-preview>`: note "Only conclusions you have individually approved as Insufficient evidence are included. AI proposals, scores and findings are never included." Each document item: `<li data-rfi-item="{{ item.item_id }}" data-rfi-kind="document">` with title, Required/Recommended, reason, every mapped id, a checkbox `<input type="checkbox" name="omit" value="{{ item.document_type }}" data-rfi-omit>` labelled "Omit (already received)", and `<span data-rfi-mapped>Evidence already mapped for {m} of {n} requirements</span>`. Requirement items: `data-rfi-kind="requirement"`, requirement id, title, group, request text. The generate form `<form data-rfi-generate-form hx-post="/api/assessments/{id}/rfi/versions" hx-include="#reviewer-name, [data-rfi-omit]" hx-swap="none">` with the button "Generate new RFI version".
4. `<section data-rfi-versions>`: one `<tr data-rfi-version-row data-snapshot-id=… data-snapshot-state=…>` per version (v#, state, generated, issued, SHA-256 prefix, "Source data changed since generation" when `source_changed`, links "PDF" → the file route and "DOCX" → the docx route, and an Issue form `data-rfi-issue-control` posting to the issue route with `hx-confirm="Issue this RFI version? Issued versions are permanent and cannot be changed or withdrawn."` only when `row.issuable`).
5. When `current_issue`: `{% include "partials/rfi_links.html" %}`. The partial is `<section id="rfi-links" data-rfi-links>`: the one-time URL in `<input data-rfi-new-link readonly>` with "Copy this link now. It will not be shown again."; the error box; `<form data-rfi-link-form hx-post="/assessments/{id}/rfi/versions/{current_issue.id}/magic-links" hx-target="#rfi-links" hx-swap="outerHTML" hx-include="#reviewer-name">` with one checkbox `name="item_ids"` per current item, the note "A link can include up to 20 items. Create several links to send different items to different people.", and the three limit inputs (defaults 7/20/100); per current item, `data-rfi-coverage="{{ item_id }}"` listing covering link prefixes or `<span data-rfi-unsent>Not yet in an active client link</span>`, and received files `<li data-rfi-received>` with filename and status linking to `/evidence/{evidence_id}`; then a table of `data-rfi-link-row` rows (prefix, version, status, items, usage, expiry). Revocation stays on the engagement page (existing route).

**Entry points.** `partials/scope_complete.html`: in the Evidence Request card header, next to the PDF/DOCX links, add `<a href="/assessments/{{ assessment.id }}/rfi" data-rfi-link …>Prepare RFI</a>`. `partials/report_summary.html`: delete the `{% if rfi %}…{% endif %}` header block (RFI PDF/DOCX links); replace section H's body (from `<div id="rfi-section">` to its closing `</div>`) with `<a href="/assessments/{{ assessment_id }}/rfi" data-rfi-link …>Open RFI</a>` and change the subtitle to "Prepare a versioned evidence request from the scope and your approved conclusions." Keep the heading "Request for Information (RFI)". Everything else in `report_summary.html` is unchanged (P5-2's `Live PDF` and `/snapshots"` guards stay green).

### D-P5-6-J. The legacy RFI is retired (the P5-2 D-P5-2-I pattern). `rfi_documents` is frozen history.

- `web.generate_rfi_web`, `download_rfi_pdf`, `download_rfi_docx` stay **registered with the same paths and methods** (the archive guard and `test_retention`'s inventory still cover the POST). Each body is only `raise HTTPException(410, LEGACY_RFI_RETIRED)` (imported from `rfi_requests`): no DB access, no gate, no writes. 410, not 404, so automation still calling them learns the route was retired.
- **Deleted:** `app/services/rfi_generator.py` (its only non-test caller is gone; it was the GapItem + desk-review + LLM path) and `app/templates/partials/rfi_generated.html`.
- **Frozen, not dropped:** `app/models/rfi.py` and the `rfi_documents` table are unchanged (zero diff). Nothing writes or reads them any more except the retention purge, the legacy-migration machinery and dev scripts. Existing rows keep whatever a consultant generated before, as inert history; they are not migrated into snapshots, because they were rendered from unapproved AI output and must not acquire an "issued version" status now.
- `web.py` drops `from app.models.rfi import RFIDocument` and `web.report_summary`'s `RFIDocument` query and `"rfi"` context key.
- **Why retire rather than keep the downloads read-only:** a stored legacy RFI is GapItem-sourced AI output. Keeping it downloadable next to the real RFI would present two "RFIs" with different provenance, and the consultant already holds any file they sent. This matches P5-2's choice for the `GapItem` review queue.

### D-P5-6-K. No schema change, no Alembic revision

`report_snapshots.type` is a free `String(30)` with no CHECK constraint, the sidecar is a file, the RFI record lives in the snapshot row plus audit metadata (D2), `magic_links.scope_json` is `Text`, and `rfi_documents` is left as it is. **No migration.** `alembic heads` after this task must equal the value recorded in Step 0. `git diff --stat main -- alembic app/models` must be empty.

### D-P5-6-L. What is deliberately not linked or automated (D8, D-P5-D)

- No `EvidenceUse` is created, suggested or pre-selected from an RFI item, a link, or an upload. The page shows what was requested and what arrived. Mapping stays the consultant's P2-1 action on the evidence page.
- No RFI item is closed automatically. "Open" means "not omitted by the consultant".
- PR-023's "each mapping is visible in the Workpaper" is met, as today, through the `EvidenceUse` rows the consultant confirms. Showing "requested as RFI-00N" in the Workpaper is open question 1, not this task.

### D-P5-6-M. Existing tests and scripts: the only permitted changes

An existing test may be changed **only** for one of these reasons, **only** in the stated way, and each changed function is listed in Results with its code:
- **(r1) Retired legacy RFI route.** A test calls `/assessments/{id}/rfi/pdf`, `/rfi/docx` or `/generate-rfi` expecting anything other than 410. Remove that path from the loop or call, and add a separate assertion that it returns 410 with `detail == LEGACY_RFI_RETIRED`. Keep every other assertion. Expected: `tests/test_correctness_bundle.py` scenario 7 (the `/rfi/pdf` entry in its release-gate loop) and `tests/test_p5_2_reader_migration.py` scenario 8 (`/rfi/pdf`, `/rfi/docx`).
- **(r2) Deleted module.** `tests/test_remaining_llm_call_sites.py`: delete exactly `test_rfi_call_parses_valid_json_and_preserves_raw_text`, `test_rfi_call_uses_empty_enhancements_for_non_json_response` and `test_rfi_evidence_items_exclude_compliant_and_not_assessed_gaps`. Nothing else in that file.
- Anything else that fails is a **stop-and-report**. Expected to pass unchanged: `test_magic_links.py`, `test_report_snapshots.py` (including the two-section count), `test_white_label.py`, `test_p5_8_mechanical_cleanup.py`, `test_p5_5_scoping_evidence.py`, `test_retention.py` (the new POST routes join its archive loop automatically), `test_data_integrity.py`, `test_longitudinal_demo.py`, `test_pdf_updates.py`, and the rest of `test_p5_2_reader_migration.py`.
- Scripts: none changed. `scripts/score_test_results.py` keeps reading `RFIDocument` (it now reads frozen rows only; open question 5).

### D-P5-6-N. Coordination and what this task does not touch

- **P5-2 (merged first):** this task calls `build_approved_report` and uses `ApprovedRow`, and changes nothing in `approved_report.py`, `review_gate.py`, `reports.py`, `pdf_export.py`, `report_content.py`, `integrated_reports.py` or P5-2's parts of `snapshots.py` (generate/issue gates, `generated_after`). In `snapshots.issue_snapshot_route` the only edit is the RFI type refusal placed immediately after `load_snapshot` (before P5-2's gate and stale check).
- **P5-4 (may be in flight):** it owns `question_engine.py` and the questionnaire parts of `web.py`/`assessment_detail`. This task's `web.py` edits are limited to: the `RFIDocument` import, `report_summary`'s RFI query and context key, the three legacy RFI route bodies, and the new `rfi_page` placed directly after them. If P5-4 lands first, rebase and keep both sides.
- **Not touched:** `app/models/*`, `alembic/*`, `app/services/approved_report.py`, `analysis_pipeline.py`, `conclusion_review.py`, `findings.py`, `workpaper.py`, `evidence.py`, `scope_profiler.py`, `retention.py`, `app/frameworks/*`, `app/utils/pdf_export.py`, `app/utils/evidence_checklist_export.py`, `app/routers/analysis.py`, `reports.py`, `review.py`, `app/templates/magic/*`, `partials/magic_links.html`, every `scripts/*` file.

### D-P5-6-O. Consistency audit against the standing guards

1. No `relationship(` in `app/models/`; `app/models` and `alembic` zero diff.
2. No template contains `overall_score`, `CyberAssess` or `|safe`. `report_summary.html` keeps `Live PDF` and `/snapshots"` and gains no `Download PDF`/`PDF Report`. `pages/rfi.html` and `partials/rfi_links.html` contain no apostrophe in new copy (the P5-2 convention).
3. `rfi_export.py` contains no `CyberAssess`; every new PDF string goes through `S()`.
4. `report_snapshots.py` keeps a single `.open(` (in `_write_file`) and no `delete`; `SNAPSHOT_TYPES`, `ASSESSMENT_SNAPSHOT_TYPES`, `ISSUE_SQL`, `MANIFEST_SCHEMA_VERSION` and `source_manifest` are unchanged.
5. `magic_links.MAX_ITEMS == 20`; `create_link`'s signature and version-1 output are unchanged.
6. `rfi_requests.py` contains none of: `GapItem`, `review_gate`, `require_review_approval`, `release_state`, `is_released`, `latest_release_event`, `review_status`, `llm_client`, `DeskReviewFinding`, `scoped_findings`, `.commit(`, `delete`. `GapReport` appears exactly twice: its import and the one `db.query(GapReport.id)` existence check (D-P5-6-B).
7. Every new route has `{assessment_id}` in its path and sits on an archive-guarded router; `app/main.py` is unchanged.

## Required approach

1. **Step 0** checks, recorded in Results.
2. `app/services/magic_links.py`: `_validated_titles`, `_insert_link`, `create_link` rewired (behaviour identical), `RFI_SCOPE_VERSION`, `RFI_UNKNOWN_ITEM_TEXT`, `create_rfi_link` (D-P5-6-H). Run `tests/test_magic_links.py` before going further; it must pass unmodified.
3. `app/services/report_snapshots.py`: D-P5-6-E items 1-7.
4. `app/utils/rfi_export.py`: D-P5-6-G edits 1-5. Run `test_white_label.py` and `test_p5_8_mechanical_cleanup.py`.
5. `app/services/rfi_requests.py` (new): constants and `RfiError` (D-P5-6-C/F), `build_rfi_document`, `current_source`, `canonical_bytes`, `render_items`, `render_pdf`, `render_docx`, `generate_version`, `issue_version`, `create_client_link`, `page_context`, `RfiLinkRow`.
6. `app/routers/snapshots.py`: `generate_rfi_version`, `issue_rfi_version`, `rfi_version_docx`, the RFI refusal in `issue_snapshot_route`, the RFI sequence lookup in `snapshot_file_route`.
7. `app/routers/magic.py`: `create_rfi_magic_link`.
8. `app/routers/web.py`: `rfi_page`; retire the three legacy routes; drop `RFIDocument` from `report_summary` and the imports.
9. Templates: `pages/rfi.html` (new), `partials/rfi_links.html` (new), `partials/scope_complete.html` (entry link), `partials/report_summary.html` (header links removed, section H body replaced); delete `partials/rfi_generated.html`. Delete `app/services/rfi_generator.py`.
10. Existing tests under D-P5-6-M, then `tests/test_p5_6_rfi_rebuild.py` (new). Copy (don't import) the fixture pattern from `tests/test_p5_2_reader_migration.py` (or `tests/test_pdf_updates.py` if P5-2's file differs): an Alembic-built, FK-enforcing SQLite `db`, `http` with `app.dependency_overrides[get_db]`, `upload_root` patched onto `settings.upload_dir`, the seed and pipeline-stub helpers, and `_pdf_text` (pdfplumber). For links, copy the helper pattern from `tests/test_magic_links.py`. Create eligible Conclusions through the real pipeline stubs plus `conclusion_review.decide` (approved/edited), never by hand, except the one legacy-bulk revision case. No test may touch `data/dpdpa.db`, the real `uploads/` or the network.
11. `tasks/todo.md`: tick P5-6 in the existing Phase 5 style with a link to this handoff's Results. Don't edit the phase summary line.

## Key files

| File | Why |
|---|---|
| `app/services/rfi_requests.py` (new) | The RFI document, source binding, versioning, links, page context (D-P5-6-B…I) |
| `app/services/report_snapshots.py` | `rfi` type, sidecar, `create_rfi_snapshot`, `read_rfi_document`, `rfi_snapshot_rows`, `current_rfi_issue`, `_store(extra_metadata=)` (D-P5-6-E) |
| `app/services/magic_links.py` | `create_rfi_link`, v2 scope by reference (D-P5-6-H) |
| `app/utils/rfi_export.py` | Additive rendering edits (D-P5-6-G) |
| `app/routers/snapshots.py` | RFI generate/issue/DOCX routes; generic-route RFI handling (D-P5-6-F) |
| `app/routers/magic.py` | RFI link route (D-P5-6-H) |
| `app/routers/web.py` | `rfi_page`; legacy RFI routes → 410; `report_summary` RFI removal (D-P5-6-I/J) |
| `app/templates/pages/rfi.html`, `partials/rfi_links.html` (new); `partials/scope_complete.html`, `partials/report_summary.html`; `partials/rfi_generated.html` (deleted) | UI |
| `app/services/rfi_generator.py` (deleted) | Legacy AI RFI (D-P5-6-J) |
| `tests/test_p5_6_rfi_rebuild.py` (new) | The contract |
| `tests/test_correctness_bundle.py`, `tests/test_p5_2_reader_migration.py`, `tests/test_remaining_llm_call_sites.py` | D-P5-6-M only |
| `app/models/*`, `alembic/*`, `approved_report.py`, `pdf_export.py`, `evidence_checklist_export.py`, `scope_profiler.py`, `retention.py`, `magic/*` templates, `partials/magic_links.html`, `scripts/*` | **Not modified** |

## Non-goals

- No schema change, no Alembic revision, no data migration of `rfi_documents`.
- No change to the report release gate, `approved_report.py`, the gap-report/workpaper/integrated snapshot types or their routes (beyond the two RFI-type branches in D-P5-6-F).
- No automatic evidence-to-requirement mapping, no mapping suggestions, no automatic closure of request items (D-P5-6-L).
- No increase to any magic-link limit; no change to the client upload page, `receive_client_upload`, v1 links or the engagement-page link form.
- No consultant-authored free-text RFI items or editable introduction (open question 2).
- No change to the P5-5 evidence-checklist PDF/DOCX exports (open question 3).
- No link revocation from the RFI page (the engagement page's existing route does it).
- No LLM call anywhere in the RFI path.

## Test scenarios

All in `tests/test_p5_6_rfi_rebuild.py`. Each test's docstring starts with `Scenario N:`.

1. **Pre-analysis, document items only, determinism.** ISO-only assessment, scope saved with `{}` answers, no `GapReport`: `build_rfi_document` has 30 items, all `kind == "document"`, `item_id`s `RFI-001`…`RFI-030` in D-P5-5-C order, `required` and `title`/`request` equal to the checklist's, `requirements` pairs all `["iso27001", id]` in `maps_to` order, `group == "Documents requested"`, `conclusion_id is None`; top-level key set exactly as D-P5-6-C; `totals == {"items": 30, "documents": 30, "requirements": 0, "required": <count of required>}`. `canonical_bytes` of two builds are identical; the document contains no ISO-8601 timestamp.
2. **Merged request, framework attribution.** DPDPA + ISO + NIST, `{}` answers: exactly one item with `document_type == "breach_procedure"`; its `requirements` pairs are DPDPA's `BN.NOTIFY.*` attributed to `"dpdpa"`, then the ISO ids to `"iso27001"`, then the NIST ids to `"nist_csf"`, in the checklist's `maps_to` order, with no duplicates. A monkeypatched checklist item mapping to an unknown id raises the exact `ValueError`.
3. **Requirement items: exact filter.** DPDPA assessment with `applicable_requirements` restricted to six requirements, analysed through the pipeline stub. Make: (a) one consultant-approved `insufficient_evidence` with gaps "Consultant gap A"; (b) one consultant-edited to `insufficient_evidence` with gaps "Consultant gap B"; (c) one approved `non_compliant`; (d) one pending AI `insufficient_evidence` whose AI gaps are "AI gap sentinel"; (e) one approved `insufficient_evidence` then reopened; (f) one legacy-bulk approved `insufficient_evidence` (actor `"Legacy Reviewer"`); plus an approved `insufficient_evidence` Conclusion **outside** scope. Only (a) and (b) become requirement items, after all document items, in registry order, each with `title` = registry title, `request` = the consultant text, `requirements == [["dpdpa", id]]`, `control_reference`, `group == row.chapter_title`, `conclusion_id`/`conclusion_version` equal to the Conclusion's. `canonical_bytes` contains neither "AI gap sentinel", nor the outcome values `non_compliant`, `partially_compliant` or `insufficient_evidence`, nor any score. With `included_rows` monkeypatched to return one row whose `gap_description` is `"   "`, `request == RFI_REQUIREMENT_FALLBACK`.
4. **Omission.** Omitting two valid document types removes them, numbering stays contiguous, `omitted_document_types` is sorted, and `source` is identical to the un-omitted build. `POST …/rfi/versions` with an unknown `omit` → 400 `RFI_UNKNOWN_OMISSION_MESSAGE`, no row, no file. Omitting every document type on an assessment with no requirement items → 409 `RFI_EMPTY_MESSAGE`, nothing written.
5. **Independent of release (D-P5-6-A).** On one assessment where `approved_report.is_released(db, a)` is False, `review_status` is hand-set to `"approved"`, and (separately) an assessment where one framework failed analysis: generate → 200, issue → 200, PDF file route → 200, DOCX → 200, link creation → 200. A second assessment with **no** `GapReport` (scope only) → the same five succeed with document items only.
6. **Scope and existence gates.** Unknown assessment → 404 on every new route. Scope not recorded (`scope_answers is None`) → generate 409 `RFI_SCOPE_REQUIRED_MESSAGE`, and the RFI page shows `data-rfi-scope-required` and no generate form.
7. **Storage.** After one generate: one `ReportSnapshot` with `type == "rfi"`, `format == "pdf"`, `is_issued` False; the PDF at `storage_path` and the sidecar at `rfi_document_path(snapshot)` both exist; the sidecar bytes equal `canonical_bytes(build_rfi_document(db, a, omitted=…))`; the generated event's metadata key set is exactly the ten P3-2 keys plus `document_sha256`, `document_size_bytes`, `omitted_document_types`, `sha256` matches the PDF, `document_sha256` matches the sidecar, and `metadata["source"]` has exactly the D-P5-6-D key set. `report_snapshots._write_file` on the sidecar path raises `FileExistsError`. A failure injected into `_store` leaves neither file nor row. A failure injected into the router's `db.commit` → 500 with both files removed.
8. **Versioning and issue lifecycle.** Generate v1 and v2: two rows, `rfi_snapshot_rows` sequences 1 and 2, v1's PDF and sidecar bytes unchanged by v2. Issue v1 → 409 "A newer version of this report exists. Issue the newest version, or generate a new one." Issue v2 → 200 with one `report_snapshot.issued` event; issuing v2 again → 409 "This version is already issued."
9. **Staleness (PR-054).** Generate a draft, then separately: (a) approve another in-scope `insufficient_evidence` Conclusion; (b) reopen a quoted Conclusion; (c) change a scope answer that changes the checklist (`ISO.SCP.4 = fully_remote`); (d) change the framework selection. Each → issue 409 `RFI_STALE_MESSAGE`, nothing issued. (e) Changing only `company_name` → issue 200 (named limitation). After an issue, performing (a) leaves the issued PDF and sidecar byte-identical and sha-verified, marks the row `source_changed`, and the file route still serves it; generating and issuing a new version then succeeds.
10. **Rendered PDF and DOCX.** For the scenario-3 assessment plus DPDPA document items: the PDF text (pdfplumber) contains "RFI-001", "Version: v1", "Required", "Requested for:", "Documents requested", "Consultant gap A", a DPDPA chapter title, and no "AI gap sentinel", no "%" score, no "Non-Compliant". A document item mapping more than 12 ids renders "and N more". The DOCX (python-docx) contains the full requirement id list for that item and "Version: v1". Two DOCX downloads of the same version have identical paragraph and table text. `inspect.signature(generate_rfi_pdf)` still starts with the seven original parameters in order, and `version_label` is keyword-only.
11. **Integrity.** Corrupt the sidecar of an issued version → its DOCX → 500 `INTEGRITY_MESSAGE` and link creation from it → 500, with no link written. Corrupt the sidecar of a draft → issuing it → 500, nothing issued. Corrupt an RFI PDF → the file route → 500 (existing behaviour).
12. **Generic snapshot routes.** `POST /snapshots` with `type=rfi` → 400 "Unknown report type."; `POST /snapshots/{rfi_id}/issue` → 400 `RFI_WRONG_ROUTE_MESSAGE` and the row stays a draft; the snapshots page still has exactly two `data-snapshot-type=` sections and no RFI row; the file route's `Content-Disposition` for an RFI PDF contains `_rfi_v1_`.
13. **Client link from the current issue.** Issue v1 of a DPDPA + ISO RFI whose engagement is active. Create a link for `RFI-002`, `RFI-005` and one requirement item: response 200 with `data-rfi-new-link`, headers `Cache-Control: no-store` and `Referrer-Policy: no-referrer`; exactly one new `MagicLink` whose `scope_json` equals the D-P5-6-H v2 shape exactly (keys, `item-1..3`, titles `"RFI-00N: …"`, `rfi.assessment_id`, `rfi.snapshot_id`), serialised with `sort_keys=True`; the `magic_link.created` event's metadata key set is the five v1 keys plus the three `rfi_*` keys. The token appears in no DB column or audit row.
14. **The client sees nothing new.** `GET /magic/{token}` lists exactly the three titles, and its body contains none of: the assessment id, the snapshot id, any conclusion id, the engagement id, the company name, "Consultant gap", "insufficient", "Conclusion", "approved". An upload against `item-3` → 200; the `magic_link.upload_received` metadata key set is exactly the v1 set; `change_reason` is "Client upload via magic link for requested item: " + the item-3 title; **no `EvidenceUse` row is created** (count before and after).
15. **Link limits and binding.** 21 item ids → "A link can request at most 20 items.", no link; no item ids → "Add at least one requested item."; an id not in the version → `RFI_UNKNOWN_ITEM_MESSAGE`, no link; from a draft, a superseded draft, or an older issued version after a newer one is issued → `RFI_LINK_NOT_CURRENT_MESSAGE`; an assessment with `engagement_id = None` → `RFI_NO_ENGAGEMENT_MESSAGE`; an archived engagement → 409 `ARCHIVED_READ_ONLY` from the guard. In every refused case the `MagicLink` and audit counts are unchanged. `magic_links.MAX_ITEMS == 20`.
16. **Several links per RFI and coverage.** A 34-item RFI (ISO + NIST, `{}` answers): link A with 20 items, link B with the other 14 → the page shows every current item with a `data-rfi-coverage` prefix and no `data-rfi-unsent`. Revoke link B through the existing engagement route → exactly those 14 items show `data-rfi-unsent`. An upload through link A appears as `data-rfi-received` under the right item with a link to `/evidence/{id}`.
17. **Version-1 links are untouched.** `create_link` still stores the exact P2-5 v1 `scope_json` and audit key set; a v1 link and a v2 link coexist in `magic_link_rows` (titles listed for both) and the RFI page lists only the v2 link. `tests/test_magic_links.py` passes unmodified (full suite).
18. **Legacy retirement.** With a seeded `RFIDocument`: `POST /assessments/{id}/generate-rfi`, `GET /assessments/{id}/rfi/pdf`, `GET /assessments/{id}/rfi/docx` → 410 `LEGACY_RFI_RETIRED`; the `RFIDocument` row is unchanged and the row count is unchanged. `importlib.util.find_spec("app.services.rfi_generator") is None`; `partials/rfi_generated.html` does not exist; `app/models/rfi.py` still exists.
19. **Entry points.** The report tab (a released assessment) contains `href="/assessments/{id}/rfi"` with `data-rfi-link` and contains none of "Generate RFI", `/rfi/pdf`, `/rfi/docx`, `generate-rfi`; it still contains `Live PDF` and `/snapshots"`. The scope tab of a scoped assessment contains `data-rfi-link`.
20. **The RFI page.** Preview shows `data-rfi-item` per item with `data-rfi-kind`, `data-rfi-omit` only on document items, and `data-rfi-mapped` reading "Evidence already mapped for 1 of N requirements" after one `EvidenceUse` is created for one of that item's requirements (and the RFI document is unchanged by it). The versions section shows `data-rfi-issue-control` only on the issuable draft, and the link form only when a current issue exists. No `|safe` and no `CyberAssess` in either new template.
21. **Retention.** Following the minimal archive-and-purge setup of `tests/test_retention.py`, purging an engagement whose assessment has an issued RFI version and a v2 link removes the `rfi` row, the PDF, the sidecar and the link.
22. **Guards (D-P5-6-O).** Every checkable item by reading source: the forbidden-token list for `rfi_requests.py`; `SNAPSHOT_TYPES`/`ASSESSMENT_SNAPSHOT_TYPES`/`ISSUE_SQL`/`MANIFEST_SCHEMA_VERSION` values; `inspect.signature(magic_links.create_link)` unchanged; no `relationship(` under `app/models`; `git diff --stat main -- app/models alembic app/services/approved_report.py app/utils/pdf_export.py app/services/scope_profiler.py app/services/retention.py` empty (via `subprocess`, with `grep`, not `rg`); `alembic heads` equals the Step 0 value.

## Done criteria

- `tests/test_p5_6_rfi_rebuild.py` passes. `.venv/bin/pytest -q` passes in full: **baseline (measured in Step 0) − 3 (the deleted `rfi_generator` tests) + N passed, 9 skipped**, with only the documented exceptions: the fresh-worktree teardown error from `tests/conftest.py::_guard_dev_database_untouched` if it appears, the two working-tree guards (`test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged`, which protects `web.py`, `magic_links.py`, `report_snapshots.py` and `magic.py` among others, and `test_retention.py::test_scenario_13_only_new_retention_test_file_changes`) failing **only** while uncommitted, and `test_longitudinal_demo.py::test_scenario_9`'s known ordering flake if it appears.
- `tests/test_magic_links.py`, `tests/test_report_snapshots.py`, `tests/test_white_label.py`, `tests/test_p5_8_mechanical_cleanup.py`, `tests/test_retention.py` pass **unmodified**.
- `git diff --stat main -- tests/` shows only the new file and the D-P5-6-M files; every changed test function appears in Results with its reason code.
- `git diff --stat main` touches only `## Key files` (plus `tasks/todo.md` and this handoff). `alembic heads` equals Step 0's value.
- **Smoke test** (record outputs in Results). Fresh Alembic-built SQLite DB, in-process ASGI `TestClient` if a socket bind is refused; analyzers patched.
  1. ISO + NIST assessment in an active engagement, scope saved with `ISO.SCP.4=fully_remote`. `POST /api/assessments/{id}/rfi/versions` → paste the JSON; paste the generated event's metadata and `totals`.
  2. `POST …/rfi/versions/{id}/issue` → paste the JSON. Then create two client links (20 + 14 items) → paste each link's `scope_json` with the token-bearing URL removed.
  3. Paste the first 40 lines of the RFI PDF text and the `GET /magic/{token}` body's item list.
  4. Run a DPDPA analysis on a second assessment, approve one Conclusion as `insufficient_evidence` without releasing, generate an RFI → paste the requirement item from the sidecar. Try to issue the older draft after approving a second one → paste the 409 body.
  5. `GET /assessments/{id}/rfi/pdf` → paste the 410 body.
  6. **Browser check** if a browser is available: the RFI page preview, the versions table and the link form. If none, say so. Do not claim it.

## Rollback

- **Code:** `git revert`. The legacy generator and its downloads return (the downloads behind P5-2's release gate). `rfi_documents` was never touched, so its rows are exactly as before.
- `rfi` snapshot rows stay in `report_snapshots` with their files. The reverted `snapshot_rows` ignores unknown types, so the snapshots page is unaffected; the reverted `snapshot_file_route` would raise `KeyError` for an RFI PDF (it indexes `snapshot_rows(...)["rfi"]`), so say in the revert PR that RFI versions become undownloadable through the app until re-applied. The files remain on disk and are purged with the assessment as before.
- Version-2 magic links keep working after a revert: every reader uses only `items[].key/title`, and the extra keys are ignored.
- No schema change, nothing to downgrade.

## Open questions (deliberately flagged, not resolved here)

1. **Request mappings in the Workpaper.** PR-023's acceptance says each mapping is visible in the Workpaper. Today that is true through the consultant's `EvidenceUse` rows. Showing "requested as RFI-00N in version vK" beside each requirement in the Workpaper would make the request side visible too. It touches `workpaper.py` and belongs with PR-026's evidence-lifecycle work.
2. **Consultant-authored RFI text.** The introduction and instructions are fixed constants, and a consultant cannot add an ad hoc item (for example, evidence for a pending proposal they have not decided yet). Either needs a stored, versioned draft field that joins the source manifest.
3. **The P5-5 evidence-checklist PDF/DOCX** remains an unversioned, live export beside the versioned RFI. Retire it, or relabel it "working list", once consultants use the RFI.
4. **Mapping suggestions from received uploads.** An upload against an RFI item knows which requirements it was requested for. Offering those as one-click `EvidenceUse` suggestions (never automatic, D-P5-D) would save the consultant work; it needs the evidence page's suggestion UI.
5. **`scripts/score_test_results.py`** scores "RFI relevance" from `RFIDocument`, which is now frozen. Port it to read the latest `rfi` sidecar, or drop that metric.
6. **A company rename** does not stale an RFI draft (D-P5-6-D). Bind a name hash if that matters.
7. **Deadlines** are fixed at 2 weeks (Required) and 4 weeks (Recommended), and no due date is stored. A consultant-set response date per version would need a stored field.

## Report back

Append a `## Results` section to this file containing:
- Step 0's outputs (the symbol checks, the `ApprovedRow` field list, the test-reference list and the Alembic head) and the baseline you measured.
- The shipped constants, messages and signatures, copied from the code: every `RFI_*` constant and message in `rfi_requests.py`, `LEGACY_RFI_RETIRED`, `RFI_SNAPSHOT_TYPE`, `RFI_DOCUMENT_SUFFIX`, `RFI_SCOPE_VERSION`, `RFI_UNKNOWN_ITEM_TEXT`, and the signatures of `build_rfi_document`, `current_source`, `canonical_bytes`, `render_items`, `generate_version`, `issue_version`, `create_client_link`, `page_context`, `create_rfi_snapshot`, `read_rfi_document`, `rfi_snapshot_rows`, `current_rfi_issue`, `create_rfi_link`, `_validated_titles`, `_insert_link`, `generate_rfi_pdf`, `generate_rfi_docx`, and the `RfiLinkRow` fields.
- The route table as implemented (method, path, success code, every error code actually returned).
- The D-P5-6-M list of every existing test you changed, with its reason code.
- `pytest -q` output for the new file and for the full suite, with the baseline and the working-tree-guard note.
- The smoke outputs.
- Anything this document got wrong about the current code. **Name it and stop if it forces a design change. Do not pick an alternative.**

Commits and PRs for this task carry **no** `Co-Authored-By: Claude` trailer and no "Generated with Claude Code" footer. Codex cannot commit (its sandbox refuses to write `.git`). Leave the tree uncommitted, and the reviewing session commits on your behalf.

## Results

### Step 0 and contract verification

The merged P5-2 implementation matches every referenced symbol and field. `app/services/approved_report.py` has `ApprovedRow`, `ApprovedReport`, `build_approved_report(db, assessment)`, `release_state(db, assessment)`, `is_released(db, assessment)`, and `in_scope_requirement_ids`; `ApprovedRow` fields are `id`, `conclusion_id`, `conclusion_version`, `framework_id`, `requirement_id`, `requirement_title`, `chapter`, `chapter_title`, `control_reference`, `compliance_status`, `current_state`, `gap_description`, `risk_level`, `remediation_action`, `remediation_priority`, `evidence_quote`, `decision`, `decided_by`, `decided_at`, `remediation_effort`, `timeline_weeks`, `maturity_level`, `root_cause_category`, and `evidence_confidence`. No P5-2 symbol or field discrepancy forced a design change.

Step 0 measured `2 failed, 623 passed, 9 skipped, 247 warnings in 94.02s`. The baseline failures were the known longitudinal scenario-9 ordering flake and the known P5-4 scenario-13 structural-guard fragility. The P5-2 handoff's claim that its migration test contained RFI route references was stale: the merged `tests/test_p5_2_reader_migration.py` does not contain those references. This did not affect any P5-2 symbol/field contract, so implementation continued. Alembic head was `8b2d5f7e1c34 (head)`.

### Shipped API and data contract

`app/services/rfi_requests.py` ships these constants/messages: `RFI_DOCUMENT_SCHEMA_VERSION = 1`, `RFI_ITEM_ID_FORMAT = "RFI-{n:03d}"`, `RFI_DOCUMENTS_GROUP = "Documents requested"`, `RFI_DOCUMENT_STATUS = "Document requested for this assessment"`, `RFI_REQUIREMENT_STATUS = "Evidence needed before this requirement can be concluded"`, `RFI_REQUIREMENT_FALLBACK = "Provide evidence showing how this requirement is met."`, `DEADLINE_WEEKS = {"Required": 2, "Recommended": 4}`, plus the fixed `RFI_INTRODUCTION` and `RFI_RESPONSE_INSTRUCTIONS`; `RFI_SCOPE_REQUIRED_MESSAGE = "Record the assessment scope before preparing an RFI."`; `RFI_EMPTY_MESSAGE = "Nothing to request: every evidence request item is omitted and no approved conclusion is marked insufficient evidence."`; `RFI_UNKNOWN_OMISSION_MESSAGE = "One of the omitted items is not in the current evidence request. Reload the page and try again."`; `RFI_STALE_MESSAGE = "This RFI version no longer matches the current scope, evidence request or approved conclusions. Generate a new version, then issue it."`; `RFI_NOT_FOUND_MESSAGE = "RFI version not found."`; `RFI_WRONG_ROUTE_MESSAGE = "RFI versions are generated and issued from the RFI page."`; `RFI_LINK_NOT_CURRENT_MESSAGE = "Client links can only be created from the current issued RFI version."`; `RFI_NO_ENGAGEMENT_MESSAGE = "This assessment is not part of an engagement, so a client link cannot be created."`; `RFI_UNKNOWN_ITEM_MESSAGE = "Choose requested items from this RFI version."`; and `LEGACY_RFI_RETIRED = "The previous RFI generator has been retired. Prepare a versioned RFI from the RFI page."`.

Implemented signatures:

```text
build_rfi_document(db, assessment, *, omitted=())
current_source(db, assessment)
canonical_bytes(document)
render_items(document)
generate_version(db, assessment, *, omitted, actor)
issue_version(db, assessment, snapshot_id, *, actor)
create_client_link(db, assessment, snapshot_id, *, item_ids, expires_in_days, max_uploads, max_total_mb, actor)
page_context(db, assessment)
create_rfi_snapshot(db, *, assessment, pdf_content, document_content, source, omitted_document_types, actor)
read_rfi_document(db, snapshot)
rfi_snapshot_rows(db, assessment, *, current_source)
current_rfi_issue(db, assessment)
create_rfi_link(db, *, engagement_id, assessment_id, snapshot_id, rfi_items, expires_in_days, max_uploads, max_total_mb, actor='consultant')
_validated_titles(db, *, engagement_id, item_titles, expires_in_days, max_uploads, max_total_mb)
_insert_link(db, *, engagement_id, scope, item_keys, expires_in_days, max_uploads, max_total_mb, actor, extra_audit=None)
generate_rfi_pdf(title, company_name, introduction, evidence_items, response_instructions, generated_at=None, framework_label='', *, version_label='')
generate_rfi_docx(title, company_name, introduction, evidence_items, response_instructions, generated_at=None, framework_label='', *, version_label='')
```

`RfiLinkRow` fields are `link_id`, `id_prefix`, `status`, `created_at`, `expires_at`, `snapshot_id`, `sequence`, `items`, `uploads_used`, and `max_uploads`. `RFI_SNAPSHOT_TYPE = "rfi"`, `RFI_DOCUMENT_SUFFIX = ".json"`, `RFI_SCOPE_VERSION = 2`, and `RFI_UNKNOWN_ITEM_TEXT = "Choose requested items from this RFI version."`. The v2 magic-link scope is reference-only: `items[{key,rfi_item_id,title}]`, `rfi{assessment_id,snapshot_id}`, and `version: 2`; the token remains only in the URL response and digest storage.

### Routes

| Method and path | Success | Errors implemented |
|---|---:|---|
| `POST /api/assessments/{assessment_id}/rfi/versions` | 200 | 404 assessment; 400 invalid omission; 409 scope required or empty RFI; 500 persistence failure |
| `POST /api/assessments/{assessment_id}/rfi/versions/{snapshot_id}/issue` | 200 | 404 assessment/version; 409 stale, already issued, or newer version; 500 integrity/persistence failure |
| `GET /api/assessments/{assessment_id}/rfi/versions/{snapshot_id}/docx` | 200 | 404 assessment/version; 500 integrity failure |
| `POST /api/assessments/{assessment_id}/snapshots/{snapshot_id}/issue` | 400 for RFI | 404 assessment/version; 400 RFI wrong route or release-gate errors; 409 generic snapshot conflicts |
| `GET /api/assessments/{assessment_id}/snapshots/{snapshot_id}/file` | 200 | 404 assessment/version; 500 integrity failure |
| `POST /assessments/{assessment_id}/rfi/versions/{snapshot_id}/magic-links` | 200 | 404 assessment/version; 200 rendered validation/conflict errors; 409 archived engagement guard; 422 invalid item selection; 500 integrity/unexpected failure |
| `GET /assessments/{assessment_id}/rfi` | 200 | 404 assessment |
| legacy `POST /assessments/{assessment_id}/generate-rfi` and `GET /assessments/{assessment_id}/rfi/{pdf,docx}` | — | 410 `LEGACY_RFI_RETIRED` |

### Implementation and tests

Implemented the deterministic, consultant-approved RFI document builder; scope/checklist and approved-conclusion source binding; immutable PDF plus canonical JSON sidecar snapshots; version issue/staleness/integrity checks; DOCX/PDF rendering; current-version client links; RFI coverage and received-upload UI; entry points from scope and report pages; legacy-generator retirement; and the standing guard forbidding release-gate calls in the new RFI path. `rfi_generator.py` and `rfi_generated.html` were removed. No schema or Alembic change was made.

The new `tests/test_p5_6_rfi_rebuild.py` contains all 22 handoff scenarios and passes. Existing tests changed under D-P5-6-M:

- `tests/test_remaining_llm_call_sites.py`: removed the three tests that imported the deleted legacy AI generator (D-P5-6-J).
- `tests/test_correctness_bundle.py::test_failed_framework_blocks_release_but_draft_pdf_and_integrated_report_explain_it`: removed the retired legacy RFI route from the release-gate assertion and added its 410 retirement assertion (D-P5-6-J).

`tests/test_p5_2_reader_migration.py` was not changed. The focused unchanged suite (`test_magic_links.py`, `test_report_snapshots.py`, `test_white_label.py`, `test_p5_8_mechanical_cleanup.py`, `test_p5_5_scoping_evidence.py`) passed; the combined retention command was otherwise green but its dirty-tree-only guard failed because the required D-P5-6 test changes are uncommitted. `git diff --check` is clean, protected P5-2/model/Alembic surfaces have zero diff, and `alembic heads` remains `8b2d5f7e1c34 (head)`.

Final focused result: `22 passed, 30 warnings`. Final full result: `641 passed, 9 skipped, 3 failed, 279 warnings in 70.18s`. The three failures were the expected uncommitted-tree protected-surface guard, the pre-existing P5-4 scenario-13 structural-guard fragility, and the retention test's uncommitted-change guard. The known workpaper teardown and longitudinal scenario-9 ordering flake did not reproduce in this run. No new RFI contract test failed.

### Smoke test

In a fresh Alembic-built SQLite database with analyzers and evidence extraction stubbed, ISO + NIST generated a draft RFI (`type: "rfi"`, `is_issued: false`), with 34 items/documents and totals `documents=34`, `items=34`, `required=15`, `requirements=0`; issue returned 200 and `is_issued: true`. The generated metadata contained the ten base snapshot keys plus `document_sha256`, `document_size_bytes`, and `omitted_document_types`; the source contained `schema_version`, `framework_ids`, `checklist_sha256`, and `conclusion_versions`. Two links for 20 and 14 items had the v2 reference-only scope and no token in persisted scope/audit data. PDF text included the firm RFI heading, framework subtitle, `Version: v1`, `15 Required | 19 Recommended`, `RFI-001`, `Documents requested`, and `Requested for:`.

The client page showed only the requested item titles. A DPDPA smoke assessment produced a requirement item for an approved insufficient-evidence conclusion; approving another conclusion made the older draft issue return 409 with `RFI_STALE_MESSAGE`. The retired PDF route returned 410 with `LEGACY_RFI_RETIRED`. No browser was available for the optional browser check.

No discrepancy required an alternative design. The only implementation note is that local httpx multipart handling required the repeated-form test helpers to submit multipart fields explicitly; the production route retains the handoff's `list[str] = Form(default=[])` signature. The tree is intentionally left uncommitted.
