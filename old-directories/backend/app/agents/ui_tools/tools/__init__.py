"""UI Tools - Specific implementations for each UI component."""

# Import all tools to trigger auto-registration via @ui_tool_registry.register decorator
from .add_employee_button import AddEmployeeButtonTool
from .contact_card import ContactCardTool
from .document_detail import DocumentDetailTool
from .f29_form_card import F29FormCardTool
from .notification_calendar_event import NotificationCalendarEventTool
from .notification_generic import NotificationGenericTool
from .pay_latest_f29 import PayLatestF29Tool
from .person_detail import PersonDetailTool
from .tax_calendar_event import TaxCalendarEventTool
from .tax_summary_expenses import TaxSummaryExpensesTool
from .tax_summary_iva import TaxSummaryIVATool
from .tax_summary_revenue import TaxSummaryRevenueTool

__all__ = [
    "AddEmployeeButtonTool",
    "ContactCardTool",
    "DocumentDetailTool",
    "F29FormCardTool",
    "NotificationCalendarEventTool",
    "NotificationGenericTool",
    "PayLatestF29Tool",
    "PersonDetailTool",
    "TaxCalendarEventTool",
    "TaxSummaryIVATool",
    "TaxSummaryRevenueTool",
    "TaxSummaryExpensesTool",
]
