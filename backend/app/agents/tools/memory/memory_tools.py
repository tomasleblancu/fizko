"""Memory tools for agent using Mem0 for context and history.

This module provides dual memory systems:
1. User Memory - Personal preferences and information specific to each user
2. Company Memory - Shared knowledge and information across the company

Each memory type is stored separately in Mem0 using different entity IDs.
"""

import asyncio
import logging
import os
from typing import Optional, Literal

from agents import function_tool, RunContextWrapper
from mem0 import AsyncMemoryClient

from app.agents.core import FizkoContext

logger = logging.getLogger(__name__)

# Global Mem0 async client (initialized lazily)
_mem0_client: Optional[AsyncMemoryClient] = None
_mem0_client_loop: Optional[asyncio.AbstractEventLoop] = None

# Memory entity types
MemoryEntityType = Literal["user", "company"]


def get_mem0_client() -> AsyncMemoryClient:
    """
    Get or create async Mem0 client.

    Detects if event loop has changed (e.g., in Celery tasks) and recreates
    the client if needed to avoid "Event loop is closed" errors.
    """
    global _mem0_client, _mem0_client_loop

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - will be created when needed
        current_loop = None

    # Recreate client if loop changed or client doesn't exist
    if _mem0_client is None or _mem0_client_loop != current_loop:
        api_key = os.getenv("MEM0_API_KEY")
        if not api_key:
            raise ValueError("MEM0_API_KEY environment variable not set")

        # Initialize Mem0 async client with API key
        _mem0_client = AsyncMemoryClient(api_key=api_key)
        _mem0_client_loop = current_loop

        if current_loop:
            logger.info(f"✨ Mem0 async client initialized for event loop {id(current_loop)}")
        else:
            logger.info("✨ Mem0 async client initialized")

    return _mem0_client


# ============================================================================
# USER MEMORY TOOLS - Personal user preferences and information
# ============================================================================

@function_tool
async def search_user_memory(
    context: RunContextWrapper[FizkoContext],
    query: str,
    limit: int = 3
) -> str:
    """
    Search through the USER'S personal memory and past conversations.

    Use this tool to recall PERSONAL information about the user:
    - User's personal preferences (e.g., "prefers short answers", "likes detailed explanations")
    - User's past personal decisions (e.g., "wants to file F29 monthly")
    - Personal context from past conversations
    - Information specific to THIS USER (not shared with company)

    Args:
        query: The search query (e.g., "user's communication preference", "user's filing schedule")
        limit: Maximum number of memories to return (default 3)

    Returns:
        Formatted string with relevant user memories, or "No relevant user memories found."
    """
    try:
        mem0 = get_mem0_client()

        # Get user_id from context
        user_id = context.context.request_context.get("user_id", "anonymous")

        logger.info(f"🔍 Searching USER memory: query='{query}', user_id={user_id}, limit={limit}")

        # Search user memories using async client with required filters
        # Use user_id directly for personal memory
        result = await mem0.search(
            query,  # Positional argument
            user_id=user_id,
            filters={"user_id": user_id}  # Required: filters cannot be empty
        )

        if result and result.get('results'):
            memories = result['results']
            logger.info(f"✅ Found {len(memories)} relevant user memories")

            # Format memories as bullet points
            formatted_memories = "\n".join([
                f"- {mem['memory']}" for mem in memories
            ])
            return formatted_memories
        else:
            logger.info("ℹ️ No relevant user memories found")
            return "No relevant user memories found."

    except Exception as e:
        # Handle 400 Bad Request gracefully (happens when no memories exist yet)
        error_msg = str(e)
        if "400" in error_msg or "Bad Request" in error_msg:
            logger.info("ℹ️ No user memories found (empty database)")
            return "No relevant user memories found."
        else:
            logger.error(f"❌ Error searching user memory: {e}", exc_info=True)
            return f"Error searching user memory: {str(e)}"


@function_tool
async def save_user_memory(
    context: RunContextWrapper[FizkoContext],
    content: str
) -> str:
    """
    Save important information to the USER'S personal long-term memory.

    Use this tool to store PERSONAL information about the user:
    - User's personal preferences (e.g., "User prefers short, concise answers")
    - User's personal decisions (e.g., "User wants to receive reminders 3 days before deadlines")
    - Personal context for future conversations
    - Information specific to THIS USER (not company-wide)

    Args:
        content: The information to save (be specific and descriptive)

    Returns:
        Confirmation message or error
    """
    try:
        mem0 = get_mem0_client()

        # Get user_id from context
        user_id = context.context.request_context.get("user_id", "anonymous")

        logger.info(f"💾 Saving USER memory: user_id={user_id}, content='{content[:100]}...'")

        # Save memory using async client (Mem0 expects a list of message-like dicts)
        await mem0.add(
            messages=[{"role": "user", "content": content}],
            user_id=user_id
        )

        logger.info("✅ User memory saved successfully")
        return "Information saved to user memory."

    except Exception as e:
        logger.error(f"❌ Error saving user memory: {e}", exc_info=True)
        return f"Error saving user memory: {str(e)}"


