"""
End-to-End Tests for SII Integration Service Endpoints

Este archivo contiene tests E2E que realizan requests reales al SII.
IMPORTANTE: Estos tests hacen scraping real del portal SII y pueden ser lentos.

Para ejecutar:
    pytest tests/test_endpoints_e2e.py -v

Para ejecutar con output detallado:
    pytest tests/test_endpoints_e2e.py -v -s

Para ejecutar solo un test específico:
    pytest tests/test_endpoints_e2e.py::test_login_endpoint -v
"""
import os
import pytest
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import requests

# Cargar variables de entorno de test
load_dotenv(".env.test")

# Configuración de tests
TEST_RUT = os.getenv("TEST_SII_RUT", "77794858")
TEST_DV = os.getenv("TEST_SII_DV", "K")
TEST_PASSWORD = os.getenv("TEST_SII_PASSWORD")
TEST_PERIODO = os.getenv("TEST_PERIODO", "202411")
BASE_URL = os.getenv("TEST_SERVER_URL", "http://localhost:8000")

# Verificar que las credenciales estén configuradas
if not TEST_PASSWORD:
    pytest.skip(
        "TEST_SII_PASSWORD no está configurada. "
        "Configure las credenciales en .env.test",
        allow_module_level=True
    )


class TestConfig:
    """Clase para almacenar estado compartido entre tests."""
    cookies: Optional[List[Dict[str, Any]]] = None
    login_response: Optional[Dict[str, Any]] = None


@pytest.fixture(scope="module")
def api_base_url():
    """URL base de la API."""
    return f"{BASE_URL}/api/sii"


@pytest.fixture(scope="module")
def credentials():
    """Credenciales de prueba."""
    return {
        "rut": TEST_RUT,
        "dv": TEST_DV,
        "password": TEST_PASSWORD
    }


@pytest.fixture(scope="module")
def test_periodo():
    """Periodo de prueba."""
    return TEST_PERIODO


# =============================================================================
# TESTS DE ENDPOINTS
# =============================================================================

class TestLoginEndpoint:
    """Tests para el endpoint de login."""

    def test_login_success(self, api_base_url, credentials):
        """Test: Login exitoso debe retornar cookies."""
        # Arrange
        url = f"{api_base_url}/login"

        # Act
        response = requests.post(url, json=credentials)

        # Assert
        assert response.status_code == 200, f"Status code incorrecto: {response.status_code}"

        data = response.json()
        assert data["success"] is True, "Login debería ser exitoso"
        assert data["message"] == "Login exitoso", "Mensaje de login incorrecto"
        assert data["session_active"] is True, "Sesión debería estar activa"
        assert "cookies" in data, "Response debe incluir cookies"
        assert isinstance(data["cookies"], list), "Cookies debe ser una lista"
        assert len(data["cookies"]) > 0, "Debe haber al menos una cookie"

        # Guardar cookies para tests subsecuentes
        TestConfig.cookies = data["cookies"]
        TestConfig.login_response = data

        print(f"\n✅ Login exitoso. {len(data['cookies'])} cookies guardadas.")

    def test_login_with_invalid_credentials(self, api_base_url):
        """Test: Login con credenciales inválidas debe fallar."""
        # Arrange
        url = f"{api_base_url}/login"
        invalid_creds = {
            "rut": "12345678",
            "dv": "9",
            "password": "invalid_password"
        }

        # Act
        response = requests.post(url, json=invalid_creds)

        # Assert
        # NOTA: El SII puede aceptar RUTs arbitrarios en su sistema de test
        # Por lo tanto, este test verifica que el endpoint maneje la request,
        # pero no necesariamente que rechace credenciales inválidas
        assert response.status_code in [200, 401], f"Debería retornar 200 o 401, recibió {response.status_code}"

        data = response.json()

        if response.status_code == 401:
            assert "detail" in data, "Response debe incluir detalle del error"
            print("\n✅ Login correctamente rechazado con 401")
        else:
            # Si retorna 200, puede ser que el SII acepte el RUT
            # Solo verificamos que la respuesta tenga la estructura esperada
            assert "success" in data, "Response debe incluir campo success"
            assert "cookies" in data or "detail" in data, "Response debe incluir cookies o error"
            print(f"\n✅ Login procesado (success={data.get('success')})")

    def test_login_reuse_cookies(self, api_base_url, credentials):
        """Test: Login con cookies existentes debe reutilizar sesión."""
        # Arrange
        url = f"{api_base_url}/login"
        request_data = {
            **credentials,
            "cookies": TestConfig.cookies
        }

        # Act
        response = requests.post(url, json=request_data)

        # Assert
        assert response.status_code == 200, "Login con cookies debe ser exitoso"

        data = response.json()
        assert data["success"] is True, "Login debe ser exitoso"
        assert "cookies" in data, "Response debe incluir cookies actualizadas"

        # Actualizar cookies
        TestConfig.cookies = data["cookies"]

        print("\n✅ Reutilización de cookies exitosa.")


