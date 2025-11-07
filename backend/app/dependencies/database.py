"""Database session dependencies."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db as _get_db, AsyncSessionLocal


async def get_db_session() -> AsyncSession:
    """
    Get database session dependency for FastAPI endpoints.

    This is a wrapper around get_db for consistency.
    Prefer using get_db directly or via Depends(get_db).

    Yields:
        AsyncSession: Database session
    """
    async for session in _get_db():
        yield session


# =============================================================================
# Background Task DB Dependencies (Celery, Webhooks, Agents)
# =============================================================================


@asynccontextmanager
async def get_background_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions in background tasks.

    Use this in Celery tasks, webhooks, or any non-FastAPI context where
    you need a database session.

    Example (Celery task):
        ```python
        @celery_app.task
        def my_task(company_id: str):
            import asyncio

            async def _run():
                async with get_background_db() as db:
                    # Your database operations here
                    result = await db.execute(select(Company).where(...))
                    await db.commit()

            return asyncio.run(_run())
        ```

    Example (Webhook handler):
        ```python
        @router.post("/webhook")
        async def handle_webhook(data: dict):
            async with get_background_db() as db:
                # Process webhook with DB access
                await process_data(db, data)
        ```

    Benefits:
    - Consistent error handling and rollback
    - Proper session lifecycle management
    - Connection pooling (reuses connections from the pool)
    - Automatic commit on success, rollback on error

    Note: This uses the same connection pool as FastAPI routes (get_db),
    so connections are efficiently reused, not created new each time.

    Yields:
        AsyncSession: Database session that auto-commits on success
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def run_in_db_context(func, *args, **kwargs):
    """
    Helper to run an async function with a database session.

    Useful for Celery tasks that need to call async functions with DB access.

    Example:
        ```python
        @celery_app.task
        def sync_documents(company_id: str):
            import asyncio

            async def _sync(db: AsyncSession):
                service = DocumentService(db)
                return await service.sync_all(company_id)

            return asyncio.run(run_in_db_context(_sync))
        ```

    Args:
        func: Async function that takes AsyncSession as first argument
        *args: Additional positional arguments for func
        **kwargs: Additional keyword arguments for func

    Returns:
        Result from func
    """
    async with get_background_db() as db:
        return await func(db, *args, **kwargs)


# =============================================================================
# Type Aliases for Convenience
# =============================================================================

DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


__all__ = [
    "get_db_session",
    "get_background_db",
    "run_in_db_context",
    "DbSessionDep",
]
