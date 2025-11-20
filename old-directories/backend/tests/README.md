# Tests

Comprehensive test suite for Fizko backend.

## Quick Start

```bash
# Run all tests
make test

# Run unit tests (fast)
make test-unit

# Run with coverage
make test-cov
```

## Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── services/           # Service layer tests
│   ├── agents/             # Agent tests
│   ├── integrations/       # Integration client tests (mocked)
│   ├── models/             # Model validation tests
│   └── utils/              # Utility function tests
│
├── integration/            # Integration tests (with DB)
│   ├── api/               # API endpoint tests
│   ├── agents/            # Multi-agent orchestration
│   ├── database/          # Database operations
│   ├── celery/            # Celery tasks
│   └── whatsapp/          # WhatsApp webhook processing
│
├── e2e/                   # End-to-end tests (complete flows)
│   ├── test_tax_document_flow.py
│   ├── test_whatsapp_conversation.py
│   └── test_notification_flow.py
│
├── security/              # Security tests
│   ├── test_authentication.py
│   ├── test_authorization.py
│   └── test_injection.py
│
├── sii_integration/       # Real SII tests (requires credentials)
│   ├── test_sii_login.py
│   ├── test_dte_extraction.py
│   └── test_f29_extraction.py
│
├── performance/           # Performance/load tests
├── contract/              # API contract tests
├── conftest.py            # Global fixtures
└── README.md              # This file
```

## Test Types

| Type | Speed | Coverage | Purpose |
|------|-------|----------|---------|
| **Unit** | Fast (< 1s) | High | Test individual components in isolation |
| **Integration** | Medium (1-5s) | Medium | Test component interactions with real DB |
| **E2E** | Slow (5-30s) | Low | Test complete user flows |
| **Security** | Medium | Critical | Test auth, authorization, RLS |
| **SII** | Very slow (30s-2min) | Specific | Test real SII scraping |

## Running Tests

### All Tests
```bash
make test
```

### By Type
```bash
make test-unit          # Unit tests only
make test-integration   # Integration tests
make test-e2e          # E2E tests
make test-security     # Security tests
make test-sii          # SII integration (requires credentials)
```

### By Performance
```bash
make test-fast         # Fast tests only (unit, skip slow)
make test-cov          # With coverage report
```

### Specific Tests
```bash
# Run specific file
make test-file FILE=tests/unit/services/test_notification_service.py

# Run specific test
pytest tests/unit/services/test_notification_service.py::test_send_instant_notification_success -v

# Re-run failed tests
make test-failed
```

### Watch Mode
```bash
make test-watch  # Auto-rerun on file changes
```

## Writing Tests

### Example Unit Test

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.unit
async def test_service_method(db_session):
    """Test that service method works correctly."""
    service = MyService(db_session)
    
    with patch('external.api.call') as mock_call:
        mock_call.return_value = {"status": "success"}
        
        result = await service.do_something()
        
        assert result["status"] == "success"
        mock_call.assert_called_once()
```

### Example Integration Test

```python
import pytest

@pytest.mark.integration
async def test_api_endpoint(client, test_user, auth_headers):
    """Test API endpoint with database."""
    response = await client.post(
        "/api/endpoint",
        json={"data": "value"},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json()["data"] == "value"
```

### Example E2E Test

```python
import pytest

@pytest.mark.e2e
@pytest.mark.slow
async def test_complete_flow(client, test_company):
    """Test complete user flow."""
    # Step 1: Setup
    # Step 2: Action
    # Step 3: Verification
    # Step 4: Cleanup (if needed)
```

## Fixtures

Common fixtures available in all tests (from `conftest.py`):

- `db_session` - Clean database session
- `client` - HTTP client with test database
- `test_user` - Test user
- `test_company` - Test company
- `test_company_tax_info` - Test tax info
- `auth_headers` - Authentication headers
- `mock_sii_credentials` - Mock SII credentials
- `mock_openai_response` - Mock OpenAI response
- `mock_kapso_response` - Mock Kapso response

## Coverage

View coverage report:
```bash
make test-cov
open htmlcov/index.html  # macOS
```

Current coverage goals:
- **Unit tests:** 80%+ coverage
- **Total:** 70%+ coverage

## CI/CD

Tests run automatically in CI with:
```bash
make ci-test  # Skips slow and SII tests
```

## Troubleshooting

### Database connection errors
Ensure test database exists:
```bash
createdb fizko_test
export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/fizko_test"
```

### Import errors
Install in editable mode:
```bash
uv pip install -e .
```

### Slow tests
Run only fast tests:
```bash
make test-fast
```

## More Information

See [docs/TESTING.md](../docs/TESTING.md) for comprehensive testing guide.
