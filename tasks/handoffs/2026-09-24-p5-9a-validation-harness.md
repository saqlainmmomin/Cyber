# P5-9a: Validation harness. Company-pack schemas, a question-pack export, a deterministic evidence renderer, pack lint, a route-driven live runner and a Conclusion-based scorer, so four blind synthetic companies can be pushed through the real product and measured against a hidden answer key

**Plan:** `docs/plans/2026-09-24-002-p5-9-end-to-end-validation-plan.md`. This is Stage B. Read the plan's decisions **D-P5-9-A to D-P5-9-J** first. They are fixed, and this handoff implements them.
**Owner:** Codex, run by Saqlain directly. The spec pins every file, schema field, CLI flag and test scenario. There is no open design question left for the implementer (`tasks/agent-ownership.md`, criteria "Mechanical", "Fully spec-able" and "Contained").
**Depends on:** nothing. Written against `main` at `d69aa71`. **Blocks:** Stage A's questionnaire answers (they need Part 1's export), the Stage C baseline run, and P5-9b.
**Runs in parallel with:** every other P5 task. P5-9a changes **no file under `app/`, `alembic/` or `templates/`** and no existing test. Its file set is disjoint from every other task (D-P5-9a-A), so it can't conflict with any other task.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, schema field, CLI flag, file path and test scenario below.

## Step 0 (Codex, before any edit)

```bash
git switch -c codex/p5-9a-validation-harness main
.venv/bin/pytest -q                                  # record the baseline pass/skip count in Results
grep -n "^ENABLED_ASSESSMENT_FRAMEWORKS" app/routers/web.py
grep -n "def build_adaptive_questionnaire" app/services/question_engine.py
grep -n "^def call_llm" app/services/llm_client.py
grep -n "def _create_hierarchy\|def _upload_assessment_document\|def _map(" scripts/seed_test_companies.py
```

Confirm that all four greps hit. Record the baseline suite count. If `ENABLED_ASSESSMENT_FRAMEWORKS` is not `("dpdpa", "iso27001", "nist_csf")`, stop and report.

## Goal

1. A **company pack** format with a strict schema. It keeps what the client hands over (`client_visible/`) physically separate from the hidden answer key (`answer_key.json`).
2. `export_question_pack`: for a pack's framework selection, it dumps the tool's own intake questions (context, scope, screening) and, once intake answers exist, the rendered questionnaire, with question ids. The authoring model then answers by real ids.
3. `render_evidence`: it turns structured evidence specs into PDF, DOCX, PNG or JPG files **deterministically**. The same spec gives byte-identical output. Optional deterministic "scan" degradation.
4. `lint_pack`: schema validity, registry-valid control ids, leak lint, structural fairness (every key fact is verbatim in client-visible material) and the image-generation rule.
5. `run_company`: drives one pack through the **real routes** with the **live LLM** in an isolated database. It records a full transcript, LLM usage, desk review output, follow-ups, Conclusions, scores and format probes. It never reads the answer key.
6. `score` and `report`: a deterministic score of a run directory against the answer key, then a per-company and cross-run summary in markdown and JSON.
7. A tiny synthetic `_example` pack and a mocked-LLM test suite that proves the whole chain works without network.

## Current state (read, don't change)

