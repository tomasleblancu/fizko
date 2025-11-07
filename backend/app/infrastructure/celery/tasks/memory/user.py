"""
Celery tasks for user memory operations.

Handles saving and updating user memories in Mem0.
"""
import logging
from typing import Dict, List, Any
from uuid import UUID

from app.infrastructure.celery import celery_app
from app.config.database import AsyncSessionLocal
from app.services.memory_service import save_user_memories
from app.agents.tools.memory.memory_tools import get_mem0_client

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="memory.save_user_memories",
    max_retries=3,
    default_retry_delay=60,
)
def save_user_memories_task(
    self,
    user_id: str,
    memories: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Celery task for saving user memories to Mem0.

    Args:
        user_id: UUID of the user (str format)
        memories: List of memories with structure [{slug, category, content}, ...]

    Returns:
        Dict with result:
        {
            "success": bool,
            "user_id": str,
            "memories_count": int,
            "error": str (if failed)
        }
    """
    import asyncio

    async def _save():
        mem0 = None
        try:
            async with AsyncSessionLocal() as db:
                mem0 = get_mem0_client()
                user_uuid = UUID(user_id)

                logger.info(
                    f"[Memory Task] 🧠 Starting user memory save for {user_id} "
                    f"({len(memories)} memories)"
                )

                await save_user_memories(
                    db=db,
                    user_id=user_uuid,
                    mem0_client=mem0,
                    memories=memories
                )

                await db.commit()

                logger.info(
                    f"[Memory Task] ✅ User memory save completed for {user_id}"
                )

                return {
                    "success": True,
                    "user_id": user_id,
                    "memories_count": len(memories)
                }

        except Exception as e:
            logger.error(
                f"[Memory Task] ❌ Error saving user memories for {user_id}: {e}",
                exc_info=True
            )

            # Retry on transient errors
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e, countdown=self.default_retry_delay)

            return {
                "success": False,
                "user_id": user_id,
                "memories_count": len(memories),
                "error": str(e)
            }
        finally:
            # Cerrar explícitamente el cliente async para evitar "Event loop is closed"
            if mem0 is not None:
                try:
                    await mem0.async_client.aclose()
                    logger.debug("[Memory Task] 🔌 Mem0 client closed")
                except Exception as close_error:
                    logger.warning(f"[Memory Task] ⚠️ Error closing Mem0 client: {close_error}")

    return asyncio.run(_save())
