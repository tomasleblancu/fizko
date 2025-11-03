"""
Repository Pattern Implementation.

Provides clean data access layer with:
- Centralized SQL queries
- Consistent interfaces
- Easy testing
- Query optimization

Usage:
    from app.repositories.personnel import PersonRepository
    from app.repositories.tax import TaxDocumentRepository
    from app.repositories.core import CompanyRepository

    repo = PersonRepository(db)
    people = await repo.find_by_company(company_id)
"""

from .base import BaseRepository
from .contacts import ContactRepository
from .core import (
    CompanyRepository,
    NotificationTemplateRepository,
    NotificationSubscriptionRepository,
    UserNotificationPreferenceRepository
)
from .personnel import PersonRepository, PayrollRepository
from .tax import (
    PurchaseDocumentRepository,
    SalesDocumentRepository,
    Form29Repository,
    TaxDocumentRepository
)

__all__ = [
    # Base
    "BaseRepository",
    # Contacts
    "ContactRepository",
    # Core
    "CompanyRepository",
    "NotificationTemplateRepository",
    "NotificationSubscriptionRepository",
    "UserNotificationPreferenceRepository",
    # Personnel
    "PersonRepository",
    "PayrollRepository",
    # Tax
    "PurchaseDocumentRepository",
    "SalesDocumentRepository",
    "Form29Repository",
    "TaxDocumentRepository",
]
