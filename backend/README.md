# SII Integration Service v2.0

Servicio de integración con el SII (Servicio de Impuestos Internos de Chile) con procesamiento asíncrono vía Celery.

## Descripción

Este servicio proporciona:
- **API REST** para extracción de datos del SII
- **Celery Workers** para procesamiento asíncrono de tareas pesadas
- **Supabase Client** para persistencia de datos
- **Multi-agent AI** para asistencia conversacional

### Diferencias con Backend Original

| Aspecto | Backend Original | Backend V2 |
|---------|-----------------|------------|
| Base de datos | SQLAlchemy (async) | Supabase Client |
| Acceso a datos | Queries SQL | Repositorios |
| Tareas | Todas (SII, calendar, notifications) | Solo SII |
| Lógica en tareas | Parcial | 100% en services |

### Características Principales

- ✅ **FastAPI**: API REST moderna y rápida
- ✅ **Celery + Redis**: Procesamiento asíncrono de tareas SII
- ✅ **Supabase**: Base de datos serverless con RLS
- ✅ **Selenium**: Web scraping del portal SII
- ✅ **Docker**: Deploy containerizado con docker-compose

## 🚀 Quick Start con Docker

La forma más rápida de ejecutar Backend V2 con todos los servicios:

```bash
# 1. Clonar y configurar
cd backend-v2
cp .env.example .env
# Editar .env con tus credenciales

# 2. Levantar todos los servicios (FastAPI + Celery + Redis)
docker-compose up -d

# 3. Ver logs
docker-compose logs -f celery-worker
```

Ver [DOCKER_CELERY.md](DOCKER_CELERY.md) para documentación completa.

## 📋 Tareas Celery Disponibles

Backend V2 incluye tareas asíncronas para:

### Sincronización de Documentos
- `sii.sync_documents` - Compras/ventas para una empresa
- `sii.sync_documents_all_companies` - Todas las empresas

### Formularios F29
- `sii.sync_f29` - F29 para una empresa
- `sii.sync_f29_all_companies` - Todas las empresas

Ver [app/infrastructure/celery/README.md](app/infrastructure/celery/README.md) para documentación completa.

## 🔌 Endpoints API Disponibles

- **POST /api/sii/login** - Verificar credenciales del SII
- **POST /api/sii/compras** - Extraer documentos de compras (DTEs)
- **POST /api/sii/ventas** - Extraer documentos de ventas (DTEs)
- **POST /api/sii/f29** - Extraer propuesta de formulario F29
- **POST /api/sii/boletas-honorarios** - Extraer boletas de honorarios
- **POST /api/sii/contribuyente** - Obtener información del contribuyente
- **GET /health** - Health check del servicio

## Instalación

### Requisitos

- Python 3.11 o superior
- Chrome/Chromium instalado (para Selenium)
- uv package manager (recomendado) o pip

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   cd backend-v2
   ```

2. **Instalar dependencias**

   Usando uv (recomendado):
   ```bash
   uv sync
   ```

   O usando pip:
   ```bash
   pip install -e .
   ```

3. **Configurar variables de entorno** (opcional)
   ```bash
   cp .env.example .env
   ```

   Editar `.env` si necesitas configuraciones personalizadas:
   ```env
   DEBUG=true
   SII_HEADLESS=true
   SII_TIMEOUT=30
   ```

## Uso

### Iniciar el Servidor

**Opción 1: Usando el script de inicio (recomendado)**
```bash
./start.sh
```

**Opción 2: Usando uvicorn directamente**
```bash
# Con uv (recomendado)
uv run uvicorn app.main:app --reload --port 8090

# Con uvicorn instalado globalmente
uvicorn app.main:app --reload --port 8090
```

El servidor estará disponible en `http://localhost:8090`

### Documentación Interactiva

Una vez iniciado el servidor, puedes acceder a:

- **Swagger UI**: http://localhost:8090/docs
- **ReDoc**: http://localhost:8090/redoc

## Ejemplos de Uso

### 1. Verificar Login

```bash
curl -X POST "http://localhost:8090/api/sii/login" \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "12345678",
    "dv": "9",
    "password": "tu_password"
  }'
```

Respuesta:
```json
{
  "success": true,
  "message": "Login exitoso",
  "session_active": true
}
```

### 2. Obtener Documentos de Compra

```bash
curl -X POST "http://localhost:8090/api/sii/compras" \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "12345678",
    "dv": "9",
    "password": "tu_password",
    "periodo": "202501"
  }'
```

