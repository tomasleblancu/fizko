"""Security tests for authentication."""
import pytest
from httpx import AsyncClient
from unittest.mock import patch
from datetime import datetime, UTC, timedelta
import jwt


@pytest.mark.security
async def test_expired_token_rejected(client: AsyncClient):
    """Test that expired JWT tokens are rejected."""
    expired_token = jwt.encode(
        {"sub": "user-id", "exp": datetime.now(UTC) - timedelta(hours=1)},
        "secret",
        algorithm="HS256"
    )
    
    response = await client.get(
        "/api/companies",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    assert response.status_code == 401


@pytest.mark.security
async def test_malformed_token_rejected(client: AsyncClient):
    """Test that malformed tokens are rejected."""
    malformed_tokens = [
        "not-a-jwt",
        "Bearer",
        "",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
    ]
    
    for token in malformed_tokens:
        response = await client.get(
            "/api/companies",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401


@pytest.mark.security
async def test_missing_authorization_header(client: AsyncClient):
    """Test that requests without auth header are rejected."""
    response = await client.get("/api/companies")
    assert response.status_code == 401


@pytest.mark.security
async def test_token_with_invalid_signature(client: AsyncClient):
    """Test that tokens with invalid signatures are rejected."""
    # Create token with wrong secret
    invalid_token = jwt.encode(
        {"sub": "user-id", "exp": datetime.now(UTC) + timedelta(hours=1)},
        "wrong-secret",
        algorithm="HS256"
    )
    
    response = await client.get(
        "/api/companies",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    assert response.status_code == 401


@pytest.mark.security
async def test_token_without_required_claims(client: AsyncClient):
    """Test that tokens without required claims are rejected."""
    # Token without 'sub' claim
    token_no_sub = jwt.encode(
        {"exp": datetime.now(UTC) + timedelta(hours=1)},
        "secret",
        algorithm="HS256"
    )
    
    response = await client.get(
        "/api/companies",
        headers={"Authorization": f"Bearer {token_no_sub}"}
    )
    
    assert response.status_code == 401
