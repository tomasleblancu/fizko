# F29 Sync Refactoring: Guardado Incremental Simplificado

## Resumen

Refactorización del proceso de sincronización de formularios F29 para simplificar el guardado incremental usando Celery tasks en lugar de queues + async workers.

## Problema Original

El guardado incremental usaba una arquitectura compleja:

```
Scraper Selenium (sync) → Queue → Async Worker → Database
```

**Complejidad:**
- Cola thread-safe manual (`Queue`)
- Worker async que consume de la cola
- Coordinación entre threads sync/async
- Difícil de debuggear
- Manejo manual de errores y reintentos

## Nueva Solución

Delegamos el guardado a Celery tasks:

```
Scraper Selenium (sync) → Celery Task → Database
```

**Ventajas:**
- ✅ Más simple: menos código, menos threads
- ✅ Celery maneja reintentos automáticamente
- ✅ Monitoring en Flower (Celery UI)
- ✅ Guardado paralelo sin complejidad manual
- ✅ Idempotente: safe para reintentar

## Cambios Implementados

### 1. Nueva Tarea Celery: `save_single_f29`

**Archivo:** `backend/app/infrastructure/celery/tasks/sii/forms.py`

```python
@celery_app.task(
    bind=True,
    name="sii.save_single_f29",
    max_retries=3,
    default_retry_delay=5,
)
def save_single_f29(
    self,
    company_id: str,
    formulario: dict,
    session_id: str = None
) -> Dict[str, Any]:
    """
    Guarda un solo formulario F29 en la DB.

    - Llamado por cada formulario extraído durante sync
    - Dispara descarga de PDF si tiene id_interno_sii
    - Reintentos automáticos vía Celery
    """
```

**Responsabilidades:**
1. Guardar formulario en DB vía `SIIService.save_f29_downloads()`
2. Disparar tarea `download_single_f29_pdf` si tiene `id_interno_sii`
3. Reintentar automáticamente en errores de DB
4. Logging detallado de progreso

### 2. Refactorización de `FormService.extract_f29_lista()`

**Archivo:** `backend/app/services/sii/form_service.py`

**Antes:**
```python
# Cola + worker async complejo
formularios_queue = Queue()

async def save_worker():
    while True:
        formulario = formularios_queue.get()
        await save_f29_downloads(...)

def sync_save_callback(formulario):
    formularios_queue.put(formulario)

# Iniciar worker
save_task = asyncio.create_task(save_worker())

# Scraper con callback
client.get_f29_lista(save_callback=sync_save_callback)

# Enviar sentinel y esperar
formularios_queue.put(None)
await save_task
```

**Después:**
```python
# Callback simple que usa Celery
def celery_save_callback(formulario):
    from app.infrastructure.celery.tasks.sii.forms import save_single_f29

    save_single_f29.apply_async(
        args=[str(company_id), formulario, str(session_id)],
        countdown=0
    )

# Scraper con callback
result = client.get_f29_lista(
    anio=anio,
    save_callback=celery_save_callback
)
```

**Reducción:** ~100 líneas → ~20 líneas

### 3. Export de Nueva Tarea

**Archivo:** `backend/app/infrastructure/celery/tasks/sii/__init__.py`

```python
from .forms import (
    sync_f29,
    sync_f29_all_companies,
    save_single_f29,  # ✅ Nueva tarea
    download_single_f29_pdf,
    sync_f29_pdfs_missing,
    sync_f29_pdfs_missing_all_companies,
)
```

## Flujo de Ejecución

### 1. Usuario Dispara Sync

```bash
# Via endpoint HTTP
POST /api/sii/sync/f29/2024?session_id=abc-123

# Via Celery task directo
sync_f29.delay(session_id="abc-123", year=2024)
```

### 2. Extracción con Selenium

```python
# form_service.py
async def extract_f29_lista(session_id, anio, company_id):
    # Scraper ejecuta en thread separado
    formularios = await asyncio.to_thread(_run_extraction)

    # Dentro del scraper (sync):
    for formulario in scrape_sii_table():
        codInt = extract_codint_from_modal(formulario)
        formulario['id_interno_sii'] = codInt

        # 📤 Dispara Celery task
        celery_save_callback(formulario)
```

### 3. Guardado via Celery

```python
# Celery worker ejecuta:
@celery_app.task(name="sii.save_single_f29")
def save_single_f29(company_id, formulario, session_id):
    # 1. Guardar en DB
    saved = await service.save_f29_downloads([formulario])

    # 2. Si tiene id_interno_sii, disparar PDF download
    if formulario.get('id_interno_sii'):
        download_single_f29_pdf.apply_async(
            args=[download_id, session_id],
            countdown=2
        )
```

