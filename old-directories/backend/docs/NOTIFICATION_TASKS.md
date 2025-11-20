# Notification Periodic Tasks

Este documento describe el sistema de tareas periódicas para notificaciones de calendario implementado con Celery Beat.

## Arquitectura

El sistema de notificaciones de calendario funciona con dos tareas periódicas que trabajan en conjunto:

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION SYSTEM                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐                    ┌──────────────────────┐
│  CalendarEvent       │                    │  NotificationTemplate│
│  (F29, F22, etc.)    │                    │  (7d, 3d, 1d, hoy)   │
└──────────────────────┘                    └──────────────────────┘
          │                                            │
          └────────────────┬───────────────────────────┘
                           ▼
         ┌─────────────────────────────────────────┐
         │  TASK 1: sync_calendar_notifications    │
         │  Frequency: Every 15 minutes            │
         │  Creates ScheduledNotifications         │
         └─────────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────────┐
         │     ScheduledNotification (DB)          │
         │  - scheduled_for: datetime              │
         │  - status: pending/sent/failed          │
         │  - template_id: FK                      │
         └─────────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────────┐
         │  TASK 2: process_pending_notifications  │
         │  Frequency: Every 5 minutes             │
         │  Sends via WhatsApp                     │
         └─────────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────────┐
         │     NotificationHistory (DB)            │
         │  - sent_at: datetime                    │
         │  - status: sent/failed                  │
         │  - whatsapp_message_id: string          │
         └─────────────────────────────────────────┘
```

## Tareas Implementadas

### 1. sync_calendar_notifications

**Archivo:** `app/infrastructure/celery/tasks/notifications/calendar_notifications.py`

**Nombre Celery:** `notifications.sync_calendar`

**Frecuencia:** Cada 15 minutos

**Responsabilidades:**
- Escanea `CalendarEvent` en los próximos 30 días
- Verifica suscripciones activas de usuarios a templates de notificaciones
- Crea `ScheduledNotification` para recordatorios automáticos:
  - 7 días antes del vencimiento
  - 3 días antes del vencimiento
  - 1 día antes del vencimiento
  - El día del vencimiento
- Es idempotente: no crea notificaciones duplicadas

**Delegación:**
Delega toda la lógica a `CalendarNotificationIntegration.schedule_notifications_for_upcoming_events()`.

**Ejemplo de output:**
```json
{
  "success": true,
  "events_processed": 45,
  "notifications_created": 180,
  "timestamp": "2025-10-30T10:00:00Z",
  "message": "Calendar notifications synced successfully"
}
```

### 2. process_pending_notifications

**Archivo:** `app/infrastructure/celery/tasks/notifications/processing.py`

**Nombre Celery:** `notifications.process_pending`

**Frecuencia:** Cada 5 minutos

**Responsabilidades:**
- Busca `ScheduledNotification` donde `scheduled_for <= now()` y `status = 'pending'`
- Valida preferencias de usuario:
  - Quiet hours (horarios de silencio)
  - Daily limits (límites diarios)
  - Muted categories (categorías silenciadas)
- Envía notificaciones vía WhatsApp usando `WhatsAppService`
- Crea registros en `NotificationHistory`
- Procesa en batches de 50 notificaciones por ejecución

**Delegación:**
Delega toda la lógica a `NotificationService.process_pending_notifications_task()`.

**Ejemplo de output:**
```json
{
  "success": true,
  "sent_count": 42,
  "skipped_count": 3,
  "failed_count": 1,
  "timestamp": "2025-10-30T10:05:00Z",
  "message": "Pending notifications processed successfully"
}
```

## Estructura de Archivos

```
backend/app/infrastructure/celery/
├── __init__.py                           # Celery app + autodiscovery
├── config.py                             # Celery config (beat scheduler)
└── tasks/
    ├── __init__.py                       # Registry de todos los módulos
    ├── notifications/
    │   ├── __init__.py                   # Exports de notification tasks
    │   ├── calendar_notifications.py     # TASK 1: Sync calendar
    │   ├── processing.py                 # TASK 2: Process pending
    │   └── setup.py                      # Setup script para DB
    ├── calendar/                         # Calendar sync tasks
    │   ├── __init__.py
    │   └── sync.py
    ├── sii/                              # SII tasks (documents, forms, etc.)
    └── ...
