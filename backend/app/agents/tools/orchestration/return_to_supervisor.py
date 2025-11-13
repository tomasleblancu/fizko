"""Tool for agents to return to supervisor and clear active agent state."""

import logging
from typing import Any

from agents import RunContextWrapper, function_tool

from ...core.context import FizkoContext

logger = logging.getLogger(__name__)


@function_tool
async def return_to_supervisor(
    ctx: RunContextWrapper[FizkoContext],
    reason: str = "User requested topic change"
) -> dict[str, Any]:
    """
    Return to supervisor agent and clear active agent state.

    Use this tool when:
    - User explicitly asks to return to main menu or change topics
    - Conversation naturally ends and user wants to discuss something else
    - Current agent cannot help with the new user request

    Args:
        reason: Explanation for why returning to supervisor

    Returns:
        dict with success status and message

    Example:
        User: "Gracias, ahora quiero ver mis facturas"
        Agent: Calls return_to_supervisor(reason="User wants to see invoices")
    """

    try:
        # Access FizkoContext from RunContextWrapper
        context: FizkoContext = ctx.context

        # Get thread_id from context
        thread_id = context.request_context.get("thread_id")

        if not thread_id:
            logger.warning("⚠️ [RETURN TO SUPERVISOR] No thread_id in context")
            return {
                "success": False,
                "message": "Could not identify conversation thread"
            }

        # Get orchestrator from handoffs_manager
        from ...orchestration import handoffs_manager

        orchestrator = handoffs_manager._orchestrators.get(thread_id)

        if not orchestrator:
            logger.warning(f"⚠️ [RETURN TO SUPERVISOR] No orchestrator for thread {thread_id[:12]}...")
            return {
                "success": False,
                "message": "Could not find conversation state"
            }

        # Get session manager from orchestrator
        session_manager = orchestrator.session_manager

        if not session_manager:
            logger.warning(f"⚠️ [RETURN TO SUPERVISOR] No session manager for thread {thread_id[:12]}...")
            return {
                "success": False,
                "message": "Session management not available"
            }

        # Clear active agent
        await session_manager.clear_active_agent(thread_id)

        logger.info(
            f"🔄 [RETURN TO SUPERVISOR] Agent returned to supervisor | "
            f"Reason: {reason} | "
            f"Thread: {thread_id[:12]}..."
        )

        return {
            "success": True,
            "message": f"Returned to supervisor. Reason: {reason}",
            "action": "transfer_to_supervisor"
        }

    except Exception as e:
        logger.exception(f"❌ [RETURN TO SUPERVISOR] Error: {e}")
        return {
            "success": False,
            "message": f"Error returning to supervisor: {str(e)}"
        }
