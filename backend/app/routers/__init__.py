"""API routers for Fizko platform.

Routers are organized by domain:
- auth: Authentication and user profiles
- companies: Company management
- tax: Tax documents and forms
- chat: Conversations and ChatKit AI agent
- whatsapp: WhatsApp integration
- admin: Administrative functions
- sii: SII (Chilean tax authority) integration
- contacts: Business contacts (providers and clients)
"""

# Import router modules
from . import admin, auth, chat, companies, contacts, sii, tax, whatsapp

# Re-export individual routers for backward compatibility
from .admin import admin as admin_router
from .admin import calendar
from .auth import profile, sessions
from .chat import chatkit, conversations
from .companies import companies as companies_router, settings as company_settings
from .tax import documents as tax_documents
from .tax import form29, purchases as purchase_documents, sales as sales_documents
from .tax import summary as tax_summary
from .whatsapp import main as whatsapp

__all__ = [
    # Domain modules
    "auth",
    "companies",
    "tax",
    "chat",
    "whatsapp",
    "admin",
    "sii",
    "contacts",
    # Individual routers (backward compatibility)
    "admin_router",
    "calendar",
    "chatkit",
    "companies_router",
    "company_settings",
    "contacts",
    "conversations",
    "form29",
    "profile",
    "purchase_documents",
    "sales_documents",
    "sessions",
    "tax_documents",
    "tax_summary",
]
