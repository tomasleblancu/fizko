"""
Extractores de datos de RPA v3
"""
from .contribuyente import ContribuyenteExtractor
from .f29 import F29Extractor
from .dtes import DTEExtractor

__all__ = [
    'ContribuyenteExtractor',
    'F29Extractor',
    'DTEExtractor',
]
