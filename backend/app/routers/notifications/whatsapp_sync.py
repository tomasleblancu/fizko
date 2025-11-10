"""REST API endpoints for WhatsApp template synchronization (Admin)."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id
from ...services.notifications import NotificationService, get_notification_service

router = APIRouter()


def get_template_service() -> NotificationService:
    """
    Dependency to get NotificationService instance.

    Returns:
        NotificationService instance
    """
    return get_notification_service()


@router.post("/notification-templates/sync-whatsapp/{template_name}")
async def sync_whatsapp_template_structure(
    template_name: str,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_template_service)
):
    """
    Sincronizar estructura de template de WhatsApp desde Meta API.

    Obtiene la estructura del template (named_parameters) desde Meta via Kapso
    y actualiza automáticamente el extra_metadata del template local que tenga
    ese whatsapp_template_id.

    - **template_name**: Nombre del template en WhatsApp/Meta (ej: daily_business_summary)
    """
    result = await service.templates.sync_whatsapp_template_structure(
        db=db,
        template_name=template_name
    )

    return {
        "data": result,
        "message": f"Template '{result['template_code']}' updated with WhatsApp structure"
    }
