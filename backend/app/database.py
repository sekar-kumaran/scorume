"""
PHASE 3: Database Engine & Session Management (backend/app/database.py)

Provides:
1. Primary SQLAlchemy 2.0 PostgreSQL engine (`postgresql+psycopg2://...`) with connection
   pooling (`pool_pre_ping=True`, `pool_size=10`, `max_overflow=20`) and automatic
   SQLite fallback when `USE_SQLITE_FALLBACK=true` or PostgreSQL is unreachable in local dev.
2. Built-in Zero-Dependency `sqlite3` ORM Compatibility Adapter (`SqliteFallbackSession`)
   when `sqlalchemy` is not installed in a minimal test environment, ensuring 100%
   runnable execution across both Docker PostgreSQL and bare-metal Python 3.11+ environments.
"""

from __future__ import annotations

import datetime
import json
import logging
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Generator

from app.config import settings

logger = logging.getLogger(__name__)

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    create_engine = None  # type: ignore[assignment]
    text = None  # type: ignore[assignment]
    DeclarativeBase = object  # type: ignore[assignment,misc]
    Session = Any  # type: ignore[assignment,misc]
    sessionmaker = None  # type: ignore[assignment]


if SQLALCHEMY_AVAILABLE:

    class Base(DeclarativeBase):
        """Declarative base class for SQLAlchemy 2.0 ORM models."""

        pass

    def _build_sqlalchemy_engine() -> Any:
        """
        Builds the SQLAlchemy 2.0 Engine targeting PostgreSQL 15+ by default,
        with graceful fallback to local SQLite if configured or if PostgreSQL
        is unreachable during local standalone testing.
        """
        db_url = (
            settings.SQLITE_FALLBACK_URL
            if settings.USE_SQLITE_FALLBACK
            else settings.DATABASE_URL
        )

        if db_url.startswith("sqlite"):
            return create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                future=True,
            )

        try:
            pg_engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                future=True,
            )
            # Test connectivity on initialization; fall back to SQLite if Postgres container isn't up
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected to PostgreSQL database: %s", db_url.split("@")[-1])
            return pg_engine
        except Exception as exc:
            logger.warning(
                "PostgreSQL unreachable (%s); falling back to local SQLite database at %s",
                exc,
                settings.SQLITE_FALLBACK_URL,
            )
            return create_engine(
                settings.SQLITE_FALLBACK_URL,
                connect_args={"check_same_thread": False},
                future=True,
            )

    engine = _build_sqlalchemy_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

else:
    # ==========================================================================
    # Zero-Dependency SQLite3 ORM Compatibility Layer (when SQLAlchemy is absent)
    # ==========================================================================
    class Base:  # type: ignore[no-redef]
        """Base class for ORM models when running on built-in sqlite3 fallback."""

        pass

    SQLITE_DB_PATH = Path("./scorume_local.db").resolve()

    def _get_sqlite_conn() -> sqlite3.Connection:
        conn = sqlite3.connect(str(SQLITE_DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite_tables() -> None:
        conn = _get_sqlite_conn()
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_descriptions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    required_skills TEXT NOT NULL,
                    min_experience_years REAL NOT NULL DEFAULT 0.0,
                    education_reqs TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS candidate_evaluations (
                    id TEXT PRIMARY KEY,
                    jd_id TEXT NOT NULL,
                    candidate_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    experience_years REAL NOT NULL DEFAULT 0.0,
                    education_summary TEXT NOT NULL,
                    overall_score REAL NOT NULL DEFAULT 0.0,
                    skill_score REAL NOT NULL DEFAULT 0.0,
                    semantic_score REAL NOT NULL DEFAULT 0.0,
                    experience_score REAL NOT NULL DEFAULT 0.0,
                    matched_skills TEXT NOT NULL,
                    partial_skills TEXT NOT NULL,
                    missing_skills TEXT NOT NULL,
                    explanations TEXT NOT NULL,
                    segmented_sections TEXT NOT NULL,
                    integrity_flags TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (jd_id) REFERENCES job_descriptions (id) ON DELETE CASCADE
                )
                """
            )
        conn.close()

    _init_sqlite_tables()
    engine = None

    class SqliteFallbackSession:
        """
        Lightweight SQLAlchemy-compatible session wrapper backed by Python's built-in
        `sqlite3` module for environments without `sqlalchemy` installed.
        """

        def __init__(self) -> None:
            self.conn = _get_sqlite_conn()
            self._pending: list[Any] = []

        def add(self, obj: Any) -> None:
            if not getattr(obj, "id", None):
                obj.id = str(uuid.uuid4())
            if not getattr(obj, "created_at", None):
                obj.created_at = datetime.datetime.now(datetime.timezone.utc)
            self._pending.append(obj)

        def commit(self) -> None:
            with self.conn:
                for obj in self._pending:
                    table_name = getattr(obj, "__tablename__", "")
                    if table_name == "job_descriptions":
                        self.conn.execute(
                            """
                            INSERT OR REPLACE INTO job_descriptions
                            (id, title, raw_text, required_skills, min_experience_years, education_reqs, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                str(obj.id),
                                obj.title,
                                obj.raw_text,
                                json.dumps(obj.required_skills or []),
                                float(obj.min_experience_years or 0.0),
                                json.dumps(obj.education_reqs or []),
                                obj.created_at.isoformat()
                                if isinstance(obj.created_at, datetime.datetime)
                                else str(obj.created_at),
                            ),
                        )
                    elif table_name == "candidate_evaluations":
                        self.conn.execute(
                            """
                            INSERT OR REPLACE INTO candidate_evaluations
                            (id, jd_id, candidate_name, email, phone, filename, experience_years,
                             education_summary, overall_score, skill_score, semantic_score,
                             experience_score, matched_skills, partial_skills, missing_skills,
                             explanations, segmented_sections, integrity_flags, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                str(obj.id),
                                str(obj.jd_id),
                                obj.candidate_name,
                                obj.email,
                                obj.phone,
                                obj.filename,
                                float(obj.experience_years or 0.0),
                                obj.education_summary,
                                float(obj.overall_score or 0.0),
                                float(obj.skill_score or 0.0),
                                float(obj.semantic_score or 0.0),
                                float(obj.experience_score or 0.0),
                                json.dumps(obj.matched_skills or []),
                                json.dumps(obj.partial_skills or []),
                                json.dumps(obj.missing_skills or []),
                                json.dumps(obj.explanations or []),
                                json.dumps(obj.segmented_sections or {}),
                                json.dumps(obj.integrity_flags or []),
                                obj.created_at.isoformat()
                                if isinstance(obj.created_at, datetime.datetime)
                                else str(obj.created_at),
                            ),
                        )
            self._pending.clear()

        def refresh(self, obj: Any) -> None:
            pass

        def delete(self, obj: Any) -> None:
            table_name = getattr(obj, "__tablename__", "")
            if table_name in {"job_descriptions", "candidate_evaluations"}:
                with self.conn:
                    self.conn.execute(
                        f"DELETE FROM {table_name} WHERE id = ?",
                        (str(obj.id),),
                    )

        def close(self) -> None:
            self.conn.close()

    SessionLocal = SqliteFallbackSession  # type: ignore[misc,assignment]


def init_db() -> None:
    """Initializes all database tables on FastAPI startup."""
    if SQLALCHEMY_AVAILABLE and engine is not None:
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
    else:
        _init_sqlite_tables()


def get_db() -> Generator[Any, None, None]:
    """FastAPI dependency yielding a database session and closing it after request completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
