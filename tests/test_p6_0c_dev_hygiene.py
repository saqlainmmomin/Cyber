"""Regression coverage for P6-0c development and CI hygiene."""

from __future__ import annotations

import ast
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import threading
import time

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app import database
from app.config import settings
from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_python_pin_and_dev_dependencies():
    assert (REPO_ROOT / ".python-version").read_text() == "3.13\n"
    assert [
        line
        for line in (REPO_ROOT / "requirements-dev.txt").read_text().splitlines()
        if line.strip()
    ] == ["-r requirements.txt", "pytest==9.1.1", "httpx==0.28.1"]
    runtime_lines = (REPO_ROOT / "requirements.txt").read_text().splitlines()
    assert not any(line.startswith(("pytest", "httpx")) for line in runtime_lines)


def test_workflow_contract():
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text()
    for required in (
        "fetch-depth: 0",
        "git show-ref --verify --quiet refs/heads/main || git branch main origin/main",
        "python-version-file: .python-version",
        "pip install -r requirements-dev.txt",
        "python -m pytest",
        'OPENROUTER_BASE_URL: "http://127.0.0.1:9/api/v1"',
        "test ! -e data/dpdpa.db",
    ):
        assert required in workflow
    assert "secrets." not in workflow


def test_wal_on_a_file_engine(tmp_path):
    db_path = tmp_path / "wal.db"
    engine = database.create_app_engine(f"sqlite:///{db_path}")
    try:
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA journal_mode").scalar().lower() == "wal"
            assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar() == 30_000
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
            connection.execute(text("CREATE TABLE values_table (value INTEGER NOT NULL)"))
            connection.execute(text("INSERT INTO values_table (value) VALUES (1)"))
            connection.commit()
            assert Path(f"{db_path}-wal").exists()
    finally:
        engine.dispose()


def test_in_memory_engine_is_unaffected():
    engine = database.create_app_engine("sqlite://")
    try:
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA journal_mode").scalar().lower() == "memory"
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
    finally:
        engine.dispose()


def test_module_engine_carries_the_listener_without_connecting():
    from sqlalchemy import event

    assert event.contains(database.engine, "connect", database._configure_sqlite_connection)
    assert database.SessionLocal.kw["bind"] is database.engine


def test_concurrent_writers_and_wal_readers(tmp_path):
    db_path = tmp_path / "concurrent.db"
    engine = database.create_app_engine(f"sqlite:///{db_path}")
    sessions = sessionmaker(bind=engine)
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE rows (value INTEGER NOT NULL)"))

        errors: list[BaseException] = []

        def insert_batch(worker: int) -> None:
            try:
                for index in range(25):
                    with sessions.begin() as session:
                        session.execute(
                            text("INSERT INTO rows (value) VALUES (:value)"),
                            {"value": worker * 25 + index},
                        )
            except BaseException as exc:
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(insert_batch, range(4)))
        assert errors == []
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM rows")).scalar_one() == 100

        writer_ready = threading.Event()
        writer_release = threading.Event()
        writer_errors: list[BaseException] = []

        def hold_write_transaction() -> None:
            try:
                with engine.connect() as connection:
                    connection.exec_driver_sql("BEGIN IMMEDIATE")
                    connection.execute(text("INSERT INTO rows (value) VALUES (1000)"))
                    writer_ready.set()
                    writer_release.wait(timeout=5)
                    connection.commit()
            except BaseException as exc:
                writer_errors.append(exc)

        writer = threading.Thread(target=hold_write_transaction)
        writer.start()
        assert writer_ready.wait(timeout=5)

        started = time.perf_counter()
        with engine.connect() as connection:
            visible_count = connection.execute(text("SELECT count(*) FROM rows")).scalar_one()
        reader_elapsed = time.perf_counter() - started
        assert visible_count == 100
        assert reader_elapsed < 0.5

        second_writer_errors: list[BaseException] = []
        second_writer_started = threading.Event()

        def second_writer() -> None:
            try:
                second_writer_started.set()
                with sessions.begin() as session:
                    session.execute(text("INSERT INTO rows (value) VALUES (1001)"))
            except BaseException as exc:
                second_writer_errors.append(exc)

        contender = threading.Thread(target=second_writer)
        contender.start()
        assert second_writer_started.wait(timeout=5)
        time.sleep(0.1)
        writer_release.set()
        writer.join(timeout=5)
        contender.join(timeout=5)
        assert not writer.is_alive() and not contender.is_alive()
        assert writer_errors == []
        assert second_writer_errors == []
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM rows")).scalar_one() == 102
    finally:
        engine.dispose()


def test_cors_is_removed_and_health_is_same_origin_only(tmp_path, monkeypatch):
    assert not any(middleware.cls is CORSMiddleware for middleware in app.user_middleware)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'cors.db'}")
    with TestClient(app, raise_server_exceptions=False) as client:
        client.cookies.set("session", "test-cookie")
        response = client.get("/health", headers={"Origin": "https://evil.example"})
        assert response.status_code == 200
        assert "access-control-allow-origin" not in response.headers
        assert "access-control-allow-credentials" not in response.headers

        preflight = client.options(
            "/health",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in preflight.headers


def _guard_flags(source: str, filename: str = "<source>") -> list[str]:
    tree = ast.parse(source, filename=filename)
    flags: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and ".venv" + "/bin/" in node.value:
            flags.append("venv")
        if not isinstance(node, ast.List):
            continue
        constants = [
            element.value
            for element in node.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        ]
        if "git" in constants and "diff" in constants and "main" in constants:
            flags.append("git-diff-main")
        if "git" in constants and "show" in constants:
            for element in node.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str) and element.value.startswith("main:"):
                    flags.append("git-show-main")
                if isinstance(element, ast.JoinedStr) and element.values:
                    first = element.values[0]
                    if isinstance(first, ast.Constant) and isinstance(first.value, str) and first.value.startswith("main:"):
                        flags.append("git-show-main")
        if constants and constants[0] == "alembic":
            flags.append("bare-alembic")
    return flags


def test_guard_meta_test_rejects_stale_git_and_venv_invocations():
    flags: list[str] = []
    for path in sorted((REPO_ROOT / "tests").rglob("*.py")):
        if path == Path(__file__).resolve():
            continue
        flags.extend(_guard_flags(path.read_text(), str(path)))
    assert flags == []

    planted = (
        'subprocess.run(["git", "diff", "--stat", '
        '"main"'
        ', "--", "x"]); '
        'subprocess.run(["alembic", "heads"]); '
        'subprocess.check_output(["git", "show", f"main:{p}"])'
    )
    assert len(_guard_flags(planted)) == 3


def test_launch_points_bind_to_localhost():
    launch = json.loads((REPO_ROOT / ".claude/launch.json").read_text())
    runtime_args = launch["configurations"][0]["runtimeArgs"]
    host_index = runtime_args.index("--host")
    assert runtime_args[host_index + 1] == "127.0.0.1"

    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    assert "127.0.0.1:8000:8000" in compose
    assert "ANTHROPIC_API_KEY" not in compose
    for relative_path in (
        "README.md",
        "CLAUDE.md",
        "AGENTS.md",
        ".claude/skills/run/SKILL.md",
        ".agents/skills/run/SKILL.md",
    ):
        assert "--host 127.0.0.1" in (REPO_ROOT / relative_path).read_text()
