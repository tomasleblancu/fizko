## 📚 Ejemplos Prácticos - Sistema de Notificaciones

Colección de ejemplos de uso real del sistema de notificaciones de Fizko.

---

## Ejemplo 1: Configuración Inicial - Primera vez

### Paso 1: Aplicar migración

```bash
cd backend
psql $DATABASE_URL -f supabase/migrations/013_notification_system.sql
```

### Paso 2: Verificar templates predefinidos

```bash
curl -X GET http://localhost:8089/api/notifications/templates \
  -H "Authorization: Bearer YOUR_TOKEN" | jq
```

### Paso 3: Suscribir empresa a recordatorios de F29

```bash
curl -X POST http://localhost:8089/api/notifications/subscriptions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "UUID_DEL_TEMPLATE_F29",
    "is_enabled": true
  }'
```

---

## Ejemplo 2: Crear Template Personalizado

### Template para recordatorio de pago de Previred

```sql
INSERT INTO notification_templates (
    code,
    name,
    description,
    category,
    entity_type,
    message_template,
    timing_config,
    priority,
    is_active
) VALUES (
    'previred_payment_reminder',
    'Recordatorio de pago Previred',
    'Notifica 2 días antes del pago de Previred',
    'payroll',
    'calendar_event',
    '💼 *Recordatorio: Pago Previred*

Vence: {{due_date}}
Período: {{period}}

Recuerda:
• Verificar nómina procesada
• Confirmar montos de cotizaciones
• Validar trabajadores activos

¿Necesitas ayuda?',
    '{"type": "relative", "offset_days": -2, "time": "10:00"}'::jsonb,
    'high',
    true
);
```

---

## Ejemplo 3: Script Python - Programar Notificaciones Masivas

### Programar recordatorios para todos los eventos del mes

```python
import asyncio
from datetime import datetime, timedelta
from app.config.database import AsyncSessionLocal
from app.services.notifications import NotificationService
from app.services.whatsapp.service import WhatsAppService
from app.db.models import CalendarEvent
from sqlalchemy import select, and_
import os

async def schedule_monthly_reminders():
    """Programa recordatorios para eventos del próximo mes."""

    # Setup servicios
    whatsapp_service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
        base_url=os.getenv("KAPSO_API_BASE_URL"),
    )
    notification_service = NotificationService(whatsapp_service)

    # Fechas
    today = datetime.utcnow().date()
    next_month = today + timedelta(days=30)

    async with AsyncSessionLocal() as db:
        # Obtener eventos próximos
        result = await db.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.due_date >= today,
                    CalendarEvent.due_date <= next_month,
                    CalendarEvent.status.in_(["pending", "in_progress"]),
                )
            )
        )
        events = result.scalars().all()

        print(f"📅 Encontrados {len(events)} eventos próximos")

        # Importar integración
        from app.services.notifications.calendar_integration import (
            CalendarNotificationIntegration,
        )

        integration = CalendarNotificationIntegration(notification_service)

        total_scheduled = 0

        for event in events:
            print(f"\n🔄 Procesando: {event.title} (vence {event.due_date})")

            try:
                # Programar notificaciones automáticas
                scheduled_ids = await integration.schedule_notifications_for_event(
                    db, event
                )

                total_scheduled += len(scheduled_ids)
                print(f"   ✅ {len(scheduled_ids)} notificaciones programadas")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        print(f"\n✅ Total: {total_scheduled} notificaciones programadas")

if __name__ == "__main__":
    asyncio.run(schedule_monthly_reminders())
```

**Ejecutar:**
```bash
cd backend
python -c "from scripts.schedule_monthly_reminders import schedule_monthly_reminders; import asyncio; asyncio.run(schedule_monthly_reminders())"
```

---

## Ejemplo 4: Integrar con Endpoint de Creación de Eventos

### Modificar router de calendario para auto-programar notificaciones

