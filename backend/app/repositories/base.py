"""
Base Repository Pattern Implementation.

Provides a generic repository class with common CRUD operations for SQLAlchemy models.
This eliminates code duplication and provides a consistent interface for data access.
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from uuid import UUID

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


# Generic type variable for the model
T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository providing common database operations.

    Usage:
        class PersonRepository(BaseRepository[Person]):
            def __init__(self, db: AsyncSession):
                super().__init__(Person, db)

    Benefits:
        - Eliminates SQL query duplication
        - Provides consistent data access patterns
        - Easy to test with mocks
        - Centralized query optimization
    """

    def __init__(self, model: Type[T], db: AsyncSession):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            db: Async database session
        """
        self.model = model
        self.db = db

    async def get(self, id: UUID) -> Optional[T]:
        """
        Get a single record by ID.

        Args:
            id: Record UUID

        Returns:
            Model instance or None if not found
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """
        Get multiple records with pagination and optional filters.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            filters: Dictionary of field:value filters

        Returns:
            List of model instances
        """
        query = select(self.model)

        # Apply filters if provided
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        """
        Create a new record.

        Args:
            **kwargs: Field values for the new record

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        """
        Update an existing record.

        Args:
            id: Record UUID
            **kwargs: Field values to update

        Returns:
            Updated model instance or None if not found
        """
        instance = await self.get(id)
        if not instance:
            return None

        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: UUID) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Record UUID

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get(id)
        if not instance:
            return False

        await self.db.delete(instance)
        await self.db.flush()
        return True

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filters.

        Args:
            filters: Dictionary of field:value filters

        Returns:
            Number of matching records
        """
        query = select(func.count(self.model.id))

        # Apply filters if provided
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def exists(self, id: UUID) -> bool:
        """
        Check if a record exists by ID.

        Args:
            id: Record UUID

        Returns:
            True if exists, False otherwise
        """
        result = await self.db.execute(
            select(func.count(self.model.id)).where(self.model.id == id)
        )
        return result.scalar_one() > 0

    def _build_query(self, **filters) -> Select:
        """
        Build a base query with filters.

        Helper method for subclasses to build custom queries.

        Args:
            **filters: Field:value filters

        Returns:
            SQLAlchemy Select statement
        """
        query = select(self.model)

        for field, value in filters.items():
            if hasattr(self.model, field):
                if value is not None:
                    query = query.where(getattr(self.model, field) == value)

        return query
