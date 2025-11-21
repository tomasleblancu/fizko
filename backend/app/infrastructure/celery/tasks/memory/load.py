"""
Memory Loading Celery Tasks

Tasks for loading memories from existing company and user data into Mem0.
This is the initial data population phase for the memory system.

These tasks orchestrate service calls without business logic.
All logic is in the service layer (app.services.memory_service).
"""
import logging
from typing import Dict, Any

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="memory.load_company_memories",
    max_retries=2,
    default_retry_delay=60,
)
def load_company_memories(
    self,
    company_id: str
) -> Dict[str, Any]:
    """
    Celery task to load memories for a specific company from existing data.

    This task orchestrates service calls:
    1. Calls build_company_memories_from_data() to extract data
    2. Calls save_company_memories() to store in Mem0 + database
    3. Is idempotent - can be run multiple times (updates existing memories)

    Args:
        company_id: UUID of the company (str format)

    Returns:
        Dict with load results:
        {
            "success": bool,
            "company_id": str,
            "company_name": str,
            "memories_saved": int,
            "errors": list[str]
        }

    Example:
        >>> load_company_memories.delay("123e4567-e89b-12d3-a456-426614174000")
    """
    try:
        import asyncio
        from app.services import build_company_memories_from_data, save_company_memories

        logger.info(
            f"🧠 [CELERY TASK] Loading company memories: company_id={company_id}"
        )

        async def _load():
            # Build memories from existing data
            build_result = await build_company_memories_from_data(company_id)

            if not build_result["success"]:
                return {
                    "success": False,
                    "company_id": company_id,
                    "errors": [build_result.get("error", "Failed to build memories")]
                }

            company_name = build_result["company_name"]
            memories = build_result["memories"]

            logger.info(
                f"🧠 Built {len(memories)} memories for company {company_name}"
            )

            if len(memories) == 0:
                logger.warning(
                    f"⚠️  No memory data available for company {company_name}"
                )
                return {
                    "success": True,
                    "company_id": company_id,
                    "company_name": company_name,
                    "memories_saved": 0,
                    "errors": ["No data available to create memories"]
                }

            # Save memories to Mem0
            save_result = await save_company_memories(
                company_id=company_id,
                memories=memories
            )

            # Return combined result
            return {
                "success": save_result["success"],
                "company_id": company_id,
                "company_name": company_name,
                "memories_saved": save_result["saved_count"],
                "errors": save_result.get("errors", [])
            }

        # Run async function
        result = asyncio.run(_load())

        # Log result
        if result.get("success"):
            logger.info(
                f"✅ [CELERY TASK] Company memories loaded: "
                f"company={result.get('company_name')}, "
                f"saved={result.get('memories_saved', 0)}"
            )
        else:
            logger.error(
                f"❌ [CELERY TASK] Company memories failed: "
                f"company_id={company_id}, "
                f"errors={result.get('errors')}"
            )

        return result

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Company memory load failed: {e}",
            exc_info=True
        )

        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            logger.info(
                f"🔄 Retrying... (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        return {
            "success": False,
            "company_id": company_id,
            "errors": [str(e)]
        }


