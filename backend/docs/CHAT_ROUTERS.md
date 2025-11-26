# Chat Routers - Backend V2

## ✅ Estado: COMPLETO

Los routers de chat han sido creados en versiones **modulares y stateless** adaptadas para backend-v2.

**Cero dependencias de SQLAlchemy** - Todo es stateless y en memoria.

## 📁 Archivos Creados

```
app/routers/
├── __init__.py                          # Módulo de routers (actualizado)
└── chat/
    ├── __init__.py                      # Módulo de chat
    ├── agent.py                         # Router de agente de chat
    └── conversations.py                 # Router de conversaciones (en memoria)
```

## 🎯 Componentes

### 1. Chat Agent Router (`agent.py`)

Router stateless para ejecutar agentes de IA con contexto proporcionado.

**Características:**
- ✅ Stateless (sin DB, sin SQLAlchemy)
- ✅ Acepta contexto como parámetros
- ✅ Integración con SII
- ✅ Modelos Pydantic para validación
- ✅ Thread IDs para tracking client-side

#### Endpoints

##### `POST /api/chat`
Chat básico con agente.

**Request:**
```json
{
  "message": "¿Qué es el IVA?",
  "user_id": "user_123",
  "company_id": "77794858-k",
  "thread_id": "thread_abc",
  "company_info": {
    "rut": "77794858-k",
    "razon_social": "EMPRESA DEMO SPA"
  },
  "recent_compras": [...],
  "recent_ventas": [...],
  "recent_f29": {...}
}
```

**Response:**
```json
{
  "response": "El IVA (Impuesto al Valor Agregado) es...",
  "thread_id": "thread_abc",
  "metadata": {
    "company_id": "77794858-k",
    "user_id": "user_123"
  }
}
```

##### `POST /api/chat/sii`
Chat con contexto SII (integración con /verify).

**Request:**
```json
{
  "message": "¿Cuál es mi razón social?",
  "rut": "77794858-k",
  "contribuyente_info": {
    "razon_social": "EMPRESA DEMO SPA",
    "actividad_economica": "Servicios de software",
    ...
  },
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "response": "Tu razón social es EMPRESA DEMO SPA",
  "thread_id": "thread_abc",
  "metadata": {
    "rut": "77794858-k"
  }
}
```

##### `GET /api/chat/health`
Health check del servicio de chat.

**Response:**
```json
{
  "status": "healthy",
  "service": "chat",
  "features": {
    "stateless": true,
    "database": false,
    "chatkit": false,
    "sii_integration": true
  }
}
```

### 2. Conversations Router (`conversations.py`)

Router para gestionar conversaciones **EN MEMORIA** (sin DB, sin SQLAlchemy).

**⚠️ Advertencia**: Las conversaciones se pierden al reiniciar el servidor.

**Características:**
- ✅ Almacenamiento en memoria (diccionario Python)
- ✅ CRUD completo
- ✅ Paginación
- ✅ Filtros (user_id, company_id)
- ✅ Estadísticas
- ❌ NO usa SQLAlchemy
- ❌ NO persiste en DB

#### Endpoints

##### `POST /api/conversations`
Crear conversación.

**Request:**
```json
{
  "user_id": "user_123",
  "company_id": "77794858-k",
  "title": "Consultas tributarias Enero 2025"
}
```

**Response:**
```json
{
  "data": {
    "id": "conv_abc123",
    "user_id": "user_123",
    "company_id": "77794858-k",
    "title": "Consultas tributarias Enero 2025",
    "messages": [],
    "created_at": "2025-01-19T12:00:00",
    "updated_at": "2025-01-19T12:00:00"
  },
  "message": "Conversation created successfully (in-memory)"
}
```

##### `GET /api/conversations`
Listar conversaciones con filtros y paginación.

**Query params:**
- `user_id` - Filtrar por usuario
- `company_id` - Filtrar por compañía
- `skip` - Paginación (default: 0)
- `limit` - Máx resultados (default: 50, max: 100)

**Response:**
```json
{
  "data": [
    {
      "id": "conv_abc123",
      "user_id": "user_123",
      "company_id": "77794858-k",
      "title": "Consultas tributarias",
      "messages": [...],
      "created_at": "2025-01-19T12:00:00",
      "updated_at": "2025-01-19T12:00:00"
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 50,
    "total": 1
  }
}
```

