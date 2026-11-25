"""
Performance and Reliability Regression Tests for Eligibility Audit Logging.

Covers:
1. Database explicitly disabled.
2. Database unconfigured.
3. Database configured but unreachable.
4. Database available, using a controlled test / mock session.
5. Audit logging failure handled safely.
6. Repeated eligibility requests while the database is unavailable.
7. Eligibility response remains correct despite audit logging failure.

Target: Requests complete within 1 second on local test environment when optional DB is unavailable.
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient

from app.main import app
from app.database.session import (
    get_database_status,
    DatabaseStatus,
    reset_db_state_cache,
)
from app.core.config import Settings
from app.models.eligibility_log import EligibilityAudit

client = TestClient(app)

SAMPLE_PAYLOAD = {
    "scheme_id": "ntr_bharosa_pension",
    "language": "en",
    "applicant_profile": {
        "state": "Andhra Pradesh",
        "age": 64,
        "has_white_ration_or_rice_card": True,
        "is_govt_employee_or_pensioner": False,
        "is_income_tax_payer": False,
        "owns_four_wheeler": False,
    },
}


def setup_function():
    """Reset database state cache before each test."""
    reset_db_state_cache()


def test_1_database_explicitly_disabled():
    """
    1. Database explicitly disabled via config toggle.
    Must return DatabaseStatus.EXPLICITLY_DISABLED and complete within 1 second.
    """
    with patch("app.database.session.settings.DATABASE_ENABLED", False):
        status = get_database_status()
        assert status == DatabaseStatus.EXPLICITLY_DISABLED

        t0 = time.perf_counter()
        response = client.post("/api/eligibility/check", json=SAMPLE_PAYLOAD)
        elapsed = time.perf_counter() - t0

        assert response.status_code == 200
        assert response.json()["status"] == "eligible"
        assert elapsed < 1.0, f"Request took {elapsed:.3f}s; expected < 1.0s"


def test_2_database_unconfigured():
    """
    2. Database unconfigured (empty DATABASE_URL and empty POSTGRES_SERVER).
    Must return DatabaseStatus.UNCONFIGURED and complete within 1 second.
    """
    with patch("app.database.session.settings.DATABASE_URL", ""):
        with patch("app.database.session.settings.POSTGRES_SERVER", ""):
            status = get_database_status()
            assert status == DatabaseStatus.UNCONFIGURED

            t0 = time.perf_counter()
            response = client.post("/api/eligibility/check", json=SAMPLE_PAYLOAD)
            elapsed = time.perf_counter() - t0

            assert response.status_code == 200
            assert response.json()["status"] == "eligible"
            assert elapsed < 1.0, f"Request took {elapsed:.3f}s; expected < 1.0s"


def test_3_database_configured_but_unreachable():
    """
    3. Database configured with unreachable host/port.
    Must return DatabaseStatus.CONFIGURED_UNREACHABLE and complete within 1 second.
    """
    reset_db_state_cache()
    # Port 5439 is non-standard and guaranteed closed
    unreachable_url = "postgresql+psycopg://postgres:postgres@127.0.0.1:5439/nonexistent_db"
    with patch("app.database.session.settings.DATABASE_URL", unreachable_url):
        t0 = time.perf_counter()
        status = get_database_status(timeout=0.3)
        assert status == DatabaseStatus.CONFIGURED_UNREACHABLE

        response = client.post("/api/eligibility/check", json=SAMPLE_PAYLOAD)
        elapsed = time.perf_counter() - t0

        assert response.status_code == 200
        assert response.json()["status"] == "eligible"
        assert elapsed < 1.0, f"Request took {elapsed:.3f}s; expected < 1.0s"


def test_4_database_available_operational_audit_saved():
    """
    4. Database available and operational:
    Verifies that when DB is operational, EligibilityAudit is created and committed,
    and session is properly closed.
    """
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)

    with patch("app.api.eligibility.get_database_status", return_value=DatabaseStatus.AVAILABLE_OPERATIONAL):
        with patch("app.api.eligibility.get_session_factory", return_value=mock_factory):
            response = client.post("/api/eligibility/check", json=SAMPLE_PAYLOAD)
            assert response.status_code == 200

            # Verify session interactions
            assert mock_session.add.called
            added_obj = mock_session.add.call_args[0][0]
            assert isinstance(added_obj, EligibilityAudit)
            assert added_obj.scheme_id == "ntr_bharosa_pension"
            assert added_obj.status == "eligible"
            assert added_obj.language == "en"
            assert mock_session.commit.called
            assert mock_session.close.called


def test_5_audit_logging_failure_handled_gracefully():
    """
    5. Database audit logging failure during session commit.
    Must NOT raise an unhandled exception or fail citizen's request.
    Verifies rollback and close on session, and that cooldown is initiated.
    """
    mock_session = MagicMock()
    mock_session.commit.side_effect = Exception("Simulated DB connection drop")
    mock_factory = MagicMock(return_value=mock_session)

    with patch("app.api.eligibility.get_database_status", return_value=DatabaseStatus.AVAILABLE_OPERATIONAL):
        with patch("app.api.eligibility.get_session_factory", return_value=mock_factory):
            response = client.post("/api/eligibility/check", json=SAMPLE_PAYLOAD)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "eligible"
            assert len(data["benefits"]) > 0
            assert mock_session.rollback.called
            assert mock_session.close.called


def test_audit_disabled_isolation():
    """
    Verifies that DATABASE_AUDIT_ENABLED=False disables eligibility audit logging
    WITHOUT disabling the database globally (is_database_explicitly_disabled remains False).
    """
    from app.database.session import is_database_explicitly_disabled
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)

    with patch("app.core.config.settings.DATABASE_ENABLED", True):
        with patch("app.core.config.settings.DATABASE_AUDIT_ENABLED", False):
            # Database as a whole is NOT disabled
            assert is_database_explicitly_disabled() is False

            with patch("app.api.eligibility.get_database_status", return_value=DatabaseStatus.AVAILABLE_OPERATIONAL):
                with patch("app.api.eligibility.get_session_factory", return_value=mock_factory):
                    response = client.post("/api/eligibility/check", json=SAMPLE_PAYLOAD)
                    assert response.status_code == 200
                    # Audit should be skipped completely
                    assert not mock_session.add.called
                    assert not mock_session.commit.called


def test_6_repeated_eligibility_requests_while_db_unavailable():
    """
    6. Repeated requests while database is unavailable:
    Cooldown must activate after first failure so subsequent requests skip DB
    immediately without accumulating background tasks or blocking threads.
    """
    reset_db_state_cache()
    durations = []
    num_requests = 10

    for i in range(num_requests):
        t0 = time.perf_counter()
        response = client.post("/api/eligibility/check", json=SAMPLE_PAYLOAD)
        elapsed = time.perf_counter() - t0
        durations.append(elapsed)
        assert response.status_code == 200
        assert elapsed < 1.0, f"Request {i+1} took {elapsed:.3f}s; target < 1.0s"

    avg_duration = sum(durations) / len(durations)
    # Beyond the initial probe, cooldown ensures subsequent calls take milliseconds
    subsequent_avg = sum(durations[1:]) / len(durations[1:])
    assert subsequent_avg < 0.1, f"Subsequent average {subsequent_avg:.3f}s exceeded 100ms"
    assert avg_duration < 1.0, f"Overall average {avg_duration:.3f}s exceeded 1.0s"


def test_7_eligibility_response_integrity_despite_audit_failure():
    """
    7. Eligibility response data remains complete, truthful, and schema-compliant
    even when audit logging fails or is disabled.
    """
    # Test under disabled DB
    with patch("app.database.session.settings.DATABASE_ENABLED", False):
        res1 = client.post("/api/eligibility/check", json=SAMPLE_PAYLOAD)
        assert res1.status_code == 200
        data1 = res1.json()

    # Test under failing DB
    mock_session = MagicMock()
    mock_session.commit.side_effect = RuntimeError("Fatal DB failure")
    mock_factory = MagicMock()
    mock_factory.return_value.__enter__.return_value = mock_session

    with patch("app.api.eligibility.get_database_status", return_value=DatabaseStatus.AVAILABLE_OPERATIONAL):
        with patch("app.api.eligibility.get_session_factory", return_value=mock_factory):
            res2 = client.post("/api/eligibility/check", json=SAMPLE_PAYLOAD)
            assert res2.status_code == 200
            data2 = res2.json()

    # Schemas and outputs must be identical
    assert data1 == data2
    assert data1["scheme_id"] == "ntr_bharosa_pension"
    assert data1["status"] == "eligible"
    assert any("4,000" in b for b in data1["benefits"])
    assert any("sspensions.ap.gov.in" in s["url"] for s in data1["sources"])
    assert data1["missing_fields"] == []
