# 📱 Push Notifications Setup - Fizko Mobile App

Sistema completo de notificaciones push para la aplicación móvil Expo de Fizko.

## 📋 Resumen de Implementación

### ✅ Archivos Creados

#### 1. Migración de Base de Datos
- **`backend/supabase/migrations/20251128140000_add_expo_push_token_to_profiles.sql`**
  - Agrega columna `expo_push_token` a tabla `profiles`
  - Incluye índice para búsquedas eficientes

#### 2. Servicio de Push Notifications
- **`backend/app/services/push_notifications/service.py`**
  - `send_push_notification()` - Envío individual por token
  - `send_push_notifications_batch()` - Envío masivo (hasta 100/batch)
  - `send_push_to_user()` - Envío por user_id (busca token en BD)
  - `send_push_to_users()` - Envío a múltiples usuarios
  - Manejo completo de errores y validación de tokens Expo

- **`backend/app/services/push_notifications/__init__.py`**
- **`backend/app/services/push_notifications/README.md`** - Documentación completa

#### 3. Servicio de Notificaciones Unificado
- **`backend/app/services/notifications/service.py`**
  - `send_push_notification_to_user()` - Wrapper simplificado
  - `send_push_notification_to_company()` - Envío a todos los usuarios de una empresa
  - `send_notification()` - Multicanal (push + WhatsApp)

- **`backend/app/services/notifications/__init__.py`**

#### 4. Tareas de Celery para Recordatorios
- **`backend/app/infrastructure/celery/tasks/notifications/reminders.py`**
  - `send_f29_reminders()` - Recordatorios automáticos para todas las empresas
  - `send_f29_reminder_for_company()` - Recordatorio para empresa específica
  - Cálculo automático de fechas de vencimiento F29

- **`backend/app/infrastructure/celery/tasks/notifications/__init__.py`**
- Actualizado **`backend/app/infrastructure/celery/tasks/__init__.py`** para registrar tareas

#### 5. Documentación
- **`PUSH_NOTIFICATIONS_SETUP.md`** (este archivo)

### ❌ Archivos Descartados
- `backend/app/routers/auth/profile.py` - No necesario, el frontend actualiza el token directamente en Supabase

---

## 🚀 Instalación y Configuración

### 1. Aplicar Migración a Supabase

```bash
# En Supabase SQL Editor, ejecutar:
backend/supabase/migrations/20251128140000_add_expo_push_token_to_profiles.sql
```

O si usas Supabase CLI:
```bash
cd backend
supabase migration up
```

### 2. Instalar Dependencias del Backend

```bash
cd backend
uv add httpx  # Si no está instalado
```

### 3. Configurar el Frontend (React Native + Expo)

El frontend debe actualizar el token directamente en Supabase cuando se obtenga:

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
    console.log('[PushToken] ✅ Saved to Supabase');
  } catch (error) {
    console.error('[PushToken] ❌ Failed to save:', error);
  }
}
```

**Usar en el layout principal:**

```typescript
// app/_layout.tsx
import { useSavePushToken } from '@/hooks/useSavePushToken';

function RootLayoutNav() {
  const { user } = useAuth();

  // Guardar push token cuando el usuario esté autenticado
  useSavePushToken();

  // ... resto del código
}
```

### 4. Configurar Celery Beat (Recordatorios Programados)

Agregar a `backend/app/infrastructure/celery/__init__.py`:

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # ... otros schedules existentes ...

    # F29 reminders - 7 days before (9 AM daily)
    "f29-reminder-7-days": {
        "task": "notifications.send_f29_reminders",
        "schedule": crontab(hour=9, minute=0),
        "args": (7,),
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

---

## 💻 Uso del Sistema

### Envío Manual de Notificaciones

#### A un usuario específico

```python
from app.services.push_notifications import send_push_to_user

result = await send_push_to_user(
    user_id="user-uuid",
    title="F29 Reminder",
    body="Tu F29 vence en 3 días",
    data={"type": "f29_reminder", "url": "/taxes"},
    badge=1
)
```

#### A toda una empresa

```python
from app.services.notifications import send_push_notification_to_company

result = await send_push_notification_to_company(
    company_id="company-uuid",
    title="Documentos Sincronizados",
    body="Tus documentos del SII han sido actualizados",
    data={"type": "sii_sync"}
)
```

#### Multicanal (Push + WhatsApp)

```python
from app.services.notifications import send_notification

result = await send_notification(
    company_id="company-uuid",
    channels=["push", "whatsapp"],
    title="F29 Reminder",
    body="Tu F29 vence mañana",
    data={"type": "f29_reminder"},
    whatsapp_recipients=["+56912345678"]
)
```

### Tareas de Celery

#### Recordatorio F29 para todas las empresas

```python
from app.infrastructure.celery.tasks.notifications import send_f29_reminders

# 3 días antes
send_f29_reminders.delay(days_before=3)

