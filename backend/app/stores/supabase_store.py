"""Supabase-backed store implementation for ChatKit using SQLAlchemy ORM."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from chatkit.store import NotFoundError, Store
from chatkit.types import Attachment, Page, Thread, ThreadItem, ThreadMetadata
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import AsyncSessionLocal
from ..db.models import ChatKitAttachment, Conversation, Message

logger = logging.getLogger(__name__)


def _serialize_for_json(obj: Any) -> Any:
    """Convert objects to JSON-serializable format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    # Handle Pydantic AnyUrl (convert to string)
    elif hasattr(obj, "__class__") and obj.__class__.__name__ == "AnyUrl":
        return str(obj)
    return obj


class SupabaseStore(Store[dict[str, Any]]):
    """Supabase-backed store using SQLAlchemy ORM compatible with ChatKit."""

    def __init__(self) -> None:
        """Initialize the store."""
        pass

    async def _get_session(self) -> AsyncSession:
        """Get a new database session."""
        return AsyncSessionLocal()

    @staticmethod
    def _coerce_thread_metadata(thread: ThreadMetadata | Thread) -> ThreadMetadata:
        """Return thread metadata without any embedded items (openai-chatkit>=1.0)."""
        has_items = isinstance(thread, Thread) or "items" in getattr(
            thread, "model_fields_set", set()
        )
        if not has_items:
            return thread.model_copy(deep=True)

        data = thread.model_dump()
        data.pop("items", None)
        return ThreadMetadata(**data).model_copy(deep=True)

    # -- Thread metadata -------------------------------------------------
    async def load_thread(self, thread_id: str, context: dict[str, Any]) -> ThreadMetadata:
        """Load a conversation thread from Supabase."""
        import time
        load_start = time.time()

        user_id = context.get("user_id")
        if not user_id:
            raise ValueError("user_id is required in context")

        query_start = time.time()
        async with await self._get_session() as session:
            stmt = select(Conversation).where(
                Conversation.chatkit_session_id == thread_id,
                Conversation.user_id == UUID(user_id),
            )
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()

        logger.info(f"  🔍 load_thread() query: {(time.time() - query_start):.3f}s")

        if not conversation:
            logger.warning(f"  ⚠️ load_thread() - Thread {thread_id} not found")
            raise NotFoundError(f"Thread {thread_id} not found")

        # Merge conversation metadata (includes active_agent) with system fields
        # Ensure meta_data is a dict (handle None or other types)
        meta_dict = conversation.meta_data if isinstance(conversation.meta_data, dict) else {}
        meta_dict.update({
            "conversation_id": str(conversation.id),
            "title": conversation.title,
            "status": conversation.status,
        })

        result = ThreadMetadata(
            id=thread_id,
            created_at=conversation.created_at,
            metadata=meta_dict,
        )

        logger.info(f"  ✅ load_thread() completed: {(time.time() - load_start):.3f}s")
        return result

    async def save_thread(self, thread: ThreadMetadata, context: dict[str, Any]) -> None:
        """Save or update a conversation thread in Supabase."""
        import time
        save_start = time.time()

        user_id = context.get("user_id")
        if not user_id:
            raise ValueError("user_id is required in context")

        metadata = self._coerce_thread_metadata(thread)

        async with await self._get_session() as session:
            # Check if conversation exists
            stmt = select(Conversation).where(
                Conversation.chatkit_session_id == thread.id,
                Conversation.user_id == UUID(user_id),
            ).with_for_update()  # Lock row to prevent race conditions
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            # Simplified title logic (no LLM generation)
            if thread.metadata and "title" in thread.metadata and thread.metadata["title"] != "Nueva conversación":
                # Use explicit title from metadata if provided
                title = thread.metadata["title"]
            elif existing:
                # Keep existing title
                title = existing.title
            else:
                # Default for new conversations
                title = "Nueva conversación"

            status = (thread.metadata.get("status") if thread.metadata else None) or "active"

            # Extract metadata fields to persist (active_agent, etc.)
            persistent_metadata = {}
            if thread.metadata:
                # Save active_agent if present
                if "active_agent" in thread.metadata:
                    persistent_metadata["active_agent"] = thread.metadata["active_agent"]

            if existing:
                # Update existing conversation
                # Always update title if it's more descriptive than current
                if title and (
                    title != "Nueva conversación" or
                    existing.title == "Nueva conversación"
                ):
                    existing.title = title
                if status and status != "active":
                    existing.status = status
                # Always update metadata to capture active_agent changes
                existing.meta_data = persistent_metadata
                existing.updated_at = datetime.now()
            else:
                # Create new conversation with conflict handling
                try:
                    new_conversation = Conversation(
                        user_id=UUID(user_id),
                        chatkit_session_id=thread.id,
                        title=title,
                        status=status,
                        meta_data=persistent_metadata,
                    )
                    session.add(new_conversation)
                    await session.flush()  # Flush to catch unique violations before commit
                except Exception as e:
                    # If unique violation, another task created it - that's OK
                    if "UniqueViolationError" in str(type(e).__name__) or "unique constraint" in str(e).lower():
                        logger.debug(f"  ℹ️  Conversation {thread.id[:12]} already exists (created by another task)")
                        await session.rollback()
                        return
                    raise

            await session.commit()

        logger.info(f"  ✅ save_thread() completed: {(time.time() - save_start):.3f}s")

    async def load_threads(
        self,
        limit: int,
        after: str | None,
        order: str,
        context: dict[str, Any],
    ) -> Page[ThreadMetadata]:
        """Load multiple conversation threads from Supabase."""
        user_id = context.get("user_id")
        if not user_id:
            raise ValueError("user_id is required in context")

        async with await self._get_session() as session:
            # Only load active conversations (exclude archived/deleted)
            stmt = select(Conversation).where(
                Conversation.user_id == UUID(user_id),
                Conversation.status == "active"
            )

            if after:
                # Find the conversation with the after ID
                after_stmt = select(Conversation).where(
                    Conversation.chatkit_session_id == after,
                    Conversation.user_id == UUID(user_id),
                )
                after_result = await session.execute(after_stmt)
                after_conv = after_result.scalar_one_or_none()

                if after_conv:
                    if order == "desc":
                        stmt = stmt.where(Conversation.created_at < after_conv.created_at)
                    else:
                        stmt = stmt.where(Conversation.created_at > after_conv.created_at)

            # Apply ordering
            if order == "desc":
                stmt = stmt.order_by(Conversation.created_at.desc())
            else:
                stmt = stmt.order_by(Conversation.created_at.asc())

            # Fetch limit + 1 to determine has_more
            stmt = stmt.limit(limit + 1)
            result = await session.execute(stmt)
            conversations = list(result.scalars().all())

        threads = []
        for conv in conversations:
            # Skip conversations without a chatkit_session_id (legacy data)
            if not conv.chatkit_session_id:
                continue

            # Merge conversation metadata with system fields
            # Ensure meta_data is a dict (handle None or other types)
            meta_dict = conv.meta_data if isinstance(conv.meta_data, dict) else {}
            meta_dict.update({
                "conversation_id": str(conv.id),
                "title": conv.title,
                "status": conv.status,
            })

            threads.append(
                ThreadMetadata(
                    id=conv.chatkit_session_id,
                    created_at=conv.created_at,
                    metadata=meta_dict,
                )
            )

        has_more = len(threads) > limit
        threads = threads[:limit]
        next_after = threads[-1].id if has_more and threads else None

        return Page(
            data=threads,
            has_more=has_more,
            after=next_after,
        )

    async def delete_thread(self, thread_id: str, context: dict[str, Any]) -> None:
        """Delete a conversation thread from Supabase (optimistic, fast response)."""
        import asyncio
        from datetime import datetime

        user_id = context.get("user_id")
        if not user_id:
            raise ValueError("user_id is required in context")

        # Quick path: Mark as archived immediately for fast UI response
        async with await self._get_session() as session:
            stmt = select(Conversation).where(
                Conversation.chatkit_session_id == thread_id,
                Conversation.user_id == UUID(user_id),
            )
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation:
                # Mark as archived instead of deleting (fast operation)
                conversation.status = "archived"
                conversation.updated_at = datetime.now()
                await session.commit()

                # Schedule actual deletion in background (non-blocking)
                asyncio.create_task(self._delete_thread_background(thread_id, user_id))

    async def _delete_thread_background(self, thread_id: str, user_id: str) -> None:
        """Background task to actually delete the conversation and related data."""
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Wait a bit to ensure UI has time to update
            import asyncio
            await asyncio.sleep(0.5)

            async with await self._get_session() as session:
                stmt = select(Conversation).where(
                    Conversation.chatkit_session_id == thread_id,
                    Conversation.user_id == UUID(user_id),
                    Conversation.status == "archived",  # Only delete if still archived
                )
                result = await session.execute(stmt)
                conversation = result.scalar_one_or_none()

                if conversation:
                    await session.delete(conversation)
                    await session.commit()
                    logger.info(f"✅ Background deletion completed for thread {thread_id}")
        except Exception as e:
            logger.error(f"❌ Error in background thread deletion for {thread_id}: {e}", exc_info=True)

    # -- Thread items ----------------------------------------------------
    async def _get_conversation_id(self, thread_id: str, user_id: str) -> UUID:
        """Get the conversation ID for a given thread ID."""
        async with await self._get_session() as session:
            stmt = select(Conversation).where(
                Conversation.chatkit_session_id == thread_id,
                Conversation.user_id == UUID(user_id),
            ).order_by(Conversation.created_at.desc())
            result = await session.execute(stmt)
            rows = result.scalars().all()

            # Handle duplicates gracefully
            if len(rows) > 1:
                logger.warning(
                    f"⚠️  Found {len(rows)} duplicate conversations for thread {thread_id[:12]}. "
                    f"Using most recent conversation."
                )

            conversation = rows[0] if rows else None

            if not conversation:
                # Create a new conversation if it doesn't exist
                new_conversation = Conversation(
                    user_id=UUID(user_id),
                    chatkit_session_id=thread_id,
                    title="Nueva conversación",
                    status="active",
                )
                session.add(new_conversation)
                await session.commit()
                await session.refresh(new_conversation)
                return new_conversation.id

            return conversation.id

    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: dict[str, Any],
    ) -> Page[ThreadItem]:
        """Load messages for a conversation thread from Supabase."""
        import time
        load_items_start = time.time()

        user_id = context.get("user_id")
        if not user_id:
            raise ValueError("user_id is required in context")

        conv_id_start = time.time()
        conversation_id = await self._get_conversation_id(thread_id, user_id)
        logger.info(f"  🔍 load_thread_items() - get_conversation_id: {(time.time() - conv_id_start):.3f}s")

        query_start = time.time()
        async with await self._get_session() as session:
            stmt = select(Message).where(Message.conversation_id == conversation_id)

            if after:
                # Find the message with the after ID
                after_stmt = select(Message).where(Message.id == UUID(after))
                after_result = await session.execute(after_stmt)
                after_msg = after_result.scalar_one_or_none()

                if after_msg:
                    if order == "desc":
                        stmt = stmt.where(Message.created_at < after_msg.created_at)
                    else:
                        stmt = stmt.where(Message.created_at > after_msg.created_at)

            # Apply ordering
            if order == "desc":
                stmt = stmt.order_by(Message.created_at.desc())
            else:
                stmt = stmt.order_by(Message.created_at.asc())

            # Fetch limit + 1 to determine has_more
            stmt = stmt.limit(limit + 1)
            result = await session.execute(stmt)
            messages = list(result.scalars().all())

        logger.info(f"  🔍 load_thread_items() - messages query: {(time.time() - query_start):.3f}s ({len(messages)} messages)")

        # For now, return empty list since ThreadItem deserialization is complex
        # You'll need to implement proper deserialization based on your ThreadItem structure
        items: list[ThreadItem] = []

        has_more = len(messages) > limit
        messages = messages[:limit]
        next_after = str(messages[-1].id) if has_more and messages else None

        logger.info(f"  ✅ load_thread_items() completed: {(time.time() - load_items_start):.3f}s")

        return Page(data=items, has_more=has_more, after=next_after)

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: dict[str, Any]
    ) -> None:
        """Add a message to a conversation thread in Supabase."""
        user_id = context.get("user_id")
        if not user_id:
            raise ValueError("user_id is required in context")

        conversation_id = await self._get_conversation_id(thread_id, user_id)

        # Serialize the ThreadItem to JSON
        item_dict = item.model_dump() if hasattr(item, "model_dump") else {}
        # Convert datetime objects to ISO format strings
        item_dict_serializable = _serialize_for_json(item_dict)

        async with await self._get_session() as session:
            new_message = Message(
                conversation_id=conversation_id,
                user_id=UUID(user_id),
                role=getattr(item, "role", "user"),
                content=json.dumps(item_dict_serializable),
                message_metadata={"thread_item_id": item.id},
            )
            session.add(new_message)
            await session.commit()

    async def save_item(
        self, thread_id: str, item: ThreadItem, context: dict[str, Any]
    ) -> None:
        """Save or update a message in Supabase."""
        user_id = context.get("user_id")
        if not user_id:
            raise ValueError("user_id is required in context")

        conversation_id = await self._get_conversation_id(thread_id, user_id)

        item_dict = item.model_dump() if hasattr(item, "model_dump") else {}
        # Convert datetime objects to ISO format strings
        item_dict_serializable = _serialize_for_json(item_dict)

        async with await self._get_session() as session:
            # Check if message exists
            stmt = select(Message).where(
                Message.conversation_id == conversation_id,
                Message.message_metadata["thread_item_id"].astext == item.id,
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing message
                existing.role = getattr(item, "role", "user")
                existing.content = json.dumps(item_dict_serializable)
                existing.message_metadata = {"thread_item_id": item.id}
            else:
                # Create new message
                new_message = Message(
                    conversation_id=conversation_id,
                    user_id=UUID(user_id),
                    role=getattr(item, "role", "user"),
                    content=json.dumps(item_dict_serializable),
                    message_metadata={"thread_item_id": item.id},
                )
                session.add(new_message)

            await session.commit()

    async def load_item(
        self, thread_id: str, item_id: str, context: dict[str, Any]
    ) -> ThreadItem:
        """Load a specific message from Supabase."""
        user_id = context.get("user_id")
        if not user_id:
            raise ValueError("user_id is required in context")

        conversation_id = await self._get_conversation_id(thread_id, user_id)

        async with await self._get_session() as session:
            stmt = select(Message).where(
                Message.conversation_id == conversation_id,
                Message.message_metadata["thread_item_id"].astext == item_id,
            )
            result = await session.execute(stmt)
            message = result.scalar_one_or_none()

        if not message:
            raise NotFoundError(f"Item {item_id} not found")

        # Deserialize ThreadItem from JSON
        # Note: This is a placeholder - implement proper deserialization
        raise NotImplementedError("ThreadItem deserialization not implemented")

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: dict[str, Any]
    ) -> None:
        """Delete a message from Supabase."""
        user_id = context.get("user_id")
        if not user_id:
            raise ValueError("user_id is required in context")

        conversation_id = await self._get_conversation_id(thread_id, user_id)

        async with await self._get_session() as session:
            stmt = select(Message).where(
                Message.conversation_id == conversation_id,
                Message.message_metadata["thread_item_id"].astext == item_id,
            )
            result = await session.execute(stmt)
            message = result.scalar_one_or_none()

            if message:
                await session.delete(message)
                await session.commit()

    # -- Files -----------------------------------------------------------
    async def save_attachment(
        self,
        attachment: Attachment,
        context: dict[str, Any],
    ) -> None:
        """
        Save or update attachment metadata in Supabase using SQLAlchemy ORM.

        Note: The actual file is uploaded separately via AttachmentStore (two-phase upload).
        This method stores the attachment metadata in the database.
        """
        async with await self._get_session() as session:
            try:
                # Extract URLs and convert Pydantic AnyUrl to string
                upload_url = getattr(attachment, "upload_url", None)
                preview_url = getattr(attachment, "preview_url", None)

                # Convert AnyUrl to string if needed (Pydantic v2)
                if upload_url is not None:
                    upload_url = str(upload_url)
                if preview_url is not None:
                    preview_url = str(preview_url)

                # Extract OpenAI metadata from context (for PDFs)
                openai_file_id = context.get("openai_file_id")
                openai_vector_store_id = context.get("openai_vector_store_id")

                # Check if attachment already exists
                stmt = select(ChatKitAttachment).where(
                    ChatKitAttachment.id == attachment.id
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing attachment
                    existing.name = attachment.name
                    existing.mime_type = attachment.mime_type
                    existing.thread_id = context.get("thread_id")
                    existing.upload_url = upload_url
                    existing.preview_url = preview_url
                    existing.openai_file_id = openai_file_id
                    existing.openai_vector_store_id = openai_vector_store_id
                    existing.updated_at = datetime.now()
                    logger.info(f"✅ Updated attachment metadata: {attachment.id}")
                else:
                    # Create new attachment
                    db_attachment = ChatKitAttachment(
                        id=attachment.id,
                        name=attachment.name,
                        mime_type=attachment.mime_type,
                        thread_id=context.get("thread_id"),
                        upload_url=upload_url,
                        preview_url=preview_url,
                        openai_file_id=openai_file_id,
                        openai_vector_store_id=openai_vector_store_id,
                    )
                    session.add(db_attachment)
                    logger.info(f"✅ Created attachment metadata: {attachment.id}")

                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving attachment {attachment.id}: {e}")
                raise

    async def load_attachment(
        self,
        attachment_id: str,
        context: dict[str, Any],
    ) -> Attachment:
        """
        Load attachment metadata from Supabase using SQLAlchemy ORM.

        Note: This loads metadata only. The actual file content is accessed via URL.
        """
        async with await self._get_session() as session:
            try:
                # Query attachment from database
                result = await session.execute(
                    select(ChatKitAttachment).where(ChatKitAttachment.id == attachment_id)
                )
                db_attachment = result.scalar_one_or_none()

                if not db_attachment:
                    raise ValueError(f"Attachment {attachment_id} not found")

                # Reconstruct the Attachment object based on type
                if db_attachment.mime_type.startswith("image/"):
                    from chatkit.types import ImageAttachment
                    return ImageAttachment(
                        id=db_attachment.id,
                        name=db_attachment.name,
                        mime_type=db_attachment.mime_type,
                        upload_url=db_attachment.upload_url or "",
                        preview_url=db_attachment.preview_url or "",
                    )
                elif db_attachment.mime_type == "application/pdf":
                    from chatkit.types import FileAttachment
                    return FileAttachment(
                        id=db_attachment.id,
                        name=db_attachment.name,
                        mime_type=db_attachment.mime_type,
                        upload_url=db_attachment.upload_url or "",
                    )
                else:
                    # Generic attachment
                    from chatkit.types import FileAttachment
                    return FileAttachment(
                        id=db_attachment.id,
                        name=db_attachment.name,
                        mime_type=db_attachment.mime_type,
                        upload_url=db_attachment.upload_url or "",
                    )

            except Exception as e:
                logger.error(f"Error loading attachment {attachment_id}: {e}")
                raise

    async def get_attachment_openai_metadata(self, attachment_id: str) -> dict[str, str] | None:
        """
        Get OpenAI metadata (file_id and vector_store_id) for an attachment.

        Args:
            attachment_id: The attachment ID

        Returns:
            Dict with file_id and vector_store_id, or None if not found or no OpenAI metadata
        """
        async with await self._get_session() as session:
            try:
                result = await session.execute(
                    select(ChatKitAttachment).where(ChatKitAttachment.id == attachment_id)
                )
                db_attachment = result.scalar_one_or_none()

                if not db_attachment:
                    return None

                # Return OpenAI metadata if both fields are present
                if db_attachment.openai_file_id and db_attachment.openai_vector_store_id:
                    return {
                        "file_id": db_attachment.openai_file_id,
                        "vector_store_id": db_attachment.openai_vector_store_id,
                    }

                return None

            except Exception as e:
                logger.error(f"Error getting OpenAI metadata for {attachment_id}: {e}")
                return None

    async def delete_attachment(self, attachment_id: str, context: dict[str, Any]) -> None:
        """Delete attachment metadata from Supabase using SQLAlchemy ORM."""
        async with await self._get_session() as session:
            try:
                # Query and delete attachment
                result = await session.execute(
                    select(ChatKitAttachment).where(ChatKitAttachment.id == attachment_id)
                )
                db_attachment = result.scalar_one_or_none()

                if not db_attachment:
                    logger.warning(f"Attachment {attachment_id} not found for deletion")
                else:
                    await session.delete(db_attachment)
                    await session.commit()
                    logger.info(f"Deleted attachment metadata: {attachment_id}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting attachment {attachment_id}: {e}")
                raise
