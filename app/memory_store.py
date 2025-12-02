"""Simple in-memory store compatible with the ChatKit Store interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from chatkit.store import NotFoundError, Store
from chatkit.types import Attachment, Page, Thread, ThreadItem, ThreadMetadata

from .request_context import RequestContext


@dataclass
class _ThreadState:
    thread: ThreadMetadata
    items: List[ThreadItem]


class MemoryStore(Store[RequestContext]):
    """Simple in-memory store compatible with the ChatKit Store interface."""

    def __init__(self) -> None:
        self._threads: Dict[str, _ThreadState] = {}
        self._attachments: Dict[str, Attachment] = {}
        self._attachment_bytes: Dict[str, bytes] = {}

    @staticmethod
    def _coerce_thread_metadata(thread: ThreadMetadata | Thread) -> ThreadMetadata:
        """Return thread metadata without any embedded items."""
        has_items = isinstance(thread, Thread) or "items" in getattr(
            thread, "model_fields_set", set()
        )
        if not has_items:
            return thread.model_copy(deep=True)

        data = thread.model_dump()
        data.pop("items", None)
        return ThreadMetadata(**data).model_copy(deep=True)

    # -- Thread metadata -------------------------------------------------
    async def load_thread(self, thread_id: str, context: RequestContext) -> ThreadMetadata:
        state = self._threads.get(thread_id)
        if not state:
            raise NotFoundError(f"Thread {thread_id} not found")
        return self._coerce_thread_metadata(state.thread)

    async def save_thread(self, thread: ThreadMetadata, context: RequestContext) -> None:
        metadata = self._coerce_thread_metadata(thread)
        state = self._threads.get(thread.id)
        if state:
            state.thread = metadata
        else:
            self._threads[thread.id] = _ThreadState(
                thread=metadata,
                items=[],
            )

    async def load_threads(
        self,
        limit: int,
        after: str | None,
        order: str,
        context: RequestContext,
    ) -> Page[ThreadMetadata]:
        threads = sorted(
            (self._coerce_thread_metadata(state.thread) for state in self._threads.values()),
            key=lambda t: t.created_at or datetime.min,
            reverse=(order == "desc"),
        )

        if after:
            index_map = {thread.id: idx for idx, thread in enumerate(threads)}
            start = index_map.get(after, -1) + 1
        else:
            start = 0

        slice_threads = threads[start : start + limit + 1]
        has_more = len(slice_threads) > limit
        slice_threads = slice_threads[:limit]
        next_after = slice_threads[-1].id if has_more and slice_threads else None
        return Page(
            data=slice_threads,
            has_more=has_more,
            after=next_after,
        )

    async def delete_thread(self, thread_id: str, context: RequestContext) -> None:
        self._threads.pop(thread_id, None)

    # -- Thread items ----------------------------------------------------
    def _thread_state(self, thread_id: str) -> _ThreadState:
        state = self._threads.get(thread_id)
        if state is None:
            state = _ThreadState(
                thread=ThreadMetadata(id=thread_id, created_at=datetime.utcnow()),
                items=[],
            )
            self._threads[thread_id] = state
        return state

    def _items(self, thread_id: str) -> List[ThreadItem]:
        state = self._thread_state(thread_id)
        return state.items

    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: RequestContext,
    ) -> Page[ThreadItem]:
        items = [item.model_copy(deep=True) for item in self._items(thread_id)]
        items.sort(
            key=lambda item: getattr(item, "created_at", datetime.utcnow()),
            reverse=(order == "desc"),
        )

        if after:
            index_map = {item.id: idx for idx, item in enumerate(items)}
            start = index_map.get(after, -1) + 1
        else:
            start = 0

        slice_items = items[start : start + limit + 1]
        has_more = len(slice_items) > limit
        slice_items = slice_items[:limit]
        next_after = slice_items[-1].id if has_more and slice_items else None
        return Page(data=slice_items, has_more=has_more, after=next_after)

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: RequestContext
    ) -> None:
        self._items(thread_id).append(item.model_copy(deep=True))

    async def save_item(self, thread_id: str, item: ThreadItem, context: RequestContext) -> None:
        items = self._items(thread_id)
        for idx, existing in enumerate(items):
            if existing.id == item.id:
                items[idx] = item.model_copy(deep=True)
                return
        items.append(item.model_copy(deep=True))

    async def load_item(self, thread_id: str, item_id: str, context: RequestContext) -> ThreadItem:
        for item in self._items(thread_id):
            if item.id == item_id:
                return item.model_copy(deep=True)
        raise NotFoundError(f"Item {item_id} not found")

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: RequestContext
    ) -> None:
        items = self._items(thread_id)
        self._threads[thread_id].items = [item for item in items if item.id != item_id]

    # -- Files -----------------------------------------------------------
    async def save_attachment(
        self,
        attachment: Attachment,
        context: RequestContext,
    ) -> None:
        """Save attachment metadata to in-memory store."""
        # In production, enforce authorization checks here
        self._attachments[attachment.id] = attachment.model_copy(deep=True)

    async def load_attachment(
        self,
        attachment_id: str,
        context: RequestContext,
    ) -> Attachment:
        """Load attachment metadata from in-memory store."""
        # In production, enforce authorization checks here
        attachment = self._attachments.get(attachment_id)
        if not attachment:
            raise NotFoundError(f"Attachment {attachment_id} not found")
        return attachment.model_copy(deep=True)

    async def delete_attachment(self, attachment_id: str, context: RequestContext) -> None:
        """Delete attachment metadata and bytes from in-memory store."""
        # In production, enforce authorization checks here
        self._attachments.pop(attachment_id, None)
        self._attachment_bytes.pop(attachment_id, None)

    def save_attachment_bytes(self, attachment_id: str, content: bytes) -> None:
        """Store attachment file bytes (internal method)."""
        self._attachment_bytes[attachment_id] = content

    def load_attachment_bytes(self, attachment_id: str) -> bytes | None:
        """Load attachment file bytes (internal method)."""
        return self._attachment_bytes.get(attachment_id)

