# P6-7a: Consultant requirement card, divergence acknowledgement and review queue `[AR: D3 + closed-set citation]`

This task builds the consultant's working surface on top of P6-4's v2 output (plan Part D D1, PR-014):

- **The requirement card.** Every Conclusion card gains the D1 sections, in order: the AI proposal and a one-line reason, the criteria checklist (✓ / ✗ / ?) with each claim linked to its highlighted span, what the client said vs what the evidence shows, evidence-quality chips, missing evidence, and the framework divergence note.
- **The divergence acknowledgement** (Part C.3). The consultant must acknowledge a divergence note before approving that Conclusion. The acknowledgement is an append-only audit event, like P6-6's report basis.
- **The review queue.** One page sorts every card by deterministic risk, then by flags. It groups UCC-shared requirements so their evidence is read once, and supports keyboard navigation. Every Conclusion is still decided on its own (D3).
- **A read-only span viewer** that shows the cited text of an Evidence version with the span highlighted.
- **v1 fallback.** When no v2 run exists, the card renders from the v1 run's fields.

**Split.** This file is **P6-7a** and is designed in full. **P6-7b**, the one-click "add to RFI" for missing evidence, is deferred (D-P6-7-H). Until then P6-7a lists missing evidence and links to the RFI page.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`: Track 2 P6-7, Part C.3, Part D D1, and Principles 2 (closed-set citation) and 4 (no LLM-invented numbers). The relevant decisions are:

- **D-P6-B** closed-set citation
- **D-P6-C** claims are system suggestions; the consultant confirms each Conclusion
- **D-P6-G** the period is required before approval (the P6-6 gate stays)
- **D-P6-L** fallback criteria and their label
- **D3** individual approval only

PR-014, PR-021, PR-022 and PR-041 are in `docs/product/2026-09-21-cyberassess-product-requirements.md`.

**Owner:** Claude designs (this file + contract tests) → Codex implements → Claude runs an adversarial review (`[AR]`, checkpoints below) → the orchestrator smoke-tests and opens the PR. Per `tasks/agent-ownership.md`, Phase 6 row "P6-6..P6-10 Deliverables".
**Branch / worktree:** `claude/p6-7-requirement-card`, from `origin/main` @ `db3fdc8` plus the kickoff commit `5cf6ea0`. Before running the suite, run `git branch -f main origin/main`: the guards diff `main...HEAD`.
**Depends on:** P6-4 (v2 judge, merged #74), P6-6 (report basis + approval gate, merged #73). **Blocks:** P6-7b (RFI one-click). **Runs in parallel with:** P6-8 (board report v2). The two tracks share no source file (see File overlap).

> **The contract tests are already written. They are the contract.** `tests/test_p6_7_requirement_card.py` (14 tests) was written by the designer before implementation.
>
> **Status on `5cf6ea0` plus the designer's commit:** 13 fail and 1 passes. The one that passes is scenario 14, the file-set guard, which must stay green. The 13 fail only for missing-code reasons:
> - `ModuleNotFoundError` for `app.services.review_queue` / `requirement_card`
> - `AttributeError: 'ConclusionCard' object has no attribute 'requirement'`
> - a 404 for the missing routes
> - `no element with data-…` for the missing card markup
>
> Make all 14 pass **without editing that file**. Do not weaken, skip, `xfail`, re-parametrize or delete any test. If you believe a test is wrong, leave it failing and explain in `## Results`: which assertion, why, and what it should be. Put extra tests in `tests/test_p6_7_extra.py`.
>
> **How the designer checked the file.** It was run against a throwaway reference implementation of this spec. That reference is not in the repo: implement from this spec, not from memory of it.
> - All 14 tests passed.
> - Each of 14 targeted mutations made at least one test fail:
>   1. gate removed from `decide`
>   2. closed-set filter removed
>   3. acknowledgement keyed per cluster instead of per Conclusion
>   4. acknowledgement ignoring the run
>   5. queue risk taken from the LLM's `risk_level`
>   6. flags ignored in the sort
>   7. no UCC grouping
>   8. stale acknowledgement accepted
>   9. period chip ignoring the cut-off
>   10. fallback label dropped
>   11. run envelope mutated on acknowledgement
>   12. group evidence repeated on every card
>   13. acknowledgement note not normalised
>   14. an acknowledgement recorded on another Conclusion counted
> - With the reference and the guard excludes in D-P6-7-M, the full suite result is recorded in `## Designer verification` below.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, name, signature, message constant, audit action, route, form field, data attribute and rendered string below.

> **Answer-key independence (D-P5-9-C).** Never open, grep, glob, list or read:
> - anything under `validation/`
> - `tasks/handoffs/*p5-9*`
> - `docs/plans/2026-09-24-002-*`
> - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
> - `scripts/validation/**`
> - `tests/test_validation_harness.py`
> - any `answer_key.json`
> - `~/cyberassess-runs/**`
>
> Scope every search to explicit paths (`grep -rn ... app/ tests/test_p6_7_*.py`), never a bare repo-root search.

> **Codex cannot write `.git`.** Do not run `git add`, `commit`, `branch` or `stash`. Read-only git is fine, and the guards use it. The orchestrator commits.

## Goal

1. On the Conclusions page, every card shows the D1 sections for its latest applied AI proposal. The sections come from the v2 run envelope when the proposal came from v2, and from the v1 envelope otherwise. A Conclusion with no linked run says so.
2. A v2 card lists only claims that are in that run's verified set and cited for that requirement. Each criterion's claims link to a span viewer that highlights the cited characters.
3. A Conclusion whose v2 record carries a framework divergence cannot be approved or edited-and-approved until the consultant acknowledges that divergence note. The acknowledgement is stored as one append-only audit event per (Conclusion, run, cluster). Run envelopes are never changed.
4. `/assessments/{id}/review-queue` shows every card once:
   - in a deterministic order: open work first, then risk, then flags
   - grouped by UCC cluster, with the group's evidence shown once
   - with j/k keyboard navigation
   - with per-Conclusion decision controls only
5. No LLM call, no migration, no model change, and no change to analysis, grounding, scoring, report or snapshot code. Risk, priority and scores are never taken from an LLM.

## Step 0 (before writing code)

