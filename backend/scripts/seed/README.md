# Fizko Seed Scripts

Sistema modular para sincronizar datos de configuración entre entornos usando Supabase SDK.

## 🎯 Propósito

Estos scripts permiten:
- Sincronizar templates de notificaciones entre entornos
- Sincronizar templates de eventos tributarios
- Sincronizar **cualquier tabla** de forma genérica
- Mantener consistencia de configuraciones en producción
- Realizar migraciones seguras con dry-run

## 📋 Requisitos

### 1. Variables de Entorno

Configurar en `.env`:

```bash
# Staging
STAGING_SUPABASE_URL=https://xxx.supabase.co
STAGING_SUPABASE_SERVICE_KEY=eyJhbG...

# Production
PROD_SUPABASE_URL=https://yyy.supabase.co
PROD_SUPABASE_SERVICE_KEY=eyJhbG...
```

**⚠️ Importante**: Usa **service keys** (no anon keys) para tener acceso completo a las tablas.

### 2. Dependencias

```bash
cd backend
uv pip install supabase python-dotenv click
```

## 🚀 Uso

### Sintaxis General

**Local (sin Docker):**
```bash
cd backend
python -m scripts.seed <command> [options]
```

**Con Docker:**
```bash
# Opción 1: Docker run directo
docker run --rm --env-file backend/.env <imagen-backend> seed <command> [options]

# Opción 2: Docker exec (si el contenedor está corriendo)
docker exec <container-name> python -m scripts.seed <command> [options]

# Opción 3: Docker compose (si usas docker-compose)
docker-compose run --rm backend seed <command> [options]
```

### Comandos Disponibles

#### 1. `notification-templates` - Sincronizar Templates de Notificaciones

```bash
# Ver qué se sincronizaría (dry run) - RECOMENDADO SIEMPRE PRIMERO
python -m scripts.seed notification-templates --to production --dry-run

# Sincronizar todos los templates
python -m scripts.seed notification-templates --to production

# Sincronizar templates específicos
python -m scripts.seed notification-templates \
  --to production \
  --codes f29_reminder,daily_business_summary

# Modo verbose (ver detalles de cambios)
python -m scripts.seed notification-templates --to production --verbose --dry-run
```

#### 2. `event-templates` - Sincronizar Templates de Eventos

```bash
# Dry run
python -m scripts.seed event-templates --to production --dry-run

# Sincronizar todos los eventos
python -m scripts.seed event-templates --to production

# Sincronizar eventos específicos
python -m scripts.seed event-templates \
  --to production \
  --codes f29_monthly,f22_annual
```

#### 3. `sync` - Sincronizar Cualquier Tabla (Genérico)

```bash
# Sincronizar brain_contexts
python -m scripts.seed sync \
  --table brain_contexts \
  --unique-key context_id \
  --to production \
  --dry-run

# Sincronizar brain_actions específicas
python -m scripts.seed sync \
  --table brain_actions \
  --unique-key action_id \
  --to production \
  --filter action_123,action_456

# Sincronizar cualquier tabla
python -m scripts.seed sync \
  --table your_table_name \
  --unique-key your_unique_column \
  --to production \
  --dry-run
```

#### 4. `all` - Sincronizar Todo

```bash
# Dry run de todo
python -m scripts.seed all --to production --dry-run

# Sincronizar todo
python -m scripts.seed all --to production
```

### Opciones Disponibles

| Opción | Descripción | Valores | Default |
|--------|-------------|---------|---------|
| `--from` | Entorno origen | `staging`, `production` | `staging` |
| `--to` | Entorno destino | `staging`, `production` | **requerido** |
| `--dry-run` | Mostrar cambios sin aplicarlos | flag | `false` |
| `--verbose`, `-v` | Mostrar detalles de cambios | flag | `false` |
| `--codes` | Filtrar por códigos específicos | comma-separated | todos |
| `--filter` | Filtrar por valores de unique key | comma-separated | todos |
| `--table` | Nombre de tabla (comando `sync`) | string | - |
| `--unique-key` | Columna única (comando `sync`) | string | - |
| `--full-sync` | **Sincronización completa**: elimina registros en target que no existen en source, y preserva IDs. **🔒 BLOQUEADO para production como target** | flag | `false` |

