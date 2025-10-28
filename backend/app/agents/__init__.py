"""Agents module for Fizko platform - Multi-Agent System with Handoffs."""

from .chat import FizkoChatKitServer


def create_chatkit_server(mode: str = "multi_agent"):
    """
    Create the ChatKit server instance.

    Args:
        mode: "unified" (single agent) or "multi_agent" (handoffs system)
              Default: "multi_agent"

    Returns:
        FizkoChatKitServer instance
    """
    return FizkoChatKitServer(mode=mode)


# Alias for backward compatibility
FizkoServer = FizkoChatKitServer

__all__ = [
    "FizkoServer",
    "FizkoChatKitServer",
    "create_chatkit_server",
]