1. The worktree exists with `.venv` symlinked; `main` == `origin/main` == `db3fdc8`.
2. Run `.venv/bin/pytest -q -p no:cacheprovider` and record the counts in `## Results`. With the designer's commit on top of `db3fdc8`, the suite is **1059 passed, 10 skipped, 13 failed**: 1058 existing tests plus scenario 14, and the 13 red contract scenarios.
3. Confirm these facts. **If any is false, stop and report.** Line numbers are from `db3fdc8`.
   1. **v2 envelope** (`app/services/analysis_v2.py:record_framework_run_v2`). `AnalysisRun.claims_json` for a v2 run has:
      - `analysis_pipeline_version: "v2"`
      - `claim_set_id`
      - `verified_claims`: dicts with `claim_id, source_id, evidence_version_id, filename, chunk_id, start, end, quote, statement, kind, requirement_ids, needs_review, derived_from_image, citation`
      - `divergences`: `{cluster_id, compliant: [[fw, rid]], non_compliant: [[fw, rid]], acknowledged: False}`, this framework's only
      - `judgment_metrics`
      - `inputs.applicable_requirements`
      - `claims`: one per requirement, `{requirement_id, cluster_id, outcome, scope_enforced, item, quality, conclusion_id, revision_id, disposition}`

      `item` is the judge record (`app/services/grounding/judge.py:_judged_record` / `_no_input_record` / `_incomplete_record` / `_scope_excluded_record`). It has:
      - `criteria[{criterion_id, kind, statement, result, claim_ids, original_result}]`
      - `contradictions[{claim_id, response_ref, note}]`
      - `conclusion_outcome`, `gap_statement`
      - `missing_evidence[{document_type, what_it_would_show}]`
      - `cited_claim_ids`
      - `response{question_id, answer, answer_source}|None`
      - `unsupported_assertion`, `analysis_incomplete`, `scope_excluded`, `flags`
      - `framework_divergence` (a cluster id or `None`)
      - `criteria_source: "approved"|"fallback"`
      - `risk_level`, `priority`
   2. **v1 envelope** (`app/services/analysis_pipeline.py:record_framework_run`). `claims[]` entries are `{requirement_id, cluster_id, outcome, scope_enforced, item, quality{citation_count, evidence_quote_grounded, unsupported_assertion, needs_review, desk_review_red_flags, desk_review_absence, contradictions: None}, conclusion_id, revision_id, disposition}`. There is no `analysis_pipeline_version` key.
   3. **Linking.** Each applied proposal is a `ConclusionRevision(action="proposed", analysis_run_id=run.id)`, and its id is the envelope entry's `revision_id`. A locked Conclusion gets `proposal_withheld` instead, so the latest `proposed` revision stays the one the Conclusion's content reflects.
   4. **Card path.** `app/services/conclusion_review.py:conclusion_cards` (`:343`) is the only card builder. It is called once per page by the Conclusions page (`web.py:conclusions_page`, imported by name), by the Workpaper (`test_workpaper.py` scenario 10 counts one call), and by `conclusion_card` after decisions. `ConclusionCard` (`:83`) is constructed only at `:477`.
   5. **Decisions.** `decide` (`:204`) is the only writer of human decisions. After the `ALLOWED_ACTIONS` check it runs the P6-6 period gate for `LOCKING_ACTIONS`, then `_latest_proposal`. The routes are in `app/routers/conclusions.py`, where `InvalidDecision` returns 400 `{"detail": message}` with an encoded error toast.
   6. **`tests/test_conclusion_approval.py:629-635` pins the exact set of routes whose path contains `/conclusions`.** That is why the acknowledgement route is `/api/assessments/{id}/divergence-notes/{conclusion_id}/acknowledge` and lives in a new router (D-P6-7-L).
   7. **`tests/test_conclusion_approval.py:641-656` greps these four files** for `approve all|approve selected|select all|approve framework` (case-insensitive): `components/conclusion_card.html`, `pages/conclusions.html`, `routers/conclusions.py`, `services/conclusion_review.py`. It also forbids `delete` and `.commit(` in `conclusion_review.py`.
   8. **Grounding dormancy.** `tests/test_p6_3a_grounding.py::test_scenario_17_package_is_dormant` and `tests/test_p6_3b_v2_flag.py::test_scenario_11_only_desk_review_v2_imports_grounding` fail if any `app/` file other than `desk_review_v2.py` / `analysis_v2.py` contains `services.grounding`. P6-7 imports neither `grounding` nor `analysis_v2` (D-P6-7-J).
   9. **No span viewer exists.** `/evidence/{id}` (`web.py:788`) shows versions and uses, but not text. Citations are `{evidence_version_id, location_type: text_span|whole_item, location_ref: "chars:a-b"|"whole", excerpt}` (`app/services/citations.py`). `resolve_citations` adds `resolved, evidence_id, filename, version_number, is_current`.
   10. **Stage 0 metadata** is stored per source in the claim set (`desk_review_v2.load_claim_set(db, assessment_id).sources[*].metadata.fields[*]{name, iso_date}`), with names including `effective_date` and `document_date`.
   11. **Report basis.** `report_basis.current_basis(db, assessment)` gives `period_recorded` and `evidence_cutoff` (`date`).
   12. **`app/templates/base.html` has `{% block scripts %}`,** so the queue's script needs no base-template change.

## Decisions (made here so they are not relitigated)

### D-P6-7-A: Scope and split

- **P6-7a (this PR):**
  - the card sections
  - the divergence acknowledgement and its approval gate
  - the span viewer
  - the review queue
- **P6-7b (deferred):** the one-click "add to RFI". See D-P6-7-H.
- One PR, because the queue is a sort and a template over the same card view model. Splitting it would ship a card nobody can triage at 228 requirements.

### D-P6-7-B: The card is a field on `ConclusionCard`, built inside `conclusion_cards`

`ConclusionCard` gains one trailing, defaulted field: `requirement: requirement_card.RequirementCard | None = None`. It must be the last field (scenario 13). `conclusion_cards` builds it in the same pass, with no second `conclusion_cards` call and no per-card run query:

1. After `period_blocker = ...`, compute `latest_proposals = {row.id: _latest_proposal(revisions_by_conclusion[row.id]) for row in ordered}`. Then compute `card_context = requirement_card.load_context(db, assessment, latest_proposals.values(), [row.id for row in ordered])`. That is one query for the runs, one parse per envelope, at most one claim-set load, one basis read and one audit-event query.
2. In the loop, use `latest_proposal = latest_proposals[conclusion.id]`. After `citations = resolve_citations(...)`, build `requirement = requirement_card.build_card(card_context, conclusion, latest_proposal, citations)`.
3. `blocker = period_blocker or requirement_card.approval_blocker(requirement) or _approval_blocker(_content(conclusion), latest_proposal)`.
4. Pass `requirement=requirement` to `ConclusionCard(...)`.
5. Import: `from app.services import analysis_pipeline, report_basis, requirement_card`.

`requirement_card` must not import `conclusion_review`, because that would be an import cycle.

### D-P6-7-C: Which run a card shows

The card shows the run of the Conclusion's **latest `proposed` revision**, which is the proposal its content reflects:

- **No run.** If there is no such revision, or it has no `analysis_run_id`, or the run or envelope is missing or unparsable, or no envelope `claims[]` entry has `revision_id == proposal.id`, then `source="none"`.
- **v2.** If `envelope.get("analysis_pipeline_version") == "v2"`, then `source="v2"`, built from that entry's `item`.
- **v1.** Otherwise `source="v1"`, built from that entry's `outcome`, `scope_enforced` and `quality`.

A withheld newer proposal keeps showing through the existing `withheld_proposal` block, unchanged. The card is a pure read. It never re-judges, never calls an LLM, and never writes to an envelope.

### D-P6-7-D: Closed-set rendering (D-P6-B)

- **Verified set.** On a v2 card, `verified = {c["claim_id"]: c for c in envelope["verified_claims"]}`.
- **Cited claims.** `cited_ids` is `[cid for cid in item["cited_claim_ids"] if cid in verified]`, in that order.
- **Criterion links.** Each criterion row's `claim_ids` keeps only ids in `cited_ids`.
- **Contradictions.** Only those whose `claim_id` is in `cited_ids` are kept.
- **Ignored ids.** An id outside the set is silently ignored; the judge already drops and flags them, so this is a defensive filter. Scenario 2 forges one and checks that it never renders.
- **Links.** A claim links to its span only through its own verified `citation`: `href = f"/evidence-versions/{citation['evidence_version_id']}/span?ref={citation['location_ref']}#cited-span"`. When `citation` is `None` (legacy source), `href` is `None` and the id renders unlinked.

### D-P6-7-E: Criteria checklist and the fallback label (D-P6-L)

- **Rows.** `CriterionRow(criterion_id, statement, kind, result, symbol, claim_ids, met_without_claim)`. The symbol comes from `CRITERION_SYMBOLS = {"met": "✓", "not_met": "✗", "no_evidence": "?"}` (unknown result → `"?"`). `met_without_claim = criterion.get("original_result") == "met"`.
- **Labels.** `criteria_label` is `FALLBACK_CRITERIA_LABEL` for `criteria_source == "fallback"`, `APPROVED_CRITERIA_LABEL` for `"approved"`, and `None` otherwise.
- **Proposal line.** `proposed_outcome = item["conclusion_outcome"]`. `reason`:
  - `REASON_SCOPE_EXCLUDED` if `scope_excluded`
  - else `gap_statement` if non-empty
  - else `REASON_COMPLIANT` if the outcome is `compliant`
  - else `None`
- **v1 cards** have no rows and show `V1_SOURCE_LABEL` in the checklist section.

### D-P6-7-F: What the client said vs what the evidence shows

