"""
Módulo de gestión de memorias para Company Settings
"""
import logging
from typing import List, Dict
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, CompanySettings

logger = logging.getLogger(__name__)


async def save_company_settings_memories(
    db: AsyncSession,
    company: Company,
    settings: CompanySettings,
    is_initial_setup: bool
) -> None:
    """
    Dispara tarea Celery para guardar memorias de company settings en Mem0.

    Esta función NO espera a que se complete el guardado de memoria.
    El guardado se ejecuta en background mediante Celery para no bloquear
    el request HTTP.

    Args:
        db: Sesión async de base de datos
        company: Company con información básica
        settings: CompanySettings con la configuración actualizada
        is_initial_setup: True si es la primera vez que se completa el setup

    Note:
        Las memorias se guardan de forma asíncrona. Si falla, Celery reintentará
        automáticamente hasta 3 veces.
    """
    try:
        from app.infrastructure.celery.tasks.memory import save_company_memories_task

        logger.info(
            f"[Company Settings] 🚀 Dispatching memory task for company {company.id}"
        )

        # Construir memorias de settings
        memories = _build_settings_memories(
            company=company,
            settings=settings,
            is_initial_setup=is_initial_setup
        )

        # Disparar tarea Celery en background
        save_company_memories_task.delay(
            company_id=str(company.id),
            memories=memories
        )

        logger.info(
            f"[Company Settings] ✅ Memory task dispatched successfully "
            f"({len(memories)} memories)"
        )

    except Exception as e:
        # No interrumpir el flujo si falla el dispatch
        logger.error(
            f"[Company Settings] ❌ Error dispatching memory task: {e}",
            exc_info=True
        )


def _build_settings_memories(
    company: Company,
    settings: CompanySettings,
    is_initial_setup: bool
) -> List[Dict[str, str]]:
    """
    Construye la lista de memorias de settings

    Returns:
        Lista de dicts con estructura: {slug, category, content}
    """
    memories = []
    business_name = company.business_name or "Empresa"

    # 1. Información sobre empleados formales
    if settings.has_formal_employees is not None:
        if settings.has_formal_employees:
            memories.append({
                "slug": "company_has_formal_employees",
                "category": "company_business",
                "content": f"{business_name} tiene empleados formales con contratos laborales y debe gestionar nóminas"
            })
        else:
            memories.append({
                "slug": "company_has_formal_employees",
                "category": "company_business",
                "content": f"{business_name} no tiene empleados formales, trabaja solo con honorarios o es unipersonal"
            })

    # 2. Información sobre importaciones
    if settings.has_imports is not None:
        if settings.has_imports:
            memories.append({
                "slug": "company_has_imports",
                "category": "company_business",
                "content": f"{business_name} realiza importaciones y debe gestionar documentación aduanera"
            })
        else:
            memories.append({
                "slug": "company_has_imports",
                "category": "company_business",
                "content": f"{business_name} no realiza importaciones"
            })

    # 3. Información sobre exportaciones
    if settings.has_exports is not None:
        if settings.has_exports:
            memories.append({
                "slug": "company_has_exports",
                "category": "company_business",
                "content": f"{business_name} realiza exportaciones y debe cumplir con regulaciones de exportación"
            })
        else:
            memories.append({
                "slug": "company_has_exports",
                "category": "company_business",
                "content": f"{business_name} no realiza exportaciones"
            })

    # 4. Información sobre contratos de arrendamiento
    if settings.has_lease_contracts is not None:
        if settings.has_lease_contracts:
            memories.append({
                "slug": "company_has_lease_contracts",
                "category": "company_business",
                "content": f"{business_name} tiene contratos de arrendamiento y debe gestionar retenciones"
            })
        else:
            memories.append({
                "slug": "company_has_lease_contracts",
                "category": "company_business",
                "content": f"{business_name} no tiene contratos de arrendamiento"
            })

    # 5. Marcar que se completó el setup inicial
    if is_initial_setup:
        today = datetime.utcnow().strftime('%d/%m/%Y')
        memories.append({
            "slug": "company_initial_setup_completed",
            "category": "company_milestones",
            "content": f"Configuración inicial de {business_name} completada el {today}"
        })

    return memories
