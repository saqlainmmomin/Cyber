# P6-0c: Dev hygiene (CI, Python pin, SQLite WAL, localhost guard, failing tests)

This task makes `main` green and keeps it green. It has four parts. It adds a GitHub Actions workflow that runs pytest on Python 3.13, which today shows zero checks on every PR. It pins Python and the dev dependencies. It turns on SQLite WAL mode with a busy timeout, because parallel batches now write while the portal reads. It removes the wide-open CORS policy and makes the local-only bind explicit. It also fixes the five tests that fail on `main` today, one of which writes to the real developer database. CI cannot go green until those five are fixed.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`, Track 0 (the `tasks/todo.md` line: "P6-0c dev hygiene (CI, `.python-version`, SQLite WAL) … localhost guard (bind 127.0.0.1, CORS to local origin)").
**Owner:** Claude designs (this file) → Codex implements → Claude reviews.
**Branch / worktree:** `codex/p6-0c-dev-hygiene` in `/Users/saqlainmomin/dpdpa-gap-tool-dev-hygiene`. The designer fast-forwarded it to `origin/main` @ `beeacf9` (PR #61 merged). It has no commits of its own. `.venv` is a symlink to the primary checkout's venv, which already has `pytest` and `httpx`.
**Depends on:** nothing. **Blocks:** nothing directly, but every later PR benefits from a real CI check.

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, file name, value and test scenario below.

> **You cannot write `.git`.** The orchestrator commits, pushes and opens the PR. Do not run `git commit`, `git add`, `git stash`, `git checkout`, `git branch -f` or anything else that writes refs or the index. Read-only git (`diff`, `show`, `log`, `merge-base`, `rev-parse`) is fine.

> **No attribution lines anywhere.** No `Co-Authored-By`, no "Generated with" footer, and no tool or agent names in code, comments, the workflow file or `## Results`.

> **Answer-key independence (D-P5-9-C).** Do not open, grep, list or read any of the following:
> - anything under `validation/` (packs, `answer_key.json`, rendered output, runs)
> - `tasks/handoffs/*p5-9*`
> - `docs/plans/2026-09-24-002-*`
> - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
>
> Scope every `grep`/`rg`/`find` so it cannot reach them. For example, use `grep -rn … app tests/*.py tests/integration` rather than `grep -rn … .`. Several tests import `scripts.seed_test_companies`. Running them is fine. Opening the script is not. `tests/test_answer_key_isolation.py` forbids the strings `answer_key`, `validation/companies`, `scripts.validation` and `scripts/validation` anywhere under `app/`.

## Goal

1. Every PR to `main`, and every push to `main`, runs the full pytest suite on Python 3.13 in GitHub Actions. It needs no secrets and makes no live LLM or network calls.
2. On `main`, the suite passes with **0 failed and 0 errors** (skips allowed), locally and in CI. A fresh checkout leaves no `data/dpdpa.db`.
3. The app's SQLite engine runs in WAL mode with a 30 s busy timeout. Restore stays correct under WAL.
4. No cross-origin site can make credentialed reads against the dev server. Every documented way of starting the server binds `127.0.0.1` explicitly.

## Step 0 (before writing code)

1. From the worktree, run `git rev-parse HEAD main origin/main` and record all three. `HEAD` and `main` must be equal, which they were at `beeacf9…` when this was written. If they are not, stop and report, because the orchestrator must re-sync before you start. Do not move refs yourself. `origin/main` is informational only, because your sandbox may not be able to fetch.
2. Run `rm -rf data && .venv/bin/python -m pytest -q -p no:cacheprovider` and record the counts in `## Results`. The designer's run on `beeacf9` (2026-09-26, ~104 s) gave **4 failed, 738 passed, 10 skipped, 1 error**:
   - `tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting`, which fails about 50% of runs
   - `tests/test_p5_4_adaptive_ucc_questionnaire.py::test_scenario_13_structural_guards`
   - `tests/test_p6_nist_csf2_alignment.py::test_dependencies_and_criteria_pending_rule`
   - `tests/test_remediation_tracking.py::test_scenario_10_engagement_rollup_and_tracker_page`
   - ERROR at teardown of `tests/test_workpaper.py::test_smoke_full_assessment_traceability`, from the dev-database guard

   **These five are expected. Do not stop on them. This task fixes them.**

   The designer also ran a CI-like run: a fresh `python3.13 -m venv` with only `requirements.txt` + `pytest==9.1.1` + `httpx==0.28.1`, no `.venv` directory, no `.env`, and `OPENROUTER_BASE_URL=http://127.0.0.1:9/api/v1` with dead `HTTP(S)_PROXY`. That run gave the same results plus one more failure, `tests/test_p5_6_rfi_rebuild.py::test_scenario_22_standing_guards_remain_satisfied`, because it shells out to `.venv/bin/alembic` (fact 9). Nothing reached the network and no test needed `OPENROUTER_KEY`.
3. Confirm the facts below. Line numbers are from `beeacf9`. **If any is false, stop and report.**

### Facts (verified by the designer on `beeacf9`; re-verify)

**CI and dependencies**

