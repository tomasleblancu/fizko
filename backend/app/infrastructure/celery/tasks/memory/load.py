"""
Memory Loading Celery Tasks

Tasks for loading memories from existing company and user data into Mem0.
This is the initial data population phase for the memory system.
"""
import logging
from typing import Dict, Any

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="memory.load_company_memories",
    max_retries=2,
    default_retry_delay=60,
)
def load_company_memories(
    self,
    company_id: str
) -> Dict[str, Any]:
    """
    Celery task to load memories for a specific company from existing data.

    This task:
    1. Fetches company data (basic info + tax info)
    2. Builds memory list with appropriate slugs
    3. Calls save_company_memories() to store in Mem0 + database
    4. Is idempotent - can be run multiple times (updates existing memories)

    Memories created:
    - company_tax_regime: Tax regime (regimen_general, pro_pyme, etc.)
    - company_activity: SII activity name and code
    - company_legal_representative: Legal representative info
    - company_start_date: Start of activities date
    - company_accounting_start: Accounting start month

    Args:
        company_id: UUID of the company (str format)

    Returns:
        Dict with load results:
        {
            "success": bool,
            "company_id": str,
            "company_name": str,
            "memories_created": int,
            "memories_updated": int,
            "errors": list[str]
        }

    Example:
        >>> load_company_memories.delay("123e4567-e89b-12d3-a456-426614174000")
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.repositories import CompaniesRepository
        from app.services import save_company_memories

        logger.info(
            f"🧠 [CELERY TASK] Loading company memories: company_id={company_id}"
        )

        # Get Supabase client and repository
        supabase = get_supabase_client()
        companies_repo = CompaniesRepository(supabase._client)

        async def _load():
            # Fetch company data with tax info
            company = await companies_repo.get_by_id(
                company_id=company_id,
                include_tax_info=True
            )

            if not company:
                raise ValueError(f"Company {company_id} not found")

            company_name = company.get("business_name", "Unknown")
            logger.info(f"🧠 Found company: {company_name}")

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

            # Log what we're about to save
            logger.info(
                f"🧠 Built {len(memories)} memories for company {company_name}"
            )

            if len(memories) == 0:
                logger.warning(
                    f"⚠️  No memory data available for company {company_name}"
                )
                return {
                    "success": True,
                    "company_id": company_id,
                    "company_name": company_name,
                    "memories_created": 0,
                    "memories_updated": 0,
                    "errors": ["No data available to create memories"]
                }

            # Save memories using memory service
            result = await save_company_memories(
                company_id=company_id,
                memories=memories
            )

            # Return enriched result
            return {
                "success": result["success"],
                "company_id": company_id,
                "company_name": company_name,
                "memories_created": result["saved_count"],
                "memories_updated": 0,  # Service doesn't distinguish create vs update
                "errors": result.get("errors", [])
            }

        # Run async function
        result = asyncio.run(_load())

        # Log result
        if result.get("success"):
            logger.info(
                f"✅ [CELERY TASK] Company memories loaded: "
                f"company={result.get('company_name')}, "
                f"created={result.get('memories_created', 0)}"
            )
        else:
            logger.error(
                f"❌ [CELERY TASK] Company memories failed: "
                f"company_id={company_id}, "
                f"errors={result.get('errors')}"
            )

        return result

    except ValueError as e:
        # Validation errors (company not found, etc.)
        error_msg = str(e)
        logger.error(
            f"❌ [CELERY TASK] Validation error: {error_msg}"
        )
        return {
            "success": False,
            "company_id": company_id,
            "errors": [error_msg]
        }

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Company memory load failed: {e}",
            exc_info=True
        )

        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            logger.info(
                f"🔄 Retrying... (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        return {
            "success": False,
            "company_id": company_id,
            "errors": [str(e)]
        }


@celery_app.task(
    bind=True,
    name="memory.load_user_memories",
    max_retries=2,
    default_retry_delay=60,
)
def load_user_memories(
    self,
    user_id: str
) -> Dict[str, Any]:
    """
    Celery task to load memories for a specific user from existing data.

    This task:
    1. Fetches user profile data
    2. Builds memory list with appropriate slugs
    3. Calls save_user_memories() to store in Mem0 + database
    4. Is idempotent - can be run multiple times (updates existing memories)

    Memories created:
    - user_full_name: User's full name
    - user_email: User's email
    - user_phone: User's phone number
    - user_role: User's role/position

    Args:
        user_id: UUID of the user (str format)

    Returns:
        Dict with load results:
        {
            "success": bool,
            "user_id": str,
            "user_name": str,
            "memories_created": int,
            "memories_updated": int,
            "errors": list[str]
        }

    Example:
        >>> load_user_memories.delay("123e4567-e89b-12d3-a456-426614174000")
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.services import save_user_memories

        logger.info(
            f"🧠 [CELERY TASK] Loading user memories: user_id={user_id}"
        )

        # Get Supabase client
        supabase = get_supabase_client()

        async def _load():
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
                raise ValueError(f"User {user_id} not found")

            user_name = profile.get("full_name", profile.get("email", "Unknown"))
            logger.info(f"🧠 Found user: {user_name}")

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

            # Log what we're about to save
            logger.info(
                f"🧠 Built {len(memories)} memories for user {user_name}"
            )

            if len(memories) == 0:
                logger.warning(
                    f"⚠️  No memory data available for user {user_name}"
                )
                return {
                    "success": True,
                    "user_id": user_id,
                    "user_name": user_name,
                    "memories_created": 0,
                    "memories_updated": 0,
                    "errors": ["No data available to create memories"]
                }

            # Save memories using memory service
            result = await save_user_memories(
                user_id=user_id,
                memories=memories
            )

            # Return enriched result
            return {
                "success": result["success"],
                "user_id": user_id,
                "user_name": user_name,
                "memories_created": result["saved_count"],
                "memories_updated": 0,  # Service doesn't distinguish create vs update
                "errors": result.get("errors", [])
            }

        # Run async function
        result = asyncio.run(_load())

        # Log result
        if result.get("success"):
            logger.info(
                f"✅ [CELERY TASK] User memories loaded: "
                f"user={result.get('user_name')}, "
                f"created={result.get('memories_created', 0)}"
            )
        else:
            logger.error(
                f"❌ [CELERY TASK] User memories failed: "
                f"user_id={user_id}, "
                f"errors={result.get('errors')}"
            )

        return result

    except ValueError as e:
        # Validation errors (user not found, etc.)
        error_msg = str(e)
        logger.error(
            f"❌ [CELERY TASK] Validation error: {error_msg}"
        )
        return {
            "success": False,
            "user_id": user_id,
            "errors": [error_msg]
        }

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] User memory load failed: {e}",
            exc_info=True
        )

        # Retry on unexpected errors
        if self.request.retries < self.max_retries:
            logger.info(
                f"🔄 Retrying... (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=e)

        return {
            "success": False,
            "user_id": user_id,
            "errors": [str(e)]
        }


@celery_app.task(
    bind=True,
    name="memory.load_all_companies_memories",
    max_retries=1,
)
def load_all_companies_memories(self) -> Dict[str, Any]:
    """
    Celery task to load memories for ALL companies in batch.

    This is a batch task that:
    1. Finds all companies in the system
    2. For each company, loads their memories
    3. Returns statistics about the batch operation

    Useful for:
    - Initial memory population
    - Recovery after system issues
    - Bulk memory refresh

    Returns:
        Dict with batch load results:
        {
            "success": bool,
            "total_companies": int,
            "loaded_companies": int,
            "failed_companies": int,
            "total_memories_created": int,
            "results": list[dict]  # Per-company results
        }

    Example:
        >>> load_all_companies_memories.delay()
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client
        from app.repositories import CompaniesRepository

        logger.info("🚀 [CELERY TASK] Batch company memory load started for ALL companies")

        # Get Supabase client and repository
        supabase = get_supabase_client()
        companies_repo = CompaniesRepository(supabase._client)

        async def _load_all():
            # Get all companies
            companies = await companies_repo.get_all(limit=1000)

            if not companies:
                logger.warning("⚠️  No companies found")
                return {
                    "success": True,
                    "total_companies": 0,
                    "loaded_companies": 0,
                    "failed_companies": 0,
                    "total_memories_created": 0,
                    "results": []
                }

            logger.info(f"🧠 Found {len(companies)} companies to process")

            loaded_count = 0
            failed_count = 0
            total_memories = 0
            results = []

            # Process each company
            for company in companies:
                company_id = company["id"]
                company_name = company.get("business_name", "Unknown")

                try:
                    # Use the single-company task synchronously
                    result = load_company_memories(company_id)

                    if result.get("success"):
                        loaded_count += 1
                        total_memories += result.get("memories_created", 0)
                    else:
                        failed_count += 1

                    results.append(result)

                except Exception as e:
                    logger.error(
                        f"❌ Failed to load memories for company {company_name}: {e}"
                    )
                    failed_count += 1
                    results.append({
                        "success": False,
                        "company_id": company_id,
                        "company_name": company_name,
                        "errors": [str(e)]
                    })

            return {
                "success": failed_count == 0,
                "total_companies": len(companies),
                "loaded_companies": loaded_count,
                "failed_companies": failed_count,
                "total_memories_created": total_memories,
                "results": results
            }

        # Run async function
        result = asyncio.run(_load_all())

        logger.info(
            f"✅ [CELERY TASK] Batch company memory load completed: "
            f"{result.get('loaded_companies', 0)}/{result.get('total_companies', 0)} companies loaded, "
            f"{result.get('failed_companies', 0)} failed, "
            f"{result.get('total_memories_created', 0)} memories created"
        )

        return result

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Batch company memory load failed: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "total_companies": 0,
            "loaded_companies": 0,
            "failed_companies": 0,
            "total_memories_created": 0,
            "results": []
        }


@celery_app.task(
    bind=True,
    name="memory.load_all_users_memories",
    max_retries=1,
)
def load_all_users_memories(self) -> Dict[str, Any]:
    """
    Celery task to load memories for ALL users in batch.

    This is a batch task that:
    1. Finds all users in the system
    2. For each user, loads their memories
    3. Returns statistics about the batch operation

    Useful for:
    - Initial memory population
    - Recovery after system issues
    - Bulk memory refresh

    Returns:
        Dict with batch load results:
        {
            "success": bool,
            "total_users": int,
            "loaded_users": int,
            "failed_users": int,
            "total_memories_created": int,
            "results": list[dict]  # Per-user results
        }

    Example:
        >>> load_all_users_memories.delay()
    """
    try:
        import asyncio
        from app.config.supabase import get_supabase_client

        logger.info("🚀 [CELERY TASK] Batch user memory load started for ALL users")

        # Get Supabase client
        supabase = get_supabase_client()

        async def _load_all():
            # Get all users
            profiles_response = (
                supabase._client
                .table("profiles")
                .select("id, full_name, email")
                .limit(1000)
                .execute()
            )
            profiles = profiles_response.data if hasattr(profiles_response, "data") else []

            if not profiles:
                logger.warning("⚠️  No users found")
                return {
                    "success": True,
                    "total_users": 0,
                    "loaded_users": 0,
                    "failed_users": 0,
                    "total_memories_created": 0,
                    "results": []
                }

            logger.info(f"🧠 Found {len(profiles)} users to process")

            loaded_count = 0
            failed_count = 0
            total_memories = 0
            results = []

            # Process each user
            for profile in profiles:
                user_id = profile["id"]
                user_name = profile.get("full_name", profile.get("email", "Unknown"))

                try:
                    # Use the single-user task synchronously
                    result = load_user_memories(user_id)

                    if result.get("success"):
                        loaded_count += 1
                        total_memories += result.get("memories_created", 0)
                    else:
                        failed_count += 1

                    results.append(result)

                except Exception as e:
                    logger.error(
                        f"❌ Failed to load memories for user {user_name}: {e}"
                    )
                    failed_count += 1
                    results.append({
                        "success": False,
                        "user_id": user_id,
                        "user_name": user_name,
                        "errors": [str(e)]
                    })

            return {
                "success": failed_count == 0,
                "total_users": len(profiles),
                "loaded_users": loaded_count,
                "failed_users": failed_count,
                "total_memories_created": total_memories,
                "results": results
            }

        # Run async function
        result = asyncio.run(_load_all())

        logger.info(
            f"✅ [CELERY TASK] Batch user memory load completed: "
            f"{result.get('loaded_users', 0)}/{result.get('total_users', 0)} users loaded, "
            f"{result.get('failed_users', 0)} failed, "
            f"{result.get('total_memories_created', 0)} memories created"
        )

        return result

    except Exception as e:
        logger.error(
            f"❌ [CELERY TASK] Batch user memory load failed: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "total_users": 0,
            "loaded_users": 0,
            "failed_users": 0,
            "total_memories_created": 0,
            "results": []
        }
