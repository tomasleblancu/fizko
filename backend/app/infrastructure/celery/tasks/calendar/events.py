"""
Celery tasks for calendar events and notifications activation.

These tasks are thin wrappers that delegate to services for business logic.
"""
import logging
from typing import Dict, Any
from uuid import UUID

from app.infrastructure.celery import celery_app
from app.config.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="calendar.activate_mandatory_events",
    max_retries=3,
    default_retry_delay=60,
)
def activate_mandatory_events_task(
    self,
    company_id: str
) -> Dict[str, Any]:
    """
    Celery task wrapper for activating mandatory events.

    Delegates business logic to EventActivationService.

    Args:
        company_id: UUID of the company (str format)

    Returns:
        Dict with result
    """
    import asyncio

    async def _activate():
        async with AsyncSessionLocal() as db:
            try:
                from app.services.calendar.event_activation_service import EventActivationService

                company_uuid = UUID(company_id)

                logger.info(
                    f"[Events Task] 🎯 Starting mandatory events activation for {company_id}"
                )

                # Delegate to service
                service = EventActivationService(db)
                activated_events = await service.activate_mandatory_events(company_uuid)

                await db.commit()

                logger.info(
                    f"[Events Task] 🎉 Completed: {len(activated_events)} events activated"
                )

                return {
                    "success": True,
                    "company_id": company_id,
                    "activated_events": activated_events
                }

            except Exception as e:
                logger.error(
                    f"[Events Task] ❌ Error: {e}",
                    exc_info=True
                )

                # Retry on transient errors
                if self.request.retries < self.max_retries:
                    raise self.retry(exc=e, countdown=self.default_retry_delay)

                return {
                    "success": False,
                    "company_id": company_id,
                    "activated_events": [],
                    "error": str(e)
                }

    return asyncio.run(_activate())


@celery_app.task(
    bind=True,
    name="calendar.assign_auto_notifications",
    max_retries=3,
    default_retry_delay=60,
)
def assign_auto_notifications_task(
    self,
    company_id: str,
    is_new_company: bool = True
) -> Dict[str, Any]:
    """
    Celery task wrapper for auto-assigning notifications.

    Delegates business logic to EventActivationService.

    Args:
        company_id: UUID of the company (str format)
        is_new_company: Whether this is a newly created company

    Returns:
        Dict with result
    """
    import asyncio

    async def _assign():
        async with AsyncSessionLocal() as db:
            try:
                from app.services.calendar.event_activation_service import EventActivationService

                company_uuid = UUID(company_id)

                logger.info(
                    f"[Events Task] 📢 Starting auto-notification assignment for {company_id}"
                )

                # Delegate to service
                service = EventActivationService(db)
                assigned_notifications = await service.assign_auto_notifications(
                    company_uuid,
                    is_new_company
                )

                await db.commit()

                logger.info(
                    f"[Events Task] 🎉 Completed: {len(assigned_notifications)} notifications assigned"
                )

                return {
                    "success": True,
                    "company_id": company_id,
                    "assigned_notifications": assigned_notifications
                }

            except Exception as e:
                logger.error(
                    f"[Events Task] ❌ Error: {e}",
                    exc_info=True
                )

                # Retry on transient errors
                if self.request.retries < self.max_retries:
                    raise self.retry(exc=e, countdown=self.default_retry_delay)

                return {
                    "success": False,
                    "company_id": company_id,
                    "assigned_notifications": [],
                    "error": str(e)
                }

    return asyncio.run(_assign())
