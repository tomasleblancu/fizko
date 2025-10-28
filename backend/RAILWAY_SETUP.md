# Despliegue en Railway - Fizko Backend

Este documento contiene las instrucciones para desplegar el backend de Fizko en Railway.

## Prerrequisitos

1. Cuenta en Railway (https://railway.app)
2. Proyecto conectado al repositorio de GitHub
3. Base de datos Supabase configurada

## Configuración del Proyecto

### 1. Crear nuevo servicio en Railway

1. Ve a tu proyecto en Railway
2. Click en "New Service" → "GitHub Repo"
3. Selecciona el repositorio `fizko-v2`
4. Railway detectará automáticamente el `railway.json` y el `Dockerfile`

### 2. Configurar Variables de Entorno

En Railway, ve a la pestaña "Variables" de tu servicio y configura las siguientes variables:

#### OpenAI (Requerido)
```
OPENAI_API_KEY=<tu_api_key_de_openai>
```

#### Supabase (Requerido)
```
SUPABASE_URL=https://fgykuqxujbwpjiebzroj.supabase.co
SUPABASE_ANON_KEY=<tu_anon_key>
SUPABASE_KEY=<tu_service_role_key>
SUPABASE_JWT_SECRET=<tu_jwt_secret>
```

#### Database (Requerido)
**IMPORTANTE**: Usa el pooler de Supabase (puerto 5432 o 6543) para mejor rendimiento:

```
DATABASE_URL=postgresql+asyncpg://postgres.fgykuqxujbwpjiebzroj:<password>@aws-1-us-east-2.pooler.supabase.com:5432/postgres
```

Notas sobre DATABASE_URL:
- Reemplaza `<password>` con tu contraseña real
- Si la contraseña contiene caracteres especiales (@, #, /), codifícalos en URL:
  - `@` → `%40`
  - `#` → `%23`
  - `/` → `%2F`
- Ejemplo: `Dfqwz518@#` → `Dfqwz518%40%23`

#### Kapso (WhatsApp - Opcional)
```
KAPSO_API_TOKEN=<tu_token>
KAPSO_API_BASE_URL=https://app.kapso.ai/api/v1
KAPSO_WEBHOOK_SECRET=<tu_webhook_secret>
DEFAULT_WHATSAPP_CONFIG_ID=<tu_config_id>
```

### 3. Configuración de Puerto

Railway asigna automáticamente la variable `PORT`. El backend está configurado para usar esta variable:
```dockerfile
CMD gunicorn app.main:app \
    --bind 0.0.0.0:${PORT:-8080}
```

**No necesitas configurar PORT manualmente** - Railway lo hace automáticamente.

### 4. Health Check

Railway monitoreará el endpoint `/health` automáticamente según el `railway.json`:
```json
{
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300
  }
}
```

## Verificación del Despliegue

### 1. Revisar Logs de Build

En Railway, ve a la pestaña "Deployments" y verifica que:
- ✅ Stage 1 (builder) se complete sin errores
- ✅ Stage 2 (runtime) instale Chromium correctamente
- ✅ La aplicación inicie con Gunicorn

### 2. Probar Endpoints

Una vez desplegado, obtén la URL pública desde Railway y prueba:

```bash
# Health check
curl https://tu-app.railway.app/health

# API root
curl https://tu-app.railway.app/

# API docs (Swagger UI)
# Abre en el navegador: https://tu-app.railway.app/docs
```

### 3. Verificar Conexión a Base de Datos

Los logs de Railway deberían mostrar:
```
✓ Database connection check passed
```

Si ves errores de conexión, verifica:
- DATABASE_URL está configurado correctamente
- La contraseña está URL-encoded si tiene caracteres especiales
- El pooler de Supabase está accesible desde Railway

## Troubleshooting

### Error: "DATABASE_URL environment variable is not set"

**Solución**: Configura la variable `DATABASE_URL` en Railway con el formato correcto.

### Error: "could not translate host name"

**Solución**: Verifica que la URL de Supabase sea correcta y esté accesible públicamente.

### Error: "password authentication failed"

**Solución**:
1. Verifica que la contraseña sea correcta
2. Si tiene caracteres especiales, asegúrate de URL-encodearlos
3. Usa la contraseña del usuario `postgres.fgykuqxujbwpjiebzroj`

### Error: "prepared statement already exists"

**Solución**: Asegúrate de usar el pooler de Supabase (puerto 6543) con `statement_cache_size=0` o usa el puerto 5432 directo. El código ya maneja esto automáticamente.

### Build falla en "uv sync"

**Solución**:
1. Verifica que `uv.lock` esté actualizado en el repositorio
2. Si no existe, ejecuta localmente: `uv lock`
3. Commit y push los cambios

### Chromium no funciona

Los logs deberían mostrar:
```
Chromium 120.0.6099.0
ChromeDriver 120.0.6099.0
```

Si falla:
1. Verifica que la imagen base sea `python:3.11` (no slim)
2. Los paquetes `chromium` y `chromium-driver` se instalan correctamente

## Optimizaciones de Producción

### 1. Workers de Gunicorn

El Dockerfile usa 2 workers por defecto:
```dockerfile
CMD gunicorn app.main:app --workers 2
```

Para instancias más grandes, puedes ajustar usando variables de entorno en Railway:
```
WORKERS=4
```

Y modificar el CMD para usar `${WORKERS:-2}`.

### 2. Timeouts

Los timeouts están configurados para operaciones largas de scraping:
```dockerfile
--timeout 120 \
--graceful-timeout 30
```

Si necesitas ajustarlos, edita el `Dockerfile`.

### 3. Pooling de Base de Datos

El código detecta automáticamente si usas pgbouncer (puerto 6543):
- Con pgbouncer: Usa `NullPool` y deshabilita prepared statements
- Conexión directa (puerto 5432): Usa pool normal con 5-15 conexiones

**Recomendación**: Usa el pooler para producción (`port 6543` o `pooler.supabase.com`).

## CORS Configuration

El backend permite los siguientes orígenes:
```python
allow_origins=[
    "http://localhost:5171",
    "http://127.0.0.1:5171",
    "https://fizko-ai-mr.vercel.app",
    "https://demo.fizko.ai",
]
```

Si despliegas el frontend en un nuevo dominio, deberás agregar el origen a `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # ... existing origins
        "https://tu-nuevo-dominio.com",
    ],
    # ...
)
```

## Monitoreo

### Logs en Railway

Railway guarda logs automáticamente. Para verlos en tiempo real:
1. Ve a tu servicio en Railway
2. Click en "Logs"
3. Filtra por nivel si es necesario

### Métricas

Railway proporciona métricas básicas:
- CPU usage
- Memory usage
- Network traffic

Para monitoreo más avanzado, considera integrar:
- Sentry (errores)
- New Relic (APM)
- Datadog (métricas)

## Rollback

Si un despliegue falla:
1. Ve a "Deployments" en Railway
2. Encuentra el último despliegue exitoso
3. Click en "..." → "Redeploy"

## Recursos Adicionales

- [Railway Docs](https://docs.railway.app/)
- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Gunicorn Deployment](https://docs.gunicorn.org/en/stable/deploy.html)
