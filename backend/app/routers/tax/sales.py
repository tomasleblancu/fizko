"""Sales documents router - Manage sales documents (documentos de venta)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import SalesDocument, Session
from ...dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/sales-documents",
    tags=["sales-documents"],
    dependencies=[Depends(require_auth)]
)


# =============================================================================
# Request/Response Models
# =============================================================================

class SalesDocumentCreate(BaseModel):
    """Request model for creating a sales document."""
    company_id: str  # UUID string
    document_type: str  # factura_venta, boleta, nota_credito_venta, nota_debito_venta, factura_exenta
    folio: Optional[int] = None
    issue_date: str  # ISO date string
    recipient_rut: Optional[str] = None
    recipient_name: Optional[str] = None
    net_amount: Decimal
    tax_amount: Decimal = Decimal("0")
    exempt_amount: Decimal = Decimal("0")
    total_amount: Decimal
    status: str = "pending"
    dte_xml: Optional[str] = None
    sii_track_id: Optional[str] = None
    file_url: Optional[str] = None
    extra_data: Optional[dict] = None


class SalesDocumentUpdate(BaseModel):
    """Request model for updating a sales document."""
    document_type: Optional[str] = None
    folio: Optional[int] = None
    issue_date: Optional[str] = None
    recipient_rut: Optional[str] = None
    recipient_name: Optional[str] = None
    net_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    exempt_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    status: Optional[str] = None
    dte_xml: Optional[str] = None
    sii_track_id: Optional[str] = None
    file_url: Optional[str] = None
    extra_data: Optional[dict] = None


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
async def list_sales_documents(
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
    List sales documents for a company with optional filtering.

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

    # Build query
    stmt = select(SalesDocument).where(
        SalesDocument.company_id == company_uuid
    )

    # Apply filters
    if document_type:
        stmt = stmt.where(SalesDocument.document_type == document_type)
    if status_filter:
        stmt = stmt.where(SalesDocument.status == status_filter)
    if date_from:
        try:
            from_date = date.fromisoformat(date_from)
            stmt = stmt.where(SalesDocument.issue_date >= from_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use ISO format (YYYY-MM-DD)"
            )
    if date_to:
        try:
            to_date = date.fromisoformat(date_to)
            stmt = stmt.where(SalesDocument.issue_date <= to_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use ISO format (YYYY-MM-DD)"
            )

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination and ordering
    stmt = stmt.offset(skip).limit(limit).order_by(SalesDocument.issue_date.desc())

    result = await db.execute(stmt)
    documents = result.scalars().all()

    return {
        "data": [
            {
                "id": str(doc.id),
                "company_id": str(doc.company_id),
                "document_type": doc.document_type,
                "folio": doc.folio,
                "issue_date": doc.issue_date.isoformat(),
                "recipient_rut": doc.recipient_rut,
                "recipient_name": doc.recipient_name,
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
async def get_sales_document(
    document_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get a single sales document by ID.

    User must have access to the company that owns this document.
    """
    # Get document
    stmt = select(SalesDocument).where(SalesDocument.id == document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales document not found"
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
            "recipient_rut": document.recipient_rut,
            "recipient_name": document.recipient_name,
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
async def create_sales_document(
    data: SalesDocumentCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Create a new sales document.

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

    # Create document
    document = SalesDocument(
        company_id=company_id,
        document_type=data.document_type,
        folio=data.folio,
        issue_date=issue_date,
        recipient_rut=data.recipient_rut,
        recipient_name=data.recipient_name,
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

    db.add(document)
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
        "message": "Sales document created successfully"
    }


@router.put("/{document_id}")
async def update_sales_document(
    document_id: UUID,
    data: SalesDocumentUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update a sales document.

    User must have access to the company that owns this document.
    """
    # Get document
    stmt = select(SalesDocument).where(SalesDocument.id == document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales document not found"
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

    for field, value in update_data.items():
        setattr(document, field, value)

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
        "message": "Sales document updated successfully"
    }


@router.delete("/{document_id}")
async def delete_sales_document(
    document_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Delete a sales document.

    User must have access to the company that owns this document.
    This is a hard delete. For soft delete, update the status instead.
    """
    # Get document
    stmt = select(SalesDocument).where(SalesDocument.id == document_id)
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales document not found"
        )

    # Verify access
    await verify_company_access(document.company_id, user_id, db)

    # Delete document
    await db.delete(document)
    await db.commit()

    return {
        "data": {
            "id": str(document_id),
        },
        "message": "Sales document deleted successfully"
    }
