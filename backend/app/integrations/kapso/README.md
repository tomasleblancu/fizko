# Kapso WhatsApp Business Integration

Integración con la API de Kapso para gestionar comunicaciones de WhatsApp Business en Fizko.

## Configuración

### Variables de Entorno

Añade estas variables a tu archivo `.env`:

```bash
# Kapso WhatsApp API
KAPSO_API_TOKEN=your-kapso-api-token-here
KAPSO_API_BASE_URL=https://app.kapso.ai/api/v1
KAPSO_WEBHOOK_SECRET=your-webhook-secret-here
```

## Estructura

```
app/integrations/kapso/
├── __init__.py          # Exports públicos
├── client.py            # Cliente HTTP de Kapso (async con httpx)
├── models.py            # Modelos Pydantic para requests/responses
├── exceptions.py        # Excepciones personalizadas
└── README.md           # Este archivo

app/services/whatsapp/
├── __init__.py
└── service.py          # Capa de servicio de alto nivel

app/routers/
└── whatsapp.py         # Endpoints FastAPI
```

## Uso

### 1. Cliente de bajo nivel (KapsoClient)

```python
from app.integrations.kapso import KapsoClient

# Inicializar cliente
client = KapsoClient(api_token="your-token")

# Enviar mensaje de texto
result = await client.send_text_message(
    conversation_id="conv-123",
    message="Hola, ¿cómo estás?"
)

# Enviar plantilla
result = await client.send_template_message(
    phone_number="+56912345678",
    template_name="welcome_message",
    template_params=["Juan"],
    whatsapp_config_id="config-123"
)

# Enviar media
result = await client.send_media_message(
    conversation_id="conv-123",
    media_url="https://example.com/image.jpg",
    media_type=MessageType.IMAGE,
    caption="Mira esta imagen"
)
```

### 2. Servicio de alto nivel (WhatsAppService)

```python
from app.services.whatsapp import WhatsAppService

# Inicializar servicio
service = WhatsAppService(api_token="your-token")

# Enviar texto (encuentra/crea conversación automáticamente)
result = await service.send_text(
    phone_number="+56912345678",
    message="Hola",
    whatsapp_config_id="config-123"
)

# Obtener historial de contacto
history = await service.get_contact_history(
    identifier="+56912345678",
    message_limit=20
)

# Listar conversaciones
conversations = await service.list_conversations(
    whatsapp_config_id="config-123",
    limit=50
)
```

### 3. API REST (FastAPI endpoints)

#### Enviar mensaje de texto

```bash
POST /api/whatsapp/send/text
Authorization: Bearer <jwt-token>

{
  "conversation_selector": {
    "conversation_id": "conv-123"
  },
  "content": "Hola, ¿cómo estás?"
}
```

#### Enviar plantilla

```bash
POST /api/whatsapp/send/template
Authorization: Bearer <jwt-token>

{
  "conversation_selector": {
    "phone_number": "+56912345678"
  },
  "template_name": "welcome_message",
  "template_params": ["Juan"],
  "whatsapp_config_id": "config-123"
}
```

#### Enviar media

```bash
POST /api/whatsapp/send/media
Authorization: Bearer <jwt-token>

{
  "conversation_selector": {
    "conversation_id": "conv-123"
  },
  "message_type": "image",
  "file_url": "https://example.com/image.jpg",
  "caption": "Mira esta imagen"
}
```

#### Listar conversaciones

```bash
GET /api/whatsapp/conversations?limit=50
Authorization: Bearer <jwt-token>
```

#### Buscar contactos

```bash
GET /api/whatsapp/contacts/search?query=Juan
Authorization: Bearer <jwt-token>
```

#### Ver bandeja de entrada

```bash
GET /api/whatsapp/inbox?whatsapp_config_id=config-123
Authorization: Bearer <jwt-token>
```

## Webhooks

El endpoint `/api/whatsapp/webhook` está configurado para recibir eventos de Kapso:

