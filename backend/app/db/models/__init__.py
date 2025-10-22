"""SQLAlchemy models for Fizko tax/accounting platform.

This module contains all database models for the Fizko application, designed to support
multi-company tax and accounting operations. The architecture separates concerns between
user profiles, company information, tax data, and session management.

Key Design Principles:
- Users can access multiple companies through Sessions
- Company information is split between basic info (Company) and tax-specific data (CompanyTaxInfo)
- Tax documents are separated into purchases (received) and sales (issued)
- Form29 represents monthly IVA declarations
- All monetary amounts use Numeric(15, 2) for precision
- JSONB fields store flexible metadata and session data
"""

from .base import Base
from .chat import ChatKitAttachment, Conversation, Message
from .company import Company, CompanyTaxInfo
from .documents import PurchaseDocument, SalesDocument
from .form29 import Form29
from .session import Session
from .user import Profile

__all__ = [
    # Base
    "Base",
    # User
    "Profile",
    # Company
    "Company",
    "CompanyTaxInfo",
    # Session
    "Session",
    # Documents
    "PurchaseDocument",
    "SalesDocument",
    # Form29
    "Form29",
    # Chat
    "Conversation",
    "Message",
    "ChatKitAttachment",
]
