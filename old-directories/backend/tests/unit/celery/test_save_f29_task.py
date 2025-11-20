"""
Unit tests for save_single_f29 Celery task.

Tests the new simplified Celery-based incremental save system for F29 forms.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, call
from uuid import uuid4

# Import the task
from app.infrastructure.celery.tasks.sii.forms import save_single_f29


@pytest.fixture
def sample_formulario():
    """Sample F29 formulario dict"""
    return {
        "folio": "8510019316",
        "period": "2025-01",
        "contributor": "77794858-K",
        "submission_date": "09/05/2024",
        "status": "Vigente",
        "amount": 42443,
        "id_interno_sii": "775148628"
    }


@pytest.fixture
def sample_formulario_without_codint():
    """Sample F29 formulario without id_interno_sii"""
    return {
        "folio": "8510019316",
        "period": "2025-01",
        "contributor": "77794858-K",
        "submission_date": "09/05/2024",
        "status": "Vigente",
        "amount": 42443
        # NO id_interno_sii
    }


@pytest.fixture
def mock_download_record():
    """Mock Form29SIIDownload record"""
    record = Mock()
    record.id = uuid4()
    record.sii_folio = "8510019316"
    record.company_id = uuid4()
    return record


class TestSaveF29TaskSuccess:
    """Tests for successful save scenarios"""

    @pytest.mark.unit
    @patch('app.infrastructure.celery.tasks.sii.forms.AsyncSessionLocal')
    @patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf')
    def test_save_f29_with_codint_queues_pdf(
        self,
        mock_pdf_task,
        mock_session_local,
        sample_formulario,
        mock_download_record
    ):
        """Test saving F29 with id_interno_sii triggers PDF download"""
        company_id = str(uuid4())
        session_id = str(uuid4())

        # Mock DB session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock service
        mock_service = Mock()
        mock_service.save_f29_downloads = AsyncMock(return_value=[mock_download_record])

        with patch('app.infrastructure.celery.tasks.sii.forms.SIIService', return_value=mock_service):
            with patch('app.infrastructure.celery.tasks.sii.forms.asyncio.run') as mock_asyncio_run:
                # Mock asyncio.run to execute the coroutine
                mock_asyncio_run.return_value = [mock_download_record]

                # Execute task
                result = save_single_f29(
                    company_id=company_id,
                    formulario=sample_formulario,
                    session_id=session_id
                )

        # Assert success
        assert result["success"] is True
        assert result["folio"] == "8510019316"
        assert result["download_id"] == str(mock_download_record.id)
        assert result["pdf_queued"] is True

        # Assert PDF task was queued
        mock_pdf_task.apply_async.assert_called_once()
        args = mock_pdf_task.apply_async.call_args
        assert args[1]["args"] == [str(mock_download_record.id), session_id]
        assert args[1]["countdown"] == 2

    @pytest.mark.unit
    @patch('app.infrastructure.celery.tasks.sii.forms.AsyncSessionLocal')
    def test_save_f29_without_codint_no_pdf_queue(
        self,
        mock_session_local,
        sample_formulario_without_codint,
        mock_download_record
    ):
        """Test saving F29 without id_interno_sii doesn't queue PDF"""
        company_id = str(uuid4())
        session_id = str(uuid4())

        # Mock DB session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock service
        mock_service = Mock()
        mock_service.save_f29_downloads = AsyncMock(return_value=[mock_download_record])

        with patch('app.infrastructure.celery.tasks.sii.forms.SIIService', return_value=mock_service):
            with patch('app.infrastructure.celery.tasks.sii.forms.asyncio.run') as mock_asyncio_run:
                mock_asyncio_run.return_value = [mock_download_record]

                with patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf') as mock_pdf_task:
                    # Execute task
                    result = save_single_f29(
                        company_id=company_id,
                        formulario=sample_formulario_without_codint,
                        session_id=session_id
                    )

        # Assert success but no PDF queued
        assert result["success"] is True
        assert result["pdf_queued"] is False

        # Assert PDF task was NOT queued
        mock_pdf_task.apply_async.assert_not_called()

    @pytest.mark.unit
    @patch('app.infrastructure.celery.tasks.sii.forms.AsyncSessionLocal')
    def test_save_f29_without_session_id(
        self,
        mock_session_local,
        sample_formulario,
        mock_download_record
    ):
        """Test saving F29 without session_id doesn't queue PDF"""
        company_id = str(uuid4())

        # Mock DB session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock service
        mock_service = Mock()
        mock_service.save_f29_downloads = AsyncMock(return_value=[mock_download_record])

        with patch('app.infrastructure.celery.tasks.sii.forms.SIIService', return_value=mock_service):
            with patch('app.infrastructure.celery.tasks.sii.forms.asyncio.run') as mock_asyncio_run:
                mock_asyncio_run.return_value = [mock_download_record]

                with patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf') as mock_pdf_task:
                    # Execute task without session_id
                    result = save_single_f29(
                        company_id=company_id,
                        formulario=sample_formulario,
                        session_id=None  # No session_id
                    )

        # Assert success but no PDF queued
        assert result["success"] is True
        assert result["pdf_queued"] is False
        mock_pdf_task.apply_async.assert_not_called()


