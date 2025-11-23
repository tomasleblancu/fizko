# WhatsApp API Endpoint - Enviar a Número de Teléfono

## Nuevo Endpoint: `POST /api/whatsapp/send/to-phone`

Endpoint simplificado para enviar mensajes de WhatsApp directamente a un número de teléfono.

## 🔒 Autenticación

Requiere JWT token en header:
```
Authorization: Bearer <your-jwt-token>
```

## 📋 Request Body

```json
{
  "phone_number": "+56912345678",
  "message": "Tu mensaje aquí",
  "whatsapp_config_id": "config_abc123"  // Opcional
}
```

### Parámetros

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `phone_number` | string | ✅ Sí | Número de teléfono (con o sin prefijo +) |
| `message` | string | ✅ Sí | Contenido del mensaje (1-4096 caracteres) |
| `whatsapp_config_id` | string | ❌ No | ID de configuración de WhatsApp para filtrar |

## 📤 Response

### Éxito (200 OK)

```json
{
  "success": true,
  "message_id": "wamid.HBgNNTY5NzUzODk5NzMVAgARGBIzQzBFRDM2M...",
  "conversation_id": "4cb85e5f-e7f6-4b1a-8e8d-7c73fd8a2e99",
  "status": "sent"
}
```

### Error: No hay conversación activa (400 Bad Request)

```json
{
  "detail": "No active conversation found for 56912345678. The user must first initiate a conversation by sending a message, or you must send an approved WhatsApp template to start the conversation."
}
```

### Error del servidor (500 Internal Server Error)

```json
{
  "detail": "Failed to send message: <error details>"
}
```

## 💻 Ejemplos de Uso

### 1. Usando cURL

```bash
# Obtener token JWT (ejemplo)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Enviar mensaje
curl -X POST "http://localhost:8089/api/whatsapp/send/to-phone" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+56912345678",
    "message": "Tu Form 29 está listo para revisar"
  }'
```

### 2. Usando Python (requests)

```python
import requests

# URL del backend
BASE_URL = "http://localhost:8089"
TOKEN = "your-jwt-token"

# Enviar mensaje
response = requests.post(
    f"{BASE_URL}/api/whatsapp/send/to-phone",
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    },
    json={
        "phone_number": "+56912345678",
        "message": "¡Hola! Tu pago fue recibido correctamente.",
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Mensaje enviado!")
    print(f"   Conversation ID: {data['conversation_id']}")
    print(f"   Message ID: {data['message_id']}")
else:
    print(f"❌ Error: {response.json()['detail']}")
```

### 3. Usando Python (httpx async)

```python
import httpx
import asyncio

async def send_whatsapp_message(phone: str, message: str):
    """Enviar mensaje de WhatsApp"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8089/api/whatsapp/send/to-phone",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "phone_number": phone,
                "message": message,
            },
            timeout=30.0,
        )

        response.raise_for_status()
        return response.json()

# Uso
result = await send_whatsapp_message(
    phone="+56912345678",
    message="Tu recordatorio de F29"
)
print(f"Message sent: {result['message_id']}")
```

### 4. Usando TypeScript/JavaScript (fetch)

```typescript
interface SendToPhoneRequest {
  phone_number: string;
  message: string;
  whatsapp_config_id?: string;
}

interface MessageResponse {
  success: boolean;
  message_id?: string;
  conversation_id?: string;
  status?: string;
}

async function sendWhatsAppMessage(
  phoneNumber: string,
  message: string,
  token: string
): Promise<MessageResponse> {
  const response = await fetch(
    "http://localhost:8089/api/whatsapp/send/to-phone",
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        phone_number: phoneNumber,
        message: message,
      }),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to send message");
  }

  return response.json();
}

// Uso
try {
  const result = await sendWhatsAppMessage(
    "+56912345678",
    "Tu Form 29 está listo",
    userToken
  );

  console.log("✅ Message sent:", result.conversation_id);
} catch (error) {
  console.error("❌ Error:", error.message);
}
```

## 🔗 Integración con Sistema de Notificaciones

### Ejemplo: Recordatorio de F29

```python
from app.config.supabase import get_supabase_client
from app.services.whatsapp import WhatsAppService

async def send_f29_reminder(user_phone: str, days_left: int):
    """Enviar recordatorio de F29 por WhatsApp"""

    supabase = get_supabase_client()
    whatsapp = WhatsAppService(supabase)

    message = (
        f"🔔 Recordatorio F29\n\n"
        f"Tu declaración mensual vence en {days_left} días.\n"
        f"Ingresa a la app para revisar los detalles."
    )

    try:
        result = await whatsapp.send_text_to_phone(
            phone_number=user_phone,
            message=message,
        )

        print(f"✅ Reminder sent: {result['conversation_id']}")
        return True

    except ValueError as e:
        print(f"⚠️ No active conversation: {e}")
        # Fallback: enviar template o notificar por otro canal
        return False
```

