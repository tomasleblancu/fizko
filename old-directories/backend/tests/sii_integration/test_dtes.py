"""
Test suite for SII DTE (electronic tax documents) extraction
"""
import pytest


class TestDTEsCompras:
    """Test cases for purchase DTEs (compras) extraction"""

    def test_get_compras_success(self, sii_client, test_period):
        """Test successful extraction of purchase DTEs"""
        result = sii_client.get_compras(periodo=test_period, tipo_doc="33")

        assert result is not None, "Compras result should not be None"
        assert isinstance(result, dict), "Compras result should be a dictionary"

    def test_compras_has_status(self, sii_client, test_period):
        """Test that compras response includes status"""
        result = sii_client.get_compras(periodo=test_period, tipo_doc="33")

        assert 'status' in result, "Compras response should include 'status' field"
        assert result['status'] == 'success', "Status should be 'success'"

    def test_compras_has_data(self, sii_client, test_period):
        """Test that compras response includes data field"""
        result = sii_client.get_compras(periodo=test_period, tipo_doc="33")

        assert 'data' in result, "Compras response should include 'data' field"
        assert isinstance(result['data'], list), "Data should be a list"

    def test_compras_extraction_method(self, sii_client, test_period):
        """Test that extraction method is reported"""
        result = sii_client.get_compras(periodo=test_period, tipo_doc="33")

        assert 'extraction_method' in result, "Response should include 'extraction_method'"

    def test_compras_document_structure(self, sii_client, test_period):
        """Test structure of purchase documents if any exist"""
        result = sii_client.get_compras(periodo=test_period, tipo_doc="33")

        if result.get('data') and len(result['data']) > 0:
            doc = result['data'][0]
            # Check for actual fields returned by SII API
            # The API returns fields like detNroDoc (folio), detMntTotal (monto_total)
            assert 'detNroDoc' in doc or 'detMntTotal' in doc, "Purchase document should contain document fields"


class TestDTEsVentas:
    """Test cases for sales DTEs (ventas) extraction"""

    def test_get_ventas_success(self, sii_client, test_period):
        """Test successful extraction of sales DTEs"""
        result = sii_client.get_ventas(periodo=test_period, tipo_doc="33")

        assert result is not None, "Ventas result should not be None"
        assert isinstance(result, dict), "Ventas result should be a dictionary"

    def test_ventas_has_status(self, sii_client, test_period):
        """Test that ventas response includes status"""
        result = sii_client.get_ventas(periodo=test_period, tipo_doc="33")

        assert 'status' in result, "Ventas response should include 'status' field"
        assert result['status'] == 'success', "Status should be 'success'"

    def test_ventas_has_data(self, sii_client, test_period):
        """Test that ventas response includes data field"""
        result = sii_client.get_ventas(periodo=test_period, tipo_doc="33")

        assert 'data' in result, "Ventas response should include 'data' field"
        assert isinstance(result['data'], list), "Data should be a list"

    def test_ventas_extraction_method(self, sii_client, test_period):
        """Test that extraction method is reported"""
        result = sii_client.get_ventas(periodo=test_period, tipo_doc="33")

        assert 'extraction_method' in result, "Response should include 'extraction_method'"


class TestDTEsResumen:
    """Test cases for purchase/sales summary extraction"""

    def test_get_resumen_success(self, sii_client, test_period):
        """Test successful extraction of purchase/sales summary"""
        result = sii_client.get_resumen(periodo=test_period)

        assert result is not None, "Resumen result should not be None"
        assert isinstance(result, dict), "Resumen result should be a dictionary"

    def test_resumen_has_status(self, sii_client, test_period):
        """Test that resumen response includes status"""
        result = sii_client.get_resumen(periodo=test_period)

        assert 'status' in result, "Resumen response should include 'status' field"
        assert result['status'] == 'success', "Status should be 'success'"

    def test_resumen_has_data(self, sii_client, test_period):
        """Test that resumen includes compras and ventas data"""
        result = sii_client.get_resumen(periodo=test_period)

        assert 'data' in result, "Resumen should include 'data' field"
        data = result['data']

        # The API returns 'resumen_compras' and 'resumen_ventas', not 'compras' and 'ventas'
        assert 'resumen_compras' in data, "Data should include 'resumen_compras'"
        assert 'resumen_ventas' in data, "Data should include 'resumen_ventas'"
        assert isinstance(data['resumen_compras'], dict), "Resumen compras should be a dictionary"
        assert isinstance(data['resumen_ventas'], dict), "Resumen ventas should be a dictionary"
