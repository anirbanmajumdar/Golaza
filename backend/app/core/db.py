"""SQLModel engine + session. SQLite with WAL for decent concurrency on
a single small VM. `get_session` is a FastAPI dependency."""

from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from .config import settings

# ensure ./data exists for the sqlite file
if settings.db_url.startswith("sqlite:///"):
    path = settings.db_url.replace("sqlite:///", "", 1)
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.db_url.startswith("sqlite") else {}
engine = create_engine(settings.db_url, echo=False, connect_args=connect_args)


@event.listens_for(engine, "connect")
def _sqlite_pragma(dbapi_conn, _rec):  # noqa: ANN001
    if settings.db_url.startswith("sqlite"):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


def create_db_and_tables() -> None:
    # import models so SQLModel.metadata is populated
    from .. import models  # noqa: F401
    SQLModel.metadata.create_all(engine)
    _migrate_sqlite()


def _migrate_sqlite() -> None:
    """Additive column migrations for SQLite (create_all won't ALTER an
    existing table). Safe to run on every boot."""
    if not settings.db_url.startswith("sqlite"):
        return
    from sqlalchemy import text
    adds = {
        "user": [
            ("password_hash", "VARCHAR"),
            ("status", "VARCHAR DEFAULT 'invited'"),
            ("invited_by", "VARCHAR"),
        ],
    }
    with engine.begin() as conn:
        for table, cols in adds.items():
            existing = {r[1] for r in conn.execute(text(f"PRAGMA table_info({table})"))}
            for name, ddl in cols:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
