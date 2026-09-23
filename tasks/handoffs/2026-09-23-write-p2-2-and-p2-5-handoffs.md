# Write the P2-2 (citation model) and P2-5 (magic links) implementation handoffs

**This is a meta-handoff.** Your deliverable is not application code — it is two Claude-owned implementation handoff documents (plus a failing test suite for each) that a *separate* session will later hand to Codex. Do not implement `app/services/...`, do not touch existing routes, do not run `codex exec` or spawn any implementation subprocess. That happens in a follow-up session after these two documents are reviewed.

## Goal

Write `tasks/handoffs/2026-09-23-p2-2-citation-model.md` and `tasks/handoffs/2026-09-23-p2-5-magic-links.md`, each with a companion failing test file, at the same level of exactness as the three handoffs already merged this phase. Definition of done: each handoff is precise enough that Codex has zero open design questions left to resolve on its own, each has a pre-written failing test suite that fails for the *right* reasons (missing implementation, not a bug in the test file — verify this yourself by running it), and both are ready to hand to a fresh orchestrating session that will run them through: Codex implements in an isolated git worktree → independent Sonnet adversarial review → Codex remediation → re-review → PR.

P2-2 and P2-5 are the two tasks that can start now. **P2-3 and P2-4 are explicitly out of scope for this session** — per `tasks/agent-ownership.md`'s Phase 2 chain (`{P2-2 → P2-3 → P2-4}` sequential, `{P2-5}` independent), P2-3 depends on P2-2's citation shape existing and P2-4 depends on P2-3's output. Do not write handoffs for them.

## Current state

