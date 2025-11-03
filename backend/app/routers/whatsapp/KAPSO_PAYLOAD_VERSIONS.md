# Kapso Webhook Payload Versions

Este documento describe las diferencias entre las versiones de payload de Kapso y cómo el webhook las maneja.

## Payload V1 (Anterior)

```json
{
  "message": {
    "id": "msg-id",
    "content": "mensaje de texto",
    "conversation_phone_number": "56912345678",
    "contact_name": "Usuario",
    "direction": "inbound",
    "message_type": "text",
    "has_media": false
  },
  "conversation": {
    "id": "conv-id"
  }
}
```

### Campos clave V1:
- `message.content` - Contenido del mensaje
- `message.conversation_phone_number` - Teléfono del remitente
- `message.message_type` - Tipo de mensaje
- `message.direction` - Dirección (inbound/outbound)

## Payload V2 (Actual)

```json
{
  "message": {
    "id": "wamid.xxx",
    "from": "56912345678",
    "text": {
      "body": "mensaje de texto"
    },
    "type": "text",
    "timestamp": "1762209446",
    "context": null,
    "kapso": {
      "direction": "inbound",
      "status": "delivered",
      "has_media": false,
      "processing_status": "pending"
    }
  },
  "conversation": {
    "id": "conv-id",
    "contact_name": "Usuario",
    "phone_number": "56912345678",
    "status": "active"
  }
}
```

### Campos clave V2:
- `message.text.body` - Contenido del mensaje de texto (estructura anidada)
- `message.from` - Teléfono del remitente
- `message.type` - Tipo de mensaje
- **`message.kapso.direction`** - Dirección (inbound/outbound) - ⚠️ Anidado en kapso!
- **`message.kapso.has_media`** - Flag de media - ⚠️ Anidado en kapso!
- **`message.kapso.status`** - Estado del mensaje
- `conversation.contact_name` - Nombre del contacto (movido a conversation)

## Principales Diferencias

| Campo | V1 | V2 |
|-------|----|----|
| Contenido del mensaje | `message.content` | `message.text.body` |
| Teléfono remitente | `message.conversation_phone_number` | `message.from` |
| Tipo de mensaje | `message.message_type` | `message.type` |
| Nombre de contacto | `message.contact_name` | `conversation.contact_name` |
| Dirección | `message.direction` | **`message.kapso.direction`** ⚠️ |
| Media flag | `message.has_media` | **`message.kapso.has_media`** ⚠️ |
| Status | `message.status` | **`message.kapso.status`** ⚠️ |

## Compatibilidad en el Webhook

El código en [webhooks.py](./routes/webhooks.py) soporta **ambas versiones** mediante fallbacks:

```python
# Contenido (v2 primero, luego v1)
if "text" in message_data and isinstance(message_data["text"], dict):
    message_content = message_data["text"].get("body", "")
else:
    message_content = message_data.get("content", "")

# Teléfono (v2 primero, luego v1)
sender_phone = message_data.get("from") or message_data.get("conversation_phone_number", "")

# Tipo (v2 primero, luego v1)
message_type = message_data.get("type") or message_data.get("message_type", "text")

# Nombre de contacto (ambas ubicaciones)
contact_name = message_data.get("contact_name") or conversation_data.get("contact_name", "")

# Direction (v2: anidado en kapso, v1: directo)
kapso_data = message_data.get("kapso", {})
direction = (
    kapso_data.get("direction") or  # V2: message.kapso.direction
    message_data.get("direction") or  # V1: message.direction
    conversation_data.get("direction", "")
)

# Media flag (v2: en kapso, v1: directo)
has_media = kapso_data.get("has_media") or message_data.get("has_media", False)
```

## Migración

Para cambiar de v1 a v2 en tu entorno:

1. **Kapso Dashboard**: Configurar webhook payload version a "v2"
2. **Código**: Ya está preparado para ambas versiones
3. **Testing**: Enviar mensaje de prueba y verificar logs

### Logs de debug

El webhook ahora muestra logs detallados:

```
🔍 Message data keys: ['id', 'from', 'text', 'type', 'timestamp', 'direction', 'status', 'has_media']
🔍 Conversation data keys: ['id', 'contact_name']
🔍 Direction: 'inbound' | Sender: 56912345678 | Type: text | Content: hola...
```

Estos logs ayudan a identificar qué versión se está recibiendo.

## Notas

- **Producción**: Usa v2
- **Local**: Configurable en Kapso dashboard
- **Retrocompatibilidad**: El código soporta ambas versiones automáticamente
