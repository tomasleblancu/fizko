# Quick Start Guide - Seed Scripts

## Setup Inicial (Una vez)

### 1. Configurar variables de entorno

Edita tu `.env` y agrega las credenciales de Supabase:

```bash
# Staging
STAGING_SUPABASE_URL=https://xxx.supabase.co
STAGING_SUPABASE_SERVICE_KEY=eyJhbG...

# Production
PROD_SUPABASE_URL=https://yyy.supabase.co
PROD_SUPABASE_SERVICE_KEY=eyJhbG...
```

💡 **Tip**: Obtén las credenciales de Supabase desde:
- Supabase Dashboard → Settings → API → Project API keys → `service_role` key (secret)
- **⚠️ NO uses anon keys**, usa service_role key para acceso completo

### 2. Verificar conexión

```bash
cd backend

# Test que las variables estén configuradas
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ STAGING_SUPABASE_URL' if os.getenv('STAGING_SUPABASE_URL') else '❌ Missing STAGING_SUPABASE_URL')"
```

## Uso Diario

> **💡 Importante**: El sistema permite sincronizar en **cualquier dirección** usando `--from` y `--to`:
> - `staging → production` (deployment normal)
> - `production → staging` (sync back de hotfixes)
>
> **🔒 Seguridad**: El flag `--full-sync` está **BLOQUEADO** para producción como target. Solo puedes usar `--full-sync` cuando sincronizas HACIA staging u otros entornos de desarrollo. Esto previene eliminaciones accidentales de datos de producción.

### Caso 1: Sincronizar Notification Templates de Staging → Production

```bash
cd backend

# 1. SIEMPRE empezar con dry-run
python -m scripts.seed notification-templates --to production --dry-run

# 2. Revisar el output. Deberías ver algo como:
#    ✨ Create: 2 records
#    🔄 Update: 5 records
#    ⏭️  Skip: 10 records

# 3. Si todo se ve bien, ejecutar sin dry-run
python -m scripts.seed notification-templates --to production

# 4. Confirmar cuando pregunte:
#    ⚠️  You are about to sync to PRODUCTION. Continue? [y/N]: y
```

### Caso 2: Sincronizar Solo Templates Específicos

```bash
# Supongamos que creaste o modificaste estos templates en staging:
# - daily_business_summary_v2
# - weekly_business_summary

python -m scripts.seed notification-templates \
  --to production \
  --codes daily_business_summary_v2,weekly_business_summary \
  --dry-run

# Si se ve bien:
python -m scripts.seed notification-templates \
  --to production \
  --codes daily_business_summary_v2,weekly_business_summary
```

### Caso 3: Sincronizar Event Templates

```bash
# Dry run
python -m scripts.seed event-templates --to production --dry-run

# Aplicar
python -m scripts.seed event-templates --to production
```

### Caso 4: Sincronizar Cualquier Tabla (Genérico)

```bash
# Ejemplo: Sincronizar brain_contexts
python -m scripts.seed sync \
  --table brain_contexts \
  --unique-key context_id \
  --to production \
  --dry-run

# Si se ve bien:
python -m scripts.seed sync \
  --table brain_contexts \
  --unique-key context_id \
  --to production
```

### Caso 5: Sincronizar Todo

```bash
# Sincroniza notification_templates + event_templates
python -m scripts.seed all --to production --dry-run

# Si todo OK:
python -m scripts.seed all --to production
```

### Caso 6: Sincronizar de Production → Staging (Sync Back)

```bash
# Escenario: Se hizo un hotfix en producción y necesitas traerlo a staging

# 1. Ver qué cambió en producción
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --dry-run \
  --verbose

# 2. Si se ve bien, aplicar
python -m scripts.seed notification-templates \
  --from production \
  --to staging
```

### Caso 7: Full Sync (Sincronización Completa con Eliminación)

```bash
# Escenario: Necesitas que staging sea una COPIA EXACTA de producción
# - Elimina registros en staging que no existen en producción
# - Crea registros faltantes
# - Actualiza registros existentes
# - PRESERVA los IDs de la fuente (producción)

# 1. SIEMPRE dry-run primero para ver qué se eliminará
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --full-sync \
  --dry-run \
  --verbose

# 2. Revisar cuidadosamente el output:
#    ✨ Create: X records
#    🔄 Update: Y records
#    🗑️  Delete: Z records  ← ¡CUIDADO CON ESTO!
#    ⏭️  Skip: W records

# 3. Si estás seguro, aplicar
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --full-sync

# ⚠️ NOTA: --full-sync está BLOQUEADO para production como target
# Este comando fallará:
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --full-sync
# Error: ❌ SAFETY BLOCK: --full-sync is not allowed when target is 'production'
```

### Caso 8: Ver Detalles de Cambios (Verbose)

```bash
# Modo verbose muestra QUÉ campos cambiaron
python -m scripts.seed notification-templates --to production --verbose --dry-run

# Output incluirá:
#    Field 'message_template' differs for daily_business_summary
#    Field 'timing_config' differs for f29_reminder
```

