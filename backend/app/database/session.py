import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import OperationalError
from app.core.config import settings

logger = logging.getLogger("ai_grama_sahayak.database")

Base = declarative_base()

_engine = None
_SessionFactory = None


def get_engine():
    """
    Safely creates or returns the PostgreSQL SQLAlchemy engine.
    Ensures PostgreSQL dialect is configured and never falls back to SQLite.
    """
    global _engine
    if _engine is None:
        db_url = settings.get_database_url()
        # Ensure dialect is PostgreSQL
        if not db_url.startswith("postgresql"):
            raise ValueError(
                f"Invalid database configuration: expected PostgreSQL URL, got '{db_url.split('://')[0]}://...'. "
                f"SQLite or non-PostgreSQL databases are not permitted."
            )
        try:
            _engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={"connect_timeout": 5},
            )
            logger.info("Configured PostgreSQL database engine.")
        except Exception as exc:
            logger.error("Failed to initialize PostgreSQL engine: %s", exc)
            raise
    return _engine


def get_session_factory():
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionFactory


def check_db_connection() -> bool:
    """
    Safely ping the PostgreSQL database to verify connectivity.
    Returns True if healthy, False if unreachable or disconnected.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except (OperationalError, Exception) as exc:
        logger.warning("PostgreSQL ping check failed: %s", exc)
        return False


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a SQLAlchemy database session.
    Safely rolls back and closes session on completion or exception.
    """
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
    except Exception as exc:
        session.rollback()
        logger.error("Database session error: %s", exc)
        raise
    finally:
        session.close()
