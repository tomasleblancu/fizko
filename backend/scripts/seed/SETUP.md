# Setup Guide - Seed Scripts

## Variables de Entorno Requeridas

Para usar los seed scripts, necesitas agregar las URLs de las bases de datos de cada entorno a tu `.env`.

### 1. Obtener las URLs de Supabase

#### Para Staging:

1. Ve a [Supabase Dashboard](https://app.supabase.com)
2. Selecciona tu proyecto de **staging**
3. Ve a **Settings** → **Database**
4. En **Connection string**, selecciona el tab **URI**
5. Cambia el mode a **Transaction** (pooler mode)
6. Copia la URL (se ve así: `postgresql://postgres.xxx:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres`)

#### Para Production:

1. Repite el mismo proceso pero en el proyecto de **production**
2. Copia la URL de production

### 2. Obtener Service Role Keys (para método genérico con SDK - opcional)

Si quieres usar el método genérico que funciona con cualquier tabla, también necesitas las **Service Role Keys**:

#### Para Staging:
1. Supabase Dashboard → Selecciona proyecto staging
2. Ve a **Settings** → **API**
3. En "Project API keys", copia el **`service_role` key** (NO el `anon` key)

#### Para Production:
1. Repite en el proyecto de production
2. Copia el **`service_role` key**

⚠️ **MUY IMPORTANTE**: El `service_role` key bypasea RLS. Úsalo SOLO para scripts backend, nunca lo expongas en frontend.

### 3. Agregar Variables al .env

Edita tu `backend/.env` y agrega estas líneas:

```bash
# Seed Scripts - Database URLs (método SQL directo)

# Local (ya la tienes)
DATABASE_URL=postgresql://postgres:your_local_pass@localhost:6543/fizko

# Staging (Supabase pooler)
STAGING_DATABASE_URL=postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# Production (Supabase pooler)
DATABASE_URL_PRODUCTION=postgresql://postgres.yyyyyyyyyyyy:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# Seed Scripts - Supabase SDK (método genérico - OPCIONAL)
# Solo necesario si usas scripts/seed_generic.py

# Staging
STAGING_SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
STAGING_SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (service_role key)

# Production
PROD_SUPABASE_URL=https://yyyyyyyyyyyy.supabase.co
PROD_SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (service_role key)
```

## Dos Métodos Disponibles

El sistema ofrece **dos métodos** de sincronización:

### Método 1: SQL Directo (scripts/seed/__main__.py)
- **Pros**: Más control, transaccional, funciona con cualquier PostgreSQL
- **Contras**: Necesitas crear un seeder específico para cada tabla
- **Variables necesarias**: `DATABASE_URL`, `STAGING_DATABASE_URL`, `DATABASE_URL_PRODUCTION`
- **Ejemplo**:
  ```bash
  python -m scripts.seed notification-templates --to production
  ```

### Método 2: Supabase SDK Genérico (scripts/seed_generic.py)
- **Pros**: Genérico (cualquier tabla), validación automática de columnas, menos código
- **Contras**: Solo Supabase, requiere service_role keys (sensibles)
- **Variables necesarias**: `STAGING_SUPABASE_URL/KEY`, `PROD_SUPABASE_URL/KEY`
- **Ejemplo**:
  ```bash
  python scripts/seed_generic.py notification_templates code --to production
  ```

**Recomendación**:
- Usa **Método 1** si ya lo configuraste o prefieres control total
- Usa **Método 2** para sincronizar tablas nuevas rápidamente sin escribir código

Ambos métodos funcionan igual de bien. Puedes usar ambos en paralelo.

⚠️ **IMPORTANTE**:
- Reemplaza `[YOUR-PASSWORD]` con la contraseña real de cada proyecto
- Usa el **pooler** (puerto 5432 o 6543), NO la conexión directa (puerto 5432 sin pooler)
- Las URLs deben empezar con `postgresql://` (el script las convierte automáticamente a `postgresql+asyncpg://`)

### 3. Verificar la Configuración

```bash
cd backend

# Test que las variables estén configuradas correctamente
python3 << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

envs = {
    "Local": os.getenv("DATABASE_URL"),
    "Staging": os.getenv("STAGING_DATABASE_URL"),
    "Production": os.getenv("DATABASE_URL_PRODUCTION")
}

print("\n🔍 Verificando configuración de environments:\n")
for name, url in envs.items():
    if url:
        # Ocultar password en el output
        masked_url = url.split('@')[0].split(':')[:-1]
        masked_url = ':'.join(masked_url) + ':****@' + url.split('@')[1]
        print(f"✅ {name:12} = {masked_url}")
    else:
        print(f"❌ {name:12} = NOT SET")

print()
EOF
```

Expected output:
```
🔍 Verificando configuración de environments:

✅ Local        = postgresql://postgres:****@localhost:6543/fizko
✅ Staging      = postgresql://postgres.xxxx:****@aws-0-us-east-1.pooler.supabase.com:5432/postgres
✅ Production   = postgresql://postgres.yyyy:****@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

### 4. Test de Conexión (Opcional)

Para verificar que puedes conectarte a cada base de datos:

```bash
cd backend

# Test staging connection
python3 << 'EOF'
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_connection(env_name, env_var):
    load_dotenv()
    url = os.getenv(env_var)

    if not url:
        print(f"❌ {env_name}: Variable {env_var} no configurada")
        return

    # Normalizar URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    try:
        engine = create_async_engine(url, echo=False)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row[0] == 1:
                print(f"✅ {env_name}: Conexión exitosa")
            else:
                print(f"❌ {env_name}: Respuesta inesperada")
        await engine.dispose()
    except Exception as e:
        print(f"❌ {env_name}: Error de conexión - {str(e)[:80]}")

async def main():
    print("\n🔌 Testing database connections...\n")
    await test_connection("Local", "DATABASE_URL")
    await test_connection("Staging", "STAGING_DATABASE_URL")
    await test_connection("Production", "DATABASE_URL_PRODUCTION")
    print()

asyncio.run(main())
EOF
```

Expected output:
```
🔌 Testing database connections...

✅ Local: Conexión exitosa
✅ Staging: Conexión exitosa
✅ Production: Conexión exitosa
```

## Estructura Final del .env

Tu `backend/.env` debería verse así:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
DATABASE_URL=postgresql://postgres:pass@localhost:6543/fizko

# OpenAI
OPENAI_API_KEY=sk-...

# Kapso WhatsApp
KAPSO_API_KEY=your-kapso-api-key
KAPSO_PROJECT_ID=your-project-id
KAPSO_WHATSAPP_CONFIG_ID=your-whatsapp-config-id

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0

# Encryption
ENCRYPTION_KEY=your-32-byte-encryption-key

# Environment
ENVIRONMENT=development

# Seed Scripts - Database URLs
DATABASE_URL=postgresql://postgres:local_pass@localhost:6543/fizko
STAGING_DATABASE_URL=postgresql://postgres.xxxx:staging_pass@aws-0-us-east-1.pooler.supabase.com:5432/postgres
DATABASE_URL_PRODUCTION=postgresql://postgres.yyyy:prod_pass@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

## Seguridad

### Proteger el .env

El archivo `.env` ya está en `.gitignore`, pero asegúrate:

```bash
# Verificar que .env no está trackeado
git status | grep .env

# Si aparece, agregarlo a .gitignore
echo "backend/.env" >> .gitignore
```

### Variables en CI/CD (Futuro)

Si quieres automatizar los seeds en CI/CD (GitHub Actions, etc.):

```yaml
# .github/workflows/sync-production.yml
env:
  STAGING_DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
  DATABASE_URL_PRODUCTION: ${{ secrets.DATABASE_URL_PRODUCTION }}
```

Agregar los secrets en GitHub:
1. Ve a Settings → Secrets and variables → Actions
2. Agregar `STAGING_DATABASE_URL`
3. Agregar `DATABASE_URL_PRODUCTION`

## Troubleshooting

### Error: "Environment variable not set"

```bash
# Verificar que las variables existen
grep -E "(DATABASE_URL|STAGING_DATABASE_URL|DATABASE_URL_PRODUCTION)" backend/.env

# Si no existen, agregarlas según la guía arriba
```

### Error: "could not connect to server"

**Problema**: No se puede conectar a Supabase.

**Soluciones**:

1. **Verificar que usas el pooler**:
   ```
   ✅ Correcto: postgresql://...@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ❌ Incorrecto: postgresql://...@db.xxxx.supabase.co:5432/postgres
   ```

2. **Verificar contraseña**:
   - La contraseña debe ser la de Supabase
   - Si perdiste la contraseña, resetearla en Supabase Dashboard → Settings → Database → Reset password

3. **Verificar firewall/IP**:
   - Supabase puede restringir IPs
   - Ve a Settings → Database → Connection Pooling → Allow connections from any IP (para testing)

### Error: "password authentication failed"

```bash
# La contraseña en el .env es incorrecta

# Para obtener nueva contraseña:
# 1. Ve a Supabase Dashboard
# 2. Settings → Database
# 3. Click "Reset database password"
# 4. Copia la nueva contraseña
# 5. Actualiza .env
```

### Error: SSL/TLS connection issues

```bash
# Agregar ?sslmode=require al final de la URL

STAGING_DATABASE_URL=postgresql://postgres.xxxx:pass@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
```

## Diferencias entre Environments

| Environment | Puerto | Uso | Connection String |
|-------------|--------|-----|-------------------|
| **Local** | 6543 | Desarrollo local | `localhost:6543` |
| **Staging** | 5432 | Testing pre-prod | `aws-0-us-east-1.pooler.supabase.com:5432` |
| **Production** | 5432 | Live app | `aws-0-us-east-1.pooler.supabase.com:5432` |

### ¿Por qué diferentes puertos?

- **Local (6543)**: Es el puerto del pgbouncer local para simular producción
- **Staging/Prod (5432)**: Supabase usa 5432 para el pooler (modo transaction)

## Próximos Pasos

Una vez configurado el `.env`, puedes:

1. Ver la [QUICKSTART Guide](./QUICKSTART.md) para uso básico
2. Ver [EXAMPLES](./EXAMPLES.md) para casos de uso comunes
3. Ver [README](./README.md) para documentación completa

## Quick Test

Para verificar que todo está configurado correctamente:

```bash
# Test dry-run de staging a local (safe)
python -m scripts.seed notification-templates --from staging --to local --dry-run

# Si funciona, verás:
# 🔄 Syncing notification_templates
#    Source: staging
#    Target: local
#    Mode: DRY RUN
# ...
```

Si el comando anterior funciona, ¡estás listo para usar los seed scripts! 🎉
