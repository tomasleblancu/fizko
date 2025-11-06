# Seed Scripts Architecture

## Overview

Sistema modular para sincronizar datos de configuración entre entornos (local, staging, production).

## Design Principles

1. **Modularidad**: Cada tabla tiene su propio seeder independiente
2. **Seguridad**: Dry-run por defecto, confirmación para producción
3. **Transparencia**: Logs detallados de todas las operaciones
4. **Idempotencia**: Puede ejecutarse múltiples veces sin duplicar datos
5. **Flexibilidad**: Filtros por códigos específicos

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                     __main__.py (Click)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ notification │  │    event     │  │     all      │      │
│  │  -templates  │  │  -templates  │  │   command    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Seeder Layer                            │
│                      base.py                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    BaseSeeder                        │   │
│  │  - sync()           : Orchestrates sync process      │   │
│  │  - should_update()  : Determines update necessity    │   │
│  │  - filter_records() : Filters by codes               │   │
│  └──────────────────────────────────────────────────────┘   │
│           ▲                              ▲                   │
│           │                              │                   │
│  ┌────────┴────────────┐    ┌───────────┴──────────┐       │
│  │ NotificationTemplate │    │   EventTemplate      │       │
│  │      Seeder          │    │      Seeder          │       │
│  │ - get_entity_name()  │    │ - get_entity_name()  │       │
│  │ - fetch_source_data()│    │ - fetch_source_data()│       │
│  │ - fetch_target_data()│    │ - fetch_target_data()│       │
│  │ - get_unique_key()   │    │ - get_unique_key()   │       │
│  │ - create_record()    │    │ - create_record()    │       │
│  │ - update_record()    │    │ - update_record()    │       │
│  │ - should_update()    │    │ - should_update()    │       │
│  └──────────────────────┘    └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer                             │
│                   base.py                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              DatabaseConnection                      │   │
│  │  - get_connection_string() : Get DB URL by env       │   │
│  │  - create_session()        : Create AsyncSession     │   │
│  └──────────────────────────────────────────────────────┘   │
│           │                              │                   │
│           ▼                              ▼                   │
│  ┌────────────────┐           ┌────────────────┐           │
│  │ Source DB      │           │ Target DB      │           │
│  │ (Staging)      │           │ (Production)   │           │
│  └────────────────┘           └────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Class Hierarchy

```
BaseSeeder (ABC)
    ├── Abstract Methods:
    │   ├── get_entity_name() -> str
    │   ├── fetch_source_data(session) -> List[Dict]
    │   ├── fetch_target_data(session) -> List[Dict]
    │   ├── get_unique_key(record) -> str
    │   ├── create_record(session, record) -> None
    │   └── update_record(session, id, record) -> None
    │
    ├── Concrete Methods:
    │   ├── sync(filter_keys) -> Dict[str, int]
    │   ├── should_update(source, target) -> bool
    │   └── filter_records(records, keys) -> List[Dict]
    │
    └── Implementations:
        ├── NotificationTemplateSeeder
        └── EventTemplateSeeder
```

## Data Flow

```
1. CLI Invocation
   python -m scripts.seed notification-templates --to production --dry-run
                                    │
                                    ▼
2. Argument Parsing (Click)
   source_env = "staging"
   target_env = "production"
   dry_run = True
   filter_keys = None
                                    │
                                    ▼
3. Seeder Initialization
   seeder = NotificationTemplateSeeder(
       source_env="staging",
       target_env="production",
       dry_run=True,
       verbose=False
   )
                                    │
                                    ▼
4. Sync Process
   ┌─────────────────────────────────────┐
   │ 4.1 Connect to Source DB            │
   │     source_session = create_session │
   │                                     │
   │ 4.2 Fetch Source Data               │
   │     source_records = fetch_source() │
   │                                     │
   │ 4.3 Apply Filters                   │
   │     if filter_keys:                 │
   │         filter_records()            │
   └─────────────────────────────────────┘
                                    │
                                    ▼
   ┌─────────────────────────────────────┐
   │ 4.4 Connect to Target DB            │
   │     target_session = create_session │
   │                                     │
   │ 4.5 Fetch Target Data               │
   │     target_records = fetch_target() │
   │                                     │
   │ 4.6 Build Lookup Map                │
   │     target_map = {key: record}      │
   └─────────────────────────────────────┘
                                    │
                                    ▼
   ┌─────────────────────────────────────┐
   │ 4.7 Determine Actions               │
   │     for source_record:              │
   │       if not in target:             │
   │           → to_create               │
   │       elif should_update():         │
   │           → to_update               │
   │       else:                         │
   │           → to_skip                 │
   └─────────────────────────────────────┘
                                    │
                                    ▼
   ┌─────────────────────────────────────┐
   │ 4.8 Display Plan                    │
   │     ✨ Create: N records            │
   │     🔄 Update: N records            │
   │     ⏭️  Skip: N records             │
   └─────────────────────────────────────┘
                                    │
                                    ▼
   ┌─────────────────────────────────────┐
   │ 4.9 Execute Changes                 │
   │     if not dry_run:                 │
   │         for record in to_create:    │
   │             create_record()         │
   │         for record in to_update:    │
   │             update_record()         │
   │         commit()                    │
   └─────────────────────────────────────┘
                                    │
                                    ▼
5. Return Statistics
   {
       "to_create": 2,
       "to_update": 5,
       "to_skip": 10,
       "errors": 0
   }
```