## Workflow Recomendado para Producción

```bash
# 1. Desarrollar y probar localmente
# 2. Subir cambios a staging (git push)
# 3. Verificar en staging que todo funciona
# 4. Sincronizar a producción:

cd backend

# a) Dry run con verbose para ver todo
python -m scripts.seed notification-templates --to production --dry-run --verbose

# b) Revisar CUIDADOSAMENTE el output

# c) Si todo correcto, aplicar
python -m scripts.seed notification-templates --to production

# d) Verificar en producción que funcionó
```

## Troubleshooting Rápido

### Error: "Missing Supabase config for staging"

```bash
# Verificar que el .env tenga las variables:
grep STAGING_SUPABASE backend/.env

# Si no existe, agregarla:
echo "STAGING_SUPABASE_URL=https://xxx.supabase.co" >> backend/.env
echo "STAGING_SUPABASE_SERVICE_KEY=eyJhbG..." >> backend/.env
```

### Error: "permission denied" o similar

```bash
# Verificar que estés usando SERVICE ROLE KEY, no anon key
# Service role key empieza con: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...
```

### Templates no se actualizan cuando deberían

```bash
# Usar verbose para ver por qué se skippea:
python -m scripts.seed notification-templates --to production --verbose --dry-run

# El script compara:
# 1. updated_at timestamp (si source > target → update)
# 2. Contenido de campos (si difieren → update)
```

## Cheat Sheet de Comandos

### Local (sin Docker)

```bash
# Notification templates: staging → prod (dry run)
python -m scripts.seed notification-templates --to production --dry-run

# Notification templates: staging → prod (live)
python -m scripts.seed notification-templates --to production

# Event templates: staging → prod (dry run)
python -m scripts.seed event-templates --to production --dry-run

# Event templates: staging → prod (live)
python -m scripts.seed event-templates --to production

# Cualquier tabla: staging → prod (dry run)
python -m scripts.seed sync --table your_table --unique-key your_key --to production --dry-run

# Todo: staging → prod (dry run)
python -m scripts.seed all --to production --dry-run

# Todo: staging → prod (live)
python -m scripts.seed all --to production

# Sincronizar templates específicos
python -m scripts.seed notification-templates --to production --codes template1,template2

# Full sync: production → staging (elimina registros en staging que no están en prod)
python -m scripts.seed notification-templates --from production --to staging --full-sync --dry-run
python -m scripts.seed notification-templates --from production --to staging --full-sync

# Modo verbose (ver detalles)
python -m scripts.seed notification-templates --to production --verbose --dry-run
```

### Con Docker

**Opción A: Docker Exec** (recomendado si el contenedor ya está corriendo):

```bash
# Notification templates: staging → prod (dry run)
docker exec fizko-backend python -m scripts.seed notification-templates --to production --dry-run

# Notification templates: staging → prod (live)
docker exec fizko-backend python -m scripts.seed notification-templates --to production

# Comando genérico para cualquier tabla
docker exec fizko-backend python -m scripts.seed sync \
  --table brain_contexts \
  --unique-key context_id \
  --to production \
  --dry-run \
  --verbose

# Full sync: production → staging
docker exec fizko-backend python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --full-sync \
  --dry-run
```

**Opción B: Docker Compose Run** (crea un nuevo contenedor temporal):

```bash
# Notification templates: staging → prod (dry run)
docker compose run --rm backend seed notification-templates --to production --dry-run

# Comando genérico para cualquier tabla
docker compose run --rm backend seed sync \
  --table brain_contexts \
  --unique-key context_id \
  --to production \
  --dry-run

# Full sync: production → staging
docker compose run --rm backend seed notification-templates \
  --from production \
  --to staging \
  --full-sync \
  --dry-run
```

**Opción C: Docker Run** (desde imagen, requiere rebuild):

```bash
# Notification templates: staging → prod (dry run)
docker run --rm --env-file backend/.env fizko-backend seed notification-templates --to production --dry-run

# Comando genérico para cualquier tabla
docker run --rm --env-file backend/.env fizko-backend seed sync \
  --table brain_contexts \
  --unique-key context_id \
  --to production \
  --dry-run

# Ejemplo real: subscription_plans
docker run --rm --env-file backend/.env fizko-backend seed sync \
  --table subscription_plans \
  --unique-key code \
  --to production \
  --dry-run \
  --verbose
```

**💡 Tip**: Usa `docker exec` si tus contenedores ya están corriendo (más rápido). Usa `docker compose run` si necesitas asegurar que tienes las últimas variables de entorno.

## Ver Ayuda

```bash
# Ayuda general
python -m scripts.seed --help

# Ayuda de comando específico
python -m scripts.seed notification-templates --help
python -m scripts.seed event-templates --help
python -m scripts.seed sync --help
python -m scripts.seed all --help
```

## Próximos Pasos

Para documentación completa, ver [README.md](./README.md)
