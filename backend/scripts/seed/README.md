# Fizko Seed Scripts

Sistema modular para sincronizar datos de configuración entre entornos (local, staging, production).

## 🎯 Propósito

Estos scripts permiten:
- Sincronizar templates de notificaciones entre entornos
- Sincronizar templates de eventos tributarios
- Mantener consistencia de configuraciones en producción
- Realizar migraciones seguras con dry-run

## 📋 Requisitos

1. **Variables de entorno**: Configurar conexiones a bases de datos en `.env`:

```bash
# Local
DATABASE_URL=postgresql://user:pass@localhost:6543/fizko

# Staging
STAGING_DATABASE_URL=postgresql://user:pass@staging-host:5432/fizko_staging

# Production
DATABASE_URL_PRODUCTION=postgresql://user:pass@prod-host:5432/fizko_prod
```

2. **Dependencias**: El script usa las dependencias ya instaladas del proyecto (SQLAlchemy, Click).

## 🚀 Uso

### Sintaxis General

```bash
cd backend
python -m scripts.seed <command> [options]
```

### Comandos Disponibles

#### 1. `notification-templates` - Sincronizar Templates de Notificaciones

Sincroniza templates de notificaciones (F29 reminders, resúmenes diarios, etc.).

```bash
# Ver qué se sincronizaría (dry run) - RECOMENDADO SIEMPRE PRIMERO
python -m scripts.seed notification-templates --to production --dry-run

# Sincronizar todos los templates
python -m scripts.seed notification-templates --from staging --to production

# Sincronizar templates específicos
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --codes f29_reminder,daily_business_summary,calendar_event_reminder

# Modo verbose (ver detalles de cambios)
python -m scripts.seed notification-templates --to production --verbose --dry-run
```

#### 2. `event-templates` - Sincronizar Templates de Eventos

Sincroniza templates de eventos tributarios (F29, F22, boletas honorarios, etc.).

```bash
# Dry run
python -m scripts.seed event-templates --to production --dry-run

# Sincronizar todos los eventos
python -m scripts.seed event-templates --from staging --to production

# Sincronizar eventos específicos
python -m scripts.seed event-templates \
  --from staging \
  --to production \
  --codes f29_monthly,f22_annual,boletas_honorarios
```

#### 3. `all` - Sincronizar Todo

Sincroniza todos los tipos de datos soportados.

```bash
# Dry run de todo
python -m scripts.seed all --to production --dry-run

# Sincronizar todo
python -m scripts.seed all --from staging --to production
```

### Opciones Disponibles

| Opción | Descripción | Valores | Default |
|--------|-------------|---------|---------|
| `--from` | Entorno origen | `local`, `staging`, `production` | `staging` |
| `--to` | Entorno destino | `local`, `staging`, `production` | **requerido** |
| `--dry-run` | Mostrar cambios sin aplicarlos | flag | `false` |
| `--verbose`, `-v` | Mostrar detalles de cambios | flag | `false` |
| `--codes` | Filtrar por códigos específicos | comma-separated | todos |

## 📊 Comportamiento

### Lógica de Sincronización

Para cada registro:

1. **Crear**: Si no existe en destino (basado en `code`)
2. **Actualizar**: Si existe pero difiere en contenido o timestamp
3. **Omitir**: Si existe y es idéntico

### Campos Sincronizados

#### Notification Templates
- ✅ `code` (identificador único)
- ✅ `name`, `description`
- ✅ `category`, `entity_type`
- ✅ `message_template`
- ✅ `timing_config`
- ✅ `priority`, `can_repeat`, `max_repeats`
- ✅ `is_active`
- ✅ `auto_assign_to_new_companies`
- ✅ `whatsapp_template_id`
- ✅ `extra_metadata`
- ❌ `id` (regenerado por destino)
- ❌ `created_at` (preservado del destino)

#### Event Templates
- ✅ `code` (identificador único)
- ✅ `name`, `description`
- ✅ `category`, `authority`
- ✅ `is_mandatory`
- ✅ `default_recurrence`
- ✅ `metadata`
- ❌ `id` (regenerado por destino)
- ❌ `created_at` (preservado del destino)

### Seguridad

- ⚠️ **Confirmación requerida** al sincronizar a producción (sin `--dry-run`)
- 🔒 **No permite** sincronizar un entorno consigo mismo
- 💾 **Transaccional**: Todo se commitea al final o rollback en caso de error
- 📝 **Logs detallados** de cada operación

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
# Supongamos que creaste 2 nuevos templates en staging:
# - f29_overdue_reminder
# - weekly_tax_summary

