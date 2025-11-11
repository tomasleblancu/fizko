"""
Router para consulta de formularios F29

Proporciona endpoints para listar y consultar formularios F29 sincronizados.
"""
import logging
from uuid import UUID
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, ConfigDict, Field

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...config.database import get_db
from ...db.models import Session as SessionModel, Profile
from ...dependencies import get_current_user_id, require_auth
from ...services.sii import SIIService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/forms",
    tags=["sii-forms"],
    dependencies=[Depends(require_auth)]
)


class F29FormResponse(BaseModel):
    """Response model for F29 form"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    folio: str
    period_year: int
    period_month: int
    period_display: str
    submission_date: Optional[date]
    status: str
    amount_cents: int
    pdf_download_status: str
    has_pdf: bool
    pdf_url: Optional[str]
    created_at: str


class F29FormsListResponse(BaseModel):
    """Response model for list of F29 forms"""
    forms: List[F29FormResponse]
    total: int
    filtered: int


async def verify_company_access(
    company_id: UUID,
    current_user_id: UUID,
    db: AsyncSession
) -> None:
    """
    Verifica que el usuario tenga acceso a la empresa

    Args:
        company_id: ID de la empresa
        current_user_id: ID del usuario autenticado
        db: Sesión de base de datos

    Raises:
        HTTPException: Si el usuario no tiene acceso
    """
    # Verificar si tiene sesión para esta empresa
    stmt_access = select(SessionModel).where(
        SessionModel.user_id == current_user_id,
        SessionModel.company_id == company_id
    )
    result_access = await db.execute(stmt_access)
    has_company_access = result_access.scalar_one_or_none() is not None

    # Verificar si es admin
    user_stmt = select(Profile).where(Profile.id == current_user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    is_admin = user and user.rol == "admin-kaiken"

    if not has_company_access and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="No tienes acceso a los formularios de esta empresa"
        )


@router.get("/f29", response_model=F29FormsListResponse)
async def list_f29_forms(
    company_id: UUID,
    form_type: Optional[str] = Query(None, description="Filter by form type: 'monthly' or 'annual'"),
    year: Optional[int] = Query(None, description="Filter by year"),
    status: Optional[str] = Query(None, description="Filter by status: 'Vigente', 'Rectificado', 'Anulado'"),
    pdf_status: Optional[str] = Query(None, description="Filter by PDF download status: 'pending', 'downloaded', 'error'"),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista formularios F29 de una empresa con filtros opcionales

    Args:
        company_id: ID de la empresa
        form_type: Tipo de formulario ('monthly' para mensuales, 'annual' para anuales)
        year: Filtrar por año
        status: Filtrar por estado del formulario
        pdf_status: Filtrar por estado de descarga del PDF
        current_user_id: ID del usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de formularios F29 con sus detalles

    Example:
        GET /api/sii/forms/f29?company_id=550e8400-e29b-41d4-a716-446655440000&form_type=monthly
        GET /api/sii/forms/f29?company_id=550e8400-e29b-41d4-a716-446655440000&year=2024&status=Vigente
    """
    logger.info(
        f"📋 F29 forms list requested by user {current_user_id}: "
        f"company={company_id}, form_type={form_type}, year={year}, status={status}"
    )

    try:
        # Verificar acceso del usuario a la empresa
        await verify_company_access(company_id, current_user_id, db)

        # Delegar al servicio
        service = SIIService(db)
        result = await service.list_f29_forms(
            company_id=company_id,
            form_type=form_type,
            year=year,
            status=status,
            pdf_status=pdf_status
        )

        # Convertir a response model
        forms_data = [
            F29FormResponse(
                id=str(form.id),
                folio=form.sii_folio,
                period_year=form.period_year,
                period_month=form.period_month,
                period_display=form.period_display,
                submission_date=form.submission_date,
                status=form.status,
                amount_cents=form.amount_cents,
                pdf_download_status=form.pdf_download_status,
                has_pdf=form.has_pdf,
                pdf_url=form.pdf_storage_url,
                created_at=form.created_at.isoformat()
            )
            for form in result["forms"]
        ]

        logger.info(
            f"✅ Returning {len(forms_data)} F29 forms (total: {result['total']})"
        )

        return F29FormsListResponse(
            forms=forms_data,
            total=result["total"],
            filtered=result["filtered"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing F29 forms: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar formularios F29: {str(e)}"
        )