Respuesta:
```json
{
  "success": true,
  "periodo": "202501",
  "tipo": "compras",
  "total_documentos": 15,
  "documentos": [
    {
      "tipo_doc": "33",
      "folio": "12345",
      "fecha": "2025-01-15",
      "rut_proveedor": "76543210-K",
      "razon_social": "Proveedor Ejemplo S.A.",
      "monto_neto": 100000,
      "monto_iva": 19000,
      "monto_total": 119000
    }
  ]
}
```

### 3. Obtener Documentos de Venta

```bash
curl -X POST "http://localhost:8090/api/sii/ventas" \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "12345678",
    "dv": "9",
    "password": "tu_password",
    "periodo": "202501"
  }'
```

### 4. Obtener Propuesta de Formulario F29

```bash
curl -X POST "http://localhost:8090/api/sii/f29" \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "12345678",
    "dv": "9",
    "password": "tu_password",
    "periodo": "202501"
  }'
```

Respuesta:
```json
{
  "success": true,
  "periodo": "202501",
  "tipo": "f29_propuesta",
  "data": {
    "debito_fiscal": 190000,
    "credito_fiscal": 150000,
    "iva_a_pagar": 40000,
    "remanente": 0,
    "codigos": [...]
  }
}
```

**Nota**: Este endpoint retorna la propuesta de F29 calculada automáticamente por el SII.

### 5. Obtener Boletas de Honorarios

```bash
curl -X POST "http://localhost:8090/api/sii/boletas-honorarios" \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "12345678",
    "dv": "9",
    "password": "tu_password",
    "periodo": "202501"
  }'
```

### 6. Obtener Información del Contribuyente

```bash
curl -X POST "http://localhost:8090/api/sii/contribuyente" \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "12345678",
    "dv": "9",
    "password": "tu_password"
  }'
```

## Reutilización de Sesiones con Cookies

### ¿Por qué usar cookies?

Cada login al SII puede tomar varios segundos. Para evitar logins innecesarios, todos los endpoints retornan las **cookies de sesión actuales** que puedes reutilizar en futuros requests.

### Ejemplo con Cookies

```bash
# 1. Primer request: Login y obtener cookies
curl -X POST "http://localhost:8090/api/sii/login" \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "12345678",
    "dv": "9",
    "password": "tu_password"
  }' > session.json

# 2. Extraer cookies del response
COOKIES=$(cat session.json | jq '.cookies')

# 3. Reutilizar cookies en siguiente request (sin login!)
curl -X POST "http://localhost:8090/api/sii/compras" \
  -H "Content-Type: application/json" \
  -d "{
    \"rut\": \"12345678\",
    \"dv\": \"9\",
    \"password\": \"tu_password\",
    \"periodo\": \"202501\",
    \"cookies\": $COOKIES
  }"
```

### Ejemplo con Python

```python
import requests

# Configuración
base_url = "http://localhost:8090/api/sii"
credentials = {
    "rut": "12345678",
    "dv": "9",
    "password": "tu_password"
}

# 1. Hacer login y guardar cookies
response = requests.post(f"{base_url}/login", json=credentials)
result = response.json()
cookies = result.get("cookies")
print(f"Login exitoso. Cookies guardadas: {len(cookies)} cookies")

# 2. Reutilizar cookies para múltiples requests sin login
# Request 1: Compras
compras_request = {**credentials, "periodo": "202501", "cookies": cookies}
response = requests.post(f"{base_url}/compras", json=compras_request)
compras = response.json()
print(f"Total compras: {compras['total_documentos']}")

# Actualizar cookies con las más recientes
cookies = compras.get("cookies", cookies)

# Request 2: Ventas (reutilizando cookies)
ventas_request = {**credentials, "periodo": "202501", "cookies": cookies}
response = requests.post(f"{base_url}/ventas", json=ventas_request)
ventas = response.json()
print(f"Total ventas: {ventas['total_documentos']}")

# Actualizar cookies nuevamente
cookies = ventas.get("cookies", cookies)

# Request 3: F29 (reutilizando cookies)
f29_request = {**credentials, "periodo": "202501", "cookies": cookies}
response = requests.post(f"{base_url}/f29", json=f29_request)
f29 = response.json()
print(f"F29 obtenido exitosamente")
```

### Beneficios de Reutilizar Cookies

- ⚡ **Más rápido**: Evita el proceso de login (ahorra ~5-10 segundos por request)
- 🔒 **Menos carga**: Reduce la carga en el servidor del SII
- 💰 **Eficiente**: Permite hacer múltiples requests en secuencia sin delays

### Notas Importantes sobre Cookies

- Las cookies tienen una **duración limitada** (típicamente ~20-30 minutos de inactividad)
- Si las cookies expiran, el servicio automáticamente hará login nuevamente
- Siempre usa las **cookies más recientes** retornadas por cada endpoint
- Las cookies son específicas por RUT (no mezcles cookies de diferentes usuarios)

## Estructura del Proyecto

