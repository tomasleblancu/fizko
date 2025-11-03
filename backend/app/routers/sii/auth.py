"""
Router para autenticación SII
Endpoints para login, logout y gestión de sesiones del SII
"""
import json
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from uuid import UUID

from ...config.database import get_db
from ...dependencies import get_current_user_id, require_auth, get_current_user
from ...services.sii.auth_service import SIIAuthService
from ...integrations.sii.exceptions import AuthenticationError, ExtractionError

router = APIRouter(
    prefix="/auth",
    tags=["SII Auth"],
    dependencies=[Depends(require_auth)]
)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class SIILoginRequest(BaseModel):
    """Request para login en el SII"""
    rut: str = Field(..., description="RUT del contribuyente (ej: 77794858-k)")
    password: str = Field(..., description="Contraseña del SII")

    class Config:
        json_schema_extra = {
            "example": {
                "rut": "77794858-k",
                "password": "SiiPfufl574@#"
            }
        }


class SIILoginResponse(BaseModel):
    """Response del login SII"""
    success: bool
    message: str
    company: dict
    company_tax_info: dict
    session: dict
    contribuyente_info: dict


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/login", response_model=SIILoginResponse)
async def sii_login_and_setup(
    request: SIILoginRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint completo de login SII y setup de compañía

    Flujo:
    1. Crea perfil de usuario si no existe (usando datos de OAuth)
    2. Autentica con el SII usando RUT y password
    3. Extrae información del contribuyente
    4. Busca o crea la compañía en la DB
    5. Busca o crea CompanyTaxInfo
    6. Obtiene o genera Session del usuario con esa compañía
    7. Guarda las cookies del SII en la session
    8. Dispara tareas de sincronización en background (documentos + F29)

    Args:
        request: RUT y password del SII
        current_user_id: ID del usuario autenticado (desde JWT)
        user: Datos completos del usuario desde JWT (email, metadata, etc.)
        db: Sesión de base de datos

    Returns:
        Información completa: company, tax_info, session, contribuyente_info

    Raises:
        HTTPException 401: Si las credenciales del SII son inválidas
        HTTPException 500: Si hay error en la extracción o DB

    Example:
        POST /api/sii/auth/login
        Headers: Authorization: Bearer <token>
        Body:
        {
            "rut": "77794858-k",
            "password": "SiiPfufl574@#"
        }

        Response:
        {
            "success": true,
            "message": "Login exitoso. Compañía creada, tax info creada, sesión creada.",
            "company": {...},
            "company_tax_info": {...},
            "session": {...},
            "contribuyente_info": {...}
        }
    """

    # Instanciar servicio de autenticación
    auth_service = SIIAuthService(db)

    try:
        # Delegar toda la lógica al servicio
        result = await auth_service.login_and_setup(
            rut=request.rut,
            password=request.password,
            user_id=current_user_id,
            user_data=user
        )

        return SIILoginResponse(**result)

    except AuthenticationError as e:
        # Error de autenticación con el SII
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error en la autenticación: {str(e)}"
        )

    except ExtractionError as e:
        # Error al extraer datos del SII
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener información del contribuyente: {str(e)}"
        )

    except Exception as e:
        # Rollback en caso de error
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado durante el login: {str(e)}"
        )


@router.post("/login/stream")
async def sii_login_and_setup_stream(
    request: SIILoginRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de login SII con streaming de progreso (Server-Sent Events)

    Envía eventos de progreso en tiempo real durante el proceso de autenticación
    y extracción de datos del SII.

    Formato de eventos SSE:
    - event: progress - Progreso del proceso (0-100)
    - event: status - Mensaje de estado actual
    - event: error - Error durante el proceso
    - event: complete - Proceso completado con datos finales

    Example response stream:
        event: progress
        data: {"progress": 10, "message": "Autenticando con el SII..."}

        event: progress
        data: {"progress": 30, "message": "Extrayendo información del contribuyente..."}

        event: complete
        data: {"success": true, "company": {...}, "session": {...}}
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Genera eventos SSE con el progreso del login"""
        try:
            # Helper para enviar eventos SSE
            def send_event(event_type: str, data: dict) -> str:
                return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

            # Paso 1: Iniciar autenticación
            yield send_event("progress", {
                "progress": 10,
                "message": "Iniciando autenticación con el SII..."
            })
            await asyncio.sleep(0.5)  # Delay visible

            # Instanciar servicio
            auth_service = SIIAuthService(db)

            # Paso 2: Autenticar
            yield send_event("progress", {
                "progress": 25,
                "message": "Conectando con el portal del SII..."
            })
            await asyncio.sleep(0.7)

            # Paso 3: Validando credenciales
            yield send_event("progress", {
                "progress": 40,
                "message": "Validando credenciales..."
            })
            await asyncio.sleep(0.5)

            # Ejecutar login (esto internamente hace varios pasos)
            # Por ahora llamamos al método completo, pero podríamos refactorizar
            # el servicio para que también emita eventos de progreso
            result = await auth_service.login_and_setup(
                rut=request.rut,
                password=request.password,
                user_id=current_user_id,
                user_data=user
            )

            # Paso 4: Datos extraídos
            yield send_event("progress", {
                "progress": 65,
                "message": "Extrayendo información del contribuyente..."
            })
            await asyncio.sleep(0.6)

            # Paso 5: Guardando en base de datos
            yield send_event("progress", {
                "progress": 85,
                "message": "Guardando información en la base de datos..."
            })
            await asyncio.sleep(0.5)

            # Paso 6: Completado
            yield send_event("progress", {
                "progress": 100,
                "message": "¡Proceso completado exitosamente!"
            })
            await asyncio.sleep(0.3)

            # Enviar resultado final
            yield send_event("complete", {
                "success": True,
                **result
            })

        except AuthenticationError as e:
            yield send_event("error", {
                "error": "authentication_error",
                "message": f"Error en la autenticación: {str(e)}"
            })

        except ExtractionError as e:
            yield send_event("error", {
                "error": "extraction_error",
                "message": f"Error al obtener información: {str(e)}"
            })

        except Exception as e:
            await db.rollback()
            yield send_event("error", {
                "error": "unexpected_error",
                "message": f"Error inesperado: {str(e)}"
            })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