```python
# En app/routers/admin/calendar.py

from app.services.notifications import NotificationService
from app.services.notifications.calendar_integration import setup_calendar_event_notifications
import os

# Inicializar servicio (al inicio del archivo)
KAPSO_API_TOKEN = os.getenv("KAPSO_API_TOKEN", "")
KAPSO_API_BASE_URL = os.getenv("KAPSO_API_BASE_URL", "https://app.kapso.ai/api/v1")

whatsapp_service = WhatsAppService(
    api_token=KAPSO_API_TOKEN,
    base_url=KAPSO_API_BASE_URL,
)
notification_service = NotificationService(whatsapp_service=whatsapp_service)

@router.post("/calendar/events")
async def create_calendar_event(
    request: CreateEventRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Crea evento y programa notificaciones automáticamente."""

    # Crear evento (lógica existente)
    new_event = CalendarEvent(
        company_event_id=request.company_event_id,
        company_id=request.company_id,
        event_template_id=request.event_template_id,
        title=request.title,
        description=request.description,
        due_date=request.due_date,
        period_start=request.period_start,
        period_end=request.period_end,
        status="pending",
    )

    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    logger.info(f"✅ Evento creado: {new_event.title}")

    # 🆕 AUTO-PROGRAMAR NOTIFICACIONES
    try:
        notification_ids = await setup_calendar_event_notifications(
            db, new_event, notification_service
        )

        logger.info(f"📱 {len(notification_ids)} notificaciones programadas")

        return {
            "event": new_event,
            "notifications_scheduled": len(notification_ids),
            "notification_ids": notification_ids,
        }

    except Exception as e:
        logger.error(f"❌ Error programando notificaciones: {e}")

        # No fallar el endpoint si las notificaciones fallan
        return {
            "event": new_event,
            "notifications_scheduled": 0,
            "error": str(e),
        }
```

---

## Ejemplo 5: Configurar Scheduler con Systemd (Linux)

### Crear servicio systemd

```ini
# /etc/systemd/system/fizko-notification-scheduler.service

[Unit]
Description=Fizko Notification Scheduler
After=network.target postgresql.service

[Service]
Type=simple
User=fizko
WorkingDirectory=/opt/fizko-v2/backend
Environment="PATH=/opt/fizko-v2/backend/.venv/bin"
Environment="DATABASE_URL=postgresql+asyncpg://user:pass@localhost/fizko"
Environment="KAPSO_API_TOKEN=your-token"
Environment="KAPSO_API_BASE_URL=https://app.kapso.ai/api/v1"

ExecStart=/opt/fizko-v2/backend/.venv/bin/python -m app.services.notifications.scheduler

# Reiniciar si falla
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=append:/var/log/fizko-notifications.log
StandardError=append:/var/log/fizko-notifications.error.log

[Install]
WantedBy=multi-user.target
```

### Crear timer para ejecución periódica

```ini
# /etc/systemd/system/fizko-notification-scheduler.timer

[Unit]
Description=Fizko Notification Scheduler Timer
Requires=fizko-notification-scheduler.service

[Timer]
# Ejecutar cada 5 minutos
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
```

### Habilitar y activar

```bash
sudo systemctl daemon-reload
sudo systemctl enable fizko-notification-scheduler.timer
sudo systemctl start fizko-notification-scheduler.timer

# Ver estado
sudo systemctl status fizko-notification-scheduler.timer

# Ver logs
sudo journalctl -u fizko-notification-scheduler.service -f
```

---

## Ejemplo 6: Preferencias de Usuario

### Usuario configura horario de silencio

```python
import httpx

token = "user-jwt-token"

# Configurar preferencias
response = httpx.put(
    "http://localhost:8089/api/notifications/preferences",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "notifications_enabled": True,
        "quiet_hours_start": "22:00",  # No enviar después de 10 PM
        "quiet_hours_end": "08:00",     # No enviar antes de 8 AM
        "quiet_days": ["saturday", "sunday"],  # No enviar fines de semana
        "muted_categories": [],  # Recibir todas las categorías
        "max_notifications_per_day": 15,
        "min_interval_minutes": 30,  # Mínimo 30 min entre notificaciones
    },
)

print(response.json())
```

