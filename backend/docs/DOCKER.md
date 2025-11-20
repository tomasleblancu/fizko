# Docker Configuration - Backend V2

## ✅ Estado: COMPLETO

Configuración de Docker lista para backend-v2 con FastAPI + ngrok.

**Simplificada**: Sin Celery, sin Redis, sin base de datos - solo lo esencial.

## 📁 Archivos Creados

```
backend-v2/
├── Dockerfile                    # Multi-stage build con Python 3.11
├── docker-compose.yml            # FastAPI + ngrok
├── docker-entrypoint.sh          # Entrypoint script
├── ngrok.yml                     # Configuración de ngrok
└── .dockerignore                 # Exclusiones de build
```

## 🐳 Servicios

### 1. Backend (FastAPI)
- **Puerto**: 8089
- **Imagen**: Python 3.11 con Chromium + ChromeDriver
- **Hot-reload**: Activado en modo desarrollo
- **Health check**: `GET /health`

### 2. ngrok
- **Puerto**: 4040 (web interface)
- **Región**: South America (sa)
- **URL pública**: Generada automáticamente
- **Inspect**: Activado

## 🚀 Uso Rápido

### Iniciar todo

```bash
docker-compose up
```

Esto inicia:
- **Backend**: http://localhost:8089
- **ngrok dashboard**: http://localhost:4040

### Iniciar solo backend

```bash
docker-compose up backend
```

### En background

```bash
docker-compose up -d
```

### Ver logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo ngrok
docker-compose logs -f ngrok
```

### Detener

```bash
docker-compose down
```

## 📋 Comandos Disponibles

El entrypoint `docker-entrypoint.sh` soporta estos comandos:

### `fastapi` (Producción)
```bash
docker-compose run backend fastapi
```
- Uvicorn con 1 worker (default)
- Sin hot-reload
- Optimizado para producción

### `fastapi-dev` (Desarrollo)
```bash
docker-compose up backend
# o
docker-compose run backend fastapi-dev
```
- Uvicorn con hot-reload
- Monta código como volumen
- Recarga automática al modificar archivos

### `test` / `pytest`
```bash
# Todos los tests
docker-compose run backend test

# Tests específicos
docker-compose run backend test tests/test_endpoints_e2e.py -v

# Con coverage
docker-compose run backend test --cov=app tests/
```

### `bash` / `sh`
```bash
docker-compose run backend bash
```
Shell interactivo dentro del contenedor.

## 🔧 Configuración

### Variables de Entorno

Crear archivo `.env` en la raíz de backend-v2:

```bash
# SII Credentials (para testing)
STC_TEST_RUT=77794858
STC_TEST_DV=K

# Selenium
STC_HEADLESS=true

# ngrok (opcional)
NGROK_AUTHTOKEN=tu_token_aqui
```

### ngrok Token

1. Registrarse en https://ngrok.com
2. Obtener authtoken de https://dashboard.ngrok.com/get-started/your-authtoken
3. Agregar a `.env`:
   ```
   NGROK_AUTHTOKEN=tu_token_aqui
   ```

## 📊 Estructura del Dockerfile

### Multi-stage Build

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
- Instala dependencias con uv
- Crea virtual environment

# Stage 2: Runtime
FROM python:3.11
- Copia .venv from builder
- Instala Chromium + ChromeDriver
- Copia código de aplicación
- Configura entrypoint
```

**Beneficios:**
- ✅ Imagen final más pequeña
- ✅ Build más rápido (cache de layers)
- ✅ Separación build/runtime

### Dependencias del Sistema

- **Chromium**: Browser para Selenium
- **ChromeDriver**: WebDriver para automatización
- **curl**: Health checks
- **netcat-openbsd**: Utilidades de red

## 🔍 Health Checks

### Backend
```bash
curl http://localhost:8089/health
# {"status": "healthy"}
```

### Docker Health Check
```bash
docker-compose ps
# Muestra estado de health check
```

## 📡 ngrok

### Acceder al Dashboard

1. Iniciar servicios:
   ```bash
   docker-compose up
   ```

2. Abrir dashboard:
   ```
   http://localhost:4040
   ```

3. Ver URL pública:
   - En el dashboard verás la URL: `https://xxxx-xx-xx-xxx-xxx.sa.ngrok.io`
   - Esta URL apunta a tu backend local (puerto 8089)

### Usar URL Pública

