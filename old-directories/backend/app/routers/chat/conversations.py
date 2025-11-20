"""REST API endpoints for conversations resource."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...config.database import get_db
from ...db.models import Conversation, Message
from ...dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/conversations",
    tags=["conversations"],
    dependencies=[Depends(require_auth)]
)


@router.get("")
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    user_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a list of conversations with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by conversation status (active, archived, completed)
    - **user_id**: Filter by user ID
    """
    query = select(Conversation).options(selectinload(Conversation.messages))

    if status:
        query = query.where(Conversation.status == status)
    if user_id:
        query = query.where(Conversation.user_id == user_id)

    query = query.offset(skip).limit(limit).order_by(Conversation.updated_at.desc())

    result = await db.execute(query)
    conversations = result.scalars().all()

    return {
        "data": [
            {
                "id": str(c.id),
                "user_id": str(c.user_id),
                "chatkit_session_id": c.chatkit_session_id,
                "title": c.title,
                "status": c.status,
                "message_count": len(c.messages),
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in conversations
        ],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": len(conversations),
        }
    }


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single conversation by ID with all messages.
    """
    query = select(Conversation).options(
        selectinload(Conversation.messages)
    ).where(Conversation.id == conversation_id)

    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "data": {
            "id": str(conversation.id),
            "user_id": str(conversation.user_id),
            "chatkit_session_id": conversation.chatkit_session_id,
            "title": conversation.title,
            "status": conversation.status,
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "metadata": m.message_metadata,
                    "created_at": m.created_at.isoformat(),
                }
                for m in sorted(conversation.messages, key=lambda x: x.created_at)
            ],
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }
    }


@router.get("/{conversation_id}/messages")
async def list_conversation_messages(
    conversation_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Get messages for a specific conversation with pagination.
    """
    # First check if conversation exists
    conv_query = select(Conversation).where(Conversation.id == conversation_id)
    conv_result = await db.execute(conv_query)
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    query = select(Message).where(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).offset(skip).limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    return {
        "data": [
            {
                "id": str(m.id),
                "conversation_id": str(m.conversation_id),
                "user_id": str(m.user_id),
                "role": m.role,
                "content": m.content,
                "metadata": m.message_metadata,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": len(messages),
        }
    }
