# Configuración de Kapso WhatsApp - Fizko

## ✅ Cambios Implementados

Se actualizó el webhook para usar los headers correctos de Kapso:
- ✅ `X-Webhook-Signature` (era `X-Kapso-Signature`)
- ✅ `X-Webhook-Event` para identificar el tipo de evento
- ✅ `X-Idempotency-Key` para evitar duplicados
- ✅ Soporte para webhooks batch (`X-Webhook-Batch`, `X-Batch-Size`)

## 📋 Pasos de Configuración

### 1. Variables de Entorno

Tu archivo `.env` debe tener:

```bash
# Kapso WhatsApp API
KAPSO_API_TOKEN=tu-token-de-api
KAPSO_API_BASE_URL=https://app.kapso.ai/api/v1
KAPSO_WEBHOOK_SECRET=c2ae059fc9f1f6dca459524a028495063e59dec64d3b722b189d721391a4d33f
```

### 2. Configuración en Panel de Kapso

Ve a https://app.kapso.ai y configura:

**Webhook URL:**
```
https://tu-dominio.com/api/whatsapp/webhook
```

**Webhook Secret/Signing Secret:**
```
c2ae059fc9f1f6dca459524a028495063e59dec64d3b722b189d721391a4d33f
```

**Eventos recomendados:**
- ✅ `whatsapp.message.received` - Mensajes entrantes
- ✅ `whatsapp.message.sent` - Confirmación de envío
- ✅ `whatsapp.message.delivered` - Mensaje entregado
- ✅ `whatsapp.message.read` - Mensaje leído
- ✅ `whatsapp.message.failed` - Error al enviar

### 3. Reiniciar Servidor

Después de actualizar el `.env`:

```bash
# Detener servidor (Ctrl+C)
# Luego reiniciar:
cd backend
uvicorn app.main:app --reload
```

## 🔍 Logs Esperados

### ✅ Webhook Exitoso

```
INFO: 📥 Webhook recibido de IP: 34.211.200.85
INFO: 📋 Evento: whatsapp.message.received
INFO: 🔑 Idempotency Key: unique-key-123
INFO: ✅ Firma del webhook validada correctamente
INFO: 📥 Procesando evento: whatsapp.message.received | Conv: conv-123 | Msg: msg-456
INFO: 💬 Mensaje text de +56912345678: Hola, necesito ayuda
INFO: 34.211.200.85:0 - "POST /api/whatsapp/webhook HTTP/1.1" 200 OK
```

### ❌ Webhook con Firma Inválida

```
INFO: 📥 Webhook recibido de IP: 34.211.200.85
WARNING: ⚠️ Webhook con firma HMAC inválida
WARNING: 🔐 Firma recibida: abc123...
WARNING: 🔑 Secret configurado: c2ae05...
INFO: 34.211.200.85:0 - "POST /api/whatsapp/webhook HTTP/1.1" 401 Unauthorized
```

## 📡 Headers de Kapso

Tu webhook ahora acepta estos headers:

```http
POST /api/whatsapp/webhook HTTP/1.1
Content-Type: application/json
X-Webhook-Event: whatsapp.message.received
X-Webhook-Signature: sha256=abc123def456...
X-Idempotency-Key: unique-event-id-12345
X-Webhook-Batch: false
```

## 🧪 Testing

### Test Manual con curl

```bash
# Generar firma HMAC
SECRET="c2ae059fc9f1f6dca459524a028495063e59dec64d3b722b189d721391a4d33f"
PAYLOAD='{"event_type":"whatsapp.message.received","conversation_id":"test-123"}'

SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

# Enviar webhook
curl -X POST http://localhost:8000/api/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: $SIGNATURE" \
  -H "X-Webhook-Event: whatsapp.message.received" \
  -H "X-Idempotency-Key: test-$(date +%s)" \
  -d "$PAYLOAD"
```

### Test con Script Python

```bash
cd backend
python test_webhook.py --with-signature
```

## 🎯 Tipos de Eventos

| Evento | Header | Descripción |
|--------|--------|-------------|
| `whatsapp.message.received` | X-Webhook-Event | Mensaje recibido del usuario |
| `whatsapp.message.sent` | X-Webhook-Event | Confirmación de envío |
| `whatsapp.message.delivered` | X-Webhook-Event | Mensaje entregado |
| `whatsapp.message.read` | X-Webhook-Event | Mensaje leído |
| `whatsapp.message.failed` | X-Webhook-Event | Error al enviar |

