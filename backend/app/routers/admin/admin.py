"""
Admin endpoints for company management
"""
import asyncio
import logging
import time
from uuid import UUID
from typing import List, Optional
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from ...config.database import get_db
from ...dependencies import get_current_user_id, require_auth
from ...db.models import (
    Company,
    CompanyTaxInfo,
    Session as SessionModel,
    Profile,
    PurchaseDocument,
    SalesDocument,
    Form29SIIDownload,
    EventTemplate,
    CompanyEvent,
    CalendarEvent,
    NotificationTemplate,
    NotificationHistory,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_auth)]
)


# Response models
class UserInfo(BaseModel):
    """User information"""
    id: str
    email: str
    full_name: Optional[str]
    name: Optional[str]
    lastname: Optional[str]
    rol: Optional[str]
    session_id: str
    is_active: bool
    last_accessed_at: Optional[datetime]
    created_at: datetime


class DocumentStats(BaseModel):
    """Document statistics"""
    total_purchase_documents: int
    total_sales_documents: int
    latest_purchase_date: Optional[datetime]
    latest_sales_date: Optional[datetime]
    total_purchase_amount: float
    total_sales_amount: float


class SyncAction(BaseModel):
    """Sync action information"""
    session_id: str
    user_email: str
    last_sync: Optional[datetime]
    total_syncs: int


class CompanySummary(BaseModel):
    """Company summary for list view"""
    id: str
    rut: str
    business_name: str
    trade_name: Optional[str]
    tax_regime: Optional[str]
    total_users: int
    total_documents: int
    created_at: datetime
    last_activity: Optional[datetime]


class CompanyDetailResponse(BaseModel):
    """Complete company information for admin view"""
    # Company info
    id: str
    rut: str
    business_name: str
    trade_name: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Tax info
    tax_regime: Optional[str]
    sii_activity_code: Optional[str]
    sii_activity_name: Optional[str]
    legal_representative_rut: Optional[str]
    legal_representative_name: Optional[str]

    # Users with access
    users: List[UserInfo]

    # Document statistics
    document_stats: DocumentStats

    # Sync actions
    sync_actions: List[SyncAction]


