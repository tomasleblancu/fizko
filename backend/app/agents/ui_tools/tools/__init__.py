"""UI Tools - Specific implementations for each UI component.

All tools refactored to use Supabase instead of SQLAlchemy.
"""

# Import all tools to trigger auto-registration via @ui_tool_registry.register decorator
from .contact_card import ContactCardTool
from .add_employee_button import AddEmployeeButtonTool
from .document_detail import DocumentDetailTool
from .f29_form_card import F29FormCardTool
from .notification_calendar_event import NotificationCalendarEventTool
from .notification_generic import NotificationGenericTool
from .pay_latest_f29 import PayLatestF29Tool
from .person_detail import PersonDetailTool
from .tax_calendar_event import TaxCalendarEventTool
from .tax_period_card import TaxPeriodCardTool
from .tax_summary_expenses import TaxSummaryExpensesTool
from .tax_summary_iva import TaxSummaryIVATool
from .tax_summary_revenue import TaxSummaryRevenueTool

__all__ = [
    "ContactCardTool",
    "AddEmployeeButtonTool",
    "DocumentDetailTool",
    "F29FormCardTool",
    "NotificationCalendarEventTool",
    "NotificationGenericTool",
    "PayLatestF29Tool",
    "PersonDetailTool",
    "TaxCalendarEventTool",
    "TaxPeriodCardTool",
    "TaxSummaryIVATool",
    "TaxSummaryRevenueTool",
    "TaxSummaryExpensesTool",
]