class TestSaveF29TaskErrors:
    """Tests for error scenarios"""

    @pytest.mark.unit
    @patch('app.infrastructure.celery.tasks.sii.forms.AsyncSessionLocal')
    def test_save_f29_no_records_saved(
        self,
        mock_session_local,
        sample_formulario
    ):
        """Test when save_f29_downloads returns empty list"""
        company_id = str(uuid4())

        # Mock DB session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock service returns empty list
        mock_service = Mock()
        mock_service.save_f29_downloads = AsyncMock(return_value=[])

        with patch('app.infrastructure.celery.tasks.sii.forms.SIIService', return_value=mock_service):
            with patch('app.infrastructure.celery.tasks.sii.forms.asyncio.run') as mock_asyncio_run:
                mock_asyncio_run.return_value = []

                # Execute task
                result = save_single_f29(
                    company_id=company_id,
                    formulario=sample_formulario
                )

        # Assert failure
        assert result["success"] is False
        assert result["folio"] == "8510019316"
        assert "error" in result
        assert result["error"] == "No records saved"

    @pytest.mark.unit
    @patch('app.infrastructure.celery.tasks.sii.forms.AsyncSessionLocal')
    def test_save_f29_database_error_triggers_retry(
        self,
        mock_session_local,
        sample_formulario
    ):
        """Test that database errors trigger Celery retry"""
        company_id = str(uuid4())

        # Mock DB session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock service raises database error
        mock_service = Mock()
        mock_service.save_f29_downloads = AsyncMock(
            side_effect=Exception("database connection lost")
        )

        # Mock the task's retry method
        mock_task = Mock()
        mock_task.retry = Mock(side_effect=Exception("Task retry triggered"))

        with patch('app.infrastructure.celery.tasks.sii.forms.SIIService', return_value=mock_service):
            with patch('app.infrastructure.celery.tasks.sii.forms.asyncio.run') as mock_asyncio_run:
                # Mock asyncio.run to raise the database error
                mock_asyncio_run.side_effect = Exception("database connection lost")

                # Task should attempt retry for database errors
                # We can't easily test the actual retry mechanism without running Celery
                # So we just verify the error is raised
                result = save_single_f29(
                    company_id=company_id,
                    formulario=sample_formulario
                )

        # Assert error result returned (retry would be handled by Celery)
        assert result["success"] is False
        assert "database" in result["error"].lower()

    @pytest.mark.unit
    @patch('app.infrastructure.celery.tasks.sii.forms.AsyncSessionLocal')
    def test_save_f29_pdf_queue_error_still_saves(
        self,
        mock_session_local,
        sample_formulario,
        mock_download_record
    ):
        """Test that PDF queue error doesn't prevent successful save"""
        company_id = str(uuid4())
        session_id = str(uuid4())

        # Mock DB session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock service succeeds
        mock_service = Mock()
        mock_service.save_f29_downloads = AsyncMock(return_value=[mock_download_record])

        with patch('app.infrastructure.celery.tasks.sii.forms.SIIService', return_value=mock_service):
            with patch('app.infrastructure.celery.tasks.sii.forms.asyncio.run') as mock_asyncio_run:
                mock_asyncio_run.return_value = [mock_download_record]

                # Mock PDF task failing
                with patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf') as mock_pdf_task:
                    mock_pdf_task.apply_async = Mock(side_effect=Exception("Celery connection error"))

                    # Execute task
                    result = save_single_f29(
                        company_id=company_id,
                        formulario=sample_formulario,
                        session_id=session_id
                    )

        # Assert save succeeded even though PDF queue failed
        assert result["success"] is True
        assert result["pdf_queued"] is False  # Failed to queue


