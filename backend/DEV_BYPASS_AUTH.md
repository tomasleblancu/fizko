# ⚠️ BYPASS TEMPORAL DE AUTENTICACIÓN - ~~SOLO DESARROLLO~~ ⚠️

## ✅ Estado Actual: REMOVIDO

**Fecha de Actualización:** 2025-11-25

**BYPASS YA NO ESTÁ ACTIVO** - El sistema ahora usa el template real de WhatsApp.

Ver [PHONE_AUTH_SETUP_COMPLETE.md](../PHONE_AUTH_SETUP_COMPLETE.md) para detalles de la implementación actual.

---

## ~~Estado Anterior~~ (OBSOLETO)

El sistema de autenticación por WhatsApp ~~está usando~~ **USABA** un **BYPASS TEMPORAL** para desarrollo.

## ¿Qué hace el bypass?

**TODOS** los códigos de verificación se envían al número de prueba:

```
56975389973
```

No importa qué número de teléfono solicite el código, **SIEMPRE** se enviará al número de prueba arriba.

## ¿Por qué?

WhatsApp Business API requiere templates pre-aprobados para enviar mensajes a usuarios que no han iniciado conversación. Mientras esperamos la aprobación del template, usamos este bypass para poder desarrollar y probar.

## Cómo funciona

1. Usuario solicita código con **cualquier** número (ej: +56912345678)
2. El código se genera y guarda en la BD asociado a ese número
3. **PERO** el mensaje de WhatsApp se envía **SIEMPRE** a 56975389973
4. El mensaje incluye:
   - El código de verificación
   - El número del usuario solicitante
   - Advertencia clara de que es un bypass de desarrollo

## Ejemplo de mensaje recibido

```
⚠️  [DEV BYPASS - TEST ONLY] ⚠️

🔐 Código de Verificación Fizko

👤 Usuario solicitante: +56912345678
🔑 Código: 123456

⏰ Expira en 5 minutos

Este es un mensaje de desarrollo. En producción,
el código se enviará al usuario real.
```

## Requisito

**DEBE existir una conversación activa** con el número 56975389973 antes de solicitar códigos. Si no existe, se recibirá el error:

```
No active conversation found with test number 56975389973.
Please send a message to the bot first.
```

**Solución**: Envía cualquier mensaje al bot de WhatsApp desde el número 56975389973.

## Testing

### 1. Solicitar código (con cualquier número)

```bash
curl -X POST http://localhost:8000/api/auth/phone/request-code \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+56912345678"
  }'
```

### 2. Verificar en WhatsApp

Revisa el WhatsApp del número **56975389973** - ahí llegará el código.

### 3. Verificar código (con el MISMO número que solicitaste)

```bash
curl -X POST http://localhost:8000/api/auth/phone/verify-code \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+56912345678",
    "code": "123456"
  }'
```

**IMPORTANTE**: El código está asociado al número solicitante, NO al número receptor. Debes verificar con el mismo número que usaste en el request-code.

## Logs

El servidor mostrará warnings claros:

```
⚠️  USING DEVELOPMENT BYPASS: Sending code to 56975389973 instead of +56912345678
⚠️  [DEV BYPASS] Verification code sent to TEST NUMBER 56975389973 for user +56912345678. CODE: 123456
```

## Remover el Bypass (CUANDO TEMPLATE ESTÉ APROBADO)

### 1. Reemplazar código en phone_auth_service.py

Buscar las líneas 119-176 y reemplazar todo el bloque con:

```python
logger.info(f"Verification code generated for {phone_number}")

# Send code via WhatsApp template
try:
    await self.kapso.messages.send_template(
        phone_number=phone_number,
        template_name=self.verification_template_name,
        template_params=[code],
        template_language=self.verification_template_language,
    )
    logger.info(f"✅ Verification code sent to {phone_number} via WhatsApp template")

except Exception as e:
    logger.error(f"Failed to send verification code via WhatsApp: {e}")
    # Delete the code from database if send fails
    self.supabase.table("phone_verification_codes").delete().eq(
        "id", verification_record.data[0]["id"]
    ).execute()
    raise ValueError(
        f"No se pudo enviar el código por WhatsApp. Error: {str(e)}"
    )
```

### 2. Configurar template

Ver [WHATSAPP_TEMPLATE_SETUP.md](WHATSAPP_TEMPLATE_SETUP.md)

### 3. Eliminar este archivo

```bash
rm backend/DEV_BYPASS_AUTH.md
```

## ⚠️ NUNCA DEPLOY A PRODUCCIÓN CON ESTE BYPASS ⚠️

Este bypass es **SOLO PARA DESARROLLO LOCAL**. Antes de deployar a producción:

- [ ] Template de WhatsApp aprobado
- [ ] Código del bypass removido
- [ ] Template implementation restaurado
- [ ] Testing con números reales
- [ ] Este archivo DEV_BYPASS_AUTH.md eliminado
