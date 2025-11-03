"""
Extractor de formularios F29
"""
import logging
import requests
import uuid
from typing import List, Dict, Any, Optional

from ..scrapers.f29_scraper import F29Scraper
from ..core import SeleniumDriver
from ..exceptions import ExtractionError

logger = logging.getLogger(__name__)


class F29Extractor:
    """
    Extrae formularios F29 desde el portal SII

    Funcionalidades:
    - Buscar lista de formularios (via scraper)
    - Descargar formulario compacto en PDF
    """

    def __init__(self, driver: SeleniumDriver, tax_id: str):
        """
        Inicializa el extractor

        Args:
            driver: Instancia de SeleniumDriver
            tax_id: RUT del contribuyente
        """
        self.driver = driver
        self.tax_id = tax_id
        self._list_scraper = F29Scraper(driver)

        logger.info("📋 F29Extractor initialized")

    def search(self, anio: str, folio: Optional[str] = None) -> List[Dict]:
        """
        Busca formularios F29

        Args:
            anio: Año (formato YYYY, ej: "2024")
            folio: Folio específico (opcional)

        Returns:
            Lista de formularios F29 encontrados

        Raises:
            ExtractionError: Si falla la búsqueda
        """
        try:
            logger.info(f"🔍 Searching F29 forms - Year: {anio}, Folio: {folio}")

            # Delegar a scraper de v2
            formularios = self._list_scraper.buscar_formularios(
                anio=anio,
                folio=folio
            )

            logger.info(f"✅ Found {len(formularios)} F29 forms")
            return formularios

        except Exception as e:
            logger.error(f"❌ Error searching F29: {e}")
            raise ExtractionError(
                f"Failed to search F29: {str(e)}",
                resource='f29_search'
            )

    def get_formulario_compacto(
        self,
        folio: str,
        id_interno_sii: str,
        form_type: str = '029'
    ) -> Optional[bytes]:
        """
        Descarga el PDF del formulario compacto usando Selenium

        Args:
            folio: Folio real del formulario (ej: "8104678626")
            id_interno_sii: ID interno del SII (codInt) (ej: "817935151")
            form_type: Tipo de formulario (default: '029' para F29)

        Returns:
            Contenido del PDF en bytes, o None si hay error

        Example:
            >>> pdf_bytes = extractor.get_formulario_compacto(
            ...     folio="8104678626",
            ...     id_interno_sii="817935151"
            ... )
            >>> if pdf_bytes:
            ...     with open('f29.pdf', 'wb') as f:
            ...         f.write(pdf_bytes)
        """
        try:
            import base64
            import time

            # Extraer RUT sin dígito verificador (soporta formato con o sin guión)
            if '-' in self.tax_id:
                rut_sin_dv = self.tax_id.split('-')[0]
            else:
                # Formato sin guión: 12345678k
                rut_sin_dv = self.tax_id[:-1]

            # Construir URL del formulario compacto
            url = (
                f"https://www4.sii.cl/rfiInternet/formCompacto"
                f"?folio={folio}"
                f"&rut={rut_sin_dv}"
                f"&form={form_type}"
                f"&codInt={id_interno_sii}"
            )

            logger.info(f"📄 Downloading compact form PDF: folio={folio}, codInt={id_interno_sii}")

            # Navegar a la URL del PDF
            self.driver.navigate_to(url)
            time.sleep(3)

            # Usar Chrome DevTools Protocol para obtener el PDF
            # Esto funciona mejor que requests porque mantiene la sesión del navegador
            try:
                pdf_base64 = self.driver.driver.execute_cdp_cmd("Page.printToPDF", {})
                pdf_bytes = base64.b64decode(pdf_base64['data'])
                logger.info(f"✅ PDF downloaded via CDP ({len(pdf_bytes)} bytes)")
                return pdf_bytes
            except Exception as cdp_error:
                logger.warning(f"⚠️ CDP method failed: {cdp_error}, trying alternative method")

                # Método alternativo: obtener el PDF del page source si está embebido
                page_source = self.driver.driver.page_source

                # Si la página contiene un embed/object con PDF
                if 'application/pdf' in page_source or 'embed' in page_source.lower():
                    # Intentar con requests usando las cookies del driver
                    current_cookies = self.driver.get_cookies()
                    cookies_dict = {c['name']: c['value'] for c in current_cookies}

                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://www4.sii.cl/sifmConsultaInternet/'
                    }

                    response = requests.get(url, cookies=cookies_dict, headers=headers, timeout=30)

                    if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):
                        logger.info(f"✅ PDF downloaded via requests ({len(response.content)} bytes)")
                        return response.content

                logger.error(f"❌ Could not download PDF. Page source preview: {page_source[:500]}")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting compact form: {str(e)}")
            raise ExtractionError(
                f"Failed to download compact form: {str(e)}",
                resource='f29_pdf'
            )

    def get_declaracion_propuesta(
        self,
        periodo: str,
        cookies: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Obtiene la propuesta de declaración F29 pre-calculada por el SII.

        Este endpoint devuelve el F29 con valores pre-llenados por el SII,
        incluyendo códigos propuestos, condiciones del contribuyente, y códigos
        que requieren complementación manual.

        Args:
            periodo: Período tributario en formato YYYYMM (ej: "202510")
            cookies: Lista de cookies de sesión SII

        Returns:
            Dict con la estructura completa de la propuesta:
            {
                'data': {
                    'tipopropuesta': int,
                    'listCondiciones': List[Dict],
                    'listCodPropuestos': List[Dict],  # Códigos con valores pre-calculados
                    'listGlosasProp': List[Dict],
                    'listCodBase': List[Dict],  # Info del contribuyente
                    'listCodAdministrativos': List[Dict],
                    'listCodComplementar': List[int],  # Códigos a completar manualmente
                    'complementoDetalleDTE': bool,
                    'documentosDelGiro': bool,
                    ...
                },
                'metaData': {...}
            }

        Raises:
            ExtractionError: Si falla la extracción

        Example:
            >>> propuesta = extractor.get_declaracion_propuesta(
            ...     periodo="202510",
            ...     cookies=session_cookies
            ... )
            >>> codigos = propuesta['data']['listCodPropuestos']
            >>> # [{"codigo": "502", "valor": "1545"}, ...]
        """
        try:
            logger.info(f"📊 Fetching F29 propuesta - Period: {periodo}")

            if not cookies:
                raise ExtractionError(
                    "No cookies provided for API request",
                    resource='f29_propuesta'
                )

            # Extraer RUT sin dígito verificador (soporta formato con o sin guión)
            if '-' in self.tax_id:
                rut_sin_dv = self.tax_id.split('-')[0]
                dv = self.tax_id.split('-')[1].upper()
            else:
                # Formato sin guión: 12345678k
                rut_sin_dv = self.tax_id[:-1]
                dv = self.tax_id[-1].upper()

            # Extraer mes y año del período
            if len(periodo) != 6:
                raise ValueError(f"Período debe estar en formato YYYYMM, recibido: {periodo}")

            anno = periodo[:4]
            mes = periodo[4:6]

            # URL del endpoint
            url = "https://www4.sii.cl/propuestaf29ui/services/data/facadeAdapterService/getDeclaracionConCondicionesYTipoPropuesta"

            # Generar IDs para la transacción
            conversation_id = str(uuid.uuid4())[:13].replace('-', '').upper()
            transaction_id = str(uuid.uuid4())

            # Construir payload según el formato del SII
            payload = {
                "metaData": {
                    "namespace": "cl.sii.sdi.lob.iva.propuestaf29.data.api.interfaces.FacadeAdapterService/getDeclaracionConCondicionesYTipoPropuesta",
                    "conversationId": conversation_id,
                    "transactionId": transaction_id
                },
                "data": {
                    "rutContribuyente": rut_sin_dv,
                    "dv": dv,
                    "formCodigo": "2",  # Código para formulario F29
                    "mes": mes,
                    "anno": anno
                }
            }

            # Convertir cookies a formato dict para requests
            cookies_dict = {c['name']: c['value'] for c in cookies}

            # Headers requeridos
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www4.sii.cl/propuestaf29ui/',
                'Origin': 'https://www4.sii.cl'
            }

            logger.debug(f"🔗 POST {url}")
            logger.debug(f"📦 Payload: periodo={periodo}, rut={rut_sin_dv}-{dv}")

            # Hacer la petición
            response = requests.post(
                url,
                json=payload,
                cookies=cookies_dict,
                headers=headers,
                timeout=30
            )

            # Verificar respuesta
            if response.status_code != 200:
                logger.error(f"❌ API returned status {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                raise ExtractionError(
                    f"API request failed with status {response.status_code}",
                    resource='f29_propuesta'
                )

            # Parsear respuesta
            result = response.json()

            # Verificar estructura de respuesta
            if 'data' not in result:
                logger.error(f"❌ Unexpected response structure: {list(result.keys())}")
                raise ExtractionError(
                    "Invalid API response structure",
                    resource='f29_propuesta'
                )

            # Contar códigos propuestos
            codigos_propuestos = result.get('data', {}).get('listCodPropuestos', [])
            codigos_complementar = result.get('data', {}).get('listCodComplementar', [])

            logger.info(
                f"✅ F29 propuesta retrieved: {len(codigos_propuestos)} códigos propuestos, "
                f"{len(codigos_complementar)} códigos a complementar"
            )

            return result

        except requests.RequestException as e:
            logger.error(f"❌ Network error fetching F29 propuesta: {e}")
            raise ExtractionError(
                f"Network error: {str(e)}",
                resource='f29_propuesta'
            )
        except Exception as e:
            logger.error(f"❌ Error fetching F29 propuesta: {e}")
            raise ExtractionError(
                f"Failed to fetch F29 propuesta: {str(e)}",
                resource='f29_propuesta'
            )

    def get_tasa_ppmo(
        self,
        periodo: str,
        categoria_tributaria: int = 1,
        tipo_formulario: str = "FMNINT",
        cookies: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Obtiene la tasa de PPMO (Pagos Provisionales Mensuales Obligatorios).

        Este endpoint calcula la tasa de PPM según la categoría tributaria
        y el tipo de formulario del contribuyente.

        Args:
            periodo: Período tributario en formato YYYYMM (ej: "202510")
            categoria_tributaria: Categoría tributaria (1=Primera categoría, default: 1)
            tipo_formulario: Tipo de formulario (default: "FMNINT")
            cookies: Lista de cookies de sesión SII

        Returns:
            Dict con la información de tasa PPMO:
            {
                'data': {
                    'rutContribuyente': str,
                    'dv': str,
                    'mes': int,
                    'anno': int,
                    'cod563': str,  # Ingresos brutos
                    'cod115': str,  # Tasa de PPM
                    'cod563Propuesto': str,
                    'categoriaTributaria': int,
                    'periodo': str,
                    'esPropyme': bool,
                    'tasaIDPC': str,
                    'tipoFormulario': str,
                    ...
                },
                'metaData': {...}
            }

        Raises:
            ExtractionError: Si falla la obtención

        Example:
            >>> tasa = extractor.get_tasa_ppmo(
            ...     periodo="202510",
            ...     categoria_tributaria=1,
            ...     cookies=session_cookies
            ... )
            >>> tasa_ppm = tasa['data']['cod115']  # "0.125"
            >>> ingresos = tasa['data']['cod563']  # "3384732"
        """
        try:
            logger.info(f"📊 Fetching PPMO tasa - Period: {periodo}")

            if not cookies:
                raise ExtractionError(
                    "No cookies provided for API request",
                    resource='f29_tasa_ppmo'
                )

            # Extraer RUT sin dígito verificador
            if '-' in self.tax_id:
                rut_sin_dv = self.tax_id.split('-')[0]
                dv = self.tax_id.split('-')[1].upper()
            else:
                rut_sin_dv = self.tax_id[:-1]
                dv = self.tax_id[-1].upper()

            # Extraer mes y año del período
            if len(periodo) != 6:
                raise ValueError(f"Período debe estar en formato YYYYMM, recibido: {periodo}")

            anno = periodo[:4]
            mes = periodo[4:6]

            # URL del endpoint
            url = "https://www4.sii.cl/propuestaf29ui/services/data/facadeAdapterService/getTasaPPMO"

            # Generar IDs para la transacción
            conversation_id = str(uuid.uuid4())[:13].replace('-', '').upper()
            transaction_id = str(uuid.uuid4())

            # Construir payload
            payload = {
                "metaData": {
                    "namespace": "cl.sii.sdi.lob.iva.propuestaf29.data.api.interfaces.FacadeAdapterService/getTasaPPMO",
                    "conversationId": conversation_id,
                    "transactionId": transaction_id
                },
                "data": {
                    "rutContribuyente": rut_sin_dv,
                    "dv": dv,
                    "mes": mes,
                    "anno": anno,
                    "categoriaTributaria": categoria_tributaria,
                    "tipoFormulario": tipo_formulario
                }
            }

            # Convertir cookies a formato dict
            cookies_dict = {c['name']: c['value'] for c in cookies}

            # Headers requeridos
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www4.sii.cl/propuestaf29ui/',
                'Origin': 'https://www4.sii.cl'
            }

            logger.debug(f"🔗 POST {url}")
            logger.debug(f"📦 Payload: periodo={periodo}, rut={rut_sin_dv}-{dv}, categoria={categoria_tributaria}")

            # Hacer la petición
            response = requests.post(
                url,
                json=payload,
                cookies=cookies_dict,
                headers=headers,
                timeout=30
            )

            # Verificar respuesta
            if response.status_code != 200:
                logger.error(f"❌ API returned status {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                raise ExtractionError(
                    f"API request failed with status {response.status_code}",
                    resource='f29_tasa_ppmo'
                )

            # Parsear respuesta
            result = response.json()

            # Verificar estructura
            if 'data' not in result:
                logger.error(f"❌ Unexpected response structure: {list(result.keys())}")
                raise ExtractionError(
                    "Invalid API response structure",
                    resource='f29_tasa_ppmo'
                )

            # Extraer información relevante
            data = result.get('data', {})
            tasa = data.get('cod115')
            ingresos = data.get('cod563')
            es_propyme = data.get('esPropyme', False)

            logger.info(
                f"✅ PPMO tasa retrieved: tasa={tasa}, ingresos={ingresos}, "
                f"propyme={es_propyme}"
            )

            return result

        except requests.RequestException as e:
            logger.error(f"❌ Network error fetching PPMO tasa: {e}")
            raise ExtractionError(
                f"Network error: {str(e)}",
                resource='f29_tasa_ppmo'
            )
        except Exception as e:
            logger.error(f"❌ Error fetching PPMO tasa: {e}")
            raise ExtractionError(
                f"Failed to fetch PPMO tasa: {str(e)}",
                resource='f29_tasa_ppmo'
            )
