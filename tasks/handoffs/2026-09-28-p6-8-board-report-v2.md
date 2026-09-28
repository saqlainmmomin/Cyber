# P6-8: Board report v2 (WeasyPrint + Noto), standalone Workpaper, DOCX/XLSX `[AR: report correctness + write-once]`

P6-8 moves the client board report onto the rendering stack approved in D-P6-H. The report becomes Jinja2 HTML rendered to PDF by WeasyPrint with vendored Noto fonts, which closes D0 #3 (Devanagari and ₹) for the new report. The reviewer's Workpaper becomes one self-contained HTML file that opens offline. Consultants and client teams get editable DOCX and XLSX files derived from a frozen report version.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`: Track 2 P6-8, Part D (D0 #3, D2, D3, D4) and Part F (**D-P6-H**: HTML → PDF with WeasyPrint; fpdf2 reports are frozen, then retired at parity). Related decisions: **D-P6-F** (narrative only from approved Findings; that is P6-10), **D-P6-G** (period and cut-off on every deliverable, shipped in P6-6). House rules: only approved Conclusions feed client outputs; deterministic fields (risk, priority, score) never come from the LLM; framework-specific copy is conditional; existing PDF sections are additive-only; snapshots are write-once.
**Owner:** Claude designs (this file + contract tests) → Codex implements → Claude runs an adversarial review (`[AR]`, checkpoints below) → PR. Per `tasks/agent-ownership.md`, Phase 6 row "P6-6..P6-10 Deliverables".
**Branch / worktree:** `claude/p6-8-board-report-v2` in `/Users/saqlainmomin/dpdpa-gap-tool-p6-8`, from `origin/main` @ `db3fdc8`. The designer's commit sits on top of it.
**Depends on:** P6-6 (report basis, sign-off, conditional copy helpers; merged #73), P5-6 (document-sidecar snapshot pattern; merged #46). **Blocks:** P6-9 (SoA, cross-framework roadmap and prior-period comparison go into this report), P6-10 (narrative slot), P6-7b (RFI add; it touches `report_snapshots.py` after this). **Runs in parallel with:** P6-7a (requirement card and review queue). The two share no source file (see "File overlap").

> **The contract tests are already written. They are the contract.** `tests/test_p6_8_board_report_v2.py` has 14 tests. On `db3fdc8` plus the designer's commit, 13 fail and 1 passes. Scenario 14, the file-set guard, must stay green. The 13 fail only because code is missing: a `ModuleNotFoundError` for `app.utils.html_pdf`, `app.services.board_report` or `app.services.standalone_workpaper`, or, in scenario 12, the workflow has no apt step yet. Make all 14 pass **without editing that file**. Do not weaken, skip, `xfail`, re-parametrize or delete any test. If you believe a test is wrong, leave it failing and explain in `## Results` which assertion is wrong, why, and what it should be. Put extra tests in `tests/test_p6_8_extra.py`.
>
> The designer checked the file against a throwaway reference implementation of this spec. It is not in the repo, so implement from this spec, not from memory of it.
> - **Contract tests.** With WeasyPrint 70.0, all 14 passed three runs in a row.
> - **Mutations.** 15 targeted mutations were tried and 14 were caught:
>   - font CSS HTML-escaped
>   - a `<link>` added to the Workpaper
>   - release gate removed
>   - fetcher allows every URL
>   - top risks not ranked by severity
>   - `weasyprint` imported at module import
>   - issue skips the sidecar check
>   - file route re-renders the board report
>   - company name placed inside CSS
>   - readiness note made unconditional
>   - rejected evidence in the register
>   - edited rows keep AI citations
>   - out-of-scope Conclusions in the register
>   - CI stops requiring the renderer
>
>   The one miss removed `font-family` from `@page`. Margin boxes still inherited Noto from the root, so it was not a defect.
> - **Full suite.** With the reference, the existing-test edits in D-P6-8-L and the guard excludes, all committed: **1072 passed, 10 skipped, 0 failed**.
> - **Without WeasyPrint.** In the repo's current `.venv`, which has no WeasyPrint, the four renderer tests skip with a clear reason and 10 pass. With `CYBERASSESS_REQUIRE_WEASYPRINT=1` those four fail instead.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, and to every name, signature, constant, route, snapshot type, metadata key, document key and rendered string below.

> **Answer-key independence (D-P5-9-C).** Do not open, grep, glob, list or read any of these:
> - anything under `validation/`
> - `tasks/handoffs/*p5-9*`
> - `docs/plans/2026-09-24-002-*`
> - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`, `scripts/validation/**`
> - `tests/test_validation_harness.py`
> - any `answer_key.json`
>
> Scope every search to explicit paths (`grep -rn ... app/ tests/test_p6_8_*.py`), never a bare repo-root search.

> **Codex cannot write `.git` and has no network.** No `git add`, `commit`, `branch` or `stash`. Read-only git is fine, and the guards use it. No `pip install`, no downloads. The orchestrator pre-steps below put the fonts and packages in place before Codex starts, and the orchestrator commits afterwards.

## Orchestrator pre-steps (before launching Codex)

Run from `/Users/saqlainmomin/dpdpa-gap-tool-p6-8`, after `git pull --ff-only` so that the designer's commit is present.

1. **System libraries (macOS).** `brew install pango`. On 2026-09-28 Homebrew already had pango 1.57.1, cairo 1.18.4 and harfbuzz 14.2.0. WeasyPrint 70.0 loaded them with no `DYLD_*` variables.
2. **Python package, into the shared `.venv`** (a symlink to `/Users/saqlainmomin/dpdpa-gap-tool/.venv`; the change is additive and safe for every worktree):
   `.venv/bin/pip install weasyprint==70.0`
   This pulls cffi, cssselect2, fonttools, Pillow, pydyf, Pyphen, tinycss2 and tinyhtml5. `fonttools` is already present through fpdf2.
   Check it: `.venv/bin/python -c "import weasyprint; print(weasyprint.__version__); weasyprint.HTML(string='<p>ok ₹</p>').write_pdf()"`
3. **Fonts (vendored, OFL 1.1).** Download the two release zips and extract the **unhinted** TTFs and each licence into `app/assets/fonts/noto/`:
   ```bash
   mkdir -p app/assets/fonts/noto /tmp/noto && cd /tmp/noto
   curl -sSLO https://github.com/notofonts/latin-greek-cyrillic/releases/download/NotoSans-v2.015/NotoSans-v2.015.zip
   curl -sSLO https://github.com/notofonts/devanagari/releases/download/NotoSansDevanagari-v2.007/NotoSansDevanagari-v2.007.zip
   unzip -o -j NotoSans-v2.015.zip NotoSans/unhinted/ttf/NotoSans-Regular.ttf NotoSans/unhinted/ttf/NotoSans-Bold.ttf OFL.txt -d latin
   unzip -o -j NotoSansDevanagari-v2.007.zip NotoSansDevanagari/unhinted/ttf/NotoSansDevanagari-Regular.ttf NotoSansDevanagari/unhinted/ttf/NotoSansDevanagari-Bold.ttf OFL.txt -d deva
   cd /Users/saqlainmomin/dpdpa-gap-tool-p6-8
   cp /tmp/noto/latin/NotoSans-*.ttf /tmp/noto/deva/NotoSansDevanagari-*.ttf app/assets/fonts/noto/
   cp /tmp/noto/latin/OFL.txt app/assets/fonts/noto/OFL-NotoSans.txt
   cp /tmp/noto/deva/OFL.txt app/assets/fonts/noto/OFL-NotoSansDevanagari.txt
   shasum -a 256 app/assets/fonts/noto/*
   ```
   The hashes must be exactly these (scenario 1 pins the four fonts):
   ```
   f3961a9cde016d41a4879aecda1474d3a36d6bf54fa0e4643de029cc2248b0e8  NotoSans-Regular.ttf            (431,364 B)
   87cb2d84472a7d66da659ee47b6cdb9552326e8c128245231f191b6ac72529d9  NotoSans-Bold.ttf               (432,376 B)
   9c7d935139ea6a1e6ad9dbac4f6d27ece1e04bca8123c8888d00a0f9df4724cd  NotoSansDevanagari-Regular.ttf  (184,228 B)
   ff2f76a23aad41e0608c2d7dbc4bacd247ff3bec78f0ec2a8fb106b561636e58  NotoSansDevanagari-Bold.ttf     (183,412 B)
   cee9892f9f0cc8fe882c9e9537ee6a89621d86ee7ceaf70b02e2b2b1c25c061a  OFL-NotoSans.txt
   a216f6f8d85c7228093e0ee5e258d9d377e6671f68acb4db1930b29583d0f331  OFL-NotoSansDevanagari.txt
   ```
   The fonts total 1.23 MB. WeasyPrint subsets them, so the 12-page reference board PDF was 37 KB.
4. Launch Codex with stdin redirected: `codex exec ... < /dev/null`.
5. After Codex finishes and before committing, record the golden. This is done once, and the reviewer reads it (see "Golden re-record rule"):
   `P6_8_RECORD_GOLDEN=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_p6_8_board_report_v2.py -k golden`
   Codex may do this step itself if the orchestrator prefers. Either way, the file is committed with the PR.

## Goal

1. **New report type.** The report version type `board_report` ("Board report v2 (PDF)") is rendered by WeasyPrint with vendored Noto Sans and Noto Sans Devanagari. A Devanagari company name and ₹ amounts render correctly in it.
2. **Frozen document.** Each board report version stores two files: the PDF, and the JSON document the PDF was rendered from, with its sha256 in the audit trail. B2 derives DOCX and XLSX from that stored document only.
3. **Standalone Workpaper.** The Workpaper snapshot becomes one self-contained HTML file: inline CSS, no scripts, no `/static`, no CDN, no links out of the page.
4. **Offline rendering.** Rendering never touches the network. The only files a render may load are the four vendored fonts, and anything else stops the render.
5. **fpdf2 untouched.** `generate_pdf`, `generate_integrated_pdf`, `reports.py` and the canonical golden are not changed. The legacy `gap_report` type still generates and still downloads.
6. **Write-once.** Old versions of every type are served from their stored bytes and never re-rendered.
7. **No new LLM call, no schema change, no migration.** Alembic head stays `8b2d5f7e1c34`.

## Split (D-P6-8-A)

| PR | Scope | Status |
|---|---|---|
| **B1 (this handoff, full design)** | Rendering stack: WeasyPrint 70.0, vendored Noto, offline fetcher, CI and Docker libraries. Board report v2 as the new `board_report` snapshot type (document-first, JSON sidecar, release-gated, issue checks the sidecar). Live HTML preview. Standalone Workpaper snapshot. | Contract tests written |
| **B2 (sketched below; designed after B1 merges)** | DOCX and XLSX derived from a `board_report` version's stored document. openpyxl. Download links on the versions page. | Sketch only |

B1 must land first because B2 reads B1's sidecar. That sidecar is the only thing that makes "derived from snapshot X, vN" literally true.

## Step 0 (before writing code)

1. Run `.venv/bin/pytest -q -p no:cacheprovider` and record the counts in `## Results`.
   - With the pre-steps done and nothing implemented, expect 13 failures in `tests/test_p6_8_board_report_v2.py`. Everything else should be green.
   - Without pre-step 2, the four renderer tests skip instead of failing, unless `CYBERASSESS_REQUIRE_WEASYPRINT=1` is set.
2. Confirm these facts. **If any is false, stop and report.** Line numbers are from `db3fdc8`.
   1. **Snapshot types.** `app/services/report_snapshots.py:22-23` defines `SNAPSHOT_TYPES = ("gap_report", "workpaper", "integrated_report")` and `ASSESSMENT_SNAPSHOT_TYPES = ("gap_report", "workpaper")`.
      - `tests/test_p5_6_rfi_rebuild.py:999-1000` pins both tuples.
      - The versions page (`pages/report_snapshots.html`) loops over `snapshot_rows(...)` groups keyed by `ASSESSMENT_SNAPSHOT_TYPES`. A new type therefore shows up with no `web.py` change.
      - `tests/test_report_snapshots.py:741-742` and `tests/test_p5_6_rfi_rebuild.py:684` count `data-snapshot-type=` as 2.
   2. **One deletion path.** `tests/test_report_snapshots.py:376-409` (scenario 3) inspects `report_snapshots.py` and `app/routers/snapshots.py`. It requires:
      - exactly one `.unlink(` in each file
      - exactly one `.open(`, the `"xb"` open, in the service
      - no `write_bytes(`, `write_text(`, `"wb"` or `"ab"` in the service
      - no word `delete` in either file, in any case
      - no `.commit(` in the service
      - no assignment to `.is_issued`

      The single `.unlink(` today is `_store` (`:216`) in the service and the commit-failure cleanup in `generate_snapshot` (`snapshots.py:125`) in the router. The RFI paths dodge the count with `getattr(..., "unlink")` (`report_snapshots.py:308`, `snapshots.py:160-161`). **Do not add another `getattr` dodge**; D-P6-8-E removes the need for one.
   3. **Workpaper snapshot today.** `snapshots.py:66-80` `_render` renders `pages/workpaper.html`, which extends `base.html`. `base.html:12-14` loads `/static/css/tailwind.css`, `/static/css/style.css` and the unpkg htmx CDN. `tailwind.css` is a build artefact and is not in git (`.gitignore`). `tests/test_report_snapshots.py:497-516` (scenario 7) asserts that the frozen Workpaper equals the live page.
   4. **Workpaper routes are pinned.** `tests/test_workpaper.py:905-911` requires exactly one route containing `/workpaper`. So this PR adds **no** live standalone-Workpaper route (D-P6-8-H).
   5. **RFI precedent.** `rfi_requests.generate_version` (`:320`) builds a JSON document, renders a PDF from it, and stores the PDF plus a `.json` sidecar with `document_sha256` in `extra_metadata`. `rfi_version_docx` (`snapshots.py:198`) renders DOCX from the stored sidecar on request. B1 and B2 copy this pattern for the board report.
   6. **P6-6 copy helpers** in `app/utils/pdf_export.py`:
      - `GAP_STATUSES` (`:89`) and `LEGAL_FRAMEWORK_IDS` (`:90`)
      - `_framework_label` (`:117`) and `_regimes` (`:125`)
      - `_nature_text` (`:146`) and `_follow_on_text` (`:162`)
      - `_disclaimer_text` (`:206`), which is part of `methodology_text` (`:243`)

      Importing these reads the module without changing it.
   7. `app/dpdpa/framework.py` defines `DPDPA_READINESS_NOTE` and `dpdpa_readiness_note_applies(frameworks, as_of)`.
   8. `app.utils.review_gate.require_review_approval(assessment_id, db)` raises:
      - `HTTPException(404)` when there is no assessment or no report
      - `409` when a framework failed
      - `403` with `approved_report.NOT_RELEASED_MESSAGE` when the report is not released
   9. `requirements.txt` has no WeasyPrint. `tests/test_p6_0c_dev_hygiene.py:26-49` pins `requirements-dev.txt` exactly and requires some strings in the workflow. P6-8 changes neither of those.
   10. **The PR adds no router.** `app/main.py` needs no change: the preview route lives in the existing snapshots router (D-P6-8-I).

## Decisions (made here so they are not relitigated)

### D-P6-8-A: Two PRs; B1 is fully specified here, B2 is a sketch

See "Split". B1 ships nothing a client edits. B2 ships nothing that renders a PDF.

### D-P6-8-B: fpdf2 and v2 co-exist as separate snapshot types; nothing old is rewritten

- **Registration.** Add the new type `board_report`, format `pdf`, with the label `"Board report v2 (PDF)"`.
  - `SNAPSHOT_TYPES = ("gap_report", "workpaper", "integrated_report", "board_report")`
  - `ASSESSMENT_SNAPSHOT_TYPES = ("gap_report", "workpaper", "board_report")`
- **Legacy stays as is.** The fpdf2 `gap_report` type keeps its generator, routes, label and golden:
  - `generate_pdf` and `generate_integrated_pdf` are untouched, which satisfies "PDF sections are additive-only": no existing page changes.
  - `pdf_export.py`, `rfi_export.py`, `reports.py`, `integrated_reports.py` and `tests/fixtures/**` are on the forbidden list in scenario 14.
- **Retirement.** Retiring fpdf2 at parity (D-P6-H) is a later decision (Open question 2). Until then consultants can generate either type.
- **D0 #3.** D0 #3 is closed for v2: Unicode throughout. The fpdf2 `gap_report` keeps its Latin-1 behaviour (`₹` → `Rs.`, Devanagari → `?`, P6-6 D-P6-6-J) until it is retired. Say this in the PR description.

### D-P6-8-C: Rendering stack: WeasyPrint 70.0, vendored Noto, offline by construction, lazy import

- **Pinned package.** `requirements.txt` gains the line `weasyprint==70.0` directly after `fpdf2==2.8.3`.
  - The version is pinned because 70.0 changed the URL-fetcher API: fetchers are `URLFetcher` subclasses, and `FatalURLFetchingError` stops a render.
  - `requirements-dev.txt` is unchanged (it is pinned exactly by P6-0c).
- **Vendored fonts** in `app/assets/fonts/noto/`: the four unhinted TTFs and two OFL files from the orchestrator pre-steps.
  - The licence is SIL OFL 1.1, which permits bundling and redistribution with the licence alongside.
  - The unhinted fonts are used because hinting does nothing in PDF output, and they are 30% smaller.
  - Noto Sans covers ₹ (U+20B9), and Noto Sans Devanagari covers the Devanagari block.
  - Neither covers `→` or `✓`, so templates must not use those glyphs (scenario 7 checks that every drawn glyph comes from Noto).
- **Why not system fonts:** the render must not depend on what a host happens to have. macOS substituted Kohinoor, Times and Songti in the probe; Ubuntu CI would substitute something else.
- **New module `app/utils/html_pdf.py`** (no app imports; WeasyPrint is imported only inside functions):
  ```python
  REPO_ROOT = Path(__file__).resolve().parents[2]
  FONT_DIR = REPO_ROOT / "app" / "assets" / "fonts" / "noto"
  FONT_FILES = {  # filename -> sha256; source URLs are in the P6-8 handoff
      "NotoSans-Regular.ttf": "f3961a9c…", "NotoSans-Bold.ttf": "87cb2d84…",
      "NotoSansDevanagari-Regular.ttf": "9c7d9351…", "NotoSansDevanagari-Bold.ttf": "ff2f76a2…",
  }  # full hashes as in pre-step 3
  LICENSE_FILES = ("OFL-NotoSans.txt", "OFL-NotoSansDevanagari.txt")
  FONT_STACK = "'Noto Sans', 'Noto Sans Devanagari'"
  REQUIRE_ENV = "CYBERASSESS_REQUIRE_WEASYPRINT"
  RENDERER_UNAVAILABLE_MESSAGE = (
      "PDF rendering is unavailable on this server: WeasyPrint or its system "
      "libraries (Pango) are not installed."
  )
  OFFLINE_REFUSED_MESSAGE = "The report tried to load an external resource: {url}"

  class RendererUnavailable(RuntimeError)   # .message = RENDERER_UNAVAILABLE_MESSAGE, .reason
  class OfflineRenderError(RuntimeError)    # .url, .message = OFFLINE_REFUSED_MESSAGE.format(url=url)
  def weasyprint_status() -> tuple[bool, str | None]   # try import weasyprint; (ImportError, OSError) -> (False, "Type: msg")
  def renderer_label() -> str                          # f"weasyprint {weasyprint.__version__}"
  def font_face_css() -> str                           # four @font-face rules
  def render_pdf(html: str) -> bytes
  ```
  - **`font_face_css()`** returns one line per face, in this order: Noto Sans 400 Regular, Noto Sans 700 Bold, Noto Sans Devanagari 400 Regular, Noto Sans Devanagari 700 Bold. Each line has the form `@font-face { font-family: '<family>'; src: url('<filename>'); font-weight: <w>; font-style: normal; }`. The URLs are **relative filenames**: no absolute path or `file:` URL ever appears in HTML.
  - **`render_pdf`** does the following, in order:
    1. If `weasyprint_status()` is false, raise `RendererUnavailable(reason)`.
    2. Otherwise build `weasyprint.HTML(string=html, base_url=f"{FONT_DIR.resolve()}{os.sep}", url_fetcher=<offline fetcher>).write_pdf()`.
    3. The offline fetcher is a `weasyprint.urls.URLFetcher` subclass, defined inside the function. Its `fetch(url, headers=None)` delegates to `super().fetch` only for a `file://` URL whose resolved path's parent is `FONT_DIR.resolve()` and whose name is a key of `FONT_FILES`. Anything else (http, https, data, other files) raises a private `FatalURLFetchingError` subclass that carries the URL.
    4. Catch that private exception around `write_pdf()` and re-raise `OfflineRenderError(url)`. `FatalURLFetchingError` is a `BaseException`, so it must never escape into FastAPI.
  - **Rendering is deterministic.** Equal HTML gives equal bytes on the same platform, because templates set `<meta name="dcterms.created">` from the document.
- **Environment and startup.**
  - **Local (macOS):** `brew install pango`. If the libraries are missing, `import app.main` still works (scenario 2 checks that `weasyprint` is not in `sys.modules` after importing the app). Generating a board report then returns **503** with `RENDERER_UNAVAILABLE_MESSAGE` and writes nothing.
  - **Tests:** renderer tests skip locally with an install hint. In CI, `CYBERASSESS_REQUIRE_WEASYPRINT: "1"` turns every skip into a failure.
- **CI** (`.github/workflows/tests.yml`). The exact change, which scenario 12 pins:
  ```yaml
        - name: Install WeasyPrint system libraries (P6-8)
          run: |
            sudo apt-get update
            sudo apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0
        - name: Install dependencies
          run: python -m pip install -r requirements-dev.txt
        - name: Renderer smoke (fails the job if WeasyPrint cannot render)
          run: python -c "from app.utils.html_pdf import render_pdf; render_pdf('<p>ok</p>')"
        - name: Run tests
          env:
            ... (existing lines unchanged)
            CYBERASSESS_REQUIRE_WEASYPRINT: "1"   # P6-8: renderer tests must run, never skip, in CI
  ```
  The apt step goes before "Install dependencies". The smoke step goes after it. The env line is appended to the existing "Run tests" env block. These are the packages WeasyPrint documents for Ubuntu 20.04 and later; `ubuntu-latest` is 24.04, which has all three. Fontconfig comes in as a Pango dependency.
- **Dockerfile.** After `WORKDIR /app` and before `COPY requirements.txt .`, add:
  ```dockerfile
  # P6-8: WeasyPrint (board report v2 PDF) needs Pango and HarfBuzz at runtime.
  RUN apt-get update \
      && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
      && rm -rf /var/lib/apt/lists/*
  ```
  `python:3.13-slim` is Debian trixie, which has all three. P6-14 (deploy) still owns non-root, `.dockerignore` and compose.

### D-P6-8-D: Document-first: the board report is a pure function of one JSON document

New module `app/services/board_report.py`:
```python
SNAPSHOT_TYPE = "board_report"
DOCUMENT_SCHEMA_VERSION = 1
TOP_RISKS_LIMIT = 10
TEMPLATE = "reports/board_report.html"
PREVIEW_VERSION_LABEL = "Preview (not a report version)"
SHA_PREFIX_CHARS = 12
DATE_FORMAT = "%d %b %Y"
OUTCOME_LABELS = {"compliant": "Compliant", "partially_compliant": "Partially Compliant",
                  "non_compliant": "Non-Compliant", "insufficient_evidence": "Insufficient Evidence",
                  "not_applicable": "Not Applicable"}
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
REGISTER_VERSION_STATUSES = ("active", "superseded")
EDITED_CITATION_NOTE = "Consultant decision; no cited evidence"
LEGACY_CITATION_NOTE = "Evidence support not captured"
NO_CITATION_NOTE = "No supporting citation"
NOT_COVERED_TEXT, RELIANCE_TEXT, CONFIDENTIALITY_TEXT   # see below
ISSUE_STATUS_TEXT = ("This version is a draft until it is issued. Whether it was issued, who issued it and "
                     "the SHA-256 of the issued file are recorded in the report version history.")
SIGN_OFF_NAMES_TEXT = "Names are recorded as entered by the consultant; they are not verified sign-ins."

def build_document(db, assessment, *, snapshot_id: str | None, version_label: str, generated_at: datetime) -> dict
def canonical_bytes(document: dict) -> bytes      # json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
def display_date(value: str | None) -> str | None # ISO date/datetime -> "30 Nov 2026"; registered as the Jinja filter "display_date"
def render_html(document: dict, *, embed_fonts: bool) -> str
def render_pdf(document: dict) -> bytes           # html_pdf.render_pdf(render_html(document, embed_fonts=True))
def generate_version(db, assessment, *, actor: str) -> ReportSnapshot
```
- **Copy text.** `NOT_COVERED_TEXT`, `RELIANCE_TEXT` and `CONFIDENTIALITY_TEXT` are copied verbatim from the fpdf2 board PDF's Scope & Limitations page (`pdf_export.py`, the `not dpdpa_only` "What Is Not Covered" text, the "Reliance on Disclosed Information" paragraph, and the first two sentences of "Confidentiality"). The confidentiality line in the document is `f"{CONFIDENTIALITY_TEXT} {settings.firm_name} and the named organization are the intended recipients of this report."`.
- **Templates.** Load them through a module-level `Jinja2Templates(directory=app/templates)` with `configure_templates(...)` (the same pattern as `snapshots.py`), and register the `display_date` filter on its env.
- **The document is built only from:**
  - `approved_report.build_approved_report(db, assessment)` (approved rows, reviews, scores, coverage, release)
  - `report_content.assessment_findings(db, assessment).findings` (approved Findings with citations and Actions)
  - `report_basis.current_basis(db, assessment)`
  - `conclusion_review.conclusion_cards(db, assessment.id)`, read-only, for per-row citations
  - `Evidence` / `EvidenceVersion` rows (the evidence register)
  - the current issued RFI (`report_snapshots.current_rfi_issue` + `read_rfi_document`)
  - `report_snapshots.source_manifest`
  - the framework registry and `settings.firm_name`
- **No LLM, no writes.** `build_document` does not flush and never adds a row.
- **Canonical and reusable.** The document is JSON-safe: ISO date strings, no datetimes. It round-trips through `canonical_bytes` (scenario 5). It is the single input to the PDF, the HTML preview and (B2) the DOCX and XLSX.

**Document schema v1.** Scenario 4 pins these exact top-level keys. Keys inside sections are listed so B2 can rely on them:

| Key | Content |
|---|---|
| `schema_version` | `1` |
| `kind` | `"board_report"` |
| `snapshot` | `{"id": <snapshot id or None for preview>, "version_label": "v<N>" or PREVIEW_VERSION_LABEL, "generated_at": <iso datetime>, "generated_on": "28 Sep 2026"}` |
| `firm_name`, `company_name`, `engagement_name` (or None), `assessment_id` | strings |
| `frameworks` | `[{"framework_id", "name", "version", "legal": framework_id in LEGAL_FRAMEWORK_IDS}]` in `assessment.frameworks` order |
| `basis` | `ReportBasis.to_metadata()` (five keys) + `"period_label"`, `"cutoff_label"` |
| `release` | `{"released_by": release.released_by, "released_on": "28 Sep 2026" or None}` |
| `summary` | `basis_of_assessment` (`_nature_text(ids)`); `scope` (`["<name>: <n> requirements in scope", …]`, n = in-scope count per framework); `limitations` (`[NOT_COVERED_TEXT, RELIANCE_TEXT, _follow_on_text(ids)]` + `DPDPA_READINESS_NOTE` when `dpdpa_readiness_note_applies(ids, generated_at.date())`); `confidentiality`; `frameworks` (per framework: `framework_id, name, status, score, rating, coverage` (the review's coverage dict), `headline`, `narrative: None`); `totals` (`requirements` = approved rows, `gaps` = rows in `GAP_STATUSES`, `critical_high_gaps`, `insufficient_evidence`, `not_applicable`) |
| `top_risks` | up to `TOP_RISKS_LIMIT` approved Findings ranked by `(SEVERITY_RANK[severity], priority, original order)`: `rank, finding_id, title, description, severity, priority, framework_id, framework_name, requirement_id, requirement_title, outcome_label, citations[{filename, version_number, location_ref, sha256_prefix, is_current}], owner, target_date, action_title` (owner/target/action from the Finding's first Action, else None) |
| `roadmap` | `actions`: every (Finding, Action), sorted by `(target_date is None, target_date, SEVERITY_RANK)`: `title, owner, target_date, status_label, closes: [{framework_name, requirement_id, finding_title}]` (one entry today; P6-9 groups cross-framework). `unplanned_gap_count`: gap rows with no Finding (same rule as P6-6 D-P6-6-H) |
| `not_assessed` | `insufficient_evidence`: `[{framework_id, requirement_id, requirement_title}]` from approved rows; `rfi`: `{"version_label": "v<N>" or None, "items": [{item_id, title, required}]}` from the current **issued** RFI |
| `framework_sections` | per framework: `framework_id, name, version, status, score, rating, domains[{domain_id, title, score, rating}]` (from the review's `domain_scores`; score/rating None when not `applicable`), `gaps[{requirement_id, requirement_title, outcome, outcome_label, risk_level, priority}]` (approved rows in `GAP_STATUSES`) |
| `sign_off` | `prepared_by, reviewed_by, issue_status (ISSUE_STATUS_TEXT), names_note (SIGN_OFF_NAMES_TEXT)` |
| `appendices` | `methodology` (`methodology_text(ids, len(approved rows))`); `requirement_register` (one row per approved row, in `approved.rows` order: `framework_id, requirement_id, requirement_title, domain_title (row.chapter_title), outcome, outcome_label, risk_level, priority (row.remediation_priority), decision_label (report_content.DECISION_LABELS), decided_by, decided_on (iso date), citation, citation_note`); `evidence_register` (see below) |
| `source` | `report_snapshots.source_manifest(db, assessment)` |

- **Headline** (`summary.frameworks[].headline`). Depends on the review status:
  - `scored`: `f"{score:.0f}% ({rating}); {coverage['insufficient_evidence']} requirement(s) insufficient evidence"`
  - `not_scored`: `"Not scored: no in-scope requirement has a scoring outcome; {n} requirement(s) insufficient evidence"`
  - anything else: `"Not scored"`
- **Register citation.** Decided per approved row, first match wins:
  - `row.decision == "edited"`: `citation=None`, `citation_note=EDITED_CITATION_NOTE`. A consultant edit carries no citations; the AI's belonged to the replaced proposal.
  - Card missing or `not card.citations_captured`: `LEGACY_CITATION_NOTE`.
  - No resolved citation: `NO_CITATION_NOTE`.
  - Otherwise: `"; ".join("<filename> v<version_number>, <location_ref>")` over resolved citations, with `citation_note=None`.
- **Evidence register.** Each row is `{filename, version_number, sha256_prefix (12 hex), added_on (iso date of the version), status, cited}`, sorted by `(filename.lower(), version_number)`. Rows are included as follows:
  - every `EvidenceVersion` whose `Evidence.assessment_id == assessment.id`, `Evidence.status != "rejected"` and `EvidenceVersion.status in REGISTER_VERSION_STATUSES`
  - plus any version cited by a resolved register citation, even if it belongs to engagement-level evidence
- **Determinism.** The only volatile inputs are `generated_at` (a parameter) and database timestamps (`decided_on`, `added_on`, `released_on`).
- **Out-of-scope Conclusions never appear.** Scenario 4 adds an unreviewed out-of-scope Conclusion after release and asserts it is absent from every client-facing section.

### D-P6-8-E: `board_report` versions: PDF + hashed JSON sidecar, one cleanup path

In `report_snapshots.py`:
- `BOARD_REPORT_SNAPSHOT_TYPE = "board_report"`; the tuple, `FORMAT_BY_TYPE` and `TYPE_LABELS` changes from D-P6-8-B.
- **`create_snapshot` refuses the type.** When `snapshot_type == BOARD_REPORT_SNAPSHOT_TYPE`, raise `InvalidSnapshot("Board reports are generated with their document.")` (constant `BOARD_REPORT_DOCUMENT_REQUIRED`). A board report without its document must be impossible.
- **`_store` stores the sidecar.** It gains the keyword `document_content: bytes | None = None`:
  ```python
  written: list[Path] = []
  try:
      written.append(_write_file(storage_path, content))
      if document_content is not None:
          written.append(_write_file(document_storage_path(storage_path), document_content))
      ...  # unchanged: ReportSnapshot row, generated event, flush
      return snapshot
  except Exception:
      for path in written:
          path.unlink(missing_ok=True)
      raise
  ```
  This is still one `.unlink(` in the file. Existing callers pass nothing and behave exactly as before. `_write_file` stays the only `open("xb")`.
- **New helpers:**
  ```python
  def document_storage_path(storage_path: str) -> str      # storage_path.removesuffix(".pdf") + ".json"
  def snapshot_files(snapshot) -> tuple[Path, ...]         # (pdf,) or (pdf, sidecar) for board_report
  def create_board_report_snapshot(db, *, assessment, snapshot_id: str, pdf_content: bytes,
                                   document_content: bytes, actor: str) -> ReportSnapshot
  def read_board_report_document(db, snapshot) -> dict
  ```
  - **`create_board_report_snapshot`:**
    - Empty content: `InvalidSnapshot("Rendered report was empty; nothing was saved.")`.
    - `storage_path = storage_path_for(snapshot_id=..., fmt="pdf", assessment_id=assessment.id)`, which gives `reports/assessments/{aid}/{sid}.pdf`, with the sidecar `{sid}.json` beside it.
    - `source=source_manifest(db, assessment)`, the same as `gap_report`, so the versions page flags "Source data changed".
    - `extra_metadata={"document_sha256", "document_size_bytes", "document_schema_version": board_report.DOCUMENT_SCHEMA_VERSION, "renderer": html_pdf.renderer_label()}`. Import both inside the function to avoid an import cycle.
    - Then `_store(..., document_content=document_content)`.

    The generated-event metadata keys are exactly the 10 base keys plus these 4 (scenario 8).
  - **`read_board_report_document`:**
    - Wrong type: `SnapshotNotFound("Report version not found.")`.
    - Read the sidecar (`rfi_document_path(snapshot)` computes the same path; you may make it call `document_storage_path`).
    - Unreadable file, hash mismatch against `document_sha256`, invalid JSON or non-dict: `SnapshotIntegrityError(INTEGRITY_MESSAGE)`.
- **`issue_snapshot` checks the sidecar.** After `verify_snapshot_file(...)`, call `read_board_report_document(db, snapshot)` when the type is `board_report`. A version whose document was altered can never be issued; the route returns 500 with `INTEGRITY_MESSAGE` (scenario 8).
- **Nothing else changes** in the RFI, integrated or gap-report paths.

**Generation.** `board_report.generate_version(db, assessment, *, actor)`:
1. `require_review_approval(assessment.id, db)`. The board report is client output, so a failed-analysis draft is **not** allowed (unlike the legacy `allow_failed_draft`).
2. `snapshot_id = _new_id()`, then `sequence = len(report_snapshots.snapshot_rows(db, assessment)["board_report"]) + 1`.
3. `document = build_document(..., snapshot_id=snapshot_id, version_label=f"v{sequence}", generated_at=datetime.now(timezone.utc))`.
4. `pdf = render_pdf(document)`.
5. `return report_snapshots.create_board_report_snapshot(..., document_content=canonical_bytes(document))`.

The PDF carries its own snapshot id and version, because the id is allocated before rendering.

**Route.** In `app/routers/snapshots.py`, `generate_snapshot` does the following:
1. It keeps its existing guards (404, blank type, unknown type, integrated).
2. It calls `board_report.generate_version` for `board_report`, and the existing `_render` + `create_snapshot` otherwise, **inside one try**. Errors map as follows:
   - `HTTPException` → `_error(exc.status_code, detail)`
   - `html_pdf.RendererUnavailable` → `_error(503, exc.message)`
   - `html_pdf.OfflineRenderError` → `_error(500, exc.message)`
   - `report_snapshots.SnapshotError` → `_error(exc.status_code, exc.message)`

   Each path calls `db.rollback()` first.
3. There is **one** commit block. On commit failure it runs `db.rollback()`, then `for path in report_snapshots.snapshot_files(snapshot): path.unlink(missing_ok=True)`, which is the router's only `.unlink(`, then `_error(500, "The report version could not be saved. Try again.")`.
4. On success, the existing `_success(...)` ("Draft version generated").

Issuing uses the existing issue route unchanged: it checks release and "generated after release". The file route is unchanged: it serves stored bytes with `X-Snapshot-Sha256`, and its generic PDF `Content-Disposition` already covers the new type.

### D-P6-8-F: What of D2 lands in B1, P6-9 and P6-10

| D2 item | B1 (this PR) | Later |
|---|---|---|
| 1 Cover | client, engagement, frameworks + versions, period, cut-off, "Report generated", "Version vN \| Snapshot <id8>", "Released for reporting by X on date", issue-status sentence | draft/issued **watermark**: never in the bytes (D-P6-8-G) |
| 2 Management summary | basis of assessment, scope (in-scope counts), limitations (not covered, reliance, follow-on, DPDPA readiness note when applicable), confidentiality, per-framework score **with coverage**, totals | per-framework **posture narrative**: slot `narrative: None`, filled by P6-10 (D-P6-F) |
| 3 Top risks | up to 10 approved Findings by severity then priority, with what is wrong (title, description), requirement, outcome, cited evidence (file, version, location, SHA-256 prefix), owner, target date, action | "why it matters in business terms" beyond the consultant's description: P6-10 |
| 4 Remediation roadmap | real Actions by target date, each with the Finding it closes | "fix once, closes N findings across frameworks": **P6-9** |
| 5 What we could not assess | insufficient-evidence requirements + current issued RFI items | per-item RFI response status (RFI has no item status yet) |
| 6 Per-framework sections | score, domain table, gaps table | domain heatmap graphics: optional polish |
| 7 Prior-period comparison | none | **P6-9** |
| 8 Sign-off | prepared by, reviewed by (free text, P6-6), period/cut-off/generated, issue-status sentence, names note | real identities: Track 4 (P6-11) |
| 9 Appendices | A Methodology (P6-6 `methodology_text`), B Requirement register (outcome + decision + citation on **every** row), C Evidence register | **ISO Statement of Applicability**: **P6-9** |

**Framework-conditional copy (D-P6-8-G below).** B1 adds no DPDPA penalty (₹ crore) exposure section; see Open question 3. The ₹ in the smoke test comes from consultant-entered text (a Finding description), which is how ₹ amounts reach a board report today.

### D-P6-8-G: Copy, conditionality and issue status

- **Reused P6-6 copy.** `_nature_text`, `_follow_on_text` and `methodology_text` are imported from `app.utils.pdf_export`, with no edit to that module, so v1 and v2 can never drift. When fpdf2 is retired, these helpers move to a copy module (not in P6-8).
- **Readiness note.** The DPDPA readiness note is included only when `dpdpa_readiness_note_applies(framework_ids, generated_at.date())` is true.
- **ISO-only output.** An ISO-only report contains none of `dpdpa`, `digital personal data protection`, `data principal`, `data fiduciary`, `legal counsel`, `legal advice`, `privacy professional`, `cmmi`, `maturity model`, and does contain "certification" (scenario 6).
- **Issue status is never in the bytes.** Versions are write-once, and issuing does not re-render. So the PDF never says "Issued" and carries no DRAFT watermark: an issued file stamped DRAFT would be wrong for the client. The cover and the sign-off page print `ISSUE_STATUS_TEXT`, and the version history is the record (Open question 1).

### D-P6-8-H: Standalone Workpaper replaces the Workpaper snapshot renderer; no new route

- **New module and template.** Add `app/services/standalone_workpaper.py` with `TEMPLATE = "reports/workpaper_standalone.html"` and `def render(db, assessment) -> str`. It renders `workpaper.build_workpaper(db, assessment)` through a module-level `Jinja2Templates` + `configure_templates`, which gives it the `branding` and `report_basis_for` globals.
- **Snapshot rendering.** `snapshots._render` for `"workpaper"` returns `standalone_workpaper.render(db, assessment).encode("utf-8")`. The snapshot type, format (`html`), label and storage stay the same.
  - Old Workpaper versions keep their stored bytes. Those depended on `/static`; they are history and are never re-rendered.
  - The now-unused `_templates`, `Jinja2Templates`, `configure_templates` and `Path` imports in `snapshots.py` are removed, because your change orphans them.
- **Template contract** for `app/templates/reports/workpaper_standalone.html`:
  - **Document shape.** It is a full document: `<!DOCTYPE html>`, `<meta charset="utf-8">`, and exactly one inline `<style>` block. It contains none of `<script`, `<link`, `src=`, `@import`, `url(`, `/static`, `http://`, `https://`, `hx-`, `<form`, `<iframe`. Every `href` starts with `#`.
  - **No links out.** Evidence, Findings and "decide" appear as text, not app links.
  - **No `|safe` filter.**
  - **No timestamp of rendering**, so a snapshot equals `render(...)` at the same database state.
  - **Font stack.** The font stack is `'Noto Sans', 'Noto Sans Devanagari', system-ui, -apple-system, 'Segoe UI', sans-serif`. No fonts are embedded: browsers render Devanagari with OS fonts, and this keeps each snapshot small (Open question 7).
  - **Same data as the live page.** It shows the same data as `pages/workpaper.html` + `components/workpaper_entry.html`. Scenario 10 compares these attribute value lists with the live page: `data-count` (with the same numbers), `data-decision-state`, `data-workpaper-section`, `data-in-scope`, `data-revision-action`, `data-run-status`, plus `<article data-workpaper-entry id="<anchor>">` ids. It also keeps:
    - `data-report-basis` with the exact text `Assessment period: … · Evidence cut-off: …`, which P6-6 scenario 15 reads
    - `data-run-stale`, `data-workpaper-unconcluded` and `data-workpaper-finding`
    - the five numbered sections per entry (client response, evidence, AI proposal, consultant decision, revision history)
    - the legacy-bulk, locked, excluded, withheld and superseded-version notices
  - **Duplication.** The markup is its own. The duplication with `workpaper_entry.html` is deliberate, because that component is Tailwind-only and cannot render without the built CSS. The attribute-parity test is what stops the two from drifting.
- **No live standalone route.** `tests/test_workpaper.py` pins exactly one `/workpaper` route. Consultants reach the standalone file through the versions page ("View" on a Workpaper version).

### D-P6-8-I: Live preview in the snapshots router; one template for preview and PDF

- **Route.** `GET /api/assessments/{assessment_id}/board-report/preview` goes in `app/routers/snapshots.py`, with `response_class=HTMLResponse`.
- **Behaviour.** It calls `require_review_approval` (403 until released) and builds the document with `snapshot_id=None`, `version_label=PREVIEW_VERSION_LABEL` and `generated_at=now`. It then calls `db.rollback()` and returns `render_html(document, embed_fonts=False)`. It writes no file, no row and no audit event.
- **Preview banner.** The template shows `<p class="preview" data-preview>{version_label}. Generate a report version to produce the PDF.</p>` only when `doc.snapshot.id` is None.
- **Template contract** for `app/templates/reports/board_report.html`:
  - **Head.** `<title>Board report: {{ doc.company_name }}</title>`: this becomes the PDF Title metadata, the one place Devanagari round-trips exactly (see the smoke plan). Also `<meta name="author">` and `<meta name="dcterms.created" content="{{ doc.snapshot.generated_at }}">`.
  - **One `<style>` block, with no user data in it.**
    - Running header and footer text comes from `string-set` on two hidden cover elements (`.running-header`: `{{ doc.firm_name }} | Board report`; `.running-footer`: `{{ doc.company_name }} | {{ doc.snapshot.version_label }}`, styled `font-size: 0; height: 0; margin: 0`). `@page` margin boxes use `string(running-header)` and `string(running-footer)`.
    - `@bottom-right` shows `"Page " counter(page) " of " counter(pages)`.
    - `@page :first` has no top-left box.
    - This rules out CSS injection from a company name (scenario 11).
  - **Trusted CSS values.** `font_face_css` and `font_stack` are passed from `render_html` as `markupsafe.Markup(...)` (trusted constants). There is **no `|safe` in either report template**. Without `Markup`, autoescape turns `'` into `&#39;` and the fonts silently fall back to system fonts (a mutation caught this).
  - **Page setup.** A4 (`size: A4`), `font-family: {{ font_stack }}` on `html` and on `@page`, `thead { display: table-header-group; }`, `tr { break-inside: avoid; }`, and every `<section>` after the cover starts a new page.
  - **Sections, in this order**, each `<section data-section="…">` with an `<h2>`:
    - `cover` (h1 "Board report"; lines as D-P6-8-F; `Version {{ label }} | Snapshot {{ id[:8] }}` when there is an id)
    - `summary` "Management summary"
    - `top-risks` "Top risks"
    - `roadmap` "Remediation roadmap"
    - `not-assessed` "What we could not assess"
    - one `framework` section per framework with `data-framework`, headed `{{ name }} ({{ version }})`
    - `sign-off` "Sign-off"
    - `methodology` "Appendix A: Methodology"
    - `requirement-register` "Appendix B: Requirement register"
    - `evidence-register` "Appendix C: Evidence register"
  - **Rendered strings the tests read:**
    - `Assessment period: {period_label} | Evidence cut-off: {cutoff_label}` (cover); `Assessment period: …` and `Evidence cut-off: …` as separate lines on the sign-off page
    - `Report generated: {generated_on}`
    - `Prepared by: {… or 'not recorded'}`, `Reviewed by: {… or 'not recorded'}`
    - `{requirements} requirements assessed | {gaps} gaps identified ({critical_high} critical or high)`
    - the scores-and-coverage table (framework, headline, in scope, compliant, partial, non-compliant, insufficient evidence, not applicable)
    - `Scores are computed and reported independently for each framework; no score is combined across frameworks.`
    - top-risk evidence as `filename vN, location (SHA-256 <prefix>)`
    - `Owner: {owner or 'Unassigned'} | Target: {target_date|display_date or 'No target date'}`
    - the roadmap intro `Actions recorded against approved findings, ordered by target date. Owners and dates are set by the consultant; nothing on this page is estimated.`
    - empty states: `No approved findings are recorded.`, `No remediation actions are recorded for the approved findings yet.`, `No requirement was concluded as insufficient evidence.`, `No request for information has been issued for this assessment.`, `No evidence documents are recorded for this assessment.`
    - dates on the page through `display_date`: ISO in the document, `30 Nov 2026` on the page; scenario 7 asserts `Target: 30 Nov 2026` and no `2026-11-30`
    - no glyph outside the Noto fonts (no `→`, `✓`, emoji)
- **Versions page** (`pages/report_snapshots.html`). Directly after the existing `gap_report` release note, add:
  ```html
  {% if type == 'board_report' %}
  <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{% if release.released %}<a data-board-report-preview href="/api/assessments/{{ assessment.id }}/board-report/preview" class="font-medium text-brand dark:text-navy-300 hover:underline">Preview the board report →</a>{% else %}Generating a board report requires the report to be released.{% endif %}</p>
  {% endif %}
  ```
  Nothing else on that page changes. The "Download" link and "Issue" control already work for the new type.

### D-P6-8-J: Golden re-record rule

- **The fpdf2 canonical golden does not move in P6-8.** That is `tests/fixtures/canonical_dpdpa/expected/pdf_text.sha256` and `pdf_meta.json`. `pdf_export.py` and `tests/fixtures/**` are forbidden in scenario 14. If it fails, something outside scope changed: stop and report.
- **The new v2 golden is the normalised document JSON:** `tests/golden/p6_8_board_document.json`. It lives outside `tests/fixtures/` on purpose. Five suites guard `tests/fixtures` and `tests/support` as canonical data, and a new golden should not dilute those guards (the same reasoning as P6-6's `tests/report_period_helper.py`).
  - Normalisation, in scenario 13: UUIDs become `<id:N>` in first-appearance order, and the run-day date fields `decided_on`, `added_on` and `released_on` become `<run-date>`.
  - The golden is platform-independent. It checked stable across three runs with random ids.
- **The PDF is never goldened by bytes or text hash.** Line breaking and shaping depend on the Pango and HarfBuzz versions, which differ between macOS Homebrew and Ubuntu CI. The PDF is checked by structure and exact strings instead (scenarios 3 and 7).
- **Who and when:**
  1. **B1:** Codex (or the orchestrator, pre-step 5) records the golden once with `P6_8_RECORD_GOLDEN=1 … -k golden`, then runs the suite without the variable. The Claude reviewer reads the **whole** JSON once during AR (checkpoint 5).
  2. **Later PRs (B2, P6-9, P6-10):** re-record only when that PR's handoff states the document changes, and only with the same command. Bump `DOCUMENT_SCHEMA_VERSION` when a key is added, removed or renamed; value-only changes keep the version. The reviewer checks every hunk of the JSON diff against a stated change.
  3. **Never re-record** to make an unexplained failure pass. Saqlain sees the JSON diff in the PR.

### D-P6-8-K: File set, P6-7a disjointness, no LLM

P6-8 B1 touches exactly:

| Path | Change |
|---|---|
| `app/utils/html_pdf.py` (new) | C |
| `app/services/board_report.py` (new) | D, F, G |
| `app/services/standalone_workpaper.py` (new) | H |
| `app/services/report_snapshots.py` | E |
| `app/routers/snapshots.py` | E, H, I |
| `app/templates/reports/board_report.html` (new), `app/templates/reports/workpaper_standalone.html` (new) | H, I |
| `app/templates/pages/report_snapshots.html` | I (one block) |
| `app/assets/fonts/noto/*` (new; orchestrator pre-step 3) | C |
| `requirements.txt`, `.github/workflows/tests.yml`, `Dockerfile` | C |
| `tests/golden/p6_8_board_document.json` (new; recorded) | J |
| `tests/test_report_snapshots.py`, `tests/test_p5_6_rfi_rebuild.py` | L (exact edits) |
| `tests/test_p6_8_board_report_v2.py`, five guard files, `tasks/todo.md` | designer (already committed) |
| `tasks/handoffs/2026-09-28-p6-8-board-report-v2.md` | append `## Results` only |

**Scenario 14 enforces this.**
- **Forbidden paths.** Neither the committed diff (`main...HEAD`) nor the working tree may touch:
  - the fpdf2 reports and goldens: `pdf_export.py`, `rfi_export.py`, `reports.py`, `integrated_reports.py`, `tests/fixtures`, `tests/support`
  - P6-7a's surfaces: `review.py`, `conclusion_review.py`, `templates/components`, `templates/partials`, `base.html`, `web.py`
  - the analyzer, LLM, scoring, report readers (`approved_report`, `report_content`, `report_basis`, `workpaper`, `findings`), packs, models, schemas, alembic, `config.py`, `scripts` and `validation`
- **Allowlist.** Every changed or untracked path under `app/` must be in the allowlist above.
- **No LLM imports.** The three new modules contain none of `llm_client`, `claude_analyzer`, `services.grounding`, `call_llm` or `openai`.

### D-P6-8-L: Existing tests that change (the complete list)

**Already applied by the designer**: per-PR `:(exclude)` lines naming P6-8 B1. Nothing was deleted or broadened; this follows the stale-guard rule.
- `tests/test_p6_3a_grounding.py` `PROTECTED_PATHS`: `app/routers/snapshots.py`, `app/templates/pages/report_snapshots.html`, `app/templates/reports`.
- `tests/test_p6_4_cap_upload_limit.py::_changed` and `tests/test_p6_4_whats_missing.py::test_scenario_13_application_files_are_limited_and_disjoint_from_p6_4_cap`: the eight B1 app paths. These are `app/utils/html_pdf.py`, `app/services/board_report.py`, `app/services/standalone_workpaper.py`, `app/services/report_snapshots.py`, `app/routers/snapshots.py`, `app/templates/reports`, `app/templates/pages/report_snapshots.html` and `app/assets/fonts/noto`. In the second test they are applied to both the diff and the untracked listing.
- `tests/test_p6_6_report_foundations.py::P6_4_AND_PROTECTED_PATHS`: `app/services/report_snapshots.py`.
- `tests/test_p6_nist_csf2_alignment.py::test_protected_surface_guard_uses_three_dot_diff`: `app/services/{report_snapshots,board_report,standalone_workpaper}.py`, `app/routers/snapshots.py`.

**Codex applies exactly these, and nothing else in existing tests:**
1. `tests/test_report_snapshots.py`, scenario 7 (`test_workpaper_snapshot_matches_live_page_then_stays_frozen`). Replace the single line `assert frozen == http.get(f"/assessments/{assessment.id}/workpaper").text` with:
   ```python
       # P6-8 (D-P6-8-H): the Workpaper snapshot is the standalone render, not the live page.
       from app.services import standalone_workpaper

       assert frozen == standalone_workpaper.render(db, assessment)
   ```
   The rest of that test, including the later live-page checks, is unchanged.
2. `tests/test_report_snapshots.py`, scenario 13. Both `== 2` counts become `== 3`, with a `# P6-8: + board_report` comment on the first: `empty.text.count("data-snapshot-type=")` and `empty.text.count("No versions generated yet.")`.
3. `tests/test_p5_6_rfi_rebuild.py:684`: `page.text.count("data-snapshot-type=") == 3  # P6-8: + board_report`.
4. `tests/test_p5_6_rfi_rebuild.py:999-1000`. Put the comment `# P6-8 adds the board report v2 type (D-P6-8-B).` above the two lines, and change them to:
   ```python
   assert report_snapshots.SNAPSHOT_TYPES == ("gap_report", "workpaper", "integrated_report", "board_report")
   assert report_snapshots.ASSESSMENT_SNAPSHOT_TYPES == ("gap_report", "workpaper", "board_report")
   ```

**Expected transient failures while the tree is uncommitted (both go green after the orchestrator commits):**
- `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes` (modified tracked files under `tests/`)
- `tests/test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` (a working-tree diff of `report_snapshots.py` and `requirements.txt`)

## File overlap with P6-7a and merge order

P6-7a (`claude/p6-7-requirement-card`, handoff `tasks/handoffs/2026-09-28-p6-7-requirement-card.md`) touches:
- `app/services/{requirement_card,review_queue}.py` (new)
- `app/routers/requirement_review.py` (new)
- `app/services/conclusion_review.py`
- `app/main.py`
- `app/templates/components/{conclusion_card,requirement_card_body}.html`
- `app/templates/pages/{review_queue,evidence_span,conclusions}.html`
- the same four guard files (not `test_p6_6_report_foundations.py`)
- `tasks/todo.md`

**No source file is shared.** P6-8 B1 does not touch `main.py` (the preview route lives in the existing snapshots router), `web.py`, `base.html`, `workpaper.html` or `workpaper_entry.html`.

**Read-only dependency.** `board_report.build_document` calls `conclusion_review.conclusion_cards` and reads `card.conclusion`, `card.state`, `card.citations` (dicts with `resolved`, `filename`, `version_number`, `location_ref`, `evidence_version_id`) and `card.citations_captured`. P6-7a adds a field and a gate but removes none of these. `report_content.assessment_findings` and `workpaper.build_workpaper` go through the same card builder. Scenarios 4 and 10 would catch a shape change.

**Shared surfaces (text conflicts only):** `tasks/todo.md` (adjacent lines) and the exclude lists in `test_p6_3a_grounding.py`, `test_p6_4_cap_upload_limit.py`, `test_p6_4_whats_missing.py` and `test_p6_nist_csf2_alignment.py`.

**Merge order: P6-7a first, then P6-8 B1.** This matches P6-7a's handoff. P6-7a is smaller and records no golden. After it merges, the P6-8 branch merges `origin/main` into itself (never rebase; the repo rejects force-pushes), keeps **both** sides of every exclude list and of `todo.md`, then reruns the full suite.
- Scenario 14's `main...HEAD` diff then excludes P6-7a's files automatically.
- The P6-8 golden JSON does not change from P6-7a, which changes no document input. If it does change, stop and report.

If P6-8 lands first, P6-7a does the same merge.

## Do not touch

- The contract test file `tests/test_p6_8_board_report_v2.py`, the designer's guard excludes, and `tests/report_period_helper.py`.
- `app/utils/pdf_export.py`, `app/utils/rfi_export.py`, `app/routers/{reports,integrated_reports,review,web,conclusions,analysis,documents,findings}.py`.
- `app/services/{approved_report,report_content,report_basis,workpaper,findings,conclusion_review,rfi_requests,claude_analyzer,desk_review,desk_review_v2,llm_client,analysis_pipeline,scoring,evidence,citations,document_processor}.py`, `app/services/grounding/**`.
- `app/main.py`, `app/config.py`, `app/template_config.py`, `app/templates/{base.html,components/**,partials/**}`, `app/templates/pages/*` except `report_snapshots.html`.
- `app/models/**`, `app/schemas/**`, `alembic/**`, `app/frameworks/**`, `app/dpdpa/**`, `scripts/**`, `tests/fixtures/**`, `tests/support/**`, `requirements-dev.txt`, `.python-version`, `docker-compose.yml`.
- Every other existing test file, fixture and golden.
- `validation/**` and everything in the independence list.

If you find you need to change any of these, stop and report.

## Non-goals

- **B2 (DOCX and XLSX):** see the sketch.
- **P6-9:** SoA, cross-framework "closes N findings" grouping, prior-period comparison.
- **P6-10:** posture narrative.
- **Track 4:** real identities in sign-off.
- **The fpdf2 reports:** no fixes to `gap_report` or `integrated_report`, not even the `_framework_label` label bug (Open question 4); no retiring them.
- **No penalty exposure section** (Open question 3).
- **No integrated (engagement-level) v2 report.**
- **No live standalone-Workpaper route.**
- **No new LLM call, no migration, no model change.**

## B2 sketch (DOCX + XLSX derived from a board-report version); designed after B1 merges

- **Source of truth.** Everything B2 produces comes from `report_snapshots.read_board_report_document(db, snapshot)`, and never from the live database.
  - Exports are rendered on request and never stored (the RFI DOCX precedent).
  - Exports are deterministic: fixed zip entry timestamps, and core properties `created`/`modified` set from `document["snapshot"]["generated_at"]`, as `tests/test_rfi_docx_determinism.py` does for the RFI.
- **Routes** (in `app/routers/snapshots.py`): `GET /api/assessments/{aid}/snapshots/{sid}/docx` and `…/xlsx`.
  - Returns 404 unless `snapshot.type == "board_report"`, and 500 with `INTEGRITY_MESSAGE` when the sidecar is tampered with.
  - `Content-Disposition` comes from `app.utils.http_headers.attachment_disposition(f"{company}_board_report_v{N}_{sid[:8]}.docx|.xlsx")`, so Devanagari survives via `filename*`.
  - Header `X-Board-Document-Sha256`.
  - The versions page gets "DOCX" and "XLSX" links on each `board_report` row.
- **Derivation label**, on the DOCX first page and as the XLSX "About" sheet's first row:

  > Derived from board report snapshot {id8}, {vN} (document SHA-256 {prefix}). Edits to this file do not change the report version it was derived from.

  It also goes in the DOCX core-properties `comments` field.
- **DOCX** (python-docx, already pinned): the same sections and order as the PDF, with the same headings, tables for scores, gaps, register and evidence, and Word heading styles, so the consultant can restyle. Fonts are left to Word (`Noto Sans`, with Word's fallback), and nothing is embedded.
- **XLSX** (new pin `openpyxl==3.1.5`; the orchestrator installs it):
  - "Requirement register": the register columns plus the domain.
  - "Action tracker": the roadmap actions plus the Finding, requirement, owner, target date and status, followed by two empty client columns, "Client update" and "Evidence of closure".
  - "About": the label, generation time, version, snapshot id and document hash.
  - Header rows are frozen, auto-filtered and bold. There are no formulas.
- **Formula injection.** Any cell string that starts with `=`, `+`, `-`, `@`, tab or CR gets a leading `'` (OWASP CSV/formula injection). Client-controlled names and consultant text reach these cells.
- **B2 contract tests to write:**
  - both files open with python-docx and openpyxl
  - the label is present
  - the content equals the document
  - B2 never reads the database (changing the database after generation changes nothing; a patched `build_document` that raises is never called)
  - a tampered sidecar gives 500
  - 404 for other snapshot types
  - injection prefixes are escaped
  - the bytes are deterministic
  - the file-set guard

## Test scenarios (all in `tests/test_p6_8_board_report_v2.py`)

The suite uses an Alembic-`head` SQLite database per test and the real FastAPI app through `TestClient`. It runs the real analysis route with both analyzer seams faked; an autouse fixture makes any `llm_client.call_llm` call fail.

The fixture is a released DPDPA + ISO assessment for the company `भारत डेटा प्राइवेट लिमिटेड`, with:
- DPDPA conclusions: non-compliant/high (cited to an evidence version), compliant, insufficient evidence
- ISO conclusions: partially compliant/critical (edited by the consultant), not applicable
- two approved Findings with Actions, one of them described as `Budget ₹12 lakh for consent tooling`
- three evidence files, one of them rejected

PDFs are read back with `pdfplumber`.

| # | Test | Covers |
|---|---|---|
| 1 | `test_scenario_1_fonts_are_vendored_pinned_and_licensed` | C: `FONT_DIR`, `FONT_FILES` hashes, OFL files, ₹ and Devanagari glyphs in the cmaps (fontTools), size under 1.5 MB, four relative `@font-face` URLs, `weasyprint==70.0` pin |
| 2 | `test_scenario_2_renderer_unavailable_is_a_clean_503_and_the_app_starts_without_pango` | C: app import does not import `weasyprint`; `RendererUnavailable` message; route 503 + error toast, nothing written |
| 3 | `test_scenario_3_renderer_is_offline_deterministic_and_fails_loud` *(needs WeasyPrint)* | C: https image, `file:///etc/hosts` stylesheet and `@import` refused (`OfflineRenderError`); no socket connect; identical bytes twice; only Noto fonts drawn; ₹ text exact |
| 4 | `test_scenario_4_document_is_built_from_approved_data_only` | D, F: exact top-level keys, snapshot block, frameworks and legal flags, basis, release, register equals `approved.rows` (outcome, risk, priority), citation/edited/no-citation notes, headline and coverage, totals, top-risk order and citation, roadmap order and `closes`, insufficient-evidence list, RFI none, framework gaps/domains, evidence register (rejected excluded, cited flag), `source`, sign-off; stray out-of-scope Conclusion absent |
| 5 | `test_scenario_5_document_bytes_are_canonical_and_deterministic` | D: `canonical_bytes` stable, UTF-8 Devanagari, JSON round-trip, canonical form |
| 6 | `test_scenario_6_framework_conditional_copy` | G: ISO-only has no legal or DPDPA copy and has "certification"; DPDPA+ISO has both; readiness note only with DPDPA |
| 7 | `test_scenario_7_board_pdf_renders_devanagari_rupee_and_all_sections` *(needs WeasyPrint)* | D0 #3, I: PDF Title metadata is the exact Devanagari name; A4; every glyph from Noto (Devanagari font present); cover contains every Devanagari code point of the name; no U+FFFD; ₹ text exact; period, cut-off, version/snapshot, "Report generated", "Page 1 of N"; section order; sign-off names; evidence file and hash prefix; `Target: 30 Nov 2026` |
| 8 | `test_scenario_8_snapshot_is_write_once_with_a_hashed_document_sidecar` *(needs WeasyPrint)* | B, E: unreleased 403 and nothing written; metadata keys; renderer label; sidecar path and hash; v1/v2 labels; sidecar equals `canonical_bytes`; `create_snapshot` refuses the type; wrong-type read 404; tampered sidecar blocks issue (500, not issued); restored sidecar issues; versions page shows the type, label and preview link |
| 9 | `test_scenario_9_stored_versions_are_never_re_rendered` *(needs WeasyPrint)* | E: after reopen, edit and re-release, a new version reflects the change while the old gap-report, Workpaper and board-report versions are served byte-identical, with every renderer and `build_document` patched to raise |
| 10 | `test_scenario_10_workpaper_snapshot_is_standalone_and_offline` | H: snapshot equals `standalone_workpaper.render`; no script, link, src, url(), `/static`, http(s), hx-, form, iframe; `#`-only hrefs; escaping; Devanagari; basis line; attribute and count parity with the live page; renders offline through `html_pdf` when available |
| 11 | `test_scenario_11_preview_shares_the_template_and_keeps_user_text_out_of_css` | I: 403 before release; 200 HTML after; writes no file, row or event; preview banner; no `@font-face` in the preview; all section headings; a hostile company name never inside `<style>`; four faces when embedded; the name escaped in HTML |
| 12 | `test_scenario_12_ci_and_docker_install_the_renderer` | C: exact apt line before pytest, `CYBERASSESS_REQUIRE_WEASYPRINT: "1"`, renderer smoke step, Dockerfile apt line before pip, apt lists cleaned |
| 13 | `test_scenario_13_document_golden` | J: normalised document equals `tests/golden/p6_8_board_document.json` (record with `P6_8_RECORD_GOLDEN=1`) |
| 14 | `test_scenario_14_no_llm_and_b1_file_set` | K: no LLM imports; forbidden paths untouched (committed and working tree); `app/` changes within the allowlist (green before and after) |

## Verification and smoke plan (before reporting done)

1. `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_8_board_report_v2.py` gives **14 passed**, with the file unmodified. Run it twice.
2. Run the same file with `CYBERASSESS_REQUIRE_WEASYPRINT=1`: still 14 passed (proves nothing skipped).
3. Neighbours, all green:
   `.venv/bin/pytest -q -p no:cacheprovider tests/test_report_snapshots.py tests/test_p5_6_rfi_rebuild.py tests/test_workpaper.py tests/test_p6_6_report_foundations.py tests/test_pdf_updates.py tests/test_golden_dpdpa.py tests/test_rfi_docx_determinism.py tests/test_retention.py tests/test_p6_0c_dev_hygiene.py`.
4. Frozen-surface check. `git diff --stat main -- app/utils/pdf_export.py app/routers/reports.py tests/fixtures tests/support app/models alembic app/services/approved_report.py app/services/report_content.py app/services/conclusion_review.py app/main.py app/routers/web.py app/templates/base.html` must be empty.
5. Full suite `.venv/bin/pytest -q -p no:cacheprovider`. Expected: everything green except the two transient uncommitted-tree guards in D-P6-8-L. List any other failure with its cause.
6. **Smoke (the orchestrator, after commit).** This is the handoff's smoke requirement: read the text back, open the files, and render offline.
   1. `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_8_board_report_v2.py -k "scenario_3 or scenario_7 or scenario_8 or scenario_10" -v`, and paste the pass lines into `## Results`. These tests generate, through the real routes with no LLM, the DPDPA+ISO Devanagari/₹ board PDF, and read back its text, fonts and metadata. They also check that the Workpaper snapshot renders offline.
   2. **Manual board-report check** in the running app (`uvicorn app.main:app --host 127.0.0.1`):
      - For a released DPDPA+ISO assessment, set the company name to a Devanagari name and add a Finding whose description contains `₹`.
      - Open `/api/assessments/{id}/board-report/preview`.
      - Generate a "Board report v2 (PDF)" version on `/assessments/{id}/snapshots` and download it.
      - Check the text: `python -c "import pdfplumber,sys; p=pdfplumber.open(sys.argv[1]); print(p.metadata['Title']); print('\n'.join(x.extract_text() or '' for x in p.pages))" file.pdf`. Confirm ₹ and the cover lines, and that the Title is the exact Devanagari name.
      - Open the PDF in Preview and confirm the Devanagari renders with correct conjuncts (for example प्रा, ट्).
   3. **Manual Workpaper check.** Generate a Workpaper version, save the "View" page as a file, turn Wi-Fi off, and open it from disk: it must be styled and complete.
   4. **CI.** Watch the first CI run of the PR: the "Renderer smoke" step must pass on `ubuntu-latest`, and the pytest step must show no P6-8 skips.
7. When the orchestrator launches Codex with `codex exec`, stdin must be redirected: `codex exec ... < /dev/null`.

**About reading Devanagari back.** Text extraction from a PDF does not round-trip Devanagari exactly. Pre-base matras (ि) and conjuncts come out reordered or split (`लिमिटेड` → `लि मिटेड`); this is a limitation of PDF ToUnicode maps, not a rendering defect. So the tests check Devanagari four ways:
- the exact PDF Title metadata
- a code-point multiset check on the cover
- which font drew each glyph
- the exact string in the HTML and JSON document

₹ and Latin text are checked exactly.

## Adversarial review checkpoints `[AR]` (after Codex, before the PR)

1. **Write-once.**
   - Can any code path write to an existing snapshot's PDF or sidecar, re-render an old version, or serve anything but stored bytes?
   - Is `_store`'s cleanup limited to files this call wrote, so an `xb` collision on someone else's file is never unlinked?
   - Is `issue_snapshot` still one-way?
2. **Sidecar integrity.** Is the tamper check applied on issue? Is `read_board_report_document` the only reader, and does it hash-check before parsing?
3. **Approved-only.**
   - Does every client-facing field trace to `approved_report` rows, approved Findings or the recorded basis?
   - Does any field read a raw proposal, `GapItem`, `GapReport` text or an unreviewed Conclusion?
   - Do risk, priority and score come only from the approved row or deterministic scoring?
4. **Offline.**
   - Can any template or user string make WeasyPrint fetch a resource?
   - Is `FatalURLFetchingError` always converted?
   - Does the standalone Workpaper contain any external reference, including in user text rendered unescaped?
5. **Golden.** Read the whole `tests/golden/p6_8_board_document.json` once. Every value must be explainable from the fixture, and no volatile value may escape normalisation.
6. **Conditional copy.** Walk each framework set: each single framework, DPDPA+ISO, ISO+NIST, all six. Is there legal wording for standards-only sets, missing standards wording anywhere, or DPDPA text outside a DPDPA report?
7. **Injection.** Is user text ever inside `<style>`, a CSS string, an attribute without quotes, or `|safe`?
8. **Degradation.** Without Pango: does the app start, does generation give a clean 503 with nothing written, and does the preview still work (it needs no WeasyPrint)?
9. **File set.** The diff must match D-P6-8-K exactly, with no `main.py`, `web.py`, `pdf_export.py` or fixture change, and nothing under `validation/` or `scripts/`.

## Ready-to-paste Codex prompt (P6-8 B1)

```
You are implementing P6-8 B1 (board report v2 + standalone Workpaper) in /Users/saqlainmomin/dpdpa-gap-tool-p6-8 on branch claude/p6-8-board-report-v2.

Read first, fully: tasks/handoffs/2026-09-28-p6-8-board-report-v2.md (the spec) and tests/test_p6_8_board_report_v2.py (the contract). Also read CLAUDE.md and AGENTS.md.

Rules:
- The contract tests are the contract. Make all 14 in tests/test_p6_8_board_report_v2.py pass WITHOUT editing that file. Do not skip, xfail, weaken or delete any test. If a test looks wrong, leave it failing and explain in the handoff's ## Results.
- Implement exactly the decisions D-P6-8-A..L. Names, signatures, constants, routes, snapshot type, metadata keys, document keys and rendered strings are fixed. If the code forces a deviation, stop and report it in ## Results; do not pick an alternative.
- Touch only the files in D-P6-8-K. Apply exactly the four existing-test edits in D-P6-8-L. Everything under "Do not touch" is off limits.
- You have no network and cannot write .git: no pip install, no downloads, no git add/commit/branch/stash. The orchestrator has already installed weasyprint==70.0 into .venv and placed the Noto fonts and OFL files in app/assets/fonts/noto/ (verify their sha256 against the handoff; if missing or different, stop and report).
- Answer-key independence: never open, grep, list or glob validation/**, tasks/handoffs/*p5-9*, docs/plans/2026-09-24-002-*, scripts/seed_test_companies.py, scripts/test_ground_truth.json, scripts/seed-v2-prompt.md, scripts/validation/**, tests/test_validation_harness.py or any answer_key.json. Scope every search to explicit paths (app/, tests/test_p6_8_*.py, the files you edit).
- No LLM calls anywhere. No migration, no model change.

Steps:
1. Step 0 in the handoff: run the full suite (.venv/bin/pytest -q -p no:cacheprovider), record counts, confirm the listed facts.
2. Implement html_pdf.py, board_report.py, standalone_workpaper.py, the two report templates, report_snapshots.py, snapshots.py, the report_snapshots.html block, requirements.txt, .github/workflows/tests.yml and Dockerfile, as specified.
3. Apply the D-P6-8-L test edits.
4. Record the golden once: P6_8_RECORD_GOLDEN=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_p6_8_board_report_v2.py -k golden (unless the orchestrator says it will), then run the file without the variable, twice, and once with CYBERASSESS_REQUIRE_WEASYPRINT=1.
5. Run the neighbour set and the full suite (Verification 1-5). The only acceptable failures are the two uncommitted-tree guards named in D-P6-8-L.
6. Append ## Results to the handoff: baseline counts, final counts, the smoke pass lines (Verification 6.1), the golden file size and top-level keys, any deviation or doubt. Change nothing else in the handoff.
```

## Open questions for Saqlain (each has a default; nothing here blocks B1)

1. **Issued stamp.** Should an issued board report carry "Issued" in the PDF?
   - The problem: versions are write-once and issuing does not re-render, so today the PDF only states that issue status lives in the version history.
   - **Default:** keep it that way.
   - If a stamped copy is wanted, issuing could additionally produce a separate "issue certificate" (a one-page PDF with the version, SHA-256, issuer and time, linked to the version) without touching the report bytes. That would be a later task.
2. **Retiring the fpdf2 `gap_report`.**
   - **Default:** keep both types offered until B2 and P6-9 merge and one real engagement has run on v2. Then hide "Generate" for `gap_report`; old versions stay downloadable.
3. **DPDPA penalty exposure in the board report.** The ₹ crore Schedule map lives only in the web view (`web.py` `_PENALTY_MAP`, signed off in P6-0d).
   - **Default:** not in P6-8. P6-9 moves the map to `app/dpdpa/`, which is a `web.py` change that P6-8 avoids while P6-7a is in flight, and adds a DPDPA-conditional "maximum exposure" line.
4. **A P6-6 label bug found while designing.**
   - `pdf_export._regimes` returns framework **names**, and `_follow_on_text` and `_disclaimer_text` then pass those names to `_framework_label`, which expects **ids**. Unknown ids are upper-cased, so reports print "INDIA DPDPA" instead of "India DPDPA".
   - It affects both the fpdf2 reports and v2, which reuse the helpers. It is visible on the v2 limitations page: "(for INDIA DPDPA requirements)".
   - **Default:** fix it in a tiny separate PR that touches `pdf_export.py` only (`_regimes` keeps ids, or the call sites stop re-labelling) and re-records the canonical DPDPA golden hash, with the reviewer checking that the text diff is exactly the label. v2 inherits the fix, and the P6-8 golden is re-recorded under D-P6-8-J.
   - Not in P6-8, because `pdf_export.py` is frozen for this PR.
5. **Top risks.**
   - **Default:** up to 10, ranked by the consultant-set Finding severity, then priority. Say if the board should see fewer (5) or rank by risk level instead.
6. **Evidence register scope.**
   - **Default:** the assessment's own non-rejected evidence (active and superseded versions) plus any engagement-level version cited by an approved conclusion. Say if superseded versions should be hidden.
7. **Fonts in the standalone Workpaper.**
   - **Default:** not embedded (system fonts render Devanagari in every current browser). Embedding the two Noto families as base64 would add about 1.6 MB to every Workpaper version.

## Self-review (designer, before dispatch)

1. **Probed before specifying.** WeasyPrint 70.0 on macOS (Homebrew pango 1.57.1) rendered Devanagari and ₹ with the vendored fonts. It also showed four things:
   - Identical bytes for identical HTML, given `dcterms.created`.
   - The Title metadata round-trips Devanagari exactly; body text extraction does not (see the smoke plan).
   - 70.0 changed the fetcher API: a plain function fetcher crashed with `_fail_on_errors`. That is why the version is pinned and a `URLFetcher` subclass is specified.
   - `@page` margin boxes do not inherit the body font when the family is set on `body` only. The probe drew Times New Roman there. So the family is set on `html` and on `@page`, and scenario 7 checks every drawn glyph's font.
2. **Autoescape in `<style>`.** The first reference passed the font CSS as a plain string. Jinja escaped `'` to `&#39;`, every face silently failed, and macOS fonts were drawn. Scenario 7 caught it. Hence `Markup(...)` for the two trusted constants and "no `|safe`" in templates.
3. **Existing source guards.** `test_report_snapshots.py` scenario 3 pins one `.unlink(` per file. The first reference added a second one. The RFI code had dodged the count with `getattr`. Instead of another dodge, `_store` now cleans up every file it wrote in one loop, and the router has one cleanup loop over `snapshot_files`. The guard's intent (one deletion path) holds.
4. **A standalone-Workpaper route was dropped.** `test_workpaper.py` pins exactly one `/workpaper` route. The snapshot is the standalone artefact, and scenario 10 plus the edited `test_report_snapshots.py` scenario 7 compare it with `standalone_workpaper.render`.
5. **The preview lives in the snapshots router, not a new router.** That avoids `main.py`, a file P6-7a edits.
6. **Golden design.** The first golden normalised "today" by value. Because the fixture's `generated_at` date equalled the run date, it also rewrote `generated_on` and would have broken the next day. Normalisation is now by key (`decided_on`, `added_on`, `released_on`).
7. **Only approved data.** Release requires every in-scope Conclusion to be approved, so "approved-only" was trivially true in the fixture. Scenario 4 now injects an unreviewed out-of-scope Conclusion after release (release stays valid) and asserts it is absent. A mutation that read all Conclusions was caught.
8. **What was not verified here.** CI on Ubuntu was not run. The apt package names come from WeasyPrint's documentation for Ubuntu 20.04 and later, and the workflow's "Renderer smoke" step fails fast if they are wrong. The Docker image was not built.

## Results

- Baseline before implementation: `.venv/bin/pytest -q -p no:cacheprovider` — **1059 passed, 10 skipped, 13 failed** in 127.57s. The 13 failures were the expected missing P6-8 modules/workflow/golden.
- Contract suite: `.venv/bin/pytest -q -p no:cacheprovider tests/test_p6_8_board_report_v2.py` — **14 passed**. Repeated twice without the environment override and once with `CYBERASSESS_REQUIRE_WEASYPRINT=1`; each run passed 14 tests.
- Required rendered smoke: `tests/test_p6_8_board_report_v2.py .... [100%]` and **4 passed, 10 deselected in 4.26s** for scenarios 3, 7, 8 and 10.
- Neighbor regression set: **111 passed, 1 failed, 64 warnings**. The sole failure is the expected uncommitted-tree guard `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes`; it sees the two mandated existing-test edits.
- Full suite: `.venv/bin/python -m pytest -q` — **1070 passed, 10 skipped, 2 failed** in 121.61s. Both failures are the expected uncommitted-tree guards: `tests/test_longitudinal_demo.py::test_scenario_13_protected_surface_is_unchanged` sees the permitted `report_snapshots.py` and `requirements.txt` changes, and the retention guard above sees the mandated test edits. They are expected to pass after the orchestrator commits the working tree.
- Golden: `tests/golden/p6_8_board_document.json`, **17,413 bytes**, recorded once with `P6_8_RECORD_GOLDEN=1`. Top-level keys: `appendices`, `assessment_id`, `basis`, `company_name`, `engagement_name`, `firm_name`, `framework_sections`, `frameworks`, `kind`, `not_assessed`, `release`, `roadmap`, `schema_version`, `sign_off`, `snapshot`, `source`, `summary`, `top_risks`.
- Deviation: none from D-P6-8-A through D-P6-8-L. The frozen-surface check and scenario 14 file-set guard are both green.

### Orchestrator smoke (2026-09-28, after commit)
- Pre-steps done: `weasyprint==70.0` is in the shared `.venv` (Homebrew pango 1.57.1). The fonts were fetched from the notofonts releases and all 6 sha256 values match the pins.
- With `CYBERASSESS_REQUIRE_WEASYPRINT=1`, scenarios 3, 7, 8 and 10 give 4 passed. The full suite gives 1072 passed and 10 skipped, with no P6-8 skips.
- **Board PDF read-back.** A DPDPA+ISO fixture was generated through the real routes, with no LLM, and read back with pdfplumber:
  - 13 pages, 42 KB. The Title metadata is exactly `Board report: भारत डेटा प्राइवेट लिमिटेड`.
  - The ₹ text reads back exactly. There are 0 `?` and 0 `Rs.`.
  - The fonts used are Noto Sans, Noto Sans Bold, Noto Sans Devanagari and Noto Sans Devanagari Bold, plus a synthesised oblique.
  - The cover was rendered to PNG and inspected. The Devanagari shapes correctly (प्रा, लि, टेड), and the period, cut-off and draft notice are present.
- **Standalone Workpaper**, from the stored bytes: no `http(s)://`, `/static`, `<script`, `<link` or `url(`, and one inline `<style>`. All 5 entries are present.
- **Pending:** the first CI run on ubuntu-latest (renderer smoke step) and the Docker build are both unverified locally.