---

## Ejemplo 7: Query Analytics - Dashboard

### Obtener estadísticas de notificaciones

```sql
-- Notificaciones enviadas hoy por template
SELECT
    nt.name as template_name,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE nh.status = 'sent') as sent,
    COUNT(*) FILTER (WHERE nh.status = 'failed') as failed
FROM notification_history nh
JOIN notification_templates nt ON nh.notification_template_id = nt.id
WHERE nh.sent_at::date = CURRENT_DATE
GROUP BY nt.name
ORDER BY count DESC;

-- Notificaciones pendientes por prioridad
SELECT
    nt.priority,
    COUNT(*) as count,
    MIN(sn.scheduled_for) as next_scheduled
FROM scheduled_notifications sn
JOIN notification_templates nt ON sn.notification_template_id = nt.id
WHERE sn.status = 'pending'
GROUP BY nt.priority
ORDER BY
    CASE nt.priority
        WHEN 'urgent' THEN 1
        WHEN 'high' THEN 2
        WHEN 'normal' THEN 3
        WHEN 'low' THEN 4
    END;

-- Usuarios con más notificaciones recibidas (último mes)
SELECT
    p.full_name,
    p.phone,
    COUNT(*) as total_notifications,
    COUNT(*) FILTER (WHERE nh.status = 'sent') as delivered
FROM notification_history nh
JOIN profiles p ON nh.user_id = p.id
WHERE nh.sent_at >= NOW() - INTERVAL '30 days'
GROUP BY p.id, p.full_name, p.phone
ORDER BY total_notifications DESC
LIMIT 10;
```

---

## Ejemplo 8: Testing - Enviar Notificación de Prueba

### Script de testing

```python
import asyncio
from app.config.database import AsyncSessionLocal
from app.services.notifications import NotificationService
from app.services.whatsapp.service import WhatsAppService
import os

async def send_test_notification(phone_number: str):
    """Envía una notificación de prueba."""

    whatsapp_service = WhatsAppService(
        api_token=os.getenv("KAPSO_API_TOKEN"),
        base_url=os.getenv("KAPSO_API_BASE_URL"),
    )
    notification_service = NotificationService(whatsapp_service)

    async with AsyncSessionLocal() as db:
        # Usar template de sistema
        template = await notification_service.get_template(
            db, code="system_reminder"
        )

        if not template:
            print("❌ Template 'system_reminder' no encontrado")
            return

        # Programar notificación inmediata
        scheduled = await notification_service.schedule_notification(
            db=db,
            company_id=YOUR_COMPANY_UUID,  # Reemplazar
            template_id=template.id,
            recipients=[{"phone": phone_number}],
            message_context={
                "message": "Esta es una notificación de prueba del sistema Fizko 🤖"
            },
            custom_timing={"type": "immediate"},
        )

        print(f"✅ Notificación programada: {scheduled.id}")

        # Enviar inmediatamente
        result = await notification_service.send_scheduled_notification(
            db, scheduled.id
        )

        print(f"📊 Resultado: {result}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python test_notification.py +56912345678")
        sys.exit(1)

    phone = sys.argv[1]
    asyncio.run(send_test_notification(phone))
```

**Ejecutar:**
```bash
python scripts/test_notification.py +56912345678
```

---

## Ejemplo 9: Webhook para Actualizar Estado (Futuro)

### Recibir webhooks de Kapso para actualizar estado de entrega

