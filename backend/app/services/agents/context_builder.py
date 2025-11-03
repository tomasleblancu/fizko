"""
Context Builder - Prepares context for agent execution.

Handles loading and formatting of:
- Company information
- UI Tool context
- User information
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.core import load_company_info, format_company_context

logger = logging.getLogger(__name__)

# In-memory cache for company info (30 minute TTL)
_company_info_cache: Dict[str, tuple[datetime, Dict[str, Any]]] = {}
_CACHE_TTL_SECONDS = 1800  # 30 minutes


class ContextBuilder:
    """
    Builds context for agent execution.

    Handles caching and formatting of company information,
    UI tool context, and other contextual data.
    """

    @staticmethod
    async def load_company_context(
        db: AsyncSession,
        company_id: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Load company information with caching.

        Args:
            db: Database session
            company_id: Company UUID
            use_cache: Whether to use cache (default: True)

        Returns:
            Company info dict
        """
        cache_key = company_id

        # Check cache first
        if use_cache and cache_key in _company_info_cache:
            cached_time, cached_data = _company_info_cache[cache_key]
            cache_age = (datetime.now() - cached_time).total_seconds()

            if cache_age < _CACHE_TTL_SECONDS:
                logger.info(f"📋 Company info from cache ({cache_age:.0f}s old)")
                return cached_data
            else:
                del _company_info_cache[cache_key]

        # Load from database
        logger.info(f"🔍 Loading company info from DB...")
        company_info = await load_company_info(db, company_id)

        # Store in cache
        if use_cache:
            _company_info_cache[cache_key] = (datetime.now(), company_info)

        return company_info

    @staticmethod
    def format_company_context_text(company_info: Dict[str, Any]) -> str:
        """
        Format company info as context text for agent.

        Args:
            company_info: Company information dict

        Returns:
            Formatted context string
        """
        return format_company_context(company_info)

    @staticmethod
    async def load_ui_tool_context(
        db: AsyncSession,
        ui_component: Optional[str],
        entity_id: Optional[str],
        entity_type: Optional[str],
        user_id: str,
        company_id: str,
        user_message: str,
    ) -> Optional[str]:
        """
        Load UI Tool context if ui_component is provided.

        Args:
            db: Database session
            ui_component: UI component name (e.g., "tax_summary_card")
            entity_id: Entity ID (if applicable)
            entity_type: Entity type (if applicable)
            user_id: User ID
            company_id: Company ID
            user_message: User's message text

        Returns:
            UI context text or None
        """
        if not ui_component:
            return None

        try:
            from app.agents.ui_tools.core import UIToolDispatcher

            logger.info(f"🎯 Loading UI Tool context: {ui_component}")

            # Build additional_data dict
            additional_data = {}
            if entity_id:
                additional_data["entity_id"] = entity_id
            if entity_type:
                additional_data["entity_type"] = entity_type

            # Dispatch to UI Tool
            result = await UIToolDispatcher.dispatch(
                ui_component=ui_component,
                user_message=user_message,
                company_id=company_id,
                user_id=user_id,
                db=db,
                additional_data=additional_data if additional_data else None,
            )

            if result and result.success and result.context_text:
                logger.info(f"✅ UI Tool context loaded: {len(result.context_text)} chars")
                return result.context_text
            elif result and not result.success:
                logger.warning(f"⚠️ UI Tool failed: {result.error}")
                return None
            else:
                logger.warning(f"⚠️ UI Tool returned no result")
                return None

        except Exception as e:
            logger.error(f"❌ Error loading UI Tool context: {e}", exc_info=True)
            return None

    @staticmethod
    def clear_cache():
        """Clear company info cache."""
        global _company_info_cache
        _company_info_cache = {}
        logger.info("🧹 Company info cache cleared")
