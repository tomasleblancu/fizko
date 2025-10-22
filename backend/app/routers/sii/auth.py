"""
Router para autenticación SII
Endpoints para login, logout y gestión de sesiones del SII
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from ...config.database import get_db
from ...db.models import Company, CompanyTaxInfo, Session as SessionModel
from ...dependencies import get_current_user_id, require_auth

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
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint completo de login SII y setup de compañía

    Flujo:
    1. Autentica con el SII usando RUT y password
    2. Extrae información del contribuyente
    3. Busca o crea la compañía en la DB
    4. Busca o crea CompanyTaxInfo
    5. Obtiene o genera Session del usuario con esa compañía
    6. Guarda las cookies del SII en la session

    Args:
        request: RUT y password del SII
        current_user_id: ID del usuario autenticado (desde JWT)
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
            "message": "Login exitoso y sesión configurada",
            "company": {...},
            "company_tax_info": {...},
            "session": {...},
            "contribuyente_info": {...}
        }
    """

    # ========================================================================
    # PASO 1: Autenticar con el SII y extraer datos del contribuyente
    # ========================================================================

    # Lazy import to avoid loading selenium at server startup
    from ...integrations.sii import SIIClient
    from ...integrations.sii.exceptions import AuthenticationError, ExtractionError

    try:
        with SIIClient(
            tax_id=request.rut,
            password=request.password,
            headless=True
        ) as sii_client:

            # Intentar login
            login_success = sii_client.login()

            if not login_success:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Error en la autenticación. Credenciales incorrectas o SII no disponible."
                )

            # Extraer información del contribuyente
            try:
                contribuyente_info = sii_client.get_contribuyente()
            except ExtractionError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error al obtener información del contribuyente: {str(e)}"
                )

            # Obtener cookies para guardar en session
            sii_cookies = sii_client.get_cookies()

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error en la autenticación: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado durante el login: {str(e)}"
        )

    # ========================================================================
    # PASO 2: Buscar o crear Company en la DB
    # ========================================================================

    # Normalizar RUT para búsqueda (mayúsculas)
    rut_normalized = request.rut.upper()

    # Buscar compañía existente
    stmt = select(Company).where(Company.rut == rut_normalized)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        # Crear nueva compañía
        company = Company(
            rut=rut_normalized,
            business_name=contribuyente_info.get('razon_social', f'Empresa {rut_normalized}'),
            trade_name=contribuyente_info.get('nombre', None),
            address=contribuyente_info.get('direccion', None),
            email=contribuyente_info.get('email', None),
        )
        company.sii_password = request.password  # Asignar password del SII (será encriptado automáticamente)
        db.add(company)
        await db.flush()  # Flush para obtener el ID
        await db.refresh(company)

        action = "creada"
    else:
        # Actualizar información de compañía existente
        company.business_name = contribuyente_info.get('razon_social', company.business_name)
        company.trade_name = contribuyente_info.get('nombre', company.trade_name)
        company.address = contribuyente_info.get('direccion', company.address)
        company.email = contribuyente_info.get('email', company.email)
        company.sii_password = request.password  # Actualizar password del SII
        company.updated_at = datetime.utcnow()

        action = "actualizada"

    # ========================================================================
    # PASO 3: Buscar o crear CompanyTaxInfo
    # ========================================================================

    # Buscar tax info existente
    stmt = select(CompanyTaxInfo).where(CompanyTaxInfo.company_id == company.id)
    result = await db.execute(stmt)
    company_tax_info = result.scalar_one_or_none()

    if not company_tax_info:
        # Crear nuevo CompanyTaxInfo
        company_tax_info = CompanyTaxInfo(
            company_id=company.id,
            tax_regime='regimen_general',  # Default
            sii_activity_code=contribuyente_info.get('activity_code', None),
            sii_activity_name=contribuyente_info.get('activity_name', None),
            legal_representative_name=contribuyente_info.get('legal_representative', None),
            extra_data={
                'sii_info': contribuyente_info,
                'last_sii_sync': datetime.utcnow().isoformat()
            }
        )
        db.add(company_tax_info)
        await db.flush()
        await db.refresh(company_tax_info)

        tax_action = "creada"
    else:
        # Actualizar CompanyTaxInfo existente
        company_tax_info.sii_activity_code = contribuyente_info.get('activity_code', company_tax_info.sii_activity_code)
        company_tax_info.sii_activity_name = contribuyente_info.get('activity_name', company_tax_info.sii_activity_name)
        company_tax_info.legal_representative_name = contribuyente_info.get('legal_representative', company_tax_info.legal_representative_name)

        # Actualizar extra_data con nueva info del SII
        extra_data = company_tax_info.extra_data or {}
        extra_data['sii_info'] = contribuyente_info
        extra_data['last_sii_sync'] = datetime.utcnow().isoformat()
        company_tax_info.extra_data = extra_data
        company_tax_info.updated_at = datetime.utcnow()

        tax_action = "actualizada"

    # ========================================================================
    # PASO 4: Obtener o generar Session del usuario con esta compañía
    # ========================================================================

    # Buscar sesión existente del usuario con esta compañía
    stmt = select(SessionModel).where(
        SessionModel.user_id == current_user_id,
        SessionModel.company_id == company.id
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        # Crear nueva sesión
        session = SessionModel(
            user_id=current_user_id,
            company_id=company.id,
            is_active=True,
            cookies={
                'sii_cookies': sii_cookies,
                'password': request.password,  # Guardamos password encriptado en producción
                'last_updated': datetime.utcnow().isoformat()
            },
            resources={},
            last_accessed_at=datetime.utcnow()
        )
        db.add(session)
        await db.flush()
        await db.refresh(session)

        session_action = "creada"
    else:
        # Actualizar cookies de sesión existente
        session.cookies = {
            'sii_cookies': sii_cookies,
            'password': request.password,
            'last_updated': datetime.utcnow().isoformat()
        }
        session.last_accessed_at = datetime.utcnow()
        session.is_active = True

        session_action = "actualizada"

    # ========================================================================
    # PASO 5: Commit de todos los cambios
    # ========================================================================

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar en la base de datos: {str(e)}"
        )

    # Refresh para obtener datos actualizados
    await db.refresh(company)
    await db.refresh(company_tax_info)
    await db.refresh(session)

    # ========================================================================
    # PASO 6: Construir respuesta
    # ========================================================================

    return SIILoginResponse(
        success=True,
        message=f"Login exitoso. Compañía {action}, tax info {tax_action}, sesión {session_action}.",
        company={
            "id": str(company.id),
            "rut": company.rut,
            "business_name": company.business_name,
            "trade_name": company.trade_name,
            "address": company.address,
            "email": company.email,
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat()
        },
        company_tax_info={
            "id": str(company_tax_info.id),
            "company_id": str(company_tax_info.company_id),
            "tax_regime": company_tax_info.tax_regime,
            "sii_activity_code": company_tax_info.sii_activity_code,
            "sii_activity_name": company_tax_info.sii_activity_name,
            "legal_representative_name": company_tax_info.legal_representative_name,
            "created_at": company_tax_info.created_at.isoformat(),
            "updated_at": company_tax_info.updated_at.isoformat()
        },
        session={
            "id": str(session.id),
            "user_id": str(session.user_id),
            "company_id": str(session.company_id),
            "is_active": session.is_active,
            "has_cookies": bool(session.cookies and session.cookies.get('sii_cookies')),
            "last_accessed_at": session.last_accessed_at.isoformat() if session.last_accessed_at else None
        },
        contribuyente_info=contribuyente_info
    )
