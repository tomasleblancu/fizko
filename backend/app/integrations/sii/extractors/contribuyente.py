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
                'direcciones': List[Dict],  # Direcciones del contribuyente
                'representantes': List[Dict],  # Representantes legales
                'socios': List[Dict],  # Socios de la empresa
                'timbrajes': List[Dict],  # Documentos autorizados (facturas, boletas, etc)
                'cumplimiento_tributario': Dict,  # Estado de cumplimiento
                'observaciones': Dict,  # Observaciones y alertas del SII
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

            # Hacer request al API para datos del contribuyente (opc=112)
            response = self._make_api_request(cookies, opc='112')

            # Parsear respuesta
            datos = self._parse_api_response(response, tax_id)

            # Obtener cumplimiento tributario (opc=118)
            try:
                cumplimiento = self._extract_cumplimiento_tributario(cookies)
                datos['cumplimiento_tributario'] = cumplimiento
                logger.debug(f"✅ Cumplimiento tributario extracted: {cumplimiento.get('estado', 'N/A')}")
            except Exception as e:
                logger.warning(f"⚠️ Could not extract cumplimiento tributario: {e}")
                datos['cumplimiento_tributario'] = None

            # Obtener observaciones/alertas (opc=28)
            try:
                observaciones = self._extract_observaciones(cookies)
                datos['observaciones'] = observaciones
                logger.debug(f"✅ Observaciones extracted: {observaciones.get('tiene_observaciones', False)}")
            except Exception as e:
                logger.warning(f"⚠️ Could not extract observaciones: {e}")
                datos['observaciones'] = None

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

    def _make_api_request(self, cookies: List[Dict], opc: str = '112') -> Dict:
        """
        Hace request al API del SII

        Args:
            cookies: Lista de cookies
            opc: Código de operación:
                - '112': Datos del contribuyente
                - '118': Cumplimiento tributario
                - '28': Observaciones y alertas

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

        # Payload
        payload = {'opc': opc}

        try:
            logger.debug(f"🌐 Making API request to {self.MISIIR_API_URL} (opc={opc})")
            response = requests.post(
                self.MISIIR_API_URL,
                data=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            logger.debug(f"✅ API response received: {data.get('codigoError', 'unknown') if 'codigoError' in data else 'success'}")

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

        # Extraer direcciones
        direcciones = []
        for dir in response.get('direcciones', []):
            direcciones.append({
                'codigo': dir.get('codigo'),
                'tipo': dir.get('tipoDomicilioDescripcion'),
                'tipo_codigo': dir.get('tipoDomicilioCodigo'),
                'calle': dir.get('calle'),
                'numero': dir.get('numero'),
                'bloque': dir.get('bloque'),
                'departamento': dir.get('departamento'),
                'villa_poblacion': dir.get('villaPoblacion'),
                'comuna': dir.get('comunaDescripcion'),
                'comuna_codigo': dir.get('comunaCodigo'),
                'region': dir.get('regionDescripcion'),
                'region_codigo': dir.get('regionCodigo'),
                'ciudad': dir.get('ciudad'),
                'tipo_propiedad': dir.get('tipoPropiedadDescripcion'),
                'tipo_propiedad_codigo': dir.get('tipoPropiedadCodigo'),
                'rut_propietario': f"{dir.get('rutPropietario')}-{dir.get('dvPropietario')}" if dir.get('rutPropietario') else None,
                'telefono': dir.get('telefono'),
                'fax': dir.get('fax'),
                'correo': dir.get('correo'),
                'mail': dir.get('mail')
            })

        # Extraer representantes
        representantes = []
        for rep in response.get('representantes', []):
            nombre_completo = None
            if rep.get('razonSocial'):
                nombre_completo = rep.get('razonSocial')
            elif rep.get('nombres'):
                nombre_completo = f"{rep.get('nombres', '')} {rep.get('apellidoPaterno', '')} {rep.get('apellidoMaterno', '')}".strip()

            representantes.append({
                'rut': f"{rep.get('rut')}-{rep.get('dv')}",
                'nombre_completo': nombre_completo,
                'nombres': rep.get('nombres'),
                'apellido_paterno': rep.get('apellidoPaterno'),
                'apellido_materno': rep.get('apellidoMaterno'),
                'fecha_inicio': rep.get('fechaInicio'),
                'fecha_termino': rep.get('fechaTermino'),
                'vigente': rep.get('vigente') == 'S'
            })

        # Extraer socios
        socios = []
        for socio in response.get('socios', []):
            nombre_completo = None
            if socio.get('razonSocial'):
                nombre_completo = socio.get('razonSocial')
            elif socio.get('nombres'):
                nombre_completo = f"{socio.get('nombres', '')} {socio.get('apellidoPaterno', '')} {socio.get('apellidoMaterno', '')}".strip()

            socios.append({
                'rut': f"{socio.get('rut')}-{socio.get('dv')}",
                'nombre_completo': nombre_completo,
                'nombres': socio.get('nombres'),
                'apellido_paterno': socio.get('apellidoPaterno'),
                'apellido_materno': socio.get('apellidoMaterno'),
                'fecha_incorporacion': socio.get('fechaIncorporacion'),
                'fecha_fin_participacion': socio.get('fechaFinParticipacion'),
                'participacion_capital': socio.get('participacionCapital'),
                'participacion_utilidades': socio.get('participacionUtilidades'),
                'aporte_enterado': socio.get('aporteEnterado'),
                'aporte_por_enterar': socio.get('aportePorEnterar'),
                'vigente': socio.get('vigente') == 'S'
            })

        # Extraer timbrajes (documentos autorizados)
        timbrajes = []
        for tim in response.get('timbrajes', []):
            timbrajes.append({
                'codigo': tim.get('codigo'),
                'descripcion': tim.get('descripcion'),
                'numero_inicial': tim.get('numeroInicial'),
                'numero_final': tim.get('numeroFinal'),
                'fecha_legalizacion': tim.get('fechaLegalizacion')
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
            'direcciones': direcciones,
            'representantes': representantes,
            'socios': socios,
            'timbrajes': timbrajes,
            # Campos adicionales
            'autorizado_declarar_dia_20': contrib.get('autorizadoDeclararDia20') == 'S',
            'fecha_termino_giro': contrib.get('fechaTerminoGiro'),
            'capital_enterado': contrib.get('capitalEnterado'),
            'capital_por_enterar': contrib.get('capitalPorEnterar'),
            # Metadata
            'extraction_method': 'api',
            'api_endpoint': self.MISIIR_API_URL
        }

        return datos

    def _extract_cumplimiento_tributario(self, cookies: List[Dict]) -> Dict[str, Any]:
        """
        Extrae el estado de cumplimiento tributario del contribuyente

        Args:
            cookies: Lista de cookies

        Returns:
            Dict con cumplimiento tributario:
            {
                'estado': str,  # "Cumple sus obligaciones tributarias" o similar
                'semestre_actual': str,
                'atributos': List[Dict],  # Lista de requisitos con su estado
                'historicos': Any  # Históricos si existen
            }

            Cada atributo contiene:
            {
                'atr_codigo': str,  # Código del requisito
                'cumple': str,  # "SI" o "NO"
                'condicion': str,  # Letra identificadora
                'titulo': str,  # Título del requisito
                'descripcion': str  # Descripción del requisito
            }

        Raises:
            ExtractionError: Si falla la extracción
        """
        try:
            # Hacer request al API con opc=118
            response = self._make_api_request(cookies, opc='118')

            # La respuesta para opc=118 tiene una estructura diferente
            # No tiene 'codigoError', es directamente el JSON con los datos

            # Formatear la respuesta
            cumplimiento = {
                'estado': response.get('estado'),
                'semestre_actual': response.get('semestreActual'),
                'atributos': [],
                'historicos': response.get('historicos')
            }

            # Procesar atributos
            for attr in response.get('atributos', []):
                cumplimiento['atributos'].append({
                    'atr_codigo': attr.get('atrCodigo'),
                    'cumple': attr.get('cumple'),
                    'condicion': attr.get('condicion'),
                    'titulo': attr.get('titulo'),
                    'descripcion': attr.get('descripcion')
                })

            return cumplimiento

        except Exception as e:
            raise ExtractionError(
                f"Failed to extract cumplimiento tributario: {str(e)}",
                resource='cumplimiento_tributario'
            )

    def _extract_observaciones(self, cookies: List[Dict]) -> Dict[str, Any]:
        """
        Extrae observaciones y alertas del contribuyente

        Args:
            cookies: Lista de cookies

        Returns:
            Dict con observaciones/alertas:
            {
                'tiene_observaciones': bool,  # True si hay observaciones vigentes
                'codigo': int,  # Código de respuesta
                'descripcion': str,  # Descripción del estado
                'observaciones': List[Dict] | None  # Lista de observaciones si existen
            }

            Si hay observaciones, cada una contiene la estructura del objSalida.
            Si no hay observaciones, objSalida será None.

        Raises:
            ExtractionError: Si falla la extracción
        """
        try:
            # Hacer request al API con opc=28
            response = self._make_api_request(cookies, opc='28')

            # Procesar la respuesta
            obj_salida = response.get('objSalida')
            codigo = response.get('codigo')
            descripcion = response.get('descripcion')

            # Determinar si hay observaciones
            # Código 97 significa "no posee observaciones/alertas vigentes"
            tiene_observaciones = obj_salida is not None and codigo != 97

            observaciones_data = {
                'tiene_observaciones': tiene_observaciones,
                'codigo': codigo,
                'descripcion': descripcion,
                'observaciones': obj_salida if tiene_observaciones else None
            }

            return observaciones_data

        except Exception as e:
            raise ExtractionError(
                f"Failed to extract observaciones: {str(e)}",
                resource='observaciones'
            )
