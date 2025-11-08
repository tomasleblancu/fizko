"""
Celery tasks for company memory operations.

Handles saving and updating company memories in Mem0.
"""
import logging
from typing import Dict, List, Any
from uuid import UUID

from app.infrastructure.celery import celery_app
from app.config.database import AsyncSessionLocal
from app.services.memory_service import save_company_memories
from app.agents.tools.memory.memory_tools import get_mem0_client

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="memory.save_company_memories",
    max_retries=3,
    default_retry_delay=60,
)
def save_company_memories_task(
    self,
    company_id: str,
    memories: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Celery task for saving company memories to Mem0.

    Args:
        company_id: UUID of the company (str format)
        memories: List of memories with structure [{slug, category, content}, ...]

    Returns:
        Dict with result:
        {
            "success": bool,
            "company_id": str,
            "memories_count": int,
            "error": str (if failed)
        }
    """
    import asyncio

    async def _save():
        try:
            async with AsyncSessionLocal() as db:
                mem0 = get_mem0_client()
                company_uuid = UUID(company_id)

                logger.info(
                    f"[Memory Task] 🧠 Starting company memory save for {company_id} "
                    f"({len(memories)} memories)"
                )

                await save_company_memories(
                    db=db,
                    company_id=company_uuid,
                    mem0_client=mem0,
                    memories=memories
                )

                await db.commit()

                logger.info(
                    f"[Memory Task] ✅ Company memory save completed for {company_id}"
                )

                return {
                    "success": True,
                    "company_id": company_id,
                    "memories_count": len(memories)
                }

        except Exception as e:
            logger.error(
                f"[Memory Task] ❌ Error saving company memories for {company_id}: {e}",
                exc_info=True
            )

            # Retry on transient errors
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e, countdown=self.default_retry_delay)

            return {
                "success": False,
                "company_id": company_id,
                "memories_count": len(memories),
                "error": str(e)
            }

    return asyncio.run(_save())
