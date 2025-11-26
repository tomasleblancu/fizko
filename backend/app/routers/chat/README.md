# Chat API

Endpoint de chat para aplicaciones Expo/React Native.

## 🚀 Quick Links

- **[Quick Start para Expo](./QUICK_START_EXPO.md)** - Implementación en 5 minutos
- **[Guía Completa](./CHAT_FRONTEND_GUIDE.md)** - Documentación exhaustiva

---

## 📋 Resumen

Endpoint REST para chat con el sistema multi-agente de Fizko, sin dependencia de ChatKit.

### Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/chat` | POST | Chat con respuesta completa (blocking) |

### Características

✅ Sistema multi-agente (Supervisor → Especializados)
✅ Memoria conversacional por thread
✅ Contexto de empresa opcional
✅ Carga de contexto UI antes de ejecución
✅ Sin autenticación requerida (por ahora)

---

## 📤 Request

### Request Básico

```json
{
  "message": "¿Cuáles son mis documentos pendientes?",
  "thread_id": "thread_abc123",  // Opcional - se autogenera
  "company_id": "550e8400-e29b-41d4-a716-446655440000",  // UUID válido
  "metadata": {}  // Opcional
}
```

**⚠️ Importante:** `company_id` debe ser un UUID válido. Valores inválidos como `"unknown"` o `"company_123"` serán ignorados.

### Request con Contexto Requerido

Para cargar contexto específico antes de ejecutar el agente (por ejemplo, detalles de un documento):

**Opción 1 - Nivel raíz (recomendado):**
```json
{
  "message": "Muéstrame los detalles del documento",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "required_context": {
    "identifier": "document_detail",
    "entity_id": "86d42e09-f9e1-480f-911b-e5d13e0d0aa1",
    "entity_type": "sales_document"
  }
}
```

**Opción 2 - Dentro de metadata (también soportado):**
```json
{
  "message": "Muéstrame los detalles del documento",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "required_context": {
      "identifier": "document_detail",
      "entity_id": "86d42e09-f9e1-480f-911b-e5d13e0d0aa1",
      "entity_type": "sales_document"
    }
  }
}
```

**Parámetros de `required_context`:**
- `identifier` (string, requerido): Identificador del componente UI (ej: `"document_detail"`, `"tax_summary_iva"`)
- `entity_id` (string, opcional): ID de la entidad específica (ej: UUID del documento, `"2025-11"`)
- `entity_type` (string, opcional): Tipo de entidad (ej: `"sales_document"`, `"tax_period"`, `"contact"`)

---

## 📥 Response

```json
{
  "response": "Tus documentos pendientes son: ...",
  "thread_id": "thread_abc123",
  "metadata": {
    "elapsed_ms": 2500,
    "char_count": 150
  }
}
```

---

## 💻 Ejemplo Mínimo

```typescript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: '¿Hola, cómo estás?',
    company_id: '550e8400-e29b-41d4-a716-446655440000'  // UUID válido
  }),
});

const data = await response.json();
console.log(data.response);  // "¡Hola! Estoy bien..."
console.log(data.thread_id);  // "thread_abc123"
```

---

## 🔑 Company ID

### ¿Qué es?

El `company_id` es el UUID de la empresa del usuario. Proporciona contexto al agente sobre qué empresa está consultando.

### ¿Es obligatorio?

No, pero **recomendado**. Sin `company_id`:
- El agente responderá preguntas generales
- No tendrá acceso a datos específicos de la empresa

### Formato

```typescript
// ✅ CORRECTO - UUID válido
"550e8400-e29b-41d4-a716-446655440000"

// ❌ INCORRECTO - se ignorará
"company_123"
"unknown"
null
undefined
```

### ¿Cómo obtenerlo?

```typescript
// Desde Supabase auth (user metadata)
const { data } = await supabase.auth.getUser();
const companyId = data.user?.user_metadata?.company_id;

// Desde tabla companies
const { data } = await supabase
  .from('companies')
  .select('id')
  .eq('user_id', userId)
  .single();
const companyId = data?.id;
```

---

## 🧵 Thread Management

