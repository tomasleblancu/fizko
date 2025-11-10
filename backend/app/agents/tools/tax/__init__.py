"""Tax-related tools for agents."""

# Re-export individual tool functions (simplified to 2 main tools)
from .documentos_tributarios_tools import (
    get_documents,
    get_documents_summary,
)

# Expense tools
from .expense_tools import (
    create_expense,
    get_expenses,
    get_expense_summary,
)

__all__ = [
    "get_documents",
    "get_documents_summary",
    "create_expense",
    "get_expenses",
    "get_expense_summary",
]