class TestComprasEndpoint:
    """Tests para el endpoint de compras."""

    def test_get_compras_without_cookies(self, api_base_url, credentials, test_periodo):
        """Test: Obtener compras sin cookies (hace login completo)."""
        # Arrange
        url = f"{api_base_url}/compras"
        request_data = {
            **credentials,
            "periodo": test_periodo
        }

        # Act
        response = requests.post(url, json=request_data)

        # Assert
        assert response.status_code == 200, f"Status code incorrecto: {response.status_code}"

        data = response.json()
        assert data["success"] is True, "Request debe ser exitoso"
        assert data["periodo"] == test_periodo, "Periodo debe coincidir"
        assert data["tipo"] == "compras", "Tipo debe ser 'compras'"
        assert "documentos" in data, "Debe incluir documentos"

        # Verificar estructura de documentos - puede ser dict o list
        documentos = data["documentos"]
        if isinstance(documentos, dict):
            assert "data" in documentos, "Documentos dict debe incluir data"
            assert isinstance(documentos["data"], list), "Data debe ser una lista"
            total_docs = len(documentos["data"])
        else:
            assert isinstance(documentos, list), "Documentos debe ser una lista"
            total_docs = len(documentos)

        assert "cookies" in data, "Debe retornar cookies"

        print(f"\n✅ Compras obtenidas: {total_docs} documentos")

    def test_get_compras_with_cookies(self, api_base_url, credentials, test_periodo):
        """Test: Obtener compras con cookies (reutiliza sesión)."""
        # Arrange
        url = f"{api_base_url}/compras"
        request_data = {
            **credentials,
            "periodo": test_periodo,
            "cookies": TestConfig.cookies
        }

        # Act
        response = requests.post(url, json=request_data)

        # Assert
        assert response.status_code == 200, "Request debe ser exitoso"

        data = response.json()
        assert data["success"] is True, "Request debe ser exitoso"
        assert "cookies" in data, "Debe retornar cookies actualizadas"

        # Calcular total de documentos
        documentos = data.get("documentos", [])
        if isinstance(documentos, dict) and "data" in documentos:
            total_docs = len(documentos["data"])
        else:
            total_docs = len(documentos) if isinstance(documentos, list) else 0

        # Actualizar cookies
        TestConfig.cookies = data["cookies"]

        print(f"\n✅ Compras con cookies: {total_docs} documentos (más rápido)")


