"""Security tests for authorization and multi-tenancy."""
import pytest
from httpx import AsyncClient
from unittest.mock import patch
from datetime import datetime, UTC

from app.db.models import User, Company


@pytest.mark.security
async def test_user_cannot_access_other_company(
    client: AsyncClient,
    test_user: User,
    test_company: Company,
    db_session: any
):
    """Test that users cannot access other users' companies (RLS)."""
    # Create another user and company
    other_user = User(
        id="other-user-id",
        email="other@example.com",
        phone="+56999999999",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    other_company = Company(
        user_id=other_user.id,
        name="Other Company",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    db_session.add(other_user)
    db_session.add(other_company)
    await db_session.commit()
    
    # Try to access other company as test_user
    with patch('app.dependencies.auth.get_current_user', return_value=test_user.id):
        response = await client.get(
            f"/api/companies/{other_company.id}",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 403


@pytest.mark.security
async def test_user_cannot_modify_other_company(
    client: AsyncClient,
    test_user: User,
    test_company: Company,
    db_session: any
):
    """Test that users cannot modify other users' companies."""
    other_user = User(
        id="other-user-id",
        email="other@example.com",
        phone="+56999999999",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    other_company = Company(
        user_id=other_user.id,
        name="Other Company",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    db_session.add(other_user)
    db_session.add(other_company)
    await db_session.commit()
    
    # Try to modify other company
    with patch('app.dependencies.auth.get_current_user', return_value=test_user.id):
        response = await client.put(
            f"/api/companies/{other_company.id}",
            json={"name": "Hacked Name"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 403


@pytest.mark.security
async def test_user_cannot_delete_other_company(
    client: AsyncClient,
    test_user: User,
    db_session: any
):
    """Test that users cannot delete other users' companies."""
    other_user = User(
        id="other-user-id",
        email="other@example.com",
        phone="+56999999999",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    other_company = Company(
        user_id=other_user.id,
        name="Other Company",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    db_session.add(other_user)
    db_session.add(other_company)
    await db_session.commit()
    
    with patch('app.dependencies.auth.get_current_user', return_value=test_user.id):
        response = await client.delete(
            f"/api/companies/{other_company.id}",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 403


@pytest.mark.security
async def test_user_cannot_access_other_tax_documents(
    client: AsyncClient,
    test_user: User,
    db_session: any
):
    """Test that users cannot access tax documents from other companies."""
    other_user = User(
        id="other-user-id",
        email="other@example.com",
        phone="+56999999999",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    other_company = Company(
        user_id=other_user.id,
        name="Other Company",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    db_session.add(other_user)
    db_session.add(other_company)
    await db_session.commit()
    
    with patch('app.dependencies.auth.get_current_user', return_value=test_user.id):
        response = await client.get(
            f"/api/tax/documents/compras?company_id={other_company.id}&periodo=202501",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 403
