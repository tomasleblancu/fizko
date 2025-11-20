# Webhook Troubleshooting Guide

## Error 401 Unauthorized - RESUELTO ✅

### Problema
```
34.211.200.85:0 - "POST /api/whatsapp/webhook HTTP/1.1" 401
```

### Causa
El endpoint del webhook estaba protegido con autenticación JWT (`Depends(require_auth)`), pero los webhooks de Kapso no envían tokens JWT - solo envían firma HMAC en el header `X-Kapso-Signature`.

### Solución Implementada
Se creó un router separado `webhook_router` sin autenticación JWT. El webhook ahora se autentica usando firma HMAC-SHA256.

```python
# Router separado para webhooks (sin autenticación JWT)
webhook_router = APIRouter(
    prefix="/api/whatsapp",
    tags=["whatsapp-webhooks"],
)

@webhook_router.post("/webhook")
async def handle_webhook(
    request: Request,
    x_kapso_signature: Optional[str] = Header(None),
) -> Dict[str, str]:
    # Validación HMAC en lugar de JWT
    ...
```

## Configuración del Webhook en Kapso

### 1. URL del Webhook
```
https://tu-dominio.com/api/whatsapp/webhook
```

### 2. Variables de Entorno Requeridas

```bash
# En tu archivo .env
KAPSO_API_TOKEN=tu-token-de-api
KAPSO_API_BASE_URL=https://app.kapso.ai/api/v1
KAPSO_WEBHOOK_SECRET=tu-secreto-compartido  # Importante para validación
```

### 3. Headers que Kapso Enviará

```
POST /api/whatsapp/webhook
Content-Type: application/json
X-Kapso-Signature: abc123def456...  # HMAC-SHA256 del payload
```

## Testing del Webhook

### Opción 1: Testing Local con ngrok

```bash
# Terminal 1: Iniciar servidor
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Exponer con ngrok
ngrok http 8000

# Usar la URL de ngrok en Kapso:
# https://abc123.ngrok.io/api/whatsapp/webhook
```

### Opción 2: Testing Manual con curl

```bash
# Sin firma (funcionará si KAPSO_WEBHOOK_SECRET no está configurado)
curl -X POST https://tu-dominio.com/api/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "message.received",
    "conversation_id": "test-conv-123",
    "message_id": "test-msg-456",
    "payload": {
      "from": "+56912345678",
      "content": "Hola desde test",
      "message_type": "text"
    }
  }'

# Respuesta esperada:
# {"status":"ok","message":"Webhook processed successfully","event_type":"message.received"}
```

### Opción 3: Testing con Firma HMAC (Producción)

```python
import hmac
import hashlib
import json

# Payload del webhook
payload = {
    "event_type": "message.received",
    "conversation_id": "test-conv-123",
    "payload": {"from": "+56912345678", "content": "Test"}
}

payload_str = json.dumps(payload)
secret = "tu-webhook-secret"

# Generar firma
signature = hmac.new(
    secret.encode('utf-8'),
    payload_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print(f"X-Kapso-Signature: {signature}")
```

Luego usa la firma en curl:
```bash
curl -X POST https://tu-dominio.com/api/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -H "X-Kapso-Signature: FIRMA_GENERADA" \
  -d '{"event_type":"message.received",...}'
```

## Logs Esperados

### Webhook Exitoso
```
INFO:     📥 Webhook recibido de IP: 34.211.200.85
INFO:     ✅ Firma del webhook validada correctamente
INFO:     📥 Evento: message.received | Conversación: conv-123 | Mensaje: msg-456
INFO:     💬 Mensaje de +56912345678: Hola, necesito ayuda
INFO:     127.0.0.1:0 - "POST /api/whatsapp/webhook HTTP/1.1" 200 OK
```

### Webhook con Error de Firma
```
INFO:     📥 Webhook recibido de IP: 34.211.200.85
WARNING:  ⚠️ Webhook con firma HMAC inválida
INFO:     127.0.0.1:0 - "POST /api/whatsapp/webhook HTTP/1.1" 401 Unauthorized
```

### Webhook sin Secreto Configurado
```
INFO:     📥 Webhook recibido de IP: 34.211.200.85
WARNING:  ⚠️ KAPSO_WEBHOOK_SECRET no configurado - webhook sin validación de firma
INFO:     📥 Evento: message.received | Conversación: conv-123 | Mensaje: msg-456
INFO:     127.0.0.1:0 - "POST /api/whatsapp/webhook HTTP/1.1" 200 OK
```

