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
    FORM_CODE = navigation.FORM_CODE

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
        Busca formularios F29 en el SII

        Args:
            anio: Ano a consultar (YYYY) - obligatorio si no se busca por folio
            folio: Folio especifico - opcional
            max_retries: Numero maximo de reintentos para navegacion
            save_callback: Callback opcional (síncrono) para guardar cada formulario
                          inmediatamente después de extraer su id_interno_sii.
                          Firma: def callback(formulario: Dict) -> None

        Returns:
            Lista de formularios F29 encontrados

        Raises:
            ValueError: Si los parametros no son validos
            ScrapingException: Si hay errores en el scraping
        """
        try:
            # Validar parametros
            validation.validar_parametros(anio, folio)

            logger.info(f"🔎 Iniciando búsqueda F29 - Año: {anio}, Folio: {folio}")

            # Validar sesión al inicio
            if not validation.check_session_valid(self.driver):
                raise ScrapingException("Sesión de Selenium inválida al inicio de búsqueda F29")

            # Navegar a pagina de busqueda
            navigation.navegar_a_busqueda(self.driver, max_retries)

            # Click en "Buscar Formulario"
            navigation.click_buscar_formulario(self.driver)

            # Seleccionar tipo y codigo de formulario
            navigation.seleccionar_tipo_formulario(self.driver)

            # Configurar criterios de busqueda
            navigation.configurar_criterios_busqueda(self.driver, anio, folio)

            # Ejecutar consulta y capturar response GWT
            gwt_response = navigation.ejecutar_consulta(self.driver)

            # Extraer resultados de la tabla HTML con codInt incluido
            # El codInt se extrae haciendo click en "Ver" → "Formulario Compacto"
            # y capturando la URL que se abre en la nueva ventana
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

    def descargar_pdf(self, id_interno_sii: str) -> Optional[bytes]:
        """
        Descarga el PDF de un formulario F29 desde el SII

        Args:
            id_interno_sii: ID interno del formulario en el sistema del SII

        Returns:
            Bytes del PDF descargado, o None si falla

        Raises:
            ScrapingException: Si hay errores en la descarga
        """
        import time
        import requests

        try:
            logger.info(f"📥 Descargando PDF F29 con ID interno: {id_interno_sii}")

            # URL para descargar el PDF del F29
            # El parámetro 'idDoc' es el id_interno_sii
            download_url = f"https://www4.sii.cl/svctsiiInternet/rtc?idDoc={id_interno_sii}"

            logger.debug(f"URL de descarga: {download_url}")

            # Navegar a la URL de descarga
            self.driver.navigate_to(download_url)

            # Esperar a que se cargue la respuesta
            time.sleep(3)

            # Usar requests para descargar el PDF con las cookies del driver
            # Obtener cookies del driver de Selenium
            selenium_cookies = self.driver.get_cookies()

            # Convertir cookies de Selenium a formato de requests
            session = requests.Session()
            for cookie in selenium_cookies:
                session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain'),
                    path=cookie.get('path', '/')
                )

            # Descargar el PDF
            logger.debug("Descargando PDF con requests...")
            response = session.get(download_url, timeout=30)

            if response.status_code != 200:
                logger.error(f"❌ Error en descarga: HTTP {response.status_code}")
                return None

            # Verificar que el contenido es un PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"⚠️ Content-Type inesperado: {content_type}")
                # Verificar si el contenido empieza con el magic number de PDF
                if not response.content.startswith(b'%PDF'):
                    logger.error("❌ El contenido descargado no es un PDF válido")
                    return None

            pdf_bytes = response.content
            logger.info(f"✅ PDF descargado exitosamente: {len(pdf_bytes):,} bytes")

            return pdf_bytes

        except Exception as e:
            logger.error(f"❌ Error descargando PDF: {str(e)}")
            raise ScrapingException(f"Error descargando PDF F29: {str(e)}") from e
