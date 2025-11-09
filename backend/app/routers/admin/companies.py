"""
Company management endpoints for admin - REFACTORED VERSION

This version uses repositories instead of direct SQL queries.
"""
import asyncio
import logging
import time
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id
from ...repositories import (
    CompanyRepository,
    ProfileRepository,
    SessionRepository,
    AdminStatsRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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


class DeleteCompanyResponse(BaseModel):
    """Response from deleting a company"""
    success: bool
    message: str
    company_id: str
    memory_deleted: bool
    details: dict


# ============================================================================
# COMPANY DETAIL
# ============================================================================

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

    # Initialize repositories
    profile_repo = ProfileRepository(db)
    company_repo = CompanyRepository(db)
    session_repo = SessionRepository(db)
    stats_repo = AdminStatsRepository(db)

    # Check user role and access permissions
    user = await profile_repo.get_by_user_id(current_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    is_admin = user.rol == "admin-kaiken"

    # If not admin, check if user has access to this company
    if not is_admin:
        has_access = await session_repo.user_has_access_to_company(current_user_id, company_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )

    # Get company with tax info
    start_time = time.time()
    company = await company_repo.get_with_tax_info(company_id)

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company {company_id} not found"
        )
    logger.info(f"[PERF] Company query took {(time.time() - start_time)*1000:.2f}ms")

    # Execute all queries in parallel using repositories
    parallel_start = time.time()
    users_data, document_stats = await asyncio.gather(
        session_repo.get_users_by_company(company_id, include_profile=True),
        stats_repo.get_document_stats(company_id)
    )
    logger.info(f"[PERF] Parallel queries took {(time.time() - parallel_start)*1000:.2f}ms")

    # Process users data
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
        if profile is not None
    ]

    # Convert NamedTuple to Pydantic model
    document_stats_model = DocumentStats(
        total_purchase_documents=document_stats.total_purchase_documents,
        total_sales_documents=document_stats.total_sales_documents,
        latest_purchase_date=document_stats.latest_purchase_date,
        latest_sales_date=document_stats.latest_sales_date,
        total_purchase_amount=document_stats.total_purchase_amount,
        total_sales_amount=document_stats.total_sales_amount
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
        if session.last_accessed_at and profile is not None
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
        document_stats=document_stats_model,
        sync_actions=sync_actions
    )


# ============================================================================
# COMPANY LIST
# ============================================================================

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

    # Initialize repositories
    profile_repo = ProfileRepository(db)
    company_repo = CompanyRepository(db)
    session_repo = SessionRepository(db)
    stats_repo = AdminStatsRepository(db)

    # Get current user's profile to check role
    user = await profile_repo.get_by_user_id(current_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    is_admin = user.rol == "admin-kaiken"

    # Build companies query based on role
    start_time = time.time()
    if is_admin:
        # Admin can see all companies
        logger.info(f"User {current_user_id} is admin-kaiken, showing all companies")
        companies = await company_repo.find_all(with_tax_info=True, order_by_created=True)
    else:
        # Regular user can only see companies they have sessions for
        logger.info(f"User {current_user_id} is regular user, showing only accessible companies")
        companies = await company_repo.find_companies_by_user(current_user_id, with_tax_info=True)

    logger.info(f"[PERF] Companies query took {(time.time() - start_time)*1000:.2f}ms")

    if not companies:
        return []

    # Extract company IDs for batch queries
    company_ids = [company.id for company in companies]

    # Execute all batch queries in parallel using repositories
    batch_start = time.time()
    users_count_map, doc_counts_map, last_activity_map = await asyncio.gather(
        session_repo.count_users_batch(company_ids),
        stats_repo.get_document_counts_batch(company_ids),
        session_repo.get_last_activity_batch(company_ids)
    )
    logger.info(f"[PERF] Batch queries took {(time.time() - batch_start)*1000:.2f}ms for {len(companies)} companies")

    # Build summaries using precomputed data
    summaries = []
    for company in companies:
        users_count = users_count_map.get(company.id, 0)
        doc_counts = doc_counts_map.get(company.id)
        total_documents = 0
        if doc_counts:
            total_documents = doc_counts.purchase_count + doc_counts.sales_count
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


# ============================================================================
# COMPANY DELETION
# ============================================================================

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

    # Initialize repositories
    profile_repo = ProfileRepository(db)
    company_repo = CompanyRepository(db)
    session_repo = SessionRepository(db)
    stats_repo = AdminStatsRepository(db)

    # 1. Verificar que el usuario sea admin-kaiken
    user = await profile_repo.get_admin_user(current_user_id)

    if not user:
        logger.warning(f"⚠️  Usuario {current_user_id} intentó eliminar compañía sin permisos de admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo usuarios admin-kaiken pueden eliminar compañías"
        )

    # 2. Verificar que la compañía existe
    company = await company_repo.get(company_id)

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

    # 4. Contar registros antes de eliminar (para el reporte) - usando repositorio
    entity_counts = await stats_repo.count_entities_for_deletion(company_id)

    # Contar sessions usando repositorio
    sessions_count = await session_repo.count_users_by_company(company_id)
    details = {
        "sessions_deleted": sessions_count,
        **entity_counts
    }

    logger.info(
        f"📊 Registros a eliminar: {sessions_count} sessions, "
        f"{entity_counts['purchase_documents_deleted']} compras, "
        f"{entity_counts['sales_documents_deleted']} ventas, "
        f"{entity_counts['f29_forms_deleted']} F29, "
        f"{entity_counts['calendar_events_deleted']} eventos, "
        f"{entity_counts['notifications_deleted']} notificaciones"
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
