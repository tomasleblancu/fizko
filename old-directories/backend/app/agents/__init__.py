"""Agents module for Fizko platform - Multi-Agent System with Handoffs."""


def create_chatkit_server():
    """
    Create the ChatKit server instance.

    Returns:
        ChatKitServerAdapter instance
    """
    from app.integrations.chatkit import ChatKitServerAdapter
    return ChatKitServerAdapter()


__all__ = [
    "create_chatkit_server",
]
