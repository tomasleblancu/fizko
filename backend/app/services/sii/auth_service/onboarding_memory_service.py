"""
Onboarding Memory Service.

Business logic for building and saving onboarding memories.
"""
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import CompanyRepository, CompanyTaxInfoRepository, ProfileRepository
from app.services.memory_service import save_company_memories, save_user_memories
from app.agents.tools.memory.memory_tools import get_mem0_client
from .memories import _build_company_memories, _build_user_memories

logger = logging.getLogger(__name__)


class OnboardingMemoryService:
    """Service for handling onboarding memory workflow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_onboarding_memories(
        self,
        user_id: UUID,
        company_id: UUID,
        company_tax_info_id: UUID,
        contribuyente_info: dict,
        is_new_company: bool
    ) -> dict:
        """
        Complete onboarding memory workflow.

        1. Load entities from DB
        2. Build company memories
        3. Build user memories
        4. Save both to Mem0

        Args:
            user_id: UUID of the user
            company_id: UUID of the company
            company_tax_info_id: UUID of CompanyTaxInfo
            contribuyente_info: Dict with contributor information from SII
            is_new_company: True if company was newly created

        Returns:
            Dict with counts: {"company_memories_count": int, "user_memories_count": int}
        """
        mem0 = get_mem0_client()

        # Load entities from DB
        company_repo = CompanyRepository(self.db)
        company = await company_repo.get(company_id)

        if not company:
            raise ValueError(f"Company {company_id} not found")

        company_tax_info_repo = CompanyTaxInfoRepository(self.db)
        company_tax_info = await company_tax_info_repo.get(company_tax_info_id)

        if not company_tax_info:
            raise ValueError(f"CompanyTaxInfo {company_tax_info_id} not found")

        profile_repo = ProfileRepository(self.db)
        profile = await profile_repo.get_by_user_id(user_id)

        # Build company memories
        company_memories = _build_company_memories(
            company=company,
            company_tax_info=company_tax_info,
            contribuyente_info=contribuyente_info,
            is_new_company=is_new_company
        )

        # Save company memories
        await save_company_memories(
            db=self.db,
            company_id=company_id,
            mem0_client=mem0,
            memories=company_memories
        )

        # Build user memories
        user_memories = await _build_user_memories(
            db=self.db,
            user_id=user_id,
            company=company,
            profile=profile
        )

        # Save user memories
        await save_user_memories(
            db=self.db,
            user_id=user_id,
            mem0_client=mem0,
            memories=user_memories
        )

        logger.info(
            f"[Onboarding Memory Service] Saved {len(company_memories)} company memories, "
            f"{len(user_memories)} user memories"
        )

        return {
            "company_memories_count": len(company_memories),
            "user_memories_count": len(user_memories)
        }
