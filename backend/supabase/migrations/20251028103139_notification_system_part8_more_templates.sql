-- Más templates predefinidos

-- Template: Evento vence HOY
INSERT INTO notification_templates (code, name, description, category, entity_type, message_template, timing_config, priority, can_repeat, max_repeats)
VALUES (
    'calendar_event_due_today',
    'Evento vence HOY',
    'Notifica el día del vencimiento',
    'calendar',
    'calendar_event',
    '⚠️ *¡VENCE HOY!* {{event_title}}

Fecha de vencimiento: {{due_date}}

{{description}}

Si necesitas ayuda, escríbeme.',
    '{"type": "absolute", "time": "08:00"}'::jsonb,
    'urgent',
    true,
    2
) ON CONFLICT (code) DO NOTHING;

-- Template: Evento completado
INSERT INTO notification_templates (code, name, description, category, entity_type, message_template, timing_config, priority, can_repeat, max_repeats)
VALUES (
    'calendar_event_completed',
    'Evento completado',
    'Confirma cuando un evento fue completado exitosamente',
    'calendar',
    'calendar_event',
    '✅ *Completado:* {{event_title}}

Fecha de completación: {{completion_date}}

¡Excelente trabajo! El evento ha sido marcado como completado.',
    '{"type": "immediate"}'::jsonb,
    'low',
    false,
    1
) ON CONFLICT (code) DO NOTHING;

-- Template: F29 próximo a vencer
INSERT INTO notification_templates (code, name, description, category, entity_type, message_template, timing_config, priority, can_repeat, max_repeats)
VALUES (
    'f29_due_soon',
    'F29 próximo a vencer',
    'Recordatorio específico para declaración de F29',
    'tax_document',
    'calendar_event',
    '📋 *Declaración F29 - {{period}}*

Vence: {{due_date}}

Recuerda:
• Revisar ventas y compras del período
• Verificar retenciones
• Calcular PPM si corresponde

¿Necesitas que revise los datos?',
    '{"type": "relative", "offset_days": -2, "time": "09:00"}'::jsonb,
    'high',
    false,
    1
) ON CONFLICT (code) DO NOTHING;

-- Template: Recordatorio general del sistema
INSERT INTO notification_templates (code, name, description, category, entity_type, message_template, timing_config, priority)
VALUES (
    'system_reminder',
    'Recordatorio del sistema',
    'Template genérico para recordatorios del sistema',
    'system',
    NULL,
    '🔔 *Recordatorio*

{{message}}',
    '{"type": "immediate"}'::jsonb,
    'normal'
) ON CONFLICT (code) DO NOTHING;