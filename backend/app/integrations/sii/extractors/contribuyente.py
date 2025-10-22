"""
Extractor de datos del contribuyente via API
"""
import logging
import requests
from typing import Dict, Any, List

from ..core import SeleniumDriver
from ..exceptions import ExtractionError

logger = logging.getLogger(__name__)


class ContribuyenteExtractor:
    """
    Extrae datos del contribuyente usando API del SII

    Usa el endpoint: https://misiir.sii.cl/cgi_misii/CViewCarta.cgi
    Con cookies obtenidas del RPA
    """

    MISIIR_API_URL = "https://misiir.sii.cl/cgi_misii/CViewCarta.cgi"

    def __init__(self, driver: SeleniumDriver):
        """
        Inicializa el extractor

        Args:
            driver: Instancia de SeleniumDriver
        """
        self.driver = driver
        logger.debug("📊 ContribuyenteExtractor initialized (API mode)")

    def extract(self, tax_id: str, cookies: List[Dict] = None) -> Dict[str, Any]:
        """
        Extrae información del contribuyente via API

        Args:
            tax_id: RUT del contribuyente
            cookies: Cookies opcionales (si no se proveen, usa las del driver)

        Returns:
            Dict con datos del contribuyente:
            {
                'rut': str,
                'razon_social': str,
                'nombre': str,  # alias de razon_social
                'tipo_contribuyente': str,
                'subtipo_contribuyente': str,
                'email': str,
                'telefono': str,
                'actividad_economica': str,
                'fecha_inicio_actividades': str,
                'fecha_constitucion': str,
                'unidad_operativa': str,
                'segmento': str,
                'actividades': List[Dict],  # Lista de actividades económicas
            }

        Raises:
            ExtractionError: Si falla la extracción
        """
        try:
            logger.debug(f"📊 Extracting contribuyente data via API for {tax_id}...")

            # Obtener cookies (de parámetro o del driver)
            if cookies is None:
                cookies = self.driver.get_cookies() if self.driver else []

            if not cookies:
                raise ExtractionError(
                    "No cookies available for API request",
                    resource='contribuyente'
                )

            # Hacer request al API
            response = self._make_api_request(cookies)

            # Parsear respuesta
            datos = self._parse_api_response(response, tax_id)

            logger.info(f"✅ Contribuyente extracted: {datos.get('razon_social', 'N/A')}")
            return datos

        except Exception as e:
            logger.error(f"❌ Error extracting contribuyente: {e}")
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(
                f"Failed to extract contribuyente: {str(e)}",
                resource='contribuyente'
            )

    def _make_api_request(self, cookies: List[Dict]) -> Dict:
        """
        Hace request al API del SII

        Args:
            cookies: Lista de cookies

        Returns:
            Dict con respuesta JSON del API
        """
        # Construir cookie string
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        # Headers
        headers = {
            'Cookie': cookie_string,
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Payload (opc=112 para obtener datos del contribuyente)
        payload = {'opc': '112'}

        try:
            logger.debug(f"🌐 Making API request to {self.MISIIR_API_URL}")
            response = requests.post(
                self.MISIIR_API_URL,
                data=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            logger.debug(f"✅ API response received: {data.get('codigoError', 'unknown')}")

            return data

        except requests.exceptions.RequestException as e:
            raise ExtractionError(
                f"API request failed: {str(e)}",
                resource='contribuyente_api'
            )

    def _parse_api_response(self, response: Dict, tax_id: str) -> Dict[str, Any]:
        """
        Parsea la respuesta del API

        Args:
            response: Respuesta JSON del API
            tax_id: RUT del contribuyente

        Returns:
            Dict con datos formateados
        """
        # Verificar error
        if response.get('codigoError') != 0:
            raise ExtractionError(
                f"API error: {response.get('descripcionError', 'Unknown error')}",
                resource='contribuyente_api'
            )

        # Extraer datos del contribuyente
        contrib = response.get('contribuyente', {})

        if contrib.get('codigoError') != 0:
            raise ExtractionError(
                f"Contribuyente error: {contrib.get('descripcionError', 'Unknown error')}",
                resource='contribuyente'
            )

        # Extraer actividades económicas
        actividades = []
        for act in response.get('actEcos', []):
            actividades.append({
                'codigo': act.get('codigo'),
                'descripcion': act.get('descripcion'),
                'categoria_tributaria': act.get('categoriaTributaria'),
                'afecto_iva': act.get('afectoIva') == 'S',
                'fecha_inicio': act.get('fechaInicio')
            })

        # Formatear datos
        datos = {
            'rut': f"{contrib.get('rut')}-{contrib.get('dv')}",
            'razon_social': contrib.get('razonSocial'),
            'nombre': contrib.get('razonSocial'),  # Alias
            'tipo_contribuyente': contrib.get('tipoContribuyenteDescripcion'),
            'tipo_contribuyente_codigo': contrib.get('tipoContribuyenteCodigo'),
            'subtipo_contribuyente': contrib.get('subtipoContribuyenteDescrip'),
            'subtipo_contribuyente_codigo': contrib.get('subtipoContribuyenteCodigo'),
            'email': contrib.get('eMail'),
            'telefono': contrib.get('telefonoMovil'),
            'actividad_economica': contrib.get('glosaActividad'),
            'fecha_inicio_actividades': contrib.get('fechaInicioActividades'),
            'fecha_constitucion': contrib.get('fechaConstitucion'),
            'fecha_nacimiento': contrib.get('fechaNacimiento'),
            'unidad_operativa': contrib.get('unidadOperativaDescripcion'),
            'unidad_operativa_codigo': contrib.get('unidadOperativaCodigo'),
            'unidad_operativa_direccion': contrib.get('unidadOperativaDireccion'),
            'segmento': contrib.get('segmentoDescripcion'),
            'segmento_codigo': contrib.get('segmentoCodigo'),
            'persona_empresa': contrib.get('personaEmpresa'),
            'actividades': actividades,
            # Campos adicionales
            'autorizado_declarar_dia_20': contrib.get('autorizadoDeclararDia20') == 'S',
            'fecha_termino_giro': contrib.get('fechaTerminoGiro'),
            # Metadata
            'extraction_method': 'api',
            'api_endpoint': self.MISIIR_API_URL
        }

        return datos
