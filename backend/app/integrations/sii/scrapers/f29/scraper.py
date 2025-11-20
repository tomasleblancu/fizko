"""
Main F29 Scraper class

Coordinates all F29 scraping operations by delegating to specialized modules.
"""
import logging
from typing import List, Optional

from ..base_scraper import BaseScraper
from ...models.f29_types import FormularioF29
from ...exceptions import ScrapingException

from . import validation
from . import navigation
from . import extraction

logger = logging.getLogger(__name__)


class F29Scraper(BaseScraper):
    """
    Scraper especializado para busqueda de formularios F29

    Proporciona funcionalidad para buscar y listar formularios F29
    en el portal del SII sin necesidad de extraer datos detallados.
    """

    SEARCH_URL = navigation.SEARCH_URL

    def scrape(self, **kwargs) -> dict:
        """
        Implementacion del metodo abstracto scrape

        Redirige a buscar_formularios con los parametros proporcionados
        """
        return {
            'status': 'error',
            'message': 'Use buscar_formularios() method instead',
            'data': None
        }

    def buscar_formularios(
        self,
        anio: Optional[str] = None,
        folio: Optional[str] = None,
        max_retries: int = 3,
        save_callback: Optional[callable] = None
    ) -> List[FormularioF29]:
        """
        Busca formularios F29 en el SII usando la página de rectificar F29

        Args:
            anio: Ano a consultar (YYYY) - obligatorio
            folio: Folio especifico - NO SOPORTADO en esta versión (búsqueda solo anual)
            max_retries: Numero maximo de reintentos para navegacion (no usado)
            save_callback: Callback opcional - NO USADO en esta versión

        Returns:
            Lista de formularios F29 encontrados

        Raises:
            ValueError: Si los parametros no son validos
            ScrapingException: Si hay errores en el scraping
        """
        try:
            # Validar parámetros
            if not anio:
                raise ValueError("Parámetro 'anio' es obligatorio")

            if folio:
                logger.warning("⚠️ Búsqueda por folio no soportada en esta versión, se ignorará")

            logger.info(f"🔎 Iniciando búsqueda F29 - Año: {anio}")

            # Validar sesión al inicio
            if not validation.check_session_valid(self.driver):
                raise ScrapingException("Sesión de Selenium inválida al inicio de búsqueda F29")

            # Navegar a página de búsqueda (rectificar F29)
            navigation.navegar_a_busqueda(self.driver, max_retries)

            # Seleccionar año en el dropdown
            navigation.seleccionar_anio(self.driver, anio)

            # Ejecutar consulta
            navigation.ejecutar_consulta(self.driver)

            # Extraer resultados de la tabla
            # Esta función ahora extrae folio + period + status + id_interno_sii
            resultados = extraction.extraer_resultados(self.driver, save_callback=save_callback)

            # Resumen final
            total = len(resultados)
            con_codint = sum(1 for r in resultados if r.get('id_interno_sii'))
            sin_codint = total - con_codint

            logger.info(
                f"✅ Búsqueda F29 completada: {total} formularios encontrados\n"
                f"   - Con id_interno_sii: {con_codint}\n"
                f"   - Sin id_interno_sii: {sin_codint}"
            )

            if sin_codint > 0:
                logger.warning(
                    f"⚠️ {sin_codint} formularios sin id_interno_sii\n"
                    f"   Estos formularios no podrán descargar PDFs hasta que se extraiga el codInt"
                )

            return resultados

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"❌ Error buscando formularios F29\n"
                f"   Error: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            raise ScrapingException(f"Error en busqueda de formularios: {str(e)}") from e

    def descargar_pdf(
        self,
        folio: str,
        id_interno_sii: str,
        rut: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Descarga el PDF de un formulario F29 desde el SII usando formCompacto

        Args:
            folio: Folio del formulario
            id_interno_sii: ID interno del SII (codInt)
            rut: RUT del contribuyente (opcional, se obtiene del driver si no se proporciona)

        Returns:
            Bytes del PDF descargado, o None si falla

        Raises:
            ScrapingException: Si hay errores en la descarga

        Example:
            >>> pdf = scraper.descargar_pdf(
            ...     folio="8104678626",
            ...     id_interno_sii="817935151",
            ...     rut="77794858"
            ... )
        """
        import requests

        try:
            logger.info(f"📥 Descargando PDF F29: folio={folio}, codInt={id_interno_sii}")

            # Obtener RUT sin dígito verificador
            if not rut:
                # Intentar obtener del driver si hay sesión activa
                rut = getattr(self.driver, 'tax_id', None)
                if not rut:
                    raise ScrapingException("RUT is required for PDF download")

            # Extraer RUT sin DV
            if '-' in rut:
                rut_sin_dv = rut.split('-')[0]
            else:
                rut_sin_dv = rut[:-1]  # Remover último carácter (DV)

            # Construir URL del formulario compacto
            url = (
                f"https://www4.sii.cl/rfiInternet/formCompacto"
                f"?folio={folio}"
                f"&rut={rut_sin_dv}"
                f"&form=029"  # F29
                f"&codInt={id_interno_sii}"
            )

            logger.debug(f"URL de descarga: {url}")

            # Obtener cookies del driver de Selenium
            selenium_cookies = self.driver.get_cookies()

            # Convertir cookies a formato dict
            cookies_dict = {c['name']: c['value'] for c in selenium_cookies}

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www4.sii.cl/sifmConsultaInternet/',
                'Accept': 'application/pdf'
            }

            # Descargar el PDF con requests
            response = requests.get(url, cookies=cookies_dict, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"❌ Error en descarga: HTTP {response.status_code}")
                return None

            # Verificar que el contenido es un PDF
            if not response.content.startswith(b'%PDF'):
                content_type = response.headers.get('Content-Type', '')
                logger.error(f"❌ Content-Type: {content_type}")
                logger.error(f"❌ Primeros 500 chars: {response.text[:500]}")
                logger.error("❌ El contenido descargado no es un PDF válido")
                return None

            pdf_bytes = response.content
            logger.info(f"✅ PDF descargado exitosamente: {len(pdf_bytes):,} bytes")

            return pdf_bytes

        except Exception as e:
            logger.error(f"❌ Error descargando PDF: {str(e)}")
            raise ScrapingException(f"Error descargando PDF F29: {str(e)}") from e