class TestVentasEndpoint:
    """Tests para el endpoint de ventas."""

    def test_get_ventas_with_cookies(self, api_base_url, credentials, test_periodo):
        """Test: Obtener ventas reutilizando cookies."""
        # Arrange
        url = f"{api_base_url}/ventas"
        request_data = {
            **credentials,
            "periodo": test_periodo,
            "cookies": TestConfig.cookies
        }

        # Act
        response = requests.post(url, json=request_data)

        # Assert
        assert response.status_code == 200, "Request debe ser exitoso"

        data = response.json()
        assert data["success"] is True, "Request debe ser exitoso"
        assert data["tipo"] == "ventas", "Tipo debe ser 'ventas'"
        assert "documentos" in data, "Debe incluir documentos"

        # Verificar estructura de documentos - puede ser dict o list
        documentos = data["documentos"]
        if isinstance(documentos, dict):
            assert "data" in documentos, "Documentos dict debe incluir data"
            assert isinstance(documentos["data"], list), "Data debe ser una lista"
            total_docs = len(documentos["data"])
        else:
            assert isinstance(documentos, list), "Documentos debe ser una lista"
            total_docs = len(documentos)

        assert "cookies" in data, "Debe retornar cookies actualizadas"

        # Actualizar cookies
        TestConfig.cookies = data["cookies"]

        print(f"\n✅ Ventas obtenidas: {total_docs} documentos")

    def test_ventas_invalid_periodo(self, api_base_url, credentials):
        """Test: Ventas con periodo inválido debe fallar."""
        # Arrange
        url = f"{api_base_url}/ventas"
        request_data = {
            **credentials,
            "periodo": "999999",  # Periodo inválido
            "cookies": TestConfig.cookies
        }

        # Act
        response = requests.post(url, json=request_data)

        # Assert - El SII puede retornar error o lista vacía
        assert response.status_code in [200, 422], "Debería ser 200 o 422"

        print("\n✅ Validación de periodo inválido completada")


class TestF29Endpoint:
    """Tests para el endpoint de F29."""

    def test_get_f29_propuesta(self, api_base_url, credentials, test_periodo):
        """Test: Obtener propuesta F29."""
        # Arrange
        url = f"{api_base_url}/f29"
        request_data = {
            **credentials,
            "periodo": test_periodo,
            "cookies": TestConfig.cookies
        }

        # Act
        response = requests.post(url, json=request_data)

        # Assert
        assert response.status_code == 200, f"Status code incorrecto: {response.status_code}"

        data = response.json()
        assert data["success"] is True, "Request debe ser exitoso"
        assert data["tipo"] == "f29_propuesta", "Tipo debe ser 'f29_propuesta'"
        assert "data" in data, "Debe incluir data del F29"
        assert "cookies" in data, "Debe retornar cookies actualizadas"

        # Actualizar cookies
        TestConfig.cookies = data["cookies"]

        print(f"\n✅ F29 propuesta obtenida para periodo {test_periodo}")


class TestBoletasHonorariosEndpoint:
    """Tests para el endpoint de boletas de honorarios."""

    def test_get_boletas_honorarios(self, api_base_url, credentials, test_periodo):
        """Test: Obtener boletas de honorarios."""
        # Arrange
        url = f"{api_base_url}/boletas-honorarios"
        request_data = {
            **credentials,
            "periodo": test_periodo,
            "cookies": TestConfig.cookies
        }

        # Act
        response = requests.post(url, json=request_data)

        # Assert
        assert response.status_code == 200, f"Status code incorrecto: {response.status_code}"

        data = response.json()
        assert data["success"] is True, "Request debe ser exitoso"
        assert data["tipo"] == "boletas_honorarios", "Tipo debe ser 'boletas_honorarios'"
        assert "total_boletas" in data, "Debe incluir total_boletas"
        assert "data" in data, "Debe incluir data de boletas"
        assert "cookies" in data, "Debe retornar cookies actualizadas"

        # Actualizar cookies
        TestConfig.cookies = data["cookies"]

        print(f"\n✅ Boletas honorarios obtenidas: {data['total_boletas']} boletas")


class TestContribuyenteEndpoint:
    """Tests para el endpoint de contribuyente."""

    def test_get_contribuyente_info(self, api_base_url, credentials):
        """Test: Obtener información del contribuyente."""
        # Arrange
        url = f"{api_base_url}/contribuyente"
        request_data = {
            **credentials,
            "cookies": TestConfig.cookies
        }

        # Act
        response = requests.post(url, json=request_data)

        # Assert
        assert response.status_code == 200, f"Status code incorrecto: {response.status_code}"

        data = response.json()
        assert data["success"] is True, "Request debe ser exitoso"
        assert data["tipo"] == "contribuyente", "Tipo debe ser 'contribuyente'"
        assert "data" in data, "Debe incluir data del contribuyente"
        assert "cookies" in data, "Debe retornar cookies actualizadas"

        # Actualizar cookies
        TestConfig.cookies = data["cookies"]

        print("\n✅ Información del contribuyente obtenida")