1. `.github/` does not exist. `requirements.txt` has 15 runtime pins and no test tooling. `pytest` (9.1.1) and `httpx` (0.28.1, needed by `fastapi.testclient`) are installed in `.venv` but declared nowhere. There is no `pytest.ini`, `pyproject.toml`, `setup.cfg` or `tox.ini`. No test uses `pytest-asyncio`/`anyio` markers. Only `tests/test_performance_benchmarks.py:36` has a `skipif` (`CYBERASSESS_RUN_BENCHMARKS`).
2. No system packages are needed. No test or app module uses WeasyPrint, `add_font` or TTF files. `app/static/css/tailwind.css` is gitignored and not needed by tests.
3. Tests never need `OPENROUTER_KEY`. `app/services/llm_client.py:143-152` builds the `OpenAI` client lazily from `settings.openrouter_key`/`openrouter_base_url`, and tests patch the seams (`claude_analyzer._call_llm`, `desk_review._call_llm`, `tests/support/analyzer_mock.py:71,96`). `app/config.py:87` reads `.env` only if it exists, and environment variables override it.

**SQLite engine**

4. `app/database.py:28-40`: `ensure_sqlite_parent_dir(settings.database_url)` runs at import time and creates `data/`. The module-level `engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})` sets only `PRAGMA foreign_keys=ON` in a `connect` listener (`set_sqlite_pragma`, L36-40). There is no WAL and no explicit busy timeout; pysqlite's default is 5 s. No other module imports `set_sqlite_pragma`. Tests build their own engines and do **not** go through this listener.
5. `scripts/backup.py:66-73` copies with `sqlite3`'s online backup API, which is WAL-safe. `scripts/restore.py:48-53` (`_copy_database_for_safety`: `shutil.copy2` of the live file), L150-155 (`db_path.unlink()`) and L164-166 (`shutil.copy2(backup_db, db_path)`) copy and replace the bare `.db` file only. They ignore `-wal`/`-shm` sidecars.

**Localhost guard**

6. `app/main.py:130-136`: `CORSMiddleware(allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])`. With a wildcard origin and credentials, Starlette echoes the caller's `Origin` back when a cookie is present, so any website can make credentialed reads. The app is server-rendered Jinja2 + HTMX and every request is same-origin. Nothing in `app/`, `tests/` or the templates relies on CORS: a grep for `cors|access-control|allow_origins` outside tag strings finds only `app/main.py`.
7. Server launch points:
   - `.claude/launch.json` (`runtimeArgs: ["app.main:app", "--port", "8001"]`)
   - `README.md:75`
   - `CLAUDE.md:21`
   - `AGENTS.md:22`
   - `.claude/skills/run/SKILL.md` and `.agents/skills/run/SKILL.md` (`uvicorn app.main:app --reload`)
   - `Dockerfile:12` (`--host 0.0.0.0`, which is correct *inside* a container)
   - `docker-compose.yml` (`ports: "8000:8000"`, which publishes on all host interfaces, plus a stale `ANTHROPIC_API_KEY`)

   `app/main.py` has no `__main__` block and there is no Makefile. Uvicorn's own default host is `127.0.0.1`. The only real exposure is docker-compose, and nothing is explicit.

**The five failing tests: root causes**

8. **Guard tests diff against bare `main`.** The following use the one-argument form `git diff main -- …`, which compares the working tree to the tip of `main`:
   - `tests/test_p5_4_adaptive_ucc_questionnaire.py:563, 949, 956`
   - `tests/test_p5_3_framework_desk_review.py:814, 822, 835`
   - `tests/test_p5_2_reader_migration.py:806`
   - `tests/test_p5_6_rfi_rebuild.py:1008` (which also has no `check=True`, so a missing `main` ref passes silently)

   When `main` moves ahead of a branch, main's newer changes show up reversed. That is how `test_scenario_13_structural_guards` failed on the designer's first run, before the fast-forward: `app/frameworks/criteria/nist_csf_draft.py | 135 +++---`, from #61. Separately, **`test_p5_4…:955-959` asserts a PR delta.** It requires `git diff main -- app/routers/analysis.py` to contain `+            "answer_source": r.answer_source,` exactly once. After P5-4 merged, that diff is empty on `main`, so the test fails there by construction (`assert 0 == 1`, L958). The line itself is present once at `app/routers/analysis.py:129`.
9. **Hard-coded venv paths.**
   - `test_p5_4…:967` and `test_p5_6…:1017` run `.venv/bin/alembic heads`, which does not exist in CI.
   - `tests/test_retention.py:622`, `test_p5_2…:810` and `tests/test_correctness_bundle.py:853` run bare `alembic`. That resolves to whatever is first on `PATH`; locally that is `/Users/saqlainmomin/miniconda/bin/alembic`, not the venv.
   - `.venv/bin/python -m alembic heads` prints `8b2d5f7e1c34 (head)`.
