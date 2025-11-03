"""
Métodos relacionados con Formulario 29 y declaraciones
"""
import logging
from typing import Dict, Any, List, Optional

from .dte_methods import DTEMethods
from ..extractors import F29Extractor
from ..exceptions import ExtractionError

logger = logging.getLogger(__name__)


class F29Methods(DTEMethods):
    """
    Métodos para Form29, propuestas, declaraciones y mensajes
    Hereda de DTEMethods
    """

    def get_f29_lista(
        self,
        anio: str,
        folio: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca formularios F29

        Args:
            anio: Año (formato YYYY, ej: "2024")
            folio: Folio específico (opcional)

        Returns:
            Lista de formularios F29 encontrados

        Raises:
            ExtractionError: Si falla la búsqueda
        """
        self._ensure_initialized()

        # F29 scraping requiere autenticación fresca por navegación Selenium
        logger.info("🔐 F29 scraping requires fresh authentication...")
        self.login(force_new=True)

        # Lazy loading del extractor
        if not self._f29_extractor:
            self._f29_extractor = F29Extractor(self._driver, self.tax_id)

        return self._f29_extractor.search(anio, folio)

    def get_f29_compacto(
        self,
        folio: str,
        id_interno_sii: str
    ) -> Optional[bytes]:
        """
        Descarga el PDF del formulario F29 compacto

        Args:
            folio: Folio del formulario
            id_interno_sii: ID interno del SII (obtenido de get_f29_lista)

        Returns:
            PDF en bytes, o None si falla

        Example:
            >>> formularios = client.get_f29_lista("2024")
            >>> f29 = formularios[0]
            >>> pdf = client.get_f29_compacto(f29['folio'], f29['id_interno_sii'])
            >>> with open('f29.pdf', 'wb') as f:
            ...     f.write(pdf)

        Raises:
            ExtractionError: Si falla la descarga
        """
        # Lazy loading del extractor
        if not self._f29_extractor:
            self._f29_extractor = F29Extractor(self._driver, self.tax_id)

        return self._f29_extractor.get_formulario_compacto(
            folio=folio,
            id_interno_sii=id_interno_sii
        )

    def get_propuesta_f29(self, periodo: str) -> Dict[str, Any]:
        """
        Obtiene la propuesta de declaración F29 pre-calculada por el SII.

        Este método consulta el endpoint que devuelve el F29 con valores
        pre-llenados automáticamente por el SII, incluyendo códigos propuestos
        basados en los DTEs del período.

        Args:
            periodo: Período tributario en formato YYYYMM (ej: "202510")

        Returns:
            Dict con la propuesta completa del F29

        Raises:
            ExtractionError: Si falla la obtención de la propuesta

        Example:
            >>> propuesta = client.get_propuesta_f29("202510")
            >>> codigos = propuesta['data']['listCodPropuestos']
        """
        # Lazy loading del extractor
        if not self._f29_extractor:
            self._f29_extractor = F29Extractor(self._driver, self.tax_id)

        # Obtener cookies (hacer login si es necesario)
        cookies = self.get_cookies()

        return self._f29_extractor.get_declaracion_propuesta(
            periodo=periodo,
            cookies=cookies
        )

    def get_tasa_ppmo(
        self,
        periodo: str,
        categoria_tributaria: int = 1,
        tipo_formulario: str = "FMNINT"
    ) -> Dict[str, Any]:
        """
        Obtiene la tasa de PPMO (Pagos Provisionales Mensuales Obligatorios).

        Args:
            periodo: Período tributario en formato YYYYMM (ej: "202510")
            categoria_tributaria: Categoría tributaria (1=Primera categoría, default: 1)
            tipo_formulario: Tipo de formulario (default: "FMNINT")

        Returns:
            Dict con información de tasa PPMO

        Raises:
            ExtractionError: Si falla la obtención

        Example:
            >>> tasa_info = client.get_tasa_ppmo("202510")
            >>> tasa = tasa_info['data']['cod115']  # "0.125"
        """
        # Lazy loading del extractor
        if not self._f29_extractor:
            self._f29_extractor = F29Extractor(self._driver, self.tax_id)

        # Obtener cookies (hacer login si es necesario)
        cookies = self.get_cookies()

        return self._f29_extractor.get_tasa_ppmo(
            periodo=periodo,
            categoria_tributaria=categoria_tributaria,
            tipo_formulario=tipo_formulario,
            cookies=cookies
        )

    def get_declaraciones_con_estados(
        self,
        mes: str,
        anio: str,
        form_id: str = "2",
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Obtiene declaraciones F29 con sus estados para un período específico.

        Args:
            mes: Mes a consultar (1-12)
            anio: Año a consultar (YYYY)
            form_id: ID del formulario (default: "2" para F29)
            max_retries: Número máximo de reintentos

        Returns:
            Lista de declaraciones (vacía si no hay)

        Raises:
            ValueError: Si los parámetros no son válidos
            ExtractionError: Si falla la obtención
        """
        from ..scrapers.boletas_honorario_scraper import BoletasHonorarioScraper

        # Validar parámetros
        if not mes or not anio:
            raise ValueError("Debe especificar mes y año")

        if not mes.isdigit() or not (1 <= int(mes) <= 12):
            raise ValueError("El mes debe ser un número entre 1 y 12")

        if not anio.isdigit() or len(anio) != 4:
            raise ValueError("El año debe ser un número de 4 dígitos")

        self._ensure_initialized()

        # Asegurar autenticación
        logger.info("🔐 Declaraciones con estados require authentication...")
        self.login()

        try:
            # Obtener datos del RUT
            scraper = BoletasHonorarioScraper(self._driver)
            rut_contribuyente, dv = scraper._obtener_datos_empresa()

            # Construir payload
            import uuid
            import random
            import string

            conversation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            transaction_id = str(uuid.uuid4())

            payload = {
                "metaData": {
                    "namespace": "cl.sii.sdi.lob.iva.propuestaf29.data.api.interfaces.FacadeAdapterService/getDeclaracionConEstados",
                    "conversationId": conversation_id,
                    "transactionId": transaction_id
                },
                "data": {
                    "rut": rut_contribuyente,
                    "dv": dv,
                    "formId": form_id,
                    "mes": mes,
                    "anno": anio
                }
            }

            # Ejecutar petición
            import requests
            import json

            url = "https://www4.sii.cl/propuestaf29ui/services/data/facadeAdapterService/getDeclaracionConEstados"

            # Obtener cookies del driver
            selenium_cookies = self._driver.get_cookies()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            }

            for attempt in range(max_retries):
                try:
                    logger.debug(f"Ejecutando petición (intento {attempt + 1}/{max_retries})")

                    response = requests.post(
                        url,
                        json=payload,
                        cookies=cookies_dict,
                        headers=headers,
                        timeout=30
                    )

                    if response.status_code == 200:
                        response_data = response.json()

                        # Verificar errores
                        metadata = response_data.get('metaData', {})
                        errors = metadata.get('errors')

                        if errors:
                            raise ExtractionError(f"Error en respuesta del SII: {errors}")

                        declaraciones = response_data.get('data', [])

                        logger.info(f"✅ Declaraciones obtenidas: {len(declaraciones)} registros")

                        return declaraciones
                    else:
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(2)
                            continue
                        else:
                            raise ExtractionError(f"Error HTTP {response.status_code}")

                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2)
                        continue
                    else:
                        raise ExtractionError(f"Error en petición: {str(e)}") from e

            raise ExtractionError("No se pudo completar la petición")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ Error obteniendo declaraciones: {e}", exc_info=True)
            raise ExtractionError(f"Error obteniendo declaraciones: {str(e)}") from e

    def get_mensajes_contribuyente(
        self,
        periodo: str,
        form_id: str = "2",
        tipo: str = "IP",
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene mensajes del SII para el contribuyente.

        Args:
            periodo: Período tributario (YYYYMM)
            form_id: ID del formulario (default: "2")
            tipo: Tipo de mensaje (default: "IP")
            max_retries: Número máximo de reintentos

        Returns:
            Dict con mensajes o None si no hay

        Raises:
            ValueError: Si los parámetros no son válidos
            ExtractionError: Si falla la obtención
        """
        from ..scrapers.boletas_honorario_scraper import BoletasHonorarioScraper

        # Validar período
        if not periodo or len(periodo) != 6 or not periodo.isdigit():
            raise ValueError("El período debe estar en formato YYYYMM")

        self._ensure_initialized()

        # Asegurar autenticación
        logger.info("🔐 Mensajes contribuyente require authentication...")
        self.login()

        try:
            # Obtener datos del RUT
            scraper = BoletasHonorarioScraper(self._driver)
            rut_contribuyente, dv = scraper._obtener_datos_empresa()

            # Construir payload
            import uuid
            import random
            import string

            conversation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            transaction_id = str(uuid.uuid4())

            payload = {
                "metaData": {
                    "namespace": "cl.sii.sdi.lob.iva.propuestaf29.data.api.interfaces.FacadeAdapterService/getMensajesContribuyente",
                    "conversationId": conversation_id,
                    "transactionId": transaction_id
                },
                "data": {
                    "rut": rut_contribuyente,
                    "periodo": periodo,
                    "formId": form_id,
                    "tipo": tipo
                }
            }

            # Ejecutar petición
            import requests

            url = "https://www4.sii.cl/propuestaf29ui/services/data/facadeAdapterService/getMensajesContribuyente"

            selenium_cookies = self._driver.get_cookies()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            }

            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        url,
                        json=payload,
                        cookies=cookies_dict,
                        headers=headers,
                        timeout=30
                    )

                    if response.status_code == 200:
                        response_data = response.json()

                        # Verificar errores
                        metadata = response_data.get('metaData', {})
                        errors = metadata.get('errors')

                        if errors:
                            raise ExtractionError(f"Error en respuesta del SII: {errors}")

                        mensajes = response_data.get('data')

                        if mensajes is None:
                            logger.info("ℹ️  No hay mensajes")
                        else:
                            logger.info(f"✅ Mensajes obtenidos")

                        return mensajes
                    else:
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(2)
                            continue
                        else:
                            raise ExtractionError(f"Error HTTP {response.status_code}")

                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2)
                        continue
                    else:
                        raise ExtractionError(f"Error en petición: {str(e)}") from e

            raise ExtractionError("No se pudo completar la petición")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ Error obteniendo mensajes: {e}", exc_info=True)
            raise ExtractionError(f"Error obteniendo mensajes: {str(e)}") from e

    def guardar_propuesta_f29(
        self,
        mes: str,
        anio: str,
        tipo_propuesta_inicial: int = 44,
        form_codigo: str = "29",
        max_retries: int = 3
    ) -> bool:
        """
        Guarda la propuesta de declaración F29 en el SII (borrador).

        Este método permite guardar un borrador de la declaración F29
        antes de presentarla oficialmente. Es útil para guardar el trabajo
        en progreso.

        Args:
            mes: Mes del período tributario (1-12)
            anio: Año del período tributario (YYYY)
            tipo_propuesta_inicial: Tipo de propuesta (default: 44)
            form_codigo: Código del formulario (default: "29")
            max_retries: Número máximo de reintentos

        Returns:
            True si se guardó exitosamente

        Raises:
            ValueError: Si los parámetros no son válidos
            ExtractionError: Si falla el guardado

        Example:
            >>> # Guardar borrador de declaración para octubre 2025
            >>> client.guardar_propuesta_f29(mes="10", anio="2025")
            True

        Note:
            - Este método NO presenta la declaración, solo guarda un borrador
            - No tiene response body, solo confirma con HTTP 200
            - El tipo_propuesta_inicial=44 es el valor estándar observado
        """
        from ..scrapers.boletas_honorario_scraper import BoletasHonorarioScraper

        # Validar parámetros
        if not mes or not anio:
            raise ValueError("Debe especificar mes y año")

        if not mes.isdigit() or not (1 <= int(mes) <= 12):
            raise ValueError("El mes debe ser un número entre 1 y 12")

        if not anio.isdigit() or len(anio) != 4:
            raise ValueError("El año debe ser un número de 4 dígitos")

        self._ensure_initialized()

        # Asegurar autenticación
        logger.info("🔐 Guardar propuesta F29 require authentication...")
        self.login()

        try:
            # Obtener datos del RUT
            scraper = BoletasHonorarioScraper(self._driver)
            rut_contribuyente, dv = scraper._obtener_datos_empresa()

            # Construir payload
            import uuid
            import random
            import string

            conversation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            transaction_id = str(uuid.uuid4())

            payload = {
                "metaData": {
                    "namespace": "cl.sii.sdi.lob.iva.propuestaf29.data.api.interfaces.FacadeService/guardarPropuesta",
                    "conversationId": conversation_id,
                    "transactionId": transaction_id
                },
                "data": {
                    "rutCntr": rut_contribuyente,
                    "dvCntr": dv,
                    "formCodigo": form_codigo,
                    "tipoPropuestaInicial": tipo_propuesta_inicial,
                    "periodo": {
                        "anno": anio,
                        "mes": mes
                    }
                }
            }

            # Ejecutar petición
            import requests

            url = "https://www4.sii.cl/propuestaf29ui/services/data/facadeService/guardarPropuesta"

            selenium_cookies = self._driver.get_cookies()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            }

            for attempt in range(max_retries):
                try:
                    logger.debug(f"Guardando propuesta F29 (intento {attempt + 1}/{max_retries})")

                    response = requests.post(
                        url,
                        json=payload,
                        cookies=cookies_dict,
                        headers=headers,
                        timeout=30
                    )

                    if response.status_code == 200:
                        # Este endpoint no tiene response body
                        # Solo confirma con 200 OK
                        logger.info(
                            f"✅ Propuesta F29 guardada exitosamente\n"
                            f"   Período: {anio}-{mes}\n"
                            f"   Form: {form_codigo}\n"
                            f"   Tipo: {tipo_propuesta_inicial}"
                        )
                        return True
                    else:
                        logger.warning(f"⚠️ HTTP {response.status_code}: {response.text[:200]}")

                        if attempt < max_retries - 1:
                            import time
                            time.sleep(2)
                            continue
                        else:
                            raise ExtractionError(
                                f"Error guardando propuesta: HTTP {response.status_code}"
                            )

                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Error en petición (intento {attempt + 1}): {str(e)}")
                        import time
                        time.sleep(2)
                        continue
                    else:
                        raise ExtractionError(f"Error en petición: {str(e)}") from e

            raise ExtractionError("No se pudo completar la petición")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ Error guardando propuesta F29: {e}", exc_info=True)
            raise ExtractionError(f"Error guardando propuesta F29: {str(e)}") from e

    def enviar_datos_flujo(
        self,
        mes: str,
        anio: str,
        tipo: int = 44,
        form: str = "29",
        max_retries: int = 3
    ) -> bool:
        """
        Envía datos al flujo de F29.

        Nota: El propósito exacto de este endpoint no está documentado,
        pero parece ser parte del flujo de procesamiento de la declaración F29.

        Args:
            mes (str): Mes (1-12 o con formato "01"-"12")
            anio (str): Año (ej: "2025")
            tipo (int): Tipo de flujo (default: 44)
            form (str): Código del formulario (default: "29")
            max_retries (int): Número máximo de reintentos en caso de error

        Returns:
            bool: True si la operación fue exitosa (HTTP 200)

        Raises:
            ValueError: Si los parámetros son inválidos
            ExtractionError: Si hay un error en la comunicación con SII

        Ejemplo:
            >>> with SIIClient(tax_id="12345678-9", password="secret") as client:
            ...     client.login()
            ...     success = client.enviar_datos_flujo(mes="10", anio="2025")
            ...     if success:
            ...         print("Datos enviados al flujo exitosamente")
        """
        try:
            # Validar parámetros
            if not mes or not anio:
                raise ValueError("mes y anio son obligatorios")

            # Normalizar mes a formato sin ceros a la izquierda para validación
            mes_int = int(mes)
            if not 1 <= mes_int <= 12:
                raise ValueError("mes debe estar entre 1 y 12")

            # Normalizar año
            anio_int = int(anio)
            if anio_int < 2000 or anio_int > 2100:
                raise ValueError("anio debe estar entre 2000 y 2100")

            # Obtener RUT y DV automáticamente
            from app.integrations.sii.scrapers.boletas_honorario_scraper import BoletasHonorarioScraper
            scraper = BoletasHonorarioScraper(self.driver)
            rut_contribuyente, dv = scraper._obtener_datos_empresa()

            logger.info(f"📤 Enviando datos al flujo F29 para {mes}/{anio}...")

            # Construir el período en formato YYYYMM
            periodo = f"{anio}{mes.zfill(2)}"

            endpoint_url = "https://www4.sii.cl/propuestaf29ui/services/data/facadeService/enviarDatosFlujo"

            for attempt in range(max_retries):
                try:
                    # Generar IDs únicos para la petición
                    conversation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                    transaction_id = str(uuid.uuid4())

                    # Construir el payload
                    payload = {
                        "metaData": {
                            "namespace": "cl.sii.sdi.lob.iva.propuestaf29.data.api.interfaces.FacadeService/enviarDatosFlujo",
                            "conversationId": conversation_id,
                            "transactionId": transaction_id
                        },
                        "data": {
                            "rut": rut_contribuyente,
                            "dv": dv,
                            "periodo": periodo,
                            "form": form,
                            "tipo": tipo
                        }
                    }

                    logger.debug(f"Payload (intento {attempt + 1}/{max_retries}): {payload}")

                    # Realizar la petición
                    response = requests.post(
                        endpoint_url,
                        json=payload,
                        cookies={cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()},
                        timeout=30
                    )

                    logger.debug(f"Status code: {response.status_code}")

                    # El endpoint retorna HTTP 200 sin body si es exitoso
                    if response.status_code == 200:
                        logger.info(f"✅ Datos enviados al flujo exitosamente para período {mes}/{anio}")
                        return True
                    else:
                        logger.warning(f"⚠️ Respuesta inesperada: {response.status_code}")
                        if attempt < max_retries - 1:
                            logger.info(f"Reintentando en 2 segundos...")
                            time.sleep(2)
                            continue
                        else:
                            raise ExtractionError(f"Error al enviar datos al flujo: HTTP {response.status_code}")

                except requests.RequestException as e:
                    logger.error(f"❌ Error en petición (intento {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        logger.info(f"Reintentando en 2 segundos...")
                        time.sleep(2)
                        continue
                    else:
                        raise ExtractionError(f"Error en petición: {str(e)}") from e

            raise ExtractionError("No se pudo completar la petición")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ Error enviando datos al flujo: {e}", exc_info=True)
            raise ExtractionError(f"Error enviando datos al flujo: {str(e)}") from e
