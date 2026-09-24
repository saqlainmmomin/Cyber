# P4-2: Longitudinal synthetic demo: two fictional clients seeded through the real routes, plus the minimal consultant-confirmed evidence-reuse prompt (age and scope warnings) the demo needs and the code does not yet have

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 4, task P4-2:
> Expand `scripts/seed_test_companies.py` with 2 synthetic clients (minimal per review recommendation): **Client A (mature):** Baseline gap assessment (DPDPA + ISO 27001), 6 months later a remediation validation with evidence reuse. **Client B (startup):** NIST CSF gap assessment, evidence uploaded via magic link, partial remediation. Demonstrates: multi-engagement, evidence reuse with age/scope warnings, reassessment, conclusion independence, action lifecycle, engagement-level reporting. **Test:** Seed script runs without error. Dashboard shows both clients with correct engagement hierarchy. Evidence reuse prompts for re-confirmation.

And the Phase 4 exit criterion "Synthetic demo covers multi-engagement, reuse, reassessment, remediation lifecycle". PRD `docs/product/2026-09-21-cyberassess-product-requirements.md`: **PR-025** ("The system may suggest Evidence reuse across Assessments but shall require consultant confirmation. Acceptance: the prompt shows Evidence age, original scope, version, period, and current lifecycle; declining reuse has no side effect; confirming reuse creates an audited Evidence-use link"), the **Reassess** flow ("The consultant duplicates an Engagement **or creates a validation Assessment** … The system shows prior Evidence age and original scope; the consultant confirms continued applicability … No prior Conclusion is copied"), and domain rule 6 ("Evidence reuse is explicit … prior Conclusions may not be copied or silently carried forward").
**Owner:** Codex, from this Claude spec (per `tasks/agent-ownership.md`: "P4-2 Longitudinal synthetic demo | Claude designs narrative/data shape → Codex implements seed script"). Every narrative and data-shape fork is closed below. **If the code forces a deviation from this design, stop and report it in `## Results`, do not pick an alternative.** Merge gate: the standard Sonnet adversarial review (`tasks/todo.md` tags Phase 4 `[AR: IAM/external ID, retention/purge, performance]`; P4-2 carries no extra gate).
**Depends on:** everything through Phase 3 (merged, PRs #16 to #33). `main` is at `a4ac3d9`.
**Runs in parallel with:** P4-1 (AWS evidence adapter), P4-3 (performance benchmarks), P4-4 (retention/archive/purge). File-overlap rules are in D-P4-2-P.
**Failing contract suite: none pre-written.** A grep of `tests/` for `longitudinal`, `evidence_reuse`, `evidence-reuse`, `reuse_candidates`, `Meridian` and `Loomwire` finds nothing. The only test that imports `scripts/seed_test_companies.py` is `tests/test_phase1_prefill.py` (it imports `ALL_REQUIREMENT_IDS`, `novapay_fixture` and `page_count`; none of these change). As with P2-4 onward, **Codex writes `tests/test_longitudinal_demo.py` itself** from `## Test scenarios`. Every scenario listed is required. You may add cases, but you may not drop or weaken one. **No existing test file is modified.**

## Goal

1. `python scripts/seed_test_companies.py --longitudinal` seeds two fictional clients into the configured database through the app's **real routes and services**, with the LLM stubbed. It takes a backup first, and refuses to run twice.
   - **Client A, "Meridian Ledger Technologies Pvt Ltd"** (mature fintech): one engagement holding a **baseline** DPDPA + ISO 27001 assessment dated about 6.5 months ago, remediation Actions worked on in between (one verified, one overdue, one untouched), and a **remediation validation** assessment (ISO 27001 only) started 7 days ago. The validation assessment **reuses two pieces of baseline evidence after the consultant confirms age and scope warnings**, **declines** a third, reaches its **own** Conclusions (none copied), and the engagement gets an **issued integrated report**.
   - **Client B, "Loomwire Labs Inc."** (startup): one NIST CSF 2.0 assessment. The client uploads two of three requested items **through a magic link**; the consultant maps them in, analysis runs, and remediation is **partial** (one Action closed and awaiting verification, one open, overdue and unassigned).
2. The **evidence-reuse prompt** exists: `GET /assessments/{assessment_id}/evidence-reuse` lists evidence from other assessments in the same engagement that could be reused here, each with its age, original scope, version and lifecycle, and **age/scope warnings**. Reuse happens only through a per-item confirmation, which must acknowledge any warning, and which writes the `EvidenceUse` link plus an `evidence_reuse.confirmed` audit event. Declining means leaving it unconfirmed, and records nothing.

## Current state

Grounded against `a4ac3d9` on `main`. Baseline `.venv/bin/pytest -q` → **502 passed, 126 warnings, 1 error** (I ran it in a fresh worktree; the one error is the known, pre-existing fresh-worktree teardown artifact of `_guard_dev_database_untouched` at `tests/test_workpaper.py::test_smoke_full_assessment_traceability`, documented in every Phase 2/3 handoff). `alembic heads` → `4e8c1a9d2b57 (head)`. Re-locate everything by symbol name, not line number.

**What the review reined in.** The superseded plan `docs/plans/2026-09-21-001-*` U7 specified "the complete demo for **four** fictional Clients, including one multi-framework reassessment, one client magic-link submission, one AWS snapshot, one Evidence invalidation, one closure verification, one integrated report, and one archive/restore cycle", and the PRD's "Product-validation and demo track" asks for four personas, each with "a baseline Engagement, at least one targeted or remediation-validation Assessment, and a later reassessment", plus "valid and stale Evidence reuse, a rejected reuse suggestion, Evidence replacement that triggers re-review, deduplicated cross-framework requests, … and an archived Engagement". The adversarial review (`tasks/2026-09-21-adversarial-review.md`, recommended phase breakdown) cut Phase 4's demo to "**Longitudinal synthetic demo (2 clients minimum)**" inside a one-week phase, and the revised plan says "2 synthetic clients (minimal per review recommendation)". **This handoff builds exactly two clients, two engagements and three assessments, and nothing from the four-persona list that the plan line does not name** (D-P4-2-A).

**`scripts/seed_test_companies.py` (1683 lines).** I read its structure and the functions named here.
- Module imports (all `# noqa: E402` after a `sys.path` insert of `ROOT`): `app.models`, `Base, SessionLocal, engine` from `app.database`, `get_all_requirements`, `DocxDocument`, `TestClient`, `app as api_app` from `app.main`, legacy models, `_extract_signals`. Constants `ROOT`, `MANIFEST_PATH`, `NOW = datetime.now(timezone.utc)` (import time), `ALL_REQUIREMENTS`, `ALL_REQUIREMENT_IDS`, `REQUIREMENTS_BY_ID`.
- Two existing modes, both left **unchanged**: the default (`seed_default_companies()`: `Base.metadata.create_all`, three legacy single-framework fixtures NovaPay/HealthBridge/Dakshin written straight into legacy tables, `purge_existing`, manifest) and `--multi` (`seed_multi_framework_companies()`: Helix and Vantara through `TestClient(api_app)` and the JSON API, with `derive_risk_profile` patched). `purge_existing` deletes only legacy tables by `Assessment.company_name`; it knows nothing about Phase 1-3 tables and must not be used for the demo.
- Reusable helpers: `json_dumps(value)`, and **`_build_docx_bytes(title, text) -> bytes`** (heading, then one paragraph per `"\n\n"`-separated block). The demo uses the second.
- `main()`: `argparse` with one flag, `--multi`.
- **The script is imported by tests** as `from scripts.seed_test_companies import …` (`scripts/` has no `__init__.py`; it works as a namespace package from the repo root, the same way `tests/test_findings.py` does `from scripts import migrate_legacy`). Importing it creates `app.database.engine` for `settings.database_url` but opens no connection.

**No evidence-reuse prompt, and no age/scope warning, exists anywhere.** `grep -rniE "reuse|stale|reconfirm|re-confirm|evidence_age|max_age" app/` finds only a comment in `routers/assessments.py`, the workpaper's *stale running analysis run* flag (`workpaper.STALE_RUNNING_AFTER`, unrelated), and `findings.STALE_*` CAS messages. P3-4's open question 5 hands it forward explicitly: "Evidence currency rules (PRD 'expiry/currentness') belong with the evidence-reuse work." **The plan's own test for this task ("Evidence reuse prompts for re-confirmation") therefore cannot pass on a seed script alone** (D-P4-2-D).

**Evidence (P2-1), `app/services/evidence.py`.** I read it in full.
- **D-P2-1-A**, the single membership rule: evidence E is in scope for assessment A iff `E.assessment_id == A.id` **or** an `EvidenceUse(evidence_id=E.id, assessment_id=A.id)` exists; it feeds analysis iff also `E.status == "active"`. P2-1 states the consequence: "mapping is **same-engagement only** (cross-engagement/client-level reuse is later work)". `map_evidence(db, *, evidence_id, assessment_id, framework_id, requirement_id, relevance, actor)` enforces it (`"Evidence and assessment belong to different engagements."`), requires `evidence.status == "active"`, a framework selected on the assessment, a real `Control.id` and `relevance ∈ RELEVANCE_VALUES = ("primary", "supporting", "contextual")`; refuses a duplicate `(evidence, assessment, framework, requirement)` with `DuplicateMapping`; writes one `evidence_use.created` audit event; never commits. This is the PRD's "audited Evidence-use link".
- `Evidence.created_at` / `EvidenceVersion.created_at` default to now; `receive_evidence(..., created_at=...)` accepts an override (P2-1's legacy migration sets `created_at == uploaded_at`), but `ingest_upload` / `ingest_engagement_upload` do not pass one.
- `current_version(db, evidence_id)` returns the active version. `verify_version(db, version_id)` re-hashes the blob. `evidence_panel_rows` marks mapped-in evidence `mapped_in=True` ("Mapped from another assessment" in `partials/document_list.html`).
- `_file_type` accepts `pdf`/`docx`/images. **`.txt` uploads are rejected** (`detect_file_type` returns `None` for them; P3-4's Results hit this). The demo uses DOCX.
- JSON routes (`app/routers/evidence.py`, prefix `/api/evidence`): `POST /{evidence_id}/uses` with JSON `{assessment_id, framework_id, requirement_id, relevance}` → 201. Upload: `POST /api/assessments/{assessment_id}/documents` (multipart `file`, form `category` ∈ `DocumentCategory`: `privacy_policy, consent_form, data_flow_diagram, dpia, processing_records, breach_procedure, retention_policy, vendor_agreement, other`) → 201 `DocumentResponse` whose `id` is the Evidence id.

**Magic links (P2-5), `app/services/magic_links.py` and `app/routers/magic.py`.**
- `create_link(db, *, engagement_id, item_titles, expires_in_days, max_uploads, max_total_mb, actor="consultant") -> CreatedLink(link, token)`: engagement must be `active`; items become `[{"key": "item-1", "title": …}, …]`; only the token's SHA-256 is stored; writes `magic_link.created`; never commits. The consultant route `POST /engagements/{engagement_id}/magic-links` wraps it and renders the one-time URL into HTML.
- Client upload: `POST /magic/{token}` (multipart `item_key` + `file`, `Content-Length` required) → `resolve_token` → `check_upload_allowed` (10 per hour, `max_uploads`) → `receive_client_upload` → writes `magic_link.upload_received` and calls `evidence_service.ingest_engagement_upload(..., uploaded_by=f"client_link:{link.id}", category=None, ...)`. **The resulting Evidence has `assessment_id = NULL`, so it is not in any assessment's scope until the consultant maps it** (D-P2-1-A). 200 renders `magic/upload.html`.
- `magic_link_rows(db, engagement_id)` (engagement page) shows status, items, uploads used. Tokens must never be logged (`MagicTokenRedactionFilter`).

**Analysis (P2-3), `app/routers/analysis.py`, `POST /api/assessments/{assessment_id}/analyze`** (`trigger_analysis`). Any `selected_frameworks` other than exactly `["dpdpa"]` takes the multi-framework path, which calls the module-level name **`run_multi_framework_analysis`** (imported from `claude_analyzer`) once, then `_persist_multi_framework_analysis` → `analysis_pipeline.record_framework_run` per framework: one `Conclusion` per returned item (`ai_proposed=True`, `version=1`), one `proposed` `ConclusionRevision` with `citations_json` from `cite_quotes` over the assessment's in-scope evidence (an empty quote gives `"[]"`, which is still approvable), `GapReport` + one `GapItem` per item with `review_status="draft"`, and `assessment.status = "completed"`. With zero questionnaire responses but in-scope documents, the 80% questionnaire gate only logs "Allowing analysis with incomplete questionnaire because documents are available". Test fakes for the multi path (`tests/test_pdf_updates.py::_stub_multi`) return `{"frameworks": {fw: {"parsed": {"executive_summary": …, "assessments": [...]}, "raw": "{}"}}, "synthesis": None, "total_usage": {}}`.

**Conclusions (P2-4):** `POST /api/assessments/{aid}/conclusions/{cid}/approve` (form `expected_version`, `reviewer_name`) → 200; blocked unless the latest proposal has non-NULL `citations_json` and complete content (`gaps_identified` + `recommended_action` for gap outcomes). Actor `conclusion_review.reviewer_actor(name)` = `"consultant:" + name`.

**Findings/Actions (P3-1, P3-4), `app/services/findings.py` and `app/routers/findings.py`.**
- `POST /api/assessments/{aid}/findings` (form fields of `FindingCreateIn`: `conclusion_id`, `conclusion_version`, `title`, `description`, `severity` ∈ critical/high/medium/low, `priority`, `action_title`, `action_owner`, `action_target_date` ISO date, `notes`, `reviewer_name`) → 200 JSON `{"finding_id": …}`. Requires an individually approved gap Conclusion. Creates the Finding (`status "open"`) and its first Action with one `created` history entry.
- `ACTION_TRANSITIONS = {"open": ("in_progress", "closed"), "in_progress": ("open", "closed"), "closed": ("verified", "in_progress"), "verified": ("in_progress",)}`; `ACTION_STATUS_LABELS`: `open` "Open", `in_progress` "In progress", `closed` "Closed, awaiting verification", `verified` "Closed and verified". Routes under `…/findings/{fid}/actions/{action_id}/`: `status` (`status` ∈ open/in_progress, `expected_history_length`, `notes`, `reviewer_name`), `update`, `close` (`evidence_version_id` must be the **active version of active evidence in `active_versions_in_scope(db, finding.assessment_id)`** and pass `verify_version`), `verify` (a separate request; re-checks the recorded version), `reopen`. History actions: `created`, `status_changed`, `updated`, `closed`, `verified`, `reopened`. `Finding.status` is derived after every Action status change: `resolved` iff every Action is `verified`, else `in_progress` if any is not `open`, else `open`.
- `app/services/remediation_rollup.py`: `engagement_rollup(db, engagement, *, today=None)` → `EngagementRollup.counts` with exactly `ROLLUP_KEYS = ("open", "in_progress", "awaiting_verification", "verified", "overdue", "unassigned", "total")`; `overdue` = `target_date.date() < today` and status in `("open", "in_progress")`; `unassigned` = owner NULL and active. Page `GET /engagements/{engagement_id}/remediation`. `assessment_label` is `f"{a.description or a.company_name} ({a.created_at:%d %b %Y})"`.

**Release and integrated report (P3-3).** `PATCH /api/assessments/{aid}/review/items/{item_id}` JSON `{"review_status": "accepted"}` per `GapItem`, then `POST /api/assessments/{aid}/review/approve` JSON `{"reviewer_name": …}` (400 while any `GapItem` is still draft) sets `assessment.review_status = "approved"`. `POST /api/engagements/{eid}/integrated-reports` (form `reviewer_name`) → 200 `{"snapshot_id", "type": "integrated_report", "is_issued": false}`, only assessments with `review_status == "approved"` and a `GapReport` become sections (`report_content.integrated_report`); `POST …/integrated-reports/{snapshot_id}/issue` → 200 (403 unless every source assessment is still approved). Page `GET /engagements/{eid}/integrated-reports`.

**Hierarchy and portfolio (P1-4).** `POST /engagements` (form `client_mode=new`, `company_name`, `industry`, `company_size`, `engagement_name`, `engagement_type` ∈ gap_assessment/audit/readiness, `description`, multi-valued `selected_frameworks` ∈ `ENABLED_ASSESSMENT_FRAMEWORKS = ("dpdpa", "iso27001", "nist_csf")`) → 303 `Location: /engagements/{id}`, creating Client + Engagement (`status "active"`) + Assessment (`description` from the form) + one `AssessmentPack` per framework (`pack_version` = registry version: dpdpa `2023`, iso27001 `2022`, nist_csf `2.0`) through `engagement_factory.create_engagement_with_assessment`. **There is no route or service that adds a second assessment to an existing engagement.** The dashboard (`GET /`) hides engagements with `status == "closed"`; `GET /engagements/{id}` lists non-archived assessments ordered `created_at` **descending**, plus magic links and client uploads. The assessment page renders `partials/documents_tab.html` only for `GET /assessments/{id}?tab=documents`.

**Timestamps.** Every model uses `default=_utcnow`. There is no clock seam and no `freezegun`/`time-machine` in `requirements.txt`. SQLite returns naive datetimes; compare `.date()` values.

**I probed the Client B flow end to end** on a fresh Alembic-built database with a temporary `upload_dir`, a `TestClient(app)` whose `get_db` override yields the seeding session, and `run_multi_framework_analysis` patched: `POST /engagements` 303 → `create_link` → `POST /magic/{token}` 200 (Evidence `uploaded_by` `client_link:…`, `assessment_id` NULL, `active`) → `POST /api/evidence/{id}/uses` 201 → `POST …/analyze` 200 → both approvals 200 → Finding 200 → both `GapItem` PATCHes 200 → release 200 → integrated report 200 → issue 200 → assessment `completed`, dashboard 200. The architecture in D-P4-2-H is therefore known to work.

## Decisions (made here so they are not relitigated)

### D-P4-2-A. Scope: exactly two clients, two engagements, three assessments

| Client | Engagement | Assessments |
|---|---|---|
| A. Meridian Ledger Technologies Pvt Ltd | "FY2026 DPDPA and ISO 27001 programme" | baseline (dpdpa + iso27001), remediation validation (iso27001) |
| B. Loomwire Labs Inc. | "NIST CSF 2.0 gap assessment" | NIST CSF baseline (nist_csf) |

**Out of scope, deliberately:** a third or fourth client; a second reassessment; an archived engagement or an archive/restore cycle (P4-4 owns archive); evidence invalidation, replacement or re-review impact (PR-026 is not built); deduplicated cross-framework request items (PR-023 is not built); a *persisted* rejected-reuse record; AWS evidence (P4-1); cross-engagement or client-level reuse; a UI to create a validation assessment; browser automation. Each is either another task's feature or the four-persona scope the review cut. Do not add any of them "for realism".

### D-P4-2-B. Client A's reassessment is a second Assessment in the **same** Engagement, not a second Engagement

**Decision:** the remediation validation is a new `Assessment` under Client A's one engagement. "Multi-engagement" is demonstrated at portfolio level (two clients, two engagements), and "reassessment" by the second assessment in engagement A.

**Why:** reuse is the point of the demo, and D-P2-1-A makes `EvidenceUse` mapping **same-engagement only** (`map_evidence` refuses cross-engagement evidence). A second engagement would need cross-engagement reuse, a schema-level decision P2-1 deferred and this task must not take. The PRD's Reassess flow allows exactly this path ("duplicates an Engagement **or creates a validation Assessment**"), and its lifecycle says completion "does not prevent a later validation Assessment". A second, empty engagement for Client A would add nothing but a card.

### D-P4-2-C. The validation assessment covers ISO 27001 only

A targeted validation re-tests the ISO 27001 gaps ahead of certification. DPDPA remediation (the consent-withdrawal Action) is still in flight, so it isn't validated. This gives the demo a real **scope** difference: baseline evidence was collected for DPDPA + ISO 27001, the validation covers ISO 27001 only. It also means DPDPA-mapped evidence is not offered for reuse at all (D-P4-2-D rule 4).

### D-P4-2-D. Build a minimal reuse-suggestion read model with two warnings, in a new module

The plan's test needs a prompt, and none exists, so this task builds the smallest one PR-025 allows: **`app/services/evidence_reuse.py`** (new; read model + one writer), **`app/routers/evidence_reuse.py`** (new; one page, one POST), **`pages/evidence_reuse.html`** (new). **Why a new module and not `evidence.py`:** P4-1 (AWS evidence creation) and P4-4 (blob purge) are both likely to edit `app/services/evidence.py` concurrently, and reuse is a separate concern that only *calls* `map_evidence` and `current_version`. `evidence.py` is **not modified**.

**Candidate rule (exact).** For target assessment T (404 `"Assessment not found"` if missing; `[]` if `T.engagement_id is None`), a candidate is one `EvidenceUse` row U (the *source use*), with its Evidence E and source Assessment S, such that:
1. `S.engagement_id == T.engagement_id`, `S.id != T.id`, `S.status != "archived"`;
2. `E.engagement_id == T.engagement_id` and `E.status == "active"`, and `evidence_service.current_version(db, E.id)` is not `None` (call it V);
3. **no** `EvidenceUse` already exists with `(E.id, T.id, U.framework_id, U.requirement_id)`;
4. `U.framework_id in T.frameworks` (a use for a framework T doesn't assess is not offered: `map_evidence` would refuse it anyway).

Deduplicate on `(E.id, U.framework_id, U.requirement_id)`, keeping the first by `(U.created_at, U.id)`. Order the result by `(received_on, filename, framework_id, requirement_id, source_use_id)`. Use a bounded number of queries (no query per candidate: load uses/evidence/assessments in one or two joined queries, the target's existing uses in one, and active versions in one `IN` query).

Evidence uploaded straight to T, engagement-level intake that no assessment has mapped (magic-link or AWS evidence), and closure evidence (P3-4 creates no `EvidenceUse`) are therefore **never** candidates.

**Dates and warnings (exact):**
- `reference_date = T.created_at.date()` (when this assessment started); `received_on = V.created_at.date()` (receipt of the **current** version); `age_days = (reference_date - received_on).days` (may be negative).
- `REUSE_AGE_WARNING_DAYS = 180`. **Age warning** iff `age_days > REUSE_AGE_WARNING_DAYS` (strictly greater).
- **Scope warning** iff `set(S.frameworks) != set(T.frameworks)`.
- `warnings` is the tuple of the codes that apply, in the order `("age", "scope")`.

**Why 180 days, and why the assessment's start date.** No threshold exists in the code or the PRD (PR-025 only says "the prompt shows Evidence age"). 180 days is one half-yearly control cycle: a document older than that, reused for a new assessment, usually needs someone to confirm it still reflects practice (quarterly access reviews and annual policies both fall on the right side of that line). Measuring age against the target assessment's start, not the wall clock, keeps the warning a fact about *this* reassessment and stops it drifting as the demo database ages. A constant, not a setting: a settings field would be an unrequested configuration surface.

**Scope** in PR-025 means "original scope". The only scope the schema records per assessment is its framework set, so that is what the warning compares. (There are no period or cut-off columns; see open question 2.)

### D-P4-2-E. Confirmation: one request per candidate; any warning must be acknowledged; audited; declining records nothing

`confirm_reuse(db, *, assessment_id, source_use_id, acknowledge_warnings, actor)`:
1. Recompute `reuse_candidates(db, assessment_id)` and find `source_use_id`, else `ReuseNotAvailable(REUSE_NOT_AVAILABLE)` (409). Recomputing means a candidate that stopped being valid (evidence invalidated, already mapped) can't be confirmed from a stale page.
2. If the candidate has warnings and `acknowledge_warnings` is false: `ReuseAcknowledgementRequired(REUSE_ACK_REQUIRED)` (400). Nothing written.
3. `use = evidence_service.map_evidence(db, evidence_id=…, assessment_id=…, framework_id=<source use's>, requirement_id=<source use's>, relevance=<source use's>, actor=actor)`. Any `EvidenceError` propagates with its own `status_code`/`message`.
4. Add one `AuditEvent(actor=actor, action="evidence_reuse.confirmed", entity_type="evidence_use", entity_id=use.id, metadata_json=json.dumps(metadata, sort_keys=True))`, with `metadata` keys **exactly** `acknowledged_warnings` (bool), `age_days` (int), `evidence_id`, `evidence_version_id`, `framework_id`, `reference_date` (ISO date string), `requirement_id`, `sha256` (the version's full hash), `source_assessment_id`, `source_use_id`, `warnings` (list of codes).
5. `db.flush()`; return `use`. **Never commits.**

So one confirmation writes exactly one `evidence_uses` row and two `audit_events` rows (`evidence_use.created` from `map_evidence`, then `evidence_reuse.confirmed`).

- **The proposed mapping is the source use's own** `(framework_id, requirement_id, relevance)`. The consultant confirms continued applicability, not a new mapping. Re-mapping to a different requirement is what the existing `POST /api/evidence/{id}/uses` is for.
- **Acknowledgement is required only when a warning shows.** A warning-free candidate still needs its own explicit confirmation; nothing is ever mapped automatically.
- **No bulk path.** One POST confirms one candidate. There is no "confirm all", no multi-select, and no checkbox list over candidates (the one checkbox is the per-candidate acknowledgement).
- **Declining = not confirming.** PR-025: "declining reuse has no side effect". No decline route, no "dismissed" state, no audit row. A declined candidate stays listed. Persisting a dismissal is open question 1.
- **No Conclusion is touched.** The target reaches its own Conclusions when it is analysed (D-P4-2-K).

### D-P4-2-F. Service API, exact (`app/services/evidence_reuse.py`)

Module docstring: `"""Consultant-confirmed evidence reuse across the assessments of one engagement (P4-2, PR-025): read-only reuse suggestions with age and scope warnings, and an audited confirmation that creates the EvidenceUse link. Never commits."""`

```python
REUSE_AGE_WARNING_DAYS = 180
WARNING_AGE = "age"
WARNING_SCOPE = "scope"
WARNING_ORDER = (WARNING_AGE, WARNING_SCOPE)
REUSE_CONFIRMED_ACTION = "evidence_reuse.confirmed"
REUSE_ENTITY_TYPE = "evidence_use"
AUDIT_METADATA_KEYS = ("acknowledged_warnings", "age_days", "evidence_id", "evidence_version_id",
                       "framework_id", "reference_date", "requirement_id", "sha256",
                       "source_assessment_id", "source_use_id", "warnings")

# Messages (exact; tests compare them)
ASSESSMENT_NOT_FOUND = "Assessment not found"
REUSE_NOT_AVAILABLE = "This evidence is no longer available for reuse in this assessment. Reload the page. Nothing was saved."
REUSE_ACK_REQUIRED = "Confirm that this evidence still applies despite the warnings shown. Nothing was saved."

class ReuseError(Exception):          # .status_code (400), .message
class ReuseNotFound(ReuseError):      # 404: ASSESSMENT_NOT_FOUND
class ReuseNotAvailable(ReuseError):  # 409
class ReuseAcknowledgementRequired(ReuseError):  # 400

@dataclass(frozen=True)
class ReuseCandidate:
    source_use_id: str
    evidence_id: str
    evidence_version_id: str
    version_number: int
    filename: str                     # the current version's original_filename
    sha256: str                       # the current version's file_hash_sha256
    evidence_status: str              # always "active" today; shown as the lifecycle
    source_assessment_id: str
    source_assessment_label: str      # f"{S.description or S.company_name} ({S.created_at:%d %b %Y})"
    source_framework_ids: tuple[str, ...]   # S.frameworks, in S's order
    framework_id: str
    requirement_id: str
    relevance: str
    received_on: date
    reference_date: date
    age_days: int
    warnings: tuple[str, ...]

def reuse_candidates(db: Session, assessment_id: str) -> list[ReuseCandidate]: ...
def confirm_reuse(db: Session, *, assessment_id: str, source_use_id: str,
                  acknowledge_warnings: bool, actor: str) -> EvidenceUse: ...
```

The module never calls `.commit(`, never deletes a row, and names its Session `db`.

### D-P4-2-G. Routes and page, exact (`app/routers/evidence_reuse.py`, `pages/evidence_reuse.html`)

`router = APIRouter(include_in_schema=False)`; templates via `from app.routers.web import templates` (the `app/routers/magic.py` pattern). Register in `app/main.py`: add `evidence_reuse,` to the `from app.routers import (...)` list (alphabetical position) and `app.include_router(evidence_reuse.router)` directly **before** `app.include_router(magic.router)` under "# Web portal routes".

| Method + path | Handler | Behaviour |
|---|---|---|
| `GET /assessments/{assessment_id}/evidence-reuse` | `evidence_reuse_page` | 404 `HTTPException("Assessment not found")` if missing. Renders the page with `candidates = reuse_candidates(...)`. Never commits. |
| `POST /assessments/{assessment_id}/evidence-reuse/{source_use_id}/confirm` | `confirm_evidence_reuse` | Form fields `acknowledge_warnings` (the value `"yes"` means true; absent or anything else means false) and `reviewer_name`. Actor `conclusion_review.reviewer_actor(reviewer_name)`. On success: one `db.commit()`, then `RedirectResponse(f"/assessments/{assessment_id}/evidence-reuse", status_code=303)`. On `ReuseNotFound`: 404. On any other `ReuseError` or `evidence_service.EvidenceError`: `db.rollback()`, then re-render the page with `error=exc.message` at `status_code=exc.status_code`. |

Page context: `request`, `assessment`, `engagement` (or `None`), `client` (or `None`), `candidates`, `framework_names` (dict id → `FrameworkRegistry.get_or_none(id).name`, falling back to `id.upper()`), `target_framework_ids` (`assessment.frameworks`), `threshold` (`REUSE_AGE_WARNING_DAYS`), `error`.

`pages/evidence_reuse.html` extends `base.html`, with paired `dark:` classes as in `pages/remediation_tracker.html`:
- `{% block title %}Evidence reuse — {{ assessment.description or assessment.company_name }}{% endblock %}`; breadcrumb `Portfolio / {{ client.name }} / {{ engagement.name }} / {{ assessment.description or assessment.company_name }} / Evidence reuse` (client and engagement segments only when present), linking `/`, `/clients/{id}`, `/engagements/{id}`, `/assessments/{id}?tab=documents`.
- `<h1>` "Reuse evidence from earlier assessments"; subtitle "Evidence already collected in this engagement can be reused here only after you confirm it still applies. Conclusions are never copied: this assessment reaches its own."
- When `error`: `<div data-reuse-error role="alert">{{ error }}</div>`.
- When `assessment.engagement_id` is `None`: "This assessment is not linked to an engagement, so no evidence can be reused." When there are no candidates: "No evidence from earlier assessments is waiting for confirmation."
- One `<li data-reuse-candidate id="reuse-{{ c.source_use_id }}" data-warnings="{{ c.warnings|join(' ') }}">` per candidate, showing: the filename linked to `/evidence/{{ c.evidence_id }}`; `v{{ c.version_number }}`; `SHA-256 {{ c.sha256[:12] }}`; `Status: {{ c.evidence_status|title }}`; `Received {{ c.received_on.strftime('%d %b %Y') }}, {{ c.age_days }} days before this assessment started`; `Original scope: {{ c.source_assessment_label }} ({{ source framework names joined with ' + ' }})`; `Proposed use: {{ framework name }} {{ c.requirement_id }} ({{ c.relevance }})`.
- Per warning: `<p data-reuse-warning="age">Older than {{ threshold }} days when this assessment started. Confirm it still reflects current practice.</p>` and `<p data-reuse-warning="scope">Collected for a different scope ({{ source names joined ' + ' }}); this assessment covers {{ target names joined ' + ' }}. Confirm it applies to this scope.</p>`.
- The form: `<form method="post" action="/assessments/{{ assessment.id }}/evidence-reuse/{{ c.source_use_id }}/confirm" hx-boost="false" data-reuse-confirm>`. When `c.warnings`: `<label><input type="checkbox" name="acknowledge_warnings" value="yes"> I confirm this evidence still applies despite the warnings above.</label>`. Then `<input type="text" name="reviewer_name" placeholder="Your name">` and `<button type="submit">Confirm reuse</button>`. **`hx-boost="false"` is required**: `base.html` boosts every form, and htmx does not swap 4xx responses, so a boosted 400/409 would silently show nothing.
- Below the list: "To decline a suggestion, leave it unconfirmed. Declining records nothing."
- Everything autoescaped: **never `|safe`**; never the `multiple` attribute; no "select all" or "confirm all" text.

**One link, additive:** in `partials/documents_tab.html`, inside the "Uploaded Documents" header `<div class="px-6 py-4 border-b …">`, directly after `<h2 …>Uploaded Documents</h2>`, add `{% if assessment.engagement_id %}<a href="/assessments/{{ assessment.id }}/evidence-reuse" data-evidence-reuse-link class="text-sm font-medium text-brand dark:text-navy-300 hover:underline">Reuse evidence from earlier assessments →</a>{% endif %}`. Nothing else in that file changes.

### D-P4-2-H. Seeder architecture: real routes through a `TestClient` bound to the seeding session

`seed_longitudinal_demo(db: Session, http: TestClient, *, anchor: date | None = None) -> LongitudinalDemo`. The caller guarantees `http` runs the real `app.main.app` with `get_db` overridden to yield `db`, so seeder reads and route writes share one session (the pattern of every Phase 2/3 test's `http` fixture). **Every consultant or client act goes through its HTTP route.** Direct service or ORM calls are allowed **only** for:
1. **creating the validation assessment** (no route exists; D-P4-2-J);
2. **creating the magic link** with `magic_links.create_link` (the consultant route renders the one-time token into HTML; the client's upload still goes through `POST /magic/{token}`);
3. **backdating** the business dates listed in D-P4-2-I;
4. **reads**: looking up ids (Conclusions, GapItems, Evidence by `uploaded_by`), and `evidence_reuse.reuse_candidates` to find a `source_use_id`.

Each HTTP call goes through one helper `_expect(response, status: int, what: str)` that raises `RuntimeError(f"{what}: expected {status}, got {response.status_code}: {response.text[:500]}")` on a mismatch. Call `db.expire_all()` before any read that follows a route write. **Binding guard:** right after `POST /engagements` for Client A, look the Engagement up through `db` by name; if it isn't there, raise `RuntimeError("The TestClient is not bound to the seeding session.")`. The library function never touches `SessionLocal`, never opens its own `TestClient`, never reads `settings.database_url`, and prints nothing (all output belongs to the CLI wrapper). The reuse confirmations and every other consultant act post `reviewer_name=DEMO_REVIEWER`.

**Why routes, not services:** the kickoff calls this task "partly a smoke test of everything built so far". Driving the routes exercises form parsing, validation, commits, gates and templates exactly as a consultant would, and the probe (Current state) shows the whole chain works.

**The CLI wrapper** `seed_longitudinal_cli()`:
1. `with TestClient(api_app) as http:` (its lifespan runs `alembic upgrade head` on the configured DB and registers frameworks).
2. Open `db = SessionLocal()` and set `api_app.dependency_overrides[get_db]` to a generator yielding `db`.
3. If either demo client name already exists: print the `DemoAlreadySeeded` message and return (exit 0, nothing written, no backup).
4. Otherwise back up first: `backup_dir = create_backup(database_path(settings.database_url), Path(settings.upload_dir), Path("backups"))` (from `scripts.backup`, the P1-3/P2-1 precedent), and print `Backup written to {backup_dir}`.
5. `demo = seed_longitudinal_demo(db, http)`, then print a summary: both client names, and the relative URLs `/`, `/engagements/{A}`, `/engagements/{B}`, `/assessments/{validation}/evidence-reuse`, `/engagements/{A}/remediation`, `/engagements/{A}/integrated-reports`, `/engagements/{B}/remediation`. **Never print the magic-link token or any `/magic/` URL.**
6. `finally`: remove the override and close `db`.

`main()` gains `--longitudinal`, in an `argparse` mutually exclusive group with `--multi`. The default mode and `--multi` are unchanged.

### D-P4-2-I. Dates: relative to an anchor (the seed run's UTC date by default); only business dates are backdated

`anchor = anchor or datetime.now(timezone.utc).date()`. Every narrative date is `anchor + timedelta(days=offset)`, and a timestamp is `_at(anchor, offset) = datetime.combine(anchor + timedelta(days=offset), time(9, 0), tzinfo=timezone.utc)`. Dates that appear **inside documents and filenames** are derived the same way, so the story is consistent for any anchor.

**Why relative, not fixed calendar dates.** The remediation tracker computes `overdue` against the real today (`engagement_rollup`'s default). With fixed dates, every open Action becomes overdue within weeks of this task landing, and "6 months later" stops meaning anything. The demo exists to be walked through on the day it is seeded. Reuse ages are anchor-independent anyway (both ends are offsets; D-P4-2-D measures against the assessment's start). Tests read `demo.anchor`, so they are exact.

**Backdated (set immediately after the row is created, and before anything reads it):** `clients.created_at`, `engagements.created_at`, `assessments.created_at` (the validation assessment is constructed with it), and for Client A's evidence, `evidence.created_at` together with its v1 `evidence_versions.created_at`. These are business dates: when the engagement started, and when a document was received. P2-1's legacy migration already sets evidence `created_at` to a receipt date.
**Never backdated:** `audit_events`, `conclusion_revisions`, `analysis_runs`, `actions.history_json` timestamps, `findings`, `evidence_uses`, `report_snapshots`, `magic_links`, any `updated_at`, **and all of Client B's evidence**. These are the append-only record of acts, and they truthfully record when the seed performed them. Rewriting an append-only trail to make a demo look older would contradict the provenance model the product sells. (Client B's story is recent, so its evidence arriving "today" is consistent.)

**The dates, with offsets, resolved for an anchor of 2026-09-24:**

| Offset | 2026-09-24 anchor | Event |
|---:|---|---|
| −230 | 2026-02-06 | Meridian policy v4.2 approved (appears in the document text only) |
| −200 | 2026-03-08 | Client A, engagement A and the baseline assessment created |
| −196 | 2026-03-12 | Received: policy, record of processing, earlier access review |
| −120 | 2026-05-27 | Received: DR test report |
| −60 | 2026-07-26 | Target date, access-review Action (verified, so never overdue) |
| −40 | 2026-08-15 | Received: access-review remediation memo (closure evidence) |
| −30 | 2026-08-25 | Client B, engagement B and the NIST assessment created |
| −14 | 2026-09-10 | Target date, baseline DR Action (in progress, so **overdue**) |
| −7 | 2026-09-17 | Validation assessment created (reuse reference date) |
| −5 | 2026-09-19 | Received: current-quarter access review (validation) |
| −3 | 2026-09-21 | Target date, incident-response Action (open, so **overdue**) |
| 0 | 2026-09-24 | The seed runs: every act, audit event and Client B upload |
| +14 | 2026-10-08 | Target date, MFA Action |
| +21 | 2026-10-15 | Target date, validation DR Action |
| +30 | 2026-10-24 | Target date, consent-withdrawal Action |

Resulting reuse ages at the validation's start (−7): policy and earlier access review **189 days** (age warning), DR test report **113 days** (no age warning).

### D-P4-2-J. Creating the validation assessment directly, mirroring the factory

Seed-local helper `_add_assessment_to_engagement(db, *, engagement, client, description, framework_ids, created_at) -> Assessment`: one `Assessment(company_name=client.name, industry=client.industry, company_size=client.size, description=description, selected_frameworks=json.dumps(framework_ids), engagement_id=engagement.id, created_at=created_at)` plus one `AssessmentPack(assessment_id=…, framework_id=…, pack_version=FrameworkRegistry.get_or_none(fw).version if resolvable else "unknown")` per framework, then commit. These are exactly the fields `engagement_factory.create_engagement_with_assessment` writes. **Do not add this to `app/`**: a product route for "new validation assessment" is out of scope (open question 3).

### D-P4-2-K. The LLM is stubbed at one seam, with scripted items; it is never called

Every demo assessment takes the multi-framework path (none is exactly `["dpdpa"]`). Each `POST …/analyze` runs inside `unittest.mock.patch("app.routers.analysis.run_multi_framework_analysis", fake)`, where `fake(**kwargs)` returns `{"frameworks": {fw: {"parsed": {"executive_summary": f"{fw} synthetic demo summary", "assessments": copy.deepcopy(ITEMS[assessment_key][fw])}, "raw": "{}"} for fw in kwargs["framework_ids"]}, "synthesis": None, "total_usage": {}}`. Nothing else is patched: questionnaire building, scoring and initiatives are deterministic and run for real. The demo writes **no questionnaire responses**; each assessment has in-scope documents, so the gate only warns.

Each item has exactly the keys `requirement_id, compliance_status, current_state, gap_description, risk_level, remediation_action, remediation_priority, remediation_effort, timeline_weeks, maturity_level, root_cause_category, evidence_quote, needs_review` (the `tests/test_pdf_updates.py::_item` shape). For compliant items use `gap_description="No gap identified."` and `remediation_action="None required."`. Use `remediation_priority` 1 for high risk, 2 for medium and 3 for low; `remediation_effort="medium"`, `timeline_weeks=6`, `maturity_level` 4 for compliant, 3 for partially compliant and 2 for non-compliant; `root_cause_category="process"`, `needs_review=False`. The exact items are in `## Data specification`, table 3. **`evidence_quote` values are exact substrings of the named document**, so the real `cite_quotes` produces real `text_span` citations (the workpaper and integrated PDF then show evidence chains).

**Conclusion independence (what it means here, exactly):** the validation assessment's Conclusions are **new rows created by its own analysis run**. No Conclusion, revision or citation is copied from the baseline. The baseline's ISO.A5.18 stays `non_compliant` and approved while the validation's ISO.A5.18 is `compliant`. Seeding the validation never writes a baseline Conclusion or revision. Within the baseline, **one policy passage supports two different framework outcomes**: ISO.A5.1 `compliant` and DPDPA CH2.SECURITY.1 `partially_compliant` (distinct framework Conclusions).

### D-P4-2-L. Client B's magic-link upload: the real client route, a real token, never printed

1. `created = magic_links.create_link(db, engagement_id=B, item_titles=["Information security policy", "MFA enforcement export", "Incident response plan"], expires_in_days=14, max_uploads=10, max_total_mb=25, actor="consultant")`; `db.commit()`.
2. `POST /magic/{created.token}` with `data={"item_key": "item-1"}` and the policy DOCX, then `item-2` with the MFA export. Expect 200 each. The TestClient sets `Content-Length`.
3. **`item-3` (incident response plan) is never uploaded.** The link stays `active`, with 2 of 10 uploads used. That outstanding item is why NIST.RS.MA.01 is non-compliant.
4. Find the two Evidence rows with `uploaded_by == f"client_link:{created.link.id}"` (ordered by `created_at, id`, matched by `original_filename`). Map them into the NIST assessment through `POST /api/evidence/{id}/uses` (table 2). **This mapping is required**: magic-link evidence has `assessment_id = NULL` and is invisible to analysis until mapped (D-P2-1-A). It is a normal consultant mapping, not "reuse": no other assessment ever used it, so it is never a reuse candidate.
5. The token lives only in a local variable. It is not returned in `LongitudinalDemo`, printed, logged or written anywhere.

### D-P4-2-M. Evidence documents: DOCX, ASCII text, each quote its own paragraph

Every file is `_build_docx_bytes(title, "\n\n".join(paragraphs))` with the content type `application/vnd.openxmlformats-officedocument.wordprocessingml.document`. All text is ASCII: no em dashes, curly quotes or currency symbols, because the integrated PDF goes through fpdf2's latin-1 sanitizer. Every file's bytes are unique (duplicate content in an engagement is refused by P2-1). Exact contents are in `## Data specification`, table 1.

### D-P4-2-N. Release and engagement-level reporting

- Client A: after each assessment's Conclusions and Findings exist, accept every `GapItem` of its report (`PATCH …/review/items/{id}` `{"review_status": "accepted"}`), then `POST …/review/approve` `{"reviewer_name": DEMO_REVIEWER}`. After **both** A assessments are released, `POST /api/engagements/{A}/integrated-reports` and then `…/{snapshot_id}/issue`. The integrated report therefore has two sections (baseline, then validation, by `created_at`), each with its own frameworks, scores and Findings, and no blended score.
- Client B: **not released** (still under review), with no integrated report. That is the realistic state of an engagement mid-remediation, and it leaves B's integrated-reports page showing the "not released" exclusion.
- `DEMO_REVIEWER = "Priya Sharma"` for every consultant act (actor `consultant:Priya Sharma`).

### D-P4-2-O. Re-running: refuse, before writing anything

`class DemoAlreadySeeded(Exception)` with `.message = "Longitudinal demo already seeded (Meridian Ledger Technologies Pvt Ltd, Loomwire Labs Inc.); nothing was changed. Restore a pre-seed backup with scripts/restore.py to seed it again."` `seed_longitudinal_demo` raises it **as its first action** if a `Client` named either `DEMO_CLIENT_NAMES` entry exists. **No purge or reset path:** deleting clients, evidence and blobs is P4-4's destructive domain, with its own dependency checks. A half-finished seed (a route failing midway leaves committed rows) is recovered by restoring the backup the CLI took in step 4.

### D-P4-2-P. File overlap with P4-1, P4-3 and P4-4 (checked against `tasks/todo.md`, `app/main.py` and `app/routers/web.py`)

P4-2 touches only: `scripts/seed_test_companies.py` (an appended section plus the `main()` flag), `app/services/evidence_reuse.py` (new), `app/routers/evidence_reuse.py` (new), `app/templates/pages/evidence_reuse.html` (new), `app/main.py` (one import-list entry and one `include_router` line), `app/templates/partials/documents_tab.html` (one link), `tests/test_longitudinal_demo.py` (new), `tasks/todo.md`, and this handoff. **It does not touch `app/routers/web.py`, `app/services/evidence.py`, any model, any Alembic revision or `requirements.txt`.**
- **Shared with others:** `app/main.py` (P4-1 and P4-4 will likely register routers too), `tasks/todo.md` (everyone), and possibly `partials/documents_tab.html` (P4-1 may add an AWS trigger near uploads). Rule: **if another task lands first, keep both sides of every conflict**. These are adjacent additive lines.
- **P4-3** (benchmarks) must seed its own dataset. It must not depend on or modify this demo. If it also appends to `seed_test_companies.py`, keep both sections.
- **P4-4** (archive): reuse candidates already exclude archived source assessments (rule 1). Whether confirming reuse *into* an archived, read-only engagement must be refused is P4-4's decision; it should add that check to `confirm_reuse` when it lands. Handed forward.
- **P4-1** (AWS): AWS evidence is engagement-level (`assessment_id` NULL) with no `EvidenceUse`, so it is never a reuse candidate until a consultant maps it. No interaction.

### D-P4-2-Q. Consistency audit of this spec (the P2-4 lesson, done in advance)

1. **Route-set guards.** Existing tests pin the route sets containing `/conclusions`, `/findings`, `/workpaper`, `/snapshots` and `/remediation`, and forbid `/gap-items/` and `remediation-summary`. Neither new path (`/assessments/{assessment_id}/evidence-reuse`, `…/evidence-reuse/{source_use_id}/confirm`) contains any of those substrings.
2. **Template guards.** `tests/test_white_label.py` forbids `CyberAssess` in templates; `tests/test_no_blended_scoring.py` forbids `overall_score`. Neither appears in `pages/evidence_reuse.html` or the `documents_tab.html` link.
3. **P3-1's regex** (`select all|create all|all conclusions|type="checkbox"|\bmultiple\b|\|\s*safe\b`) scans only `findings.py`, its router and schema, `pages/findings.html` and `components/finding_card.html`. The acknowledgement checkbox lives in a new template outside that set. This task's own guard (scenario 12) uses a narrower regex that permits one checkbox.
4. **Mandated strings vs this task's guard.** Scenario 12 forbids `confirm all|select all|approve all|\bmultiple\b|\|\s*safe\b|bulk` in the three new app files. Checked against every mandated string and identifier here ("Confirm reuse", "Reuse evidence from earlier assessments", "To decline a suggestion, leave it unconfirmed. Declining records nothing.", both warning texts, every message and constant): **none matches.** `REUSE_ACK_REQUIRED` contains "Confirm that", not "confirm all". Don't use the words "multiple" or "bulk" in comments or docstrings of those files.
5. **"delete" guard.** Scenario 12 asserts `"delete"` is absent from the lower-cased `evidence_reuse.py` service source. No mandated text contains it; say "remove" in comments if you need to.
6. **Counted attributes** `data-reuse-candidate`, `data-reuse-warning`, `data-reuse-confirm`, `data-reuse-error` and `data-evidence-reuse-link` don't contain one another. Tests count `data-reuse-candidate ` (with the trailing space before `id=`) or parse the HTML, never `data-reuse` alone.
7. **Seed-script import side effects.** Nothing new runs at import time: the new section defines constants, dataclasses and functions only, and the CLI runs only under `__main__`. `tests/test_phase1_prefill.py`'s imports are untouched.
8. **Actor strings.** The raw `consultant:` prefix is never rendered by the new page (it shows no actor).

## Data specification

`T` is the anchor; `d(n)` is `anchor + timedelta(days=n)`; `at(n)` is 09:00 UTC on `d(n)`. Filenames and titles below are f-strings over `d(n)`.

**Clients and engagements** (created through `POST /engagements`, `client_mode=new`, `engagement_type=gap_assessment`, then backdated):

| | Client A | Client B |
|---|---|---|
| `company_name` | `Meridian Ledger Technologies Pvt Ltd` | `Loomwire Labs Inc.` |
| `industry` / `company_size` | `fintech` / `large` | `it_services` / `startup` |
| `engagement_name` | `FY2026 DPDPA and ISO 27001 programme` | `NIST CSF 2.0 gap assessment` |
| `selected_frameworks` | `["dpdpa", "iso27001"]` | `["nist_csf"]` |
| first assessment `description` | `Baseline gap assessment (DPDPA + ISO 27001)` | `NIST CSF 2.0 baseline gap assessment` |
| created (client, engagement, assessment) | `at(-200)` | `at(-30)` |
| second assessment | `Remediation validation (ISO 27001)`, `["iso27001"]`, `at(-7)` (D-P4-2-J) | none |

`retention_years` stays at the default 7. Both engagements stay `active`.

**Table 1: evidence.** "Route" is how it arrives. Backdate A's rows (Evidence and v1 version) to the "Received" column; B's rows are not backdated.

| Key | Arrives in / route | Received | Filename | Category | Title | Paragraphs (in order) |
|---|---|---|---|---|---|---|
| `a_policy` | baseline / documents upload | `at(-196)` | `Meridian_Information_Security_Policy_v4.2.docx` | `other` | `Meridian Ledger Technologies - Information Security Policy v4.2` | `f"Approved by the Board Risk Committee on {d(-230):%d %B %Y}. Owner: Chief Information Security Officer."`; **Q_POLICY_REVIEW**; **Q_POLICY_ENCRYPTION**; `Backup media encryption is managed by the hosting provider under its standard terms.` |
| `a_ropa` | baseline / documents upload | `at(-196)` | `Meridian_Record_of_Processing.docx` | `processing_records` | `f"Record of Processing Activities - {d(-196):%B %Y}"` | **Q_ROPA**; `The Data Protection Officer maintains the record and reviews it every quarter.` |
| `a_access_q1` | baseline / documents upload | `at(-196)` | `f"Meridian_Access_Review_{d(-196):%Y-%m}.docx"` | `other` | `f"Quarterly User Access Review - {d(-196):%B %Y}"` | **Q_ACCESS_EARLIER**; `Review owner: IT Operations. Exceptions were not approved by the system owners.` |
| `a_dr_report` | baseline / documents upload | `at(-120)` | `f"Meridian_DR_Test_Report_{d(-120):%Y-%m}.docx"` | `other` | `f"Business Continuity and DR Test Report - {d(-120):%B %Y}"` | **Q_DR**; `The runbook step for promoting the replica database had to be performed manually.` |
| `a_access_memo` | baseline / documents upload | `at(-40)` | `f"Meridian_Access_Review_Remediation_Memo_{d(-40):%Y-%m}.docx"` | `other` | `Access Review Remediation Memo` | `f"Prepared by IT Operations on {d(-40):%d %B %Y}."`; `The payments ledger, card vault and data warehouse were added to the quarterly access review and reviewed in full.`; `Sign-off by each system owner is attached to the review record.` |
| `a_access_q3` | validation / documents upload | `at(-5)` | `f"Meridian_Access_Review_{d(-5):%Y-%m}.docx"` | `other` | `f"Quarterly User Access Review - {d(-5):%B %Y}"` | **Q_ACCESS_CURRENT**; `Every exception was approved by the system owner.` |
| `b_policy` | engagement B / `POST /magic/{token}` `item-1` | seed time | `Loomwire_Security_Policy.docx` | (none) | `Loomwire Labs - Information Security Policy` | **Q_B_POLICY**; `All staff acknowledge the policy during onboarding.` |
| `b_mfa_export` | engagement B / `POST /magic/{token}` `item-2` | seed time | `Loomwire_MFA_Enforcement_Export.docx` | (none) | `Identity Provider MFA Enforcement Export` | **Q_B_MFA**; `Exempt accounts: ci-deploy, backup-agent, legacy-billing.` |
| `b_mfa_fix` | NIST assessment / documents upload | seed time | `Loomwire_Service_Account_Remediation.docx` | `other` | `Service Account Remediation Note` | `The 3 exempt service accounts were moved to workload identity federation and can no longer sign in interactively.`; `Change ticket SEC-142 records the configuration change.` |

The quote constants (module-level, exact):

```python
Q_POLICY_REVIEW = "The information security policy is reviewed annually and communicated to all employees and contractors."
Q_POLICY_ENCRYPTION = "All production databases and customer data stores are encrypted at rest using AES-256."
Q_ROPA = "The record of processing lists 23 processing activities with the purpose, data categories, retention period and recipients of each."
Q_ACCESS_EARLIER = "Access reviews were completed for 11 of 14 production systems; the payments ledger, card vault and data warehouse were not reviewed."
Q_DR = "The failover of the payments platform completed in 6 hours against a recovery time objective of 4 hours."
Q_ACCESS_CURRENT = "Access reviews were completed for all 14 production systems, and 37 stale accounts were removed."
Q_B_POLICY = "This policy is owned by the CTO, approved by the founders and reviewed every twelve months."
Q_B_MFA = "MFA is enforced for 38 of 41 accounts; 3 service accounts are exempt from MFA."
```

**Table 2: evidence mappings** made through `POST /api/evidence/{id}/uses`, **before** the assessment's analysis. These are the only direct mappings. The two reuse links come from D-P4-2-E.

| Evidence | Assessment | Framework | Requirement | Relevance |
|---|---|---|---|---|
| `a_policy` | baseline | `iso27001` | `ISO.A5.1` | `primary` |
| `a_policy` | baseline | `dpdpa` | `CH2.SECURITY.1` | `supporting` |
| `a_ropa` | baseline | `dpdpa` | `CH3.ACCESS.1` | `primary` |
| `a_access_q1` | baseline | `iso27001` | `ISO.A5.18` | `primary` |
| `a_dr_report` | baseline | `iso27001` | `ISO.A5.30` | `primary` |
| `b_policy` | NIST | `nist_csf` | `NIST.GV.PO.01` | `primary` |
| `b_mfa_export` | NIST | `nist_csf` | `NIST.PR.AA.03` | `primary` |

**Table 3: scripted analysis items** (`ITEMS[assessment_key][framework_id]`, in this order). Quote "none" means `evidence_quote=""`.

| Assessment | Framework | Requirement | `compliance_status` | Risk | Quote | `current_state` | `gap_description` / `remediation_action` (gap outcomes only) |
|---|---|---|---|---|---|---|---|
| baseline | dpdpa | `CH3.ACCESS.1` | compliant | low | Q_ROPA | `A maintained record of processing covers every processing activity.` | |
| baseline | dpdpa | `CH2.SECURITY.1` | partially_compliant | medium | Q_POLICY_ENCRYPTION | `Encryption at rest is documented for production data stores.` | `Backup encryption is delegated to the hosting provider without evidence.` / `Obtain and file the hosting provider's backup encryption attestation.` |
| baseline | dpdpa | `CH2.CONSENT.3` | non_compliant | high | none | `The mobile app offers no way to withdraw consent once given.` | `There is no consent withdrawal mechanism.` / `Ship an in-app consent withdrawal flow that is as easy as giving consent.` |
| baseline | iso27001 | `ISO.A5.1` | compliant | low | Q_POLICY_REVIEW | `An approved information security policy is reviewed annually.` | |
| baseline | iso27001 | `ISO.A5.18` | non_compliant | high | Q_ACCESS_EARLIER | `Quarterly access reviews skipped three production systems.` | `Three production systems were left out of the quarterly access review.` / `Extend the quarterly access review to every production system.` |
| baseline | iso27001 | `ISO.A5.30` | partially_compliant | medium | Q_DR | `A DR failover test was run but missed its recovery time objective.` | `The last failover test took 6 hours against a 4-hour RTO.` / `Fix the failover runbook and re-test within the 4-hour RTO.` |
| validation | iso27001 | `ISO.A5.1` | compliant | low | Q_POLICY_REVIEW | `The reused policy is still current and reviewed annually.` | |
| validation | iso27001 | `ISO.A5.18` | compliant | low | Q_ACCESS_CURRENT | `The current quarterly access review covers all 14 production systems.` | |
| validation | iso27001 | `ISO.A5.30` | partially_compliant | medium | Q_DR | `No failover test has been run since the test that missed the RTO.` | `The failover has not been re-tested within the 4-hour RTO.` / `Run and evidence a failover test within the 4-hour RTO.` |
| nist | nist_csf | `NIST.GV.PO.01` | compliant | low | Q_B_POLICY | `An owned, approved security policy with a yearly review exists.` | |
| nist | nist_csf | `NIST.PR.AA.03` | partially_compliant | high | Q_B_MFA | `MFA is enforced for most accounts, with three exempt service accounts.` | `Three service accounts are exempt from MFA.` / `Remove the MFA exemptions or apply compensating controls.` |
| nist | nist_csf | `NIST.RS.MA.01` | non_compliant | high | none | `No incident response plan was provided; the requested item is outstanding.` | `There is no documented incident response plan.` / `Document and tabletop-test an incident response plan.` |

Every Conclusion (12 in total) is then **approved individually** through `…/conclusions/{cid}/approve`. That makes each one version 2, with revisions `["proposed", "approved"]`.

**Table 4: Findings and Actions** (through `POST /api/assessments/{aid}/findings`, from the approved Conclusion; `description` = the Conclusion's `gaps_identified`; `priority` 1 for high and 2 for medium), then their lifecycle steps in order through the Action routes (`expected_history_length` read fresh from the DB each time; `reviewer_name=DEMO_REVIEWER`).

| Key | Assessment / Conclusion | Title | Severity | Action title | Owner | Target | Steps after creation | Final Action / Finding status | History actions |
|---|---|---|---|---|---|---|---|---|---|
| `a_consent` | baseline / `CH2.CONSENT.3` | `No in-app consent withdrawal` | high | `Ship an in-app consent withdrawal flow` | `Rhea Kapoor` | `d(30)` | none | `open` / `open` | `created` |
| `a_access` | baseline / `ISO.A5.18` | `Quarterly access review skipped three production systems` | high | `Extend the quarterly access review to every production system` | `Arjun Mehta` | `d(-60)` | `status` → `in_progress` (notes `Remediation started`); upload `a_access_memo`; `close` with its active version (notes `Remediation memo received`); `verify` (notes `Memo checked against the system owner sign-offs`) | `verified` / `resolved` | `created, status_changed, closed, verified` |
| `a_dr` | baseline / `ISO.A5.30` | `DR failover exceeded the 4-hour RTO` | medium | `Re-run the DR failover test within the 4-hour RTO` | `Arjun Mehta` | `d(-14)` | `status` → `in_progress` (notes `Runbook fix in progress`) | `in_progress` / `in_progress` (overdue) | `created, status_changed` |
| `v_dr` | validation / `ISO.A5.30` | `DR failover still not re-tested within the RTO` | medium | `Run and evidence a DR failover test within the RTO` | `Arjun Mehta` | `d(21)` | none | `open` / `open` | `created` |
| `b_mfa` | NIST / `NIST.PR.AA.03` | `Three service accounts exempt from MFA` | high | `Remove MFA exemptions for service accounts` | `Dev Anand` | `d(14)` | `status` → `in_progress` (notes `Moving accounts to workload identity`); upload `b_mfa_fix`; `close` with its active version (notes `Remediation note received`); **no verify** | `closed` / `in_progress` | `created, status_changed, closed` |
| `b_ir` | NIST / `NIST.RS.MA.01` | `No documented incident response plan` | high | `Document and tabletop-test an incident response plan` | (none: omit `action_owner`) | `d(-3)` | none | `open` / `open` (overdue, unassigned) | `created` |

No Finding is created for DPDPA `CH2.SECURITY.1`, even though it is a gap: not every gap Conclusion becomes a Finding (the P3-1 model), and it stays visible as an approved Conclusion in the workpaper and report.

**Expected rollups** (`engagement_rollup(db, engagement, today=demo.anchor).counts`):
- A: `{"open": 2, "in_progress": 1, "awaiting_verification": 0, "verified": 1, "overdue": 1, "unassigned": 0, "total": 4}`
- B: `{"open": 1, "in_progress": 0, "awaiting_verification": 1, "verified": 0, "overdue": 1, "unassigned": 1, "total": 2}`

**Reuse in the validation assessment** (after it is created, before its analysis). `reuse_candidates(db, validation)` returns exactly three, in this order:

| # | Evidence | Framework / requirement | Relevance | `age_days` | `warnings` | Seed action |
|---|---|---|---|---:|---|---|
| 1 | `a_access_q1` | iso27001 / ISO.A5.18 | primary | 189 | `("age", "scope")` | **declined** (left unconfirmed: a stale quarter can't show current operating effectiveness, so the consultant obtained `a_access_q3` instead) |
| 2 | `a_policy` | iso27001 / ISO.A5.1 | primary | 189 | `("age", "scope")` | **confirmed** with `acknowledge_warnings=yes` (policy v4.2 is still the current approved version) |
| 3 | `a_dr_report` | iso27001 / ISO.A5.30 | primary | 113 | `("scope",)` | **confirmed** with `acknowledge_warnings=yes` (it is still the latest DR test) |

(Candidates 1 and 2 share a receipt date, so they order by filename: `Meridian_Access_Review_…` sorts before `Meridian_Information_…`.) The DPDPA uses of `a_policy` and `a_ropa` are never candidates (rule 4). Confirm through `POST /assessments/{validation}/evidence-reuse/{source_use_id}/confirm` → 303, finding `source_use_id` via `reuse_candidates`. After seeding, the validation's reuse page shows exactly candidate 1. The baseline and NIST assessments have zero candidates.

## Required approach

Do the steps in this order. Each backdate happens right after the row it touches is created. Commit through the routes; the seeder itself commits only after a backdate or after a direct write (D-P4-2-H exceptions).

1. **`app/services/evidence_reuse.py`** (D-P4-2-D/E/F).
2. **`app/routers/evidence_reuse.py`**, **`pages/evidence_reuse.html`**, the `app/main.py` registration and the `documents_tab.html` link (D-P4-2-G).
3. **`scripts/seed_test_companies.py`:** append one section headed `# --- P4-2 longitudinal demo (tasks/handoffs/2026-09-24-p4-2-longitudinal-demo.md) ---` **above** `main()`, containing: `DEMO_CLIENT_A`, `DEMO_CLIENT_B`, `DEMO_CLIENT_NAMES`, `DEMO_REVIEWER`, `REUSE_DECLINED_KEY = "a_access_q1"`, the `Q_*` constants, `DemoAlreadySeeded`, `LongitudinalDemo`, `_at`, `_expect`, `_add_assessment_to_engagement`, the item/document tables as module-level data or builder functions, `seed_longitudinal_demo` and `seed_longitudinal_cli`. Then edit `main()` (D-P4-2-H). **Do not edit any existing function or constant.**

   ```python
   @dataclass(frozen=True)
   class LongitudinalDemo:
       anchor: date
       client_ids: dict[str, str]          # {"a": …, "b": …}
       engagement_ids: dict[str, str]      # {"a": …, "b": …}
       assessment_ids: dict[str, str]      # {"baseline": …, "validation": …, "nist": …}
       evidence_ids: dict[str, str]        # the nine table 1 keys
       finding_ids: dict[str, str]         # the six table 4 keys
       action_ids: dict[str, str]          # the six table 4 keys (each Finding's only Action)
       magic_link_id: str
       integrated_snapshot_id: str
   ```

4. **`seed_longitudinal_demo` sequence:**
   1. Refuse if seeded (D-P4-2-O). Resolve `anchor`.
   2. **Client A baseline:** `POST /engagements` (303) → binding guard → backdate client, engagement and baseline to `at(-200)` → upload `a_policy`, `a_ropa`, `a_access_q1`, `a_dr_report` (201 each; backdate each) → the five baseline mappings (201 each) → analyze (stubbed, 200) → approve its six Conclusions → create Findings `a_consent`, `a_access`, `a_dr` → accept its `GapItem`s and release it.
   3. **Client A remediation:** the `a_access` steps (status, upload and backdate `a_access_memo`, close, verify) and the `a_dr` status step.
   4. **Client A validation:** `_add_assessment_to_engagement(..., created_at=at(-7))` → confirm reuse of `a_policy`/ISO.A5.1 and `a_dr_report`/ISO.A5.30 (303 each), leave `a_access_q1` unconfirmed → upload `a_access_q3` to the validation assessment (201; backdate `at(-5)`) → analyze (200) → approve its three Conclusions → create Finding `v_dr` → accept its `GapItem`s and release it → generate the integrated report (200) and issue it (200).
   5. **Client B:** `POST /engagements` (303) → backdate client, engagement and assessment to `at(-30)` → create the magic link → two client uploads (200 each) → the two NIST mappings (201 each) → analyze (200) → approve its three Conclusions → create Findings `b_mfa`, `b_ir` → the `b_mfa` steps (status, upload `b_mfa_fix`, close). Not released.
   6. Return `LongitudinalDemo`.
5. **`tests/test_longitudinal_demo.py`** (`## Test scenarios`).
6. **`tasks/todo.md`:** add a P4-2 line under the Phase 4 bullet, in the existing style, with its status and a link to this handoff's Results. Don't mark Phase 4 done.

## Key files

| File | Why it matters |
|---|---|
| `scripts/seed_test_companies.py` | Appended demo section and `--longitudinal` (D-P4-2-H/I/J/K/L/O, Data specification). |
| `app/services/evidence_reuse.py` (new) | Candidate rule, warnings, confirmation (D-P4-2-D/E/F). |
| `app/routers/evidence_reuse.py` (new), `app/templates/pages/evidence_reuse.html` (new) | The prompt (D-P4-2-G). |
| `app/main.py`, `app/templates/partials/documents_tab.html` | One registration, one link (D-P4-2-G). |
| `app/services/evidence.py` | `map_evidence`, `current_version`, D-P2-1-A. **Read only; not modified.** |
| `app/services/magic_links.py`, `app/routers/magic.py` | `create_link`, `POST /magic/{token}`. **Not modified.** |
| `app/routers/analysis.py` | The one LLM seam, `run_multi_framework_analysis`. **Not modified.** |
| `app/services/findings.py`, `app/services/remediation_rollup.py`, `app/services/report_content.py`, `app/routers/integrated_reports.py`, `app/routers/review.py` | Lifecycle, rollup, release and integrated report used as-is. **Not modified.** |
| `scripts/backup.py` | `create_backup`, `database_path` for the CLI's backup-first step. **Not modified.** |
| `tests/test_findings.py`, `tests/test_pdf_updates.py` | Fixture patterns to copy (Alembic-built DB, `http`, `upload_root`). **Not modified.** |

## Non-goals

- No schema change, no Alembic revision, no model change, no new dependency. `alembic heads` stays `4e8c1a9d2b57`.
- Nothing from D-P4-2-A's out-of-scope list.
- No change to `app/services/evidence.py`, `app/routers/web.py` or any existing route's behaviour. No reuse suggestions on any page other than the new one (for example, none injected into the upload flow).
- No persisted decline, no reuse-threshold setting, no period/cut-off fields.
- No change to the default seed mode, `--multi`, `purge_existing`, `test_ground_truth.json` or `tests/test_phase1_prefill.py`.
- No real LLM call, ever, in the seed or its tests.

## Test scenarios

All in `tests/test_longitudinal_demo.py`. Copy (don't import) from `tests/test_findings.py` the Alembic-built `db_path` / `engine` / `db` fixtures, the `http` fixture (use `TestClient(app)` with the default `raise_server_exceptions=True`) and the module-level `_register_frameworks` autouse fixture; from `tests/test_pdf_updates.py`, the autouse `upload_root` fixture (**no test may write under the real `uploads/`**). Add an autouse fixture that monkeypatches `app.services.llm_client._get_client` to raise `AssertionError("The demo must never call the LLM.")`. Import the seeder as `from scripts.seed_test_companies import …`. Most scenarios need the seeded demo: a `demo` fixture calls `seed_longitudinal_demo(db, http)` with the default anchor, and tests read `demo.anchor` for dates. Every scenario is one or more test functions whose docstrings start with `Scenario N:`.

1. **The plan's test, part 1: the seed runs without error, and never calls the LLM.** It returns a `LongitudinalDemo` with every key listed in step 3. Exact row counts: `clients` 2, `engagements` 2, `assessments` 3, `assessment_packs` 4, `evidence` 9, `evidence_versions` 9, `evidence_uses` 9 (7 from table 2 plus 2 reuse links), `conclusions` 12, `findings` 6, `actions` 6, `magic_links` 1, `report_snapshots` 1. Audit counts by action: `evidence_reuse.confirmed` 2, `magic_link.upload_received` 2, `magic_link.created` 1, `evidence_use.created` 9. Every evidence version's blob is under the temporary upload root and `verify_version` is `True`.
2. **The plan's test, part 2: the dashboard shows both clients with the correct engagement hierarchy.**
   - DB: Client A has exactly one engagement with exactly two assessments, the baseline (`["dpdpa", "iso27001"]`, two packs `2023`/`2022`) and the validation (`["iso27001"]`, one pack `2022`); Client B has one engagement with one assessment (`["nist_csf"]`, pack `2.0`). Both engagements are `active`. All three assessments are `completed`.
   - `GET /` → 200: contains both client names, both engagement names, and `href="/clients/{id}"` and `href="/engagements/{id}"` for both.
   - `GET /engagements/{A}` → 200: contains both assessment descriptions, `href="/assessments/{validation}"` **before** `href="/assessments/{baseline}"` (newest first). `GET /engagements/{B}` → 200: contains the NIST description and the magic-link row ("Information security policy", "Incident response plan").
   - `GET /clients/{A}` → 200 and lists engagement A.
3. **Business dates are anchor-relative; the audit trail is not backdated.** `created_at.date()`: Client A, engagement A and the baseline `== d(-200)`; validation `== d(-7)`; Client B, engagement B and NIST `== d(-30)`. Evidence and v1 versions: `a_policy`, `a_ropa`, `a_access_q1` `== d(-196)`; `a_dr_report` `== d(-120)`; `a_access_memo` `== d(-40)`; `a_access_q3` `== d(-5)`. The `a_access_q1` filename is `f"Meridian_Access_Review_{d(-196):%Y-%m}.docx"`, and its extracted text contains `f"Quarterly User Access Review - {d(-196):%B %Y}"`. Every `audit_events.created_at.date()` is `>= d(-1)` (none backdated), and so is every B evidence row.
4. **The plan's test, part 3: evidence reuse prompts for re-confirmation (D-P4-2-D/E/G).**
   - `reuse_candidates(db, validation)` returns exactly one candidate: `a_access_q1`, `iso27001`/`ISO.A5.18`/`primary`, `age_days == 189`, `warnings == ("age", "scope")`, `received_on == d(-196)`, `reference_date == d(-7)`, `version_number == 1`, `sha256` equal to its version's hash, `source_assessment_id == baseline`, `source_framework_ids == ("dpdpa", "iso27001")`.
   - `GET /assessments/{validation}/evidence-reuse` → 200: exactly one `data-reuse-candidate`, with `data-warnings="age scope"`; both `data-reuse-warning="age"` and `data-reuse-warning="scope"`; the text "189 days"; `name="acknowledge_warnings"`; "Confirm reuse"; `hx-boost="false"`; `href="/evidence/{a_access_q1}"`; and "Declining records nothing."
   - Posting `…/confirm` **without** `acknowledge_warnings` → 400, the page contains `data-reuse-error` and `REUSE_ACK_REQUIRED` (compared through the constant, HTML-escaped as rendered), and `evidence_uses`/`audit_events` counts are unchanged. The same with `acknowledge_warnings=no` → 400.
   - Posting with `acknowledge_warnings=yes` and `reviewer_name=Priya Sharma` → 303 to the reuse page. Exactly one new `EvidenceUse` (`a_access_q1`, validation, `iso27001`, `ISO.A5.18`, `primary`) and exactly two new audit events: `evidence_use.created`, then `evidence_reuse.confirmed` (actor `consultant:Priya Sharma`, `entity_type == "evidence_use"`, `entity_id` = the new use, metadata keys `== set(AUDIT_METADATA_KEYS)`, `age_days == 189`, `warnings == ["age", "scope"]`, `acknowledged_warnings is True`, `reference_date == d(-7).isoformat()`). The page now shows zero candidates and "No evidence from earlier assessments is waiting for confirmation." Re-posting the same `source_use_id` → 409 with `REUSE_NOT_AVAILABLE`, nothing written.
   - `GET /assessments/{validation}?tab=documents` contains `data-evidence-reuse-link` and `href="/assessments/{validation}/evidence-reuse"`.
5. **The age boundary and the candidate rules.** On the seeded DB, before any test confirmation:
   - Set `a_access_q1`'s active version `created_at` to `at(-7 - 180)`: its warnings are `("scope",)` and `age_days == 180`. Set it to `at(-7 - 181)`: `("age", "scope")`.
   - `reuse_candidates` for the baseline and NIST assessments is `[]`. No candidate anywhere has `framework_id == "dpdpa"`.
   - Invalidate `a_access_q1` through `evidence_service.transition_evidence(..., to_status="invalidated", reason="test")`: validation candidates become `[]`; posting its (old) `source_use_id` → 409.
   - An unknown assessment id → `GET` 404.
   - Unmigrated: an Assessment with `engagement_id=None` → `reuse_candidates == []`, and its page renders "not linked to an engagement".
   - Statement bound: `reuse_candidates` on the validation issues at most 6 SQL statements (count with a SQLAlchemy `before_cursor_execute` listener).
6. **Seeded reuse confirmations are audited, and reused evidence feeds the validation's analysis.**
   - Exactly two `evidence_reuse.confirmed` events for the validation: `a_policy` (`ISO.A5.1`, `age_days` 189, warnings `["age", "scope"]`) and `a_dr_report` (`ISO.A5.30`, 113, `["scope"]`), both with `acknowledged_warnings: True`.
   - `evidence_panel_rows(db, validation)` includes `a_policy` and `a_dr_report` with `mapped_in is True`, and `a_access_q3` with `mapped_in is False`; it does not include `a_ropa` or `a_access_q1`.
   - The validation's ISO.A5.1 `proposed` revision's `citations_json` cites `a_policy`'s version id, and ISO.A5.30's cites `a_dr_report`'s. ISO.A5.18's cites `a_access_q3`'s version, **not** `a_access_q1`'s.
7. **Conclusion independence (D-P4-2-K).**
   - Baseline Conclusions: exactly `{dpdpa: CH3.ACCESS.1, CH2.SECURITY.1, CH2.CONSENT.3; iso27001: ISO.A5.1, ISO.A5.18, ISO.A5.30}`. Validation: exactly `{iso27001: ISO.A5.1, ISO.A5.18, ISO.A5.30}`, with no dpdpa row. NIST: `{nist_csf: NIST.GV.PO.01, NIST.PR.AA.03, NIST.RS.MA.01}`. The outcomes match table 3.
   - The baseline and validation Conclusion id sets are disjoint. Baseline ISO.A5.18 is `non_compliant` and validation ISO.A5.18 is `compliant`.
   - Every Conclusion has `version == 2` and revisions exactly `["proposed", "approved"]` (the validation never touched a baseline row). Every `proposed` revision's `analysis_run_id` belongs to an `AnalysisRun` of the **same** assessment.
   - Baseline ISO.A5.1 (`compliant`) and DPDPA CH2.SECURITY.1 (`partially_compliant`) both cite a version of `a_policy` (distinct framework Conclusions from one document).
8. **Action lifecycle (table 4).** For each of the six keys: the Action's `status`, the Finding's `status`, the history action sequence, `owner` and `target_date.date()` equal table 4. `a_access`'s `closed` and `verified` entries carry `evidence == {"evidence_id": a_access_memo, "evidence_version_id": <its v1>, "version_number": 1, "sha256": <its hash>, "filename": <its filename>}`. `b_mfa`'s `closed` entry names `b_mfa_fix`'s version. Every actor in every entry is `consultant:Priya Sharma`.
9. **Engagement-level reporting (D-P4-2-N).**
   - `engagement_rollup(db, A, today=demo.anchor).counts` and `(…, B, …)` equal the expected rollups exactly. A's `overdue` list is exactly `a_dr`; B's is exactly `b_ir`; B's `awaiting_verification` list is exactly `b_mfa`.
   - `GET /engagements/{A}/remediation` → 200, and `data-rollup-count="total"`'s cell shows 4. `GET /engagements/{B}/remediation` → 200 and shows 2.
   - The one `report_snapshots` row has `type == "integrated_report"`, `engagement_id == A`, `is_issued` true. Its `generated_event` source lists exactly the baseline then the validation assessment ids. The baseline and validation have `review_status == "approved"`; NIST's is not `"approved"`.
   - `GET /engagements/{A}/integrated-reports` → 200; `GET /engagements/{B}/integrated-reports` → 200. `report_content.integrated_report(db, B).sections == []`.
10. **Magic-link intake (D-P4-2-L).** `b_policy` and `b_mfa_export` have `uploaded_by == f"client_link:{demo.magic_link_id}"` and `assessment_id is None`; `b_mfa_fix` has `uploaded_by == "consultant"` and `assessment_id == nist`. The two `magic_link.upload_received` events name `item-1` and `item-2`, and no upload names `item-3`. `magic_link_rows(db, B)` has one row: `status == "active"`, `uploads_used == 2`, items equal the three titles. `LongitudinalDemo` has no field containing a token (no field value matches `^[A-Za-z0-9_-]{22}$`).
11. **Re-running is refused (D-P4-2-O).** A second `seed_longitudinal_demo(db, http)` raises `DemoAlreadySeeded` whose `.message` equals the D-P4-2-O text. Every table count from scenario 1 and the blob file count under the upload root are unchanged. A fresh database with only a `Client` named `Loomwire Labs Inc.` also raises it before any write.
12. **Structural guards.**
    - The set of `(method, path)` over `app.routes` whose path contains `/evidence-reuse` is exactly `{("GET", "/assessments/{assessment_id}/evidence-reuse"), ("POST", "/assessments/{assessment_id}/evidence-reuse/{source_use_id}/confirm")}`.
    - `app/services/evidence_reuse.py` contains none of `.commit(`, `db.delete(`, `session.delete(`, and `"delete" not in` its lower-cased source. `inspect.getsource(evidence_reuse_page)` has no `.commit(`.
    - The regex `confirm all|select all|approve all|\bmultiple\b|\|\s*safe\b|bulk` (case-insensitive) matches nothing in `app/services/evidence_reuse.py`, `app/routers/evidence_reuse.py` or `pages/evidence_reuse.html`. The template contains exactly one `type="checkbox"` literal. It contains neither `CyberAssess` nor `overall_score`.
    - `inspect.getsource(seed_longitudinal_demo)` contains neither `SessionLocal` nor `settings.database_url`, nor the word `print(`. `inspect.getsource(seed_longitudinal_cli)` contains `create_backup(` and doesn't contain `token`.
    - `inspect.signature(confirm_reuse)` has `acknowledge_warnings`, and no parameter annotation contains `list` (one candidate per call).
13. **Nothing else moved.** The full suite passes, including `tests/test_phase1_prefill.py` (which imports the seed module), `tests/test_evidence_service.py`, `tests/test_magic_links.py`, `tests/test_findings.py`, `tests/test_remediation_tracking.py`, `tests/test_pdf_updates.py`, `tests/test_white_label.py` and `tests/test_no_blended_scoring.py`, all unmodified.

## Done criteria

- `tests/test_longitudinal_demo.py` passes. `.venv/bin/pytest -q` passes in full: **502 + N**, where N is the number of new cases. State the baseline you measured. In a fresh `git worktree`, expect the known one-time `_guard_dev_database_untouched` teardown error described above, and nothing else.
- `git diff --stat main` shows changes **only** in: `scripts/seed_test_companies.py`, `app/services/evidence_reuse.py` (new), `app/routers/evidence_reuse.py` (new), `app/templates/pages/evidence_reuse.html` (new), `app/main.py`, `app/templates/partials/documents_tab.html`, `tests/test_longitudinal_demo.py` (new), `tasks/todo.md` and this handoff.
- `git diff main -- scripts/seed_test_companies.py` shows only the appended section and the `main()` flag: **no existing line of any existing function changes except inside `main()`.**
- `git diff --stat main -- app/services/evidence.py app/services/magic_links.py app/services/findings.py app/services/remediation_rollup.py app/services/report_content.py app/services/report_snapshots.py app/routers/web.py app/routers/analysis.py app/routers/magic.py app/routers/evidence.py app/models alembic/versions scripts/backup.py scripts/migrate_legacy.py requirements.txt tests/test_phase1_prefill.py` is empty. `alembic heads` is still exactly `4e8c1a9d2b57`. `grep -rn "relationship(" app/models/` is empty.
- **Smoke test** (per the project rule; record the outputs in Results). Use a throwaway database and upload tree, never the real dev DB: `DATABASE_URL=sqlite:///<tmp>/demo.db UPLOAD_DIR=<tmp>/uploads .venv/bin/python scripts/seed_test_companies.py --longitudinal`. Then:
  1. Paste the CLI output (it must show the backup path and the URLs, and contain no `/magic/`).
  2. Run it a second time and paste the "already seeded" line.
  3. Paste `SELECT c.name, e.name, a.description, a.selected_frameworks, date(a.created_at) FROM clients c JOIN engagements e ON e.client_id = c.id JOIN assessments a ON a.engagement_id = e.id ORDER BY c.name, a.created_at;`
  4. Paste `SELECT action, metadata_json FROM audit_events WHERE action = 'evidence_reuse.confirmed';`
  5. Paste `SELECT f.title, f.status, a.status, a.owner, date(a.target_date) FROM findings f JOIN actions a ON a.finding_id = f.id ORDER BY f.title;`
  6. Against the same temporary DB, through the in-process ASGI app (or `uvicorn` if a socket bind is allowed): `GET /` shows both clients; `GET /assessments/{validation}/evidence-reuse` shows one candidate with both warnings; `GET /engagements/{A}/remediation` and `/engagements/{A}/integrated-reports` return 200.
  7. **Browser check**, if a browser is available: walk dashboard → engagement A → validation → Documents tab → "Reuse evidence from earlier assessments" → confirm the remaining candidate without, then with, the acknowledgement. If no browser is available, say so in Results. Do not claim it.

## Rollback

- **Code:** `git revert`. No schema change. Rows written by `confirm_reuse` are ordinary `evidence_uses` and `audit_events` rows that the reverted app reads normally (the mapped evidence stays in the target's scope, which is exactly what a manual `POST /api/evidence/{id}/uses` would have produced).
- **Demo data:** the CLI takes a P1-6 backup before writing; `scripts/restore.py <backup_dir>` returns the DB and upload tree to their pre-seed state. There is deliberately no in-script purge (D-P4-2-O).

## Open questions (deliberately flagged, not resolved here)

1. **Persisted decline.** PR-025 requires that declining has no side effect, which this satisfies, but a declined suggestion then stays listed forever. A "dismissed" record (and whether it counts as a side effect) is a product decision. The PRD demo-track's "rejected reuse suggestion" would need it.
2. **Period and cut-off.** PR-025's prompt should also show the evidence's *period*, and the scope warning should eventually compare assessment period/cut-off, not just frameworks. The schema has no period or cut-off columns on `assessments` or `evidence`. That is a Claude-owned schema decision.
3. **Creating a validation assessment in the product.** There is no route to add an assessment to an existing engagement (the seed does it directly, D-P4-2-J). The PRD's Reassess step 1 needs one. It is a small `engagement_factory` extension plus a form, but it is not in the plan's P4-2 line.
4. **Cross-engagement / client-level reuse** (PRD: "`Client` owns … client-level evidence reuse eligibility") remains deferred from P2-1.
5. **Reuse into an archived engagement:** P4-4's call (D-P4-2-P).

## Report back

Append a `## Results` section to this file containing:
- The route table as implemented (method, path, success code, template), flagging any deviation from D-P4-2-G.
- `REUSE_AGE_WARNING_DAYS`, the message constants and `AUDIT_METADATA_KEYS`, copied from the code.
- The anchor date of your smoke run and the seven smoke outputs from Done criteria.
- `pytest -q` output (baseline you measured, final count) and the pass count of `tests/test_longitudinal_demo.py`, plus confirmation that no existing test file was modified and that the protected-file `git diff --stat` is empty.
- Anything this document got wrong about the current code (a drifted symbol, a route that behaves differently, a count that doesn't hold). Name it; don't silently work around it.

## Results

Implemented with no deviation from D-P4-2-A through D-P4-2-Q.

### Routes

| Method | Path | Success | Template |
|---|---|---:|---|
| GET | `/assessments/{assessment_id}/evidence-reuse` | 200 | `pages/evidence_reuse.html` |
| POST | `/assessments/{assessment_id}/evidence-reuse/{source_use_id}/confirm` | 303 | Redirects to the reuse page; 400/409 re-renders `pages/evidence_reuse.html`, and 404 uses the declared HTTP error |

No deviation from D-P4-2-G.

### Reuse constants

```text
REUSE_AGE_WARNING_DAYS = 180
ASSESSMENT_NOT_FOUND = "Assessment not found"
REUSE_NOT_AVAILABLE = "This evidence is no longer available for reuse in this assessment. Reload the page. Nothing was saved."
REUSE_ACK_REQUIRED = "Confirm that this evidence still applies despite the warnings shown. Nothing was saved."
AUDIT_METADATA_KEYS = (
    "acknowledged_warnings", "age_days", "evidence_id", "evidence_version_id",
    "framework_id", "reference_date", "requirement_id", "sha256",
    "source_assessment_id", "source_use_id", "warnings",
)
```

### Smoke run

Anchor date: `2026-09-24`. The smoke used `/private/tmp/p42-longitudinal-smoke.xFvdYi`, a throwaway database, and a throwaway upload tree.

1. First CLI run:

```text
Backup written to backups/20260924-041802-668259
Seeded Meridian Ledger Technologies Pvt Ltd and Loomwire Labs Inc.
URLs:
/
/engagements/c77e8768-20fd-4f3f-9f40-bc0435f3d752
/engagements/460b1a31-3e62-4647-aa85-da67459b4e18
/assessments/c2ff6c73-a2a9-4cf3-88a8-8d4684ee87d2/evidence-reuse
/engagements/c77e8768-20fd-4f3f-9f40-bc0435f3d752/remediation
/engagements/c77e8768-20fd-4f3f-9f40-bc0435f3d752/integrated-reports
/engagements/460b1a31-3e62-4647-aa85-da67459b4e18/remediation
FIRST_EXIT=0
```

No `/magic/` URL was printed.

2. Second CLI run:

```text
Longitudinal demo already seeded (Meridian Ledger Technologies Pvt Ltd, Loomwire Labs Inc.); nothing was changed. Restore a pre-seed backup with scripts/restore.py to seed it again.
SECOND_EXIT=0
```

3. Hierarchy query:

```text
Loomwire Labs Inc.|NIST CSF 2.0 gap assessment|NIST CSF 2.0 baseline gap assessment|["nist_csf"]|2026-08-25
Meridian Ledger Technologies Pvt Ltd|FY2026 DPDPA and ISO 27001 programme|Baseline gap assessment (DPDPA + ISO 27001)|["dpdpa", "iso27001"]|2026-03-08
Meridian Ledger Technologies Pvt Ltd|FY2026 DPDPA and ISO 27001 programme|Remediation validation (ISO 27001)|["iso27001"]|2026-09-17
```

4. Reuse audit query:

```text
evidence_reuse.confirmed|{"acknowledged_warnings": true, "age_days": 189, "evidence_id": "384093d5-e8cd-442a-a59b-220fe091b4c6", "evidence_version_id": "56a9bc5a-eeb2-47a1-bc54-3ba1e0308a58", "framework_id": "iso27001", "reference_date": "2026-09-17", "requirement_id": "ISO.A5.1", "sha256": "07f88aeed1632ac91b066242d9325af7e3de2175b20080214c490548661f46cb", "source_assessment_id": "2efaebc3-0a6d-4ad9-81b4-36b709330491", "source_use_id": "238b2210-8370-4395-92bb-614af806b3bc", "warnings": ["age", "scope"]}
evidence_reuse.confirmed|{"acknowledged_warnings": true, "age_days": 113, "evidence_id": "1863b8f9-b8b4-4e83-b20b-8dd581f49511", "evidence_version_id": "e7c9b474-c14d-4146-a1dd-e4e68fdad56e", "framework_id": "iso27001", "reference_date": "2026-09-17", "requirement_id": "ISO.A5.30", "sha256": "80e37b05ac713f59b4cfafa8714a703aa7a6cc084eb045045f7735575955aaa1", "source_assessment_id": "2efaebc3-0a6d-4ad9-81b4-36b709330491", "source_use_id": "bdae10eb-f416-4991-b572-b7ef2f2b11a5", "warnings": ["scope"]}
```

5. Action query:

```text
DR failover exceeded the 4-hour RTO|in_progress|in_progress|Arjun Mehta|2026-09-10
DR failover still not re-tested within the RTO|open|open|Arjun Mehta|2026-10-15
No documented incident response plan|open|open||2026-09-21
No in-app consent withdrawal|open|open|Rhea Kapoor|2026-10-24
Quarterly access review skipped three production systems|resolved|verified|Arjun Mehta|2026-07-26
Three service accounts exempt from MFA|in_progress|closed|Dev Anand|2026-10-08
```

6. In-process ASGI checks against the same database:

```text
{'dashboard_both_clients': True, 'reuse_page': True, 'remediation': True, 'integrated_reports': True}
```

7. Browser check: no browser was available in this environment, so no browser result is claimed.

### Tests and scope

- Existing-suite baseline: `502 passed, 126 warnings in 44.92s` using `pytest -q --ignore=tests/test_longitudinal_demo.py`.
- `tests/test_longitudinal_demo.py`: `13 passed, 44 warnings in 10.16s`.
- Final `.venv/bin/pytest -q`: `515 passed, 170 warnings in 53.83s`.
- No existing test file was modified; the test inventory was grepped before implementation and had no longitudinal/reuse contract file.
- The protected-file `git diff --stat` is empty.
- `alembic heads` remains `4e8c1a9d2b57 (head)`.
- No current-code drift forced an alternative; no numbered decision was changed.
