"""
Router para autenticación con WhatsApp OTP
Usa la infraestructura existente de Kapso y templates
"""
from __future__ import annotations

import logging
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.core.auth import get_jwt_secret
from app.db.models import Profile
from app.services.whatsapp import WhatsAppService
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/whatsapp", tags=["auth"])

# Cache en memoria para OTPs (temporal - en producción usar Redis)
# Estructura: {phone: {"otp": "123456", "expires": datetime, "attempts": 0}}
_otp_cache: dict[str, dict] = {}


class RequestOTPSchema(BaseModel):
    phone: str  # Formato: +56912345678


class VerifyOTPSchema(BaseModel):
    phone: str
    otp: str


def _normalize_phone(phone: str) -> str:
    """Normaliza el número de teléfono al formato +56912345678"""
    phone = phone.strip()
    if not phone.startswith("+"):
        phone = f"+{phone}"
    return phone


def _generate_otp() -> str:
    """Genera un código OTP de 6 dígitos"""
    return "".join([str(secrets.randbelow(10)) for _ in range(6)])


def _is_otp_valid(phone: str, otp: str) -> bool:
    """Verifica si el OTP es válido para el teléfono dado"""
    if phone not in _otp_cache:
        return False

    cached = _otp_cache[phone]

    # Verificar expiración
    if datetime.utcnow() > cached["expires"]:
        logger.info(f"OTP expirado para {phone}")
        del _otp_cache[phone]
        return False

    # Verificar intentos
    if cached["attempts"] >= 3:
        logger.warning(f"Demasiados intentos para {phone}")
        return False

    # Verificar código
    if cached["otp"] != otp:
        cached["attempts"] += 1
        logger.info(f"OTP incorrecto para {phone} (intento {cached['attempts']})")
        return False

    return True


@router.post("/request-otp")
async def request_otp(
    data: RequestOTPSchema,
    db: AsyncSession = Depends(get_db),
):
    """
    Solicita un código OTP vía WhatsApp.

    1. Genera código de 6 dígitos
    2. Guarda en caché con expiración de 5 minutos
    3. Envía por WhatsApp usando template pre-aprobado

    Endpoint público (no requiere autenticación)
    """
    try:
        phone = _normalize_phone(data.phone)
        logger.info(f"📱 Solicitud de OTP para {phone}")

        # Rate limiting simple: no más de 1 OTP cada 60 segundos
        if phone in _otp_cache:
            time_since_last = datetime.utcnow() - _otp_cache[phone].get("created", datetime.utcnow())
            if time_since_last.total_seconds() < 60:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Espera {60 - int(time_since_last.total_seconds())} segundos antes de solicitar otro código"
                )

        # Generar OTP
        otp_code = _generate_otp()

        # Guardar en caché (expira en 5 minutos)
        _otp_cache[phone] = {
            "otp": otp_code,
            "expires": datetime.utcnow() + timedelta(minutes=5),
            "attempts": 0,
            "created": datetime.utcnow(),
        }

        logger.info(f"🔐 OTP generado para {phone}: {otp_code}")

        # Enviar por WhatsApp usando template
        # Nota: Requiere que el template "otp_login" esté aprobado en Meta
        whatsapp_service = WhatsAppService(
            api_token=os.getenv("KAPSO_API_KEY", ""),
        )

        whatsapp_config_id = os.getenv("KAPSO_WHATSAPP_CONFIG_ID")
        if not whatsapp_config_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="WhatsApp no configurado"
            )

        try:
            # Enviar template de autenticación
            # Nota: Para autenticación sin toque, el template debe estar configurado
            # en Meta Business Manager con la opción "Zero-tap autofill"
            await whatsapp_service.send_template(
                phone_number=phone,
                template_name="otp_login",  # Template aprobado con categoría AUTHENTICATION
                whatsapp_config_id=whatsapp_config_id,
                template_params=[otp_code],  # {{1}} = código OTP
                template_language="es",
                # Nota: Para zero-tap, el botón debe ser de tipo OTP autofill
                # Meta automáticamente detecta esto si el template es AUTHENTICATION
            )
            logger.info(f"✅ OTP enviado por WhatsApp a {phone}")
        except Exception as e:
            logger.error(f"❌ Error enviando OTP por WhatsApp: {e}")
            # No fallar si el envío falla - el código está guardado
            # En desarrollo, esto permite testing sin WhatsApp real

        return {
            "success": True,
            "message": "Código enviado por WhatsApp",
            "phone": phone,
            # En desarrollo, retornar el código (QUITAR EN PRODUCCIÓN)
            **({"otp": otp_code} if os.getenv("ENVIRONMENT") == "development" else {})
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en request_otp: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar código"
        )


