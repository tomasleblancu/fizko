"""
Data extraction logic for F29 scraper

Handles extraction of F29 data from tables and codInt extraction from modal windows.
"""
import logging
import time
import re
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    InvalidSessionIdException,
    WebDriverException,
    NoSuchWindowException,
    ElementClickInterceptedException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ...models.f29_types import FormularioF29
from .validation import check_session_valid
from .debugging import take_debug_screenshot
from .navigation import SEARCH_URL

logger = logging.getLogger(__name__)


def _cerrar_overlays(driver) -> None:
    """Detecta y cierra overlays que puedan estar bloqueando clicks"""
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
                overlays = driver.driver.find_elements(By.XPATH, overlay_selector)
                for overlay in overlays:
                    if overlay.is_displayed():
                        logger.debug(f"   ⚠️ Overlay detectado, intentando ocultar: {overlay_selector}")
                        # Ocultar con JavaScript
                        driver.driver.execute_script(
                            "arguments[0].style.display = 'none';",
                            overlay
                        )
                        time.sleep(0.3)
            except:
                pass
    except Exception as overlay_error:
        logger.debug(f"   No se pudo detectar/cerrar overlays: {overlay_error}")


def _analizar_interceptor(driver, element, folio: str) -> None:
    """Analiza qué elemento está interceptando el click"""
    try:
        interceptor_info = driver.driver.execute_script("""
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
        """, element)

        logger.error(f"🎯 Elemento interceptor detectado para folio {folio}:")
        logger.error(f"   - Tag: {interceptor_info.get('interceptor_tag')}")
        logger.error(f"   - Class: {interceptor_info.get('interceptor_class')}")
        logger.error(f"   - ID: {interceptor_info.get('interceptor_id')}")
        logger.error(f"   - Text: {interceptor_info.get('interceptor_text')}")
        logger.error(f"   - Botón visible: {interceptor_info.get('button_visible')}")
        logger.error(f"   - Botón rect: {interceptor_info.get('button_rect')}")
    except Exception as js_error:
        logger.warning(f"⚠️ No se pudo analizar interceptor: {js_error}")


def _click_con_retry(driver, element, folio: str, button_name: str, max_retries: int = 5) -> None:
    """
    Hace click en un elemento con retry robusto y manejo de interceptores

    Args:
        driver: WebDriver instance
        element: Elemento a clickear
        folio: Folio del formulario (para logging)
        button_name: Nombre del botón (para logging)
        max_retries: Número máximo de intentos

    Raises:
        Exception: Si todos los intentos fallan
    """
    for attempt in range(max_retries):
        try:
            # ESTRATEGIA 1: Esperar más tiempo inicial en cada reintento
            if attempt > 0:
                wait_time = 1.0 + (attempt * 0.5)
                logger.debug(f"   Esperando {wait_time}s antes de reintento {attempt + 1}...")
                time.sleep(wait_time)

            # ESTRATEGIA 2: Cerrar overlays antes del click
            _cerrar_overlays(driver)

            # ESTRATEGIA 3: Scroll al elemento y esperar que sea clickable
            try:
                driver.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                    element
                )
                time.sleep(0.5)

                # Esperar a que sea clickable
                WebDriverWait(driver.driver, 5).until(
                    EC.element_to_be_clickable(element)
                )
            except TimeoutException:
                logger.debug(f"   ⚠️ Timeout esperando elemento clickable, intentando de todas formas")

            # ESTRATEGIA 4: Intentar click según el intento
            if attempt < 3:
                # Primeros 3 intentos: click normal
                element.click()
                logger.debug(f"✓ Click normal exitoso en '{button_name}' (intento {attempt + 1})")
            else:
                # Últimos intentos: JavaScript click directo
                logger.debug(f"   Usando JavaScript click directo (intento {attempt + 1})")
                driver.driver.execute_script("arguments[0].click();", element)
                logger.debug(f"✓ JavaScript click exitoso en '{button_name}' (intento {attempt + 1})")

            # Si llegamos aquí, el click fue exitoso
            return

        except ElementClickInterceptedException as click_error:
            # 📸 Capturar screenshot para debugging
            try:
                take_debug_screenshot(driver, f"click_intercepted_{button_name.replace(' ', '_').lower()}", folio)
                _analizar_interceptor(driver, element, folio)
            except:
                pass

            if attempt < max_retries - 1:
                logger.debug(
                    f"⚠️ Click en '{button_name}' bloqueado (intento {attempt + 1}/{max_retries}): "
                    f"{str(click_error)[:100]}"
                )
            else:
                logger.error(
                    f"❌ Click en '{button_name}' bloqueado después de {max_retries} intentos para folio {folio}"
                )
                raise

        except Exception as e:
            if attempt < max_retries - 1:
                logger.debug(f"⚠️ Error en intento {attempt + 1} de click en '{button_name}': {type(e).__name__}")
            else:
                logger.error(f"❌ Error final en click de '{button_name}' después de {max_retries} intentos: {e}")
                raise


