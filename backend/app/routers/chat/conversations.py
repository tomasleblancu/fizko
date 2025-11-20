"""
Conversations Router - In-Memory Implementation for Backend V2.

Provides conversation management WITHOUT database persistence.
Conversations are stored in memory and lost on restart.

This is a simplified version for demonstration and testing purposes.
For production use with persistence, consider:
- External state management (Redis, etc.)
- Client-side conversation storage
- Migrate to full backend with database
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


# ============================================================================
# In-Memory Storage (lost on restart)
# ============================================================================

# Structure: {conversation_id: ConversationData}
_conversations_store: Dict[str, "ConversationData"] = {}


# ============================================================================
# Models
# ============================================================================

class MessageData(BaseModel):
    """Message data model."""
    id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: str


class ConversationData(BaseModel):
    """Conversation data model."""
    id: str
    user_id: str
    company_id: Optional[str] = None
    title: Optional[str] = None
    messages: List[MessageData] = Field(default_factory=list)
    metadata: Optional[Dict] = None
    created_at: str
    updated_at: str


class CreateConversationRequest(BaseModel):
    """Request to create a conversation."""
    user_id: str = Field(..., description="User identifier")
    company_id: Optional[str] = Field(None, description="Company RUT")
    title: Optional[str] = Field(None, description="Conversation title")
    metadata: Optional[Dict] = Field(None, description="Additional metadata")


class AddMessageRequest(BaseModel):
    """Request to add a message to a conversation."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation(request: CreateConversationRequest):
    """
    Create a new conversation (in-memory).

    **Note**: Conversations are stored in memory and will be lost on server restart.

    Example:
        ```python
        response = requests.post("/api/conversations", json={
            "user_id": "user_123",
            "company_id": "77794858-k",
            "title": "Consultas tributarias Enero 2025"
        })
        conversation_id = response.json()["data"]["id"]
        ```
    """
    conversation_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    conversation = ConversationData(
        id=conversation_id,
        user_id=request.user_id,
        company_id=request.company_id,
        title=request.title or f"Conversation {conversation_id[:8]}",
        messages=[],
        metadata=request.metadata,
        created_at=now,
        updated_at=now,
    )

    _conversations_store[conversation_id] = conversation

    logger.info(f"✅ Created conversation {conversation_id} for user {request.user_id}")

    return {
        "data": conversation.model_dump(),
        "message": "Conversation created successfully (in-memory)"
    }


@router.get("")
async def list_conversations(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    skip: int = Query(0, ge=0, description="Skip N conversations"),
    limit: int = Query(50, ge=1, le=100, description="Max conversations to return"),
):
    """
    List conversations (in-memory).

    Supports filtering by user_id and company_id.

    **Note**: Only returns conversations from current server session.

    Example:
        ```python
        response = requests.get("/api/conversations?user_id=user_123&limit=10")
        conversations = response.json()["data"]
        ```
    """
    # Filter conversations
    conversations = list(_conversations_store.values())

    if user_id:
        conversations = [c for c in conversations if c.user_id == user_id]

    if company_id:
        conversations = [c for c in conversations if c.company_id == company_id]

    # Sort by updated_at (most recent first)
    conversations.sort(key=lambda c: c.updated_at, reverse=True)

    # Pagination
    total = len(conversations)
    conversations = conversations[skip:skip + limit]

    return {
        "data": [c.model_dump() for c in conversations],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total,
        }
    }


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get a conversation by ID (in-memory).

    Returns the conversation with all messages.

    Example:
        ```python
        response = requests.get(f"/api/conversations/{conversation_id}")
        conversation = response.json()["data"]
        messages = conversation["messages"]
        ```
    """
    conversation = _conversations_store.get(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found (may have been lost on server restart)"
        )

    return {"data": conversation.model_dump()}


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def add_message(conversation_id: str, request: AddMessageRequest):
    """
    Add a message to a conversation (in-memory).

    Example:
        ```python
        # Add user message
        requests.post(f"/api/conversations/{conversation_id}/messages", json={
            "role": "user",
            "content": "¿Qué es el IVA?"
        })

        # Add assistant response
        requests.post(f"/api/conversations/{conversation_id}/messages", json={
            "role": "assistant",
            "content": "El IVA es el Impuesto al Valor Agregado..."
        })
        ```
    """
    conversation = _conversations_store.get(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    message = MessageData(
        id=str(uuid4()),
        role=request.role,
        content=request.content,
        created_at=datetime.utcnow().isoformat(),
    )

    conversation.messages.append(message)
    conversation.updated_at = datetime.utcnow().isoformat()

    logger.info(f"✅ Added {request.role} message to conversation {conversation_id}")

    return {
        "data": message.model_dump(),
        "message": "Message added successfully"
    }


@router.get("/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    skip: int = Query(0, ge=0, description="Skip N messages"),
    limit: int = Query(100, ge=1, le=200, description="Max messages to return"),
):
    """
    Get messages for a conversation (in-memory).

    Returns messages in chronological order.

    Example:
        ```python
        response = requests.get(f"/api/conversations/{conversation_id}/messages")
        messages = response.json()["data"]
        ```
    """
    conversation = _conversations_store.get(conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    # Pagination
    total = len(conversation.messages)
    messages = conversation.messages[skip:skip + limit]

    return {
        "data": [m.model_dump() for m in messages],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total,
        }
    }


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation (in-memory).

    Example:
        ```python
        requests.delete(f"/api/conversations/{conversation_id}")
        ```
    """
    if conversation_id not in _conversations_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    del _conversations_store[conversation_id]
    logger.info(f"🗑️  Deleted conversation {conversation_id}")

    return None


@router.get("/stats/summary")
async def get_stats():
    """
    Get conversation statistics (in-memory).

    Returns summary stats about current conversations.

    Example:
        ```python
        response = requests.get("/api/conversations/stats/summary")
        stats = response.json()["data"]
        print(f"Total conversations: {stats['total_conversations']}")
        ```
    """
    total_conversations = len(_conversations_store)
    total_messages = sum(len(c.messages) for c in _conversations_store.values())

    unique_users = len(set(c.user_id for c in _conversations_store.values()))
    unique_companies = len(set(c.company_id for c in _conversations_store.values() if c.company_id))

    return {
        "data": {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "unique_users": unique_users,
            "unique_companies": unique_companies,
            "storage": "in-memory (volatile)",
        }
    }


@router.post("/clear", status_code=status.HTTP_200_OK)
async def clear_all_conversations():
    """
    Clear all conversations from memory.

    **Warning**: This deletes ALL conversations permanently.
    Use only for testing/development.

    Example:
        ```python
        requests.post("/api/conversations/clear")
        ```
    """
    count = len(_conversations_store)
    _conversations_store.clear()

    logger.warning(f"⚠️  Cleared all {count} conversations from memory")

    return {
        "message": f"Cleared {count} conversations from memory",
        "warning": "All conversation data has been permanently deleted"
    }
