"""
Template management service for notifications
Handles CRUD operations for notification templates
"""
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationTemplate
from app.repositories import NotificationTemplateRepository
from .base_service import BaseNotificationService

logger = logging.getLogger(__name__)


class TemplateService(BaseNotificationService):
    """
    Service for managing notification templates.
    Handles creation, reading, updating, and deletion of templates.
    Delegates all database operations to NotificationTemplateRepository.
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
        repo = NotificationTemplateRepository(db)

        if template_id:
            return await repo.get(template_id)
        elif code:
            return await repo.find_by_code(code, active_only=False)
        else:
            raise ValueError("template_id or code is required")

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
        # Build query with filters
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
        repo = NotificationTemplateRepository(db)

        # Check if code already exists
        existing = await repo.find_by_code(code, active_only=False)
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
            whatsapp_template_id=whatsapp_template_id,
        )

        created = await repo.create(new_template)

        logger.info(f"Created notification template: {code}")
        if whatsapp_template_id:
            logger.info(f"  └─ WhatsApp template ID: {whatsapp_template_id}")

        return created

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
        repo = NotificationTemplateRepository(db)

        # Find template
        template = await repo.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # If changing code, check it doesn't exist
        if code and code != template.code:
            existing = await repo.find_by_code(code, active_only=False)
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

        updated = await repo.update(template)

        logger.info(f"Updated notification template: {updated.code}")
        return updated

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
        repo = NotificationTemplateRepository(db)

        # Find template
        template = await repo.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Delete template (CASCADE will handle subscriptions automatically)
        await repo.delete(template_id)

        logger.info(f"Deleted notification template: {template.code}")
        return True
