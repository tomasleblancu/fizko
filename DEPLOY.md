# Guía de Deployment - Fizko

Esta guía te ayudará a deployear la aplicación Fizko en Railway (backend) y Vercel (frontend) usando un monorepo.

## Arquitectura

```
┌─────────────────┐
│  Vercel (FREE)  │ → Frontend React/Vite
│  fizko.vercel   │
│  .app            │
└────────┬────────┘
         │ HTTPS API calls
         ↓
┌─────────────────┐
│ Railway ($10/mo)│ → Backend FastAPI
│ api.fizko.com   │    - REST API
│                 │    - SII Integration (Selenium)
│                 │    - Multi-agent ChatKit
└────────┬────────┘
         │ PostgreSQL
         ↓
┌─────────────────┐
│ Supabase        │ → Database + Auth
│ (tu plan)       │
└─────────────────┘
```

## Pre-requisitos

- [ ] Cuenta en [Railway](https://railway.app/)
- [ ] Cuenta en [Vercel](https://vercel.com/)
- [ ] Proyecto Supabase configurado
- [ ] OpenAI API Key
- [ ] Repositorio Git (GitHub, GitLab, etc.)

---

## 1. Preparar el Repositorio

### Crear repositorio en GitHub/GitLab

```bash
# Ya inicializado localmente, ahora conecta al remoto
git remote add origin https://github.com/tu-usuario/fizko-v2.git

# Hacer primer commit
git add .
git commit -m "Initial commit: Fizko monorepo setup

- Backend: FastAPI + ChatKit + SII integration
- Frontend: React + Vite + Supabase Auth
- Deployment configs for Railway + Vercel"

# Push
git push -u origin main
```

---

## 2. Deploy Backend en Railway

### Paso 1: Crear Proyecto en Railway

1. Ve a [railway.app/new](https://railway.app/new)
2. Selecciona **"Deploy from GitHub repo"**
3. Conecta tu cuenta de GitHub
4. Selecciona el repositorio `fizko-v2`

### Paso 2: Configurar Variables de Entorno

En el dashboard de Railway, ve a **Variables** y agrega:

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-tu-key-aqui

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu-anon-key
SUPABASE_JWT_SECRET=tu-jwt-secret

# Database (desde Supabase Settings > Database > Connection String)
DATABASE_URL=postgresql+asyncpg://postgres:password@db.proyecto.supabase.co:5432/postgres

# Encryption (generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=tu-encryption-key-base64

# Environment
ENVIRONMENT=production

# CORS (agregar tu dominio de Vercel después)
ALLOWED_ORIGINS=https://fizko.vercel.app,https://fizko-preview-*.vercel.app
```

### Paso 3: Configurar Build

Railway debería detectar automáticamente el `railway.json`, pero verifica:

- **Build Command**: Docker (detectado por `Dockerfile`)
- **Root Directory**: `backend/`
- **Dockerfile Path**: `backend/Dockerfile`

### Paso 4: Deploy

1. Railway automáticamente deployará
2. Espera a que el build complete (~3-5 min)
3. Verifica los logs para asegurar que no hay errores
4. Anota la URL generada (ej: `fizko-backend-production.up.railway.app`)

### Paso 5: Configurar Dominio Custom (Opcional)

1. En Railway Settings > Domains
2. Agrega un dominio custom (ej: `api.fizko.cl`)
3. Configura los DNS según las instrucciones

---

## 3. Deploy Frontend en Vercel

### Paso 1: Crear Proyecto en Vercel

1. Ve a [vercel.com/new](https://vercel.com/new)
2. **Import Git Repository**
3. Selecciona `fizko-v2`

### Paso 2: Configurar Project Settings

Vercel debería detectar `vercel.json`, pero verifica:

- **Framework Preset**: Vite
- **Root Directory**: `frontend/`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### Paso 3: Configurar Variables de Entorno

En **Settings > Environment Variables**, agrega:

#### Production

```bash
VITE_API_URL=https://fizko-backend-production.up.railway.app
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=tu-anon-key
VITE_CHATKIT_API_DOMAIN_KEY=domain_pk_tu_dominio_verificado
```

#### Preview & Development

```bash
VITE_API_URL=https://fizko-backend-production.up.railway.app
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=tu-anon-key
VITE_CHATKIT_API_DOMAIN_KEY=domain_pk_localhost_dev
```

### Paso 4: Deploy

1. Click **Deploy**
2. Espera 1-2 minutos
3. Vercel te dará una URL (ej: `fizko.vercel.app`)

### Paso 5: Actualizar CORS en Backend

Regresa a **Railway** y actualiza la variable:

```bash
ALLOWED_ORIGINS=https://fizko.vercel.app,https://fizko-git-*.vercel.app
```

---

## 4. Verificar Deployment

### Backend Health Check

```bash
curl https://tu-backend.railway.app/health
# Debería retornar: {"status": "healthy"}
```

### Frontend

1. Abre `https://fizko.vercel.app`
2. Intenta hacer login con Supabase
3. Verifica que la API responda correctamente

---

## 5. Configuración Post-Deploy

### Migraciones de Base de Datos

**IMPORTANTE**: Debes aplicar todas las migraciones en Supabase **antes** de que los usuarios empiecen a registrarse.

#### Aplicar Migraciones en Supabase

1. Ve a **Supabase Dashboard > SQL Editor**
2. Aplica las migraciones en orden:

```sql
-- 001_initial_schema.sql (tablas base)
-- 002_add_sii_password.sql
-- ...
-- 011_add_profile_trigger.sql (CRÍTICO - crea perfiles automáticamente)
```

#### Migration 011 - Profile Trigger (CRÍTICO)

La migration `011_add_profile_trigger.sql` es **esencial** porque:
- ✅ Crea automáticamente un perfil cuando un usuario se registra
- ✅ Extrae datos de Google OAuth (nombre, avatar, email)
- ✅ Previene errores cuando la app intenta acceder al perfil

**Si tienes usuarios existentes sin perfil**, descomenta el bloque de BACKFILL en la migration 011 para crearles perfiles.

#### Verificar que el Trigger Funciona

```sql
-- Verificar que el trigger existe
SELECT tgname, tgenabled
FROM pg_trigger
WHERE tgname = 'on_auth_user_created';

-- Verificar que todos los usuarios tienen perfil
SELECT
    COUNT(*) as users_without_profile
FROM auth.users u
LEFT JOIN public.profiles p ON p.id = u.id
WHERE p.id IS NULL;
-- Debería retornar 0
```

### Monitoreo

#### Railway
- Logs: Dashboard > Deployments > View Logs
- Metrics: Dashboard > Metrics

#### Vercel
- Logs: Dashboard > Deployments > Logs
- Analytics: Dashboard > Analytics

#### Supabase
- Database: Dashboard > Database > Logs
- Auth: Dashboard > Authentication > Logs

---

## 6. CI/CD Automático

Ambos servicios tienen CI/CD automático:

### Railway
- Push a `main` → Deploy automático a producción
- Webhooks disponibles para notificaciones

### Vercel
- Push a `main` → Deploy a producción
- PRs → Preview deployments automáticos
- Comentarios en PRs con preview URLs

---

## 7. Costos Estimados

| Servicio | Plan | Costo Mensual |
|----------|------|---------------|
| Railway (Backend) | Hobby | ~$10-15 USD |
| Vercel (Frontend) | Hobby | $0 USD |
| Supabase | Free/Pro | $0-25 USD |
| **Total** | | **~$10-40 USD/mes** |

---

## 8. Troubleshooting

### Backend no inicia

```bash
# Verifica logs en Railway
# Común: falta una variable de entorno
# Solución: revisa que todas las variables estén configuradas
```

### Frontend no conecta al backend

```bash
# Verifica CORS en backend
# Verifica que VITE_API_URL apunte a Railway
# Verifica que Railway esté corriendo
```

### SII Integration falla

```bash
# Chrome/Selenium puede necesitar más memoria en Railway
# Upgrade a plan con más RAM si es necesario
```

---

## 9. Desarrollo Local

### Backend

```bash
cd backend
cp .env.example .env
# Edita .env con tus credenciales
uv sync
uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.example .env
# Edita .env con tus credenciales
npm install
npm run dev
```

---

## 10. Próximos Pasos

- [ ] Configurar dominio custom en ambos servicios
- [ ] Agregar Sentry para error tracking
- [ ] Configurar rate limiting en backend
- [ ] Setup de backups automáticos en Supabase
- [ ] Configurar alertas de uptime (ej: UptimeRobot)

---

## Recursos

- [Railway Docs](https://docs.railway.app/)
- [Vercel Docs](https://vercel.com/docs)
- [Supabase Docs](https://supabase.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)
