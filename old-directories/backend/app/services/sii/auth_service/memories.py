"""
Módulo de gestión de memorias en Mem0 durante onboarding
"""
import logging
from typing import Dict, List
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models import Company, CompanyTaxInfo, Profile, Session as SessionModel

logger = logging.getLogger(__name__)


async def save_onboarding_memories(
    db: AsyncSession,
    user_id: UUID,
    company: Company,
    company_tax_info: CompanyTaxInfo,
    contribuyente_info: dict,
    is_new_company: bool,
    profile: Profile
) -> None:
    """
    Dispara tarea Celery para guardar memorias de onboarding en Mem0.

    Esta función NO espera a que se complete el guardado de memoria.
    El guardado se ejecuta en background mediante Celery para no bloquear
    el flujo de onboarding.

    Args:
        db: Sesión async de base de datos
        user_id: UUID del usuario
        company: Company creada/actualizada
        company_tax_info: CompanyTaxInfo con datos tributarios
        contribuyente_info: Información del contribuyente desde SII
        is_new_company: True si la empresa fue creada, False si fue actualizada
        profile: Profile del usuario

    Note:
        Las memorias se guardan de forma asíncrona. Si falla, Celery reintentará
        automáticamente hasta 3 veces.
    """
    try:
        from app.infrastructure.celery.tasks.memory import save_onboarding_memories_task

        logger.info(
            f"[Memories] 🚀 Dispatching memory task for user {user_id}, "
            f"company {company.id}"
        )

        # Disparar tarea Celery en background
        save_onboarding_memories_task.delay(
            user_id=str(user_id),
            company_id=str(company.id),
            company_tax_info_id=str(company_tax_info.id),
            contribuyente_info=contribuyente_info,
            is_new_company=is_new_company
        )

        logger.info(
            f"[Memories] ✅ Memory task dispatched successfully"
        )

    except Exception as e:
        # No interrumpir el flujo de onboarding si falla el dispatch
        logger.error(
            f"[Memories] ❌ Error dispatching memory task: {e}",
            exc_info=True
        )


def _build_company_memories(
    company: Company,
    company_tax_info: CompanyTaxInfo,
    contribuyente_info: dict,
    is_new_company: bool
) -> List[Dict[str, str]]:
    """
    Construye la lista de memorias de empresa

    Returns:
        Lista de dicts con estructura: {slug, category, content}
    """
    memories = []
    business_name = company.business_name or "Empresa"

    # 1. Información básica de la empresa
    trade_name = company.trade_name
    if trade_name and trade_name != business_name:
        memories.append({
            "slug": "company_basic_info",
            "category": "company_info",
            "content": f"La empresa {business_name} (nombre de fantasía: {trade_name}) está registrada en el SII con RUT {company.rut}"
        })
    else:
        memories.append({
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
        memories.append({
            "slug": "company_tax_regime",
            "category": "company_tax",
            "content": f"Régimen tributario de la empresa: {regime_display}"
        })

    # 3. Actividad económica principal
    if company_tax_info.sii_activity_code and company_tax_info.sii_activity_name:
        memories.append({
            "slug": "company_activity",
            "category": "company_tax",
            "content": f"Actividad económica principal: {company_tax_info.sii_activity_code} - {company_tax_info.sii_activity_name}"
        })

    # 4. Inicio de actividades
    if company_tax_info.start_of_activities_date:
        start_date = company_tax_info.start_of_activities_date.strftime('%d/%m/%Y')
        memories.append({
            "slug": "company_start_date",
            "category": "company_tax",
            "content": f"Fecha de inicio de actividades: {start_date}"
        })
    elif contribuyente_info.get('fecha_inicio_actividades'):
        memories.append({
            "slug": "company_start_date",
            "category": "company_tax",
            "content": f"Inicio de actividades: {contribuyente_info['fecha_inicio_actividades']}"
        })

    # 5. Información de dirección
    if company.address:
        memories.append({
            "slug": "company_address",
            "category": "company_info",
            "content": f"Dirección registrada: {company.address}"
        })

    # 6. Fecha de incorporación a Fizko
    if is_new_company:
        memories.append({
            "slug": "company_fizko_join_date",
            "category": "company_info",
            "content": f"Empresa incorporada a Fizko el {datetime.utcnow().strftime('%d/%m/%Y')}"
        })

    # 7-12: Información extendida del SII
    _add_extended_sii_memories(memories, contribuyente_info)

    return memories


def _add_extended_sii_memories(memories: List[Dict[str, str]], contribuyente_info: dict) -> None:
    """
    Agrega memorias extendidas del SII (cumplimiento, observaciones, representantes, etc)

    Modifica la lista memories in-place
    """
    # 7. Cumplimiento tributario (desde opc=118)
    cumplimiento = contribuyente_info.get('cumplimiento_tributario')
    if cumplimiento:
        estado = cumplimiento.get('estado', 'Desconocido')
        atributos = cumplimiento.get('atributos', [])

        # Estado general de cumplimiento
        memories.append({
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

            memories.append({
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

            memories.append({
                "slug": "company_sii_alerts",
                "category": "company_tax",
                "content": f"Alertas/Observaciones del SII: {'; '.join(alertas_desc)}"
            })
    elif observaciones and not observaciones.get('tiene_observaciones'):
        # Registrar que NO hay observaciones (información positiva)
        memories.append({
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

            memories.append({
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

            memories.append({
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
                memories.append({
                    "slug": "company_primary_address",
                    "category": "company_info",
                    "content": f"{tipo} principal: {direccion_completa}"
                })
            else:
                memories.append({
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

        memories.append({
            "slug": "company_authorized_documents",
            "category": "company_tax",
            "content": f"Documentos tributarios autorizados: {'; '.join(docs_info)}"
        })


async def _build_user_memories(
    db: AsyncSession,
    user_id: UUID,
    company: Company,
    profile: Profile
) -> List[Dict[str, str]]:
    """
    Construye la lista de memorias de usuario

    Returns:
        Lista de dicts con estructura: {slug, category, content}
    """
    memories = []
    business_name = company.business_name or "Empresa"

    # 1. Vinculación con la empresa
    today = datetime.utcnow().strftime('%d/%m/%Y')
    memories.append({
        "slug": f"user_company_join_{company.id}",
        "category": "user_company_relationship",
        "content": f"Se vinculó con {business_name} el {today}"
    })

    # 2. Determinar rol del usuario
    stmt = select(func.count(SessionModel.id)).where(
        SessionModel.company_id == company.id,
        SessionModel.is_active == True
    )
    result = await db.execute(stmt)
    active_sessions_count = result.scalar()

    if active_sessions_count <= 1:
        memories.append({
            "slug": f"user_role_{company.id}",
            "category": "user_company_relationship",
            "content": f"Rol en {business_name}: Propietario/Administrador"
        })
    else:
        memories.append({
            "slug": f"user_role_{company.id}",
            "category": "user_company_relationship",
            "content": f"Rol en {business_name}: Miembro del equipo"
        })

    # 3. Información del perfil
    if profile:
        if profile.full_name:
            memories.append({
                "slug": "user_full_name",
                "category": "user_profile",
                "content": f"Nombre completo: {profile.full_name}"
            })
        if profile.phone:
            memories.append({
                "slug": "user_phone",
                "category": "user_profile",
                "content": f"Teléfono de contacto: {profile.phone}"
            })

    return memories