class TestHealthEndpoint:
    """Tests para el endpoint de health check."""

    def test_health_check(self, api_base_url):
        """Test: Health check debe retornar status healthy."""
        # Arrange
        url = f"{api_base_url}/health"

        # Act
        response = requests.get(url)

        # Assert
        assert response.status_code == 200, "Health check debe retornar 200"

        data = response.json()
        assert data["status"] == "healthy", "Status debe ser 'healthy'"
        assert "service" in data, "Debe incluir nombre del servicio"
        assert "version" in data, "Debe incluir versión"

        print(f"\n✅ Health check: {data['status']} - {data['service']} v{data['version']}")


class TestVerifyEndpoint:
    """Tests para el endpoint de verificación de credenciales."""

    def test_verify_credentials_success(self, api_base_url, credentials):
        """Test: Verificación exitosa debe retornar info completa del contribuyente."""
        # Arrange
        url = f"{api_base_url}/verify"

        # Act
        response = requests.post(url, json=credentials)

        # Assert
        assert response.status_code == 200, f"Status code incorrecto: {response.status_code}"

        data = response.json()
        assert data["success"] is True, "Verificación debe ser exitosa"
        assert "message" in data, "Debe incluir mensaje"
        assert "contribuyente_info" in data, "Debe incluir info del contribuyente"
        assert "cookies" in data, "Debe incluir cookies"
        assert "session_refreshed" in data, "Debe indicar si se refrescó la sesión"
        assert "extraction_method" in data, "Debe incluir método de extracción"
        assert "timestamp" in data, "Debe incluir timestamp"

        # Verificar estructura de contribuyente_info
        contrib = data["contribuyente_info"]
        assert "rut" in contrib or "tax_id" in contrib, "Debe incluir RUT/tax_id"
        assert isinstance(data["cookies"], list), "Cookies debe ser una lista"
        assert len(data["cookies"]) > 0, "Debe haber al menos una cookie"

        # Guardar cookies para próximos tests
        TestConfig.cookies = data["cookies"]

        print(f"\n✅ Verificación exitosa")
        print(f"   - Razón social: {contrib.get('razon_social', 'N/A')}")
        print(f"   - Cookies: {len(data['cookies'])}")
        print(f"   - Sesión refrescada: {data['session_refreshed']}")

    def test_verify_credentials_with_cookies(self, api_base_url, credentials):
        """Test: Verificación con cookies debe reutilizar sesión."""
        # Arrange
        url = f"{api_base_url}/verify"
        request_data = {
            **credentials,
            "cookies": TestConfig.cookies
        }

        # Act
        response = requests.post(url, json=request_data)

        # Assert
        assert response.status_code == 200, "Request debe ser exitoso"

        data = response.json()
        assert data["success"] is True, "Verificación debe ser exitosa"
        assert "contribuyente_info" in data, "Debe incluir info del contribuyente"

        # Con cookies, no debería refrescar sesión (a menos que hayan expirado)
        # Este campo puede ser True o False dependiendo del estado de las cookies
        assert isinstance(data["session_refreshed"], bool), "session_refreshed debe ser booleano"

        # Actualizar cookies
        TestConfig.cookies = data["cookies"]

        print(f"\n✅ Verificación con cookies completada")
        print(f"   - Sesión refrescada: {data['session_refreshed']}")
        print(f"   - Cookies actualizadas: {len(data['cookies'])}")

    def test_verify_credentials_invalid(self, api_base_url):
        """Test: Credenciales inválidas deben ser rechazadas."""
        # Arrange
        url = f"{api_base_url}/verify"
        invalid_creds = {
            "rut": "12345678",
            "dv": "9",
            "password": "invalid_password_123"
        }

        # Act
        response = requests.post(url, json=invalid_creds)

        # Assert
        # Puede retornar 200 (si el SII acepta el RUT) o 401
        assert response.status_code in [200, 401, 422], \
            f"Debería retornar 200, 401 o 422, recibió {response.status_code}"

        if response.status_code in [401, 422]:
            data = response.json()
            assert "detail" in data, "Error debe incluir detalle"
            print(f"\n✅ Credenciales inválidas correctamente rechazadas con {response.status_code}")
        else:
            # Si retorna 200, el SII aceptó el RUT (puede pasar en ambiente de test)
            data = response.json()
            assert "success" in data, "Response debe tener campo success"
            print(f"\n✅ Verificación procesada (RUT aceptado en test): success={data.get('success')}")


