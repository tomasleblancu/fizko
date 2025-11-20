# Celery Tasks API

API REST para gestionar tareas Celery en Backend V2. Permite lanzar tareas en background y consultar su estado.

## Endpoints Disponibles

### 1. Listar Tareas Disponibles

```http
GET /api/celery/tasks
```

Lista todas las tareas Celery disponibles con sus descripciones y parámetros.

**Respuesta:**
```json
[
  {
    "task_type": "sii.sync_documents",
    "name": "sii.sync_documents",
    "description": "Sync tax documents (purchases, sales, honorarios) for a single company",
    "parameters": {
      "company_id": {
        "type": "string",
        "required": true,
        "description": "Company UUID"
      },
      "months": {
        "type": "integer",
        "required": false,
        "default": 1,
        "min": 1,
        "max": 12
      },
      "month_offset": {
        "type": "integer",
        "required": false,
        "default": 0,
        "min": 0
      }
    }
  }
]
```

### 2. Lanzar una Tarea

```http
POST /api/celery/tasks/launch
Content-Type: application/json
```

Lanza una tarea Celery y retorna su task ID para seguimiento.

**Request Body:**
```json
{
  "task_type": "sii.sync_documents",
  "params": {
    "company_id": "123e4567-e89b-12d3-a456-426614174000",
    "months": 3,
    "month_offset": 0
  }
}
```

**Respuesta:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_type": "sii.sync_documents",
  "status": "PENDING",
  "message": "Task sii.sync_documents launched successfully"
}
```

### 3. Consultar Estado de Tarea

```http
GET /api/celery/tasks/{task_id}
```

Consulta el estado actual de una tarea por su ID.

**Respuesta (en progreso):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "STARTED",
  "result": null,
  "error": null,
  "traceback": null,
  "meta": {
    "info": "Task is running"
  }
}
```

**Respuesta (completada exitosamente):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "result": {
    "success": true,
    "compras": {
      "total": 150,
      "period": "202501"
    },
    "ventas": {
      "total": 89,
      "period": "202501"
    },
    "honorarios": {
      "total": 12
    }
  },
  "error": null,
  "traceback": null,
  "meta": null
}
```

**Respuesta (error):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "FAILURE",
  "result": null,
  "error": "Company not found",
  "traceback": "Traceback (most recent call last):\n  File ...",
  "meta": null
}
```

### 4. Revocar/Cancelar una Tarea

```http
DELETE /api/celery/tasks/{task_id}?terminate=false
```

Cancela una tarea que está pendiente o en ejecución.

**Query Parameters:**
- `terminate` (boolean, default: false): Si es `true`, termina forzosamente la tarea si está en ejecución.

**Respuesta:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "revoked",
  "terminate": false,
  "message": "Task 550e8400-e29b-41d4-a716-446655440000 has been revoked"
}
```

### 5. Estadísticas de Celery

```http
GET /api/celery/stats
```

Obtiene estadísticas de workers y colas de Celery.

**Respuesta:**
```json
{
  "active_tasks": {
    "celery@worker1": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "sii.sync_documents",
        "args": [],
        "kwargs": {
          "company_id": "123e4567-e89b-12d3-a456-426614174000"
        }
      }
    ]
  },
  "scheduled_tasks": {},
  "registered_tasks": [
    "sii.sync_documents",
    "sii.sync_documents_all_companies",
    "sii.sync_f29",
    "sii.sync_f29_all_companies"
  ],
  "worker_stats": {
    "celery@worker1": {
      "total": 156,
      "pool": {
        "max-concurrency": 4,
        "processes": [12345, 12346, 12347, 12348]
      }
    }
  }
}
```

## Tareas Disponibles

### 1. Sincronizar Documentos (Una Empresa)

**Task Type:** `sii.sync_documents`

Sincroniza documentos tributarios (compras, ventas, boletas honorarios) para una empresa específica.

**Parámetros:**
- `company_id` (string, requerido): UUID de la empresa
- `months` (int, opcional, default: 1): Número de meses a sincronizar (1-12)
- `month_offset` (int, opcional, default: 0): Offset desde el mes actual (0=actual, 1=mes pasado)

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/api/celery/tasks/launch \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sii.sync_documents",
    "params": {
      "company_id": "123e4567-e89b-12d3-a456-426614174000",
      "months": 3,
      "month_offset": 0
    }
  }'
```

### 2. Sincronizar Documentos (Todas las Empresas)

**Task Type:** `sii.sync_documents_all_companies`

Sincroniza documentos para TODAS las empresas con suscripciones activas.

**Parámetros:**
- `months` (int, opcional, default: 1): Número de meses a sincronizar
- `month_offset` (int, opcional, default: 0): Offset desde el mes actual

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/api/celery/tasks/launch \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sii.sync_documents_all_companies",
    "params": {
      "months": 1,
      "month_offset": 1
    }
  }'
```

### 3. Sincronizar F29 (Una Empresa)

**Task Type:** `sii.sync_f29`

Sincroniza formularios F29 para una empresa específica.

**Parámetros:**
- `company_id` (string, requerido): UUID de la empresa
- `year` (string, opcional, default: año actual): Año a sincronizar en formato YYYY

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/api/celery/tasks/launch \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sii.sync_f29",
    "params": {
      "company_id": "123e4567-e89b-12d3-a456-426614174000",
      "year": "2025"
    }
  }'
```

**Nota:** Si no se especifica `year`, se usa el año actual.

### 4. Sincronizar F29 (Todas las Empresas)

**Task Type:** `sii.sync_f29_all_companies`

Sincroniza formularios F29 para TODAS las empresas.

**Parámetros:**
- `year` (string, opcional, default: año actual): Año a sincronizar en formato YYYY

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/api/celery/tasks/launch \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sii.sync_f29_all_companies",
    "params": {
      "year": "2025"
    }
  }'