10. **NIST test asserts a PR delta.** `tests/test_p6_nist_csf2_alignment.py:337` asserts `set(current_draft) - set(main_draft) == new_ids`, where `main_draft` comes from `git show main:app/frameworks/criteria/nist_csf_draft.py` (`_main_namespace`, L44-50). After #61 merged, current equals main, so the left side is `set()` and the test fails on `main` by construction. `_main_namespace` is also used at L138, 223, 258 and 384. Those uses compare *unchanged* fields for equality, so they pass post-merge. They use `main`'s tip rather than the fork point, so they would go stale on a branch that falls behind.
11. **Remediation test uses a hard-coded date.** `tests/test_remediation_tracking.py:923` and `:937` set target dates from `date.today() ± 1 day` (local wall clock). `:949` then evaluates the rollup at the hard-coded `today = date(2026, 9, 24)`. On 2026-09-26, `a_open`'s target (09-25) is not before 09-24, so `overdue` is 0 against the expected 1 (`{'overdue': 0} != {'overdue': 1}`, L951). The page render later in the same test (L982-990) uses the service's own clock, `remediation_rollup._date_today` = `datetime.now(timezone.utc).date()` (`app/services/remediation_rollup.py:74-75`). So the test mixes local-today, UTC-today and a frozen date.
12. **Longitudinal ordering flake: the test expects the wrong order.** `tests/test_longitudinal_demo.py:470` expects `source["assessments"]` in chronological order `[baseline, validation]`. `app/services/report_content.py:337` builds that manifest deliberately in **assessment-id order** (`sorted(sections, key=lambda item: item.assessment_id)`, unchanged since P3-3 `399511c`). The same function also sorts `excluded_assessment_ids` and `finding_ids`, because it is a canonical, write-once snapshot manifest. `tests/test_pdf_updates.py:843` (scenario 5) pins exactly that id order. Assessment ids are random UUIDs, so the longitudinal test passes about half the time. The query `ORDER BY` (`report_content.py:273`, `remediation_rollup.py:158`: `created_at, id`) is deterministic and is not the cause. Observed failure: `At index 0 diff: '55314435-…' != '63e073f1-…'`.
13. **The dev-DB leak is not in `test_workpaper`.** The session-scoped guard `tests/conftest.py:33-47` checks `data/dpdpa.db` at session teardown, so pytest reports its failure as an ERROR on the **last test collected**, which happens to be `test_workpaper.py::test_smoke_full_assessment_traceability`. The actual writer is **`tests/integration/test_desk_review.py::test_trigger_desk_review`** (L25-48):
    - `POST /assessments/{id}/run-desk-review` queues `_bg_run` (`app/routers/web.py:2539-2543`), which opens `with SessionLocal() as bg_db:`. `SessionLocal` is bound to the module-level dev engine (fact 4).
    - The test overrides `get_db` but not `SessionLocal`. Its mock `run_desk_review` queries through `bg_db`, so the dev engine connects and SQLite creates a 0-byte `data/dpdpa.db`. The query then fails ("no such table") inside the background task, and that failure is swallowed.
    - **Why it is intermittent:** the guard only fails when the file did not exist before the run. The first run in a fresh checkout or worktree fails. Every later run passes, because the 0-byte file already exists and is not modified. CI is always a fresh checkout, so it would always fail. The designer reproduced this: running that one file in a clean tree gives `1 passed, 1 error`, and running it again gives `1 passed`.
    - `tests/integration/test_analysis.py:57` already shows the correct pattern: `patch("app.database.SessionLocal", return_value=db_session)`.
    - With WAL on (D-P6-0c-E), even a leak that only *reads* an existing dev DB would rewrite its header. That would make the leak fail on every run, which is one more reason to fix it here.

**Guards that constrain this task's own diff** (so CI passes on this PR)

14. These guards are relevant to what this task touches:
    - `tests/test_p6_nist_csf2_alignment.py:409` (three-dot) protects `app/config.py`, `app/services`, `app/routers`, `app/models`, `alembic`, `app/frameworks/{schema,prompts,batching,compat,registry}.py`, the definitions, `tests/fixtures` and `tests/support`.
    - `tests/test_longitudinal_demo.py:562-579` (working tree) protects `requirements.txt`, `scripts/backup.py`, `app/routers/web.py`, `tests/test_phase1_prefill.py` and others.
    - `tests/test_retention.py:1612-1629` fails whenever **any** file under `tests/` is modified and uncommitted. It will fail during your run and passes once the orchestrator commits (see Verification).

    This task touches none of the protected paths. That is deliberate, and it is why D-P6-0c-F adds no Settings field.

## Decisions (made here so they are not relitigated)

### D-P6-0c-A: CI workflow, `.github/workflows/tests.yml` (new)

Use exactly this shape. Keep the comments short.

```yaml
name: tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: tests-${{ github.ref }}
  cancel-in-progress: true

jobs:
  pytest:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # guard tests run `git diff main...HEAD` and `git merge-base`
      - name: Provide a local main ref for guard tests
        run: |
          git show-ref --verify --quiet refs/heads/main || git branch main origin/main
          git rev-parse main HEAD
      - uses: actions/setup-python@v5
        with:
          python-version-file: .python-version
          cache: pip
          cache-dependency-path: |
            requirements.txt
            requirements-dev.txt
      - name: Install dependencies
        run: python -m pip install -r requirements-dev.txt
      - name: Run tests
        env:
          OPENROUTER_KEY: ""
          OPENROUTER_BASE_URL: "http://127.0.0.1:9/api/v1"   # any unstubbed LLM call fails fast
          HTTP_PROXY: "http://127.0.0.1:9"
          HTTPS_PROXY: "http://127.0.0.1:9"
          NO_PROXY: "localhost,127.0.0.1,testserver"
        run: python -m pytest -q
      - name: Suite must not create the developer database
        run: test ! -e data/dpdpa.db
```

**Why each piece.**

- **`fetch-depth: 0` plus the `main` step.** On `pull_request`, `actions/checkout` checks out the detached merge commit and creates no local `main`. The guard tests call `git diff main...HEAD`, `git merge-base HEAD main` and `git show <ref>:path`, so a local `main` must exist. On a `push` to `main`, checkout already creates local `main`, so the `show-ref ||` form skips branch creation. A bare `git branch main origin/main` would fail there because the branch already exists. In the PR merge commit, `main...HEAD` is exactly the PR's changes, which is the intended guard scope.
- **Dead `OPENROUTER_BASE_URL` and proxy.** The designer's CI-like run passed with both, so any future test that accidentally goes live fails loudly and never spends money. There is no `.env` in CI.
- **No `.venv` in CI.** D-P6-0c-D removes the only `.venv` dependencies.
- **`python -m pytest`.** It matches the local invocation and puts the repo root on `sys.path`.
- **Deliberately not in scope:** no matrix (3.13 only, and 3.14 is known-broken), no lint, no coverage, no Tailwind or Node build, no Docker build, no scheduled runs.

