"""
Métodos relacionados con boletas de honorarios
"""
import logging
import random
import string
import uuid
import time
from typing import Dict, Any, List

import requests

from .f29_methods import F29Methods
from ..exceptions import ExtractionError

logger = logging.getLogger(__name__)


class BoletasMethods(F29Methods):
    """
    Métodos para boletas de honorarios
    Hereda de F29Methods (que tiene todos los métodos de F29/declaraciones)
    """

    def get_boletas_honorarios(
        self,
        mes: str,
        anio: str,
        pagina: int = 1,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Obtiene boletas de honorarios para un período específico mediante HTTP request.

        Args:
            mes: Mes a consultar (1-12)
            anio: Año a consultar (YYYY)
            pagina: Número de página (default: 1)
            max_retries: Número máximo de reintentos

        Returns:
            Dict con boletas, totales y paginación:
            {
                "boletas": [...],
                "totales": {
                    "total_registros": int,
                    "total_paginas": int,
                    "pagina_actual": int
                }
            }

        Raises:
            ValueError: Si los parámetros no son válidos
            ExtractionError: Si falla la obtención

        Example:
            >>> boletas = client.get_boletas_honorarios(mes="10", anio="2025")
            >>> print(f"Total: {boletas['totales']['total_registros']}")
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

            # Validar página
            if pagina < 1:
                raise ValueError("pagina debe ser >= 1")

            self._ensure_initialized()

            # Obtener RUT y DV del tax_id (formato: "12345678-9")
            if '-' in self.tax_id:
                rut_contribuyente, dv = self.tax_id.rsplit('-', 1)
            else:
                # Si no tiene guion, asumir que el último caracter es el DV
                rut_contribuyente = self.tax_id[:-1]
                dv = self.tax_id[-1]

            # DV debe estar en mayúscula
            dv = dv.upper()

            # Obtener cookies (hace login automáticamente si es necesario)
            # Mismo patrón que get_compras() y get_ventas()
            cookies = self.get_cookies()

            logger.info(f"💼 Obteniendo boletas de honorarios para {mes}/{anio} (página {pagina})...")

            endpoint_url = "https://www4.sii.cl/propuestaf29ui/services/data/riacFacadeService/getBoletasHonorario"

            for attempt in range(max_retries):
                try:
                    # Generar IDs únicos para la petición
                    conversation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                    transaction_id = str(uuid.uuid4())

                    # Convertir cookies a dict para requests
                    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}

                    # Construir el payload (estructura exacta del scraper)
                    payload = {
                        "metaData": {
                            "namespace": "cl.sii.sdi.lob.iva.propuestaf29.data.api.interfaces.RiacFacadeService/getBoletasHonorario",
                            "conversationId": conversation_id,
                            "transactionId": transaction_id
                        },
                        "data": {
                            "rutContribuyente": rut_contribuyente,  # ← Cambiado de "rut"
                            "dv": dv,
                            "mes": mes,
                            "anno": anio,
                            "paginaActual": pagina  # ← Cambiado de "pagina"
                        }
                    }

                    logger.info(f"📤 Payload (intento {attempt + 1}/{max_retries}): {payload}")

                    # Headers necesarios para la petición (mismo patrón que otros métodos F29)
                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    }

                    # Realizar la petición
                    response = requests.post(
                        endpoint_url,
                        json=payload,
                        cookies=cookies_dict,
                        headers=headers,
                        timeout=30
                    )

                    logger.info(f"📥 Status code: {response.status_code}")

                    # Verificar respuesta exitosa
                    if response.status_code == 200:
                        result = response.json()
                        data = result.get("data", {})

                        logger.info(f"✅ Boletas de honorarios obtenidas exitosamente para {mes}/{anio} (página {pagina})")

                        # Transformar formato API (camelCase) a formato parser (snake_case)
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

                        # Retornar estructura compatible con el parser
                        return {
                            'boletas': boletas,
                            'totales': {
                                'total_registros': data.get('totalRegistros', 0),
                                'total_paginas': data.get('totalPaginas', 0),
                                'pagina_actual': data.get('paginaActual', pagina),
                                'honorarios_bruto_total': data.get('honorariosBrutoTotal', 0),
                                'honorarios_retencion_emisor_total': data.get('honorariosRetencionEmisorTotal', 0),
                                'honorarios_retencion_receptor_total': data.get('honorariosRetencionReceptorTotal', 0),
                                'honorarios_liquido_total': data.get('honorariosLiquidoTotal', 0)
                            }
                        }
                    else:
                        # Log response body para debugging
                        try:
                            response_body = response.text[:500]  # Primeros 500 caracteres
                            logger.warning(f"⚠️ Respuesta inesperada: {response.status_code}")
                            logger.warning(f"📄 Response body: {response_body}")
                        except Exception:
                            logger.warning(f"⚠️ Respuesta inesperada: {response.status_code}")

                        if attempt < max_retries - 1:
                            logger.info(f"Reintentando en 2 segundos...")
                            time.sleep(2)
                            continue
                        else:
                            raise ExtractionError(f"Error al obtener boletas de honorarios: HTTP {response.status_code}")

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
            logger.error(f"❌ Error obteniendo boletas de honorarios: {e}", exc_info=True)
            raise ExtractionError(f"Error obteniendo boletas de honorarios: {str(e)}") from e

    def get_boletas_honorarios_todas_paginas(
        self,
        mes: str,
        anio: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Obtiene TODAS las páginas de boletas de honorarios mediante HTTP requests.

        Args:
            mes: Mes a consultar (1-12)
            anio: Año a consultar (YYYY)
            max_retries: Número máximo de reintentos por página

        Returns:
            Dict con todas las boletas y totales:
            {
                "boletas": [...],  # Lista completa de todas las páginas
                "totales": {
                    "total_registros": int,
                    "total_paginas": int
                }
            }

        Raises:
            ValueError: Si los parámetros no son válidos
            ExtractionError: Si falla la obtención

        Example:
            >>> boletas = client.get_boletas_honorarios_todas_paginas(mes="10", anio="2025")
            >>> print(f"Total: {len(boletas['boletas'])}")
        """
        try:
            logger.info(f"📚 Obteniendo TODAS las páginas de boletas de honorarios para {mes}/{anio}...")

            # Obtener primera página para conocer el total de páginas
            primera_pagina = self.get_boletas_honorarios(
                mes=mes,
                anio=anio,
                pagina=1,
                max_retries=max_retries
            )

            # Extraer información de paginación
            totales = primera_pagina.get("totales", {})
            total_paginas = totales.get("total_paginas", 1)
            total_registros = totales.get("total_registros", 0)

            logger.info(f"  📊 Total de páginas: {total_paginas}")
            logger.info(f"  📊 Total de registros: {total_registros}")

            # Acumular todas las boletas
            todas_boletas: List[Dict[str, Any]] = primera_pagina.get("boletas", [])

            # Obtener páginas restantes si hay más de 1 página
            if total_paginas > 1:
                for pagina in range(2, total_paginas + 1):
                    logger.info(f"  📄 Obteniendo página {pagina}/{total_paginas}...")

                    try:
                        pagina_data = self.get_boletas_honorarios(
                            mes=mes,
                            anio=anio,
                            pagina=pagina,
                            max_retries=max_retries
                        )

                        boletas_pagina = pagina_data.get("boletas", [])
                        todas_boletas.extend(boletas_pagina)

                        logger.info(f"    ✅ {len(boletas_pagina)} boletas de página {pagina}")

                        # Pequeño delay entre páginas para no sobrecargar el servidor
                        time.sleep(0.5)

                    except Exception as e:
                        logger.error(f"❌ Error obteniendo página {pagina}: {e}")
                        # Continuar con las demás páginas
                        continue

            logger.info(f"✅ Total de boletas obtenidas: {len(todas_boletas)}")

            return {
                "boletas": todas_boletas,
                "totales": {
                    "total_registros": len(todas_boletas),
                    "total_paginas": total_paginas
                }
            }

        except Exception as e:
            logger.error(f"❌ Error obteniendo todas las páginas de boletas de honorarios: {e}", exc_info=True)
            raise ExtractionError(f"Error obteniendo boletas de honorarios: {str(e)}") from e
