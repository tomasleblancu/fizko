"""
Person Service - Business logic for employee management.

This service layer encapsulates all business logic for person (employee) operations,
using repositories for data access.
"""

from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Person
from app.repositories.personnel import PersonRepository
from app.schemas.personnel import PersonCreate, PersonUpdate


class PersonService:
    """
    Service for managing employee (person) operations.

    Handles all business logic related to employees including:
    - Creation
    - Updates
    - Deletion
    - Querying with filters
    - Status management
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the person service.

        Args:
            db: Database session
        """
        self.db = db
        self.person_repo = PersonRepository(db)

    async def create_person(self, person_data: PersonCreate) -> Person:
        """
        Create a new employee.

        Args:
            person_data: Person creation data

        Returns:
            Created Person instance
        """
        new_person = await self.person_repo.create(**person_data.model_dump())
        await self.db.commit()
        await self.db.refresh(new_person)

        return new_person

    async def list_people(
        self,
        company_id: UUID,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[list[Person], int]:
        """
        List employees with filtering and pagination.

        Args:
            company_id: Company ID to filter by
            status: Optional status filter (active, inactive, terminated)
            search: Optional search term for name or RUT
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (people_records, total_count)
        """
        skip = (page - 1) * page_size

        # Get people records
        people = await self.person_repo.find_by_company(
            company_id=company_id,
            status=status,
            search=search,
            skip=skip,
            limit=page_size,
        )

        # Get total count
        total = await self.person_repo.count(
            filters={'company_id': company_id}
        )

        return people, total

    async def get_person_by_id(self, person_id: UUID) -> Person:
        """
        Get a single employee by ID.

        Args:
            person_id: Person UUID

        Returns:
            Person instance

        Raises:
            HTTPException: If person not found
        """
        person = await self.person_repo.get(person_id)

        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found",
            )

        return person

    async def update_person(
        self,
        person_id: UUID,
        person_data: PersonUpdate,
    ) -> Person:
        """
        Update an employee's information.

        Args:
            person_id: Person UUID
            person_data: Fields to update

        Returns:
            Updated Person instance

        Raises:
            HTTPException: If person not found
        """
        update_data = person_data.model_dump(exclude_unset=True)

        person = await self.person_repo.update(person_id, **update_data)

        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found",
            )

        await self.db.commit()
        await self.db.refresh(person)

        return person

    async def delete_person(self, person_id: UUID) -> None:
        """
        Delete an employee.

        This will also delete all associated payroll records due to cascading.

        Args:
            person_id: Person UUID

        Raises:
            HTTPException: If person not found
        """
        deleted = await self.person_repo.delete(person_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found",
            )

        await self.db.commit()

    async def update_person_status(
        self,
        person_id: UUID,
        new_status: str,
        termination_date: Optional[str] = None,
        termination_reason: Optional[str] = None,
    ) -> Person:
        """
        Update employee status (for terminations, reactivations).

        Args:
            person_id: Person UUID
            new_status: New status (active, inactive, terminated)
            termination_date: Date of termination (if applicable)
            termination_reason: Reason for termination (if applicable)

        Returns:
            Updated Person instance

        Raises:
            HTTPException: If person not found
        """
        person = await self.person_repo.update_status(
            person_id=person_id,
            status=new_status,
            termination_date=termination_date,
            termination_reason=termination_reason,
        )

        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found",
            )

        await self.db.commit()
        await self.db.refresh(person)

        return person

    async def get_active_count(self, company_id: UUID) -> int:
        """
        Get count of active employees.

        Args:
            company_id: Company UUID

        Returns:
            Number of active employees
        """
        return await self.person_repo.get_active_count(company_id)

    async def count_by_status(self, company_id: UUID) -> dict:
        """
        Count employees grouped by status.

        Args:
            company_id: Company UUID

        Returns:
            Dictionary with status as key and count as value
        """
        return await self.person_repo.count_by_status(company_id)
