# P2-5: Magic links (client evidence upload): a scoped, expiring, unauthenticated capability

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 2, task P2-5; Target Schema `magic_links`; URL Strategy `/magic/{token}`; risk row "Magic link token leakage". PRD: PR-024 (operative), the Client-contributor persona, the Permissions table + "Magic-link authorization is capability-based…", Guardrails ("No client magic link exposes a questionnaire, Conclusion, other request, or unrelated Evidence"), Data & security expectations ("signed magic-link tokens must not be logged"; upload size/type enforcement), PR-056 (magic-link actions audited).
**Owner:** Claude designs + reviews security → Codex implements (per `tasks/agent-ownership.md`). This is a **named security boundary**: it is the product's only unauthenticated write path. Every security-relevant choice is pinned below. **If the code forces a deviation from any of them, stop and report it in `## Results`. Do not pick an alternative.** Review gate: a `security-sentinel` (or equivalent) adversarial review before merge.
**Depends on:** P2-1 (Evidence service; `receive_evidence(assessment_id=None)` supported for exactly this case, D-P2-1-A), which is **merged** (PR #24).
**Blocks:** P2-6 (the workpaper shows client-provided evidence), P4-2 (the synthetic demo's "evidence uploaded via magic link").
**Parallel lane:** P2-2 (citations) runs concurrently and owns the only Alembic revision (`3d8b6f0a2c51`). **P2-5 adds no Alembic revision and no model column.** If you find you need one, stop and report it.
**Failing contract suite (already written, run it first):** `tests/test_magic_links.py` has 29 cases, all red at `b19aa64` on `ModuleNotFoundError: No module named 'app.services.magic_links'` and nothing else. The suite was validated against a throwaway prototype of this spec, which turned all 29 green (full suite 338 passed, no existing test touched) before it was discarded. Turn it green **without editing its assertions**.

## Goal

A consultant creates a link for one Engagement, naming the evidence items requested. The client opens `/magic/{token}` with no account, sees only those item titles and the link's remaining limits, and uploads files against a chosen item. Each upload becomes engagement-level Evidence through the P2-1 pipeline (hash → quarantine → release → extract), attributed to the link, audited, and invisible to every Assessment until a consultant maps it. The link is expiring, revocable, non-enumerable, restricted to its named items, rate-limited, size-limited, and cannot read any other engagement data (PR-024).

## Current state

Grounded against `b19aa64` on `main`. Re-locate everything by symbol name.

- **`app/models/magic_link.py`, `MagicLink`** (P1-2): `id`, `engagement_id` FK, `token_digest` String(64), `scope_json` Text, `max_uploads` Integer, `max_size_bytes` Integer, `expires_at` DateTime(tz), `revoked_at` nullable, `created_at`. All columns are NOT NULL except `revoked_at`. There's no index on `token_digest`. **Zero application code uses it** (`grep -rn "MagicLink\|magic_link" app scripts --include='*.py'` finds only the model, its export, and `migrate_legacy.py`'s "never touched" docstring). There is no `EvidenceRequest` model.
- **`app/services/evidence.py`**: `receive_evidence(db, *, engagement_id, assessment_id, filename, content, category, uploaded_by, actor, file_type=None, evidence_id=None, created_at=None, change_reason=None, allow_duplicate=False)` (non-committing); `release_from_quarantine` (scan placeholder `scan_blob`, looked up at call time); `ingest_upload` (committing orchestrator that requires an **Assessment**, bumps its status, and rolls back and unlinks blobs on any exception). `BLOCKING_DUPLICATE_STATUSES`, `SCAN_REJECTED_MESSAGE`, and the `EvidenceError` hierarchy (`status_code` + `message`). **There is no engagement-level orchestrator.** Scan-driven status changes are audited with actor `SCAN_ACTOR = "system:scan-placeholder"`.
- **D-P2-1-C dedupe** is scoped to the same engagement plus the same originating `assessment_id`, with NULL matching NULL. Its message names the existing file: `This file is identical to '{name}' already in this engagement's evidence.` For magic-link uploads (all `assessment_id=NULL`), that would **disclose another contributor's filename to a client**. Decision E below handles it.
- **Engagement page:** `app/routers/web.py` `engagement_detail` → `pages/engagement_detail.html` (context: `engagement`, `client`, `card`, `assessments`). Engagements are only ever created with `status="active"` (`engagement_factory.py`, `migrate_legacy.py`).
- **App wiring:** `app/main.py` registers the API routers, then `web.router`. There's `CORSMiddleware(allow_origins=["*"], allow_credentials=True)` (pre-existing and out of scope, noted under Open questions) and `SessionMiddleware`. There's no auth; every internal route is consultant-trusted (single-user MVP).
- **Logging exposure that exists today:** uvicorn's access logger (`uvicorn.access`) logs every request path. A path of `/magic/{token}` would write the raw token to the access log on every client visit, violating the PRD's "tokens must not be logged". Decision F handles it.
- **Base template:** `base.html` carries internal navigation and loads external assets. It must not be used for client pages (Decision G).
- **Baseline:** `pytest -q` → 309 passed (plus this suite's 29 red cases).

## Decisions (security design, pinned)

### D-P2-5-A. Token: 128 bits from `secrets`, URL-safe, digest-only storage

- **Generation:** `secrets.token_urlsafe(TOKEN_BYTES)` with `TOKEN_BYTES = 16`. The module does `import secrets` and calls it as `secrets.token_urlsafe`, which the suite spies on. That's 128 bits from the OS CSPRNG, encoded as **22** URL-safe base64 characters (`[A-Za-z0-9_-]`, no padding). No other source of randomness, and no derivation from ids or time.
- **Storage:** `token_digest(token) = hashlib.sha256(token.encode("ascii")).hexdigest()` goes in `magic_links.token_digest`. The raw token is **never** stored in any column, audit metadata, log line, or `uploaded_by` value, and neither is any prefix of it. **Why plain SHA-256, not HMAC or a slow KDF:** the input already carries 128 bits of entropy, so a DB leak gives an attacker a 2^128 preimage search. Peppering or stretching only matters for low-entropy secrets. The plan pins SHA-256.
- **Shown once:** the raw token (as a full URL) appears only in the HTTP response to the consultant's create request, which is sent with `Cache-Control: no-store`. It can't be retrieved again. If it's lost, create a new link and revoke the old one.
- **Lookup:** check the format first, `TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{22}$")`. A malformed token returns "invalid" with **zero** DB statements. Then query `WHERE token_digest = :digest`. The equality comparison runs on the digest inside SQLite, so timing reveals nothing about the token. That's why no constant-time compare is needed. If more than one row matches (impossible barring a bug), treat it as invalid and `logger.error("Multiple magic links share a token digest")` without logging the digest.
- **No `token_digest` index or unique constraint in P2-5.** That would need a migration, which would fork the head with P2-2. The table holds tens of rows, so a scan is trivial, and uniqueness follows from 128-bit randomness. **Handed forward:** add `uq_magic_links_token_digest` in the first migration after both lanes merge (listed in Report back).

### D-P2-5-B. Non-enumerability: every invalid token looks identical

Malformed, unknown, expired, revoked, and "engagement missing or not `active`" all produce the **same** response: HTTP **404**, the same template (`magic/invalid.html`) rendered with the same fixed context, a **byte-identical body**, and the same security headers, on both GET and POST. **Why 404, not 410/403:** a 410 for expired or revoked links would confirm that a token *was* valid once, which is an oracle for anyone holding a leaked old link or probing candidates. PR-024's "non-enumerable" is only true if expired, revoked, and never-existed are indistinguishable. The one message covers the legitimate client's need: `This link is invalid or has expired. Contact your consultant for a new link.` Responses that are distinguishable (413/422/429/403/409) happen **only after** a valid token has resolved, so they reveal nothing to a token-guesser.

**No per-IP limiter for invalid attempts.** At 2^128 candidates, online guessing is infeasible at any request rate. A per-IP limiter would need in-process state, which is non-durable and wrong behind a proxy, and would buy no security. Invalid attempts write no audit row, because an attacker could otherwise flood `audit_events`. They are logged at `INFO` without the token (`logger.info("Rejected magic-link request: invalid, expired or revoked link")`).

### D-P2-5-C. Scope: `scope_json` = the named request items. Nothing else is readable.

There's no `EvidenceRequest` model, and PR-023 request deduplication is later work (see Open questions). `scope_json` is exactly:

```json
{"items": [{"key": "item-1", "title": "Information security policy"}, {"key": "item-2", "title": "Access review evidence"}], "version": 1}
```

It's serialised with `json.dumps(..., sort_keys=True)`. Keys are `item-{n}`, 1-based in the order given, and titles are stripped. What "restricted to named request items" means concretely:
- The client page renders **only** these titles.
- Every upload must name one of these keys (`item_key`), otherwise 422. A key from another link's scope is also 422.
- The upload is bound to its item: `EvidenceVersion.change_reason` (v1) = `Client upload via magic link for requested item: {title}`, and audit metadata `item_key`.

**What the client can read, exhaustively:** the firm name (the `settings.firm_name` title), this link's item titles, its remaining upload count, its expiry, and the filenames plus Received/Rejected label of files **uploaded through this same link**. The page must **not** render the client name, engagement name, assessment names, any id (engagement, assessment, client, evidence, or link), other links' items, any evidence not uploaded through this link, anything questionnaire- or conclusion-related, or the consultant's lifecycle decisions (invalidated/archived show as "Received"). The suite seeds sentinels for each of these and asserts absence.

### D-P2-5-D. Evidence created by a link: engagement-level, attributed to the link, invisible until mapped

- **`assessment_id = None`**, per **D-P2-1-A** ("NULL for engagement-level intake (P2-5 magic links…)"). The Evidence/Assessment scoping question is closed there and is not relitigated here. A link is engagement-scoped, so its uploads are too.
- **Consequence, accepted and intended:** by D-P2-1-A's membership rule, a magic-link upload is fed to **no** Assessment's analysis until a consultant creates an `EvidenceUse` via the existing P2-1 `POST /api/evidence/{id}/uses`. This is the control that keeps client-supplied content from entering an AI analysis without consultant review (PRD rule on consultant-confirmed use, D8). No Assessment status is bumped.
- **`uploaded_by = "client_link:{magic_link.id}"`**, the link's UUID. **Deliberate deviation from the plan's `client_link:{token_prefix}`:** a token prefix is secret material. It would sit in a column shown in the UI and in audit rows, and it reduces the remaining entropy of any leaked link. The link id is non-secret, stable, and joinable. The same value is the `actor` of every audit row the client causes.
- **Category:** `None` (analysis sees `"other"`). The request item title, not a category, is what the consultant sees.

### D-P2-5-E. Deduplication is per link, and discloses nothing

Magic-link uploads pass `allow_duplicate=True` to the P2-1 pipeline and do their own check instead: refuse with 409 `You have already uploaded this file through this link.` when an Evidence with `uploaded_by == client_actor(link)`, the same `file_hash_sha256`, and `status in BLOCKING_DUPLICATE_STATUSES` exists. The same bytes through a **different** link are accepted as a separate receipt, which is correct for chain of custody. **Why:** P2-1's engagement-wide NULL-scope dedupe message names an existing file. Surfacing it would tell link B's holder that link A's contributor uploaded `board-minutes.pdf`. Surfacing even a generic "already received" would be a membership oracle ("does this engagement hold a file with these exact bytes?"). The suite asserts link B's responses never contain link A's filename.

### D-P2-5-F. Rate and size limits: durable, derived from rows that already exist

**Where the state lives:** there's no counter table and nothing in-process. Usage is computed per request from the link's own `Evidence` rows (`uploaded_by == client_actor(link)`), selecting `created_at` and `file_size_bytes` in **one** statement, with the window arithmetic done in Python after `_as_utc` normalisation (SQLite returns naive datetimes). **Why:** it survives restarts and multiple workers with zero new schema. The counted object is exactly what a quota should count: received files, including scan-rejected receipts, which P2-1 commits. Refused attempts (validation errors, dedupe, limits) create no Evidence and so don't count.

| Limit | Value | Source | Check | Response |
|---|---|---|---|---|
| Hourly rate | `UPLOADS_PER_HOUR = 10` per link | module constant, read at call time | uploads with `created_at > now − 1h` ≥ limit | **429** `Too many uploads in the last hour. Try again later.` + `Retry-After: {s}`, where `s = ceil(oldest_in_window + 1h − now)` clamped to `[1, 3600]` |
| Total count | `link.max_uploads` (consultant-set, 1–100, default 20) | row | all-time uploads ≥ max | **403** `UPLOAD_LIMIT_MESSAGE = "This link has reached its upload limit. Contact your consultant."` |
| Request body | `MAX_FILE_BYTES + MULTIPART_OVERHEAD_BYTES` (25 MiB + 64 KiB) | module constants, read at call time | `Content-Length` header, **before the body is parsed** | missing or non-numeric → **411** `Content-Length required.`; too large → **413** `FILE_TOO_LARGE_MESSAGE` |
| Per file | `MAX_FILE_BYTES = 25 * 1024 * 1024` | module constant, read at call time | `await upload.read(MAX_FILE_BYTES + 1)`, then `len > MAX_FILE_BYTES` | **413** `FILE_TOO_LARGE_MESSAGE = "Files must be 25 MB or smaller."` |
| Link total | `link.max_size_bytes` (= `max_total_mb × 1024 × 1024`, 1–500 MB, default 100) | row | `bytes_total + len(content) > max_size_bytes` | **413** `This upload would exceed the total size limit for this link.` |

The `Content-Length` guard exists because Starlette spools the whole multipart body before a handler sees `UploadFile`, so the per-file check alone would not stop a multi-GB body from filling the disk. **Race (named, accepted):** usage is check-then-insert, the same class as P2-1's D-P2-1-C race. Two truly concurrent uploads at the boundary can exceed a limit by one. Single-user MVP; revisit with a DB-level counter if it matters.

### D-P2-5-G. Response hardening for every `/magic/*` response

`SECURITY_HEADERS`, applied to **every** response from the two client routes (200, 404, 411, 413, 422, 403, 409, 429, 400). An unhandled 500 is the one exception, and it carries no token-bearing content:

```python
SECURITY_HEADERS = {
    "Referrer-Policy": "no-referrer",            # the plan's requirement: the URL never leaks via Referer
    "Cache-Control": "no-store",                 # no shared or browser cache keeps a capability URL's page
    "X-Robots-Tag": "noindex, nofollow",         # a pasted link must never be indexed (in scope: yes)
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",                   # no clickjacking of the upload form
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
}
```

The client templates are **standalone** (not `base.html`). They have no `<script>`, no `<link>`, no `src=`, no absolute `http(s)://` URL, and inline `<style>` only, so the CSP above is satisfiable and no third party ever receives a request carrying the page URL. They include `<meta name="referrer" content="no-referrer">` (the exact string is asserted) and `<meta name="robots" content="noindex, nofollow">`. The upload `<form method="post" enctype="multipart/form-data">` has **no `action` attribute**: it posts to the current URL, so the token is never written into the HTML. The suite asserts the token is absent from the body. The consultant create/revoke responses carry `Cache-Control: no-store` and `Referrer-Policy: no-referrer` (they display a capability URL).

**Access-log redaction:** `app/main.py` installs, at import time, `logging.getLogger("uvicorn.access").addFilter(MagicTokenRedactionFilter())`. The filter rewrites every `str` in `record.args` and a `str` `record.msg` with `redact_magic_tokens`, which is `re.sub(r"(/magic/)[^/?#\s\"]+", r"\1[redacted]", text)`, and always returns `True`. No application logger in this feature may format a token, a digest, a full magic URL, or `request.url`.

### D-P2-5-H. Audit events (PR-056)

`entity_type = "magic_link"`, `entity_id = link.id`, `metadata_json = json.dumps(..., sort_keys=True)`. **Never** the token or the digest.

| action | actor | metadata keys | written |
|---|---|---|---|
| `magic_link.created` | `consultant` | `engagement_id`, `expires_at` (ISO), `item_keys`, `max_size_bytes`, `max_uploads` | `create_link` |
| `magic_link.revoked` | `consultant` | `engagement_id`, `revoked_at` (ISO) | `revoke_link` |
| `magic_link.upload_received` | `client_link:{id}` | `evidence_id`, `item_key`, `magic_link_id`, `sha256`, `size_bytes` | `receive_client_upload` |

**Atomicity:** `receive_client_upload` pre-generates the evidence id (`_new_id()`), `db.add`s the `upload_received` row, and **then** calls `ingest_engagement_upload(..., evidence_id=that_id)`. The orchestrator's single commit persists both, and its rollback on any error discards both. A successful upload therefore writes, in rowid order: `magic_link.upload_received`, `evidence.created`, `evidence_version.created` (actor `client_link:{id}`), then `evidence_version.status_changed` and `evidence.status_changed` (actor `system:scan-placeholder`, per P2-1). Refusals (limits, dedupe, bad item) are logged at `INFO` with the link id and reason, never audited.

## Required approach

### 1. `app/services/evidence.py`: add `ingest_engagement_upload`

```python
def ingest_engagement_upload(db, *, engagement_id: str, filename: str, content: bytes, category: str | None,
                             uploaded_by: str, change_reason: str | None = None, evidence_id: str | None = None,
                             allow_duplicate: bool = False) -> IngestResult
```

It **commits**. Order: engagement exists (`db.get(Engagement, …)`, else `EvidenceNotFound("Engagement not found")`) → `receive_evidence(assessment_id=None, actor=uploaded_by, …)` → `release_from_quarantine` → if released, extract (blank → `EvidenceValidationError` with P2-1's exact extraction message, full rollback) → commit. If not released, commit (the rejected receipt is kept) and return `released=False`. On any exception: `db.rollback()`, unlink blobs written in this call, and re-raise. This is exactly `ingest_upload`'s contract minus the Assessment lookup and status bump. You may factor the shared body into a private helper as long as `tests/test_evidence_service.py` stays green **unmodified**.

### 2. `app/services/magic_links.py`: exact API

```python
import secrets  # called as secrets.token_urlsafe
TOKEN_BYTES = 16
TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{22}$")
UPLOADS_PER_HOUR = 10
MAX_FILE_BYTES = 25 * 1024 * 1024
MULTIPART_OVERHEAD_BYTES = 64 * 1024
MAX_ITEMS = 20; MAX_ITEM_TITLE_CHARS = 200
EXPIRES_DAYS_RANGE = (1, 30); MAX_UPLOADS_RANGE = (1, 100); MAX_TOTAL_MB_RANGE = (1, 500)
INVALID_LINK_MESSAGE = "This link is invalid or has expired. Contact your consultant for a new link."
FILE_TOO_LARGE_MESSAGE = "Files must be 25 MB or smaller."
UPLOAD_LIMIT_MESSAGE = "This link has reached its upload limit. Contact your consultant."
SECURITY_HEADERS = {...}   # D-P2-5-G

def _now() -> datetime: return datetime.now(timezone.utc)   # module global; tests patch it
def _as_utc(dt) -> datetime                                  # naive → UTC-aware
```

**Errors:** `MagicLinkError(Exception)` (`__init__(self, message)`, `.message`, `status_code = 400`); `MagicLinkNotFound` 404; `MagicLinkValidationError` 422; `MagicLinkConflict` 409; `UploadLimitReached` 403; `PayloadTooLarge` 413; `RateLimited` 429 with extra `retry_after_seconds: int`.

**Functions** (keyword-only after `db`):

- `generate_token() -> str`; `token_digest(token) -> str`; `client_actor(link) -> str` (`f"client_link:{link.id}"`); `scope_items(link) -> list[dict]`.
- `@dataclass(frozen=True) CreatedLink(link: MagicLink, token: str)`.
- `create_link(db, *, engagement_id, item_titles: list[str], expires_in_days: int, max_uploads: int, max_total_mb: int, actor="consultant") -> CreatedLink`. It flushes and does not commit. Validation order and messages:
  1. engagement exists → `MagicLinkNotFound("Engagement not found")`
  2. `engagement.status == "active"` → `MagicLinkConflict("Magic links can only be created for active engagements.")`
  3. titles = stripped non-blank entries; none → `MagicLinkValidationError("Add at least one requested item.")`
  4. > 20 → `"A link can request at most 20 items."`
  5. any > 200 chars → `"Requested item titles must be 200 characters or fewer."`
  6. duplicates by `casefold()` → `"Requested item titles must be unique."`
  7. expiry outside 1–30 → `"Expiry must be between 1 and 30 days."`
  8. uploads outside 1–100 → `"Upload limit must be between 1 and 100."`
  9. total outside 1–500 → `"Total size limit must be between 1 and 500 MB."`

  Then generate the token, build `scope_json` (D-P2-5-C), set `max_size_bytes = max_total_mb * 1024 * 1024` and `expires_at = _now() + timedelta(days=expires_in_days)`, add the link and its `magic_link.created` audit row, and flush.
- `revoke_link(db, *, engagement_id, link_id, actor="consultant") -> MagicLink`: link missing **or** `link.engagement_id != engagement_id` → `MagicLinkNotFound("Magic link not found")`; already revoked → `MagicLinkConflict("Magic link is already revoked.")`; otherwise `revoked_at = _now()`, add the audit row, and flush. Revoking an expired link is allowed.
- `link_status(link, now=None) -> "active" | "expired" | "revoked"` (revoked wins; expired when `_as_utc(expires_at) <= now`).
- `resolve_token(db, token) -> MagicLink | None`: format → digest lookup → exactly one row → `link_status == "active"` → engagement exists and `status == "active"`. Anything else returns `None`. It never raises and never logs the token.
- `@dataclass(frozen=True) LinkUsage(uploads_total, uploads_last_hour, bytes_total, oldest_in_window: datetime | None)`; `link_usage(db, link) -> LinkUsage` (1 statement, D-P2-5-F).
- `check_upload_allowed(db, link) -> LinkUsage`: hourly (`RateLimited`), then count (`UploadLimitReached`).
- `receive_client_upload(db, *, link, item_key, filename, content) -> IngestResult`, which **commits via the orchestrator**. Order:
  1. `item_key` in scope → `MagicLinkValidationError("Choose one of the requested items.")`
  2. `check_upload_allowed`
  3. `len(content) > MAX_FILE_BYTES` → `PayloadTooLarge(FILE_TOO_LARGE_MESSAGE)`
  4. link total → `PayloadTooLarge("This upload would exceed the total size limit for this link.")`
  5. per-link dedupe (D-P2-5-E) → `MagicLinkConflict(...)`
  6. pre-generate the evidence id and add the `upload_received` audit row
  7. `ingest_engagement_upload(engagement_id=link.engagement_id, filename=filename, content=content, category=None, uploaded_by=client_actor(link), change_reason=f"Client upload via magic link for requested item: {title}", evidence_id=…, allow_duplicate=True)`

  It must not write blobs, hash for storage, release, or extract itself. The suite greps `magic_links.py` and `magic.py` for `_write_blob`, `.write_bytes(`, `open(`, `receive_evidence(`, `release_from_quarantine(`, and `extract_text(`, and requires `ingest_engagement_upload`.
- `magic_link_rows(db, engagement_id) -> list[dict]`, newest first: `id`, `id_prefix` (`id[:8]`), `status`, `created_at`, `expires_at`, `items` (titles), `uploads_used`, `max_uploads`, `bytes_used`, `max_size_bytes`. **Never** `token_digest`.
- `client_upload_rows(db, engagement_id) -> list[dict]`, newest first, Evidence with `engagement_id` and `uploaded_by LIKE 'client_link:%'`: `id`, `filename` (v1 `original_filename`), `status`, `uploaded_at`, `magic_link_id` (suffix of `uploaded_by`), `change_reason` (v1).
- `redact_magic_tokens(text) -> str` and `class MagicTokenRedactionFilter(logging.Filter)` (D-P2-5-G).

### 3. `app/routers/magic.py`: routes

`router = APIRouter(include_in_schema=False)`. The client routes are unauthenticated capability endpoints and are kept out of the OpenAPI schema. Register it in `app/main.py` **before** `web.router`. Templates come from `app.routers.web.templates`.

| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/magic/{token}` | 200 `magic/upload.html` | 404 `magic/invalid.html` (D-P2-5-B) |
| POST | `/magic/{token}` | 200 `magic/upload.html` with the success banner `File received: {filename}` | as below |
| POST | `/engagements/{engagement_id}/magic-links` | 200 `partials/magic_links.html` with `new_link_url` | 404 unknown engagement; any `MagicLinkError` → the same partial with `error=message` at **200** (HTMX pattern, like P2-1's `upload_status`) |
| POST | `/engagements/{engagement_id}/magic-links/{link_id}/revoke` | 200 `partials/magic_links.html` | `MagicLinkNotFound` → **404**; `MagicLinkConflict` → the partial with `error` at 200 |

**`POST /magic/{token}`: exact order.** It takes `request: Request` and parses the form itself, so the guards run before the body is read. Every error renders `magic/upload.html` with `error=message` at the listed status, with the security headers:

1. `resolve_token` → `None` → the D-P2-5-B 404.
2. `Content-Length` missing or non-numeric → 411. `> MAX_FILE_BYTES + MULTIPART_OVERHEAD_BYTES` → 413 `FILE_TOO_LARGE_MESSAGE`. (Read the constants at call time.)
3. `check_upload_allowed` → 429 (+ `Retry-After`) / 403.
4. `form = await request.form()`. `item_key` not in scope → 422 `Choose one of the requested items.`
5. `file` absent, not an `UploadFile`, or with an empty filename → 422 `Choose a file to upload.` (A zero-byte file **with** a filename goes on to P2-1, which returns 422 `The uploaded file is empty.`)
6. `content = await upload.read(MAX_FILE_BYTES + 1)`, then `receive_client_upload(...)`. A `MagicLinkError` or `EvidenceError` → `db.rollback()` and render with `exc.status_code` / `exc.message` (so unsupported type → 400, empty or extraction failure → 422).
7. `released is False` → 422 `SCAN_REJECTED_MESSAGE` (the receipt stays committed and counts toward the quota).
8. Success → 200 with `File received: {filename}` (autoescaped).

**Consultant create form fields:** `items` (textarea; `splitlines()`, the service strips and drops blanks), `expires_in_days` (default 7), `max_uploads` (default 20), `max_total_mb` (default 100). `new_link_url = str(request.base_url).rstrip("/") + "/magic/" + token`. Both consultant responses set `Cache-Control: no-store` and `Referrer-Policy: no-referrer`.

### 4. `app/routers/web.py` `engagement_detail`

Add the context keys `engagement_id`, `magic_links = magic_link_rows(db, engagement_id)`, and `client_uploads = client_upload_rows(db, engagement_id)`. `pages/engagement_detail.html` includes `partials/magic_links.html` as a new section after Assessments.

### 5. Templates

- `magic/upload.html` (**new, standalone**, D-P2-5-G). Title `{{ firm_name }} · Evidence upload`. It has the success/error banners and a list of item titles. If uploads remain: `"{remaining} of {max_uploads} uploads remaining"` (exact phrase), the expiry `Link expires {{ expires_at }} UTC`, and the form (a `<select name="item_key">` with `<option value="item-n">title</option>`, `<input type="file" name="file" required>`, a submit button). If none remain: the text `This link has reached its upload limit.` and **no** form or file input. It closes with a "Files received through this link" list: filename and `Received` / `Rejected` (the latter only for `status == "rejected"`). Inline `<style>` only, and legible without any external CSS.
- `magic/invalid.html` (**new, standalone**): same `<head>` meta, and the body is `INVALID_LINK_MESSAGE` only. Its context is the fixed `firm_name` and message, and **nothing request-dependent** (so the body is byte-identical).
- `partials/magic_links.html` (**new**, `id="magic-links"`, HTMX target). It holds:
  - The create form: `hx-post="/engagements/{{ engagement_id }}/magic-links"`, `hx-target="#magic-links"`, `hx-swap="outerHTML"`, a textarea `items` labelled "Requested items (one per line)", and the three numeric fields with their defaults and ranges.
  - When `new_link_url` is set, a highlighted box with the URL in a read-only input and the text "Copy this link now. It will not be shown again."
  - The error banner.
  - A links table: `id_prefix`, status badge (`Active`/`Expired`/`Revoked`), item titles, `"{uploads_used} of {max_uploads} uploads"` (exact phrase), expiry, and a Revoke button (`hx-post=".../revoke"`, `hx-confirm="Revoke this link? The client will no longer be able to upload."`) for active links only.
  - A "Client uploads" table: filename linked to `/evidence/{{ id }}`, status badge via `components/evidence_status_badge.html`, received at, and change reason, with an empty state.
  - `dark:` variants throughout.

## Key files

| File | Why it matters |
|---|---|
| `app/services/magic_links.py` (new) | The security contract (step 2). |
| `app/routers/magic.py` (new) | Step 3; the only unauthenticated write path in the product. |
| `app/services/evidence.py` | `ingest_engagement_upload` (step 1). No other change. |
| `app/main.py` | Router registration and the access-log filter. |
| `app/routers/web.py`, `pages/engagement_detail.html` | Consultant panel context. |
| `app/templates/magic/upload.html`, `magic/invalid.html`, `partials/magic_links.html` (new) | Step 5. |
| `app/models/magic_link.py` | Used as-is. **No column or index changes.** |
| `tests/test_magic_links.py` | The contract. No existing test changes are expected. |

## Non-goals

- **No Alembic revision, no model change**, including the `token_digest` unique index (handed forward, D-P2-5-A).
- No `EvidenceRequest`/`EvidenceRequestItem` model, no request↔requirement mapping, no PR-023 dedup across links, no reuse suggestions (PR-025). The item titles are free text.
- No automatic `EvidenceUse` creation from a client upload, and no Assessment status change. Mapping stays consultant-driven via the P2-1 JSON API (no new mapping UI).
- No client-side versioning, deletion, download, or preview. A client can't read any file content, including their own.
- No email or other sending of links. The consultant copies the URL.
- No per-IP limiting, CAPTCHA, or in-memory rate state (D-P2-5-B/F).
- No JSON API for magic links, and no client routes in the OpenAPI schema.
- No change to P2-1's dedupe or messages, `scan_blob`, or `base.html`.
- No fix to the pre-existing `CORSMiddleware(allow_origins=["*"], allow_credentials=True)` (see Open questions).

## Test scenarios

All in `tests/test_magic_links.py` (already written). The numbers match the test docstrings.

1. **Token.** `secrets.token_urlsafe(16)` is called once per token. 500 tokens are unique and all 22 chars `[A-Za-z0-9_-]`, and the digest is SHA-256 hex of the ASCII token.
2. **Digest-only storage.** The stored row has the digest, the exact `scope_json`, the limits, and `expires_at ≈ now + days`. The audit row `magic_link.created` has the exact key set. A full SQLite `iterdump` contains neither the token nor its first 12 characters.
3. **Create validation.** Every message and status in step 2's order, with nothing written. There's also a missing engagement → 404 and an archived engagement → 409.
4. **Consultant route.** The URL is shown once, with `no-store` and `no-referrer` headers. The engagement page lists `id_prefix`, `Active`, and `0 of 20 uploads`, without the token. A validation error returns the partial at 200, and an unknown engagement returns 404.
5. **`resolve_token`.** Six malformed shapes resolve to `None` with **0** SQL statements. Unknown, expired (via `_now`), inactive-engagement, and revoked tokens all resolve to `None`.
6. **Non-enumerability.** Malformed, unknown, expired, revoked, and inactive-engagement tokens on GET and POST all get 404, one byte-identical body, the message, and all six headers. No Evidence is written.
7. **Scoped page.** The item titles, `5 of 5 uploads remaining`, the file input, and the referrer meta tag are present. The client/engagement/assessment names and ids, a consultant evidence filename, a conclusion sentinel, another link's item, and the token are absent. There's no `<script`, `<link`, `src=`, `http://`/`https://`, or ` action=`.
8. **Upload.** 200 with `File received: …` and `19 of 20 uploads remaining`. The Evidence is engagement-level (`assessment_id None`) with `uploaded_by client_link:{id}`, active, with the hash and the exact v1 `change_reason`. The exact audit sequence and actors, and the exact `upload_received` metadata, are checked. The upload is invisible to the Assessment until `map_evidence`, the Assessment status is unchanged, the client page lists the file as Received, and the engagement page links `/evidence/{id}` with `1 of 20 uploads`.
9. **Item restriction.** An unknown, empty, or path-like `item_key` → 422 with the headers. A missing file → 422. Nothing is written.
10. **Hourly limit.** With `UPLOADS_PER_HOUR=2`, the third upload → 429, `Retry-After` is in 1–3600, and nothing is written. After ageing the rows 61 minutes, it's accepted again.
11. **Count limit.** A scan-rejected receipt counts toward it. The third upload → 403 with the exact message. The page then shows the limit text and no file input.
12. **Size.** The `Content-Length` guard returns 413 on a non-multipart oversized body, which proves it runs before parsing. The per-file cap is exact (1001 bytes refused, 1000 accepted), and the link total produces 413 with the exact message.
13. **Dedupe.** The same bytes through the same link → 409. Through another link → 200, and link A's filename never appears in link B's responses.
14. **Pass-through.** Unsupported → 400 and empty → 422 with P2-1's messages, and blank extraction → 422. Nothing is written: no rows, no audit row, no blob. `ingest_engagement_upload` is also tested directly, including `Engagement not found`.
15. **Revocation.** The wrong engagement gets 404. Revoking returns 200 with `Revoked`, sets `revoked_at`, and writes the audit row (`engagement_id`, `revoked_at`). The token then gets 404 on GET and POST. A second revoke shows `Magic link is already revoked.` The service errors are checked too.
16. **Secrecy.** The filter is installed on `uvicorn.access` and redacts a real access-log record. `redact_magic_tokens` works. No non-httpx log record, no audit metadata, and nothing in the DB dump contains the token (or the digest, in the audit metadata).
17. **Pipeline reuse.** The grep guard described in step 2.

## Done criteria

- `tests/test_magic_links.py` passes unmodified. `pytest -q` passes in full (338 = 309 + 29), with **no existing test modified**. If P2-2 has merged first, the total is 364 (309 + 26 + 29), and the P2-2 head `3d8b6f0a2c51` is unchanged by this task.
- `alembic heads` shows one head, unchanged by this task.
- `grep -rn "relationship(" app/models/` is empty. `grep -rn "token_urlsafe\|token_digest" app/` shows only `magic_links.py` (and the model).
- **Security smoke** (per the project smoke-test rule; record the outputs):
  1. Run the app, create a link on a real engagement, and open the URL in a private window: only the item titles are visible.
  2. `curl -sI` the URL and paste the six headers.
  3. Upload a PDF, then confirm `evidence.uploaded_by = client_link:<link id>` and `assessment_id IS NULL` via `sqlite3`.
  4. Revoke the link, then `curl -s` the old URL and a random 22-char token, and `diff` the two bodies (they must be identical).
  5. `grep -c "<token>"` on the uvicorn console log and on `sqlite3 <db> .dump` → both 0.
  6. Exceed the hourly limit with a loop of uploads, and paste the 429 and its `Retry-After`.

## Rollback

- **Code:** `git revert`. There's no schema change. Existing `magic_links` rows become inert, since nothing reads them. Client-uploaded Evidence stays as ordinary engagement-level Evidence (visible on `/evidence/{id}`, mapped via the P2-1 API).
- **Emergency kill switch without a deploy:** `UPDATE magic_links SET revoked_at = CURRENT_TIMESTAMP WHERE revoked_at IS NULL;` invalidates every outstanding link immediately. D-P2-5-B guarantees clients see only the generic 404.
- **Known residual risks** (single-user MVP, named so they aren't forgotten): the limit checks race (D-P2-5-F); there's no `token_digest` uniqueness constraint yet (D-P2-5-A); the malware scan is still P2-1's auto-pass placeholder, and **this task makes it reachable by an unauthenticated party**, which raises the priority of PRD open question 5 (a real scanner) before any external pilot.

## Open questions (deliberately flagged, not resolved here)

1. **Real malware scanning before external use.** Magic links are the first path where untrusted parties submit files. The placeholder is acceptable for synthetic demos (P4-2), **not** for a real client pilot. Owner: the PRD open question 5 decision.
2. **`CORSMiddleware(allow_origins=["*"], allow_credentials=True)`** in `app/main.py` is pre-existing and affects every internal route, not magic links specifically (magic-link POSTs are simple form posts that CORS doesn't gate). It should be tightened when auth lands. It's out of scope here.
3. **EvidenceRequest model / PR-023 dedup.** `scope_json` items are free-text titles. When request deduplication lands, `scope_json` should reference request-item ids. `"version": 1` in the blob exists so that migration can tell the shapes apart.
4. **`uq_magic_links_token_digest`**: add it in the first migration after P2-2 and P2-5 both merge.

## Report back

Append a `## Results` section to this file containing:
- The route table as implemented (method, path, success code, template), and every error status actually returned by `POST /magic/{token}`, flagging any deviation from step 3.
- `SECURITY_HEADERS`, `TOKEN_BYTES`, the limit constants, and the `scope_json` shape, copied from the code.
- `pytest -q` output and the pass count of `tests/test_magic_links.py`, and confirmation that no existing test file was modified.
- The six security-smoke outputs listed in Done criteria.
- Anything this document got wrong about the current code.
