"""Tax-related tools for agents."""

# Re-export individual tool functions (simplified to 2 main tools)
from .documentos_tributarios_tools import (
    get_documents,
    get_documents_summary,
)

__all__ = [
    "get_documents",
    "get_documents_summary",
]
