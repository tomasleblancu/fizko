"""
ChatKit Widgets for Fizko - Rich UI components for agent responses.

This module now serves as a compatibility layer, re-exporting all widgets
from the modular builders/ subdirectory. All widget implementations have
been moved to their respective domain-focused modules:

- builders/tax_calculation.py     - Tax calculation breakdown widget
- builders/document_detail.py     - Document detail widget
- builders/person_confirmation.py - Person confirmation widget

For new code, prefer importing directly from the builders modules.
This file maintains backward compatibility for existing imports.
"""

from __future__ import annotations

# Re-export all widgets from builders for backward compatibility
from .builders.tax_calculation import (
    create_tax_calculation_widget,
    tax_calculation_widget_copy_text,
)
from .builders.document_detail import (
    create_document_detail_widget,
    document_detail_widget_copy_text,
)
from .builders.person_confirmation import (
    create_person_confirmation_widget,
    person_confirmation_widget_copy_text,
)

__all__ = [
    # Tax calculation widget
    "create_tax_calculation_widget",
    "tax_calculation_widget_copy_text",
    # Document detail widget
    "create_document_detail_widget",
    "document_detail_widget_copy_text",
    # Person confirmation widget
    "create_person_confirmation_widget",
    "person_confirmation_widget_copy_text",
]
