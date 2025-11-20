# WhatsApp Integration

Integración de WhatsApp para Fizko usando Kapso WhatsApp Business API.

## Arquitectura

La integración sigue una arquitectura modular en 3 capas:

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Routes Layer                      │
│  (JWT Auth for REST endpoints, HMAC for webhooks)           │
├─────────────────────────────────────────────────────────────┤
│  ├─ /api/whatsapp/send/*        (messaging.py)              │
│  └─ /api/whatsapp/webhook       (webhooks.py)               │
├─────────────────────────────────────────────────────────────┤
│              WhatsApp Service Layer (Business Logic)         │
│  ├─ WhatsAppService (high-level wrapper)                    │
│  ├─ WhatsAppConversationManager (message/conversation state)│
│  └─ authenticate_user_by_whatsapp (phone-based auth)        │
├─────────────────────────────────────────────────────────────┤
│            Kapso Integration Layer (Modular Client)          │
│  ├─ KapsoClient (main orchestrator)                         │
│  ├─ MessagesAPI (send text, media, interactive)             │
│  ├─ ConversationsAPI (list, get, update status)             │
│  ├─ ContactsAPI (search, history, notes)                    │
│  ├─ TemplatesAPI (template operations)                      │
│  └─ WebhooksAPI (HMAC validation)                           │
└─────────────────────────────────────────────────────────────┘
```

## Estructura de Archivos

```
backend/app/
├── integrations/kapso/          # Cliente de Kapso API
│   ├── __init__.py
│   ├── client.py                # KapsoClient principal
│   ├── models.py                # Modelos Pydantic
│   ├── exceptions.py            # Excepciones personalizadas
│   └── api/                     # Módulos de API por dominio
│       ├── base.py              # BaseAPI con HTTP común
│       ├── messages.py          # MessagesAPI
│       ├── conversations.py     # ConversationsAPI
│       ├── contacts.py          # ContactsAPI
│       ├── templates.py         # TemplatesAPI
│       └── webhooks.py          # WebhooksAPI (HMAC validation)
│
├── repositories/
│   └── whatsapp.py              # WhatsAppRepository (DB operations)
│
├── services/whatsapp/           # Servicios de WhatsApp
│   ├── __init__.py
│   ├── auth.py                  # Autenticación por teléfono
│   ├── conversation_manager.py  # Gestión de conversaciones
│   └── service.py               # WhatsAppService (wrapper principal)
│
└── routers/whatsapp/            # Routes de WhatsApp
    ├── __init__.py
    ├── main.py                  # Router principal
    ├── schemas.py               # Esquemas de respuesta
    └── routes/
        ├── messaging.py         # Envío de mensajes
        └── webhooks.py          # Procesamiento de webhooks
```

## Variables de Entorno

Agregar a `.env`:

```bash
# Kapso WhatsApp Integration
KAPSO_API_KEY=sk_...                    # API key de Kapso
KAPSO_PROJECT_ID=proj_...               # ID del proyecto Kapso
KAPSO_WEBHOOK_SECRET=whsec_...          # Secret para HMAC validation

# Supabase (ya existentes)
SUPABASE_URL=https://....supabase.co
SUPABASE_ANON_KEY=...
```

## Endpoints

### Webhook (sin autenticación JWT)

**POST `/api/whatsapp/webhook`**

Recibe mensajes entrantes de Kapso. Validación HMAC obligatoria en producción.

Headers:
- `X-Webhook-Signature`: Firma HMAC-SHA256
- `X-Webhook-Batch`: "true" si es batch

### Mensajería (requiere JWT)

**POST `/api/whatsapp/send/text`**

Envía mensaje de texto.

```json
{
  "conversation_selector": {
    "conversation_id": "conv_xxx",
    "phone_number": "+56912345678"
  },
  "content": "Hola!",
  "whatsapp_config_id": null
}
```

**POST `/api/whatsapp/send/media`**

Envía imagen, video, audio o documento.

```json
{
  "conversation_selector": {
    "conversation_id": "conv_xxx"
  },
  "file_url": "https://example.com/image.jpg",
  "message_type": "image",
  "caption": "Mira esto"
}
```

**POST `/api/whatsapp/send/interactive`**

Envía mensaje interactivo (botones o lista).

```json
{
  "conversation_selector": {
    "conversation_id": "conv_xxx"
  },
  "interactive_type": "button",
  "body_text": "¿Qué deseas hacer?",
  "buttons": [
    {"id": "opt1", "title": "Opción 1"},
    {"id": "opt2", "title": "Opción 2"}
  ]
}
```

## Flujo de Webhook

1. **Validación HMAC**: Verifica firma `X-Webhook-Signature`
2. **Extracción de datos**: Soporta formatos V1 y V2 de Kapso
3. **Autenticación**: Busca usuario por número de teléfono en `profiles.phone`
4. **Procesamiento**:
   - Usuario encontrado: Procesa mensaje y envía respuesta
   - Usuario no encontrado: Envía mensaje de registro
5. **Respuesta asíncrona**: No bloquea el webhook

## Autenticación por Teléfono

Los usuarios se autentican por su número de WhatsApp:

```python
from app.services.whatsapp import authenticate_user_by_whatsapp

user_id = await authenticate_user_by_whatsapp(supabase, "+56912345678")
```

El número se normaliza automáticamente con prefijo `+`.

## Gestión de Conversaciones

Las conversaciones de WhatsApp usan las mismas tablas que ChatKit (`conversations`, `messages`) pero se distinguen por metadata:

```json
{
  "channel": "whatsapp",
  "created_via": "whatsapp_webhook",
  "user_id": "uuid...",
  "company_id": "uuid...",
  "phone_number": "+56912345678"
}
```

**Optimización**: Se cachea `user_id` y `company_id` en metadata para evitar queries repetidas.

## Uso del Cliente Kapso

```python
from app.integrations.kapso import KapsoClient

client = KapsoClient(api_token="your_token")

# Enviar texto
await client.messages.send_text(
    conversation_id="conv_123",
    message="Hola!"
)

# Enviar media
await client.messages.send_media(
    conversation_id="conv_123",
    media_url="https://example.com/image.jpg",
    media_type=MessageType.IMAGE,
    caption="Mira esto"
)

# Buscar conversaciones
conversations = await client.conversations.search(
    query="John",
    status="active"
)

# Buscar contactos
contacts = await client.contacts.search(query="+569")
```

## Manejo de Errores

Excepciones personalizadas de Kapso:

- `KapsoAPIError`: Error general de API
- `KapsoAuthenticationError`: Token inválido (401)
- `KapsoNotFoundError`: Recurso no encontrado (404)
- `KapsoValidationError`: Error de validación (422)
- `KapsoTimeoutError`: Timeout de request

```python
try:
    await service.send_text(conversation_id, "Hola")
except KapsoAuthenticationError:
    # Token inválido
    pass
except KapsoNotFoundError:
    # Conversación no existe
    pass
except KapsoAPIError as e:
    # Otro error de API
    logger.error(f"Error: {e.message}, status: {e.status_code}")
```

## Testing

Para probar localmente:

1. Instalar dependencias:
   ```bash
   cd backend
   uv sync
   ```

2. Configurar `.env` con credenciales de Kapso

3. Iniciar servidor:
   ```bash
   ./dev.sh
   ```

4. Probar endpoint de webhook (ejemplo con curl):
   ```bash
   curl -X POST http://localhost:8089/api/whatsapp/webhook \
     -H "Content-Type: application/json" \
     -H "X-Webhook-Signature: dummy" \
     -H "X-Webhook-Batch: false" \
     -d '{...webhook payload...}'
   ```

## Próximos Pasos

- [ ] Integrar con sistema de agentes AI
- [ ] Implementar media processor para adjuntos
- [ ] Agregar soporte para templates de WhatsApp
- [ ] Implementar rate limiting
- [ ] Agregar métricas y monitoreo

## Referencias

- [Documentación Kapso API](https://docs.kapso.ai)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- CLAUDE.md: Guía principal del proyecto