### Ejemplo: Notificación de Pago Recibido

```python
async def notify_payment_received(
    user_phone: str,
    amount: float,
    reference: str,
):
    """Notificar pago recibido por WhatsApp"""

    supabase = get_supabase_client()
    whatsapp = WhatsAppService(supabase)

    message = (
        f"✅ Pago Recibido\n\n"
        f"Monto: ${amount:,.0f}\n"
        f"Referencia: {reference}\n\n"
        f"Gracias por tu pago!"
    )

    try:
        result = await whatsapp.send_text_to_phone(
            phone_number=user_phone,
            message=message,
        )

        return {"success": True, "conversation_id": result["conversation_id"]}

    except Exception as e:
        return {"success": False, "error": str(e)}
```

## ⚠️ Limitaciones Importantes

### 1. Solo Conversaciones Activas

Este endpoint **NO crea conversaciones nuevas**. Solo envía a conversaciones activas existentes.

**Razón**: WhatsApp Business API tiene reglas estrictas:
- Solo puedes **iniciar** conversaciones con **templates aprobados**
- Mensajes normales solo funcionan dentro de la ventana de 24 horas después de que el usuario envíe un mensaje

### 2. Si No Existe Conversación Activa

Recibirás un error 400:
```json
{
  "detail": "No active conversation found for 56912345678..."
}
```

**Soluciones**:
1. Pedir al usuario que inicie la conversación primero
2. Enviar un template aprobado para iniciar la conversación
3. Usar otro canal de comunicación (email, SMS)

### 3. Ventana de 24 Horas

WhatsApp Business solo permite mensajes normales dentro de las 24 horas después del último mensaje del usuario.

Después de 24 horas, debes usar templates aprobados.

## 🧪 Testing

### Test Manual en Postman

1. **Obtener Token**:
   - Login en `/api/auth/login`
   - Copiar el JWT token

2. **Enviar Mensaje**:
   ```
   POST http://localhost:8089/api/whatsapp/send/to-phone

   Headers:
   - Authorization: Bearer <token>
   - Content-Type: application/json

   Body:
   {
     "phone_number": "+56975389973",
     "message": "Test desde Postman"
   }
   ```

### Test con Script Python

```python
#!/usr/bin/env python3
"""Test script for WhatsApp send-to-phone endpoint"""

import requests
import sys

def test_send_to_phone():
    # Configuración
    BASE_URL = "http://localhost:8089"
    TOKEN = "your-jwt-token"  # Obtener de login
    PHONE = "+56975389973"    # Tu número de prueba

    # Enviar mensaje
    response = requests.post(
        f"{BASE_URL}/api/whatsapp/send/to-phone",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "phone_number": PHONE,
            "message": "🧪 Test desde script Python",
        }
    )

    # Verificar resultado
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS!")
        print(f"   Message ID: {data['message_id']}")
        print(f"   Conversation ID: {data['conversation_id']}")
        print(f"   Status: {data['status']}")
        return 0
    else:
        print("❌ FAILED!")
        print(f"   Status Code: {response.status_code}")
        print(f"   Error: {response.json()}")
        return 1

if __name__ == "__main__":
    sys.exit(test_send_to_phone())
```

## 📊 Comparación con Endpoint Existente

| Característica | `/send/to-phone` (Nuevo) | `/send/text` (Existente) |
|----------------|--------------------------|-------------------------|
| Payload | Más simple | Más complejo |
| Requiere `conversation_id` | ❌ No | ✅ Sí (o phone_number) |
| Busca conversación automáticamente | ✅ Sí | ✅ Sí (si se provee phone) |
| Error si no hay conversación | HTTP 400 | HTTP 200 con `success: false` |
| Uso principal | Scripts, notificaciones | UI, aplicaciones |

## 📚 Documentación Relacionada

- [WHATSAPP_SEND_TO_PHONE_EXAMPLE.md](./WHATSAPP_SEND_TO_PHONE_EXAMPLE.md) - Ejemplos de uso del servicio
- [app/routers/whatsapp/README.md](./app/routers/whatsapp/README.md) - Documentación completa de WhatsApp
- [app/services/whatsapp/service.py](./app/services/whatsapp/service.py) - Implementación del servicio

## 🚀 Próximos Pasos

1. **Templates**: Agregar endpoint para enviar templates aprobados (para iniciar conversaciones)
2. **Webhooks**: Mejorar manejo de eventos de delivery/read
3. **Rate Limiting**: Implementar límites de envío
4. **Retry Logic**: Reintentos automáticos en caso de fallo temporal