### D-P6-0c-B: Python pin and dev dependencies

- **`.python-version` (new).** Exactly `3.13` plus a newline. pyenv, uv and `setup-python` (`python-version-file`) all read it.
- **`requirements-dev.txt` (new).** Exactly:
  ```
  -r requirements.txt
  pytest==9.1.1
  httpx==0.28.1
  ```
  These are the versions in `.venv`. The designer verified that a fresh 3.13 venv with only these three lines installed runs the whole suite (Step 0.2). Do **not** add anything else, such as pytest-xdist, freezegun, pytest-cov or PyYAML. D-P6-0c-G avoids freezegun on purpose.
- **`requirements.txt` is not touched** (fact 14).
- **Docs.** In `README.md` "Running", `CLAUDE.md` "Running" and `AGENTS.md` "Running", change `pip install -r requirements.txt` to `pip install -r requirements-dev.txt`. Only these lines change (and the host flag in D-P6-0c-F). `CLAUDE.md` has a word-count contract, so make no other edits there.

### D-P6-0c-C: Guard-test hygiene (the rule, then the call sites)

**The rule.** A guard must pass on `main` after its PR merges. It must also pass on any later branch that does not touch the surface it protects. Concretely:

1. **Diff against the fork point, never the tip.** Every `git diff … main -- …` becomes `git diff … main...HEAD -- …`, keeping the same flags (`--stat`, `-U0`) and the same pathspecs, including the existing `:!`/`:(exclude)` entries and their comments. Every one of these `subprocess.run` calls gets `check=True` if it lacks it. That covers `test_p5_6…:1007-1014`, so a missing ref fails loudly.
   - Call sites: `test_p5_4…:563`, `:949`; `test_p5_3…:814`, `:822`, `:835`; `test_p5_2…:806`; `test_p5_6…:1008`.
2. **Assert invariants, not deltas.**
   - **`test_p5_4…:955-959`.** Replace the `analysis_diff` subprocess and its two assertions with one post-merge invariant:
     ```python
     analysis_source = (REPO_ROOT / "app/routers/analysis.py").read_text()
     assert analysis_source.count('"answer_source": r.answer_source,') == 1
     ```
   - **`test_p6_nist_csf2_alignment.py:337`.** Change it to `assert set(nist_csf_draft.NIST_CSF_CRITERIA_DRAFT) - set(main_draft) <= new_ids`. On the P6-2d branch the set was exactly `new_ids`. Post-merge it is empty. Either way, no id other than the 13 new ones may appear. Leave the rest of the test as it is. The loop at L338-342 already skips `new_ids`, and the later "all 106 drafted" assertions are the real invariant.
   - **`_main_namespace` (`test_p6_nist_csf2_alignment.py:44-50`).** Make it read the fork point, consistent with rule 1: resolve `git merge-base main HEAD` once (with `check=True`), then `git show <merge_base>:{path}`. Its five callers are unchanged.
3. **Never hard-code a venv or rely on `PATH` for alembic.** Replace all five `alembic heads` invocations (fact 9) with `[sys.executable, "-m", "alembic", "heads"]`, with the same `cwd`, the same `check`/`capture_output`/`text` kwargs and the same assertions. Add `import sys` where it is missing.
4. **Do not touch** these, which are already correct or out of scope:
   - the three-dot guards in `test_p6_1_llm_plumbing.py:766`, `test_p6_1b_framework_batching.py:766` and `test_p6_nist_csf2_alignment.py:409`
   - `test_validation_harness.py:386-426`, which already uses `merge-base` and skips when the harness is untouched
   - the working-tree guards in `test_longitudinal_demo.py:562-579` and `test_retention.py:1612-1629`
   - every `grep`-based source guard
5. **A meta-guard stops this from coming back.** It lives in the new test file; see scenario 9.

**Why not delete the P5-era protected-surface guards?** They still protect scoring, reports, models and alembic, and removing them is a policy change for Saqlain to make. Three-dot keeps their intent. They do still veto any future PR that touches those paths. That is the existing house convention: add a pathspec exclude with a comment in the PR that needs it. Do not change it here.

### D-P6-0c-D: No test depends on `.venv`

This is covered by D-P6-0c-C.3. After the change, `grep -rn '\.venv' tests/*.py tests/integration` must return nothing. `tests/fixtures/canonical_dpdpa/README.md` is documentation and is out of scope.

### D-P6-0c-E: SQLite WAL and busy timeout (`app/database.py`)

Restructure the engine setup so it can be tested without connecting to the dev DB:

```python
SQLITE_BUSY_TIMEOUT_MS = 30_000

def _configure_sqlite_connection(dbapi_connection, connection_record) -> None:
    """Per-connection pragmas. WAL + busy_timeout only for file-backed databases."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        main_file = next(row[2] for row in cursor.execute("PRAGMA database_list") if row[1] == "main")
        if main_file:  # "" for in-memory and temporary databases
            cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
            cursor.execute("PRAGMA journal_mode=WAL")
    finally:
        cursor.close()

def create_app_engine(url: str) -> Engine:
    engine = create_engine(url, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", _configure_sqlite_connection)
    return engine

ensure_sqlite_parent_dir(settings.database_url)
engine = create_app_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
```