```python
# En app/routers/whatsapp/main.py

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Webhook de Kapso - actualiza estado de notificaciones."""

    payload = await request.body()
    signature = request.headers.get("X-Webhook-Signature", "")

    # Validar firma (código existente)
    # ...

    # Parsear evento
    event_data = await request.json()
    event_type = request.headers.get("X-Webhook-Event")

    # 🆕 Actualizar historial de notificaciones
    if event_type == "message.delivered":
        message_id = event_data.get("message_id")

        # Buscar en historial
        from app.db.models import NotificationHistory

        result = await db.execute(
            select(NotificationHistory).where(
                NotificationHistory.whatsapp_message_id == message_id
            )
        )
        history = result.scalar_one_or_none()

        if history:
            history.status = "delivered"
            history.delivered_at = datetime.utcnow()
            await db.commit()

            logger.info(f"✅ Notificación marcada como entregada: {message_id}")

    elif event_type == "message.read":
        message_id = event_data.get("message_id")

        result = await db.execute(
            select(NotificationHistory).where(
                NotificationHistory.whatsapp_message_id == message_id
            )
        )
        history = result.scalar_one_or_none()

        if history:
            history.status = "read"
            history.read_at = datetime.utcnow()
            await db.commit()

            logger.info(f"✅ Notificación marcada como leída: {message_id}")

    return {"status": "ok"}
```

---

## Ejemplo 10: Backup y Restore

### Backup de templates y suscripciones

```bash
# Exportar templates
psql $DATABASE_URL -c "COPY (
    SELECT * FROM notification_templates
) TO STDOUT WITH CSV HEADER" > notification_templates_backup.csv

# Exportar suscripciones
psql $DATABASE_URL -c "COPY (
    SELECT * FROM notification_subscriptions
) TO STDOUT WITH CSV HEADER" > notification_subscriptions_backup.csv
```

### Restore

```bash
# Importar templates
psql $DATABASE_URL -c "COPY notification_templates FROM STDIN WITH CSV HEADER" < notification_templates_backup.csv

# Importar suscripciones
psql $DATABASE_URL -c "COPY notification_subscriptions FROM STDIN WITH CSV HEADER" < notification_subscriptions_backup.csv
```

---

## Tips y Best Practices

### 1. Monitorear Fallos

```sql
-- Notificaciones con intentos fallidos
SELECT
    sn.id,
    sn.scheduled_for,
    sn.send_attempts,
    sn.error_message,
    nt.name
FROM scheduled_notifications sn
JOIN notification_templates nt ON sn.notification_template_id = nt.id
WHERE sn.status = 'failed'
ORDER BY sn.updated_at DESC
LIMIT 20;
```

### 2. Limpiar Historial Antiguo

```sql
-- Archivar historial mayor a 90 días
DELETE FROM notification_history
WHERE sent_at < NOW() - INTERVAL '90 days'
AND status IN ('sent', 'delivered', 'read');
```

### 3. Validar Números de Teléfono

```python
def validate_phone_number(phone: str) -> bool:
    """Valida formato de teléfono chileno."""
    import re

    # Formato: +56912345678 o +56212345678
    pattern = r'^\+56[29]\d{8}$'
    return bool(re.match(pattern, phone))
```

### 4. Rate Limiting

```python
# En NotificationService, antes de enviar
async def _check_rate_limit(
    self,
    db: AsyncSession,
    user_id: UUID,
    company_id: UUID,
) -> bool:
    """Verifica límites de frecuencia."""

    # Obtener preferencias
    prefs = await self._get_user_preferences(db, user_id, company_id)

    if not prefs:
        return True

    # Contar notificaciones hoy
    today = datetime.utcnow().date()

    result = await db.execute(
        select(func.count(NotificationHistory.id)).where(
            and_(
                NotificationHistory.user_id == user_id,
                NotificationHistory.sent_at >= today,
                NotificationHistory.status == 'sent',
            )
        )
    )
    count_today = result.scalar()

    if count_today >= prefs.max_notifications_per_day:
        logger.warning(f"🚫 Rate limit alcanzado para usuario {user_id}")
        return False

    # TODO: Verificar min_interval_minutes

    return True
```

---

## Recursos Adicionales

- **Documentación completa**: `backend/docs/NOTIFICATION_SYSTEM.md`
- **Migración SQL**: `backend/supabase/migrations/013_notification_system.sql`
- **Modelos**: `backend/app/db/models/notifications.py`
- **Servicio**: `backend/app/services/notifications/service.py`
- **Scheduler**: `backend/app/services/notifications/scheduler.py`
- **API**: `backend/app/routers/notifications.py`