python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --codes f29_overdue_reminder,weekly_tax_summary \
  --dry-run

# Si se ve bien:
python -m scripts.seed notification-templates \
  --from staging \
  --to production \
  --codes f29_overdue_reminder,weekly_tax_summary
```

### Actualizar Template Modificado

```bash
# Si modificaste el template 'daily_business_summary' en staging
python -m scripts.seed notification-templates \
  --to production \
  --codes daily_business_summary \
  --verbose --dry-run

# Verás qué campos cambiaron exactamente
# Si está bien, aplicar:
python -m scripts.seed notification-templates \
  --to production \
  --codes daily_business_summary
```

### Sincronizar Desde Local a Staging (Testing)

```bash
# Útil para probar templates locales en staging primero
python -m scripts.seed notification-templates \
  --from local \
  --to staging \
  --codes my_new_template
```

## 🔧 Crear Nuevos Seeders

Para agregar soporte a nuevas tablas:

### 1. Crear archivo del seeder

```python
# backend/scripts/seed/your_table.py
from .base import BaseSeeder

class YourTableSeeder(BaseSeeder):
    def get_entity_name(self) -> str:
        return "your_table"

    def get_unique_key(self, record) -> str:
        return record["code"]  # o el campo único

    async def fetch_source_data(self, session):
        # SQL query para obtener datos
        pass

    async def create_record(self, session, record):
        # INSERT query
        pass

    async def update_record(self, session, existing_id, source_record):
        # UPDATE query
        pass
```

### 2. Agregar comando CLI

```python
# En __main__.py, agregar:

@cli.command()
@click.option("--from", "source_env", ...)
@click.option("--to", "target_env", ...)
# ... más opciones
def your_table(source_env, target_env, ...):
    """Sync your_table between environments."""
    seeder = YourTableSeeder(...)
    asyncio.run(seeder.sync())
```

### 3. Agregar al comando `all`

En la función `all()`, agregar:

```python
seeder = YourTableSeeder(...)
stats = asyncio.run(seeder.sync())
```

## 🐛 Troubleshooting

### Error: "Environment variable not set"

**Problema**: Variables de entorno faltantes.

**Solución**: Verificar que `.env` tenga las variables necesarias:
```bash
grep -E "(DATABASE_URL|STAGING_DATABASE_URL|DATABASE_URL_PRODUCTION)" backend/.env
```

### Error: "Source and target cannot be the same"

**Problema**: Intentaste sincronizar un entorno consigo mismo.

**Solución**: Usar `--from` y `--to` con valores diferentes.

### Error: Connection timeout

**Problema**: No se puede conectar a la base de datos.

**Solución**:
1. Verificar que el host sea accesible
2. Verificar credenciales
3. Verificar firewall/security groups

### Templates no se actualizan

**Problema**: El script dice "skip" pero esperabas una actualización.

**Solución**:
1. Usar `--verbose` para ver qué se compara
2. Verificar que `updated_at` en origen sea más reciente
3. Verificar que realmente hayan cambios en los campos comparados

## 📚 Estructura del Código

```
backend/scripts/seed/
├── __init__.py              # Documentación de módulo
├── __main__.py              # CLI entry point (Click)
├── base.py                  # BaseSeeder, DatabaseConnection
├── notification_templates.py # Seeder para notification_templates
├── event_templates.py       # Seeder para event_templates
└── README.md               # Esta documentación
```

## ✅ Best Practices

1. **SIEMPRE** hacer dry-run primero antes de sincronizar a producción
2. **Usar `--codes`** para sincronizar cambios específicos en lugar de todo
3. **Revisar logs** cuidadosamente en modo verbose
4. **Mantener staging actualizado** como fuente de verdad antes de prod
5. **Documentar cambios** importantes en commits
6. **Probar localmente** antes de staging
7. **Hacer backup** de producción antes de cambios grandes

## 🔮 Futuras Mejoras

- [ ] Soporte para rollback automático
- [ ] Exportar/importar a JSON
- [ ] Validación de foreign keys
- [ ] Diff visual de cambios
- [ ] Soporte para tablas relacionadas (e.g., sincronizar notification_event_triggers junto con templates)
- [ ] CI/CD integration (GitHub Actions)