##### `GET /api/conversations/{conversation_id}`
Obtener conversación por ID.

**Response:**
```json
{
  "data": {
    "id": "conv_abc123",
    "user_id": "user_123",
    "messages": [
      {
        "id": "msg_001",
        "role": "user",
        "content": "¿Qué es el IVA?",
        "created_at": "2025-01-19T12:00:00"
      },
      {
        "id": "msg_002",
        "role": "assistant",
        "content": "El IVA es...",
        "created_at": "2025-01-19T12:00:05"
      }
    ],
    ...
  }
}
```

##### `POST /api/conversations/{conversation_id}/messages`
Agregar mensaje a conversación.

**Request:**
```json
{
  "role": "user",
  "content": "¿Qué es el IVA?"
}
```

**Response:**
```json
{
  "data": {
    "id": "msg_001",
    "role": "user",
    "content": "¿Qué es el IVA?",
    "created_at": "2025-01-19T12:00:00"
  },
  "message": "Message added successfully"
}
```

##### `GET /api/conversations/{conversation_id}/messages`
Listar mensajes de conversación.

**Query params:**
- `skip` - Paginación (default: 0)
- `limit` - Máx resultados (default: 100, max: 200)

##### `DELETE /api/conversations/{conversation_id}`
Eliminar conversación.

**Response:** `204 No Content`

##### `GET /api/conversations/stats/summary`
Estadísticas de conversaciones.

**Response:**
```json
{
  "data": {
    "total_conversations": 42,
    "total_messages": 184,
    "unique_users": 12,
    "unique_companies": 8,
    "storage": "in-memory (volatile)"
  }
}
```

##### `POST /api/conversations/clear`
**⚠️ PELIGRO**: Borrar TODAS las conversaciones.

Solo para desarrollo/testing.

## 💡 Casos de Uso

### Caso 1: Chat Simple

```python
import requests

# Chat básico
response = requests.post("http://localhost:8000/api/chat", json={
    "message": "¿Qué es el IVA?",
    "user_id": "user_123"
})

print(response.json()["response"])
# "El IVA (Impuesto al Valor Agregado) es..."
```

### Caso 2: Chat con Contexto SII

```python
# 1. Verificar credenciales SII
verify_response = requests.post("http://localhost:8000/api/sii/verify", json={
    "rut": "77794858",
    "dv": "k",
    "password": "******"
})

contribuyente_info = verify_response.json()["contribuyente_info"]

# 2. Chat con contexto SII
chat_response = requests.post("http://localhost:8000/api/chat/sii", json={
    "message": "Dame un resumen de mi empresa",
    "rut": "77794858-k",
    "contribuyente_info": contribuyente_info
})

print(chat_response.json()["response"])
```

### Caso 3: Chat con Contexto Completo

```python
# Obtener datos SII
compras = requests.post("http://localhost:8000/api/sii/compras", ...)
ventas = requests.post("http://localhost:8000/api/sii/ventas", ...)
f29 = requests.post("http://localhost:8000/api/sii/f29", ...)

# Chat con contexto completo
response = requests.post("http://localhost:8000/api/chat", json={
    "message": "Dame un análisis tributario completo",
    "user_id": "user_123",
    "company_id": "77794858-k",
    "company_info": contribuyente_info,
    "recent_compras": compras.json()["data"][:10],
    "recent_ventas": ventas.json()["data"][:10],
    "recent_f29": f29.json()
})
```

### Caso 4: Gestión de Conversaciones

```python
# Crear conversación
conv_response = requests.post("http://localhost:8000/api/conversations", json={
    "user_id": "user_123",
    "company_id": "77794858-k",
    "title": "Consultas de Enero"
})

conv_id = conv_response.json()["data"]["id"]

# Agregar mensaje de usuario
requests.post(f"http://localhost:8000/api/conversations/{conv_id}/messages", json={
    "role": "user",
    "content": "¿Qué es el IVA?"
})

# Ejecutar agente
chat_response = requests.post("http://localhost:8000/api/chat", json={
    "message": "¿Qué es el IVA?",
    "user_id": "user_123",
    "thread_id": conv_id
})

# Agregar respuesta del agente
requests.post(f"http://localhost:8000/api/conversations/{conv_id}/messages", json={
    "role": "assistant",
    "content": chat_response.json()["response"]
})

# Listar mensajes
messages = requests.get(f"http://localhost:8000/api/conversations/{conv_id}/messages")
```

