# 📱 Sistema de Notificaciones por WhatsApp - Documentación

## Índice

1. [Visión General](#visión-general)
2. [Arquitectura](#arquitectura)
3. [Esquema de Base de Datos](#esquema-de-base-de-datos)
4. [Flujos de Trabajo](#flujos-de-trabajo)
5. [Guía de Uso](#guía-de-uso)
6. [API Reference](#api-reference)
7. [Integración con Calendario](#integración-con-calendario)
8. [Scheduler](#scheduler)
9. [Templates Predefinidos](#templates-predefinidos)
10. [Configuración](#configuración)

---

## Visión General

El sistema de notificaciones de Fizko permite enviar recordatorios y alertas automáticas a usuarios vía WhatsApp. El sistema está diseñado para:

- ✅ **Notificaciones de Calendario**: Recordatorios de eventos tributarios (F29, F22, Previred, etc.)
- ✅ **Notificaciones de Documentos**: Alertas sobre documentos tributarios
- ✅ **Notificaciones de Nómina**: Recordatorios de deadlines de payroll
- ✅ **Notificaciones Custom**: Cualquier tipo de notificación personalizada

### Características Principales

- 🎯 **Templates Reutilizables**: Define una vez, usa múltiples veces
- ⏰ **Timing Flexible**: Relativo (X días antes), absoluto (hora específica), o inmediato
- 🔕 **Preferencias de Usuario**: Horarios de silencio, categorías silenciadas, límites de frecuencia
- 📊 **Historial Completo**: Auditoría y analytics de todas las notificaciones
- 🔄 **Scheduler Flexible**: Ejecuta manual o con Celery
- 🔗 **Integración con Entidades**: Vincula notificaciones a eventos, documentos, tareas, etc.

---

## Arquitectura

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────┐
│                  API Endpoints                       │
│         /api/notifications/* (FastAPI)              │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│            NotificationService                      │
│  • Template management                              │
│  • Subscription management                          │
│  • Notification scheduling                          │
│  • Sending logic                                    │
│  • History & analytics                              │
└────────────────┬────────────────────────────────────┘
                 │
       ┌─────────┼─────────┐
       │                   │
┌──────▼──────┐   ┌───────▼────────┐
│ WhatsApp    │   │  Database      │
│ Service     │   │  (Supabase)    │
│ (Kapso)     │   │  6 tables      │
└─────────────┘   └────────────────┘
```

### Componentes Clave

1. **NotificationService** (`app/services/notifications/service.py`)
   - Gestión de templates
   - Suscripciones de empresas
   - Programación de notificaciones
   - Envío y tracking

2. **Scheduler** (`app/services/notifications/scheduler.py`)
   - Procesamiento de notificaciones pendientes
   - Ejecutable manual o con Celery

3. **Calendar Integration** (`app/services/notifications/calendar_integration.py`)
   - Integración automática con eventos de calendario
   - Programación automática de recordatorios

4. **API Endpoints** (`app/routers/notifications.py`)
   - RESTful API para gestión completa
   - Autenticación JWT

---

## Esquema de Base de Datos

### Tablas

#### 1. `notification_templates`
Plantillas reutilizables de notificaciones.

```sql
CREATE TABLE notification_templates (
    id UUID PRIMARY KEY,
    code VARCHAR(100) UNIQUE,  -- "calendar_event_reminder_1d"
    name TEXT,
    category VARCHAR(50),  -- 'calendar', 'tax_document', etc.
    entity_type VARCHAR(50),  -- 'calendar_event', 'form29', etc.
    message_template TEXT,  -- Con variables {{variable}}
    timing_config JSONB,  -- {"type": "relative", "offset_days": -1, "time": "09:00"}
    priority VARCHAR(20),  -- 'low', 'normal', 'high', 'urgent'
    can_repeat BOOLEAN,
    max_repeats INTEGER,
    is_active BOOLEAN,
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 2. `notification_subscriptions`
Suscripciones de empresas a notificaciones.

```sql
CREATE TABLE notification_subscriptions (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    notification_template_id UUID REFERENCES notification_templates(id),
    is_enabled BOOLEAN,
    custom_timing_config JSONB,  -- Sobrescribe template
    custom_message_template TEXT,
    channels JSONB,  -- ["whatsapp"]
    filters JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(company_id, notification_template_id)
);
```

#### 3. `scheduled_notifications`
Cola de notificaciones programadas (procesada por scheduler).

```sql
CREATE TABLE scheduled_notifications (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    notification_template_id UUID REFERENCES notification_templates(id),
    entity_type VARCHAR(50),  -- 'calendar_event', etc.
    entity_id UUID,
    recipients JSONB,  -- [{"user_id": "...", "phone": "+56..."}]
    message_content TEXT,  -- Ya renderizado
    scheduled_for TIMESTAMP,  -- Cuándo enviar
    status VARCHAR(30),  -- 'pending', 'processing', 'sent', 'failed', etc.
    sent_at TIMESTAMP,
    send_attempts INTEGER,
    error_message TEXT,
    send_results JSONB,
    is_repeat BOOLEAN,
    repeat_of UUID REFERENCES scheduled_notifications(id),
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 4. `notification_history`
Historial completo de notificaciones enviadas.

```sql
CREATE TABLE notification_history (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    notification_template_id UUID REFERENCES notification_templates(id),
    scheduled_notification_id UUID REFERENCES scheduled_notifications(id),
    entity_type VARCHAR(50),
    entity_id UUID,
    user_id UUID REFERENCES profiles(id),
    phone_number VARCHAR(20),
    message_content TEXT,
    status VARCHAR(30),  -- 'sent', 'failed', 'delivered', 'read'
    whatsapp_conversation_id VARCHAR(100),
    whatsapp_message_id VARCHAR(100),
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP
);
```

#### 5. `notification_event_triggers`
Triggers automáticos para generar notificaciones.

```sql
CREATE TABLE notification_event_triggers (
    id UUID PRIMARY KEY,
    name TEXT,
    entity_type VARCHAR(50),  -- 'calendar_event', etc.
    trigger_event VARCHAR(50),  -- 'created', 'status_changed', etc.
    trigger_conditions JSONB,
    notification_template_id UUID REFERENCES notification_templates(id),
    is_active BOOLEAN,
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 6. `user_notification_preferences`
Preferencias individuales de usuarios.

```sql
CREATE TABLE user_notification_preferences (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    company_id UUID REFERENCES companies(id),
    notifications_enabled BOOLEAN,
    quiet_hours_start TIME,  -- 22:00
    quiet_hours_end TIME,  -- 08:00
    quiet_days JSONB,  -- ["saturday", "sunday"]
    muted_categories JSONB,  -- ["system"]
    muted_templates JSONB,  -- [template_id_1, ...]
    max_notifications_per_day INTEGER,
    min_interval_minutes INTEGER,
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, company_id)
);
```

---

## Flujos de Trabajo

### 1. Flujo: Crear y Programar Notificación Manual

```
1. Usuario/Sistema llama POST /api/notifications/schedule
        ↓
2. NotificationService.schedule_notification()
        ↓
3. Obtiene template y verifica suscripción de empresa
        ↓
4. Calcula scheduled_for basado en timing_config
        ↓
5. Renderiza mensaje con variables
        ↓
6. Crea registro en scheduled_notifications (status=pending)
        ↓
7. Retorna ScheduledNotification
```

### 2. Flujo: Scheduler Procesa Notificaciones

```
1. Scheduler ejecuta (manual o Celery cada N minutos)
        ↓
2. NotificationService.process_pending_notifications()
        ↓
3. Query: scheduled_notifications WHERE status=pending AND scheduled_for <= NOW()
        ↓
4. Para cada notificación:
   a. Marca status=processing
   b. Para cada destinatario:
      - Verifica preferencias de usuario
      - Envía por WhatsApp
      - Registra en notification_history
   c. Actualiza status=sent/failed/skipped
        ↓
5. Retorna estadísticas
```

### 3. Flujo: Integración con Calendario

```
1. Se crea CalendarEvent en DB
        ↓
2. setup_calendar_event_notifications(event)
        ↓
3. CalendarNotificationIntegration.schedule_notifications_for_event()
        ↓
4. Programa 4 notificaciones:
   - 7 días antes (reminder_7d)
   - 3 días antes (reminder_3d)
   - 1 día antes (reminder_1d)
   - Día del vencimiento (due_today)
        ↓
5. Cada notificación se crea en scheduled_notifications con scheduled_for calculado
```

### 4. Flujo: Usuario Configura Preferencias

```
1. Usuario llama PUT /api/notifications/preferences
        ↓
2. Guarda/actualiza en user_notification_preferences
        ↓
3. Preferencias aplicadas en próximos envíos:
   - Horarios de silencio
   - Días silenciados
   - Categorías/templates silenciados
   - Límites de frecuencia
```

---

## Guía de Uso

### 1. Configurar Notificaciones para una Empresa

#### Paso 1: Listar templates disponibles

```bash
GET /api/notifications/templates
```

```json
[
  {
    "id": "uuid-here",
    "code": "calendar_event_reminder_1d",
    "name": "Recordatorio de evento - 1 día antes",
    "category": "calendar",
    "entity_type": "calendar_event",
    "message_template": "📅 *Recordatorio:* {{event_title}}\n\nVence mañana: {{due_date}}",
    "timing_config": {
      "type": "relative",
      "offset_days": -1,
      "time": "09:00"
    },
    "priority": "high",
    "is_active": true
  }
]
```

#### Paso 2: Suscribir empresa a notificación

```bash
POST /api/notifications/subscriptions
```

```json
{
  "template_id": "uuid-del-template",
  "is_enabled": true,
  "custom_timing": {
    "type": "relative",
    "offset_days": -1,
    "time": "08:00"  // Personalizar hora
  }
}
```

### 2. Programar Notificación Manual

```bash
POST /api/notifications/schedule
```

```json
{
  "template_code": "calendar_event_reminder_1d",
  "recipients": [
    {
      "user_id": "user-uuid-1",
      "phone": "+56912345678"
    },
    {
      "user_id": "user-uuid-2",
      "phone": "+56987654321"
    }
  ],
  "message_context": {
    "event_title": "Declaración F29 - Octubre 2025",
    "due_date": "12 de Noviembre",
    "description": "Presentación mensual de IVA"
  },
  "entity_type": "calendar_event",
  "entity_id": "event-uuid",
  "reference_date": "2025-11-12T00:00:00Z"
}
```

### 3. Integración con Calendario (al crear evento)

```python
from app.services.notifications import NotificationService
from app.services.notifications.calendar_integration import setup_calendar_event_notifications

# En el endpoint de creación de calendario
notification_service = NotificationService(whatsapp_service)

# Programa automáticamente 4 notificaciones (7d, 3d, 1d, today)
notification_ids = await setup_calendar_event_notifications(
    db,
    new_calendar_event,
    notification_service
)

logger.info(f"Programadas {len(notification_ids)} notificaciones")
```

### 4. Ejecutar Scheduler Manualmente

```bash
# Desde línea de comandos
python -m app.services.notifications.scheduler

# O via API
POST /api/notifications/process?batch_size=50
```

Respuesta:
```json
{
  "processed": 15,
  "sent": 42,
  "failed": 2,
  "skipped": 3
}
```

### 5. Configurar Preferencias de Usuario

```bash
PUT /api/notifications/preferences
```

```json
{
  "notifications_enabled": true,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "quiet_days": ["saturday", "sunday"],
  "muted_categories": ["system"],
  "max_notifications_per_day": 10,
  "min_interval_minutes": 60
}
```

### 6. Ver Historial de Notificaciones

```bash
GET /api/notifications/history?entity_type=calendar_event&limit=50
```

```json
[
  {
    "id": "uuid",
    "company_id": "company-uuid",
    "entity_type": "calendar_event",
    "entity_id": "event-uuid",
    "user_id": "user-uuid",
    "phone_number": "+56912345678",
    "message_content": "📅 *Recordatorio:* Declaración F29...",
    "status": "sent",
    "sent_at": "2025-11-11T09:00:00Z",
    "whatsapp_message_id": "msg-id-from-kapso"
  }
]
```

---

## API Reference

### Templates

| Endpoint | Method | Description |
|---|---|---|
| `/api/notifications/templates` | GET | Lista templates disponibles |
| `/api/notifications/templates/{id}` | GET | Obtiene template específico |

### Subscriptions

| Endpoint | Method | Description |
|---|---|---|
| `/api/notifications/subscriptions` | GET | Lista suscripciones de la empresa |
| `/api/notifications/subscriptions` | POST | Suscribe a notificación |
| `/api/notifications/subscriptions/{template_id}` | DELETE | Desuscribe |

### Scheduling

| Endpoint | Method | Description |
|---|---|---|
| `/api/notifications/schedule` | POST | Programa notificación |
| `/api/notifications/process` | POST | Procesa pendientes (manual) |

### History

| Endpoint | Method | Description |
|---|---|---|
| `/api/notifications/history` | GET | Historial de notificaciones |

### Preferences

| Endpoint | Method | Description |
|---|---|---|
| `/api/notifications/preferences` | GET | Obtiene preferencias del usuario |
| `/api/notifications/preferences` | PUT | Actualiza preferencias |

---

## Integración con Calendario

### Auto-programar notificaciones al crear evento

```python
# En app/routers/admin/calendar.py o donde se crean eventos

from app.services.notifications import NotificationService
from app.services.notifications.calendar_integration import setup_calendar_event_notifications

@router.post("/calendar/events")
async def create_calendar_event(
    request: CreateEventRequest,
    db: AsyncSession = Depends(get_db),
):
    # Crear evento
    new_event = CalendarEvent(...)
    db.add(new_event)
    await db.commit()

    # Auto-programar notificaciones
    notification_service = NotificationService(whatsapp_service)
    notification_ids = await setup_calendar_event_notifications(
        db, new_event, notification_service
    )

    return {"event": new_event, "notifications_scheduled": len(notification_ids)}
```

### Notificar cuando evento se completa

```python
from app.services.notifications.calendar_integration import notify_calendar_event_completed

@router.put("/calendar/events/{event_id}/status")
async def update_event_status(
    event_id: UUID,
    new_status: str,
    db: AsyncSession = Depends(get_db),
):
    event = await get_event(db, event_id)
    old_status = event.status

    # Actualizar estado
    event.status = new_status
    await db.commit()

    # Notificar si fue completado
    if new_status == "completed" and old_status != "completed":
        notification_service = NotificationService(whatsapp_service)
        await notify_calendar_event_completed(db, event, notification_service)

    return {"event": event}
```

---

## Scheduler

### Ejecución Manual

```bash
# Opción 1: Script directo
python -m app.services.notifications.scheduler

# Opción 2: Via API
curl -X POST http://localhost:8089/api/notifications/process \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Configuración con Celery (Futuro)

```python
# En app/celery_app.py

from celery import Celery
from celery.schedules import crontab

celery_app = Celery('fizko')

celery_app.conf.beat_schedule = {
    'process-notifications-every-5-minutes': {
        'task': 'process_pending_notifications',
        'schedule': crontab(minute='*/5'),  # Cada 5 minutos
        'args': (50,),  # batch_size
    },
}
```

```python
# En app/services/notifications/scheduler.py (descomentar)

from app.celery_app import celery_app

@celery_app.task(name="process_pending_notifications")
def celery_process_pending_notifications(batch_size: int = 50):
    return asyncio.run(process_pending_notifications_task(batch_size=batch_size))
```

### Cron (Alternativa sin Celery)

```bash
# Agregar a crontab
# Ejecutar cada 5 minutos
*/5 * * * * cd /path/to/fizko-v2/backend && python -m app.services.notifications.scheduler >> /var/log/fizko-notifications.log 2>&1
```

---

## Templates Predefinidos

El sistema incluye 7 templates predefinidos:

### 1. `calendar_event_reminder_7d`
- **Categoría**: calendar
- **Timing**: 7 días antes a las 09:00
- **Mensaje**: "📅 *Aviso semanal:* {{event_title}}..."

### 2. `calendar_event_reminder_3d`
- **Categoría**: calendar
- **Timing**: 3 días antes a las 10:00
- **Mensaje**: "📅 *Próximamente:* {{event_title}}..."

### 3. `calendar_event_reminder_1d`
- **Categoría**: calendar
- **Timing**: 1 día antes a las 09:00
- **Prioridad**: high
- **Mensaje**: "📅 *Recordatorio:* {{event_title}}..."

### 4. `calendar_event_due_today`
- **Categoría**: calendar
- **Timing**: Día del evento a las 08:00
- **Prioridad**: urgent
- **Puede repetir**: Sí (máx 2 veces)
- **Mensaje**: "⚠️ *¡VENCE HOY!* {{event_title}}..."

### 5. `calendar_event_completed`
- **Categoría**: calendar
- **Timing**: Inmediato
- **Mensaje**: "✅ *Completado:* {{event_title}}..."

### 6. `f29_due_soon`
- **Categoría**: tax_document
- **Timing**: 2 días antes a las 09:00
- **Prioridad**: high
- **Mensaje**: "📋 *Declaración F29 - {{period}}*..."

### 7. `system_reminder`
- **Categoría**: system
- **Timing**: Inmediato
- **Mensaje**: "🔔 *Recordatorio* {{message}}"

---

## Configuración

### Variables de Entorno

```bash
# WhatsApp/Kapso (ya configuradas para WhatsApp)
KAPSO_API_TOKEN=your-kapso-token
KAPSO_API_BASE_URL=https://app.kapso.ai/api/v1
KAPSO_WEBHOOK_SECRET=your-webhook-secret

# Base de datos (ya configurada)
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
```

### Aplicar Migración

```bash
# 1. Aplicar migración SQL
psql -U your_user -d your_database -f backend/supabase/migrations/013_notification_system.sql

# 2. Verificar tablas creadas
psql -U your_user -d your_database -c "\dt notification*"
```

### Inicialización

Las tablas se crean automáticamente con:
- 7 templates predefinidos
- Índices optimizados
- Vistas útiles
- Funciones auxiliares

---

## Ejemplos Completos

### Ejemplo 1: Suscribir empresa a recordatorios de F29

```python
import httpx

# 1. Obtener token JWT
token = "your-jwt-token"

# 2. Buscar template de F29
response = httpx.get(
    "http://localhost:8089/api/notifications/templates",
    headers={"Authorization": f"Bearer {token}"},
    params={"category": "tax_document"}
)
templates = response.json()
f29_template = next(t for t in templates if t["code"] == "f29_due_soon")

# 3. Suscribir empresa
response = httpx.post(
    "http://localhost:8089/api/notifications/subscriptions",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "template_id": f29_template["id"],
        "is_enabled": True,
        "custom_timing": {
            "type": "relative",
            "offset_days": -2,
            "time": "08:30"  # Personalizar a las 8:30 AM
        }
    }
)
```

### Ejemplo 2: Programar recordatorio custom

```python
# Crear recordatorio para una reunión importante
response = httpx.post(
    "http://localhost:8089/api/notifications/schedule",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "template_code": "system_reminder",
        "recipients": [
            {"user_id": "user-uuid", "phone": "+56912345678"}
        ],
        "message_context": {
            "message": "Recordatorio: Reunión con contador mañana a las 10:00 AM"
        },
        "custom_timing": {
            "type": "absolute",
            "time": "09:00"  # Mañana a las 9 AM
        },
        "reference_date": "2025-11-13T00:00:00Z"
    }
)
```

### Ejemplo 3: Script para programar notificaciones de eventos próximos

```python
from app.services.notifications import NotificationService
from app.services.notifications.calendar_integration import CalendarNotificationIntegration
from app.config.database import AsyncSessionLocal

async def schedule_upcoming_events():
    notification_service = NotificationService(whatsapp_service)
    integration = CalendarNotificationIntegration(notification_service)

    async with AsyncSessionLocal() as db:
        stats = await integration.schedule_notifications_for_upcoming_events(
            db=db,
            days_ahead=30  # Próximos 30 días
        )

        print(f"✅ {stats['events_processed']} eventos procesados")
        print(f"✅ {stats['notifications_scheduled']} notificaciones programadas")

# Ejecutar
asyncio.run(schedule_upcoming_events())
```

---

## Troubleshooting

### Problema: Notificaciones no se envían

**Verificar:**
1. ¿Scheduler está corriendo? `POST /api/notifications/process`
2. ¿La empresa está suscrita? `GET /api/notifications/subscriptions`
3. ¿Usuarios tienen teléfono configurado? Revisar `profiles.phone`
4. ¿Preferencias de usuario bloquean envío? `GET /api/notifications/preferences`

### Problema: Template no encontrado

```sql
-- Listar templates disponibles
SELECT code, name, is_active FROM notification_templates;
```

### Problema: Ver notificaciones pendientes

```sql
-- Ver notificaciones en cola
SELECT
    id,
    scheduled_for,
    status,
    send_attempts,
    error_message
FROM scheduled_notifications
WHERE status = 'pending'
ORDER BY scheduled_for;
```

---

## Métricas y Monitoreo

### Vista: Estadísticas por empresa

```sql
SELECT * FROM notification_stats_by_company
WHERE company_id = 'your-company-uuid'
AND date >= CURRENT_DATE - INTERVAL '7 days';
```

### Query: Tasa de éxito por template

```sql
SELECT
    nt.name,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE nh.status = 'sent') as sent,
    COUNT(*) FILTER (WHERE nh.status = 'failed') as failed,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE nh.status = 'sent') / COUNT(*),
        2
    ) as success_rate
FROM notification_history nh
JOIN notification_templates nt ON nh.notification_template_id = nt.id
WHERE nh.sent_at >= NOW() - INTERVAL '30 days'
GROUP BY nt.name
ORDER BY total DESC;
```

---

## Próximos Pasos

1. ✅ Aplicar migración SQL
2. ✅ Suscribir empresas a notificaciones deseadas
3. ✅ Integrar con creación de eventos de calendario
4. ✅ Ejecutar scheduler manualmente (testing)
5. ⏳ Configurar Celery para ejecución automática (futuro)
6. ⏳ Agregar más templates según necesidad

---

## Soporte

Para dudas o problemas:
- Revisar logs: `/var/log/fizko-notifications.log`
- Ver historial: `GET /api/notifications/history`
- Revisar tablas: `scheduled_notifications`, `notification_history`
