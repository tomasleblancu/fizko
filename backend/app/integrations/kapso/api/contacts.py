"""Contacts API - manage WhatsApp contacts."""

import logging
from typing import Any, Optional

from .base import BaseAPI

logger = logging.getLogger(__name__)


class ContactsAPI(BaseAPI):
    """API for WhatsApp contact operations."""

    async def search(
        self,
        query: str,
        limit: int = 20,
        page: int = 1,
    ) -> dict[str, Any]:
        """
        Search contacts by name or phone.

        Args:
            query: Search query (name or phone substring)
            limit: Max results per page
            page: Page number

        Returns:
            Matching contacts
        """
        params = {
            "query": query,
            "limit": limit,
            "page": page,
        }

        return await self._make_request(
            method="GET",
            endpoint="whatsapp_contacts",
            params=params,
        )

    async def get_context(
        self,
        identifier: str,
        include_recent_messages: bool = True,
        recent_message_limit: int = 20,
    ) -> dict[str, Any]:
        """
        Get contact context with conversation and recent messages.

        Args:
            identifier: Contact ID or phone number
            include_recent_messages: Whether to include recent messages
            recent_message_limit: Number of recent messages

        Returns:
            Contact with conversation and messages
        """
        params = {
            "include_recent_messages": include_recent_messages,
            "recent_message_limit": recent_message_limit,
        }

        return await self._make_request(
            method="GET",
            endpoint=f"whatsapp_contacts/{identifier}/context",
            params=params,
        )

    async def add_note(
        self,
        contact_identifier: str,
        content: str,
        name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Add a note to a contact.

        Args:
            contact_identifier: Contact ID or phone number
            content: Note content
            name: Optional note label
            metadata: Optional JSON metadata

        Returns:
            Created note
        """
        payload: dict[str, Any] = {"content": content}

        if name:
            payload["name"] = name
        if metadata:
            payload["metadata"] = metadata

        return await self._make_request(
            method="POST",
            endpoint=f"whatsapp_contacts/{contact_identifier}/notes",
            data=payload,
        )

    async def update(
        self,
        contact_identifier: str,
        display_name: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Update contact information.

        Args:
            contact_identifier: Contact ID or phone number
            display_name: Optional new display name
            customer_id: Optional customer ID to link

        Returns:
            Updated contact
        """
        payload: dict[str, Any] = {}

        if display_name:
            payload["display_name"] = display_name
        if customer_id:
            payload["customer_id"] = customer_id

        return await self._make_request(
            method="PATCH",
            endpoint=f"whatsapp_contacts/{contact_identifier}",
            data=payload,
        )
