"""
Repository dependency injection factories.

Provides FastAPI dependencies for repository injection, eliminating
the need to manually instantiate repositories in every endpoint.

Usage:
    @router.get("/people")
    async def list_people(
        repo: PersonRepository = Depends(get_person_repository)
    ):
        return await repo.find_by_company(company_id)

Benefits:
    - DRY: No more `repo = PersonRepository(db)` in every endpoint
    - Testable: Easy to mock repositories in tests
    - Consistent: Standardized repository instantiation
    - Clean: Less boilerplate in endpoint functions
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.repositories.personnel import PersonRepository, PayrollRepository
from app.repositories.tax import (
    PurchaseDocumentRepository,
    SalesDocumentRepository,
    Form29Repository,
    TaxDocumentRepository
)


# =============================================================================
# Personnel Repositories
# =============================================================================

def get_person_repository(
    db: AsyncSession = Depends(get_db)
) -> PersonRepository:
    """
    Get PersonRepository instance.

    Args:
        db: Database session (injected)

    Returns:
        PersonRepository instance
    """
    return PersonRepository(db)


def get_payroll_repository(
    db: AsyncSession = Depends(get_db)
) -> PayrollRepository:
    """
    Get PayrollRepository instance.

    Args:
        db: Database session (injected)

    Returns:
        PayrollRepository instance
    """
    return PayrollRepository(db)


# =============================================================================
# Tax Document Repositories
# =============================================================================

def get_purchase_document_repository(
    db: AsyncSession = Depends(get_db)
) -> PurchaseDocumentRepository:
    """
    Get PurchaseDocumentRepository instance.

    Args:
        db: Database session (injected)

    Returns:
        PurchaseDocumentRepository instance
    """
    return PurchaseDocumentRepository(db)


def get_sales_document_repository(
    db: AsyncSession = Depends(get_db)
) -> SalesDocumentRepository:
    """
    Get SalesDocumentRepository instance.

    Args:
        db: Database session (injected)

    Returns:
        SalesDocumentRepository instance
    """
    return SalesDocumentRepository(db)


def get_form29_repository(
    db: AsyncSession = Depends(get_db)
) -> Form29Repository:
    """
    Get Form29Repository instance.

    Args:
        db: Database session (injected)

    Returns:
        Form29Repository instance
    """
    return Form29Repository(db)


def get_tax_document_repository(
    db: AsyncSession = Depends(get_db)
) -> TaxDocumentRepository:
    """
    Get TaxDocumentRepository (composite) instance.

    Args:
        db: Database session (injected)

    Returns:
        TaxDocumentRepository instance
    """
    return TaxDocumentRepository(db)


# =============================================================================
# Type Aliases for Convenience
# =============================================================================

# These make endpoint signatures even cleaner:
# async def list_people(repo: PersonRepositoryDep):
#     ...

PersonRepositoryDep = Annotated[PersonRepository, Depends(get_person_repository)]
PayrollRepositoryDep = Annotated[PayrollRepository, Depends(get_payroll_repository)]
PurchaseDocumentRepositoryDep = Annotated[PurchaseDocumentRepository, Depends(get_purchase_document_repository)]
SalesDocumentRepositoryDep = Annotated[SalesDocumentRepository, Depends(get_sales_document_repository)]
Form29RepositoryDep = Annotated[Form29Repository, Depends(get_form29_repository)]
TaxDocumentRepositoryDep = Annotated[TaxDocumentRepository, Depends(get_tax_document_repository)]
