# Testing Guide

This document describes the testing architecture and best practices for the Fizko backend.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Architecture](#test-architecture)
- [Writing Tests](#writing-tests)
- [Running Tests](#running-tests)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)

## Quick Start

```bash
# Install dependencies
make install

# Run all tests
make test

# Run only unit tests (fast)
make test-unit

# Run with coverage
make test-cov

# Run specific test file
make test-file FILE=tests/unit/services/test_notification_service.py
```

## Test Architecture

Our testing strategy follows the testing pyramid:

```
         /\
        /  \  E2E (few)
       /____\
      /      \  Integration (some)
     /________\
    /          \  Unit (many)
   /____________\
```

### Test Types

#### 1. Unit Tests (`tests/unit/`)

**Purpose:** Test individual components in isolation with mocked dependencies.

**Characteristics:**
- Fast execution (< 1s per test)
- No external dependencies (DB, APIs, etc.)
- Use mocks extensively
- High code coverage

**Example:**
```python
@pytest.mark.unit
async def test_validate_rut_format():
    """Test RUT validation logic."""
    service = SIIAuthService(AsyncMock())
    
    assert service.validate_rut_format("12345678", "9") is True
    assert service.validate_rut_format("invalid", "X") is False
```

**Directory structure:**
```
tests/unit/
├── services/        # Service layer tests
├── agents/          # Agent tests
├── integrations/    # Integration client tests (mocked)
├── models/          # Model validation tests
└── utils/           # Utility function tests
```

#### 2. Integration Tests (`tests/integration/`)

**Purpose:** Test interactions between components with real dependencies.

**Characteristics:**
- Moderate execution time (1-5s per test)
- Use test database
- Real database queries
- Minimal external API mocking

**Example:**
```python
@pytest.mark.integration
async def test_create_company(client, test_user, auth_headers, db_session):
    """Test company creation API endpoint."""
    response = await client.post(
        "/api/companies",
        json={"name": "Test Company"},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    # Verify in database
    company = await db_session.get(Company, response.json()["id"])
    assert company is not None
```

**Directory structure:**
```
tests/integration/
├── api/             # API endpoint tests
├── agents/          # Multi-agent orchestration
├── database/        # Database operations, RLS
├── celery/          # Celery task execution
└── whatsapp/        # WhatsApp webhook processing
```

#### 3. E2E Tests (`tests/e2e/`)

**Purpose:** Test complete user flows from end to end.

**Characteristics:**
- Slow execution (5-30s per test)
- Test entire workflows
- Multiple API calls
- Realistic scenarios

**Example:**
```python
@pytest.mark.e2e
@pytest.mark.slow
async def test_complete_tax_document_sync_flow(client, test_company):
    """Test: Configure SII → Sync → Retrieve documents."""
    # 1. Configure credentials
    # 2. Trigger sync
    # 3. Verify documents
    # 4. Get summary
```

**Directory structure:**
```
tests/e2e/
├── test_tax_document_flow.py
├── test_whatsapp_conversation.py
├── test_notification_flow.py
└── test_onboarding_flow.py
```

#### 4. Security Tests (`tests/security/`)

**Purpose:** Test authentication, authorization, and security vulnerabilities.

**Characteristics:**
- Verify access controls
- Test JWT validation
- Check multi-tenancy isolation (RLS)
- Prevent common vulnerabilities

**Example:**
```python
@pytest.mark.security
async def test_user_cannot_access_other_company(client, test_user):
    """Test RLS: users cannot access other users' companies."""
    other_company_id = "other-company-id"
    
    response = await client.get(
        f"/api/companies/{other_company_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 403
```

**Directory structure:**
```
tests/security/
├── test_authentication.py    # JWT validation, expiration
├── test_authorization.py     # RLS, multi-tenancy
├── test_injection.py         # SQL injection prevention
└── test_rate_limiting.py     # Rate limit enforcement
```

#### 5. SII Integration Tests (`tests/sii_integration/`)

**Purpose:** Test real SII scraping with actual credentials (controlled environment).

**Characteristics:**
- Requires real SII credentials
- Very slow (30s-2min per test)
- Marked with `@pytest.mark.sii`
- Skipped by default in CI

**Example:**
```python
@pytest.mark.sii
@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("SII_TEST_RUT"), reason="No credentials")
async def test_sii_login_real(db_session):
    """Test real SII authentication."""
    async with SIIClient(...) as client:
        success = await client.login()
        assert success is True
```

## Writing Tests

### Test Fixtures

Global fixtures are defined in `tests/conftest.py`:

**Database fixtures:**
```python
@pytest.fixture
async def db_session():
    """Provides a clean database session for each test."""
    # Creates tables, yields session, rolls back, drops tables

@pytest.fixture
async def client(db_session):
    """Provides HTTP client with test database."""
    # Overrides get_db dependency
```

**Data fixtures:**
```python
@pytest.fixture
async def test_user(db_session):
    """Creates a test user."""
    
@pytest.fixture
async def test_company(db_session, test_user):
    """Creates a test company for test_user."""
    
@pytest.fixture
async def test_company_tax_info(db_session, test_company):
    """Creates tax info for test_company."""
```

**Mock fixtures:**
```python
@pytest.fixture
def mock_sii_credentials():
    """Mock SII credentials."""
    
@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    
@pytest.fixture
def mock_kapso_response():
    """Mock Kapso WhatsApp response."""
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit           # Unit test
@pytest.mark.integration    # Integration test
@pytest.mark.e2e           # End-to-end test
@pytest.mark.sii           # Requires SII credentials
@pytest.mark.security      # Security test
@pytest.mark.slow          # Slow-running test
@pytest.mark.skip_ci       # Skip in CI environment
```

### Mocking External Services

#### Mocking SII Client:
```python
with patch('app.integrations.sii.client.SIIClient.get_compras') as mock:
    mock.return_value = [{"folio": "12345", ...}]
    # Test code
```

#### Mocking OpenAI:
```python
with patch('chatkit.run_agent') as mock_agent:
    mock_agent.return_value = "AI response"
    # Test code
```

#### Mocking Kapso:
```python
with patch('app.integrations.kapso.client.KapsoClient.send_text') as mock:
    mock.return_value = {"status": "sent"}
    # Test code
```

### Testing Async Code

All database operations are async. Use `async def` and `await`:

```python
@pytest.mark.unit
async def test_create_user(db_session):
    user = User(id="test-id", email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.id == "test-id"
```

## Running Tests

### Using Makefile (Recommended)

```bash
# Run all tests
make test

# Run specific test type
make test-unit
make test-integration
make test-e2e
make test-security
make test-sii

# Run with coverage
make test-cov

# Run fast tests only
make test-fast

# Run specific file
make test-file FILE=tests/unit/services/test_notification_service.py

# Re-run failed tests
make test-failed

# Watch mode (auto-rerun on changes)
make test-watch
```

### Using pytest directly

```bash
# Run all tests
.venv/bin/pytest tests/ -v

# Run specific marker
.venv/bin/pytest -m unit -v
.venv/bin/pytest -m "not slow" -v

# Run specific file
.venv/bin/pytest tests/unit/services/test_notification_service.py -v

# Run specific test
.venv/bin/pytest tests/unit/services/test_notification_service.py::test_send_instant_notification_success -v

# Show coverage
.venv/bin/pytest --cov=app --cov-report=html

# Stop on first failure
.venv/bin/pytest -x

# Show print statements
.venv/bin/pytest -s
```

## Best Practices

### 1. Test Naming

- Use descriptive names: `test_user_cannot_access_other_company`
- Follow pattern: `test_<what>_<condition>_<expected_result>`
- Use docstrings to explain complex tests

### 2. Test Independence

- Each test should be independent
- Don't rely on test execution order
- Clean up after each test (fixtures handle this)

### 3. Arrange-Act-Assert Pattern

```python
async def test_create_company():
    # Arrange
    company_data = {"name": "Test Company"}
    
    # Act
    response = await client.post("/api/companies", json=company_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "Test Company"
```

### 4. Mock External Services

- Always mock external APIs in unit/integration tests
- Use real services only in E2E or specific integration tests
- Mock at the appropriate level (client, not HTTP)

### 5. Test Data

- Use fixtures for common test data
- Keep test data minimal
- Use realistic data (real RUTs, valid formats)

### 6. Coverage Goals

- **Unit tests:** 80%+ coverage
- **Integration tests:** Cover critical paths
- **E2E tests:** Cover main user flows
- **Total:** 70%+ coverage

### 7. Performance

- Unit tests should be < 1s each
- Integration tests should be < 5s each
- Mark slow tests with `@pytest.mark.slow`

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: make install
      
      - name: Run tests
        run: make ci-test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Railway/Render Integration

Tests can run automatically on deploy:

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "uv sync && make test-fast"
  }
}
```

## Troubleshooting

### Tests fail with database errors

**Solution:** Ensure test database exists:
```bash
createdb fizko_test
export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/fizko_test"
```

### Async tests not running

**Solution:** Check `pytest.ini` has `asyncio_mode = auto`

### Import errors

**Solution:** Install package in editable mode:
```bash
uv pip install -e .
```

### Slow tests

**Solution:** Run only fast tests:
```bash
make test-fast
# or
pytest -m "not slow"
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [httpx testing](https://www.python-httpx.org/async/)
- [SQLAlchemy testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
