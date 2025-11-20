"""
Feedback Repository - Handles feedback/bug report queries.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class FeedbackRepository(BaseRepository):
    """Repository for feedback data access."""

    async def create(
        self,
        profile_id: str,
        category: str,
        priority: str,
        title: str,
        feedback: str,
        company_id: str | None = None,
        conversation_context: str | None = None,
        channel: str = "chatkit",
        thread_id: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Create a new feedback entry.

        Args:
            profile_id: User UUID
            category: Feedback category (bug, feature_request, etc.)
            priority: Priority level (low, medium, high, urgent)
            title: Short summary
            feedback: Detailed feedback content
            company_id: Optional company UUID
            conversation_context: Optional conversation context
            channel: Channel where feedback originated
            thread_id: Optional thread ID

        Returns:
            Created feedback dict or None if error
        """
        try:
            data = {
                "profile_id": profile_id,
                "company_id": company_id,
                "category": category,
                "priority": priority,
                "title": title,
                "feedback": feedback,
                "conversation_context": conversation_context,
                "channel": channel,
                "thread_id": thread_id,
                "status": "new",
            }

            response = (
                self._client
                .table("feedback")
                .insert(data)
                .execute()
            )

            return self._extract_data(response, "create_feedback")
        except Exception as e:
            self._log_error(
                "create_feedback",
                e,
                profile_id=profile_id,
                category=category
            )
            return None

    async def update(
        self,
        feedback_id: str,
        **kwargs
    ) -> dict[str, Any] | None:
        """
        Update a feedback entry.

        Args:
            feedback_id: Feedback UUID
            **kwargs: Fields to update

        Returns:
            Updated feedback dict or None if error
        """
        try:
            response = (
                self._client
                .table("feedback")
                .update(kwargs)
                .eq("id", feedback_id)
                .execute()
            )

            return self._extract_data(response, "update_feedback")
        except Exception as e:
            self._log_error("update_feedback", e, feedback_id=feedback_id)
            return None

    async def get_by_id(
        self,
        feedback_id: str,
        profile_id: str | None = None
    ) -> dict[str, Any] | None:
        """
        Get feedback by ID.

        Args:
            feedback_id: Feedback UUID
            profile_id: Optional profile UUID to verify ownership

        Returns:
            Feedback dict or None if not found
        """
        try:
            query = (
                self._client
                .table("feedback")
                .select("*")
                .eq("id", feedback_id)
            )

            if profile_id:
                query = query.eq("profile_id", profile_id)

            response = query.maybe_single().execute()
            return self._extract_data(response, "get_feedback_by_id")
        except Exception as e:
            self._log_error("get_feedback_by_id", e, feedback_id=feedback_id)
            return None

    async def list_by_profile(
        self,
        profile_id: str,
        status: str | None = None,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        List feedback for a profile.

        Args:
            profile_id: Profile UUID
            status: Optional status filter
            limit: Maximum number of feedback

        Returns:
            List of feedback dicts
        """
        try:
            query = (
                self._client
                .table("feedback")
                .select("*")
                .eq("profile_id", profile_id)
            )

            if status:
                query = query.eq("status", status)

            query = query.order("created_at", desc=True).limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "list_feedback_by_profile")
        except Exception as e:
            self._log_error(
                "list_feedback_by_profile",
                e,
                profile_id=profile_id,
                status=status
            )
            return []
