"""Global test fixtures and configuration."""
import pytest
import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import Mock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from datetime import datetime, UTC

from app.main import app
from app.config.database import Base, get_db
try:
    from app.db.models import Company, CompanyTaxInfo, Profile
except ImportError:
    # Models may not be available for all test types
    Company = None
    CompanyTaxInfo = None
    Profile = None

# Test database URL (use separate test DB or in-memory SQLite for fast tests)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/fizko_test"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session with automatic rollback.
    
    This fixture:
    1. Creates all tables before the test
    2. Provides a session for the test
    3. Rolls back all changes after the test
    4. Drops all tables after the test
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client with database override.
    
    This fixture automatically injects the test database session
    into all API endpoints.
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use ASGITransport to avoid deprecation warnings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# NOTE: The following fixtures are commented out because they reference User model
# which doesn't exist in the current schema (uses Supabase auth instead).
# Uncomment and update these fixtures when needed for API/integration tests.

# @pytest.fixture
# async def test_profile(db_session: AsyncSession) -> Profile:
#     """Create a test profile."""
#     if Profile is None:
#         pytest.skip("Profile model not available")
#     profile = Profile(
#         user_id="test-user-id",
#         first_name="Test",
#         last_name="User",
#         rut="12345678",
#         dv="9",
#         created_at=datetime.now(UTC),
#         updated_at=datetime.now(UTC)
#     )
#     db_session.add(profile)
#     await db_session.commit()
#     await db_session.refresh(profile)
#     return profile


# @pytest.fixture
# async def test_company(db_session: AsyncSession) -> Company:
#     """Create a test company."""
#     if Company is None:
#         pytest.skip("Company model not available")
#     company = Company(
#         user_id="test-user-id",
#         name="Test Company",
#         legal_name="Test Company SpA",
#         created_at=datetime.now(UTC),
#         updated_at=datetime.now(UTC)
#     )
#     db_session.add(company)
#     await db_session.commit()
#     await db_session.refresh(company)
#     return company


# @pytest.fixture
# async def test_company_tax_info(
#     db_session: AsyncSession,
#     test_company: Company
# ) -> CompanyTaxInfo:
#     """Create test company tax info."""
#     if CompanyTaxInfo is None:
#         pytest.skip("CompanyTaxInfo model not available")
#     tax_info = CompanyTaxInfo(
#         company_id=test_company.id,
#         rut="12345678",
#         dv="9",
#         tax_regime="14A",
#         activity_code="620200",
#         activity_description="Consultores en software",
#         created_at=datetime.now(UTC),
#         updated_at=datetime.now(UTC)
#     )
#     db_session.add(tax_info)
#     await db_session.commit()
#     await db_session.refresh(tax_info)
#     return tax_info


# @pytest.fixture
# def auth_headers() -> dict:
#     """
#     Create authentication headers for API requests.
#
#     Note: In real tests, you should generate a proper JWT token
#     using Supabase. This is a simplified version for testing.
#     """
#     # Mock JWT token (in production tests, generate proper JWT)
#     return {
#         "Authorization": "Bearer mock-jwt-token",
#         "X-User-ID": "test-user-id"  # For testing purposes
#     }