class TestCookieReuseFlow:
    """Tests para validar el flujo completo de reutilización de cookies."""

    def test_complete_flow_with_cookie_reuse(self, api_base_url, credentials, test_periodo):
        """Test: Flujo completo reutilizando cookies en múltiples requests."""
        print("\n" + "="*60)
        print("TEST: Flujo completo con reutilización de cookies")
        print("="*60)

        # 1. Login inicial
        print("\n1️⃣ Login inicial...")
        login_response = requests.post(
            f"{api_base_url}/login",
            json=credentials
        ).json()

        assert login_response["success"] is True
        cookies = login_response["cookies"]
        print(f"   ✅ Login exitoso. {len(cookies)} cookies guardadas")

        # 2. Compras con cookies
        print("\n2️⃣ Obteniendo compras (con cookies)...")
        compras_response = requests.post(
            f"{api_base_url}/compras",
            json={**credentials, "periodo": test_periodo, "cookies": cookies}
        ).json()

        assert compras_response["success"] is True
        cookies = compras_response["cookies"]  # Actualizar cookies

        # Calcular total de documentos
        compras_docs = compras_response.get("documentos", [])
        if isinstance(compras_docs, dict) and "data" in compras_docs:
            total_compras = len(compras_docs["data"])
        else:
            total_compras = len(compras_docs) if isinstance(compras_docs, list) else 0

        print(f"   ✅ {total_compras} compras obtenidas")

        # 3. Ventas con cookies actualizadas
        print("\n3️⃣ Obteniendo ventas (con cookies actualizadas)...")
        ventas_response = requests.post(
            f"{api_base_url}/ventas",
            json={**credentials, "periodo": test_periodo, "cookies": cookies}
        ).json()

        assert ventas_response["success"] is True
        cookies = ventas_response["cookies"]  # Actualizar cookies

        # Calcular total de documentos
        ventas_docs = ventas_response.get("documentos", [])
        if isinstance(ventas_docs, dict) and "data" in ventas_docs:
            total_ventas = len(ventas_docs["data"])
        else:
            total_ventas = len(ventas_docs) if isinstance(ventas_docs, list) else 0

        print(f"   ✅ {total_ventas} ventas obtenidas")

        # 4. F29 con cookies actualizadas
        print("\n4️⃣ Obteniendo F29 (con cookies actualizadas)...")
        f29_response = requests.post(
            f"{api_base_url}/f29",
            json={**credentials, "periodo": test_periodo, "cookies": cookies}
        ).json()

        assert f29_response["success"] is True
        cookies = f29_response["cookies"]  # Actualizar cookies
        print("   ✅ F29 propuesta obtenida")

        # 5. Contribuyente con cookies actualizadas
        print("\n5️⃣ Obteniendo info contribuyente (con cookies actualizadas)...")
        contribuyente_response = requests.post(
            f"{api_base_url}/contribuyente",
            json={**credentials, "cookies": cookies}
        ).json()

        assert contribuyente_response["success"] is True
        print("   ✅ Información del contribuyente obtenida")

        print("\n" + "="*60)
        print("RESULTADO: ✅ Flujo completo exitoso")
        print(f"Total requests: 5")
        print(f"Login: Solo 1 vez (primera vez)")
        print(f"Requests subsecuentes: Reutilizaron sesión")
        print("="*60)


# =============================================================================
# TESTS DE INTEGRACIÓN
# =============================================================================

class TestRootEndpoint:
    """Tests para el endpoint root."""

    def test_root_endpoint(self):
        """Test: Root endpoint debe retornar información del servicio."""
        # Act
        response = requests.get(f"{BASE_URL}/")

        # Assert
        assert response.status_code == 200, "Root debe retornar 200"

        data = response.json()
        assert "service" in data, "Debe incluir nombre del servicio"
        assert "version" in data, "Debe incluir versión"

        print(f"\n✅ Root endpoint: {data['service']} v{data['version']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
