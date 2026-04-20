from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def _prepare_sqlite_path(db_url: str) -> None:
    sqlite_prefix = "sqlite:///"
    if not db_url.startswith(sqlite_prefix):
        return
    raw_path = db_url[len(sqlite_prefix):]
    if not raw_path or raw_path == ":memory:":
        return
    db_path = Path(raw_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)


_prepare_sqlite_path(settings.db_url)

engine = create_engine(settings.db_url, future=True, connect_args={"check_same_thread": False} if settings.db_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def ensure_sqlite_schema_compatibility() -> None:
    """Add newly introduced nullable columns to existing SQLite tables.

    The demonstrator keeps one long-lived local SQLite file across many
    release lines. `create_all()` does not alter existing tables, so we add
    safe nullable columns here to keep older local databases compatible with
    newer patch lines.
    """

    if not settings.db_url.startswith("sqlite"):
        return
    expected_columns = {
        "appointment_cache": {
            "address_id": "ALTER TABLE appointment_cache ADD COLUMN address_id VARCHAR(80)",
            "correlation_ref": "ALTER TABLE appointment_cache ADD COLUMN correlation_ref VARCHAR(120)",
        },
        "reminder_jobs": {
            "address_id": "ALTER TABLE reminder_jobs ADD COLUMN address_id VARCHAR(80)",
            "correlation_ref": "ALTER TABLE reminder_jobs ADD COLUMN correlation_ref VARCHAR(120)",
        },
        "message_records": {
            "address_id": "ALTER TABLE message_records ADD COLUMN address_id VARCHAR(80)",
            "appointment_id": "ALTER TABLE message_records ADD COLUMN appointment_id VARCHAR(255)",
            "correlation_ref": "ALTER TABLE message_records ADD COLUMN correlation_ref VARCHAR(120)",
        },
        "address_records": {
            "timezone": "ALTER TABLE address_records ADD COLUMN timezone VARCHAR(80)",
        },
    }
    with engine.begin() as connection:
        for table_name, definitions in expected_columns.items():
            table_exists = connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                {"table_name": table_name},
            ).first()
            if table_exists is None:
                continue
            existing_columns = {
                row[1]
                for row in connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            }
            for column_name, ddl in definitions.items():
                if column_name not in existing_columns:
                    connection.execute(text(ddl))


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