- **Order.** `busy_timeout` is set before `journal_mode=WAL`. The switch to WAL briefly needs an exclusive lock, and with the timeout set first it waits instead of failing.
- **Behaviour kept.** `foreign_keys=ON` is still set on every connection, as today. `engine`, `SessionLocal`, `Base`, `get_db` and `ensure_sqlite_parent_dir` keep their names and behaviour, because tests monkeypatch `app.database.SessionLocal` and `app.main` reads `database.engine.url`. `set_sqlite_pragma` is removed. It has no other references (fact 4).
- **Why 30 s.** Worker threads never hold DB sessions (P6-1b). Contention comes from HTMX polling reads and request writes while a long persist commits. WAL removes reader/writer blocking. Writer/writer waits are short, and 30 s bounds the worst case without hanging requests forever. pysqlite's 5 s default is too tight for a large analysis persist.
- **Not added:** `synchronous=NORMAL`, `journal_size_limit` and `wal_autocheckpoint` tuning. WAL defaults are fine at this scale.
- **Alembic.** `alembic/env.py` builds its own engine. That is fine because WAL mode persists in the database file once any app connection sets it. Do not touch `alembic/`.

**Restore under WAL (`scripts/restore.py`).** This is a required consequence of WAL. After a crash, committed rows can live only in `dpdpa.db-wal`, and restore copies and replaces only `dpdpa.db` (fact 5). The safety copy would silently miss data. Worse, a stale `-wal` left beside a restored file can be replayed onto it.

- Add two helpers:
  - `_checkpoint_wal(db_path: Path) -> None` opens `sqlite3.connect(db_path)`, runs `PRAGMA wal_checkpoint(TRUNCATE)` and closes. Opening the file recovers a crash-left WAL. The checkpoint folds it into the main file, and closing the last connection removes the sidecar.
  - `_assert_wal_empty(db_path: Path) -> None` raises `RuntimeError("Live database has an active write-ahead log; stop the app and retry the restore")` if `Path(f"{db_path}-wal")` exists with size > 0.
- In `restore_backup`, call both in that order, only when `db_path.exists()`. Put the calls **after** the confirmation prompt and **before** `safety_dir` is created (`restore.py:133-138`). A refusal then leaves no empty `pre-restore-*` directory and no live file touched.
- Right after `db_path.unlink()`, also unlink `f"{db_path}-wal"` and `f"{db_path}-shm"` if they exist.
- Change nothing else in the rollback logic. `scripts/backup.py` needs no change (the backup API is WAL-safe) and must not be touched (fact 14).

**Dev-DB guard (`tests/conftest.py:22-47`).** Extend `_dev_db_fingerprint` so the session guard also fails if `data/dpdpa.db-wal` or `data/dpdpa.db-shm` appears or changes during the run. Keep the existing message. Include the sidecar existence and size in the fingerprint.

### D-P6-0c-F: Localhost guard

- **Remove `CORSMiddleware` entirely.** Delete the `app.add_middleware(CORSMiddleware, …)` block (`app/main.py:130-136`) and its import (L8). Add **no** Settings field.
  - *Why not an allowlist of local origins?* CORS only ever *relaxes* the same-origin policy. This app is same-origin by construction (fact 6), so it needs no relaxation. An allowlist such as `http://localhost:3000` would grant credentialed reads to *other* local apps, which is strictly worse than none. Removing the middleware is the "local origin only" outcome: browsers already allow same-origin requests.
  - *Why no Settings field?* There is no consumer. Adding one would also edit `app/config.py`, which the NIST three-dot guard protects (fact 14). If a cross-origin consumer ever appears, add an explicit `cors_allow_origins: list[str] = []` then.
- **Explicit bind everywhere a human or agent starts the server:**
  - `.claude/launch.json`: `runtimeArgs` becomes `["app.main:app", "--host", "127.0.0.1", "--port", "8001"]`.
  - In `README.md`, `CLAUDE.md`, `AGENTS.md`, `.claude/skills/run/SKILL.md` and `.agents/skills/run/SKILL.md`, the run line becomes `uvicorn app.main:app --host 127.0.0.1 --reload`. In the two `SKILL.md` files and `README.md`, also fix the stale `# add ANTHROPIC_API_KEY` comment to `# add OPENROUTER_KEY` on the line you are already editing. Make no other edits.
  - `docker-compose.yml`: `ports: - "127.0.0.1:8000:8000"`, and replace the stale `ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}` with `OPENROUTER_KEY=${OPENROUTER_KEY}`.
  - `Dockerfile:12` keeps `--host 0.0.0.0`, which is required inside the container for port publishing. Add one comment line above `CMD`: `# 0.0.0.0 is container-internal; docker-compose publishes it on 127.0.0.1 only.`
- **Non-goals, noted for a follow-up and not done here:**
  - DNS-rebinding protection (`TrustedHostMiddleware`). It would need a hosts setting and a decision about how magic-link clients reach a future deployment.
  - CSRF tokens.
  - Auth.

### D-P6-0c-G: Remediation scenario 10, one UTC anchor

In `tests/test_remediation_tracking.py::test_scenario_10_engagement_rollup_and_tracker_page`:

1. Define `today = datetime.now(timezone.utc).date()` **once**, before L923. This is the same clock as `remediation_rollup._date_today`.
2. Derive both target dates from it: `today - timedelta(days=1)` at L923 and `today + timedelta(days=1)` at L937, with the same `datetime.combine(..., tzinfo=timezone.utc)` shape.
3. Delete the hard-coded `today = date(2026, 9, 24)` at L949. The rollup calls at L950 and L979 use the new `today`.