- **Response.** From `item["response"]` when it has an `answer`: `ResponseView(question_id, answer, answer_label=answer.replace("_", " ").capitalize(), source_label=ANSWER_SOURCE_LABELS.get(source, f"Source: {source}"))`, where `source = answer_source or "human"`. Otherwise `NO_RESPONSE_LABEL`.
- **Evidence shows.** The cited claims (statement, quote, file link, kind), or `NO_CLAIMS_LABEL`.
- **Contradictions** are highlighted, one row per contradiction.
- **Unsupported.** `unsupported_assertion` comes from the record (v2) or from `quality.unsupported_assertion` (v1). It renders `UNSUPPORTED_ASSERTION_LABEL`.
- **v1 cards** do not show the two-column comparison, because v1 stores no response or claims. They still show the unsupported label when flagged.

### D-P6-7-G: Evidence-quality chips (PR-022: separate dimensions, never one number)

`QualityChip(key, label, tone)` with tone `ok | warn | neutral`. The vocabulary is fixed in `requirement_card.CHIPS`:

| Key | Label | Tone | When |
|---|---|---|---|
| `currency:current` | Current evidence version | ok | resolved citations exist and all `is_current` |
| `currency:superseded` | Cites a superseded evidence version | warn | any resolved citation not `is_current` |
| `currency:none` | No cited evidence | neutral | no resolved citations |
| `period:not_recorded` | Assessment period not recorded | neutral | v2, ≥1 cited claim, basis not recorded |
| `period:dated` | Evidence dated on or before the cut-off | ok | every cited claim's source has a date ≤ cut-off |
| `period:after_cutoff` | Evidence dated after the cut-off | warn | any cited source dated after the cut-off |
| `period:undated` | Evidence has no document date | warn | none after the cut-off, but a cited source is undated |
| `period:unknown` | Document dates unavailable: desk review changed since this analysis | neutral | no stored claim set, or its `claim_set_id` differs from the envelope's |
| `scope:in_scope` | In recorded scope | ok | `inputs.applicable_requirements` set and requirement in it |
| `scope:excluded` | Outside recorded scope | warn | v2 `item.scope_excluded` / v1 `scope_enforced` |
| `scope:not_recorded` | Scope not recorded | neutral | `applicable_requirements` empty/None |
| `kind:design` / `kind:operating` / `kind:context` | Design evidence / Operating evidence / Context only | neutral | v2, one chip per kind present among cited claims, in that order |
| `support:needs_review` | A cited claim is only partly supported by its quote | warn | v2, any cited claim `needs_review` |
| `support:image` | Includes text read from an image | neutral | v2, any cited claim `derived_from_image` |
| `analysis:incomplete` | Analysis incomplete: not judged after one retry | warn | v2 `item.analysis_incomplete` |
| `grounding:grounded` | Quote found in the evidence | ok | v1 `quality.evidence_quote_grounded is True` |
| `grounding:ungrounded` | Quote not found in the evidence | warn | v1 `quality.evidence_quote_grounded is False` |

- **Order.**
  - v2: currency, period (only with ≥1 cited claim), scope, then kinds, support and image (only with ≥1 cited claim), then incomplete.
  - v1: currency, scope, grounding.
  - `none`: no chips.
- **Document date.** A source's date is the first `iso_date` among its metadata fields named `effective_date`, then `document_date`. The date is compared with `basis.evidence_cutoff` only. A policy effective before the period is still in force during it, so it gets no warning.
- **No confidence number.** The requirement section never renders the word "confidence" or a percentage (scenario 4).

### D-P6-7-H: Missing evidence; the one-click RFI write is deferred to P6-7b

- **Sources.**
  - v2: `item["missing_evidence"]`, rendered as `MissingEvidence(document_type, label, what_it_would_show)`. `label` is the framework's `EvidenceRequest.label` for that `document_type`, or else `document_type.replace("_", " ").capitalize()`.
  - v1: when the outcome is `partially_compliant`, `non_compliant` or `insufficient_evidence`, up to 3 of the pack's `evidence_requests` whose `maps_to` contains the requirement, labelled `V1_MISSING_EVIDENCE_LABEL`.
- **Rendering.** The section renders `MISSING_EVIDENCE_RFI_NOTE` and a link to `/assessments/{id}/rfi`, and nothing on the card posts to an RFI route.
- **Why P6-7b.** The P5-6 RFI is a derived, versioned document. Its items come only from the scope checklist plus approved insufficient-evidence Conclusions, which is already one route from the card to the RFI. It records `source = {schema_version, framework_ids, checklist_sha256, conclusion_versions}`, and that exact key set is pinned by `tests/test_p5_6_rfi_rebuild.py:330, :494`. A consultant-added request needs three things: a new item kind, a new source key (which makes older drafts stale), and a request store. That touches `rfi_requests.py`, the P5-6 pins and `report_snapshots.py`, which is P6-8's file. So P6-7b waits for P6-8 and is designed on its own (Open question 1).

### D-P6-7-I: Divergence acknowledgement: append-only audit event, per Conclusion and run; required before approval

**Storage.** One `AuditEvent` with these fields, and no migration:
- `actor = reviewer_actor(reviewer_name)`
- `action = "conclusion.divergence_acknowledged"` (`DIVERGENCE_ACK_ACTION`)
- `entity_type = "conclusion"`
- `entity_id = conclusion.id`
- `metadata_json = json.dumps({"analysis_run_id", "cluster_id", "compliant": [[fw, rid]], "non_compliant": [[fw, rid]], "note"}, sort_keys=True)`

**Why an audit event, not the envelope or a column.**
- The `AnalysisRun` envelope is the immutable record of what the run produced (D-P2-3-E). Flipping `acknowledged` in it would destroy that, and would record neither who acknowledged nor when.
- A column or table needs a migration. The Alembic head `8b2d5f7e1c34` is pinned in ten test files.
- P6-6's report basis and the release event already use this pattern.
- The envelope keeps `"acknowledged": False` as produced. The card computes the effective state from events (scenario 6 asserts the envelope bytes are unchanged).

**Scope of one acknowledgement.** One acknowledgement covers one `(conclusion_id, analysis_run_id, cluster_id)`.
- **Per Conclusion.** D3 is per Conclusion. Acknowledging on the ISO card must not clear the DPDPA card, which the consultant never read (scenario 6 plants an event on the other Conclusion).
- **Per run.** Re-analysis can produce different claims. A new run with the same divergence needs a new acknowledgement. The old event stays as history (scenario 7).

**Current note.** `build_card` finds the divergence entry whose `cluster_id == item["framework_divergence"]` in this run's `envelope["divergences"]`. It builds `DivergenceNote(cluster_id, analysis_run_id, compliant, non_compliant, sentence, acknowledged, acknowledged_by, acknowledged_at, note)`:
- `sentence = DIVERGENCE_SENTENCE.format(compliant=..., non_compliant=...)`, where each member renders as `f"{framework.name} {requirement_id}"` joined by `", "`. An unknown framework renders as `fw.upper()`.
- `acknowledged_by` is the event's actor without the `consultant:` prefix.
- If several events match, the first by `created_at, rowid` wins.
- v1 and `none` cards have no divergence.

**The gate.** Divergence is not a block on the outcome: requirements can legitimately differ (Part C.3). The block is on approving without having looked.
- `requirement_card.approval_blocker(card)` returns `DIVERGENCE_ACK_REQUIRED_MESSAGE` when `card.divergence` exists and is not acknowledged, otherwise `None`.
- In `decide`, directly after `latest_proposal = _latest_proposal(revisions)`, add:
  ```python
  if action in analysis_pipeline.LOCKING_ACTIONS:
      divergence_blocker = requirement_card.divergence_blocker(db, conclusion, latest_proposal)
      if divergence_blocker:
          raise InvalidDecision(divergence_blocker)
  ```
  This runs after the P6-6 period gate, so an unrecorded period is reported first. No revision is written. Reject and reopen are unaffected.