```bash
# Ejemplo: Verificar SII desde ngrok
curl https://xxxx-xx-xx-xxx-xxx.sa.ngrok.io/api/sii/verify \
  -H "Content-Type: application/json" \
  -d '{
    "rut": "77794858",
    "dv": "k",
    "password": "******"
  }'
```

### Configuración Avanzada

Editar `ngrok.yml` para:
- Cambiar región
- Agregar dominios custom (plan pago)
- Configurar múltiples tunnels
- Ajustar logging

## 🛠️ Desarrollo

### Hot-Reload

El código en `./app` está montado como volumen:

```yaml
volumes:
  - ./app:/app/app
```

**Cambios se reflejan automáticamente** sin reiniciar el contenedor.

### Debugging

Agregar breakpoints con `pdb`:

```python
import pdb; pdb.set_trace()
```

Luego attach al contenedor:

```bash
docker attach fizko-v2-backend
```

### Rebuild

Después de cambiar dependencias:

```bash
docker-compose build
# o
docker-compose up --build
```

## 📊 Comparación con Backend Original

| Característica | Backend Original | Backend V2 |
|----------------|------------------|------------|
| **Servicios** | 7 (FastAPI, Celery x3, Redis, Flower, ngrok) | **2 (FastAPI, ngrok)** |
| **Complejidad** | Alta | **Baja** |
| **Tiempo inicio** | ~30-40 segundos | **~10-15 segundos** |
| **Memoria** | ~1.5GB | **~300MB** |
| **Dependencias** | Redis, PostgreSQL | **Ninguna** |
| **Workers** | Gunicorn + Uvicorn | **Uvicorn** |
| **Background tasks** | Celery | ❌ No |
| **Monitoring** | Flower | ❌ No |

## 🔐 Seguridad

### Producción

Para producción, modificar:

1. **No exponer ngrok** (comentar en docker-compose.yml)

2. **HTTPS**: Usar reverse proxy (nginx/traefik)

3. **Secrets**: Usar secrets management
   ```bash
   docker secret create sii_creds ./secrets.json
   ```

4. **Read-only filesystem**:
   ```yaml
   read_only: true
   tmpfs:
     - /tmp
     - /app/sessions
   ```

## 📝 Troubleshooting

### Port already in use

```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "9000:8089"  # Usar puerto 9000 en host
```

### Chromium no funciona

Verificar que esté instalado:

```bash
docker-compose run backend bash
chromium --version
chromedriver --version
```

### ngrok no inicia

Verificar token:

```bash
# En .env
NGROK_AUTHTOKEN=tu_token_valido

# Logs de ngrok
docker-compose logs ngrok
```

### Build fails

Limpiar cache:

```bash
docker-compose down
docker system prune -f
docker-compose build --no-cache
```

## 🎯 Ejemplos Completos

### Desarrollo Local con ngrok

```bash
# 1. Iniciar servicios
docker-compose up -d

# 2. Ver logs
docker-compose logs -f backend

# 3. Obtener URL pública
open http://localhost:4040

# 4. Probar endpoint desde internet
curl https://xxxx.sa.ngrok.io/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola", "user_id": "test"}'

# 5. Detener
docker-compose down
```

### Testing en Docker

```bash
# Run all tests
docker-compose run backend test

# Run specific test file
docker-compose run backend test tests/test_endpoints_e2e.py -v

# Run with coverage
docker-compose run backend test --cov=app --cov-report=html
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build Docker image
        run: docker-compose build

      - name: Run tests
        run: docker-compose run backend test

      - name: Health check
        run: |
          docker-compose up -d backend
          sleep 10
          curl -f http://localhost:8089/health
```

## ✅ Checklist de Deployment

- [ ] `.env` configurado con credenciales
- [ ] `NGROK_AUTHTOKEN` agregado (si se usa ngrok)
- [ ] Tests pasando: `docker-compose run backend test`
- [ ] Health check OK: `curl localhost:8089/health`
- [ ] Logs sin errores: `docker-compose logs`
- [ ] ngrok funcionando: http://localhost:4040

## 📚 Referencias

- **Docker**: https://docs.docker.com
- **Docker Compose**: https://docs.docker.com/compose/
- **ngrok**: https://ngrok.com/docs
- **Uvicorn**: https://www.uvicorn.org
- **FastAPI**: https://fastapi.tiangolo.com

---

**Creado**: 19 de Noviembre, 2025
**Servicios**: 2 (FastAPI + ngrok)
**Complejidad**: Baja ✅
**Status**: DOCKER CONFIG COMPLETE
