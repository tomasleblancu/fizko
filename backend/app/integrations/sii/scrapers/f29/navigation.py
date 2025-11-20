"""
Navigation logic for F29 scraper - SIMPLIFIED VERSION

Uses the rectificar F29 page which is much simpler and more reliable.
"""
import logging
import time
import os
import re
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ...exceptions import ScrapingException

logger = logging.getLogger(__name__)


# Nueva URL más simple y directa
SEARCH_URL = "https://www4.sii.cl/rfiInternet/rectificarF29/index.html#rfiBusquedaDeclaracionForm"


def _take_debug_screenshot(driver, step_name: str, error_msg: str = "") -> None:
    """
    Toma screenshot y guarda HTML para debugging

    Args:
        driver: WebDriver instance
        step_name: Nombre del paso donde ocurrió el error
        error_msg: Mensaje de error opcional
    """
    try:
        timestamp = int(time.time())
        screenshot_dir = "/app/screenshots"

        # Crear directorio si no existe
        os.makedirs(screenshot_dir, exist_ok=True)

        screenshot_path = f"{screenshot_dir}/f29_nav_{step_name}_{timestamp}.png"
        html_path = f"{screenshot_dir}/f29_nav_{step_name}_{timestamp}.html"

        # Guardar screenshot
        try:
            driver.driver.save_screenshot(screenshot_path)
            logger.error(f"📸 Screenshot guardado: backend/screenshots/f29_nav_{step_name}_{timestamp}.png")
        except Exception as screenshot_error:
            logger.warning(f"⚠️ No se pudo guardar screenshot: {screenshot_error}")

        # Guardar HTML
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(f"<!-- ERROR: {error_msg} -->\n")
                f.write(f"<!-- URL: {driver.driver.current_url} -->\n")
                f.write(driver.driver.page_source)
            logger.error(f"📄 HTML guardado: backend/screenshots/f29_nav_{step_name}_{timestamp}.html")
        except Exception as html_error:
            logger.warning(f"⚠️ No se pudo guardar HTML: {html_error}")

    except Exception as e:
        logger.warning(f"⚠️ Error en _take_debug_screenshot: {e}")


def navegar_a_busqueda(driver, max_retries: int = 3) -> None:
    """
    Navega a la página de búsqueda de F29 (rectificar)

    Args:
        driver: WebDriver instance
        max_retries: No usado (mantener por compatibilidad)
    """
    try:
        logger.info(f"Navegando a página de búsqueda F29 (rectificar)")
        driver.navigate_to(SEARCH_URL)

        # DELAY: Esperar para copiar body después de navegar
        logger.info("⏸️  DELAY 2s después de navegar - puedes copiar page body")
        time.sleep(2)

        # Verificar URL después de navegar (para detectar redirects al login)
        current_url = driver.driver.current_url

        # Detectar si fuimos redirigidos al login
        if "AUT2000" in current_url or "IngresoRutClave" in current_url:
            logger.error(f"❌ Redirigido al login - sesión no válida")
            _take_debug_screenshot(driver, "redirect_to_login", "Redirigido a página de login")
            raise ScrapingException(
                "Redirigido a página de login - sesión no válida. "
                "Las cookies de autenticación no se están propagando correctamente"
            )

        logger.info("✅ Navegación completada")

    except Exception as e:
        if "Redirigido a página de login" in str(e):
            raise
        raise ScrapingException(f"No se pudo navegar a búsqueda: {str(e)}") from e


