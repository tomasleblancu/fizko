"""
Módulo de setup de Company, CompanyTaxInfo y Session
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Company, CompanyTaxInfo, CompanySettings, Profile, Session as SessionModel

logger = logging.getLogger(__name__)


async def ensure_profile(
    db: AsyncSession,
    user_id: UUID,
    user_data: dict
) -> Profile:
    """
    Crea perfil de usuario si no existe

    Args:
        db: Sesión async de base de datos
        user_id: UUID del usuario
        user_data: Datos del usuario desde JWT (email, user_metadata, etc.)

    Returns:
        Profile: Perfil del usuario (existente o nuevo)
    """
    # Buscar perfil existente
    stmt = select(Profile).where(Profile.id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile:
        return profile

    # Extraer datos del JWT
    email = user_data.get("email", "")
    user_metadata = user_data.get("user_metadata", {})
    full_name = user_metadata.get("full_name", "")

    # Split full_name en name y lastname
    if full_name:
        parts = full_name.split(" ", 1)
        name = parts[0]
        lastname = parts[1] if len(parts) > 1 else ""
    else:
        name = ""
        lastname = ""

    # Extraer otros campos de OAuth metadata
    phone = user_metadata.get("phone")
    avatar_url = user_metadata.get("avatar_url") or user_metadata.get("picture")

    # Crear nuevo perfil
    profile = Profile(
        id=user_id,
        email=email,
        full_name=full_name,
        name=name,
        lastname=lastname,
        phone=phone,
        avatar_url=avatar_url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(profile)
    await db.flush()

    logger.info(f"[Setup] Created new profile for user {user_id}")
    return profile


async def setup_company(
    db: AsyncSession,
    rut: str,
    password: str,
    sii_data: Dict[str, Any]
) -> tuple[Company, str]:
    """
    Busca o crea Company en la base de datos

    Args:
        db: Sesión async de base de datos
        rut: RUT del contribuyente
        password: Contraseña del SII (será encriptada)
        sii_data: Datos extraídos del SII

    Returns:
        Tuple[Company, str]: (Company, action) donde action es "creada" o "actualizada"
    """
    contribuyente_info = sii_data['contribuyente_info']

    # Normalizar RUT para búsqueda (minúsculas, sin puntos ni guiones)
    rut_normalized = rut.replace(".", "").replace("-", "").lower()

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
            address=contribuyente_info.get('unidad_operativa_direccion', None),
            email=contribuyente_info.get('email', None),
        )
        company.sii_password = password  # Será encriptado automáticamente
        db.add(company)
        await db.flush()
        await db.refresh(company)

        return company, "creada"
    else:
        # Actualizar información de compañía existente
        company.business_name = contribuyente_info.get('razon_social', company.business_name)
        company.trade_name = contribuyente_info.get('nombre', company.trade_name)
        company.address = contribuyente_info.get('unidad_operativa_direccion', company.address)
        company.email = contribuyente_info.get('email', company.email)
        company.sii_password = password  # Actualizar password
        company.updated_at = datetime.utcnow()

        return company, "actualizada"


async def setup_tax_info(
    db: AsyncSession,
    company_id: UUID,
    sii_data: Dict[str, Any]
) -> tuple[CompanyTaxInfo, str]:
    """
    Busca o crea CompanyTaxInfo en la base de datos

    Args:
        db: Sesión async de base de datos
        company_id: UUID de la compañía
        sii_data: Datos extraídos del SII

    Returns:
        Tuple[CompanyTaxInfo, str]: (CompanyTaxInfo, action) donde action es "creada" o "actualizada"
    """
    contribuyente_info = sii_data['contribuyente_info']

    # Extraer la primera actividad económica (actividad principal)
    actividades = contribuyente_info.get('actividades', [])
    actividad_principal = actividades[0] if actividades else {}

    # Buscar tax info existente
    stmt = select(CompanyTaxInfo).where(CompanyTaxInfo.company_id == company_id)
    result = await db.execute(stmt)
    company_tax_info = result.scalar_one_or_none()

    if not company_tax_info:
        # Crear nuevo CompanyTaxInfo
        company_tax_info = CompanyTaxInfo(
            company_id=company_id,
            tax_regime='regimen_general',  # Default
            sii_activity_code=actividad_principal.get('codigo', None),
            sii_activity_name=actividad_principal.get('descripcion', None),
            legal_representative_name=None,  # El SII no provee representante legal
            extra_data={
                'sii_info': contribuyente_info,
                'last_sii_sync': datetime.utcnow().isoformat()
            }
        )
        db.add(company_tax_info)
        await db.flush()
        await db.refresh(company_tax_info)

        return company_tax_info, "creada"
    else:
        # Actualizar CompanyTaxInfo existente
        company_tax_info.sii_activity_code = actividad_principal.get(
            'codigo',
            company_tax_info.sii_activity_code
        )
        company_tax_info.sii_activity_name = actividad_principal.get(
            'descripcion',
            company_tax_info.sii_activity_name
        )

        # Actualizar extra_data con nueva info del SII
        extra_data = company_tax_info.extra_data or {}
        extra_data['sii_info'] = contribuyente_info
        extra_data['last_sii_sync'] = datetime.utcnow().isoformat()
        company_tax_info.extra_data = extra_data
        company_tax_info.updated_at = datetime.utcnow()

        return company_tax_info, "actualizada"


async def setup_session(
    db: AsyncSession,
    user_id: UUID,
    company_id: UUID,
    password: str,
    sii_cookies: list
) -> tuple[SessionModel, str]:
    """
    Busca o crea Session del usuario con esta compañía

    Args:
        db: Sesión async de base de datos
        user_id: UUID del usuario
        company_id: UUID de la compañía
        password: Contraseña del SII
        sii_cookies: Cookies de sesión del SII

    Returns:
        Tuple[SessionModel, str]: (Session, action) donde action es "creada" o "actualizada"
    """
    # Buscar sesión existente del usuario con esta compañía
    stmt = select(SessionModel).where(
        SessionModel.user_id == user_id,
        SessionModel.company_id == company_id
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        # Crear nueva sesión
        session = SessionModel(
            user_id=user_id,
            company_id=company_id,
            is_active=True,
            cookies={
                'sii_cookies': sii_cookies,
                'password': password,
                'last_updated': datetime.utcnow().isoformat()
            },
            resources={},
            last_accessed_at=datetime.utcnow()
        )
        db.add(session)
        await db.flush()
        await db.refresh(session)

        return session, "creada"
    else:
        # Actualizar cookies de sesión existente
        session.cookies = {
            'sii_cookies': sii_cookies,
            'password': password,
            'last_updated': datetime.utcnow().isoformat()
        }
        session.last_accessed_at = datetime.utcnow()
        session.is_active = True

        return session, "actualizada"


async def check_needs_initial_setup(db: AsyncSession, company_id: UUID) -> bool:
    """
    Verifica si la empresa necesita completar la configuración inicial.

    Args:
        db: Sesión async de base de datos
        company_id: UUID de la empresa

    Returns:
        bool: True si necesita setup inicial, False si ya está configurada
    """
    # Buscar settings de la empresa
    stmt = select(CompanySettings).where(CompanySettings.company_id == company_id)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()

    # Si no existe settings o no está completo el setup inicial
    if not settings or not settings.is_initial_setup_complete:
        return True

    return False
