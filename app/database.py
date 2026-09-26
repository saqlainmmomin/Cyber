from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


SQLITE_BUSY_TIMEOUT_MS = 30_000


def ensure_sqlite_parent_dir(url: str) -> None:
    """Create the parent directory for a file-backed SQLite URL if needed.

    No-op for in-memory SQLite (":memory:") or any non-SQLite URL — never
    touches an externally supplied database URL (e.g. Postgres). A clean
    checkout has no `data/` directory, and SQLite will not create it on
    its own — only the file — so the default `sqlite:///data/dpdpa.db`
    would otherwise fail to open on first boot.
    """
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite":
        return
    database = parsed.database
    if not database or database == ":memory:":
        return
    Path(database).parent.mkdir(parents=True, exist_ok=True)


def _configure_sqlite_connection(dbapi_connection, connection_record) -> None:
    """Per-connection pragmas. WAL + busy_timeout only for file-backed databases."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        main_file = next(
            row[2] for row in cursor.execute("PRAGMA database_list") if row[1] == "main"
        )
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


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
