# Celery Infrastructure - Backend V2

Infraestructura de Celery para Backend V2, enfocada exclusivamente en tareas de integración con SII.

## 🎯 Diferencias con Backend Original

Backend V2 utiliza una arquitectura diferente:

| Aspecto | Backend Original | Backend V2 |
|---------|-----------------|------------|
| **Base de datos** | SQLAlchemy (async) | Supabase Client |
| **Acceso a datos** | Queries SQL directas | Repositorios |
| **Tareas** | Todas (SII, notificaciones, calendario) | Solo SII |
| **Colas** | high, default, low | default, low |
| **Lógica** | En tareas + services | Solo en services |

## 📁 Estructura

```
app/infrastructure/celery/
├── __init__.py           # Inicialización de Celery app
├── config.py             # Configuración (colas, routing, Beat)
├── worker.py             # Entry point para workers
├── tasks/                # Tareas organizadas por dominio
│   ├── __init__.py      # Registry de tareas
│   └── sii/             # Tareas SII
│       ├── __init__.py
│       ├── documents.py # Sincronización de documentos
│       └── forms.py     # Sincronización de F29
└── README.md            # Este archivo
```

## ⚙️ Configuración

### Variables de Entorno

Requeridas en `.env`:

```bash
# Redis (broker y result backend)
REDIS_URL=redis://localhost:6379/0

# PostgreSQL (para Beat scheduler)
DATABASE_URL=postgresql://user:pass@host:6543/db

# Supabase (para acceso a datos)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```

### Colas

Backend V2 utiliza solo 2 colas:

- **`default`** (media prioridad): Tareas generales
- **`low`** (baja prioridad): Tareas pesadas de SII (Selenium scraping)

### Routing de Tareas

Configurado en [config.py](config.py):

```python
task_routes = {
    "sii.sync_documents": {"queue": "low"},
    "sii.sync_documents_all_companies": {"queue": "low"},
    "sii.sync_f29": {"queue": "low"},
    "sii.sync_f29_all_companies": {"queue": "low"},
}
```

## 🚀 Uso

### Instalación

```bash
cd backend-v2

# Instalar dependencias (incluye Celery)
uv sync

# Verificar instalación
.venv/bin/celery --version
```

### Worker

```bash
# Worker para todas las colas
celery -A app.infrastructure.celery.worker worker --loglevel=info

# Worker para cola específica
celery -A app.infrastructure.celery.worker worker -Q low --loglevel=info

# Worker con autoreload (desarrollo)
celery -A app.infrastructure.celery.worker worker --loglevel=info --reload
```

### Beat Scheduler

```bash
# Usando script de inicio (recomendado)
./start_beat.sh

# O manualmente
celery -A app.infrastructure.celery.worker beat --loglevel=info
```

### Monitoring con Flower

```bash
# Instalar Flower (opcional)
uv pip install flower

# Iniciar Flower
celery -A app.infrastructure.celery.worker flower
# Acceder en http://localhost:5555
```

## 📋 Tareas Disponibles

### Documentos SII

#### `sii.sync_documents`

Sincroniza documentos tributarios (compras y ventas) para una empresa.

```python
from app.infrastructure.celery.tasks.sii import sync_documents

# Sincronizar último mes
result = sync_documents.delay(
    company_id="085ed9db-d666-4a98-bb05-13a79257e9c9",
    months=1,
    month_offset=0
)

# Sincronizar últimos 3 meses
result = sync_documents.delay(
    company_id="085ed9db-d666-4a98-bb05-13a79257e9c9",
    months=3,
    month_offset=0
)
```

**Parámetros:**
- `company_id` (str): UUID de la empresa
- `months` (int): Número de meses a sincronizar (1-12)
- `month_offset` (int): Offset de meses desde hoy (0=mes actual, 1=mes pasado)

**Retorna:**
```python
{
    "success": True,
    "company_id": "...",
    "compras": {"total": 10, "nuevos": 5, "actualizados": 5},
    "ventas": {"total": 8, "nuevos": 3, "actualizados": 5},
    "duration_seconds": 45.2,
    "errors": 0
}
```

#### `sii.sync_documents_all_companies`

Sincroniza documentos para todas las empresas con suscripción activa.

```python
from app.infrastructure.celery.tasks.sii import sync_documents_all_companies

result = sync_documents_all_companies.delay(months=1, month_offset=0)
```

### Formularios F29

#### `sii.sync_f29`

Sincroniza formularios F29 para una empresa.

```python
from app.infrastructure.celery.tasks.sii import sync_f29

# Sincronizar año actual
result = sync_f29.delay(
    company_id="085ed9db-d666-4a98-bb05-13a79257e9c9"
)

# Sincronizar año específico
result = sync_f29.delay(
    company_id="085ed9db-d666-4a98-bb05-13a79257e9c9",
    year="2024"
)
```

**Parámetros:**
- `company_id` (str): UUID de la empresa
- `year` (str, opcional): Año en formato YYYY (default: año actual)

**Retorna:**
```python
{
    "success": True,
    "company_id": "...",
    "year": "2024",
    "total": 12,
    "nuevos": 2,
    "actualizados": 10,
    "duration_seconds": 120.5
}
```

#### `sii.sync_f29_all_companies`

Sincroniza F29 para todas las empresas con suscripción activa.

```python
from app.infrastructure.celery.tasks.sii import sync_f29_all_companies

result = sync_f29_all_companies.delay(year="2024")
```

