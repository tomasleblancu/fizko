"""Repository for Session management."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Session as SessionModel, Profile
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[SessionModel]):
    """Repository for managing user sessions."""

    def __init__(self, db: AsyncSession):
        super().__init__(SessionModel, db)

    async def find_by_user_and_company(
        self,
        user_id: UUID,
        company_id: UUID
    ) -> Optional[SessionModel]:
        """
        Find a session for a specific user and company.

        Args:
            user_id: User UUID
            company_id: Company UUID

        Returns:
            Session instance or None if not found
        """
        result = await self.db.execute(
            select(SessionModel).where(
                SessionModel.user_id == user_id,
                SessionModel.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def user_has_access_to_company(
        self,
        user_id: UUID,
        company_id: UUID
    ) -> bool:
        """
        Check if a user has access to a company.

        Args:
            user_id: User UUID
            company_id: Company UUID

        Returns:
            True if user has access, False otherwise
        """
        session = await self.find_by_user_and_company(user_id, company_id)
        return session is not None

    async def get_users_by_company(
        self,
        company_id: UUID,
        include_profile: bool = True
    ) -> List[tuple[SessionModel, Optional[Profile]]]:
        """
        Get all users (sessions) for a company with their profiles.

        Args:
            company_id: Company UUID
            include_profile: Whether to join and return Profile data

        Returns:
            List of tuples (Session, Profile) ordered by last accessed date
        """
        if include_profile:
            stmt = (
                select(SessionModel, Profile)
                .join(Profile, SessionModel.user_id == Profile.id)
                .where(SessionModel.company_id == company_id)
                .order_by(desc(SessionModel.last_accessed_at))
            )
            result = await self.db.execute(stmt)
            return list(result.all())
        else:
            stmt = (
                select(SessionModel)
                .where(SessionModel.company_id == company_id)
                .order_by(desc(SessionModel.last_accessed_at))
            )
            result = await self.db.execute(stmt)
            return [(session, None) for session in result.scalars().all()]

    async def get_users_with_verified_phone(
        self,
        company_id: UUID,
        active_only: bool = True
    ) -> List[Profile]:
        """
        Get all users with verified phone for a company.

        Args:
            company_id: Company UUID
            active_only: Only return users with active sessions

        Returns:
            List of Profile instances with verified phone numbers
        """
        stmt = (
            select(Profile)
            .join(SessionModel, SessionModel.user_id == Profile.id)
            .where(
                SessionModel.company_id == company_id,
                Profile.phone.isnot(None),
                Profile.phone_verified == True,
            )
        )

        if active_only:
            stmt = stmt.where(SessionModel.is_active == True)

        stmt = stmt.distinct()

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_users_by_company(self, company_id: UUID) -> int:
        """
        Count total users for a company.

        Args:
            company_id: Company UUID

        Returns:
            Number of users (sessions)
        """
        result = await self.db.execute(
            select(func.count(SessionModel.id)).where(
                SessionModel.company_id == company_id
            )
        )
        return result.scalar_one() or 0

    async def count_users_batch(
        self,
        company_ids: List[UUID]
    ) -> dict[UUID, int]:
        """
        Count users for multiple companies in a single query.

        Args:
            company_ids: List of company UUIDs

        Returns:
            Dictionary mapping company_id to user count
        """
        stmt = (
            select(
                SessionModel.company_id,
                func.count(SessionModel.id).label('user_count')
            )
            .where(SessionModel.company_id.in_(company_ids))
            .group_by(SessionModel.company_id)
        )

        result = await self.db.execute(stmt)
        return {row.company_id: row.user_count for row in result.all()}

    async def get_last_activity_batch(
        self,
        company_ids: List[UUID]
    ) -> dict[UUID, Optional[datetime]]:
        """
        Get last activity timestamp for multiple companies.

        Args:
            company_ids: List of company UUIDs

        Returns:
            Dictionary mapping company_id to last activity datetime
        """
        stmt = (
            select(
                SessionModel.company_id,
                func.max(SessionModel.last_accessed_at).label('last_activity')
            )
            .where(SessionModel.company_id.in_(company_ids))
            .group_by(SessionModel.company_id)
        )

        result = await self.db.execute(stmt)
        return {row.company_id: row.last_activity for row in result.all()}

    async def delete_by_company(self, company_id: UUID) -> int:
        """
        Delete all sessions for a company.

        Args:
            company_id: Company UUID

        Returns:
            Number of sessions deleted
        """
        count = await self.count_users_by_company(company_id)

        # Delete all sessions for the company
        stmt = select(SessionModel).where(SessionModel.company_id == company_id)
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        for session in sessions:
            await self.db.delete(session)

        return count
