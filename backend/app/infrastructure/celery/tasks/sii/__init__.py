"""
SII (Servicio de Impuestos Internos) Celery tasks for Backend V2.

This module contains all Celery tasks related to SII operations:
- Document synchronization (purchases, sales) - documents.py
- Form processing (F29, F22, etc.) - forms.py

Key differences from original backend:
- Uses Supabase client instead of SQLAlchemy
- All database operations go through repositories
- No direct SQL queries in task code
"""
from .documents import sync_documents, sync_documents_all_companies
from .forms import (
    sync_f29,
    sync_f29_all_companies,
    download_f29_pdf,
    download_all_pending_f29_pdfs,
)

__all__ = [
    # Document tasks
    "sync_documents",
    "sync_documents_all_companies",
    # Form tasks
    "sync_f29",
    "sync_f29_all_companies",
    "download_f29_pdf",
    "download_all_pending_f29_pdfs",
]
