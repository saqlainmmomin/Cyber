# Handoff: evidence fixes A, B, C (make the AI's evidence work visible and checkable)

Owner: Codex implements, Claude reviews adversarially, Saqlain clicks through and merges (`tasks/agent-ownership.md`). No Claude/Codex attribution lines in commits or PRs. Never merge. Never open `validation/companies/*/answer_key.json`. **No LLM prompt changes and no new LLM calls** (the analysis prompt is frozen by `tasks/2026-09-30-p6-5c-decision-park-v2.md`).

Why this exists: `tasks/2026-10-08-ai-coherence-map.md` (read it first, 5 minutes). Rule behind every part: **each AI step must produce something the auditor can see, check against the original evidence in one click, and act on.** Today the AI reads client evidence but most of its work never reaches the screen.

## Delivery: three PRs, in this order

| Part | Branch (off `main`) | Depends on |
|---|---|---|
| A. Client-link uploads reach the assessment | `codex/evidence-a-link-scope` | nothing |
| B. Evidence viewer | `codex/evidence-b-viewer` | nothing (A and B can run in parallel worktrees; files are disjoint) |
| C. Checkable conclusion card | `codex/evidence-c-card` | B merged (links into B's viewer) |

Each PR: behaviour tests for what it changes, full suite green with `OPENROUTER_KEY="" .venv/bin/pytest -q` (never `env -u`; `.env` still loads), and a **Click-through** section in the PR body copied from this file so Saqlain can check it in 10 minutes. Screens follow `docs/product/2026-10-07-hierarchy-rules.md` (design-pass checklist) and the Yozora macros in `app/templates/components/`. Framework-specific copy must be conditional, never a default.

Demo data for every click-through: `python scripts/demo/seed_demo.py --db data/demo.db`, then `OPENROUTER_KEY="" DATABASE_URL=sqlite:///data/demo.db UPLOAD_DIR=data/uploads/demo .venv/bin/uvicorn app.main:app --host 127.0.0.1`. The seed prints the assessment ids. Saqlain's synthetic access-review workbook (220 records, 35 rows with exception notes, no client data) is at `/Users/saqlainmomin/dpdpa-s6f1/data/uploads/demo/evidence/61b0212c-338f-4001-922a-033a569d2c71/8afb5b24-1743-4d81-81ef-f57c40d5d3f8/v1.xlsx`: read or upload it, never commit it.

---

## A. Client-link uploads reach the assessment

**Problem (confirmed in code 2026-10-08):** `magic_links.py` (around the `ingest_engagement_upload` call, ~line 506) stores client uploads at engagement level with `assessment_id=None` and no `EvidenceUse`. `evidence.active_versions_in_scope` (`app/services/evidence.py`, ~line 841) only includes evidence whose `assessment_id` matches or that has a use row, and the only UI that creates use rows is "Reuse from another assessment" (`map_evidence` callers: `routers/evidence.py:76` API-only, `evidence_reuse.py:226`). So client uploads are never analysed and the consultant has no route to them from the assessment.

**Do:**
1. When a link's `scope_json` carries `rfi.assessment_id` (set at ~line 306), after ingest call `evidence_service.map_evidence` for that assessment and each requirement/framework the requested RFI item covers (find the item → requirement mapping in the RFI snapshot the link points to; `rfi_requests.py` already counts "Evidence already mapped for N of M requirements" from the same data). Relevance: use the existing value that means "requested for".
2. Links with no RFI assessment stay engagement-level. On their evidence record, show a plain note: "Not used by any assessment's analysis yet" with the existing reuse action. Don't invent new linking UI.
3. The RFI item's "Already received" / mapped count reflects the new uploads.
4. No backfill (local-only data). No migration.

**Click-through:** issue an RFI link on the demo's current assessment, open the client link, upload any file against the access-review item → the file appears in that assessment's Evidence tab, its record lists the item's controls under Supports, the RFI item counts it as received.

---

## B. Evidence viewer (the evidence record shows what the client sent and what the AI made of it)

**Problem:** `/evidence/{id}` (`web.py` ~1496, `pages/evidence_detail.html`) shows hash, version and category only. No route serves original bytes (no `FileResponse` anywhere for evidence). The extracted text is reachable only via `/evidence-versions/{id}/span` (`requirement_review.py:199`), linked only from a small chevron hidden on small screens, and even `ref=whole` cuts at `SPAN_CONTEXT_CHARS = 1500` (`requirement_card.py:50`). The desk review's per-document catalog (summary, document_type, coverage_areas) is stored in `DeskReviewSummary.document_catalog` and never rendered (only its count, `desk_review_findings.html:4`). The record also labels a stored `access_control_policy` file as "Other".

**Do, on the evidence record page, four sections:**
1. **Original file.** New route `GET /evidence-versions/{version_id}/file` serving the stored bytes: `?download=1` → attachment; otherwise inline **only** for PDF and PNG/JPG/WEBP, attachment for everything else. Guards: version must be active/available (not scanning or rejected); resolve the storage path and refuse anything outside `UPLOAD_DIR`; content type from the stored mime; `X-Content-Type-Options: nosniff`; `Content-Disposition` filename sanitised. (No auth exists yet; Track 4 adds it. Note that in the PR.) Render: PDF in an `<iframe>`/`<embed>`, images as `<img>`, everything else a Download button. XLSX/CSV get the table in section 2.
2. **What the AI read.** The full `extracted_text` of the current version, scrollable, no 1,500 cap. Spreadsheets (text in the `Sheet: <name>` + ` | ` format from `document_processor.py`) render as one HTML table per sheet; marker lines (`[stored rows ...]`, `[sheet ... not stored ...]`, `[OCR page N]`, `[cell truncated]`) render as visible notes, not table rows. Also make `span?ref=whole` show the full text.
3. **What the AI made of it.** The matching `document_catalog` entry (catalog entries are keyed by filename; match on the version's filename and say in the PR if anything is ambiguous): summary, document type, coverage areas. If desk review hasn't run: "Desk review hasn't read this file yet."
4. **Where it's used.** The existing Supports table, visible at every width, each row linking to the text. Plus every citation of this version (conclusions and desk-review findings) linking to the highlighted passage.
5. Fix the category label so it shows the stored category.

**Click-through:** upload Saqlain's access-review workbook to the demo NIST assessment → its record shows a Download button, the "What the AI read" table has 220 detail rows including record 131 (E131, terminated, Admin, "access still enabled"), section 3 says desk review hasn't run, category shows the chosen category. Open the demo's consent PNG and a PDF → both render inline.

---

## C. Checkable conclusion card

**Problem (demo, ISO A.5.18 Access rights):** the card cites `Veldhara_Access_Review_Q2_FY26.docx, chars:37-93` with the location as raw text and the filename linking to a record with no content; it never mentions the access-review spreadsheet linked to the same control; it shows "Missing evidence: recent user access review records" while three access files are linked; the auditor can't tell which documents the AI didn't read. Desk review drops later documents silently once the 20,000-word budget is used (`desk_review.py` ~678). Desk-review citation labels fall back to "Document" for new Evidence uploads because `doc_names` is built from `AssessmentDocument` only (`web.py` ~3660; `document_id` comes from `legacy_document_id`, None for new uploads, `evidence.py` ~897).

**Do (templates `components/conclusion_card.html`, `components/requirement_card_body.html`, `partials/desk_review_findings.html`; service `requirement_card.py`):**
1. Every citation: a human location label (reuse the page/characters/whole-document wording from `pages/evidence_span.html`) linking to `/evidence-versions/{id}/span?ref=...#cited-span`. Filename links to B's evidence record.
2. **Evidence on this control:** list every active evidence item linked to the requirement in this assessment, each marked "Cited" or "Not cited by the analysis".
3. When at least one file is linked, replace the "Missing evidence" RFI suggestion with "N files linked, M cited". Keep the suggestion when nothing is linked.
4. Desk review records which documents it didn't send because of the word budget (store the filenames in the existing summary JSON; no migration, no prompt change). Show "Not read by the analysis (size limit): …" on the desk-review page and on any card whose linked evidence includes one of them.
5. Fix the "Document" label: resolve names from `Evidence`/`EvidenceVersion` as well as `AssessmentDocument`.

**Click-through:** demo current assessment → Review → Conclusions → Access rights: citation reads "Characters 37–93" and opens the highlighted passage; "Evidence on this control" lists the Q2 review (Cited) and the spreadsheet and Dec 2023 review (Not cited); no "Missing evidence" box.

---

## Out of scope (decided, don't start)
- Sending test criteria to the analysis or showing them (item 4 of the coherence map: needs Saqlain's decision, touches the parked prompt).
- Deterministic access-review checks (item 5: needs Saqlain's design).
- Fleshing out the Veldhara demo documents (Saqlain wants this later).
- Flow-plan slices S3+ (paused until A–C merge).

## Results
(Codex: append per part: files changed, test counts, click-through evidence, anything unsure.)
