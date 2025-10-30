"""ChatKit widgets (legacy)."""

# Re-export widget creation functions
from .widgets import (
    create_tax_calculation_widget,
    create_document_detail_widget,
    create_person_confirmation_widget,
)

# Re-export widget tools
from .tax_widget_tools import (
    show_tax_calculation_widget,
    show_document_detail_widget,
)
from .payroll_widget_tools import (
    show_person_confirmation,
)

__all__ = [
    "create_tax_calculation_widget",
    "create_document_detail_widget",
    "create_person_confirmation_widget",
    "show_tax_calculation_widget",
    "show_document_detail_widget",
    "show_person_confirmation",
]