@router.get("/company/{company_id}", response_model=CompanyDetailResponse)
async def get_company_admin_detail(
    company_id: UUID,
    response: Response,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete company information for admin view

    Includes:
    - Company basic info and tax info
    - All users with access to the company
    - Document statistics (purchase and sales)
    - Sync action history

    Args:
        company_id: Company UUID
        current_user_id: Authenticated user ID
        db: Database session

    Returns:
        CompanyDetailResponse with all company information

    Raises:
        404: Company not found
    """
    logger.info(f"Company detail requested for {company_id} by user {current_user_id}")

    # Check user role and access permissions
    user_stmt = select(Profile).where(Profile.id == current_user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    is_admin = user.rol == "admin-kaiken"

    # If not admin, check if user has access to this company
    if not is_admin:
        session_check_stmt = select(SessionModel).where(
            SessionModel.user_id == current_user_id,
            SessionModel.company_id == company_id
        )
        session_check = await db.execute(session_check_stmt)
        if not session_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )

    # Get company with tax info
    start_time = time.time()
    company_stmt = select(Company).options(
        selectinload(Company.tax_info)
    ).where(Company.id == company_id)

    result = await db.execute(company_stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company {company_id} not found"
        )
    logger.info(f"[PERF] Company query took {(time.time() - start_time)*1000:.2f}ms")

    # Prepare queries to execute in parallel
    users_stmt = (
        select(SessionModel, Profile)
        .join(Profile, SessionModel.user_id == Profile.id)
        .where(SessionModel.company_id == company_id)
        .order_by(desc(SessionModel.last_accessed_at))
    )

    purchase_stats_stmt = select(
        func.count(PurchaseDocument.id).label('count'),
        func.max(PurchaseDocument.created_at).label('latest'),
        func.sum(PurchaseDocument.total_amount).label('total')
    ).where(PurchaseDocument.company_id == company_id)

    sales_stats_stmt = select(
        func.count(SalesDocument.id).label('count'),
        func.max(SalesDocument.created_at).label('latest'),
        func.sum(SalesDocument.total_amount).label('total')
    ).where(SalesDocument.company_id == company_id)

    # Execute all queries in parallel
    parallel_start = time.time()
    users_result, purchase_stats_result, sales_stats_result = await asyncio.gather(
        db.execute(users_stmt),
        db.execute(purchase_stats_stmt),
        db.execute(sales_stats_stmt)
    )
    logger.info(f"[PERF] Parallel queries took {(time.time() - parallel_start)*1000:.2f}ms")

    # Process users data
    users_data = users_result.all()
    users = [
        UserInfo(
            id=str(profile.id),
            email=profile.email,
            full_name=profile.full_name,
            name=profile.name,
            lastname=profile.lastname,
            rol=profile.rol,
            session_id=str(session.id),
            is_active=session.is_active,
            last_accessed_at=session.last_accessed_at,
            created_at=session.created_at
        )
        for session, profile in users_data
    ]

    # Process stats
    purchase_stats = purchase_stats_result.one()
    sales_stats = sales_stats_result.one()

    document_stats = DocumentStats(
        total_purchase_documents=purchase_stats.count or 0,
        total_sales_documents=sales_stats.count or 0,
        latest_purchase_date=purchase_stats.latest,
        latest_sales_date=sales_stats.latest,
        total_purchase_amount=float(purchase_stats.total or 0),
        total_sales_amount=float(sales_stats.total or 0)
    )

    # Get sync actions (from sessions with last_accessed_at)
    # TODO: When we implement sync job tracking, use that instead
    sync_actions = [
        SyncAction(
            session_id=str(session.id),
            user_email=profile.email,
            last_sync=session.last_accessed_at,
            total_syncs=1 if session.last_accessed_at else 0  # Placeholder
        )
        for session, profile in users_data
        if session.last_accessed_at
    ]

    # Set cache headers (30 seconds cache, revalidate)
    response.headers["Cache-Control"] = "private, max-age=30, must-revalidate"
    response.headers["ETag"] = f'"{company.id}-{company.updated_at.timestamp()}"'

    # Build response
    return CompanyDetailResponse(
        id=str(company.id),
        rut=company.rut,
        business_name=company.business_name,
        trade_name=company.trade_name,
        address=company.address,
        phone=company.phone,
        email=company.email,
        created_at=company.created_at,
        updated_at=company.updated_at,
        tax_regime=company.tax_info.tax_regime if company.tax_info else None,
        sii_activity_code=company.tax_info.sii_activity_code if company.tax_info else None,
        sii_activity_name=company.tax_info.sii_activity_name if company.tax_info else None,
        legal_representative_rut=company.tax_info.legal_representative_rut if company.tax_info else None,
        legal_representative_name=company.tax_info.legal_representative_name if company.tax_info else None,
        users=users,
        document_stats=document_stats,
        sync_actions=sync_actions
    )


@router.get("/companies", response_model=List[CompanySummary])
async def list_all_companies(
    response: Response,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List companies accessible to the current user

    - If user has rol="admin-kaiken": returns ALL companies
    - Otherwise: returns only companies where user has an active session

    Returns a list of companies with:
    - Basic company info
    - Number of users with access
    - Total number of documents
    - Last activity timestamp

    Args:
        current_user_id: Authenticated user ID
        db: Database session

    Returns:
        List of CompanySummary objects
    """
    logger.info(f"Companies list requested by user {current_user_id}")

    # Get current user's profile to check role
    user_stmt = select(Profile).where(Profile.id == current_user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    is_admin = user.rol == "admin-kaiken"

    # Build companies query based on role
    if is_admin:
        # Admin can see all companies
        logger.info(f"User {current_user_id} is admin-kaiken, showing all companies")
        companies_stmt = select(Company).options(
            selectinload(Company.tax_info)
        ).order_by(desc(Company.created_at))
    else:
        # Regular user can only see companies they have sessions for
        logger.info(f"User {current_user_id} is regular user, showing only accessible companies")
        companies_stmt = (
            select(Company)
            .join(SessionModel, SessionModel.company_id == Company.id)
            .options(selectinload(Company.tax_info))
            .where(SessionModel.user_id == current_user_id)
            .order_by(desc(Company.created_at))
        )

    start_time = time.time()
    result = await db.execute(companies_stmt)
    companies = result.scalars().all()
    logger.info(f"[PERF] Companies query took {(time.time() - start_time)*1000:.2f}ms")

    if not companies:
        return []

    # Extract company IDs for batch queries
    company_ids = [company.id for company in companies]

    # Build batch queries for all companies at once
    users_count_stmt = (
        select(
            SessionModel.company_id,
            func.count(SessionModel.id).label('user_count')
        )
        .where(SessionModel.company_id.in_(company_ids))
        .group_by(SessionModel.company_id)
    )

    purchase_count_stmt = (
        select(
            PurchaseDocument.company_id,
            func.count(PurchaseDocument.id).label('purchase_count')
        )
        .where(PurchaseDocument.company_id.in_(company_ids))
        .group_by(PurchaseDocument.company_id)
    )

    sales_count_stmt = (
        select(
            SalesDocument.company_id,
            func.count(SalesDocument.id).label('sales_count')
        )
        .where(SalesDocument.company_id.in_(company_ids))
        .group_by(SalesDocument.company_id)
    )

    last_activity_stmt = (
        select(
            SessionModel.company_id,
            func.max(SessionModel.last_accessed_at).label('last_activity')
        )
        .where(SessionModel.company_id.in_(company_ids))
        .group_by(SessionModel.company_id)
    )

    # Execute all batch queries in parallel
    batch_start = time.time()
    users_result, purchase_result, sales_result, activity_result = await asyncio.gather(
        db.execute(users_count_stmt),
        db.execute(purchase_count_stmt),
        db.execute(sales_count_stmt),
        db.execute(last_activity_stmt)
    )
    logger.info(f"[PERF] Batch queries took {(time.time() - batch_start)*1000:.2f}ms for {len(companies)} companies")

    # Build lookup dictionaries for O(1) access
    users_count_map = {row.company_id: row.user_count for row in users_result.all()}
    purchase_count_map = {row.company_id: row.purchase_count for row in purchase_result.all()}
    sales_count_map = {row.company_id: row.sales_count for row in sales_result.all()}
    last_activity_map = {row.company_id: row.last_activity for row in activity_result.all()}

    # Build summaries using precomputed data
    summaries = []
    for company in companies:
        users_count = users_count_map.get(company.id, 0)
        purchase_count = purchase_count_map.get(company.id, 0)
        sales_count = sales_count_map.get(company.id, 0)
        total_documents = purchase_count + sales_count
        last_activity = last_activity_map.get(company.id)

        summaries.append(CompanySummary(
            id=str(company.id),
            rut=company.rut,
            business_name=company.business_name,
            trade_name=company.trade_name,
            tax_regime=company.tax_info.tax_regime if company.tax_info else None,
            total_users=users_count,
            total_documents=total_documents,
            created_at=company.created_at,
            last_activity=last_activity
        ))

    logger.info(f"[PERF] Total list_all_companies took {(time.time() - start_time)*1000:.2f}ms")

    # Set cache headers (60 seconds cache for list view)
    response.headers["Cache-Control"] = "private, max-age=60, must-revalidate"
    # Generate ETag based on most recent company update
    if companies:
        latest_update = max(c.updated_at for c in companies)
        response.headers["ETag"] = f'"companies-{len(companies)}-{latest_update.timestamp()}"'

    return summaries


class F29DownloadInfo(BaseModel):
    """F29 download information"""
    id: str
    sii_folio: str
    sii_id_interno: Optional[str]
    period_year: int
    period_month: int
    period_display: str
    contributor_rut: str
    submission_date: Optional[datetime]
    status: str
    amount_cents: int
    pdf_storage_url: Optional[str]
    pdf_download_status: str
    pdf_download_error: Optional[str]
    pdf_downloaded_at: Optional[datetime]
    has_pdf: bool
    can_download_pdf: bool
    extra_data: Optional[dict]
    created_at: datetime
    updated_at: datetime


@router.get("/company/{company_id}/f29", response_model=List[F29DownloadInfo])
async def get_company_f29_list(
    company_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    year: Optional[int] = None,
    status: Optional[str] = None
):
    """
    Get F29 forms for a company

    Returns all Form29SIIDownload records for the specified company.
    Can be filtered by year and status.

    Args:
        company_id: Company UUID
        current_user_id: Authenticated user ID
        db: Database session
        year: Optional year filter
        status: Optional status filter (Vigente, Rectificado, Anulado)

    Returns:
        List of F29DownloadInfo

    Raises:
        404: Company not found
        403: User doesn't have access to this company
    """
    logger.info(f"F29 list requested for company {company_id} by user {current_user_id}")

    # Check user role and access permissions
    user_stmt = select(Profile).where(Profile.id == current_user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    is_admin = user.rol == "admin-kaiken"

    # If not admin, check if user has access to this company
    if not is_admin:
        session_check_stmt = select(SessionModel).where(
            SessionModel.user_id == current_user_id,
            SessionModel.company_id == company_id
        )
        session_check = await db.execute(session_check_stmt)
        if not session_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )

    # Verify company exists
    company_stmt = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_stmt)
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company {company_id} not found"
        )

    # Build F29 query
    f29_stmt = select(Form29SIIDownload).where(
        Form29SIIDownload.company_id == company_id
    ).order_by(
        desc(Form29SIIDownload.period_year),
        desc(Form29SIIDownload.period_month)
    )

    # Apply filters
    if year:
        f29_stmt = f29_stmt.where(Form29SIIDownload.period_year == year)

    if status:
        f29_stmt = f29_stmt.where(Form29SIIDownload.status == status)

    result = await db.execute(f29_stmt)
    f29_downloads = result.scalars().all()

    return [
        F29DownloadInfo(
            id=str(download.id),
            sii_folio=download.sii_folio,
            sii_id_interno=download.sii_id_interno,
            period_year=download.period_year,
            period_month=download.period_month,
            period_display=download.period_display,
            contributor_rut=download.contributor_rut,
            submission_date=download.submission_date,
            status=download.status,
            amount_cents=download.amount_cents,
            pdf_storage_url=download.pdf_storage_url,
            pdf_download_status=download.pdf_download_status,
            pdf_download_error=download.pdf_download_error,
            pdf_downloaded_at=download.pdf_downloaded_at,
            has_pdf=download.has_pdf,
            can_download_pdf=download.can_download_pdf,
            extra_data=download.extra_data,
            created_at=download.created_at,
            updated_at=download.updated_at
        )
        for download in f29_downloads
    ]


