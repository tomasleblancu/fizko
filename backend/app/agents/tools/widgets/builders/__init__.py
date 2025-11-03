"""
Widget Builders - Modular widget creation functions.

Each builder module is responsible for creating widgets for a specific domain.
"""

from .tax_calculation import create_tax_calculation_widget, tax_calculation_widget_copy_text
from .document_detail import create_document_detail_widget, document_detail_widget_copy_text
from .person_confirmation import create_person_confirmation_widget, person_confirmation_widget_copy_text

__all__ = [
    # Tax widgets
    "create_tax_calculation_widget",
    "tax_calculation_widget_copy_text",
    # Document widgets
    "create_document_detail_widget",
    "document_detail_widget_copy_text",
    # Person widgets
    "create_person_confirmation_widget",
    "person_confirmation_widget_copy_text",
]