This removes both the hard-coded date and the latent local-versus-UTC mismatch around midnight: in IST, local-today runs one day ahead of UTC between 00:00 and 05:30. Change no expected values. Do not add freezegun. `target_date="2026-12-31"` at L406 is a plain update payload with no past-date validation, so leave it.

### D-P6-0c-H: Longitudinal scenario 9, the fix goes in the test

The manifest order is a P3-3 contract (fact 12). The test's expectation is what's wrong. At `tests/test_longitudinal_demo.py:470`, change the expected list to `sorted([demo.assessment_ids["baseline"], demo.assessment_ids["validation"]])`, with the same shape as `test_pdf_updates.py:843`. Do **not** touch `app/services/report_content.py` (snapshot manifests are write-once and hashed downstream), and do not open the seed script.

### D-P6-0c-I: Dev-DB leak, the fix goes in the test

In `tests/integration/test_desk_review.py::test_trigger_desk_review`:

- Patch the background session the same way `test_analysis.py:57` does: `patch("app.database.SessionLocal", return_value=db_session)`, alongside the existing `run_desk_review` patch in the same `with`.
- Tighten the final assertion from `summary.status in ("analyzing", "completed")` to `summary.status == "completed"`. That proves the background task ran against the test DB.
  - If it is not `"completed"` because of session state, add `db_session.expire_all()` before the query.
  - If it still isn't, stop and report.

`app/routers/web.py` is **not** changed. Opening a fresh `SessionLocal()` in the background task is correct in production.

## Key files

| Path | Change |
|---|---|
| `.github/workflows/tests.yml` (new) | CI (D-P6-0c-A) |
| `.python-version`, `requirements-dev.txt` (new) | Pins (D-P6-0c-B) |
| `app/database.py` | `_configure_sqlite_connection`, `create_app_engine`, WAL + busy_timeout (D-P6-0c-E) |
| `scripts/restore.py` | `_checkpoint_wal`, sidecar cleanup (D-P6-0c-E) |
| `app/main.py` | Remove `CORSMiddleware` and its import (D-P6-0c-F) |
| `.claude/launch.json`, `docker-compose.yml`, `Dockerfile` (comment only) | Explicit local bind (D-P6-0c-F) |
| `README.md`, `CLAUDE.md`, `AGENTS.md`, `.claude/skills/run/SKILL.md`, `.agents/skills/run/SKILL.md` | Run and install lines only (D-P6-0c-B, F) |
| `tests/conftest.py` | Dev-DB guard also covers `-wal`/`-shm` (D-P6-0c-E) |
| `tests/test_p5_4_adaptive_ucc_questionnaire.py`, `tests/test_p5_3_framework_desk_review.py`, `tests/test_p5_2_reader_migration.py`, `tests/test_p5_6_rfi_rebuild.py`, `tests/test_retention.py` (L622 only), `tests/test_correctness_bundle.py` (L853 only), `tests/test_p6_nist_csf2_alignment.py` | Guard hygiene (D-P6-0c-C) |
| `tests/test_remediation_tracking.py`, `tests/test_longitudinal_demo.py` (L470 only), `tests/integration/test_desk_review.py` | The failing-test fixes (D-P6-0c-G, H, I) |
| `tests/test_p6_0c_dev_hygiene.py` (new) | Scenarios below |
| `tasks/todo.md` | Tick the P6-0c and localhost-guard parts of the Track 0 line |

**Do not touch:**
- Any prompt text anywhere. `app/services/claude_analyzer.py`, `app/services/desk_review.py`, `app/services/llm_client.py` (logic or docstrings), and `app/frameworks/**` (definitions, criteria, mappings, prompts, schema, batching). `app/dpdpa/**`.
- `app/config.py`, `requirements.txt`, `scripts/backup.py`, `app/routers/web.py`, `app/services/report_content.py`, `app/services/remediation_rollup.py`, `alembic/**`, `app/models/**`, `tests/fixtures/**`, `tests/support/**`
- `validation/**`, `scripts/validation/**`, and the forbidden files listed at the top
- Any test assertion not named in D-P6-0c-C, G, H or I. If another test fails because of your change, stop and report. Do not edit it.

## Non-goals

- A Settings-driven CORS or hosts list, `TrustedHostMiddleware`, CSRF, auth.
- Lint, format, type-check or coverage jobs. A Python matrix. Docker or Tailwind builds in CI.
- Changing the protected-surface policy of existing guards beyond two-dot → three-dot and delta → invariant.
- Any change to production ordering, snapshot manifests or background-task session handling.
- WeasyPrint system packages. When the WeasyPrint PDF work lands, that PR adds the `apt-get` step it needs.

## Test scenarios (all required; you may add cases, not drop or weaken them)

All scenarios go in `tests/test_p6_0c_dev_hygiene.py` unless stated. None may connect `app.database.engine`. The conftest guard would catch that.

1. **Python pin and dev deps.**
   - `.python-version` reads exactly `"3.13\n"`.
   - `requirements-dev.txt`'s non-blank lines are exactly `["-r requirements.txt", "pytest==9.1.1", "httpx==0.28.1"]`.
   - `requirements.txt` contains no `pytest` or `httpx` line.