## 🏗️ Arquitectura

### Separación de Responsabilidades

Backend V2 sigue estrictamente el patrón de capas:

```
Celery Task (infraestructura)
    ↓ delega a
Service Layer (lógica de negocio)
    ↓ usa
Repository Layer (acceso a datos)
    ↓ usa
Supabase Client (cliente de BD)
```

### Ejemplo: Tarea Simplificada

Las tareas en Backend V2 son **extremadamente simples**:

```python
# tasks/sii/documents.py
@celery_app.task(bind=True, name="sii.sync_documents")
def sync_documents(self, company_id: str, months: int = 1):
    try:
        # 1. Obtener cliente y servicio
        supabase = get_supabase_client()
        service = SIIService(supabase)

        # 2. Delegar TODO al servicio
        result = service.sync_documents(company_id, months)

        return result
    except Exception as e:
        # 3. Solo manejo de errores y retry
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {"success": False, "error": str(e)}
```

### Ejemplo: Service con Lógica

La lógica de negocio vive en el **service layer**:

```python
# services/sii_service.py
class SIIService:
    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase

    def sync_documents(self, company_id: str, months: int):
        # 1. Validación
        company = self.supabase.companies.get_by_id(company_id)
        if not company:
            raise ValueError("Company not found")

        # 2. Lógica de negocio compleja
        with SIIClient(tax_id=rut, password=pwd) as client:
            for period in periods:
                compras = client.get_compras(periodo=period)
                for doc in compras:
                    # Guardar via repository
                    self.supabase.documents.create(doc)

        # 3. Retornar resultado
        return {"success": True, ...}
```

## 🔧 Desarrollo

### Agregar Nueva Tarea

1. **Crear el servicio** (si no existe):
```python
# app/services/nueva_feature_service.py
class NuevaFeatureService:
    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase

    def hacer_algo(self, param1: str):
        # Lógica de negocio aquí
        pass
```

2. **Crear la tarea** (simple wrapper):
```python
# app/infrastructure/celery/tasks/sii/nueva_tarea.py
@celery_app.task(bind=True, name="sii.nueva_tarea")
def nueva_tarea(self, param1: str):
    try:
        supabase = get_supabase_client()
        service = NuevaFeatureService(supabase)
        return service.hacer_algo(param1)
    except Exception as e:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {"success": False, "error": str(e)}
```

3. **Registrar en `__init__.py`**:
```python
# app/infrastructure/celery/tasks/sii/__init__.py
from .nueva_tarea import nueva_tarea

__all__ = [..., "nueva_tarea"]
```

4. **Configurar routing** (opcional):
```python
# app/infrastructure/celery/config.py
task_routes = {
    "sii.nueva_tarea": {"queue": "low"},
}
```

### Testing

```bash
# Test unitario de servicio (sin Celery)
pytest tests/services/test_sii_service.py

# Test de tarea (requiere Redis y worker)
pytest tests/infrastructure/celery/test_sii_tasks.py
```

## 📊 Monitoring

### Logs

Las tareas usan logging estructurado con emojis:

```
🚀 [CELERY TASK] Document sync started: company_id=..., months=1
📅 Syncing periods: ['202411', '202410']
📥 Processing period 202411...
   Compras: 10 documents
   Ventas: 8 documents
✅ [CELERY TASK] Document sync completed: compras=10, ventas=8
```

### Flower Dashboard

Acceder a http://localhost:5555 para ver:
- Tareas activas
- Historial de ejecuciones
- Tasas de éxito/fallo
- Tiempos de ejecución

### Database Queries

```sql
-- Ver tareas periódicas configuradas
SELECT * FROM celery_schema.celery_periodictask WHERE enabled = true;

-- Ver últimas ejecuciones
SELECT * FROM celery_schema.celery_crontabschedule;

-- Ver resultados de tareas
SELECT * FROM celery_schema.celery_taskmeta ORDER BY date_done DESC LIMIT 10;
```

## 🐛 Troubleshooting

### Worker no encuentra tareas

```bash
# Verificar que las tareas se importan correctamente
python -c "from app.infrastructure.celery.tasks.sii import sync_documents; print(sync_documents)"
```

### Beat no programa tareas

```bash
# Verificar conexión a PostgreSQL
psql $DATABASE_URL -c "SELECT * FROM celery_schema.celery_periodictask;"

# Verificar configuración de Beat
celery -A app.infrastructure.celery.worker inspect scheduled
```

### Redis connection refused

```bash
# Iniciar Redis
redis-server

# O con Docker
docker run -d -p 6379:6379 redis:latest
```

### Tareas fallan silenciosamente

```bash
# Ver logs detallados
celery -A app.infrastructure.celery.worker worker --loglevel=debug

# Ver resultado de tarea específica
celery -A app.infrastructure.celery.worker result <task-id>
```

## 📚 Referencias

- [Celery Documentation](https://docs.celeryq.dev/)
- [SQLAlchemy-Celery-Beat](https://github.com/AngelLiang/sqlalchemy-celery-beat)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Redis](https://redis.io/docs/)

## 🔗 Archivos Relacionados

- [SIIService](../../services/sii_service.py) - Service layer para SII
- [Repositories](../../repositories/) - Acceso a datos via Supabase
- [SIIClient](../../integrations/sii/client/) - Cliente RPA para SII