def extraer_codint_from_formulario_compacto(driver, folio_text: str) -> Optional[str]:
    """
    Extrae el codInt haciendo click en "Formulario Compacto" y capturando la URL

    Este método debe ejecutarse cuando ya estamos en la vista de detalle del folio
    (después de hacer click en "Ver")

    Args:
        driver: WebDriver instance
        folio_text: Texto del folio para logging

    Returns:
        codInt (id_interno_sii) o None si no se encuentra
    """
    # Validar sesión ANTES de intentar operaciones
    if not check_session_valid(driver):
        logger.error(
            f"❌ SESIÓN INVÁLIDA antes de extraer codInt para folio {folio_text}\n"
            f"   La sesión de Selenium ya estaba cerrada/expirada antes de comenzar"
        )
        return None

    try:
        logger.debug(f"🔍 Iniciando extracción de codInt para folio {folio_text}")

        # Paso 1: Buscar el botón "Formulario Compacto"
        logger.debug(f"   [1/6] Buscando botón 'Formulario Compacto'...")

        # Esperar a que el botón esté presente
        formulario_compacto_btn = WebDriverWait(driver.driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//button[contains(text(), 'Formulario Compacto')]"
            ))
        )
        logger.debug(f"   [1/6] ✓ Botón encontrado")

        # Paso 2: Guardar ventanas actuales
        logger.debug(f"   [2/6] Obteniendo ventanas actuales...")
        ventanas_antes = driver.driver.window_handles
        logger.debug(f"   [2/6] ✓ Ventanas antes: {len(ventanas_antes)}")

        # Paso 3: Click en Formulario Compacto con retry anti-interceptor
        logger.debug(f"   [3/6] Haciendo click en 'Formulario Compacto' (con anti-interceptor)...")
        _click_con_retry(driver, formulario_compacto_btn, folio_text, "Formulario Compacto")
        logger.debug(f"   [3/6] ✓ Click realizado, esperando 3s...")
        time.sleep(3)  # Aumentado a 3s para dar más tiempo en Docker

        # Paso 4: Verificar sesión después del click
        logger.debug(f"   [4/6] Verificando sesión después del click...")
        if not check_session_valid(driver):
            logger.error(f"   [4/6] ❌ SESIÓN SE INVALIDÓ DESPUÉS DEL CLICK en 'Formulario Compacto'")
            return None
        logger.debug(f"   [4/6] ✓ Sesión sigue válida")

        # Paso 5: Verificar si se abrió nueva pestaña
        logger.debug(f"   [5/6] Verificando nuevas ventanas...")
        ventanas_despues = driver.driver.window_handles
        logger.debug(f"   [5/6] ✓ Ventanas después: {len(ventanas_despues)}")

        if len(ventanas_despues) > len(ventanas_antes):
            # Paso 6a: Cambiar a la nueva pestaña
            logger.debug(f"   [6a] Cambiando a nueva ventana...")
            nueva_ventana = ventanas_despues[-1]
            driver.driver.switch_to.window(nueva_ventana)
            logger.debug(f"   [6a] ✓ Cambiado a ventana nueva")

            # Verificar sesión después del switch
            if not check_session_valid(driver):
                logger.error(f"   [6a] ❌ SESIÓN SE INVALIDÓ DESPUÉS DE switch_to.window()")
                return None

            # Obtener la URL (contiene el codInt)
            logger.debug(f"   [6b] Obteniendo URL del formulario compacto...")
            url_compacto = driver.driver.current_url
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
            driver.driver.close()
            logger.debug(f"   [6d] ✓ Ventana cerrada")

            # Volver a la ventana original
            # NOTA: No verificamos la sesión aquí porque window_handles puede fallar temporalmente
            # después de close(), pero switch_to.window() funciona correctamente
            logger.debug(f"   [6e] Volviendo a ventana original...")
            try:
                driver.driver.switch_to.window(ventanas_antes[0])
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
            take_debug_screenshot(driver, "invalid_session_codint", folio_text)
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
            take_debug_screenshot(driver, "webdriver_codint", folio_text)
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
        if check_session_valid(driver):
            try:
                ventanas = driver.driver.window_handles
                if len(ventanas) > 1:
                    logger.debug("🔄 Intentando cerrar ventanas adicionales...")
                    driver.driver.close()
                    driver.driver.switch_to.window(ventanas[0])
                    logger.debug("✅ Ventanas cerradas correctamente")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Error limpiando ventanas: {cleanup_error}")
        else:
            logger.warning("⚠️ No se puede limpiar ventanas: sesión inválida")

        return None


