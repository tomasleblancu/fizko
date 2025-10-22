"""
Ejemplo de Router para integración SII
Este archivo muestra cómo usar el SIIService desde los endpoints de FastAPI
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.services.sii import SIIService
from app.database import get_db
from app.config.database import AsyncSessionLocal
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/sii", tags=["SII Integration"])


# ============================================================================
# Endpoints de Extracción de Datos
# ============================================================================

@router.get("/contribuyente")
async def get_contribuyente_info(
    session_id: int,
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene información del contribuyente desde el SII

    Args:
        session_id: ID de la sesión en la DB
        force_refresh: Si True, ignora cookies y hace login fresco
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Información del contribuyente (RUT, razón social, email, etc.)

    Example:
        GET /api/sii/contribuyente?session_id=123
        Response:
        {
            "rut": "77794858-K",
            "razon_social": "COMERCIAL ATAL SPA",
            "nombre": "COMERCIAL ATAL",
            "email": "contacto@atal.cl",
            "direccion": "Av. Principal 123",
            "comuna": "Santiago"
        }
    """
    try:
        # Verificar que la sesión pertenece al usuario
        # TODO: Implementar verificación de permisos

        service = SIIService(db)
        info = await service.extract_contribuyente(
            session_id=session_id,
            force_new_login=force_refresh
        )

        return {
            "success": True,
            "data": info,
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting data: {str(e)}")


@router.get("/compras/{periodo}")
async def get_compras_periodo(
    periodo: str,
    session_id: int,
    tipo_doc: str = "33",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene DTEs de compra para un período específico

    Args:
        periodo: Período en formato YYYYMM (ej: "202510")
        session_id: ID de la sesión
        tipo_doc: Tipo de documento (default: "33" = Factura Electrónica)
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de documentos de compra

    Example:
        GET /api/sii/compras/202510?session_id=123&tipo_doc=33
        Response:
        {
            "success": true,
            "status": "success",
            "data": [
                {
                    "detNroDoc": 12217,
                    "detRznSoc": "PROVEEDOR LTDA",
                    "detMntTotal": 419990,
                    "detFchDoc": "08/10/2025"
                }
            ],
            "extraction_method": "api",
            "total_documents": 5
        }
    """
    try:
        service = SIIService(db)
        result = await service.extract_compras(
            session_id=session_id,
            periodo=periodo,
            tipo_doc=tipo_doc
        )

        return {
            "success": True,
            **result,
            "total_documents": len(result.get("data", [])),
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting purchases: {str(e)}")


@router.get("/ventas/{periodo}")
async def get_ventas_periodo(
    periodo: str,
    session_id: int,
    tipo_doc: str = "33",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene DTEs de venta para un período específico

    Args:
        periodo: Período en formato YYYYMM
        session_id: ID de la sesión
        tipo_doc: Tipo de documento
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de documentos de venta
    """
    try:
        service = SIIService(db)
        result = await service.extract_ventas(
            session_id=session_id,
            periodo=periodo,
            tipo_doc=tipo_doc
        )

        return {
            "success": True,
            **result,
            "total_documents": len(result.get("data", [])),
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting sales: {str(e)}")


@router.get("/f29/{anio}")
async def get_f29_lista(
    anio: str,
    session_id: int,
    save_to_db: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene lista de formularios F29 para un año y opcionalmente los guarda en DB

    Args:
        anio: Año (ej: "2024")
        session_id: ID de la sesión
        save_to_db: Si True, guarda los formularios en la DB (default: True)
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de formularios F29

    Example:
        GET /api/sii/f29/2024?session_id=123&save_to_db=true
        Response:
        {
            "success": true,
            "data": [
                {
                    "folio": "123456",
                    "period": "2024-01",
                    "contributor": "77794858-K",
                    "submission_date": "15/02/2024",
                    "status": "Vigente",
                    "amount": 50000,
                    "id_interno_sii": "775148628"
                }
            ],
            "total_forms": 12,
            "saved_to_db": true,
            "saved_count": 12
        }
    """
    try:
        from sqlalchemy import select
        from app.db.models import Session as SessionModel

        service = SIIService(db)

        # Extraer formularios del SII
        formularios = await service.extract_f29_lista(
            session_id=session_id,
            anio=anio
        )

        saved_count = 0
        if save_to_db and formularios:
            # Obtener company_id de la sesión
            stmt = select(SessionModel).where(SessionModel.id == session_id)
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()

            if session:
                # Guardar en la base de datos
                saved_downloads = await service.save_f29_downloads(
                    company_id=str(session.company_id),
                    formularios=formularios
                )
                saved_count = len(saved_downloads)

        return {
            "success": True,
            "data": formularios,
            "total_forms": len(formularios),
            "saved_to_db": save_to_db,
            "saved_count": saved_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting F29: {str(e)}")


@router.post("/f29/sync/{year}")
async def sync_f29_for_year(
    year: int,
    session_id: int,
    download_pdfs: bool = True,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sincronización completa de F29: Extrae lista del SII y opcionalmente descarga PDFs

    Args:
        year: Año a sincronizar (ej: 2024)
        session_id: ID de la sesión
        download_pdfs: Si True, descarga PDFs en background (default: True)
        background_tasks: Background tasks de FastAPI
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Resultado de la sincronización

    Example:
        POST /api/sii/f29/sync/2024?session_id=123&download_pdfs=true
        Response:
        {
            "success": true,
            "forms_synced": 12,
            "pdfs_pending": 9,
            "message": "F29 sync completed. PDF downloads initiated in background."
        }
    """
    try:
        from sqlalchemy import select
        from app.db.models import Session as SessionModel

        service = SIIService(db)

        # 1. Extraer formularios del SII
        formularios = await service.extract_f29_lista(
            session_id=session_id,
            anio=str(year)
        )

        if not formularios:
            return {
                "success": True,
                "forms_synced": 0,
                "pdfs_pending": 0,
                "message": f"No F29 forms found for year {year}"
            }

        # 2. Obtener company_id de la sesión
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 3. Guardar en la base de datos
        saved_downloads = await service.save_f29_downloads(
            company_id=str(session.company_id),
            formularios=formularios
        )

        # 4. Iniciar descargas de PDFs en background si se solicita
        pdfs_pending = 0
        if download_pdfs:
            from app.db.models import Form29SIIDownload

            # Buscar F29 pendientes con id_interno_sii
            stmt = select(Form29SIIDownload).where(
                Form29SIIDownload.company_id == session.company_id,
                Form29SIIDownload.period_year == year,
                Form29SIIDownload.pdf_download_status == "pending",
                Form29SIIDownload.sii_id_interno.isnot(None)
            )

            result = await db.execute(stmt)
            pending_downloads = result.scalars().all()
            pdfs_pending = len(pending_downloads)

            # Agregar task en background para cada PDF
            async def download_pdf_task(download_id: str):
                from app.config.database import AsyncSessionLocal
                async with AsyncSessionLocal() as task_db:
                    task_service = SIIService(task_db)
                    result = await task_service.download_and_save_f29_pdf(
                        download_id=str(download_id),
                        session_id=session_id
                    )
                    logger.info(f"Background PDF download: {result}")

            # Agregar todas las descargas al background
            for download in pending_downloads:
                if background_tasks:
                    background_tasks.add_task(download_pdf_task, download.id)

        return {
            "success": True,
            "forms_synced": len(saved_downloads),
            "pdfs_pending": pdfs_pending,
            "message": f"F29 sync completed. {pdfs_pending} PDF downloads initiated in background." if download_pdfs else "F29 sync completed without PDF downloads.",
            "year": year,
            "company_id": str(session.company_id)
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error syncing F29: {str(e)}")


# ============================================================================
# Endpoints de Descarga de PDFs de F29
# ============================================================================

@router.post("/f29/download-pdf/{download_id}")
async def download_f29_pdf(
    download_id: str,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Descarga el PDF de un F29 y lo guarda en Supabase Storage

    Args:
        download_id: UUID del registro Form29SIIDownload
        session_id: ID de la sesión
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Resultado de la descarga con URL del PDF

    Example:
        POST /api/sii/f29/download-pdf/550e8400-e29b-41d4-a716-446655440000?session_id=123
        Response:
        {
            "success": true,
            "url": "https://...storage.supabase.co/...",
            "size_mb": 0.15,
            "validation_msg": "PDF appears to be a valid F29"
        }
    """
    try:
        service = SIIService(db)

        result = await service.download_and_save_f29_pdf(
            download_id=download_id,
            session_id=session_id
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to download PDF")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")


@router.post("/f29/download-pdfs-batch")
async def download_f29_pdfs_batch(
    session_id: int,
    year: int,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Descarga PDFs de todos los F29 de un año en batch (background task)

    Args:
        session_id: ID de la sesión
        year: Año de los formularios
        background_tasks: Background tasks de FastAPI
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Información sobre el proceso iniciado

    Example:
        POST /api/sii/f29/download-pdfs-batch?session_id=123&year=2024
        Response:
        {
            "success": true,
            "message": "Batch download initiated for 12 PDFs",
            "total_pending": 12,
            "year": 2024
        }
    """
    try:
        from sqlalchemy import select
        from app.db.models import Session as SessionModel, Form29SIIDownload

        # Obtener company_id de la sesión
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Buscar F29 pendientes de descarga
        stmt = select(Form29SIIDownload).where(
            Form29SIIDownload.company_id == session.company_id,
            Form29SIIDownload.period_year == year,
            Form29SIIDownload.pdf_download_status == "pending",
            Form29SIIDownload.sii_id_interno.isnot(None)  # Solo los que tienen ID
        )

        result = await db.execute(stmt)
        pending_downloads = result.scalars().all()

        if not pending_downloads:
            return {
                "success": True,
                "message": "No pending PDFs to download",
                "total_pending": 0,
                "year": year
            }

        # Agregar task en background para cada PDF
        async def download_pdf_task(download_id: str):
            async with AsyncSessionLocal() as task_db:
                service = SIIService(task_db)
                result = await service.download_and_save_f29_pdf(
                    download_id=str(download_id),
                    session_id=session_id
                )
                logger.info(f"Background PDF download: {result}")

        # Agregar todas las descargas al background
        for download in pending_downloads:
            if background_tasks:
                background_tasks.add_task(download_pdf_task, download.id)

        return {
            "success": True,
            "message": f"Batch download initiated for {len(pending_downloads)} PDFs",
            "total_pending": len(pending_downloads),
            "year": year
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating batch download: {str(e)}")


@router.get("/f29/download-status/{company_id}")
async def get_f29_download_status(
    company_id: str,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el estado de descarga de PDFs de F29

    Args:
        company_id: UUID de la compañía
        year: Año opcional para filtrar
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Estadísticas de descarga

    Example:
        GET /api/sii/f29/download-status/550e8400-e29b-41d4-a716-446655440000?year=2024
        Response:
        {
            "success": true,
            "total": 12,
            "downloaded": 9,
            "pending": 0,
            "error": 3,
            "downloads": [...]
        }
    """
    try:
        from uuid import UUID
        from app.db.models import Form29SIIDownload

        # Construir query
        stmt = select(Form29SIIDownload).where(
            Form29SIIDownload.company_id == UUID(company_id)
        )

        if year:
            stmt = stmt.where(Form29SIIDownload.period_year == year)

        stmt = stmt.order_by(
            Form29SIIDownload.period_year,
            Form29SIIDownload.period_month
        )

        result = await db.execute(stmt)
        downloads = result.scalars().all()

        # Calcular estadísticas
        total = len(downloads)
        downloaded = sum(1 for d in downloads if d.pdf_download_status == "downloaded")
        pending = sum(1 for d in downloads if d.pdf_download_status == "pending")
        error = sum(1 for d in downloads if d.pdf_download_status == "error")

        # Serializar downloads
        downloads_data = []
        for d in downloads:
            downloads_data.append({
                "id": str(d.id),
                "folio": d.sii_folio,
                "period": d.period_display,
                "status": d.pdf_download_status,
                "has_id_interno": d.sii_id_interno is not None,
                "pdf_url": d.pdf_storage_url,
                "error": d.pdf_download_error,
                "downloaded_at": d.pdf_downloaded_at.isoformat() if d.pdf_downloaded_at else None
            })

        return {
            "success": True,
            "total": total,
            "downloaded": downloaded,
            "pending": pending,
            "error": error,
            "downloads": downloads_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting download status: {str(e)}")


# ============================================================================
# Endpoint de Sincronización Completa
# ============================================================================

@router.post("/sync")
async def sync_all_sii_data(
    session_id: int,
    periodo: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sincroniza todos los datos del SII en background

    Args:
        session_id: ID de la sesión
        periodo: Período a sincronizar (default: mes actual)
        background_tasks: Background tasks de FastAPI
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Status de la sincronización

    Example:
        POST /api/sii/sync
        Body: {"session_id": 123, "periodo": "202510"}
        Response:
        {
            "success": true,
            "status": "syncing",
            "session_id": 123,
            "tasks": ["contribuyente", "compras", "ventas", "f29"]
        }
    """
    if not periodo:
        periodo = datetime.now().strftime("%Y%m")

    async def sync_task():
        """Tarea de sincronización en background"""
        service = SIIService(db)

        try:
            # 1. Contribuyente
            await service.extract_contribuyente(session_id)

            # 2. Compras
            await service.extract_compras(session_id, periodo)

            # 3. Ventas
            await service.extract_ventas(session_id, periodo)

            # 4. F29 del año actual
            anio = str(datetime.now().year)
            await service.extract_f29_lista(session_id, anio)

            # TODO: Actualizar estado de sync en DB

        except Exception as e:
            # TODO: Log error y actualizar estado en DB
            print(f"Error in sync task: {e}")

    if background_tasks:
        background_tasks.add_task(sync_task)

    return {
        "success": True,
        "status": "syncing",
        "session_id": session_id,
        "periodo": periodo,
        "tasks": ["contribuyente", "compras", "ventas", "f29"],
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Endpoint de Health Check / Status
# ============================================================================

@router.get("/status/{session_id}")
async def get_session_status(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el estado de la sesión SII (cookies, última sincronización, etc.)

    Args:
        session_id: ID de la sesión
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Estado de la sesión

    Example:
        GET /api/sii/status/123
        Response:
        {
            "success": true,
            "session_id": 123,
            "has_cookies": true,
            "last_sync": "2025-10-21T14:30:00Z",
            "cookies_valid": true
        }
    """
    try:
        service = SIIService(db)
        creds = await service.get_stored_credentials(session_id)

        if not creds:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "success": True,
            "session_id": session_id,
            "has_cookies": bool(creds.get("cookies")),
            "company_rut": creds.get("rut"),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking status: {str(e)}")
