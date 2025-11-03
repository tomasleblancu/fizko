"""Contacts router - Manage contacts (providers and clients)."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from ..db.models import Contact
from ..dependencies import get_current_user_id, require_auth
from ..utils.company_resolver import get_user_primary_company_id

router = APIRouter(
    prefix="/api/contacts",
    tags=["contacts"],
    dependencies=[Depends(require_auth)]
)


# =============================================================================
# Response Models
# =============================================================================

class ContactResponse(BaseModel):
    """Response model for a contact."""
    id: str
    rut: str
    business_name: str
    trade_name: Optional[str] = None
    contact_type: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# =============================================================================
# Routes
# =============================================================================

@router.get("", response_model=list[ContactResponse])
async def get_contacts(
    company_id: Optional[UUID] = Query(None, description="Company ID (optional, resolved from user if not provided)"),
    contact_type: Optional[str] = Query(None, description="Filter by contact type: provider, client, or both"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> Any:
    """
    Get all contacts for a company.

    - **company_id**: UUID of the company (opcional, se resuelve automáticamente del usuario si no se proporciona)
    - **contact_type**: Optional filter by type (provider, client, both)
    """
    # Resolve company_id from user's active session if not provided
    if company_id is None:
        company_id = await get_user_primary_company_id(user_id, db)
        if not company_id:
            raise HTTPException(
                status_code=404,
                detail="No active company found for user"
            )

    # Build query
    query = select(Contact).where(Contact.company_id == company_id)

    # Apply optional filter
    if contact_type:
        query = query.where(Contact.contact_type == contact_type)

    # Order by business name
    query = query.order_by(Contact.business_name)

    # Execute query
    result = await db.execute(query)
    contacts = result.scalars().all()

    # Convert to response format
    return [
        ContactResponse(
            id=str(contact.id),
            rut=contact.rut,
            business_name=contact.business_name,
            trade_name=contact.trade_name,
            contact_type=contact.contact_type,
            address=contact.address,
            phone=contact.phone,
            email=contact.email,
            created_at=contact.created_at.isoformat() if contact.created_at else "",
            updated_at=contact.updated_at.isoformat() if contact.updated_at else "",
        )
        for contact in contacts
    ]


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Any:
    """Get a specific contact by ID."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    return ContactResponse(
        id=str(contact.id),
        rut=contact.rut,
        business_name=contact.business_name,
        trade_name=contact.trade_name,
        contact_type=contact.contact_type,
        address=contact.address,
        phone=contact.phone,
        email=contact.email,
        created_at=contact.created_at.isoformat() if contact.created_at else "",
        updated_at=contact.updated_at.isoformat() if contact.updated_at else "",
    )