2. **Workflow contract** (plain-text assertions; PyYAML is deliberately not a dependency). `.github/workflows/tests.yml` contains:
   - `fetch-depth: 0`
   - `git show-ref --verify --quiet refs/heads/main || git branch main origin/main`
   - `python-version-file: .python-version`
   - `pip install -r requirements-dev.txt`
   - `python -m pytest`
   - `OPENROUTER_BASE_URL: "http://127.0.0.1:9/api/v1"`
   - `test ! -e data/dpdpa.db`

   It contains no `secrets.` reference.
3. **WAL on a file engine.** Build `database.create_app_engine(f"sqlite:///{tmp_path / 'wal.db'}")`. On a connection, `PRAGMA journal_mode` is `"wal"`, `PRAGMA busy_timeout` is `30000`, and `PRAGMA foreign_keys` is `1`. Once something has been written, `wal.db-wal` exists beside it. Dispose the engine.
4. **In-memory engine unaffected.** `create_app_engine("sqlite://")` connects without error. `journal_mode` is `"memory"`, `foreign_keys` is `1`.
5. **The module engine carries the listener, without connecting to it.** `sqlalchemy.event.contains(database.engine, "connect", database._configure_sqlite_connection)` is `True`, and `database.SessionLocal.kw["bind"] is database.engine`.
6. **Concurrent writers.**
   - On a WAL file engine from `create_app_engine`, create a one-table schema. Run 4 threads, each doing 25 separate insert-and-commit cycles through its own `sessionmaker(bind=engine)()` session.
   - All 100 rows land, and no thread raises `OperationalError`.
   - While one connection holds an open write transaction (`BEGIN IMMEDIATE`, insert, sleep 1.0 s, commit), a reader on another connection from the same engine completes `SELECT count(*)` in < 0.5 s and does not see the uncommitted row.
   - A second writer that starts during that window succeeds after the first commits, instead of raising `database is locked`.
7. **Restore under WAL** (can live in `tests/test_backup_restore.py` or the new file; your choice, but say which in Results). Simulate a crash-left WAL:
   1. Connection A: `journal_mode=WAL`, `wal_autocheckpoint=0`. Create a table, insert row X, commit, and keep A open.
   2. Copy `live.db` and `live.db-wal` to a scratch directory. Close A.
   3. Put the copied pair back as `live.db` + `live.db-wal`. The main file lacks X; the WAL has it.
   4. Run `restore_backup(backup_dir, live_db, uploads, force=True)`, using a backup made by `create_backup` from a different database.
   5. The pre-restore safety copy contains row X. The restored `live.db` passes `PRAGMA integrity_check`, has the backup's content, and has no `live.db-wal` of nonzero size beside it.
   6. A second case uses the same crash-left pair and monkeypatches `scripts.restore._checkpoint_wal` to a no-op. Restore raises the `_assert_wal_empty` `RuntimeError`, `live.db` and `live.db-wal` are byte-identical to before, and no `pre-restore-*` directory was created. Do not hold a reader open to force this path: the checkpoint would wait out the 5 s busy handler.
8. **CORS removed.**
   - No entry in `app.main.app.user_middleware` has `cls is CORSMiddleware`.
   - Through a `TestClient` that follows the existing isolated-DB pattern (redirect `settings.database_url` to `tmp_path` before entering the lifespan, as `tests/integration/conftest.py` does):
     - `GET /health` with `Origin: https://evil.example` and a cookie returns 200 with **no** `access-control-allow-origin` or `access-control-allow-credentials` header.
     - `OPTIONS /health` with `Origin: https://evil.example` and `Access-Control-Request-Method: POST` returns no `access-control-allow-origin` header.
9. **Guard meta-test (AST, not regex).** Parse every `tests/**/*.py` except this file with `ast`. For each `ast.List` whose elements include string constants, flag it when any of these holds:
   - it contains `"git"` and `"diff"`, and an element that is exactly `"main"`. This stays legal: `"main...HEAD"`, and `["git", "merge-base", "main", "HEAD"]`, which has no `"diff"`.
   - it contains `"git"` and `"show"`, and an element that is a string constant starting with `"main:"` or an f-string (`ast.JoinedStr`) whose first part is a constant starting with `"main:"`
   - it starts with the constant `"alembic"` (bare-`PATH` alembic)

   Separately, flag any string constant containing `.venv/bin/`. Assert that the flag list is empty. Also include a self-check: running the same checker on a planted source string, `subprocess.run(["git", "diff", "--stat", "main", "--", "x"]); subprocess.run(["alembic", "heads"]); subprocess.check_output(["git", "show", f"main:{p}"])`, flags exactly three items.
10. **Launch points.**
    - `json.loads(".claude/launch.json")` has `"--host", "127.0.0.1"` adjacent in `runtimeArgs`.
    - `docker-compose.yml` contains `"127.0.0.1:8000:8000"` and no `ANTHROPIC_API_KEY`.
    - `README.md`, `CLAUDE.md`, `AGENTS.md` and both `SKILL.md` files contain `--host 127.0.0.1`.
11. **The five formerly failing tests pass.**
    - The four named tests and the whole suite pass (scenario-level: they are existing tests; nothing new to write).
    - `test_trigger_desk_review` asserts `"completed"`.
    - Run `test_scenario_9_rollups_and_integrated_reporting` 10 times in a row (Verification 3). It passes every time.
12. **Fresh-checkout leak check** (Verification 2). `rm -rf data`, run the full suite, and `data/dpdpa.db` does not exist afterwards. The `data/` directory itself may exist, because `ensure_sqlite_parent_dir` creates it at import. That is expected, and the guard does not check it.

## Verification (before reporting done)

