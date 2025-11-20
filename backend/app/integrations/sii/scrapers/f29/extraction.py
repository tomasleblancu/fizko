"""
Extraction logic for F29 scraper - SIMPLIFIED VERSION

Extracts F29 data from the rectificar F29 page table.
"""
import logging
import re
import time
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ...exceptions import ScrapingException

logger = logging.getLogger(__name__)


def extraer_resultados(driver, save_callback: Optional[callable] = None) -> List[Dict[str, Any]]:
    """
    Extrae formularios F29 de la tabla de resultados

    Args:
        driver: WebDriver instance
        save_callback: Callback opcional para guardar cada formulario (no usado en esta versión)

    Returns:
        Lista de formularios F29 con folio, period, status, etc.
    """
    try:
        # Buscar la tabla de resultados
        tabla = driver.wait_for_element(
            By.CSS_SELECTOR,
            "table.tabla_internet",
            timeout=10
        )

        logger.info("✅ Tabla de resultados encontrada")

        # Obtener todas las filas (excepto header)
        filas = tabla.find_elements(By.TAG_NAME, "tr")

        # Las primeras 2 filas son headers
        filas_datos = filas[2:]  # Skip "Declaraciones Vigentes" y columnas header

        logger.info(f"📋 Filas de datos encontradas: {len(filas_datos)}")

        formularios = []

        for idx, fila in enumerate(filas_datos, 1):
            try:
                formulario = _extraer_formulario_de_fila(driver, fila, idx)
                if formulario:
                    formularios.append(formulario)
                    logger.info(
                        f"✅ Formulario {idx}/{len(filas_datos)}: "
                        f"Folio {formulario['folio']} - "
                        f"Periodo {formulario['period']} - "
                        f"codInt: {formulario.get('id_interno_sii', 'N/A')}"
                    )
            except Exception as e:
                logger.error(f"❌ Error extrayendo fila {idx}: {str(e)}")
                continue

        logger.info(f"✅ Total formularios extraídos: {len(formularios)}")
        return formularios

    except Exception as e:
        raise ScrapingException(f"Error extrayendo resultados: {str(e)}") from e


def _extraer_formulario_de_fila(driver, fila, idx: int) -> Optional[Dict[str, Any]]:
    """
    Extrae datos de un formulario de una fila de la tabla

    Args:
        driver: WebDriver instance
        fila: Elemento tr de la tabla
        idx: Índice de la fila (para logging)

    Returns:
        Dict con datos del formulario o None si falla
    """
    try:
        # Obtener todas las celdas
        celdas = fila.find_elements(By.TAG_NAME, "td")

        if len(celdas) < 7:
            logger.warning(f"⚠️ Fila {idx} tiene solo {len(celdas)} celdas, se esperaban 8")
            return None

        # Estructura de la tabla:
        # 0: Período (link)
        # 1: Folio
        # 2: Contribuyente (RUT)
        # 3: Fecha Presentación
        # 4: Estado
        # 5: Ver (con links: Detalle, Formulario, C. Solemne)
        # 6: Opciones (Rectificar)
        # 7: Giros

        # Extraer período
        period_link = celdas[0].find_element(By.TAG_NAME, "a")
        period_text = period_link.text.strip()  # Ej: "Ene 2025", "Feb 2025"

        # Extraer folio
        folio_label = celdas[1].find_element(By.CLASS_NAME, "gwt-Label")
        folio = folio_label.text.strip()

        # Extraer RUT del contribuyente (celda 2)
        try:
            rut_label = celdas[2].find_element(By.CLASS_NAME, "gwt-Label")
            contributor_rut = rut_label.text.strip()
        except Exception as e:
            logger.warning(f"⚠️ No se pudo extraer RUT de fila {idx}: {e}")
            contributor_rut = None

        # Extraer fecha presentación
        fecha_label = celdas[3].find_element(By.CLASS_NAME, "gwt-Label")
        fecha_presentacion = fecha_label.text.strip()

        # Extraer estado
        estado_label = celdas[4].find_element(By.CLASS_NAME, "gwt-Label")
        estado = estado_label.text.strip()

        # Buscar el link "Formulario" en la celda "Ver"
        try:
            links = celdas[5].find_elements(By.TAG_NAME, "a")
            formulario_link = None
            for link in links:
                if "Formulario" in link.text:
                    formulario_link = link
                    break

            if not formulario_link:
                logger.warning(f"⚠️ No se encontró link 'Formulario' en fila {idx}")
                id_interno_sii = None
            else:
                # Click en el link "Formulario" para abrir ventana con URL que contiene codInt
                id_interno_sii = _extraer_codint_desde_formulario(driver, formulario_link, folio)

        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo codInt de fila {idx}: {e}")
            id_interno_sii = None

        # Parsear período a formato YYYY-MM y separar en componentes
        period_parsed, period_year, period_month = _parse_period_with_components(period_text)

        formulario_data = {
            'folio': folio,
            'period': period_parsed,  # "YYYY-MM" format
            'period_year': period_year,  # Integer year
            'period_month': period_month,  # Integer month
            'contributor_rut': contributor_rut,  # RUT from table
            'status': _map_status(estado),
            'submission_date': fecha_presentacion,
            'id_interno_sii': id_interno_sii,
        }

        return formulario_data

    except Exception as e:
        logger.error(f"❌ Error procesando fila {idx}: {str(e)}")
        return None


