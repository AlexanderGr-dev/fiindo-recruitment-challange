"""SQLAlchemy base and database utilities.

This module exposes the SQLAlchemy `Base` declarative class, a configured
`engine`, and a `SessionLocal` factory for creating DB sessions. The
`init_db` helper will create database tables defined on `Base`.

The project uses SQLite by default (see `src.core.config.settings`).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.config import settings

# Create engine with sqlite threading settings used in local development.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Declarative base for ORM models.
Base = declarative_base()


def init_db() -> None:
    """Create all tables in the database.

    This is a convenience wrapper around `Base.metadata.create_all` and is
    intended for local development / first-time initialization.
    """
    Base.metadata.create_all(bind=engine)
