"""
Testing endpoints for admin - send test notifications - REFACTORED VERSION

This version uses repositories instead of direct SQL queries.
"""
import logging
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...config.database import get_db
from ...dependencies import get_current_user_id
from ...db.models import NotificationTemplate, NotificationHistory
from ...repositories import (
    CompanyRepository,
    SessionRepository,
    NotificationTemplateRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class SendTestNotificationRequest(BaseModel):
    """Request to send a test notification"""
    message: Optional[str] = "🔔 Notificación de prueba desde Fizko Admin"
    template_code: Optional[str] = None


class SendTestNotificationResponse(BaseModel):
    """Response from sending test notification"""
    success: bool
    message: str
    notifications_sent: int
    details: List[dict]


@router.post("/company/{company_id}/send-test-notification", response_model=SendTestNotificationResponse)
async def send_test_notification(
    company_id: UUID,
    request: SendTestNotificationRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Envía una notificación de prueba por WhatsApp a todos los usuarios con teléfono verificado de la empresa.

    Útil para:
    - Probar el sistema de notificaciones
    - Verificar integración con WhatsApp/Kapso
    - Testear el contexto de notificaciones en el agente

    Args:
        company_id: ID de la empresa
        request: Configuración de la notificación (mensaje personalizado y template opcional)

    Returns:
        Resumen de notificaciones enviadas
    """
    logger.info(f"📬 Admin solicitó envío de notificación de prueba para empresa {company_id}")

    # Initialize repositories
    company_repo = CompanyRepository(db)
    session_repo = SessionRepository(db)
    template_repo = NotificationTemplateRepository(db)

    # 1. Verificar que la empresa existe
    company = await company_repo.get(company_id)

    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    # 2. Obtener usuarios de la empresa con teléfono verificado usando repositorio
    users = await session_repo.get_users_with_verified_phone(company_id, active_only=True)

    if not users:
        return SendTestNotificationResponse(
            success=False,
            message="No hay usuarios con teléfono verificado asociados a esta empresa",
            notifications_sent=0,
            details=[]
        )

    logger.info(f"📱 Encontrados {len(users)} usuarios con teléfono verificado")

    # 3. Obtener o crear template de notificación de prueba
    template = None
    if request.template_code:
        # Buscar template específico usando repositorio
        template = await template_repo.find_by_code(request.template_code)

        if not template or not template.is_active:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{request.template_code}' no encontrado o inactivo"
            )
    else:
        # Buscar template genérico de prueba usando repositorio
        template = await template_repo.find_by_code("test_notification")

    # 4. Importar WhatsApp service
    from ...services.whatsapp import WhatsAppService
    import os

    whatsapp_service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN", ""),
        base_url=os.getenv("KAPSO_API_BASE_URL", "https://app.kapso.ai/api/v1"),
    )

    # Get WhatsApp config ID
    whatsapp_config_id = os.getenv("DEFAULT_WHATSAPP_CONFIG_ID")

    if not whatsapp_config_id:
        raise HTTPException(
            status_code=500,
            detail="DEFAULT_WHATSAPP_CONFIG_ID no configurado en el servidor"
        )

    # 5. Enviar notificaciones a cada usuario
    details = []
    success_count = 0

    for user in users:
        try:
            # Preparar mensaje
            message = request.message or "🔔 Notificación de prueba desde Fizko Admin"

            if template:
                # Si hay template, usar su mensaje
                message = template.message_template.replace("{{company_name}}", company.business_name)
                message = message.replace("{{user_name}}", user.full_name or user.name or "Usuario")

            # Normalize phone number - remove '+' prefix if present
            normalized_phone = user.phone.lstrip('+') if user.phone else None

            if not normalized_phone:
                raise ValueError(f"Número de teléfono inválido: {user.phone}")

            # Find existing active conversation
            conversations = await whatsapp_service.list_conversations(
                whatsapp_config_id=whatsapp_config_id,
                limit=50,
            )

            conversation_id = None
            nodes = (
                conversations.get("data") or
                conversations.get("nodes") or
                conversations.get("conversations") or
                conversations.get("items") or
                []
            )

            for conv in nodes:
                conv_phone = conv.get("phone_number", "").lstrip('+')
                conv_status = conv.get("status", "")

                if conv_phone == normalized_phone and conv_status == "active":
                    conversation_id = conv.get("id")
                    break

            if not conversation_id:
                raise ValueError(f"No se encontró conversación activa para {normalized_phone}")

            # Enviar mensaje por WhatsApp
            result = await whatsapp_service.send_text(
                conversation_id=conversation_id,
                message=message,
            )

            # Guardar en historial de notificaciones
            notification_history = NotificationHistory(
                company_id=company_id,
                notification_template_id=template.id if template else None,
                entity_type="test",
                entity_id=None,
                user_id=user.id,
                phone_number=user.phone,
                message_content=message,
                status="sent",
                whatsapp_conversation_id=result.get("conversation_id"),
                whatsapp_message_id=result.get("id"),
                sent_at=datetime.utcnow(),
                extra_metadata={
                    "test_notification": True,
                    "sent_by_admin": str(user_id),
                    "template_code": template.code if template else None,
                }
            )

            db.add(notification_history)
            success_count += 1

            details.append({
                "user_email": user.email,
                "user_name": user.full_name or user.name,
                "phone": user.phone,
                "status": "sent",
                "message_id": result.get("id"),
                "conversation_id": result.get("conversation_id"),
            })

            logger.info(f"✅ Notificación enviada a {user.email} ({user.phone})")

        except Exception as e:
            logger.error(f"❌ Error enviando notificación a {user.email}: {e}")
            details.append({
                "user_email": user.email,
                "user_name": user.full_name or user.name,
                "phone": user.phone,
                "status": "error",
                "error": str(e),
            })

    # 6. Commit de historial
    await db.commit()

    return SendTestNotificationResponse(
        success=success_count > 0,
        message=f"Notificación enviada a {success_count} de {len(users)} usuarios",
        notifications_sent=success_count,
        details=details
    )
