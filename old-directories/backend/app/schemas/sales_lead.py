"""Pydantic schemas for sales lead contact forms."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SalesLeadCreate(BaseModel):
    """Schema for creating a new sales lead (contact form submission)."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Juan Pérez",
            "email": "juan@example.com",
            "phone": "+56912345678",
            "company_name": "Mi Empresa SpA",
            "message": "Estoy interesado en conocer más sobre Fizko para mi empresa",
            "source": "landing_page",
        }
    })

    name: str = Field(..., min_length=1, max_length=255, description="Contact's full name")
    email: EmailStr = Field(..., description="Contact's email address")
    phone: Optional[str] = Field(None, max_length=50, description="Contact's phone number")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    message: Optional[str] = Field(None, max_length=2000, description="Contact message")
    source: str = Field(default="landing_page", description="Source of the lead")


class SalesLeadResponse(BaseModel):
    """Schema for sales lead response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    phone: Optional[str]
    company_name: Optional[str]
    message: Optional[str]
    source: str
    status: str
    created_at: datetime
    updated_at: datetime


class SalesLeadUpdate(BaseModel):
    """Schema for updating a sales lead (admin only)."""

    status: Optional[str] = Field(
        None,
        pattern="^(new|contacted|qualified|converted|rejected)$",
        description="Lead status",
    )
    message: Optional[str] = Field(None, max_length=2000, description="Additional notes")
