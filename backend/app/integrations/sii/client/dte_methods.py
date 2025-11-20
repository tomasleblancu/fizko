"""
Métodos relacionados con Documentos Tributarios Electrónicos (DTEs)
"""
import logging
import random
import string
import uuid
import time
from typing import Dict, Any, List

import requests

from .contribuyente_methods import ContribuyenteMethods
from ..extractors import DTEExtractor
from ..exceptions import ExtractionError

logger = logging.getLogger(__name__)


class DTEMethods(ContribuyenteMethods):
    """
    Métodos para obtener documentos tributarios electrónicos (DTEs)
    Hereda de ContribuyenteMethods
    """

    def get_compras(
        self,
        periodo: str,
        tipo_doc: str = "33",
        estado_contab: str = "REGISTRO"
    ) -> Dict[str, Any]:
        """
        Obtiene documentos de compra vía API del SII

        Args:
            periodo: Período tributario (formato YYYYMM, ej: "202501")
            tipo_doc: Código tipo documento (default "33" = factura electrónica)
            estado_contab: Estado contable (default "REGISTRO", también puede ser "PENDIENTE")

        Returns:
            Dict con:
            - status: 'success' | 'error'
            - data: List[Dict] con documentos
            - extraction_method: str
            - periodo_tributario: str
            - estado_contab: str

        Raises:
            ExtractionError: Si falla la extracción
        """
        # Lazy loading del extractor DTE
        if not self._dte_extractor:
            self._dte_extractor = DTEExtractor(tax_id=self.tax_id)

        # Verificar y refrescar sesión si es necesario
        self.verify_session()

        # Obtener cookies validadas
        cookies = self.get_cookies()

        return self._dte_extractor.extract_compras(periodo, tipo_doc, cookies, estado_contab)

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

        # Verificar y refrescar sesión si es necesario
        self.verify_session()

        # Obtener cookies validadas
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

        # Verificar y refrescar sesión si es necesario
        self.verify_session()

        # Obtener cookies validadas
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

        # Verificar y refrescar sesión si es necesario
        self.verify_session()

        # Obtener cookies validadas
        cookies = self.get_cookies()

        return self._dte_extractor.extract_boletas_diarias(periodo, tipo_doc, cookies)

    def ingresar_aceptacion_reclamo_docs(
        self,
        documentos: List[Dict[str, str]],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Ingresa acuses de recibo (aceptación/reclamo) de documentos masivamente.

        Args:
            documentos: Lista de documentos a procesar, cada uno con:
                - detRutDoc: RUT del emisor (sin guión)
                - detDvDoc: Dígito verificador
                - detTipoDoc: Código tipo documento (ej: "33" para factura)
                - detNroDoc: Número del documento
                - dedCodEvento: Código del evento (ej: "ERM" para acuse de recibo mercaderías)
            max_retries: Número máximo de reintentos

        Returns:
            Dict con:
            {
                "data": [
                    {
                        "detRutDoc": str,
                        "detDvDoc": str,
                        "detTipoDoc": str,
                        "detNroDoc": str,
                        "dedCodEvento": str,
                        "respuesta": str,
                        "codRespuesta": int
                    },
                    ...
                ],
                "eventosOk": int,
                "metaData": {...},
                "respEstado": {...}
            }

        Raises:
            ValueError: Si los parámetros no son válidos
            ExtractionError: Si falla el procesamiento

        Example:
            >>> documentos = [
            ...     {
            ...         "detRutDoc": "76035322",
            ...         "detDvDoc": "1",
            ...         "detTipoDoc": "33",
            ...         "detNroDoc": "22474",
            ...         "dedCodEvento": "ERM"
            ...     }
            ... ]
            >>> resultado = client.ingresar_aceptacion_reclamo_docs(documentos)
            >>> print(f"Eventos OK: {resultado['eventosOk']}")
        """
        try:
            # Validar parámetros
            if not documentos or not isinstance(documentos, list):
                raise ValueError("documentos debe ser una lista no vacía")

            # Validar cada documento
            for idx, doc in enumerate(documentos):
                required_fields = ["detRutDoc", "detDvDoc", "detTipoDoc", "detNroDoc", "dedCodEvento"]
                for field in required_fields:
                    if field not in doc:
                        raise ValueError(f"Documento {idx}: falta campo requerido '{field}'")

            self._ensure_initialized()

            # Obtener RUT y DV del tax_id (formato: "12345678-9")
            if '-' in self.tax_id:
                rut_autenticado, dv_autenticado = self.tax_id.rsplit('-', 1)
            else:
                # Si no tiene guion, asumir que el último caracter es el DV
                rut_autenticado = self.tax_id[:-1]
                dv_autenticado = self.tax_id[-1]

            # DV debe estar en mayúscula
            dv_autenticado = dv_autenticado.upper()

            # Verificar y refrescar sesión si es necesario
            self.verify_session()

            # Obtener cookies validadas
            cookies = self.get_cookies()

            logger.info(f"📝 Ingresando acuses de recibo para {len(documentos)} documentos...")

            endpoint_url = "https://www4.sii.cl/consdcvinternetui/services/data/facadeService/ingresarAceptacionReclamoDocs"

            for attempt in range(max_retries):
                try:
                    # Generar IDs únicos para la petición
                    conversation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=13))
                    transaction_id = str(uuid.uuid4())

                    # Convertir cookies a dict para requests
                    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}

                    # Construir el payload
                    payload = {
                        "metaData": {
                            "namespace": "cl.sii.sdi.lob.diii.consdcv.data.api.interfaces.FacadeService/ingresarAceptacionReclamoDocs",
                            "conversationId": conversation_id,
                            "transactionId": transaction_id,
                            "page": None
                        },
                        "data": {
                            "dteAcuRe": documentos,
                            "rutAutenticado": rut_autenticado,
                            "dvAutenticado": dv_autenticado
                        }
                    }

                    logger.info(f"📤 Payload (intento {attempt + 1}/{max_retries}): {len(documentos)} documentos")

                    # Headers necesarios para la petición
                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    }

                    # Realizar la petición
                    response = requests.post(
                        endpoint_url,
                        json=payload,
                        cookies=cookies_dict,
                        headers=headers,
                        timeout=30
                    )

                    logger.info(f"📥 Status code: {response.status_code}")

                    # Verificar respuesta exitosa
                    if response.status_code == 200:
                        result = response.json()

                        logger.info(f"✅ Acuses de recibo procesados exitosamente")
                        logger.info(f"   Eventos OK: {result.get('eventosOk', 0)}")

                        return result
                    else:
                        # Log response body para debugging
                        try:
                            response_body = response.text[:500]  # Primeros 500 caracteres
                            logger.warning(f"⚠️ Respuesta inesperada: {response.status_code}")
                            logger.warning(f"📄 Response body: {response_body}")
                        except Exception:
                            logger.warning(f"⚠️ Respuesta inesperada: {response.status_code}")

                        if attempt < max_retries - 1:
                            logger.info(f"Reintentando en 2 segundos...")
                            time.sleep(2)
                            continue
                        else:
                            raise ExtractionError(f"Error al ingresar acuses de recibo: HTTP {response.status_code}")

                except requests.RequestException as e:
                    logger.error(f"❌ Error en petición (intento {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        logger.info(f"Reintentando en 2 segundos...")
                        time.sleep(2)
                        continue
                    else:
                        raise ExtractionError(f"Error en petición: {str(e)}") from e

            raise ExtractionError("No se pudo completar la petición")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ Error ingresando acuses de recibo: {e}", exc_info=True)
            raise ExtractionError(f"Error ingresando acuses de recibo: {str(e)}") from e
