"""Sales leads router - Handle contact form submissions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from ..db.models import SalesLead
from ..dependencies import get_current_user_id, require_auth
from ..schemas.sales_lead import SalesLeadCreate, SalesLeadResponse, SalesLeadUpdate

# Public router for contact form (no auth required)
public_router = APIRouter(
    prefix="/api/sales-leads",
    tags=["sales-leads"],
)

# Admin router for managing leads (auth required)
admin_router = APIRouter(
    prefix="/api/admin/sales-leads",
    tags=["sales-leads", "admin"],
    dependencies=[Depends(require_auth)],
)


@public_router.post("", response_model=SalesLeadResponse, status_code=status.HTTP_201_CREATED)
async def create_sales_lead(
    lead_data: SalesLeadCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new sales lead from contact form submission.

    This endpoint is public and does not require authentication.
    Used by the landing page contact form.
    """
    # Create new sales lead
    new_lead = SalesLead(
        name=lead_data.name,
        email=lead_data.email,
        phone=lead_data.phone,
        company_name=lead_data.company_name,
        message=lead_data.message,
        source=lead_data.source,
        status="new",
    )

    db.add(new_lead)
    await db.commit()
    await db.refresh(new_lead)

    return new_lead


@admin_router.get("", response_model=list[SalesLeadResponse])
async def list_sales_leads(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Any:
    """
    List all sales leads (admin only).

    Returns all contact form submissions ordered by creation date (newest first).
    """
    result = await db.execute(
        select(SalesLead).order_by(SalesLead.created_at.desc())
    )
    leads = result.scalars().all()
    return leads


@admin_router.get("/{lead_id}", response_model=SalesLeadResponse)
async def get_sales_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Any:
    """
    Get a specific sales lead by ID (admin only).
    """
    result = await db.execute(
        select(SalesLead).where(SalesLead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales lead not found",
        )

    return lead


@admin_router.patch("/{lead_id}", response_model=SalesLeadResponse)
async def update_sales_lead(
    lead_id: UUID,
    lead_update: SalesLeadUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Any:
    """
    Update a sales lead (admin only).

    Currently supports updating status and adding notes.
    """
    result = await db.execute(
        select(SalesLead).where(SalesLead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales lead not found",
        )

    # Update fields if provided
    if lead_update.status is not None:
        lead.status = lead_update.status
    if lead_update.message is not None:
        lead.message = lead_update.message

    await db.commit()
    await db.refresh(lead)

    return lead
