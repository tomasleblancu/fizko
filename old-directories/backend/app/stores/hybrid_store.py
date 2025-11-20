"""Hybrid store: Fast in-memory with background Supabase persistence."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from chatkit.store import NotFoundError, Store
from chatkit.types import Attachment, Page, Thread, ThreadItem, ThreadMetadata

logger = logging.getLogger(__name__)


@dataclass
class _ThreadState:
    thread: ThreadMetadata
    items: List[ThreadItem]


class HybridStore(Store[dict[str, Any]]):
    """
    Hybrid store that combines MemoryStore speed with Supabase persistence.

    - All reads are from memory (instantaneous)
    - Writes go to memory first, then background sync to Supabase
    - On startup, loads from Supabase to memory
    """

    def __init__(self, supabase_store=None) -> None:
        self._threads: Dict[str, _ThreadState] = {}
        self._supabase_store = supabase_store
        self._sync_tasks: List[asyncio.Task] = []
        logger.info("HybridStore initialized (memory + background Supabase sync)")

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

    def _schedule_background_sync(self, coro):
        """Schedule a coroutine to run in the background without blocking."""
        task = asyncio.create_task(coro)
        self._sync_tasks.append(task)
        # Clean up finished tasks
        self._sync_tasks = [t for t in self._sync_tasks if not t.done()]

    # -- Thread metadata -------------------------------------------------
    async def load_thread(self, thread_id: str, context: dict[str, Any]) -> ThreadMetadata:
        """Load thread from memory (fast). If not found, try Supabase."""
        state = self._threads.get(thread_id)
        if state:
            logger.debug(f"  💾 HybridStore: Thread {thread_id[:12]} loaded from memory")
            return self._coerce_thread_metadata(state.thread)

        # Not in memory, try loading from Supabase
        if self._supabase_store:
            try:
                logger.debug(f"  🔄 HybridStore: Loading thread {thread_id[:12]} from Supabase...")
                thread = await self._supabase_store.load_thread(thread_id, context)
                # Cache in memory for next time
                self._threads[thread_id] = _ThreadState(thread=thread, items=[])
                logger.debug(f"  ✅ HybridStore: Thread {thread_id[:12]} cached from Supabase")
                return thread
            except NotFoundError:
                pass

        raise NotFoundError(f"Thread {thread_id} not found")

    async def save_thread(self, thread: ThreadMetadata, context: dict[str, Any]) -> None:
        """Save thread to memory (instant), sync to Supabase in background."""
        metadata = self._coerce_thread_metadata(thread)
        state = self._threads.get(thread.id)
        if state:
            state.thread = metadata
        else:
            self._threads[thread.id] = _ThreadState(thread=metadata, items=[])

        logger.debug(f"  ⚡ HybridStore: Thread {thread.id[:12]} saved to memory")

        # Background sync to Supabase (non-blocking)
        if self._supabase_store:
            self._schedule_background_sync(
                self._background_save_thread(thread, context)
            )

    async def _background_save_thread(self, thread: ThreadMetadata, context: dict[str, Any]) -> None:
        """Background task to save thread to Supabase."""
        try:
            await self._supabase_store.save_thread(thread, context)
            logger.debug(f"  🔄 HybridStore: Thread {thread.id[:12]} synced to Supabase")
        except Exception as e:
            logger.error(f"  ❌ HybridStore: Failed to sync thread to Supabase: {e}")

    async def load_threads(
        self,
        limit: int,
        after: str | None,
        order: str,
        context: dict[str, Any],
    ) -> Page[ThreadMetadata]:
        """Load threads from memory."""
        from datetime import datetime, timezone

        threads = []
        for thread_id, state in self._threads.items():
            threads.append(self._coerce_thread_metadata(state.thread))

        # Simple sorting by created_at (handle timezone-aware and naive datetimes)
        def get_sort_key(t):
            if t.created_at is None:
                return datetime.min.replace(tzinfo=timezone.utc)
            # Ensure timezone-aware datetime
            if t.created_at.tzinfo is None:
                return t.created_at.replace(tzinfo=timezone.utc)
            return t.created_at

        threads.sort(
            key=get_sort_key,
            reverse=(order == "desc")
        )

        # Simple pagination
        if after:
            try:
                after_idx = next(i for i, t in enumerate(threads) if t.id == after)
                threads = threads[after_idx + 1:]
            except StopIteration:
                pass

        has_more = len(threads) > limit
        threads = threads[:limit]
        next_after = threads[-1].id if has_more and threads else None

        return Page(data=threads, has_more=has_more, after=next_after)

    async def delete_thread(self, thread_id: str, context: dict[str, Any]) -> None:
        """Delete thread from memory and Supabase."""
        if thread_id in self._threads:
            del self._threads[thread_id]

        # Background sync to Supabase
        if self._supabase_store:
            self._schedule_background_sync(
                self._supabase_store.delete_thread(thread_id, context)
            )

    # -- Thread items ----------------------------------------------------
    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: dict[str, Any],
    ) -> Page[ThreadItem]:
        """Load items from memory."""
        state = self._threads.get(thread_id)
        if not state:
            # Try loading from Supabase first
            if self._supabase_store:
                try:
                    await self.load_thread(thread_id, context)
                    state = self._threads.get(thread_id)
                except NotFoundError:
                    pass

            if not state:
                return Page(data=[], has_more=False, after=None)

        items = state.items

        # Simple pagination
        if after:
            try:
                after_idx = next(i for i, item in enumerate(items) if item.id == after)
                items = items[after_idx + 1:]
            except StopIteration:
                pass

        has_more = len(items) > limit
        items = items[:limit]
        next_after = items[-1].id if has_more and items else None

        logger.debug(f"  💾 HybridStore: Loaded {len(items)} items from memory")

        return Page(data=items, has_more=has_more, after=next_after)

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: dict[str, Any]
    ) -> None:
        """Add item to memory and sync to Supabase in background."""
        state = self._threads.get(thread_id)
        if not state:
            # Create thread state if doesn't exist
            self._threads[thread_id] = _ThreadState(
                thread=ThreadMetadata(id=thread_id),
                items=[]
            )
            state = self._threads[thread_id]

        state.items.append(item)
        logger.debug(f"  ⚡ HybridStore: Item added to memory")

        # Background sync to Supabase
        if self._supabase_store:
            self._schedule_background_sync(
                self._supabase_store.add_thread_item(thread_id, item, context)
            )

    async def save_item(
        self, thread_id: str, item: ThreadItem, context: dict[str, Any]
    ) -> None:
        """Save item to memory and sync to Supabase in background."""
        state = self._threads.get(thread_id)
        if state:
            # Update existing item or append
            for i, existing_item in enumerate(state.items):
                if existing_item.id == item.id:
                    state.items[i] = item
                    break
            else:
                state.items.append(item)

        # Background sync to Supabase
        if self._supabase_store:
            self._schedule_background_sync(
                self._supabase_store.save_item(thread_id, item, context)
            )

    async def load_item(
        self, thread_id: str, item_id: str, context: dict[str, Any]
    ) -> ThreadItem:
        """Load item from memory."""
        state = self._threads.get(thread_id)
        if state:
            for item in state.items:
                if item.id == item_id:
                    return item

        raise NotFoundError(f"Item {item_id} not found")

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: dict[str, Any]
    ) -> None:
        """Delete item from memory and Supabase."""
        state = self._threads.get(thread_id)
        if state:
            state.items = [item for item in state.items if item.id != item_id]

        # Background sync to Supabase
        if self._supabase_store:
            self._schedule_background_sync(
                self._supabase_store.delete_thread_item(thread_id, item_id, context)
            )

    # -- Attachments (delegate to Supabase) -----------------------------
    async def save_attachment(
        self, attachment: Attachment, context: dict[str, Any]
    ) -> None:
        """Delegate to Supabase store."""
        if self._supabase_store:
            await self._supabase_store.save_attachment(attachment, context)

    async def load_attachment(
        self, attachment_id: str, context: dict[str, Any]
    ) -> Attachment:
        """Delegate to Supabase store."""
        if self._supabase_store:
            return await self._supabase_store.load_attachment(attachment_id, context)
        raise NotFoundError(f"Attachment {attachment_id} not found")

    async def delete_attachment(
        self, attachment_id: str, context: dict[str, Any]
    ) -> None:
        """Delegate to Supabase store."""
        if self._supabase_store:
            await self._supabase_store.delete_attachment(attachment_id, context)
