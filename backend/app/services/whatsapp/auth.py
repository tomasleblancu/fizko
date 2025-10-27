"""
Servicio de autenticación por WhatsApp
Identifica usuarios por su número de teléfono
"""
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile

logger = logging.getLogger(__name__)


async def authenticate_user_by_whatsapp(
    db: AsyncSession,
    phone_number: str,
) -> Optional[UUID]:
    """
    Autentica un usuario por su número de WhatsApp.

    Args:
        db: Sesión de base de datos
        phone_number: Número de WhatsApp (ej: "56975389973")

    Returns:
        UUID del usuario si se encuentra, None si no existe

    Example:
        >>> user_id = await authenticate_user_by_whatsapp(db, "56975389973")
        >>> if user_id:
        >>>     print(f"Usuario autenticado: {user_id}")
    """
    try:
        # Asegurarse de que el número tenga el prefijo "+"
        normalized_phone = phone_number if phone_number.startswith("+") else f"+{phone_number}"

        logger.info(f"🔍 Buscando usuario con número: {normalized_phone}")

        # Buscar en la tabla profiles por el campo phone
        result = await db.execute(
            select(Profile).where(Profile.phone == normalized_phone)
        )
        profile = result.scalar_one_or_none()

        if profile:
            logger.info(f"✅ Usuario encontrado: {profile.id} ({profile.full_name or profile.email})")
            return profile.id
        else:
            logger.warning(f"⚠️ No se encontró usuario con el número: {normalized_phone}")
            return None

    except Exception as e:
        logger.error(f"❌ Error autenticando usuario por WhatsApp: {e}")
        return None


async def get_user_info_by_whatsapp(
    db: AsyncSession,
    phone_number: str,
) -> Optional[dict]:
    """
    Obtiene información completa del usuario por su número de WhatsApp.

    Args:
        db: Sesión de base de datos
        phone_number: Número de WhatsApp

    Returns:
        Diccionario con información del usuario o None
    """
    try:
        # Normalizar número
        normalized_phone = phone_number if phone_number.startswith("+") else f"+{phone_number}"

        # Buscar perfil
        result = await db.execute(
            select(Profile).where(Profile.phone == normalized_phone)
        )
        profile = result.scalar_one_or_none()

        if profile:
            return {
                "user_id": profile.id,
                "email": profile.email,
                "full_name": profile.full_name,
                "name": profile.name,
                "lastname": profile.lastname,
                "phone": profile.phone,
                "phone_verified": profile.phone_verified,
                "company_name": profile.company_name,
                "avatar_url": profile.avatar_url,
                "rol": profile.rol,
            }
        else:
            return None

    except Exception as e:
        logger.error(f"❌ Error obteniendo info de usuario: {e}")
        return None


async def update_phone_verification(
    db: AsyncSession,
    phone_number: str,
    verified: bool = True,
) -> bool:
    """
    Marca el teléfono de un usuario como verificado.
    Útil cuando el usuario envía un mensaje por WhatsApp (prueba de posesión).

    Args:
        db: Sesión de base de datos
        phone_number: Número de WhatsApp
        verified: Si el teléfono está verificado

    Returns:
        True si se actualizó, False si no
    """
    try:
        normalized_phone = phone_number if phone_number.startswith("+") else f"+{phone_number}"

        result = await db.execute(
            select(Profile).where(Profile.phone == normalized_phone)
        )
        profile = result.scalar_one_or_none()

        if profile:
            profile.phone_verified = verified
            if verified:
                from datetime import datetime
                profile.phone_verified_at = datetime.utcnow()

            await db.commit()
            logger.info(f"✅ Teléfono verificado para usuario: {profile.id}")
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"❌ Error actualizando verificación de teléfono: {e}")
        await db.rollback()
        return False
