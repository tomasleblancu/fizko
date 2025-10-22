"""
Scraper especializado para formularios F29
"""
import time
import logging
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from .base_scraper import BaseScraper
from ..models.f29_types import FormularioF29
from ..exceptions import ScrapingException

logger = logging.getLogger(__name__)


class F29Scraper(BaseScraper):
    """
    Scraper especializado para busqueda de formularios F29

    Proporciona funcionalidad para buscar y listar formularios F29
    en el portal del SII sin necesidad de extraer datos detallados.
    """

    SEARCH_URL = "https://www4.sii.cl/sifmConsultaInternet/index.html?dest=cifxx&form=29"
    FORM_CODE = "29"

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
        max_retries: int = 3
    ) -> List[FormularioF29]:
        """
        Busca formularios F29 en el SII

        Args:
            anio: Ano a consultar (YYYY) - obligatorio si no se busca por folio
            folio: Folio especifico - opcional
            max_retries: Numero maximo de reintentos para navegacion

        Returns:
            Lista de formularios F29 encontrados

        Raises:
            ValueError: Si los parametros no son validos
            ScrapingException: Si hay errores en el scraping
        """
        try:
            # Validar parametros
            self._validar_parametros(anio, folio)

            logger.info(f"Buscando F29 - Ano: {anio}, Folio: {folio}")

            # Navegar a pagina de busqueda
            self._navegar_a_busqueda(max_retries)

            # Click en "Buscar Formulario"
            self._click_buscar_formulario()

            # Seleccionar tipo y codigo de formulario
            self._seleccionar_tipo_formulario()

            # Configurar criterios de busqueda
            self._configurar_criterios_busqueda(anio, folio)

            # Ejecutar consulta y capturar response GWT
            gwt_response = self._ejecutar_consulta()

            # Extraer resultados de la tabla HTML
            resultados = self._extraer_resultados()

            # Parsear response GWT para obtener id_interno_sii de cada formulario
            if gwt_response:
                resultados = self._enriquecer_con_gwt_data(resultados, gwt_response)

            logger.info(f"Busqueda completada: {len(resultados)} formularios")
            return resultados

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error buscando formularios: {str(e)}")
            raise ScrapingException(f"Error en busqueda de formularios: {str(e)}") from e

    def _validar_parametros(
        self,
        anio: Optional[str],
        folio: Optional[str]
    ) -> None:
        """Valida que los parametros de busqueda sean correctos"""
        if not folio and not anio:
            raise ValueError("Debe especificar ano o folio para buscar")

        if anio and (not anio.isdigit() or len(anio) != 4):
            raise ValueError("El ano debe ser un numero de 4 digitos")

    def _navegar_a_busqueda(self, max_retries: int) -> None:
        """Navega a la pagina de busqueda con reintentos"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Navegando a busqueda (intento {attempt + 1}/{max_retries})")
                self.driver.navigate_to(self.SEARCH_URL)
                time.sleep(3)  # Aumentado de 2 a 3 segundos

                # Verificar múltiples indicadores de que la página cargó
                page_source = self.driver.driver.page_source

                # Verificar si ya estamos en el formulario de búsqueda
                try:
                    listboxes = self.driver.driver.find_elements(By.CLASS_NAME, "gwt-ListBox")
                    if len(listboxes) >= 2:
                        logger.info("✅ Formulario de búsqueda ya cargado directamente")
                        return
                except:
                    pass

                # Verificar si aparece el botón o texto de búsqueda
                if "Buscar Formulario" in page_source or "buscar" in page_source.lower() or "gwt-" in page_source:
                    logger.info("Pagina de busqueda cargada")
                    return

                if attempt < max_retries - 1:
                    logger.warning(f"Pagina no cargo correctamente (intento {attempt + 1})")
                    # Refrescar la página puede ayudar
                    self.driver.driver.refresh()
                    time.sleep(3)
                    continue
                else:
                    logger.warning("Continuando a pesar de no detectar pagina...")
                    return  # Continuar de todas formas

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Error navegando (intento {attempt + 1}): {str(e)}")
                    time.sleep(3)
                    continue
                else:
                    raise ScrapingException(f"No se pudo navegar a busqueda: {str(e)}") from e

    def _click_buscar_formulario(self) -> None:
        """Click en boton 'Buscar Formulario' o verifica si ya está en el formulario"""
        try:
            # Primero verificar si ya estamos en el formulario de búsqueda
            # (puede suceder si la sesión reutilizada ya tiene la página cargada)
            try:
                listboxes = self.driver.driver.find_elements(By.CLASS_NAME, "gwt-ListBox")
                if len(listboxes) >= 2:
                    logger.info("✅ Formulario de búsqueda ya está cargado, saltando click en botón")
                    return
            except:
                pass  # Continuar con el click normal

            # Intentar con múltiples selectores para el botón
            button_selectors = [
                "//button[contains(@class, 'gw-button-blue-bootstrap') and contains(text(), 'Buscar Formulario')]",
                "//button[contains(text(), 'Buscar Formulario')]",
                "//button[contains(@class, 'gw-button-blue')]",
                "//*[contains(text(), 'Buscar Formulario')]"
            ]

            buscar_button = None
            last_error = None

            for selector in button_selectors:
                try:
                    buscar_button = self.driver.wait_for_clickable(
                        By.XPATH,
                        selector,
                        timeout=10
                    )
                    if buscar_button:
                        logger.debug(f"Botón encontrado con selector: {selector}")
                        break
                except Exception as e:
                    last_error = e
                    continue

            if not buscar_button:
                raise ScrapingException(
                    f"No se pudo encontrar el botón 'Buscar Formulario' con ningún selector. "
                    f"Último error: {str(last_error)}"
                )

            buscar_button.click()
            time.sleep(1)
            logger.debug("Click en 'Buscar Formulario'")

        except Exception as e:
            if "No se pudo encontrar el botón" in str(e):
                raise
            raise ScrapingException(f"No se pudo hacer click en 'Buscar Formulario': {str(e)}") from e

    def _seleccionar_tipo_formulario(self) -> None:
        """Selecciona el tipo de formulario (DPS) y codigo (29)"""
        try:
            # Seleccionar tipo DPS (Formularios de Impuesto)
            tipo_select = self.driver.wait_for_element(
                By.CLASS_NAME,
                "gwt-ListBox",
                timeout=30
            )
            self.driver.select_option_by_value(tipo_select, "DPS")
            time.sleep(0.5)
            logger.debug("Tipo DPS seleccionado")

            # Seleccionar codigo 29
            listboxes = self.driver.wait_for_elements(
                By.CLASS_NAME,
                "gwt-ListBox",
                timeout=30
            )

            if len(listboxes) < 2:
                raise ScrapingException("No se encontraron suficientes dropdowns")

            codigo_select = listboxes[1]

            # Verificar que el codigo esta disponible
            opciones = [
                opt.get_attribute("value")
                for opt in codigo_select.find_elements(By.TAG_NAME, "option")
            ]
            logger.debug(f"Opciones disponibles: {opciones}")

            if self.FORM_CODE not in opciones:
                raise ScrapingException(
                    f"Codigo '{self.FORM_CODE}' no disponible. Opciones: {opciones}"
                )

            self.driver.select_option_by_value(codigo_select, self.FORM_CODE)
            time.sleep(0.5)
            logger.debug("Codigo F29 seleccionado")

        except Exception as e:
            raise ScrapingException(f"Error seleccionando tipo de formulario: {str(e)}") from e

    def _configurar_criterios_busqueda(
        self,
        anio: Optional[str],
        folio: Optional[str]
    ) -> None:
        """Configura los criterios de busqueda (folio o anual)"""
        try:
            if folio:
                self._busqueda_por_folio(folio)
            else:
                self._busqueda_anual(anio)

        except Exception as e:
            raise ScrapingException(f"Error configurando criterios: {str(e)}") from e

    def _busqueda_por_folio(self, folio: str) -> None:
        """Configura busqueda por folio"""
        folio_radio = self.driver.wait_for_element(
            By.XPATH,
            "//label[contains(text(), 'Folio')]/..//input",
            timeout=30
        )
        folio_radio.click()

        folio_input = self.driver.wait_for_element(
            By.CLASS_NAME,
            "gwt-TextBox",
            timeout=30
        )
        folio_input.send_keys(folio)
        logger.debug(f"Busqueda por folio: {folio}")

    def _busqueda_anual(self, anio: str) -> None:
        """Configura busqueda anual"""
        anual_radio = self.driver.wait_for_element(
            By.XPATH,
            "//label[contains(text(), 'Anual')]/..//input",
            timeout=30
        )
        anual_radio.click()

        selects = self.driver.wait_for_elements(
            By.CLASS_NAME,
            "gwt-ListBox",
            timeout=30
        )

        # El select de ano anual esta en posicion 2
        anio_select = selects[2]
        self.driver.select_option_by_value(anio_select, anio)
        logger.debug(f"Busqueda anual: {anio}")

    def _ejecutar_consulta(self) -> str:
        """
        Ejecuta la consulta haciendo click en 'Consultar' y captura el response GWT

        Returns:
            Response body del request GWT-RPC automático, o string vacío si no se captura
        """
        try:
            consultar_button = self.driver.wait_for_clickable(
                By.XPATH,
                "//button[contains(text(), 'Consultar')]",
                timeout=30
            )
            consultar_button.click()

            # Esperar a que se ejecute el request GWT-RPC automático
            time.sleep(2)  # Aumentado para dar tiempo al request

            # Capturar el response GWT del performance log
            # Filtrar por el método específico getDocumentosBusqueda
            from ..core.auth_handler import capture_gwt_response
            gwt_response = capture_gwt_response(
                self.driver,
                url_filter="svcConsulta",
                method_filter="getDocumentosBusqueda"
            )

            logger.debug("Consulta ejecutada")
            return gwt_response

        except Exception as e:
            raise ScrapingException(f"Error ejecutando consulta: {str(e)}") from e

    def _extraer_resultados(self) -> List[FormularioF29]:
        """Extrae los resultados de la tabla"""
        resultados: List[FormularioF29] = []

        try:
            tabla = self.driver.wait_for_element(
                By.CLASS_NAME,
                "gw-detalle-center-busqueda",
                timeout=30
            )

            filas = tabla.find_elements(By.TAG_NAME, "tr")[1:]  # Ignorar header
            logger.info(f"Encontradas {len(filas)} filas")

            for i, fila in enumerate(filas):
                try:
                    celdas = fila.find_elements(By.TAG_NAME, "td")
                    if len(celdas) >= 7:
                        # Limpiar y convertir monto
                        monto_texto = celdas[5].text.replace(',', '').replace('$', '').replace('.', '').strip()
                        try:
                            monto = int(monto_texto) if monto_texto.isdigit() else 0
                        except (ValueError, TypeError):
                            monto = 0

                        formulario: FormularioF29 = {
                            "folio": celdas[1].text.strip(),
                            "period": celdas[0].text.strip(),
                            "contributor": celdas[2].text.strip(),
                            "submission_date": celdas[3].text.strip(),
                            "status": celdas[4].text.strip(),
                            "amount": monto
                        }
                        resultados.append(formulario)
                        logger.debug(f"F29 {i+1}: {formulario['folio']} - {formulario['period']}")

                except Exception as e:
                    logger.warning(f"Error procesando fila {i+1}: {str(e)}")
                    continue

        except TimeoutException:
            logger.warning("No se encontraron resultados")

        return resultados

    def _enriquecer_con_gwt_data(
        self,
        resultados_tabla: List[FormularioF29],
        gwt_response: str
    ) -> List[FormularioF29]:
        """
        Enriquece los resultados de la tabla con id_interno_sii del response GWT

        Args:
            resultados_tabla: Formularios extraídos de la tabla HTML
            gwt_response: Response body del GWT-RPC

        Returns:
            Lista de formularios enriquecidos con id_interno_sii
        """
        try:
            import re

            # Parsear response GWT usando mismo patrón que en servicev2.py
            if not gwt_response.startswith("//OK"):
                logger.warning(f"⚠️ Response GWT no tiene formato esperado")
                return resultados_tabla

            # Patrón: "dd/mm/yyyy","folio_interno","Mxx"
            pattern = r'"(\d{2}/\d{2}/\d{4})","(\d+)","(M\d+)"'
            matches = re.findall(pattern, gwt_response)

            if not matches:
                logger.warning(f"⚠️ No se encontraron datos GWT en response")
                return resultados_tabla

            # Crear diccionario de período -> id_interno_sii
            gwt_data_by_period = {}
            for fecha, folio_interno, mes_codigo in matches:
                # Extraer año de la fecha (formato dd/mm/yyyy)
                year = int(fecha.split('/')[-1])

                # Extraer número de mes del código (M01 -> 1)
                mes_match = re.match(r'M(\d+)', mes_codigo)
                mes = int(mes_match.group(1)) if mes_match else None

                if mes and year:
                    # Formato período: "YYYY-MM" (debe coincidir con period de la tabla)
                    period_key = f"{year}-{mes:02d}"
                    gwt_data_by_period[period_key] = folio_interno

            logger.info(f"📊 Datos GWT parseados: {len(gwt_data_by_period)} períodos")

            # Enriquecer resultados de tabla con id_interno_sii
            resultados_enriquecidos = []
            for formulario in resultados_tabla:
                period = formulario.get('period', '')

                # Buscar id_interno_sii correspondiente
                id_interno = gwt_data_by_period.get(period)

                if id_interno:
                    # Crear copia con id_interno_sii
                    formulario_enriquecido = formulario.copy()
                    formulario_enriquecido['id_interno_sii'] = id_interno
                    resultados_enriquecidos.append(formulario_enriquecido)
                    logger.debug(f"✅ Enriquecido {period}: id_interno_sii={id_interno}")
                else:
                    # Si no encontramos match, agregar sin id_interno_sii
                    resultados_enriquecidos.append(formulario)
                    logger.warning(f"⚠️ No se encontró id_interno_sii para período {period}")

            logger.info(f"✅ {len(resultados_enriquecidos)} formularios enriquecidos con id_interno_sii")
            return resultados_enriquecidos

        except Exception as e:
            logger.error(f"❌ Error enriqueciendo con datos GWT: {str(e)}")
            # Retornar resultados originales si hay error
            return resultados_tabla
