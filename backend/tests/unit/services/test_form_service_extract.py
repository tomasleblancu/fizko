"""
Unit tests for FormService.extract_f29_lista method.

Tests the service layer that orchestrates F29 extraction with Celery callbacks.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4

from app.services.sii.form_service import FormService


@pytest.fixture
def form_service():
    """FormService instance with mocked DB session"""
    mock_db = AsyncMock()
    service = FormService(mock_db)
    return service


@pytest.fixture
def mock_sii_credentials():
    """Mock SII credentials"""
    return {
        "rut": "77794858-K",
        "password": "test_password",
        "cookies": [
            {"name": "SESSION", "value": "abc123"},
            {"name": "AUTH", "value": "xyz789"}
        ]
    }


@pytest.fixture
def mock_formularios():
    """Mock list of formularios returned by SIIClient"""
    return [
        {
            "folio": "F1",
            "period": "2025-01",
            "contributor": "77794858-K",
            "submission_date": "01/01/2025",
            "status": "Vigente",
            "amount": 100,
            "id_interno_sii": "123"
        },
        {
            "folio": "F2",
            "period": "2025-02",
            "contributor": "77794858-K",
            "submission_date": "01/02/2025",
            "status": "Vigente",
            "amount": 200,
            "id_interno_sii": "456"
        },
        {
            "folio": "F3",
            "period": "2025-03",
            "contributor": "77794858-K",
            "submission_date": "01/03/2025",
            "status": "Vigente",
            "amount": 300
            # No id_interno_sii
        }
    ]


class TestFormServiceExtractF29Lista:
    """Tests for extract_f29_lista method"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_triggers_celery_callback(
        self,
        form_service,
        mock_sii_credentials,
        mock_formularios
    ):
        """Test that extraction triggers Celery save_single_f29 for each formulario"""
        session_id = str(uuid4())
        company_id = str(uuid4())
        anio = "2025"

        # Mock get_stored_credentials
        form_service.get_stored_credentials = AsyncMock(return_value=mock_sii_credentials)

        # Mock get_company_id_from_session
        form_service.get_company_id_from_session = AsyncMock(return_value=company_id)

        # Mock save_cookies
        form_service.save_cookies = AsyncMock()

        # Mock SIIClient context manager and get_f29_lista
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get_f29_lista = Mock(return_value=mock_formularios)
        mock_client.get_cookies = Mock(return_value=[])

        with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
            with patch('app.infrastructure.celery.tasks.sii.forms.save_single_f29') as mock_task:
                mock_task.apply_async = Mock()

                # Execute
                result = await form_service.extract_f29_lista(
                    session_id=session_id,
                    anio=anio,
                    company_id=company_id
                )

        # Assert result
        assert len(result) == 3
        assert result == mock_formularios

        # Assert Celery task was called 3 times (once per formulario)
        assert mock_task.apply_async.call_count == 3

        # Verify each call had correct arguments
        calls = mock_task.apply_async.call_args_list
        for i, call in enumerate(calls):
            args = call[1]["args"]
            assert args[0] == company_id  # company_id
            assert args[1] == mock_formularios[i]  # formulario
            assert args[2] == session_id  # session_id

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_updates_cookies(
        self,
        form_service,
        mock_sii_credentials,
        mock_formularios
    ):
        """Test that cookies are updated after extraction"""
        session_id = str(uuid4())
        company_id = str(uuid4())
        anio = "2025"

        updated_cookies = [
            {"name": "SESSION", "value": "new_abc123"},
            {"name": "AUTH", "value": "new_xyz789"}
        ]

        # Mock methods
        form_service.get_stored_credentials = AsyncMock(return_value=mock_sii_credentials)
        form_service.get_company_id_from_session = AsyncMock(return_value=company_id)
        form_service.save_cookies = AsyncMock()

        # Mock SIIClient
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get_f29_lista = Mock(return_value=mock_formularios)
        mock_client.get_cookies = Mock(return_value=updated_cookies)

        with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
            with patch('app.infrastructure.celery.tasks.sii.forms.save_single_f29.apply_async'):
                # Execute
                await form_service.extract_f29_lista(
                    session_id=session_id,
                    anio=anio,
                    company_id=company_id
                )

        # Assert cookies were saved
        form_service.save_cookies.assert_called_once_with(session_id, updated_cookies)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_without_company_id_fetches_from_session(
        self,
        form_service,
        mock_sii_credentials,
        mock_formularios
    ):
        """Test that company_id is fetched from session if not provided"""
        session_id = str(uuid4())
        company_id = str(uuid4())
        anio = "2025"

        # Mock methods
        form_service.get_stored_credentials = AsyncMock(return_value=mock_sii_credentials)
        form_service.get_company_id_from_session = AsyncMock(return_value=company_id)
        form_service.save_cookies = AsyncMock()

        # Mock SIIClient
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get_f29_lista = Mock(return_value=mock_formularios)
        mock_client.get_cookies = Mock(return_value=[])

        with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
            with patch('app.infrastructure.celery.tasks.sii.forms.save_single_f29.apply_async'):
                # Execute WITHOUT company_id
                result = await form_service.extract_f29_lista(
                    session_id=session_id,
                    anio=anio
                    # company_id=None (not provided)
                )

        # Assert company_id was fetched
        form_service.get_company_id_from_session.assert_called_once_with(session_id)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_handles_celery_callback_error_gracefully(
        self,
        form_service,
        mock_sii_credentials,
        mock_formularios
    ):
        """Test that Celery callback errors don't stop extraction"""
        session_id = str(uuid4())
        company_id = str(uuid4())
        anio = "2025"

        # Mock methods
        form_service.get_stored_credentials = AsyncMock(return_value=mock_sii_credentials)
        form_service.get_company_id_from_session = AsyncMock(return_value=company_id)
        form_service.save_cookies = AsyncMock()

        # Mock SIIClient
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get_f29_lista = Mock(return_value=mock_formularios)
        mock_client.get_cookies = Mock(return_value=[])

        with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
            with patch('app.infrastructure.celery.tasks.sii.forms.save_single_f29') as mock_task:
                # Make Celery task fail
                mock_task.apply_async = Mock(side_effect=Exception("Celery connection error"))

                # Execute - should not raise exception
                result = await form_service.extract_f29_lista(
                    session_id=session_id,
                    anio=anio,
                    company_id=company_id
                )

        # Assert extraction completed despite Celery errors
        assert len(result) == 3
        assert result == mock_formularios