```bash
POST /api/whatsapp/webhook
X-Kapso-Signature: <hmac-sha256-signature>

{
  "event_type": "message.received",
  "conversation_id": "conv-123",
  "message_id": "msg-456",
  "payload": { ... }
}
```

Los webhooks se validan usando HMAC-SHA256 con el `KAPSO_WEBHOOK_SECRET`.

## Tipos de Mensajes Soportados

- **text**: Mensajes de texto simple
- **image**: Imágenes (JPEG, PNG)
- **video**: Videos (MP4, 3GP)
- **audio**: Audio (AAC, MP3, OGG)
- **document**: Documentos (PDF, DOC, XLS, etc.)
- **template**: Plantillas aprobadas de WhatsApp Business
- **interactive**: Mensajes con botones o listas

## Modelos de Datos

### MessageType (Enum)
- TEXT
- IMAGE
- VIDEO
- AUDIO
- DOCUMENT
- TEMPLATE
- INTERACTIVE

### ConversationStatus (Enum)
- ACTIVE
- ENDED

### SendTextRequest
```python
{
  "conversation_selector": {
    "conversation_id": "conv-123",  # O phone_number
    "phone_number": "+56912345678"
  },
  "content": "Mensaje de texto",
  "whatsapp_config_id": "config-123"  # Opcional
}
```

### SendTemplateRequest
```python
{
  "conversation_selector": {
    "phone_number": "+56912345678"
  },
  "template_name": "welcome_message",
  "template_language": "es",
  "template_params": ["Juan", "Pérez"],  # Lista o dict
  "whatsapp_config_id": "config-123"
}
```

## Excepciones

- `KapsoAPIError`: Error genérico de la API
- `KapsoAuthenticationError`: Error de autenticación (401)
- `KapsoValidationError`: Error de validación (422)
- `KapsoTimeoutError`: Timeout en la petición
- `KapsoNotFoundError`: Recurso no encontrado (404)

## Testing

```python
# Health check
result = await service.health_check()
# {"status": "healthy", "response_time": 0.123}
```

## Endpoints Disponibles

### Mensajes
- `POST /api/whatsapp/send/text` - Enviar texto
- `POST /api/whatsapp/send/media` - Enviar media
- `POST /api/whatsapp/send/template` - Enviar plantilla
- `POST /api/whatsapp/send/interactive` - Enviar mensaje interactivo
- `GET /api/whatsapp/messages/search` - Buscar mensajes
- `POST /api/whatsapp/messages/mark-read` - Marcar como leído

### Conversaciones
- `GET /api/whatsapp/conversations` - Listar conversaciones
- `GET /api/whatsapp/conversations/{id}` - Ver conversación
- `POST /api/whatsapp/conversations/{id}/end` - Finalizar conversación

### Contactos
- `GET /api/whatsapp/contacts/search` - Buscar contactos
- `GET /api/whatsapp/contacts/{id}/history` - Ver historial
- `POST /api/whatsapp/contacts/{id}/note` - Añadir nota

### Otros
- `GET /api/whatsapp/templates` - Listar plantillas disponibles
- `GET /api/whatsapp/inbox` - Ver bandeja de entrada
- `POST /api/whatsapp/webhook` - Recibir webhooks de Kapso
- `GET /api/whatsapp/health` - Health check

## Flujo de Trabajo Recomendado

### Para iniciar una conversación nueva:
1. Usar `send_template` con el número de teléfono
2. Guardar el `conversation_id` retornado
3. Usar `send_text` o `send_interactive` para mensajes subsiguientes

### Para responder a un contacto existente:
1. Buscar el contacto con `search_contacts`
2. Obtener el historial con `get_contact_history`
3. Enviar respuesta con `send_text` usando el `conversation_id`

### Para gestionar la bandeja de entrada:
1. Obtener conversaciones con `get_inbox`
2. Procesar mensajes entrantes desde el webhook
3. Marcar como leído con `mark_messages_as_read`
4. Finalizar conversaciones cerradas con `end_conversation`

## Referencias

- [Documentación de Kapso API](https://app.kapso.ai/api/docs)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
