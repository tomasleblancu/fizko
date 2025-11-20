"""
Router para verificación de credenciales SII

Endpoint simplificado para verificar credenciales y extraer información
completa del contribuyente, sin interacción con base de datos.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.integrations.sii.client import SIIClient
from app.integrations.sii.exceptions import (
    AuthenticationError,
    ExtractionError,
    ScrapingException
)

router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================

class VerifyCredentialsRequest(BaseModel):
    """Request para verificar credenciales SII"""
    rut: str = Field(..., description="RUT sin puntos ni guión")
    dv: str = Field(..., description="Dígito verificador")
    password: str = Field(..., description="Contraseña del SII")
    cookies: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Cookies de sesión existentes (opcional)"
    )


class VerifyCredentialsResponse(BaseModel):
    """Response completa de verificación de credenciales"""
    success: bool = Field(..., description="Indica si la verificación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo del resultado")

    # Información del contribuyente
    contribuyente_info: Dict[str, Any] = Field(
        ...,
        description="Información completa del contribuyente extraída del SII"
    )

    # Cookies de sesión
    cookies: List[Dict[str, Any]] = Field(
        ...,
        description="Cookies de sesión actualizadas para reutilización"
    )

    # Metadatos del proceso
    session_refreshed: bool = Field(
        ...,
        description="True si se hizo login nuevo, False si se reutilizó sesión"
    )
    extraction_method: str = Field(
        ...,
        description="Método usado para extraer datos (scraping, api, etc.)"
    )
    timestamp: str = Field(..., description="Timestamp de la extracción")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/verify", response_model=VerifyCredentialsResponse)
async def verify_credentials(request: VerifyCredentialsRequest):
    """
    Verifica credenciales del SII y extrae toda la información del contribuyente

    Este endpoint:
    1. Autentica con el SII (o reutiliza sesión si hay cookies)
    2. Extrae TODA la información disponible del contribuyente
    3. Retorna datos completos sin guardar nada en base de datos

    Información extraída incluye:
    - Datos básicos (RUT, razón social, nombre fantasía)
    - Actividades económicas completas
    - Dirección comercial
    - Contacto (email, teléfono)
    - Régimen tributario
    - Estado del contribuyente
    - Fechas importantes (inicio actividades, etc.)
    - Representantes legales (si aplica)
    - Sucursales (si aplica)
    - Y cualquier otra información disponible en el perfil SII

    Args:
        request: RUT, DV, password y cookies opcionales

    Returns:
        Información completa del contribuyente + cookies actualizadas

    Raises:
        HTTPException 401: Credenciales inválidas
        HTTPException 422: Error en extracción de datos
        HTTPException 500: Error inesperado

    Ejemplo:
        POST /api/sii/verify
        {
            "rut": "77794858",
            "dv": "K",
            "password": "SiiPfufl574@#",
            "cookies": []  // opcional
        }

        Response:
        {
            "success": true,
            "message": "Credenciales verificadas exitosamente",
            "contribuyente_info": {
                "rut": "77794858-K",
                "razon_social": "MI EMPRESA SPA",
                "nombre_fantasia": "Mi Empresa",
                "actividades_economicas": [...],
                "direccion": {...},
                "contacto": {...},
                "regimen_tributario": {...},
                "representantes_legales": [...],
                "sucursales": [...],
                // ... más campos
            },
            "cookies": [...],
            "session_refreshed": false,
            "extraction_method": "scraping",
            "timestamp": "2025-11-19T01:30:00.123456"
        }
    """
    try:
        # Construir tax_id en formato RUT-DV
        tax_id = f"{request.rut}-{request.dv}"

        # Ejecutar autenticación y extracción usando SIIClient
        result = await _authenticate_and_extract_contribuyente(
            tax_id=tax_id,
            password=request.password,
            cookies=request.cookies
        )

        # Construir response
        return VerifyCredentialsResponse(
            success=True,
            message="Credenciales verificadas exitosamente" if not result["session_refreshed"]
                    else "Credenciales verificadas (nueva sesión iniciada)",
            contribuyente_info=result["contribuyente_info"],
            cookies=result["cookies"],
            session_refreshed=result["session_refreshed"],
            extraction_method=result.get("extraction_method", "scraping"),
            timestamp=result.get("timestamp", "")
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Error de autenticación: {str(e)}"
        )

    except ExtractionError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error al extraer información del contribuyente: {str(e)}"
        )

    except ScrapingException as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error durante scraping del SII: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================

async def _authenticate_and_extract_contribuyente(
    tax_id: str,
    password: str,
    cookies: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Autentica con el SII y extrae información completa del contribuyente

    Args:
        tax_id: RUT en formato XX-X
        password: Contraseña del SII
        cookies: Cookies de sesión existentes (opcional)

    Returns:
        Dict con:
        {
            "contribuyente_info": dict,  # Info completa del contribuyente
            "cookies": list,  # Cookies actualizadas
            "session_refreshed": bool,  # True si se hizo login nuevo
            "extraction_method": str,  # Método de extracción
            "timestamp": str  # Timestamp de extracción
        }
    """
    import asyncio
    from datetime import datetime

    def _execute_sync():
        """Ejecuta la operación síncrona dentro del contexto de SIIClient"""
        with SIIClient(
            tax_id=tax_id,
            password=password,
            headless=True,
            cookies=cookies
        ) as sii_client:

            session_refreshed = False

            # Si hay cookies, verificar sesión
            if cookies:
                try:
                    verification_result = sii_client.verify_session()
                    session_refreshed = verification_result.get('refreshed', False)
                except Exception:
                    # Si falla la verificación, hacer login completo
                    sii_client.login(force_new=True)
                    session_refreshed = True
            else:
                # Sin cookies, hacer login completo
                sii_client.login()
                session_refreshed = True

            # Extraer información completa del contribuyente
            # Esto incluye TODOS los datos disponibles en el perfil SII
            contribuyente_info = sii_client.get_contribuyente()

            # Obtener cookies actualizadas
            updated_cookies = sii_client.get_cookies()

            return {
                "contribuyente_info": contribuyente_info,
                "cookies": updated_cookies,
                "session_refreshed": session_refreshed,
                "extraction_method": "scraping",
                "timestamp": datetime.utcnow().isoformat()
            }

    # Ejecutar en thread separado para no bloquear el event loop
    result = await asyncio.to_thread(_execute_sync)
    return result