- On the card, the blocker order is period → divergence → existing blockers (D-P6-7-B).

**`acknowledge_divergence(db, *, assessment_id, conclusion_id, analysis_run_id, cluster_id, note, actor) -> tuple[AuditEvent, bool]`** runs these checks in order:
1. Unknown Conclusion, or one from another assessment → `RequirementCardError(CONCLUSION_NOT_FOUND_MESSAGE, 404)`.
2. The card for its latest `proposed` revision has no divergence → `NO_DIVERGENCE_MESSAGE`, 400.
3. The submitted `analysis_run_id` or `cluster_id` differs from the current note → `DIVERGENCE_STALE_MESSAGE`, 409. This covers a stale form after re-analysis.
4. An event for the same `(conclusion, run, cluster)` exists → return `(existing, False)` and write nothing.
5. Otherwise add the event, `db.flush()`, and return `(event, True)`.

The note is cleaned by collapsing whitespace, stripping, truncating to `ACK_NOTE_MAX_CHARS = 500`, and storing empty as `None`. The note is optional (Open question 2). The caller commits.

### D-P6-7-J: Queue risk is deterministic, and P6-7 imports no grounding code

- **Risk.** `review_queue.deterministic_queue_risk(criticality, outcome)` is a line-for-line mirror of `judge.deterministic_risk`:
  - the base is `criticality` if it is in `("low", "medium", "high", "critical")`, else `"medium"`
  - `compliant` / `not_applicable` → `"low"`
  - `non_compliant` → base
  - otherwise one level below base, floored at `"low"`
- **Parity test.** Scenario 10 asserts equality with the judge for every criticality × outcome.
- **`queue_risk(framework_id, requirement_id, outcome)`** uses the pack control's `criticality` and the Conclusion's **current** `outcome`; an unknown control → `"medium"`. This is the same value v2 stores. For v1 it replaces the LLM-invented `risk_level` in the queue (scenario 10). A consultant's edited `risk_level` stays on the card, where it came from a human. The queue does not use it, and decided cards sort last anyway.
- **Why a mirror instead of an import.** The dormancy guards (fact 8) forbid a third importer of `app.services.grounding`. Adding one to the guards would widen a protected boundary for a pure six-line table. `requirement_card.py`, `review_queue.py` and `requirement_review.py` must not contain `services.grounding`, `llm_client`, `call_llm` or `analysis_v2` (scenario 10).

### D-P6-7-K: The review queue

**`app/services/review_queue.py`:**
```python
QUEUE_RISK_LEVELS = ("low", "medium", "high", "critical")
RISK_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
STATE_RANK = {"pending": 0, "rejected": 1, "approved": 2, "edited": 2}
QUEUE_FLAGS = ("inconsistency", "unsupported_assertion", "divergence")

@dataclass(frozen=True)
class QueueEntry: card: ConclusionCard; risk: str; flags: tuple[str, ...]; key: tuple
@dataclass(frozen=True)
class QueueGroup: group_key: str; cluster_id: str | None; topic: str | None
                  entries: tuple[QueueEntry, ...]; shared_claims: tuple[ClaimView, ...]
                  shared -> bool   # property: len(entries) > 1
def deterministic_queue_risk(criticality: str, outcome: str) -> str
def queue_risk(framework_id: str, requirement_id: str, outcome: str) -> str
def queue_flags(card) -> tuple[str, ...]
def build_queue(cards) -> list[QueueGroup]
def review_queue(db, assessment_id) -> list[QueueGroup]   # exactly one conclusion_review.conclusion_cards call, via the module attribute
```

**Flags** (`queue_flags`; `()` when `card.requirement is None`), returned in `QUEUE_FLAGS` order:
- `inconsistency`: `"model_criteria_inconsistency" in requirement.flags` or any contradiction.
- `unsupported_assertion`: `requirement.unsupported_assertion`.
- `divergence`: a divergence that is **not yet acknowledged**. Acknowledged ones stop pulling the card up.

**Entry key.** `(STATE_RANK[state], RISK_RANK[risk], tuple(flag not in flags for flag in QUEUE_FLAGS), position)`, where `position` is the card's index in `conclusion_cards` order (framework order, then pack order). This puts open work first, then higher risk; among equals, an inconsistency outranks an unsupported assertion, which outranks a divergence.

**Groups.**
- **Shared groups.** Conclusions whose `conclusion.cluster_id` is shared by ≥2 cards in this assessment form one group:
  - `group_key = cluster_id`
  - `topic` from `CONTROL_CLUSTERS`
  - members sorted by key
  - `shared_claims` is the union of the members' `requirement.claims`, de-duplicated by `claim_id` in first-seen order
- **Singles.** Every other card is a group of one with `group_key = f"single-{conclusion.id}"`.
- **Order.** Groups are sorted by their first member's key. A group can therefore pull a low-risk or decided member up next to its riskiest open member. That is the point: read the evidence once.

**Keyboard.** `j` moves to the next item and `k` to the previous one. Each item is focusable (`tabindex="-1"`), and the script scrolls it into view. Keys are ignored while typing in `INPUT`, `TEXTAREA` or `SELECT`, and when a modifier key is held. There is **no keyboard approval and no bulk action**. Each card keeps its own Approve / Edit / Reject forms, which work in the queue because they swap `#conclusion-card-{id}`. A card swapped after a decision re-renders without the group context, so it shows its own evidence list; that is acceptable.

### D-P6-7-L: Routes, a new router, and why `conclusions.py` and `web.py` are untouched

New `app/routers/requirement_review.py`, `router = APIRouter(tags=["requirement-review"])`, with its own `Jinja2Templates` + `configure_templates` (the `conclusions.py` pattern). It is registered in `app/main.py` directly after `conclusions.router`, with `dependencies=_ARCHIVE_GUARD`, plus the import in the `from app.routers import (...)` list.

| Method | Path | Behaviour |
|---|---|---|
| GET | `/assessments/{assessment_id}/review-queue` | 404 `"Assessment not found"`. Renders `pages/review_queue.html` with `assessment, groups, total, open_count` (pending + rejected), `reviewer_name` (from `app.routers.web._latest_reviewer_name`, imported inside the function), `shared_evidence_label` |
| POST | `/api/assessments/{assessment_id}/divergence-notes/{conclusion_id}/acknowledge` | Form `analysis_run_id, cluster_id, note, reviewer_name` (all `Form("")`). `RequirementCardError` → `db.rollback()`, JSON `{"detail": message}` at its status, headers `X-Toast-Message: quote(message)`, `X-Toast-Type: error`. Success → `db.commit()`, 200, renders `components/conclusion_card.html` with `{"assessment", "card": conclusion_review.conclusion_card(...)}`, headers `X-Toast-Message: Framework divergence acknowledged`, `X-Toast-Type: success` (the same for a no-op repeat) |
| GET | `/evidence-versions/{version_id}/span?ref=` | `requirement_card.span_view(db, version_id, ref)`. `RequirementCardError` → `HTTPException(status, message)`. Renders `pages/evidence_span.html` with `{"view": view}` |

`conclusions.py` stays untouched because of fact 6. `web.py` and `base.html` stay untouched because the Conclusions page already renders `components/conclusion_card.html`, and the queue script uses `{% block scripts %}`.

**`span_view(db, version_id, ref) -> SpanView`:**
- **Errors.**
  - Unknown version or evidence → `VERSION_NOT_FOUND_MESSAGE`, 404.
  - A `ref` that is neither `"whole"` nor `chars:<start>-<end>` (regex `^chars:(0|[1-9]\d*)-(0|[1-9]\d*)$`), or has `start >= end`, or `end > len(text)` → `SPAN_INVALID_MESSAGE`, 400.
- **Fields.** `SpanView(evidence_id, version_id, filename, version_number, is_current, location_ref, whole, available, before, span, after, truncated_before, truncated_after)`. `is_current` is `version.status == "active" and evidence.status == "active"`.
- **Text not available.** `extracted_text is None` → `available=False`.
- **Whole.** `ref == "whole"` → `before = text[:3000]`, with `truncated_after` set if the text is longer.
- **Span.** Otherwise the window is `SPAN_CONTEXT_CHARS = 1500` characters either side of the span.
- **Read-only.** No forms and no htmx attributes.