@pytest.fixture
def mock_sii_credentials():
    """Mock SII credentials for testing."""
    return {
        "rut": "12345678",
        "dv": "9",
        "password": "test-password"
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for agent tests."""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response from AI agent"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@pytest.fixture
def mock_kapso_response():
    """Mock Kapso API response for WhatsApp tests."""
    return {
        "status": "sent",
        "message_id": "test-message-id",
        "timestamp": "2025-01-15T10:00:00Z"
    }


# Utility functions for tests

async def create_test_data(db_session: AsyncSession, model_class, **kwargs):
    """Helper to create test data for any model."""
    instance = model_class(**kwargs)
    db_session.add(instance)
    await db_session.commit()
    await db_session.refresh(instance)
    return instance


async def clean_database(db_session: AsyncSession):
    """Helper to clean all data from database."""
    async with db_session.begin():
        for table in reversed(Base.metadata.sorted_tables):
            await db_session.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
    await db_session.commit()


# =============================================================================
# F29 Sync Test Fixtures
# =============================================================================

@pytest.fixture
def celery_eager_mode():
    """
    Run Celery tasks synchronously for testing.

    This fixture sets Celery to eager mode, which executes tasks
    synchronously instead of asynchronously. This allows tests to
    run without needing a Celery worker.
    """
    from app.infrastructure.celery import celery_app

    # Store original config
    original_always_eager = celery_app.conf.task_always_eager
    original_eager_propagates = celery_app.conf.task_eager_propagates

    # Set to eager mode
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    yield

    # Restore original config
    celery_app.conf.task_always_eager = original_always_eager
    celery_app.conf.task_eager_propagates = original_eager_propagates


@pytest.fixture
def mock_selenium_driver():
    """
    Mock Selenium WebDriver with common behaviors.

    Provides a mock driver that simulates browser behavior for
    testing scrapers without actual browser automation.
    """
    driver = MagicMock()

    # Mock find_element to return clickable elements
    mock_element = MagicMock()
    mock_element.click = Mock()
    mock_element.send_keys = Mock()
    mock_element.get_attribute = Mock(return_value="test-value")
    mock_element.text = "Test Text"
    driver.find_element = Mock(return_value=mock_element)

    # Mock page source
    driver.page_source = "<html><body>Test Page</body></html>"

    # Mock current URL
    driver.current_url = "https://misiitio.sii.cl/cgi_misii/siihome.cgi"

    # Mock window handles
    driver.window_handles = ["main_window"]
    driver.current_window_handle = "main_window"

    # Mock switch_to
    driver.switch_to = MagicMock()
    driver.switch_to.window = Mock()

    # Mock close and quit
    driver.close = Mock()
    driver.quit = Mock()

    return driver


@pytest.fixture
def mock_f29_scraper_driver():
    """
    Mock Selenium driver specifically configured for F29 scraper tests.

    Includes F29-specific behaviors like button clicks opening windows
    with codInt in URL.
    """
    driver = MagicMock()

    # Mock find_element for F29-specific elements
    def mock_find_element(by, value):
        element = MagicMock()
        element.click = Mock()

        # Simulate button click opening new window with codInt
        if "Formulario Compacto" in value:
            def open_window_with_codint():
                # Simulate new window with codInt in URL
                driver.window_handles = ["main_window", "new_window"]
                driver.current_url = "https://www2.sii.cl/cgi-bin/formcomp.pl?codInt=775148628&periodo=202501"
            element.click.side_effect = open_window_with_codint

        return element

    driver.find_element = mock_find_element

    # Mock page source with F29 table
    driver.page_source = """
        <table>
            <tr>
                <td>8510019316</td>
                <td>2025-01</td>
                <td>42443</td>
                <td><button>Formulario Compacto</button></td>
            </tr>
        </table>
    """

    # Initial state
    driver.current_url = "https://misiitio.sii.cl/cgi_misii/siihome.cgi"
    driver.window_handles = ["main_window"]
    driver.current_window_handle = "main_window"

    # Mock switch_to
    driver.switch_to = MagicMock()
    driver.switch_to.window = Mock()

    # Mock close
    driver.close = Mock()

    return driver


@pytest.fixture
def test_period():
    """Common test period for SII tests."""
    return "202501"


@pytest.fixture
def mock_f29_formularios():
    """
    Mock list of F29 formularios with mixed codInt availability.

    Simulates real-world scenario where some forms have codInt
    (id_interno_sii) and others don't.
    """
    return [
        {
            "folio": "F1",
            "period": "2025-01",
            "contributor": "77794858-K",
            "submission_date": "01/01/2025",
            "status": "Vigente",
            "amount": 100,
            "id_interno_sii": "111"  # Has codInt
        },
        {
            "folio": "F2",
            "period": "2025-02",
            "contributor": "77794858-K",
            "submission_date": "01/02/2025",
            "status": "Vigente",
            "amount": 200,
            "id_interno_sii": "222"  # Has codInt
        },
        {
            "folio": "F3",
            "period": "2025-03",
            "contributor": "77794858-K",
            "submission_date": "01/03/2025",
            "status": "Vigente",
            "amount": 300
            # No codInt - simulates extraction failure
        }
    ]


@pytest.fixture
def mock_f29_formulario_with_codint():
    """Single F29 formulario with codInt for focused tests."""
    return {
        "folio": "8510019316",
        "period": "2025-01",
        "contributor": "77794858-K",
        "submission_date": "01/01/2025",
        "status": "Vigente",
        "amount": 42443,
        "id_interno_sii": "775148628"
    }


@pytest.fixture
def mock_f29_formulario_without_codint():
    """Single F29 formulario without codInt for edge case tests."""
    return {
        "folio": "8510019316",
        "period": "2025-01",
        "contributor": "77794858-K",
        "submission_date": "01/01/2025",
        "status": "Vigente",
        "amount": 42443
        # No id_interno_sii
    }


@pytest.fixture
def mock_sii_cookies():
    """Mock SII session cookies."""
    return [
        {"name": "SESSION", "value": "abc123"},
        {"name": "AUTH", "value": "xyz789"}
    ]
