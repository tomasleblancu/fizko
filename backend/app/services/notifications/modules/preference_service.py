"""
User preference service for notifications
Handles user-specific notification preferences and settings
"""
import logging
from datetime import datetime, time as dt_time
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserNotificationPreference
from .base_service import BaseNotificationService

logger = logging.getLogger(__name__)


class PreferenceService(BaseNotificationService):
    """
    Service for managing user notification preferences.
    Handles user-specific settings for notification delivery.
    """

    async def get_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID
    ) -> Dict[str, Any]:
        """
        Get a user's notification preferences.

        Args:
            db: Database session
            user_id: User ID
            company_id: Company ID

        Returns:
            Dict with user preferences or default values
        """
        result = await db.execute(
            select(UserNotificationPreference).where(
                and_(
                    UserNotificationPreference.user_id == user_id,
                    UserNotificationPreference.company_id == company_id,
                )
            )
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            # Return default values
            return {
                "notifications_enabled": True,
                "quiet_hours_start": None,
                "quiet_hours_end": None,
                "quiet_days": None,
                "muted_categories": None,
                "muted_templates": [],
                "max_notifications_per_day": 20,
                "min_interval_minutes": 30,
            }

        return {
            "notifications_enabled": prefs.notifications_enabled,
            "quiet_hours_start": str(prefs.quiet_hours_start) if prefs.quiet_hours_start else None,
            "quiet_hours_end": str(prefs.quiet_hours_end) if prefs.quiet_hours_end else None,
            "quiet_days": prefs.quiet_days,
            "muted_categories": prefs.muted_categories,
            "muted_templates": prefs.muted_templates or [],
            "max_notifications_per_day": prefs.max_notifications_per_day,
            "min_interval_minutes": prefs.min_interval_minutes,
        }

    async def update_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        notifications_enabled: Optional[bool] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        quiet_days: Optional[List[str]] = None,
        muted_categories: Optional[List[str]] = None,
        muted_templates: Optional[List[str]] = None,
        max_notifications_per_day: Optional[int] = None,
        min_interval_minutes: Optional[int] = None
    ) -> UserNotificationPreference:
        """
        Update a user's notification preferences.

        Args:
            db: Database session
            user_id: User ID
            company_id: Company ID
            notifications_enabled: Whether notifications are enabled
            quiet_hours_start: Quiet hours start time (HH:MM)
            quiet_hours_end: Quiet hours end time (HH:MM)
            quiet_days: Quiet days list
            muted_categories: Muted categories list
            muted_templates: Muted template IDs list
            max_notifications_per_day: Maximum notifications per day
            min_interval_minutes: Minimum interval between notifications

        Returns:
            Updated UserNotificationPreference
        """
        result = await db.execute(
            select(UserNotificationPreference).where(
                and_(
                    UserNotificationPreference.user_id == user_id,
                    UserNotificationPreference.company_id == company_id,
                )
            )
        )
        prefs = result.scalar_one_or_none()

        # Parse time strings if provided
        quiet_start = None
        quiet_end = None
        if quiet_hours_start:
            hour, minute = map(int, quiet_hours_start.split(":"))
            quiet_start = dt_time(hour=hour, minute=minute)
        if quiet_hours_end:
            hour, minute = map(int, quiet_hours_end.split(":"))
            quiet_end = dt_time(hour=hour, minute=minute)

        if prefs:
            # Update existing - only update provided fields
            if notifications_enabled is not None:
                prefs.notifications_enabled = notifications_enabled
            if quiet_start is not None:
                prefs.quiet_hours_start = quiet_start
            if quiet_end is not None:
                prefs.quiet_hours_end = quiet_end
            if quiet_days is not None:
                prefs.quiet_days = quiet_days
            if muted_categories is not None:
                prefs.muted_categories = muted_categories
            if muted_templates is not None:
                prefs.muted_templates = muted_templates
            if max_notifications_per_day is not None:
                prefs.max_notifications_per_day = max_notifications_per_day
            if min_interval_minutes is not None:
                prefs.min_interval_minutes = min_interval_minutes
            prefs.updated_at = datetime.utcnow()
        else:
            # Create new
            prefs = UserNotificationPreference(
                user_id=user_id,
                company_id=company_id,
                notifications_enabled=notifications_enabled if notifications_enabled is not None else True,
                quiet_hours_start=quiet_start,
                quiet_hours_end=quiet_end,
                quiet_days=quiet_days,
                muted_categories=muted_categories,
                muted_templates=muted_templates or [],
                max_notifications_per_day=max_notifications_per_day if max_notifications_per_day is not None else 20,
                min_interval_minutes=min_interval_minutes if min_interval_minutes is not None else 30,
            )
            db.add(prefs)

        await db.commit()
        await db.refresh(prefs)

        return prefs