### D-P6-7-M: Stale guards (designer applied the excludes)

Per the stale-guard rule (add `:(exclude)` for exactly the touched files, with a comment naming the PR; never delete or broaden), the designer added P6-7a excludes to:
- `tests/test_p6_3a_grounding.py` `PROTECTED_PATHS`: `app/routers/requirement_review.py`, `app/templates/components/conclusion_card.html`, `app/templates/components/requirement_card_body.html`, `app/templates/pages/review_queue.html`, `app/templates/pages/evidence_span.html`. `conclusions.html` is already excluded by P6-6.
- `tests/test_p6_nist_csf2_alignment.py::test_protected_surface_guard_uses_three_dot_diff`: `app/services/requirement_card.py`, `app/services/review_queue.py`, `app/routers/requirement_review.py`. `conclusion_review.py` is already excluded.
- `tests/test_p6_4_cap_upload_limit.py::_changed` (scenario 9): the ten P6-7a `app/` files.
- `tests/test_p6_4_whats_missing.py::test_scenario_13_...`: the ten P6-7a `app/` files, in both the committed diff and the untracked listing.

If the full suite shows another guard tripping on exactly these files, add the same kind of exclude with a `# P6-7a` comment and list it in `## Results`. Change nothing else in existing tests.

## Card markup contract (`app/templates/components/requirement_card_body.html`)

`components/conclusion_card.html` gets exactly one change. Add `{% include "components/requirement_card_body.html" %}` between the "Current conclusion" `</section>` and the "Evidence summary" `<section>`. Every existing block stays, so D1 items 1 and 7 remain the header chip, "Current conclusion" and the decision controls. The partial renders nothing when `card.requirement` is `None`. Otherwise it renders one `<section data-requirement-card data-requirement-source="{source}" data-criteria-source="{criteria_source or ''}">` containing, in D1 order:

| # | Element | Contract |
|---|---|---|
| — | `none` source | only the text `NO_RUN_LABEL` |
| 1 | proposal | "AI proposal: {Outcome Title}" when `proposed_outcome`; `<p data-proposal-reason>{reason}</p>` when `reason` |
| 2 | criteria | heading "Criteria checklist". v1: `V1_SOURCE_LABEL`. v2: `criteria_label` text, then one `<li data-criterion="{id}" data-criterion-result="{result}">` per row (no nested `<li>`) with the symbol, id, statement and, per claim, `<a data-claim-link="{claim_id}" href="{href}">` (or a `<span data-claim-link>` when `href` is None); `met_without_claim` adds "The model said met without a verified claim; treated as no evidence." |
| 3 | said vs shows (v2) | `<div data-client-said>` (no nested `<div>`): "What the client said", then `answer_label` + `source_label` or `NO_RESPONSE_LABEL`. `<div data-evidence-shows>` (+ `data-evidence-shared` when `group_evidence`): "What the evidence shows", then `SHARED_EVIDENCE_LABEL` if `group_evidence`, else one `<li data-claim="{claim_id}">` per claim (statement, quote, filename linked to `href`, kind), else `NO_CLAIMS_LABEL`. Contradictions: `<li data-contradiction="{claim_id}">Contradiction ({claim_id}): {note}</li>` |
| 3 | unsupported (v1 and v2) | `<p data-unsupported-assertion>` with `UNSUPPORTED_ASSERTION_LABEL` |
| 4 | chips | one `<span data-quality-chip="{key}" data-tone="{tone}">{label}</span>` per chip, attributes in that order |
| 5 | missing evidence | heading "Missing evidence", `missing_evidence_label` if set, one `<li data-missing-evidence="{document_type}">{label}: {what_it_would_show}</li>` each, then `MISSING_EVIDENCE_RFI_NOTE` and `<a href="/assessments/{assessment.id}/rfi">Open the RFI page →</a>`. Whole section omitted when empty |
| 6 | divergence | `<div data-divergence-note="{cluster_id}" data-acknowledged="yes|no">`: "Framework divergence ({cluster_id})", the sentence; if acknowledged, "Acknowledged by {acknowledged_by} at {acknowledged_at}" + `: {note}` when set; else `<form data-divergence-ack-form hx-post="/api/assessments/{assessment.id}/divergence-notes/{conclusion.id}/acknowledge" hx-target="#conclusion-card-{conclusion.id}" hx-swap="outerHTML" hx-include="#reviewer-name">` with hidden `analysis_run_id` and `cluster_id` inputs, an optional `note` textarea (`maxlength="500"`) and an "Acknowledge divergence" button |

`group_evidence` is read as `group_evidence is defined and group_evidence`. Styling follows the existing card's Tailwind classes. No `|safe` anywhere, and none of the bulk-approval phrases (fact 7).

## Queue page contract (`app/templates/pages/review_queue.html`)

- Extends `base.html`, with a breadcrumb and the h1 "Review queue".
- Intro: "{open_count} open of {total} conclusions." plus one sentence explaining the order and grouping (free wording, no bulk phrases).
- `<p data-queue-keys>Keyboard: j next, k previous</p>`.
- The same `#reviewer-name` input as the Conclusions page.
- **Groups.** Per group, `<section data-queue-group="{group_key}" data-shared="yes|no">`. Shared groups first show a panel: "Shared evidence: {topic or cluster_id} ({n} requirements)", then one `<li data-shared-claim="{claim_id}">` per shared claim (statement, quote, id, file linked to `href`).
- **Items.** Per entry, `<div data-queue-item data-conclusion-id="{id}" data-queue-index="{n}" data-state="{state}" data-risk="{risk}" data-flags="{comma-joined flags}" tabindex="-1">`, with the attributes in that order and `n` running from 0 across the whole page, wrapping `{% with card=entry.card, group_evidence=group.shared %}{% include "components/conclusion_card.html" %}{% endwith %}`.
- **Script.** `{% block scripts %}<script data-queue-nav>…</script>{% endblock %}`, implementing D-P6-7-K's keys. It uses `"j"` and `"k"` (double-quoted), `scrollIntoView`, and the `"INPUT"`, `"TEXTAREA"`, `"SELECT"` guard, and selects `[data-queue-item]`.
- The Conclusions page gets one link, "Review queue →", to `/assessments/{id}/review-queue`, after "Findings and actions →".

## Span page contract (`app/templates/pages/evidence_span.html`)

- Extends `base.html`.
- **Header.** A link to `/evidence/{evidence_id}`, the filename, "Version {n}", then "Current version" or "Superseded version", then `location_ref`.
- **Body by case.**
  - Not available: `<p data-span-unavailable>The extracted text of this version is no longer available.</p>`.
  - Whole: "Whole document cited.", then `<pre data-evidence-span-text>` holding the preview, with "…" if truncated. The string `cited-span` must not appear anywhere on this page.
  - Span: `<pre data-evidence-span-text>` holding, in order:
    - "…" if `truncated_before`
    - `{{ before }}`
    - `<mark id="cited-span" data-cited-span>{{ span }}</mark>`, with no whitespace inside `<mark>`
    - `{{ after }}`
    - "…" if `truncated_after`
- No forms and no htmx attributes.

## `app/services/requirement_card.py` (new): names and signatures

