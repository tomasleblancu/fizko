# Sincronización Paralela de Documentos Tributarios

## Resumen

Se implementó un sistema de sincronización paralela para documentos tributarios que permite sincronizar los últimos 3 meses en workers independientes, mejorando el rendimiento y distribuyendo la carga.

## Problema Anterior

Antes, cuando se incorporaba una empresa nueva, se disparaba una sola tarea Celery que sincronizaba los 3 meses secuencialmente:

```python
# Sistema anterior
sync_documents.delay(
    company_id=str(company_id),
    months=3  # Sincroniza 3 meses en un solo worker
)
```

**Desventajas:**
- Un solo worker procesa los 3 meses secuencialmente
- Tiempo total: ~3x el tiempo de un mes
- Si falla un mes, puede afectar a los demás
- No hay priorización (mes más reciente es tan importante como meses antiguos)

## Solución Implementada

Ahora se disparan **3 tareas independientes**, cada una sincronizando un mes específico:

```python
# Mes más reciente (offset=0) - inmediato
sync_documents.delay(
    company_id=str(company_id),
    months=1,
    month_offset=0
)

# Mes -1 (offset=1) - delay de 5 minutos
sync_documents.apply_async(
    kwargs={
        "company_id": str(company_id),
        "months": 1,
        "month_offset": 1
    },
    countdown=300
)

# Mes -2 (offset=2) - delay de 5 minutos
sync_documents.apply_async(
    kwargs={
        "company_id": str(company_id),
        "months": 1,
        "month_offset": 2
    },
    countdown=300
)
```

### Parámetro `month_offset`

El nuevo parámetro `month_offset` permite especificar cuántos meses saltar desde el mes actual:

- `offset=0`: Mes actual (noviembre 2025 → `202511`)
- `offset=1`: Mes pasado (octubre 2025 → `202510`)
- `offset=2`: Hace 2 meses (septiembre 2025 → `202509`)

## Ventajas

1. **Paralelización**: Los 3 meses corren en workers distintos simultáneamente
2. **Priorización**: El mes más reciente se ejecuta inmediatamente (más importante)
3. **Distribución de carga**: Los meses antiguos se retrasan 5 minutos para no saturar el SII
4. **Independencia**: Si un mes falla, los otros continúan sin problemas
5. **Tiempo total reducido**: ~N/3 segundos vs ~N segundos (teórico)

## Cambios Implementados

### 1. Tarea Celery: `sync_documents`
**Archivo**: [`backend/app/infrastructure/celery/tasks/sii/documents.py`](../app/infrastructure/celery/tasks/sii/documents.py)

Agregado parámetro `month_offset`:

```python
def sync_documents(
    self,
    session_id: str = None,
    months: int = 1,
    company_id: str = None,
    month_offset: int = 0,  # ← NUEVO
) -> Dict[str, Any]:
```

### 2. Servicio: `SIISyncService.sync_last_n_months`
**Archivo**: [`backend/app/services/sii/sync_service/__init__.py`](../app/services/sii/sync_service/__init__.py)

Agregado parámetro `month_offset`:

```python
async def sync_last_n_months(
    self,
    session_id: UUID,
    months: int = 3,
    month_offset: int = 0  # ← NUEVO
) -> Dict[str, Any]:
```

### 3. Cálculo de períodos: `_calculate_periods`
**Archivo**: [`backend/app/services/sii/sync_service/__init__.py`](../app/services/sii/sync_service/__init__.py)

Modificado para soportar offset:

```python
def _calculate_periods(self, months: int, month_offset: int = 0) -> List[str]:
    """
    Calcula los períodos en formato YYYYMM

    Example:
        Si hoy es 2024-03-15:
        - months=3, offset=0: ['202403', '202402', '202401']
        - months=1, offset=0: ['202403']
        - months=1, offset=1: ['202402']
        - months=1, offset=2: ['202401']
    """
    periods = []
    now = datetime.now()

    for i in range(months):
        # Retroceder (offset + i) meses desde ahora
        target_date = now - timedelta(days=30 * (month_offset + i))
        period = target_date.strftime("%Y%m")

        if period not in periods:
            periods.append(period)

    return periods
```

### 4. Disparador: `trigger_sync_tasks`
**Archivo**: [`backend/app/services/sii/auth_service/events.py`](../app/services/sii/auth_service/events.py)

Modificado para usar 3 tareas paralelas con offsets:

```python
# Mes más reciente (offset=0) - inmediato
sync_documents.delay(
    company_id=str(company_id),
    months=1,
    month_offset=0
)

# Mes -1 (offset=1) - delay de 5 minutos
sync_documents.apply_async(
    kwargs={"company_id": str(company_id), "months": 1, "month_offset": 1},
    countdown=300
)

# Mes -2 (offset=2) - delay de 5 minutos
sync_documents.apply_async(
    kwargs={"company_id": str(company_id), "months": 1, "month_offset": 2},
    countdown=300
)
```

## Compatibilidad hacia atrás

La implementación es **100% compatible** con código existente:

- El parámetro `month_offset` tiene valor por defecto `0`
- Llamados antiguos como `sync_documents(company_id=X, months=3)` siguen funcionando
- El comportamiento por defecto no cambia

## Ejemplo de uso

### Sincronización paralela (nuevo)

```python
from app.infrastructure.celery.tasks.sii.documents import sync_documents

# Sincronizar noviembre 2025 inmediatamente
sync_documents.delay(company_id="uuid", months=1, month_offset=0)

# Sincronizar octubre 2025 con delay
sync_documents.apply_async(
    kwargs={"company_id": "uuid", "months": 1, "month_offset": 1},
    countdown=300
)
```

### Sincronización tradicional (compatible)

```python
# Sigue funcionando igual que antes
sync_documents.delay(company_id="uuid", months=3)
```

## Logs esperados

Cuando se disparan las tareas, los logs muestran:

```
[Events] sync_documents task triggered (offset=0, most recent month) for company XXX - immediate execution
[Events] sync_documents task triggered (offset=1) for company XXX - delayed 5 minutes
[Events] sync_documents task triggered (offset=2) for company XXX - delayed 5 minutes

🚀 [CELERY TASK] Document sync started: session_id=XXX, company_id=XXX, months=1, offset=0
🚀 [CELERY TASK] Document sync started: session_id=XXX, company_id=XXX, months=1, offset=1
🚀 [CELERY TASK] Document sync started: session_id=XXX, company_id=XXX, months=1, offset=2
```

## Testing

Para probar manualmente:

```python
from app.services.sii.sync_service import SIISyncService

# Simular el cálculo de períodos
service = SIISyncService(db)

# Mes actual
service._calculate_periods(months=1, month_offset=0)  # ['202511']

# Mes pasado
service._calculate_periods(months=1, month_offset=1)  # ['202510']

# Hace 2 meses
service._calculate_periods(months=1, month_offset=2)  # ['202509']
```

## Consideraciones futuras

1. **Monitoring**: Agregar métricas para trackear el tiempo de sincronización por mes
2. **Retry logic**: Considerar retry automático para meses que fallen
3. **Dynamic delay**: Ajustar el delay de 5 minutos basado en carga del sistema
4. **Progressive rollout**: Considerar sincronizar solo 1 mes inmediatamente y los demás después

## Referencias

- Task Celery: [backend/app/infrastructure/celery/tasks/sii/documents.py](../app/infrastructure/celery/tasks/sii/documents.py)
- Sync Service: [backend/app/services/sii/sync_service/__init__.py](../app/services/sii/sync_service/__init__.py)
- Event Triggers: [backend/app/services/sii/auth_service/events.py](../app/services/sii/auth_service/events.py)
