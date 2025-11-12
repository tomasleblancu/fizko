"""
Navigation logic for F29 scraper

Handles page navigation, button clicks, form selection, and search configuration.
"""
import logging
import time
from typing import Optional
from selenium.webdriver.common.by import By

from ...exceptions import ScrapingException

logger = logging.getLogger(__name__)


SEARCH_URL = "https://www4.sii.cl/sifmConsultaInternet/index.html?dest=cifxx&form=29"
FORM_CODE = "29"


def navegar_a_busqueda(driver, max_retries: int) -> None:
    """
    Navega a la pagina de busqueda con reintentos

    Args:
        driver: WebDriver instance
        max_retries: Número máximo de reintentos
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Navegando a busqueda (intento {attempt + 1}/{max_retries})")

            driver.navigate_to(SEARCH_URL)
            time.sleep(3)

            # Verificar URL después de navegar (para detectar redirects al login)
            current_url = driver.driver.current_url

            # Detectar si fuimos redirigidos al login
            if "AUT2000" in current_url or "IngresoRutClave" in current_url:
                logger.error(f"❌ Redirigido al login - sesión no válida")
                raise ScrapingException(
                    "Redirigido a página de login - sesión no válida. "
                    "Las cookies de autenticación no se están propagando correctamente"
                )

            # Verificar múltiples indicadores de que la página cargó
            page_source = driver.driver.page_source

            # Verificar si ya estamos en el formulario de búsqueda
            try:
                listboxes = driver.driver.find_elements(By.CLASS_NAME, "gwt-ListBox")
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
                driver.driver.refresh()
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


def click_buscar_formulario(driver) -> None:
    """
    Click en boton 'Buscar Formulario' o verifica si ya está en el formulario

    Args:
        driver: WebDriver instance
    """
    try:
        # Esperar un poco más para que cargue completamente (GWT es lento)
        time.sleep(3)

        # Primero verificar si ya estamos en el formulario de búsqueda
        try:
            listboxes = driver.driver.find_elements(By.CLASS_NAME, "gwt-ListBox")
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
                buscar_button = driver.wait_for_clickable(
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
                driver.driver.save_screenshot(screenshot_path)
                logger.error(f"📸 Screenshot: backend/screenshots/f29_error_{timestamp}.png")
            except Exception as screenshot_error:
                logger.warning(f"⚠️ No se pudo guardar screenshot: {screenshot_error}")

            try:
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(driver.driver.page_source)
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


def seleccionar_tipo_formulario(driver) -> None:
    """
    Selecciona el tipo de formulario (DPS) y codigo (29)

    Args:
        driver: WebDriver instance
    """
    try:
        # Seleccionar tipo DPS (Formularios de Impuesto)
        tipo_select = driver.wait_for_element(
            By.CLASS_NAME,
            "gwt-ListBox",
            timeout=30
        )
        driver.select_option_by_value(tipo_select, "DPS")
        time.sleep(0.5)
        logger.debug("Tipo DPS seleccionado")

        # Seleccionar codigo 29
        listboxes = driver.wait_for_elements(
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

        if FORM_CODE not in opciones:
            raise ScrapingException(
                f"Codigo '{FORM_CODE}' no disponible. Opciones: {opciones}"
            )

        driver.select_option_by_value(codigo_select, FORM_CODE)
        time.sleep(0.5)
        logger.debug("Codigo F29 seleccionado")

    except Exception as e:
        raise ScrapingException(f"Error seleccionando tipo de formulario: {str(e)}") from e


def configurar_criterios_busqueda(driver, anio: Optional[str], folio: Optional[str]) -> None:
    """
    Configura los criterios de busqueda (folio o anual)

    Args:
        driver: WebDriver instance
        anio: Año a consultar
        folio: Folio específico
    """
    try:
        if folio:
            _busqueda_por_folio(driver, folio)
        else:
            _busqueda_anual(driver, anio)

    except Exception as e:
        raise ScrapingException(f"Error configurando criterios: {str(e)}") from e


def _busqueda_por_folio(driver, folio: str) -> None:
    """Configura busqueda por folio"""
    folio_radio = driver.wait_for_element(
        By.XPATH,
        "//label[contains(text(), 'Folio')]/..//input",
        timeout=30
    )
    folio_radio.click()

    folio_input = driver.wait_for_element(
        By.CLASS_NAME,
        "gwt-TextBox",
        timeout=30
    )
    folio_input.send_keys(folio)
    logger.debug(f"Busqueda por folio: {folio}")


def _busqueda_anual(driver, anio: str) -> None:
    """Configura busqueda anual"""
    anual_radio = driver.wait_for_element(
        By.XPATH,
        "//label[contains(text(), 'Anual')]/..//input",
        timeout=30
    )
    anual_radio.click()

    selects = driver.wait_for_elements(
        By.CLASS_NAME,
        "gwt-ListBox",
        timeout=30
    )

    # El select de ano anual esta en posicion 2
    anio_select = selects[2]
    driver.select_option_by_value(anio_select, anio)
    logger.debug(f"Busqueda anual: {anio}")


def ejecutar_consulta(driver) -> str:
    """
    Ejecuta la consulta haciendo click en 'Consultar' y captura el response GWT

    Args:
        driver: WebDriver instance

    Returns:
        Response body del request GWT-RPC automático, o string vacío si no se captura
    """
    try:
        consultar_button = driver.wait_for_clickable(
            By.XPATH,
            "//button[contains(text(), 'Consultar')]",
            timeout=30
        )
        consultar_button.click()

        # Esperar a que se ejecute el request GWT-RPC automático
        time.sleep(2)  # Aumentado para dar tiempo al request

        # Capturar el response GWT del performance log
        # Filtrar por el método específico getDocumentosBusqueda
        from ...core.auth_handler import capture_gwt_response
        gwt_response = capture_gwt_response(
            driver,
            url_filter="svcConsulta",
            method_filter="getDocumentosBusqueda"
        )

        logger.debug("Consulta ejecutada")
        return gwt_response

    except Exception as e:
        raise ScrapingException(f"Error ejecutando consulta: {str(e)}") from e


def cerrar_modal(driver):
    """
    Intenta cerrar cualquier modal abierto

    Args:
        driver: WebDriver instance
    """
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
                close_button = driver.driver.find_element(By.XPATH, selector)
                close_button.click()
                time.sleep(0.5)
                logger.debug("✅ Modal cerrado")
                return
            except:
                continue

        # Si no hay botón, intentar presionar ESC
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains

        actions = ActionChains(driver.driver)
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
        logger.debug("✅ Modal cerrado con ESC")

    except Exception as e:
        logger.debug(f"No se pudo cerrar modal: {e}")
