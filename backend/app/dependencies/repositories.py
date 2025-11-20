"""
Repository dependency injection factories - Stub for Backend V2.

Backend-v2 uses Supabase directly, not SQLAlchemy repositories.
This file exists for compatibility but shouldn't be used.
"""

from typing import Annotated

from fastapi import Depends


# Stub function - not used in backend-v2
def get_db():
    """Stub - backend-v2 uses Supabase directly."""
    raise NotImplementedError("Use get_supabase_client() instead")


# All repository dependencies are stubs in backend-v2
def get_person_repository():
    """Stub - backend-v2 uses Supabase directly."""
    raise NotImplementedError("Use Supabase client instead")


def get_payroll_repository():
    """Stub - backend-v2 uses Supabase directly."""
    raise NotImplementedError("Use Supabase client instead")


def get_purchase_document_repository():
    """Stub - backend-v2 uses Supabase directly."""
    raise NotImplementedError("Use Supabase client instead")


def get_sales_document_repository():
    """Stub - backend-v2 uses Supabase directly."""
    raise NotImplementedError("Use Supabase client instead")


def get_form29_repository():
    """Stub - backend-v2 uses Supabase directly."""
    raise NotImplementedError("Use Supabase client instead")


def get_tax_document_repository():
    """Stub - backend-v2 uses Supabase directly."""
    raise NotImplementedError("Use Supabase client instead")
