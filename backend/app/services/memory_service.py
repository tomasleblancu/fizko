"""
Memory Service - Shared service for managing memories with Mem0 using Brain pattern.

This module provides reusable functions for saving/updating memories in Mem0
with the Brain pattern (slug + category) for both Company and User.

Architecture:
1. Each memory has a unique slug (e.g., "company_tax_regime")
2. Memories are tracked in Supabase (user_brain, company_brain tables)
3. Memory content is stored in Mem0 cloud service
4. Updates use slug to find existing memories instead of creating duplicates

Functions:
- save_company_memories: Save/update company memories
- save_user_memories: Save/update user memories
- build_company_memories_from_data: Build memory list from company data
- build_user_memories_from_data: Build memory list from user data
"""

import logging
from typing import Any

from app.config.supabase import get_supabase_client
from app.integrations.mem0 import get_mem0_client, is_mem0_configured
from app.repositories import CompanyBrainRepository, UserBrainRepository, CompaniesRepository
from app.utils.rut import normalize_rut

logger = logging.getLogger(__name__)


async def save_company_memories(
    company_id: str,
    memories: list[dict[str, str]]
) -> dict[str, Any]:
    """
    Save or update company memories in Mem0 using Brain pattern.

    Args:
        company_id: Company UUID
        memories: List of memories with structure {slug, category, content}

    Returns:
        Dict with result:
        {
            "success": bool,
            "saved_count": int,
            "failed_count": int,
            "errors": list[str]
        }

    Example:
        memories = [
            {
                "slug": "company_tax_regime",
                "category": "company_tax",
                "content": "Régimen tributario: ProPyme General"
            }
        ]
        result = await save_company_memories(company_id, memories)
    """
    if not is_mem0_configured():
        logger.warning("[Memory Service] MEM0_API_KEY not configured - skipping memory save")
        return {
            "success": False,
            "saved_count": 0,
            "failed_count": len(memories),
            "errors": ["Mem0 not configured"]
        }

    mem0_client = get_mem0_client()
    supabase = get_supabase_client()
    brain_repo = CompanyBrainRepository(supabase._client)
    companies_repo = CompaniesRepository(supabase._client)

    # Get company RUT to use as entity_id in Mem0
    company = await companies_repo.get_by_id(company_id, include_tax_info=False)
    if not company or not company.get("rut"):
        error_msg = f"Company {company_id} not found or has no RUT"
        logger.error(f"[Memory Service] ❌ {error_msg}")
        return {
            "success": False,
            "saved_count": 0,
            "failed_count": len(memories),
            "errors": [error_msg]
        }

    # Use normalized RUT (without hyphens) as entity_id in Mem0
    company_rut = normalize_rut(company["rut"])
    logger.info(f"[Memory Service] Using company RUT as entity_id: {company_rut}")

    saved_count = 0
    failed_count = 0
    errors: list[str] = []

    for memory_data in memories:
        try:
            slug = memory_data["slug"]
            category = memory_data["category"]
            content = memory_data["content"]

            # Look for existing memory with this slug
            existing_brain = await brain_repo.get_by_company_and_slug(
                company_id=company_id,
                slug=slug
            )

            if existing_brain:
                # Try UPDATE in Mem0
                logger.info(
                    f"[Memory Service] 🔄 Updating company memory: {slug} "
                    f"(category: {category})"
                )

                try:
                    await mem0_client.update(
                        memory_id=existing_brain["memory_id"],
                        text=content
                    )

                    # Update in DB
                    await brain_repo.update(
                        id=existing_brain["id"],
                        content=content,
                        extra_metadata={"category": category}
                    )
                    logger.info(
                        f"[Memory Service] ✅ Updated company memory: {slug}"
                    )
                    saved_count += 1

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
                            user_id=company_rut,
                            metadata={"slug": slug, "category": category}
                        )

                        # Extract new memory_id
                        new_memory_id = _extract_memory_id(result)

                        if new_memory_id:
                            # Update DB with new memory_id
                            await brain_repo.update(
                                id=existing_brain["id"],
                                memory_id=new_memory_id,
                                content=content,
                                extra_metadata={"category": category}
                            )
                            logger.info(
                                f"[Memory Service] ✅ Recreated company memory: "
                                f"{slug} (new ID: {new_memory_id})"
                            )
                            saved_count += 1
                        else:
                            error_msg = f"Failed to get memory_id after recreating {slug}"
                            logger.error(f"[Memory Service] ❌ {error_msg}")
                            errors.append(error_msg)
                            failed_count += 1
                    else:
                        # Other error, re-raise
                        raise
            else:
                # CREATE in Mem0
                logger.info(
                    f"[Memory Service] ✨ Creating company memory: {slug} "
                    f"(category: {category})"
                )
                result = await mem0_client.add(
                    messages=[{"role": "user", "content": content}],
                    user_id=company_rut,
                    metadata={"slug": slug, "category": category}
                )

                # Get memory_id from result
                memory_id = _extract_memory_id(result)

                if not memory_id:
                    error_msg = f"No memory_id returned from Mem0 for slug: {slug}"
                    logger.error(f"[Memory Service] ❌ {error_msg}")
                    errors.append(error_msg)
                    failed_count += 1
                    continue

                # Create in DB
                await brain_repo.create(
                    company_id=company_id,
                    memory_id=memory_id,
                    slug=slug,
                    content=content,
                    extra_metadata={"category": category}
                )
                logger.info(
                    f"[Memory Service] ✅ Created company memory: {slug}"
                )
                saved_count += 1

        except Exception as e:
            error_msg = f"Error with company memory {memory_data.get('slug')}: {str(e)}"
            logger.error(
                f"[Memory Service] ❌ {error_msg}",
                exc_info=True
            )
            errors.append(error_msg)
            failed_count += 1

    return {
        "success": failed_count == 0,
        "saved_count": saved_count,
        "failed_count": failed_count,
        "errors": errors
    }


