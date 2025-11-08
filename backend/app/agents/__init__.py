"""Agents module for Fizko platform - Multi-Agent System with Handoffs."""

# Import legacy ChatKitServer for backward compatibility
from .chat import FizkoChatKitServer


def create_chatkit_server(use_new_adapter: bool = True):
    """
    Create the ChatKit server instance.

    Args:
        use_new_adapter: Use new ChatKitServerAdapter (default: True)
                        Set to False to use legacy FizkoChatKitServer

    Returns:
        ChatKitServerAdapter or FizkoChatKitServer instance
    """
    if use_new_adapter:
        # Import here to avoid circular dependency
        from app.integrations.chatkit import ChatKitServerAdapter
        return ChatKitServerAdapter()
    else:
        return FizkoChatKitServer()


# For backward compatibility, FizkoServer is an alias to FizkoChatKitServer
# This maintains the type annotation compatibility in main.py
# To use the new adapter, use create_chatkit_server() or ChatKitServerAdapter directly
FizkoServer = FizkoChatKitServer
LegacyFizkoServer = FizkoChatKitServer  # Keep explicit legacy alias

__all__ = [
    "FizkoServer",
    "FizkoChatKitServer",
    "LegacyFizkoServer",
    "create_chatkit_server",
]