```
backend-v2/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py              # Configuration settings
│   ├── routers/
│   │   ├── __init__.py
│   │   └── sii.py                   # SII endpoints
│   └── integrations/
│       └── sii/                     # SII integration code
│           ├── client/              # SII client
│           ├── scrapers/            # Web scrapers
│           ├── extractors/          # Data extractors
│           └── core/                # Core utilities
├── pyproject.toml                   # Dependencies
├── .env.example                     # Environment variables template
└── README.md                        # This file
```

## Notas Técnicas

### Selenium y Headless Mode

Por defecto, el servicio ejecuta Chrome en modo headless (sin interfaz gráfica). Para debugging, puedes cambiar esto en `.env`:

```env
SII_HEADLESS=false
```

### Manejo de Sesiones y Cookies

El servicio soporta dos modos de operación:

**Modo 1: Sin cookies (simple pero lento)**
- Cada request hace login completo al SII
- Más lento (~5-10 segundos extra por request)
- Útil para requests aislados

**Modo 2: Con cookies (rápido y eficiente) ✅ Recomendado**
- Login solo en el primer request
- Requests subsecuentes reutilizan la sesión
- Hasta 10x más rápido para múltiples requests
- Ver sección "Reutilización de Sesiones con Cookies" arriba

El cliente maneja automáticamente:
- Validación de cookies existentes
- Re-login automático si las cookies expiraron
- Cierre automático de navegador

### Timeouts

El timeout por defecto es de 30 segundos. Puedes ajustarlo en `.env`:

```env
SII_TIMEOUT=60
```

### Errores Comunes

**Error 401 - Authentication Failed**
- Verifica que el RUT y contraseña sean correctos
- Asegúrate de que el RUT esté sin puntos ni guión

**Error 422 - Extraction Failed**
- El periodo puede no tener datos disponibles
- Verifica el formato del periodo (YYYYMM)

**Error 500 - Internal Server Error**
- Revisa los logs del servidor
- Puede ser un problema con Selenium/Chrome

## Diferencias con Backend Original

| Característica | Backend Original | Backend v2 |
|---------------|------------------|------------|
| Base de datos | ✅ PostgreSQL + Supabase | ❌ Sin DB |
| Autenticación | ✅ JWT + Supabase Auth | ❌ Sin auth |
| Multi-tenancy | ✅ Company isolation | ❌ N/A |
| Celery tasks | ✅ Background jobs | ❌ Sin jobs |
| WhatsApp | ✅ Kapso integration | ❌ N/A |
| AI Agents | ✅ Multi-agent system | ❌ N/A |
| Persistencia | ✅ Guarda documentos | ❌ Solo extrae |
| Complejidad | Alta | Baja |

## Limitaciones

- **Stateless**: No se guardan datos entre requests
- **No cache**: Cada request hace scraping real del SII
- **Sin rate limiting**: No hay control de tasa de requests
- **Sin autenticación**: Cualquiera puede usar el servicio si tiene acceso

## Testing

El servicio incluye una suite completa de tests End-to-End que validan todos los endpoints.

### Ejecutar Tests

```bash
# Opción 1: Usando el script helper (recomendado)
./run_tests.sh

# Opción 2: Directamente con pytest
pytest tests/test_endpoints_e2e.py -v

# Ejecutar solo tests rápidos
./run_tests.sh quick

# Ejecutar test de flujo completo con cookies
./run_tests.sh flow
```

### Configurar Tests

1. Copiar template de configuración:
   ```bash
   cp .env.test.example .env.test
   ```

2. Editar `.env.test` con credenciales válidas:
   ```env
   TEST_SII_RUT=77794858
   TEST_SII_DV=K
   TEST_SII_PASSWORD=SiiPfufl574@#
   TEST_PERIODO=202411
   ```

3. Iniciar el servidor en una terminal separada:
   ```bash
   ./start.sh
   ```

4. Ejecutar tests:
   ```bash
   ./run_tests.sh
   ```

**⚠️ Importante**: Los tests hacen requests REALES al SII y pueden ser lentos (varios minutos).

Ver [tests/README.md](tests/README.md) para documentación completa de testing.

## Roadmap

Posibles mejoras futuras:

- [ ] Cache de sesiones SII en memoria (Redis opcional)
- [ ] Rate limiting por RUT
- [ ] API keys simples (opcional)
- [ ] Modo batch para múltiples periodos
- [ ] WebSocket para progreso en tiempo real
- [ ] Docker image

## Soporte

Para problemas o preguntas:

1. Revisa la documentación del SII: https://www.sii.cl
2. Verifica los logs del servidor
3. Consulta la documentación de Selenium: https://selenium-python.readthedocs.io/

## Licencia

MIT
