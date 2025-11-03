"""
Scraper especializado para boletas de honorarios
"""
import logging
import time
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from .base_scraper import BaseScraper
from ..exceptions import ScrapingException

logger = logging.getLogger(__name__)


class BoletasHonorarioScraper(BaseScraper):
    """
    Scraper especializado para obtener boletas de honorarios

    Extrae boletas de honorarios emitidas y recibidas usando el endpoint
    de la Propuesta F29 del SII.
    """

    def scrape(self, **kwargs) -> dict:
        """
        Implementacion del metodo abstracto scrape

        Redirige a obtener_boletas con los parametros proporcionados
        """
        return {
            'status': 'error',
            'message': 'Use obtener_boletas() method instead',
            'data': None
        }

    def obtener_boletas(
        self,
        mes: str,
        anio: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Obtiene boletas de honorarios para un período específico

        Args:
            mes: Mes a consultar (1-12)
            anio: Año a consultar (YYYY)
            max_retries: Número máximo de reintentos

        Returns:
            Dict con:
                - boletas: Lista de boletas
                - totales: Totales agregados
                - paginacion: Info de paginación

        Raises:
            ValueError: Si los parámetros no son válidos
            ScrapingException: Si hay errores en el scraping
        """
        try:
            # Validar parámetros
            self._validar_parametros(mes, anio)

            logger.info(f"🔎 Obteniendo boletas de honorarios - {anio}-{mes}")

            # Obtener datos de la empresa actual
            rut_contribuyente, dv = self._obtener_datos_empresa()

            # Construir payload para la petición
            payload = self._construir_payload(
                rut_contribuyente=rut_contribuyente,
                dv=dv,
                mes=mes,
                anio=anio,
                pagina_actual=1
            )

            # Ejecutar petición al endpoint
            response = self._ejecutar_peticion(payload, max_retries)

            # Parsear respuesta
            resultado = self._parsear_respuesta(response)

            logger.info(
                f"✅ Boletas obtenidas: {resultado['totales']['total_registros']} boletas\n"
                f"   - Total Honorarios Brutos: ${resultado['totales']['honorarios_bruto']:,}\n"
                f"   - Total Retención Receptor: ${resultado['totales']['honorarios_retencion_receptor']:,}\n"
                f"   - Total Honorarios Líquidos: ${resultado['totales']['honorarios_liquido']:,}"
            )

            return resultado

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"❌ Error obteniendo boletas de honorarios\n"
                f"   Error: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            raise ScrapingException(f"Error obteniendo boletas: {str(e)}") from e

    def _validar_parametros(self, mes: str, anio: str) -> None:
        """Valida que los parámetros sean correctos"""
        if not mes or not anio:
            raise ValueError("Debe especificar mes y año")

        if not mes.isdigit() or not (1 <= int(mes) <= 12):
            raise ValueError("El mes debe ser un número entre 1 y 12")

        if not anio.isdigit() or len(anio) != 4:
            raise ValueError("El año debe ser un número de 4 dígitos")

    def _obtener_datos_empresa(self) -> tuple[str, str]:
        """
        Obtiene el RUT y DV de la empresa desde la página actual del SII

        Returns:
            Tupla (rut_sin_puntos, dv)
        """
        try:
            # El RUT aparece en varios lugares del SII
            # Opción 1: Buscar en el HTML de la página actual
            page_source = self.driver.driver.page_source

            # Buscar patrón RUT en el HTML
            import re
            # Patrón: XX.XXX.XXX-X
            rut_match = re.search(r'(\d{1,2}\.?\d{3}\.?\d{3})-([0-9Kk])', page_source)

            if rut_match:
                rut_con_puntos = rut_match.group(1)
                dv = rut_match.group(2).upper()

                # Limpiar puntos del RUT
                rut_sin_puntos = rut_con_puntos.replace('.', '')

                logger.info(f"📋 RUT detectado: {rut_sin_puntos}-{dv}")
                return rut_sin_puntos, dv

            # Opción 2: Si no se encuentra en el HTML, intentar obtener de cookies/localStorage
            try:
                # Ejecutar JavaScript para obtener el RUT del localStorage
                rut_localStorage = self.driver.driver.execute_script(
                    "return localStorage.getItem('rutContribuyente') || sessionStorage.getItem('rutContribuyente');"
                )

                if rut_localStorage:
                    # Parsear RUT-DV
                    rut_match = re.match(r'(\d+)-([0-9Kk])', rut_localStorage)
                    if rut_match:
                        return rut_match.group(1), rut_match.group(2).upper()
            except Exception as e:
                logger.debug(f"No se pudo obtener RUT de localStorage: {e}")

            raise ScrapingException(
                "No se pudo detectar el RUT de la empresa. "
                "Asegúrese de estar autenticado en el SII."
            )

        except Exception as e:
            raise ScrapingException(f"Error obteniendo datos de empresa: {str(e)}") from e

    def _construir_payload(
        self,
        rut_contribuyente: str,
        dv: str,
        mes: str,
        anio: str,
        pagina_actual: int = 1
    ) -> Dict[str, Any]:
        """
        Construye el payload para la petición al endpoint

        Returns:
            Dict con el payload en formato JSON
        """
        return {
            "metaData": {
                "namespace": "cl.sii.sdi.lob.iva.propuestaf29.data.api.interfaces.RiacFacadeService/getBoletasHonorario",
                "conversationId": self._generar_conversation_id(),
                "transactionId": self._generar_transaction_id()
            },
            "data": {
                "rutContribuyente": rut_contribuyente,
                "dv": dv,
                "mes": mes,
                "anno": anio,
                "paginaActual": pagina_actual
            }
        }

    def _generar_conversation_id(self) -> str:
        """Genera un ID de conversación único"""
        import random
        import string
        # Formato: XXXXXXXXXX (10 caracteres alfanuméricos)
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    def _generar_transaction_id(self) -> str:
        """Genera un ID de transacción único (UUID)"""
        import uuid
        return str(uuid.uuid4())

    def _ejecutar_peticion(
        self,
        payload: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Ejecuta la petición HTTP al endpoint del SII

        Args:
            payload: Payload JSON para la petición
            max_retries: Número máximo de reintentos

        Returns:
            Response JSON parseado
        """
        import requests
        import json

        url = "https://www4.sii.cl/propuestaf29ui/services/data/riacFacadeService/getBoletasHonorario"

        # Obtener cookies del driver de Selenium
        selenium_cookies = self.driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        }

        for attempt in range(max_retries):
            try:
                logger.debug(f"Ejecutando petición (intento {attempt + 1}/{max_retries})")
                logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

                response = requests.post(
                    url,
                    json=payload,
                    cookies=cookies_dict,
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    response_data = response.json()

                    # Verificar si hay errores en la respuesta
                    metadata = response_data.get('metaData', {})
                    errors = metadata.get('errors')

                    if errors:
                        raise ScrapingException(f"Error en respuesta del SII: {errors}")

                    logger.debug(f"✅ Petición exitosa")
                    return response_data
                else:
                    logger.warning(f"⚠️ HTTP {response.status_code}: {response.text[:200]}")

                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        raise ScrapingException(
                            f"Error HTTP {response.status_code}: {response.text[:200]}"
                        )

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Error en petición (intento {attempt + 1}): {str(e)}")
                    time.sleep(2)
                    continue
                else:
                    raise ScrapingException(f"Error en petición: {str(e)}") from e

        raise ScrapingException("No se pudo completar la petición después de varios intentos")

    def _parsear_respuesta(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parsea la respuesta JSON del SII

        Args:
            response_data: Response JSON del endpoint

        Returns:
            Dict estructurado con boletas y totales
        """
        try:
            data = response_data.get('data', {})

            # Extraer lista de boletas
            boletas_raw = data.get('listBoletasHonorarios', [])
            boletas = []

            for boleta_raw in boletas_raw:
                boleta = {
                    'numero_boleta': boleta_raw.get('cantBoletas'),
                    'estado': boleta_raw.get('estadoBoleta'),
                    'fecha_boleta': boleta_raw.get('fechaBoleta'),
                    'fecha_emision': boleta_raw.get('fechaEmision'),
                    'usuario_emision': boleta_raw.get('usuarioEmision'),
                    'sociedad_profesional': boleta_raw.get('socProf') == 'SI',
                    'rut_receptor': boleta_raw.get('rutReceptor'),
                    'nombre_receptor': boleta_raw.get('nombreReceptor'),
                    'honorarios_brutos': boleta_raw.get('hBrutos', 0),
                    'retencion_emisor': boleta_raw.get('hRetencionEmisor', 0),
                    'retencion_receptor': boleta_raw.get('hRetencionReceptor', 0),
                    'honorarios_liquidos': boleta_raw.get('hLiquidos', 0),
                    'manual': boleta_raw.get('manual', False)
                }
                boletas.append(boleta)

            # Extraer totales
            totales = {
                'honorarios_bruto': data.get('honorariosBrutoTotal', 0),
                'honorarios_retencion_emisor': data.get('honorariosRetencionEmisorTotal', 0),
                'honorarios_retencion_receptor': data.get('honorariosRetencionReceptorTotal', 0),
                'honorarios_liquido': data.get('honorariosLiquidoTotal', 0),
                'total_registros': data.get('totalRegistros', 0),
                'bhep': data.get('bhep', False)
            }

            # Extraer info de paginación
            paginacion = {
                'pagina_actual': data.get('paginaActual', 1),
                'total_paginas': data.get('totalPaginas', 1),
                'tam_pagina': data.get('tamPagina', 10)
            }

            return {
                'boletas': boletas,
                'totales': totales,
                'paginacion': paginacion
            }

        except Exception as e:
            logger.error(f"❌ Error parseando respuesta: {str(e)}")
            raise ScrapingException(f"Error parseando respuesta: {str(e)}") from e

    def obtener_todas_las_paginas(
        self,
        mes: str,
        anio: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Obtiene todas las páginas de boletas para un período

        Args:
            mes: Mes a consultar (1-12)
            anio: Año a consultar (YYYY)
            max_retries: Número máximo de reintentos por página

        Returns:
            Dict con todas las boletas agregadas y totales
        """
        logger.info(f"📥 Obteniendo todas las páginas de boletas - {anio}-{mes}")

        # Obtener primera página
        resultado_primera = self.obtener_boletas(mes, anio, max_retries)

        boletas_completas = resultado_primera['boletas'].copy()
        paginacion = resultado_primera['paginacion']
        total_paginas = paginacion['total_paginas']

        # Si hay más páginas, obtenerlas
        if total_paginas > 1:
            logger.info(f"📑 Obteniendo {total_paginas - 1} páginas adicionales...")

            for pagina in range(2, total_paginas + 1):
                logger.debug(f"Obteniendo página {pagina}/{total_paginas}")

                # Construir payload para página específica
                rut_contribuyente, dv = self._obtener_datos_empresa()
                payload = self._construir_payload(
                    rut_contribuyente=rut_contribuyente,
                    dv=dv,
                    mes=mes,
                    anio=anio,
                    pagina_actual=pagina
                )

                # Ejecutar petición
                response = self._ejecutar_peticion(payload, max_retries)
                resultado_pagina = self._parsear_respuesta(response)

                # Agregar boletas
                boletas_completas.extend(resultado_pagina['boletas'])

                # Pequeña pausa entre páginas
                time.sleep(0.5)

        logger.info(f"✅ Total de boletas obtenidas: {len(boletas_completas)}")

        return {
            'boletas': boletas_completas,
            'totales': resultado_primera['totales'],
            'paginacion': {
                'total_paginas': total_paginas,
                'total_registros': len(boletas_completas)
            }
        }
