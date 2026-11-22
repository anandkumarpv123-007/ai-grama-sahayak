import pytest
from unittest.mock import patch
from app.database.session import check_db_connection, get_engine
from app.core.config import Settings


def test_database_safe_ping_does_not_crash_when_unreachable():
    # If PostgreSQL is not running locally, check_db_connection should safely return False without an unhandled exception
    is_connected = check_db_connection()
    assert isinstance(is_connected, bool)


def test_reject_sqlite_configuration():
    # Enforces frozen stack rule: "Do not use SQLite as a silent replacement for PostgreSQL"
    custom_settings = Settings(DATABASE_URL="sqlite:///./test.db")
    with patch("app.database.session.settings", custom_settings):
        # Force re-creating engine with sqlite setting
        with patch("app.database.session._engine", None):
            with pytest.raises(ValueError) as excinfo:
                get_engine()
            assert "SQLite or non-PostgreSQL databases are not permitted" in str(excinfo.value)


def test_postgresql_url_normalization():
    s = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/testdb")
    url = s.get_database_url()
    assert url.startswith("postgresql+psycopg://")


def test_production_safety_blocks_insecure_secret():
    """
    Requirement 5: Ensure development-only defaults cannot be used silently in production.
    """
    with pytest.raises(ValueError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="dev_insecure_key",
            POSTGRES_PASSWORD="secure_prod_password_123",
        )
    assert "Production safety violation" in str(excinfo.value)
    assert "SECRET_KEY" in str(excinfo.value)


def test_production_safety_blocks_default_postgres_password():
    with pytest.raises(ValueError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a_very_secure_long_random_production_secret_key_32_chars!",
            POSTGRES_PASSWORD="postgres",
        )
    assert "production safety violation" in str(excinfo.value).lower()
    assert "default postgresql credentials" in str(excinfo.value).lower()


def test_production_safety_allows_valid_production_config():
    s = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a_very_secure_long_random_production_secret_key_32_chars!",
        POSTGRES_PASSWORD="strong_production_db_password_xyz",
    )
    assert s.ENVIRONMENT == "production"
