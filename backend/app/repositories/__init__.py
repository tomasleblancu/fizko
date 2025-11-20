"""
Repositories Module - Modular data access layer for Supabase.

This module provides domain-specific repositories for database access,
replacing the monolithic SupabaseClient approach.

Architecture:
- Each repository handles queries for a specific domain
- BaseRepository provides common functionality and error handling
- Repositories receive a Supabase client instance at initialization
- All methods use async/await for consistency

Usage:
    from app.repositories import ContactsRepository
    from app.config.supabase import get_supabase_client

    supabase = get_supabase_client()
    contacts_repo = ContactsRepository(supabase._client)

    contact = await contacts_repo.get_by_rut(company_id, rut)
"""

from .base import BaseRepository
from .calendar import CalendarRepository
from .companies import CompaniesRepository
from .contacts import ContactsRepository
from .documents import DocumentsRepository
from .expenses import ExpensesRepository
from .f29 import F29Repository
from .feedback import FeedbackRepository
from .honorarios import HonorariosRepository
from .notifications import NotificationsRepository
from .people import PeopleRepository
from .tax_summaries import TaxSummariesRepository

__all__ = [
    "BaseRepository",
    "CalendarRepository",
    "CompaniesRepository",
    "ContactsRepository",
    "DocumentsRepository",
    "ExpensesRepository",
    "F29Repository",
    "FeedbackRepository",
    "HonorariosRepository",
    "NotificationsRepository",
    "PeopleRepository",
    "TaxSummariesRepository",
]