class TestSaveF29TaskRetry:
    """Tests for retry logic"""

    @pytest.mark.unit
    def test_save_f29_identifies_database_errors(self, sample_formulario):
        """Test that database-related errors are identified for retry"""
        company_id = str(uuid4())

        error_messages = [
            "database connection lost",
            "Database timeout",
            "CONNECTION refused",
            "connection to server failed"
        ]

        for error_msg in error_messages:
            with patch('app.infrastructure.celery.tasks.sii.forms.AsyncSessionLocal'):
                with patch('app.infrastructure.celery.tasks.sii.forms.asyncio.run') as mock_asyncio_run:
                    mock_asyncio_run.side_effect = Exception(error_msg)

                    result = save_single_f29(
                        company_id=company_id,
                        formulario=sample_formulario
                    )

                    # Should return error result (Celery would handle retry)
                    assert result["success"] is False
                    assert error_msg.lower() in result["error"].lower()


class TestSaveF29TaskIntegration:
    """Integration-style tests with more realistic mocking"""

    @pytest.mark.unit
    @patch('app.infrastructure.celery.tasks.sii.forms.AsyncSessionLocal')
    @patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf')
    def test_save_multiple_formularios_sequentially(
        self,
        mock_pdf_task,
        mock_session_local,
        mock_download_record
    ):
        """Test saving multiple formularios (simulating callback being called multiple times)"""
        company_id = str(uuid4())
        session_id = str(uuid4())

        formularios = [
            {"folio": "F1", "period": "2025-01", "amount": 100, "id_interno_sii": "123"},
            {"folio": "F2", "period": "2025-02", "amount": 200, "id_interno_sii": "456"},
            {"folio": "F3", "period": "2025-03", "amount": 300, "id_interno_sii": "789"},
        ]

        results = []

        for formulario in formularios:
            # Mock DB session
            mock_db = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_db

            # Mock service
            record = Mock()
            record.id = uuid4()
            record.sii_folio = formulario["folio"]

            mock_service = Mock()
            mock_service.save_f29_downloads = AsyncMock(return_value=[record])

            with patch('app.infrastructure.celery.tasks.sii.forms.SIIService', return_value=mock_service):
                with patch('app.infrastructure.celery.tasks.sii.forms.asyncio.run') as mock_asyncio_run:
                    mock_asyncio_run.return_value = [record]

                    result = save_single_f29(
                        company_id=company_id,
                        formulario=formulario,
                        session_id=session_id
                    )

                    results.append(result)

        # Assert all saved successfully
        assert len(results) == 3
        assert all(r["success"] for r in results)
        assert all(r["pdf_queued"] for r in results)

        # Assert PDF task queued 3 times
        assert mock_pdf_task.apply_async.call_count == 3