```

## Configuración

Las tareas se configuran usando **Database Scheduler** (`sqlalchemy-celery-beat`), no archivos de configuración estáticos.

### Tablas de Base de Datos

El scheduler usa las siguientes tablas (schema `celery_schema`):

- `celery_intervalschedule` - Define intervalos (15 min, 5 min, etc.)
- `celery_crontabschedule` - Define schedules tipo cron (opcional)
- `celery_periodictask` - Define tareas periódicas
- `celery_periodictaskchanged` - Notifica cambios al beat worker

### Setup Inicial

Las tareas periódicas se crean **manualmente** en la base de datos. Tienes 3 opciones:

#### Opción 1: Admin UI (Recomendado)

```
http://localhost:8000/admin/scheduled-tasks

Crear dos tareas:

1. Task: notifications.sync_calendar
   - Schedule: Interval, every 15 minutes
   - Enabled: ✅

2. Task: notifications.process_pending
   - Schedule: Interval, every 5 minutes
   - Enabled: ✅
```

#### Opción 2: SQL Directo

```sql
-- 1. Crear interval schedules
INSERT INTO celery_intervalschedule (every, period) VALUES (15, 'minutes') RETURNING id; -- ej: 101
INSERT INTO celery_intervalschedule (every, period) VALUES (5, 'minutes') RETURNING id;  -- ej: 102

-- 2. Crear periodic tasks
INSERT INTO celery_periodictask (name, task, interval_id, enabled, description) VALUES
('Sync Calendar Notifications', 'notifications.sync_calendar', 101, true, 'Sincroniza notificaciones de calendario cada 15 min'),
('Process Pending Notifications', 'notifications.process_pending', 102, true, 'Procesa y envía notificaciones pendientes cada 5 min');

-- 3. Notificar cambio a Beat
INSERT INTO celery_periodictaskchanged (last_update) VALUES (NOW())
ON CONFLICT DO UPDATE SET last_update = NOW();
```

#### Opción 3: API Endpoint

```bash
# Crear sync_calendar_notifications
curl -X POST http://localhost:8000/api/admin/scheduled-tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sync Calendar Notifications",
    "task": "notifications.sync_calendar",
    "schedule_type": "interval",
    "interval_every": 15,
    "interval_period": "minutes",
    "enabled": true
  }'

# Crear process_pending_notifications
curl -X POST http://localhost:8000/api/admin/scheduled-tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Process Pending Notifications",
    "task": "notifications.process_pending",
    "schedule_type": "interval",
    "interval_every": 5,
    "interval_period": "minutes",
    "enabled": true
  }'
```

### Verificación

Después de crear las tareas periódicas, verifica:

```bash
# Ver tareas registradas en Celery
celery -A app.infrastructure.celery.celery_app inspect registered

