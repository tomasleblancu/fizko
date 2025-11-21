"""
Brain Repository - Manages UserBrain and CompanyBrain records.

These repositories track memories stored in Mem0, enabling:
1. Update existing memories instead of creating duplicates
2. Query and manage memories from the database
3. Track memory metadata and slugs for organized retrieval
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class UserBrainRepository(BaseRepository):
    """
    Repository for UserBrain model operations.

    Provides methods to manage user memory records including
    slug-based lookups and updates.
    """

    async def get_by_user_and_slug(
        self, user_id: str, slug: str
    ) -> dict[str, Any] | None:
        """
        Get a user brain record by user_id and slug.

        Args:
            user_id: User UUID
            slug: Memory slug identifier

        Returns:
            UserBrain record or None if not found
        """
        try:
            response = (
                self._client
                .table("user_brain")
                .select("*")
                .eq("user_id", user_id)
                .eq("slug", slug)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_by_user_and_slug")
        except Exception as e:
            self._log_error("get_by_user_and_slug", e, user_id=user_id, slug=slug)
            return None

    async def get_by_memory_id(self, memory_id: str) -> dict[str, Any] | None:
        """
        Get a user brain record by Mem0 memory_id.

        Args:
            memory_id: Mem0 memory identifier

        Returns:
            UserBrain record or None if not found
        """
        try:
            response = (
                self._client
                .table("user_brain")
                .select("*")
                .eq("memory_id", memory_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_by_memory_id")
        except Exception as e:
            self._log_error("get_by_memory_id", e, memory_id=memory_id)
            return None

    async def get_all_by_user(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get all brain records for a specific user.

        Args:
            user_id: User UUID

        Returns:
            List of UserBrain records
        """
        try:
            response = (
                self._client
                .table("user_brain")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return self._extract_data_list(response, "get_all_by_user")
        except Exception as e:
            self._log_error("get_all_by_user", e, user_id=user_id)
            return []

    async def create(
        self,
        user_id: str,
        memory_id: str,
        slug: str,
        content: str,
        extra_metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """
        Create a new user brain record.

        Args:
            user_id: User UUID
            memory_id: Mem0 memory ID
            slug: Memory slug identifier
            content: Memory content
            extra_metadata: Optional metadata (e.g., {"category": "user_profile"})

        Returns:
            Created UserBrain record or None if failed
        """
        try:
            data = {
                "user_id": user_id,
                "memory_id": memory_id,
                "slug": slug,
                "content": content,
                "extra_metadata": extra_metadata or {}
            }
            response = (
                self._client
                .table("user_brain")
                .insert(data)
                .execute()
            )
            return self._extract_data(response, "create")
        except Exception as e:
            self._log_error("create", e, user_id=user_id, slug=slug)
            return None

    async def update(
        self,
        id: str,
        content: str | None = None,
        memory_id: str | None = None,
        extra_metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """
        Update an existing user brain record.

        Args:
            id: UserBrain record ID
            content: New content (optional)
            memory_id: New memory_id (optional, for recreating deleted memories)
            extra_metadata: New metadata (optional)

        Returns:
            Updated UserBrain record or None if failed
        """
        try:
            update_data: dict[str, Any] = {}
            if content is not None:
                update_data["content"] = content
            if memory_id is not None:
                update_data["memory_id"] = memory_id
            if extra_metadata is not None:
                update_data["extra_metadata"] = extra_metadata

            if not update_data:
                logger.warning("No fields to update")
                return None

            response = (
                self._client
                .table("user_brain")
                .update(update_data)
                .eq("id", id)
                .execute()
            )
            return self._extract_data(response, "update")
        except Exception as e:
            self._log_error("update", e, id=id)
            return None

    async def delete_all_by_user(self, user_id: str) -> int:
        """
        Delete all brain records for a specific user.

        Args:
            user_id: User UUID

        Returns:
            Number of deleted records
        """
        try:
            response = (
                self._client
                .table("user_brain")
                .delete()
                .eq("user_id", user_id)
                .execute()
            )
            data = self._extract_data_list(response, "delete_all_by_user")
            return len(data)
        except Exception as e:
            self._log_error("delete_all_by_user", e, user_id=user_id)
            return 0


class CompanyBrainRepository(BaseRepository):
    """
    Repository for CompanyBrain model operations.

    Provides methods to manage company memory records including
    slug-based lookups and updates.
    """

    async def get_by_company_and_slug(
        self, company_id: str, slug: str
    ) -> dict[str, Any] | None:
        """
        Get a company brain record by company_id and slug.

        Args:
            company_id: Company UUID
            slug: Memory slug identifier

        Returns:
            CompanyBrain record or None if not found
        """
        try:
            response = (
                self._client
                .table("company_brain")
                .select("*")
                .eq("company_id", company_id)
                .eq("slug", slug)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_by_company_and_slug")
        except Exception as e:
            self._log_error("get_by_company_and_slug", e, company_id=company_id, slug=slug)
            return None

    async def get_by_memory_id(self, memory_id: str) -> dict[str, Any] | None:
        """
        Get a company brain record by Mem0 memory_id.

        Args:
            memory_id: Mem0 memory identifier

        Returns:
            CompanyBrain record or None if not found
        """
        try:
            response = (
                self._client
                .table("company_brain")
                .select("*")
                .eq("memory_id", memory_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_by_memory_id")
        except Exception as e:
            self._log_error("get_by_memory_id", e, memory_id=memory_id)
            return None

    async def get_all_by_company(self, company_id: str) -> list[dict[str, Any]]:
        """
        Get all brain records for a specific company.

        Args:
            company_id: Company UUID

        Returns:
            List of CompanyBrain records
        """
        try:
            response = (
                self._client
                .table("company_brain")
                .select("*")
                .eq("company_id", company_id)
                .order("created_at", desc=True)
                .execute()
            )
            return self._extract_data_list(response, "get_all_by_company")
        except Exception as e:
            self._log_error("get_all_by_company", e, company_id=company_id)
            return []

    async def create(
        self,
        company_id: str,
        memory_id: str,
        slug: str,
        content: str,
        extra_metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """
        Create a new company brain record.

        Args:
            company_id: Company UUID
            memory_id: Mem0 memory ID
            slug: Memory slug identifier
            content: Memory content
            extra_metadata: Optional metadata (e.g., {"category": "company_tax"})

        Returns:
            Created CompanyBrain record or None if failed
        """
        try:
            data = {
                "company_id": company_id,
                "memory_id": memory_id,
                "slug": slug,
                "content": content,
                "extra_metadata": extra_metadata or {}
            }
            response = (
                self._client
                .table("company_brain")
                .insert(data)
                .execute()
            )
            return self._extract_data(response, "create")
        except Exception as e:
            self._log_error("create", e, company_id=company_id, slug=slug)
            return None

    async def update(
        self,
        id: str,
        content: str | None = None,
        memory_id: str | None = None,
        extra_metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """
        Update an existing company brain record.

        Args:
            id: CompanyBrain record ID
            content: New content (optional)
            memory_id: New memory_id (optional, for recreating deleted memories)
            extra_metadata: New metadata (optional)

        Returns:
            Updated CompanyBrain record or None if failed
        """
        try:
            update_data: dict[str, Any] = {}
            if content is not None:
                update_data["content"] = content
            if memory_id is not None:
                update_data["memory_id"] = memory_id
            if extra_metadata is not None:
                update_data["extra_metadata"] = extra_metadata

            if not update_data:
                logger.warning("No fields to update")
                return None

            response = (
                self._client
                .table("company_brain")
                .update(update_data)
                .eq("id", id)
                .execute()
            )
            return self._extract_data(response, "update")
        except Exception as e:
            self._log_error("update", e, id=id)
            return None

    async def delete_all_by_company(self, company_id: str) -> int:
        """
        Delete all brain records for a specific company.

        Args:
            company_id: Company UUID

        Returns:
            Number of deleted records
        """
        try:
            response = (
                self._client
                .table("company_brain")
                .delete()
                .eq("company_id", company_id)
                .execute()
            )
            data = self._extract_data_list(response, "delete_all_by_company")
            return len(data)
        except Exception as e:
            self._log_error("delete_all_by_company", e, company_id=company_id)
            return 0
