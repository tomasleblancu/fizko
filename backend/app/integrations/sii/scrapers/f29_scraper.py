"""
Scraper especializado para formularios F29
"""
import time
import logging
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    InvalidSessionIdException,
    WebDriverException,
    NoSuchWindowException
)

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

    def _check_session_valid(self) -> bool:
        """
        Verifica si la sesión de Selenium sigue activa

        Returns:
            True si la sesión está activa, False si no
        """
        try:
            _ = self.driver.driver.current_url
            _ = self.driver.driver.window_handles
            return True
        except (InvalidSessionIdException, WebDriverException) as e:
            logger.warning(f"⚠️ Sesión de Selenium inválida detectada: {type(e).__name__}")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Error verificando sesión: {type(e).__name__}: {e}")
            return False

    def _take_debug_screenshot(self, context: str, folio: str = "unknown") -> None:
        """
        Toma screenshot y guarda HTML para debugging en Supabase Storage

        Args:
            context: Contexto del error (ej: "click_intercepted", "codint_extraction", etc.)
            folio: Folio del formulario siendo procesado
        """
        try:
            from app.services.storage import get_debug_storage
            import tempfile

            timestamp = int(time.time())
            storage = get_debug_storage()

            # Info adicional de contexto
            context_info = ""
            try:
                current_url = self.driver.driver.current_url
                window_count = len(self.driver.driver.window_handles)
                context_info = f"URL={current_url}, Windows={window_count}"
                logger.error(f"🔍 Context: {context_info}")
            except:
                pass

            # Screenshot a Supabase
            try:
                # Guardar screenshot temporalmente
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                    self.driver.driver.save_screenshot(tmp_path)

                    # Leer bytes y subir a Supabase
                    with open(tmp_path, 'rb') as f:
                        screenshot_bytes = f.read()

                    success, url, error = storage.upload_screenshot(
                        process="f29",
                        context=context,
                        folio=folio,
                        timestamp=timestamp,
                        screenshot_bytes=screenshot_bytes
                    )

                    if success:
                        logger.error(f"📸 Screenshot guardado en Supabase: {url}")
                    else:
                        logger.warning(f"⚠️ No se pudo guardar screenshot en Supabase: {error}")

                    # Limpiar archivo temporal
                    import os
                    os.unlink(tmp_path)

            except Exception as ss_error:
                logger.warning(f"⚠️ No se pudo guardar screenshot: {ss_error}")

            # HTML source a Supabase
            try:
                html_content = self.driver.driver.page_source

                # Agregar contexto al HTML
                html_with_context = f"""
<!-- DEBUG CONTEXT -->
<!-- Timestamp: {timestamp} -->
<!-- Folio: {folio} -->
<!-- Context: {context} -->
<!-- Info: {context_info} -->

{html_content}
"""

                success, url, error = storage.upload_html(
                    process="f29",
                    context=context,
                    folio=folio,
                    timestamp=timestamp,
                    html_content=html_with_context
                )

                if success:
                    logger.error(f"📄 HTML guardado en Supabase: {url}")
                else:
                    logger.warning(f"⚠️ No se pudo guardar HTML en Supabase: {error}")

            except Exception as html_error:
                logger.warning(f"⚠️ No se pudo guardar HTML: {html_error}")

        except Exception as e:
            logger.warning(f"⚠️ Error en _take_debug_screenshot: {e}")

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
            self._validar_parametros(anio, folio)

            logger.info(f"🔎 Iniciando búsqueda F29 - Año: {anio}, Folio: {folio}")

            # Validar sesión al inicio
            if not self._check_session_valid():
                raise ScrapingException("Sesión de Selenium inválida al inicio de búsqueda F29")

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

            # Extraer resultados de la tabla HTML con codInt incluido
            # El codInt se extrae haciendo click en "Ver" → "Formulario Compacto"
            # y capturando la URL que se abre en la nueva ventana
            resultados = self._extraer_resultados(save_callback=save_callback)

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
                time.sleep(3)

                # Verificar URL después de navegar (para detectar redirects al login)
                current_url = self.driver.driver.current_url

                # Detectar si fuimos redirigidos al login
                if "AUT2000" in current_url or "IngresoRutClave" in current_url:
                    logger.error(f"❌ Redirigido al login - sesión no válida")
                    raise ScrapingException(
                        "Redirigido a página de login - sesión no válida. "
                        "Las cookies de autenticación no se están propagando correctamente"
                    )

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
            # Esperar un poco más para que cargue completamente (GWT es lento)
            time.sleep(3)

            # Primero verificar si ya estamos en el formulario de búsqueda
            try:
                listboxes = self.driver.driver.find_elements(By.CLASS_NAME, "gwt-ListBox")
                if len(listboxes) >= 2:
                    logger.info("✅ Formulario de búsqueda ya está cargado")
                    return
            except:
                pass  # Continuar con el click normal

            # Intentar con múltiples selectores para el botón
            button_selectors = [
                "//button[contains(@class, 'gw-button-blue-bootstrap') and contains(text(), 'Buscar Formulario')]",
                "//button[contains(text(), 'Buscar Formulario')]",
                "//button[contains(@class, 'gw-button-blue')]",
                "//a[contains(text(), 'Buscar Formulario')]",
                "//*[contains(text(), 'Buscar Formulario')]"
            ]

            buscar_button = None
            last_error = None

            for i, selector in enumerate(button_selectors, 1):
                try:
                    buscar_button = self.driver.wait_for_clickable(
                        By.XPATH,
                        selector,
                        timeout=15
                    )
                    if buscar_button:
                        logger.debug(f"Botón encontrado con selector {i}")
                        break
                except Exception as e:
                    last_error = e
                    continue

            if not buscar_button:
                # Tomar screenshot para debugging
                import os
                timestamp = int(time.time())
                screenshot_dir = "/app/screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)

                screenshot_path = f"{screenshot_dir}/f29_error_{timestamp}.png"
                html_path = f"{screenshot_dir}/f29_error_{timestamp}.html"

                logger.error(f"❌ No se pudo encontrar el botón 'Buscar Formulario'")

                try:
                    self.driver.driver.save_screenshot(screenshot_path)
                    logger.error(f"📸 Screenshot: backend/screenshots/f29_error_{timestamp}.png")
                except Exception as screenshot_error:
                    logger.warning(f"⚠️ No se pudo guardar screenshot: {screenshot_error}")

                try:
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.driver.page_source)
                    logger.error(f"📄 HTML: backend/screenshots/f29_error_{timestamp}.html")
                except Exception as html_error:
                    logger.warning(f"⚠️ No se pudo guardar HTML: {html_error}")

                raise ScrapingException(
                    f"No se pudo encontrar el botón 'Buscar Formulario'. "
                    f"Último error: {str(last_error)}"
                )

            buscar_button.click()
            time.sleep(2)
            logger.debug("Click en 'Buscar Formulario' exitoso")

        except Exception as e:
            if "No se pudo encontrar el botón" in str(e):
                raise
            raise ScrapingException(f"Error en click 'Buscar Formulario': {str(e)}") from e

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

    def _extraer_codint_from_formulario_compacto(self, folio_text: str) -> Optional[str]:
        """
        Extrae el codInt haciendo click en "Formulario Compacto" y capturando la URL

        Este método debe ejecutarse cuando ya estamos en la vista de detalle del folio
        (después de hacer click en "Ver")

        Args:
            folio_text: Texto del folio para logging

        Returns:
            codInt (id_interno_sii) o None si no se encuentra
        """
        import re
        import time

        # Validar sesión ANTES de intentar operaciones
        if not self._check_session_valid():
            logger.error(
                f"❌ SESIÓN INVÁLIDA antes de extraer codInt para folio {folio_text}\n"
                f"   La sesión de Selenium ya estaba cerrada/expirada antes de comenzar"
            )
            return None

        try:
            logger.debug(f"🔍 Iniciando extracción de codInt para folio {folio_text}")

            # Paso 1: Buscar el botón "Formulario Compacto"
            logger.debug(f"   [1/6] Buscando botón 'Formulario Compacto'...")
            formulario_compacto_btn = self.driver.driver.find_element(
                By.XPATH,
                "//button[contains(text(), 'Formulario Compacto')]"
            )
            logger.debug(f"   [1/6] ✓ Botón encontrado")

            # Paso 2: Guardar ventanas actuales
            logger.debug(f"   [2/6] Obteniendo ventanas actuales...")
            ventanas_antes = self.driver.driver.window_handles
            logger.debug(f"   [2/6] ✓ Ventanas antes: {len(ventanas_antes)}")

            # Paso 3: Click en Formulario Compacto (abrirá nueva pestaña con el PDF)
            logger.debug(f"   [3/6] Haciendo click en 'Formulario Compacto'...")
            formulario_compacto_btn.click()
            logger.debug(f"   [3/6] ✓ Click realizado, esperando 3s (más tiempo en Docker)...")
            time.sleep(3)  # Aumentado a 3s para dar más tiempo en Docker

            # Paso 4: Verificar sesión después del click
            logger.debug(f"   [4/6] Verificando sesión después del click...")
            if not self._check_session_valid():
                logger.error(f"   [4/6] ❌ SESIÓN SE INVALIDÓ DESPUÉS DEL CLICK en 'Formulario Compacto'")
                return None
            logger.debug(f"   [4/6] ✓ Sesión sigue válida")

            # Paso 5: Verificar si se abrió nueva pestaña
            logger.debug(f"   [5/6] Verificando nuevas ventanas...")
            ventanas_despues = self.driver.driver.window_handles
            logger.debug(f"   [5/6] ✓ Ventanas después: {len(ventanas_despues)}")

            if len(ventanas_despues) > len(ventanas_antes):
                # Paso 6a: Cambiar a la nueva pestaña
                logger.debug(f"   [6a] Cambiando a nueva ventana...")
                nueva_ventana = ventanas_despues[-1]
                self.driver.driver.switch_to.window(nueva_ventana)
                logger.debug(f"   [6a] ✓ Cambiado a ventana nueva")

                # Verificar sesión después del switch
                if not self._check_session_valid():
                    logger.error(f"   [6a] ❌ SESIÓN SE INVALIDÓ DESPUÉS DE switch_to.window()")
                    return None

                # Obtener la URL (contiene el codInt)
                logger.debug(f"   [6b] Obteniendo URL del formulario compacto...")
                url_compacto = self.driver.driver.current_url
                logger.debug(f"   [6b] ✓ URL Formulario Compacto: {url_compacto}")

                # Extraer codInt de la URL usando regex
                # Formato: ...?folio=XXX&rut=YYY&form=029&codInt=ZZZ
                match = re.search(r'codInt=(\d+)', url_compacto)

                cod_int = None
                if match:
                    cod_int = match.group(1)
                    logger.debug(f"   [6c] ✅ codInt extraído de URL: {cod_int}")
                else:
                    logger.warning(f"   [6c] ⚠️ No se encontró codInt en URL: {url_compacto}")

                # Cerrar la pestaña del PDF y volver a la anterior
                logger.debug(f"   [6d] Cerrando ventana del PDF...")
                self.driver.driver.close()
                logger.debug(f"   [6d] ✓ Ventana cerrada")

                # Volver a la ventana original
                # NOTA: No verificamos la sesión aquí porque window_handles puede fallar temporalmente
                # después de close(), pero switch_to.window() funciona correctamente
                logger.debug(f"   [6e] Volviendo a ventana original...")
                try:
                    self.driver.driver.switch_to.window(ventanas_antes[0])
                    logger.debug(f"   [6e] ✓ Vuelto a ventana original")
                except Exception as e:
                    logger.warning(f"   [6e] ⚠️ Error al volver a ventana: {e}")
                    # Aún así, devolver el codInt que ya extrajimos
                    return cod_int

                logger.debug(f"   ✅ Extracción completada exitosamente: codInt={cod_int}")
                return cod_int
            else:
                logger.warning("⚠️ No se abrió nueva pestaña al hacer click en Formulario Compacto")
                return None

        except InvalidSessionIdException as e:
            # 📸 CAPTURAR SCREENSHOT si la sesión todavía permite
            try:
                self._take_debug_screenshot("invalid_session_codint", folio_text)
            except:
                pass  # Sesión ya inválida, no se puede capturar

            logger.error(
                f"🔴 INVALID SESSION ID para folio {folio_text}\n"
                f"   Error: {e}\n"
                f"   Tipo: {type(e).__name__}\n"
                f"   Causa probable: La sesión de Selenium expiró durante la operación\n"
                f"   Posibles razones:\n"
                f"     - Timeout del navegador (inactividad)\n"
                f"     - Driver cerrado prematuramente por otro proceso\n"
                f"     - Problema de red con Selenium/ChromeDriver\n"
                f"     - Navegador crasheó o fue cerrado manualmente",
                exc_info=True
            )
            return None

        except NoSuchWindowException as e:
            logger.error(
                f"🪟 VENTANA NO ENCONTRADA para folio {folio_text}\n"
                f"   Error: {e}\n"
                f"   Tipo: {type(e).__name__}\n"
                f"   La ventana/pestaña que intentamos usar ya no existe\n"
                f"   Posible causa: El navegador cerró la pestaña automáticamente",
                exc_info=True
            )
            return None

        except WebDriverException as e:
            # 📸 CAPTURAR SCREENSHOT si es posible
            try:
                self._take_debug_screenshot("webdriver_codint", folio_text)
            except:
                pass  # No se puede capturar si el driver falló

            logger.error(
                f"🌐 WEBDRIVER ERROR para folio {folio_text}\n"
                f"   Error: {e}\n"
                f"   Tipo: {type(e).__name__}\n"
                f"   Error general de comunicación con el navegador\n"
                f"   Posibles causas:\n"
                f"     - ChromeDriver no responde\n"
                f"     - Navegador no responde\n"
                f"     - Problema de red entre Selenium y Chrome",
                exc_info=True
            )
            return None

        except Exception as e:
            logger.error(
                f"❌ ERROR INESPERADO extrayendo codInt para folio {folio_text}\n"
                f"   Error: {e}\n"
                f"   Tipo: {type(e).__name__}\n"
                f"   Este es un error no manejado específicamente",
                exc_info=True
            )

            # Asegurarse de volver a la ventana original en caso de error
            # Solo si la sesión sigue válida
            if self._check_session_valid():
                try:
                    ventanas = self.driver.driver.window_handles
                    if len(ventanas) > 1:
                        logger.debug("🔄 Intentando cerrar ventanas adicionales...")
                        self.driver.driver.close()
                        self.driver.driver.switch_to.window(ventanas[0])
                        logger.debug("✅ Ventanas cerradas correctamente")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Error limpiando ventanas: {cleanup_error}")
            else:
                logger.warning("⚠️ No se puede limpiar ventanas: sesión inválida")

            return None

    def _descargar_pdf_desde_modal(self, folio_link, folio_text: str, rut: str) -> Optional[bytes]:
        """
        Hace click en el folio para abrir el modal, captura la URL del PDF y lo descarga

        Args:
            folio_link: WebElement del link <a> del folio
            folio_text: Texto del folio
            rut: RUT del contribuyente

        Returns:
            Contenido del PDF en bytes, o None si falla
        """
        import time
        import requests

        try:
            logger.info(f"📥 Descargando PDF para folio {folio_text}...")

            # Click en el link para abrir el modal/iframe con el PDF
            folio_link.click()
            time.sleep(2)  # Esperar a que se abra el modal

            # Estrategia 1: Buscar iframe con el PDF
            try:
                iframes = self.driver.driver.find_elements(By.TAG_NAME, "iframe")
                logger.debug(f"Encontrados {len(iframes)} iframes")

                for iframe in iframes:
                    src = iframe.get_attribute('src')
                    if src and 'formCompacto' in src:
                        logger.info(f"✅ URL del PDF encontrada: {src}")

                        # Obtener cookies de la sesión actual
                        selenium_cookies = self.driver.driver.get_cookies()
                        cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}

                        # Descargar el PDF usando requests con las cookies de la sesión
                        response = requests.get(src, cookies=cookies_dict, timeout=30)

                        if response.status_code == 200 and response.content.startswith(b'%PDF'):
                            logger.info(f"✅ PDF descargado exitosamente ({len(response.content)} bytes)")

                            # Cerrar el modal
                            self._cerrar_modal()

                            return response.content
                        else:
                            logger.warning(f"⚠️ Response no es un PDF válido (status: {response.status_code})")

            except Exception as e:
                logger.debug(f"Error con estrategia iframe: {e}")

            # Estrategia 2: Capturar URL desde performance logs
            try:
                import json

                logs = self.driver.driver.get_log('performance')

                for log in logs:
                    try:
                        message = json.loads(log['message'])
                        method = message.get('message', {}).get('method', '')

                        if method == 'Network.responseReceived':
                            params = message.get('message', {}).get('params', {})
                            response_data = params.get('response', {})
                            url = response_data.get('url', '')
                            mime_type = response_data.get('mimeType', '')

                            if 'formCompacto' in url or mime_type == 'application/pdf':
                                logger.info(f"✅ URL del PDF encontrada en logs: {url}")

                                # Descargar el PDF
                                selenium_cookies = self.driver.driver.get_cookies()
                                cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}

                                response = requests.get(url, cookies=cookies_dict, timeout=30)

                                if response.status_code == 200 and response.content.startswith(b'%PDF'):
                                    logger.info(f"✅ PDF descargado ({len(response.content)} bytes)")
                                    self._cerrar_modal()
                                    return response.content

                    except Exception as e:
                        continue

            except Exception as e:
                logger.debug(f"Error con estrategia performance logs: {e}")

            # Si llegamos aquí, no pudimos descargar el PDF
            logger.warning(f"⚠️ No se pudo descargar PDF para folio {folio_text}")
            self._cerrar_modal()
            return None

        except Exception as e:
            logger.error(f"❌ Error descargando PDF para folio {folio_text}: {e}")
            self._cerrar_modal()
            return None

    def _cerrar_modal(self):
        """Intenta cerrar cualquier modal abierto"""
        import time

        try:
            # Buscar botón de cerrar (X, Cerrar, etc.)
            close_selectors = [
                "//button[contains(@class, 'close')]",
                "//button[contains(text(), '×')]",
                "//button[contains(text(), 'Cerrar')]",
                "//a[contains(@class, 'close')]",
                "//*[contains(@class, 'modal')]//button",
            ]

            for selector in close_selectors:
                try:
                    close_button = self.driver.driver.find_element(By.XPATH, selector)
                    close_button.click()
                    time.sleep(0.5)
                    logger.debug("✅ Modal cerrado")
                    return
                except:
                    continue

            # Si no hay botón, intentar presionar ESC
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains

            actions = ActionChains(self.driver.driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            logger.debug("✅ Modal cerrado con ESC")

        except Exception as e:
            logger.debug(f"No se pudo cerrar modal: {e}")

    def _extraer_resultados(self, save_callback: Optional[callable] = None) -> List[FormularioF29]:
        """
        Extrae los resultados de la tabla

        Args:
            save_callback: Callback opcional para guardar cada formulario inmediatamente
        """
        resultados: List[FormularioF29] = []

        try:
            tabla = self.driver.wait_for_element(
                By.CLASS_NAME,
                "gw-detalle-center-busqueda",
                timeout=30
            )

            filas = tabla.find_elements(By.TAG_NAME, "tr")[1:]  # Ignorar header
            logger.info(f"Encontradas {len(filas)} filas")

            # PASO 1: Extraer datos básicos de TODAS las filas primero (antes de hacer clicks)
            datos_basicos = []
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

                        datos_basicos.append({
                            "folio": celdas[1].text.strip(),
                            "period": celdas[0].text.strip(),
                            "contributor": celdas[2].text.strip(),
                            "submission_date": celdas[3].text.strip(),
                            "status": celdas[4].text.strip(),
                            "amount": monto,
                            "row_index": i
                        })
                except Exception as e:
                    logger.warning(f"Error extrayendo datos básicos de fila {i+1}: {e}")
                    continue

            logger.info(f"Datos básicos extraídos: {len(datos_basicos)} formularios")

            # PASO 2: Para cada formulario, hacer el flujo de extracción de codInt
            import time
            for datos in datos_basicos:
                formulario: FormularioF29 = {
                    "folio": datos["folio"],
                    "period": datos["period"],
                    "contributor": datos["contributor"],
                    "submission_date": datos["submission_date"],
                    "status": datos["status"],
                    "amount": datos["amount"]
                }

                # Extraer codInt usando el flujo completo (Ver → Formulario Compacto)
                try:
                    # Validar que la sesión sigue activa antes de intentar
                    if not self._check_session_valid():
                        logger.error(
                            f"❌ Sesión inválida al intentar extraer codInt para folio {datos['folio']}\n"
                            f"   Saltando este formulario"
                        )
                        resultados.append(formulario)
                        continue

                    logger.debug(f"🔍 Procesando folio {datos['folio']} (índice {datos['row_index']})")

                    # Re-obtener la tabla actualizada
                    tabla = self.driver.wait_for_element(
                        By.CLASS_NAME,
                        "gw-detalle-center-busqueda",
                        timeout=30
                    )
                    filas = tabla.find_elements(By.TAG_NAME, "tr")[1:]

                    # Obtener la fila correspondiente por índice
                    if datos["row_index"] < len(filas):
                        fila = filas[datos["row_index"]]
                        celdas = fila.find_elements(By.TAG_NAME, "td")

                        # Buscar el botón "Ver" en la última celda
                        ultima_celda = celdas[-1]
                        ver_link = ultima_celda.find_element(By.LINK_TEXT, "Ver")

                        # Click en Ver para abrir vista de detalle
                        logger.debug(f"👁️  Click en 'Ver' para folio {datos['folio']}")
                        ver_link.click()
                        time.sleep(1.5)

                        # Extraer codInt desde el botón "Formulario Compacto"
                        id_interno_sii = self._extraer_codint_from_formulario_compacto(datos['folio'])

                        if id_interno_sii:
                            formulario['id_interno_sii'] = id_interno_sii
                            logger.info(f"✅ Folio {datos['folio']} → codInt {id_interno_sii}")
                        else:
                            logger.warning(
                                f"⚠️ No se pudo extraer codInt para folio {datos['folio']}\n"
                                f"   El formulario se guardará sin id_interno_sii"
                            )

                        # 💾 GUARDADO INCREMENTAL: Llamar callback si existe
                        # El callback es síncrono y deposita el formulario en una cola
                        # para guardado async en paralelo
                        if save_callback:
                            try:
                                save_callback(formulario)
                            except Exception as save_error:
                                logger.error(
                                    f"❌ Error en callback para formulario {datos['folio']}: {save_error}\n"
                                    f"   Continuando con siguiente formulario..."
                                )

                        # Volver a la tabla principal con retry mejorado y múltiples estrategias
                        try:
                            if self._check_session_valid():
                                from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException as SeleniumTimeout
                                from selenium.webdriver.support.ui import WebDriverWait
                                from selenium.webdriver.support import expected_conditions as EC

                                # 📊 LOGGING DE ESTADO ANTES DE INTENTAR VOLVER
                                try:
                                    logger.debug(f"📊 Estado antes de click 'Volver' para folio {datos['folio']}:")
                                    logger.debug(f"   - URL actual: {self.driver.driver.current_url}")
                                    logger.debug(f"   - Ventanas abiertas: {len(self.driver.driver.window_handles)}")
                                    logger.debug(f"   - Document readyState: {self.driver.driver.execute_script('return document.readyState')}")

                                    # Verificar si hay overlays visibles con z-index alto
                                    overlay_count = self.driver.driver.execute_script("""
                                        return Array.from(document.querySelectorAll('div')).filter(el => {
                                            const style = window.getComputedStyle(el);
                                            const zIndex = parseInt(style.zIndex);
                                            return zIndex > 1000 && style.display !== 'none' && style.visibility !== 'hidden';
                                        }).length;
                                    """)
                                    logger.debug(f"   - Overlays con z-index > 1000: {overlay_count}")
                                except Exception as log_error:
                                    logger.warning(f"⚠️ Error obteniendo estado: {log_error}")

                                max_retries = 5
                                for attempt in range(max_retries):
                                    try:
                                        # ESTRATEGIA 1: Esperar más tiempo inicial para que se cargue la página
                                        wait_time = 1.5 + (attempt * 0.5)  # Aumentar tiempo en cada reintento
                                        logger.debug(f"   Esperando {wait_time}s antes de buscar botón 'Volver'...")
                                        time.sleep(wait_time)

                                        # ESTRATEGIA 2: Buscar el botón con múltiples selectores
                                        volver_selectors = [
                                            "//button[contains(text(), 'Volver')]",
                                            "//button[contains(@class, 'gw-button') and contains(text(), 'Volver')]",
                                            "//*[contains(text(), 'Volver') and (name()='button' or name()='a')]"
                                        ]

                                        volver_btn = None
                                        for selector in volver_selectors:
                                            try:
                                                volver_btn = WebDriverWait(self.driver.driver, 3).until(
                                                    EC.presence_of_element_located((By.XPATH, selector))
                                                )
                                                if volver_btn:
                                                    logger.debug(f"   Botón 'Volver' encontrado con selector: {selector}")
                                                    break
                                            except:
                                                continue

                                        if not volver_btn:
                                            raise Exception("No se encontró el botón 'Volver' con ningún selector")

                                        # ESTRATEGIA 3: Detectar y cerrar overlays explícitamente
                                        try:
                                            # Buscar overlays comunes del SII
                                            overlay_selectors = [
                                                "//div[contains(@class, 'gw-par-negrita')]",  # El div específico del error
                                                "//div[contains(@class, 'modal')]",
                                                "//div[contains(@class, 'overlay')]",
                                                "//div[contains(@class, 'loading')]"
                                            ]

                                            for overlay_selector in overlay_selectors:
                                                try:
                                                    overlays = self.driver.driver.find_elements(By.XPATH, overlay_selector)
                                                    for overlay in overlays:
                                                        if overlay.is_displayed():
                                                            logger.debug(f"   ⚠️ Overlay detectado, intentando ocultar: {overlay_selector}")
                                                            # Ocultar con JavaScript
                                                            self.driver.driver.execute_script(
                                                                "arguments[0].style.display = 'none';",
                                                                overlay
                                                            )
                                                            time.sleep(0.3)
                                                except:
                                                    pass
                                        except Exception as overlay_error:
                                            logger.debug(f"   No se pudo detectar/cerrar overlays: {overlay_error}")

                                        # ESTRATEGIA 4: Scroll y esperar que el elemento sea clickable
                                        try:
                                            self.driver.driver.execute_script(
                                                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                                                volver_btn
                                            )
                                            time.sleep(0.5)

                                            # Esperar a que sea clickable
                                            volver_btn = WebDriverWait(self.driver.driver, 3).until(
                                                EC.element_to_be_clickable(volver_btn)
                                            )
                                        except SeleniumTimeout:
                                            logger.debug(f"   ⚠️ Timeout esperando elemento clickable, intentando de todas formas")

                                        # ESTRATEGIA 5: Intentar click según el intento
                                        if attempt < 3:
                                            # Primeros 3 intentos: click normal
                                            volver_btn.click()
                                            logger.debug(f"🔙 Click normal exitoso en 'Volver' (intento {attempt + 1})")
                                        else:
                                            # Últimos 2 intentos: JavaScript click directo
                                            logger.debug(f"   Usando JavaScript click directo (intento {attempt + 1})")
                                            self.driver.driver.execute_script("arguments[0].click();", volver_btn)
                                            logger.debug(f"🔙 JavaScript click exitoso en 'Volver' (intento {attempt + 1})")

                                        # Si llegamos aquí, el click fue exitoso
                                        time.sleep(0.5)
                                        break

                                    except ElementClickInterceptedException as click_error:
                                        # 📸 CAPTURAR SCREENSHOT + HTML para debugging
                                        self._take_debug_screenshot("click_intercepted", datos['folio'])

                                        # 🔍 ANALIZAR QUÉ ELEMENTO ESTÁ INTERCEPTANDO
                                        try:
                                            interceptor_info = self.driver.driver.execute_script("""
                                                const btn = arguments[0];
                                                const rect = btn.getBoundingClientRect();
                                                const centerX = rect.left + rect.width / 2;
                                                const centerY = rect.top + rect.height / 2;
                                                const topElement = document.elementFromPoint(centerX, centerY);

                                                return {
                                                    interceptor_tag: topElement?.tagName,
                                                    interceptor_class: topElement?.className,
                                                    interceptor_id: topElement?.id,
                                                    interceptor_text: topElement?.innerText?.substring(0, 50),
                                                    button_visible: btn.offsetParent !== null,
                                                    button_rect: {
                                                        top: rect.top,
                                                        left: rect.left,
                                                        width: rect.width,
                                                        height: rect.height
                                                    }
                                                };
                                            """, volver_btn)

                                            logger.error(f"🎯 Elemento interceptor detectado para folio {datos['folio']}:")
                                            logger.error(f"   - Tag: {interceptor_info.get('interceptor_tag')}")
                                            logger.error(f"   - Class: {interceptor_info.get('interceptor_class')}")
                                            logger.error(f"   - ID: {interceptor_info.get('interceptor_id')}")
                                            logger.error(f"   - Text: {interceptor_info.get('interceptor_text')}")
                                            logger.error(f"   - Botón visible: {interceptor_info.get('button_visible')}")
                                            logger.error(f"   - Botón rect: {interceptor_info.get('button_rect')}")
                                        except Exception as js_error:
                                            logger.warning(f"⚠️ No se pudo analizar interceptor: {js_error}")

                                        if attempt < max_retries - 1:
                                            logger.debug(
                                                f"⚠️ Click bloqueado (intento {attempt + 1}/{max_retries}): {str(click_error)[:100]}"
                                            )
                                        else:
                                            # ESTRATEGIA 6: Último recurso - navegar directamente
                                            logger.warning(
                                                f"⚠️ Click bloqueado después de {max_retries} intentos, "
                                                f"usando estrategia de navegación directa"
                                            )
                                            try:
                                                # Usar history.back() de JavaScript
                                                self.driver.driver.execute_script("window.history.back();")
                                                time.sleep(1)
                                                logger.debug("✅ Navegación con history.back() exitosa")
                                                break
                                            except Exception as nav_error:
                                                logger.warning(f"⚠️ Navegación también falló: {nav_error}")
                                                # Última alternativa: navegar a la URL de búsqueda
                                                try:
                                                    self.driver.navigate_to(self.SEARCH_URL)
                                                    time.sleep(2)
                                                    logger.debug("✅ Navegación directa a SEARCH_URL exitosa")
                                                    break
                                                except Exception as url_error:
                                                    logger.error(f"❌ Todas las estrategias de navegación fallaron: {url_error}")
                                                    raise

                                    except Exception as e:
                                        if attempt < max_retries - 1:
                                            logger.debug(f"⚠️ Error en intento {attempt + 1}: {type(e).__name__}: {str(e)[:100]}")
                                        else:
                                            logger.warning(f"⚠️ Error final después de {max_retries} intentos: {e}")
                                            raise

                                logger.debug(f"🔙 Volviendo a tabla principal")
                            else:
                                logger.error("❌ Sesión inválida, no se puede hacer click en 'Volver'")
                        except Exception as e:
                            logger.warning(
                                f"⚠️ Error al volver a tabla principal: {type(e).__name__}: {e}\n"
                                f"   No es crítico - el formulario ya fue procesado. Continuando..."
                            )
                            # No es crítico - continuar procesando
                            # El formulario ya fue guardado con su codInt

                except InvalidSessionIdException as e:
                    # 📸 CAPTURAR SCREENSHOT si es posible
                    try:
                        self._take_debug_screenshot("invalid_session_proceso", datos['folio'])
                    except:
                        pass

                    logger.error(
                        f"🔴 INVALID SESSION ID al procesar folio {datos['folio']}\n"
                        f"   Error: {e}\n"
                        f"   El formulario se guardará sin id_interno_sii\n"
                        f"   La sesión expiró durante el procesamiento de este formulario",
                        exc_info=True
                    )
                    # Continuar sin codInt si falla

                except WebDriverException as e:
                    # 📸 CAPTURAR SCREENSHOT si es posible
                    try:
                        self._take_debug_screenshot("webdriver_proceso", datos['folio'])
                    except:
                        pass

                    logger.error(
                        f"🌐 WEBDRIVER ERROR al procesar folio {datos['folio']}\n"
                        f"   Error: {type(e).__name__}: {e}\n"
                        f"   El formulario se guardará sin id_interno_sii",
                        exc_info=True
                    )
                    # Continuar sin codInt si falla

                except Exception as e:
                    logger.error(
                        f"❌ ERROR INESPERADO al procesar folio {datos['folio']}\n"
                        f"   Error: {type(e).__name__}: {e}\n"
                        f"   El formulario se guardará sin id_interno_sii",
                        exc_info=True
                    )
                    # Continuar sin codInt si falla

                resultados.append(formulario)
                logger.debug(f"F29: {formulario['folio']} - {formulario['period']}")

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

            # 🔍 DEBUG: Log completo del response GWT para análisis
            logger.info(f"📋 GWT Response length: {len(gwt_response)} characters")
            logger.info(f"🔍 GWT Response (first 1000 chars): {gwt_response[:1000]}")
            logger.info(f"🔍 GWT Response (last 500 chars): {gwt_response[-500:]}")

            # Guardar response completo en archivo para análisis
            try:
                with open('/tmp/gwt_response_f29.txt', 'w') as f:
                    f.write(gwt_response)
                logger.info("💾 Response GWT completo guardado en /tmp/gwt_response_f29.txt")
            except Exception as e:
                logger.warning(f"No se pudo guardar response GWT: {e}")

            # Parsear response GWT usando mismo patrón que en servicev2.py
            if not gwt_response.startswith("//OK"):
                logger.warning(f"⚠️ Response GWT no tiene formato esperado")
                return resultados_tabla

            # 🔍 Buscar TODOS los posibles patrones para entender la estructura
            # Patrón 1: folio de 10 dígitos (ej: "7913650886")
            pattern_folio = r'"(\d{10})"'
            folios_found = re.findall(pattern_folio, gwt_response)
            logger.info(f"📊 Folios encontrados (10 dígitos): {len(folios_found)}")
            if folios_found:
                logger.debug(f"🔍 Primeros 5 folios: {folios_found[:5]}")

            # Patrón 2: id_interno de 9 dígitos
            pattern_id_interno = r'"(\d{9})"'
            ids_internos_found = re.findall(pattern_id_interno, gwt_response)
            logger.info(f"📊 IDs internos encontrados (9 dígitos): {len(ids_internos_found)}")
            if ids_internos_found:
                logger.debug(f"🔍 Primeros 5 IDs internos: {ids_internos_found[:5]}")

            # Patrón 3: códigos de mes (M01, M02, etc.)
            pattern_mes = r'"(M\d{2})"'
            meses_found = re.findall(pattern_mes, gwt_response)
            logger.info(f"📊 Códigos de mes encontrados: {len(meses_found)}")
            if meses_found:
                logger.debug(f"🔍 Meses: {set(meses_found)}")

            # Patrón original: "id_interno","Mxx"
            pattern_new = r'"(\d{9})","(M\d{2})"'
            matches_new = re.findall(pattern_new, gwt_response)
            logger.info(f"📊 Matches patrón nuevo (id_interno,Mxx): {len(matches_new)}")

            # Patrón antiguo: "fecha","id_interno","Mxx"
            pattern_old = r'"(\d{2}/\d{2}/\d{4})","(\d+)","(M\d+)"'
            matches_old = re.findall(pattern_old, gwt_response)
            logger.info(f"📊 Matches patrón antiguo (fecha,id_interno,Mxx): {len(matches_old)}")

            # 🔍 NUEVO: Buscar patrón correcto con FOLIO en el response GWT
            # El formato real es: "Vigente","FechaPresentación","Folio","OtraFecha","IDInterno","Mes"
            # Ejemplo: "Vigente","09/05/2024","785646823","22/03/2024","781272307","M02"
            pattern_with_folio = r'"Vigente","(?:\d{2}/\d{2}/\d{4})","(\d{10})","(?:\d{2}/\d{2}/\d{4})","(\d{9})","(M\d{2})"'
            matches_with_folio = re.findall(pattern_with_folio, gwt_response)
            logger.info(f"📊 Matches con folio (Vigente,Fecha,Folio,Fecha,IDInterno,Mes): {len(matches_with_folio)}")
            if matches_with_folio:
                logger.info(f"✅ ENCONTRADO! Primeros 3 matches: {matches_with_folio[:3]}")

            # También buscar F29 anulados (para logging)
            pattern_anulados = r'"Anulada","(?:\d{2}/\d{2}/\d{4})","(\d{10})","(?:\d{2}/\d{2}/\d{4})","(\d{9})","(M\d{2})"'
            matches_anulados = re.findall(pattern_anulados, gwt_response)
            if matches_anulados:
                logger.info(f"📊 F29 Anulados encontrados: {len(matches_anulados)}")
                logger.info(f"   Primeros 3 anulados: {matches_anulados[:3]}")

            # 🎯 ESTRATEGIA: Matching POSICIONAL (ya que GWT no tiene folios de 10 dígitos)
            # El response GWT solo contiene id_internos (9 dígitos), no folios (10 dígitos)
            # Debemos hacer match basándonos en el ORDEN de aparición

            # Paso 1: Agrupar formularios de la tabla HTML por período
            formularios_por_periodo = {}
            for formulario in resultados_tabla:
                period = formulario.get('period', '')
                if period not in formularios_por_periodo:
                    formularios_por_periodo[period] = []
                formularios_por_periodo[period].append(formulario)

            logger.info(f"📋 Formularios agrupados por período: {len(formularios_por_periodo)} períodos")

            # Paso 2: Extraer TODOS los id_internos del GWT en orden
            # Patrón mejorado: buscar secuencias de "id_interno","Mes"
            # Hay múltiples ids por mes, debemos extraer SOLO el último antes del código de mes
            pattern_all_ids = r'"(\d{9})","(M\d{2})"'
            all_id_matches = re.findall(pattern_all_ids, gwt_response)
            logger.info(f"📊 IDs internos encontrados con mes: {len(all_id_matches)}")

            # Paso 3: Agrupar IDs internos por mes (el ÚLTIMO id antes de cada Mxx es el vigente)
            gwt_ids_por_mes = {}
            for id_interno, mes_codigo in all_id_matches:
                # El patrón captura múltiples IDs, pero queremos el último por mes
                # que es el que aparece justo antes del código Mxx
                gwt_ids_por_mes[mes_codigo] = id_interno
                logger.debug(f"  {mes_codigo} → ID interno: {id_interno}")

            logger.info(f"📊 IDs internos únicos por mes: {len(gwt_ids_por_mes)} meses")

            # Paso 4: Hacer matching posicional
            resultados_enriquecidos = []
            for formulario in resultados_tabla:
                period = formulario.get('period', '')

                # Convertir período "2024-01" a código mes "M01"
                if period:
                    try:
                        year, month = period.split('-')
                        mes_codigo = f"M{int(month):02d}"
                        id_interno = gwt_ids_por_mes.get(mes_codigo)

                        if id_interno:
                            formulario_enriquecido = formulario.copy()
                            formulario_enriquecido['id_interno_sii'] = id_interno
                            resultados_enriquecidos.append(formulario_enriquecido)
                            logger.debug(f"✅ {period} (folio {formulario.get('folio')}): id_interno={id_interno}")
                        else:
                            resultados_enriquecidos.append(formulario)
                            logger.warning(f"⚠️ No se encontró id_interno para {period}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error procesando período {period}: {e}")
                        resultados_enriquecidos.append(formulario)
                else:
                    resultados_enriquecidos.append(formulario)

            logger.info(f"✅ {len(resultados_enriquecidos)} formularios enriquecidos posicionalmente")
            return resultados_enriquecidos

            # 🎯 FALLBACK: Usar match por período (menos preciso, puede fallar con múltiples F29 del mismo período)
            logger.warning(f"⚠️ No se encontró patrón con folio, usando match por período (menos preciso)")
            gwt_data_by_period = {}

            if matches_new:
                # Usar patrón nuevo: "id_interno","Mxx"
                # Necesitamos extraer el año del contexto (sabemos que es 2024)
                # Buscar el año en el response
                year_match = re.search(r',(\d{4}),3,2', gwt_response)
                year = int(year_match.group(1)) if year_match else 2024

                for id_interno, mes_codigo in matches_new:
                    # Extraer número de mes del código (M01 -> 1)
                    mes_match = re.match(r'M(\d+)', mes_codigo)
                    mes = int(mes_match.group(1)) if mes_match else None

                    if mes:
                        period_key = f"{year}-{mes:02d}"
                        # ⚠️ PROBLEMA: Si ya existe, se sobrescribe (perdemos F29 anteriores del mismo período)
                        if period_key in gwt_data_by_period:
                            logger.warning(f"⚠️ Período {period_key} ya existe, sobrescribiendo (puede causar mapeo incorrecto)")
                        gwt_data_by_period[period_key] = id_interno

            elif matches_old:
                # Usar patrón antiguo: "fecha","id_interno","Mxx"
                for fecha, folio_interno, mes_codigo in matches_old:
                    year = int(fecha.split('/')[-1])
                    mes_match = re.match(r'M(\d+)', mes_codigo)
                    mes = int(mes_match.group(1)) if mes_match else None

                    if mes and year:
                        period_key = f"{year}-{mes:02d}"
                        if period_key in gwt_data_by_period:
                            logger.warning(f"⚠️ Período {period_key} ya existe, sobrescribiendo (puede causar mapeo incorrecto)")
                        gwt_data_by_period[period_key] = folio_interno
            else:
                logger.warning(f"⚠️ No se encontraron datos GWT en response con ningún patrón")
                return resultados_tabla

            logger.info(f"📊 Datos GWT parseados: {len(gwt_data_by_period)} períodos")

            # Enriquecer resultados de tabla con id_interno_sii (por período)
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

            # El SII puede devolver el PDF directamente o mostrar una página intermedia
            # Intentar obtener el contenido de la página actual
            page_source = self.driver.driver.page_source

            # Si la página contiene "PDF" en el tipo de contenido o es binario
            # entonces el navegador está mostrando el PDF
            current_url = self.driver.driver.current_url

            # Usar requests para descargar el PDF con las cookies del driver
            import requests

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