### ¿Qué es un thread?

Un thread mantiene el contexto de la conversación. Los mensajes en el mismo thread tienen memoria compartida.

### Auto-generación

Si no envías `thread_id`, se genera automáticamente:

```typescript
// Primera llamada - sin thread_id
{ message: "Hola" }

// Response incluye el thread_id
{ "response": "¡Hola!", "thread_id": "thread_abc123", ... }

// Llamadas siguientes - usa el mismo thread_id
{ message: "¿Y mis documentos?", thread_id: "thread_abc123" }
```

### Persistencia

Para continuar conversaciones:

```typescript
// Guardar
localStorage.setItem('chat_thread_id', threadId);

// Cargar
const threadId = localStorage.getItem('chat_thread_id');
```

---

## 🔧 Testing

### Con curl

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola",
    "company_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Con Postman

1. Método: POST
2. URL: `http://localhost:8000/api/chat`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "message": "Hola",
  "company_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 🏗️ Arquitectura

```
HTTP Request
    ↓
/api/chat
    ↓
ChatService.execute()
    ↓
HandoffsManager.get_supervisor_agent()
    ↓
Supervisor Agent (OpenAI)
    ↓
├─→ Tax Documents Agent
├─→ General Knowledge Agent
└─→ [Otros agentes especializados]
    ↓
JSON Response
```

### Componentes

- **Router**: [chat.py](./chat.py) - Endpoint HTTP
- **Service**: [chat_service.py](../../services/chat/chat_service.py) - Lógica de negocio
- **Agents**: Sistema multi-agente con handoffs
- **Memory**: Sesiones por thread para contexto conversacional

---

## 📊 Response Fields

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `response` | string | Respuesta completa del agente |
| `thread_id` | string | ID del thread para continuidad |
| `metadata.elapsed_ms` | number | Tiempo de ejecución en ms |
| `metadata.char_count` | number | Caracteres en la respuesta |

---

## ⚠️ Errores Comunes

### "Invalid company_id format"

**Causa:** El `company_id` no es un UUID válido.

**Solución:**
```typescript
// ❌ Incorrecto
company_id: "company_123"

// ✅ Correcto
company_id: "550e8400-e29b-41d4-a716-446655440000"
```

### "Request timeout"

**Causa:** El agente tarda mucho en responder (operación compleja o herramientas lentas).

**Solución:**
- Implementa timeout en el cliente (ej: 30-60 segundos)
- Verifica logs del backend para ver qué herramientas se están ejecutando
- Reduce complejidad de la consulta si es muy amplia

---

## 🔐 Seguridad (TODO)

Actualmente **sin autenticación**. Próximamente:

- [ ] JWT authentication
- [ ] Rate limiting
- [ ] Request validation
- [ ] CORS configurado

---

## 📚 Más Recursos

- [FastAPI Docs](http://localhost:8000/docs) - Swagger UI interactivo
- [Guía Multi-Agente](../../agents/README.md) - Sistema de agentes
- [Supabase Setup](../../../supabase/README.md) - Base de datos

---

## 🐛 Debugging

### Logs del Backend

```bash
# Ver logs en tiempo real
docker logs -f <container_id>

# Buscar errores específicos
docker logs <container_id> | grep "❌"
```

### Network Inspector

```typescript
// React Native Debugger
// Cmd+D (iOS) / Cmd+M (Android) → Debug

// Headers
console.log('Request headers:', {
  'Content-Type': 'application/json',
});

// Body
console.log('Request body:', {
  message,
  thread_id,
  company_id,
});
```

---

## 🚀 Próximos Pasos

1. Implementa el hook `useChat` ([Quick Start](./QUICK_START_EXPO.md))
2. Obtén el `company_id` del usuario
3. Prueba con curl primero
4. Integra en tu app Expo
5. Agrega persistencia del `thread_id`

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs del backend
2. Verifica que el `company_id` sea UUID válido
3. Prueba con curl para aislar el problema
4. Consulta la [Guía Completa](./CHAT_FRONTEND_GUIDE.md)

---

**Versión:** 1.0.0
**Última actualización:** 2024-11
