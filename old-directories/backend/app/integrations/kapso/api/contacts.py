"""
Contacts API - Contact management and search.
"""
import logging
from typing import Dict, Optional, Any

from .base import BaseAPI

logger = logging.getLogger(__name__)


class ContactsAPI(BaseAPI):
    """API for contact operations."""

    async def search(
        self,
        query: str,
        limit: int = 20,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Search contacts by name or phone.

        Args:
            query: Search text
            limit: Results limit
            page: Page number

        Returns:
            List of contacts
        """
        params = {
            "query": query,
            "limit": limit,
            "page": page,
        }

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/search_contacts",
            params=params,
        )

        return result

    async def get_context(
        self,
        identifier: str,
        include_recent_messages: bool = True,
        recent_message_limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get contact context with recent messages.

        Args:
            identifier: Contact ID or phone number
            include_recent_messages: Include recent messages
            recent_message_limit: Messages limit

        Returns:
            Contact context
        """
        params = {
            "identifier": identifier,
            "include_recent_messages": include_recent_messages,
            "recent_message_limit": recent_message_limit,
        }

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/get_contact_context",
            params=params,
        )

        return result

    async def add_note(
        self,
        contact_identifier: str,
        content: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Add a note to a contact.

        Args:
            contact_identifier: Contact ID or number
            content: Note content
            name: Note name/label
            metadata: Additional metadata

        Returns:
            Created note
        """
        payload = {
            "contact_identifier": contact_identifier,
            "content": content,
        }

        if name:
            payload["name"] = name
        if metadata:
            payload["metadata"] = metadata

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp/contact_add_note",
            data=payload,
        )

        logger.info(f"✅ Note added to contact {contact_identifier}")
        return result
