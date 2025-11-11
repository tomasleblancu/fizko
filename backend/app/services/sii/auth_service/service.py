"""
Servicio principal de autenticación SII
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Session as SessionModel, Company

from .sii_auth import authenticate_and_extract_sii
from .setup import (
    ensure_profile,
    setup_company,
    setup_tax_info,
    setup_session,
    check_needs_initial_setup,
    create_trial_subscription
)
from .memories import save_onboarding_memories
from .events import (
    activate_mandatory_events,
    assign_auto_notifications,
    trigger_sync_tasks
)

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

    async def _get_existing_session_with_cookies(
        self,
        rut: str,
        user_id: UUID
    ) -> Optional[SessionModel]:
        """
        Busca una sesión existente para este RUT y usuario con cookies

        Args:
            rut: RUT del contribuyente
            user_id: UUID del usuario

        Returns:
            SessionModel si existe, None si no
        """
        # Normalizar RUT
        rut_normalized = rut.replace(".", "").replace("-", "").lower()

        # Buscar sesión existente
        stmt = (
            select(SessionModel)
            .join(Company)
            .where(
                Company.rut == rut_normalized,
                SessionModel.user_id == user_id,
                SessionModel.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session and session.cookies and session.cookies.get('sii_cookies'):
            return session

        return None

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
        profile = await ensure_profile(self.db, user_id, user_data)
        logger.info(f"[SII Auth Service] Profile ensured for user {user_id}")

        # PASO 2: Buscar cookies existentes (si las hay)
        existing_cookies = None
        existing_session = await self._get_existing_session_with_cookies(rut, user_id)
        if existing_session:
            existing_cookies = existing_session.cookies.get('sii_cookies', [])
            logger.info(f"[SII Auth Service] Found existing session with {len(existing_cookies)} cookies for {rut}")

        # PASO 3: Autenticar y extraer (verifica sesión si hay cookies, o hace login si no hay)
        # Esta función maneja todo dentro del contexto de Selenium:
        # - Si hay cookies: las verifica, refresca si expiraron, extrae contribuyente
        # - Si no hay cookies: hace login, extrae contribuyente
        logger.info(f"[SII Auth Service] Starting authentication and extraction for {rut}...")
        auth_result = await authenticate_and_extract_sii(
            rut=rut,
            password=password,
            cookies=existing_cookies
        )
        logger.info(f"[SII Auth Service] Authentication and extraction completed for {rut}")


        sii_cookies = auth_result['cookies']
        contribuyente_info = auth_result['contribuyente_info']
        session_refreshed = auth_result['session_refreshed']

        if session_refreshed:
            logger.info(f"[SII Auth Service] ✅ Session was refreshed or created for {rut}")
        else:
            logger.info(f"[SII Auth Service] ✅ Reused existing valid session for {rut}")

        # Construir sii_data en el formato esperado
        sii_data = {
            'contribuyente_info': contribuyente_info,
            'cookies': sii_cookies
        }

        # PASO 3: Setup de Company
        company, company_action = await setup_company(self.db, rut, password, sii_data)
        logger.info(f"[SII Auth Service] Company {company_action}: {company.business_name}")

        # PASO 3.5: Create trial subscription for new companies
        is_new_company = company_action == "creada"
        if is_new_company:
            subscription, subscription_action = await create_trial_subscription(
                self.db,
                company.id,
                trial_days=14  # 14 días de prueba gratis
            )
            logger.info(
                f"[SII Auth Service] Trial subscription {subscription_action} for company {company.id}: "
                f"14 days trial with Basic plan"
            )

        # PASO 4: Setup de CompanyTaxInfo
        company_tax_info, tax_action = await setup_tax_info(self.db, company.id, sii_data)
        logger.info(f"[SII Auth Service] CompanyTaxInfo {tax_action}")

        # PASO 5: Setup de Session con cookies
        session, session_action = await setup_session(
            self.db,
            user_id,
            company.id,
            password,
            sii_data['cookies']
        )
        logger.info(f"[SII Auth Service] Session {session_action}")

        # PASO 6: Disparar activación de eventos tributarios obligatorios (async)
        await activate_mandatory_events(company.id)
        logger.info(
            f"[SII Auth Service] Mandatory events activation task dispatched "
            f"for company {company.id}"
        )

        # PASO 6.5: Disparar asignación de notificaciones automáticas (async)
        await assign_auto_notifications(
            company.id,
            is_new_company
        )
        logger.info(
            f"[SII Auth Service] Auto-notifications assignment task dispatched "
            f"for company {company.id} (is_new={is_new_company})"
        )

        # PASO 7: Commit de todos los cambios (incluye eventos y notificaciones)
        await self.db.commit()

        # Refresh para obtener datos actualizados
        await self.db.refresh(company)
        await self.db.refresh(company_tax_info)
        await self.db.refresh(session)

        # PASO 7.5: Guardar información en memoria (Mem0) para uso de agentes AI
        await save_onboarding_memories(
            db=self.db,
            user_id=user_id,
            company=company,
            company_tax_info=company_tax_info,
            contribuyente_info=sii_data['contribuyente_info'],
            is_new_company=is_new_company,
            profile=profile
        )
        logger.info(f"[SII Auth Service] Onboarding memories saved for user {user_id}, company {company.id}")

        # PASO 8: Disparar tareas de sincronización en background (solo para empresas nuevas)
        if is_new_company:
            await trigger_sync_tasks(company.id)
            logger.info(f"[SII Auth Service] Sync tasks triggered for new company {company.id}")
        else:
            logger.info(f"[SII Auth Service] Skipping sync tasks for existing company {company.id}")

        # PASO 9: Verificar si necesita configuración inicial
        needs_initial_setup = await check_needs_initial_setup(self.db, company.id)
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

    def _build_response(
        self,
        company,
        company_tax_info,
        session,
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