def _extraer_codint_desde_formulario(driver, formulario_link, folio: str) -> Optional[str]:
    """
    Extrae el codInt haciendo click en el link "Formulario" y capturando la URL de la ventana nueva

    Args:
        driver: WebDriver instance
        formulario_link: Elemento link "Formulario"
        folio: Folio del formulario (para logging)

    Returns:
        codInt extraído de la URL o None si falla
    """
    try:
        # Guardar ventanas actuales
        ventanas_antes = driver.driver.window_handles

        # Click en "Formulario"
        formulario_link.click()
        logger.debug(f"Click en 'Formulario' para folio {folio}")

        # Esperar a que se abra nueva ventana
        try:
            WebDriverWait(driver.driver, 5).until(
                lambda d: len(d.window_handles) > len(ventanas_antes)
            )
        except Exception:
            logger.warning(f"⚠️ No se abrió nueva ventana para folio {folio}")
            return None

        # Cambiar a la nueva ventana
        ventanas_despues = driver.driver.window_handles
        nueva_ventana = [v for v in ventanas_despues if v not in ventanas_antes][0]

        driver.driver.switch_to.window(nueva_ventana)

        # Esperar a que cargue la URL
        time.sleep(0.5)

        # Capturar la URL
        url = driver.driver.current_url
        logger.debug(f"URL capturada: {url}")

        # Extraer codInt de la URL
        # Formato: https://www4.sii.cl/rfiInternet/formCompacto?folio=8104678626&rut=77794858&form=29&codInt=817935151
        match = re.search(r'codInt=(\d+)', url)
        codint = match.group(1) if match else None

        if codint:
            logger.debug(f"✅ codInt extraído: {codint} para folio {folio}")
        else:
            logger.warning(f"⚠️ No se pudo extraer codInt de URL: {url}")

        # Cerrar la ventana nueva
        driver.driver.close()

        # Volver a la ventana original
        driver.driver.switch_to.window(ventanas_antes[0])

        return codint

    except Exception as e:
        logger.error(f"❌ Error extrayendo codInt para folio {folio}: {str(e)}")

        # Asegurarse de volver a la ventana original
        try:
            ventanas_actuales = driver.driver.window_handles
            if len(ventanas_actuales) > 1:
                # Cerrar ventanas adicionales
                for ventana in ventanas_actuales[1:]:
                    driver.driver.switch_to.window(ventana)
                    driver.driver.close()
            # Volver a la primera ventana
            driver.driver.switch_to.window(ventanas_actuales[0])
        except Exception:
            pass

        return None


def _parse_period(period_text: str) -> str:
    """
    Parsea el texto de período a formato YYYY-MM

    Args:
        period_text: Texto del período (ej: "Ene 2025", "Feb 2025")

    Returns:
        Período en formato YYYY-MM (ej: "2025-01", "2025-02")
    """
    # Mapeo de meses en español a números
    meses = {
        'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Ago': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dic': '12'
    }

    try:
        # Formato esperado: "Mes YYYY"
        partes = period_text.strip().split()
        if len(partes) != 2:
            logger.warning(f"⚠️ Formato de período inesperado: {period_text}")
            return period_text  # Devolver original si no se puede parsear

        mes_texto = partes[0]
        anio = partes[1]

        mes_num = meses.get(mes_texto)
        if not mes_num:
            logger.warning(f"⚠️ Mes desconocido: {mes_texto}")
            return period_text

        return f"{anio}-{mes_num}"

    except Exception as e:
        logger.warning(f"⚠️ Error parseando período '{period_text}': {e}")
        return period_text


def _parse_period_with_components(period_text: str) -> tuple[str, int | None, int | None]:
    """
    Parsea el texto de período a formato YYYY-MM y separa en componentes

    Args:
        period_text: Texto del período (ej: "Ene 2025", "Feb 2025")

    Returns:
        Tuple con (period_display, period_year, period_month)
        - period_display: "YYYY-MM" format
        - period_year: Integer year or None if parsing fails
        - period_month: Integer month (1-12) or None if parsing fails
    """
    # Mapeo de meses en español a números
    meses = {
        'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4,
        'May': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8,
        'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12
    }

    try:
        # Formato esperado: "Mes YYYY"
        partes = period_text.strip().split()
        if len(partes) != 2:
            logger.warning(f"⚠️ Formato de período inesperado: {period_text}")
            return period_text, None, None

        mes_texto = partes[0]
        anio_str = partes[1]

        mes_num = meses.get(mes_texto)
        if not mes_num:
            logger.warning(f"⚠️ Mes desconocido: {mes_texto}")
            return period_text, None, None

        try:
            anio = int(anio_str)
        except ValueError:
            logger.warning(f"⚠️ Año inválido: {anio_str}")
            return period_text, None, None

        # Construir period_display en formato YYYY-MM
        period_display = f"{anio}-{mes_num:02d}"

        return period_display, anio, mes_num

    except Exception as e:
        logger.warning(f"⚠️ Error parseando período '{period_text}': {e}")
        return period_text, None, None


def _map_status(estado_text: str) -> str:
    """
    Mapea el texto de estado a un valor normalizado

    Args:
        estado_text: Texto del estado (ej: "Vigente", "Pendiente", etc.)

    Returns:
        Estado normalizado (with capital first letter for DB constraint)
    """
    estado_lower = estado_text.lower()

    if 'vigente' in estado_lower:
        return 'Vigente'
    elif 'rectificad' in estado_lower:
        return 'Rectificado'
    elif 'anulad' in estado_lower:
        return 'Anulado'
    else:
        # Default to Vigente if unknown status
        logger.warning(f"⚠️ Estado desconocido: {estado_text}, usando 'Vigente' por defecto")
        return 'Vigente'
