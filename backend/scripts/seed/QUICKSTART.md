# Quick Start Guide - Seed Scripts

## Setup Inicial (Una vez)

### 1. Configurar variables de entorno

Edita tu `.env` y agrega las URLs de las bases de datos:

```bash
# Backend local
DATABASE_URL=postgresql://postgres:your_pass@localhost:6543/fizko

# Staging (Supabase)
STAGING_DATABASE_URL=postgresql://postgres.xxxx:your_pass@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# Production (Supabase)
DATABASE_URL_PRODUCTION=postgresql://postgres.yyyy:your_pass@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

💡 **Tip**: Obtén las URLs de Supabase desde:
- Supabase Dashboard → Settings → Database → Connection string (Transaction mode)

### 2. Verificar conexión

```bash
cd backend

# Test que las variables estén configuradas
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ STAGING_DATABASE_URL' if os.getenv('STAGING_DATABASE_URL') else '❌ Missing STAGING_DATABASE_URL')"
```

## Uso Diario

> **💡 Importante**: El sistema permite sincronizar en **cualquier dirección** usando `--from` y `--to`:
> - `staging → production` (deployment normal)
> - `production → staging` (sync back de hotfixes)
> - `local → staging` (test local changes)
> - `staging → local` (get latest config)
> - Cualquier combinación válida

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

### Caso 4: Sincronizar Todo

```bash
# Sincroniza notification_templates + event_templates
python -m scripts.seed all --to production --dry-run

# Si todo OK:
python -m scripts.seed all --to production
```

### Caso 5: Sincronizar de Production → Staging (Sync Back)

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

### Caso 6: Traer Config Reciente a Local

```bash
# Traer templates de staging a tu entorno local
python -m scripts.seed all --from staging --to local

# O solo notification templates
python -m scripts.seed notification-templates --from staging --to local
```

### Caso 7: Ver Detalles de Cambios (Verbose)

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

### Error: "Environment variable STAGING_DATABASE_URL not set"

```bash
# Verificar que el .env tenga las variables:
grep STAGING_DATABASE_URL backend/.env

# Si no existe, agregarla:
echo "STAGING_DATABASE_URL=postgresql://..." >> backend/.env
```

### Error: "could not connect to server"

```bash
# Verificar que la URL sea correcta y accesible
# Para Supabase, usar el pooler (port 5432 o 6543), NO direct connection
```

### Templates no se actualizan cuando deberían

```bash
# Usar verbose para ver por qué se skippea:
python -m scripts.seed notification-templates --to production --verbose --dry-run

# El script compara:
# 1. updated_at timestamp (si source > target → update)
# 2. Contenido de campos clave (message_template, timing_config, etc.)
```

## Cheat Sheet de Comandos

```bash
# Notification templates: staging → prod (dry run)
python -m scripts.seed notification-templates --to production --dry-run

# Notification templates: staging → prod (live)
python -m scripts.seed notification-templates --to production

# Event templates: staging → prod (dry run)
python -m scripts.seed event-templates --to production --dry-run

# Event templates: staging → prod (live)
python -m scripts.seed event-templates --to production

# Todo: staging → prod (dry run)
python -m scripts.seed all --to production --dry-run

# Todo: staging → prod (live)
python -m scripts.seed all --to production

# Sincronizar templates específicos
python -m scripts.seed notification-templates --to production --codes template1,template2

# Modo verbose (ver detalles)
python -m scripts.seed notification-templates --to production --verbose --dry-run

# Local → Staging (útil para testing)
python -m scripts.seed notification-templates --from local --to staging
```

## Ver Ayuda

```bash
# Ayuda general
python -m scripts.seed --help

# Ayuda de comando específico
python -m scripts.seed notification-templates --help
python -m scripts.seed event-templates --help
python -m scripts.seed all --help
```

## Próximos Pasos

Para documentación completa, ver [README.md](./README.md)