1. **Full suite.** Run `.venv/bin/python -m pytest -q -p no:cacheprovider`. Because your test edits are uncommitted, exactly one failure is expected: `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes`. It passes after the orchestrator commits. Any other failure or error means you are not done. Record the counts.
2. **Fresh-checkout leak.** Run `rm -rf data && .venv/bin/python -m pytest -q -p no:cacheprovider; test ! -e data/dpdpa.db && echo NO_DEV_DB`. Paste the tail and `NO_DEV_DB`.
3. **Flake check.** Run `for i in $(seq 10); do .venv/bin/python -m pytest -q -p no:cacheprovider "tests/test_longitudinal_demo.py::test_scenario_9_rollups_and_integrated_reporting" | tail -1; done`. That should give 10 × `1 passed`.
4. **CI-parity run**, without `.env` values and with no network (env vars override `.env`):
   ```bash
   env -u ANTHROPIC_API_KEY OPENROUTER_KEY= OPENROUTER_BASE_URL=http://127.0.0.1:9/api/v1 \
     HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 NO_PROXY=localhost,127.0.0.1,testserver \
     .venv/bin/python -m pytest -q -p no:cacheprovider
   ```
   Results should be the same as step 1.
5. **Greps**, each with empty output. Paste the commands:
   - `grep -rn '\.venv/' tests/*.py tests/integration`
   - `grep -rnE '"main",[[:space:]]*"--"' tests/*.py tests/integration`
   - `grep -rn 'CORSMiddleware' app`
6. **Workflow syntax.** If `actionlint` is on `PATH`, run it on the workflow. Otherwise say it was not available. Do not install it.
7. **Smoke.** In the worktree, start `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8767` (the sandbox may refuse the bind; if so, say so and use the in-process `TestClient` route check from scenario 8 instead). Check the following, then stop the server:
   - `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8767/health` returns `200`
   - `curl -sI -H 'Origin: https://evil.example' http://127.0.0.1:8767/health | grep -i access-control` returns nothing
   - `sqlite3 data/dpdpa.db 'PRAGMA journal_mode'` prints `wal`

   Then delete the worktree's `data/` directory, since it is gitignored scratch.
8. **Orchestrator (after commit and push; not Codex).**
   - The PR shows a `tests / pytest` check, and it is green.
   - `test_retention::test_scenario_13` passes locally after the commit.
   - If CI fails only on Linux, record the test and the error in `## Results` and send it back to Codex. Do not mark tests `xfail` or `skip`.

## Results

Committed-state record:

- `HEAD`: `10fb129cb25879e72fe69dafa062140f503d02ef`.
- `main`: `beeacf993b5ca69d40cea5b14804a45d6694cae2`.
- `origin/main`: `beeacf993b5ca69d40cea5b14804a45d6694cae2`.
- The orchestrator applied the `.agents/skills/run/SKILL.md` edit.
- The committed suite was 753 passed, 10 skipped, 0 failed.

Files changed:

- `.gitignore`, `.github/workflows/tests.yml`, `.python-version`, `requirements-dev.txt`.
- `.claude/launch.json`, `.claude/skills/run/SKILL.md`, `README.md`, `CLAUDE.md`, `AGENTS.md`, `Dockerfile`, `docker-compose.yml`.
- `app/database.py`, `app/main.py`, `scripts/restore.py`, `tests/conftest.py`, `tasks/todo.md`.
- `tests/test_backup_restore.py`, `tests/test_p6_0c_dev_hygiene.py`, `tests/integration/test_desk_review.py`, `tests/test_longitudinal_demo.py`, `tests/test_remediation_tracking.py`.
- `tests/test_p5_2_reader_migration.py`, `tests/test_p5_3_framework_desk_review.py`, `tests/test_p5_4_adaptive_ucc_questionnaire.py`, `tests/test_p5_6_rfi_rebuild.py`, `tests/test_retention.py`, `tests/test_correctness_bundle.py`, `tests/test_p6_nist_csf2_alignment.py`.
- This handoff's Results section.

Scenario notes:

- Scenarios 1–10 pass in `tests/test_p6_0c_dev_hygiene.py`, including a contender that waits on the SQLite busy timeout for a held writer lock.
- Scenario 7 is in `tests/test_backup_restore.py`; crash-left-WAL, active-WAL refusal, and corrupt-live-database raw-byte safety-copy cases pass.

Verification:

1. The focused review set (`tests/test_backup_restore.py` and `tests/test_p6_0c_dev_hygiene.py`) ended with `18 passed`.
2. The exact `.venv/bin/python -m pytest -q` run ended with `1 failed, 753 passed, 10 skipped, 0 errors`; the only failure was `tests/test_retention.py::test_scenario_13_only_new_retention_test_file_changes`, which detects these intentionally uncommitted test edits. After the orchestrator commits this review delta, the expected full-suite count is `754 passed, 10 skipped, 0 failed`.
3. Re-running the exact suite with a temporary clean Git work-tree view, without writing `.git`, ended with `754 passed, 10 skipped, 0 failed`.
4. `data/dpdpa.db` was absent after both full-suite runs.

Deviations and reasons:

- The retention guard is expected to pass after the orchestrator commits the review changes; no commit or `.git` write was performed here.
- No commit, staging, ref movement, or other `.git` write was performed.

## Done criteria

- Every scenario passes.
- On `main` after merge, the full suite has 0 failed and 0 errors, locally and in CI.
- A fresh checkout leaves no `data/dpdpa.db`.
- The PR's `tests` check is green.
- `## Results` is filled in. Claude reviews before merge.
