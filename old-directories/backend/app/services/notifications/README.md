# 📱 Guía Rápida - Sistema de Notificaciones

## Uso Simple y Rápido

### 1. Enviar Notificación Instantánea

```python
from app.services.notifications import send_instant_notification

# En cualquier endpoint o función async
await send_instant_notification(
    db,
    company_id,
    ["+56912345678", "+56987654321"],
    "¡Tu F29 fue procesado exitosamente! ✅"
)
```

### 2. Programar Recordatorio de Calendario

```python
from app.services.notifications import send_calendar_reminder
from datetime import datetime

await send_calendar_reminder(
    db,
    company_id,
    "Declaración F29 - Octubre 2025",
    datetime(2025, 11, 12),
    "Presentación mensual de IVA",
    ["+56912345678"],
    days_before=1  # 1 día antes
)
```

### 3. Enviar Recordatorio de F29

```python
from app.services.notifications import send_f29_reminder

await send_f29_reminder(
    db,
    company_id,
    "Octubre 2025",
    datetime(2025, 11, 12),
    ["+56912345678"]
)
```

### 4. Notificar a Toda la Empresa

```python
from app.services.notifications import notify_company_users

await notify_company_users(
    db,
    company_id,
    "El sistema estará en mantenimiento mañana de 2-4 AM",
    send_immediately=True
)
```

### 5. Usar Template Personalizado

```python
from app.services.notifications import schedule_notification_with_template

notification_id = await schedule_notification_with_template(
    db,
    company_id,
    "calendar_event_reminder_3d",  # Template code
    ["+56912345678"],
    {
        "event_title": "Pago Previred",
        "due_date": "15 de Noviembre",
        "description": "Pago de cotizaciones"
    },
    send_immediately=False  # False = programa, True = envía ahora
)
```

### 6. Cancelar Notificación Programada

```python
from app.services.notifications import cancel_scheduled_notification

await cancel_scheduled_notification(db, notification_id)
```

---

## Ejemplo Completo: Endpoint de Creación de F29

```python
from fastapi import APIRouter, Depends
from app.services.notifications import send_f29_reminder, get_company_phones
from app.config.database import get_db

router = APIRouter()

@router.post("/f29")
async def create_f29(
    request: CreateF29Request,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_user_company_id),
):
    # 1. Crear F29 (lógica existente)
    new_f29 = Form29(...)
    db.add(new_f29)
    await db.commit()

    # 2. Obtener teléfonos de la empresa
    recipients = await get_company_phones(db, company_id)
    phones = [r["phone"] for r in recipients]

    # 3. Programar recordatorio automático
    if phones:
        notification_id = await send_f29_reminder(
            db,
            company_id,
            new_f29.period,
            new_f29.due_date,
            phones,
            user_ids=[UUID(r["user_id"]) for r in recipients]
        )

        logger.info(f"📱 Recordatorio F29 programado: {notification_id}")

    return {"f29": new_f29, "notification_scheduled": bool(phones)}
```

---

## Ejemplo: Integración con Calendario

```python
# En app/routers/admin/calendar.py

from app.services.notifications.calendar_integration import setup_calendar_event_notifications
from app.services.notifications import get_notification_service

@router.post("/calendar/events")
async def create_calendar_event(
    request: CreateEventRequest,
    db: AsyncSession = Depends(get_db),
):
    # Crear evento
    new_event = CalendarEvent(...)
    db.add(new_event)
    await db.commit()

    # Auto-programar notificaciones (7d, 3d, 1d, today)
    notification_service = get_notification_service()
    notification_ids = await setup_calendar_event_notifications(
        db, new_event, notification_service
    )

    return {
        "event": new_event,
        "notifications_scheduled": len(notification_ids)
    }
```

---

## Utilidades

### Normalizar Teléfono

```python
from app.services.notifications import format_phone_number

phone = format_phone_number("9 1234 5678")
# Result: +56912345678
```

### Obtener Teléfonos de Empresa

```python
from app.services.notifications import get_company_phones

users = await get_company_phones(db, company_id)
# Result: [{"user_id": "uuid", "phone": "+56..."}, ...]
```

---

## Ejecutar Scheduler

### Manual (desarrollo)

```bash
python -m app.services.notifications.scheduler
```

### Via API

```bash
POST /api/notifications/process?batch_size=50
Authorization: Bearer YOUR_TOKEN
```

### Systemd (producción)

```bash
sudo systemctl status fizko-notification-scheduler.timer
```

---

## Documentación Completa

- **Docs**: `backend/docs/NOTIFICATION_SYSTEM.md`
- **Ejemplos**: `backend/docs/NOTIFICATION_EXAMPLES.md`
- **Migración**: `backend/supabase/migrations/013_notification_system.sql`

---

## Templates Disponibles

| Code | Descripción | Timing |
|---|---|---|
| `calendar_event_reminder_7d` | 7 días antes | -7d @ 09:00 |
| `calendar_event_reminder_3d` | 3 días antes | -3d @ 10:00 |
| `calendar_event_reminder_1d` | 1 día antes | -1d @ 09:00 |
| `calendar_event_due_today` | Día del vencimiento | same day @ 08:00 |
| `calendar_event_completed` | Evento completado | Inmediato |
| `f29_due_soon` | F29 próximo | -2d @ 09:00 |
| `system_reminder` | Genérico | Inmediato |

---

## Tips

1. **Siempre usar `await`** - Todas las funciones son async
2. **Verificar teléfonos** - Los usuarios deben tener `profile.phone` configurado
3. **Respetar preferencias** - El sistema automáticamente respeta horarios de silencio
4. **Monitorear historial** - Usar `GET /api/notifications/history`
5. **Probar con test** - Usar `send_instant_notification()` para testing rápido

---

## Troubleshooting

### Notificación no se envió

```python
# Ver historial
from app.db.models import NotificationHistory
result = await db.execute(
    select(NotificationHistory)
    .where(NotificationHistory.company_id == company_id)
    .order_by(desc(NotificationHistory.sent_at))
    .limit(10)
)
```

### Template no encontrado

```bash
# Listar templates disponibles
GET /api/notifications/templates
```

### Ver notificaciones pendientes

```sql
SELECT * FROM scheduled_notifications
WHERE status = 'pending'
ORDER BY scheduled_for;
```
