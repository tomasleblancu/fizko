# WhatsApp: Enviar Mensaje a Número de Teléfono

## Nuevo Método: `send_text_to_phone()`

Se agregó un método conveniente para enviar mensajes directamente a un número de teléfono sin necesidad de conocer el `conversation_id`.

## Uso Básico

```python
from app.config.supabase import get_supabase_client
from app.services.whatsapp import WhatsAppService

# Inicializar servicio
supabase = get_supabase_client()
whatsapp_service = WhatsAppService(supabase)

# Enviar mensaje a un número
try:
    result = await whatsapp_service.send_text_to_phone(
        phone_number="+56912345678",  # Con o sin prefijo '+'
        message="¡Hola! Tu Form 29 está listo.",
    )
    print(f"✅ Mensaje enviado a conversación: {result['conversation_id']}")

except ValueError as e:
    print(f"❌ Error: {e}")
    # "No active conversation found for 56912345678.
    #  The user must first initiate a conversation..."
```

## Uso con `whatsapp_config_id`

Si tienes múltiples números de WhatsApp Business, puedes filtrar por configuración:

```python
result = await whatsapp_service.send_text_to_phone(
    phone_number="+56912345678",
    message="Tu pago fue recibido",
    whatsapp_config_id="config_abc123",  # Filtrar por este número de negocio
)
```

## Alternativa: Usar `send_text()` Directamente

El método `send_text()` también fue actualizado para aceptar `phone_number`:

```python
# Método 1: Con conversation_id (si lo conoces)
await whatsapp_service.send_text(
    conversation_id="conv_xyz789",
    message="Hola"
)

# Método 2: Con phone_number (busca automáticamente)
await whatsapp_service.send_text(
    phone_number="+56912345678",
    message="Hola",
    whatsapp_config_id="config_abc123"  # Opcional
)
```

## ⚠️ Limitaciones Importantes

### 1. Solo Conversaciones Activas

Este método **NO crea conversaciones nuevas**. Solo busca conversaciones activas existentes.

**¿Por qué?** WhatsApp Business API tiene reglas estrictas:
- Solo puedes **iniciar** conversaciones con **templates aprobados**
- Mensajes normales solo funcionan dentro de la ventana de 24 horas después de que el usuario envíe un mensaje

### 2. Si No Existe Conversación Activa

Si el usuario no ha escrito recientemente, obtendrás este error:

```python
ValueError: No active conversation found for 56912345678.
The user must first initiate a conversation by sending a message,
or you must send an approved WhatsApp template to start the conversation.
```

**Solución**: Enviar un template aprobado primero:

```python
# TODO: Implementar send_template() en el servicio actual
# await whatsapp_service.send_template(
#     phone_number="56912345678",
#     template_name="f29_reminder",
#     ...
# )
```

## Integración con Sistema de Notificaciones

Ejemplo de uso en el sistema de notificaciones:

```python
from app.services.notifications import NotificationService
from app.services.whatsapp import WhatsAppService

async def send_f29_reminder(company_id: str, user_phone: str):
    """Enviar recordatorio de F29 por WhatsApp"""

    whatsapp_service = WhatsAppService(supabase)

    try:
        result = await whatsapp_service.send_text_to_phone(
            phone_number=user_phone,
            message=(
                "🔔 Recordatorio F29\n\n"
                "Tu declaración mensual vence en 3 días.\n"
                "Ingresa a la app para revisar los detalles."
            )
        )

        logger.info(f"✅ Reminder sent to {user_phone}: {result['conversation_id']}")
        return result

    except ValueError as e:
        logger.warning(f"⚠️ Cannot send to {user_phone}: {e}")
        # Fallback: enviar template o notificar por otro canal
        return None
```

## Testing

Probar el nuevo método:

```python
# Test en consola interactiva
import asyncio
from app.config.supabase import get_supabase_client
from app.services.whatsapp import WhatsAppService

async def test_send_to_phone():
    supabase = get_supabase_client()
    service = WhatsAppService(supabase)

    # Asegúrate de que este número tenga una conversación activa
    result = await service.send_text_to_phone(
        phone_number="+56975389973",  # Tu número de prueba
        message="Test desde backend actualizado"
    )

    print(f"Success! Conversation ID: {result['conversation_id']}")

# Ejecutar
asyncio.run(test_send_to_phone())
```

## Cambios Realizados

### Archivo: `backend/app/services/whatsapp/service.py`

1. **Actualizado `send_text()`**:
   - Ahora acepta `phone_number` como parámetro opcional
   - Busca automáticamente conversación activa si no se provee `conversation_id`
   - Lanza error claro si no se encuentra conversación

2. **Nuevo método `send_text_to_phone()`**:
   - Wrapper conveniente sobre `send_text()`
   - Signatura más clara para enviar directamente a número

3. **Nuevo método privado `_find_active_conversation()`**:
   - Busca conversaciones activas por número de teléfono
   - Normaliza números automáticamente (maneja `+` prefix)
   - Soporta filtrado por `whatsapp_config_id`
   - Lanza error descriptivo si no encuentra conversación

## Migración desde Código Antiguo

Si estabas usando el código del directorio `old-directories`:

```python
# Antiguo (old-directories)
service = WhatsAppService(api_token="...")
result = await service.send_text(
    phone_number="+56912345678",
    message="Hola",
    whatsapp_config_id="config_123"
)

# Nuevo (actual)
service = WhatsAppService(supabase_client)
result = await service.send_text_to_phone(
    phone_number="+56912345678",
    message="Hola",
    whatsapp_config_id="config_123"
)
```

La funcionalidad es idéntica, solo cambió la inicialización del servicio.
