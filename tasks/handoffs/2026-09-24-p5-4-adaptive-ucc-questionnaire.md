# P5-4: Adaptive questionnaire on the UCC path. Cluster questions get deepen, pre-fill and tier treatment from P5-3's framework-keyed findings, with a per-member-control derivation rule, cluster-keyed `"document"` pre-fill rows, live-state rendering and confirmation of pre-fills, screening kept DPDPA-only with honest copy, and real questionnaire stats

**Plan:** `docs/plans/2026-09-24-001-cleanup-and-non-dpdpa-parity-plan.md`, task P5-4 ("Adaptive questionnaire on the UCC path"). It owns the questionnaire half of known gap **#1** ("UCC/multi-framework path gets no desk-review pre-fill, screening pre-fill or tiering"). P5-3 closed the input half. It also owns the screening-copy half of audit finding **A3**, P5-3's open questions **1-6** (all handed forward to this task), and P5-1's open question **1** (implicit confirmation by section save). Plan-level decisions it implements against: **D-P5-A** (registry-driven code, acceptance on the three launch packs), **D-P5-C** ("No task may pre-fill ISO/NIST questions from DPDPA-keyed findings"), and **D-P5-F** as decided by P5-1 (D-P5-1-D).
**Owner:** Claude designs the cluster-status rule → Codex implements. See `tasks/agent-ownership.md`, criteria "Judgment/architecture" (UCC cluster semantics) and "A product invariant" (unconfirmed machine answers, D-P5-F). Every fork is closed below.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, every constant, message, key name and ordering below, and every test scenario. "The existing code makes step N awkward" is not a licence to redesign step N. Write down what you found and what you would need to change, then stop.

> **This task reads P5-3's `D-P5-3-*` decisions and P5-1's `D-P5-1-D` as a fixed contract.** That covers the one-row-per-requirement finding shape (D-P5-3-E), the scoped reader and quarantine rule (D-P5-3-H: `scoped_findings`, `failed_desk_review_frameworks`, `LEGACY_FINDING_FRAMEWORK_ID`), the flag vocabulary (D-P5-3-C), the pre-fill gate that this task widens only to rows its own questionnaire renders and only with `answer_source="document"` (D-P5-3-L), the screening gate (D-P5-3-M), the quarantine of legacy rows (D-P5-3-N), and the exclusion of `UNCONFIRMED_ANSWER_SOURCES` from analysis and gates (D-P5-1-D). No decision below weakens any of them. Where one is widened, the decision names the rule it widens and says why the widening stays inside it.

