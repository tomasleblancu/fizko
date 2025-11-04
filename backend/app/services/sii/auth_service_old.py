"""
Servicio de autenticación SII
Maneja el proceso completo de login y setup inicial de empresas
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models import Company, CompanyTaxInfo, CompanySettings, Profile, Session as SessionModel
from app.integrations.sii import SIIClient
from app.integrations.sii.exceptions import AuthenticationError, ExtractionError
from app.agents.tools.memory.memory_tools import get_mem0_client

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
    7. Guardar información en memoria (Mem0) para agentes AI
    8. Disparar tareas de sincronización en background

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

        # PASO 7.5: Guardar información en memoria (Mem0) para uso de agentes AI
        await self._save_onboarding_memories(
            user_id=user_id,
            company=company,
            company_tax_info=company_tax_info,
            contribuyente_info=sii_data['contribuyente_info'],
            is_new_company=is_new_company,
            profile=profile
        )
        logger.info(f"[SII Auth Service] Onboarding memories saved for user {user_id}, company {company.id}")

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

    async def _save_onboarding_memories(
        self,
        user_id: UUID,
        company: Company,
        company_tax_info: CompanyTaxInfo,
        contribuyente_info: dict,
        is_new_company: bool,
        profile: Profile
    ) -> None:
        """
        Guarda información relevante en memoria (Mem0) durante el onboarding.

        Usa modelos UserBrain y CompanyBrain para rastrear memorias y hacer
        UPDATE en lugar de CREATE cuando ya existe una memoria con el mismo slug.

        Guarda información en dos espacios de memoria:
        1. Memoria de Empresa (company memory) - Información compartida
        2. Memoria de Usuario (user memory) - Información personal

        Args:
            user_id: UUID del usuario
            company: Company creada/actualizada
            company_tax_info: CompanyTaxInfo con datos tributarios
            contribuyente_info: Información del contribuyente desde SII
            is_new_company: True si la empresa fue creada, False si fue actualizada
            profile: Profile del usuario

        Note:
            Si falla el guardado de memoria, solo se logea el error sin interrumpir
            el flujo de onboarding.
        """
        try:
            from ...repositories import CompanyBrainRepository, UserBrainRepository

            mem0 = get_mem0_client()
            company_brain_repo = CompanyBrainRepository(self.db)
            user_brain_repo = UserBrainRepository(self.db)

            logger.info(
                f"[SII Auth Service] 🧠 Starting memory save for user {user_id}, "
                f"company {company.id}"
            )

            company_entity_id = f"company_{company.id}"
            business_name = company.business_name or "Empresa"

            # ===================================================================
            # MEMORIA DE EMPRESA (Company Memory) - Con UPDATE/CREATE y categorías
            # ===================================================================
            company_memories_to_save = []

            # 1. Información básica de la empresa
            trade_name = company.trade_name
            if trade_name and trade_name != business_name:
                company_memories_to_save.append({
                    "slug": "company_basic_info",
                    "category": "company_info",
                    "content": f"La empresa {business_name} (nombre de fantasía: {trade_name}) está registrada en el SII con RUT {company.rut}"
                })
            else:
                company_memories_to_save.append({
                    "slug": "company_basic_info",
                    "category": "company_info",
                    "content": f"La empresa {business_name} está registrada en el SII con RUT {company.rut}"
                })

            # 2. Régimen tributario
            if company_tax_info.tax_regime:
                regime_names = {
                    'regimen_general': 'Régimen General',
                    'propyme_general': 'ProPyme General',
                    'propyme_transparente': 'ProPyme Transparente',
                    'semi_integrado': 'Semi Integrado',
                    '14ter': 'Régimen 14 TER'
                }
                regime_display = regime_names.get(
                    company_tax_info.tax_regime,
                    company_tax_info.tax_regime
                )
                company_memories_to_save.append({
                    "slug": "company_tax_regime",
                    "category": "company_tax",
                    "content": f"Régimen tributario de la empresa: {regime_display}"
                })

            # 3. Actividad económica principal
            if company_tax_info.sii_activity_code and company_tax_info.sii_activity_name:
                company_memories_to_save.append({
                    "slug": "company_activity",
                    "category": "company_tax",
                    "content": f"Actividad económica principal: {company_tax_info.sii_activity_code} - {company_tax_info.sii_activity_name}"
                })

            # 4. Inicio de actividades
            if company_tax_info.start_of_activities_date:
                start_date = company_tax_info.start_of_activities_date.strftime('%d/%m/%Y')
                company_memories_to_save.append({
                    "slug": "company_start_date",
                    "category": "company_tax",
                    "content": f"Fecha de inicio de actividades: {start_date}"
                })
            elif contribuyente_info.get('inicio_actividades'):
                company_memories_to_save.append({
                    "slug": "company_start_date",
                    "category": "company_tax",
                    "content": f"Inicio de actividades: {contribuyente_info['inicio_actividades']}"
                })

            # 5. Información de dirección
            if company.address:
                company_memories_to_save.append({
                    "slug": "company_address",
                    "category": "company_info",
                    "content": f"Dirección registrada: {company.address}"
                })

            # 6. Fecha de incorporación a Fizko
            if is_new_company:
                company_memories_to_save.append({
                    "slug": "company_fizko_join_date",
                    "category": "company_info",
                    "content": f"Empresa incorporada a Fizko el {datetime.utcnow().strftime('%d/%m/%Y')}"
                })

            # 7. Cumplimiento tributario (desde opc=118)
            cumplimiento = contribuyente_info.get('cumplimiento_tributario')
            if cumplimiento:
                estado = cumplimiento.get('estado', 'Desconocido')
                atributos = cumplimiento.get('atributos', [])

                # Estado general de cumplimiento
                company_memories_to_save.append({
                    "slug": "company_tax_compliance_status",
                    "category": "company_tax",
                    "content": f"Estado de cumplimiento tributario: {estado}"
                })

                # Detalle de requisitos incumplidos (si los hay)
                requisitos_incumplidos = [
                    attr for attr in atributos
                    if attr.get('cumple') == 'NO'
                ]

                if requisitos_incumplidos:
                    incumplimientos = []
                    for req in requisitos_incumplidos:
                        incumplimientos.append(
                            f"[{req.get('condicion')}] {req.get('titulo')}: {req.get('descripcion')}"
                        )

                    company_memories_to_save.append({
                        "slug": "company_tax_compliance_issues",
                        "category": "company_tax",
                        "content": f"Requisitos tributarios incumplidos: {'; '.join(incumplimientos)}"
                    })

            # 8. Observaciones y alertas del SII (desde opc=28)
            observaciones = contribuyente_info.get('observaciones')
            if observaciones and observaciones.get('tiene_observaciones'):
                obs_list = observaciones.get('observaciones', [])
                if obs_list:
                    alertas_desc = []
                    for obs in obs_list:
                        tipo = obs.get('tipo', 'OBSERVACION')
                        desc = obs.get('descripcion', '')
                        alertas_desc.append(f"[{tipo}] {desc}")

                    company_memories_to_save.append({
                        "slug": "company_sii_alerts",
                        "category": "company_tax",
                        "content": f"Alertas/Observaciones del SII: {'; '.join(alertas_desc)}"
                    })
            elif observaciones and not observaciones.get('tiene_observaciones'):
                # Registrar que NO hay observaciones (información positiva)
                company_memories_to_save.append({
                    "slug": "company_sii_alerts",
                    "category": "company_tax",
                    "content": "La empresa no tiene observaciones ni alertas vigentes del SII"
                })

            # 9. Representantes legales
            representantes = contribuyente_info.get('representantes', [])
            if representantes:
                rep_vigentes = [rep for rep in representantes if rep.get('vigente')]
                if rep_vigentes:
                    rep_names = []
                    for rep in rep_vigentes:
                        nombre = rep.get('nombre_completo', 'Sin nombre')
                        rut = rep.get('rut', 'Sin RUT')
                        rep_names.append(f"{nombre} (RUT: {rut})")

                    company_memories_to_save.append({
                        "slug": "company_legal_representatives",
                        "category": "company_info",
                        "content": f"Representantes legales vigentes: {', '.join(rep_names)}"
                    })

            # 10. Socios/Accionistas
            socios = contribuyente_info.get('socios', [])
            if socios:
                socios_vigentes = [socio for socio in socios if socio.get('vigente')]
                if socios_vigentes:
                    socios_info = []
                    for socio in socios_vigentes:
                        nombre = socio.get('nombre_completo', 'Sin nombre')
                        rut = socio.get('rut', 'Sin RUT')
                        participacion = socio.get('participacion_capital', 'N/A')
                        socios_info.append(f"{nombre} (RUT: {rut}, {participacion}% capital)")

                    company_memories_to_save.append({
                        "slug": "company_shareholders",
                        "category": "company_info",
                        "content": f"Composición societaria: {'; '.join(socios_info)}"
                    })

            # 11. Direcciones registradas
            direcciones = contribuyente_info.get('direcciones', [])
            if direcciones:
                for idx, dir in enumerate(direcciones):
                    tipo = dir.get('tipo', 'Dirección')
                    calle = dir.get('calle', '')
                    comuna = dir.get('comuna', '')
                    region = dir.get('region', '')

                    direccion_completa = f"{calle}, {comuna}, {region}".strip(', ')

                    if idx == 0:  # Primera dirección (principal)
                        company_memories_to_save.append({
                            "slug": "company_primary_address",
                            "category": "company_info",
                            "content": f"{tipo} principal: {direccion_completa}"
                        })
                    else:
                        company_memories_to_save.append({
                            "slug": f"company_secondary_address_{idx}",
                            "category": "company_info",
                            "content": f"{tipo} secundaria: {direccion_completa}"
                        })

            # 12. Documentos autorizados (Timbrajes)
            timbrajes = contribuyente_info.get('timbrajes', [])
            if timbrajes:
                docs_info = []
                for tim in timbrajes:
                    desc = tim.get('descripcion', 'Documento')
                    num_inicial = tim.get('numero_inicial', '')
                    num_final = tim.get('numero_final', '')
                    fecha_legal = tim.get('fecha_legalizacion', '')

                    docs_info.append(
                        f"{desc} (N° {num_inicial}-{num_final}, legalizado hasta {fecha_legal})"
                    )

                company_memories_to_save.append({
                    "slug": "company_authorized_documents",
                    "category": "company_tax",
                    "content": f"Documentos tributarios autorizados: {'; '.join(docs_info)}"
                })

            # Guardar/actualizar memorias de empresa
            for memory_data in company_memories_to_save:
                try:
                    slug = memory_data["slug"]
                    category = memory_data["category"]
                    content = memory_data["content"]

                    # Buscar si ya existe una memoria con este slug
                    existing_brain = await company_brain_repo.get_by_company_and_slug(
                        company_id=company.id,
                        slug=slug
                    )

                    if existing_brain:
                        # UPDATE en Mem0
                        logger.info(f"[SII Auth Service] 🔄 Updating company memory: {slug} (category: {category})")
                        import asyncio
                        await asyncio.to_thread(
                            mem0.update,
                            memory_id=existing_brain.memory_id,
                            text=content
                        )

                        # Actualizar en BD usando repositorio (incluir category en metadata)
                        await company_brain_repo.update(
                            id=existing_brain.id,
                            content=content,
                            extra_metadata={"category": category}
                        )
                        logger.info(f"[SII Auth Service] ✅ Updated company memory: {slug}")
                    else:
                        # CREATE en Mem0
                        logger.info(f"[SII Auth Service] ✨ Creating company memory: {slug} (category: {category})")
                        result = await mem0.add(
                            messages=[{"role": "user", "content": content}],
                            user_id=company_entity_id,
                            metadata={"slug": slug, "category": category}
                        )

                        # Obtener memory_id o event_id del resultado
                        # Mem0 puede retornar procesamiento asíncrono (status: PENDING) con event_id
                        memory_id = None
                        if isinstance(result, dict):
                            # Intentar diferentes estructuras de respuesta
                            if "results" in result and isinstance(result["results"], list) and len(result["results"]) > 0:
                                first_result = result["results"][0]
                                # Puede tener 'id' (memoria creada) o 'event_id' (procesamiento pendiente)
                                memory_id = first_result.get("id") or first_result.get("event_id")
                                status = first_result.get("status", "UNKNOWN")
                                logger.info(f"[SII Auth Service] Mem0 status: {status}, memory_id: {memory_id}")
                            elif "id" in result:
                                memory_id = result.get("id")
                            elif "event_id" in result:
                                memory_id = result.get("event_id")
                            elif "memory_id" in result:
                                memory_id = result.get("memory_id")

                        if not memory_id:
                            logger.error(f"[SII Auth Service] ❌ No memory_id/event_id returned from Mem0. Response: {result}")
                            continue

                        # Crear en BD usando repositorio
                        await company_brain_repo.create(
                            company_id=company.id,
                            memory_id=memory_id,
                            slug=slug,
                            content=content,
                            extra_metadata={"category": category}
                        )
                        logger.info(f"[SII Auth Service] ✅ Created company memory: {slug}")

                except Exception as e:
                    logger.error(
                        f"[SII Auth Service] ❌ Error with company memory {memory_data.get('slug')}: {e}",
                        exc_info=True
                    )

            # ===================================================================
            # MEMORIA DE USUARIO (User Memory) - Con UPDATE/CREATE y categorías
            # ===================================================================
            user_memories_to_save = []

            # 1. Vinculación con la empresa
            today = datetime.utcnow().strftime('%d/%m/%Y')
            user_memories_to_save.append({
                "slug": f"user_company_join_{company.id}",
                "category": "user_company_relationship",
                "content": f"Se vinculó con {business_name} el {today}"
            })

            # 2. Determinar rol del usuario
            stmt = select(func.count(SessionModel.id)).where(
                SessionModel.company_id == company.id,
                SessionModel.is_active == True
            )
            result = await self.db.execute(stmt)
            active_sessions_count = result.scalar()

            if active_sessions_count <= 1:
                user_memories_to_save.append({
                    "slug": f"user_role_{company.id}",
                    "category": "user_company_relationship",
                    "content": f"Rol en {business_name}: Propietario/Administrador"
                })
            else:
                user_memories_to_save.append({
                    "slug": f"user_role_{company.id}",
                    "category": "user_company_relationship",
                    "content": f"Rol en {business_name}: Miembro del equipo"
                })

            # 3. Información del perfil
            if profile:
                if profile.full_name:
                    user_memories_to_save.append({
                        "slug": "user_full_name",
                        "category": "user_profile",
                        "content": f"Nombre completo: {profile.full_name}"
                    })
                if profile.phone:
                    user_memories_to_save.append({
                        "slug": "user_phone",
                        "category": "user_profile",
                        "content": f"Teléfono de contacto: {profile.phone}"
                    })

            # Guardar/actualizar memorias de usuario
            for memory_data in user_memories_to_save:
                try:
                    slug = memory_data["slug"]
                    category = memory_data["category"]
                    content = memory_data["content"]

                    # Buscar si ya existe una memoria con este slug
                    existing_brain = await user_brain_repo.get_by_user_and_slug(
                        user_id=user_id,
                        slug=slug
                    )

                    if existing_brain:
                        # UPDATE en Mem0
                        logger.info(f"[SII Auth Service] 🔄 Updating user memory: {slug} (category: {category})")
                        import asyncio
                        await asyncio.to_thread(
                            mem0.update,
                            memory_id=existing_brain.memory_id,
                            text=content
                        )

                        # Actualizar en BD usando repositorio (incluir category en metadata)
                        await user_brain_repo.update(
                            id=existing_brain.id,
                            content=content,
                            extra_metadata={"category": category}
                        )
                        logger.info(f"[SII Auth Service] ✅ Updated user memory: {slug}")
                    else:
                        # CREATE en Mem0
                        logger.info(f"[SII Auth Service] ✨ Creating user memory: {slug} (category: {category})")
                        result = await mem0.add(
                            messages=[{"role": "user", "content": content}],
                            user_id=str(user_id),
                            metadata={"slug": slug, "category": category}
                        )

                        # Obtener memory_id o event_id del resultado
                        # Mem0 puede retornar procesamiento asíncrono (status: PENDING) con event_id
                        memory_id = None
                        if isinstance(result, dict):
                            # Intentar diferentes estructuras de respuesta
                            if "results" in result and isinstance(result["results"], list) and len(result["results"]) > 0:
                                first_result = result["results"][0]
                                # Puede tener 'id' (memoria creada) o 'event_id' (procesamiento pendiente)
                                memory_id = first_result.get("id") or first_result.get("event_id")
                                status = first_result.get("status", "UNKNOWN")
                                logger.info(f"[SII Auth Service] Mem0 status: {status}, memory_id: {memory_id}")
                            elif "id" in result:
                                memory_id = result.get("id")
                            elif "event_id" in result:
                                memory_id = result.get("event_id")
                            elif "memory_id" in result:
                                memory_id = result.get("memory_id")

                        if not memory_id:
                            logger.error(f"[SII Auth Service] ❌ No memory_id/event_id returned from Mem0. Response: {result}")
                            continue

                        # Crear en BD usando repositorio
                        await user_brain_repo.create(
                            user_id=user_id,
                            memory_id=memory_id,
                            slug=slug,
                            content=content,
                            extra_metadata={"category": category}
                        )
                        logger.info(f"[SII Auth Service] ✅ Created user memory: {slug}")

                except Exception as e:
                    logger.error(
                        f"[SII Auth Service] ❌ Error with user memory {memory_data.get('slug')}: {e}",
                        exc_info=True
                    )

            # Commit de cambios en BD
            await self.db.commit()

            logger.info(
                f"[SII Auth Service] 🎉 Memory save completed: "
                f"{len(company_memories_to_save)} company memories, "
                f"{len(user_memories_to_save)} user memories"
            )

        except Exception as e:
            # No interrumpir el flujo de onboarding si falla la memoria
            logger.error(
                f"[SII Auth Service] ❌ Error in _save_onboarding_memories: {e}",
                exc_info=True
            )

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
