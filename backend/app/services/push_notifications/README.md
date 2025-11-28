# Push Notifications Service

Sistema de notificaciones push para la aplicación móvil Expo de Fizko.

## Descripción

Este servicio maneja el envío de notificaciones push a dispositivos móviles mediante el servicio Expo Push Notifications. Soporta:

- Envío individual a un token específico
- Envío masivo en lotes (batch)
- Envío por usuario ID (busca el token en la BD)
- Envío por lista de usuarios

## Arquitectura

```
┌─────────────────┐
│   Mobile App    │
│  (React Native  │
│   + Expo)       │
└────────┬────────┘
         │ 1. Register push token
         │    (Supabase client updates profiles)
         ↓
┌─────────────────┐
│   Supabase DB   │
│   profiles      │
│  expo_push_token│
└────────┬────────┘
         │ 2. Backend reads token
         │
         ↓
┌─────────────────┐
│  Push Service   │
│  (service.py)   │
└────────┬────────┘
         │ 3. Send via Expo API
         ↓
┌─────────────────┐
│  Expo Push      │
│   Service       │
└────────┬────────┘
         │ 4. Deliver to device
         ↓
┌─────────────────┐
│   Mobile App    │
│  (Notification) │
└─────────────────┘
```

## Instalación

### 1. Migración de Base de Datos

Aplicar la migración para agregar el campo `expo_push_token` a la tabla `profiles`:

```bash
# Ejecutar en Supabase SQL Editor
backend/supabase/migrations/20251128140000_add_expo_push_token_to_profiles.sql
```

### 2. Dependencias

El servicio usa `httpx` para comunicarse con Expo:

```bash
cd backend
uv add httpx
```

### 3. Frontend - Registro de Token

El frontend debe actualizar el token directamente en Supabase:

```typescript
// app/hooks/useSavePushToken.ts
import { useEffect } from 'react';
import { useNotifications } from '@/hooks/useNotifications';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/hooks/useAuth';

export function useSavePushToken() {
  const { expoPushToken } = useNotifications();
  const { user } = useAuth();

  useEffect(() => {
    if (expoPushToken && user) {
      savePushToken(expoPushToken, user.id);
    }
  }, [expoPushToken, user]);
}

async function savePushToken(token: string, userId: string) {
  try {
    const { error } = await supabase
      .from('profiles')
      .update({ expo_push_token: token })
      .eq('id', userId);

    if (error) throw error;
    console.log('[PushToken] Saved to Supabase');
  } catch (error) {
    console.error('[PushToken] Failed to save:', error);
  }
}
```

## Uso

### Envío Individual por Token

```python
from app.services.push_notifications import send_push_notification

result = await send_push_notification(
    expo_push_token="ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
    title="F29 Próximo a Vencer",
    body="Tu F29 vence en 3 días",
    data={
        "type": "f29_reminder",
        "company_id": "uuid",
        "url": "/taxes"
    },
    badge=1
)
```

### Envío por Usuario ID

```python
from app.services.push_notifications import send_push_to_user
from app.config.database import get_db

async with get_db() as db:
    result = await send_push_to_user(
        db=db,
        user_id="user-uuid",
        title="Documento Listo",
        body="Tu factura está lista para ver",
        data={"type": "document_ready", "document_id": "123"}
    )
```

### Envío Masivo (Batch)

```python
from app.services.push_notifications import send_push_to_users
from app.config.database import get_db

async with get_db() as db:
    result = await send_push_to_users(
        db=db,
        user_ids=["uuid1", "uuid2", "uuid3"],
        title="Actualización del Sistema",
        body="Fizko ha sido actualizado con nuevas funcionalidades",
        data={"type": "system_update"}
    )

# Resultado:
# {
#     "sent": 2,
#     "skipped": 1,  # Usuario sin token
#     "errors": []
# }
```

### Uso en Tareas de Celery

```python
from app.infrastructure.celery import celery_app
from app.services.push_notifications import send_push_to_user
from app.config.database import get_db

@celery_app.task
async def send_daily_summary(user_id: str):
    async with get_db() as db:
        await send_push_to_user(
            db=db,
            user_id=user_id,
            title="Resumen Diario",
            body="Tu resumen fiscal está listo",
            data={"type": "daily_summary"}
        )
```

## Parámetros de Notificación

### Campos Básicos

- **title** (str): Título de la notificación
- **body** (str): Cuerpo/mensaje de la notificación
- **data** (dict): Payload JSON accesible en la app cuando se toca la notificación

### Campos Opcionales

- **sound** (str): Sonido a reproducir (`"default"` o `None` para silencioso)
- **badge** (int): Contador de badge en el ícono de la app
- **category_id** (str): ID de categoría para iOS
- **channel_id** (str): ID de canal para Android
- **ttl** (int): Time-to-live en segundos
- **priority** (str): `"default"`, `"normal"`, o `"high"`

