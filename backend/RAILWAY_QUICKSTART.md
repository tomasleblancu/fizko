# 🚂 Railway Quick Start

Guía express para deployar Fizko Backend a Railway en **15 minutos**.

## 1️⃣ Preparar Variables (5 min)

```bash
# Tener listas estas variables desde Supabase, OpenAI, etc.
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://....supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_JWT_SECRET=...
DATABASE_URL=postgresql+asyncpg://postgres:...@db....supabase.co:6543/postgres
ENCRYPTION_KEY=... (generar con: python -c "import base64; import os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())")
```

## 2️⃣ Crear Proyecto Railway (2 min)

1. Login: https://railway.app/new
2. "Deploy from GitHub repo"
3. Seleccionar repo: `tu-org/fizko-v2`
4. Branch: `main`
5. Nombre proyecto: `fizko-production`

## 3️⃣ Agregar Redis Plugin (1 min)

1. Railway Dashboard > "+ New"
2. "Database" > "Add Redis"
3. Plan: Starter ($5/mes)

## 4️⃣ Crear 4 Servicios (3 min)

Railway detecta automáticamente los archivos `railway.*.json` y crea los servicios.

Si no aparecen automáticamente, crear manualmente:

### Backend (FastAPI)
- "+ New" > "Empty Service"
- Nombre: `backend`
- Source: GitHub repo
- Root: `backend/`
- Dockerfile: `backend/Dockerfile`
- Start Command: `/docker-entrypoint.sh fastapi`
- ✅ Generate Domain

### Celery Worker
- "+ New" > "Empty Service"
- Nombre: `celery-worker`
- Source: GitHub repo
- Root: `backend/`
- Dockerfile: `backend/Dockerfile`
- Start Command: `/docker-entrypoint.sh celery-worker`

### Celery Beat
- "+ New" > "Empty Service"
- Nombre: `celery-beat`
- Source: GitHub repo
- Root: `backend/`
- Dockerfile: `backend/Dockerfile`
- Start Command: `/docker-entrypoint.sh celery-beat`
- **Réplicas: 1** (IMPORTANTE)

### Flower (Monitoring)
- "+ New" > "Empty Service"
- Nombre: `flower`
- Source: GitHub repo
- Root: `backend/`
- Dockerfile: `backend/Dockerfile`
- Start Command: `/docker-entrypoint.sh flower`
- ✅ Generate Domain

## 5️⃣ Configurar Variables (2 min)

Railway Dashboard > Settings > Variables > Raw Editor

```bash
# Copiar desde .env.railway.example y reemplazar valores
OPENAI_API_KEY=sk-proj-TU-KEY-REAL
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_JWT_SECRET=...
DATABASE_URL=postgresql+asyncpg://postgres:PASS@db.tu-proyecto.supabase.co:6543/postgres
ENCRYPTION_KEY=...
REDIS_URL=${{Redis.REDIS_URL}}
ENVIRONMENT=production
ALLOWED_ORIGINS=https://tu-frontend.vercel.app
CELERY_LOG_LEVEL=info
CELERY_CONCURRENCY=2
CHATKIT_MODE=multi_agent
```

**Save** → Railway redeploya automáticamente.

## 6️⃣ Verificar (2 min)

### Backend Health Check
```bash
curl https://tu-backend.up.railway.app/health
# Esperado: {"status":"healthy"}
```

### Flower UI
```bash
open https://tu-flower.up.railway.app
# Debe mostrar 1 worker activo
```

### Logs
Railway Dashboard > Cada servicio > Logs tab
- Backend: `Application startup complete`
- Worker: `celery@... ready`
- Beat: `Scheduler: Sending due task`

---

## ✅ Checklist Final

- [ ] 4 servicios corriendo (backend, worker, beat, flower)
- [ ] Redis plugin activo
- [ ] Variables configuradas (10+ variables)
- [ ] Backend health check OK
- [ ] Flower muestra 1+ workers
- [ ] Logs sin errores

---

## 🎯 URLs Importantes

| Servicio | URL |
|----------|-----|
| Backend API | `https://tu-backend.up.railway.app` |
| API Docs | `https://tu-backend.up.railway.app/docs` |
| Flower UI | `https://tu-flower.up.railway.app` |
| Railway Dashboard | `https://railway.app/project/tu-project-id` |

---

## 📊 Costos Estimados

| Servicio | Costo/mes |
|----------|-----------|
| Backend (FastAPI) | ~$7 |
| Celery Worker | ~$5 |
| Celery Beat | ~$3 |
| Flower | ~$3 |
| Redis Plugin | ~$5 |
| **Total** | **~$23** |

---

## 🐛 Troubleshooting Rápido

**Build falla**: Ver logs en Railway Dashboard > Servicio > Deployments > Build Logs

**Health check falla**:
```bash
railway logs -s backend | grep ERROR
```

**Celery no procesa tasks**:
```bash
railway logs -s celery-worker | grep "ready"
```

**502 Bad Gateway**: Verificar que `$PORT` no esté hardcodeado

---

Para guía completa ver [RAILWAY_SETUP.md](./RAILWAY_SETUP.md)

**Última actualización**: 2025-01-29