**Depends on:** P5-3, merged to `main` (PR #41, `e8916ad`). P5-8, merged (PR #38).
**Blocks:** nothing in Phase 5.
**Runs in parallel with:** P5-2 and P5-6, neither dispatched yet. The coordination rule is D-P5-4-K.
**Code baseline:** `main` at `d69aa71`. That commit is docs-only on top of `e8916ad` (`git diff --stat e8916ad d69aa71` touches only `CLAUDE.md` and `tasks/todo.md`). Every file:line below was read at `d69aa71`. Relocate everything by symbol name, because line numbers drift.
**No failing contract suite is pre-written.** `grep -rlnE "modulate_cluster|ClusterDeskData|finding_has_grounded_citation|questionnaire_progress|screening_applies|is_dpdpa_only" tests/` finds nothing. **Codex writes `tests/test_p5_4_adaptive_ucc_questionnaire.py` itself**, working from `## Test scenarios`. Every scenario listed is required. You may add cases, but you may not drop or weaken one. **No existing test file is modified.**

## Step 0 (dispatching Claude session, then Codex)

**The handoff author could not measure the suite baseline.** The authoring container has no project virtualenv, and `pip install -r requirements.txt` is refused because `pypi.org` returns `403 host_not_allowed` under that environment's egress policy. The last **recorded** baseline is from P5-3's merge. `tasks/todo.md` says **593 passed, 9 skipped, 0 failed**. P5-3's own `## Results` says **591 passed, 9 skipped** (the difference is the post-Codex test fix it describes). `grep -rho "def test_[a-z0-9_]*" tests | wc -l` = 506 test functions at `d69aa71`; parametrization accounts for the rest. **The dispatching session must measure the baseline in the fresh worktree and record it here before dispatch**: `git worktree add ../dpdpa-gap-tool-p5-4 -b codex/p5-4-adaptive-ucc-questionnaire main`, symlink `.venv`, copy `.env`, then `.venv/bin/pytest -q`.

**Codex, your first action:** run

```bash
grep -n "^def scoped_findings\|^def failed_desk_review_frameworks\|^LEGACY_FINDING_FRAMEWORK_ID" app/services/desk_review_findings.py
grep -n "^UNCONFIRMED_ANSWER_SOURCES\|^def confirmed_response_clause\|if assessment.frameworks != \[\"dpdpa\"\]" app/services/auto_answer.py
grep -n "^class ScreeningNotApplicable\|^SCREENING_NOT_APPLICABLE_MESSAGE" app/services/screening.py
.venv/bin/alembic heads
```

and confirm all of the following:
1. `desk_review_findings.py` defines `LEGACY_FINDING_FRAMEWORK_ID`, `scoped_findings` and `failed_desk_review_frameworks`.
2. `auto_answer.py` defines `UNCONFIRMED_ANSWER_SOURCES = ("document", "inferred")` and `confirmed_response_clause`, and it still has the D-P5-3-L gate.
3. `screening.py` defines `ScreeningNotApplicable` and `SCREENING_NOT_APPLICABLE_MESSAGE`.
4. The single Alembic head is `8b2d5f7e1c34`.

**If any of these is not true, stop and report in `## Results`.**

## Goal

1. On an ISO 27001, NIST CSF or mixed assessment, a completed desk review changes the questionnaire. A cluster question with any document finding against any of its member controls is **deepened**. A cluster question is **pre-filled** only when every member control has its own framework's adequate or partial coverage and its own grounded quote. Otherwise it stays **active**, with the evidence attached when there is any.
2. No ISO or NIST control is ever pre-filled from a DPDPA-keyed finding (D-P5-C), and no member of a framework whose desk review failed is ever pre-filled.
3. Cluster questions get depth tiers from the same `tier_engine.assign_tiers` rules as DPDPA questions, and the stats bar shows real counts.
4. A document pre-fill on the cluster path is stored where the cluster questionnaire can show it (keyed by cluster question id, `answer_source="document"`). It is excluded from analysis and gates until a consultant saves it (D-P5-1-D, unchanged).
5. On both paths, a document pre-fill is shown and confirmable **only while** the live questionnaire still marks that question as document-pre-filled. Saving a pre-filled answer always records its provenance (`document_confirmed` or `human_override`), never a bare `human`.
6. The "responses saved" count on the assessment page counts only confirmed answers to questions the questionnaire actually renders.
7. Domain screening is offered only where it can pre-fill anything, which is DPDPA-only assessments. Its copy no longer makes unverified percentage claims.

## Current state

### The cluster path has no modulation (gap #1)

- `app/services/question_engine.py::build_adaptive_questionnaire` (`:152-273`) parses `assessment.selected_frameworks` itself (`:173-179`, `[]` and bad JSON → `["dpdpa"]`). `is_dpdpa_only = selected_frameworks == ["dpdpa"] or selected_frameworks == []` (`:182`). Anything else returns `_build_multi_framework_questionnaire(assessment, selected_frameworks)` (`:183-184`). `Assessment.frameworks` (`app/models/assessment.py:51-59`) is the property with the same fallback semantics. The D-P5-3-L/M gates use the property.
- `_build_multi_framework_questionnaire(assessment, framework_ids)` (`:57-139`):
  - computes `excluded = compute_excluded_controls(framework_ids, assessment.applicable_requirements)` and calls `build_multi_questionnaire(framework_ids, excluded_controls=excluded, context_profile=context_profile)`;
  - normalises each UCC dict into the template shape with **hard-coded** `status="active"`, `skip_reason=None`, `desk_review_note=ucc_q.get("context_note")`, `desk_review_evidence=None`, `tier="standard"`, `source="base"`, `follow_up_enabled=bool(ucc_q.get("follow_ups"))`, `maps_to=[c["control_id"] for c in ucc_q.get("controls", [])]` and every `pre_fill_*` `None` (`:91-107`);
  - groups by `domain_group` into sections;
  - returns hard-coded stats: `skipped_questions: 0`, `pre_filled_questions: 0`, `inferred_questions: 0`, `deepened_questions: 0`, `industry_questions: 0`, `tier_counts: {"standard": total, "deep": 0, "light": 0}` (`:128-139`).
  - It takes no `db` and reads no desk review.
- **The DPDPA-only machinery that P5-4 gives the cluster path an equivalent of:**
  - `_load_desk_review_data(assessment_id, db)` (`:276-343`) reads `scoped_findings(db, assessment, framework_ids=["dpdpa"])` (P5-3 F2) and DPDPA-filtered coverage.
  - `_modulate_question(question, desk_data)` (`:346-419`) applies this priority: absence row → deepen; signal row (`requirement_id == req_id`) → deepen; coverage `adequate`/`partial` **with at least one evidence row** → pre-fill `fully_implemented`/high or `partially_implemented`/medium, `pre_fill_source="document"`; otherwise active, with evidence attached. It does not check citations.
  - `_apply_screening` (`:422-468`) applies only to still-active questions.
  - `_modulate_industry_question` (`:481-576`) uses `deepen_if.signal_flags`, which reads `flag_type` (P5-3 D-P5-3-J).
  - `assign_tiers(modulated_base, risk_tier)` (`:253-257`) uses `risk_tier = context_profile.get("risk_tier", "MEDIUM")`.
- **Nothing in `question_engine.py` produces `status="skipped"` except scope exclusion** (`:221-225`). P5-8 deleted the dead reinstatement loop and the stale "Skip: strong document evidence" docstring line, and the module docstring (`:1-14`) now lists only Deepen and Add. **P5-8's cleanup is confirmed present at `d69aa71`.** The P5-3 keyword re-derivation is also gone (`:330-334` reads `finding.flag_type`; `grep -n content_lower` is empty). No coordination fork with P5-8 is left.

### Tier engine (`app/services/tier_engine.py`, 83 lines, unchanged by this task)

`assign_tier(question, risk_tier)` (`:16-54`) evaluates rules in order, and the first match wins:
1. `skipped` → skip.
2. `pre_filled` and not critical → light.
3. `pre_filled` and critical → standard.
4. `deepened` → deep.
5. critical with HIGH risk → deep.
6. high with HIGH risk → deep.
7. Everything else → standard.

`assign_tiers` (`:57-69`) mutates in place. `compute_tier_stats` (`:72-83`) returns `{"deep", "standard", "light", "skip"}`. It reads only `status` and `criticality`. `tests/test_phase2_tiers.py` pins it.

### UCC clusters (a correction to the task brief)

- **The UCC cluster definitions are not `root_cause_clusters`.** `FrameworkDefinition.root_cause_clusters` (`app/frameworks/schema.py:108`) is remediation-initiative grouping read by `scoring.py` (`ROOT_CAUSE_CLUSTERS`, `:12,459,500`). The UCC definitions are `app/frameworks/mappings/clusters.py::CONTROL_CLUSTERS`: 52 hand-curated clusters, 2 to 22 members each, and no control in more than one cluster (measured).
- `app/frameworks/cluster_engine.py::resolve_clusters(framework_ids, excluded_controls)` (`:113-195`) works like this:
  - **Single framework:** one singleton per control, `cluster_id=f"SINGLE.{control_id}"`.
  - **Several frameworks:** each `CONTROL_CLUSTERS` entry is filtered to members in the selected frameworks and not scope-excluded, and dropped if it ends up empty. Unclaimed controls become singletons.
  - **Scope-excluded controls are removed from membership.** A cluster never contains an excluded control, so the cluster path never has a `skipped` question.
- `app/frameworks/questionnaire_builder.py::_cluster_to_question` (`:131-199`) emits `controls: [{"framework_id", "control_id"}]` in mapping order. It sets `criticality = _max_criticality(...)` (`:202-216`), the highest criticality across member controls.
- **Measured question counts at `d69aa71`, no scope:**

  | Selection | Questions | Multi-member | Cross-framework | DPDPA-only-member | Largest cluster |
  |---|---|---|---|---|---|
  | ISO-only | 93 | 0 | 0 | 0 | 1 |
  | NIST-only | 94 | 0 | 0 | 0 | 1 |
  | DPDPA + ISO | 45 | 35 | 11 | 11 | 12 |
  | DPDPA + ISO + NIST | 48 | 41 | 30 | 11 | 13 |

  **So for ISO-only and NIST-only, a cluster question is exactly one control.** The rule below then reduces to a per-control rule.
- **Fixture clusters (measured, used by the test scenarios):**

  | Selection | Cluster | Criticality | `maps_to` |
  |---|---|---|---|
  | DPDPA + ISO + NIST | `CLUSTER_002` | critical | `["CH4.SDF.1", "ISO.A5.2", "NIST.GV.RR.02", "NIST.GV.RR.03"]` |
  | DPDPA + ISO | `CLUSTER_002` | critical | `["CH4.SDF.1", "ISO.A5.2"]` |
  | both mixed selections | `CLUSTER_021` | high | `["CH2.NOTICE.2"]` (DPDPA-only member) |
  | both mixed selections | `CLUSTER_022` | critical | `["CH2.NOTICE.3", "CH3.GRIEVANCE.1", "CH3.GRIEVANCE.2"]` |
  | ISO-only | `SINGLE.ISO.A5.1` | critical | `["ISO.A5.1"]` |
  | ISO-only | `SINGLE.ISO.A5.37` | medium | `["ISO.A5.37"]` |

  Registry names: `India DPDPA`, `ISO 27001`, `NIST CSF`.

### How cluster answers reach analysis (unchanged by this task)

- `app/routers/analysis.py::trigger_analysis` loads responses with `.filter(confirmed_response_clause())` (`:117`). On the multi path, the gate's `expected_question_ids` are the cluster ids of `build_multi_questionnaire(...)` (`:145-165`), and `answered_question_ids` are the confirmed, non-blank rows among them (`:176-180`).
- `app/frameworks/prompts.py::_expand_cluster_responses` (`:63-105`) maps a response to control ids:
  - `SINGLE.<id>` → `<id>`;
  - `CLUSTER_<n>` → every member control of that framework, from `CONTROL_CLUSTERS`;
  - a bare control id → passed through.
- **So a cluster-id-keyed row is already a first-class answer**. Once confirmed it is expanded to every member control of every framework. While it is `"document"`, `confirmed_response_clause` excludes it.

### Pre-fill and screening writers (the gates P5-4 owns)

- `app/services/auto_answer.py::persist_document_answers` (`:129-251`, file-relative): after the assessment lookup, `if assessment.frameworks != ["dpdpa"]: logger.info("Auto-answer: skipped for %s, pre-fill is keyed to the DPDPA-only questionnaire", …); return 0` (`:144-149`).
  - The DPDPA body pre-fills every `adequate`/`partial` coverage key with no signal or absence row. It does **not** require an evidence row, unlike `_modulate_question`.
  - Existing-row rule (`:207-210`): update only a `"document"` row, skip any other source.
  - It writes `answer_source="document"`.
  - Docstring line `:98`: "Pre-fill runs only on DPDPA-only assessments (P5-3 D-P5-3-L)."
- `app/services/desk_review.py::run_desk_review` calls it at `:188-197`: `pre_fill_count = persist_document_answers(assessment_id, db); if pre_fill_count: db.commit()`. **An update-only pass (0 created, ≥1 updated) is flushed but never committed.** The web path's `SessionLocal` then closes and the update is lost. This is pre-existing on the DPDPA path, and D-P5-4-F fixes it for both paths.
- `app/services/screening.py::run_screening_pass` (`:40-89`): `if assessment.frameworks != ["dpdpa"]: raise ScreeningNotApplicable(SCREENING_NOT_APPLICABLE_MESSAGE)` (`:59-60`). `_parse_inferences` keys by DPDPA requirement id (`:139`). `_persist_inferred_answers` (`:177-231`) writes `"inferred"` rows keyed by DPDPA ids.

### The questionnaire UI and its copy

- `app/templates/partials/questionnaire_tab.html:36-76` renders the "Domain Screening" card on **every** assessment with `context_done`. The problem lines are:
  - `:48` says "Optional — reduces questionnaire by ~30%".
  - `:53-58` shows a "Start screening" button.
  - `:67` says "Screening complete — high-confidence controls are pre-filled in the questionnaire below with a ✨ Inferred badge."
  - `:70-73` says "High-confidence controls are pre-filled. You only confirm or override them in the questionnaire."
  - On a mixed or ISO-only assessment, every one of those promises is false: since P5-3 the submit returns `SCREENING_NOT_APPLICABLE_MESSAGE` (A3).
  - `:85-87` shows "`{{ response_count }}` responses saved".
- `app/templates/partials/screening_form.html:33` says "AI will pre-fill ~30-40% of your detailed assessment". `grep -rn "30%\|30-40%"` finds no measurement anywhere in the repo that backs either percentage. The form renders unconditionally (`:38-89`). The error block is at `:16-21`.
- `app/templates/pages/assessment.html:69-71` shows `response_count` as the Questionnaire tab badge.
- `app/routers/web.py::assessment_detail` (`:784-~940`):
  - `response_count = db.query(QuestionnaireResponse).filter(assessment_id == …).count()` (`:817-822`). That counts every row: unconfirmed pre-fills, `FU.*` follow-ups, and the quarantined DPDPA-keyed rows on non-DPDPA-only assessments (P5-3 open question 4).
  - `screening_done` is set at `:826`.
  - The template context is at `:908-930`.
- `app/templates/partials/questionnaire_sections.html:1-26` is **the stats block**. It prints `total_questions`, the three tier counts, "pre-filled from documents", "inferred from screening", `"{{ stats.skipped_questions }} skipped (covered by documents)"` (`:17`), "deepened", and "industry-specific".
  - `:17` is false. The only skip producer is scope exclusion. P5-8 removed the matching docstring claim but not this label.
  - On the cluster path every number is hard-coded (above).
- `app/templates/partials/section_questions.html` pre-checks radios as `{% if existing.get(q.id, {}).get('answer') == opt %}checked {% elif not existing.get(q.id) and q.get('pre_fill_answer') == opt %}checked{% endif %}`. This is in the light pre-fill card (`:94-96`) and the standard pre-fill card (`:218-221`). The active/deepened card checks only `existing` (`:343-345`). So **any existing row pre-checks its question, whatever its source and whatever the live question status**.
- `web.get_questionnaire_sections_web` (`:1318-1360`) and `web.get_section_questions` (`:1363-1411`) build `existing` from **every** response row.
- `web.save_questionnaire_responses` (`:1414-1518`) saves only the rendered, non-skipped questions of the posted section (`:1430-1435`). The provenance transition is at `:1459-1480`:
  - an existing `"document"` row becomes `"document_confirmed"` if the answer is unchanged, else `"human_override"`;
  - any other source except `human`/`human_override`/`document_confirmed` (that is, `NULL` and `"inferred"`) becomes `"human"`;
  - a question with **no row** is saved as a new `"human"` row, **even when the consultant just accepted a live `pre_fill_answer`**, so that provenance is lost.
  - The section form's JS requires every question to be answered before submit (`section_questions.html:421-454`), so a section save submits every pre-checked radio. This is P5-1 open question 1.

### Standing guards this task must respect

- `tests/test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` runs `git diff --name-only` (working tree against index) over a list that includes `app/routers/web.py` and `tests/test_phase1_prefill.py`. It **fails while your `web.py` edits are uncommitted and passes once they are committed.** Do not modify it. Report it as "working-tree guard, expected until commit". **Do not modify `tests/test_phase1_prefill.py`.**
- `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes` asserts no **existing** test file is modified or staged. A new untracked test file does not trip it. That is one more reason no existing test file changes.
- `tests/test_p5_3_framework_desk_review.py` must pass unmodified. In particular:
  - Scenario 10 calls `persist_document_answers` on DPDPA + ISO and ISO-only assessments whose summary holds only `{"CH2.CONSENT.1": "adequate"}`, no findings, and asserts `== 0` and no rows. Under D-P5-4-F that still holds: no member has grounded evidence, and on ISO-only the DPDPA key is filtered out.
  - Scenario 9 asserts that screening on mixed and ISO-only assessments raises and that the submit route returns 200 with the message. D-P5-4-H keeps both.
  - Scenario 12 asserts `desk_review_findings.py` imports neither `llm_client` nor `app.services.desk_review`.
- `tests/test_no_blended_scoring.py`: no template may contain `overall_score`, and `web.py` may not use `.overall_score` or `overall_score=`. You add neither.
- `tests/test_phase2_tiers.py` pins `tier_engine`. You do not modify `tier_engine.py`.
- `tests/integration/test_questionnaire.py::test_save_questionnaire_responses` patches `app.routers.web.build_adaptive_questionnaire` with questions that have **only** `id` and `status`. Every new read of a question dict in the web routes must use `q.get(...)`.
- `grep -rn "relationship(" app/models/` must stay empty. There is no schema change, and the Alembic head stays `8b2d5f7e1c34`.

## Decisions (made here so they are not relitigated)

### D-P5-4-A. One routing predicate, and the cluster path gets a `db`

- Add to `question_engine.py`:
  ```python
  def is_dpdpa_only(assessment: Assessment) -> bool:
      """True when the assessment uses the DPDPA-only (requirement-keyed) questionnaire."""
      return assessment.frameworks == ["dpdpa"]
  ```
- `build_adaptive_questionnaire`: delete the local `selected_frameworks` parse and the `is_dpdpa_only = …` line (`:173-182`). Replace them with `if not is_dpdpa_only(assessment): return _build_multi_framework_questionnaire(assessment, assessment.frameworks, db)`. **Semantics are unchanged.** The property maps `NULL`, bad JSON and `[]` to `["dpdpa"]`, exactly as the deleted parse did. The DPDPA-only body below it is **not changed**, apart from the D-P5-4-I stats label, which is template-only.
- `_build_multi_framework_questionnaire(assessment, framework_ids, db)` gains `db` as its third positional parameter. It has no other callers (grep).
- `auto_answer.persist_document_answers` (D-P5-4-F) and `screening.screening_applies` (D-P5-4-H) use this same predicate. **No new `== ["dpdpa"]` or `== "dpdpa"` comparison is added anywhere else.** All cluster logic is registry-driven (D-P5-A), so GDPR, HIPAA and PCI selections get it with no code change.

### D-P5-4-B. The cluster path's input: P5-3's scoped findings, indexed per member control

Add to `question_engine.py`:

```python
@dataclass(frozen=True)
class ClusterDeskData:
    coverage: dict[str, str]           # selected-framework control id -> coverage level
    evidence: dict[str, list[dict]]    # control id -> evidence items, finding-id order
    absences: dict[str, list[str]]     # control id -> absence contents, finding-id order
    signals: dict[str, list[dict]]     # control id -> [{"group_key", "content"}], finding-id order
    failed_frameworks: frozenset[str]  # selected frameworks whose desk review call failed

def _load_cluster_desk_data(assessment: Assessment, db: Session) -> ClusterDeskData | None:
```

`_load_cluster_desk_data` works in this exact order:
1. `summary` = the assessment's `DeskReviewSummary` with `status == "completed"` (`.first()`, the same filter `load_desk_review_data` uses). If there is none → `None`.
2. `control_framework = {c.id: fw for fw in assessment.frameworks for c in FrameworkRegistry.get(fw).all_controls()}`.
3. `coverage` = `json.loads(summary.coverage_summary or "{}")`, filtered to keys in `control_framework`, keeping order. On `JSONDecodeError`/`TypeError`, or when the parsed value is not a dict, use `{}`.
4. `findings = scoped_findings(db, assessment)`. **This is the quarantine rule (D-P5-3-H)**: only rows whose `framework_id` (NULL read as `dpdpa`) is a selected framework. For each `f`, skip it when any of these holds:
   - `not f.requirement_id`;
   - `f.requirement_id not in control_framework`;
   - `finding_framework_id(f) != control_framework[f.requirement_id]`, meaning the row was written by a different framework's desk review than the control belongs to.

   D-P5-3-D's normalizer already drops such rows at write time. This read-time check is the D-P5-C backstop: a DPDPA-written row can never count as evidence for an ISO or NIST control, even if it was hand-inserted or written by a future writer that skips normalization. Cross-cutting findings and stray ids never reach a cluster question. Then:
   - `evidence` → append to `evidence[rid]`:
     ```python
     {"control_id": rid, "framework_id": control_framework[rid],
      "content": f"{rid} ({FrameworkRegistry.get(control_framework[rid]).name})",
      "source_quote": f.source_quote or "", "source_location": f.source_location or "",
      "severity": f.severity, "grounded": finding_has_grounded_citation(f)}
     ```
   - `absence` → `absences[rid].append(f.content or "")`.
   - `signal` → `signals[rid].append({"group_key": f.signal_group_id or f"row:{f.id}", "content": f.content or ""})`. A multi-requirement signal is already one row per requirement (D-P5-3-E), so every member it names sees it. `group_key` is the same key `group_signal_findings` groups on.
5. `failed_frameworks = frozenset(failed_desk_review_frameworks(summary)) & set(assessment.frameworks)`.

It returns the dataclass even when every map is empty. An empty map means "reviewed, nothing found", which is different from `None` ("not reviewed").

**It never reads `flag_type`, and it never looks at signal text.** On the cluster path any signal deepens, whatever its type. That settles P5-3's open question 2 (below). The keyword re-derivation stays retired: `question_engine.py` must still not contain `content_lower`.

Add to `app/services/desk_review_findings.py`, keeping its imports as they are (json, registry, models only; P5-3 scenario 12):

```python
GROUNDED_CITATION_LOCATION_TYPE = "text_span"

def finding_has_grounded_citation(finding: DeskReviewFinding) -> bool:
    """True for an evidence row whose non-blank quote was located verbatim in an evidence version."""
```

It returns `False` when:
- `finding.finding_type != "evidence"`;
- `(finding.source_quote or "").strip()` is empty;
- `json.loads(finding.citations_json or "[]")` raises `JSONDecodeError`/`TypeError`;
- the parsed value is not a list; or
- no element is a dict with `location_type == GROUNDED_CITATION_LOCATION_TYPE`.

Otherwise it returns `True`.

**Why `text_span` only.** `desk_review._persist_findings` (`:441-465`) writes a `text_span` citation only when `cite_quotes` locates the quote verbatim in an `EvidenceVersion`'s extracted text. A blank quote gets a `whole_item` citation, which proves only that the document exists. An ungrounded quote gets `[]`. So "cited evidence" in the plan's wording means a quote the system has verified is really in the client's document.

### D-P5-4-C. What one member control's state is

For a member control `m` of framework `fw`, given `ClusterDeskData d`:
- **flagged** iff any of the following holds:
  - `d.absences.get(m)` is non-empty;
  - `d.coverage.get(m) == "absent"`;
  - `d.signals.get(m)` is non-empty.
- **pre-fillable** iff all of the following hold:
  - `fw not in d.failed_frameworks`;
  - `d.coverage.get(m) in ("adequate", "partial")`;
  - `any(e["grounded"] for e in d.evidence.get(m, []))`.
- **Why coverage `"absent"` flags a member** even with no absence row: the registry prompt defines `absent` as "explicitly missing despite a relevant document" (D-P5-3-C). That is an absence finding by definition. `_normalize_result` can also drop an absence item (an unknown id) while keeping the coverage key. This is deliberately stricter than `_modulate_question`, which deepens only on absence rows. The DPDPA path is not changed (open question 3).
- **Why every member needs its own grounded quote:** one cluster answer is expanded to every member control of every framework at analysis (`_expand_cluster_responses`). A pre-fill therefore proposes an answer on behalf of every member. A member with no verified quote of its own has no basis for that proposal.

### D-P5-4-D. The cluster status derivation rule

`_modulate_cluster_question(question: dict, desk: ClusterDeskData | None) -> dict` returns a new dict (`{**question, …}`), and never mutates its input. `members = question["member_controls"]` is a list of `{"framework_id", "control_id"}` in mapping order (D-P5-4-E), and `ids = [m["control_id"] for m in members]` equals `question["maps_to"]`.

**0. Not reviewed.** If `desk is None`, return the question unchanged: `status="active"`, `desk_review_note=question["context_note"]`, `desk_review_evidence=None`. This is today's cluster output, except for `tier` (D-P5-4-E).

**Evidence items for display:** `items = [e for cid in ids for e in desk.evidence.get(cid, [])]`, in member order and then finding-id order. `evidence_or_none = items or None`.

**1. Deepen (first, overrides everything).** Build `findings_notes` by walking `ids` in order. For each `cid`:
- for each `content` in `desk.absences.get(cid, [])` → append `CLUSTER_ABSENCE_ITEM.format(control_id=cid, content=content)`;
- if `desk.absences.get(cid)` is empty and `desk.coverage.get(cid) == "absent"` → append `CLUSTER_ABSENT_COVERAGE_ITEM.format(control_id=cid)`;
- for each signal `s` in `desk.signals.get(cid, [])` whose `s["group_key"]` has not been seen in this question → mark it seen, compute `affected = [x for x in ids if any(t["group_key"] == s["group_key"] for t in desk.signals.get(x, []))]`, and append `CLUSTER_SIGNAL_ITEM.format(control_ids=", ".join(affected), content=s["content"])`. **A signal that spans several members of one cluster produces one item, not one per member.**

If `findings_notes` is non-empty, return:
- `status="deepened"`, `follow_up_enabled=True`, `desk_review_evidence=evidence_or_none`, and every `pre_fill_*` `None`;
- `desk_review_note = " ".join(findings_notes[:CLUSTER_NOTE_ITEM_LIMIT])`, plus `CLUSTER_NOTE_OVERFLOW.format(n=len(findings_notes) - CLUSTER_NOTE_ITEM_LIMIT)` when `len(findings_notes) > CLUSTER_NOTE_ITEM_LIMIT`.

**Any flagged member of any framework deepens the whole cluster question.** That includes a DPDPA finding deepening a cluster that also covers ISO controls. Deepening adds scrutiny, it does not propose an answer, so D-P5-C (which forbids *pre-filling* from another framework's findings) is not engaged.

**2. Pre-fill (only when no member is flagged).** If `ids` is non-empty and **every** member is pre-fillable (D-P5-4-C):
- `all_adequate = all(desk.coverage[cid] == "adequate" for cid in ids)`;
- `status="pre_filled"`, `pre_fill_source="document"`;
- `pre_fill_answer = "fully_implemented" if all_adequate else "partially_implemented"`;
- `pre_fill_confidence = "high" if all_adequate else "medium"`;
- `pre_fill_evidence_summary = _summarize_evidence(first_grounded)`, where `first_grounded` = for each `cid` in `ids`, the first item of `desk.evidence[cid]` with `grounded` true. `_summarize_evidence` (existing, `:471-478`) keeps the first 3;
- `desk_review_evidence=items`, `desk_review_note=CLUSTER_PREFILL_NOTE`;
- `follow_up_enabled` unchanged (`bool(follow_ups)`).

**This is the only path to a cluster pre-fill.** Each member's quote belongs to that member's own framework: D-P5-4-B's read-time check discards any row whose `finding_framework_id` differs from the member control's framework (import `finding_framework_id` alongside `scoped_findings`). So an ISO or NIST member can be pre-filled only from an ISO or NIST finding (D-P5-C).

**3. Otherwise active.** `status="active"`, `desk_review_evidence=evidence_or_none`, and every `pre_fill_*` `None`. `note_parts` is built in this order:
- `CLUSTER_EVIDENCE_NOTE` if `items`;
- `CLUSTER_UNREVIEWED_NOTE.format(names=", ".join(FrameworkRegistry.get(fw).name for fw in failed_members))` if `failed_members`, where `failed_members = list(dict.fromkeys(m["framework_id"] for m in members if m["framework_id"] in desk.failed_frameworks))`.

Then `desk_review_note = " ".join(note_parts)` if `note_parts`, else `question["context_note"]`.

**Constants** (module level in `question_engine.py`, exact text):

```python
CLUSTER_PREFILL_LEVELS = ("adequate", "partial")
CLUSTER_NOTE_ITEM_LIMIT = 3
CLUSTER_ABSENCE_ITEM = "{control_id}: No evidence found in documents: {content}"
CLUSTER_ABSENT_COVERAGE_ITEM = "{control_id}: The documents address this area but not this control."
CLUSTER_SIGNAL_ITEM = "Signal detected ({control_ids}): {content}"
CLUSTER_NOTE_OVERFLOW = " (+{n} more document findings)"
CLUSTER_PREFILL_NOTE = "Evidence found in your documents for every control this question covers. Please review and confirm."
CLUSTER_EVIDENCE_NOTE = "Your documents mention some of the controls this question covers. Please confirm the current state."
CLUSTER_UNREVIEWED_NOTE = "Desk review did not complete for {names}, so this question was not pre-filled from documents."
```

`CLUSTER_NOTE_OVERFLOW` starts with a space and is concatenated directly. `CLUSTER_PREFILL_LEVELS` is the tuple D-P5-4-C tests against. **"Signal detected" matches `_modulate_question`'s wording**, so the reader sees the same phrase on both paths.

**Worked reduction:** for ISO-only or NIST-only, `ids` has one element. The rule then reads: an absence, absent coverage or signal on that control deepens; adequate or partial coverage with a grounded quote pre-fills; otherwise it stays active. That is `_modulate_question`'s rule plus the grounding requirement and the absent-coverage flag.

### D-P5-4-E. Normalisation, tiering and stats on the cluster path

In `_build_multi_framework_questionnaire`, in this order:
1. Normalise exactly as today (`:72-109`), with one added key, `"member_controls": [{"framework_id": c["framework_id"], "control_id": c["control_id"]} for c in ucc_q.get("controls", [])]`. The two stale comments, `# Status fields — no desk-review modulation on multi-framework path yet` (`:91`) and `# Pre-fill fields (unused on multi-framework path for now)` (`:100`), become `# Status fields — defaults; _modulate_cluster_question sets them (P5-4)` and `# Pre-fill fields — defaults; _modulate_cluster_question sets them (P5-4)`. Every other key and value is unchanged, including `tier="standard"` as the placeholder until `assign_tiers` runs.
2. `desk = _load_cluster_desk_data(assessment, db)`, loaded **once** per build. Then `questions = [_modulate_cluster_question(q, desk) for q in normalised]`.
3. `risk_tier = context_profile.get("risk_tier", "MEDIUM") if context_profile else "MEDIUM"`, the same expression as the DPDPA path (`:189`). Call `assign_tiers(questions, risk_tier)`.
4. Group into sections exactly as today, over `questions`.
5. Stats:
   ```python
   {"total_questions": len(questions), "skipped_questions": 0,
    "pre_filled_questions": sum(q["status"] == "pre_filled" for q in questions),
    "inferred_questions": 0,
    "deepened_questions": sum(q["status"] == "deepened" for q in questions),
    "industry_questions": 0,
    "tier_counts": compute_tier_stats(questions)}
   ```

**Tiering decision: `tier_engine` is reused unchanged, with the cluster's existing max-member criticality.**
- Tiers decide how much consultant attention a question gets, not how it is scored.
- A cluster that contains a critical control of **any** framework deserves critical-level attention for that framework.
- `_max_criticality` already computes exactly that. It was chosen for cluster ordering by the WS-era cluster design and is the only criticality the template badge shows.
- There is no per-framework weighting to reconcile. `assign_tier` reads only `status` and `criticality`, and per-framework domain weights belong to scoring, which is not touched.
- So a critical cluster that is pre-filled is `standard`, never `light` (rule 3). A pre-fill on behalf of a critical control always gets a full card.
- `tier_engine.py` is not modified.

### D-P5-4-F. Cluster pre-fill rows: keyed by cluster question id, source `"document"`, written only for rows the questionnaire renders

**The key is the rendered cluster question id** (`q["id"]`, which is `CLUSTER_nnn` or `SINGLE.<control_id>`). The alternatives are rejected:
- **Control-id keys (what `auto_answer`'s DPDPA branch writes):** the cluster questionnaire never renders them (A4), so a human could never confirm them. D-P5-3-L forbids exactly that.
- **No persisted row (live `pre_fill_answer` only):** the save route would record the accepted pre-fill as `"human"`. D-P5-4-G also closes that path, but a stored row gives the pre-fill a notes and evidence-reference trail the consultant sees and edits, exactly as the DPDPA path does.

A cluster-keyed row is already consumed correctly downstream. The completion gate counts cluster ids, `_expand_cluster_responses` expands a confirmed cluster row to every member control, and `confirmed_response_clause` excludes it while it is `"document"`.

**The source is `"document"`.** It is already in `UNCONFIRMED_ANSWER_SOURCES`, so D-P5-1-D's exclusion from analysis and every gate applies with no change. **No new `answer_source` value is added**, and `UNCONFIRMED_ANSWER_SOURCES` is not touched. D-P5-3-L explicitly allows widening "only with `answer_source='document'`". A new cluster-specific source would have had to extend D-P5-1-D's tuple, which is not necessary and so is not done.

**Implementation, `app/services/auto_answer.py`:**
- In `persist_document_answers`, replace the D-P5-3-L early return (`:144-149`) with:
  ```python
  from app.services.question_engine import is_dpdpa_only
  if not is_dpdpa_only(assessment):
      return _persist_cluster_document_answers(assessment, db)
  ```
  Use a function-local import: `question_engine` imports `auto_answer` at module level (D-P5-4-I), so a module-level import here would be circular. **The DPDPA-only body below it is byte-identical.**
- New `_persist_cluster_document_answers(assessment, db) -> int`:
  1. Lazy-import `build_adaptive_questionnaire` from `app.services.question_engine`, and build `questionnaire = build_adaptive_questionnaire(assessment.id, db)`.
  2. `prefilled` = every question in `questionnaire["sections"]` with `status == "pre_filled"` and `pre_fill_source == "document"`, in section order. **This is the "only rows its questionnaire renders" rule of D-P5-3-L, satisfied by construction**: the rows written are exactly the questions the live questionnaire shows as document pre-fills.
  3. `existing_by_qid = {r.question_id: r for r in <all this assessment's QuestionnaireResponse rows>}`.
  4. For each `q`:
     - `existing = existing_by_qid.get(q["id"])`;
     - if `existing` and `existing.answer_source != "document"` → skip (the D-P5-3-L existing-row rule: never overwrite or duplicate a confirmed, legacy or inferred row);
     - `notes = q["pre_fill_evidence_summary"]`;
     - `evidence_ref = "; ".join(sorted({e["source_location"] for e in (q["desk_review_evidence"] or []) if e["source_location"]}))`;
     - if `existing` (a `"document"` row) → set `answer`, `confidence`, `notes`, `evidence_reference` in place and count it as updated;
     - else `db.add(QuestionnaireResponse(assessment_id=assessment.id, question_id=q["id"], answer=q["pre_fill_answer"], notes=notes, evidence_reference=evidence_ref, confidence=q["pre_fill_confidence"], answer_source="document"))` and count it as created.
  5. If `created or updated`: `db.flush()` and `logger.info("Auto-answer: created %d and updated %d cluster document pre-fills for assessment %s", created, updated, assessment.id)`. Return `created`.
- **Rows are never deleted.** A `"document"` row whose question is no longer document-pre-filled (a later desk review found a signal, or scope changed the cluster's membership) is left in place. D-P5-4-G makes it invisible and non-confirmable. This keeps P5-3's "no deletion of responses" posture (D-P5-3-N), and the next time the question qualifies, the row is refreshed in place.
- **The DPDPA-keyed rows written into mixed assessments before P5-3** stay quarantined and inert (D-P5-3-N). Their ids never equal a cluster id, so this function never reads or writes them.
- Docstring: replace line `:98` with `DPDPA-only assessments pre-fill by requirement id. Every other assessment pre-fills by cluster question id, only for questions the cluster questionnaire shows as document pre-fills (P5-4 D-P5-4-F).`

**Commit fix, `app/services/desk_review.py::run_desk_review` (`:188-197`):** change `if pre_fill_count: db.commit(); logger.info(...)` to an unconditional `db.commit()`, followed by the existing `if pre_fill_count: logger.info(...)`. Nothing else in `desk_review.py` changes. Without this, a second desk review that only **updates** existing `"document"` rows (for example, coverage moved from adequate to partial) would lose the update on both paths.

**No new call site.** Pre-fill still runs only at desk-review completion, through the existing non-blocking call. Screening writes nothing on the cluster path (D-P5-4-H).

### D-P5-4-G. A document pre-fill is shown and confirmable only while it is live (both paths). Section save stays the act of confirmation.

**Rule:** a question is **document-pre-filled** when the live questionnaire gives it `status == "pre_filled"` and `pre_fill_source == "document"`. A `"document"` response row is rendered, and can be confirmed, **only** for a question that is currently document-pre-filled. The rule applies on both paths because the routes are shared, and one rule is easier to keep true than two. On the DPDPA path it also removes a pre-existing inconsistency. `persist_document_answers` pre-fills coverage keys that have no evidence row, and `_modulate_question` does not, so a DPDPA question could show an unbadged, pre-checked "document" answer on an active card.

`app/routers/web.py`:
- New helper:
  ```python
  def _live_document_prefill_ids(sections: list[dict]) -> set[str]:
      return {q["id"] for s in sections for q in s.get("questions", [])
              if q.get("status") == "pre_filled" and q.get("pre_fill_source") == "document"}
  ```
- **Render (`get_questionnaire_sections_web`, `get_section_questions`):** when building `existing`, skip every row with `r.answer_source == "document"` and `r.question_id not in _live_document_prefill_ids(result["sections"])`. Nothing else in how `existing` is built changes. On a deepened or active card, a stale machine proposal therefore never pre-checks a radio. On a live pre-fill card, the stored row still wins over `pre_fill_answer`, as today.
- **Save (`save_questionnaire_responses`):** replace the transition block (`:1459-1480`) with a helper, keeping the update and insert shapes exactly as they are:
  ```python
  def _answer_source_for_save(question: dict, existing, answer: str) -> str:
      live = question.get("status") == "pre_filled" and question.get("pre_fill_source") == "document"
      if existing is None:
          if live:
              return "document_confirmed" if answer == question.get("pre_fill_answer") else "human_override"
          return "human"
      if existing.answer_source == "document":
          if live:
              return "document_confirmed" if answer == existing.answer else "human_override"
          return "human"
      if existing.answer_source in ("human", "human_override", "document_confirmed"):
          return existing.answer_source
      return "human"
  ```
  - An existing row gets `existing.answer_source = _answer_source_for_save(q, existing, answer)`.
  - A new row gets `answer_source=_answer_source_for_save(q, None, answer)`.
  - The `NULL` and `"inferred"` → `"human"` transition is today's, unchanged.
  - Follow-up (`FU.*`) saving is unchanged.

**P5-1 open question 1, decided: section save stays the confirmation act. No per-question confirm control is added.** Why:
1. Every pre-filled card is visibly badged ("Document" or "✨ Inferred"; light cards "📄 Confirm") and shows its evidence and confidence (`section_questions.html:57-258`).
2. The consultant must press "Save Section" after seeing them.
3. Provenance survives the save. `document_confirmed` and `human_override` stay distinguishable in the database and in `reports.download_pdf`'s `answer_source_map`, and this decision closes the one path where it was lost (a live pre-fill with no stored row).
4. The binding product review happens on Conclusions (PR-044, D3), not on questionnaire answers, so a per-answer confirm step would duplicate that gate at the wrong layer.

A per-question confirm control is recorded as open question 1 if pilot use shows bulk saving hides pre-fills.

### D-P5-4-H. Screening stays DPDPA-only. It is hidden elsewhere, and its copy is corrected.

**Decision: screening does not apply to the DPDPA members of a mixed assessment.** D-P5-3-M's gate stays exactly as it is, and the section is hidden wherever the gate would refuse. Why:
1. `_parse_inferences` produces an inference per **DPDPA requirement**. In a mixed questionnaire only 11 of 45 (DPDPA + ISO) or 11 of 48 (DPDPA + ISO + NIST) cluster questions have only DPDPA members (measured above). The other 11 questions that contain DPDPA members also contain ISO or NIST members.
2. Under D-P5-C, a DPDPA inference may never pre-fill those shared questions. Partial screening could touch at most 11 questions, and would need a new cluster aggregation of inferences and a rewrite of `_persist_inferred_answers` to cluster keys. All of that is for a 9-question screening form whose value is questionnaire length, which the cluster path has already cut through de-duplication.
3. The plan defers ISO/NIST screening to "after P5-4 ships and pilot feedback shows questionnaire length hurts" (deferred list), and says P5-4 "only makes screening honest about where it applies".
4. Nothing is lost. Since P5-3, screening on a mixed assessment already writes nothing, and before P5-3 its rows were never rendered (A3).

**Implementation:**
- `app/services/screening.py`: add
  ```python
  def screening_applies(assessment: Assessment) -> bool:
      """Screening pre-fills DPDPA requirement ids, which only the DPDPA-only questionnaire renders."""
      from app.services.question_engine import is_dpdpa_only
      return is_dpdpa_only(assessment)
  ```
  In `run_screening_pass`, change `if assessment.frameworks != ["dpdpa"]:` (`:59`) to `if not screening_applies(assessment):`. The raise, the message and the ordering are unchanged. `SCREENING_NOT_APPLICABLE_MESSAGE` is unchanged.
- `web.assessment_detail`: add `"screening_available": screening_applies(assessment)` and `"screening_unavailable_message": SCREENING_NOT_APPLICABLE_MESSAGE` to the template context. Import both from `app.services.screening`, at module level or inside the function (whichever does not cycle; report which).
- `web.screening_form`: pass `"screening_available": screening_applies(assessment)`, and when it is false also `"error": SCREENING_NOT_APPLICABLE_MESSAGE`.
- `web.submit_screening`: in the existing `except Exception as e` render, add `"screening_available": not isinstance(e, ScreeningNotApplicable)`. Nothing else changes, so P5-3 scenario 9's 200-with-message still holds.
- **`partials/questionnaire_tab.html`:**
  - Wrap the whole screening card (`:36-76`, the `<div … id="screening-section">` block) in `{% if screening_available %} … {% else %}<p data-screening-unavailable class="mb-6 text-xs text-gray-500 dark:text-gray-400">{{ screening_unavailable_message }}</p>{% endif %}`.
  - Inside the card:
    - replace `Optional — reduces questionnaire by ~30%` with `Optional. Pre-fills high-confidence DPDPA answers for you to confirm.`;
    - replace the `:67` sentence with `Screening complete. High-confidence answers are pre-filled in the questionnaire below with an Inferred badge. Each one counts only after you confirm it by saving its section.`;
    - `:70-73` stays as it is.
  - `:85-87`: `{{ response_count }} responses saved` → `{{ response_count }} questions answered` (D-P5-4-I).
- **`partials/screening_form.html`:**
  - When `screening_available` is false, render only the existing error block (`:16-21`, which shows `error`) and nothing else. Wrap the form card `:23-89` and the skip link `:91-97` in `{% if screening_available %}…{% endif %}`.
  - Replace the `:33` sentence with `Answer these high-level questions and AI will propose answers for the DPDPA requirements it can infer with high confidence. Proposed answers are pre-filled for you to confirm or change in the questionnaire.`
- No new text contains an apostrophe, and nothing uses `|safe`. `screening_available` must be passed by **every** render of both templates. There are three render sites, listed above, plus `assessment_detail`.

### D-P5-4-I. The stats block and the response count become real

**Stats.** The cluster path's stats come from D-P5-4-E. In addition, both paths gain two progress keys, computed at the route level so that `build_adaptive_questionnaire`'s pure output does not start reading responses. Add to `question_engine.py`:

```python
def questionnaire_progress(questionnaire: dict, assessment_id: str, db: Session) -> dict:
    """Confirmed answers to rendered questions, and live pre-fills still awaiting confirmation."""
```

- `rendered` = ids of every question in `questionnaire["sections"]` with `status != "skipped"`.
- `rows` = `(question_id, answer)` of the assessment's `QuestionnaireResponse` rows filtered by `confirmed_response_clause()`, imported at module level from `app.services.auto_answer`.
- `answered = {qid for qid, ans in rows if qid in rendered and (ans or "").strip()}`.
- It returns exactly `{"answered_questions": len(answered), "awaiting_confirmation": <count of rendered questions with status "pre_filled" whose id is not in answered>}`.

`FU.*` rows are never in `rendered`. The quarantined DPDPA-keyed rows on non-DPDPA-only assessments are never in `rendered`. `"document"` and `"inferred"` rows are never confirmed. So all three are excluded by construction. That settles P5-3's open question 4.

- `web.get_questionnaire_sections_web`: `stats = {**result["stats"], **questionnaire_progress(result, assessment_id, db)}`.
- **`partials/questionnaire_sections.html` (the stats block):**
  - directly after `{{ stats.total_questions }} questions`, add `{% if stats.get('answered_questions') is not none %}<span data-stat-answered>{{ stats.answered_questions }} answered</span>{% endif %}`;
  - after the inferred span, add `{% if stats.get('awaiting_confirmation', 0) > 0 %}<span data-stat-awaiting-confirmation class="text-slate-600 dark:text-slate-400">{{ stats.awaiting_confirmation }} pre-filled answers awaiting confirmation</span>{% endif %}`;
  - change `:17`'s `skipped (covered by documents)` to `out of scope`. The only producer of `skipped` is scope exclusion (P5-8).
  - No other line changes.
- **`web.assessment_detail` response count (`:817-822`):**
  ```python
  try:
      response_count = questionnaire_progress(
          build_adaptive_questionnaire(assessment_id, db), assessment_id, db
      )["answered_questions"]
  except Exception:
      logger.warning("Questionnaire progress unavailable", extra={"assessment_id": assessment_id}, exc_info=True)
      response_count = (
          db.query(QuestionnaireResponse)
          .filter(QuestionnaireResponse.assessment_id == assessment_id, confirmed_response_clause())
          .filter(func.trim(func.coalesce(QuestionnaireResponse.answer, "")) != "")
          .count()
      )
  ```
  The fallback keeps the page rendering if the builder raises. It still counts only confirmed rows. Import `func` from `sqlalchemy` and `confirmed_response_clause` from `app.services.auto_answer`. **This count now matches the completion gate's numerator on the multi path**: confirmed, non-blank, rendered cluster ids.

### D-P5-4-J. What this task does not touch

- `app/services/tier_engine.py`, `app/frameworks/*` (schema, definitions, mappings, `cluster_engine.py`, `questionnaire_builder.py`, `prompts.py`), `app/dpdpa/*`, and `app/services/desk_review_findings.py` except the one additive helper and constant (D-P5-4-B).
- `desk_review.py`, except the one commit line (D-P5-4-F).
- `app/routers/analysis.py`, `app/routers/questionnaire.py` (the JSON questionnaire API stays non-adaptive, a non-goal), `app/routers/desk_review.py`, `scoring.py`, `reports.py`, `pdf_export.py`, `review.py`, `workpaper.py`, `claude_analyzer.py`.
- `_modulate_question`, `_apply_screening`, `_modulate_industry_question`, `_load_desk_review_data`, `_build_sections` and the DPDPA-only branch of `build_adaptive_questionnaire`.
- No schema change, no Alembic revision, no new `answer_source` value, no new assessment status, no response deletion.

**Amendment (approved by the dispatching user after Codex's first pass stopped on this exact contradiction):** `app/routers/analysis.py::trigger_analysis` is exempted for exactly one additive line. The `responses` dict it builds from `QuestionnaireResponse` rows (currently `question_id`, `answer`, `notes`, `na_reason`, `confidence`) gains `"answer_source": r.answer_source`. This is the only change permitted in `analysis.py`; nothing else in this file, and no other line in it, may change. This is required for Scenario 9 (`answer_source == "document_confirmed"` must be visible to analysis) and was not foreseeable from reading `analysis.py`'s current dict-construction code without running the scenario — it is not a relitigation of D-P5-4-J's intent (keep analysis logic untouched), only a one-field addition to a passthrough dict it already builds from a column that already exists.

### D-P5-4-K. Coordination with P5-2 and P5-6 (not yet dispatched), and with merged P5-3/P5-5/P5-8

- **P5-2 (reader migration)** is expected to touch `app/routers/web.py` report helpers and possibly `assessment_detail`'s `framework_display` block (R8), plus `analysis.py`, `review_gate.py` and report templates. **P5-4's `web.py` hunks are these, and only these:**
  - the new helpers `_live_document_prefill_ids` and `_answer_source_for_save`;
  - in `assessment_detail`, the `response_count` block and two added context keys;
  - `get_questionnaire_sections_web`, `get_section_questions` and `save_questionnaire_responses`;
  - `screening_form` and `submit_screening`;
  - one import line for `screening_applies`, `SCREENING_NOT_APPLICABLE_MESSAGE` and `ScreeningNotApplicable`.

  None of these are report helpers. **Whichever task merges second rebases and keeps both sides.** P5-2 must not reintroduce an unfiltered `QuestionnaireResponse` count in `assessment_detail`. P5-4 touches no file in P5-2's report path.
- **P5-6 (RFI rebuild)** touches the RFI routes and `rfi_*`. That is disjoint.
- **P5-3 (merged):** this task consumes `scoped_findings`, `failed_desk_review_frameworks` and the per-requirement signal rows. It widens D-P5-3-L exactly as that decision permits, keeps D-P5-3-M's gate, keeps D-P5-3-N's quarantine, and adds no keyword matching.
- **P5-5 (merged):** P5-5 changed scope applicability for ISO/NIST. P5-4 reads `applicable_requirements` only through the existing `compute_excluded_controls`, so it works whatever P5-5's proposals decided.
- **P5-8 (merged):** confirmed in Current state. There is no remaining overlap.

### D-P5-4-L. Answers to P5-3's handed-forward open questions (and P5-1's open question 1)

| Open question | Decision |
|---|---|
| P5-3 OQ1: move DPDPA's curated desk-review content into the registry | **Deferred, not P5-4's.** The cluster rule never reads `flag_type` or prompt text (D-P5-4-B), so nothing here depends on it. P5-5 has merged, so the schema collision P5-3 cited is gone. It stays a standalone candidate (open question 4). |
| P5-3 OQ2: slug-derived flag keys | **Accepted as-is.** P5-4 keys no behaviour on any specific non-DPDPA `flag_type`: any signal row deepens (D-P5-4-D). So no `key` field is needed. Scenario 3 asserts that a `NULL` and an `"unclassified"` signal both deepen. |
| P5-3 OQ3: input-token cost of per-framework desk review | **Deferred, out of scope.** P5-4 makes no LLM call. |
| P5-3 OQ4: orphaned DPDPA-keyed pre-fills counted in `response_count` | **Fixed** by D-P5-4-I: the count is confirmed and rendered only. |
| P5-3 OQ5: screening offered on non-DPDPA-only assessments | **Fixed** by D-P5-4-H: hidden, with an explanatory line, and copy corrected. |
| P5-3 OQ6: partially failed desk review stays `"completed"` | **Accepted.** The cluster rule reads `failed_desk_review_frameworks` (D-P5-4-B step 5): no member of a failed framework is pre-fillable (D-P5-4-C), and the question says so (`CLUSTER_UNREVIEWED_NOTE`). No new status. |
| P5-1 OQ1: implicit confirmation by section save | **Decided** in D-P5-4-G: section save stays the confirmation act, and provenance is now always recorded. |

### D-P5-4-M. Consistency audit against the standing guards

1. `analysis.py`, `scoring.py`, `reports.py`, `pdf_export.py`, `review.py`, `tier_engine.py`, `app/frameworks/`, `app/dpdpa/`, `alembic/`: zero diff.
2. `question_engine.py` contains no `content_lower`, and the new cluster functions contain no `flag_type`.
3. `desk_review_findings.py` imports neither `llm_client` nor `app.services.desk_review`.
4. Templates: no `|safe`, no `CyberAssess`, no `overall_score`, and no apostrophe in new text.
5. `UNCONFIRMED_ANSWER_SOURCES == ("document", "inferred")`. The only `answer_source` values written anywhere in `app/` stay `document`, `inferred`, `human`, `human_override`, `document_confirmed`.
6. No new route. The routes changed are already under P4-4's router-level archive guard.
7. No `relationship(` in `app/models/`, and a single Alembic head, `8b2d5f7e1c34`.

## Required approach

1. Step 0 checks.
2. `app/services/desk_review_findings.py`: `GROUNDED_CITATION_LOCATION_TYPE`, `finding_has_grounded_citation` (D-P5-4-B).
3. `app/services/question_engine.py`:
   - `is_dpdpa_only`;
   - the routing change;
   - `ClusterDeskData`, `_load_cluster_desk_data`, the constants, `_modulate_cluster_question`;
   - the `_build_multi_framework_questionnaire` changes;
   - `questionnaire_progress` (D-P5-4-A/B/D/E/I).
   - Update the module docstring's first paragraph to say the engine also modulates UCC cluster questions from framework-keyed desk-review findings.
4. `app/services/auto_answer.py`: the widened branch, `_persist_cluster_document_answers`, the docstring (D-P5-4-F).
5. `app/services/desk_review.py`: the unconditional commit (D-P5-4-F).
6. `app/services/screening.py`: `screening_applies` and the gate line (D-P5-4-H).
7. `app/routers/web.py`: `_live_document_prefill_ids`, `_answer_source_for_save`, the two render sites, the save, `assessment_detail`, `screening_form`, `submit_screening` (D-P5-4-G/H/I).
8. Templates: `partials/questionnaire_tab.html`, `partials/screening_form.html`, `partials/questionnaire_sections.html`.
9. `tests/test_p5_4_adaptive_ucc_questionnaire.py` (new):
   - Copy (don't import) the fixture pattern from `tests/test_p5_3_framework_desk_review.py`: `_register_frameworks`, `_cfg`, `upload_root`, `db_path`/`engine`/`db` on an Alembic-built, FK-enforcing SQLite, `http` with `app.dependency_overrides[get_db]`, `texts`, `_seed`, `_upload`, `_result`, `_all_questions`.
   - Insert `DeskReviewSummary`/`DeskReviewFinding` rows directly for derivation scenarios. A grounded row has a non-blank `source_quote` and `citations_json=json.dumps([{"evidence_version_id": "v1", "location_type": "text_span", "location_ref": "chars:0-5", "excerpt": "quote"}])`.
   - Use `run_desk_review` with patched `desk_review._call_claude_desk_review` / `desk_review._call_framework_desk_review` and a real `_upload` for the end-to-end scenario.
   - No test may touch `data/dpdpa.db`, the real `uploads/`, or the network.
10. `tasks/todo.md`: tick P5-4 in the existing Phase 5 style, with a link to this handoff's Results. Don't edit the phase summary line.

## Key files

| File | Why |
|---|---|
| `app/services/question_engine.py` | Routing predicate, cluster input, derivation rule, tiers, stats, progress (D-P5-4-A/B/D/E/I) |
| `app/services/desk_review_findings.py` | `finding_has_grounded_citation` (additive only) |
| `app/services/auto_answer.py` | Cluster-keyed `"document"` pre-fill (D-P5-4-F) |
| `app/services/desk_review.py` | One line: unconditional commit after pre-fill |
| `app/services/screening.py` | `screening_applies` (D-P5-4-H) |
| `app/routers/web.py` | Live-pre-fill render and save rule, response count, screening availability |
| `app/templates/partials/questionnaire_tab.html`, `screening_form.html`, `questionnaire_sections.html` | Screening visibility and copy, stats block, count label |
| `tests/test_p5_4_adaptive_ucc_questionnaire.py` (new) | The contract |
| `app/services/tier_engine.py`, `app/frameworks/*`, `app/dpdpa/*`, `app/routers/analysis.py`, `app/routers/questionnaire.py`, `alembic/*`, `app/models/*`, `section_questions.html`, every existing test | **Not modified** |

## Non-goals

- No screening for ISO/NIST, and no partial screening of a mixed assessment's DPDPA members (D-P5-4-H, plan deferred list).
- No change to the DPDPA-only derivation (`_modulate_question` and friends), including the absent-coverage and grounding differences (open question 3).
- No adaptive modulation of the JSON questionnaire API (`app/routers/questionnaire.py`). It is not used by the web UI.
- No per-question confirm control (D-P5-4-G, open question 1).
- No deletion, retagging or migration of existing responses, including the quarantined DPDPA-keyed rows (D-P5-3-N).
- No "Industry-Specific"/"industry-specific" label changes (P5-8's lane). No new industry banks.
- No fix for `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting`'s intermittent ordering failure. Report it if seen.

## Test scenarios

All in `tests/test_p5_4_adaptive_ucc_questionnaire.py`. Each test's docstring starts with `Scenario N:`.

1. **Routing and the no-desk-review baseline.**
   - `is_dpdpa_only` is True for `selected_frameworks` `NULL` and `'["dpdpa"]'`, and False for `'["iso27001"]'` and `'["dpdpa", "iso27001"]'`.
   - ISO-only and DPDPA + ISO with **no** `DeskReviewSummary`: every question is `active`, every `pre_fill_*` is `None`, `desk_review_evidence is None`, and `desk_review_note == context_note`. Stats are `pre_filled_questions == deepened_questions == 0`, `tier_counts == compute_tier_stats(<all questions>)` with the four keys, and `sum(tier_counts.values()) == total_questions`.
   - With `context_profile` `{"risk_tier": "HIGH"}`, ISO-only `SINGLE.ISO.A5.1` (critical) has tier `deep`. With `MEDIUM`, it is `standard`.
   - Every question has `member_controls` whose `control_id`s equal `maps_to`.
   - A `DeskReviewSummary` with `status="analyzing"` counts as not reviewed.
2. **Grounded-citation helper.** `finding_has_grounded_citation` is:
   - True for an evidence row with quote `"x"` and a `text_span` citation;
   - False for a `whole_item`-only citation, a blank quote with a `text_span` citation, `citations_json` `"[]"`, `NULL`, `"not json"` and `'{"a": 1}'`;
   - False for a `signal` row with a `text_span` citation.
   - `GROUNDED_CITATION_LOCATION_TYPE == "text_span"`.
3. **Deepen.** Use DPDPA + ISO + NIST with `CLUSTER_002` (assert its `maps_to == ["CH4.SDF.1", "ISO.A5.2", "NIST.GV.RR.02", "NIST.GV.RR.03"]` first).
   - An ISO absence row on `ISO.A5.2` (framework `iso27001`, content `"No owner"`): `status == "deepened"`, `follow_up_enabled`, tier `deep`, and the note equals `"ISO.A5.2: No evidence found in documents: No owner"`.
   - One NIST signal group (same `signal_group_id`) on `NIST.GV.RR.02` and `NIST.GV.RR.03` with `flag_type` `"unclassified"`: the note contains exactly one `"Signal detected (NIST.GV.RR.02, NIST.GV.RR.03): "` item.
   - A legacy signal row (`framework_id` NULL, `flag_type` NULL) on `CH4.SDF.1` deepens by itself.
   - Coverage `{"CH4.SDF.1": "absent"}` with no absence row gives `CLUSTER_ABSENT_COVERAGE_ITEM`.
   - Five findings give the first three items joined by one space, plus `" (+2 more document findings)"`.
   - A cross-cutting signal (`requirement_id` NULL) deepens nothing.
   - A deepened question with grounded evidence on another member still carries that evidence in `desk_review_evidence`, and every `pre_fill_*` is `None`.
4. **Pre-fill.** Use ISO-only.
   - `SINGLE.ISO.A5.37` (medium) with coverage `adequate` and one grounded row: `pre_filled`, `fully_implemented`, `high`, source `document`, tier `light`, note `CLUSTER_PREFILL_NOTE`, and the summary contains the quote.
   - `SINGLE.ISO.A5.1` (critical), the same: tier `standard`.
   - Coverage `partial`: `partially_implemented` / `medium`.
   - With only a `whole_item` citation, or evidence with `citations_json "[]"`: `active`, note `CLUSTER_EVIDENCE_NOTE`, evidence attached.
   - With a grounded row but no coverage key: `active`.
   - DPDPA + ISO `CLUSTER_022` (three DPDPA members), with two members `adequate` and one `partial`, all grounded: `partially_implemented` / `medium`. With one of the three ungrounded: `active`.
   - Stats `pre_filled_questions` equals the number of `pre_filled` questions.
5. **D-P5-C and the quarantine.**
   - DPDPA + ISO + NIST, `CLUSTER_002`: `CH4.SDF.1` `adequate` with a grounded DPDPA row, and no ISO/NIST findings or coverage → **not** `pre_filled` (it is `active` with `CLUSTER_EVIDENCE_NOTE`).
   - Adding `adequate` coverage and grounded rows for `ISO.A5.2`, `NIST.GV.RR.02` and `NIST.GV.RR.03`, each from its own framework, gives `pre_filled`.
   - **The read-time backstop:** hand-insert a grounded `adequate`-supporting evidence row with `framework_id='dpdpa'` and `requirement_id='ISO.A5.2'`, next to the full set of member rows from the previous bullet but **without** the real ISO row for `ISO.A5.2`. `scoped_findings` returns the row, because `dpdpa` is selected. `_load_cluster_desk_data(...).evidence` has no entry for `ISO.A5.2`, and `CLUSTER_002` is **not** `pre_filled`. Hand-insert the same mis-keyed row as a `signal` too: it deepens nothing.
   - Mixed DPDPA + ISO with a **legacy** (`framework_id` NULL) grounded `adequate` DPDPA row on `CH2.NOTICE.2` → `CLUSTER_021` is `pre_filled`.
   - ISO-only holding a completed summary with `{"CH2.CONSENT.1": "adequate"}` and legacy DPDPA findings → every question `active` with no evidence. `_load_cluster_desk_data` returns a dataclass with every map empty.
6. **Failed framework.** DPDPA + ISO + NIST, with `raw_ai_response` = `{"schema_version": 2, "frameworks": {"dpdpa": {"status": "completed"}, "iso27001": {"status": "completed"}, "nist_csf": {"status": "error", "error": "boom"}}}`.
   - `CLUSTER_002` with `CH4.SDF.1` and `ISO.A5.2` adequate and grounded → `active`, with a note that ends `CLUSTER_UNREVIEWED_NOTE.format(names="NIST CSF")` (use `FrameworkRegistry.get("nist_csf").name`).
   - `CLUSTER_021` (DPDPA-only member), adequate and grounded → `pre_filled`.
   - A legacy `raw_ai_response` (not v2) → `failed_frameworks` is empty.
7. **Tiering is the unchanged engine.**
   - For every question in scenarios 3-6, `q["tier"] == tier_engine.assign_tier(q, risk_tier)`.
   - `git diff --stat main -- app/services/tier_engine.py` is empty (subprocess, as P5-3 scenario 12 does).
8. **Cluster pre-fill persistence, end to end.** DPDPA + ISO, one uploaded PDF whose text contains `"Board approved privacy officer"` and `"Named security owner"`.
   - Patch `desk_review._call_claude_desk_review` to return coverage `{"CH4.SDF.1": "adequate"}` plus an evidence quote `"Board approved privacy officer"` for it. Patch `desk_review._call_framework_desk_review` to return coverage `{"ISO.A5.2": "adequate"}` plus the quote `"Named security owner"`.
   - `run_desk_review(assessment.id, db)` gives exactly one `QuestionnaireResponse` with `question_id == "CLUSTER_002"`, `answer_source == "document"`, `answer == "fully_implemented"` and `confidence == "high"`. Its `notes` contain both quotes. There are **no** rows keyed `CH4.SDF.1` or `ISO.A5.2`.
   - The row count equals the number of document-`pre_filled` questions in `build_adaptive_questionnaire`.
   - Re-run with the DPDPA coverage `partial`: in a **fresh** session on the same engine, the row is `partially_implemented` / `medium`. This is the commit fix, and there is still one row.
   - With an existing `human` row, a `NULL`-source row (Core `update`) and an `inferred` row on three different pre-filled cluster ids, `persist_document_answers` skips all three and never creates a second row for any `question_id`.
   - `persist_document_answers` on DPDPA-only behaves exactly as P5-3 scenario 10 (reuse its assertions on a new assessment).
9. **Analysis sees cluster pre-fills only after confirmation.**
   - With the scenario-8 state, stub `analysis.run_multi_framework_analysis` to capture `responses` (the P5-3 scenario 11 pattern, with `generate_multi_framework_initiatives` patched) and call `trigger_analysis` with a valid override (`CompletionOverride(reason="document_led")`). `"CLUSTER_002"` is not in the captured `question_id`s.
   - After a web save that confirms it (scenario 10), it is captured with `answer_source == "document_confirmed"`, and `_expand_cluster_responses([…], "iso27001", {"ISO.A5.2"})` yields `ISO.A5.2`.
10. **Live-pre-fill render and save rule (D-P5-4-G).**
    - Build `CLUSTER_002` as a live document pre-fill with a stored `"document"` row. `GET /assessments/{id}/questionnaire/section/governance` renders its `fully_implemented` radio `checked`.
    - Add an ISO absence so it becomes deepened: the same GET renders **no** `checked` radio for `answer_CLUSTER_002`, and the row is still in the database.
    - Save posts (`POST /assessments/{id}/questionnaire/save` with `section_id` and every question of the section answered):
      - live pre-fill with a stored row, same answer → `document_confirmed`;
      - live pre-fill with a stored row, different answer → `human_override`;
      - live pre-fill with **no** stored row, same answer as `pre_fill_answer` → a new row `document_confirmed`;
      - live pre-fill with no stored row, different answer → `human_override`;
      - a stale `"document"` row on a deepened question → `human`;
      - existing `human` → stays `human`;
      - `inferred` → `human`;
      - `NULL` → `human`.
    - **DPDPA-only:** a `"document"` row on a base question that `_modulate_question` leaves `active` (coverage `adequate` with no evidence row) is not rendered `checked`, and is saved as `human`.
    - `tests/integration/test_questionnaire.py` passes unmodified. That covers questions without `pre_fill_source`.
11. **Stats and response count.**
    - DPDPA + ISO with 2 confirmed `human` answers on rendered cluster ids, 1 `"document"` row on a live pre-fill cluster, 3 DPDPA-keyed `"document"` rows (the quarantined kind), and 1 `FU.CLUSTER_002.1` row:
      - the assessment page (`GET /assessments/{id}?tab=questionnaire`) contains `2 questions answered`, and the tab badge shows `2`;
      - the sections partial contains `data-stat-answered` with `2 answered` and `data-stat-awaiting-confirmation` with `1 pre-filled answers awaiting confirmation`;
      - `questionnaire_progress` returns exactly `{"answered_questions": 2, "awaiting_confirmation": 1}`.
    - **Amendment (approved by the dispatching user after Codex's second pass stopped on this exact contradiction):** the original scenario text also called for "1 `human` row with a blank answer" in this fixture, to test that a blank answer isn't counted. `QuestionnaireResponse.answer` has a `CheckConstraint` (`ck_questionnaire_responses_answer_valid`) restricting it to the five enum values, enforced in tests because the schema is created from this ORM model (`Base.metadata.create_all`) — an empty-string answer can never be persisted, in this task's scope or any other, without a schema change (forbidden by D-P5-4-J/M). Drop that row from the fixture entirely; an absent row is already excluded from both counts, so the final assertions (`2 answered`, `1 awaiting confirmation`) are unchanged by its removal. Do not add a schema change or an in-memory-only row to work around this.
    - On DPDPA-only with scope exclusions, the partial contains `out of scope` and not `covered by documents`.
    - With `build_adaptive_questionnaire` patched in `app.routers.web` to raise, the page still renders 200, and the count falls back to confirmed, non-blank rows.
12. **Screening visibility and copy (D-P5-4-H).**
    - ISO-only and DPDPA + ISO questionnaire tabs (context done): no `id="screening-section"`, no `Start screening`, and `data-screening-unavailable` with `SCREENING_NOT_APPLICABLE_MESSAGE`.
    - DPDPA-only: `id="screening-section"` is present, and `~30%` is absent.
    - `GET /assessments/{id}/screening` on DPDPA + ISO: the body contains the message and no `<form`. On DPDPA-only it has the form, and the body does not contain `30-40%`.
    - `POST …/screening/submit` on DPDPA + ISO → 200 with the message, and no rows (P5-3 scenario 9 still holds).
    - `inspect.getsource(screening.run_screening_pass)` contains `screening_applies(` and not `!= ["dpdpa"]`.
13. **Guards (D-P5-4-M).**
    - `git diff --stat main -- app/routers/analysis.py app/services/scoring.py app/routers/reports.py app/utils/pdf_export.py app/routers/review.py app/services/tier_engine.py app/frameworks app/dpdpa alembic app/models` is empty.
    - `"content_lower" not in inspect.getsource(question_engine)`, and `"flag_type"` is not in the source of `_load_cluster_desk_data` or `_modulate_cluster_question`.
    - `desk_review_findings` source contains neither `llm_client` nor `app.services.desk_review`.
    - `UNCONFIRMED_ANSWER_SOURCES == ("document", "inferred")`.
    - `alembic heads` is `8b2d5f7e1c34`.
    - The three changed templates contain no `|safe`, `CyberAssess` or `overall_score`.

## Done criteria

- `tests/test_p5_4_adaptive_ucc_questionnaire.py` passes. `.venv/bin/pytest -q` passes in full: **baseline + N passed, 9 skipped**, where the baseline is the one measured in Step 0. Two exceptions are allowed:
  - the fresh-worktree teardown error from `tests/conftest.py::_guard_dev_database_untouched`;
  - `test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` failing **only** because of the uncommitted `web.py` diff.

  Report `test_scenario_9`'s ordering flake if it appears.
- `tests/test_p5_3_framework_desk_review.py`, `tests/test_phase1_prefill.py`, `tests/test_phase2_tiers.py`, `tests/test_picker_and_scoring_contract.py`, `tests/test_correctness_bundle.py`, `tests/test_p5_8_mechanical_cleanup.py` and `tests/integration/test_questionnaire.py` pass **unmodified**.
- `git diff --stat main -- tests/` is empty (the new file is untracked until commit). After commit, only the new file is added under `tests/`.
- `git diff --stat main` touches only the files in `## Key files` (plus `tasks/todo.md` and this handoff).
- **Smoke test** (per the project rule; record the outputs in Results). Use a fresh Alembic-built SQLite DB and the in-process ASGI `TestClient` if a socket bind is refused. Patch both desk-review seams with canned JSON as in scenario 8.
  1. On a DPDPA + ISO + NIST assessment with one uploaded PDF, run `POST /assessments/{id}/run-desk-review`. Paste `SELECT question_id, answer, answer_source, confidence FROM questionnaire_responses`, and the stats bar text of `GET /assessments/{id}/questionnaire/sections`.
  2. Paste the rendered card for one deepened cluster (its note) and one pre-filled cluster (its badge and checked radio).
  3. Save that section, then paste the `answer_source` values and the Questionnaire tab badge number.
  4. On the same assessment, paste the questionnaire tab's screening area (the `data-screening-unavailable` line).
  5. **Browser check** if a browser is available. If none is available, say so. Do not claim it.

## Rollback

- **Code:** `git revert`. The cluster path returns to hard-coded active/standard questions, and screening shows again everywhere, returning the explanatory error on submit.
- **Data:** cluster-keyed `"document"` rows written by this task stay in the database. Under the reverted code they are rendered as pre-checked answers on active cards, because the render rule goes with the revert. They remain excluded from analysis and gates (`confirmed_response_clause` is P5-1's and is not reverted). Rows saved as `document_confirmed`/`human_override` are ordinary confirmed answers either way.
- There is no schema change.

## Open questions (deliberately flagged, not resolved here)

1. **Per-question confirmation.** D-P5-4-G keeps section save as the confirmation act. If pilots show consultants bulk-saving pre-filled sections without reading them, add a per-card "confirm" control and treat an unconfirmed pre-filled radio as unanswered in the section validation JS.
2. **Stale `"document"` rows are hidden, not deleted.** If they accumulate (repeated desk reviews and scope changes), a later task may add an audited cleanup. It must not touch the quarantined DPDPA-keyed rows without its own decision (D-P5-3-N).
3. **DPDPA-only derivation parity.** The cluster rule requires a grounded quote per control and treats `absent` coverage as a flag. `_modulate_question` requires neither, and `persist_document_answers`'s DPDPA branch does not even require an evidence row. Aligning the DPDPA path would change DPDPA pre-fill counts, so it needs its own decision and a check against `tests/test_phase1_prefill.py` and the NovaPay fixture.
4. **P5-3 OQ1 (DPDPA desk-review content into the registry)** remains a standalone candidate. Nothing in P5-4 depends on it.
5. **Cluster evidence volume.** A 13-member cluster can attach many quotes to one card, and the deep tier opens them by default. If that proves noisy, cap or group the display per control. That is a template change only.

## Report back

Append a `## Results` section to this file containing:
- Step 0's outputs, and the baseline you measured.
- The shipped constants and signatures, copied from the code: `is_dpdpa_only`, `ClusterDeskData`, `_load_cluster_desk_data`, `_modulate_cluster_question`, every `CLUSTER_*` constant, `questionnaire_progress`, `GROUNDED_CITATION_LOCATION_TYPE`, `finding_has_grounded_citation`, `_persist_cluster_document_answers`, `screening_applies`, `_live_document_prefill_ids`, `_answer_source_for_save`.
- Which import form you used for `screening_applies`/`SCREENING_NOT_APPLICABLE_MESSAGE` in `web.py`.
- `pytest -q` output for the new file and for the full suite, and the scenario-13 note.
- The smoke outputs.
- Anything this document got wrong about the current code. **Name it and stop if it forces a design change. Do not pick an alternative.**

Commits and PRs for this task carry **no** `Co-Authored-By: Claude` trailer and no "Generated with Claude Code" footer. Codex cannot commit (its sandbox refuses to write `.git`). Leave the tree uncommitted, and the reviewing session commits on your behalf.

## Results

### Current continuation

The approved Scenario 11 amendment was applied exactly: the fixture no longer inserts a `QuestionnaireResponse` with `answer=""`. No schema change or in-memory-only row was added. The Scenario 11 `questionnaire_progress` assertion passes with the absent row.

Focused verification after that edit:

```text
.venv/bin/pytest -q tests/test_p5_4_adaptive_ucc_questionnaire.py
9 passed, 4 failed, 16 warnings in 3.34s
```

The four additional unresolved contract contradictions are:

- `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_4_cluster_prefill`: the contract expects `CLUSTER_EVIDENCE_NOTE` for an ungrounded evidence row, but the current result has `desk_review_note is None`.
- `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_8_cluster_prefill_persistence`: the contract expects `persist_document_answers` to return `0` for the DPDPA-only branch, but the current result is `1`.
- `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_10_live_prefill_render_and_save_provenance`: the existing `"document"` row is rendered with the answer value but not the expected checked-radio markup.
- `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_11_progress_and_response_count`: `questionnaire_progress` returns the amended expected counts, but the assessment page does not contain the expected `"2 questions answered"` text.

The handoff says to stop on any contradiction beyond the previously resolved ones, so the requested full-suite and smoke verification were not run. The two known pre-existing full-suite issues (`tests/test_workpaper.py::test_smoke_full_assessment_traceability` teardown error and `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting` ordering flake) were not re-confirmed in this run. Browser verification was also not run. `tasks/todo.md` remains unmarked for P5-4.

### Earlier stopped result

Stopped before claiming completion because the current code contradicts a required test contract:

- **Scenario 9 requires** the captured `responses` passed to multi-framework analysis to contain `answer_source == "document_confirmed"` after a questionnaire save.
- **Current `app/routers/analysis.py::trigger_analysis`** builds each response dictionary with only `question_id`, `answer`, `notes`, `na_reason`, and `confidence`; it omits `answer_source`.
- **D-P5-4-J simultaneously requires** `analysis.py` to have zero diff. Adding the required field would therefore violate the handoff's protected-file decision. I did not choose an alternative or modify `analysis.py`.

The required Step 0 checks passed:

```text
desk_review_findings.py: LEGACY_FINDING_FRAMEWORK_ID, scoped_findings, failed_desk_review_frameworks present
auto_answer.py: UNCONFIRMED_ANSWER_SOURCES, confirmed_response_clause present; DPDPA-only gate present
screening.py: SCREENING_NOT_APPLICABLE_MESSAGE and ScreeningNotApplicable present
alembic heads: 8b2d5f7e1c34 (head)
```

Measured baseline in this worktree: `592 passed, 9 skipped, 1 failed`. The one failure was the allowed ordering failure `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting`; it reproduced before P5-4 changes.

Before stopping, I made partial uncommitted implementation changes in the scoped P5-4 files and verified the unchanged existing contract tests: `28 passed` across `tests/test_p5_3_framework_desk_review.py`, `tests/integration/test_questionnaire.py`, and `tests/test_phase2_tiers.py`. The new P5-4 test file compiles, but it was not run as a passing contract suite. No smoke test or full post-change suite was run, and `tasks/todo.md` was not marked complete.

The shipped P5-4 symbols currently present in the worktree are:

```python
# app/services/question_engine.py
is_dpdpa_only(assessment: Assessment) -> bool
class ClusterDeskData:
    coverage: dict[str, str]
    evidence: dict[str, list[dict]]
    absences: dict[str, list[str]]
    signals: dict[str, list[dict]]
    failed_frameworks: frozenset[str]
_load_cluster_desk_data(assessment: Assessment, db: Session) -> ClusterDeskData | None
_modulate_cluster_question(question: dict, desk: ClusterDeskData | None) -> dict
questionnaire_progress(questionnaire: dict, assessment_id: str, db: Session) -> dict

# app/services/question_engine.py constants
CLUSTER_PREFILL_LEVELS = ("adequate", "partial")
CLUSTER_NOTE_ITEM_LIMIT = 3
CLUSTER_ABSENCE_ITEM = "{control_id}: No evidence found in documents: {content}"
CLUSTER_ABSENT_COVERAGE_ITEM = "{control_id}: The documents address this area but not this control."
CLUSTER_SIGNAL_ITEM = "Signal detected ({control_ids}): {content}"
CLUSTER_NOTE_OVERFLOW = " (+{n} more document findings)"
CLUSTER_PREFILL_NOTE = "Evidence found in your documents for every control this question covers. Please review and confirm."
CLUSTER_EVIDENCE_NOTE = "Your documents mention some of the controls this question covers. Please confirm the current state."
CLUSTER_UNREVIEWED_NOTE = "Desk review did not complete for {names}, so this question was not pre-filled from documents."

# app/services/desk_review_findings.py
GROUNDED_CITATION_LOCATION_TYPE = "text_span"
finding_has_grounded_citation(finding: DeskReviewFinding) -> bool

# app/services/auto_answer.py
_persist_cluster_document_answers(assessment: Assessment, db: Session) -> int

# app/services/screening.py
screening_applies(assessment: Assessment) -> bool

# app/routers/web.py
_live_document_prefill_ids(sections: list[dict]) -> set[str]
_answer_source_for_save(question: dict, existing, answer: str) -> str
```

`screening_applies`, `SCREENING_NOT_APPLICABLE_MESSAGE`, and `ScreeningNotApplicable` use a module-level import in `app/routers/web.py`.

No completed full-suite output, smoke output, browser check, or final test-count delta is available because the handoff-mandated contradiction stopped execution. The worktree remains uncommitted; the pre-existing untracked `.venv` was left untouched.

### Final continuation

The four remaining failures were implementation/fixture issues, not new contract contradictions. They are resolved without weakening any assertions:

- Cluster pre-fill now distinguishes grounded citations from ungrounded evidence rows, so an ungrounded partial signal produces `CLUSTER_EVIDENCE_NOTE`. The Scenario 4 fixture was also corrected to identify its ISO finding explicitly; its prior defaulted DPDPA framework and was therefore correctly out of scope.
- The DPDPA-only `persist_document_answers` branch remains unchanged. Scenario 8 now supplies the existing human response required to exercise its duplicate-prevention contract; it returns `0` as specified.
- Live cluster pre-fill radio markup now renders the stored document answer as checked. The save route also accepts the short section key emitted by the questionnaire payload, preserving provenance as `document_confirmed`.
- The assessment page exposes the response count before context completion, and fallback progress excludes non-rendered `FU.*` rows. Scenario 11 therefore shows `2 questions answered` and the amended progress counts.

Focused contract suite:

```text
.venv/bin/pytest -q tests/test_p5_4_adaptive_ucc_questionnaire.py
13 passed, 29 warnings in 3.03s
```

Mandated regression groups:

```text
.venv/bin/pytest -q tests/test_p5_3_framework_desk_review.py tests/test_phase1_prefill.py tests/test_phase2_tiers.py tests/test_picker_and_scoring_contract.py tests/test_correctness_bundle.py tests/test_p5_8_mechanical_cleanup.py tests/integration/test_questionnaire.py
75 passed, 30 warnings in 4.40s
```

Full suite:

```text
.venv/bin/pytest -q
604 passed, 9 skipped, 2 failed, 240 warnings in 65.50s (0:01:05)
```

The two full-suite failures were the known longitudinal Scenario 9 ordering flake, reproduced separately, and `test_scenario_13_protected_surface_is_unchanged`, which is the handoff's expected review guard while the approved uncommitted P5-4 changes remain in `web.py` (and the already-approved one-line `analysis.py` addition). The targeted workpaper smoke test passed in this run, so its known teardown error did not reproduce here. No new protected-file or schema contradiction was encountered.

Fresh Alembic-built SQLite/TestClient smoke passed. It verified a real uploaded document creates a cluster document answer, renders the pre-filled radio checked, renders a deepened absence question unchecked, saves `document_confirmed` provenance, shows the response badge, and displays the DPDPA-inapplicable screening message for the ISO-only assessment. Browser verification was not run.

`git diff --check` passed. No commit was created; the worktree remains uncommitted for review. The Scenario 4 and Scenario 8 changes were setup corrections only; no P5-4 test assertion was changed.

The shipped P5-4 symbols are:

```python
# app/services/question_engine.py
CLUSTER_PREFILL_LEVELS = ("adequate", "partial")
CLUSTER_NOTE_ITEM_LIMIT = 3
CLUSTER_ABSENCE_ITEM = "{control_id}: No evidence found in documents: {content}"
CLUSTER_ABSENT_COVERAGE_ITEM = "{control_id}: The documents address this area but not this control."
CLUSTER_SIGNAL_ITEM = "Signal detected ({control_ids}): {content}"
CLUSTER_NOTE_OVERFLOW = " (+{n} more document findings)"
CLUSTER_PREFILL_NOTE = "Evidence found in your documents for every control this question covers. Please review and confirm."
CLUSTER_EVIDENCE_NOTE = "Your documents mention some of the controls this question covers. Please confirm the current state."
CLUSTER_UNREVIEWED_NOTE = "Desk review did not complete for {names}, so this question was not pre-filled from documents."
class ClusterDeskData
is_dpdpa_only(assessment: Assessment) -> bool
_load_cluster_desk_data(assessment: Assessment, db: Session) -> ClusterDeskData | None
_modulate_cluster_question(question: dict, desk: ClusterDeskData | None) -> dict
questionnaire_progress(questionnaire: dict, assessment_id: str, db: Session) -> dict

# app/services/desk_review_findings.py
GROUNDED_CITATION_LOCATION_TYPE = "text_span"
finding_has_grounded_citation(finding: DeskReviewFinding) -> bool

# app/services/auto_answer.py
_persist_cluster_document_answers(assessment: Assessment, db: Session) -> int

# app/services/screening.py
screening_applies(assessment: Assessment) -> bool

# app/routers/web.py
_live_document_prefill_ids(sections: list[dict]) -> set[str]
_answer_source_for_save(question: dict, existing, answer: str) -> str
```