## 📊 Comportamiento

### Lógica de Sincronización

**Modo Normal** (sin `--full-sync`):

Para cada registro:

1. **Crear**: Si no existe en destino (basado en `unique_key`)
2. **Actualizar**: Si existe pero:
   - `updated_at` del origen es más reciente, O
   - El contenido difiere (comparación campo por campo)
3. **Omitir**: Si existe y es idéntico

**Modo Full Sync** (con `--full-sync`):

Además de crear, actualizar y omitir:

4. **Eliminar**: Registros en target que NO existen en source
5. **Preservar IDs**: Los IDs de la fuente se mantienen en el destino

⚠️ **IMPORTANTE**: `--full-sync` está **BLOQUEADO** cuando el target es `production` para prevenir eliminaciones accidentales de datos críticos.

### Campos Sincronizados

El sistema **automáticamente detecta** todas las columnas comunes entre origen y destino.

**Campos excluidos** (auto-generados):

Modo normal:
- `id` - Se regenera en destino
- `created_at` - Se preserva del destino

Modo `--full-sync`:
- `id` - Se **PRESERVA** del origen (no se regenera)
- `created_at` - Se preserva del destino

**Todos los demás campos** se sincronizan automáticamente.

### Seguridad

- ⚠️ **Confirmación requerida** al sincronizar a producción (sin `--dry-run`)
- 🔒 **No permite** sincronizar un entorno consigo mismo
- 🛡️ **BLOQUEADO**: `--full-sync` con `production` como target está prohibido
- 📝 **Logs detallados** de cada operación
- ✅ **Validación de esquema** automática

**Regla Crítica de Seguridad**:

```
❌ NUNCA se puede eliminar registros de producción
✅ Solo se puede eliminar de staging o desarrollo
```

El sistema implementa esta regla mediante un bloqueo explícito:

```python
if full_sync and target_env == "production":
    raise ValueError("❌ SAFETY BLOCK: --full-sync is not allowed when target is 'production'")
```

## 📖 Ejemplos de Uso Común

### Workflow Recomendado para Producción

```bash
# 1. Primero SIEMPRE hacer dry-run
python -m scripts.seed notification-templates --to production --dry-run --verbose

# 2. Revisar el output cuidadosamente

# 3. Si todo se ve bien, aplicar cambios
python -m scripts.seed notification-templates --to production

# 4. Verificar en producción que todo funcionó
```

### Sincronizar Templates Nuevos Solamente

```bash
# Supongamos que creaste 2 nuevos templates en staging
python -m scripts.seed notification-templates \
  --to production \
  --codes f29_overdue_reminder,weekly_tax_summary \
  --dry-run

# Si se ve bien, aplicar
python -m scripts.seed notification-templates \
  --to production \
  --codes f29_overdue_reminder,weekly_tax_summary
```

### Sincronizar Nueva Tabla (Brain System)

```bash
# Sincronizar contextos del brain system
python -m scripts.seed sync \
  --table brain_contexts \
  --unique-key context_id \
  --to production \
  --dry-run

# Sincronizar acciones
python -m scripts.seed sync \
  --table brain_actions \
  --unique-key action_id \
  --to production \
  --dry-run
```

### Sincronizar Entre Staging y Production Bidireccionalmente

```bash
# Desde staging a production (común)
python -m scripts.seed notification-templates --from staging --to production

# Desde production a staging (rollback o testing)
python -m scripts.seed notification-templates --from production --to staging
```

### Full Sync - Sincronización Completa con Eliminación

```bash
# Escenario: Hacer que staging sea una copia EXACTA de producción
# - Elimina registros en staging que no existen en producción
# - Crea registros faltantes
# - Actualiza registros existentes
# - Preserva IDs de la fuente

# 1. SIEMPRE dry-run primero
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --full-sync \
  --dry-run \
  --verbose

# 2. Revisar output cuidadosamente (especialmente las eliminaciones)
#    ✨ Create: X records
#    🔄 Update: Y records
#    🗑️  Delete: Z records  ← ¡Verificar cuidadosamente!
#    ⏭️  Skip: W records

# 3. Si estás seguro, aplicar
python -m scripts.seed notification-templates \
  --from production \
  --to staging \
  --full-sync

# ⚠️ SEGURIDAD: Este comando fallará (bloqueado para producción)
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --full-sync
# Error: ❌ SAFETY BLOCK: --full-sync is not allowed when target is 'production'
```

