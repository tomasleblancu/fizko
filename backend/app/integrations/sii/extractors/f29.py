"""
Extractor de formularios F29
"""
import logging
import requests
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