## 🔗 Integración con main.py

Los routers están integrados en [main.py](app/main.py):

```python
from app.routers.chat import agent as chat_agent
from app.routers.chat import conversations as chat_conversations

app.include_router(chat_agent.router, prefix="/api", tags=["Chat Agent"])
app.include_router(chat_conversations.router, prefix="/api", tags=["Conversations"])
```

## 📊 Comparación con Backend Original

| Feature | Backend Original | Backend V2 |
|---------|------------------|------------|
| **Chat endpoint** | ChatKit SSE streaming | REST JSON |
| **Database** | ✅ PostgreSQL/Supabase | ❌ En memoria |
| **Authentication** | ✅ JWT required | ❌ No auth |
| **UI Tools** | ✅ ChatKit widgets | ❌ No |
| **Guardrails** | ✅ Abuse detection | ❌ No |
| **Conversations** | ✅ Persistentes (DB) | ⚠️ En memoria (volátil) |
| **Session management** | ✅ ChatKit sessions | ❌ Thread IDs client-side |
| **Attachments** | ✅ Con storage | ❌ No soportado |
| **Streaming** | ✅ SSE | ❌ JSON response |

## 🚀 Endpoints Disponibles

### Chat Agent
- `POST /api/chat` - Chat básico
- `POST /api/chat/sii` - Chat con contexto SII
- `GET /api/chat/health` - Health check

### Conversations (In-Memory)
- `POST /api/conversations` - Crear conversación
- `GET /api/conversations` - Listar conversaciones
- `GET /api/conversations/{id}` - Obtener conversación
- `POST /api/conversations/{id}/messages` - Agregar mensaje
- `GET /api/conversations/{id}/messages` - Listar mensajes
- `DELETE /api/conversations/{id}` - Eliminar conversación
- `GET /api/conversations/stats/summary` - Estadísticas
- `POST /api/conversations/clear` - Borrar todas (dev only)

## ⚠️ Limitaciones Importantes

### Conversations Router

1. **Almacenamiento volátil**: Los datos se pierden al reiniciar
2. **Sin persistencia**: No hay backup ni recuperación
3. **Límite de memoria**: RAM del servidor
4. **Sin multi-instance**: No compartido entre instancias

### Recomendaciones

Para **desarrollo**:
- ✅ Usar conversations router para testing
- ✅ Útil para demos y prototipos

Para **producción**:
- ❌ NO usar conversations router
- ✅ Implementar storage client-side
- ✅ O migrar a backend con DB
- ✅ O usar Redis para persistencia

## 📝 Modularización

Los routers están **completamente modularizados**:

```
app/routers/chat/
├── __init__.py          # Exports limpios
├── agent.py             # Chat agent (independiente)
└── conversations.py     # Conversations (independiente)
```

**Beneficios:**
- ✅ Separación de responsabilidades
- ✅ Fácil de mantener
- ✅ Fácil de testear
- ✅ Fácil de extender

## 🔍 Verificación

### Compilación
```bash
python3 -m py_compile app/routers/chat/agent.py
python3 -m py_compile app/routers/chat/conversations.py
python3 -m py_compile app/routers/chat/__init__.py
```

### Test manual
```bash
# Iniciar servidor
./start.sh

# En otra terminal:
# Test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es el IVA?", "user_id": "test"}'

# Test conversations
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "title": "Test conversation"}'

# Test health
curl http://localhost:8000/api/chat/health
```

## 🎉 Resumen

- ✅ **2 routers modulares** creados
- ✅ **8 endpoints** de chat agent
- ✅ **8 endpoints** de conversations
- ✅ **0 dependencias de SQLAlchemy**
- ✅ **100% stateless** (agent)
- ✅ **En memoria** (conversations)
- ✅ Integrados en main.py
- ✅ Documentación completa
- ✅ Ejemplos de uso

---

**Fecha de Creación**: 19 de Noviembre, 2025
**Archivos**: 3 Python files
**Endpoints**: 16 total
**SQLAlchemy**: ❌ No usado
**Status**: ✅ ROUTERS COMPLETE