# ============================================================================
# COMPANY MEMORY TOOLS - Shared company knowledge and information
# ============================================================================

@function_tool
async def search_company_memory(
    context: RunContextWrapper[FizkoContext],
    query: str,
    limit: int = 3
) -> str:
    """
    Search through the COMPANY'S shared memory and knowledge base.

    Use this tool to recall COMPANY-WIDE information:
    - Company's tax regime and settings (e.g., "Company is on ProPyme regime")
    - Company policies and decisions (e.g., "Uses monthly IVA filing")
    - Shared business context (e.g., "Company changed accountant in Q2 2024")
    - Information that applies to ALL users in the company

    Args:
        query: The search query (e.g., "company's tax regime", "accounting policies")
        limit: Maximum number of memories to return (default 3)

    Returns:
        Formatted string with relevant company memories, or "No relevant company memories found."
    """
    try:
        mem0 = get_mem0_client()

        # Get company_id from request_context (via context.context)
        company_id = context.context.request_context.get("company_id")

        if not company_id:
            logger.warning("⚠️ No company_id in request_context, cannot search company memory")
            return "No company context available."

        # Use company_id prefixed with 'company_' to distinguish from user IDs
        entity_id = f"company_{company_id}"

        logger.info(f"🔍 Searching COMPANY memory: query='{query}', company_id={company_id}, limit={limit}")

        # Search company memories using async client
        # Use company_id as the user_id (Mem0's entity identifier)
        result = await mem0.search(
            query,  # Positional argument
            user_id=entity_id,
            filters={"user_id": entity_id}  # Required: filters cannot be empty
        )

        if result and result.get('results'):
            memories = result['results']
            logger.info(f"✅ Found {len(memories)} relevant company memories")

            # Format memories as bullet points
            formatted_memories = "\n".join([
                f"- {mem['memory']}" for mem in memories
            ])
            return formatted_memories
        else:
            logger.info("ℹ️ No relevant company memories found")
            return "No relevant company memories found."

    except Exception as e:
        # Handle 400 Bad Request gracefully (happens when no memories exist yet)
        error_msg = str(e)
        if "400" in error_msg or "Bad Request" in error_msg:
            logger.info("ℹ️ No company memories found (empty database)")
            return "No relevant company memories found."
        else:
            logger.error(f"❌ Error searching company memory: {e}", exc_info=True)
            return f"Error searching company memory: {str(e)}"


@function_tool
async def save_company_memory(
    context: RunContextWrapper[FizkoContext],
    content: str
) -> str:
    """
    Save important information to the COMPANY'S shared long-term memory.

    Use this tool to store COMPANY-WIDE information:
    - Company's tax regime and settings (e.g., "Company is on ProPyme regime")
    - Company policies (e.g., "Company files IVA monthly")
    - Business context (e.g., "Company started operations in January 2023")
    - Information that should be accessible to ALL users in the company

    Args:
        content: The information to save (be specific and descriptive)

    Returns:
        Confirmation message or error
    """
    try:
        mem0 = get_mem0_client()

        # Get company_id from request_context (via context.context)
        company_id = context.context.request_context.get("company_id")

        if not company_id:
            logger.warning("⚠️ No company_id in request_context, cannot save company memory")
            return "No company context available. Cannot save company memory."

        # Use company_id prefixed with 'company_' to distinguish from user IDs
        entity_id = f"company_{company_id}"

        logger.info(f"💾 Saving COMPANY memory: company_id={company_id}, content='{content[:100]}...'")

        # Save memory using async client (Mem0 expects a list of message-like dicts)
        await mem0.add(
            messages=[{"role": "user", "content": content}],
            user_id=entity_id
        )

        logger.info("✅ Company memory saved successfully")
        return "Information saved to company memory."

    except Exception as e:
        logger.error(f"❌ Error saving company memory: {e}", exc_info=True)
        return f"Error saving company memory: {str(e)}"


# ============================================================================
# LEGACY COMPATIBILITY - Keep old function names for backward compatibility
# ============================================================================

@function_tool
async def search_memory(
    context: RunContextWrapper[FizkoContext],
    query: str,
    limit: int = 3
) -> str:
    """
    [DEPRECATED] Search through memories. Use search_user_memory or search_company_memory instead.

    This function defaults to searching user memory for backward compatibility.
    """
    logger.warning("⚠️ Using deprecated search_memory. Use search_user_memory or search_company_memory instead.")
    return await search_user_memory(context, query, limit)


@function_tool
async def save_memory(
    context: RunContextWrapper[FizkoContext],
    content: str
) -> str:
    """
    [DEPRECATED] Save information to memory. Use save_user_memory or save_company_memory instead.

    This function defaults to saving to user memory for backward compatibility.
    """
    logger.warning("⚠️ Using deprecated save_memory. Use save_user_memory or save_company_memory instead.")
    return await save_user_memory(context, content)
