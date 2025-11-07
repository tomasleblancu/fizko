"""Purchase documents router - Manage purchase documents (documentos de compra)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import Session
from ...dependencies import (
    get_current_user_id,
    require_auth,
    PurchaseDocumentRepositoryDep,
)
from ...schemas.tax import PurchaseDocumentCreate, PurchaseDocumentUpdate

router = APIRouter(
    prefix="/api/purchase-documents",
    tags=["purchase-documents"],
    dependencies=[
        Depends(require_auth)
    ]
)


# =============================================================================
# Helper Functions
# =============================================================================

async def verify_company_access(
    company_id: UUID,
    user_id: str,
    db: AsyncSession
) -> None:
    """Verify that the user has access to the company via an active session."""
    stmt = select(Session).where(
        Session.user_id == UUID(user_id),
        Session.company_id == company_id,
        Session.is_active == True
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company"
        )


# =============================================================================
# Endpoints
# =============================================================================

@router.get("")
async def list_purchase_documents(
    repo: PurchaseDocumentRepositoryDep,
    company_id: str = Query(..., description="Company ID (required)"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    document_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """
    List purchase documents for a company with optional filtering.

    Query params:
    - company_id: Company ID (required)
    - document_type: Filter by document type
    - status: Filter by status (pending, approved, rejected, cancelled)
    - date_from: Filter by issue date from (ISO format)
    - date_to: Filter by issue date to (ISO format)
    - skip: Pagination offset
    - limit: Number of records to return
    """
    company_uuid = UUID(company_id)

    # Verify access
    await verify_company_access(company_uuid, user_id, db)

    # Parse dates
    from_date = None
    to_date = None
    if date_from:
        try:
            from_date = date.fromisoformat(date_from)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use ISO format (YYYY-MM-DD)"
            )
    if date_to:
        try:
            to_date = date.fromisoformat(date_to)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use ISO format (YYYY-MM-DD)"
            )

    # Use repository (injected via Depends)
    documents = await repo.find_by_company(
        company_id=company_uuid,
        document_type=document_type,
        start_date=from_date,
        end_date=to_date,
        status=status_filter,
        skip=skip,
        limit=limit
    )

    # Get total count
    total = await repo.count(filters={'company_id': company_uuid})

    return {
        "data": [
            {
                "id": str(doc.id),
                "company_id": str(doc.company_id),
                "document_type": doc.document_type,
                "folio": doc.folio,
                "issue_date": doc.issue_date.isoformat(),
                "sender_rut": doc.sender_rut,
                "sender_name": doc.sender_name,
                "net_amount": float(doc.net_amount),
                "tax_amount": float(doc.tax_amount),
                "exempt_amount": float(doc.exempt_amount),
                "total_amount": float(doc.total_amount),
                "status": doc.status,
                "sii_track_id": doc.sii_track_id,
                "file_url": doc.file_url,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
            }
            for doc in documents
        ],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total,
        }
    }


@router.get("/{document_id}")
async def get_purchase_document(
    document_id: UUID,
    repo: PurchaseDocumentRepositoryDep,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get a single purchase document by ID.

    User must have access to the company that owns this document.
    """
    # Get document using repository (injected via Depends)
    document = await repo.get(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase document not found"
        )

    # Verify access
    await verify_company_access(document.company_id, user_id, db)

    return {
        "data": {
            "id": str(document.id),
            "company_id": str(document.company_id),
            "document_type": document.document_type,
            "folio": document.folio,
            "issue_date": document.issue_date.isoformat(),
            "sender_rut": document.sender_rut,
            "sender_name": document.sender_name,
            "net_amount": float(document.net_amount),
            "tax_amount": float(document.tax_amount),
            "exempt_amount": float(document.exempt_amount),
            "total_amount": float(document.total_amount),
            "status": document.status,
            "dte_xml": document.dte_xml,
            "sii_track_id": document.sii_track_id,
            "file_url": document.file_url,
            "extra_data": document.extra_data,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
        }
    }


@router.post("")
async def create_purchase_document(
    data: PurchaseDocumentCreate,
    repo: PurchaseDocumentRepositoryDep,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Create a new purchase document.

    User must have access to the specified company.
    """
    company_id = UUID(data.company_id)

    # Verify access
    await verify_company_access(company_id, user_id, db)

    # Parse issue date
    try:
        issue_date = date.fromisoformat(data.issue_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid issue_date format. Use ISO format (YYYY-MM-DD)"
        )

    # Create document using repository (injected via Depends)
    document = await repo.create(
        company_id=company_id,
        document_type=data.document_type,
        folio=data.folio,
        issue_date=issue_date,
        sender_rut=data.sender_rut,
        sender_name=data.sender_name,
        net_amount=data.net_amount,
        tax_amount=data.tax_amount,
        exempt_amount=data.exempt_amount,
        total_amount=data.total_amount,
        status=data.status,
        dte_xml=data.dte_xml,
        sii_track_id=data.sii_track_id,
        file_url=data.file_url,
        extra_data=data.extra_data or {},
    )
    await db.commit()
    await db.refresh(document)

    return {
        "data": {
            "id": str(document.id),
            "company_id": str(document.company_id),
            "document_type": document.document_type,
            "folio": document.folio,
            "issue_date": document.issue_date.isoformat(),
            "total_amount": float(document.total_amount),
            "status": document.status,
        },
        "message": "Purchase document created successfully"
    }


@router.put("/{document_id}")
async def update_purchase_document(
    document_id: UUID,
    data: PurchaseDocumentUpdate,
    repo: PurchaseDocumentRepositoryDep,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update a purchase document.

    User must have access to the company that owns this document.
    """
    # Get document using repository (injected via Depends)
    document = await repo.get(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase document not found"
        )

    # Verify access
    await verify_company_access(document.company_id, user_id, db)

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)

    # Handle date conversion
    if "issue_date" in update_data and update_data["issue_date"]:
        try:
            update_data["issue_date"] = date.fromisoformat(update_data["issue_date"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid issue_date format. Use ISO format (YYYY-MM-DD)"
            )

    # Update using repository
    document = await repo.update(document_id, **update_data)
    await db.commit()
    await db.refresh(document)

    return {
        "data": {
            "id": str(document.id),
            "company_id": str(document.company_id),
            "document_type": document.document_type,
            "folio": document.folio,
            "issue_date": document.issue_date.isoformat(),
            "total_amount": float(document.total_amount),
            "status": document.status,
            "updated_at": document.updated_at.isoformat(),
        },
        "message": "Purchase document updated successfully"
    }


@router.delete("/{document_id}")
async def delete_purchase_document(
    document_id: UUID,
    repo: PurchaseDocumentRepositoryDep,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Delete a purchase document.

    User must have access to the company that owns this document.
    This is a hard delete. For soft delete, update the status instead.
    """
    # Get document using repository (injected via Depends)
    document = await repo.get(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase document not found"
        )

    # Verify access
    await verify_company_access(document.company_id, user_id, db)

    # Delete document using repository
    await repo.delete(document_id)
    await db.commit()

    return {
        "data": {
            "id": str(document_id),
        },
        "message": "Purchase document deleted successfully"
    }
