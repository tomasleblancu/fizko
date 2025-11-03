"""UI Tools - Specific implementations for each UI component."""

# Import all tools to trigger auto-registration via @ui_tool_registry.register decorator
from .contact_card import ContactCardTool
from .document_detail import DocumentDetailTool
from .notification_calendar_event import NotificationCalendarEventTool
from .notification_generic import NotificationGenericTool
from .person_detail import PersonDetailTool
from .tax_calendar_event import TaxCalendarEventTool
from .tax_summary_expenses import TaxSummaryExpensesTool
from .tax_summary_iva import TaxSummaryIVATool
from .tax_summary_revenue import TaxSummaryRevenueTool

__all__ = [
    "ContactCardTool",
    "DocumentDetailTool",
    "NotificationCalendarEventTool",
    "NotificationGenericTool",
    "PersonDetailTool",
    "TaxCalendarEventTool",
    "TaxSummaryIVATool",
    "TaxSummaryRevenueTool",
    "TaxSummaryExpensesTool",
]
