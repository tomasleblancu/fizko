"""
Métodos relacionados con Documentos Tributarios Electrónicos (DTEs)
"""
import logging
from typing import Dict, Any

from .contribuyente_methods import ContribuyenteMethods
from ..extractors import DTEExtractor

logger = logging.getLogger(__name__)


class DTEMethods(ContribuyenteMethods):
    """
    Métodos para obtener documentos tributarios electrónicos (DTEs)
    Hereda de ContribuyenteMethods
    """

    def get_compras(
        self,
        periodo: str,
        tipo_doc: str = "33"
    ) -> Dict[str, Any]:
        """
        Obtiene documentos de compra vía API del SII

        Args:
            periodo: Período tributario (formato YYYYMM, ej: "202501")
            tipo_doc: Código tipo documento (default "33" = factura electrónica)

        Returns:
            Dict con:
            - status: 'success' | 'error'
            - data: List[Dict] con documentos
            - extraction_method: str
            - periodo_tributario: str

        Raises:
            ExtractionError: Si falla la extracción
        """
        # Lazy loading del extractor DTE
        if not self._dte_extractor:
            self._dte_extractor = DTEExtractor(tax_id=self.tax_id)

        # Obtener cookies (hacer login si es necesario)
        cookies = self.get_cookies()

        return self._dte_extractor.extract_compras(periodo, tipo_doc, cookies)

    def get_ventas(
        self,
        periodo: str,
        tipo_doc: str = "33"
    ) -> Dict[str, Any]:
        """
        Obtiene documentos de venta vía API del SII

        Args:
            periodo: Período tributario (formato YYYYMM)
            tipo_doc: Código tipo documento

        Returns:
            Dict con documentos de venta

        Raises:
            ExtractionError: Si falla la extracción
        """
        # Lazy loading del extractor DTE
        if not self._dte_extractor:
            self._dte_extractor = DTEExtractor(tax_id=self.tax_id)

        # Obtener cookies (hacer login si es necesario)
        cookies = self.get_cookies()

        return self._dte_extractor.extract_ventas(periodo, tipo_doc, cookies)

    def get_resumen(self, periodo: str) -> Dict[str, Any]:
        """
        Obtiene resumen de compras y ventas del período

        Args:
            periodo: Período tributario (YYYYMM)

        Returns:
            Dict con totales por tipo de documento

        Raises:
            ExtractionError: Si falla la extracción
        """
        # Lazy loading del extractor DTE
        if not self._dte_extractor:
            self._dte_extractor = DTEExtractor(tax_id=self.tax_id)

        # Obtener cookies (hacer login si es necesario)
        cookies = self.get_cookies()

        return self._dte_extractor.extract_resumen(periodo, cookies)

    def get_boletas_diarias(
        self,
        periodo: str,
        tipo_doc: str
    ) -> Dict[str, Any]:
        """
        Obtiene boletas o comprobantes diarios del período

        Args:
            periodo: Período tributario (YYYYMM)
            tipo_doc: Tipo de documento ("39" = boletas, "48" = comprobantes)

        Returns:
            Dict con totales diarios

        Raises:
            ExtractionError: Si falla la extracción
        """
        # Lazy loading del extractor DTE
        if not self._dte_extractor:
            self._dte_extractor = DTEExtractor(tax_id=self.tax_id)

        # Obtener cookies (hacer login si es necesario)
        cookies = self.get_cookies()

        return self._dte_extractor.extract_boletas_diarias(periodo, tipo_doc, cookies)