## Manejo de Errores

### Excepciones

- **InvalidTokenError**: Token de Expo en formato inválido
- **ExpoServiceError**: Error del servicio de Expo
- **PushNotificationError**: Error general del servicio

### Tokens Inválidos

Cuando un token es inválido (usuario desinstaló la app, token expiró), Expo retorna un error `DeviceNotRegistered`. El servicio lo registra pero no lanza excepción.

**Recomendación**: Implementar limpieza periódica de tokens inválidos:

```python
# Tarea de limpieza (ejecutar mensualmente)
@celery_app.task
async def cleanup_invalid_tokens():
    # Buscar tokens que fallaron con DeviceNotRegistered
    # Limpiar de la base de datos
    pass
```

## Integración con Sistema de Notificaciones

El servicio unificado de notificaciones en [`app/services/notifications/`](../notifications/) integra push notifications con WhatsApp:

```python
from app.services.notifications import send_notification
from app.config.database import get_db

async with get_db() as db:
    await send_notification(
        db=db,
        company_id="uuid",
        channels=["push", "whatsapp"],  # Multicanal
        title="F29 Reminder",
        body="Your F29 is due tomorrow",
        data={"type": "f29_reminder"},
        whatsapp_recipients=["+56912345678"]
    )
```

## Tareas Programadas (Celery Beat)

Las tareas de recordatorio están en [`app/infrastructure/celery/tasks/notifications/`](../../infrastructure/celery/tasks/notifications/):

### Recordatorio F29

```python
from app.infrastructure.celery.tasks.notifications import send_f29_reminders

# Ejecutar diariamente (configurar en Celery Beat)
send_f29_reminders.delay(days_before=3)
```

### Configuración de Celery Beat

Agregar a la configuración de Beat en `app/infrastructure/celery/__init__.py`:

```python
celery_app.conf.beat_schedule = {
    # ... otros schedules ...

    # F29 reminders - 7 days before
    "f29-reminder-7-days": {
        "task": "notifications.send_f29_reminders",
        "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
        "args": (7,),  # 7 days before
    },

    # F29 reminders - 3 days before
    "f29-reminder-3-days": {
        "task": "notifications.send_f29_reminders",
        "schedule": crontab(hour=9, minute=0),
        "args": (3,),
    },

    # F29 reminders - 1 day before
    "f29-reminder-1-day": {
        "task": "notifications.send_f29_reminders",
        "schedule": crontab(hour=9, minute=0),
        "args": (1,),
    },
}
```

## Testing

### Test Manual de Envío

```python
import asyncio
from app.services.push_notifications import send_push_notification

async def test_push():
    result = await send_push_notification(
        expo_push_token="ExponentPushToken[YOUR_TEST_TOKEN]",
        title="Test Notification",
        body="This is a test from backend",
        data={"test": True}
    )
    print(result)

asyncio.run(test_push())
```

### Verificar Token en BD

```sql
-- Ver usuarios con push tokens registrados
SELECT id, email, expo_push_token, created_at
FROM profiles
WHERE expo_push_token IS NOT NULL;
```

## Límites y Consideraciones

### Expo Push Service

- **Límite de batch**: 100 notificaciones por request
- **Rate limiting**: Expo aplica límites por token/proyecto
- **TTL máximo**: 2,419,200 segundos (28 días)

### Performance

- El servicio maneja batching automático para listas > 100 usuarios
- Usa async/await para operaciones no bloqueantes
- Timeout de 10s para requests individuales, 30s para batches

## Troubleshooting

### Token no se guarda en BD

**Problema**: El token no aparece en `profiles.expo_push_token`

**Solución**:
1. Verificar que el frontend esté llamando a `supabase.update()`
2. Verificar RLS policies en Supabase
3. Revisar logs del frontend para errores

### Notificación no llega al dispositivo

**Problema**: El servicio reporta éxito pero la notificación no aparece

**Posibles causas**:
1. Token inválido/expirado
2. Permisos de notificación deshabilitados en el dispositivo
3. App en background killing (Android)
4. Notificaciones silenciosas (badge/data-only)

**Debug**:
```python
# Verificar que el token sea válido
result = await send_push_notification(
    expo_push_token=token,
    title="Test",
    body="Test notification",
    sound="default"  # Asegurar que no sea silencioso
)

# Revisar respuesta de Expo
print(result)
```

## Referencias

- [Expo Push Notifications Docs](https://docs.expo.dev/push-notifications/overview/)
- [Expo Push API Reference](https://docs.expo.dev/push-notifications/sending-notifications/)
- [Push Notification Tool (Testing)](https://expo.dev/notifications)
