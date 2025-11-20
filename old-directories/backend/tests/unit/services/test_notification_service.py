"""Unit tests for notification service."""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.services.notifications import send_instant_notification


@pytest.mark.unit
async def test_send_instant_notification_success(db_session):
    """Test successful instant notification sending."""
    company_id = "test-company-id"
    phone_numbers = ["+56912345678"]
    message = "Test notification"

    with patch('app.services.notifications.modules.whatsapp.send_whatsapp_notification') as mock_send:
        mock_send.return_value = {"status": "sent", "message_id": "test-123"}

        result = await send_instant_notification(
            db_session,
            company_id,
            phone_numbers,
            message
        )

        assert result is not None
        mock_send.assert_called_once()


@pytest.mark.unit
async def test_send_instant_notification_multiple_recipients(db_session):
    """Test notification with multiple recipients."""
    company_id = "test-company-id"
    phone_numbers = ["+56912345678", "+56987654321", "+56911111111"]
    message = "Broadcast notification"

    with patch('app.services.notifications.modules.whatsapp.send_whatsapp_notification') as mock_send:
        mock_send.return_value = {"status": "sent"}

        result = await send_instant_notification(
            db_session,
            company_id,
            phone_numbers,
            message
        )

        # Should be called for each recipient
        assert mock_send.call_count == len(phone_numbers)