@celery_app.task(
    bind=True,
    name="memory.load_user_memories",
    max_retries=2,
    default_retry_delay=60,
)
def load_user_memories(
    self,
    user_id: str
) -> Dict[str, Any]:
    """
    Celery task to load memories for a specific user from existing data.

    This task orchestrates service calls:
    1. Calls build_user_memories_from_data() to extract data
    2. Calls save_user_memories() to store in Mem0 + database
    3. Is idempotent - can be run multiple times (updates existing memories)

    Args:
        user_id: UUID of the user (str format)

    Returns:
        Dict with load results:
        {
            "success": bool,
            "user_id": str,
            "user_name": str,
            "memories_saved": int,
            "errors": list[str]
        }

    Example:
        >>> load_user_memories.delay("123e4567-e89b-12d3-a456-426614174000")
    """
    try:
        import asyncio
        from app.services import build_user_memories_from_data, save_user_memories

        logger.info(
            f"🧠 [CELERY TASK] Loading user memories: user_id={user_id}"
        )

        async def _load():
            # Build memories from existing data
            build_result = await build_user_memories_from_data(user_id)

            if not build_result["success"]:
                return {
                    "success": False,
                    "user_id": user_id,
                    "errors": [build_result.get("error", "Failed to build memories")]
                }

            user_name = build_result["user_name"]
            memories = build_result["memories"]

            logger.info(
                f"🧠 Built {len(memories)} memories for user {user_name}"
            )

            if len(memories) == 0:
                logger.warning(
                    f"⚠️  No memory data available for user {user_name}"
                )
                return {
                    "success": True,
                    "user_id": user_id,
                    "user_name": user_name,
                    "memories_saved": 0,
                    "errors": ["No data available to create memories"]
                }

            # Save memories to Mem0
            save_result = await save_user_memories(
                user_id=user_id,
                memories=memories
            )

            # Return combined result
            return {
                "success": save_result["success"],
                "user_id": user_id,
                "user_name": user_name,
                "memories_saved": save_result["saved_count"],
                "errors": save_result.get("errors", [])
            }

        # Run async function
        result = asyncio.run(_load())

        # Log result
        if result.get("success"):
            logger.info(
                f"✅ [CELERY TASK] User memories loaded: "
                f"user={result.get('user_name')}, "
                f"saved={result.get('memories_saved', 0)}"
            )
        else:
            logger.error(
                f"❌ [CELERY TASK] User memories failed: "
                f"user_id={user_id}, "
                f"errors={result.get('errors')}"
            )

        return result

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] User memory load failed: {e}",
            exc_info=True
        )

        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            logger.info(
                f"🔄 Retrying... (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        return {
            "success": False,
            "user_id": user_id,
            "errors": [str(e)]
        }


