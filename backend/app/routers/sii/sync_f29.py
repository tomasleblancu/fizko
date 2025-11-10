"""
Router para sincronización de formularios F29

Proporciona endpoints para sincronizar formularios F29 desde el SII,
incluyendo descarga automática de PDFs y extracción de datos.
"""
import logging
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...config.database import get_db
from ...db.models import Session as SessionModel, Form29SIIDownload, Profile
from ...dependencies import get_current_user_id, require_auth
from ...services.sii import SIIService

logger = logging.getLogger(__name__)


async def validate_session_access(
    session_id: UUID,
    current_user_id: UUID,
    db: AsyncSession
) -> SessionModel:
    """
    Valida que el usuario tenga acceso a usar la sesión.

    Permite acceso si:
    - Usuario es admin-kaiken (puede usar cualquier sesión)
    - Usuario tiene una sesión activa para la misma compañía
    - Usuario es el dueño de la sesión

    Args:
        session_id: ID de la sesión a validar
        current_user_id: ID del usuario que intenta usar la sesión
        db: Sesión de base de datos

    Returns:
        SessionModel si el acceso es permitido

    Raises:
        HTTPException 404 si la sesión no existe
        HTTPException 403 si el usuario no tiene permisos
        HTTPException 400 si la sesión no está activa
    """
    # 1. Obtener la sesión
    stmt = select(SessionModel).where(SessionModel.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        logger.warning(f"⚠️ Session {session_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sesión {session_id} no encontrada"
        )

    # 2. Verificar si la sesión está activa
    if not session.is_active:
        logger.warning(f"⚠️ Session {session_id} is not active")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La sesión no está activa. Por favor, vuelve a autenticarte con el SII."
        )

    # 3. Convertir current_user_id a UUID si es string
    if isinstance(current_user_id, str):
        from uuid import UUID as UUIDType
        current_user_id = UUIDType(current_user_id)

    # 4. Si el usuario es el dueño de la sesión, permitir
    if session.user_id == current_user_id:
        logger.info(f"✅ User {current_user_id} is owner of session {session_id}")
        return session

    # 5. Obtener el perfil del usuario para verificar si es admin
    user_stmt = select(Profile).where(Profile.id == current_user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        logger.warning(f"⚠️ User profile {current_user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de usuario no encontrado"
        )

    # 6. Si es admin, permitir usar cualquier sesión
    is_admin = user.rol == "admin-kaiken"
    if is_admin:
        logger.info(f"✅ Admin user {current_user_id} accessing session {session_id}")
        return session

    # 7. Verificar si el usuario tiene acceso a la compañía (tiene alguna sesión para esa compañía)
    company_access_stmt = select(SessionModel).where(
        SessionModel.user_id == current_user_id,
        SessionModel.company_id == session.company_id
    )
    company_access_result = await db.execute(company_access_stmt)
    has_company_access = company_access_result.scalar_one_or_none() is not None

    if has_company_access:
        logger.info(
            f"✅ User {current_user_id} has access to company {session.company_id}, "
            f"allowing use of session {session_id}"
        )
        return session

    # 8. Si no cumple ninguna condición, rechazar
    logger.warning(
        f"⚠️ User {current_user_id} attempted to use session {session_id} "
        f"belonging to user {session.user_id} without proper permissions"
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para usar esta sesión"
    )

router = APIRouter(
    prefix="/f29",
    tags=["sii-sync-f29"],
    dependencies=[Depends(require_auth)]
)


# ============================================================================
# F29 PDF Download - DEBE IR ANTES del endpoint /{year} para evitar conflictos
# ============================================================================

class DownloadPDFsRequest(BaseModel):
    """Request para descargar PDFs de F29"""
    session_id: UUID = Field(..., description="ID de sesión SII activa")
    year: Optional[int] = Field(None, description="Año a filtrar (opcional)")
    download_ids: Optional[List[UUID]] = Field(None, description="IDs específicos a descargar (opcional)")


class DownloadSinglePDFRequest(BaseModel):
    """Request para descargar un solo PDF de F29"""
    session_id: UUID = Field(..., description="ID de sesión SII activa")
    download_id: UUID = Field(..., description="ID del Form29SIIDownload a descargar")


@router.post("/download-single-pdf")
async def download_single_f29_pdf(
    request: DownloadSinglePDFRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Descarga el PDF de un solo formulario F29 específico (para testing/debug)

    Este endpoint es útil para probar la descarga de PDFs individuales
    antes de ejecutar descargas masivas.

    Args:
        request: Parámetros con session_id y download_id
        current_user_id: ID del usuario autenticado
        db: Sesión de base de datos

    Returns:
        Resultado de la descarga con detalles

    Example:
        POST /api/sii/sync/f29/download-single-pdf
        {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "download_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    """
    logger.info(
        f"📥 Single F29 PDF download requested by user {current_user_id}: "
        f"session={request.session_id}, download_id={request.download_id}"
    )

    # Validar que el usuario tenga acceso a usar la sesión
    session = await validate_session_access(request.session_id, current_user_id, db)

    # 2. Verificar que el download existe y pertenece a la company de la sesión
    stmt_download = select(Form29SIIDownload).where(
        Form29SIIDownload.id == request.download_id,
        Form29SIIDownload.company_id == session.company_id
    )
    result_download = await db.execute(stmt_download)
    download = result_download.scalar_one_or_none()

    if not download:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form29 download record not found"
        )

    # 3. Log session info for debugging
    logger.info(f"📋 Session {request.session_id} is active, downloading PDF with Selenium")

    # 4. Descargar el PDF (incluye extracción automática de datos)
    service = SIIService(db)
    result = await service.download_and_save_f29_pdf(
        download_id=str(request.download_id),
        session_id=request.session_id
    )

    if not result.get("success"):
        logger.error(f"❌ Single PDF download failed: {result.get('error')}")
        return {
            "success": False,
            "error": result.get("error"),
            "download_id": str(request.download_id),
            "folio": download.sii_folio
        }

    logger.info(f"✅ Single PDF downloaded successfully: folio={download.sii_folio}")
    return {
        "success": True,
        "download_id": str(request.download_id),
        "folio": download.sii_folio,
        "url": result.get("url"),
        "size_bytes": result.get("size_bytes")
    }


@router.post("/download-pdfs")
async def download_f29_pdfs(
    request: DownloadPDFsRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Descarga PDFs de formularios F29 que están sincronizados pero sin PDF

    Este endpoint descarga los PDFs reales del SII para formularios que ya están
    sincronizados en la base de datos pero que no tienen el PDF descargado.

    Usa la misma lógica que el task de Celery `sync_f29_pdfs_missing`.

    Args:
        request: Parámetros de descarga (session_id, year opcional, download_ids opcional)
        current_user_id: ID del usuario autenticado
        db: Sesión de base de datos

    Returns:
        Resultado de la descarga con estadísticas

    Example:
        POST /api/sii/sync/f29/download-pdfs
        {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "year": 2024
        }

        Response:
        {
            "success": true,
            "company_id": "...",
            "session_id": "...",
            "total_pending": 12,
            "downloaded": 10,
            "failed": 2,
            "errors": [...]
        }

    Note:
        Los parámetros `year` y `download_ids` actualmente se ignoran.
        Para implementarlos, deben agregarse al servicio FormService.download_f29_pdfs_for_session()
    """
    logger.info(
        f"📥 F29 PDF download requested by user {current_user_id}: "
        f"session={request.session_id}, year={request.year}, download_ids={request.download_ids}"
    )

    # Validar que el usuario tenga acceso a usar la sesión
    session = await validate_session_access(request.session_id, current_user_id, db)

    try:
        service = SIIService(db)

        # Delegar toda la lógica al servicio (igual que el task de Celery)
        result = await service.download_f29_pdfs_for_session(
            session_id=request.session_id,
            company_id=session.company_id,
            max_per_company=999  # Sin límite para requests manuales del usuario
        )

        if not result.get("success"):
            logger.error(f"❌ F29 PDF download failed: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Error al descargar PDFs de F29")
            )

        logger.info(
            f"✅ F29 PDF download completed: {result['downloaded']} downloaded, "
            f"{result['failed']} failed"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ F29 PDF download failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al descargar PDFs de F29: {str(e)}"
        )


# ============================================================================
# F29 List Sync
# ============================================================================

@router.post("/{year}")
async def sync_f29_for_year(
    year: int,
    session_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Sincroniza formularios F29 del SII para un año específico

    Extrae la lista de F29s desde el portal SII y los guarda en la base de datos.
    NO descarga los PDFs automáticamente - usar el endpoint /download-pdfs para eso.

    Args:
        year: Año a sincronizar (ej: 2024)
        session_id: ID de la sesión SII activa
        current_user_id: ID del usuario autenticado
        db: Sesión de base de datos

    Returns:
        Resultado de la sincronización con estadísticas

    Example:
        POST /api/sii/sync/f29/2024?session_id=550e8400-e29b-41d4-a716-446655440000

        Response:
        {
            "success": true,
            "forms_synced": 12,
            "year": 2024,
            "company_id": "...",
            "message": "12 formularios F29 sincronizados"
        }
    """
    logger.info(
        f"🔄 F29 sync requested by user {current_user_id}: "
        f"session={session_id}, year={year}"
    )

    # Validar que el usuario tenga acceso a usar la sesión
    session = await validate_session_access(session_id, current_user_id, db)

    try:
        service = SIIService(db)

        # Extraer formularios del SII
        formularios = await service.extract_f29_lista(
            session_id=str(session_id),
            anio=str(year)
        )

        if not formularios:
            logger.info(f"No F29 forms found for year {year}")
            return {
                "success": True,
                "forms_synced": 0,
                "year": year,
                "company_id": str(session.company_id),
                "message": f"No se encontraron formularios F29 para el año {year}"
            }

        # Guardar en la base de datos
        saved_downloads = await service.save_f29_downloads(
            company_id=str(session.company_id),
            formularios=formularios
        )

        # Commit de cambios
        await db.commit()

        logger.info(f"✅ F29 sync completed: {len(saved_downloads)} forms synced")

        return {
            "success": True,
            "forms_synced": len(saved_downloads),
            "year": year,
            "company_id": str(session.company_id),
            "message": f"{len(saved_downloads)} formularios F29 sincronizados"
        }

    except ValueError as e:
        await db.rollback()
        logger.error(f"❌ F29 sync validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ F29 sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al sincronizar F29: {str(e)}"
        )



# ============================================================================
# F29 Data Extraction
# ============================================================================

@router.get("/extract-data/{download_id}")
async def get_extracted_f29_data(
    download_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los datos estructurados ya extraídos del PDF F29

    Los datos se extraen automáticamente cuando se descarga el PDF,
    por lo que este endpoint simplemente retorna los datos almacenados
    en el campo extra_data del registro Form29SIIDownload.

    Si el PDF no ha sido descargado aún, retorna un error indicando
    que primero debe descargarse el PDF usando /download-single-pdf.

    Args:
        download_id: UUID del registro Form29SIIDownload
        current_user_id: ID del usuario autenticado
        db: Sesión de base de datos

    Returns:
        Datos extraídos del PDF

    Example:
        GET /api/sii/sync/f29/extract-data/550e8400...

        Response:
        {
            "success": true,
            "download_id": "550e8400...",
            "folio": "7904207766",
            "has_pdf": true,
            "has_extracted_data": true,
            "extracted_data": {
                "extraction_success": true,
                "codes_extracted": 45,
                "encabezado": {...},
                "debitos": {...},
                "creditos": {...},
                ...
            }
        }
    """
    logger.info(
        f"🔍 F29 extracted data requested by user {current_user_id}: "
        f"download_id={download_id}"
    )

    try:
        # 1. Obtener el registro Form29SIIDownload
        stmt = select(Form29SIIDownload).where(
            Form29SIIDownload.id == download_id
        )
        result = await db.execute(stmt)
        download = result.scalar_one_or_none()

        if not download:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Form29SIIDownload {download_id} no encontrado"
            )

        # 2. Verificar que el usuario tenga acceso (verificar que pertenece a su company)
        # Obtener sesiones del usuario para esta company
        stmt_access = select(SessionModel).where(
            SessionModel.user_id == current_user_id,
            SessionModel.company_id == download.company_id
        )
        result_access = await db.execute(stmt_access)
        has_access = result_access.scalar_one_or_none() is not None

        # Verificar si es admin
        user_stmt = select(Profile).where(Profile.id == current_user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        is_admin = user and user.rol == "admin-kaiken"

        if not has_access and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este formulario"
            )

        # 3. Verificar si tiene PDF descargado
        if not download.pdf_storage_url:
            return {
                "success": False,
                "download_id": str(download_id),
                "folio": download.sii_folio,
                "has_pdf": False,
                "has_extracted_data": False,
                "message": "El PDF no ha sido descargado aún. Usa /download-single-pdf primero."
            }

        # 4. Verificar si tiene datos extraídos
        extracted_data = download.extra_data.get('f29_data') if download.extra_data else None

        if not extracted_data:
            return {
                "success": False,
                "download_id": str(download_id),
                "folio": download.sii_folio,
                "has_pdf": True,
                "has_extracted_data": False,
                "message": "El PDF fue descargado pero no se extrajeron datos. Intenta re-descargar el PDF."
            }

        # 5. Retornar datos extraídos
        logger.info(f"✅ Returning extracted data for folio {download.sii_folio}")

        return {
            "success": True,
            "download_id": str(download_id),
            "folio": download.sii_folio,
            "period": download.period_display,
            "has_pdf": True,
            "has_extracted_data": True,
            "pdf_url": download.pdf_storage_url,
            "extracted_data": extracted_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get extracted F29 data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener datos extraídos del F29: {str(e)}"
        )