def seleccionar_anio(driver, anio: str) -> None:
    """
    Selecciona el año en el dropdown de búsqueda

    Args:
        driver: WebDriver instance
        anio: Año a seleccionar (YYYY)
    """
    try:
        logger.info(f"🔍 Seleccionando año {anio} del dropdown")

        # DELAY: Esperar para que cargue la página
        logger.info("⏸️  DELAY 2s para que cargue la página - puedes copiar page body")
        time.sleep(2)

        # Buscar TODOS los dropdowns (hay varios: formulario, año, etc.)
        dropdowns = driver.wait_for_elements(
            By.CSS_SELECTOR,
            "select.gwt-ListBox",
            timeout=10
        )

        logger.info(f"✅ Encontrados {len(dropdowns)} dropdowns totales")

        # Filtrar solo los dropdowns VISIBLES (no hidden)
        dropdowns_visibles = [d for d in dropdowns if d.is_displayed()]
        logger.info(f"✅ Dropdowns visibles: {len(dropdowns_visibles)}")

        # 1. Primero buscar y seleccionar "Formulario 29" en el dropdown de tipo de formulario
        dropdown_formulario = None
        for dropdown in dropdowns_visibles:
            opciones = dropdown.find_elements(By.TAG_NAME, "option")
            opciones_texto = [opt.get_attribute("textContent") or opt.get_attribute("value") or opt.text for opt in opciones]

            # El dropdown de formulario contiene "Formulario 29" o "Formulario 50"
            tiene_formularios = any(texto and "Formulario" in texto for texto in opciones_texto)

            if tiene_formularios:
                dropdown_formulario = dropdown
                logger.info(f"✅ Dropdown de tipo de formulario encontrado: {opciones_texto}")

                # Seleccionar "Formulario 29"
                for opcion in opciones:
                    texto = opcion.get_attribute("textContent") or opcion.get_attribute("value") or opcion.text
                    if texto and "Formulario 29" in texto:
                        opcion.click()
                        logger.info("✅ 'Formulario 29' seleccionado")
                        time.sleep(0.5)  # Pequeña espera después de seleccionar
                        break
                break

        if not dropdown_formulario:
            logger.warning("⚠️ No se encontró dropdown de tipo de formulario (puede ser opcional)")

        # 2. Ahora buscar el dropdown que contiene años (el que tiene opciones como "2024", "2023", etc.)
        dropdown_anio = None
        for dropdown in dropdowns_visibles:
            opciones = dropdown.find_elements(By.TAG_NAME, "option")
            opciones_texto = [opt.get_attribute("textContent") or opt.get_attribute("value") or opt.text for opt in opciones]

            # El dropdown de año contendrá números de 4 dígitos (2024, 2023, etc.)
            tiene_anios = any(texto and texto.strip().isdigit() and len(texto.strip()) == 4 for texto in opciones_texto)

            if tiene_anios:
                dropdown_anio = dropdown
                logger.info(f"✅ Dropdown de año encontrado con opciones: {opciones_texto[:5]}...")
                break

        if not dropdown_anio:
            raise ScrapingException("No se encontró dropdown de año en la página")

        # Ahora seleccionar el año del dropdown correcto
        opciones = dropdown_anio.find_elements(By.TAG_NAME, "option")
        opciones_texto = [opt.get_attribute("textContent") or opt.get_attribute("value") or opt.text for opt in opciones]
        logger.info(f"📋 Años disponibles: {opciones_texto}")

        # Buscar y seleccionar el año por texto interno
        found = False
        for opcion in opciones:
            # Intentar múltiples formas de obtener el texto
            texto = opcion.get_attribute("textContent") or opcion.get_attribute("value") or opcion.text
            if texto and texto.strip() == anio:
                opcion.click()
                logger.info(f"✅ Año {anio} seleccionado")
                found = True
                break

        if not found:
            raise ScrapingException(
                f"Año {anio} no disponible en dropdown. Opciones: {opciones_texto}"
            )

        # DELAY: Esperar después de seleccionar
        logger.info("⏸️  DELAY 2s después de seleccionar año - puedes copiar page body")
        time.sleep(2)

    except Exception as e:
        _take_debug_screenshot(
            driver,
            "error_seleccionar_anio",
            str(e)
        )
        raise ScrapingException(f"Error seleccionando año: {str(e)}") from e


def ejecutar_consulta(driver) -> None:
    """
    Ejecuta la consulta haciendo click en 'Consultar'

    Args:
        driver: WebDriver instance
    """
    try:
        # Buscar el botón "Consultar"
        consultar_button = driver.wait_for_clickable(
            By.XPATH,
            "//button[contains(text(), 'Consultar')]",
            timeout=10
        )

        logger.info("✅ Botón 'Consultar' encontrado")

        # DELAY: Esperar para copiar body antes de click
        logger.info("⏸️  DELAY 2s antes de click en 'Consultar' - puedes copiar page body")
        time.sleep(2)

        consultar_button.click()
        logger.info("✅ Click en 'Consultar' exitoso")

        # Esperar a que aparezca la tabla de resultados
        try:
            WebDriverWait(driver.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "table.tabla_internet"
                ))
            )
            logger.info("✅ Tabla de resultados cargada")
        except Exception as e:
            logger.warning(f"⚠️ Tabla de resultados no apareció: {e}")

        # DELAY: Esperar para copiar body después de click
        logger.info("⏸️  DELAY 2s después de click en 'Consultar' - puedes copiar page body")
        time.sleep(2)

    except Exception as e:
        _take_debug_screenshot(
            driver,
            "error_ejecutar_consulta",
            str(e)
        )
        raise ScrapingException(f"Error ejecutando consulta: {str(e)}") from e
