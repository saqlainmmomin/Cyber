# P2-2: Citation model — structured, validated citations to immutable Evidence versions

**Plan:** `docs/plans/2026-09-21-002-revised-implementation-plan.md`, Phase 2, task P2-2; decision **D2** (`tasks/2026-09-21-adversarial-review.md`); PRD PR-021, PR-041, PR-050; P2-1 handoff step 8 (which deferred the desk-review → Evidence link to this task).
**Owner:** Codex, from this Claude spec (per `tasks/agent-ownership.md`). Every schema, message, and algorithm is pinned below. If something here contradicts the code, stop and say so in `## Results`. Do not resolve it yourself.
**Depends on:** P2-1 (Evidence service, alembic head `7a3f1e2b9c80`), which is **merged** (PR #24).
**Blocks:** P2-3 (analysis writes `ConclusionRevision.citations_json` through this module), P2-4 (approval card shows resolved citations), P2-6 (workpaper walks Finding → revision → citation → EvidenceVersion).
**Parallel lane:** P2-5 (magic links) runs concurrently. **P2-2 owns the only Alembic revision in Phase 2's parallel lanes.** P2-5 adds no revision, so the two lanes can't fork the head.
**Failing contract suite (already written, run it first):** `tests/test_citations.py` has 26 cases, all red at `b19aa64` for the intended reasons only: 23 fail on `ModuleNotFoundError: No module named 'app.services.citations'`, 2 fail on the missing head revision `3d8b6f0a2c51` (`assert '7a3f1e2b9c80' == '3d8b6f0a2c51'`), and 1 grep guard finds the still-present `Citation` model (`app/models/citation.py:10:class Citation(Base):`). The suite was validated against a throwaway prototype of this spec, which turned all 26 green before it was discarded, so the assertions are satisfiable as written. Turn it green **without editing its assertions**.

## Goal

Give the product exactly one citation representation, one way to produce it from pipeline output, and one way to validate and resolve it:

- a citation is a JSON object `{evidence_version_id, location_type, location_ref, excerpt}` pointing at one **immutable** `EvidenceVersion`;
- the location is **machine-verifiable**: a character span into that version's `extracted_text`. When no quote exists, it is an explicit whole-item reference, labelled as one (PR-021);
- citations are stored as JSON arrays, on `conclusion_revisions.citations_json` (the plan's D2 target, written by P2-3) and on a new `desk_review_findings.citations_json` (the desk-review producer that exists today);
- the unused standalone `citations` table is dropped.

## Current state

Grounded against `b19aa64` on `main`. Re-locate everything by symbol name.

- **`app/models/citation.py`, `Citation`** (P1-2): `citations` table (`id`, `evidence_version_id` FK → `evidence_versions.id`, `location_type`, `location_ref`, `excerpt`, `created_at`, index `ix_citations_evidence_version_id`). Exported from `app/models/__init__.py`. **Zero application code reads or writes it** (`grep -rn "Citation" app scripts --include='*.py'` finds only the model, the `__init__` export, and a comment in `claude_analyzer.py`). `scripts/migrate_legacy.py` only mentions it in a docstring as "never touched". The P1-2 revision `5c7c75960f43` creates it.
- **`app/models/conclusion.py`, `ConclusionRevision.citations_json`**: `Text`, nullable. Its only writer is `scripts/migrate_legacy.py`, which writes `None` on the `proposed`/`approved` revisions it backfills from legacy `GapItem`s. **No code in `app/` creates `Conclusion` or `ConclusionRevision` rows yet.** P2-3 does.
- **Desk review** (`app/services/desk_review.py`): `run_desk_review` → `_call_claude_desk_review` → `_persist_findings(db, assessment_id, result, doc_id_by_filename)`. The model returns `evidence_map: {req_id: [{"document", "quote", "location"}]}`, `absence_findings: [{"requirement_id", "description", "severity"}]` and `signal_flags: [{"document", "requirement_ids", "description", "severity", "source_quote", "location"}]`. Each becomes a `DeskReviewFinding`. `document_id` is FK → `assessment_documents.id`, so since P2-1 it is `None` for Evidence uploaded after P2-1. P2-1 step 8 left that gap for this task.
- **`app/routers/desk_review.py` `get_desk_review`** serialises evidence and signal findings with `requirement_id`, `content`, `source_quote`, `source_location`, `document_id` (signals add `severity`). Absences serialise `requirement_id`, `content`, `severity`.
- **Quote grounding already exists**: `app/services/claude_analyzer.py` `_ground_evidence_quotes(evidence, documents)` drops Call-1 quotes whose normalized form is not a substring of the normalized concatenated document text. Normalization: de-hyphenate `-\s*\n\s*`, map ‘’“” to straight quotes, collapse whitespace with `" ".join(text.split())`, then `lower()`. It works on concatenated text, so it cannot say **which** document or **where**. Call 2's per-requirement `evidence_quote` (`app/schemas/llm_output.py`) is also a verbatim quote.
- **Extracted text has no page markers.** `document_processor._extract_pdf` joins pages with `"\n\n"`, and DOCX/image extraction produces plain text. A "page" location cannot be derived today (see Non-goals).
- **Evidence membership** (D-P2-1-A) is implemented inline in both `analysis_documents()` and `evidence_panel_rows()` in `app/services/evidence.py`. `analysis_documents()` returns `{"id", "filename", "category", "text", "legacy_document_id", "source"}`. It carries **no version id**, and its exact key set is asserted by the P2-1 suite, so don't add a key.
- **Baseline:** `pytest -q` → 309 passed (plus the 26 red cases of this suite).

## Decisions (made here so they are not relitigated)

### D-P2-2-A. The JSON column is canonical. The standalone `citations` table is dropped in this task.

**Decision:** Citations live only as JSON arrays in `citations_json` columns: `conclusion_revisions.citations_json` (existing) and `desk_review_findings.citations_json` (new, step 2). Revision `3d8b6f0a2c51` drops the `citations` table, and this task deletes `app/models/citation.py` and its export.

**Why the table exists at all:** it's schema drift. The plan's Target Schema lists `citations` as a table *and* `conclusion_revisions.citations_json` with the annotation `← D2: JSON array, not relational CitationClaim table`. D2 ("JSON for claims/citations/action-history… Normalize later if query needs emerge") was decided after the table list was drafted, and P1-2 transcribed both. The plan's own P2-2 bullet says the JSON column is the store.

**Why JSON, not the table (with `citations_json` as a cache):**
1. A citation belongs to one immutable judgment record (a `ConclusionRevision`, or a desk-review finding). It is never edited, shared, or queried independently of that record. A child table with no parent FK (the P1-2 `citations` table has none) can't even say which revision it belongs to. Making it canonical would need a new FK column, and a join on every revision read, for no query we have.
2. Two representations of one fact is exactly the trap the ownership contract says Claude must close. Every later consumer (P2-4, P2-6, P3-2 snapshots, P3-3 PDF) would have to know which one is authoritative.
3. The name `Citation` would collide with the concept this module defines, and send P2-6's implementer to a dead table.

**Why drop it now, not later:** it has zero rows and zero readers, so this is the cheapest moment. P2-2 already needs a revision (step 2), and a later drop would cost another round of head-pin churn in the tests.

**Known cost, accepted and handed forward:** JSON references to `evidence_version_id` are not FK-enforced. The mitigations are: (a) P2-1 has no code path that deletes a version; (b) `resolve_citations` reports a dangling id as `resolved: False` instead of crashing; (c) **P4-4 (purge) must scan `citations_json` columns for a version id before purging it**, and this is recorded under Rollback/Report back for P4-4's designer. If a real query need appears ("every conclusion citing version X"), normalize then, per D2.

### D-P2-2-B. Location = a verified character span into the version's `extracted_text`, or an explicit whole-item reference

`LOCATION_TYPES = ("text_span", "whole_item")`. The set is closed. Later tasks extend it together with a ref grammar for each new type (for example, P4-1 AWS snapshots: `config_item`/`finding_id`).

| `location_type` | `location_ref` | `excerpt` | When |
|---|---|---|---|
| `text_span` | `chars:{start}-{end}`: 0-based, end-exclusive offsets into `EvidenceVersion.extracted_text`; decimal with no leading zeros; `start < end ≤ len(text)` | **exactly** `extracted_text[start:end]`, meaning the document's own words, not the model's paraphrase; ≤ `MAX_EXCERPT_CHARS = 2000` | A quote was located in the version's text |
| `whole_item` | literal `"whole"` | `""` | The pipeline attributed a finding to a document **without** a quote. This satisfies PR-021's "identified as such" |

**Why offsets, not the plan's `page | section | table_cell`:** page boundaries aren't preserved by extraction (see Current state), and a model-reported "Section 4.2" is unverifiable text. A span into immutable `extracted_text` (written once at release, never re-extracted, per D-P2-1-E) is deterministic, re-checkable by `validate_citations`, and lets P2-6 highlight the passage. The model's `location` string stays where it already lives (`DeskReviewFinding.source_location`), as a display hint only.

**An ungrounded quote gets no citation.** It is never downgraded to `whole_item`, because that would launder a fabricated quote into apparent support (PR-041: "an ungrounded quote cannot be treated as supporting Evidence").

**Only `active` versions of `active` Evidence may be cited at write time.** A citation must point at what analysis actually saw: quarantined or rejected bytes never reach analysis, and invalidated or archived Evidence is excluded from it. At **read** time a citation to a since-superseded version stays valid and is shown as not current (`is_current: False`). It is history, not an error.

### D-P2-2-C. Matching normalization is the analyzer's grounding normalization, made offset-preserving

`locate_excerpt` must accept exactly the quotes `_ground_evidence_quotes` accepts, so nothing the pipeline treats as grounded is uncitable (scenario 2 checks this). Do **not** modify `_ground_evidence_quotes`. Re-implement the same rules with an offset map (step 3). One deliberate deviation: `lower()` is applied per character, which differs from whole-string `lower()` only for the Greek final-sigma rule. That is irrelevant to this corpus and is noted in the code comment.

### D-P2-2-D. `NULL` vs `"[]"`

- `citations_json IS NULL` means **not captured**: legacy rows from `migrate_legacy.py`, and pre-P2-2 desk-review rows.
- `"[]"` means **captured, no source-grounded citation**: an absence finding, an ungrounded quote, or a quote only in an un-migrated legacy document.

P2-4's approval guard (PR-043 "supporting Evidence **or explicit Evidence absence**") depends on this distinction. Every writer in this task writes a JSON array, never `NULL`.

### D-P2-2-E. What P2-2 wires, and what it leaves to P2-3

P2-2 wires the **desk-review producer** (it exists today, and P2-1 promised it) and provides `attach_citations(db, revision=..., citations=...)` for `ConclusionRevision`. P2-2 does **not** create `Conclusion`/`ConclusionRevision` rows or touch `app/routers/analysis.py`/`claude_analyzer.py`. That is P2-3, which will call `citable_sources` → `cite_quotes(sources, [evidence_quote, *call1_quotes])` → `attach_citations`. The plan's P2-2 test ("analysis run produces conclusion revisions with citation JSON") is therefore covered here at the `attach_citations` level (scenario 8), and end to end by P2-3's suite.

## Required approach

### 1. Models

- Delete `app/models/citation.py`. Remove `from app.models.citation import Citation` and `"Citation"` from `app/models/__init__.py`.
- `app/models/desk_review.py` `DeskReviewFinding`: add, directly after `source_location`:
  ```python
  citations_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array; see app.services.citations
  ```
- No `relationship()` (house rule; `grep -rn "relationship(" app/models/` must stay empty).

### 2. Alembic revision: pinned id `3d8b6f0a2c51`

File `alembic/versions/3d8b6f0a2c51_p2_2_citations_json.py`, `revision = "3d8b6f0a2c51"`, `down_revision = "7a3f1e2b9c80"`. Hand-written, with `op.batch_alter_table` for every ALTER.

`upgrade()`:
1. Guard: `SELECT COUNT(*) FROM citations` > 0 → `RuntimeError("Refusing to drop the citations table: it holds N rows. P2-2 moves citations to citations_json columns; migrate or remove those rows first.")`. No code writes it, so this can't fire on a real DB. It exists so a hand-edited DB is never silently truncated.
2. `batch_alter_table("citations")`: `drop_index("ix_citations_evidence_version_id")`. Then `op.drop_table("citations")`.
3. `batch_alter_table("desk_review_findings")`: `add_column(sa.Column("citations_json", sa.Text(), nullable=True))`.

`downgrade()`:
1. Guard: `SELECT COUNT(*) FROM desk_review_findings WHERE citations_json IS NOT NULL` > 0 → `RuntimeError("Refusing to downgrade past P2-2 revision 3d8b6f0a2c51: N desk_review_findings rows hold citations. Downgrading would drop them -- restore a verified backup instead.")`. The suite matches on `Refusing to downgrade past P2-2`.
2. Drop column `desk_review_findings.citations_json`.
3. Recreate `citations` **exactly** as P1-2 created it: same columns, types, nullability, the unnamed FK to `evidence_versions.id`, PK, and index `ix_citations_evidence_version_id` via `batch_op.f(...)`. Copy the block from `5c7c75960f43`. `tests/test_data_integrity.py::TestAlembicRoundTrip` compares a full schema snapshot across `downgrade -1` → `upgrade head`, so any difference fails it.

**Existing tests to update in lockstep.** This is the complete list: the prototype run of this spec produced exactly these 13 failures and no others. Change only what is listed.

| File | Change |
|---|---|
| `tests/test_alembic_baseline_immutable.py` | both probe templates: `down_revision = "7a3f1e2b9c80"` → `"3d8b6f0a2c51"` (otherwise the probe forks a second head) |
| `tests/test_data_integrity.py` | the three `"7a3f1e2b9c80"` head assertions (in `test_fresh_upgrade_downgrade_upgrade_round_trip`, `test_downgrade_refuses_when_data_present`, `test_data_bearing_adopted_db_refuses_then_recovers_to_head`) → `"3d8b6f0a2c51"` |
| `tests/test_startup_invariants.py` | both `assert version == "7a3f1e2b9c80"` → `"3d8b6f0a2c51"` |
| `tests/test_evidence_service.py` | `test_p2_1_revision_is_head_and_adds_columns_and_constraints` and `test_downgrade_past_p2_1_succeeds_when_evidence_tables_are_empty`: replace `get_current_head() == P2_1_REVISION` with `ScriptDirectory.from_config(...).get_revision("3d8b6f0a2c51").down_revision == P2_1_REVISION` (P2-1's revision is no longer head, and its contract is otherwise unchanged). No other edits to that file. |
| `tests/test_migrate_legacy.py` | `PHASE_2_TABLES`: remove `"citations"` |
| `tests/test_target_schema.py` | `NEW_TABLES`: remove `"citations"`; remove the `("citations", "evidence_version_id", "evidence_versions")` parametrize row |

### 3. `app/services/citations.py`: public API, exact

Module docstring states D-P2-2-A…D in one paragraph each. `logger = logging.getLogger(__name__)`.

```python
LOCATION_TYPES = ("text_span", "whole_item")
CITATION_KEYS = ("evidence_version_id", "location_type", "location_ref", "excerpt")
WHOLE_ITEM_REF = "whole"
MAX_EXCERPT_CHARS = 2000
_TEXT_SPAN_REF = re.compile(r"^chars:(0|[1-9]\d*)-(0|[1-9]\d*)$")
_QUOTE_TABLE = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})
_HYPHEN_BREAK = re.compile(r"-\s*\n\s*")

class CitationError(Exception):
    status_code = 422
    def __init__(self, message: str): super().__init__(message); self.message = message

@dataclass(frozen=True)
class CitableSource:
    evidence_id: str
    version_id: str
    filename: str      # the active version's original_filename
    text: str          # the active version's extracted_text or ""
```

**Functions:**

- `normalize_with_offsets(text: str) -> tuple[str, list[int]]`. Pure. Returns the normalized string and, for each normalized character, the index of the raw character it came from. The algorithm is exact:
  1. Mark every character covered by a `_HYPHEN_BREAK.finditer(text)` match as removed.
  2. Walk the raw characters `i, ch`, skipping removed ones. Set `ch = ch.translate(_QUOTE_TABLE)`.
  3. If `ch.isspace()`: when output is non-empty and no space is pending, record `pending = i`, then continue. (Leading whitespace is dropped, and a run collapses to one space mapped to the run's **first** whitespace character.)
  4. Otherwise, if a space is pending, emit `" "` with offset `pending` and clear it. Then emit each character of `ch.lower()` with offset `i`.
  5. Trailing whitespace is never emitted.

  Example: `normalize_with_offsets("  Ab  C’d-\n e ") == ("ab c'de", [2, 3, 4, 6, 7, 8, 12])`.
- `locate_excerpt(text: str, excerpt: str) -> tuple[int, int] | None`. Normalize `excerpt` (discard its offsets). If the result is empty, return `None`. Normalize `text`, then `idx = norm_text.find(norm_excerpt)`. If it's `-1`, return `None`. Otherwise return `(offsets[idx], offsets[idx + len(norm_excerpt) - 1] + 1)`. This is the **first** occurrence.
- `text_span_citation(source: CitableSource, excerpt: str) -> dict | None`. Returns `None` when `locate_excerpt` is `None` or `end - start > MAX_EXCERPT_CHARS`. Otherwise returns `{"evidence_version_id": source.version_id, "location_type": "text_span", "location_ref": f"chars:{start}-{end}", "excerpt": source.text[start:end]}`.
- `whole_item_citation(source: CitableSource) -> dict` returns `{"evidence_version_id": source.version_id, "location_type": "whole_item", "location_ref": "whole", "excerpt": ""}`.
- `citable_sources(db, assessment_id) -> list[CitableSource]`. Covers in-scope (D-P2-1-A), `status == "active"` Evidence that has an `active` version, ordered `(Evidence.created_at, Evidence.id)`. **Add to `app/services/evidence.py`** a public `active_versions_in_scope(db, assessment_id) -> list[tuple[Evidence, EvidenceVersion]]` that holds the membership query plus the active-version query (2 statements), and make `analysis_documents()` use it for its evidence part, so the membership rule stays in one function. `citable_sources` maps its output. The P2-1 suite must stay green with the lockstep edits above as the only changes.
- `cite_quotes(sources: list[CitableSource], quotes: list[str], *, preferred_filename: str | None = None) -> list[dict]`. Pure. Candidate order is sources whose `filename == preferred_filename` (stable), then the rest in the given order. For each quote in order: skip it if blank. The first non-`None` `text_span_citation` wins. If none, count it as dropped. A citation identical by `(evidence_version_id, location_type, location_ref)` to an earlier one is skipped (not counted as dropped). If `dropped > 0`, log once: `logger.warning("Citation grounding dropped %d ungrounded quote(s)", dropped)`. **Never log quote text** (PRD data minimization: quotes are client content).
- `validate_citations(db, citations, *, assessment_id) -> list[dict]`. The gate for **every** writer that did not build its citations via `cite_quotes`/`whole_item_citation` from `citable_sources` in the same transaction. It returns citations rebuilt with keys in `CITATION_KEYS` order. **Query budget: ≤ 3 statements** (versions by id; their Evidence; `EvidenceUse.evidence_id` rows for this assessment among those evidence ids), independent of count. Checks and exact messages (the first failure raises `CitationError`; `i` is the 0-based index):

  | # | Check | Message |
  |---|---|---|
  | 1 | `citations` is a `list` | `Citations must be a list.` |
  | 2 | every item is a `dict` whose key set equals `CITATION_KEYS` (checked for all items before any DB query) | `Citation {i}: must have exactly the keys evidence_version_id, location_type, location_ref, excerpt.` |
  | 3 | all four values are `str` (all items, before any DB query) | `Citation {i}: all fields must be strings.` |
  | 4 | `location_type in LOCATION_TYPES` | `Citation {i}: unknown location_type '{t}'.` |
  | 5 | version exists | `Citation {i}: evidence version '{id}' not found.` |
  | 6 | `version.status == "active"` **and** `evidence.status == "active"` | `Citation {i}: evidence version '{id}' is not active and cannot be cited.` |
  | 7 | in scope: `evidence.assessment_id == assessment_id` or an `EvidenceUse(evidence_id, assessment_id)` exists | `Citation {i}: evidence version '{id}' is not in scope for this assessment.` |
  | 8 | `whole_item`: `location_ref == "whole"` and `excerpt == ""` | `Citation {i}: whole_item citations must have location_ref 'whole' and an empty excerpt.` |
  | 9 | `text_span`: `len(excerpt) ≤ MAX_EXCERPT_CHARS` | `Citation {i}: excerpt exceeds 2000 characters.` |
  | 10 | `text_span`: ref matches `_TEXT_SPAN_REF` and `start < end ≤ len(version.extracted_text or "")` | `Citation {i}: invalid text_span location_ref '{ref}'.` |
  | 11 | `text_span`: `excerpt == extracted_text[start:end]` exactly | `Citation {i}: excerpt does not match the cited evidence text.` |
  | 12 | not a duplicate of an earlier item by `(evidence_version_id, location_type, location_ref)` | `Citation {i}: duplicate citation.` |

  Checks 4–12 run per item in index order (all of item 0's checks before item 1's).
- `dumps_citations(citations: list[dict]) -> str` returns `json.dumps([{k: c[k] for k in CITATION_KEYS} for c in citations], sort_keys=True)`. `[]` → `"[]"`.
- `loads_citations(raw: str | None) -> list[dict]`. `None` → `[]`. Otherwise `json.loads`. A non-list raises `CitationError("Stored citations are not a JSON array.")`. There is no DB validation here.
- `attach_citations(db, *, revision: ConclusionRevision, citations: list[dict]) -> ConclusionRevision`:
  1. `revision.citations_json is not None` → `CitationError("Citations on a conclusion revision are immutable once set.")`.
  2. `conclusion = db.get(Conclusion, revision.conclusion_id)`. If it's `None` → `CitationError("Conclusion revision is not linked to an existing conclusion.")`.
  3. `validate_citations(..., assessment_id=conclusion.assessment_id)`.
  4. `revision.citations_json = dumps_citations(normalized)`.
  5. `db.flush()` and return the revision.

  There is no commit here: the caller owns the transaction, following the P2-1 rule. On validation failure nothing is written.
- `resolve_citations(db, raw: str | None) -> list[dict]`. For display (P2-4/P2-6). **≤ 2 statements** (versions by id, then their Evidence). Each output is the stored citation plus `resolved: bool`, `evidence_id`, `filename` (the **cited version's** `original_filename`), `version_number`, `version_status`, `evidence_status`, and `is_current` (`version_status == "active" and evidence_status == "active"`). For a missing version, all added fields are `None` and `resolved`/`is_current` are `False`.

### 4. Desk-review producer (`app/services/desk_review.py`)

- `run_desk_review`: pass `sources=citable_sources(db, assessment_id)` to `_persist_findings`. Compute it right before the call (after the LLM returns), and don't change the `documents` dicts sent to the LLM.
- `_persist_findings(db, assessment_id, result, doc_id_by_filename, sources: list[CitableSource] = ())`. The default keeps other call shapes working. It sets `citations_json` on **every** row it creates:
  - **evidence** item and **signal** flag: `quote = item.get("quote", "")` for evidence and `flag.get("source_quote", "")` for signals, and `document = item/flag.get("document", "")`. If `quote.strip()`: `dumps_citations(cite_quotes(sources, [quote], preferred_filename=document))`. Otherwise: the first source with `filename == document` → `dumps_citations([whole_item_citation(src)])`; if there's none → `"[]"`.
  - **absence**: `"[]"`.
  - Everything else about the rows (`document_id`, `content`, `source_quote`, `source_location`, `severity`, and the fact that ungrounded evidence findings are still persisted) is **unchanged**. Changing what gets persisted would change `auto_answer` pre-fill, which is out of scope.
- Producer-built citations are valid by construction (same transaction, from `citable_sources`), so `_persist_findings` doesn't call `validate_citations`. The suite still re-validates every persisted row.

### 5. Desk-review API (`app/routers/desk_review.py` `get_desk_review`)

Add `"citations": loads_citations(f.citations_json)` to each **evidence** and **signal** finding dict. Absence dicts are unchanged (no `citations` key). All existing keys stay, including `document_id`. No HTML template changes. Rendering citations is P2-4/P2-6.

## Key files

| File | Why it matters |
|---|---|
| `app/services/citations.py` (new) | The whole contract (step 3). |
| `app/services/evidence.py` | New `active_versions_in_scope`; `analysis_documents` reuses it. The membership rule stays in one place. |
| `app/models/citation.py` (deleted), `app/models/__init__.py` | D-P2-2-A. |
| `app/models/desk_review.py` | `DeskReviewFinding.citations_json`. |
| `alembic/versions/3d8b6f0a2c51_p2_2_citations_json.py` (new) | Step 2; pinned id; both guards; exact P1-2 recreation on downgrade. |
| `app/services/desk_review.py`, `app/routers/desk_review.py` | Steps 4–5. |
| `app/services/claude_analyzer.py` | `_ground_evidence_quotes`: read-only reference for D-P2-2-C. **Not modified.** |
| `app/models/conclusion.py` | `ConclusionRevision.citations_json`: target of `attach_citations`. Not modified. |
| `tests/test_citations.py` | The contract. Plus the six lockstep test files in step 2. |

## Non-goals

- Do **not** create `Conclusion`/`ConclusionRevision` rows, or touch `app/routers/analysis.py` or `claude_analyzer.py` (**P2-3**).
- Do **not** render citations in any template, or add a citation UI (**P2-4/P2-6**; P3-3 for PDF).
- Do **not** add `page`/`section`/`table_cell`/`config_item`/`finding_id` location types. Page-level citations would need page markers preserved at extraction, which would change `extracted_text` for new versions. That is a separate, deliberate change. **P4-1** adds AWS types together with their ref grammar.
- Do **not** retarget `DeskReviewFinding.document_id` or change which desk-review findings are persisted.
- Do **not** modify `_ground_evidence_quotes` or any prompt.
- Do **not** add a relational citation table, an FK from JSON, or a `relationship()`.
- Do **not** backfill `citations_json` on existing rows. `NULL` = not captured (D-P2-2-D).
- Do **not** add a route. Citations are reachable via the existing desk-review JSON only.

## Test scenarios

All in `tests/test_citations.py` (already written). The numbers match the test docstrings.

1. **Location is exact on raw text.** `locate_excerpt` returns raw offsets across case, whitespace runs, tabs, smart quotes, and line-break hyphenation, and the raw slice is the document's text. Misses, blank excerpts, and empty text → `None`. `normalize_with_offsets` matches the step 3 example exactly.
2. **Parity with analysis grounding.** For 7 (text, quote) pairs, `locate_excerpt(...) is not None` if and only if `_ground_evidence_quotes` keeps the quote.
3. **Constructors and constants.** Exact dict shapes. An excerpt over 2000 chars → `None`, and exactly 2000 is allowed.
4. **`citable_sources` follows D-P2-1-A.** Returns the active v2 (not superseded v1) and mapped-in Evidence. Excludes archived Evidence and legacy `AssessmentDocument` rows. Ordering is `(created_at, id)`.
5. **`cite_quotes`.** Preferred filename first, with fallback to other sources. Blanks are skipped. Dedupe works. Exactly one warning, `Citation grounding dropped 1 ungrounded quote(s)`, and the quote text is never logged.
6. **`validate_citations`.** The happy path returns canonical key order in ≤ 3 statements. Each of the 12 rules produces its exact message and status 422, including rejection of a superseded version and of an invalidated Evidence's active version.
7. **Serialization.** `sort_keys` JSON, `"[]"`, `NULL → []`, and a non-array → the exact error.
8. **`attach_citations`.** A revision gets citation JSON whose every entry resolves to a real `EvidenceVersion`. It is immutable once set. Invalid input writes nothing, and `[]` stores `"[]"`.
9. **`resolve_citations`.** After supersession: `resolved True`, `version_status "superseded"`, `is_current False`. A dangling id → `resolved False` and `None` fields. ≤ 2 statements.
10. **Desk review.** A grounded quote gets a `text_span` citation to the right version with the raw slice as excerpt. A misnamed document still resolves in the other source. A fabricated quote → `"[]"`. A legacy-only quote → `"[]"`, and `document_id` stays the legacy id. Absence → `"[]"`. A signal with no quote → `whole_item` for its document. Every persisted row passes `validate_citations`. The GET JSON carries `citations` on evidence and signal findings only.
11. **Alembic.** The head is `3d8b6f0a2c51` with `down_revision` `7a3f1e2b9c80`, the `citations` table is gone, `desk_review_findings.citations_json` is a nullable TEXT, and the `Citation` model is gone. The downgrade refuses while a finding holds citations. Once cleared, it recreates `citations` with its FK and index, and re-upgrade drops it again.
12. **Standing guard.** No `app.models.citation` import and no `Citation(` constructor in `app/` or `scripts/`.

## Done criteria

- `tests/test_citations.py` passes unmodified. `pytest -q` passes in full, with the lockstep edits of step 2 as the only changes to existing tests (335 = 309 + 26).
- `alembic upgrade head` → `3d8b6f0a2c51`. `alembic downgrade 7a3f1e2b9c80` succeeds on an empty DB and refuses with citations present.
- `grep -rn "relationship(" app/models/` is empty. `grep -rnE "app\.models\.citation|\bCitation\(" app scripts --include='*.py'` is empty.
- Smoke test, per the project rule: on a dev DB copy, upload a PDF to an assessment, run desk review with the LLM seam mocked to return one grounded quote, then `GET /api/assessments/{id}/desk-review` and confirm the evidence finding's `citations[0].excerpt` equals the substring at those offsets of the version's `extracted_text` (check it in a Python shell).

## Rollback

- **Code:** `git revert`. The reverted app ignores `desk_review_findings.citations_json` (it's an unknown column, and SQLAlchemy doesn't select it) and has no `Citation` model. The table is gone, but nothing used it.
- **Schema:** `alembic downgrade 7a3f1e2b9c80` restores the P1-2 `citations` table exactly. It refuses once desk review has written citations. In that case, restore the P1-6 backup (`scripts/restore.py`), or clear `desk_review_findings.citations_json` (it's regenerated on the next desk-review run) and downgrade.
- **Handed forward:** JSON citation references are not FK-protected. **P4-4 must refuse to purge an `EvidenceVersion` referenced by any `conclusion_revisions.citations_json` or `desk_review_findings.citations_json`**, or mark those citations as purged-source. That task's designer must pick one.

## Report back

Append a `## Results` section to this file containing:
- The public API of `app/services/citations.py` as shipped (names and signatures copied from the code), and the `active_versions_in_scope` signature in `evidence.py`.
- The Alembic revision as shipped, and confirmation that the existing-test edits match the step 2 table exactly (list any file you had to touch that is not in it, and why).
- `pytest -q` output and the pass count of `tests/test_citations.py`.
- The smoke-test output: the stored citation, and a Python-shell proof that `extracted_text[start:end] == excerpt`.
- Anything this document got wrong about the current code.

## Results

- Public API shipped by `app/services/citations.py`:
  - `LOCATION_TYPES = ("text_span", "whole_item")`
  - `CITATION_KEYS = ("evidence_version_id", "location_type", "location_ref", "excerpt")`
  - `WHOLE_ITEM_REF = "whole"`
  - `MAX_EXCERPT_CHARS = 2000`
  - `class CitationError(Exception)`
  - `@dataclass(frozen=True) class CitableSource`
  - `normalize_with_offsets(text: str) -> tuple[str, list[int]]`
  - `locate_excerpt(text: str, excerpt: str) -> tuple[int, int] | None`
  - `text_span_citation(source: CitableSource, excerpt: str) -> dict | None`
  - `whole_item_citation(source: CitableSource) -> dict`
  - `citable_sources(db: Session, assessment_id: str) -> list[CitableSource]`
  - `cite_quotes(sources: list[CitableSource], quotes: list[str], *, preferred_filename: str | None = None) -> list[dict]`
  - `validate_citations(db: Session, citations: list[dict], *, assessment_id: str) -> list[dict]`
  - `dumps_citations(citations: list[dict]) -> str`
  - `loads_citations(raw: str | None) -> list[dict]`
  - `attach_citations(db: Session, *, revision: ConclusionRevision, citations: list[dict]) -> ConclusionRevision`
  - `resolve_citations(db: Session, raw: str | None) -> list[dict]`
  - `active_versions_in_scope(db: Session, assessment_id: str) -> list[tuple[Evidence, EvidenceVersion]]` in `app/services/evidence.py`.
- Alembic revision shipped: `3d8b6f0a2c51_p2_2_citations_json.py`, revision `3d8b6f0a2c51`, down revision `7a3f1e2b9c80`. It guards both destructive upgrade and citation-bearing downgrade, drops the standalone `citations` table, adds nullable `desk_review_findings.citations_json`, and recreates the original table/FK/index on downgrade. Existing-test edits match the handoff step 2 table exactly: `tests/test_alembic_baseline_immutable.py`, `tests/test_data_integrity.py`, `tests/test_startup_invariants.py`, `tests/test_evidence_service.py`, `tests/test_migrate_legacy.py`, and `tests/test_target_schema.py`. No other test files were touched.
- Verification:
  - `.venv/bin/pytest -q tests/test_citations.py` → `26 passed, 1 warning in 1.79s`.
  - In-scope regression set (the contract suite plus the six lockstep suites) → `160 passed, 6 warnings in 11.07s`.
  - Required `.venv/bin/pytest -q` → `334 passed, 29 failed, 1 error in 19.30s`. All 29 failures are the parallel P2-5 `tests/test_magic_links.py` contract importing the not-yet-implemented `app.services.magic_links`; the teardown error is the existing session guard detecting another test’s creation of `data/dpdpa.db`. No P2-2 test failed.
- Live isolated-DB ASGI smoke output:
  - `upload_status: 201`
  - `review_status: 200 completed`
  - `stored citation: {"evidence_version_id": "e5c05138-74bb-4fa0-8a58-1f11e819a923", "excerpt": "RETAINED for seven years", "location_ref": "chars:28-52", "location_type": "text_span"}`
  - `offset proof: True`
  - `raw slice: 'RETAINED for seven years'`
- The handoff’s current-state baseline count does not match this worktree’s test inventory: P2-5 contract tests are already present while their implementation is intentionally in the sibling lane, so the full suite cannot reach the handoff’s expected `335` pass count here. The citation-specific current-state assumptions and the six-file lockstep list were otherwise accurate.