# Ver tareas periódicas activas
celery -A app.infrastructure.celery.celery_app beat inspect scheduled
```

O desde la UI:
- Admin UI: http://localhost:8000/admin/scheduled-tasks

## Dependencias

### Servicios Requeridos

1. **CalendarNotificationIntegration** (`app/services/notifications/calendar_integration.py`)
   - `schedule_notifications_for_upcoming_events()` - Crea notificaciones para eventos próximos

2. **NotificationService** (`app/services/notifications/service.py`)
   - `process_pending_notifications_task()` - Procesa y envía notificaciones pendientes

3. **WhatsAppService** (`app/services/whatsapp/service.py`)
   - `send_message()` - Envía mensajes vía WhatsApp

### Templates de Notificaciones

Las siguientes templates deben existir en la base de datos:

| Code | Category | Type | When |
|------|----------|------|------|
| `calendar_event_reminder_7d` | calendar | recurrent | 7 días antes |
| `calendar_event_reminder_3d` | calendar | recurrent | 3 días antes |
| `calendar_event_reminder_1d` | calendar | recurrent | 1 día antes |
| `calendar_event_due_today` | calendar | recurrent | Día del vencimiento |
| `calendar_event_completed` | calendar | one_off | Evento completado |
| `calendar_event_cancelled` | calendar | one_off | Evento cancelado |

## Ejecución

### Workers

Los workers de Celery deben estar corriendo para ejecutar las tareas:

```bash
cd backend
./start_celery.sh  # Inicia worker
```

### Beat Scheduler

El beat scheduler debe estar corriendo para disparar las tareas periódicas:

```bash
cd backend
./start_beat.sh  # Inicia beat
```

**IMPORTANTE:** Beat consulta la base de datos cada 5 segundos (`beat_max_loop_interval = 5`), por lo que los cambios en tareas periódicas se detectan automáticamente sin reiniciar.

## Monitoreo

### Logs

Los logs de las tareas incluyen:

```
[2025-10-30 10:00:00: INFO/MainProcess][notifications.sync_calendar(abc-123)] 🔔 Starting calendar notifications sync...
[2025-10-30 10:00:15: INFO/MainProcess][notifications.sync_calendar(abc-123)] ✅ Calendar notifications sync completed: 45 events processed, 180 notifications created
```

### Flower (opcional)

Para monitoreo visual de Celery:

```bash
pip install flower
celery -A app.infrastructure.celery.celery_app flower
```

Accede a http://localhost:5555

## Extensibilidad

### Agregar Nuevos Tipos de Notificaciones

Para agregar notificaciones de otro tipo (ej: payroll, documents):

1. **Crear nuevo archivo en `tasks/notifications/`:**
   ```python
   # app/infrastructure/celery/tasks/notifications/payroll_notifications.py

   @celery_app.task(name="notifications.sync_payroll")
   def sync_payroll_notifications(self):
       """Sincroniza notificaciones de nómina"""
       # ... implementación
   ```

2. **Exportar en `__init__.py`:**
   ```python
   from .payroll_notifications import sync_payroll_notifications

   __all__ = [
       "sync_calendar_notifications",
       "process_pending_notifications",
       "sync_payroll_notifications",  # Nuevo
   ]
   ```

3. **Crear tarea periódica en BD** (usando `SchedulerService` o script de setup)

El procesamiento (`process_pending_notifications`) es genérico y funcionará para todos los tipos de notificaciones.

## Troubleshooting

### Las tareas no se ejecutan

1. Verificar que beat está corriendo: `ps aux | grep celery`
2. Verificar que las tareas existen en BD: Consultar tabla `celery_periodictask`
3. Verificar que `enabled=true` en la tarea
4. Revisar logs de beat: `./start_beat.sh` (debería mostrar las tareas cargadas)

### Las notificaciones no se envían

1. Verificar que `process_pending_notifications` está activo
2. Verificar que hay `ScheduledNotification` con `status='pending'`
3. Verificar que `scheduled_for <= now()`
4. Revisar preferencias de usuario (quiet hours, daily limits)
5. Verificar que WhatsApp service está configurado correctamente

### Duplicación de notificaciones

El sistema es idempotente. Verificar:
1. `sync_calendar_notifications` no crea duplicados (chequea existing notifications)
2. `process_pending_notifications` actualiza status a 'sent' después de enviar
3. No ejecutar el setup script múltiples veces sin verificar

## Referencias

- [Celery Beat Documentation](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
- [sqlalchemy-celery-beat](https://github.com/AngelLiang/sqlalchemy-celery-beat)
- [Sistema de Notificaciones](./NOTIFICATION_SYSTEM.md)