async def save_user_memories(
    user_id: str,
    memories: list[dict[str, str]]
) -> dict[str, Any]:
    """
    Save or update user memories in Mem0 using Brain pattern.

    Args:
        user_id: User UUID
        memories: List of memories with structure {slug, category, content}

    Returns:
        Dict with result:
        {
            "success": bool,
            "saved_count": int,
            "failed_count": int,
            "errors": list[str]
        }

    Example:
        memories = [
            {
                "slug": "user_full_name",
                "category": "user_profile",
                "content": "Nombre completo: Juan Pérez"
            }
        ]
        result = await save_user_memories(user_id, memories)
    """
    if not is_mem0_configured():
        logger.warning("[Memory Service] MEM0_API_KEY not configured - skipping memory save")
        return {
            "success": False,
            "saved_count": 0,
            "failed_count": len(memories),
            "errors": ["Mem0 not configured"]
        }

    mem0_client = get_mem0_client()
    supabase = get_supabase_client()
    brain_repo = UserBrainRepository(supabase._client)

    # Get user profile RUT to use as entity_id in Mem0
    profile_response = (
        supabase._client
        .table("profiles")
        .select("rut")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    profile = profile_response.data if hasattr(profile_response, "data") else None

    if not profile or not profile.get("rut"):
        error_msg = f"User {user_id} not found or has no RUT"
        logger.error(f"[Memory Service] ❌ {error_msg}")
        return {
            "success": False,
            "saved_count": 0,
            "failed_count": len(memories),
            "errors": [error_msg]
        }

    # Use normalized RUT (without hyphens) as entity_id in Mem0
    user_rut = normalize_rut(profile["rut"])
    logger.info(f"[Memory Service] Using user RUT as entity_id: {user_rut}")

    saved_count = 0
    failed_count = 0
    errors: list[str] = []

    for memory_data in memories:
        try:
            slug = memory_data["slug"]
            category = memory_data["category"]
            content = memory_data["content"]

            # Look for existing memory with this slug
            existing_brain = await brain_repo.get_by_user_and_slug(
                user_id=user_id,
                slug=slug
            )

            if existing_brain:
                # Try UPDATE in Mem0
                logger.info(
                    f"[Memory Service] 🔄 Updating user memory: {slug} "
                    f"(category: {category})"
                )

                try:
                    await mem0_client.update(
                        memory_id=existing_brain["memory_id"],
                        text=content
                    )

                    # Update in DB
                    await brain_repo.update(
                        id=existing_brain["id"],
                        content=content,
                        extra_metadata={"category": category}
                    )
                    logger.info(
                        f"[Memory Service] ✅ Updated user memory: {slug}"
                    )
                    saved_count += 1

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
                            user_id=user_rut,
                            metadata={"slug": slug, "category": category}
                        )

                        # Extract new memory_id
                        new_memory_id = _extract_memory_id(result)

                        if new_memory_id:
                            # Update DB with new memory_id
                            await brain_repo.update(
                                id=existing_brain["id"],
                                memory_id=new_memory_id,
                                content=content,
                                extra_metadata={"category": category}
                            )
                            logger.info(
                                f"[Memory Service] ✅ Recreated user memory: "
                                f"{slug} (new ID: {new_memory_id})"
                            )
                            saved_count += 1
                        else:
                            error_msg = f"Failed to get memory_id after recreating {slug}"
                            logger.error(f"[Memory Service] ❌ {error_msg}")
                            errors.append(error_msg)
                            failed_count += 1
                    else:
                        # Other error, re-raise
                        raise
            else:
                # CREATE in Mem0
                logger.info(
                    f"[Memory Service] ✨ Creating user memory: {slug} "
                    f"(category: {category})"
                )
                result = await mem0_client.add(
                    messages=[{"role": "user", "content": content}],
                    user_id=user_rut,
                    metadata={"slug": slug, "category": category}
                )

                # Get memory_id from result
                memory_id = _extract_memory_id(result)

                if not memory_id:
                    error_msg = f"No memory_id returned from Mem0 for slug: {slug}"
                    logger.error(f"[Memory Service] ❌ {error_msg}")
                    errors.append(error_msg)
                    failed_count += 1
                    continue

                # Create in DB
                await brain_repo.create(
                    user_id=user_id,
                    memory_id=memory_id,
                    slug=slug,
                    content=content,
                    extra_metadata={"category": category}
                )
                logger.info(
                    f"[Memory Service] ✅ Created user memory: {slug}"
                )
                saved_count += 1

        except Exception as e:
            error_msg = f"Error with user memory {memory_data.get('slug')}: {str(e)}"
            logger.error(
                f"[Memory Service] ❌ {error_msg}",
                exc_info=True
            )
            errors.append(error_msg)
            failed_count += 1

    return {
        "success": failed_count == 0,
        "saved_count": saved_count,
        "failed_count": failed_count,
        "errors": errors
    }


