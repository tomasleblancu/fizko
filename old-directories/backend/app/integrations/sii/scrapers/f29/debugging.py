"""
Debugging utilities for F29 scraper

Handles screenshot capture and HTML saving to Supabase Storage.
"""
import logging
import time
import tempfile
import os

logger = logging.getLogger(__name__)


def take_debug_screenshot(driver, context: str, folio: str = "unknown") -> None:
    """
    Toma screenshot y guarda HTML para debugging en Supabase Storage

    Args:
        driver: WebDriver instance
        context: Contexto del error (ej: "click_intercepted", "codint_extraction", etc.)
        folio: Folio del formulario siendo procesado
    """
    try:
        from app.services.storage import get_debug_storage

        timestamp = int(time.time())
        storage = get_debug_storage()

        # Info adicional de contexto
        context_info = ""
        try:
            current_url = driver.driver.current_url
            window_count = len(driver.driver.window_handles)
            context_info = f"URL={current_url}, Windows={window_count}"
            logger.error(f"🔍 Context: {context_info}")
        except:
            pass

        # Screenshot a Supabase
        try:
            # Guardar screenshot temporalmente
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                driver.driver.save_screenshot(tmp_path)

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
                os.unlink(tmp_path)

        except Exception as ss_error:
            logger.warning(f"⚠️ No se pudo guardar screenshot: {ss_error}")

        # HTML source a Supabase
        try:
            html_content = driver.driver.page_source

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
        logger.warning(f"⚠️ Error en take_debug_screenshot: {e}")