### 4. Descarga de PDF (Paralelo)

```python
@celery_app.task(name="sii.download_single_f29_pdf")
def download_single_f29_pdf(download_id, session_id):
    # Descarga PDF desde SII con Selenium
    pdf_bytes = await client.get_f29_compacto(folio, id_interno)

    # Guarda en Supabase Storage
    storage.upload_pdf(company_id, year, period, folio, pdf_bytes)

    # Extrae datos estructurados del PDF
    extracted_data = extract_f29_data_from_pdf(pdf_bytes)
    download.extra_data = {'f29_data': extracted_data}
```

## Manejo de Errores

### Errores de Guardado

Si `save_single_f29` falla:
1. Celery reintenta automáticamente (3 veces, delay 5s)
2. Si es error de DB/conexión, usa `self.retry(exc=e)`
3. Si falla definitivamente, queda registrado en Redis
4. Visible en Flower para debugging

### Errores de Scraping

Si el scraper falla a mitad:
- Los formularios ya guardados permanecen en DB ✅
- Los formularios no procesados se pierden ⚠️
- Solución: Re-ejecutar `sync_f29` (detecta duplicados por folio)

### Errores de PDF Download

Si falla descarga de PDF:
- El formulario ya está guardado con metadata ✅
- El PDF se puede descargar después con:
  - `sync_f29_pdfs_missing.delay(session_id, company_id)`
  - Endpoint: `POST /api/sii/sync/f29/download-pdfs`

## Monitoreo

### Flower (Celery UI)

```bash
# Iniciar Flower
celery -A app.infrastructure.celery flower --port=5555

# Ver en navegador
open http://localhost:5555
```

**Métricas disponibles:**
- Tasks activas, exitosas, fallidas
- Tiempo promedio de ejecución
- Workers disponibles
- Errores con stack traces

### Logs

```python
# Extracción
logger.info(f"📤 Encolando guardado de F29 {folio} via Celery")

# Guardado
logger.info(f"💾 Saving F29 form: folio={folio}, period={period}")
logger.info(f"✅ F29 saved: folio={folio}, id={download_id}")

# PDF
logger.info(f"📥 PDF download queued for folio {folio}")
```

## Testing

### Test Manual

```python
# 1. Disparar sync
from app.infrastructure.celery.tasks.sii.forms import sync_f29

result = sync_f29.delay(
    session_id="your-session-id",
    year=2024,
    company_id="your-company-id"
)

# 2. Ver resultado
print(result.get())  # Espera a que termine
```

### Test Individual

```python
# Guardar un solo formulario
from app.infrastructure.celery.tasks.sii.forms import save_single_f29

formulario = {
    "folio": "7904207766",
    "period": "2024-01",
    "contributor": "77794858-K",
    "submission_date": "09/05/2024",
    "status": "Vigente",
    "amount": 42443,
    "id_interno_sii": "775148628"
}

result = save_single_f29.delay(
    company_id="your-company-id",
    formulario=formulario,
    session_id="your-session-id"
)

print(result.get())
```

## Comparación de Performance

### Antes (Queue + Worker)

```
Extracción:  2-3 min (12 formularios)
Guardado:    Paralelo con extracción ✅
PDF:         Paralelo con guardado ✅

Complejidad: Alta (3 threads diferentes)
Debugging:   Difícil (logs mezclados)
```

### Después (Celery)

```
Extracción:  2-3 min (12 formularios)
Guardado:    Paralelo via Celery ✅
PDF:         Paralelo via Celery ✅

Complejidad: Baja (Celery maneja todo)
Debugging:   Fácil (Flower UI + logs claros)
```

**Performance similar, código mucho más simple.**

## Rollback Plan

Si hay problemas, revertir a la versión anterior:

```bash
git revert <commit-hash>
```

La lógica anterior sigue funcional, solo cambió la implementación del callback.

## Próximos Pasos

1. ✅ Implementado: Nueva tarea `save_single_f29`
2. ✅ Implementado: Refactorización de `extract_f29_lista`
3. ⏳ Pendiente: Testing en staging
4. ⏳ Pendiente: Monitoreo en producción con Flower
5. ⏳ Pendiente: Documentar patrones de error comunes

## Referencias

- Código anterior: Commit antes de refactorización
- Celery docs: https://docs.celeryq.dev/
- Flower docs: https://flower.readthedocs.io/