async def build_company_memories_from_data(
    company_id: str
) -> dict[str, Any]:
    """
    Build memory list from existing company data.

    Extracts data from companies and company_tax_info tables and builds
    a list of memories ready to be saved.

    Args:
        company_id: Company UUID

    Returns:
        Dict with result:
        {
            "success": bool,
            "company_name": str,
            "memories": list[dict],  # Ready for save_company_memories
            "error": str  # Only if failed
        }

    Example:
        result = await build_company_memories_from_data(company_id)
        if result["success"]:
            await save_company_memories(company_id, result["memories"])
    """
    try:
        supabase = get_supabase_client()
        companies_repo = CompaniesRepository(supabase._client)

        # Fetch company data with tax info
        company = await companies_repo.get_by_id(
            company_id=company_id,
            include_tax_info=True
        )

        if not company:
            return {
                "success": False,
                "error": f"Company {company_id} not found"
            }

        company_name = company.get("business_name", "Unknown")

        # Build memory list from available data
        memories: list[dict[str, str]] = []

        # Extract tax info (can be None if not set)
        tax_info = None
        if "company_tax_info" in company and company["company_tax_info"]:
            # Handle both list and dict responses
            tax_info_data = company["company_tax_info"]
            if isinstance(tax_info_data, list) and len(tax_info_data) > 0:
                tax_info = tax_info_data[0]
            elif isinstance(tax_info_data, dict):
                tax_info = tax_info_data

        # Memory 1: Tax Regime
        if tax_info and tax_info.get("tax_regime"):
            tax_regime = tax_info["tax_regime"]
            # Translate regime to Spanish
            regime_names = {
                "regimen_general": "Régimen General",
                "regimen_simplificado": "Régimen Simplificado",
                "pro_pyme": "ProPyme General",
                "14_ter": "14 TER"
            }
            regime_label = regime_names.get(tax_regime, tax_regime)
            memories.append({
                "slug": "company_tax_regime",
                "category": "company_tax",
                "content": f"Régimen tributario: {regime_label}"
            })

        # Memory 2: SII Activity
        if tax_info and (tax_info.get("sii_activity_name") or tax_info.get("sii_activity_code")):
            activity_name = tax_info.get("sii_activity_name", "No especificado")
            activity_code = tax_info.get("sii_activity_code", "")
            activity_text = f"Actividad económica: {activity_name}"
            if activity_code:
                activity_text += f" (Código SII: {activity_code})"
            memories.append({
                "slug": "company_activity",
                "category": "company_tax",
                "content": activity_text
            })

        # Memory 3: Legal Representative
        if tax_info and (tax_info.get("legal_representative_name") or tax_info.get("legal_representative_rut")):
            rep_name = tax_info.get("legal_representative_name", "")
            rep_rut = tax_info.get("legal_representative_rut", "")
            rep_text = "Representante legal: "
            if rep_name and rep_rut:
                rep_text += f"{rep_name} (RUT: {rep_rut})"
            elif rep_name:
                rep_text += rep_name
            elif rep_rut:
                rep_text += f"RUT {rep_rut}"
            memories.append({
                "slug": "company_legal_representative",
                "category": "company_tax",
                "content": rep_text
            })

        # Memory 4: Start of Activities Date
        if tax_info and tax_info.get("start_of_activities_date"):
            start_date = tax_info["start_of_activities_date"]
            memories.append({
                "slug": "company_start_date",
                "category": "company_tax",
                "content": f"Fecha de inicio de actividades: {start_date}"
            })

        # Memory 5: Accounting Start Month
        if tax_info and tax_info.get("accounting_start_month"):
            month = tax_info["accounting_start_month"]
            month_names = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            month_name = month_names.get(month, str(month))
            memories.append({
                "slug": "company_accounting_start",
                "category": "company_tax",
                "content": f"Mes de inicio contable: {month_name} (mes {month})"
            })

        return {
            "success": True,
            "company_name": company_name,
            "memories": memories
        }

    except Exception as e:
        logger.error(
            f"[Memory Service] Error building company memories: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e)
        }