## Comparison Logic

### How should_update() Works

```python
def should_update(source_record, target_record) -> bool:
    # Step 1: Compare timestamps
    if source_record.updated_at > target_record.updated_at:
        return True  # Source is newer

    # Step 2: Compare critical fields
    fields_to_compare = [
        "name",
        "description",
        "message_template",
        "timing_config",
        # ... more fields
    ]

    for field in fields_to_compare:
        if source_record[field] != target_record[field]:
            return True  # Content differs

    return False  # No changes needed
```

### Update Decision Tree

```
┌─────────────────────────────┐
│ Record exists in target?    │
└─────────┬───────────────────┘
          │
    ┌─────┴─────┐
    NO          YES
    │           │
    ▼           ▼
┌───────┐   ┌───────────────────────────┐
│CREATE │   │ Compare updated_at        │
└───────┘   └───────┬───────────────────┘
                    │
              ┌─────┴─────┐
              │           │
        source newer   source older/same
              │           │
              ▼           ▼
          ┌───────┐   ┌───────────────────┐
          │UPDATE │   │ Compare fields    │
          └───────┘   └───────┬───────────┘
                              │
                        ┌─────┴─────┐
                        │           │
                  fields differ  fields same
                        │           │
                        ▼           ▼
                    ┌───────┐   ┌──────┐
                    │UPDATE │   │ SKIP │
                    └───────┘   └──────┘
```

## Database Connections

### Environment Variables Mapping

```
DatabaseConnection.ENVIRONMENTS = {
    "local":      "DATABASE_URL",
    "staging":    "STAGING_DATABASE_URL",
    "production": "DATABASE_URL_PRODUCTION"
}
```

### Connection String Normalization

```python
# Input variations:
postgres://user:pass@host:port/db
postgresql://user:pass@host:port/db

# Output (normalized):
postgresql+asyncpg://user:pass@host:port/db
```

## Error Handling

### Transaction Safety

```
BEGIN TRANSACTION
    ├── Create Record 1  ✅
    ├── Create Record 2  ✅
    ├── Update Record 3  ❌ ERROR
    └── ROLLBACK         ← All changes reverted
```

### Error Statistics

```python
stats = {
    "to_create": 10,
    "to_update": 5,
    "to_skip": 20,
    "errors": 1  # Non-zero = exit code 1
}
```

## Security Features

1. **Environment Isolation**
   - Prevents syncing env to itself
   - Requires explicit target specification

2. **Production Safeguards**
   - Interactive confirmation for production
   - Dry-run mode as safety net
   - No destructive operations (only create/update)

3. **Audit Trail**
   - Detailed logging of all operations
   - Verbose mode for debugging
   - Statistics summary

## Performance Considerations

1. **Single Connection per Environment**
   - One session for source (read-only)
   - One session for target (read-write)

2. **Batch Operations**
   - All reads happen first
   - All writes happen in single transaction
   - Commit once at the end

3. **Memory Efficiency**
   - Records loaded as dictionaries (not ORM objects)
   - Lookup maps for O(1) comparison

## Extension Points

### Adding a New Seeder

```python
# 1. Create seeder class
class MyTableSeeder(BaseSeeder):
    def get_entity_name(self) -> str:
        return "my_table"

    # Implement other abstract methods...

# 2. Add CLI command
@cli.command()
def my_table(...):
    seeder = MyTableSeeder(...)
    asyncio.run(seeder.sync())

# 3. Add to 'all' command
# In all() function:
seeder = MyTableSeeder(...)
asyncio.run(seeder.sync())
```

### Custom Comparison Logic

Override `should_update()`:

```python
class CustomSeeder(BaseSeeder):
    def should_update(self, source, target) -> bool:
        # Custom logic
        if source["priority"] != target["priority"]:
            return True

        # Fall back to default
        return super().should_update(source, target)
```

## Testing Strategy

### Manual Testing

```bash
# 1. Test with dry-run
python -m scripts.seed <command> --to local --dry-run

# 2. Test with verbose
python -m scripts.seed <command> --to local --verbose --dry-run

# 3. Test live to local
python -m scripts.seed <command> --to local

# 4. Verify results
psql -d fizko_local -c "SELECT * FROM notification_templates;"
```

### Integration Testing (Future)

```python
# tests/test_seed_scripts.py
async def test_notification_template_sync():
    # Setup test databases
    # Run sync
    # Assert records created/updated
    # Cleanup
```

## Future Enhancements

1. **Rollback Support**
   - Save snapshots before sync
   - Ability to rollback failed syncs

2. **Diff Viewer**
   - Visual diff of changes
   - JSON/YAML export

3. **Dependency Resolution**
   - Sync related tables together
   - Handle foreign key constraints

4. **CI/CD Integration**
   - GitHub Actions workflow
   - Automated staging → prod sync

5. **Conflict Resolution**
   - 3-way merge for conflicts
   - Manual resolution UI

6. **Performance Optimization**
   - Parallel record processing
   - Incremental syncs
   - Change tracking
