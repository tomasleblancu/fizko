"""
Test suite for SII F29 (monthly tax declaration) extraction
"""
import pytest


class TestF29:
    """Test cases for F29 form extraction"""

    def test_get_f29_lista_success(self, sii_client, test_year):
        """Test successful extraction of F29 forms list"""
        formularios = sii_client.get_f29_lista(anio=test_year)

        assert formularios is not None, "F29 lista should not be None"
        assert isinstance(formularios, list), "F29 lista should be a list"

    def test_f29_lista_structure(self, sii_client, test_year):
        """Test structure of F29 form entries"""
        formularios = sii_client.get_f29_lista(anio=test_year)

        if len(formularios) > 0:
            form = formularios[0]
            assert isinstance(form, dict), "Each F29 entry should be a dictionary"

            expected_fields = ['folio', 'period']
            for field in expected_fields:
                assert field in form, f"F29 entry should contain '{field}' field"

    def test_f29_lista_folio_format(self, sii_client, test_year):
        """Test that F29 folios are not empty"""
        formularios = sii_client.get_f29_lista(anio=test_year)

        if len(formularios) > 0:
            form = formularios[0]
            assert form.get('folio'), "F29 folio should not be empty"

    def test_f29_lista_period_format(self, sii_client, test_year):
        """Test that F29 periods are in correct format"""
        formularios = sii_client.get_f29_lista(anio=test_year)

        if len(formularios) > 0:
            form = formularios[0]
            period = form.get('period')
            assert period, "F29 period should not be empty"
            # Period should be in format MM-YYYY or similar
            assert '-' in period or len(period) >= 4, f"Period format seems invalid: {period}"

    def test_f29_lista_count(self, sii_client, test_year):
        """Test that F29 lista returns reasonable number of forms"""
        formularios = sii_client.get_f29_lista(anio=test_year)

        # A year can have at most 12 monthly declarations
        assert len(formularios) <= 12, f"F29 lista should have at most 12 entries, got {len(formularios)}"

    def test_f29_current_year(self, sii_client):
        """Test F29 extraction for current year"""
        from datetime import datetime
        current_year = str(datetime.now().year)

        formularios = sii_client.get_f29_lista(anio=current_year)

        assert formularios is not None, "F29 lista for current year should not be None"
        assert isinstance(formularios, list), "F29 lista should be a list"
