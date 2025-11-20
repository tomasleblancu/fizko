"""Repository for person (employee) management."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.personnel import Person
from app.repositories.base import BaseRepository


class PersonRepository(BaseRepository[Person]):
    """Repository for managing Person (employee) records."""

    def __init__(self, db: AsyncSession):
        super().__init__(Person, db)

    async def find_by_company(
        self,
        company_id: UUID,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Person]:
        """
        Find people by company with optional filters.

        Args:
            company_id: Company UUID
            status: Filter by status (active, inactive, terminated)
            search: Search in name, lastname, or RUT
            skip: Pagination offset
            limit: Max results

        Returns:
            List of Person instances
        """
        query = select(Person).where(Person.company_id == company_id)

        # Filter by status
        if status:
            query = query.where(Person.status == status)

        # Search in multiple fields
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Person.first_name.ilike(search_pattern),
                    Person.last_name.ilike(search_pattern),
                    Person.rut.ilike(search_pattern),
                    Person.email.ilike(search_pattern)
                )
            )

        # Pagination and ordering
        query = query.order_by(Person.first_name, Person.last_name)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_by_rut(
        self,
        company_id: UUID,
        rut: str
    ) -> Optional[Person]:
        """
        Find a person by RUT within a company.

        Args:
            company_id: Company UUID
            rut: Chilean RUT (will be normalized)

        Returns:
            Person instance or None
        """
        # Normalize RUT (remove dots, normalize format)
        normalized_rut = rut.replace(".", "").replace("-", "").upper()

        query = select(Person).where(
            Person.company_id == company_id,
            Person.rut.ilike(f"%{normalized_rut}%")
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def count_by_status(self, company_id: UUID) -> dict:
        """
        Count people grouped by status.

        Args:
            company_id: Company UUID

        Returns:
            Dictionary with status as key and count as value
        """
        query = select(
            Person.status,
            func.count(Person.id).label('count')
        ).where(
            Person.company_id == company_id
        ).group_by(Person.status)

        result = await self.db.execute(query)
        return {row.status: row.count for row in result}

    async def get_active_count(self, company_id: UUID) -> int:
        """
        Get count of active employees.

        Args:
            company_id: Company UUID

        Returns:
            Number of active employees
        """
        query = select(func.count(Person.id)).where(
            Person.company_id == company_id,
            Person.status == 'active'
        )

        result = await self.db.execute(query)
        return result.scalar_one()

    async def update_status(
        self,
        person_id: UUID,
        status: str,
        termination_date: Optional[str] = None,
        termination_reason: Optional[str] = None
    ) -> Optional[Person]:
        """
        Update person status (used for terminations, reactivations).

        Args:
            person_id: Person UUID
            status: New status
            termination_date: Date of termination (if applicable)
            termination_reason: Reason for termination (if applicable)

        Returns:
            Updated Person instance or None
        """
        person = await self.get(person_id)
        if not person:
            return None

        person.status = status
        if termination_date:
            person.termination_date = termination_date
        if termination_reason:
            person.termination_reason = termination_reason

        await self.db.flush()
        await self.db.refresh(person)
        return person
