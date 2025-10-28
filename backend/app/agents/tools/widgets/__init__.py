"""ChatKit widgets (legacy)."""

from .widgets import (
    TaxSummaryWidget,
    DocumentDetailWidget,
    CalendarEventWidget,
    ContactCardWidget,
)
from .tax_widget_tools import get_tax_widget_tools

__all__ = [
    "TaxSummaryWidget",
    "DocumentDetailWidget",
    "CalendarEventWidget",
    "ContactCardWidget",
    "get_tax_widget_tools",
]
