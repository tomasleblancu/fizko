# SII Integration Tests

Suite de tests profesional para el módulo de integración con el SII (Servicio de Impuestos Internos de Chile).

## Estructura

```
tests/
├── conftest.py                 # Configuración de pytest y fixtures compartidos
├── test_authentication.py      # Tests de autenticación y login
├── test_contribuyente.py       # Tests de extracción de datos del contribuyente
├── test_dtes.py               # Tests de extracción de DTEs (compras/ventas)
├── test_f29.py                # Tests de extracción de formularios F29
├── test_performance.py        # Tests de rendimiento y optimización
└── README.md                  # Esta documentación
```

## Requisitos

- Python 3.9+
- pytest
- Chrome/Chromium (para Selenium)
- Credenciales válidas del SII

## Instalación

```bash
pip install pytest pytest-cov
```

## Configuración

Las credenciales de prueba están definidas en `conftest.py`. Para usar credenciales diferentes, modifica:

```python
TEST_RUT = "tu-rut-aqui"
TEST_PASSWORD = "tu-password-aqui"
```

## Ejecución de Tests

### Todos los tests

```bash
# Desde el directorio backend/
pytest app/integrations/sii/tests/

# Con output verbose
pytest app/integrations/sii/tests/ -v

# Con coverage
pytest app/integrations/sii/tests/ --cov=app.integrations.sii
```

### Tests específicos por archivo

```bash
# Solo tests de autenticación
pytest app/integrations/sii/tests/test_authentication.py

# Solo tests de DTEs
pytest app/integrations/sii/tests/test_dtes.py

# Solo tests de F29
pytest app/integrations/sii/tests/test_f29.py
```

### Tests específicos por clase o función

```bash
# Solo una clase específica
pytest app/integrations/sii/tests/test_dtes.py::TestDTEsCompras

# Solo un test específico
pytest app/integrations/sii/tests/test_authentication.py::TestAuthentication::test_login_success
```

### Filtros y marcadores

```bash
# Excluir tests lentos
pytest app/integrations/sii/tests/ -m "not slow"

# Solo tests de rendimiento
pytest app/integrations/sii/tests/test_performance.py
```

## Fixtures Disponibles

### `sii_client`
Cliente SII autenticado y listo para usar. Se cierra automáticamente al finalizar el test.

```python
def test_example(sii_client):
    info = sii_client.get_contribuyente()
    assert info is not None
```

### `sii_client_no_login`
Cliente SII sin autenticar. Útil para tests de autenticación.

```python
def test_login(sii_client_no_login):
    success = sii_client_no_login.login()
    assert success is True
```

### `test_credentials`
Diccionario con credenciales de prueba.

```python
def test_example(test_credentials):
    assert test_credentials['rut']
    assert test_credentials['password']
```

### `test_period`
Período actual en formato YYYYMM.

```python
def test_example(sii_client, test_period):
    result = sii_client.get_compras(periodo=test_period)
    assert result is not None
```

### `test_year`
Año anterior (para tests de F29).

```python
def test_example(sii_client, test_year):
    formularios = sii_client.get_f29_lista(anio=test_year)
    assert isinstance(formularios, list)
```

## Estructura de Tests

Cada archivo sigue el patrón:

```python
class TestFeature:
    """Test cases for a specific feature"""

    def test_basic_functionality(self, sii_client):
        """Test description"""
        result = sii_client.some_method()
        assert result is not None

    def test_specific_aspect(self, sii_client):
        """Test description"""
        # Test implementation
        pass
```

## Mejores Prácticas

1. **Nombres descriptivos**: Cada test tiene un nombre que describe claramente lo que prueba
2. **Docstrings**: Todos los tests incluyen docstrings explicativos
3. **Fixtures**: Uso extensivo de fixtures para evitar repetición
4. **Aserciones claras**: Mensajes de error descriptivos en las aserciones
5. **Aislamiento**: Cada test es independiente y no depende del estado de otros

## Cobertura de Tests

Los tests cubren:

- ✅ Autenticación y login
- ✅ Gestión de cookies
- ✅ Extracción de información del contribuyente
- ✅ Extracción de DTEs de compra
- ✅ Extracción de DTEs de venta
- ✅ Resumen de compras/ventas
- ✅ Extracción de formularios F29
- ✅ Rendimiento y optimización

## Troubleshooting

### Error: "No module named 'app.integrations.sii'"

Asegúrate de estar ejecutando pytest desde el directorio `backend/`:

```bash
cd backend/
pytest app/integrations/sii/tests/
```

### Tests fallan con errores de Selenium

Verifica que Chrome/Chromium esté instalado:

```bash
# macOS
brew install --cask google-chrome

# Linux
sudo apt-get install chromium-browser
```

### Credenciales inválidas

Modifica las credenciales en `conftest.py` con credenciales válidas del SII.

## CI/CD

Para integración continua, ejemplo con GitHub Actions:

```yaml
- name: Run SII Integration Tests
  run: |
    cd backend
    pytest app/integrations/sii/tests/ -v --cov=app.integrations.sii
  env:
    SII_TEST_RUT: ${{ secrets.SII_TEST_RUT }}
    SII_TEST_PASSWORD: ${{ secrets.SII_TEST_PASSWORD }}
```

## Contribuir

Al agregar nuevos tests:

1. Usa fixtures existentes cuando sea posible
2. Agrupa tests relacionados en clases
3. Incluye docstrings descriptivos
4. Asegúrate que los tests sean independientes
5. Ejecuta toda la suite antes de hacer commit