## 📦 Webhooks Batch

Kapso puede enviar múltiples eventos en un solo request:

```json
[
  {
    "event_type": "whatsapp.message.received",
    "conversation_id": "conv-1",
    "message_id": "msg-1",
    "payload": {...}
  },
  {
    "event_type": "whatsapp.message.received",
    "conversation_id": "conv-2",
    "message_id": "msg-2",
    "payload": {...}
  }
]
```

Headers batch:
```
X-Webhook-Batch: true
X-Batch-Size: 2
```

Tu webhook ya maneja esto automáticamente.

## 🔐 Seguridad

### Validación HMAC-SHA256

El webhook valida que el payload no ha sido modificado:

1. Kapso genera: `HMAC-SHA256(payload, secret)`
2. Envía en header: `X-Webhook-Signature: <hash>`
3. Tu servidor verifica con el mismo secret
4. Si coinciden → webhook válido ✅
5. Si no coinciden → webhook rechazado ❌

### Idempotencia

Usa `X-Idempotency-Key` para evitar procesar el mismo evento dos veces:

```python
# En tu código (opcional):
idempotency_cache = {}

if x_idempotency_key in idempotency_cache:
    logger.info(f"⚠️ Evento duplicado: {x_idempotency_key}")
    return {"status": "ok", "message": "Already processed"}

# Procesar evento...
idempotency_cache[x_idempotency_key] = True
```

## 🚀 Implementar Lógica de Negocio

Edita [app/routers/whatsapp.py:639](app/routers/whatsapp.py#L639):

```python
if event_type in ["message.received", "whatsapp.message.received"]:
    payload_data = event_data.get("payload", {})
    message_content = payload_data.get("content", "")
    sender_phone = payload_data.get("from", "")

    # Tu lógica aquí:

    # 1. Guardar en base de datos
    async with AsyncSessionLocal() as db:
        # Guardar mensaje...
        pass

    # 2. Auto-responder
    if "ayuda" in message_content.lower():
        await whatsapp_service.send_text(
            conversation_id=conversation_id,
            message="¿En qué puedo ayudarte? 🤖"
        )

    # 3. Enviar a agente de IA
    # response = await ai_agent.process(message_content)
    # await whatsapp_service.send_text(conversation_id, response)

    # 4. Marcar como leído
    await whatsapp_service.mark_as_read(conversation_id=conversation_id)
```

## ✅ Checklist

- [ ] `KAPSO_WEBHOOK_SECRET` configurado en `.env`
- [ ] Mismo secret configurado en panel de Kapso
- [ ] URL del webhook configurada en Kapso
- [ ] Eventos suscritos en Kapso
- [ ] Servidor reiniciado después de cambios en `.env`
- [ ] Logs mostrando firma validada correctamente
- [ ] Respuesta 200 OK desde el webhook

## 🐛 Troubleshooting

### Problema: 401 Unauthorized

**Causa:** Secret no coincide o header faltante

**Solución:**
1. Verifica que el secret en `.env` sea idéntico al de Kapso
2. Verifica que Kapso esté enviando `X-Webhook-Signature`
3. Revisa logs para ver exactamente qué falta

### Problema: Firma inválida

**Causa:** Secret diferente o payload modificado

**Solución:**
1. Copia el secret exacto de Kapso
2. Pégalo en `.env` sin espacios extra
3. Reinicia el servidor
4. Los logs mostrarán los primeros 20 chars de la firma para debug

### Problema: No llegan webhooks

**Causa:** URL incorrecta o firewall

**Solución:**
1. Verifica que la URL sea accesible desde internet
2. Prueba con `curl` desde otra máquina
3. Verifica firewall/security groups
4. Para desarrollo local, usa ngrok

## 📚 Referencias

- Código del webhook: [app/routers/whatsapp.py:539](app/routers/whatsapp.py#L539)
- Ejemplos de uso: [app/integrations/kapso/examples.py](app/integrations/kapso/examples.py)
- Documentación completa: [app/integrations/kapso/README.md](app/integrations/kapso/README.md)
- Troubleshooting: [app/integrations/kapso/WEBHOOK_TROUBLESHOOTING.md](app/integrations/kapso/WEBHOOK_TROUBLESHOOTING.md)
