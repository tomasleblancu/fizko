"""Tax Documents router - Get company tax documents."""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import Company, PurchaseDocument, SalesDocument
from ...dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/tax-documents",
    tags=["tax-documents"],
    dependencies=[Depends(require_auth)]
)


class TaxDocument(BaseModel):
    """Tax document response model"""
    id: str
    company_id: str
    document_type: str
    document_number: str
    issue_date: str
    amount: float
    tax_amount: float | None
    status: str
    description: str | None
    created_at: str


@router.get("/{company_id}", response_model=List[TaxDocument])
async def get_tax_documents(
    company_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent tax documents for a company.

    Returns both purchase and sales documents, sorted by date descending.
    """

    # Verify company exists
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Get recent sales documents
    sales_stmt = select(SalesDocument).where(
        SalesDocument.company_id == company_id
    ).order_by(desc(SalesDocument.issue_date)).limit(limit // 2)

    sales_result = await db.execute(sales_stmt)
    sales_docs = sales_result.scalars().all()

    # Get recent purchase documents
    purchases_stmt = select(PurchaseDocument).where(
        PurchaseDocument.company_id == company_id
    ).order_by(desc(PurchaseDocument.issue_date)).limit(limit // 2)

    purchases_result = await db.execute(purchases_stmt)
    purchase_docs = purchases_result.scalars().all()

    # Convert to TaxDocument format
    documents: List[TaxDocument] = []

    for doc in sales_docs:
        documents.append(TaxDocument(
            id=str(doc.id),
            company_id=str(doc.company_id),
            document_type=f"venta_{doc.document_type}",
            document_number=str(doc.folio) if doc.folio else "N/A",
            issue_date=doc.issue_date.isoformat(),
            amount=float(doc.total_amount),
            tax_amount=float(doc.tax_amount) if doc.tax_amount else None,
            status=doc.status,
            description=f"{doc.document_type} - {doc.recipient_name or 'N/A'}",
            created_at=doc.created_at.isoformat()
        ))

    for doc in purchase_docs:
        documents.append(TaxDocument(
            id=str(doc.id),
            company_id=str(doc.company_id),
            document_type=f"compra_{doc.document_type}",
            document_number=str(doc.folio) if doc.folio else "N/A",
            issue_date=doc.issue_date.isoformat(),
            amount=float(doc.total_amount),
            tax_amount=float(doc.tax_amount) if doc.tax_amount else None,
            status=doc.status,
            description=f"{doc.document_type} - {doc.sender_name or 'N/A'}",
            created_at=doc.created_at.isoformat()
        ))

    # Sort by issue_date descending and limit
    documents.sort(key=lambda x: x.issue_date, reverse=True)

    return documents[:limit]
