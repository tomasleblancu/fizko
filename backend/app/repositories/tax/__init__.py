"""Tax repositories - Document and form management."""

from .form29 import Form29Repository
from .honorarios import HonorariosRepository
from .purchase_documents import PurchaseDocumentRepository
from .sales_documents import SalesDocumentRepository
from .tax_documents import TaxDocumentRepository
from .tax_summary import TaxSummaryRepository

__all__ = [
    "Form29Repository",
    "HonorariosRepository",
    "PurchaseDocumentRepository",
    "SalesDocumentRepository",
    "TaxDocumentRepository",
    "TaxSummaryRepository",
]
