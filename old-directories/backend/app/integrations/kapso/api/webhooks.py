"""
Webhooks API - Webhook validation utilities.
"""
import logging
import hmac
import hashlib
from typing import Dict, Any

logger = logging.getLogger(__name__)


class WebhooksAPI:
    """
    Webhook utilities.

    Note: This class doesn't inherit from BaseAPI because it doesn't make HTTP requests.
    It only provides static utility methods.
    """

    @staticmethod
    def validate_signature(
        payload: str,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Validate webhook signature from Kapso.

        Args:
            payload: Webhook payload as string
            signature: Signature from header
            secret: Webhook shared secret

        Returns:
            True if signature is valid
        """
        try:
            expected_signature = hmac.new(
                secret.encode("utf-8"),
                payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False

    @staticmethod
    async def health_check() -> Dict[str, Any]:
        """
        Basic health check.

        Returns:
            Health status
        """
        return {
            "status": "healthy",
            "message": "Webhook utilities available"
        }
