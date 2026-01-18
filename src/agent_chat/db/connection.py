"""Database connection and session management."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agent_chat.config import settings
from agent_chat.db.models import Base

# Create engine
engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all database tables (for testing)."""
    Base.metadata.drop_all(bind=engine)


@contextmanager
def get_db() -> Generator[Session]:
    """Get a database session with automatic cleanup.

    Usage:
        with get_db() as db:
            # Use db session
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
