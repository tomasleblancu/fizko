"""
Test suite for SII contribuyente (taxpayer) information extraction
"""
import pytest


class TestContribuyente:
    """Test cases for contribuyente information extraction"""

    def test_get_contribuyente_success(self, sii_client):
        """Test successful extraction of contribuyente information"""
        info = sii_client.get_contribuyente()

        assert info is not None, "Contribuyente info should not be None"
        assert isinstance(info, dict), "Contribuyente info should be a dictionary"

    def test_contribuyente_has_rut(self, sii_client):
        """Test that contribuyente info contains RUT"""
        info = sii_client.get_contribuyente()

        assert 'rut' in info, "Contribuyente info should contain 'rut' field"
        assert info['rut'], "RUT should not be empty"

    def test_contribuyente_has_razon_social(self, sii_client):
        """Test that contribuyente info contains business name"""
        info = sii_client.get_contribuyente()

        assert 'razon_social' in info, "Contribuyente info should contain 'razon_social' field"
        assert info['razon_social'], "Razón social should not be empty"

    def test_contribuyente_fields(self, sii_client):
        """Test that all expected fields are present in contribuyente info"""
        info = sii_client.get_contribuyente()

        expected_fields = ['rut', 'razon_social']
        for field in expected_fields:
            assert field in info, f"Contribuyente info should contain '{field}' field"

    def test_contribuyente_rut_format(self, sii_client, test_credentials):
        """Test that RUT in contribuyente matches test RUT"""
        info = sii_client.get_contribuyente()

        # Extract just the number part for comparison
        test_rut_base = test_credentials['rut'].split('-')[0]
        info_rut_base = info['rut'].split('-')[0]

        assert test_rut_base == info_rut_base, f"Contribuyente RUT should match test RUT"
