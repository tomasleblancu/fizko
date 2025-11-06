# Seed Scripts - Ejemplos de Uso

## Índice
- [Direcciones de Sincronización](#direcciones-de-sincronización)
- [Casos de Uso Comunes](#casos-de-uso-comunes)
- [Workflows Completos](#workflows-completos)

## Direcciones de Sincronización

El sistema permite sincronizar en **cualquier dirección** usando `--from` y `--to`:

```
         staging → production  (deployment normal)
         production → staging  (sync back, troubleshooting)
         local → staging       (testing local changes)
         staging → local       (get latest config)
         production → local    (debug production issues)
         local → production    (emergency hotfix - no recomendado)
```

## Casos de Uso Comunes

### 1. Deployment Normal: Staging → Production

**Escenario**: Desarrollaste y probaste nuevos templates en staging, listo para producción.

```bash
# 1. Dry run para ver qué se sincronizará
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --dry-run

# 2. Revisar output cuidadosamente

# 3. Aplicar cambios
python -m scripts.seed notification-templates \
  --from staging \
  --to production
```

### 2. Sync Back: Production → Staging

**Escenario**: Alguien modificó templates directamente en producción (hotfix) y necesitas traer esos cambios a staging.

```bash
# 1. Ver qué cambios hay en producción
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --dry-run \
  --verbose

# 2. Sincronizar de prod a staging
python -m scripts.seed notification-templates \
  --from production \
  --to staging
```

⚠️ **Nota**: Esto sobrescribirá templates en staging si producción es más reciente.

### 3. Get Latest Config: Staging → Local

**Escenario**: Quieres trabajar con los templates más recientes de staging en tu entorno local.

```bash
# Traer templates de staging a local
python -m scripts.seed notification-templates \
  --from staging \
  --to local

# También event templates
python -m scripts.seed event-templates \
  --from staging \
  --to local

# O todo junto
python -m scripts.seed all \
  --from staging \
  --to local
```

### 4. Test Local Changes: Local → Staging

**Escenario**: Creaste templates nuevos localmente y quieres probarlos en staging antes de producción.

```bash
# Sincronizar solo tus nuevos templates
python -m scripts.seed notification-templates \
  --from local \
  --to staging \
  --codes my_new_template_1,my_new_template_2 \
  --dry-run

# Si se ve bien, aplicar
python -m scripts.seed notification-templates \
  --from local \
  --to staging \
  --codes my_new_template_1,my_new_template_2
```

### 5. Debug Production: Production → Local

**Escenario**: Hay un problema en producción y necesitas los templates exactos de prod en local para debuggear.

```bash
# Traer configuración exacta de producción
python -m scripts.seed all \
  --from production \
  --to local

# Ahora tienes el estado exacto de prod en local para testing
```

### 6. Sincronizar Templates Específicos

**Escenario**: Solo necesitas sincronizar algunos templates, no todos.

```bash
# Staging → Production (solo 3 templates)
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --codes f29_reminder,daily_business_summary,weekly_business_summary \
  --dry-run

# Production → Staging (solo 1 template que se modificó)
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --codes emergency_notification
```

### 7. Emergency Hotfix: Local → Production

**Escenario**: Necesitas hacer un hotfix urgente directamente desde local a producción.

```bash
# 🚨 SOLO PARA EMERGENCIAS 🚨

# 1. SIEMPRE dry run primero
python -m scripts.seed notification-templates \
  --from local \
  --to production \
  --codes emergency_fix_template \
  --dry-run \
  --verbose

# 2. Confirmar múltiples veces que es correcto

# 3. Aplicar
python -m scripts.seed notification-templates \
  --from local \
  --to production \
  --codes emergency_fix_template

# 4. Sincronizar el cambio a staging después
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --codes emergency_fix_template
```

⚠️ **IMPORTANTE**: Después de un hotfix directo a producción, **siempre sincronizar de vuelta a staging** para mantener consistencia.

## Workflows Completos

### Workflow A: Desarrollo de Nuevo Template

```bash
# 1. Desarrollar localmente
# - Crear template en base de datos local
# - Probar con datos locales

# 2. Subir a staging para testing
python -m scripts.seed notification-templates \
  --from local \
  --to staging \
  --codes new_template_v1

# 3. Probar en staging
# - Verificar que funciona con datos reales
# - Hacer ajustes si es necesario

# 4. Si se necesitan ajustes, actualizar local y volver a subir
python -m scripts.seed notification-templates \
  --from local \
  --to staging \
  --codes new_template_v1

# 5. Cuando esté listo, subir a producción
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --codes new_template_v1 \
  --dry-run

python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --codes new_template_v1
```

### Workflow B: Actualización Masiva de Templates

```bash
# 1. Verificar estado actual
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --dry-run \
  --verbose

# 2. Analizar output
# - ¿Cuántos templates se crearán?
# - ¿Cuántos se actualizarán?
# - ¿Hay cambios inesperados?

# 3. Si todo se ve bien, proceder con cada tipo
python -m scripts.seed notification-templates \
  --from staging \
  --to production

python -m scripts.seed event-templates \
  --from staging \
  --to production

# 4. Verificar en producción que todo funcionó
# - Revisar logs
# - Probar una notificación de prueba
```

### Workflow C: Mantener Environments Sincronizados

```bash
# Escenario: Staging es la "fuente de verdad"
# Goal: Mantener local y producción sincronizados con staging

# Cada día/semana:

# 1. Actualizar local desde staging
python -m scripts.seed all --from staging --to local

# 2. Hacer desarrollo local
# ... cambios ...

# 3. Subir cambios a staging
python -m scripts.seed all --from local --to staging --codes my_changes

# 4. Cuando esté listo para release, subir a producción
python -m scripts.seed all --from staging --to production --dry-run
python -m scripts.seed all --from staging --to production
```

### Workflow D: Rollback de Cambios Malos

```bash
# Escenario: Subiste cambios a producción pero hay un problema

# 1. Si staging tiene la versión buena:
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --codes problematic_template

# 2. Si necesitas restaurar desde un backup:
# a) Restaurar template en staging desde backup
# b) Luego sincronizar a producción
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --codes problematic_template

# 3. Verificar en producción que se arregló
```

### Workflow E: Sync Bidireccional (Merge Cambios)

```bash
# Escenario:
# - En staging creaste template A
# - En producción se modificó template B (hotfix)
# - Necesitas ambos cambios en ambos lados

# 1. Subir template A de staging a producción
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --codes template_a

# 2. Bajar template B de producción a staging
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --codes template_b

# 3. Opcional: actualizar local con todo
python -m scripts.seed all --from staging --to local
```

## Comparación de Comandos

### Staging → Production (más común)

```bash
# Opción 1: Explicit (recomendado para scripts)
python -m scripts.seed notification-templates --from staging --to production

# Opción 2: Implicit (staging es default)
python -m scripts.seed notification-templates --to production

# Son equivalentes
```

### Production → Staging (sync back)

```bash
# DEBE ser explicit (no hay default para production como source)
python -m scripts.seed notification-templates --from production --to staging
```

### Local → Anywhere (testing)

```bash
# Local a staging
python -m scripts.seed notification-templates --from local --to staging

# Local a production (emergencia)
python -m scripts.seed notification-templates --from local --to production
```

### Anywhere → Local (debug)

```bash
# Staging a local
python -m scripts.seed notification-templates --from staging --to local

# Production a local
python -m scripts.seed notification-templates --from production --to local
```

## Matrix de Direcciones

| From → To | Command | Uso Común | Frecuencia |
|-----------|---------|-----------|------------|
| staging → production | `--to production` | Deployment normal | Diario |
| production → staging | `--from production --to staging` | Sync back hotfix | Raro |
| staging → local | `--from staging --to local` | Get latest config | Diario |
| local → staging | `--from local --to staging` | Test local changes | Diario |
| production → local | `--from production --to local` | Debug production | Ocasional |
| local → production | `--from local --to production` | Emergency hotfix | Muy raro |

## Tips & Best Practices

### 1. Siempre usar --dry-run primero

```bash
# ❌ MAL
python -m scripts.seed notification-templates --to production

# ✅ BIEN
python -m scripts.seed notification-templates --to production --dry-run
# revisar output...
python -m scripts.seed notification-templates --to production
```

### 2. Usar --verbose para cambios importantes

```bash
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --verbose \
  --dry-run

# Output mostrará exactamente qué campos cambiaron:
# Field 'message_template' differs for daily_business_summary
# Field 'timing_config' differs for f29_reminder
```

### 3. Filtrar por --codes para cambios específicos

```bash
# En lugar de sincronizar todo:
python -m scripts.seed notification-templates --to production

# Sincronizar solo lo que cambió:
python -m scripts.seed notification-templates \
  --to production \
  --codes new_template,modified_template
```

### 4. Mantener staging como fuente de verdad

```bash
# Flujo recomendado:
# local → staging (desarrollo)
# staging → production (deployment)
# production → staging (solo para hotfixes)

# Evitar:
# local → production (skips staging testing)
# production cambios manuales (sin tracking)
```

### 5. Documentar hotfixes

```bash
# Si haces un hotfix directo a producción:

# 1. Aplicar el hotfix
python -m scripts.seed notification-templates \
  --from local \
  --to production \
  --codes hotfix_template

# 2. Sincronizar a staging inmediatamente
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --codes hotfix_template

# 3. Documentar en git commit y/o issue tracker
git commit -m "hotfix: Fix notification template X in production"
```

## Troubleshooting

### Error: "Source and target cannot be the same"

```bash
# ❌ Esto fallará:
python -m scripts.seed notification-templates --from staging --to staging

# ✅ Asegurar que from ≠ to
python -m scripts.seed notification-templates --from staging --to production
```

### Templates no se actualizan (se skippean)

```bash
# Usar --verbose para ver por qué:
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --verbose \
  --dry-run

# Si staging.updated_at es más viejo que production.updated_at,
# el script skippea la actualización (asume que production es más reciente)

# Solución: Actualizar el timestamp en staging manualmente:
# UPDATE notification_templates
# SET updated_at = NOW()
# WHERE code = 'template_name';
```

### Sincronización bidireccional causó conflictos

```bash
# Si modificaste el mismo template en ambos lados:

# Opción 1: Decidir cuál es la "verdad"
# a) Si staging es correcto:
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --codes conflicted_template

# b) Si production es correcto:
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --codes conflicted_template

# Opción 2: Merge manual
# 1. Exportar ambos a JSON para comparar
# 2. Decidir qué campos tomar de cada uno
# 3. Actualizar manualmente el que sea fuente de verdad
# 4. Sincronizar normalmente
```
