"""
Servicio compartido para gestión de memorias con Mem0 usando Brain pattern.

Este módulo proporciona funciones reutilizables para guardar/actualizar
memorias en Mem0 con el patrón Brain (slug + category) tanto para
Company como para User.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import CompanyBrainRepository, UserBrainRepository

logger = logging.getLogger(__name__)


async def save_company_memories(
    db: AsyncSession,
    company_id: UUID,
    mem0_client: Any,
    memories: List[Dict[str, str]]
) -> None:
    """
    Guarda o actualiza memorias de empresa en Mem0 usando Brain pattern.

    Args:
        db: Sesión async de base de datos
        company_id: UUID de la compañía
        mem0_client: Cliente de Mem0
        memories: Lista de memorias con estructura {slug, category, content}

    Example:
        memories = [
            {
                "slug": "company_tax_regime",
                "category": "company_tax",
                "content": "Régimen tributario: ProPyme General"
            }
        ]
    """
    company_entity_id = f"company_{company_id}"
    brain_repo = CompanyBrainRepository(db)

    await _save_memories(
        db=db,
        brain_repo=brain_repo,
        entity_id=company_entity_id,
        entity_type="company",
        mem0_client=mem0_client,
        memories=memories,
        company_id=company_id,
        user_id=None
    )


async def save_user_memories(
    db: AsyncSession,
    user_id: UUID,
    mem0_client: Any,
    memories: List[Dict[str, str]]
) -> None:
    """
    Guarda o actualiza memorias de usuario en Mem0 usando Brain pattern.

    Args:
        db: Sesión async de base de datos
        user_id: UUID del usuario
        mem0_client: Cliente de Mem0
        memories: Lista de memorias con estructura {slug, category, content}

    Example:
        memories = [
            {
                "slug": "user_full_name",
                "category": "user_profile",
                "content": "Nombre completo: Juan Pérez"
            }
        ]
    """
    brain_repo = UserBrainRepository(db)

    await _save_memories(
        db=db,
        brain_repo=brain_repo,
        entity_id=str(user_id),
        entity_type="user",
        mem0_client=mem0_client,
        memories=memories,
        company_id=None,
        user_id=user_id
    )


async def _save_memories(
    db: AsyncSession,
    brain_repo: Any,
    entity_id: str,
    entity_type: str,
    mem0_client: Any,
    memories: List[Dict[str, str]],
    company_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None
) -> None:
    """
    Guarda o actualiza memorias en Mem0 y base de datos usando Brain pattern.

    Esta función:
    1. Busca si existe una memoria con el mismo slug
    2. Si existe: actualiza en Mem0 y BD
    3. Si no existe: crea en Mem0 y BD

    Args:
        db: Sesión async de base de datos
        brain_repo: CompanyBrainRepository o UserBrainRepository
        entity_id: ID de la entidad para Mem0 (company_xxx o user_id)
        entity_type: "company" o "user"
        mem0_client: Cliente de Mem0
        memories: Lista de memorias con {slug, category, content}
        company_id: UUID de la compañía (para company memories)
        user_id: UUID del usuario (para user memories)
    """
    for memory_data in memories:
        try:
            slug = memory_data["slug"]
            category = memory_data["category"]
            content = memory_data["content"]

            # Buscar si ya existe una memoria con este slug
            if entity_type == "company":
                existing_brain = await brain_repo.get_by_company_and_slug(
                    company_id=company_id,
                    slug=slug
                )
            else:  # user
                existing_brain = await brain_repo.get_by_user_and_slug(
                    user_id=user_id,
                    slug=slug
                )

            if existing_brain:
                # Try UPDATE en Mem0
                logger.info(
                    f"[Memory Service] 🔄 Updating {entity_type} memory: {slug} "
                    f"(category: {category})"
                )

                try:
                    await mem0_client.update(
                        memory_id=existing_brain.memory_id,
                        text=content
                    )

                    # Actualizar en BD usando repositorio
                    await brain_repo.update(
                        id=existing_brain.id,
                        content=content,
                        extra_metadata={"category": category}
                    )
                    logger.info(
                        f"[Memory Service] ✅ Updated {entity_type} memory: {slug}"
                    )

                except Exception as update_error:
                    # Check if memory doesn't exist in Mem0 (404)
                    error_str = str(update_error).lower()
                    is_not_found = "404" in error_str or "not found" in error_str

                    if is_not_found:
                        logger.warning(
                            f"[Memory Service] ⚠️  Memory {slug} not found in Mem0, "
                            f"recreating..."
                        )

                        # CREATE new memory in Mem0
                        result = await mem0_client.add(
                            messages=[{"role": "user", "content": content}],
                            user_id=entity_id,
                            metadata={"slug": slug, "category": category}
                        )

                        # Extract new memory_id
                        new_memory_id = _extract_memory_id(result)

                        if new_memory_id:
                            # Update DB with new memory_id
                            await brain_repo.update(
                                id=existing_brain.id,
                                memory_id=new_memory_id,
                                content=content,
                                extra_metadata={"category": category}
                            )
                            logger.info(
                                f"[Memory Service] ✅ Recreated {entity_type} memory: "
                                f"{slug} (new ID: {new_memory_id})"
                            )
                        else:
                            logger.error(
                                f"[Memory Service] ❌ Failed to get memory_id after "
                                f"recreating {slug}"
                            )
                    else:
                        # Other error, re-raise
                        raise
            else:
                # CREATE en Mem0
                logger.info(
                    f"[Memory Service] ✨ Creating {entity_type} memory: {slug} "
                    f"(category: {category})"
                )
                result = await mem0_client.add(
                    messages=[{"role": "user", "content": content}],
                    user_id=entity_id,
                    metadata={"slug": slug, "category": category}
                )

                # Obtener memory_id del resultado
                memory_id = _extract_memory_id(result)

                if not memory_id:
                    logger.error(
                        f"[Memory Service] ❌ No memory_id returned from Mem0. "
                        f"Response: {result}"
                    )
                    continue

                # Crear en BD usando repositorio
                if entity_type == "company":
                    await brain_repo.create(
                        company_id=company_id,
                        memory_id=memory_id,
                        slug=slug,
                        content=content,
                        extra_metadata={"category": category}
                    )
                else:  # user
                    await brain_repo.create(
                        user_id=user_id,
                        memory_id=memory_id,
                        slug=slug,
                        content=content,
                        extra_metadata={"category": category}
                    )
                logger.info(
                    f"[Memory Service] ✅ Created {entity_type} memory: {slug}"
                )

        except Exception as e:
            logger.error(
                f"[Memory Service] ❌ Error with {entity_type} memory "
                f"{memory_data.get('slug')}: {e}",
                exc_info=True
            )


def _extract_memory_id(result: Any) -> Optional[str]:
    """
    Extrae memory_id de la respuesta de Mem0.

    Mem0 puede retornar diferentes estructuras de respuesta:
    - Memoria creada inmediatamente: {"results": [{"id": "mem_xxx", "status": "COMPLETED"}]}
    - Memoria en procesamiento: {"results": [{"event_id": "evt_xxx", "status": "PENDING"}]}
    - Formato directo: {"id": "mem_xxx"} o {"event_id": "evt_xxx"}

    Args:
        result: Respuesta de Mem0

    Returns:
        Memory ID (mem_xxx) o event ID (evt_xxx), o None si no se encuentra
    """
    memory_id = None
    if isinstance(result, dict):
        # Intentar diferentes estructuras de respuesta
        if "results" in result and isinstance(result["results"], list) and len(result["results"]) > 0:
            first_result = result["results"][0]
            # Puede tener 'id' (memoria creada) o 'event_id' (procesamiento pendiente)
            memory_id = first_result.get("id") or first_result.get("event_id")
            status = first_result.get("status", "UNKNOWN")
            logger.info(
                f"[Memory Service] Mem0 status: {status}, memory_id: {memory_id}"
            )
        elif "id" in result:
            memory_id = result.get("id")
        elif "event_id" in result:
            memory_id = result.get("event_id")
        elif "memory_id" in result:
            memory_id = result.get("memory_id")

    return memory_id
