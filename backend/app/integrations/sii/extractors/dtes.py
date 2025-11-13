"""
Extractor de DTEs vía API del SII - Sin dependencia de DB
"""
import logging
import requests
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..exceptions import ExtractionError

logger = logging.getLogger(__name__)


class DTEExtractor:
    """
    Extrae documentos tributarios electrónicos vía API del SII.

    Usa cookies directamente sin dependencia de base de datos.
    Solo llamadas HTTP a la API del SII.
    """

    BASE_URL = "https://www4.sii.cl/consdcvinternetui/services/data/facadeService"

    def __init__(self, tax_id: str):
        """
        Inicializa el extractor de DTEs

        Args:
            tax_id: RUT del contribuyente (formato: 12345678-9 o 12345678k)
        """
        self.tax_id = tax_id

        # Extraer RUT y DV (soporta formato con o sin guión)
        if '-' in tax_id:
            # Formato con guión: 12345678-9
            parts = tax_id.split('-')
            self.rut = parts[0]
            self.dv = parts[1].upper()
        else:
            # Formato sin guión: 12345678k (normalizado)
            self.rut = tax_id[:-1]  # Todo menos el último carácter
            self.dv = tax_id[-1].upper()  # Último carácter

        logger.debug(f"📦 DTEExtractor initialized for {tax_id} (RUT: {self.rut}, DV: {self.dv})")

    def extract_compras(
        self,
        periodo: str,
        tipo_doc: str = "33",
        cookies: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Extrae documentos de compra vía API

        Args:
            periodo: Período tributario (formato YYYYMM, ej: "202501")
            tipo_doc: Código tipo documento (default "33" = factura electrónica)
            cookies: Lista de cookies de sesión

        Returns:
            Dict con:
            {
                'status': 'success' | 'error',
                'data': List[Dict],  # Lista de documentos
                'extraction_method': str,
                'periodo_tributario': str,
                'message': str (opcional)
            }

        Raises:
            ExtractionError: Si falla la extracción
        """
        try:
            logger.info(f"📥 Extracting purchase documents - Period: {periodo}, Type: {tipo_doc}")

            if not cookies:
                raise ExtractionError(
                    "No cookies provided for API request",
                    resource='dtes_compra'
                )

            result = self._get_documentos_financieros(
                cookies=cookies,
                periodo_tributario=periodo,
                cod_tipo_doc=tipo_doc,
                operacion="COMPRA"
            )

            # Manejar respuesta con data=null
            data = result.get('data') or []
            total = len(data)
            logger.info(f"✅ Purchase documents extracted: {total} documents")

            return {
                'status': 'success',
                'data': data,
                'extraction_method': 'api_direct',
                'periodo_tributario': periodo,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error extracting purchase documents: {e}")
            raise ExtractionError(
                f"Failed to extract purchase documents: {str(e)}",
                resource='dtes_compra'
            )

    def extract_ventas(
        self,
        periodo: str,
        tipo_doc: str = "33",
        cookies: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Extrae documentos de venta vía API

        Args:
            periodo: Período tributario (formato YYYYMM)
            tipo_doc: Código tipo documento
            cookies: Lista de cookies de sesión

        Returns:
            Dict con documentos de venta

        Raises:
            ExtractionError: Si falla la extracción
        """
        try:
            logger.info(f"📤 Extracting sale documents - Period: {periodo}, Type: {tipo_doc}")

            if not cookies:
                raise ExtractionError(
                    "No cookies provided for API request",
                    resource='dtes_venta'
                )

            result = self._get_documentos_financieros(
                cookies=cookies,
                periodo_tributario=periodo,
                cod_tipo_doc=tipo_doc,
                operacion="VENTA"
            )

            # Manejar respuesta con data=null
            data = result.get('data') or []
            total = len(data)
            logger.info(f"✅ Sale documents extracted: {total} documents")

            return {
                'status': 'success',
                'data': data,
                'extraction_method': 'api_direct',
                'periodo_tributario': periodo,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error extracting sale documents: {e}")
            raise ExtractionError(
                f"Failed to extract sale documents: {str(e)}",
                resource='dtes_venta'
            )

    def extract_resumen(
        self,
        periodo: str,
        cookies: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Extrae resumen de compras y ventas del período usando endpoint específico

        Args:
            periodo: Período tributario (formato YYYYMM)
            cookies: Lista de cookies de sesión

        Returns:
            Dict con totales por tipo de documento

        Raises:
            ExtractionError: Si falla la extracción
        """
        try:
            logger.info(f"📊 Extracting summary - Period: {periodo}")

            if not cookies:
                raise ExtractionError(
                    "No cookies provided for API request",
                    resource='dtes_resumen'
                )

            # Obtener resumen de compras y ventas mediante endpoint específico
            resumen_compras = self._get_resumen_operacion(cookies, periodo, "COMPRA")
            resumen_ventas = self._get_resumen_operacion(cookies, periodo, "VENTA")

            logger.info("✅ Summary extracted")

            return {
                'status': 'success',
                'data': {
                    'periodo': periodo,
                    'resumen_compras': resumen_compras,
                    'resumen_ventas': resumen_ventas
                },
                'extraction_method': 'api_resumen_endpoint',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error extracting summary: {e}")
            raise ExtractionError(
                f"Failed to extract summary: {str(e)}",
                resource='dtes_resumen'
            )

    def _get_documentos_financieros(
        self,
        cookies: List[Dict],
        periodo_tributario: str,
        cod_tipo_doc: str = "33",
        operacion: str = "COMPRA",
        token_recaptcha: str = "t-o-k-e-n-web"
    ) -> Dict[str, Any]:
        """
        Método interno para obtener documentos financieros vía API

        Args:
            cookies: Lista de cookies de sesión
            periodo_tributario: Período en formato YYYYMM
            cod_tipo_doc: Código tipo documento
            operacion: "COMPRA" o "VENTA"
            token_recaptcha: Token recaptcha

        Returns:
            Dict con respuesta de la API
        """
        # Determinar endpoint y acción según operación
        if operacion == "VENTA":
            url = f"{self.BASE_URL}/getDetalleVenta"
            accion_recaptcha = "RCV_DETV"
            namespace = "cl.sii.sdi.lob.diii.consdcv.data.api.interfaces.FacadeService/getDetalleVenta"
            operacion_param = ""
            estado_contab = ""
        else:
            url = f"{self.BASE_URL}/getDetalleCompra"
            accion_recaptcha = "RCV_DETC"
            namespace = "cl.sii.sdi.lob.diii.consdcv.data.api.interfaces.FacadeService/getDetalleCompra"
            operacion_param = operacion
            estado_contab = "REGISTRO"

        # Construir headers con cookies
        logger.debug(f"🍪 Available cookies: {[c['name'] for c in cookies]}")

        token_cookie = next((c for c in cookies if c['name'] == 'TOKEN'), None)
        if not token_cookie:
            logger.error(f"❌ No TOKEN cookie found. Available cookies: {[c['name'] for c in cookies]}")
            raise ExtractionError("No se encontró el cookie TOKEN requerido", resource='api_cookies')

        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        headers = {
            'Cookie': cookie_string,
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Construir payload
        payload = {
            "metaData": self._generate_metadata(namespace, token_cookie['value']),
            "data": {
                "rutEmisor": self.rut,
                "dvEmisor": self.dv,
                "ptributario": periodo_tributario,
                "codTipoDoc": cod_tipo_doc,
                "operacion": operacion_param,
                "estadoContab": estado_contab,
                "accionRecaptcha": accion_recaptcha,
                "tokenRecaptcha": token_recaptcha
            }
        }

        try:
            logger.debug(f"🌐 Making API request to {url}")
            logger.debug(f"📦 Payload: {payload}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            # Log response for debugging
            logger.debug(f"📥 Response status: {response.status_code}")
            logger.debug(f"📥 Response body: {response.text[:500]}")

            response.raise_for_status()

            result = response.json()
            logger.debug(f"✅ API response received")

            return result if result is not None else {}

        except requests.exceptions.RequestException as e:
            raise ExtractionError(
                f"API request failed: {str(e)}",
                resource='api_request'
            )

    def _generate_metadata(self, namespace: str, conversation_id: str) -> Dict[str, Any]:
        """
        Genera metadata para la petición API

        Args:
            namespace: Namespace del servicio
            conversation_id: ID de conversación (valor del cookie TOKEN)

        Returns:
            Dict con metadata
        """
        return {
            "namespace": namespace,
            "conversationId": conversation_id,
            "transactionId": str(uuid.uuid4()),
            "page": None
        }

    def _get_resumen_operacion(
        self,
        cookies: List[Dict],
        periodo_tributario: str,
        operacion: str
    ) -> Dict[str, Any]:
        """
        Obtiene resumen de una operación (COMPRA o VENTA) mediante endpoint específico

        Args:
            cookies: Lista de cookies de sesión
            periodo_tributario: Período en formato YYYYMM
            operacion: "COMPRA" o "VENTA"

        Returns:
            Dict con resumen de la operación
        """
        try:
            url = f"{self.BASE_URL}/getResumen"
            namespace = "cl.sii.sdi.lob.diii.consdcv.data.api.interfaces.FacadeService/getResumen"

            # Obtener TOKEN cookie
            token_cookie = next((c for c in cookies if c['name'] == 'TOKEN'), None)
            if not token_cookie:
                raise ExtractionError("No se encontró el cookie TOKEN requerido", resource='api_cookies')

            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            headers = {
                'Cookie': cookie_string,
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Construir payload según operación
            payload = {
                "metaData": self._generate_metadata(namespace, token_cookie['value']),
                "data": {
                    "rutEmisor": self.rut,
                    "dvEmisor": self.dv,
                    "ptributario": periodo_tributario,
                    "estadoContab": "REGISTRO",
                    "operacion": operacion
                }
            }

            # Para COMPRA agregar busquedaInicial
            if operacion == "COMPRA":
                payload["data"]["busquedaInicial"] = True

            logger.debug(f"🌐 Getting {operacion} summary for period {periodo_tributario}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            result = response.json()
            logger.debug(f"✅ {operacion} summary received")

            return result if result is not None else {}

        except requests.exceptions.RequestException as e:
            raise ExtractionError(
                f"API request failed for {operacion} summary: {str(e)}",
                resource='api_resumen'
            )

    def extract_boletas_diarias(
        self,
        periodo: str,
        tipo_doc: str,
        cookies: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Extrae boletas o comprobantes diarios del período mediante endpoint específico

        Args:
            periodo: Período tributario (formato YYYYMM, ej: "202509")
            tipo_doc: Tipo de documento ("39" = boletas, "48" = comprobantes)
            cookies: Lista de cookies de sesión

        Returns:
            Dict con:
            {
                'status': 'success' | 'error',
                'data': List[Dict],  # Lista de totales diarios
                'extraction_method': str,
                'periodo_tributario': str
            }

        Raises:
            ExtractionError: Si falla la extracción
        """
        try:
            logger.info(f"📅 Extracting daily receipts - Period: {periodo}, Type: {tipo_doc}")

            if not cookies:
                raise ExtractionError(
                    "No cookies provided for API request",
                    resource='boletas_diarias'
                )

            # Validar tipo de documento
            if tipo_doc not in ["39", "48"]:
                raise ExtractionError(
                    f"Invalid document type for daily receipts: {tipo_doc}. Only 39 (boletas) and 48 (comprobantes) are supported.",
                    resource='boletas_diarias'
                )

            url = "https://www4.sii.cl/complementoscvui/services/data/facadeServiceBoletasDiarias/obtieneListaBoletasMes"
            namespace = "cl.sii.sdi.lob.diii.dcv.data.impl.boletasdiarias.FacadeSettingApplicationService/obtieneListaBoletasMes"

            # Obtener TOKEN cookie
            token_cookie = next((c for c in cookies if c['name'] == 'TOKEN'), None)
            if not token_cookie:
                raise ExtractionError("No se encontró el cookie TOKEN requerido", resource='api_cookies')

            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            headers = {
                'Cookie': cookie_string,
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Construir payload
            payload = {
                "metaData": {
                    "namespace": namespace,
                    "conversationId": token_cookie['value'],
                    "transactionId": str(uuid.uuid4()),
                    "page": {
                        "pageSize": 1,
                        "pageIndex": 1
                    }
                },
                "data": {
                    "rut": self.rut,
                    "dv": self.dv,
                    "periodo": periodo,
                    "tipoDocumento": tipo_doc
                }
            }

            logger.debug(f"🌐 Making API request to {url}")
            logger.debug(f"📦 Payload: {payload}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            # Log response for debugging
            logger.debug(f"📥 Response status: {response.status_code}")
            logger.debug(f"📥 Response body: {response.text[:500]}")

            response.raise_for_status()

            result = response.json()

            # Extraer data de la respuesta
            # La estructura es: {"data": {"boletas": [...]}}
            data_wrapper = result.get('data', {})
            boletas_raw = data_wrapper.get('boletas', [])

            # Filtrar solo los objetos dict que tienen 'dia' (totales diarios)
            # El SII a veces incluye strings o valores null en el array
            boletas = [
                item for item in boletas_raw
                if isinstance(item, dict) and 'dia' in item
            ]

            if not boletas:
                logger.warning(f"⚠️ No daily data in response for tipo {tipo_doc}")

            total = len(boletas)
            logger.info(f"✅ Daily receipts extracted: {total} days with data")

            return {
                'status': 'success',
                'data': boletas,  # Array de totales diarios
                'summary': {
                    'total_documents': data_wrapper.get('totalDocumentos', 0),
                    'total_amount': data_wrapper.get('montoTotal', 0),
                    'net_amount': data_wrapper.get('montoNeto', 0),
                    'tax_amount': data_wrapper.get('montoIva', 0),
                    'exempt_amount': data_wrapper.get('montoExento', 0)
                },
                'extraction_method': 'api_boletas_diarias',
                'periodo_tributario': periodo,
                'timestamp': datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error extracting daily receipts: {e}")
            raise ExtractionError(
                f"API request failed for daily receipts: {str(e)}",
                resource='boletas_diarias'
            )
        except Exception as e:
            logger.error(f"❌ Error extracting daily receipts: {e}")
            raise ExtractionError(
                f"Failed to extract daily receipts: {str(e)}",
                resource='boletas_diarias'
            )

    def close(self):
        """Cierra el extractor y libera recursos"""
        logger.debug("🔴 Closing DTEExtractor...")
