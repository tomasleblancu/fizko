"""
FastAPI dependencies for Fizko.

Organized by domain for easy imports and maintenance.

This module provides dependencies for:
- Authentication and authorization (auth.py)
- Database session management (database.py)
- Company resolution (company.py)
- Repository injection (repositories.py)
- Subscription and feature access (subscription.py)
"""

from __future__ import annotations

# =============================================================================
# Auth Dependencies
# =============================================================================

# Import get_current_user from core.auth for backward compatibility
from ..core.auth import get_current_user

from .auth import (
    get_current_active_user,
    get_current_user_id,
    require_auth,
    CurrentUserDep,
    CurrentUserIdDep,
)

# =============================================================================
# Database Dependencies
# =============================================================================

from .database import (
    get_db_session,
    get_background_db,
    run_in_db_context,
    DbSessionDep,
)

# =============================================================================
# Company Resolution
# =============================================================================

from .company import (
    get_user_company_id,
    CompanyIdDep,
)

# =============================================================================
# Repository Dependencies
# =============================================================================

from .repositories import (
    # Factory functions
    get_person_repository,
    get_payroll_repository,
    get_purchase_document_repository,
    get_sales_document_repository,
    get_form29_repository,
    get_tax_document_repository,
    # Type aliases
    PersonRepositoryDep,
    PayrollRepositoryDep,
    PurchaseDocumentRepositoryDep,
    SalesDocumentRepositoryDep,
    Form29RepositoryDep,
    TaxDocumentRepositoryDep,
)

# =============================================================================
# Subscription Dependencies
# =============================================================================

from .subscription import (
    # Service
    get_subscription_service,
    SubscriptionServiceDep,
    # Global subscription check
    get_subscription_or_none,
    require_active_subscription,
    ActiveSubscriptionDep,
    # Factories
    require_feature,
    check_usage_limit,
    # Pre-configured feature checks
    require_whatsapp,
    require_ai_assistant,
    require_advanced_reports,
    require_api_access,
    # Pre-configured limit checks
    check_transaction_limit,
    check_user_limit,
    check_api_call_limit,
    check_whatsapp_limit,
    # Helpers
    get_subscription_info,
)


__all__ = [
    # Auth
    "get_current_user",  # Re-exported from core.auth for backward compatibility
    "get_current_active_user",
    "get_current_user_id",
    "require_auth",
    "CurrentUserDep",
    "CurrentUserIdDep",
    # Database
    "get_db_session",
    "get_background_db",
    "run_in_db_context",
    "DbSessionDep",
    # Company
    "get_user_company_id",
    "CompanyIdDep",
    # Repositories
    "get_person_repository",
    "get_payroll_repository",
    "get_purchase_document_repository",
    "get_sales_document_repository",
    "get_form29_repository",
    "get_tax_document_repository",
    "PersonRepositoryDep",
    "PayrollRepositoryDep",
    "PurchaseDocumentRepositoryDep",
    "SalesDocumentRepositoryDep",
    "Form29RepositoryDep",
    "TaxDocumentRepositoryDep",
    # Subscription
    "get_subscription_service",
    "SubscriptionServiceDep",
    "get_subscription_or_none",
    "require_active_subscription",
    "ActiveSubscriptionDep",
    "require_feature",
    "check_usage_limit",
    "require_whatsapp",
    "require_ai_assistant",
    "require_advanced_reports",
    "require_api_access",
    "check_transaction_limit",
    "check_user_limit",
    "check_api_call_limit",
    "check_whatsapp_limit",
    "get_subscription_info",
]