Constants (exact strings; the tests pin most of them):
```python
FALLBACK_CRITERIA_LABEL = "Judged against the control description; no approved test criteria yet"
APPROVED_CRITERIA_LABEL = "Judged against approved test criteria"
V1_SOURCE_LABEL = "Proposed by the v1 analysis: no criteria checklist or verified claims are available for this requirement."
NO_RUN_LABEL = "No analysis run is linked to this conclusion."
REASON_COMPLIANT = "Every test criterion is met by at least one verified claim."
REASON_SCOPE_EXCLUDED = "Outside the recorded assessment scope."
NO_RESPONSE_LABEL = "No confirmed questionnaire response."
NO_CLAIMS_LABEL = "No verified claim addresses this requirement."
UNSUPPORTED_ASSERTION_LABEL = "Unsupported assertion: no verified evidence supports this response or proposal."
SHARED_EVIDENCE_LABEL = "Evidence for this group is shown once, above."
MISSING_EVIDENCE_RFI_NOTE = "Approved insufficient-evidence conclusions are added to the next RFI version."
V1_MISSING_EVIDENCE_LABEL = "Suggested by the framework's evidence request list."
DIVERGENCE_SENTENCE = ("The same verified claims were judged Compliant under {compliant} and "
                       "Non-Compliant under {non_compliant}. Requirements can legitimately differ; "
                       "acknowledge that you have reviewed this before approving.")
DIVERGENCE_ACK_REQUIRED_MESSAGE = "Acknowledge the framework divergence note before approving this conclusion."
NO_DIVERGENCE_MESSAGE = "This conclusion has no framework divergence note to acknowledge."
DIVERGENCE_STALE_MESSAGE = "The framework divergence note changed since you loaded it. Reload the card and review it again."
CONCLUSION_NOT_FOUND_MESSAGE = "Conclusion not found"
DIVERGENCE_ACK_ACTION = "conclusion.divergence_acknowledged"
AUDIT_ENTITY_TYPE = "conclusion"
ACK_NOTE_MAX_CHARS = 500
ANSWER_SOURCE_LABELS = {"human": "Entered in the questionnaire"}
CRITERION_SYMBOLS = {"met": "✓", "not_met": "✗", "no_evidence": "?"}
CLAIM_KINDS = ("design", "operating", "context")
DATE_FIELDS = ("effective_date", "document_date")
SPAN_CONTEXT_CHARS = 1500
WHOLE_PREVIEW_CHARS = 3000
SPAN_INVALID_MESSAGE = "Citation span not found in this evidence version."
VERSION_NOT_FOUND_MESSAGE = "Evidence version not found"
CHIPS = {...}   # the D-P6-7-G table, key -> (label, tone)
```

Frozen dataclasses: `ClaimView(claim_id, statement, quote, kind, filename, href, needs_review, derived_from_image)`, `CriterionRow` (E), `ResponseView` (F), `Contradiction(claim_id, note)`, `QualityChip(key, label, tone)`, `MissingEvidence(document_type, label, what_it_would_show)`, `DivergenceNote` (I), `CardContext(assessment, runs, envelopes, basis, source_dates, claim_set_id, acks)`, `SpanView` (L), and:
```python
@dataclass(frozen=True)
class RequirementCard:
    source: str                       # "v2" | "v1" | "none"
    analysis_run_id: str | None
    proposed_outcome: str | None
    reason: str | None
    criteria_source: str | None
    criteria_label: str | None
    criteria: tuple[CriterionRow, ...]
    claims: tuple[ClaimView, ...]     # cited, verified, in cited order
    response: ResponseView | None
    contradictions: tuple[Contradiction, ...]
    unsupported_assertion: bool
    analysis_incomplete: bool
    flags: tuple[str, ...]            # the judge record's flags (v2), () otherwise
    quality: tuple[QualityChip, ...]
    missing_evidence: tuple[MissingEvidence, ...]
    missing_evidence_label: str | None
    divergence: DivergenceNote | None

class RequirementCardError(Exception): .message, .status_code
def load_context(db, assessment, proposals, conclusion_ids) -> CardContext
def build_card(context, conclusion, proposal, citations) -> RequirementCard
def approval_blocker(card: RequirementCard | None) -> str | None
def card_for(db, conclusion, proposal) -> RequirementCard            # single-card load_context + build_card
def divergence_blocker(db, conclusion, proposal) -> str | None       # approval_blocker(card_for(...))
def acknowledge_divergence(db, *, assessment_id, conclusion_id, analysis_run_id, cluster_id, note, actor) -> tuple[AuditEvent, bool]
def span_view(db, version_id, ref) -> SpanView
```

`load_context` loads the claim set (`desk_review_v2.load_claim_set`) only when at least one loaded envelope is v2. It maps each claim-set `source_id` to its date (D-P6-7-G). It loads all acknowledgement events for `conclusion_ids` in one query, ordered by `created_at, rowid`, keyed by `(entity_id, metadata.analysis_run_id, metadata.cluster_id)`, with the first event winning. Events with malformed metadata are skipped. The module never commits.

## File overlap with P6-8 and merge order

P6-7a touches exactly these files. Scenario 14 enforces the `app/` part:

| Path | Change |
|---|---|
| `app/services/requirement_card.py` (new) | B–J, L |
| `app/services/review_queue.py` (new) | J, K |
| `app/routers/requirement_review.py` (new) | L |
| `app/services/conclusion_review.py` | B (field, context, blocker), I (gate in `decide`), import |
| `app/main.py` | L (import + one `include_router` line) |
| `app/templates/components/requirement_card_body.html` (new) | card contract |
| `app/templates/components/conclusion_card.html` | one `include` line |
| `app/templates/pages/review_queue.html` (new), `pages/evidence_span.html` (new) | page contracts |
| `app/templates/pages/conclusions.html` | one link |
| `tests/test_p6_7_requirement_card.py` (designer) | contract |
| `tests/test_p6_3a_grounding.py`, `tests/test_p6_nist_csf2_alignment.py`, `tests/test_p6_4_cap_upload_limit.py`, `tests/test_p6_4_whats_missing.py` | M: guard excludes (designer) |
| `tasks/todo.md` | one P6-7a line |
| `tasks/handoffs/2026-09-28-p6-7-requirement-card.md` | this file; Codex appends `## Results` only |

**P6-8 owns** `app/routers/reports.py`, `app/services/report_snapshots.py`, `app/utils/pdf_export.py`, the new report-rendering modules, the report templates, `requirements.txt`, `.github/workflows/`, and `Dockerfile`. P6-7a touches none of them. Scenario 14 fails if it does, and also if it touches `web.py`, `base.html`, `workpaper.html` or `workpaper_entry.html`, which a standalone Workpaper might change.

**Shared surfaces (text conflicts only):**
- `tasks/todo.md` (both add a line)
- `app/main.py`, if P6-8 registers a router
- the four guard files, if P6-8 adds excludes to the same lists (it will for `test_p6_3a_grounding.py` if it touches `app/templates` or `app/routers`)

**Merge order:** P6-7a first. It is smaller, adds no dependency or fixture, and does not re-record goldens. P6-8 then merges `origin/main` into its branch and keeps both sides in the guard lists, `todo.md` and `main.py`. If P6-8 lands first, P6-7a does the same. The repo rejects force-pushes, so never rebase. P6-8's standalone Workpaper is unaffected: the requirement section is only in `conclusion_card.html`, and the Workpaper renders `workpaper_entry.html`.

## Do not touch

- The contract test file `tests/test_p6_7_requirement_card.py`, and the four designer-edited guard files beyond what is already there.
- **Services, models and config:**
  - `app/services/{analysis_v2,analysis_pipeline,claude_analyzer,desk_review,desk_review_v2,llm_client,scoring,report_basis,report_snapshots,rfi_requests,citations,evidence,approved_report,workpaper}.py`
  - `app/services/grounding/**`, `app/models/**`, `app/schemas/**`, `alembic/**`, `app/config.py`, `app/frameworks/**`, `app/dpdpa/**`
- **Routes and templates:**
  - `app/routers/{conclusions,review,reports,web,snapshots,analysis,documents}.py`
  - `app/utils/**`
  - `app/templates/base.html`, `pages/workpaper.html`, `components/workpaper_entry.html`
- **Everything else:** `requirements.txt`, `.github/**`, `Dockerfile`, `scripts/**`, every other existing test and fixture, and everything in the independence list.

If you find you need to change any of these, stop and report.

## Non-goals