# 7 días antes
send_f29_reminders.delay(days_before=7)
```

#### Recordatorio para empresa específica

```python
from app.infrastructure.celery.tasks.notifications import send_f29_reminder_for_company

send_f29_reminder_for_company.delay(
    company_id="company-uuid",
    days_before=3
)
```

---

## 🧪 Testing

### Test Manual del Servicio

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

### Verificar Tokens en BD

```sql
-- Ver usuarios con push tokens registrados
SELECT id, email, expo_push_token, created_at
FROM profiles
WHERE expo_push_token IS NOT NULL
ORDER BY created_at DESC;
```

### Test con Celery

```bash
# En consola Python del backend
cd backend
.venv/bin/python

>>> from app.infrastructure.celery.tasks.notifications import send_f29_reminder_for_company
>>> send_f29_reminder_for_company.delay(company_id="your-company-id", days_before=3)
```

---

## 📊 Estructura de Datos

### Campo en Base de Datos

```sql
-- Columna agregada a profiles
expo_push_token TEXT  -- Formato: "ExponentPushToken[...]"

-- Índice para búsquedas eficientes
CREATE INDEX idx_profiles_expo_push_token ON profiles(expo_push_token)
WHERE expo_push_token IS NOT NULL;
```

### Formato de Notificación Push

```json
{
  "to": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
  "title": "F29 Reminder",
  "body": "Tu F29 vence en 3 días",
  "data": {
    "type": "f29_reminder",
    "company_id": "uuid",
    "url": "/taxes",
    "due_date": "2025-12-12T00:00:00"
  },
  "sound": "default",
  "badge": 1,
  "priority": "default"
}
```

---

## 🔧 Características Implementadas

- ✅ Almacenamiento de tokens push en `profiles.expo_push_token`
- ✅ Envío individual y masivo de notificaciones
- ✅ Batching automático para listas grandes (>100 usuarios)
- ✅ Integración con sistema de notificaciones existente
- ✅ Soporte multicanal (push + WhatsApp)
- ✅ Tareas de Celery para recordatorios F29
- ✅ Cálculo automático de fechas de vencimiento (día 12 del mes siguiente)
- ✅ Manejo robusto de errores (`InvalidTokenError`, `ExpoServiceError`)
- ✅ Validación de formato de tokens Expo
- ✅ Logging completo
- ✅ Documentación exhaustiva

---

## ⚠️ Consideraciones Importantes

### Límites de Expo Push Service

- **Límite de batch**: 100 notificaciones por request
- **Rate limiting**: Expo aplica límites por token/proyecto
- **TTL máximo**: 2,419,200 segundos (28 días)

### Tokens Inválidos

Cuando un token es inválido (usuario desinstaló la app, token expiró), Expo retorna error `DeviceNotRegistered`. El servicio lo registra pero no lanza excepción.

**Recomendación**: Implementar limpieza periódica de tokens inválidos.

### Permisos en la App

Asegurarse de que la app solicite permisos de notificaciones:

```typescript
import * as Notifications from 'expo-notifications';

const { status } = await Notifications.requestPermissionsAsync();
if (status !== 'granted') {
  console.log('No push notification permissions');
}
```

---

## 🐛 Troubleshooting

### Token no se guarda en BD

**Solución**:
1. Verificar que el frontend esté llamando a `supabase.update()`
2. Verificar RLS policies en Supabase
3. Revisar logs del frontend para errores

### Notificación no llega al dispositivo

**Posibles causas**:
1. Token inválido/expirado
2. Permisos de notificación deshabilitados
3. App en background killing (Android)
4. Notificaciones silenciosas (solo data)

**Debug**:
```python
result = await send_push_notification(
    expo_push_token=token,
    title="Test",
    body="Test notification",
    sound="default"  # Asegurar que no sea silencioso
)
print(result)  # Revisar respuesta de Expo
```

### Error al arrancar el backend

Si hay errores de importación, verificar que no haya referencias a módulos inexistentes como `app.config.database`.

---

## 📚 Referencias

- [Expo Push Notifications Docs](https://docs.expo.dev/push-notifications/overview/)
- [Expo Push API Reference](https://docs.expo.dev/push-notifications/sending-notifications/)
- [Push Notification Testing Tool](https://expo.dev/notifications)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)

---

## 🎯 Próximos Pasos Recomendados

1. **Aplicar la migración** en Supabase (staging y producción)
2. **Implementar el hook** `useSavePushToken` en el frontend
3. **Configurar Celery Beat** con los schedules de recordatorios
4. **Realizar pruebas** con tokens reales de dispositivos
5. **Monitorear logs** de Celery para verificar el envío de recordatorios
6. **Implementar limpieza periódica** de tokens inválidos (opcional)

---

**Implementación completa** ✅
**Fecha**: 2025-11-28
**Versión**: 1.0