- **Route-driven seeding already exists.** `scripts/seed_test_companies.py` (P4-2) drives the app with `fastapi.testclient.TestClient`. It uses `_create_hierarchy` (`POST /engagements`, form fields `client_mode, company_name, industry, company_size, engagement_name, engagement_type, description, selected_frameworks`), `_upload_assessment_document` (`POST /api/assessments/{id}/documents`, multipart `category` + `file`, 201) and `_map` (`POST /api/evidence/{evidence_id}/uses`, JSON `assessment_id, framework_id, requirement_id, relevance`, 201). P4-2 **mocks** `run_multi_framework_analysis`. P5-9a must not mock anything in live mode. **Do not import from or modify `seed_test_companies.py`.** Copy the patterns you need.
- **Database and uploads.** `app/config.py` `Settings.database_url` (default `sqlite:///data/dpdpa.db`) and `upload_dir` (default `uploads`) come from the environment (`DATABASE_URL`, `UPLOAD_DIR`) through pydantic-settings. `app/database.py` builds the engine **at import time**. `app/main.py`'s lifespan runs `alembic upgrade head` on startup, which the `TestClient` context manager triggers. Consequence: the runner must set both env vars **before importing anything from `app`**.
- **Routes the runner uses** (relocate by symbol if lines drift):
  - Context: `POST /assessments/{id}/context/save` (`web.save_context_answers`). Form keys are the question ids from `app/dpdpa/context_questions.CONTEXT_BLOCKS`. A `multi_select` question submits the key repeated. It calls the LLM (`derive_risk_profile`).
  - Scope: `POST /assessments/{id}/scope/save` (`web.save_scope`). Form keys are each selected framework's `FrameworkDefinition.scope_questions[*].id`. 303 on success.
  - Screening, DPDPA-only assessments only: `POST /assessments/{id}/screening/submit`. Form keys are `app.services.screening.get_domain_coverage()[*]["id"]`. LLM.
  - Consultant upload: `POST /api/assessments/{id}/documents`, 201. `category` must be a `DocumentCategory` value (`app/schemas/assessment.py:27`).
  - Magic link: `POST /engagements/{engagement_id}/magic-links` (form `items` newline-separated, plus `expires_in_days`, `max_uploads`, `max_total_mb`). The new URL appears **only in the rendered HTML** (`new_link_url`, `/magic/<token>`). Parse it. `GET /magic/{token}` renders the item keys. `POST /magic/{token}` takes multipart `item_key` + `file` and requires `Content-Length`. Magic-link evidence counts toward analysis only once mapped (`evidence.analysis_documents`), so map it with `POST /api/evidence/{id}/uses`.
  - Desk review: `POST /api/assessments/{id}/desk-review` (synchronous JSON: `status, finding_count, failed_frameworks, message`). `GET` on the same path returns findings.
  - Questionnaire read: `app.services.question_engine.build_adaptive_questionnaire(assessment_id, db)` (read-only; returns `{"sections": [{"section_id", "questions": [{"id", "status", ...}]}]}`). Write: `POST /assessments/{id}/questionnaire/save` (form `section_id`, and per question `answer_<qid>`, `notes_<qid>`, `evidence_<qid>`). Valid answers are `ANSWER_OPTIONS` (`fully_implemented, partially_implemented, planned, not_implemented, not_applicable`). The route records provenance itself (`document` → `document_confirmed` / `human_override`).
  - Follow-ups: `POST /assessments/{id}/questionnaire/followup` (form `question_id`, `answer`), returns HTML. LLM.
  - Analysis: `POST /api/assessments/{id}/analyze` (synchronous; body is an optional `CompletionOverride{reason, reviewer_name}`). **The runner never sends an override** (D-P5-9a-F).
- **Where outcomes live.** `app/models/conclusion.py::Conclusion` (`assessment_id, framework_id, requirement_id, cluster_id, outcome, rationale, evidence_summary, gaps_identified, risk_level, recommended_action, ai_proposed, version`). `ConclusionRevision.citations_json` + `analysis_run_id`. `AnalysisRun(framework_id, status, model_id, started_at, completed_at, ...)`. Outcome vocabulary (`app/services/analysis_pipeline.py:53-63`): `compliant, partially_compliant, non_compliant, not_applicable, insufficient_evidence`. Resolve citations with the existing helpers (`app/services/citations.py`: `loads_citations` / `resolve_citations`). Read their signatures; don't reimplement them.
- **LLM seam.** Every call goes through `app.services.llm_client.call_llm(...)`. A passive wrapper that records then delegates is allowed in live mode (D-P5-9a-G).
- **Formats.** `detect_file_type` (`app/services/document_processor.py:222`) returns `pdf`, `docx` or an image extension (`png`, `jpg`, `jpeg`, `webp`). Anything else, including `txt`, is rejected at upload. Rendering targets are therefore `pdf | docx | png | jpg` only.
- **Existing validation assets.** `scripts/score_test_results.py` and `scripts/test_ground_truth.json` (three v2 companies, `GapItem`-based). **Leave both untouched.** P5-9a builds a separate scorer.
- **Available libraries.** `python-docx`, `fpdf2` (Pillow comes with it) and `pdfplumber` are already in `requirements.txt`. **Add no dependency to `requirements.txt`.**

## Decisions

### D-P5-9a-A. File set (complete; nothing else changes except as listed)

```
scripts/validation/__init__.py
scripts/validation/models.py              # pydantic schemas (D-P5-9a-B)
scripts/validation/paths.py               # pack/run path helpers, the client_visible allow-list
scripts/validation/export_question_pack.py
scripts/validation/render_evidence.py
scripts/validation/lint_pack.py
scripts/validation/run_company.py
scripts/validation/score.py
scripts/validation/report.py
scripts/validation/fonts/DejaVuSans.ttf, DejaVuSansMono.ttf   # vendored, license file alongside
validation/README.md                      # how to author, lint, render, run, score; the held-out rule (D-P5-9-C)
validation/companies/_example/...          # tiny pack used by tests (D-P5-9a-J)
tests/test_validation_harness.py
.gitignore                                # add: validation/runs/  and  validation/companies/*/rendered/
tasks/todo.md                             # tick P5-9a after merge only (D-P5-9a-K)
```

`scripts/validation/` is a package run as `python -m scripts.validation.<module>`. Check that `scripts/` is importable as a package (add an empty `scripts/__init__.py` only if one is needed and none exists, and record that in Results).

### D-P5-9a-B. Pack layout and schemas (`models.py`, pydantic v2, `extra="forbid"` everywhere)

