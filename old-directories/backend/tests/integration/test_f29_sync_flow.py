"""
Integration tests for F29 sync flow.

Tests the complete flow from scraper → Celery → Database → PDF queue.
Uses real database but mocked Selenium for speed.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from sqlalchemy import select

from app.infrastructure.celery.tasks.sii.forms import sync_f29, save_single_f29
from app.db.models.form29_sii_download import Form29SIIDownload
from app.db.models.session import Session as SessionModel
from app.db.models.company import Company


@pytest.fixture
async def test_company(db_session):
    """Create test company"""
    company = Company(
        id=uuid4(),
        legal_name="Test Company S.A.",
        rut="77794858-K"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest.fixture
async def test_session(db_session, test_company, test_user):
    """Create test SII session"""
    session = SessionModel(
        id=uuid4(),
        user_id=test_user.id,
        company_id=test_company.id,
        rut="77794858-K",
        sii_password_encrypted=b"encrypted_password",
        is_active=True,
        cookies={"SESSION": "abc123"}
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
def mock_f29_formularios():
    """Mock F29 formularios with mixed codInt availability"""
    return [
        {
            "folio": "F1",
            "period": "2025-01",
            "contributor": "77794858-K",
            "submission_date": "01/01/2025",
            "status": "Vigente",
            "amount": 100,
            "id_interno_sii": "111"  # Has codInt
        },
        {
            "folio": "F2",
            "period": "2025-02",
            "contributor": "77794858-K",
            "submission_date": "01/02/2025",
            "status": "Vigente",
            "amount": 200,
            "id_interno_sii": "222"  # Has codInt
        },
        {
            "folio": "F3",
            "period": "2025-03",
            "contributor": "77794858-K",
            "submission_date": "01/03/2025",
            "status": "Vigente",
            "amount": 300
            # No codInt
        }
    ]


class TestF29SyncFlowIntegration:
    """Integration tests for complete F29 sync flow"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sync_f29_complete_flow(
        self,
        db_session,
        test_company,
        test_session,
        mock_f29_formularios,
        celery_eager_mode
    ):
        """Test complete sync flow from task to database"""
        # Mock SIIClient to return formularios
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get_f29_lista = Mock(return_value=mock_f29_formularios)
        mock_client.get_cookies = Mock(return_value=[])

        with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
            # Mock download_single_f29_pdf to prevent actual PDF downloads
            with patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf.apply_async'):
                # Execute sync task
                result = sync_f29(
                    session_id=str(test_session.id),
                    year=2025,
                    company_id=str(test_company.id)
                )

        # Assert task succeeded
        assert result["success"] is True
        assert result["forms_synced"] == 3

        # Verify records in database
        stmt = select(Form29SIIDownload).where(
            Form29SIIDownload.company_id == test_company.id
        )
        db_result = await db_session.execute(stmt)
        saved_forms = db_result.scalars().all()

        assert len(saved_forms) == 3

        # Verify forms with codInt
        forms_with_codint = [f for f in saved_forms if f.sii_id_interno]
        assert len(forms_with_codint) == 2

        # Verify forms without codInt
        forms_without_codint = [f for f in saved_forms if not f.sii_id_interno]
        assert len(forms_without_codint) == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sync_f29_pdf_queue_triggered(
        self,
        db_session,
        test_company,
        test_session,
        mock_f29_formularios,
        celery_eager_mode
    ):
        """Test that PDF download is queued for forms with codInt"""
        # Mock SIIClient
        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get_f29_lista = Mock(return_value=mock_f29_formularios)
        mock_client.get_cookies = Mock(return_value=[])

        with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
            with patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf') as mock_pdf_task:
                mock_pdf_task.apply_async = Mock()

                # Execute sync
                sync_f29(
                    session_id=str(test_session.id),
                    year=2025,
                    company_id=str(test_company.id)
                )

        # Assert PDF download queued 2 times (only for forms with codInt)
        assert mock_pdf_task.apply_async.call_count == 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sync_f29_incremental_save(
        self,
        db_session,
        test_company,
        test_session,
        celery_eager_mode
    ):
        """Test that forms are saved incrementally as they are extracted"""
        formularios = [
            {"folio": "F1", "period": "2025-01", "amount": 100, "id_interno_sii": "111"},
            {"folio": "F2", "period": "2025-02", "amount": 200, "id_interno_sii": "222"},
        ]

        # Track save order
        save_order = []

        original_save = save_single_f29.__wrapped__  # Get unwrapped function

        def tracking_save(*args, **kwargs):
            save_order.append(args[1]["folio"])  # Track folio
            return original_save(*args, **kwargs)

        with patch('app.infrastructure.celery.tasks.sii.forms.save_single_f29', side_effect=tracking_save):
            # Mock SIIClient
            mock_client = MagicMock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client.get_f29_lista = Mock(return_value=formularios)
            mock_client.get_cookies = Mock(return_value=[])

            with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
                with patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf.apply_async'):
                    # Execute
                    sync_f29(
                        session_id=str(test_session.id),
                        year=2025,
                        company_id=str(test_company.id)
                    )

        # Assert forms were saved in order
        assert save_order == ["F1", "F2"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sync_f29_handles_duplicate_folios(
        self,
        db_session,
        test_company,
        test_session,
        celery_eager_mode
    ):
        """Test that re-syncing updates existing records"""
        # First sync
        formularios_v1 = [
            {"folio": "F1", "period": "2025-01", "amount": 100, "status": "Vigente"}
        ]

        mock_client = MagicMock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client.get_f29_lista = Mock(return_value=formularios_v1)
        mock_client.get_cookies = Mock(return_value=[])

        with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
            with patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf.apply_async'):
                sync_f29(
                    session_id=str(test_session.id),
                    year=2025,
                    company_id=str(test_company.id)
                )

        # Second sync - same folio, updated data
        formularios_v2 = [
            {"folio": "F1", "period": "2025-01", "amount": 100, "status": "Vigente", "id_interno_sii": "999"}
        ]

        mock_client.get_f29_lista = Mock(return_value=formularios_v2)

        with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
            with patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf.apply_async'):
                sync_f29(
                    session_id=str(test_session.id),
                    year=2025,
                    company_id=str(test_company.id)
                )

        # Verify only 1 record exists (updated, not duplicated)
        stmt = select(Form29SIIDownload).where(
            Form29SIIDownload.company_id == test_company.id,
            Form29SIIDownload.sii_folio == "F1"
        )
        db_result = await db_session.execute(stmt)
        forms = db_result.scalars().all()

        assert len(forms) == 1
        assert forms[0].sii_id_interno == "999"  # Updated


class TestF29SyncFlowErrors:
    """Integration tests for error scenarios"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sync_f29_session_not_found(
        self,
        db_session,
        celery_eager_mode
    ):
        """Test sync fails gracefully when session doesn't exist"""
        non_existent_session = str(uuid4())

        result = sync_f29(
            session_id=non_existent_session,
            year=2025
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sync_f29_company_not_found(
        self,
        db_session,
        test_user,
        celery_eager_mode
    ):
        """Test sync fails when session has no company"""
        # Create session without company
        session = SessionModel(
            id=uuid4(),
            user_id=test_user.id,
            company_id=None,  # No company
            rut="77794858-K",
            sii_password_encrypted=b"encrypted_password",
            is_active=True
        )
        db_session.add(session)
        await db_session.commit()

        result = sync_f29(
            session_id=str(session.id),
            year=2025
        )

        assert result["success"] is False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sync_f29_partial_failure_still_saves(
        self,
        db_session,
        test_company,
        test_session,
        celery_eager_mode
    ):
        """Test that partial scraper failures still save successful extractions"""
        formularios = [
            {"folio": "F1", "period": "2025-01", "amount": 100},
            {"folio": "F2", "period": "2025-02", "amount": 200},
        ]

        # Mock save_single_f29 to fail on first, succeed on second
        call_count = {"count": 0}

        def failing_save(*args, **kwargs):
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise Exception("Database error")
            return save_single_f29.__wrapped__(*args, **kwargs)

        with patch('app.infrastructure.celery.tasks.sii.forms.save_single_f29', side_effect=failing_save):
            mock_client = MagicMock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client.get_f29_lista = Mock(return_value=formularios)
            mock_client.get_cookies = Mock(return_value=[])

            with patch('app.services.sii.form_service.SIIClient', return_value=mock_client):
                with patch('app.infrastructure.celery.tasks.sii.forms.download_single_f29_pdf.apply_async'):
                    # Execute - should not fail completely
                    result = sync_f29(
                        session_id=str(test_session.id),
                        year=2025,
                        company_id=str(test_company.id)
                    )

        # Task succeeds (extraction completed)
        assert result["success"] is True

        # Only 1 form saved (F2)
        stmt = select(Form29SIIDownload).where(
            Form29SIIDownload.company_id == test_company.id
        )
        db_result = await db_session.execute(stmt)
        saved_forms = db_result.scalars().all()

        assert len(saved_forms) == 1
        assert saved_forms[0].sii_folio == "F2"
