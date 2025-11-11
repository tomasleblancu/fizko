"""Global test fixtures and configuration."""
import pytest
import asyncio
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from datetime import datetime, UTC

from app.main import app
from app.config.database import Base, get_db
from app.db.models import User, Company, CompanyTaxInfo, Profile

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


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id="test-user-id",
        email="test@example.com",
        phone="+56912345678",
        phone_verified=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_profile(db_session: AsyncSession, test_user: User) -> Profile:
    """Create a test profile."""
    profile = Profile(
        user_id=test_user.id,
        first_name="Test",
        last_name="User",
        rut="12345678",
        dv="9",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest.fixture
async def test_company(db_session: AsyncSession, test_user: User) -> Company:
    """Create a test company."""
    company = Company(
        user_id=test_user.id,
        name="Test Company",
        legal_name="Test Company SpA",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest.fixture
async def test_company_tax_info(
    db_session: AsyncSession,
    test_company: Company
) -> CompanyTaxInfo:
    """Create test company tax info."""
    tax_info = CompanyTaxInfo(
        company_id=test_company.id,
        rut="12345678",
        dv="9",
        tax_regime="14A",
        activity_code="620200",
        activity_description="Consultores en software",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    db_session.add(tax_info)
    await db_session.commit()
    await db_session.refresh(tax_info)
    return tax_info


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """
    Create authentication headers for API requests.
    
    Note: In real tests, you should generate a proper JWT token
    using Supabase. This is a simplified version for testing.
    """
    # Mock JWT token (in production tests, generate proper JWT)
    return {
        "Authorization": "Bearer mock-jwt-token",
        "X-User-ID": test_user.id  # For testing purposes
    }


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