```
validation/companies/<slug>/
  company.json                 # CompanyMeta (client-visible)
  client_visible/
    intake_answers.json        # IntakeAnswers
    questionnaire_answers.json # QuestionnaireAnswers   (authored after the questionnaire export)
    evidence/<artifact_id>.json# EvidenceSpec, one per artifact
    images/<file>              # realism-only external images (optional)
  answer_key.json              # AnswerKey  (HIDDEN; only lint_pack and score may open it)
  question_pack.intake.json    # written by export (stage intake)
  question_pack.questionnaire.json  # written by export (stage questionnaire)
  rendered/                    # written by render_evidence (git-ignored)
```

**CompanyMeta:** `slug` (`^[a-z0-9-]+$`), `company_name`, `industry` (must be a valid `Industry` enum value, `app/schemas/assessment.py`), `company_size` (a valid `CompanySize` enum value, `app/schemas/assessment.py`), `engagement_name`, `description`, `frameworks: list[Literal["dpdpa","iso27001","nist_csf"]]` (non-empty, no duplicates).

**IntakeAnswers:** `context: dict[str, str | list[str]]` (keys are `CONTEXT_BLOCKS` question ids), `scope: dict[str, str]` (keys are scope question ids of the selected frameworks), `screening: dict[str, str] | None` (required when `frameworks == ["dpdpa"]`, forbidden otherwise), `magic_link_items: list[str]` (the consultant's evidence request titles; may be empty).

**QuestionnaireAnswers:** `answers: dict[str, AnswerEntry]` keyed by questionnaire question id, where `AnswerEntry = {answer: <ANSWER_OPTIONS value>, notes: str = "", evidence_reference: str = ""}`.

**EvidenceSpec:**
- `artifact_id` (`^E\d{2}$`), `filename` (the extension must match `render.format`), `category` (a `DocumentCategory` value), `channel: Literal["consultant_upload","magic_link"]`, `magic_item: str | None` (required when `channel == "magic_link"`, and must equal one of `intake.magic_link_items`), `consultant_maps_to: list[{framework_id, requirement_id}]` (required and non-empty for `magic_link`; this is the consultant's topical mapping, not answer-key data).
- `render: {kind: Literal["prose","table","config","console","external_image"], format: Literal["pdf","docx","png","jpg"], degrade: Literal["none","scan_light","scan_heavy"] = "none"}`.
- Content, exactly one group matching `kind`:
  - `prose`: `title, subtitle, sections: [{heading, paragraphs: [str]}]`
  - `table`: `title, subtitle, preamble: [str], columns: [str], rows: [[str]], footer: [str]` (every row has `len(columns)` cells)
  - `config` / `console`: `title, lines: [str]`
  - `external_image`: `image_path` (relative to `client_visible/images/`), `transcript: str` (the text the image shows; used only by lint for leak checks)
- Allowed `kind`×`format`: prose → pdf, docx; table → pdf, docx, png; config → pdf, png; console → png, jpg; external_image → png, jpg. Anything else is a validation error. `degrade != "none"` is allowed only with `png`/`jpg`.

**AnswerKey:**
- `schema_version: Literal[1]`, `company_slug`
- `control_truth: dict[framework_id, {default: Outcome, overrides: dict[requirement_id, Outcome]}]`, where `Outcome` is the five-value Conclusion vocabulary
- `planted_gaps: list[PlantedGap]`, `decoys: list[Decoy]`, `clean_controls: list[{framework_id, requirement_id, supporting_artifacts: list[artifact_id]}]`
- `authoring_notes: str`

**PlantedGap:**
- `gap_id` (`^G\d{2}$`)
- `requirements: list[{framework_id, requirement_id}]` (non-empty)
- `gap_class`: one of `honest_gap, overclaim, cross_document, chained_dependency, temporal, quantitative, wrong_citation, joint_impossibility, substance_over_form, cross_framework_divergence, artifact_discrepancy, stale_evidence, scope_coverage`
- `actual_status: Literal["non_compliant","partially_compliant"]`, `surface_answer`: an `ANSWER_OPTIONS` value
- `probing_depth: 1..5`, `severity_expected: Literal["high","medium","low"]`, `description`
- `evidence_trail: list[{source: str, locator: str, fact: str}]` (non-empty). `source` is `evidence:<artifact_id>`, `answer:<question_id>`, `context:<question_id>` or `scope:<question_id>`.
- `key_facts: list[str]` (1-4 short verbatim strings), `what_followup_should_ask: str`

**Decoy:** `decoy_id` (`^D\d{2}$`), `requirements`, `why_it_looks_like_a_gap`, `why_it_is_compliant`, `evidence_trail`.

Cross-object rules, validated in `models.py` and re-run by lint:
- every planted-gap and decoy requirement has the matching `control_truth` override (gap → its `actual_status`, decoy → `compliant`);
- `clean_controls` and decoy requirements resolve to `compliant`;
- no requirement is both a gap and a decoy.

### D-P5-9a-C. `export_question_pack` (a temporary database, never the working one)

`python -m scripts.validation.export_question_pack <slug> --stage intake|questionnaire`

- Creates a temporary directory. Sets `DATABASE_URL=sqlite:///<tmp>/export.db` and `UPLOAD_DIR=<tmp>/uploads` **before** importing `app`. Opens `TestClient(app)` (runs migrations) and creates the hierarchy through `POST /engagements` from `company.json`.
- `--stage intake` writes `question_pack.intake.json`:
  - `context`: every `CONTEXT_BLOCKS` question (`id, text, type, options`)
  - `scope`: per selected framework, `{framework_id: [{id, text, options, help_text}]}`
  - `screening`: `get_domain_coverage()` when `frameworks == ["dpdpa"]`, else `null`
  - `document_categories`: the `DocumentCategory` values
  - `controls`: per selected framework, every registry control as `{requirement_id, title, category/domain, description}`. Use whichever of these fields the `FrameworkDefinition` control objects actually carry, and record the real field names in Results. The authoring model needs this catalogue to write the answer key with valid ids. For ISO, emit only what the registry holds (reference text; D4 applies and nothing is added).
  - `magic_link_limits`: the form defaults (7 days, 20 uploads, 100 MB), so the author sizes magic-link item lists sensibly
- `--stage questionnaire` requires `client_visible/intake_answers.json`. It submits scope answers through `POST /scope/save`. It writes context answers **directly on the `Assessment` row** (`context_answers` JSON, the same shape `save_context_answers` stores) instead of calling the route, because the route makes an LLM call. This is the one allowed direct write, it happens only in the throwaway export database, and it's documented in the module docstring. Then it calls `build_adaptive_questionnaire` and writes `question_pack.questionnaire.json`: `sections: [{section_id, title, questions: [{id, cluster_id?, text, status, member_controls?: [{framework_id, requirement_id}], guidance?}]}]`. Copy the fields the builder actually returns; don't invent them. Record the real keys in Results. Questions with `status == "skipped"` are included and marked, and the authoring brief tells the author not to answer them.
- No LLM calls in either stage. The test asserts this by making `call_llm` raise (scenario 3).

### D-P5-9a-D. `render_evidence` (deterministic)

`python -m scripts.validation.render_evidence <slug>` writes `rendered/<filename>` for every spec, plus `rendered/manifest.json` (`filename → {sha256, artifact_id, text}`, where `text` is the exact visible text the renderer drew, used by lint and score).

- DOCX: `python-docx`. Headings and paragraphs, tables with a header row. Set `core_properties` created, modified, author and title to fixed values derived from the spec (the author is the company name), so the bytes don't depend on the clock.
- PDF: `fpdf2` with the vendored DejaVu fonts (Unicode-safe, so `₹` and `–` render). Set `creation_date` to a fixed value, and `set_creator` / `set_producer` to fixed strings. Tables use `fpdf2`'s table API, with multiple pages when needed.
- PNG/JPG: Pillow. `table` draws a spreadsheet-like grid. `config` draws monospaced lines. `console` draws a dark-theme terminal or admin-console frame with the lines inside. Fixed canvas width 1600 px, height grown to fit, DejaVu fonts, no antialiasing randomness. JPG quality 90 for `none`.
- Degradation applies to `png`/`jpg` formats only. `degrade != "none"` on a `pdf`/`docx` spec is a schema error. `scan_light`: grayscale, rotate 0.8° (white fill), per-pixel noise σ=6 drawn from `random.Random(int(sha256(artifact_id), 16))` (pure Pillow and stdlib, no numpy), saved as JPG quality 70 even when the format is png: keep the `.png` extension and container, and apply the JPG round-trip in memory first. `scan_heavy`: the same with rotate 2.2°, σ=14, contrast 0.8 and JPG quality 45. Seeded, so output is byte-identical across runs.
- `external_image`: copied as is. Its `text` in the manifest is the spec's `transcript`.
- Determinism contract: running twice gives identical `sha256` for every file (scenario 4).

### D-P5-9a-E. `lint_pack` (exit 1 on any error; warnings don't fail)

`python -m scripts.validation.lint_pack <slug> [--require-questionnaire]` checks, in order:

1. **Schema.** Every file parses with its model. The `models.py` cross-object rules hold.
2. **Registry ids.** Every `framework_id`/`requirement_id` in the answer key, `consultant_maps_to` and `control_truth` exists in `app.frameworks.registry.FrameworkRegistry` for a framework in `company.frameworks`.
3. **Question ids.** With `--require-questionnaire`, every `questionnaire_answers` key exists in `question_pack.questionnaire.json` and isn't `skipped`. Every non-skipped question has an answer (missing ones are **errors**). Every `answer:<qid>` trail source exists. Every `context:`/`scope:` trail source exists in the intake pack.
4. **Trail artifacts.** Every `evidence:<artifact_id>` trail source and every `supporting_artifacts` entry is an existing spec. **No trail may reference an `external_image` artifact** (D-P5-9-D).
5. **Structural fairness.** Each `key_facts` string of each gap appears verbatim in the client-visible text of at least one of that gap's trail sources. Compare case-insensitively after collapsing whitespace. For `evidence:` sources the text is the rendered manifest's `text`. For `answer:` it's `notes` + `evidence_reference`. For `context:`/`scope:` it's the answer value. Rendering must have run first. If `rendered/manifest.json` is missing or stale (a spec's sha has changed), that's an error.
6. **Leak lint** over all client-visible text: rendered manifest text, filenames, intake answers, questionnaire answers and magic item titles.
   - (a) Case-insensitive denylist: `answer key`, `ground truth`, `planted`, `decoy`, `hidden gap`, `test company`, `validation pack`, `seeded gap`.
   - (b) Regex `\b[GD]\d{2}\b`.
   - (c) Any 8-word shingle, lowercased and with punctuation stripped, shared between client-visible text and the answer key's `description`, `why_it_looks_like_a_gap`, `why_it_is_compliant` or `authoring_notes`.
   - Each hit is an error naming the file and the offending text.
7. **Coverage warnings, not errors.** Gap, decoy and clean-control counts outside the plan's matrix range for the company's `slug` prefix (`c1-` … `c4-`). A `gap_class` taxonomy with fewer than 5 distinct classes, for `c2-`, `c3-` and `c4-` packs.

### D-P5-9a-F. `run_company` (live by default; never reads the answer key)

`python -m scripts.validation.run_company <slug> [--runs N=1] [--stop-after STAGE] [--followups] [--llm live|mock] [--out validation/runs/<UTC timestamp>]`

- **Blinding is structural.** `paths.py` exposes `client_visible_files(slug)`, which returns only `company.json`, files under `client_visible/`, the question packs and `rendered/`. The runner loads inputs **only** through it. `run_company.py` must not contain the string `answer_key` (scenario 6 checks the source text).
- **Preconditions.** `lint_pack <slug> --require-questionnaire` passes (import and call it, and abort on errors). For `--llm live`, `OPENROUTER_KEY` is set.
- **Per run `k`:** directory `<out>/<slug>/run-<k>/`. A fresh `DATABASE_URL=sqlite:///<dir>/app.db`, `UPLOAD_DIR=<dir>/uploads`. Import `app` inside a **subprocess per run** (`python -m scripts.validation.run_company --_child ...`), because the engine is bound at import time and each run needs a fresh one. The parent only orchestrates.
- **Stages, in order.** Each stage appends to `transcript.jsonl` (`{ts, stage, method, path, status, elapsed_ms, note}`, where response bodies are truncated to 2 KB) and to `stages.json` (`{stage, ok, elapsed_s, detail}`). The stage names are the `--stop-after` values:
  1. `hierarchy`: `POST /engagements`. Resolve the ids from the database read-only.
  2. `context`: `POST /context/save` with `intake.context`.
  3. `scope`: `POST /scope/save` with `intake.scope`.
  4. `evidence`: for each spec with `channel == consultant_upload`, `POST /api/assessments/{id}/documents` with `rendered/<filename>` and its MIME type. If `magic_link_items` isn't empty, create one link with all items, parse the token, `GET` the page to learn each item key, and `POST` each `magic_link` spec's file under its item. Then map each magic upload with `POST /api/evidence/{id}/uses` for every `consultant_maps_to` entry, relevance `"primary"` (check that the `relevance` vocabulary allows it, and record the actual value). A non-2xx upload is a recorded stage failure, and the run continues.
  5. `format_probes`: upload three tiny probe files (`probe-access-review.xlsx` from `openpyxl` **if installed, else skipped with a note**, `probe-users.csv`, `probe-router.conf`) through the consultant route. Record `{format, status_code, detail}` in `probes.json`. **Then archive any probe that was accepted**, so it can't reach analysis: use the evidence lifecycle transition route (`POST /api/evidence/{id}/transitions`; read the service for the "archived" transition name). If it can't be archived, record that and delete nothing.
  6. `desk_review`: `POST /api/assessments/{id}/desk-review`. Save the `GET` output to `desk_review.json`.
  7. `screening` (only when `frameworks == ["dpdpa"]`): `POST /screening/submit` with `intake.screening`.
  8. `questionnaire`: call `build_adaptive_questionnaire` (read-only). For every section, submit one `POST /questionnaire/save` with every non-skipped rendered question that has an answer in the sheet. Write `questionnaire_coverage.json`: `rendered_ids`, `answered`, `rendered_without_answer`, `answer_without_render`, `prefilled_before_save` (rows with `answer_source` in `document`/`inferred` before saving, read-only), and `provenance_after_save` (count by `answer_source`).
  9. `followups` (only with `--followups`): for each answered question whose answer isn't `fully_implemented`, `POST /questionnaire/followup` and store the stripped text per question id in `followups.json`. Also record whether any follow-up input is persisted anywhere analysis reads. Answer by reading the route and templates, and state that answer in Results. Don't answer follow-ups.
  10. `analysis`: `POST /api/assessments/{id}/analyze` with **no** override. If it doesn't return 200, record the status and body, and the run ends here with `stages.json` saying so (the scorer handles a missing analysis).
  11. `collect`: read-only dump to `conclusions.json`. Every `Conclusion` for the assessment, with the latest `ConclusionRevision`'s resolved citations (each citation carries the evidence filename) and `analysis_run_id`, all `AnalysisRun` rows, and `GapReport.framework_scores` if present.
- **LLM tap (D-P5-9-E allows this).** In the child process, in live mode, wrap `app.services.llm_client.call_llm` with a function that calls the original unchanged and appends `{ts, tier, model, input_tokens, output_tokens, cache_read_input_tokens, elapsed_ms, ok}` to `llm_usage.jsonl`. Patch every module that imported it by name as well. Find them with `grep -rn "from app.services.llm_client import" app` and list them in Results. The wrapper must pass through all arguments and return values, and re-raise any exception.
- **`--llm mock`** replaces `call_llm` with a deterministic stub from `scripts/validation/run_company.py::MockLLM`. For each call it returns the minimal valid JSON the calling site needs. Recognise the site by `tier` and a marker in the prompt, and reuse the shapes from `tests/support/analyzer_mock.py` where they fit. It's used only by tests and `--llm mock` smoke runs. The summary of a mock run is stamped `MOCK`.
- **Errors.** Any stage exception is caught, recorded in `stages.json` with its traceback, and ends that run. Other runs and companies continue. Exit code is 0 when every run reached `collect`, else 2.

### D-P5-9a-G. `score` (deterministic, reads the answer key)

`python -m scripts.validation.score <run_dir>...` writes `score.json` beside each run's `conclusions.json`.

- Outcome for a requirement is the **current** `Conclusion.outcome` for `(framework_id, requirement_id)`. A missing Conclusion is `missing`.
- Distance table (`truth → tool`):

| truth \ tool | non_compliant | partially_compliant | insufficient_evidence | compliant | not_applicable | missing |
|---|---|---|---|---|---|---|
| non_compliant | 1.0 | 0.5 | 0.3 | 0 | 0 | 0 |
| partially_compliant | 0.7 | 1.0 | 0.3 | 0 | 0 | 0 |

- **Per gap:**
  - `req_scores`; `gap_score = mean(req_scores)`; `caught = max(req_scores) >= 0.7`;
  - `grounded`: for requirements scoring ≥ 0.7, whether any citation's filename is the filename of an `evidence:` trail artifact; `null` if the gap has no evidence trail;
  - `key_fact_recall`: share of `key_facts` found (normalised as in lint) in that gap's requirements' `rationale + gaps_identified + evidence_summary`;
  - `severity`: 1 / 0.5 / 0 for exact / adjacent / opposite `risk_level` vs `severity_expected`, over requirements scoring ≥ 0.7; `null` if none.
- **Per decoy:** `false_positive = any requirement outcome in {non_compliant, partially_compliant}`. **Per clean control:** the same.
- **Coverage:** applicable requirements come from `Assessment.applicable_requirements` when set, else every control of the selected frameworks. Report the count with a Conclusion, `missing` ids, and failed `AnalysisRun` framework ids.
- **Background agreement:** over applicable requirements that aren't in any gap, decoy or clean control, the share whose tool outcome equals `control_truth` (override, else default).
- **Aggregates:** `catch_rate` (overall, by `gap_class`, by `probing_depth`), `mean_gap_score`, `grounding_rate`, `mean_key_fact_recall`, `mean_severity`, `decoy_fp_rate`, `clean_fp_rate`, `background_agreement`.
- **Cost:** sums from `llm_usage.jsonl` by tier and model, plus wall time per stage from `stages.json`.

### D-P5-9a-H. `report` (cross-run, cross-company)

`python -m scripts.validation.report <out_dir>` writes `<out_dir>/summary.json` and `<out_dir>/summary.md`.

- **Stamp:** `BASELINE` only if every run was live **and** `--baseline` was passed; otherwise `SMOKE` (or `MOCK`). Add the git SHA and dirty flag, the `app/config.py` model ids, and the date.
- **Per company:** the headline pair table (catch rate | decoy FP | clean FP), the per-gap-class table, per-gap rows (`gap_id, class, depth, caught k/N, mean gap_score, grounded, key facts`), decoy rows, stability (per-requirement modal agreement, and the list of requirements whose outcome changed across runs), coverage, questionnaire coverage diffs, format probes and cost.
- **Cross-company totals.**
- A "defects to file" section. It lists mechanically detectable problems only: a non-2xx stage, a failed framework, `rendered_without_answer` not empty, `answer_without_render` not empty, a probe rejected, missing Conclusions. It never lists "missed gap" as a defect. Detection quality is a metric, not a bug.
- **Don't print answer-key descriptions in `summary.md`.** Print ids, classes and scores only, so the summary can be shared without exposing the held-out set. `summary.json` may include them.

### D-P5-9a-I. What P5-9a doesn't do

- No consultant approval, edits, release, snapshots or PDF. That's P5-9b, after P5-2.
- No UI screenshots. That's P5-9b.
- No app code changes, even for a defect the run reveals. It's recorded, not fixed.
- No real company packs. `_example` only. The four real packs come from Stage A.

### D-P5-9a-J. The `_example` pack (a test fixture, not a real company)

Slug `c0-example`. Its `frameworks` is `["iso27001"]`, which gives the smallest cluster questionnaire without screening. Three artifacts: one `prose` docx, one `table` png, one `config` pdf. Two planted gaps: one `artifact_discrepancy` carried by the table, one `quantitative` whose trail joins the prose doc and a questionnaire answer. One decoy and two clean controls. Answers for every non-skipped question: generate the answer sheet from the exported pack in the test setup, mostly `fully_implemented`, and commit the result. Keep all text short. It must pass `lint_pack --require-questionnaire` cleanly.

### D-P5-9a-K. Docs

- `validation/README.md`: the pack layout, the command sequence (export intake → author intake → export questionnaire → author answers → render → lint → run → score → report), and the **held-out rule verbatim** from D-P5-9-C.
- `CLAUDE.md` (held-out gotcha) and `tasks/todo.md` (the P5-9 line) were already updated when this handoff was written. After merge, tick the P5-9a sub-item in `tasks/todo.md`. Change neither file otherwise.

## Test scenarios (`tests/test_validation_harness.py`, all network-free)

Every scenario is required. You may add cases, not drop or weaken them.

1. **Schema rejects bad packs.** A table row with the wrong cell count, a `prose`+`png` combination, a magic-link spec without `magic_item`, a gap requirement without its `control_truth` override, and a requirement that's both gap and decoy. Each raises a `ValidationError` naming the field.
2. **Registry ids.** An answer key with `CH2.CONSENT.1` in an ISO-only pack fails lint. A made-up `ISO.A.9.99` fails lint.
3. **Export uses no LLM and a throwaway database.** Patch `app.services.llm_client.call_llm` to raise. Both export stages succeed for `_example`. The working `DATABASE_URL` file (if any) has the same mtime and size before and after.
4. **Render is deterministic.** Render `_example` twice into two directories. Every file's sha256 is equal, and each `manifest.json` `text` equals what the spec says. A `scan_heavy` png is byte-identical across two renders.
5. **Lint catches unfairness and leaks.** Mutate a copy of `_example` (in `tmp_path`):
   - (a) remove a key fact from the table → fairness error;
   - (b) put "decoy" in a filename → leak error;
   - (c) copy an 8-word run from a gap description into a prose paragraph → leak error;
   - (d) point a gap trail at an `external_image` artifact → error;
   - (e) delete one questionnaire answer → error under `--require-questionnaire`.
   - The clean `_example` passes with zero errors.
6. **Runner blinding.** The source text of `run_company.py` doesn't contain `answer_key`. With `builtins.open` and `Path.read_text` wrapped to record paths, a mock run of `_example` never opens `answer_key.json`.
7. **Mock end-to-end.** `run_company c0-example --llm mock --runs 2` exits 0. Each run directory has `transcript.jsonl`, `stages.json` (every stage `ok` except `followups`, which is absent without the flag), `conclusions.json` with one Conclusion per applicable ISO control, `questionnaire_coverage.json` with empty `answer_without_render`, and `probes.json` with three entries. The two runs' databases are different files.
8. **Scorer arithmetic.** On a hand-built `conclusions.json`, check that:
   - truth `non_compliant` vs `partially_compliant` gives 0.5 and isn't caught; vs `non_compliant` gives 1.0 and is caught;
   - a gap with requirements scoring [0.3, 1.0] has `gap_score` 0.65 and is caught;
   - a decoy proposed `partially_compliant` is a false positive;
   - a citation filename matching a trail artifact sets `grounded` true;
   - key-fact recall counts a case- and whitespace-varied match.
9. **Report stamping and sharing.** Mock runs are stamped `MOCK`. `summary.md` contains no text from any answer-key `description` / `why_*` field. `--baseline` on a mock run is refused with a clear error.
10. **App untouched.** `git diff --name-only main -- app alembic app/templates requirements.txt` is empty. Assert this with `subprocess` and skip if not in a git checkout.
11. **Existing suite.** `.venv/bin/pytest -q` pass count equals the Step 0 baseline plus the new tests. There are no new skips outside this file.

## Verification (run before reporting done)

```bash
.venv/bin/python -m scripts.validation.export_question_pack c0-example --stage intake
.venv/bin/python -m scripts.validation.export_question_pack c0-example --stage questionnaire
.venv/bin/python -m scripts.validation.render_evidence c0-example
.venv/bin/python -m scripts.validation.lint_pack c0-example --require-questionnaire
.venv/bin/python -m scripts.validation.run_company c0-example --llm mock --runs 2 --out validation/runs/verify
.venv/bin/python -m scripts.validation.score validation/runs/verify/c0-example/run-*
.venv/bin/python -m scripts.validation.report validation/runs/verify
.venv/bin/pytest -q
git diff --stat main
```

Optional, if `OPENROUTER_KEY` is set: `run_company c0-example --runs 1` live, and paste the `summary.md` headline table into Results. Label it SMOKE.

## Report back

Append `## Results` to this file with:
- the baseline and final suite counts;
- the real key names `build_adaptive_questionnaire` returns;
- the `relevance` and archive-transition vocabulary you used;
- the list of modules patched by the LLM tap;
- the follow-up persistence finding (D-P5-9a-F stage 9);
- the format probe results from the mock run;
- the verification output;
- anything in this spec the code forced you to deviate from (and where you stopped).

Commit on `codex/p5-9a-validation-harness` with the message `P5-9a: validation harness (packs, export, render, lint, runner, scorer, report)`.

## Results

- Baseline: **593 passed, 9 skipped**. Harness tests: **9 passed**. The final full suite reached **601 passed, 1 failed, 9 skipped**: existing `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting` failed its integrated-report assessment ordering assertion twice in the full suite; the isolated test passed. Kept this handoff's scope and left app code and existing tests untouched.
- `build_adaptive_questionnaire` returns root keys `sections`, `stats`. Sections use `section_id`, `chapter_title`, `section_title`, `source`, `questions`. The exercised ISO question objects use `id`, `cluster_id`, `question`, `guidance`, `criticality`, `chapter`, `chapter_title`, `section`, `section_title`, `section_ref`, `frameworks_covered`, `follow_ups`, `status`, `skip_reason`, `desk_review_note`, `desk_review_evidence`, `tier`, `source`, `follow_up_enabled`, `maps_to`, `pre_fill_answer`, `pre_fill_confidence`, `pre_fill_source`, `pre_fill_evidence_summary`, `skip_if`, `relevance_weight`, `context_note`, `answer_options`.
- Evidence vocabulary: `relevance` allows `primary`, `supporting`, `contextual`; the magic-link mapping uses `primary`. Evidence archive target is `archived`. No format probe was accepted, so the archive route was not exercised in the mock run.
- LLM tap wraps `app.services.llm_client.call_llm`. `claude_analyzer`, `context_profiler`, `desk_review`, `document_processor`, `followup_engine`, `rfi_generator`, and `screening` call it dynamically. No module directly imports it by name (`rg "from app.services.llm_client import" app` returned no matches), so no other patches were needed.
- Follow-up generation returns questions in HTML. The save route persists submitted `followup_FU.*` fields as `QuestionnaireResponse` rows, but the runner does not answer or submit those fields, and the analysis path reads no generated follow-up response. The runner records this as `persisted_or_sent_to_analysis: false`.
- Both mock runs completed every stage and collected **93/93 Conclusions**; questionnaire coverage was **93/93**, provenance `human: 93`. Each probe file had three entries: XLSX skipped because `openpyxl` is absent; CSV and `.conf` received HTTP 400 as unsupported file types. None was accepted.
- Verification: both question-pack exports succeeded; render produced three artifacts; lint reported **0 errors, 0 warnings**; two-run mock runner, scorer, and report succeeded and stamped the summary `MOCK`. Determinism tests passed after normalizing DOCX ZIP timestamps. Full-suite outcome and existing failure are recorded above. No live baseline was run because P5-2/P5-4 are prerequisites.
- Claude's PR #47 review found the questionnaire exporter omitted `maps_to` from its cluster-to-control mapping. The exporter now resolves those requirement ids against the selected framework registries and emits the documented `{framework_id, requirement_id}` `member_controls`; the C2-C4 questionnaire packs were re-exported.
- Claude's independent Stage A5 audit found three C1 gap-class labels inconsistent with their evidence trails. G04 and G13 are now `overclaim`; G08 is now `cross_document`. The evidence content and hidden answer-key boundary are unchanged.
- The renderer now preserves scan-light/heavy JPEG quality for JPG outputs, and the app-untouched test compares against `merge-base HEAD main` so stale local `main` refs do not create false positives.
- No application code was changed. The unrelated Stage A handoff file already present in the working tree was not changed or staged. `tasks/todo.md` records Stage A complete after the independent audit and re-lint.
