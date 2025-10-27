"""API endpoints for managing people (employees)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import Person
from ...schemas.personnel import (
    Person as PersonSchema,
    PersonCreate,
    PersonListResponse,
    PersonUpdate,
)

router = APIRouter()


@router.post("/", response_model=PersonSchema, status_code=status.HTTP_201_CREATED)
async def create_person(
    person_data: PersonCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new employee.

    Creates a new person (employee) record for a company.
    """
    # Create new person
    new_person = Person(**person_data.model_dump())

    db.add(new_person)
    await db.commit()
    await db.refresh(new_person)

    return new_person


@router.get("/", response_model=PersonListResponse)
async def list_people(
    company_id: UUID = Query(..., description="Company ID to filter by"),
    status: Optional[str] = Query(None, description="Filter by status (active, inactive, terminated)"),
    search: Optional[str] = Query(None, description="Search by name or RUT"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all people (employees) for a company.

    Returns a paginated list of employees with optional filtering.
    """
    # Build base query
    query = select(Person).where(Person.company_id == company_id)

    # Apply filters
    if status:
        query = query.where(Person.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Person.first_name.ilike(search_term))
            | (Person.last_name.ilike(search_term))
            | (Person.rut.ilike(search_term))
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Person.first_name, Person.last_name)

    # Execute query
    result = await db.execute(query)
    people = result.scalars().all()

    return PersonListResponse(
        data=people,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{person_id}", response_model=PersonSchema)
async def get_person(
    person_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single person by ID.

    Returns detailed information about a specific employee.
    """
    query = select(Person).where(Person.id == person_id)
    result = await db.execute(query)
    person = result.scalar_one_or_none()

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
    db: AsyncSession = Depends(get_db),
):
    """
    Update a person's information.

    Updates an existing employee record. Only provided fields will be updated.
    """
    # Get existing person
    query = select(Person).where(Person.id == person_id)
    result = await db.execute(query)
    person = result.scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )

    # Update fields
    update_data = person_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(person, field, value)

    await db.commit()
    await db.refresh(person)

    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a person.

    Permanently deletes an employee record. This will also delete all associated payroll records.
    """
    # Get existing person
    query = select(Person).where(Person.id == person_id)
    result = await db.execute(query)
    person = result.scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )

    await db.delete(person)
    await db.commit()

    return None
