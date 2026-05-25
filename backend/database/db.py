"""
Database engine and session factory.

Locally uses SQLite (data/app.db).
In production set DATABASE_URL to a PostgreSQL connection string:
  postgresql+psycopg2://user:pass@host:5432/dbname
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ── Connection URL ────────────────────────────────────────────────────────────

_DEFAULT_SQLITE = "sqlite:///" + str(
    Path(__file__).resolve().parent.parent / "data" / "app.db"
)
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_SQLITE)

# SQLite needs check_same_thread=False; ignored by other drivers
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ── Dependency (FastAPI Depends) ──────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
