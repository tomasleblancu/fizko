"""Webhooks API - webhook validation."""

import hashlib
import hmac
import logging

from .base import BaseAPI

logger = logging.getLogger(__name__)


class WebhooksAPI(BaseAPI):
    """API for webhook validation."""

    @staticmethod
    def validate_signature(
        payload: str,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Validate webhook HMAC signature.

        Args:
            payload: Raw request body as string
            signature: X-Webhook-Signature header value
            secret: Webhook secret from Kapso

        Returns:
            True if signature is valid, False otherwise
        """
        if not secret:
            logger.warning("No webhook secret configured - skipping validation")
            return True

        try:
            # Compute HMAC-SHA256 signature
            computed_signature = hmac.new(
                key=secret.encode("utf-8"),
                msg=payload.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).hexdigest()

            # Compare signatures (constant-time comparison)
            return hmac.compare_digest(computed_signature, signature)

        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False
