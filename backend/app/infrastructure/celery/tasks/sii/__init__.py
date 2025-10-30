"""
SII (Servicio de Impuestos Internos) Celery tasks.

This module contains all Celery tasks related to SII operations:
- Document synchronization (purchases, sales) - documents.py
- Form processing (F29, F22, etc.) - forms.py
- Company operations (contribuyente info, DTE, etc.) - company.py
"""
from .documents import sync_documents, sync_documents_all_companies
from .forms import (
    sync_f29,
    sync_f29_all_companies,
    sync_f29_pdfs_missing,
    sync_f29_pdfs_missing_all_companies,
)

__all__ = [
    # Document tasks
    "sync_documents",
    "sync_documents_all_companies",
    # Form tasks
    "sync_f29",
    "sync_f29_all_companies",
    # F29 PDF download tasks
    "sync_f29_pdfs_missing",
    "sync_f29_pdfs_missing_all_companies",
]
