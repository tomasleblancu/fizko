"""Repository for notification management."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    NotificationTemplate,
    NotificationSubscription,
    UserNotificationPreference,
    Profile,
    Session as UserSession
)
from app.repositories.base import BaseRepository


class NotificationTemplateRepository(BaseRepository[NotificationTemplate]):
    """Repository for managing notification templates."""

    def __init__(self, db: AsyncSession):
        super().__init__(NotificationTemplate, db)

    async def find_by_code(self, code: str, active_only: bool = True) -> Optional[NotificationTemplate]:
        """
        Find a template by code.

        Args:
            code: Template code
            active_only: Only return active templates

        Returns:
            NotificationTemplate instance or None if not found
        """
        query = select(NotificationTemplate).where(
            NotificationTemplate.code == code
        )

        if active_only:
            query = query.where(NotificationTemplate.is_active == True)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_by_whatsapp_template_id(self, whatsapp_template_id: str) -> Optional[NotificationTemplate]:
        """
        Find a template by whatsapp_template_id.

        Args:
            whatsapp_template_id: WhatsApp template ID from Meta

        Returns:
            NotificationTemplate instance or None if not found
        """
        query = select(NotificationTemplate).where(
            NotificationTemplate.whatsapp_template_id == whatsapp_template_id
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_whatsapp_template_structure(
        self,
        template_id: UUID,
        whatsapp_template_structure: dict
    ) -> NotificationTemplate:
        """
        Update the whatsapp_template_structure in extra_metadata.

        Args:
            template_id: Template UUID
            whatsapp_template_structure: Structure with header_params and body_params

        Returns:
            Updated NotificationTemplate instance

        Raises:
            ValueError: If template not found
        """
        from sqlalchemy.orm.attributes import flag_modified

        # Get template
        template = await self.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Merge with existing metadata
        current_metadata = template.extra_metadata or {}
        current_metadata["whatsapp_template_structure"] = whatsapp_template_structure

        # Update template (flag_modified needed for JSON fields)
        template.extra_metadata = current_metadata
        flag_modified(template, "extra_metadata")

        await self.db.commit()
        await self.db.refresh(template)

        return template

    async def find_auto_assign_templates(self) -> List[NotificationTemplate]:
        """
        Find all active templates with auto_assign_to_new_companies enabled.

        Returns:
            List of NotificationTemplate instances
        """
        result = await self.db.execute(
            select(NotificationTemplate).where(
                and_(
                    NotificationTemplate.auto_assign_to_new_companies == True,
                    NotificationTemplate.is_active == True
                )
            )
        )
        return list(result.scalars().all())


class NotificationSubscriptionRepository(BaseRepository[NotificationSubscription]):
    """Repository for managing notification subscriptions."""

    def __init__(self, db: AsyncSession):
        super().__init__(NotificationSubscription, db)

    async def find_by_company_and_template(
        self,
        company_id: UUID,
        template_id: UUID,
        enabled_only: bool = True
    ) -> Optional[NotificationSubscription]:
        """
        Find a subscription by company and template.

        Args:
            company_id: Company UUID
            template_id: Template UUID
            enabled_only: Only return enabled subscriptions

        Returns:
            NotificationSubscription instance or None if not found
        """
        query = select(NotificationSubscription).where(
            and_(
                NotificationSubscription.company_id == company_id,
                NotificationSubscription.notification_template_id == template_id
            )
        )

        if enabled_only:
            query = query.where(NotificationSubscription.is_enabled == True)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_by_company_with_templates(
        self,
        company_id: UUID
    ) -> List[tuple[NotificationSubscription, NotificationTemplate]]:
        """
        Find all subscriptions for a company with their templates.

        Args:
            company_id: Company UUID

        Returns:
            List of (NotificationSubscription, NotificationTemplate) tuples
        """
        result = await self.db.execute(
            select(NotificationSubscription, NotificationTemplate)
            .join(
                NotificationTemplate,
                NotificationSubscription.notification_template_id == NotificationTemplate.id
            )
            .where(NotificationSubscription.company_id == company_id)
        )
        return list(result.all())

    async def find_by_company_and_subscription_id(
        self,
        company_id: UUID,
        subscription_id: UUID
    ) -> Optional[NotificationSubscription]:
        """
        Find a subscription by company and subscription ID.

        Args:
            company_id: Company UUID
            subscription_id: Subscription UUID

        Returns:
            NotificationSubscription instance or None if not found
        """
        result = await self.db.execute(
            select(NotificationSubscription).where(
                and_(
                    NotificationSubscription.id == subscription_id,
                    NotificationSubscription.company_id == company_id
                )
            )
        )
        return result.scalar_one_or_none()


class UserNotificationPreferenceRepository(BaseRepository[UserNotificationPreference]):
    """Repository for managing user notification preferences."""

    def __init__(self, db: AsyncSession):
        super().__init__(UserNotificationPreference, db)

    async def find_by_user_and_company(
        self,
        user_id: UUID,
        company_id: UUID
    ) -> Optional[UserNotificationPreference]:
        """
        Find preferences by user and company.

        Args:
            user_id: User UUID
            company_id: Company UUID

        Returns:
            UserNotificationPreference instance or None if not found
        """
        result = await self.db.execute(
            select(UserNotificationPreference).where(
                and_(
                    UserNotificationPreference.user_id == user_id,
                    UserNotificationPreference.company_id == company_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def find_active_users_with_phone(
        self,
        company_id: UUID
    ) -> List[tuple[Profile, UserSession]]:
        """
        Find active users with phone for a company.

        Args:
            company_id: Company UUID

        Returns:
            List of (Profile, UserSession) tuples
        """
        result = await self.db.execute(
            select(Profile, UserSession)
            .join(UserSession, UserSession.user_id == Profile.id)
            .where(
                and_(
                    UserSession.company_id == company_id,
                    UserSession.is_active == True,
                    Profile.phone.isnot(None),
                    Profile.phone != ""
                )
            )
            .distinct()
        )
        return list(result.all())
