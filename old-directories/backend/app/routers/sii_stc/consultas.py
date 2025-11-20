"""
Router para consultas públicas STC del SII

Endpoints para consultar estado de proveedores y documentos tributarios
sin necesidad de autenticación.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict

from app.integrations.sii_stc import STCClient
from app.integrations.sii_stc.exceptions import (
    STCException,
    STCRecaptchaError,
    STCQueryError,
    STCTimeoutError
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/stc",
    tags=["SII STC (Public Queries)"]
)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class ConsultaDocumentoRequest(BaseModel):
    """Request para consultar documento tributario"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "rut": "77794858",
            "dv": "K"
        }
    })

    rut: str = Field(
        ...,
        description="RUT del proveedor (sin DV, sin puntos, solo números)",
        pattern=r"^\d+$"
    )
    dv: str = Field(
        ...,
        description="Dígito verificador",
        max_length=1
    )
    headless: bool = Field(
        default=True,
        description="Ejecutar navegador en modo headless"
    )
    recaptcha_timeout: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Timeout para esperar el token reCAPTCHA (segundos)"
    )
    query_timeout: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Timeout para la consulta (segundos)"
    )


class ConsultaDocumentoResponse(BaseModel):
    """Response de consulta de documento"""
    success: bool
    message: str
    data: Optional[dict] = None
    rut: str
    dv: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/consultar-documento", response_model=ConsultaDocumentoResponse)
async def consultar_documento(request: ConsultaDocumentoRequest):
    """
    Consulta el estado de un proveedor y sus documentos tributarios

    Este endpoint NO requiere autenticación. Es una consulta pública del SII.

    Flujo:
    1. Navega al portal STC del SII
    2. Captura cookies del navegador
    3. Intercepta el token reCAPTCHA (rresp)
    4. Realiza la consulta a la API del SII

    Args:
        request: RUT y DV del proveedor a consultar

    Returns:
        Información del proveedor y sus documentos tributarios

    Raises:
        HTTPException 408: Si timeout esperando reCAPTCHA o consulta
        HTTPException 422: Si falla la validación de reCAPTCHA
        HTTPException 500: Si error en la consulta

    Example:
        POST /api/sii-stc/consultar-documento
        Body:
        {
            "rut": "77794858",
            "dv": "K"
        }

        Response:
        {
            "success": true,
            "message": "Consulta exitosa",
            "data": {...},
            "rut": "77794858",
            "dv": "K"
        }
    """

    logger.info(f"📋 [STC] Consulta de documento para RUT: {request.rut}-{request.dv}")

    try:
        # Crear cliente STC
        with STCClient(headless=request.headless) as client:

            # Preparar cliente (navegar, capturar cookies y token)
            logger.info("🔧 [STC] Preparing client...")
            client.prepare(recaptcha_timeout=request.recaptcha_timeout)

            # Realizar consulta
            logger.info("🔍 [STC] Querying document...")
            result = client.consultar_documento(
                rut=request.rut,
                dv=request.dv,
                auto_prepare=False,  # Ya preparamos manualmente
                timeout=request.query_timeout
            )

            logger.info(f"✅ [STC] Query successful for RUT {request.rut}-{request.dv}")

            return ConsultaDocumentoResponse(
                success=True,
                message="Consulta exitosa",
                data=result,
                rut=request.rut,
                dv=request.dv
            )

    except STCTimeoutError as e:
        logger.error(f"⏰ [STC] Timeout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Timeout durante la consulta: {str(e)}"
        )

    except STCRecaptchaError as e:
        logger.error(f"🤖 [STC] reCAPTCHA error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error validando reCAPTCHA: {str(e)}"
        )

    except STCQueryError as e:
        logger.error(f"❌ [STC] Query error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la consulta: {str(e)}"
        )

    except STCException as e:
        logger.error(f"❌ [STC] STC error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el cliente STC: {str(e)}"
        )

    except Exception as e:
        logger.error(f"❌ [STC] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint para verificar que el servicio está disponible

    Returns:
        Status del servicio
    """
    return {
        "status": "ok",
        "service": "SII STC (Public Queries)",
        "message": "Service is running"
    }
