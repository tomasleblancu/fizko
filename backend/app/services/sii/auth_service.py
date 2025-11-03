"""
Servicio de autenticación SII
Maneja el proceso completo de login y setup inicial de empresas
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Company, CompanyTaxInfo, CompanySettings, Profile, Session as SessionModel
from app.integrations.sii import SIIClient
from app.integrations.sii.exceptions import AuthenticationError, ExtractionError

logger = logging.getLogger(__name__)


class SIIAuthService:
    """
    Servicio que maneja la autenticación SII y setup inicial de empresas.

    Responsabilidades:
    1. Crear perfil de usuario si no existe
    2. Autenticar con el SII (Selenium)
    3. Extraer información del contribuyente
    4. Crear/actualizar Company
    5. Crear/actualizar CompanyTaxInfo
    6. Crear/actualizar Session con cookies
    7. Disparar tareas de sincronización en background

    Este servicio separa la lógica de negocio del router HTTP.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio de autenticación

        Args:
            db: Sesión async de base de datos
        """
        self.db = db

    async def login_and_setup(
        self,
        rut: str,
        password: str,
        user_id: UUID,
        user_data: dict
    ) -> Dict[str, Any]:
        """
        Proceso completo de login SII y setup de empresa

        Args:
            rut: RUT del contribuyente (ej: "77794858-k")
            password: Contraseña del SII
            user_id: UUID del usuario autenticado
            user_data: Datos completos del usuario desde JWT (email, metadata, etc.)

        Returns:
            Dict con estructura:
            {
                "success": bool,
                "message": str,
                "company": dict,
                "company_tax_info": dict,
                "session": dict,
                "contribuyente_info": dict
            }

        Raises:
            AuthenticationError: Si las credenciales del SII son inválidas
            ExtractionError: Si hay error extrayendo datos del SII
            Exception: Errores de base de datos u otros
        """

        # PASO 1: Crear perfil de usuario si no existe
        profile = await self._ensure_profile(user_id, user_data)
        logger.info(f"[SII Auth Service] Profile ensured for user {user_id}")

        # PASO 2: Autenticar con SII y extraer datos
        sii_data = await self._authenticate_sii(rut, password)
        logger.info(f"[SII Auth Service] SII authentication successful for {rut}")

        # PASO 3: Setup de Company
        company, company_action = await self._setup_company(rut, password, sii_data)
        logger.info(f"[SII Auth Service] Company {company_action}: {company.business_name}")

        # PASO 4: Setup de CompanyTaxInfo
        company_tax_info, tax_action = await self._setup_tax_info(company.id, sii_data)
        logger.info(f"[SII Auth Service] CompanyTaxInfo {tax_action}")

        # PASO 5: Setup de Session con cookies
        session, session_action = await self._setup_session(
            user_id,
            company.id,
            password,
            sii_data['cookies']
        )
        logger.info(f"[SII Auth Service] Session {session_action}")

        # PASO 6: Activar eventos tributarios obligatorios
        activated_events = await self._activate_mandatory_events(company.id)
        logger.info(
            f"[SII Auth Service] Activated {len(activated_events)} mandatory events "
            f"for company {company.id}"
        )

        # PASO 6.5: Asignar notificaciones con auto-asignación activada
        is_new_company = company_action == "creada"
        assigned_notifications = await self._assign_auto_notifications(company.id, is_new_company)
        logger.info(
            f"[SII Auth Service] Assigned {len(assigned_notifications)} auto-assign notifications "
            f"for company {company.id} (is_new={is_new_company})"
        )

        # PASO 7: Commit de todos los cambios (incluye eventos y notificaciones)
        await self.db.commit()

        # Refresh para obtener datos actualizados
        await self.db.refresh(company)
        await self.db.refresh(company_tax_info)
        await self.db.refresh(session)

        # PASO 8: Disparar tareas de sincronización en background (solo para empresas nuevas)
        is_new_company = company_action == "creada"
        if is_new_company:
            await self._trigger_sync_tasks(company.id)
            logger.info(f"[SII Auth Service] Sync tasks triggered for new company {company.id}")
        else:
            logger.info(f"[SII Auth Service] Skipping sync tasks for existing company {company.id}")

        # PASO 9: Verificar si necesita configuración inicial
        needs_initial_setup = await self._check_needs_initial_setup(company.id)
        logger.info(f"[SII Auth Service] needs_initial_setup={needs_initial_setup} for company {company.id}")

        # PASO 10: Construir y retornar respuesta
        return self._build_response(
            company=company,
            company_tax_info=company_tax_info,
            session=session,
            contribuyente_info=sii_data['contribuyente_info'],
            actions={
                'company': company_action,
                'tax_info': tax_action,
                'session': session_action
            },
            needs_initial_setup=needs_initial_setup
        )

    async def _ensure_profile(self, user_id: UUID, user_data: dict) -> Profile:
        """
        Crea perfil de usuario si no existe

        Args:
            user_id: UUID del usuario
            user_data: Datos del usuario desde JWT (email, user_metadata, etc.)

        Returns:
            Profile: Perfil del usuario (existente o nuevo)
        """
        # Buscar perfil existente
        stmt = select(Profile).where(Profile.id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()

        if profile:
            return profile

        # Extraer datos del JWT
        email = user_data.get("email", "")
        user_metadata = user_data.get("user_metadata", {})
        full_name = user_metadata.get("full_name", "")

        # Split full_name en name y lastname
        if full_name:
            parts = full_name.split(" ", 1)
            name = parts[0]
            lastname = parts[1] if len(parts) > 1 else ""
        else:
            name = ""
            lastname = ""

        # Extraer otros campos de OAuth metadata
        phone = user_metadata.get("phone")
        avatar_url = user_metadata.get("avatar_url") or user_metadata.get("picture")

        # Crear nuevo perfil
        profile = Profile(
            id=user_id,
            email=email,
            full_name=full_name,
            name=name,
            lastname=lastname,
            phone=phone,
            avatar_url=avatar_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(profile)
        await self.db.flush()

        logger.info(f"[SII Auth Service] Created new profile for user {user_id}")
        return profile

    async def _authenticate_sii(self, rut: str, password: str) -> Dict[str, Any]:
        """
        Autentica con el SII y extrae información del contribuyente

        Args:
            rut: RUT del contribuyente
            password: Contraseña del SII

        Returns:
            Dict con:
            {
                "contribuyente_info": dict,  # Datos del contribuyente
                "cookies": list              # Cookies de sesión SII
            }

        Raises:
            AuthenticationError: Si falla la autenticación
            ExtractionError: Si falla la extracción de datos
        """
        # Usar context manager para manejar recursos de Selenium
        with SIIClient(
            tax_id=rut,
            password=password,
            headless=True
        ) as sii_client:

            # Intentar login
            login_success = sii_client.login()

            if not login_success:
                raise AuthenticationError(
                    "Error en la autenticación. Credenciales incorrectas o SII no disponible."
                )

            # Extraer información del contribuyente
            contribuyente_info = sii_client.get_contribuyente()

            # Obtener cookies para guardar en session
            sii_cookies = sii_client.get_cookies()

            return {
                "contribuyente_info": contribuyente_info,
                "cookies": sii_cookies
            }

    async def _setup_company(
        self,
        rut: str,
        password: str,
        sii_data: Dict[str, Any]
    ) -> tuple[Company, str]:
        """
        Busca o crea Company en la base de datos

        Args:
            rut: RUT del contribuyente
            password: Contraseña del SII (será encriptada)
            sii_data: Datos extraídos del SII

        Returns:
            Tuple[Company, str]: (Company, action) donde action es "creada" o "actualizada"
        """
        contribuyente_info = sii_data['contribuyente_info']

        # Normalizar RUT para búsqueda (minúsculas, sin puntos ni guiones)
        rut_normalized = rut.replace(".", "").replace("-", "").lower()

        # Buscar compañía existente
        stmt = select(Company).where(Company.rut == rut_normalized)
        result = await self.db.execute(stmt)
        company = result.scalar_one_or_none()

        if not company:
            # Crear nueva compañía
            company = Company(
                rut=rut_normalized,
                business_name=contribuyente_info.get('razon_social', f'Empresa {rut_normalized}'),
                trade_name=contribuyente_info.get('nombre', None),
                address=contribuyente_info.get('unidad_operativa_direccion', None),
                email=contribuyente_info.get('email', None),
            )
            company.sii_password = password  # Será encriptado automáticamente
            self.db.add(company)
            await self.db.flush()
            await self.db.refresh(company)

            return company, "creada"
        else:
            # Actualizar información de compañía existente
            company.business_name = contribuyente_info.get('razon_social', company.business_name)
            company.trade_name = contribuyente_info.get('nombre', company.trade_name)
            company.address = contribuyente_info.get('unidad_operativa_direccion', company.address)
            company.email = contribuyente_info.get('email', company.email)
            company.sii_password = password  # Actualizar password
            company.updated_at = datetime.utcnow()

            return company, "actualizada"

    async def _setup_tax_info(
        self,
        company_id: UUID,
        sii_data: Dict[str, Any]
    ) -> tuple[CompanyTaxInfo, str]:
        """
        Busca o crea CompanyTaxInfo en la base de datos

        Args:
            company_id: UUID de la compañía
            sii_data: Datos extraídos del SII

        Returns:
            Tuple[CompanyTaxInfo, str]: (CompanyTaxInfo, action) donde action es "creada" o "actualizada"
        """
        contribuyente_info = sii_data['contribuyente_info']

        # Extraer la primera actividad económica (actividad principal)
        actividades = contribuyente_info.get('actividades', [])
        actividad_principal = actividades[0] if actividades else {}

        # Buscar tax info existente
        stmt = select(CompanyTaxInfo).where(CompanyTaxInfo.company_id == company_id)
        result = await self.db.execute(stmt)
        company_tax_info = result.scalar_one_or_none()

        if not company_tax_info:
            # Crear nuevo CompanyTaxInfo
            company_tax_info = CompanyTaxInfo(
                company_id=company_id,
                tax_regime='regimen_general',  # Default
                sii_activity_code=actividad_principal.get('codigo', None),
                sii_activity_name=actividad_principal.get('descripcion', None),
                legal_representative_name=None,  # El SII no provee representante legal
                extra_data={
                    'sii_info': contribuyente_info,
                    'last_sii_sync': datetime.utcnow().isoformat()
                }
            )
            self.db.add(company_tax_info)
            await self.db.flush()
            await self.db.refresh(company_tax_info)

            return company_tax_info, "creada"
        else:
            # Actualizar CompanyTaxInfo existente
            company_tax_info.sii_activity_code = actividad_principal.get(
                'codigo',
                company_tax_info.sii_activity_code
            )
            company_tax_info.sii_activity_name = actividad_principal.get(
                'descripcion',
                company_tax_info.sii_activity_name
            )

            # Actualizar extra_data con nueva info del SII
            extra_data = company_tax_info.extra_data or {}
            extra_data['sii_info'] = contribuyente_info
            extra_data['last_sii_sync'] = datetime.utcnow().isoformat()
            company_tax_info.extra_data = extra_data
            company_tax_info.updated_at = datetime.utcnow()

            return company_tax_info, "actualizada"

    async def _setup_session(
        self,
        user_id: UUID,
        company_id: UUID,
        password: str,
        sii_cookies: list
    ) -> tuple[SessionModel, str]:
        """
        Busca o crea Session del usuario con esta compañía

        Args:
            user_id: UUID del usuario
            company_id: UUID de la compañía
            password: Contraseña del SII
            sii_cookies: Cookies de sesión del SII

        Returns:
            Tuple[SessionModel, str]: (Session, action) donde action es "creada" o "actualizada"
        """
        # Buscar sesión existente del usuario con esta compañía
        stmt = select(SessionModel).where(
            SessionModel.user_id == user_id,
            SessionModel.company_id == company_id
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            # Crear nueva sesión
            session = SessionModel(
                user_id=user_id,
                company_id=company_id,
                is_active=True,
                cookies={
                    'sii_cookies': sii_cookies,
                    'password': password,
                    'last_updated': datetime.utcnow().isoformat()
                },
                resources={},
                last_accessed_at=datetime.utcnow()
            )
            self.db.add(session)
            await self.db.flush()
            await self.db.refresh(session)

            return session, "creada"
        else:
            # Actualizar cookies de sesión existente
            session.cookies = {
                'sii_cookies': sii_cookies,
                'password': password,
                'last_updated': datetime.utcnow().isoformat()
            }
            session.last_accessed_at = datetime.utcnow()
            session.is_active = True

            return session, "actualizada"

    async def _activate_mandatory_events(self, company_id: UUID) -> list[str]:
        """
        Activa todos los eventos tributarios obligatorios para una empresa

        Args:
            company_id: UUID de la compañía

        Returns:
            Lista de códigos de eventos activados
        """
        from app.db.models import EventTemplate
        from app.services.calendar import EventConfigService

        # Obtener todos los event templates obligatorios
        stmt = select(EventTemplate).where(EventTemplate.is_mandatory == True)
        result = await self.db.execute(stmt)
        mandatory_templates = result.scalars().all()

        if not mandatory_templates:
            logger.warning("[SII Auth Service] No mandatory event templates found in database")
            return []

        # Activar cada evento obligatorio
        event_config_service = EventConfigService(self.db)
        activated_events = []

        for template in mandatory_templates:
            try:
                await event_config_service.activate_event(
                    company_id=company_id,
                    event_template_id=template.id,
                    custom_config=None  # Usar configuración por defecto
                )
                activated_events.append(template.code)
                logger.info(
                    f"[SII Auth Service] Activated mandatory event: {template.code} "
                    f"for company {company_id}"
                )
            except Exception as e:
                logger.error(
                    f"[SII Auth Service] Error activating event {template.code}: {e}",
                    exc_info=True
                )

        return activated_events

    async def _assign_auto_notifications(self, company_id: UUID, is_new_company: bool) -> list[str]:
        """
        Asigna notificaciones con auto_assign_to_new_companies=True a la empresa

        Args:
            company_id: UUID de la compañía
            is_new_company: Si es una empresa recién creada (True) o existente (False)

        Returns:
            Lista de códigos de notificaciones asignadas
        """
        from app.db.models.notifications import NotificationTemplate, NotificationSubscription

        # Solo asignar si es una empresa nueva
        if not is_new_company:
            logger.info(
                f"[SII Auth Service] Skipping auto-assign notifications for existing company {company_id}"
            )
            return []

        # Obtener todos los notification templates con auto-asignación activada
        stmt = select(NotificationTemplate).where(
            NotificationTemplate.auto_assign_to_new_companies == True,
            NotificationTemplate.is_active == True
        )
        result = await self.db.execute(stmt)
        auto_assign_templates = result.scalars().all()

        if not auto_assign_templates:
            logger.info("[SII Auth Service] No auto-assign notification templates found")
            return []

        # Asignar cada notificación
        assigned_notifications = []

        for template in auto_assign_templates:
            try:
                # Verificar si ya existe una suscripción
                check_stmt = select(NotificationSubscription).where(
                    NotificationSubscription.company_id == company_id,
                    NotificationSubscription.notification_template_id == template.id
                )
                check_result = await self.db.execute(check_stmt)
                existing = check_result.scalar_one_or_none()

                if existing:
                    logger.debug(
                        f"[SII Auth Service] Subscription already exists for template {template.code}"
                    )
                    continue

                # Crear nueva suscripción
                subscription = NotificationSubscription(
                    company_id=company_id,
                    notification_template_id=template.id,
                    is_enabled=True,
                    channels=["whatsapp"],
                    custom_timing_config=None,  # Usar configuración del template
                    custom_message_template=None  # Usar mensaje del template
                )
                self.db.add(subscription)
                assigned_notifications.append(template.code)

                logger.info(
                    f"[SII Auth Service] Auto-assigned notification: {template.code} "
                    f"to company {company_id}"
                )
            except Exception as e:
                logger.error(
                    f"[SII Auth Service] Error auto-assigning notification {template.code}: {e}",
                    exc_info=True
                )

        return assigned_notifications

    async def _trigger_sync_tasks(self, company_id: UUID) -> None:
        """
        Dispara tareas de Celery en background para sincronización

        Args:
            company_id: UUID de la compañía
        """
        # Importar tareas de Celery
        from app.infrastructure.celery.tasks.sii.documents import sync_documents
        from app.infrastructure.celery.tasks.sii.forms import sync_f29
        from app.infrastructure.celery.tasks.calendar import sync_company_calendar

        # 1. Disparar sincronización de calendario (eventos tributarios)
        try:
            sync_company_calendar.delay(company_id=str(company_id))
            logger.info(
                f"[SII Auth Service] sync_company_calendar task triggered "
                f"for company {company_id}"
            )
        except Exception as e:
            logger.error(
                f"[SII Auth Service] Error triggering sync_company_calendar: {e}"
            )

        # 2. Disparar sincronización de documentos tributarios (últimos 3 meses)
        try:
            sync_documents.delay(
                company_id=str(company_id),
                months=3
            )
            logger.info(
                f"[SII Auth Service] sync_documents task triggered "
                f"for company {company_id}"
            )
        except Exception as e:
            logger.error(f"[SII Auth Service] Error triggering sync_documents: {e}")

        # 3. Disparar sincronización de formularios F29 (año actual)
        try:
            current_year = datetime.utcnow().year
            sync_f29.delay(
                company_id=str(company_id),
                year=current_year
            )
            logger.info(
                f"[SII Auth Service] sync_f29 task triggered for company {company_id}, "
                f"year {current_year}"
            )
        except Exception as e:
            logger.error(f"[SII Auth Service] Error triggering sync_f29: {e}")

    async def _check_needs_initial_setup(self, company_id: UUID) -> bool:
        """
        Verifica si la empresa necesita completar la configuración inicial.

        Args:
            company_id: UUID de la empresa

        Returns:
            bool: True si necesita setup inicial, False si ya está configurada
        """
        # Buscar settings de la empresa
        stmt = select(CompanySettings).where(CompanySettings.company_id == company_id)
        result = await self.db.execute(stmt)
        settings = result.scalar_one_or_none()

        # Si no existe settings o no está completo el setup inicial
        if not settings or not settings.is_initial_setup_complete:
            return True

        return False

    def _build_response(
        self,
        company: Company,
        company_tax_info: CompanyTaxInfo,
        session: SessionModel,
        contribuyente_info: dict,
        actions: dict,
        needs_initial_setup: bool = False
    ) -> Dict[str, Any]:
        """
        Construye la respuesta del endpoint

        Args:
            company: Company creada/actualizada
            company_tax_info: CompanyTaxInfo creada/actualizada
            session: Session creada/actualizada
            contribuyente_info: Información del contribuyente desde SII
            actions: Dict con las acciones realizadas
            needs_initial_setup: Flag que indica si necesita configuración inicial

        Returns:
            Dict con la estructura de respuesta completa
        """
        return {
            "success": True,
            "message": (
                f"Login exitoso. Compañía {actions['company']}, "
                f"tax info {actions['tax_info']}, "
                f"sesión {actions['session']}."
            ),
            "company": {
                "id": str(company.id),
                "rut": company.rut,
                "business_name": company.business_name,
                "trade_name": company.trade_name,
                "address": company.address,
                "email": company.email,
                "created_at": company.created_at.isoformat(),
                "updated_at": company.updated_at.isoformat()
            },
            "company_tax_info": {
                "id": str(company_tax_info.id),
                "company_id": str(company_tax_info.company_id),
                "tax_regime": company_tax_info.tax_regime,
                "sii_activity_code": company_tax_info.sii_activity_code,
                "sii_activity_name": company_tax_info.sii_activity_name,
                "legal_representative_name": company_tax_info.legal_representative_name,
                "created_at": company_tax_info.created_at.isoformat(),
                "updated_at": company_tax_info.updated_at.isoformat()
            },
            "session": {
                "id": str(session.id),
                "user_id": str(session.user_id),
                "company_id": str(session.company_id),
                "is_active": session.is_active,
                "has_cookies": bool(session.cookies and session.cookies.get('sii_cookies')),
                "last_accessed_at": session.last_accessed_at.isoformat() if session.last_accessed_at else None
            },
            "contribuyente_info": contribuyente_info,
            "needs_initial_setup": needs_initial_setup
        }
