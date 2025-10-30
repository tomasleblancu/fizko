# 🚂 Railway Setup - Fizko Backend

Guía completa para deployar el backend de Fizko en Railway con **4 servicios** desde un único repositorio.

## 📋 Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Requisitos Previos](#requisitos-previos)
- [Setup Inicial](#setup-inicial)
- [Configurar Servicios](#configurar-servicios)
- [Variables de Entorno](#variables-de-entorno)
- [Deploy y Verificación](#deploy-y-verificación)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Mantenimiento](#mantenimiento)

---

## 🏗️ Arquitectura

### Servicios en Railway

```
Railway Project: fizko-production
│
├── Service: backend
│   ├── Tipo: Web (puerto público)
│   ├── URL: https://fizko-backend.up.railway.app
│   ├── Health: /health
│   └── Comando: /docker-entrypoint.sh fastapi
│
├── Service: celery-worker
│   ├── Tipo: Worker (sin puerto)
│   ├── Comando: /docker-entrypoint.sh celery-worker
│   └── Réplicas: 1-2
│
├── Service: celery-beat
│   ├── Tipo: Worker (sin puerto)
│   ├── Comando: /docker-entrypoint.sh celery-beat
│   └── Réplicas: 1 (IMPORTANTE: solo 1)
│
├── Service: flower
│   ├── Tipo: Web (puerto público)
│   ├── URL: https://fizko-flower.up.railway.app
│   └── Comando: /docker-entrypoint.sh flower
│
└── Plugin: Redis
    ├── Provider: Railway (managed)
    ├── Variable: ${{Redis.REDIS_URL}}
    └── Plan: Starter (~$5/mes)
```

### Diagrama de Conexiones

```
┌─────────────────────────────────────────────┐
│              Railway Project                 │
│                                              │
│  ┌──────────┐  ┌────────────┐  ┌─────────┐ │
│  │  Redis   │◄─┤  Backend   │  │ Flower  │ │
│  │ (Plugin) │  │  (FastAPI) │  │  (UI)   │ │
│  └────┬─────┘  └──────┬─────┘  └────┬────┘ │
│       │               │              │      │
│       │      ┌────────┴────────┐     │      │
│       ▼      ▼                 ▼     ▼      │
│  ┌─────────────┐      ┌──────────────┐     │
│  │   Celery    │      │    Celery    │     │
│  │   Worker    │      │     Beat     │     │
│  └─────────────┘      └──────────────┘     │
│                                             │
└─────────────────┬───────────────────────────┘
                  │
      ┌───────────┴──────────┐
      ▼                      ▼
  Supabase             OpenAI API
  (PostgreSQL)         (External)
```

---

## ✅ Requisitos Previos

### 1. Cuenta de Railway
- Crear cuenta en [railway.app](https://railway.app)
- Plan: Hobby ($5/mes) o Pro ($20/mes)
- Método de pago configurado

### 2. Repositorio GitHub
- Repositorio con el código del backend
- Branch `main` o `master` limpio
- Permisos de admin en el repo

### 3. Servicios Externos

**Supabase** (obligatorio):
- Proyecto creado
- PostgreSQL funcionando
- Migrations aplicadas
- Credenciales disponibles:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_JWT_SECRET`
  - `DATABASE_URL` (usar puerto 6543 para pgbouncer)

**OpenAI** (obligatorio):
- API Key válida con créditos

**Kapso** (opcional):
- Para integración de WhatsApp
- API Token y Webhook Secret

### 4. Variables Preparadas

Tener listas las siguientes variables (ver [.env.railway.example](./railway.example)):
- ✅ `OPENAI_API_KEY`
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_ANON_KEY`
- ✅ `SUPABASE_JWT_SECRET`
- ✅ `DATABASE_URL`
- ✅ `ENCRYPTION_KEY`
- ❓ `KAPSO_API_TOKEN` (opcional)

---

## 🚀 Setup Inicial

### Paso 1: Crear Proyecto en Railway

1. **Login en Railway**:
   ```bash
   # Opción A: Web Dashboard (recomendado para primera vez)
   open https://railway.app/new

   # Opción B: Railway CLI (avanzado)
   npm install -g @railway/cli
   railway login
   ```

2. **Crear nuevo proyecto**:
   - Click en "New Project"
   - Seleccionar "Deploy from GitHub repo"
   - Autorizar Railway en GitHub
   - Seleccionar repositorio: `tu-org/fizko-v2`
   - Seleccionar branch: `main`

3. **Nombrar el proyecto**:
   - Nombre: `fizko-production`
   - Descripción: "Fizko Backend - Multi-service (FastAPI, Celery, Flower)"

### Paso 2: Conectar GitHub

1. **Configurar auto-deploy**:
   - Settings > GitHub Integration
   - Connect repository
   - Branch: `main`
   - Auto-deploy: ✅ Enabled
   - Build path: `backend/`

2. **Verificar webhook**:
   - GitHub repo > Settings > Webhooks
   - Debe aparecer webhook de Railway
   - Recent Deliveries: revisar que funcione

---

## 🔧 Configurar Servicios

Railway creará automáticamente los servicios al detectar los archivos `railway.*.json` en el repositorio.

### Paso 3: Agregar Redis Plugin

**IMPORTANTE**: Hacer esto ANTES de configurar los servicios.

1. **Agregar plugin**:
   - Railway Dashboard > Tu proyecto
   - Click "+ New"
   - Seleccionar "Database" > "Add Redis"
   - Plan: Starter ($5/mes, 256MB)

2. **Verificar variable**:
   - Plugin Redis > Variables tab
   - Debe existir: `REDIS_URL`
   - Valor: `redis://default:...@containers-us-west-...`
   - Esta variable estará disponible para todos los servicios

### Paso 4: Crear Servicio Backend (FastAPI)

1. **Crear servicio**:
   - Click "+ New" > "Empty Service"
   - Nombre: `backend`
   - Source: GitHub repo
   - Root directory: `backend/`

2. **Configurar build**:
   - Settings > Build
   - Builder: Dockerfile
   - Dockerfile Path: `backend/Dockerfile`
   - Build Command: (vacío, usa Dockerfile)
   - Start Command: `/docker-entrypoint.sh fastapi`

3. **Configurar deploy**:
   - Settings > Deploy
   - Watch Paths: `backend/**`
   - Health Check Path: `/health`
   - Health Check Timeout: 300 (5 min)
   - Restart Policy: ON_FAILURE
   - Max Retries: 10

4. **Configurar networking**:
   - Settings > Networking
   - Generate Domain: ✅
   - Domain: `fizko-backend.up.railway.app`

### Paso 5: Crear Servicio Celery Worker

1. **Crear servicio**:
   - Click "+ New" > "Empty Service"
   - Nombre: `celery-worker`
   - Source: GitHub repo (mismo)
   - Root directory: `backend/`

2. **Configurar build**:
   - Settings > Build
   - Builder: Dockerfile
   - Dockerfile Path: `backend/Dockerfile`
   - Start Command: `/docker-entrypoint.sh celery-worker`

3. **Configurar deploy**:
   - Settings > Deploy
   - Watch Paths: `backend/**`
   - Health Check: (ninguno, es worker)
   - Restart Policy: ON_FAILURE

4. **NO exponer puerto** (es un worker interno)

### Paso 6: Crear Servicio Celery Beat

1. **Crear servicio**:
   - Click "+ New" > "Empty Service"
   - Nombre: `celery-beat`
   - Source: GitHub repo (mismo)
   - Root directory: `backend/`

2. **Configurar build**:
   - Settings > Build
   - Builder: Dockerfile
   - Dockerfile Path: `backend/Dockerfile`
   - Start Command: `/docker-entrypoint.sh celery-beat`

3. **Configurar deploy**:
   - Settings > Deploy
   - Replicas: **1** (IMPORTANTE: solo UNO)
   - Watch Paths: `backend/**`
   - Restart Policy: ON_FAILURE

**⚠️ IMPORTANTE**: Celery Beat debe tener solo 1 réplica para evitar duplicación de tareas.

### Paso 7: Crear Servicio Flower (Monitoring)

1. **Crear servicio**:
   - Click "+ New" > "Empty Service"
   - Nombre: `flower`
   - Source: GitHub repo (mismo)
   - Root directory: `backend/`

2. **Configurar build**:
   - Settings > Build
   - Builder: Dockerfile
   - Dockerfile Path: `backend/Dockerfile`
   - Start Command: `/docker-entrypoint.sh flower`

3. **Configurar networking**:
   - Settings > Networking
   - Generate Domain: ✅
   - Domain: `fizko-flower.up.railway.app`

4. **Opcional - Proteger con auth**:
   - Agregar variables en Flower:
     - `FLOWER_BASIC_AUTH=user:password`

---

## ⚙️ Variables de Entorno

### Paso 8: Configurar Variables Compartidas

**IMPORTANTE**: Configurar en el nivel de PROYECTO (no por servicio individual).

1. **Acceder a variables de proyecto**:
   - Railway Dashboard > Tu proyecto
   - Click en "Settings" (del proyecto, no del servicio)
   - Tab "Variables"

2. **Opción A: Raw Editor (Recomendado)**:
   - Click "Raw Editor"
   - Copiar contenido de [.env.railway.example](./.env.railway.example)
   - Reemplazar valores de ejemplo con reales
   - Click "Save"

3. **Opción B: Una por una**:
   - Click "+ New Variable"
   - Agregar cada variable manualmente

### Variables Obligatorias

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-TU-API-KEY-REAL

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=tu-jwt-secret-desde-supabase
DATABASE_URL=postgresql+asyncpg://postgres:TU-PASSWORD@db.tu-proyecto.supabase.co:6543/postgres

# Encryption
ENCRYPTION_KEY=tu-base64-key-32-bytes

# Redis (auto-configurado)
REDIS_URL=${{Redis.REDIS_URL}}

# Environment
ENVIRONMENT=production

# CORS
ALLOWED_ORIGINS=https://tu-frontend.vercel.app
```

### Variables Opcionales

```bash
# Celery
CELERY_LOG_LEVEL=info
CELERY_CONCURRENCY=2
CELERY_MAX_TASKS_PER_CHILD=1000

# ChatKit
CHATKIT_MODE=multi_agent

# Kapso (WhatsApp)
KAPSO_API_TOKEN=tu-token
KAPSO_API_BASE_URL=https://app.kapso.ai/api/v1
KAPSO_WEBHOOK_SECRET=tu-webhook-secret

# Monitoring
SENTRY_DSN=tu-sentry-dsn
```

### Paso 9: Verificar Variables en Servicios

1. **Verificar en cada servicio**:
   - Backend > Variables tab
   - Celery Worker > Variables tab
   - Celery Beat > Variables tab
   - Flower > Variables tab

2. **Todas deben mostrar las mismas variables compartidas**

3. **Si falta alguna**:
   - Volver a Settings del proyecto
   - Verificar que la variable existe
   - Redeploy el servicio afectado

---

## 🚀 Deploy y Verificación

### Paso 10: Primer Deploy

1. **Trigger manual (opcional)**:
   - Cada servicio > Settings > Deploy
   - Click "Deploy"

2. **O hacer push a GitHub**:
   ```bash
   git add .
   git commit -m "feat: Railway multi-service setup"
   git push origin main
   ```

3. **Railway auto-deploya todos los servicios**

### Paso 11: Monitorear Build

1. **Ver logs de build en tiempo real**:
   - Railway Dashboard
   - Click en cada servicio
   - Tab "Deployments"
   - Click en deployment activo
   - Ver logs

2. **Tiempo estimado de build**:
   - Primera build: ~5-7 min (descarga Chromium)
   - Builds subsecuentes: ~2-3 min (con cache)

### Paso 12: Verificar Health Checks

1. **Backend**:
   ```bash
   curl https://fizko-backend.up.railway.app/health
   # Esperado: {"status":"healthy","service":"fizko-backend"}
   ```

2. **Backend - Docs**:
   ```bash
   open https://fizko-backend.up.railway.app/docs
   ```

3. **Flower**:
   ```bash
   open https://fizko-flower.up.railway.app
   # Debe mostrar Flower UI con workers conectados
   ```

### Paso 13: Verificar Servicios Internos

1. **Celery Worker**:
   - Railway Dashboard > celery-worker > Logs
   - Buscar: `celery@... ready`
   - Debe mostrar: `2 processes`

2. **Celery Beat**:
   - Railway Dashboard > celery-beat > Logs
   - Buscar: `Scheduler: Sending due task`
   - Debe mostrar tareas programadas

3. **Conectividad Redis**:
   - Backend logs: buscar `Redis connection: OK`
   - Worker logs: buscar `Connected to redis://...`

---

## 📊 Monitoring

### Logs

**Ver logs en tiempo real**:
```bash
# Opción A: Railway Dashboard
# Servicio > Logs tab

# Opción B: Railway CLI
railway logs -s backend
railway logs -s celery-worker
railway logs -s celery-beat
railway logs -s flower
```

**Filtrar logs**:
```bash
# Por nivel
railway logs -s backend | grep ERROR

# Por keyword
railway logs -s celery-worker | grep "Task received"

# Últimas 100 líneas
railway logs -s backend --tail 100
```

### Flower UI

**Acceder**:
```bash
open https://fizko-flower.up.railway.app
```

**Features**:
- ✅ Ver workers activos
- ✅ Monitorear tareas en tiempo real
- ✅ Ver historial de tareas
- ✅ Estadísticas de performance
- ✅ Retry failed tasks
- ✅ Purge queues

### Métricas de Railway

**Ver en dashboard**:
- CPU usage por servicio
- Memory usage por servicio
- Network in/out
- Request count (backend/flower)
- Response time (backend)
- Uptime

**Alerts** (Railway Pro):
- Configurar alertas para:
  - CPU > 80%
  - Memory > 90%
  - Deploy failures
  - Health check failures

---

## 🐛 Troubleshooting

### Problema: Build falla

**Síntoma**: Build error en Railway

**Soluciones**:

1. **Ver logs de build**:
   ```bash
   railway logs -s backend --build
   ```

2. **Error común: Chromium install**:
   - Verificar que `Dockerfile` incluya `chromium` y `chromium-driver`
   - Verificar espacio en disco (Railway limits)

3. **Error: Dependencies**:
   - Verificar `pyproject.toml` y `uv.lock` están sincronizados
   - Rebuild sin cache:
     ```bash
     # Railway Dashboard > Servicio > Settings > Build
     # Click "Rebuild" (NO "Deploy")
     ```

### Problema: Health check falla

**Síntoma**: Backend no pasa health check

**Soluciones**:

1. **Verificar endpoint**:
   ```bash
   curl https://fizko-backend.up.railway.app/health
   ```

2. **Ver logs de FastAPI**:
   ```bash
   railway logs -s backend | grep health
   ```

3. **Verificar DATABASE_URL**:
   - Railway Dashboard > backend > Variables
   - Verificar que `DATABASE_URL` tiene puerto 6543
   - Probar conexión desde Railway:
     ```bash
     railway run -s backend python -c "import asyncpg; print('OK')"
     ```

### Problema: Celery tasks no se ejecutan

**Síntoma**: Tasks quedan en "pending"

**Soluciones**:

1. **Verificar worker está corriendo**:
   ```bash
   railway logs -s celery-worker | grep "ready"
   # Debe mostrar: celery@... ready
   ```

2. **Verificar Redis connection**:
   ```bash
   railway logs -s celery-worker | grep "redis"
   # Debe mostrar: Connected to redis://...
   ```

3. **Verificar tasks en Flower**:
   - Open https://fizko-flower.up.railway.app
   - Tab "Workers"
   - Debe aparecer al menos 1 worker
   - Tab "Tasks" > Ver si hay tasks pending

4. **Reiniciar worker**:
   ```bash
   railway restart -s celery-worker
   ```

### Problema: Celery Beat duplica tareas

**Síntoma**: Tareas programadas se ejecutan múltiples veces

**Solución**:

1. **Verificar réplicas**:
   - Railway Dashboard > celery-beat > Settings
   - Replicas: Debe ser **1**

2. **Si hay >1 réplica**:
   - Cambiar a 1
   - Restart servicio

### Problema: Redis connection refused

**Síntoma**: `ConnectionError: Error connecting to Redis`

**Soluciones**:

1. **Verificar plugin Redis**:
   - Railway Dashboard > Redis plugin
   - Status: Debe estar "Running"

2. **Verificar variable `REDIS_URL`**:
   - Railway Dashboard > Settings > Variables
   - Debe existir: `REDIS_URL=${{Redis.REDIS_URL}}`
   - **NO** debe ser URL hardcodeada

3. **Verificar networking**:
   - Redis y servicios deben estar en el mismo proyecto
   - Railway crea network interno automáticamente

### Problema: 502 Bad Gateway

**Síntoma**: Backend responde 502

**Soluciones**:

1. **Verificar puerto**:
   - Railway asigna `$PORT` automáticamente
   - Dockerfile debe usar: `EXPOSE ${PORT:-8080}`
   - Entrypoint debe usar: `--bind 0.0.0.0:${PORT:-8080}`

2. **Verificar logs**:
   ```bash
   railway logs -s backend | tail -50
   ```

3. **Aumentar health check timeout**:
   - Railway Dashboard > backend > Settings > Deploy
   - Health Check Timeout: 300 (5 min)

---

## 🔧 Mantenimiento

### Actualizar Código

**Push to GitHub**:
```bash
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main

# Railway auto-deploya todos los servicios afectados
```

**Rollback a versión anterior**:
- Railway Dashboard > Servicio > Deployments
- Click en deployment anterior
- Click "Rollback"

### Actualizar Variables

1. **Cambiar variable**:
   - Railway Dashboard > Settings > Variables
   - Edit variable
   - Save

2. **Railway redeploya automáticamente** todos los servicios

3. **O redeploy manual**:
   ```bash
   railway redeploy -s backend
   railway redeploy -s celery-worker
   railway redeploy -s celery-beat
   railway redeploy -s flower
   ```

### Escalar Servicios

**Celery Worker (aumentar concurrencia)**:

1. **Opción A: Variable**:
   - Railway Dashboard > Settings > Variables
   - Cambiar `CELERY_CONCURRENCY=4`
   - Redeploy

2. **Opción B: Múltiples réplicas**:
   - Railway Dashboard > celery-worker > Settings
   - Replicas: 2-3
   - Cada réplica procesa tasks en paralelo

**⚠️ IMPORTANTE**: Celery Beat SIEMPRE debe tener 1 réplica.

### Monitorear Costos

**Ver uso actual**:
- Railway Dashboard > Usage
- Ver por servicio:
  - CPU hours
  - Memory GB-hours
  - Network egress
- Estimate mensual

**Optimizar costos**:
- Reducir réplicas cuando no hay carga
- Usar Railway Hobby plan ($5/mes base)
- Monitorear usage diario

---

## 📚 Recursos Adicionales

### Documentación

- [Railway Docs](https://docs.railway.app/)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Celery Docs](https://docs.celeryproject.org/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

### Guías Relacionadas

- [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Deploy local con Docker
- [RAILWAY_QUICKSTART.md](./RAILWAY_QUICKSTART.md) - Guía express
- [.env.railway.example](./.env.railway.example) - Template de variables

### Soporte

- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Railway Status: [status.railway.app](https://status.railway.app)
- GitHub Issues: Reportar bugs del proyecto

---

**Última actualización**: 2025-01-29
**Versión**: 1.0.0