```

## Estados de Tarea

Las tareas pueden estar en los siguientes estados:

- **PENDING**: Tarea esperando ser ejecutada (o no existe)
- **STARTED**: Tarea en ejecución
- **SUCCESS**: Tarea completada exitosamente
- **FAILURE**: Tarea falló con error
- **RETRY**: Tarea está siendo reintentada
- **REVOKED**: Tarea fue cancelada

## Flujo de Trabajo Típico

### 1. Lanzar una tarea y obtener su ID

```bash
TASK_ID=$(curl -X POST http://localhost:8000/api/celery/tasks/launch \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sii.sync_documents",
    "params": {
      "company_id": "123e4567-e89b-12d3-a456-426614174000"
    }
  }' | jq -r '.task_id')

echo "Task ID: $TASK_ID"
```

### 2. Consultar el estado periódicamente

```bash
# Polling cada 5 segundos
while true; do
  STATUS=$(curl -s http://localhost:8000/api/celery/tasks/$TASK_ID | jq -r '.status')
  echo "Status: $STATUS"

  if [[ "$STATUS" == "SUCCESS" ]] || [[ "$STATUS" == "FAILURE" ]]; then
    break
  fi

  sleep 5
done
```

### 3. Obtener el resultado final

```bash
curl -s http://localhost:8000/api/celery/tasks/$TASK_ID | jq .
```

## Ejemplo con Python

```python
import requests
import time

# Base URL
BASE_URL = "http://localhost:8000/api/celery"

# 1. Lanzar tarea
response = requests.post(
    f"{BASE_URL}/tasks/launch",
    json={
        "task_type": "sii.sync_documents",
        "params": {
            "company_id": "123e4567-e89b-12d3-a456-426614174000",
            "months": 1
        }
    }
)
task_id = response.json()["task_id"]
print(f"Task launched: {task_id}")

# 2. Poll por el resultado
while True:
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    data = response.json()
    status = data["status"]

    print(f"Status: {status}")

    if status in ["SUCCESS", "FAILURE"]:
        if status == "SUCCESS":
            print("Result:", data["result"])
        else:
            print("Error:", data["error"])
        break

    time.sleep(5)
```

## Ejemplo con JavaScript/TypeScript

```typescript
const BASE_URL = "http://localhost:8000/api/celery";

// 1. Lanzar tarea
async function launchTask(taskType: string, params: any): Promise<string> {
  const response = await fetch(`${BASE_URL}/tasks/launch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_type: taskType, params })
  });

  const data = await response.json();
  return data.task_id;
}

// 2. Consultar estado
async function getTaskStatus(taskId: string) {
  const response = await fetch(`${BASE_URL}/tasks/${taskId}`);
  return await response.json();
}

// 3. Esperar por resultado
async function waitForTask(taskId: string, pollInterval = 5000) {
  while (true) {
    const status = await getTaskStatus(taskId);
    console.log("Status:", status.status);

    if (status.status === "SUCCESS") {
      return status.result;
    } else if (status.status === "FAILURE") {
      throw new Error(status.error);
    }

    await new Promise(resolve => setTimeout(resolve, pollInterval));
  }
}

// Uso
const taskId = await launchTask("sii.sync_documents", {
  company_id: "123e4567-e89b-12d3-a456-426614174000",
  months: 1
});

const result = await waitForTask(taskId);
console.log("Result:", result);
```

## Manejo de Errores

### Error de Validación (422)

```json
{
  "detail": "Invalid parameters: company_id is required"
}
```

### Error Interno (500)

```json
{
  "detail": "Failed to launch task: Redis connection refused"
}
```

### Tarea No Encontrada (Status PENDING)

Nota: `PENDING` también se retorna para task IDs que no existen.

```json
{
  "task_id": "non-existent-id",
  "status": "PENDING",
  "result": null,
  "error": null,
  "traceback": null,
  "meta": {
    "info": "Task is waiting to be executed or doesn't exist"
  }
}
```

## Notas Importantes

1. **Redis Requerido**: El sistema Celery requiere Redis corriendo. Asegúrate de que esté configurado en `REDIS_URL`.

2. **Worker Requerido**: Debe haber al menos un Celery worker ejecutándose:
   ```bash
   cd backend-v2
   .venv/bin/celery -A app.infrastructure.celery worker --loglevel=info
   ```

3. **Timeouts**: Las tareas tienen timeouts configurados. Si una tarea tarda demasiado, puede ser terminada automáticamente.

4. **Reintentos**: Las tareas tienen reintentos automáticos configurados (máximo 3 por defecto).

5. **Task IDs**: Los task IDs son UUIDs generados por Celery. Son únicos y pueden ser usados para tracking.

6. **Persistencia**: Los resultados de tareas se almacenan en Redis por un tiempo limitado (configurable).

## Testing

Para probar los endpoints con curl:

```bash
# 1. Listar tareas disponibles
curl http://localhost:8000/api/celery/tasks

# 2. Lanzar una tarea
curl -X POST http://localhost:8000/api/celery/tasks/launch \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sii.sync_documents",
    "params": {
      "company_id": "test-company-id",
      "months": 1
    }
  }'

# 3. Consultar estado (reemplazar TASK_ID)
curl http://localhost:8000/api/celery/tasks/TASK_ID

# 4. Ver estadísticas
curl http://localhost:8000/api/celery/stats

# 5. Revocar tarea
curl -X DELETE http://localhost:8000/api/celery/tasks/TASK_ID
```

## Swagger/OpenAPI Docs

La documentación interactiva está disponible en:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

Navega a la sección "Celery Tasks" para probar los endpoints directamente desde el navegador.
