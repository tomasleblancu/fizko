"""REST API endpoints for WhatsApp template synchronization (Admin)."""

import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id
from ...integrations.kapso import KapsoClient
from ...integrations.kapso.exceptions import KapsoNotFoundError, KapsoAPIError
from ...repositories import NotificationTemplateRepository

router = APIRouter()


@router.post("/notification-templates/sync-whatsapp/{template_name}")
async def sync_whatsapp_template_structure(
    template_name: str,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Sincronizar estructura de template de WhatsApp desde Meta API.

    Obtiene la estructura del template (named_parameters) desde Meta via Kapso
    y actualiza automáticamente el extra_metadata del template local que tenga
    ese whatsapp_template_id.

    - **template_name**: Nombre del template en WhatsApp/Meta (ej: daily_business_summary)
    """
    # Get credentials from env
    kapso_api_token = os.getenv("KAPSO_API_TOKEN", "")
    business_account_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")

    if not kapso_api_token:
        raise HTTPException(
            status_code=500,
            detail="KAPSO_API_TOKEN not configured"
        )

    if not business_account_id:
        raise HTTPException(
            status_code=500,
            detail="WHATSAPP_BUSINESS_ACCOUNT_ID not configured"
        )

    try:
        # 1. Get template structure from Kapso/Meta API
        kapso_client = KapsoClient(api_token=kapso_api_token)
        result = await kapso_client.templates.get_structure(
            template_name=template_name,
            business_account_id=business_account_id
        )

        # 2. Find local template with this whatsapp_template_id
        template_repo = NotificationTemplateRepository(db)
        local_template = await template_repo.find_by_whatsapp_template_id(template_name)

        if not local_template:
            raise HTTPException(
                status_code=404,
                detail=f"No local template found with whatsapp_template_id='{template_name}'. Create the template first."
            )

        # 3. Update extra_metadata with whatsapp_template_structure (delegate to repository)
        template_structure = result["whatsapp_template_structure"]
        updated_template = await template_repo.update_whatsapp_template_structure(
            template_id=local_template.id,
            whatsapp_template_structure=template_structure
        )

        return {
            "data": {
                "template_id": str(updated_template.id),
                "template_code": updated_template.code,
                "template_name": updated_template.name,
                "whatsapp_template_id": template_name,
                "whatsapp_template_structure": template_structure,
                "named_parameters": result["named_parameters"]
            },
            "message": f"Template '{updated_template.code}' updated with WhatsApp structure"
        }

    except KapsoNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_name}' not found in Meta API"
        )
    except KapsoAPIError as e:
        raise HTTPException(
            status_code=e.status_code if hasattr(e, 'status_code') else 500,
            detail=f"Error fetching template from Meta API: {str(e)}"
        )
    except ValueError as e:
        # Repository errors (template not found, etc.)
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