- The one-click RFI write (P6-7b).
- Keyboard approval or any bulk action (D3).
- Changing risk on the card.
- Re-judging or new LLM calls.
- Workpaper or report changes (P6-8).
- Filtering evidence by date. The period chip informs; it does not exclude.
- Remediation drafting (P6-10).
- Real user identities (Track 4).
- A migration.

## Test scenarios (all in `tests/test_p6_7_requirement_card.py`)

The suite uses an Alembic-`head` SQLite database per test and the real app through `TestClient`. v2 fixtures run the real Stage 0-1 pipeline and P6-4 judge over invented text (`policy_text(Q_*)`, and `tests/grounding_fixtures/infosec_policy.txt` for dates), using the P6-3b/P6-4 provider fakes (`JudgeProvider`, `e2e_script`). After each fixture is built, any `llm_client.call_llm` fails. Approvals call `tests/report_period_helper.record_test_period` first. The default fixture produces:
- a DPDPA `CH4.SDF.1` compliant vs ISO `ISO.A5.2` non-compliant divergence (`CLUSTER_002`)
- `CH2.CONSENT.2` with a positive response and no claim (unsupported)
- no-input requirements that are insufficient evidence with pack missing-evidence

| # | Test | Covers |
|---|---|---|
| 1 | `test_scenario_1_v2_card_criteria_checklist_links_only_verified_claims` | C, D, E: source/criteria attributes, fallback label, reason, ✓/✗/? rows, claim links = the cited verified claims with span hrefs, no cross-requirement claim, service view fields |
| 2 | `test_scenario_2_claim_ids_outside_the_verified_set_never_render` | D: forged claim id and contradiction in the envelope never render or reach the view |
| 3 | `test_scenario_3_client_said_vs_evidence_shows` | F: response label and source, unsupported label, no-claims/no-response labels, claim body, contradiction row |
| 4 | `test_scenario_4_quality_chips` | G: currency current/superseded/none, period not_recorded/dated/after_cutoff/undated, scope in/excluded/not_recorded, kind, analysis incomplete, no "confidence" or percentage |
| 5 | `test_scenario_5_missing_evidence_lists_judge_output_and_links_the_rfi` | H: missing items, RFI note and link, no RFI write |
| 6 | `test_scenario_6_divergence_must_be_acknowledged_before_approval` | I: note content and form, approve/edit/service refused, card blocker, foreign-Conclusion event ignored, stale 409, 404, no-divergence 400, acknowledgement event shape and note cleaning, idempotence, envelope bytes unchanged, per-Conclusion, approve after acknowledgement |
| 7 | `test_scenario_7_acknowledgement_belongs_to_one_run` | I: reopen → re-analysis → new run needs a new acknowledgement; old event kept |
| 8 | `test_scenario_8_v1_fallback_and_legacy_cards` | C, G, H: v1 label, no criteria/divergence, grounding chips, pack missing evidence, `none` card, v1 approval needs no acknowledgement |
| 9 | `test_scenario_9_review_queue_sorts_flags_groups_and_navigates` | K, L: 404, every card once, indexes, deterministic risk, flags, the `CLUSTER_002` shared group with shared claims and per-card controls, the sort invariants, keyboard script, no bulk phrases, Conclusions-page link |
| 10 | `test_scenario_10_queue_risk_matches_the_judge_table_without_importing_grounding` | J: parity with `judge.deterministic_risk`, unknown control, v1 LLM risk ignored, no grounding/LLM/analysis_v2 imports |
| 11 | `test_scenario_11_span_viewer_highlights_the_cited_span` | L: exact `<mark>`, header, read-only, 400/404, whole, superseded |
| 12 | `test_scenario_12_approved_criteria_label` | E: approved criteria rows and label per requirement |
| 13 | `test_scenario_13_single_card_pass_and_field_shape` | B: one `conclusion_cards` call for the queue, trailing `requirement` field, constants, frozen dataclasses |
| 14 | `test_scenario_14_p6_7_touches_only_its_files` | file set (green before and after) |

## Verification (before reporting done)

1. `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_7_requirement_card.py` → **14 passed**, file unmodified.
2. **Neighbours, all green:**
   ```
   .venv/bin/pytest -q -p no:cacheprovider tests/test_conclusion_approval.py tests/test_workpaper.py tests/test_findings.py tests/test_p5_2_reader_migration.py tests/test_p6_6_report_foundations.py tests/test_p6_4_v2_judge.py tests/test_p6_3b_v2_flag.py tests/test_p6_3a_grounding.py tests/test_p6_nist_csf2_alignment.py tests/test_p6_4_cap_upload_limit.py tests/test_p6_4_whats_missing.py tests/test_p5_6_rfi_rebuild.py tests/test_performance_benchmarks.py
   ```
3. **Scope checks.**
   - `git diff --stat main -- app/services/analysis_v2.py app/services/grounding app/services/analysis_pipeline.py app/services/scoring.py app/models alembic app/routers/conclusions.py app/routers/web.py app/templates/base.html` is empty.
   - `grep -n "services.grounding\|llm_client\|analysis_v2" app/services/requirement_card.py app/services/review_queue.py app/routers/requirement_review.py` finds nothing.
4. **Full suite:** `.venv/bin/pytest -q -p no:cacheprovider`. Everything should be green except `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes`, which fails while `tests/` is uncommitted and goes green once the orchestrator commits. List any other failure and its cause.
5. When the orchestrator launches Codex with `codex exec`, stdin must be redirected: `codex exec ... < /dev/null`.

## Smoke plan (orchestrator, after Codex, before the PR)

Codex has no network. The orchestrator runs this.

1. **Contract smoke, no network:**
   ```
   .venv/bin/pytest -q -p no:cacheprovider tests/test_p6_7_requirement_card.py -k "scenario_1 or scenario_6 or scenario_9 or scenario_11" -v
   ```
   Paste the pass lines into `## Results`.
2. **Rendered smoke on a v2 fixture run**, with the app running locally (`run` skill, `--host 127.0.0.1`) and `ANALYSIS_PIPELINE_VERSION=v2`:
   1. Create a DPDPA+ISO assessment.
   2. Upload `tests/grounding_fixtures/infosec_policy.txt` and `privacy_notice.txt`. Never anything from `validation/`.
   3. Run desk review, then analysis. This makes real OpenRouter calls: estimate the cost first (two small documents, about 40 judge requirements with inputs).
   4. Record a period on the Conclusions page.
   5. Check these, and save the page HTML to the scratchpad:
      - **(a)** A card shows "Judged against the control description; no approved test criteria yet", with ✓/✗/? rows. Every `data-claim-link` id appears in that run's `verified_claims`. Check this with a one-off script that reads `AnalysisRun.claims_json` from the local DB.
      - **(b)** A claim link opens `/evidence-versions/{id}/span` with the quote inside `<mark>`.
      - **(c)** If the run has a divergence (`grep -c data-divergence-note`): Approve gives the acknowledgement toast; acknowledge; Approve succeeds; one `conclusion.divergence_acknowledged` audit row exists. If the live run has no divergence, say so and rely on scenario 6.
      - **(d)** `/assessments/{id}/review-queue` renders, j/k moves the focus in a browser, and shared groups show the evidence once.
      - **(e)** No card shows a confidence number.
3. **Fallback without network.** If the live run is not possible, run the same checks against the scenario 9 fixture: dump `http.get(...).text` from a throwaway script using the test helpers, and record that in Results.

## Adversarial review checkpoints `[AR]` (after Codex, before the PR)

