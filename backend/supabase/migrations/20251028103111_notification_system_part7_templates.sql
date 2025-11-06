-- 9. TEMPLATES PREDEFINIDOS

-- Template: Recordatorio de evento de calendario (1 día antes)
INSERT INTO notification_templates (code, name, description, category, entity_type, message_template, timing_config, priority, can_repeat, max_repeats)
VALUES (
    'calendar_event_reminder_1d',
    'Recordatorio de evento - 1 día antes',
    'Notifica 1 día antes del vencimiento de un evento de calendario',
    'calendar',
    'calendar_event',
    '📅 *Recordatorio:* {{event_title}}

Vence mañana: {{due_date}}

{{description}}

¿Necesitas ayuda? Pregúntame cualquier cosa.',
    '{"type": "relative", "offset_days": -1, "time": "09:00"}'::jsonb,
    'high',
    false,
    1
) ON CONFLICT (code) DO NOTHING;

-- Template: Recordatorio de evento de calendario (3 días antes)
INSERT INTO notification_templates (code, name, description, category, entity_type, message_template, timing_config, priority, can_repeat, max_repeats)
VALUES (
    'calendar_event_reminder_3d',
    'Recordatorio de evento - 3 días antes',
    'Notifica 3 días antes del vencimiento de un evento de calendario',
    'calendar',
    'calendar_event',
    '📅 *Próximamente:* {{event_title}}

Vence en 3 días: {{due_date}}

Te ayudo con cualquier consulta sobre este evento.',
    '{"type": "relative", "offset_days": -3, "time": "10:00"}'::jsonb,
    'normal',
    false,
    1
) ON CONFLICT (code) DO NOTHING;

-- Template: Recordatorio de evento de calendario (7 días antes)
INSERT INTO notification_templates (code, name, description, category, entity_type, message_template, timing_config, priority, can_repeat, max_repeats)
VALUES (
    'calendar_event_reminder_7d',
    'Recordatorio de evento - 7 días antes',
    'Notifica 1 semana antes del vencimiento de un evento de calendario',
    'calendar',
    'calendar_event',
    '📅 *Aviso semanal:* {{event_title}}

Vence en 1 semana: {{due_date}}

Es un buen momento para preparar la documentación necesaria.',
    '{"type": "relative", "offset_days": -7, "time": "09:00"}'::jsonb,
    'normal',
    false,
    1
) ON CONFLICT (code) DO NOTHING;