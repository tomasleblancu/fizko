"""
Document Service - Manejo de documentos tributarios (DTEs, compras, ventas, resumen)
"""
import logging
import asyncio
from typing import Dict, Any, Union
from uuid import UUID

from app.integrations.sii import SIIClient
from app.integrations.sii.exceptions import (
    AuthenticationError,
    ExtractionError
)

from .base_service import BaseSIIService

logger = logging.getLogger(__name__)


class DocumentService(BaseSIIService):
    """
    Servicio para manejo de documentos tributarios del SII

    Responsabilidades:
    - Extracción de información del contribuyente
    - Extracción de DTEs de compra
    - Extracción de DTEs de venta
    - Extracción de resúmenes de período
    """

    # =============================================================================
    # INFORMACIÓN DEL CONTRIBUYENTE
    # =============================================================================

    async def extract_contribuyente(
        self,
        session_id: Union[str, UUID],
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae información del contribuyente usando el módulo SII

        Args:
            session_id: ID de la sesión en la DB
            force_new_login: Si True, ignora cookies y hace login fresco

        Returns:
            Información del contribuyente

        Raises:
            AuthenticationError: Si falla la autenticación
            ExtractionError: Si falla la extracción
        """
        # 1. Obtener credenciales desde DB
        creds = await self.get_stored_credentials(session_id)
        if not creds:
            raise ValueError(f"Session {session_id} not found")

        # 2. Usar cookies almacenadas si existen (a menos que se fuerce nuevo login)
        cookies = None if force_new_login else creds.get("cookies")

        # 3. Usar el módulo SII (completamente agnostic de DB)
        # Función sincrónica que ejecuta Selenium
        def _run_extraction():
            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=cookies,
                headless=True
            ) as client:

                # Login solo si no hay cookies válidas
                if not cookies:
                    logger.info(f"🔐 No cookies found, performing login for {creds['rut']}")
                    client.login()
                    new_cookies = client.get_cookies()
                else:
                    logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")
                    new_cookies = None

                # Extraer datos
                info = client.get_contribuyente()

                # Actualizar cookies por si cambiaron
                updated_cookies = client.get_cookies()

                return info, new_cookies, updated_cookies

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            info, new_cookies, updated_cookies = await asyncio.to_thread(_run_extraction)

            # Ahora SÍ podemos hacer operaciones async de DB
            if new_cookies:
                await self.save_cookies(session_id, new_cookies)

            if updated_cookies:
                await self.save_cookies(session_id, updated_cookies)

            return info

        except AuthenticationError as e:
            logger.error(f"❌ Authentication failed for session {session_id}: {e}")

            # Si falló con cookies, reintentar con login fresco
            if cookies and not force_new_login:
                logger.info("🔄 Retrying with fresh login...")
                return await self.extract_contribuyente(session_id, force_new_login=True)

            raise

    # =============================================================================
    # COMPRAS
    # =============================================================================

    async def extract_compras(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        tipo_doc: str = "33",
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae DTEs de compra

        Args:
            session_id: ID de la sesión en la DB
            periodo: Período en formato YYYYMM (ej: "202510")
            tipo_doc: Tipo de documento (default: "33" = Factura Electrónica)
            force_new_login: Si True, ignora cookies y hace login fresco

        Returns:
            Dict con status, data, extraction_method
        """
        # Función sincrónica que ejecuta TODO en sync (Selenium + DB)
        def _run_extraction():
            # Obtener credenciales de forma síncrona
            creds = self._get_stored_credentials_sync(session_id)
            if not creds:
                raise ValueError(f"Session {session_id} not found")

            # Usar cookies solo si no forzamos nuevo login
            cookies = None if force_new_login else creds.get("cookies")

            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=cookies,
                headless=True
            ) as client:

                # Login si no hay cookies o si se fuerza
                if not cookies:
                    logger.info(f"🔐 Performing login for {creds['rut']}")
                    client.login()
                    new_cookies = client.get_cookies()
                    # Guardar cookies de forma síncrona
                    self._save_cookies_sync(session_id, new_cookies)
                else:
                    logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")

                # Extraer compras (operación sincrónica de Selenium)
                result = client.get_compras(periodo=periodo, tipo_doc=tipo_doc)

                # Actualizar cookies de forma síncrona
                updated_cookies = client.get_cookies()
                self._save_cookies_sync(session_id, updated_cookies)

                return result

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            result = await asyncio.to_thread(_run_extraction)
            return result

        except (AuthenticationError, ExtractionError) as e:
            # Si falló con cookies almacenadas, reintentar con login fresco
            if not force_new_login and "401" in str(e):
                logger.warning(f"⚠️ Cookies expired (401), retrying with fresh login...")
                return await self.extract_compras(session_id, periodo, tipo_doc, force_new_login=True)
            raise

    # =============================================================================
    # VENTAS
    # =============================================================================

    async def extract_ventas(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        tipo_doc: str = "33",
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae DTEs de venta

        Args:
            session_id: ID de la sesión en la DB
            periodo: Período en formato YYYYMM
            tipo_doc: Tipo de documento
            force_new_login: Si True, ignora cookies y hace login fresco

        Returns:
            Dict con status, data, extraction_method
        """
        # Función sincrónica que ejecuta TODO en sync (Selenium + DB)
        def _run_extraction():
            # Obtener credenciales de forma síncrona
            creds = self._get_stored_credentials_sync(session_id)
            if not creds:
                raise ValueError(f"Session {session_id} not found")

            # Usar cookies solo si no forzamos nuevo login
            cookies = None if force_new_login else creds.get("cookies")

            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=cookies,
                headless=True
            ) as client:

                # Login si no hay cookies o si se fuerza
                if not cookies:
                    logger.info(f"🔐 Performing login for {creds['rut']}")
                    client.login()
                    new_cookies = client.get_cookies()
                    # Guardar cookies de forma síncrona
                    self._save_cookies_sync(session_id, new_cookies)
                else:
                    logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")

                # Extraer ventas (operación sincrónica de Selenium)
                result = client.get_ventas(periodo=periodo, tipo_doc=tipo_doc)

                # Actualizar cookies de forma síncrona
                updated_cookies = client.get_cookies()
                self._save_cookies_sync(session_id, updated_cookies)

                return result

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            result = await asyncio.to_thread(_run_extraction)
            return result

        except (AuthenticationError, ExtractionError) as e:
            # Si falló con cookies almacenadas, reintentar con login fresco
            if not force_new_login and "401" in str(e):
                logger.warning(f"⚠️ Cookies expired (401), retrying with fresh login...")
                return await self.extract_ventas(session_id, periodo, tipo_doc, force_new_login=True)
            raise

    # =============================================================================
    # RESUMEN
    # =============================================================================

    async def extract_resumen(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae resumen de compras y ventas del período

        Args:
            session_id: ID de la sesión en la DB
            periodo: Período en formato YYYYMM (ej: "202510")
            force_new_login: Si True, ignora cookies y hace login fresco

        Returns:
            Dict con resumen_compras y resumen_ventas por tipo de documento
        """
        # Función sincrónica que ejecuta TODO en sync (Selenium + DB)
        def _run_extraction():
            # Obtener credenciales de forma síncrona
            creds = self._get_stored_credentials_sync(session_id)
            if not creds:
                raise ValueError(f"Session {session_id} not found")

            # Usar cookies solo si no forzamos nuevo login
            cookies = None if force_new_login else creds.get("cookies")

            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=cookies,
                headless=True
            ) as client:

                # Login si no hay cookies o si se fuerza
                if not cookies:
                    logger.info(f"🔐 Performing login for {creds['rut']}")
                    client.login()
                    new_cookies = client.get_cookies()
                    # Guardar cookies de forma síncrona
                    self._save_cookies_sync(session_id, new_cookies)
                else:
                    logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")

                # Extraer resumen (operación sincrónica)
                result = client.get_resumen(periodo=periodo)

                # Actualizar cookies de forma síncrona
                updated_cookies = client.get_cookies()
                self._save_cookies_sync(session_id, updated_cookies)

                return result

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            result = await asyncio.to_thread(_run_extraction)
            return result

        except (AuthenticationError, ExtractionError) as e:
            # Si falló con cookies almacenadas, reintentar con login fresco
            if not force_new_login and "401" in str(e):
                logger.warning(f"⚠️ Cookies expired (401), retrying with fresh login...")
                return await self.extract_resumen(session_id, periodo, force_new_login=True)
            raise

    # =============================================================================
    # BOLETAS Y COMPROBANTES DIARIOS
    # =============================================================================

    async def extract_boletas_diarias(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        tipo_doc: str,
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae boletas o comprobantes diarios del período

        Args:
            session_id: ID de la sesión en la DB
            periodo: Período en formato YYYYMM (ej: "202509")
            tipo_doc: Tipo de documento ("39" = boletas, "48" = comprobantes)
            force_new_login: Si True, ignora cookies y hace login fresco

        Returns:
            Dict con totales diarios del período
        """
        # Función sincrónica que ejecuta TODO en sync (Selenium + DB)
        def _run_extraction():
            # Obtener credenciales de forma síncrona
            creds = self._get_stored_credentials_sync(session_id)
            if not creds:
                raise ValueError(f"Session {session_id} not found")

            # Usar cookies solo si no forzamos nuevo login
            cookies = None if force_new_login else creds.get("cookies")

            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=cookies,
                headless=True
            ) as client:

                # Login si no hay cookies o si se fuerza
                if not cookies:
                    logger.info(f"🔐 Performing login for {creds['rut']}")
                    client.login()
                    new_cookies = client.get_cookies()
                    # Guardar cookies de forma síncrona
                    self._save_cookies_sync(session_id, new_cookies)
                else:
                    logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")

                # Extraer boletas diarias (operación sincrónica)
                result = client.get_boletas_diarias(periodo=periodo, tipo_doc=tipo_doc)

                # Actualizar cookies de forma síncrona
                updated_cookies = client.get_cookies()
                self._save_cookies_sync(session_id, updated_cookies)

                return result

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            result = await asyncio.to_thread(_run_extraction)
            return result

        except (AuthenticationError, ExtractionError) as e:
            # Si falló con cookies almacenadas, reintentar con login fresco
            if not force_new_login and "401" in str(e):
                logger.warning(f"⚠️ Cookies expired (401), retrying with fresh login...")
                return await self.extract_boletas_diarias(session_id, periodo, tipo_doc, force_new_login=True)
            raise

    # =============================================================================
    # BOLETAS DE HONORARIOS
    # =============================================================================

    async def extract_boletas_honorarios(
        self,
        session_id: Union[str, UUID],
        mes: str,
        anio: str,
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae boletas de honorarios del período

        Args:
            session_id: ID de la sesión en la DB
            mes: Mes (1-12)
            anio: Año (YYYY)
            force_new_login: Si True, ignora cookies y hace login fresco

        Returns:
            Dict con boletas y totales:
            {
                "data": {
                    "boletas": [...],
                    "totales": {...}
                }
            }
        """
        # Función sincrónica que ejecuta TODO en sync (Selenium + DB)
        def _run_extraction():
            # Obtener credenciales de forma síncrona
            creds = self._get_stored_credentials_sync(session_id)
            if not creds:
                raise ValueError(f"Session {session_id} not found")

            # Usar cookies solo si no forzamos nuevo login
            cookies = None if force_new_login else creds.get("cookies")

            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=cookies,
                headless=True
            ) as client:

                # Login si no hay cookies o si se fuerza
                if not cookies:
                    logger.info(f"🔐 Performing login for {creds['rut']}")
                    client.login()
                    new_cookies = client.get_cookies()
                    # Guardar cookies de forma síncrona
                    self._save_cookies_sync(session_id, new_cookies)
                else:
                    logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")

                # Extraer boletas de honorarios (operación sincrónica)
                result = client.get_boletas_honorarios(mes=mes, anio=anio)

                # Actualizar cookies de forma síncrona
                updated_cookies = client.get_cookies()
                self._save_cookies_sync(session_id, updated_cookies)

                return result

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            result = await asyncio.to_thread(_run_extraction)

            # Formatear resultado para match con parser
            return {
                "data": result
            }

        except (AuthenticationError, ExtractionError) as e:
            # Si falló con cookies almacenadas, reintentar con login fresco
            if not force_new_login and "401" in str(e):
                logger.warning(f"⚠️ Cookies expired (401), retrying with fresh login...")
                return await self.extract_boletas_honorarios(session_id, mes, anio, force_new_login=True)
            raise
