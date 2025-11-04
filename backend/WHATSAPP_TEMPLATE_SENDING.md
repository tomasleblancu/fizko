# WhatsApp Template Sending

## Overview

Este documento explica cómo enviar mensajes usando templates de WhatsApp que ya están creados y aprobados en Meta Business Manager.

**IMPORTANTE:** Los templates deben ser creados manualmente en Meta Business Manager. Este sistema solo los **envía**, no los crea.

## Crear Template en Meta

1. Ve a Meta Business Manager → WhatsApp → Message Templates
2. Crea un nuevo template (ej: `daily_business_summary_v2`)
3. Define el contenido con variables (ej: `{{day_name}}`, `{{sales_count}}`)
4. Envía para aprobación
5. Espera aprobación de Meta (puede tomar 24-48 horas)
6. Copia el **nombre del template** (no el ID de Meta, sino el nombre que le diste)

## Guardar Template ID en Fizko

En el formulario de Notification Templates, ingresa el nombre del template en el campo **WhatsApp Template ID**:

```
whatsapp_template_id: "daily_business_summary_v2"
```

Este es el nombre que usaste en Meta, NO el ID numérico.

## Enviar Template via API

### Método 1: Usando KapsoClient directamente

```python
from app.integrations.kapso import KapsoClient
import os

kapso_client = KapsoClient(api_token=os.getenv("KAPSO_API_TOKEN"))

# Enviar template sin variables
result = await kapso_client.send_whatsapp_template(
    phone_number_id="647015955153740",  # Tu WhatsApp Business Phone Number ID
    to="56912345678",  # Número destino (sin +)
    template_name="daily_business_summary_v2",
    language_code="es"
)

# Enviar template con variables en header y body
result = await kapso_client.send_whatsapp_template(
    phone_number_id="647015955153740",
    to="56912345678",
    template_name="daily_business_summary_v2",
    language_code="es",
    header_params=[
        {"type": "text", "text": "Lunes"}  # {{day_name}}
    ],
    body_params=[
        {"type": "text", "text": "5"},          # {{sales_count}}
        {"type": "text", "text": "$1,500,000"}, # {{sales_total_formatted}}
        {"type": "text", "text": "3"},          # {{purchases_count}}
        {"type": "text", "text": "$800,000"},   # {{purchases_total_formatted}}
    ]
)
```

### Método 2: Desde el sistema de notificaciones

El sistema de notificaciones puede usar templates de WhatsApp automáticamente si:

1. El `NotificationTemplate` tiene `whatsapp_template_id` configurado
2. El servicio de envío detecta este campo y usa el template en lugar de mensaje de texto

**Ejemplo en el servicio de notificaciones:**

```python
# En send_instant_notification o similar
template = await get_template(db, template_code="daily_business_summary")

if template.whatsapp_template_id:
    # Usar template de WhatsApp
    kapso_client = KapsoClient(api_token=os.getenv("KAPSO_API_TOKEN"))

    # Renderizar variables del template
    variables = extract_variables_from_message(template.message_template, context)

    # Mapear a parámetros de WhatsApp
    header_params, body_params = map_variables_to_whatsapp_params(
        template.whatsapp_template_id,
        variables
    )

    await kapso_client.send_whatsapp_template(
        phone_number_id=phone_number_id,
        to=phone_number,
        template_name=template.whatsapp_template_id,
        language_code="es",
        header_params=header_params,
        body_params=body_params
    )
else:
    # Usar mensaje de texto normal
    await kapso_client.send_text_message(...)
```

## Formato de Parámetros

### Header Parameters

Si tu template tiene un header con variables:

```
Header: "📊 Tu resumen del día {{day_name}}"
```

Parámetros:
```python
header_params=[
    {"type": "text", "text": "Lunes"}
]
```

### Body Parameters

Si tu template tiene body con variables:

```
Body: "🛒 *Ventas*: {{sales_count}} documentos por ${{sales_total}}"
```

Parámetros (en orden de aparición):
```python
body_params=[
    {"type": "text", "text": "5"},
    {"type": "text", "text": "$1,500,000"}
]
```

**IMPORTANTE:** Los parámetros deben ir en el mismo orden que aparecen en el template.

## Variables Especiales

### Template con imágenes en header

Si el template tiene una imagen en el header:

```python
header_params=[
    {
        "type": "image",
        "image": {
            "link": "https://example.com/image.jpg"
        }
    }
]
```

### Template con documentos

```python
header_params=[
    {
        "type": "document",
        "document": {
            "link": "https://example.com/report.pdf",
            "filename": "Reporte_Diario.pdf"
        }
    }
]
```

## Configuración de Environment

Asegúrate de tener estas variables en `.env`:

```bash
KAPSO_API_TOKEN=your_kapso_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_waba_id
WHATSAPP_PHONE_NUMBER_ID=647015955153740
```

## Testing

Para probar el envío de templates:

```bash
# Desde el backend
cd backend
.venv/bin/python

# En el REPL
import asyncio
from app.integrations.kapso import KapsoClient
import os

async def test():
    client = KapsoClient(api_token=os.getenv("KAPSO_API_TOKEN"))
    result = await client.send_whatsapp_template(
        phone_number_id="647015955153740",
        to="56912345678",  # Tu número de prueba
        template_name="daily_business_summary_v2",
        language_code="es"
    )
    print(result)

asyncio.run(test())
```

## Errores Comunes

### Error: Template not found
- Verifica que el nombre del template sea exacto (case-sensitive)
- Asegúrate de que el template esté aprobado en Meta
- Verifica que el template exista para el idioma especificado

### Error: Invalid parameters
- Los parámetros deben estar en el orden correcto
- El número de parámetros debe coincidir con las variables del template
- Los tipos deben ser correctos (text, image, document, etc.)

### Error: Phone number not registered
- El número destino debe haber iniciado conversación contigo primero
- O debes usar un template pre-aprobado para iniciar conversaciones

## Logs

Los logs del envío de templates aparecen como:

```
📤 Sending WhatsApp template message:
  - Phone Number ID: 647015955153740
  - To: 56912345678
  - Template: daily_business_summary_v2
  - Language: es
  - Payload: {...}
📬 Template sent successfully. Status: 200
✅ Message ID: wamid.HBgNNTY5MTIzNDU2NzgVAgARGBI5...
```

## Próximos Pasos

1. **Crear templates en Meta** para diferentes tipos de notificaciones
2. **Configurar templates en Fizko** usando el campo `whatsapp_template_id`
3. **Integrar el envío** en el servicio de notificaciones existente
4. **Mapear variables** del sistema a parámetros de WhatsApp

## Referencias

- [Kapso API Docs](https://docs.kapso.ai)
- [Meta WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates)
