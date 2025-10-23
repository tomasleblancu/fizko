"""Agents module for Fizko platform - Unified Agent System."""

from .chat import FizkoChatKitServer


def create_chatkit_server():
    """Create the ChatKit server instance."""
    return FizkoChatKitServer()


# Alias for backward compatibility
FizkoServer = FizkoChatKitServer

__all__ = [
    "FizkoServer",
    "FizkoChatKitServer",
    "create_chatkit_server",
]