## Eventos Soportados

El webhook puede recibir los siguientes tipos de eventos:

| Evento | Descripción |
|--------|-------------|
| `message.received` | Mensaje recibido del usuario |
| `message.sent` | Confirmación de mensaje enviado |
| `message.delivered` | Mensaje entregado al destinatario |
| `message.read` | Mensaje leído por el destinatario |
| `message.failed` | Error al enviar mensaje |
| `conversation.status_changed` | Estado de conversación cambió (activa/finalizada) |
| `contact.created` | Nuevo contacto creado |
| `contact.updated` | Contacto actualizado |

## Estructura de Payload por Evento

### message.received
```json
{
  "event_type": "message.received",
  "conversation_id": "conv-abc123",
  "message_id": "msg-xyz789",
  "timestamp": "2025-10-26T10:30:00Z",
  "payload": {
    "from": "+56912345678",
    "to": "+56987654321",
    "content": "Hola, necesito ayuda",
    "message_type": "text",
    "timestamp": "2025-10-26T10:30:00Z",
    "contact": {
      "id": "contact-123",
      "phone_number": "+56912345678",
      "display_name": "Juan Pérez"
    }
  }
}
```

### message.sent
```json
{
  "event_type": "message.sent",
  "conversation_id": "conv-abc123",
  "message_id": "msg-xyz789",
  "timestamp": "2025-10-26T10:30:00Z",
  "payload": {
    "status": "sent",
    "message_type": "text"
  }
}
```

### message.delivered
```json
{
  "event_type": "message.delivered",
  "conversation_id": "conv-abc123",
  "message_id": "msg-xyz789",
  "timestamp": "2025-10-26T10:30:05Z",
  "payload": {
    "status": "delivered"
  }
}
```

### message.read
```json
{
  "event_type": "message.read",
  "conversation_id": "conv-abc123",
  "message_id": "msg-xyz789",
  "timestamp": "2025-10-26T10:35:00Z",
  "payload": {
    "status": "read"
  }
}
```

## Implementar Lógica de Procesamiento

Edita el archivo `/backend/app/routers/whatsapp.py` en la línea ~606:

```python
if event_type == "message.received":
    payload_data = data.get("payload", {})
    message_content = payload_data.get("content", "")
    sender_phone = payload_data.get("from", "")

    # 1. Guardar en base de datos
    async with AsyncSessionLocal() as db:
        # Guardar mensaje
        pass

    # 2. Responder automáticamente
    if "ayuda" in message_content.lower():
        await whatsapp_service.send_text(
            conversation_id=conversation_id,
            message="¿En qué puedo ayudarte?"
        )

    # 3. Enviar a agente de IA
    # ai_response = await process_with_ai(message_content)

    # 4. Marcar como leído
    await whatsapp_service.mark_as_read(conversation_id=conversation_id)
```

## Checklist de Verificación

- [ ] `KAPSO_WEBHOOK_SECRET` configurado en `.env`
- [ ] URL del webhook configurada en panel de Kapso
- [ ] Webhook router registrado en `main.py`
- [ ] Servidor corriendo y accesible desde internet
- [ ] Logs del servidor mostrando webhooks entrantes
- [ ] Firma HMAC validando correctamente (ver logs)
- [ ] Respuesta 200 OK desde el webhook

## Troubleshooting Común

### Error: "Missing X-Kapso-Signature header"
**Causa:** Kapso no está enviando la firma
**Solución:** Verifica la configuración del webhook en el panel de Kapso

### Error: "Invalid webhook signature"
**Causa:** El secreto en tu `.env` no coincide con el de Kapso
**Solución:** Verifica que `KAPSO_WEBHOOK_SECRET` sea idéntico en ambos lados

### Error: Connection refused
**Causa:** El servidor no es accesible desde internet
**Solución:**
- Verifica firewall/security groups
- Usa ngrok para testing local
- Verifica que el servidor esté corriendo

### No se reciben webhooks
**Causa:** URL incorrecta o eventos no suscritos
**Solución:**
- Verifica la URL en panel de Kapso
- Verifica que los eventos estén suscritos
- Revisa logs del servidor

## Referencias

- Documentación de webhooks: [Kapso API Docs](https://app.kapso.ai/api/docs)
- Código del webhook: `backend/app/routers/whatsapp.py:538`
- Ejemplos de procesamiento: `backend/app/integrations/kapso/examples.py:106`
