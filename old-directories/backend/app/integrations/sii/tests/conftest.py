"""
Pytest configuration and fixtures for SII integration tests
"""
import pytest
from app.integrations.sii import SIIClient


# Test credentials
TEST_RUT = "77794858-k"
TEST_PASSWORD = "SiiPfufl574@#"


@pytest.fixture(scope="function")
def sii_client():
    """
    Fixture that provides a fresh SIIClient instance for each test.
    Automatically handles login and cleanup.
    """
    client = SIIClient(tax_id=TEST_RUT, password=TEST_PASSWORD, headless=True)
    client.login()
    yield client
    client.close()


@pytest.fixture(scope="function")
def sii_client_no_login():
    """
    Fixture that provides an SIIClient instance without automatic login.
    Useful for testing authentication flows.
    """
    client = SIIClient(tax_id=TEST_RUT, password=TEST_PASSWORD, headless=True)
    yield client
    client.close()


@pytest.fixture(scope="session")
def test_credentials():
    """Session-scoped fixture providing test credentials"""
    return {
        "rut": TEST_RUT,
        "password": TEST_PASSWORD
    }


@pytest.fixture(scope="session")
def test_period():
    """Session-scoped fixture providing current test period"""
    from datetime import datetime
    return datetime.now().strftime("%Y%m")


@pytest.fixture(scope="session")
def test_year():
    """Session-scoped fixture providing test year (last year)"""
    from datetime import datetime
    return str(datetime.now().year - 1)
