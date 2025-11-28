"""
Supabase Client Configuration for Backend V2.

This module provides a Supabase client with access to domain-specific repositories.
Uses the repository pattern for modular, organized database access.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client
    from app.repositories import (
        CalendarRepository,
        CompaniesRepository,
        ContactsRepository,
        DocumentsRepository,
        ExpensesRepository,
        F29Repository,
        FeedbackRepository,
        HonorariosRepository,
        NotificationsRepository,
        PeopleRepository,
        TaxSummariesRepository,
    )

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Supabase client with domain-specific repositories.

    Provides organized access to database operations through specialized repositories.
    Each repository handles queries for a specific domain (contacts, documents, etc.).

    Usage:
        supabase = get_supabase_client()

        # Access repositories
        contact = await supabase.contacts.get_by_rut(company_id, rut)
        sales = await supabase.documents.get_recent_sales(company_id)
        summary = await supabase.tax_summaries.get_iva_summary(company_id)
    """

    def __init__(self):
        """Initialize Supabase client and repositories from environment variables."""
        try:
            from supabase import create_client, ClientOptions

            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

            if not supabase_url or not supabase_key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_ANON_KEY) "
                    "must be set in environment variables"
                )

            # Configure client options with explicit headers
            options = ClientOptions(
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )

            self._client: Client = create_client(supabase_url, supabase_key, options=options)

            # Initialize repositories (lazy loaded on first access)
            self._calendar_repo: CalendarRepository | None = None
            self._companies_repo: CompaniesRepository | None = None
            self._contacts_repo: ContactsRepository | None = None
            self._documents_repo: DocumentsRepository | None = None
            self._expenses_repo: ExpensesRepository | None = None
            self._f29_repo: F29Repository | None = None
            self._feedback_repo: FeedbackRepository | None = None
            self._honorarios_repo: HonorariosRepository | None = None
            self._notifications_repo: NotificationsRepository | None = None
            self._people_repo: PeopleRepository | None = None
            self._tax_summaries_repo: TaxSummariesRepository | None = None

            logger.info("✅ Supabase client initialized successfully")

        except ImportError:
            logger.error(
                "❌ supabase-py not installed. "
                "Install with: uv pip install supabase"
            )
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise

    @property
    def client(self) -> Client:
        """Get the underlying Supabase client."""
        return self._client

    @property
    def calendar(self) -> CalendarRepository:
        """Get the calendar repository."""
        if self._calendar_repo is None:
            from app.repositories import CalendarRepository
            self._calendar_repo = CalendarRepository(self._client)
        return self._calendar_repo

    @property
    def companies(self) -> CompaniesRepository:
        """Get the companies repository."""
        if self._companies_repo is None:
            from app.repositories import CompaniesRepository
            self._companies_repo = CompaniesRepository(self._client)
        return self._companies_repo

    @property
    def contacts(self) -> ContactsRepository:
        """Get the contacts repository."""
        if self._contacts_repo is None:
            from app.repositories import ContactsRepository
            self._contacts_repo = ContactsRepository(self._client)
        return self._contacts_repo

    @property
    def documents(self) -> DocumentsRepository:
        """Get the documents repository."""
        if self._documents_repo is None:
            from app.repositories import DocumentsRepository
            self._documents_repo = DocumentsRepository(self._client)
        return self._documents_repo

    @property
    def expenses(self) -> ExpensesRepository:
        """Get the expenses repository."""
        if self._expenses_repo is None:
            from app.repositories import ExpensesRepository
            self._expenses_repo = ExpensesRepository(self._client)
        return self._expenses_repo

    @property
    def f29(self) -> F29Repository:
        """Get the F29 repository."""
        if self._f29_repo is None:
            from app.repositories import F29Repository
            self._f29_repo = F29Repository(self._client)
        return self._f29_repo

    @property
    def honorarios(self) -> HonorariosRepository:
        """Get the honorarios repository."""
        if self._honorarios_repo is None:
            from app.repositories import HonorariosRepository
            self._honorarios_repo = HonorariosRepository(self._client)
        return self._honorarios_repo

    @property
    def notifications(self) -> NotificationsRepository:
        """Get the notifications repository."""
        if self._notifications_repo is None:
            from app.repositories import NotificationsRepository
            self._notifications_repo = NotificationsRepository(self._client)
        return self._notifications_repo

    @property
    def people(self) -> PeopleRepository:
        """Get the people repository."""
        if self._people_repo is None:
            from app.repositories import PeopleRepository
            self._people_repo = PeopleRepository(self._client)
        return self._people_repo

    @property
    def feedback(self) -> FeedbackRepository:
        """Get the feedback repository."""
        if self._feedback_repo is None:
            from app.repositories import FeedbackRepository
            self._feedback_repo = FeedbackRepository(self._client)
        return self._feedback_repo

    @property
    def tax_summaries(self) -> TaxSummariesRepository:
        """Get the tax summaries repository."""
        if self._tax_summaries_repo is None:
            from app.repositories import TaxSummariesRepository
            self._tax_summaries_repo = TaxSummariesRepository(self._client)
        return self._tax_summaries_repo


# Singleton instance
_supabase_client: SupabaseClient | None = None


def get_supabase_client() -> SupabaseClient:
    """
    Get the singleton Supabase client instance.

    Returns:
        SupabaseClient instance with access to all repositories
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