### Uso con Docker

```bash
# Dry run con Docker
docker run --rm --env-file backend/.env fizko-backend seed notification-templates --to production --dry-run

# Sincronizar con Docker
docker run --rm --env-file backend/.env fizko-backend seed notification-templates --to production

# Sincronizar todo con Docker
docker run --rm --env-file backend/.env fizko-backend seed all --to production --dry-run

# Comando genérico con Docker
docker run --rm --env-file backend/.env fizko-backend seed sync \
  --table brain_contexts \
  --unique-key context_id \
  --to production \
  --dry-run
```

**⚠️ Importante con Docker:**
- Asegúrate de que tu `.env` contenga las variables de Supabase
- Usa `--rm` para eliminar el contenedor después de ejecutar
- El contenedor debe tener acceso a red para conectarse a Supabase

## 🔧 Arquitectura

### Estructura del Código

```
backend/scripts/seed/
├── __init__.py              # Documentación de módulo
├── __main__.py              # CLI entry point (Click)
├── generic.py               # GenericSupabaseSeeder (motor principal)
├── README.md                # Esta documentación
├── QUICKSTART.md            # Guía rápida
├── EXAMPLES.md              # Ejemplos detallados
└── SETUP.md                 # Configuración inicial
```

### GenericSupabaseSeeder

El corazón del sistema es la clase `GenericSupabaseSeeder` que:

1. **Auto-detecta columnas** mediante introspección de Supabase
2. **Valida esquemas** automáticamente
3. **Compara contenido** campo por campo
4. **Aplica cambios** de forma incremental (no transaccional)

**Ventajas**:
- ✅ No requiere código custom por tabla
- ✅ Validación automática de esquemas
- ✅ Fácil de extender a nuevas tablas

**Limitaciones**:
- ⚠️ No usa transacciones (ejecuta cambio por cambio)
- ⚠️ Requiere service keys de Supabase
- ⚠️ Puede ser más lento que SQL directo (llamadas HTTP)

## 🐛 Troubleshooting

### Error: "Missing Supabase config"

**Problema**: Variables de entorno faltantes.

**Solución**: Verificar `.env`:
```bash
grep -E "(STAGING_SUPABASE|PROD_SUPABASE)" backend/.env
```

Deben estar:
- `STAGING_SUPABASE_URL`
- `STAGING_SUPABASE_SERVICE_KEY`
- `PROD_SUPABASE_URL`
- `PROD_SUPABASE_SERVICE_KEY`

### Error: "Source and target cannot be the same"

**Problema**: Intentaste sincronizar un entorno consigo mismo.

**Solución**: Usar `--from` y `--to` con valores diferentes.

### Error: "Unique key 'xxx' not found"

**Problema**: La columna especificada como unique key no existe en ambos entornos.

**Solución**: Verificar esquema de la tabla y usar una columna que exista en ambos.

### Templates no se actualizan

**Problema**: El script dice "skip" pero esperabas una actualización.

**Solución**:
1. Usar `--verbose` para ver qué se compara
2. Verificar que `updated_at` en origen sea más reciente
3. Verificar que realmente hayan cambios en los campos

### Error de permisos

**Problema**: "permission denied" o similar.

**Solución**: Asegurar que estás usando **service keys**, no anon keys.

## ✅ Best Practices

1. **SIEMPRE** hacer dry-run primero antes de sincronizar a producción
2. **Usar `--codes`/`--filter`** para sincronizar cambios específicos
3. **Revisar logs** cuidadosamente en modo verbose
4. **Mantener staging actualizado** como fuente de verdad
5. **Documentar cambios** importantes en commits
6. **Probar localmente** antes de staging (si aplica)
7. **Usar service keys** seguras y rotarlas periódicamente

## 🔮 Futuras Mejoras

- [ ] Soporte para transacciones (rollback automático)
- [ ] Exportar/importar a JSON
- [ ] Validación de foreign keys
- [ ] Diff visual de cambios
- [ ] Soporte para tablas relacionadas en cascada
- [ ] CI/CD integration (GitHub Actions)
- [ ] Logs persistentes/auditables
