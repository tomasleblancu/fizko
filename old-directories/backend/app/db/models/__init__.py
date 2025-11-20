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
from .brain import CompanyBrain, UserBrain
from .calendar import CalendarEvent, CompanyEvent, EventDependency, EventHistory, EventTask, EventTemplate
from .chat import ChatKitAttachment, Conversation, Message
from .company import Company, CompanyTaxInfo, CompanySettings
from .contact import Contact
from .documents import PurchaseDocument, SalesDocument
from .expenses import Expense, ExpenseCategory, ExpenseStatus
from .feedback import Feedback, FeedbackCategory, FeedbackPriority, FeedbackStatus
from .form29 import Form29
from .honorarios import HonorariosReceipt
from .form29_sii_download import Form29SIIDownload
from .notifications import (
    NotificationEventTrigger,
    NotificationHistory,
    NotificationSubscription,
    NotificationTemplate,
    ScheduledNotification,
    UserNotificationPreference,
)
from .personnel import Payroll, Person
from .phone_verification import PhoneVerification
from .sales_lead import SalesLead
from .scheduled_tasks import (
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    PeriodicTaskChanged,
    TaskResult,
    create_crontab_schedule,
    create_interval_schedule,
)
from .session import Session
from .subscriptions import Invoice, Subscription, SubscriptionPlan, SubscriptionUsage
from .user import Profile

__all__ = [
    # Base
    "Base",
    # User
    "Profile",
    # Company
    "Company",
    "CompanyTaxInfo",
    "CompanySettings",
    # Brain (Memory)
    "UserBrain",
    "CompanyBrain",
    # Session
    "Session",
    # Contacts
    "Contact",
    # Documents
    "PurchaseDocument",
    "SalesDocument",
    "HonorariosReceipt",
    # Expenses
    "Expense",
    "ExpenseCategory",
    "ExpenseStatus",
    # Feedback
    "Feedback",
    "FeedbackCategory",
    "FeedbackStatus",
    "FeedbackPriority",
    # Form29
    "Form29",
    "Form29SIIDownload",
    # Chat
    "Conversation",
    "Message",
    "ChatKitAttachment",
    # Calendar
    "EventTemplate",
    "CompanyEvent",
    "CalendarEvent",
    "EventTask",
    "EventDependency",
    "EventHistory",
    # Personnel
    "Person",
    "Payroll",
    # Phone Verification
    "PhoneVerification",
    # Sales Leads
    "SalesLead",
    # Notifications
    "NotificationTemplate",
    "NotificationSubscription",
    "ScheduledNotification",
    "NotificationHistory",
    "NotificationEventTrigger",
    "UserNotificationPreference",
    # Celery Beat Scheduled Tasks
    "IntervalSchedule",
    "CrontabSchedule",
    "PeriodicTask",
    "PeriodicTaskChanged",
    "TaskResult",
    "create_interval_schedule",
    "create_crontab_schedule",
    # Subscriptions
    "SubscriptionPlan",
    "Subscription",
    "SubscriptionUsage",
    "Invoice",
]