@router.post("/verify-otp")
async def verify_otp(
    data: VerifyOTPSchema,
    db: AsyncSession = Depends(get_db),
):
    """
    Verifica código OTP y retorna JWT de Supabase.

    1. Valida OTP
    2. Crea/actualiza usuario en Supabase (si no existe)
    3. Genera JWT compatible con Supabase
    4. Retorna access_token + refresh_token

    Endpoint público (no requiere autenticación)
    """
    try:
        phone = _normalize_phone(data.phone)
        logger.info(f"🔍 Verificación de OTP para {phone}")

        # Validar OTP
        if not _is_otp_valid(phone, data.otp):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código inválido o expirado"
            )

        # OTP válido - eliminar de caché
        del _otp_cache[phone]
        logger.info(f"✅ OTP válido para {phone}")

        # Buscar perfil existente por teléfono
        result = await db.execute(
            select(Profile).where(Profile.phone == phone)
        )
        profile = result.scalar_one_or_none()

        if profile:
            # Usuario existe
            user_id = str(profile.id)
            email = profile.email
            logger.info(f"👤 Usuario existente encontrado: {user_id}")

            # Marcar teléfono como verificado si no lo estaba
            if not profile.phone_verified:
                profile.phone_verified = True
                profile.phone_verified_at = datetime.utcnow()
                await db.commit()
                logger.info(f"✓ Teléfono verificado para {user_id}")
        else:
            # Crear nuevo usuario
            # Usar phone como email temporal: +56912345678 -> 56912345678@whatsapp.fizko.ai
            temp_email = f"{phone.replace('+', '')}@whatsapp.fizko.ai"
            user_id = str(uuid4())

            logger.info(f"🆕 Creando nuevo usuario: {user_id}")

            new_profile = Profile(
                id=UUID(user_id),
                email=temp_email,
                phone=phone,
                phone_verified=True,
                phone_verified_at=datetime.utcnow(),
                rol="client",
            )
            db.add(new_profile)
            await db.commit()

            email = temp_email
            logger.info(f"✅ Usuario creado: {user_id}")

        # Generar JWT compatible con Supabase
        now = datetime.utcnow()
        exp = now + timedelta(hours=1)  # Token válido por 1 hora

        # Payload compatible con Supabase JWT
        payload = {
            "aud": "authenticated",
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
            "sub": user_id,
            "email": email,
            "phone": phone,
            "app_metadata": {
                "provider": "whatsapp",
                "providers": ["whatsapp"]
            },
            "user_metadata": {
                "auth_method": "whatsapp",
                "phone": phone
            },
            "role": "authenticated"
        }

        secret = get_jwt_secret()
        access_token = jwt.encode(payload, secret, algorithm="HS256")

        # Generar refresh token (válido por 30 días)
        refresh_exp = now + timedelta(days=30)
        refresh_payload = {**payload, "exp": int(refresh_exp.timestamp())}
        refresh_token = jwt.encode(refresh_payload, secret, algorithm="HS256")

        logger.info(f"🎫 JWT generado para {user_id}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": user_id,
                "email": email,
                "phone": phone,
                "phone_verified": True,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en verify_otp: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al verificar código"
        )


@router.get("/health")
async def health():
    """Health check para el servicio de autenticación WhatsApp"""
    return {
        "status": "ok",
        "service": "whatsapp_auth",
        "active_otps": len(_otp_cache),
    }
