"""Tax-related tools for agents."""

# Re-export individual tool functions
from .documentos_tributarios_tools import (
    search_documents_by_rut,
    search_document_by_folio,
    get_documents_by_date_range,
    get_purchase_documents,
    get_sales_documents,
    get_document_details,
    get_documents_summary,
)

__all__ = [
    "search_documents_by_rut",
    "search_document_by_folio",
    "get_documents_by_date_range",
    "get_purchase_documents",
    "get_sales_documents",
    "get_document_details",
    "get_documents_summary",
]
