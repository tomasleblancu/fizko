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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene lista de formularios F29 para un año

    Args:
        anio: Año (ej: "2024")
        session_id: ID de la sesión
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de formularios F29

    Example:
        GET /api/sii/f29/2024?session_id=123
        Response:
        {
            "success": true,
            "data": [
                {
                    "folio": "123456",
                    "period": "01-2024",
                    "contributor": "COMERCIAL ATAL SPA",
                    "submission_date": "15/02/2024",
                    "status": "Vigente",
                    "amount": 50000
                }
            ],
            "total_forms": 12
        }
    """
    try:
        service = SIIService(db)
        formularios = await service.extract_f29_lista(
            session_id=session_id,
            anio=anio
        )

        return {
            "success": True,
            "data": formularios,
            "total_forms": len(formularios),
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting F29: {str(e)}")


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