1. **D3.** Is there any path that approves more than one Conclusion per request? Check keyboard, forms and routes. Is `decide` still the only writer?
2. **Gate completeness.** Can a Conclusion with an unacknowledged divergence be approved or edited-and-approved by any route, a stale form, or a race? Two tabs: acknowledge on run A while re-analysis creates run B. What does `decide` see?
3. **Closed set.** Can any claim id, quote or href on the card come from anything but the run's own `verified_claims` ∩ the record's `cited_claim_ids`? Is any `|safe` or unescaped text used?
4. **Determinism.** Is any number or risk shown in the queue or on the card taken from LLM output? Does the queue mirror stay equal to the judge table (scenario 10)?
5. **Audit trail.** Is there one event per acknowledgement, with nothing written on error or on a repeat? Is the envelope never mutated? Does ordering stay deterministic for same-timestamp events?
6. **Performance.** Is there still one `conclusion_cards` call per page, one run query, and no per-card claim-set load? Check `tests/test_performance_benchmarks.py` timings.
7. **Span viewer.** Are the bounds checked? Is there any path that reads a file from disk (there should be none; extracted text only)?
8. **File set and independence.** The diff must match the File overlap table exactly, with nothing under grounding, analysis, models, alembic, report or P6-8 files.

## Codex implementation prompt (ready to paste)

The orchestrator commits the designer files first. It prepares the worktree: `.venv` symlink, `.env` copy, and `git branch -f main origin/main`. Then it runs:

```bash
codex exec -m gpt-5.6-luna -c model_reasoning_effort=xhigh -s workspace-write -c 'plugins."compound-engineering@compound-engineering-plugin".enabled=false' -C <worktree> "<prompt below>" < /dev/null
```

```text
You are implementing P6-7a (consultant requirement card, divergence acknowledgement,
review queue, span viewer) in the CyberAssess repo in this working directory.

Read, in order:
1. CLAUDE.md
2. tasks/handoffs/2026-09-28-p6-7-requirement-card.md. This is the spec. Every name,
   signature, constant, route, form field, data attribute and rendered string in it
   is binding.
3. tests/test_p6_7_requirement_card.py. This is the contract. Do not edit it.
4. The code named in the handoff's Step 0.

Rules:
- Make all 14 tests in tests/test_p6_7_requirement_card.py pass WITHOUT editing that
  file. Never skip, xfail, weaken, re-parametrize or delete a test. If a test looks
  wrong, leave it failing and explain it in the handoff's "## Results". Put extra
  tests in tests/test_p6_7_extra.py.
- Touch only the files in the handoff's "File overlap" table. Scenario 14 enforces
  the app/ part. Do not touch anything listed under "Do not touch".
- Make no LLM call, no migration and no model change. The new modules must not
  import app.services.grounding, llm_client or analysis_v2 (D-P6-7-J). Never take
  risk, priority or a score from LLM output.
- Answer-key independence (D-P5-9-C). Never open, grep, glob, list or read:
  validation/**, tasks/handoffs/*p5-9*, docs/plans/2026-09-24-002-*,
  scripts/seed_test_companies.py, scripts/test_ground_truth.json,
  scripts/seed-v2-prompt.md, scripts/validation/**, tests/test_validation_harness.py,
  any answer_key.json, ~/cyberassess-runs/**. Scope every search to explicit paths
  under app/ and tests/test_p6_7_*.py. Never run a bare repo-root search.
- You cannot write .git: no git add, commit, branch or stash. Read-only git is fine,
  and the guards use it.
- You have no network. Use .venv/bin/pytest (Python 3.13).
- If the code forces a deviation from the design, stop and report it in "## Results".
  Do not choose an alternative.

Steps:
1. Do the handoff's Step 0: record the baseline suite counts and confirm facts 1-12.
2. Implement D-P6-7-B through L and the three markup contracts (card partial, queue
   page, span page).
3. Run the handoff's Verification section:
   - the contract file must show 14 passed
   - the neighbour list must be green
   - the scope greps must be empty
   - run the full suite: .venv/bin/pytest -q -p no:cacheprovider
   Expect all green, except tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes
   if you left anything under tests/ uncommitted. That test passes once the
   orchestrator commits.
4. Append to the handoff's "## Results":
   - the files changed
   - the Step 0 baseline
   - the contract, neighbour and full-suite counts
   - any guard exclude you had to add, and why
   - any deviation or still-failing assertion, with your reasoning
```

## Open questions for Saqlain (recommended defaults; nothing here blocks P6-7a)

1. **P6-7b, the one-click "add to RFI" for missing evidence.** This needs a new RFI item kind, the consultant-requested items, and a new RFI `source` key, which would make existing drafts stale on their next issue check. It touches `rfi_requests.py`, the P5-6 test pins, and `report_snapshots.py` (P6-8's file).
   - **Recommended:** design P6-7b after P6-8 merges. Store requests as append-only `rfi.evidence_requested` audit events, and bump the RFI `schema_version` to 2 with the new key added only when requests exist, so current drafts do not go stale.
   - **Alternative:** ship the button now as a "queued for the next RFI" note with no document effect. Not recommended: it is a button that does not do what it says.
2. **Acknowledgement note.**
   - **Recommended:** optional, up to 500 characters.
   - **Alternative:** required, so every acknowledgement carries a reason. That is stronger for an auditor, but adds friction on every divergence.
3. **Acknowledgement scope.**
   - **Recommended:** per Conclusion and per run (D-P6-7-I).
   - **Alternative:** per cluster, so one acknowledgement clears every member. That is fewer clicks, but it lets a consultant clear a card they never opened.
4. **Queue risk for consultant-edited conclusions.**
   - **Recommended:** always the pack table over the current outcome. Edited cards are decided and sort last anyway.
   - **Alternative:** use the consultant's edited `risk_level` for edited cards.
5. **"In period" meaning.**
   - **Recommended:** the chip checks only that the document is dated on or before the evidence cut-off. A policy effective before the period start is treated as in force.
   - **Alternative:** also warn when a `next_review_date` falls before the period start (review overdue).

## Designer verification

All runs used Python 3.13 (`.venv`) on 2026-09-28.

| State | Result |
|---|---|
| Designer commit on `db3fdc8` (red) | **1059 passed, 10 skipped, 13 failed.** Only the 13 P6-7 contract scenarios fail, each for a missing-code reason. Scenario 14 passes. |
| Throwaway reference implementation, committed on a local scratch branch that was then deleted (never pushed) | **1072 passed, 10 skipped, 0 failed.** All 14 contract tests pass, and the four guard files with the D-P6-7-M excludes pass. |
| The reference, uncommitted, before the excludes were added | 3 guard failures (`test_p6_3a_grounding` s17, `test_p6_4_cap_upload_limit` s9, `test_p6_4_whats_missing` s13). `test_p6_nist_csf2_alignment` would trip once committed. This is why the excludes were added. |
| Mutations | 14 of 14 caught (see the list at the top of this file). |

`tests/test_performance_benchmarks.py` and `tests/test_workpaper.py` scenario 10 (one `conclusion_cards` call) stayed green with the reference.

## Results

### Implementation

Changed only the P6-7a file set plus the required tracker and this Results section:

- `app/services/requirement_card.py`
- `app/services/review_queue.py`
- `app/services/conclusion_review.py`
- `app/routers/requirement_review.py`
- `app/main.py`
- `app/templates/components/conclusion_card.html`
- `app/templates/components/requirement_card_body.html`
- `app/templates/pages/conclusions.html`
- `app/templates/pages/review_queue.html`
- `app/templates/pages/evidence_span.html`
- `tasks/todo.md`
- `tasks/handoffs/2026-09-28-p6-7-requirement-card.md`

The contract test file was not edited. No migrations, models, analysis, grounding, scoring, report, snapshot, RFI, or existing route files were changed. No additional stale-guard excludes were needed; the designer's P6-7a excludes were already present.

### Verification

- Step 0 baseline: **1059 passed, 10 skipped, 13 failed**. The 13 failures were the expected missing P6-7a implementation failures; scenario 14 passed.
- Contract: `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_7_requirement_card.py` → **14 passed**.
- Neighbours: the handoff's required neighbour command → **299 passed, 9 skipped**.
- Scope: forbidden app diff was empty; the new modules contained none of `services.grounding`, `llm_client`, `call_llm`, or `analysis_v2`.
- Full suite: `.venv/bin/python -m pytest -q` → **1072 passed, 10 skipped, 286 warnings**.

No deviations or still-failing assertions.