# ============================================================================
# Calendar Configuration Endpoints
# ============================================================================

@router.get("/companies/{company_id}/calendar-config")
async def get_company_calendar_config(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Obtiene la configuración de eventos tributarios para una empresa.

    Retorna:
    - Todos los event types disponibles
    - Cuáles están activos para esta empresa
    - Configuración de recurrencia personalizada
    """
    import time
    start_time = time.time()
    logger.info(f"[PERF] START get calendar config for company {company_id}")

    # Query optimizado: Company + EventTemplates con LEFT JOIN a CompanyEvents en una sola query
    from sqlalchemy.orm import joinedload
    from sqlalchemy import outerjoin

    # Verificar empresa y obtener todos los templates con sus company_events en una sola query
    company_stmt = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_stmt)
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    logger.info(f"[PERF] Company query took {(time.time() - start_time)*1000:.2f}ms")

    # Obtener todos los templates y los company_events de esta empresa en paralelo
    templates_start = time.time()
    event_templates_stmt = select(EventTemplate).order_by(EventTemplate.category, EventTemplate.name)
    rules_stmt = select(CompanyEvent).where(CompanyEvent.company_id == company_id)

    # Ejecutar ambas queries en paralelo
    import asyncio
    templates_result, rules_result = await asyncio.gather(
        db.execute(event_templates_stmt),
        db.execute(rules_stmt)
    )

    all_event_templates = templates_result.scalars().all()
    active_rules = {rule.event_template_id: rule for rule in rules_result.scalars().all()}

    logger.info(f"[PERF] Templates + rules query took {(time.time() - templates_start)*1000:.2f}ms")

    # Construir respuesta
    build_start = time.time()
    event_templates_config = []
    total_active = 0

    for event_template in all_event_templates:
        company_event = active_rules.get(event_template.id)
        is_active = company_event is not None and company_event.is_active
        if is_active:
            total_active += 1

        event_templates_config.append({
            "event_template_id": str(event_template.id),
            "code": event_template.code,
            "name": event_template.name,
            "description": event_template.description,
            "category": event_template.category,
            "authority": event_template.authority,
            "is_mandatory": event_template.is_mandatory,
            "default_recurrence": event_template.default_recurrence,
            "is_active": is_active,
            "company_event_id": str(company_event.id) if company_event else None,
            "custom_config": company_event.custom_config if company_event else {},
        })

    logger.info(f"[PERF] Build response took {(time.time() - build_start)*1000:.2f}ms")
    logger.info(f"[PERF] TOTAL get calendar config took {(time.time() - start_time)*1000:.2f}ms")

    return {
        "company_id": str(company_id),
        "company_name": company.business_name,
        "event_templates": event_templates_config,
        "total_available": len(event_templates_config),
        "total_active": total_active
    }


class ActivateEventRequest(BaseModel):
    """Request para activar un evento para una empresa"""
    event_template_id: UUID
    custom_config: Optional[dict] = None  # Opcional: overrides solo para casos edge


@router.post("/companies/{company_id}/calendar-config/activate")
async def activate_event_for_company(
    company_id: UUID,
    request: ActivateEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Activa un tipo de evento tributario para una empresa.

    Crea o actualiza un CompanyEvent vinculando el evento a la empresa.

    Este endpoint delega la lógica de negocio a CalendarService.
    """
    from app.services.calendar import CalendarService
    import time

    start_time = time.time()
    logger.info(
        f"[PERF] START activate event {request.event_template_id} "
        f"for company {company_id} by user {current_user_id}"
    )

    try:
        # Delegar a la capa de servicio
        service = CalendarService(db)
        result = await service.activate_event(
            company_id=company_id,
            event_template_id=request.event_template_id,
            custom_config=request.custom_config
        )

        logger.info(
            f"[PERF] TOTAL activate took {(time.time() - start_time)*1000:.2f}ms - "
            f"{result['action']}"
        )

        return result

    except ValueError as e:
        # Event template no existe
        logger.error(f"Activate event validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Activate event failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al activar evento: {str(e)}"
        )


@router.post("/companies/{company_id}/calendar-config/deactivate")
async def deactivate_event_for_company(
    company_id: UUID,
    request: ActivateEventRequest,  # Solo usamos event_template_id
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Desactiva un tipo de evento tributario para una empresa.

    Marca el CompanyEvent como inactivo (no lo elimina para mantener historial).

    Este endpoint delega la lógica de negocio a CalendarService.
    """
    from app.services.calendar import CalendarService
    import time

    start_time = time.time()
    logger.info(
        f"[PERF] START deactivate event {request.event_template_id} "
        f"for company {company_id} by user {current_user_id}"
    )

    try:
        # Delegar a la capa de servicio
        service = CalendarService(db)
        result = await service.deactivate_event(
            company_id=company_id,
            event_template_id=request.event_template_id
        )

        logger.info(
            f"[PERF] TOTAL deactivate took {(time.time() - start_time)*1000:.2f}ms"
        )

        return result

    except ValueError as e:
        # Company event no existe
        logger.error(f"Deactivate event validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Deactivate event failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desactivar evento: {str(e)}"
        )


@router.post("/companies/{company_id}/sync-calendar")
async def sync_calendar_events(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Sincroniza el calendario de eventos tributarios para una empresa.

    IMPORTANTE: Este endpoint es idempotente. Puede ejecutarse múltiples veces sin duplicar eventos.
    Solo sincroniza eventos para los company_events activos (is_active=true).

    Este endpoint delega la lógica de negocio a CalendarService:
    1. Verifica que la empresa existe
    2. Obtiene los vínculos empresa-evento activos (company_events)
    3. Para cada tipo de evento (F29, F22, etc.):
       - Crea eventos faltantes para los próximos periodos
       - Actualiza el estado de eventos existentes
       - Solo el próximo a vencer queda con estado 'in_progress'
       - Los demás quedan con estado 'pending'
    4. No modifica eventos completados o cancelados

    Args:
        company_id: UUID de la empresa

    Returns:
        Resumen de eventos creados y actualizados
    """
    from app.services.calendar import CalendarService

    logger.info(f"Calendar sync requested for company {company_id} by user {current_user_id}")

    try:
        # Delegar a la capa de servicio
        service = CalendarService(db)
        result = await service.sync_company_calendar(company_id=company_id)

        logger.info(
            f"Calendar sync completed for company {company_id}: "
            f"{result['total_created']} created, {result['total_updated']} updated"
        )

        return result

    except ValueError as e:
        # Empresa no existe o no tiene eventos activos
        logger.error(f"Calendar sync validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Calendar sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al sincronizar calendario: {str(e)}"
        )


class CalendarEventInfo(BaseModel):
    """Calendar event information"""
    id: str
    title: str
    description: Optional[str]
    event_template_code: str
    event_template_name: str
    category: str
    due_date: date
    period_start: Optional[date]
    period_end: Optional[date]
    status: str
    completion_date: Optional[datetime]
    completion_data: Optional[dict]
    auto_generated: bool
    created_at: datetime


@router.get("/company/{company_id}/calendar-events", response_model=List[CalendarEventInfo])
async def get_company_calendar_events(
    company_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """
    Get calendar events for a company.

    Returns all CalendarEvent records for the specified company.
    Can be filtered by date range and status.

    Args:
        company_id: Company UUID
        current_user_id: Authenticated user ID
        db: Database session
        start_date: Optional start date filter
        end_date: Optional end date filter
        status: Optional status filter (pending, in_progress, completed, overdue, cancelled)
        limit: Maximum number of results (default 100, max 500)

    Returns:
        List of CalendarEventInfo

    Raises:
        404: Company not found
        403: User doesn't have access to this company
    """
    logger.info(f"Calendar events requested for company {company_id} by user {current_user_id}")

    # Check user role and access permissions
    user_stmt = select(Profile).where(Profile.id == current_user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    is_admin = user.rol == "admin-kaiken"

    # If not admin, check if user has access to this company
    if not is_admin:
        session_check_stmt = select(SessionModel).where(
            SessionModel.user_id == current_user_id,
            SessionModel.company_id == company_id
        )
        session_check = await db.execute(session_check_stmt)
        if not session_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )

    # Verify company exists
    company_stmt = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_stmt)
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company {company_id} not found"
        )

    # Build calendar events query
    events_stmt = select(CalendarEvent).options(
        selectinload(CalendarEvent.event_template)
    ).where(
        CalendarEvent.company_id == company_id
    ).order_by(
        CalendarEvent.due_date
    )

    # Apply filters
    if start_date:
        events_stmt = events_stmt.where(CalendarEvent.due_date >= start_date)

    if end_date:
        events_stmt = events_stmt.where(CalendarEvent.due_date <= end_date)

    if status:
        events_stmt = events_stmt.where(CalendarEvent.status == status)

    events_stmt = events_stmt.limit(limit)

    result = await db.execute(events_stmt)
    calendar_events = result.scalars().all()

    return [
        CalendarEventInfo(
            id=str(event.id),
            title=event.title,
            description=event.description,
            event_template_code=event.event_template.code,
            event_template_name=event.event_template.name,
            category=event.event_template.category,
            due_date=event.due_date,
            period_start=event.period_start,
            period_end=event.period_end,
            status=event.status,
            completion_date=event.completion_date,
            completion_data=event.completion_data,
            auto_generated=event.auto_generated,
            created_at=event.created_at
        )
        for event in calendar_events
    ]


# =============================================================================
# NOTIFICATION TESTING
# =============================================================================

class SendTestNotificationRequest(BaseModel):
    """Request to send a test notification"""
    message: Optional[str] = "🔔 Notificación de prueba desde Fizko Admin"
    template_code: Optional[str] = None


class SendTestNotificationResponse(BaseModel):
    """Response from sending test notification"""
    success: bool
    message: str
    notifications_sent: int
    details: List[dict]


@router.post("/company/{company_id}/send-test-notification", response_model=SendTestNotificationResponse)
async def send_test_notification(
    company_id: UUID,
    request: SendTestNotificationRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Envía una notificación de prueba por WhatsApp a todos los usuarios con teléfono verificado de la empresa.

    Útil para:
    - Probar el sistema de notificaciones
    - Verificar integración con WhatsApp/Kapso
    - Testear el contexto de notificaciones en el agente

    Args:
        company_id: ID de la empresa
        request: Configuración de la notificación (mensaje personalizado y template opcional)

    Returns:
        Resumen de notificaciones enviadas
    """
    logger.info(f"📬 Admin solicitó envío de notificación de prueba para empresa {company_id}")

    # 1. Verificar que la empresa existe
    company_stmt = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_stmt)
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    # 2. Obtener usuarios de la empresa con teléfono verificado
    users_stmt = (
        select(Profile)
        .join(SessionModel, SessionModel.user_id == Profile.id)
        .where(
            SessionModel.company_id == company_id,
            SessionModel.is_active == True,
            Profile.phone.isnot(None),
            Profile.phone_verified == True,
        )
        .distinct()
    )

    users_result = await db.execute(users_stmt)
    users = users_result.scalars().all()

    if not users:
        return SendTestNotificationResponse(
            success=False,
            message="No hay usuarios con teléfono verificado asociados a esta empresa",
            notifications_sent=0,
            details=[]
        )

    logger.info(f"📱 Encontrados {len(users)} usuarios con teléfono verificado")

    # 3. Obtener o crear template de notificación de prueba
    template = None
    if request.template_code:
        # Buscar template específico
        template_stmt = select(NotificationTemplate).where(
            NotificationTemplate.code == request.template_code,
            NotificationTemplate.is_active == True
        )
        template_result = await db.execute(template_stmt)
        template = template_result.scalar_one_or_none()

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{request.template_code}' no encontrado o inactivo"
            )
    else:
        # Buscar template genérico de prueba
        template_stmt = select(NotificationTemplate).where(
            NotificationTemplate.code == "test_notification"
        )
        template_result = await db.execute(template_stmt)
        template = template_result.scalar_one_or_none()

    # 4. Importar WhatsApp service
    from ...services.whatsapp import WhatsAppService
    import os

    whatsapp_service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN", ""),
        base_url=os.getenv("KAPSO_API_BASE_URL", "https://app.kapso.ai/api/v1"),
    )

    # Get WhatsApp config ID
    whatsapp_config_id = os.getenv("DEFAULT_WHATSAPP_CONFIG_ID")

    if not whatsapp_config_id:
        raise HTTPException(
            status_code=500,
            detail="DEFAULT_WHATSAPP_CONFIG_ID no configurado en el servidor"
        )

    # 5. Enviar notificaciones a cada usuario
    details = []
    success_count = 0

    for user in users:
        try:
            # Preparar mensaje
            message = request.message or "🔔 Notificación de prueba desde Fizko Admin"

            if template:
                # Si hay template, usar su mensaje
                message = template.message_template.replace("{{company_name}}", company.business_name)
                message = message.replace("{{user_name}}", user.full_name or user.name or "Usuario")

            # Normalize phone number - remove '+' prefix if present
            normalized_phone = user.phone.lstrip('+') if user.phone else None

            if not normalized_phone:
                raise ValueError(f"Número de teléfono inválido: {user.phone}")

            # Find existing active conversation
            conversations = await whatsapp_service.list_conversations(
                whatsapp_config_id=whatsapp_config_id,
                limit=50,
            )

            conversation_id = None
            nodes = (
                conversations.get("data") or
                conversations.get("nodes") or
                conversations.get("conversations") or
                conversations.get("items") or
                []
            )

            for conv in nodes:
                conv_phone = conv.get("phone_number", "").lstrip('+')
                conv_status = conv.get("status", "")

                if conv_phone == normalized_phone and conv_status == "active":
                    conversation_id = conv.get("id")
                    break

            if not conversation_id:
                raise ValueError(f"No se encontró conversación activa para {normalized_phone}")

            # Enviar mensaje por WhatsApp
            result = await whatsapp_service.send_text(
                conversation_id=conversation_id,
                message=message,
            )

            # Guardar en historial de notificaciones
            notification_history = NotificationHistory(
                company_id=company_id,
                notification_template_id=template.id if template else None,
                entity_type="test",
                entity_id=None,
                user_id=user.id,
                phone_number=user.phone,
                message_content=message,
                status="sent",
                whatsapp_conversation_id=result.get("conversation_id"),
                whatsapp_message_id=result.get("id"),
                sent_at=datetime.utcnow(),
                extra_metadata={
                    "test_notification": True,
                    "sent_by_admin": str(user_id),
                    "template_code": template.code if template else None,
                }
            )

            db.add(notification_history)
            success_count += 1

            details.append({
                "user_email": user.email,
                "user_name": user.full_name or user.name,
                "phone": user.phone,
                "status": "sent",
                "message_id": result.get("id"),
                "conversation_id": result.get("conversation_id"),
            })

            logger.info(f"✅ Notificación enviada a {user.email} ({user.phone})")

        except Exception as e:
            logger.error(f"❌ Error enviando notificación a {user.email}: {e}")
            details.append({
                "user_email": user.email,
                "user_name": user.full_name or user.name,
                "phone": user.phone,
                "status": "error",
                "error": str(e),
            })

    # 6. Commit de historial
    await db.commit()

    return SendTestNotificationResponse(
        success=success_count > 0,
        message=f"Notificación enviada a {success_count} de {len(users)} usuarios",
        notifications_sent=success_count,
        details=details
    )


# ============================================================================
# NOTIFICATION SUBSCRIPTIONS
# ============================================================================

@router.get("/company/{company_id}/notification-subscriptions")
async def get_company_notification_subscriptions(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user_id)
):
    """
    Obtener todas las suscripciones de notificaciones de una empresa.
    """
    from app.db.models import NotificationSubscription, NotificationTemplate
    from sqlalchemy import select

    result = await db.execute(
        select(NotificationSubscription, NotificationTemplate)
        .join(
            NotificationTemplate,
            NotificationSubscription.notification_template_id == NotificationTemplate.id
        )
        .where(NotificationSubscription.company_id == company_id)
    )

    subscriptions_data = []
    for subscription, template in result.all():
        subscriptions_data.append({
            "id": str(subscription.id),
            "notification_template_id": str(subscription.notification_template_id),
            "is_enabled": subscription.is_enabled,
            "custom_timing_config": subscription.custom_timing_config,
            "custom_message_template": subscription.custom_message_template,
            "created_at": subscription.created_at.isoformat(),
            "template": {
                "id": str(template.id),
                "code": template.code,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "entity_type": template.entity_type,
                "is_active": template.is_active,
            }
        })

    return {"data": subscriptions_data}


@router.post("/company/{company_id}/notification-subscriptions")
async def create_company_notification_subscription(
    company_id: UUID,
    notification_template_id: UUID = Body(...),
    is_enabled: bool = Body(True),
    custom_timing_config: dict | None = Body(None),
    custom_message_template: str | None = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user_id)
):
    """
    Crear una nueva suscripción de notificación para una empresa.
    """
    from app.db.models import NotificationSubscription, NotificationTemplate
    from sqlalchemy import select

    # Verificar que el template existe
    template_result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == notification_template_id)
    )
    template = template_result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template de notificación no encontrado")

    # Verificar si ya existe una suscripción
    existing_result = await db.execute(
        select(NotificationSubscription).where(
            NotificationSubscription.company_id == company_id,
            NotificationSubscription.notification_template_id == notification_template_id
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una suscripción a este template para esta empresa"
        )

    # Crear suscripción
    subscription = NotificationSubscription(
        company_id=company_id,
        notification_template_id=notification_template_id,
        is_enabled=is_enabled,
        custom_timing_config=custom_timing_config,
        custom_message_template=custom_message_template
    )

    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    return {
        "data": {
            "id": str(subscription.id),
            "notification_template_id": str(subscription.notification_template_id),
            "is_enabled": subscription.is_enabled,
            "custom_timing_config": subscription.custom_timing_config,
            "custom_message_template": subscription.custom_message_template,
            "created_at": subscription.created_at.isoformat(),
        },
        "message": "Suscripción creada exitosamente"
    }


@router.put("/company/{company_id}/notification-subscriptions/{subscription_id}")
async def update_company_notification_subscription(
    company_id: UUID,
    subscription_id: UUID,
    is_enabled: bool | None = Body(None),
    custom_timing_config: dict | None = Body(None),
    custom_message_template: str | None = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user_id)
):
    """
    Actualizar una suscripción de notificación.
    """
    from app.db.models import NotificationSubscription
    from sqlalchemy import select

    result = await db.execute(
        select(NotificationSubscription).where(
            NotificationSubscription.id == subscription_id,
            NotificationSubscription.company_id == company_id
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")

    # Actualizar campos
    if is_enabled is not None:
        subscription.is_enabled = is_enabled
    if custom_timing_config is not None:
        subscription.custom_timing_config = custom_timing_config
    if custom_message_template is not None:
        subscription.custom_message_template = custom_message_template

    await db.commit()
    await db.refresh(subscription)

    return {
        "data": {
            "id": str(subscription.id),
            "notification_template_id": str(subscription.notification_template_id),
            "is_enabled": subscription.is_enabled,
            "custom_timing_config": subscription.custom_timing_config,
            "custom_message_template": subscription.custom_message_template,
        },
        "message": "Suscripción actualizada exitosamente"
    }


@router.delete("/company/{company_id}/notification-subscriptions/{subscription_id}")
async def delete_company_notification_subscription(
    company_id: UUID,
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user_id)
):
    """
    Eliminar una suscripción de notificación.
    """
    from app.db.models import NotificationSubscription
    from sqlalchemy import select

    result = await db.execute(
        select(NotificationSubscription).where(
            NotificationSubscription.id == subscription_id,
            NotificationSubscription.company_id == company_id
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")

    await db.delete(subscription)
    await db.commit()

    return {"message": "Suscripción eliminada exitosamente"}


# ============================================================================
# COMPANY DELETION
# ============================================================================

class DeleteCompanyResponse(BaseModel):
    """Response from deleting a company"""
    success: bool
    message: str
    company_id: str
    memory_deleted: bool
    details: dict


@router.delete("/company/{company_id}", response_model=DeleteCompanyResponse)
async def delete_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Elimina una compañía y todos sus datos relacionados.

    SOLO accesible para usuarios con rol admin-kaiken.

    Esta operación:
    1. Verifica permisos de admin
    2. Elimina toda la memoria asociada (Mem0)
    3. Elimina todos los registros en cascada:
       - Sessions
       - Documents (purchases, sales)
       - F29 forms
       - Calendar events
       - Notifications
       - Tax info
       - Company settings
    4. Elimina la compañía

    Args:
        company_id: ID de la compañía a eliminar
        current_user_id: ID del usuario autenticado
        db: Sesión de base de datos

    Returns:
        DeleteCompanyResponse con detalles de la eliminación

    Raises:
        403: Usuario no tiene permisos de admin
        404: Compañía no encontrada
        500: Error durante la eliminación
    """
    logger.info(f"🗑️  Solicitud de eliminación de compañía {company_id} por usuario {current_user_id}")

    # 1. Verificar que el usuario sea admin-kaiken
    user_stmt = select(Profile).where(Profile.id == current_user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    if user.rol != "admin-kaiken":
        logger.warning(f"⚠️  Usuario {current_user_id} intentó eliminar compañía sin permisos de admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo usuarios admin-kaiken pueden eliminar compañías"
        )

    # 2. Verificar que la compañía existe
    company_stmt = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_stmt)
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compañía {company_id} no encontrada"
        )

    company_name = company.business_name
    logger.info(f"📋 Eliminando compañía: {company_name} (RUT: {company.rut})")

    # 3. Eliminar memoria asociada en Mem0
    memory_deleted = False
    try:
        from ...agents.tools.memory.memory_tools import get_mem0_client

        mem0_client = get_mem0_client()
        entity_id = f"company_{company_id}"

        logger.info(f"🧠 Eliminando memoria de Mem0 para entity_id: {entity_id}")

        # Usar método síncrono con asyncio
        import asyncio
        await asyncio.to_thread(
            mem0_client.delete_all,
            user_id=entity_id
        )

        memory_deleted = True
        logger.info(f"✅ Memoria de compañía eliminada exitosamente de Mem0")

    except Exception as e:
        logger.error(f"❌ Error eliminando memoria de Mem0: {e}", exc_info=True)
        # No fallar la eliminación completa si falla Mem0
        memory_deleted = False

    # 4. Contar registros antes de eliminar (para el reporte)
    details = {}

    # Contar sessions
    sessions_count_stmt = select(func.count(SessionModel.id)).where(
        SessionModel.company_id == company_id
    )
    sessions_count = (await db.execute(sessions_count_stmt)).scalar() or 0
    details["sessions_deleted"] = sessions_count

    # Contar documentos de compra
    purchases_count_stmt = select(func.count(PurchaseDocument.id)).where(
        PurchaseDocument.company_id == company_id
    )
    purchases_count = (await db.execute(purchases_count_stmt)).scalar() or 0
    details["purchase_documents_deleted"] = purchases_count

    # Contar documentos de venta
    sales_count_stmt = select(func.count(SalesDocument.id)).where(
        SalesDocument.company_id == company_id
    )
    sales_count = (await db.execute(sales_count_stmt)).scalar() or 0
    details["sales_documents_deleted"] = sales_count

    # Contar F29
    f29_count_stmt = select(func.count(Form29SIIDownload.id)).where(
        Form29SIIDownload.company_id == company_id
    )
    f29_count = (await db.execute(f29_count_stmt)).scalar() or 0
    details["f29_forms_deleted"] = f29_count

    # Contar eventos de calendario
    calendar_count_stmt = select(func.count(CalendarEvent.id)).where(
        CalendarEvent.company_id == company_id
    )
    calendar_count = (await db.execute(calendar_count_stmt)).scalar() or 0
    details["calendar_events_deleted"] = calendar_count

    # Contar notificaciones
    notifications_count_stmt = select(func.count(NotificationHistory.id)).where(
        NotificationHistory.company_id == company_id
    )
    notifications_count = (await db.execute(notifications_count_stmt)).scalar() or 0
    details["notifications_deleted"] = notifications_count

    logger.info(
        f"📊 Registros a eliminar: {sessions_count} sessions, "
        f"{purchases_count} compras, {sales_count} ventas, "
        f"{f29_count} F29, {calendar_count} eventos, "
        f"{notifications_count} notificaciones"
    )

    # 5. Eliminar la compañía (cascada se encarga del resto según las relaciones del modelo)
    try:
        await db.delete(company)
        await db.commit()

        logger.info(f"✅ Compañía {company_name} eliminada exitosamente")

        return DeleteCompanyResponse(
            success=True,
            message=f"Compañía '{company_name}' eliminada exitosamente",
            company_id=str(company_id),
            memory_deleted=memory_deleted,
            details=details
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error eliminando compañía: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar compañía: {str(e)}"
        )