def extraer_resultados(driver, save_callback: Optional[callable] = None) -> List[FormularioF29]:
    """
    Extrae los resultados de la tabla

    Args:
        driver: WebDriver instance
        save_callback: Callback opcional para guardar cada formulario inmediatamente

    Returns:
        Lista de formularios F29 extraídos
    """
    resultados: List[FormularioF29] = []

    try:
        tabla = driver.wait_for_element(
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
                if not check_session_valid(driver):
                    logger.error(
                        f"❌ Sesión inválida al intentar extraer codInt para folio {datos['folio']}\n"
                        f"   Saltando este formulario"
                    )
                    resultados.append(formulario)
                    continue

                logger.debug(f"🔍 Procesando folio {datos['folio']} (índice {datos['row_index']})")

                # Re-obtener la tabla actualizada
                tabla = driver.wait_for_element(
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
                    id_interno_sii = extraer_codint_from_formulario_compacto(driver, datos['folio'])

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

                    # Volver a la tabla principal
                    _volver_a_tabla_principal(driver, datos['folio'])

            except InvalidSessionIdException as e:
                # 📸 CAPTURAR SCREENSHOT si es posible
                try:
                    take_debug_screenshot(driver, "invalid_session_proceso", datos['folio'])
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
                    take_debug_screenshot(driver, "webdriver_proceso", datos['folio'])
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


def _volver_a_tabla_principal(driver, folio: str) -> None:
    """
    Vuelve a la tabla principal después de extraer codInt con retry mejorado

    Args:
        driver: WebDriver instance
        folio: Folio del formulario actual (para logging)
    """
    try:
        if not check_session_valid(driver):
            logger.error("❌ Sesión inválida, no se puede hacer click en 'Volver'")
            return

        # 📊 LOGGING DE ESTADO ANTES DE INTENTAR VOLVER
        try:
            logger.debug(f"📊 Estado antes de click 'Volver' para folio {folio}:")
            logger.debug(f"   - URL actual: {driver.driver.current_url}")
            logger.debug(f"   - Ventanas abiertas: {len(driver.driver.window_handles)}")
            logger.debug(f"   - Document readyState: {driver.driver.execute_script('return document.readyState')}")

            # Verificar si hay overlays visibles con z-index alto
            overlay_count = driver.driver.execute_script("""
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
                        volver_btn = WebDriverWait(driver.driver, 3).until(
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
                _cerrar_overlays(driver)

                # ESTRATEGIA 4: Scroll y esperar que el elemento sea clickable
                try:
                    driver.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                        volver_btn
                    )
                    time.sleep(0.5)

                    # Esperar a que sea clickable
                    volver_btn = WebDriverWait(driver.driver, 3).until(
                        EC.element_to_be_clickable(volver_btn)
                    )
                except TimeoutException:
                    logger.debug(f"   ⚠️ Timeout esperando elemento clickable, intentando de todas formas")

                # ESTRATEGIA 5: Intentar click según el intento
                if attempt < 3:
                    # Primeros 3 intentos: click normal
                    volver_btn.click()
                    logger.debug(f"🔙 Click normal exitoso en 'Volver' (intento {attempt + 1})")
                else:
                    # Últimos 2 intentos: JavaScript click directo
                    logger.debug(f"   Usando JavaScript click directo (intento {attempt + 1})")
                    driver.driver.execute_script("arguments[0].click();", volver_btn)
                    logger.debug(f"🔙 JavaScript click exitoso en 'Volver' (intento {attempt + 1})")

                # Si llegamos aquí, el click fue exitoso
                time.sleep(0.5)
                break

            except ElementClickInterceptedException as click_error:
                # 📸 CAPTURAR SCREENSHOT + HTML para debugging
                take_debug_screenshot(driver, "click_intercepted", folio)
                _analizar_interceptor(driver, volver_btn, folio)

                if attempt < max_retries - 1:
                    logger.debug(
                        f"⚠️ Click bloqueado (intento {attempt + 1}/{max_retries}): {str(click_error)[:100]}"
                    )
                else:
                    # ESTRATEGIA 6: Último recurso - navegar directamente
                    _navegar_directo_a_tabla(driver)
                    break

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.debug(f"⚠️ Error en intento {attempt + 1}: {type(e).__name__}: {str(e)[:100]}")
                else:
                    logger.warning(f"⚠️ Error final después de {max_retries} intentos: {e}")
                    raise

        logger.debug(f"🔙 Volviendo a tabla principal")

    except Exception as e:
        logger.warning(
            f"⚠️ Error al volver a tabla principal: {type(e).__name__}: {e}\n"
            f"   No es crítico - el formulario ya fue procesado. Continuando..."
        )
        # No es crítico - continuar procesando
        # El formulario ya fue guardado con su codInt


def _navegar_directo_a_tabla(driver) -> None:
    """Último recurso: navega directamente de vuelta a la tabla de búsqueda"""
    logger.warning("⚠️ Click bloqueado después de todos los intentos, usando estrategia de navegación directa")
    try:
        # Usar history.back() de JavaScript
        driver.driver.execute_script("window.history.back();")
        time.sleep(1)
        logger.debug("✅ Navegación con history.back() exitosa")
    except Exception as nav_error:
        logger.warning(f"⚠️ Navegación también falló: {nav_error}")
        # Última alternativa: navegar a la URL de búsqueda
        try:
            driver.navigate_to(SEARCH_URL)
            time.sleep(2)
            logger.debug("✅ Navegación directa a SEARCH_URL exitosa")
        except Exception as url_error:
            logger.error(f"❌ Todas las estrategias de navegación fallaron: {url_error}")
            raise
