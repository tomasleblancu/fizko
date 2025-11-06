"""
Template management service for notifications
Handles CRUD operations for notification templates
"""
import logging
import re
import os
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationTemplate, NotificationSubscription
from .base_service import BaseNotificationService

logger = logging.getLogger(__name__)


class TemplateService(BaseNotificationService):
    """
    Service for managing notification templates.
    Handles creation, reading, updating, and deletion of templates.
    """

    # ========== TEMPLATE CRUD METHODS ==========

    async def get_template(
        self,
        db: AsyncSession,
        template_id: Optional[UUID] = None,
        code: Optional[str] = None,
    ) -> Optional[NotificationTemplate]:
        """
        Get a notification template by ID or code.

        Args:
            db: Database session
            template_id: Template ID
            code: Template code

        Returns:
            NotificationTemplate or None if not found
        """
        if template_id:
            result = await db.execute(
                select(NotificationTemplate).where(NotificationTemplate.id == template_id)
            )
        elif code:
            result = await db.execute(
                select(NotificationTemplate).where(NotificationTemplate.code == code)
            )
        else:
            raise ValueError("template_id or code is required")

        return result.scalar_one_or_none()

    async def list_templates(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        entity_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[NotificationTemplate]:
        """
        List notification templates with optional filters.

        Args:
            db: Database session
            category: Filter by category
            entity_type: Filter by entity type
            is_active: Filter by active status

        Returns:
            List of notification templates
        """
        query = select(NotificationTemplate)

        if category:
            query = query.where(NotificationTemplate.category == category)
        if entity_type:
            query = query.where(NotificationTemplate.entity_type == entity_type)
        if is_active is not None:
            query = query.where(NotificationTemplate.is_active == is_active)

        query = query.order_by(NotificationTemplate.category, NotificationTemplate.name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_template(
        self,
        db: AsyncSession,
        code: str,
        name: str,
        category: str,
        message_template: str,
        timing_config: dict,
        description: Optional[str] = None,
        entity_type: Optional[str] = None,
        priority: str = "normal",
        is_active: bool = True,
        auto_assign_to_new_companies: bool = False,
        metadata: Optional[dict] = None,
        # WhatsApp Template ID (from Meta Business Manager)
        whatsapp_template_id: Optional[str] = None,
    ) -> NotificationTemplate:
        """
        Create a new notification template.

        Args:
            db: Database session
            code: Unique template code
            name: Template name
            category: Template category
            message_template: Message template with variables
            timing_config: Timing configuration
            description: Optional description
            entity_type: Related entity type
            priority: Priority (low, normal, high, urgent)
            is_active: Whether template is active
            auto_assign_to_new_companies: Auto-assign to new companies
            metadata: Additional metadata
            whatsapp_template_id: WhatsApp template ID from Meta (optional)

        Returns:
            Created NotificationTemplate

        Raises:
            ValueError: If template with code already exists
        """
        # Check if code already exists
        result = await db.execute(
            select(NotificationTemplate).where(NotificationTemplate.code == code)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Template with code '{code}' already exists")

        # Create new template
        new_template = NotificationTemplate(
            code=code,
            name=name,
            description=description,
            category=category,
            entity_type=entity_type,
            message_template=message_template,
            timing_config=timing_config,
            priority=priority,
            is_active=is_active,
            auto_assign_to_new_companies=auto_assign_to_new_companies,
            extra_metadata=metadata or {},
            # WhatsApp template ID (manually created in Meta)
            whatsapp_template_id=whatsapp_template_id,
        )

        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)

        logger.info(f"Created notification template: {code}")
        if whatsapp_template_id:
            logger.info(f"  └─ WhatsApp template ID: {whatsapp_template_id}")

        return new_template

    async def update_template(
        self,
        db: AsyncSession,
        template_id: UUID,
        code: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        entity_type: Optional[str] = None,
        message_template: Optional[str] = None,
        timing_config: Optional[dict] = None,
        priority: Optional[str] = None,
        is_active: Optional[bool] = None,
        auto_assign_to_new_companies: Optional[bool] = None,
        metadata: Optional[dict] = None,
        whatsapp_template_id: Optional[str] = None
    ) -> NotificationTemplate:
        """
        Update a notification template.

        Args:
            db: Database session
            template_id: Template ID to update
            (other optional parameters for update)

        Returns:
            Updated NotificationTemplate

        Raises:
            ValueError: If template not found or code already in use
        """
        # Find template
        result = await db.execute(
            select(NotificationTemplate).where(NotificationTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()

        if not template:
            raise ValueError(f"Template {template_id} not found")

        # If changing code, check it doesn't exist
        if code and code != template.code:
            result = await db.execute(
                select(NotificationTemplate).where(NotificationTemplate.code == code)
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise ValueError(f"Template with code '{code}' already exists")

        # Update only provided fields
        if code is not None:
            template.code = code
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if category is not None:
            template.category = category
        if entity_type is not None:
            template.entity_type = entity_type
        if message_template is not None:
            template.message_template = message_template
        if timing_config is not None:
            template.timing_config = timing_config
        if priority is not None:
            template.priority = priority
        if is_active is not None:
            template.is_active = is_active
        if auto_assign_to_new_companies is not None:
            template.auto_assign_to_new_companies = auto_assign_to_new_companies
        if metadata is not None:
            template.extra_metadata = metadata
        if whatsapp_template_id is not None:
            template.whatsapp_template_id = whatsapp_template_id

        await db.commit()
        await db.refresh(template)

        logger.info(f"Updated notification template: {template.code}")
        return template

    async def delete_template(
        self,
        db: AsyncSession,
        template_id: UUID
    ) -> bool:
        """
        Delete a notification template.

        Note: Associated subscriptions will be automatically deleted via ON DELETE CASCADE.

        Args:
            db: Database session
            template_id: Template ID to delete

        Returns:
            True if successfully deleted

        Raises:
            ValueError: If template not found
        """
        # Find template
        result = await db.execute(
            select(NotificationTemplate).where(NotificationTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()

        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Delete template (CASCADE will handle subscriptions automatically)
        await db.delete(template)
        await db.commit()

        logger.info(f"Deleted notification template: {template.code}")
        return True
