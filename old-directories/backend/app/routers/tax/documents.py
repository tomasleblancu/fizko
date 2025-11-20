"""Tax Documents router - Get company tax documents."""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import (
    get_current_user_id,
    require_auth,
    TaxDocumentRepositoryDep,
)
from ...utils.company_resolver import get_user_primary_company_id

router = APIRouter(
    prefix="/api/tax-documents",
    tags=["tax-documents"],
    dependencies=[
        Depends(require_auth)
    ]
)


@router.get("")
async def get_tax_documents_for_user(
    repo: TaxDocumentRepositoryDep,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0, description="Number of documents to skip (for pagination)"),
    contact_rut: str | None = Query(None, description="Filter by contact RUT (provider or client)"),
    company_id: UUID | None = Query(None, description="Company ID to get documents for"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent tax documents for the authenticated user's company.

    If company_id is provided, uses that. Otherwise, resolves from user's active session.
    Returns both purchase and sales documents, sorted by date descending.

    Optional filters:
    - contact_rut: Filter documents by provider (purchases) or client (sales) RUT
    - offset: Number of documents to skip (for pagination/infinite scroll)
    """
    # Use provided company_id or resolve from user's active session
    resolved_company_id = company_id or await get_user_primary_company_id(current_user_id, db)

    if not resolved_company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active company found for user"
        )

    # Repository injected via Depends
    documents = await repo.get_all_documents(
        company_id=resolved_company_id,
        limit=limit,
        offset=offset,
        contact_rut=contact_rut
    )

    return documents


@router.get("/{company_id}")
async def get_tax_documents(
    company_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent tax documents for a specific company.

    (Legacy endpoint for backward compatibility)
    Returns both purchase and sales documents, sorted by date descending.
    """
    # Repository injected via Depends
    documents = await repo.get_all_documents(company_id=company_id, limit=limit)

    return documents
