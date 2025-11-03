"""
Centralized Pydantic schemas for the application.

This module consolidates all request/response schemas for FastAPI endpoints.
Following best practices, schemas are organized by domain and separated from
routers to improve:
- Code reusability
- Testing capability
- API documentation
- Type safety

Usage:
    from app.schemas.calendar import CreateEventTemplateRequest
    from app.schemas.notifications import CreateNotificationTemplateRequest
    from app.schemas.tax import Form29Create, PurchaseDocumentCreate
    from app.schemas.personnel import PersonCreate, PayrollCreate
"""

# Re-export commonly used schemas for convenience
from .personnel import (
    Person,
    PersonCreate,
    PersonUpdate,
    Payroll,
    PayrollCreate,
    PayrollUpdate,
)

__all__ = [
    # Personnel
    "Person",
    "PersonCreate",
    "PersonUpdate",
    "Payroll",
    "PayrollCreate",
    "PayrollUpdate",
]