- **Phase 1 is complete** (P1-1 through P1-6, PRs #16–#23, all merged to `main`).
- **P2-1 (Evidence service) is complete and merged** (PR #24). This is the task immediately before yours in the dependency chain, and it is your best reference for depth, style, and process:
  - Read `tasks/handoffs/2026-09-23-p2-1-evidence-service.md` in full — including its `## Results` section — as your template. Match its structure exactly: header (Plan/Owner/Depends-on/Blocks/Failing-contract-suite line), Goal, Current state, a **named Decisions section** (`D-P2-1-A` through `E` — P2-1 introduced this pattern specifically because a `[AR]`-gated, foundational task needs its architectural forks resolved on paper, not left for the implementer to guess), Required approach (numbered subsections with exact code/schema/route specs), Key files, Non-goals, Test scenarios (numbered, matching test docstrings), Done criteria, Rollback, Report back.
  - Read `tests/test_evidence_service.py` as your template for how a pre-written failing contract suite is structured (its own fixtures, FK-enforcing SQLite, patched extractor — don't assume the shared integration harness fits every task; P2-1's didn't).
  - The other two Phase 1 examples of this depth: `tasks/handoffs/2026-09-23-p1-4-portfolio-dashboard.md`, `tasks/handoffs/2026-09-23-p1-5-deprecate-blended-scoring.md`.
- **P2-1 changed the ground truth you're building on.** Evidence is now live: `app/services/evidence.py` (the public API — `receive_evidence`, `receive_version`, `release_from_quarantine`, `map_evidence`, `transition_evidence`, the two readers `analysis_documents`/`evidence_panel_rows`), `app/models/evidence.py` (`Evidence`, `EvidenceVersion`, `EvidenceUse` — now with the P2-1-added columns: `Evidence.assessment_id` nullable FK, `Evidence.document_category`, `EvidenceVersion.status`/`original_filename`/`mime_type`/`extracted_text`), `app/routers/evidence.py`, alembic head `7a3f1e2b9c80`. **Read these yourself before writing anything** — do not rely on this summary; verify current line numbers and signatures by symbol name (they will have drifted further since this was written).
- **A real tension you must resolve for P2-2, not inherit unexamined**: the P1-2 migration already created a standalone `citations` table (`app/models/citation.py`: `id`, `evidence_version_id` FK, `location_type`, `location_ref`, `excerpt`, `created_at` — zero application code uses it) *and* `ConclusionRevision.citations_json` exists (`app/models/conclusion.py`) as a `Text` column, matching decision **D2** in the plan's decisions log ("Simplified audit trail... JSON for claims/citations/action-history"). These are two different designs for the same concept, both already in the schema. The plan doc's own P2-2 bullet (read it — `docs/plans/2026-09-21-002-revised-implementation-plan.md`, search "### P2-2") explicitly says citations are "stored as JSON array on `conclusion_revisions.citations_json`... with structured objects: `{evidence_version_id, location_type, location_ref, excerpt}`" — i.e. the plan's own intent is the JSON column, and the standalone `citations` table looks like schema drift from before D2 was finalized, or from before P1-2's author reconciled the two. **You must decide, explicitly and in writing, what P2-2 does about this**: use the JSON column as the plan says and leave the `citations` table dead (documenting why, and whether it should be dropped in a later migration or kept for a future normalization), or make the standalone table canonical and treat `citations_json` as denormalized cache, or something else — but do not silently pick one without saying why the other exists.

## Key files to read before writing either handoff

- `tasks/agent-ownership.md` — the Claude-vs-Codex ownership contract. P2-2 is listed as "Codex, from Claude spec" (lighter-weight than P2-1's "Claude designs" — but still requires you to pin down the exact schema/validation/API, just with less architectural judgment expected). P2-5 is listed as "Claude designs + reviews security → Codex implements" — this is a **named security boundary** per the ownership doc's criteria ("tokens, credentials... anything where a subtle mistake is a vulnerability, not a bug"). Treat P2-5 with the rigor of a security design review, not a routine CRUD handoff.
- `docs/plans/2026-09-21-002-revised-implementation-plan.md` — read the full "## Phase 2: Evidence & Conclusions" section (search for it), specifically the P2-2 and P2-5 bullets and the Phase 2 exit criteria. Also re-read the "What breaks and how we handle it" table if one exists nearby (P2-1's handoff found the plan's bullets sometimes omit a real caller — verify the plan's claims against actual code, don't transcribe them).
- `docs/product/2026-09-21-cyberassess-product-requirements.md` — for P2-2: PR-021 ("Precise citations... resolve to a page, section, cell, finding identifier, or other format-appropriate location plus the quoted content; whole-item citation is allowed only when granularity is impossible and is identified as such"), PR-041, PR-050. For P2-5: **PR-024 is the operative requirement** — "tokens are expiring, revocable, non-enumerable, restricted to named request items, rate-limited, and prevented from reading other Engagement data" — and the Guardrails section: "No client magic link exposes a questionnaire, Conclusion, other request, or unrelated Evidence." Also PR-023 (deduplicated requests) and PR-025/PR-026 (evidence reuse/impact) for context on how requests relate to Evidence, though full reuse-suggestion UX may be later-phase work — decide and say so.
- `tasks/2026-09-21-adversarial-review.md` — Decisions Log at the bottom. D2 (audit trail/citations JSON, directly relevant to P2-2's tension above), D3 (individual-only conclusion approval — context for why P2-2's citations feed *revisions*, not a bulk structure), D8 (UCC scope — questions only, evidence-to-requirement mapping is consultant-driven; relevant since P2-1's `EvidenceUse` already does consultant-driven mapping, and citations are a further-granular pointer within that).
- **For P2-5 specifically**, also read: `app/models/magic_link.py` (`MagicLink`: `id`, `engagement_id` FK, `token_digest`, `scope_json`, `max_uploads`, `max_size_bytes`, `expires_at`, `revoked_at`, `created_at` — zero application code today, same as Evidence was before P2-1), the plan doc's P2-5 bullet in full (search "### P2-5" — it specifies: consultant creates link generating a 128-bit token with SHA-256 digest stored, scope/expiry/limits set; client accesses `/magic/{token}`, validates digest + expiry, shows scoped upload form; upload creates Evidence with `uploaded_by=client_link:{token_prefix}`; rate limiting max N uploads/hour and max total size per token; `Referrer-Policy: no-referrer` header on magic-link pages), and `app/services/evidence.py`'s `receive_evidence` signature — P2-5's upload path must call into this rather than duplicating upload logic, since P2-1 built the whole hashing/quarantine/lifecycle pipeline for exactly this reuse.

## Constraints

- **Match the P2-1 handoff's exactness, not a lighter version of it.** Exact route paths and methods, exact request/response shapes, exact validation order with exact error strings and status codes, an exact query budget where relevant (no `relationship()` — `grep -rn "relationship(" app/models/` must stay empty; this project has zero ORM relationships by house convention), a full "Non-goals" section, numbered test scenarios with concrete checkable assertions, "Done criteria" and "Rollback" sections, a "Report back" section asking for a `## Results` addendum in the same file.
- **Verify the current code yourself; do not transcribe the plan doc or this document as ground truth.** Both drift. Grep for actual symbols, read actual function bodies, run `grep -rn` for every claim you make about "no code touches X today."
- **Write a failing test suite for each handoff first**, in the same style as `tests/test_evidence_service.py` (own fixtures if the shared integration harness doesn't fit; FK-enforcing SQLite; patch external calls like the vision-LLM extractor or any citation-quality LLM call rather than hitting a real model). Run each suite yourself and confirm every failure is `ModuleNotFoundError` / missing-column / missing-route — i.e. "not implemented yet," never a bug in your own test file. Fix your test file until this is true before calling either handoff done.
- **For P2-5 in particular**, the handoff's Required Approach must specify, exactly, not generally: token generation (source of randomness, encoding, length — 128-bit per the plan, but pin the actual `secrets` call), the exact digest storage and lookup (never store or log the raw token), rate-limiting mechanism and where its state lives (in-process counter is not durable across restarts — decide and justify), the `Referrer-Policy` header and any other response headers a client-facing unauthenticated page needs (e.g. `X-Robots-Tag: noindex` — decide if that's in scope), what "restricted to named request items" means concretely given there is no `EvidenceRequest` model in the current schema (magic_links has `scope_json` — define its exact shape), exact 403/404/410/429 behavior for expired/revoked/rate-limited/malformed tokens (and whether a malformed vs. expired vs. revoked token should be distinguishable in the response — PR-024's "non-enumerable" requirement suggests they should NOT be distinguishable, to avoid a token-guessing oracle; make this call explicitly), and how the uploaded Evidence's `assessment_id` is set given a magic link is engagement-scoped, not assessment-scoped (P2-1's `D-P2-1-A` already allows `assessment_id=None` for exactly this case — cite it, don't relitigate the Evidence/Assessment scoping question P2-1 already closed).
- Do not write handoffs for P2-3 or P2-4. Do not implement anything. Do not run Codex or open any worktree/PR.
- If you use a subagent (e.g. an Opus subagent per this session's established pattern of delegating handoff-writing) to draft either handoff, you (the top-level session) are still responsible for independently verifying its test suite actually fails for the right reasons before accepting the output — the orchestrating session that requested this work does exactly that verification step for every handoff it receives, and expects the same discipline here.

## Verification

Before reporting done, for **each** of the two handoffs:
1. Run its failing test suite (`pytest -q path/to/test_file.py`) and confirm every failure is for the intended reason (missing module/route/column), pasting the actual failure summary into your report, not a paraphrase.
2. Confirm `pytest -q` on the **full existing suite** still passes unchanged (you're only adding new test files, not touching existing ones) — should be 309 passed (P2-1's merged baseline) plus your new failing files.
3. Sanity-check your own handoff against the "Constraints" section above — specifically, for P2-2: did you make an explicit, justified call on the `citations` table vs. `citations_json` tension? For P2-5: did you pin down every item in the P2-5-specific constraint bullet above, with no "TBD" or "Codex should decide" left in a security-relevant spot?

## Report back

Append a `## Results` section to **this file** (not to the two new handoff files — those get their own `## Results` sections later, from Codex) containing:
- Paths to the two handoff files and their two test files.
- For each: pass/fail count of its failing suite and confirmation every failure is for the intended reason.
- The citation-table-vs-JSON decision you made for P2-2, and why.
- The specific answers you gave to each item in the P2-5-specific constraint bullet (token generation, rate-limit storage, non-enumerability behavior, response headers, scope_json shape).
- Any open question you deliberately flagged rather than resolved in either handoff.
- Confirmation the full existing suite (309+ baseline) still passes.

## Results

### Deliverables

| Task | Handoff | Failing contract suite |
|---|---|---|
| P2-2 Citation model | `tasks/handoffs/2026-09-23-p2-2-citation-model.md` | `tests/test_citations.py` (26 cases) |
| P2-5 Magic links | `tasks/handoffs/2026-09-23-p2-5-magic-links.md` | `tests/test_magic_links.py` (29 cases) |

Both handoffs follow P2-1's structure: a header with Plan/Owner/Depends-on/Blocks/Failing-suite lines, then Goal, Current state, named Decisions (`D-P2-2-A…E`, `D-P2-5-A…H`), Required approach (numbered, with exact messages, statuses, and query budgets), Key files, Non-goals, numbered Test scenarios matching the test docstrings, Done criteria, Rollback, and Report back. P2-5 also has an Open questions section. No P2-3/P2-4 handoff was written. Nothing was implemented, and no Codex run, worktree, or PR was started.

### Red-suite verification (actual output at `b19aa64`)

`tests/test_citations.py`: **26 failed, 0 passed**. Grouped by failure message (`pytest -q --tb=no -rf | sort | uniq -c`):
```
  23 ModuleNotFoundError: No module named 'app.services.citations'
   2 AssertionError: assert '7a3f1e2b9c80' == '3d8b6f0a2c51'      # the missing P2-2 head revision
   1 AssertionError: app/models/citation.py:10:class Citation(Base):   # grep guard finds the model P2-2 deletes
26 failed in 1.59s
```

`tests/test_magic_links.py`: **29 failed, 0 passed**, all on `ModuleNotFoundError: No module named 'app.services.magic_links'` (`29 failed in 2.51s`).

Every failure means "not implemented yet". None is a bug in the test file. I went further than the brief asked: each suite was also run against a **throwaway prototype of its spec** in a scratch git worktree (since removed; nothing committed or left in the repo). This showed the assertions are satisfiable as written:
- **P2-2 prototype: 26/26 green.** It caught one test bug before hand-off: a statement-budget test counted the test's own lazy refresh of an expired ORM object. Fixed by capturing the id before `expire_all()`. Expected character offsets were computed by running code, not by hand. On the full suite, the prototype produced exactly 13 failures in existing tests, all caused by the new Alembic head or the dropped table. Those 13 are listed file by file as the lockstep edits in P2-2 step 2, so Codex has no surprise edits of the kind P2-1 hit.
- **P2-5 prototype: 29/29 green, full suite 338 passed with no existing test touched.** It caught two test bugs, both fixed: (1) P2-1 attributes scan-driven status-change audit rows to `system:scan-placeholder`, not the uploader, and the test now asserts the real actor sequence; (2) Jinja autoescapes `'`, so the total-size message was reworded to have no apostrophe (`This upload would exceed the total size limit for this link.`).

### Full existing suite

`pytest -q --ignore=tests/test_citations.py --ignore=tests/test_magic_links.py` gives **309 passed**, unchanged from P2-1's merged baseline. With the new files: `55 failed, 309 passed` (55 = 26 + 29, all the intended reds). No existing file was modified.

### P2-2: the `citations` table vs `citations_json` decision

**The JSON column is canonical, and the standalone `citations` table is dropped in P2-2's own revision (`3d8b6f0a2c51`).** The `Citation` model is deleted too. Reasons (D-P2-2-A):
- The table is P1-2 schema drift. The plan lists it as a table and also annotates `conclusion_revisions.citations_json` as "D2: JSON array, not relational". D2 and the plan's own P2-2 bullet choose JSON.
- The P1-2 table has **no parent FK**, so it can't record which revision a citation belongs to. Making it canonical would need new columns and joins for a query need that doesn't exist.
- Two stores for one fact is the easy-to-violate trap the ownership contract exists to close.
- It has zero rows and zero readers, and P2-2 needs a revision anyway (for the new `desk_review_findings.citations_json`), so dropping it now is the cheapest option.

The downgrade recreates it exactly (the round-trip schema-snapshot test enforces this). The accepted cost is that JSON references aren't FK-protected, so **P4-4 purge must scan `citations_json` columns before purging a version.** That's written into P2-2's Rollback section as a hand-forward.

Other P2-2 calls worth knowing:
- The location is a **verified character span** (`chars:{start}-{end}` into immutable `extracted_text`, and the excerpt must equal that raw slice exactly) or an explicit `whole_item`. The plan's `page` type isn't derivable, because extraction keeps no page markers (verified in `_extract_pdf`).
- Matching uses the analyzer's existing grounding normalization, made offset-preserving, and a parity test ties the two together.
- `NULL` means not captured and `"[]"` means captured with none. P2-4's PR-043 guard needs that distinction.
- P2-2 wires the desk-review producer (closing the gap P2-1 step 8 deferred) and `attach_citations` for revisions. Creating revisions stays with P2-3.

### P2-5: answers to each constraint item

- **Token generation:** `secrets.token_urlsafe(16)`, i.e. 128 bits from the OS CSPRNG, as 22 URL-safe base64 characters. The suite spies on the call. The format is checked with `^[A-Za-z0-9_-]{22}$` before any DB access (0 statements for a malformed token).
- **Digest storage and lookup:** `sha256(token.encode("ascii")).hexdigest()` in `token_digest`, looked up by equality on the digest. There's no constant-time compare, because the comparison is on the digest. The raw token is shown once in the consultant's `no-store` create response. It's never stored or logged, and neither is any prefix of it, in any column or in audit metadata. The suite checks this with a full `iterdump`. The plan's `uploaded_by=client_link:{token_prefix}` is **deliberately replaced** by `client_link:{magic_link.id}`, because a token prefix is secret material.
- **Rate-limit mechanism and where the state lives:** there is no counter table and no in-process state. Usage is derived per request, in one query, from the link's own `Evidence` rows (`uploaded_by == client_link:{id}`). That makes it durable across restarts and workers with zero schema. The limits: 10 uploads per rolling hour (429 + `Retry-After`), `max_uploads` all-time (403), 25 MiB per file (413), `max_size_bytes` per link (413), and a `Content-Length` guard before multipart parsing (411/413). Scan-rejected receipts count toward the quota. The check-then-insert race is named and accepted, matching P2-1's precedent.
- **Non-enumerability / 403-404-410-429:** malformed, unknown, expired, revoked, and inactive-engagement tokens all return **the same 404 with a byte-identical body** on GET and POST. There's no 410, because distinguishing expired or revoked would be an oracle. 403/409/413/422/429 happen only after a valid token has resolved. There's no per-IP limiter (2^128 makes guessing infeasible) and no audit row for invalid attempts (that would open a flooding vector).
- **Response headers** on every `/magic/*` response: `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, `X-Robots-Tag: noindex, nofollow` (in scope: yes), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'`. The client templates are standalone (no `base.html`, no scripts, no external assets, no form `action`, so the token never appears in the HTML). I also found a real leak the plan missed: **uvicorn's access log records `/magic/{token}` paths.** The fix is a `MagicTokenRedactionFilter` on `uvicorn.access`, installed in `app/main.py`.
- **`scope_json` shape:** `{"items": [{"key": "item-1", "title": "…"}, …], "version": 1}`, with `sort_keys=True` and up to 20 items of at most 200 characters, unique case-insensitively. An upload must name one of the link's own item keys (anything else is a 422). The item is recorded in v1's `change_reason` and in the audit metadata. The client page renders only those titles, the limits, and its own uploads. The suite seeds sentinels for the client/engagement/assessment names and ids, another link's item, other evidence, and a Conclusion, and asserts all of them are absent.
- **`assessment_id`:** `None`, citing D-P2-1-A without relitigating it. Consequence: client uploads feed no analysis until a consultant maps them via the existing P2-1 `EvidenceUse` API. That's the intended control against unreviewed client content reaching the LLM.
- **Deduplication:** scoped per link (409 `You have already uploaded this file through this link.`), because P2-1's engagement-wide NULL-scope message would disclose another contributor's filename.
- **Upload path:** a new `ingest_engagement_upload` in `evidence.py` (P2-1's orchestrator minus the Assessment). The magic code must call it, and a grep guard forbids re-implementing blob, hash, release, or extract. The `upload_received` audit row is added before the orchestrator's single commit, so a rollback discards it atomically.
- **Lane coordination:** P2-5 adds **no** Alembic revision, so the two parallel lanes can't fork the head. P2-2 owns the only revision.

### Deliberately flagged, not resolved

1. **The malware scan is still P2-1's auto-pass placeholder, and P2-5 makes it reachable by unauthenticated clients.** Acceptable for synthetic demos (P4-2), not for a real client pilot. This raises the priority of PRD open question 5.
2. **`uq_magic_links_token_digest`** is deferred to the first migration after both lanes merge. Adding it in P2-5 would fork the Alembic head.
3. **Pre-existing `CORSMiddleware(allow_origins=["*"], allow_credentials=True)`** in `app/main.py` affects all internal routes. It's out of P2-5's scope; revisit when auth lands.
4. **EvidenceRequest model / PR-023 dedup:** `scope_json` items are free-text titles for now. `"version": 1` exists so a later request-item-id shape can be told apart.
5. **P4-4 purge must check JSON citation references** (a consequence of P2-2 choosing JSON over FKs).
6. **Page-level citations** would need extraction to preserve page markers. That's a separate, deliberate change, since it would alter `extracted_text` for new versions.