async def build_user_memories_from_data(
    user_id: str
) -> dict[str, Any]:
    """
    Build memory list from existing user data.

    Extracts data from profiles table and builds a list of memories
    ready to be saved.

    Args:
        user_id: User UUID

    Returns:
        Dict with result:
        {
            "success": bool,
            "user_name": str,
            "memories": list[dict],  # Ready for save_user_memories
            "error": str  # Only if failed
        }

    Example:
        result = await build_user_memories_from_data(user_id)
        if result["success"]:
            await save_user_memories(user_id, result["memories"])
    """
    try:
        supabase = get_supabase_client()

        # Fetch user profile
        profile_response = (
            supabase._client
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        profile = profile_response.data if hasattr(profile_response, "data") else None

        if not profile:
            return {
                "success": False,
                "error": f"User {user_id} not found"
            }

        user_name = profile.get("full_name", profile.get("email", "Unknown"))

        # Build memory list from available data
        memories: list[dict[str, str]] = []

        # Memory 1: Full Name
        if profile.get("full_name"):
            memories.append({
                "slug": "user_full_name",
                "category": "user_profile",
                "content": f"Nombre completo: {profile['full_name']}"
            })

        # Memory 2: Email
        if profile.get("email"):
            memories.append({
                "slug": "user_email",
                "category": "user_profile",
                "content": f"Email: {profile['email']}"
            })

        # Memory 3: Phone
        if profile.get("phone"):
            memories.append({
                "slug": "user_phone",
                "category": "user_profile",
                "content": f"Teléfono: {profile['phone']}"
            })

        # Memory 4: Role/Position
        if profile.get("rol"):
            memories.append({
                "slug": "user_role",
                "category": "user_profile",
                "content": f"Rol/Cargo: {profile['rol']}"
            })

        return {
            "success": True,
            "user_name": user_name,
            "memories": memories
        }

    except Exception as e:
        logger.error(
            f"[Memory Service] Error building user memories: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e)
        }


def _extract_memory_id(result: Any) -> str | None:
    """
    Extract memory_id from Mem0 response.

    Mem0 can return different response structures:
    - Memory created immediately: {"results": [{"id": "mem_xxx", "status": "COMPLETED"}]}
    - Memory in processing: {"results": [{"event_id": "evt_xxx", "status": "PENDING"}]}
    - Direct format: {"id": "mem_xxx"} or {"event_id": "evt_xxx"}

    Args:
        result: Response from Mem0

    Returns:
        Memory ID (mem_xxx) or event ID (evt_xxx), or None if not found
    """
    memory_id = None
    if isinstance(result, dict):
        # Try different response structures
        if "results" in result and isinstance(result["results"], list) and len(result["results"]) > 0:
            first_result = result["results"][0]
            # Can have 'id' (memory created) or 'event_id' (pending processing)
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
