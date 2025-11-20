"""
Endpoints misceláneos: templates, inbox, health
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user_id
from app.services.whatsapp import get_whatsapp_service
from app.integrations.kapso.exceptions import KapsoAPIError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/templates")
async def list_templates(
    whatsapp_config_id: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Lista las plantillas de WhatsApp Business disponibles.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.list_templates(
            whatsapp_config_id=whatsapp_config_id,
        )
        return result

    except KapsoAPIError as e:
        logger.error(f"Error listando templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/inbox")
async def get_inbox(
    whatsapp_config_id: str,
    limit: int = 20,
    status_filter: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Obtiene la bandeja de entrada de conversaciones.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.get_inbox(
            whatsapp_config_id=whatsapp_config_id,
            limit=limit,
            status=status_filter,
        )
        return result

    except KapsoAPIError as e:
        logger.error(f"Error obteniendo inbox: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Verifica el estado de la conexión con Kapso.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.health_check()
        return result

    except Exception as e:
        logger.error(f"Health check falló: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
