"""Company Settings router - Manage company business configuration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import Company, CompanySettings, Session
from ...dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/companies",
    tags=["company-settings"],
    dependencies=[Depends(require_auth)]
)


# =============================================================================
# Request/Response Models
# =============================================================================

class CompanySettingsUpdate(BaseModel):
    """Request model for updating company settings."""
    has_formal_employees: Optional[bool] = None
    has_imports: Optional[bool] = None
    has_exports: Optional[bool] = None
    has_lease_contracts: Optional[bool] = None


class CompanySettingsResponse(BaseModel):
    """Response model for company settings."""
    id: str
    company_id: str
    has_formal_employees: Optional[bool]
    has_imports: Optional[bool]
    has_exports: Optional[bool]
    has_lease_contracts: Optional[bool]
    is_initial_setup_complete: bool
    initial_setup_completed_at: Optional[str]
    created_at: str
    updated_at: str


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/{company_id}/settings")
async def get_company_settings(
    company_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get company settings for a specific company.

    User must have an active session with the company to access settings.
    """
    # Verify user has access to this company
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
            detail="No tienes acceso a esta empresa"
        )

    # Get settings
    stmt = select(CompanySettings).where(
        CompanySettings.company_id == company_id
    )
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()

    if not settings:
        # Return default/empty settings if none exist yet
        return {
            "data": {
                "company_id": str(company_id),
                "has_formal_employees": None,
                "has_imports": None,
                "has_exports": None,
                "has_lease_contracts": None,
                "is_initial_setup_complete": False,
                "initial_setup_completed_at": None,
            },
            "message": "No settings found, using defaults"
        }

    return {
        "data": {
            "id": str(settings.id),
            "company_id": str(settings.company_id),
            "has_formal_employees": settings.has_formal_employees,
            "has_imports": settings.has_imports,
            "has_exports": settings.has_exports,
            "has_lease_contracts": settings.has_lease_contracts,
            "is_initial_setup_complete": settings.is_initial_setup_complete,
            "initial_setup_completed_at": settings.initial_setup_completed_at.isoformat() if settings.initial_setup_completed_at else None,
            "created_at": settings.created_at.isoformat(),
            "updated_at": settings.updated_at.isoformat(),
        }
    }


@router.post("/{company_id}/settings")
async def create_or_update_company_settings(
    company_id: UUID,
    data: CompanySettingsUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Create or update company settings.

    If this is the first time settings are being saved, marks initial_setup_complete.
    User must have an active session with the company.
    """
    # Verify user has access to this company
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
            detail="No tienes acceso a esta empresa"
        )

    # Check if company exists
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )

    # Check if settings exist
    stmt = select(CompanySettings).where(
        CompanySettings.company_id == company_id
    )
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()

    update_data = data.model_dump(exclude_unset=True)

    if settings:
        # Update existing settings
        for field, value in update_data.items():
            setattr(settings, field, value)

        # If all required fields are set and initial setup was not complete, mark as complete
        if not settings.is_initial_setup_complete:
            # Check if at least one setting has been configured (not None)
            has_any_setting = any([
                settings.has_formal_employees is not None,
                settings.has_imports is not None,
                settings.has_exports is not None,
                settings.has_lease_contracts is not None,
            ])

            if has_any_setting:
                settings.is_initial_setup_complete = True
                settings.initial_setup_completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(settings)
    else:
        # Create new settings
        settings = CompanySettings(
            company_id=company_id,
            **update_data
        )

        # Mark as complete if at least one setting is provided
        has_any_setting = any([
            update_data.get('has_formal_employees') is not None,
            update_data.get('has_imports') is not None,
            update_data.get('has_exports') is not None,
            update_data.get('has_lease_contracts') is not None,
        ])

        if has_any_setting:
            settings.is_initial_setup_complete = True
            settings.initial_setup_completed_at = datetime.utcnow()

        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return {
        "data": {
            "id": str(settings.id),
            "company_id": str(settings.company_id),
            "has_formal_employees": settings.has_formal_employees,
            "has_imports": settings.has_imports,
            "has_exports": settings.has_exports,
            "has_lease_contracts": settings.has_lease_contracts,
            "is_initial_setup_complete": settings.is_initial_setup_complete,
            "initial_setup_completed_at": settings.initial_setup_completed_at.isoformat() if settings.initial_setup_completed_at else None,
            "created_at": settings.created_at.isoformat(),
            "updated_at": settings.updated_at.isoformat(),
        },
        "message": "Configuración guardada exitosamente"
    }
