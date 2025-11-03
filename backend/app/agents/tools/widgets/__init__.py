"""
ChatKit Widgets - Rich UI components for agent responses.

Structure:
    builders/       - Widget builder functions (create_*_widget)
        tax_calculation.py    - Tax calculation breakdown widget
        document_detail.py    - Document detail widget
        person_confirmation.py - Person confirmation widget

    tax_widget_tools.py       - Agent tools using tax widgets
    payroll_widget_tools.py   - Agent tools using payroll widgets
"""

# Import from new modular structure
from .builders import (
    create_tax_calculation_widget,
    tax_calculation_widget_copy_text,
    create_document_detail_widget,
    document_detail_widget_copy_text,
    create_person_confirmation_widget,
    person_confirmation_widget_copy_text,
)

# Re-export widget tools (these stay as-is)
from .tax_widget_tools import (
    show_tax_calculation_widget,
    show_document_detail_widget,
)
from .payroll_widget_tools import (
    show_person_confirmation,
)

__all__ = [
    # Widget builders
    "create_tax_calculation_widget",
    "tax_calculation_widget_copy_text",
    "create_document_detail_widget",
    "document_detail_widget_copy_text",
    "create_person_confirmation_widget",
    "person_confirmation_widget_copy_text",
    # Widget tools (agent-facing)
    "show_tax_calculation_widget",
    "show_document_detail_widget",
    "show_person_confirmation",
]
