"""
Test suite for SII client performance and optimization
"""
import pytest
import time
from app.integrations.sii import SIIClient


class TestPerformance:
    """Test cases for performance and optimization features"""

    @pytest.mark.slow
    def test_login_performance(self, test_credentials):
        """Test that login completes in reasonable time"""
        start = time.time()

        client = SIIClient(
            tax_id=test_credentials['rut'],
            password=test_credentials['password'],
            headless=True
        )
        client.login()
        duration = time.time() - start
        client.close()

        # Login should complete in less than 30 seconds
        assert duration < 30, f"Login took {duration:.2f}s, should be under 30s"

    def test_cookie_caching(self, sii_client):
        """Test that cookies are cached after login"""
        cookies1 = sii_client.get_cookies()
        cookies2 = sii_client.get_cookies()

        # Should return the same cookies without re-authenticating
        assert len(cookies1) == len(cookies2), "Cookie count should be consistent"

    def test_multiple_extractions_same_session(self, sii_client, test_period):
        """Test that multiple extractions can be performed in same session"""
        # This tests session reuse

        # First extraction
        result1 = sii_client.get_contribuyente()
        assert result1 is not None, "First extraction should succeed"

        # Second extraction
        result2 = sii_client.get_resumen(periodo=test_period)
        assert result2 is not None, "Second extraction should succeed"

        # Third extraction
        result3 = sii_client.get_compras(periodo=test_period, tipo_doc="33")
        assert result3 is not None, "Third extraction should succeed"

    @pytest.mark.slow
    def test_extraction_speed(self, sii_client, test_period):
        """Test that API extractions are reasonably fast"""
        start = time.time()
        sii_client.get_compras(periodo=test_period, tipo_doc="33")
        duration = time.time() - start

        # API calls should complete in less than 10 seconds
        assert duration < 10, f"Extraction took {duration:.2f}s, should be under 10s"
