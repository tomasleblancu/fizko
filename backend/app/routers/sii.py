"""
SII Integration Router - Simplified version without auth or database.
Provides direct access to SII scraping and extraction services.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import date

from app.integrations.sii.client import SIIClient
from app.integrations.sii.exceptions import (
    AuthenticationError,
    ExtractionError,
    ScrapingException
)
from app.utils.encryption import encrypt_password

router = APIRouter()


# Request/Response Models
class LoginRequest(BaseModel):
    """Request model for SII login."""
    rut: str = Field(..., description="RUT sin puntos ni guión (ej: 12345678)")
    dv: str = Field(..., description="Dígito verificador (ej: K)")
    password: str = Field(..., description="Contraseña del SII")
    cookies: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Cookies de sesión existentes (opcional). Si se proveen, se intentará reutilizar la sesión."
    )


class LoginResponse(BaseModel):
    """Response model for SII login."""
    success: bool
    message: str
    session_active: bool
    cookies: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Cookies de sesión actuales para reutilizar en futuros requests"
    )
    contribuyente_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Información completa del contribuyente extraída del SII"
    )
    encrypted_password: Optional[str] = Field(
        None,
        description="Contraseña SII encriptada con Fernet para almacenamiento seguro"
    )


class DTERequest(BaseModel):
    """Request model for DTE extraction."""
    rut: str = Field(..., description="RUT sin puntos ni guión")
    dv: str = Field(..., description="Dígito verificador")
    password: str = Field(..., description="Contraseña del SII")
    periodo: str = Field(..., description="Periodo YYYYMM (ej: 202501)")
    cookies: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Cookies de sesión existentes (opcional). Evita login si la sesión es válida."
    )


class F29Request(BaseModel):
    """Request model for F29 extraction."""
    rut: str = Field(..., description="RUT sin puntos ni guión")
    dv: str = Field(..., description="Dígito verificador")
    password: str = Field(..., description="Contraseña del SII")
    periodo: str = Field(..., description="Periodo YYYYMM (ej: 202501)")
    cookies: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Cookies de sesión existentes (opcional). Evita login si la sesión es válida."
    )


class BoletasRequest(BaseModel):
    """Request model for Boletas Honorarios extraction."""
    rut: str = Field(..., description="RUT sin puntos ni guión")
    dv: str = Field(..., description="Dígito verificador")
    password: str = Field(..., description="Contraseña del SII")
    periodo: str = Field(..., description="Periodo YYYYMM (ej: 202501)")
    cookies: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Cookies de sesión existentes (opcional). Evita login si la sesión es válida."
    )


class ContribuyenteRequest(BaseModel):
    """Request model for contributor info extraction."""
    rut: str = Field(..., description="RUT sin puntos ni guión")
    dv: str = Field(..., description="Dígito verificador")
    password: str = Field(..., description="Contraseña del SII")
    cookies: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Cookies de sesión existentes (opcional). Evita login si la sesión es válida."
    )


# Endpoints
@router.post("/login", response_model=LoginResponse)
async def login_to_sii(request: LoginRequest):
    """
    Complete SII login with full data extraction.

    This endpoint performs:
    1. Authentication with SII portal (reusing cookies if provided)
    2. Extraction of complete contributor information including:
       - Basic info (RUT, razón social, dirección, email, teléfono)
       - Economic activities (actividades económicas)
       - Tax regime and segment
       - Legal representatives (representantes legales)
       - Partners/shareholders (socios)
       - Authorized documents (timbrajes)
       - Tax compliance status (cumplimiento tributario)
       - SII observations and alerts

    Returns updated session cookies for future requests.
    """
    try:
        # Construir tax_id en formato RUT-DV
        tax_id = f"{request.rut}-{request.dv}"

        with SIIClient(
            tax_id=tax_id,
            password=request.password,
            headless=True,
            cookies=request.cookies
        ) as client:
            # Login (usa cookies si están disponibles)
            success = client.login()

            # Extraer información completa del contribuyente
            # Este método llama internamente al API del SII con las cookies
            # y extrae TODA la información disponible
            contribuyente_info = client.get_contribuyente()

            # Obtener cookies actuales para reutilización
            # Estas cookies ya fueron actualizadas/validadas durante get_contribuyente()
            current_cookies = client.get_cookies()

            # Encriptar contraseña para almacenamiento seguro
            encrypted_pwd = encrypt_password(request.password)

            return LoginResponse(
                success=success,
                message="Login exitoso y datos extraídos" if success else "Login fallido",
                session_active=success,
                cookies=current_cookies,
                contribuyente_info=contribuyente_info,
                encrypted_password=encrypted_pwd
            )
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"Error de autenticación: {str(e)}")
    except ExtractionError as e:
        raise HTTPException(status_code=422, detail=f"Error al extraer información del contribuyente: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@router.post("/compras")
async def get_compras(request: DTERequest):
    """
    Extract purchase documents (compras) from SII for a given period.

    Returns a list of DTEs (Documentos Tributarios Electrónicos) for purchases.
    If cookies are provided, it will attempt to reuse the session without logging in again.
    """
    try:
        tax_id = f"{request.rut}-{request.dv}"

        with SIIClient(
            tax_id=tax_id,
            password=request.password,
            headless=True,
            cookies=request.cookies
        ) as client:
            client.login()
            compras = client.get_compras(periodo=request.periodo)

            # Retornar cookies actuales para próximos requests
            current_cookies = client.get_cookies()

            return {
                "success": True,
                "periodo": request.periodo,
                "tipo": "compras",
                "total_documentos": len(compras),
                "documentos": compras,
                "cookies": current_cookies
            }
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"Error de autenticación: {str(e)}")
    except (ScrapingException, ExtractionError) as e:
        raise HTTPException(status_code=422, detail=f"Error al extraer datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@router.post("/ventas")
async def get_ventas(request: DTERequest):
    """
    Extract sales documents (ventas) from SII for a given period.

    Returns a list of DTEs (Documentos Tributarios Electrónicos) for sales.
    If cookies are provided, it will attempt to reuse the session without logging in again.
    """
    try:
        tax_id = f"{request.rut}-{request.dv}"

        with SIIClient(
            tax_id=tax_id,
            password=request.password,
            headless=True,
            cookies=request.cookies
        ) as client:
            client.login()
            ventas = client.get_ventas(periodo=request.periodo)

            # Retornar cookies actuales para próximos requests
            current_cookies = client.get_cookies()

            return {
                "success": True,
                "periodo": request.periodo,
                "tipo": "ventas",
                "total_documentos": len(ventas),
                "documentos": ventas,
                "cookies": current_cookies
            }
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"Error de autenticación: {str(e)}")
    except (ScrapingException, ExtractionError) as e:
        raise HTTPException(status_code=422, detail=f"Error al extraer datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@router.post("/f29")
async def get_f29_propuesta(request: F29Request):
    """
    Extract F29 proposal data from SII for a given period.

    Returns the complete F29 proposal with pre-filled values calculated by SII.
    If cookies are provided, it will attempt to reuse the session without logging in again.
    """
    try:
        tax_id = f"{request.rut}-{request.dv}"

        with SIIClient(
            tax_id=tax_id,
            password=request.password,
            headless=True,
            cookies=request.cookies
        ) as client:
            client.login()
            f29_data = client.get_propuesta_f29(periodo=request.periodo)

            # Retornar cookies actuales para próximos requests
            current_cookies = client.get_cookies()

            return {
                "success": True,
                "periodo": request.periodo,
                "tipo": "f29_propuesta",
                "data": f29_data,
                "cookies": current_cookies
            }
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"Error de autenticación: {str(e)}")
    except (ScrapingException, ExtractionError) as e:
        raise HTTPException(status_code=422, detail=f"Error al extraer datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@router.post("/boletas-honorarios")
async def get_boletas_honorarios(request: BoletasRequest):
    """
    Extract Boletas de Honorarios (receipts) from SII for a given period.

    Returns a list of professional service receipts.
    If cookies are provided, it will attempt to reuse the session without logging in again.
    """
    try:
        tax_id = f"{request.rut}-{request.dv}"

        # Convertir periodo YYYYMM a mes y año
        anio = request.periodo[:4]
        mes = request.periodo[4:6]

        with SIIClient(
            tax_id=tax_id,
            password=request.password,
            headless=True,
            cookies=request.cookies
        ) as client:
            client.login()
            result = client.get_boletas_honorarios(mes=mes, anio=anio)

            # Retornar cookies actuales para próximos requests
            current_cookies = client.get_cookies()

            return {
                "success": True,
                "periodo": request.periodo,
                "tipo": "boletas_honorarios",
                "total_boletas": result.get("totales", {}).get("total_registros", 0),
                "data": result,
                "cookies": current_cookies
            }
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"Error de autenticación: {str(e)}")
    except (ScrapingException, ExtractionError) as e:
        raise HTTPException(status_code=422, detail=f"Error al extraer datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@router.post("/contribuyente")
async def get_contribuyente_info(request: ContribuyenteRequest):
    """
    Extract contributor information from SII.

    Returns basic information about the taxpayer from SII records.
    If cookies are provided, it will attempt to reuse the session without logging in again.
    """
    try:
        tax_id = f"{request.rut}-{request.dv}"

        with SIIClient(
            tax_id=tax_id,
            password=request.password,
            headless=True,
            cookies=request.cookies
        ) as client:
            client.login()
            info = client.get_contribuyente()

            # Retornar cookies actuales para próximos requests
            current_cookies = client.get_cookies()

            return {
                "success": True,
                "tipo": "contribuyente",
                "data": info,
                "cookies": current_cookies
            }
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=f"Error de autenticación: {str(e)}")
    except (ScrapingException, ExtractionError) as e:
        raise HTTPException(status_code=422, detail=f"Error al extraer datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for SII router."""
    return {
        "status": "healthy",
        "service": "sii-integration",
        "version": "2.0.0"
    }
