import logging
import socket
import threading
import time
from enum import Enum
from typing import Generator, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.core.config import settings

logger = logging.getLogger("ai_grama_sahayak.database")

Base = declarative_base()

_engine = None
_SessionFactory = None

# Failure cooldown state to avoid repeated blocking connection attempts
_last_failure_time: Optional[float] = None
_cooldown_seconds: float = 30.0
_is_operational: Optional[bool] = None
_status_lock = threading.Lock()


class DatabaseStatus(str, Enum):
    EXPLICITLY_DISABLED = "explicitly_disabled"
    UNCONFIGURED = "unconfigured"
    CONFIGURED_UNREACHABLE = "configured_unreachable"
    AVAILABLE_OPERATIONAL = "available_operational"


def reset_db_state_cache() -> None:
    """Reset the failure cooldown, status cache, and engine for clean test isolation."""
    global _last_failure_time, _is_operational, _engine, _SessionFactory
    with _status_lock:
        _last_failure_time = None
        _is_operational = None
        _engine = None
        _SessionFactory = None


def record_db_failure() -> None:
    """Record database failure timestamp to initiate backoff cooldown."""
    global _last_failure_time, _is_operational
    _last_failure_time = time.monotonic()
    _is_operational = False


def record_db_success() -> None:
    """Record database success to clear cooldown and mark operational."""
    global _last_failure_time, _is_operational
    _last_failure_time = None
    _is_operational = True


def is_database_explicitly_disabled() -> bool:
    """Check if database integration is explicitly disabled via config."""
    if not getattr(settings, "DATABASE_ENABLED", True):
        return True
    if settings.DATABASE_URL:
        clean = settings.DATABASE_URL.strip().lower()
        if clean in ("disabled", "none", "off", "false", "0"):
            return True
    return False


def is_database_unconfigured() -> bool:
    """Check if database parameters are missing or empty."""
    if settings.DATABASE_URL is not None and settings.DATABASE_URL.strip() == "":
        return True
    if settings.DATABASE_URL is None:
        if not settings.POSTGRES_SERVER or not settings.POSTGRES_DB or not settings.POSTGRES_USER:
            return True
    return False


def _parse_host_and_port(db_url: str) -> Tuple[str, int]:
    """Safely extract host and port for fast pre-flight socket reachability."""
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname or settings.POSTGRES_SERVER or "localhost"
        port = parsed.port or settings.POSTGRES_PORT or 5432
        return host, port
    except Exception:
        return settings.POSTGRES_SERVER or "localhost", settings.POSTGRES_PORT or 5432


def is_host_reachable(host: str, port: int, timeout: float = 0.3) -> bool:
    """Fast non-blocking TCP socket check with bounded timeout."""
    target_host = "127.0.0.1" if host in ("localhost", "127.0.0.1") else host
    try:
        with socket.create_connection((target_host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def get_database_status(timeout: float = 0.3) -> DatabaseStatus:
    """
    Determine the current state of the PostgreSQL database:
    - EXPLICITLY_DISABLED
    - UNCONFIGURED
    - CONFIGURED_UNREACHABLE
    - AVAILABLE_OPERATIONAL
    """
    if is_database_explicitly_disabled():
        return DatabaseStatus.EXPLICITLY_DISABLED

    if is_database_unconfigured():
        return DatabaseStatus.UNCONFIGURED

    # Fast-path check: cooldown window active
    global _last_failure_time, _is_operational
    now = time.monotonic()
    if _last_failure_time is not None and (now - _last_failure_time < _cooldown_seconds):
        return DatabaseStatus.CONFIGURED_UNREACHABLE

    # Thread-safe lock to prevent redundant socket/SQL probes under concurrent requests
    with _status_lock:
        now = time.monotonic()
        if _last_failure_time is not None and (now - _last_failure_time < _cooldown_seconds):
            return DatabaseStatus.CONFIGURED_UNREACHABLE

        try:
            db_url = settings.get_database_url()
        except Exception:
            return DatabaseStatus.UNCONFIGURED

        if not db_url or not db_url.startswith("postgresql"):
            return DatabaseStatus.UNCONFIGURED

        host, port = _parse_host_and_port(db_url)
        if not is_host_reachable(host, port, timeout=timeout):
            record_db_failure()
            return DatabaseStatus.CONFIGURED_UNREACHABLE

        # Host is reachable, verify SQL operation
        try:
            if check_db_connection():
                record_db_success()
                return DatabaseStatus.AVAILABLE_OPERATIONAL
            else:
                record_db_failure()
                return DatabaseStatus.CONFIGURED_UNREACHABLE
        except Exception:
            record_db_failure()
            return DatabaseStatus.CONFIGURED_UNREACHABLE


def get_engine():
    """
    Safely creates or returns the PostgreSQL SQLAlchemy engine.
    Ensures PostgreSQL dialect is configured and never falls back to SQLite.
    Uses bounded connection timeout to prevent thread hangs.
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
                connect_args={"connect_timeout": 2},
            )
            logger.info("Configured PostgreSQL database engine.")
        except Exception as exc:
            logger.error("Failed to initialize PostgreSQL engine: %s", type(exc).__name__)
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
    if is_database_explicitly_disabled() or is_database_unconfigured():
        return False
    try:
        db_url = settings.get_database_url()
        if db_url and db_url.startswith("postgresql"):
            host, port = _parse_host_and_port(db_url)
            if not is_host_reachable(host, port, timeout=0.3):
                return False
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except (OperationalError, SQLAlchemyError, Exception) as exc:
        logger.warning("PostgreSQL ping check failed: %s", type(exc).__name__)
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
        logger.error("Database session error: %s", type(exc).__name__)
        raise
    finally:
        session.close()
