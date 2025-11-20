"""API endpoints for managing people (employees)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...schemas.personnel import (
    Person as PersonSchema,
    PersonCreate,
    PersonListResponse,
    PersonUpdate,
)
from ...utils.company_resolver import get_user_primary_company_id
from ...dependencies import get_current_user_id
from ...services.personnel import PersonService

router = APIRouter()


def get_person_service(db: AsyncSession = Depends(get_db)) -> PersonService:
    """
    Dependency to get PersonService instance.

    Args:
        db: Database session from dependency injection

    Returns:
        PersonService instance
    """
    return PersonService(db)


@router.post("/", response_model=PersonSchema, status_code=status.HTTP_201_CREATED)
async def create_person(
    person_data: PersonCreate,
    service: PersonService = Depends(get_person_service),
):
    """
    Create a new employee.

    Creates a new person (employee) record for a company.
    """
    return await service.create_person(person_data)


@router.get("/", response_model=PersonListResponse)
async def list_people(
    company_id: Optional[UUID] = Query(None, description="Company ID (optional, resolved from user if not provided)"),
    status: Optional[str] = Query(None, description="Filter by status (active, inactive, terminated)"),
    search: Optional[str] = Query(None, description="Search by name or RUT"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    service: PersonService = Depends(get_person_service),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    List all people (employees) for a company.

    Returns a paginated list of employees with optional filtering.
    """
    # Resolve company_id from user's active session if not provided
    if company_id is None:
        company_id = await get_user_primary_company_id(user_id, db)
        if not company_id:
            raise HTTPException(
                status_code=404,
                detail="No active company found for user"
            )

    people, total = await service.list_people(
        company_id=company_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )

    return PersonListResponse(
        data=people,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{person_id}", response_model=PersonSchema)
async def get_person(
    person_id: UUID,
    service: PersonService = Depends(get_person_service),
):
    """
    Get a single person by ID.

    Returns detailed information about a specific employee.
    """
    return await service.get_person_by_id(person_id)


@router.patch("/{person_id}", response_model=PersonSchema)
async def update_person(
    person_id: UUID,
    person_data: PersonUpdate,
    service: PersonService = Depends(get_person_service),
):
    """
    Update a person's information.

    Updates an existing employee record. Only provided fields will be updated.
    """
    return await service.update_person(person_id, person_data)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: UUID,
    service: PersonService = Depends(get_person_service),
):
    """
    Delete a person.

    Permanently deletes an employee record. This will also delete all associated payroll records.
    """
    await service.delete_person(person_id)
    return None
