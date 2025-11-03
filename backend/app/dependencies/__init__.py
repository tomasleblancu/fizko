"""Shared dependencies for FastAPI routes."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db, AsyncSessionLocal
from ..core.auth import get_current_user


async def get_current_active_user(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Get the current active user."""
    # You can add additional checks here (e.g., user is not banned)
    return user


async def get_current_user_id(
    user: dict[str, Any] = Depends(get_current_user),
) -> str:
    """Extract user ID from authenticated user."""
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    return user_id


async def get_user_company_id(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> str:
    """
    Get the company_id from the user's active session.

    This ensures that operations are always associated with the company
    the user is currently accessing.

    Raises:
        HTTPException: If no active session is found for the user.

    Returns:
        str: The company_id from the active session.
    """
    from uuid import UUID
    from sqlalchemy import desc, select
    from ..db.models import Session as SessionModel

    # Find active session for this user
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.user_id == UUID(current_user_id))
        .where(SessionModel.is_active == True)
        .order_by(desc(SessionModel.last_accessed_at))
        .limit(1)
    )
    session = result.scalar_one_or_none()

    if not session or not session.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active company session found. Please select a company first."
        )

    return str(session.company_id)


async def require_auth(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Require authentication - raises 401 if not authenticated."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


async def get_db_session() -> AsyncSession:
    """Get database session dependency."""
    async for session in get_db():
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


# Export repository factories
from .repositories import (  # noqa: E402
    # Factory functions
    get_person_repository,
    get_payroll_repository,
    get_purchase_document_repository,
    get_sales_document_repository,
    get_form29_repository,
    get_tax_document_repository,
    # Type aliases
    PersonRepositoryDep,
    PayrollRepositoryDep,
    PurchaseDocumentRepositoryDep,
    SalesDocumentRepositoryDep,
    Form29RepositoryDep,
    TaxDocumentRepositoryDep,
)

__all__ = [
    # Auth
    "get_current_active_user",
    "get_current_user_id",
    "get_user_company_id",
    "require_auth",
    "get_db_session",
    # Background tasks
    "get_background_db",
    "run_in_db_context",
    # Repository factories
    "get_person_repository",
    "get_payroll_repository",
    "get_purchase_document_repository",
    "get_sales_document_repository",
    "get_form29_repository",
    "get_tax_document_repository",
    # Repository type aliases
    "PersonRepositoryDep",
    "PayrollRepositoryDep",
    "PurchaseDocumentRepositoryDep",
    "SalesDocumentRepositoryDep",
    "Form29RepositoryDep",
    "TaxDocumentRepositoryDep",
]
