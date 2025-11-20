# Tests - SII Integration Service

Tests End-to-End para el servicio de integración con el SII.

## ⚠️ Importante

**Estos tests hacen requests REALES al portal del SII**. Por lo tanto:

- ✅ Requieren credenciales válidas del SII
- ⏱️ Son lentos (pueden tomar varios minutos)
- 🌐 Requieren conexión a internet
- 🔒 Usan credenciales de prueba (NO usar credenciales de producción)

## Configuración

### 1. Instalar Dependencias de Testing

```bash
# Con uv (recomendado)
uv sync --extra dev

# O con pip
pip install -e ".[dev]"
```

### 2. Configurar Credenciales de Prueba

Editar el archivo `.env.test` con credenciales válidas:

```bash
# Copiar template
cp .env.test.example .env.test

# Editar con tus credenciales
nano .env.test
```

**Contenido de `.env.test`:**
```env
# Credenciales SII para tests E2E
TEST_SII_RUT=77794858
TEST_SII_DV=K
TEST_SII_PASSWORD=SiiPfufl574@#

# Periodo de prueba (ajustar según disponibilidad de datos)
TEST_PERIODO=202411

# URL del servidor (debe estar corriendo)
TEST_SERVER_URL=http://localhost:8090
```

### 3. Iniciar el Servidor

Los tests requieren que el servidor esté corriendo:

```bash
# En una terminal separada
./start.sh

# O manualmente
uv run uvicorn app.main:app --reload --port 8090
```

## Ejecutar Tests

### Ejecutar Todos los Tests

```bash
pytest tests/test_endpoints_e2e.py -v
```

### Ejecutar con Output Detallado

```bash
pytest tests/test_endpoints_e2e.py -v -s
```

### Ejecutar un Test Específico

```bash
# Solo el test de login
pytest tests/test_endpoints_e2e.py::TestLoginEndpoint::test_login_success -v

# Solo tests de compras
pytest tests/test_endpoints_e2e.py::TestComprasEndpoint -v

# Solo el flujo completo
pytest tests/test_endpoints_e2e.py::TestCookieReuseFlow::test_complete_flow_with_cookie_reuse -v -s
```

### Ejecutar con Coverage

```bash
pytest tests/test_endpoints_e2e.py --cov=app --cov-report=html
```

Luego abrir `htmlcov/index.html` en el navegador.

## Estructura de Tests

### Tests por Endpoint

| Clase de Test | Endpoint | Descripción |
|---------------|----------|-------------|
| `TestLoginEndpoint` | `/api/sii/login` | Login, cookies, credenciales inválidas |
| `TestComprasEndpoint` | `/api/sii/compras` | Compras con/sin cookies |
| `TestVentasEndpoint` | `/api/sii/ventas` | Ventas, validación de periodo |
| `TestF29Endpoint` | `/api/sii/f29` | Propuesta F29 |
| `TestBoletasHonorariosEndpoint` | `/api/sii/boletas-honorarios` | Boletas de honorarios |
| `TestContribuyenteEndpoint` | `/api/sii/contribuyente` | Info del contribuyente |
| `TestHealthEndpoint` | `/api/sii/health` | Health check |
| `TestCookieReuseFlow` | Múltiples | Flujo completo con reutilización de cookies |

### Tests Específicos

#### `test_login_success`
Verifica que el login sea exitoso y retorne cookies válidas.

```bash
pytest tests/test_endpoints_e2e.py::TestLoginEndpoint::test_login_success -v -s
```

#### `test_login_with_invalid_credentials`
Verifica que credenciales inválidas sean rechazadas correctamente.

```bash
pytest tests/test_endpoints_e2e.py::TestLoginEndpoint::test_login_with_invalid_credentials -v -s
```

#### `test_complete_flow_with_cookie_reuse`
Flujo completo que valida la reutilización de cookies en múltiples requests.

```bash
pytest tests/test_endpoints_e2e.py::TestCookieReuseFlow::test_complete_flow_with_cookie_reuse -v -s
```

## Output Esperado

### Test Exitoso

```
tests/test_endpoints_e2e.py::TestLoginEndpoint::test_login_success
✅ Login exitoso. 12 cookies guardadas.
PASSED

tests/test_endpoints_e2e.py::TestComprasEndpoint::test_get_compras_with_cookies
✅ Compras con cookies: 15 documentos (más rápido)
PASSED
```

### Test Fallido

```
tests/test_endpoints_e2e.py::TestLoginEndpoint::test_login_with_invalid_credentials
✅ Login con credenciales inválidas correctamente rechazado.
PASSED
```

## Troubleshooting

### Error: "TEST_SII_PASSWORD no está configurada"

**Solución**: Configurar las credenciales en `.env.test`

```bash
# Verificar que el archivo existe
ls -la .env.test

# Verificar contenido
cat .env.test
```

### Error: "Connection refused"

**Solución**: El servidor no está corriendo. Iniciarlo:

```bash
./start.sh
```

### Error: "Error de autenticación"

**Solución**: Verificar credenciales en `.env.test`. Las credenciales deben ser válidas.

### Tests muy lentos

**Causa**: Los tests E2E hacen scraping real del SII, lo cual es lento.

**Optimización**:
- Usar reutilización de cookies (ya implementado en los tests)
- Ejecutar solo tests específicos en lugar de toda la suite

### Error: "chromedriver not found"

**Solución**: El chromedriver se descarga automáticamente la primera vez. Si hay problemas:

```bash
# Verificar que Chrome está instalado
google-chrome --version  # Linux
"Google Chrome" --version  # Mac

# Limpiar cache de webdriver-manager
rm -rf ~/.wdm
```

## Mejores Prácticas

1. **NO usar credenciales de producción** en tests
2. **Ejecutar tests en ambiente de desarrollo** únicamente
3. **No ejecutar tests muy frecuentemente** para evitar sobrecarga al SII
4. **Usar reutilización de cookies** para tests más rápidos
5. **Ejecutar tests específicos** durante desarrollo

## Agregar Nuevos Tests

Para agregar un nuevo test:

```python
class TestNuevoEndpoint:
    """Tests para nuevo endpoint."""

    def test_nuevo_caso(self, api_base_url, credentials):
        """Test: Descripción del caso de prueba."""
        # Arrange
        url = f"{api_base_url}/nuevo-endpoint"
        request_data = {**credentials}

        # Act
        response = requests.post(url, json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        print("\n✅ Nuevo test completado")
```

## CI/CD

Para ejecutar tests en CI/CD, configurar las siguientes variables de entorno:

- `TEST_SII_RUT`
- `TEST_SII_DV`
- `TEST_SII_PASSWORD`
- `TEST_PERIODO`
- `TEST_SERVER_URL`

**Ejemplo GitHub Actions:**

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --extra dev

      - name: Start server
        run: |
          uv run uvicorn app.main:app --port 8090 &
          sleep 5

      - name: Run tests
        env:
          TEST_SII_RUT: ${{ secrets.TEST_SII_RUT }}
          TEST_SII_DV: ${{ secrets.TEST_SII_DV }}
          TEST_SII_PASSWORD: ${{ secrets.TEST_SII_PASSWORD }}
          TEST_PERIODO: "202411"
        run: |
          pytest tests/test_endpoints_e2e.py -v
```

## Soporte

Para problemas con los tests:

1. Verificar que el servidor esté corriendo
2. Verificar credenciales en `.env.test`
3. Verificar logs del servidor
4. Ejecutar tests individuales para aislar el problema
