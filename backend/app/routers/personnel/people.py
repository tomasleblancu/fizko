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
from ...dependencies import get_current_user_id, PersonRepositoryDep

router = APIRouter()


@router.post("/", response_model=PersonSchema, status_code=status.HTTP_201_CREATED)
async def create_person(
    person_data: PersonCreate,
    repo: PersonRepositoryDep,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new employee.

    Creates a new person (employee) record for a company.
    """
    # Repository injected via Depends
    new_person = await repo.create(**person_data.model_dump())
    await db.commit()

    return new_person


@router.get("/", response_model=PersonListResponse)
async def list_people(
    repo: PersonRepositoryDep,
    company_id: Optional[UUID] = Query(None, description="Company ID (optional, resolved from user if not provided)"),
    status: Optional[str] = Query(None, description="Filter by status (active, inactive, terminated)"),
    search: Optional[str] = Query(None, description="Search by name or RUT"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
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

    # Use repository for clean data access
    # Repository injected via Depends
    skip = (page - 1) * page_size

    people = await repo.find_by_company(
        company_id=company_id,
        status=status,
        search=search,
        skip=skip,
        limit=page_size
    )

    # Get total count for pagination
    total = await repo.count(filters={'company_id': company_id})

    return PersonListResponse(
        data=people,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{person_id}", response_model=PersonSchema)
async def get_person(
    person_id: UUID,
    repo: PersonRepositoryDep,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single person by ID.

    Returns detailed information about a specific employee.
    """
    # Repository injected via Depends
    person = await repo.get(person_id)

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )

    return person


@router.patch("/{person_id}", response_model=PersonSchema)
async def update_person(
    person_id: UUID,
    person_data: PersonUpdate,
    repo: PersonRepositoryDep,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a person's information.

    Updates an existing employee record. Only provided fields will be updated.
    """
    # Repository injected via Depends
    update_data = person_data.model_dump(exclude_unset=True)

    person = await repo.update(person_id, **update_data)

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )

    await db.commit()

    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: UUID,
    repo: PersonRepositoryDep,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a person.

    Permanently deletes an employee record. This will also delete all associated payroll records.
    """
    # Repository injected via Depends
    deleted = await repo.delete(person_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )

    await db.commit()

    return None