class TestFormServiceExtractErrors:
    """Tests for error scenarios"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_raises_when_session_not_found(self, form_service):
        """Test ValueError raised when session credentials not found"""
        session_id = str(uuid4())
        anio = "2025"

        # Mock get_stored_credentials returns None
        form_service.get_stored_credentials = AsyncMock(return_value=None)

        # Execute - should raise ValueError
        with pytest.raises(ValueError, match="not found"):
            await form_service.extract_f29_lista(
                session_id=session_id,
                anio=anio
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_raises_when_company_id_not_found(
        self,
        form_service,
        mock_sii_credentials
    ):
        """Test ValueError raised when company_id not found for session"""
        session_id = str(uuid4())
        anio = "2025"

        # Mock methods
        form_service.get_stored_credentials = AsyncMock(return_value=mock_sii_credentials)
        form_service.get_company_id_from_session = AsyncMock(return_value=None)

        # Execute - should raise ValueError
        with pytest.raises(ValueError, match="no associated company"):
            await form_service.extract_f29_lista(
                session_id=session_id,
                anio=anio
            )


class TestFormServiceCallbackBehavior:
    """Tests for the Celery callback behavior"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_callback_receives_formulario_with_codint(
        self,
        form_service,
        mock_sii_credentials
    ):
        """Test that callback receives formulario with id_interno_sii"""
        session_id = str(uuid4())
        company_id = str(uuid4())
        anio = "2025"

        formulario_with_codint = {
            "folio": "8510019316",
            "period": "2025-01",
            "amount": 42443,
            "id_interno_sii": "775148628"
        }

        # Mock methods
        form_service.get_stored_credentials = AsyncMock(return_value=mock_sii_credentials)
        form_service.get_company_id_from_session = AsyncMock(return_value=company_id)
        form_service.save_cookies = AsyncMock()

        # Mock SIIClient
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get_f29_lista = Mock(return_value=[formulario_with_codint])
        mock_client.get_cookies = Mock(return_value=[])

        with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
            with patch('app.infrastructure.celery.tasks.sii.forms.save_single_f29') as mock_task:
                mock_task.apply_async = Mock()

                # Execute
                await form_service.extract_f29_lista(
                    session_id=session_id,
                    anio=anio,
                    company_id=company_id
                )

        # Assert callback called with formulario containing id_interno_sii
        mock_task.apply_async.assert_called_once()
        call_args = mock_task.apply_async.call_args[1]["args"]
        formulario_arg = call_args[1]
        assert formulario_arg["id_interno_sii"] == "775148628"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_callback_receives_formulario_without_codint(
        self,
        form_service,
        mock_sii_credentials
    ):
        """Test that callback receives formulario even without id_interno_sii"""
        session_id = str(uuid4())
        company_id = str(uuid4())
        anio = "2025"

        formulario_without_codint = {
            "folio": "8510019316",
            "period": "2025-01",
            "amount": 42443
            # No id_interno_sii
        }

        # Mock methods
        form_service.get_stored_credentials = AsyncMock(return_value=mock_sii_credentials)
        form_service.get_company_id_from_session = AsyncMock(return_value=company_id)
        form_service.save_cookies = AsyncMock()

        # Mock SIIClient
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get_f29_lista = Mock(return_value=[formulario_without_codint])
        mock_client.get_cookies = Mock(return_value=[])

        with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
            with patch('app.infrastructure.celery.tasks.sii.forms.save_single_f29') as mock_task:
                mock_task.apply_async = Mock()

                # Execute
                await form_service.extract_f29_lista(
                    session_id=session_id,
                    anio=anio,
                    company_id=company_id
                )

        # Assert callback called even without id_interno_sii
        mock_task.apply_async.assert_called_once()
        call_args = mock_task.apply_async.call_args[1]["args"]
        formulario_arg = call_args[1]
        assert "id_interno_sii" not in formulario_arg
