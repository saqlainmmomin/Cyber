from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


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


ensure_sqlite_parent_dir(settings.database_url)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
