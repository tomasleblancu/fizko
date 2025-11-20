"""
Celery tasks for onboarding memory operations.

Thin wrapper that delegates to OnboardingMemoryService for business logic.
"""
import logging
from typing import Dict, Any
from uuid import UUID

from app.infrastructure.celery import celery_app
from app.config.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="memory.save_onboarding_memories",
    max_retries=3,
    default_retry_delay=60,
)
def save_onboarding_memories_task(
    self,
    user_id: str,
    company_id: str,
    company_tax_info_id: str,
    contribuyente_info: dict,
    is_new_company: bool
) -> Dict[str, Any]:
    """
    Celery task wrapper for saving onboarding memories.

    Delegates business logic to OnboardingMemoryService.

    Args:
        user_id: UUID of the user (str format)
        company_id: UUID of the company (str format)
        company_tax_info_id: UUID of CompanyTaxInfo (str format)
        contribuyente_info: Dict with contributor information from SII
        is_new_company: True if company was newly created

    Returns:
        Dict with result
    """
    import asyncio

    async def _save():
        async with AsyncSessionLocal() as db:
            try:
                from app.services.sii.auth_service.onboarding_memory_service import OnboardingMemoryService

                user_uuid = UUID(user_id)
                company_uuid = UUID(company_id)
                company_tax_info_uuid = UUID(company_tax_info_id)

                logger.info(
                    f"[Memory Task] 🧠 Starting onboarding memory save for "
                    f"user {user_id}, company {company_id}"
                )

                # Delegate to service
                service = OnboardingMemoryService(db)
                result = await service.save_onboarding_memories(
                    user_id=user_uuid,
                    company_id=company_uuid,
                    company_tax_info_id=company_tax_info_uuid,
                    contribuyente_info=contribuyente_info,
                    is_new_company=is_new_company
                )

                await db.commit()

                logger.info(
                    f"[Memory Task] ✅ Completed: "
                    f"{result['company_memories_count']} company memories, "
                    f"{result['user_memories_count']} user memories"
                )

                return {
                    "success": True,
                    "user_id": user_id,
                    "company_id": company_id,
                    **result
                }

            except Exception as e:
                logger.error(
                    f"[Memory Task] ❌ Error: {e}",
                    exc_info=True
                )

                # Retry on transient errors
                if self.request.retries < self.max_retries:
                    raise self.retry(exc=e, countdown=self.default_retry_delay)

                return {
                    "success": False,
                    "user_id": user_id,
                    "company_id": company_id,
                    "error": str(e)
                }

    return asyncio.run(_save())