@celery_app.task(
    bind=True,
    name="memory.load_all_companies_memories",
    max_retries=1,
)
def load_all_companies_memories(self) -> Dict[str, Any]:
    """
    Celery task to load memories for ALL companies in batch.

    This is a batch task that:
    1. Finds all companies in the system (via repository)
    2. For each company, calls load_company_memories task
    3. Returns statistics about the batch operation

    Useful for:
    - Initial memory population
    - Recovery after system issues
    - Bulk memory refresh

    Returns:
        Dict with batch load results:
        {
            "success": bool,
            "total_companies": int,
            "loaded_companies": int,
            "failed_companies": int,
            "total_memories_saved": int,
            "results": list[dict]  # Per-company results
        }

    Example:
        >>> load_all_companies_memories.delay()
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.repositories import CompaniesRepository

        logger.info("🚀 [CELERY TASK] Batch company memory load started for ALL companies")

        async def _load_all():
            # Get all companies (via repository)
            supabase = get_supabase_client()
            companies_repo = CompaniesRepository(supabase._client)
            companies = await companies_repo.get_all(limit=1000)

            if not companies:
                logger.warning("⚠️  No companies found")
                return {
                    "success": True,
                    "total_companies": 0,
                    "loaded_companies": 0,
                    "failed_companies": 0,
                    "total_memories_saved": 0,
                    "results": []
                }

            logger.info(f"🧠 Found {len(companies)} companies to process")

            loaded_count = 0
            failed_count = 0
            total_memories = 0
            results = []

            # Process each company
            for company in companies:
                company_id = company["id"]
                company_name = company.get("business_name", "Unknown")

                try:
                    # Use the single-company task synchronously
                    result = load_company_memories(company_id)

                    if result.get("success"):
                        loaded_count += 1
                        total_memories += result.get("memories_saved", 0)
                    else:
                        failed_count += 1

                    results.append(result)

                except Exception as e:
                    logger.error(
                        f"❌ Failed to load memories for company {company_name}: {e}"
                    )
                    failed_count += 1
                    results.append({
                        "success": False,
                        "company_id": company_id,
                        "company_name": company_name,
                        "errors": [str(e)]
                    })

            return {
                "success": failed_count == 0,
                "total_companies": len(companies),
                "loaded_companies": loaded_count,
                "failed_companies": failed_count,
                "total_memories_saved": total_memories,
                "results": results
            }

        # Run async function
        result = asyncio.run(_load_all())

        logger.info(
            f"✅ [CELERY TASK] Batch company memory load completed: "
            f"{result.get('loaded_companies', 0)}/{result.get('total_companies', 0)} companies loaded, "
            f"{result.get('failed_companies', 0)} failed, "
            f"{result.get('total_memories_saved', 0)} memories saved"
        )

        return result

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Batch company memory load failed: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "total_companies": 0,
            "loaded_companies": 0,
            "failed_companies": 0,
            "total_memories_saved": 0,
            "results": []
        }


@celery_app.task(
    bind=True,
    name="memory.load_all_users_memories",
    max_retries=1,
)
def load_all_users_memories(self) -> Dict[str, Any]:
    """
    Celery task to load memories for ALL users in batch.

    This is a batch task that:
    1. Finds all users in the system (via Supabase client)
    2. For each user, calls load_user_memories task
    3. Returns statistics about the batch operation

    Useful for:
    - Initial memory population
    - Recovery after system issues
    - Bulk memory refresh

    Returns:
        Dict with batch load results:
        {
            "success": bool,
            "total_users": int,
            "loaded_users": int,
            "failed_users": int,
            "total_memories_saved": int,
            "results": list[dict]  # Per-user results
        }

    Example:
        >>> load_all_users_memories.delay()
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client

        logger.info("🚀 [CELERY TASK] Batch user memory load started for ALL users")

        async def _load_all():
            # Get all users (via Supabase client)
            supabase = get_supabase_client()
            profiles_response = (
                supabase._client
                .table("profiles")
                .select("id, full_name, email")
                .limit(1000)
                .execute()
            )
            profiles = profiles_response.data if hasattr(profiles_response, "data") else []

            if not profiles:
                logger.warning("⚠️  No users found")
                return {
                    "success": True,
                    "total_users": 0,
                    "loaded_users": 0,
                    "failed_users": 0,
                    "total_memories_saved": 0,
                    "results": []
                }

            logger.info(f"🧠 Found {len(profiles)} users to process")

            loaded_count = 0
            failed_count = 0
            total_memories = 0
            results = []

            # Process each user
            for profile in profiles:
                user_id = profile["id"]
                user_name = profile.get("full_name", profile.get("email", "Unknown"))

                try:
                    # Use the single-user task synchronously
                    result = load_user_memories(user_id)

                    if result.get("success"):
                        loaded_count += 1
                        total_memories += result.get("memories_saved", 0)
                    else:
                        failed_count += 1

                    results.append(result)

                except Exception as e:
                    logger.error(
                        f"❌ Failed to load memories for user {user_name}: {e}"
                    )
                    failed_count += 1
                    results.append({
                        "success": False,
                        "user_id": user_id,
                        "user_name": user_name,
                        "errors": [str(e)]
                    })

            return {
                "success": failed_count == 0,
                "total_users": len(profiles),
                "loaded_users": loaded_count,
                "failed_users": failed_count,
                "total_memories_saved": total_memories,
                "results": results
            }

        # Run async function
        result = asyncio.run(_load_all())

        logger.info(
            f"✅ [CELERY TASK] Batch user memory load completed: "
            f"{result.get('loaded_users', 0)}/{result.get('total_users', 0)} users loaded, "
            f"{result.get('failed_users', 0)} failed, "
            f"{result.get('total_memories_saved', 0)} memories saved"
        )

        return result

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Batch user memory load failed: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "total_users": 0,
            "loaded_users": 0,
            "failed_users": 0,
            "total_memories_saved": 0,
            "results": []
        }
