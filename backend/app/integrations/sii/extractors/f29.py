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

    def __init__(self, driver: Optional[SeleniumDriver], tax_id: str):
        """
        Inicializa el extractor

        Args:
            driver: Instancia de SeleniumDriver (opcional, solo necesario para búsqueda)
            tax_id: RUT del contribuyente
        """
        self.driver = driver
        self.tax_id = tax_id
        self._list_scraper = F29Scraper(driver) if driver else None

        logger.info("📋 F29Extractor initialized")

    def search(self, anio: str, folio: Optional[str] = None) -> List[Dict]:
        """
        Busca formularios F29 (requiere Selenium driver)

        Args:
            anio: Año (formato YYYY, ej: "2024")
            folio: Folio específico (opcional)

        Returns:
            Lista de formularios F29 encontrados

        Raises:
            ExtractionError: Si falla la búsqueda o no hay driver disponible
        """
        if not self.driver or not self._list_scraper:
            raise ExtractionError(
                "Search requires a Selenium driver, but none was provided",
                resource='f29_search'
            )

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

    def download_formulario_compacto_pdf(
        self,
        folio: str,
        id_interno_sii: str,
        form_type: str = '029',
        cookies: Optional[List[Dict]] = None
    ) -> Optional[bytes]:
        """
        Descarga el PDF del formulario compacto usando requests (sin Selenium)

        Args:
            folio: Folio real del formulario (ej: "8104678626")
            id_interno_sii: ID interno del SII (codInt) (ej: "817935151")
            form_type: Tipo de formulario (default: '029' para F29)
            cookies: Lista de cookies para autenticación (requerido)

        Returns:
            Contenido del PDF en bytes

        Raises:
            ExtractionError: Si falla la descarga

        Example:
            >>> pdf_bytes = extractor.download_formulario_compacto_pdf(
            ...     folio="8104678626",
            ...     id_interno_sii="817935151",
            ...     cookies=session_cookies
            ... )
            >>> with open('f29.pdf', 'wb') as f:
            ...     f.write(pdf_bytes)
        """
        if not cookies:
            raise ExtractionError(
                "Cookies are required for PDF download",
                resource='f29_pdf'
            )

        try:
            # Extraer RUT sin dígito verificador
            if '-' in self.tax_id:
                rut_sin_dv = self.tax_id.split('-')[0]
            else:
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

            # Convertir cookies a formato dict
            cookies_dict = {c['name']: c['value'] for c in cookies}

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www4.sii.cl/sifmConsultaInternet/',
                'Accept': 'application/pdf'
            }

            response = requests.get(url, cookies=cookies_dict, headers=headers, timeout=30)

            # Verificar respuesta exitosa
            if response.status_code != 200:
                raise ExtractionError(
                    f"HTTP {response.status_code} al descargar PDF",
                    resource='f29_pdf'
                )

            # Verificar que sea un PDF válido
            if not response.content.startswith(b'%PDF'):
                logger.error(f"Respuesta no es un PDF válido. Content-Type: {response.headers.get('content-type')}")
                raise ExtractionError(
                    "La respuesta no es un PDF válido",
                    resource='f29_pdf'
                )

            logger.info(f"✅ PDF downloaded successfully ({len(response.content)} bytes)")
            return response.content

        except requests.RequestException as e:
            logger.error(f"❌ Network error downloading PDF: {e}")
            raise ExtractionError(
                f"Network error: {str(e)}",
                resource='f29_pdf'
            )
        except Exception as e:
            logger.error(f"❌ Error downloading compact form PDF: {e}")
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
