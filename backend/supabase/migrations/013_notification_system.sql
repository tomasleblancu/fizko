-- ============================================================================
-- SISTEMA DE NOTIFICACIONES POR WHATSAPP
-- ============================================================================
-- Soporta notificaciones vinculadas a:
-- - Eventos de calendario (tax deadlines, reminders)
-- - Documentos tributarios (F29, F22)
-- - Tareas de personal (payroll deadlines)
-- - Eventos custom de la aplicación
-- ============================================================================

-- ============================================================================
-- 1. NOTIFICATION TEMPLATES
-- ============================================================================
-- Plantillas reutilizables de notificaciones
-- Define el contenido, timing y configuración de notificaciones

CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificación
    code VARCHAR(100) UNIQUE NOT NULL,  -- ej: "calendar_event_reminder_1d", "f29_due_soon"
    name TEXT NOT NULL,
    description TEXT,

    -- Categoría
    category VARCHAR(50) NOT NULL,  -- 'calendar', 'tax_document', 'payroll', 'system', 'custom'

    -- Tipo de entidad asociada (para vincular con otras tablas)
    entity_type VARCHAR(50),  -- 'calendar_event', 'form29', 'payroll', 'task', null

    -- Contenido del mensaje
    -- Soporta variables: {{company_name}}, {{event_title}}, {{due_date}}, etc.
    message_template TEXT NOT NULL,

    -- Configuración de timing
    -- Ejemplos:
    -- {"type": "relative", "offset_days": -1, "time": "09:00"}  -> 1 día antes a las 9am
    -- {"type": "relative", "offset_days": -7, "time": "10:00"}  -> 7 días antes a las 10am
    -- {"type": "absolute", "time": "17:00"}  -> El día del evento a las 5pm
    -- {"type": "immediate"}  -> Enviar inmediatamente
    timing_config JSONB NOT NULL DEFAULT '{"type": "immediate"}'::jsonb,

    -- Configuración de prioridad y repetición
    priority VARCHAR(20) DEFAULT 'normal',  -- 'low', 'normal', 'high', 'urgent'
    can_repeat BOOLEAN DEFAULT false,  -- Si puede enviarse múltiples veces
    max_repeats INTEGER DEFAULT 1,  -- Máximo número de envíos
    repeat_interval_hours INTEGER,  -- Intervalo entre repeticiones (si aplica)

    -- Condiciones para envío (opcional)
    -- Ejemplo: {"event_status": ["pending", "in_progress"], "days_to_due": {"lte": 7}}
    send_conditions JSONB,

    -- Estado
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notification_templates_category ON notification_templates(category);
CREATE INDEX idx_notification_templates_entity_type ON notification_templates(entity_type);
CREATE INDEX idx_notification_templates_active ON notification_templates(is_active) WHERE is_active = true;


-- ============================================================================
-- 2. NOTIFICATION SUBSCRIPTIONS
-- ============================================================================
-- Define qué notificaciones están activas para cada empresa
-- Permite a las empresas suscribirse/desuscribirse de notificaciones

CREATE TABLE IF NOT EXISTS notification_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relaciones
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    notification_template_id UUID NOT NULL REFERENCES notification_templates(id) ON DELETE CASCADE,

    -- Configuración personalizada (sobrescribe template si existe)
    custom_timing_config JSONB,  -- Permite personalizar el timing
    custom_message_template TEXT,  -- Permite personalizar el mensaje

    -- Estado
    is_enabled BOOLEAN DEFAULT true,

    -- Preferencias de canal (futuro: email, push, etc.)
    channels JSONB DEFAULT '["whatsapp"]'::jsonb,

    -- Filtros adicionales (opcional)
    -- Ejemplo: {"event_categories": ["impuesto_mensual"], "min_priority": "normal"}
    filters JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(company_id, notification_template_id)
);

CREATE INDEX idx_notification_subscriptions_company ON notification_subscriptions(company_id);
CREATE INDEX idx_notification_subscriptions_template ON notification_subscriptions(notification_template_id);
CREATE INDEX idx_notification_subscriptions_enabled ON notification_subscriptions(company_id, is_enabled)
    WHERE is_enabled = true;


-- ============================================================================
-- 3. SCHEDULED NOTIFICATIONS
-- ============================================================================
-- Notificaciones programadas para envío futuro
-- El scheduler (manual o Celery) procesa esta tabla

CREATE TABLE IF NOT EXISTS scheduled_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relaciones
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    notification_template_id UUID NOT NULL REFERENCES notification_templates(id) ON DELETE CASCADE,

    -- Entidad relacionada (flexible - puede ser null para notificaciones custom)
    entity_type VARCHAR(50),  -- 'calendar_event', 'form29', etc.
    entity_id UUID,  -- ID de la entidad (calendar_event.id, form29.id, etc.)

    -- Destinatarios
    -- Puede ser una lista de user_ids o phone_numbers
    recipients JSONB NOT NULL,  -- [{"user_id": "uuid", "phone": "+56..."}, ...]

    -- Contenido del mensaje (ya renderizado con variables)
    message_content TEXT NOT NULL,

    -- Timing
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,  -- Cuándo debe enviarse
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Cuándo fue programada

    -- Estado
    status VARCHAR(30) DEFAULT 'pending',
    -- 'pending': Esperando envío
    -- 'processing': En proceso de envío
    -- 'sent': Enviada exitosamente
    -- 'failed': Falló el envío
    -- 'cancelled': Cancelada manualmente
    -- 'skipped': Omitida por condiciones

    -- Resultados del envío
    sent_at TIMESTAMP WITH TIME ZONE,
    send_attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,

    -- Datos del envío exitoso (IDs de Kapso, etc.)
    send_results JSONB,  -- {"conversation_id": "...", "message_id": "...", ...}

    -- Repetición (si aplica)
    is_repeat BOOLEAN DEFAULT false,
    repeat_of UUID REFERENCES scheduled_notifications(id) ON DELETE SET NULL,
    repeat_count INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_scheduled_notifications_company ON scheduled_notifications(company_id);
CREATE INDEX idx_scheduled_notifications_status ON scheduled_notifications(status);
CREATE INDEX idx_scheduled_notifications_scheduled_for ON scheduled_notifications(scheduled_for)
    WHERE status = 'pending';
CREATE INDEX idx_scheduled_notifications_entity ON scheduled_notifications(entity_type, entity_id);

-- Índice compuesto para el scheduler: buscar notificaciones pendientes listas para enviar
CREATE INDEX idx_scheduled_notifications_ready ON scheduled_notifications(status, scheduled_for)
    WHERE status = 'pending';


-- ============================================================================
-- 4. NOTIFICATION HISTORY
-- ============================================================================
-- Historial completo de todas las notificaciones enviadas
-- Para auditoría, analytics y debugging

CREATE TABLE IF NOT EXISTS notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relaciones
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    notification_template_id UUID REFERENCES notification_templates(id) ON DELETE SET NULL,
    scheduled_notification_id UUID REFERENCES scheduled_notifications(id) ON DELETE SET NULL,

    -- Entidad relacionada
    entity_type VARCHAR(50),
    entity_id UUID,

    -- Destinatario
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    phone_number VARCHAR(20) NOT NULL,

    -- Contenido
    message_content TEXT NOT NULL,

    -- Resultado del envío
    status VARCHAR(30) NOT NULL,  -- 'sent', 'failed', 'delivered', 'read'

    -- Datos de Kapso/WhatsApp
    whatsapp_conversation_id VARCHAR(100),
    whatsapp_message_id VARCHAR(100),

    -- Timing
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,

    -- Error (si aplica)
    error_message TEXT,
    error_code VARCHAR(50),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notification_history_company ON notification_history(company_id);
CREATE INDEX idx_notification_history_user ON notification_history(user_id);
CREATE INDEX idx_notification_history_phone ON notification_history(phone_number);
CREATE INDEX idx_notification_history_status ON notification_history(status);
CREATE INDEX idx_notification_history_entity ON notification_history(entity_type, entity_id);
CREATE INDEX idx_notification_history_sent_at ON notification_history(sent_at DESC);

-- Índice para tracking de mensajes de WhatsApp
CREATE INDEX idx_notification_history_whatsapp_message ON notification_history(whatsapp_message_id)
    WHERE whatsapp_message_id IS NOT NULL;


-- ============================================================================
-- 5. NOTIFICATION EVENT TRIGGERS
-- ============================================================================
-- Define triggers automáticos para generar notificaciones
-- Ejemplo: cuando un calendar_event cambia a "in_progress", crear notificación

CREATE TABLE IF NOT EXISTS notification_event_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificación
    name TEXT NOT NULL,
    description TEXT,

    -- Configuración del trigger
    entity_type VARCHAR(50) NOT NULL,  -- 'calendar_event', 'form29', etc.
    trigger_event VARCHAR(50) NOT NULL,  -- 'created', 'status_changed', 'due_date_approaching', etc.

    -- Condiciones para activar el trigger
    -- Ejemplo: {"status": "in_progress", "days_to_due": {"lte": 3}}
    trigger_conditions JSONB,

    -- Template de notificación a usar
    notification_template_id UUID NOT NULL REFERENCES notification_templates(id) ON DELETE CASCADE,

    -- Estado
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notification_triggers_entity ON notification_event_triggers(entity_type);
CREATE INDEX idx_notification_triggers_active ON notification_event_triggers(is_active)
    WHERE is_active = true;


-- ============================================================================
-- 6. USER NOTIFICATION PREFERENCES
-- ============================================================================
-- Preferencias individuales de notificaciones por usuario
-- Permite a usuarios silenciar notificaciones, cambiar horarios, etc.

CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relaciones
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,

    -- Configuración global
    notifications_enabled BOOLEAN DEFAULT true,

    -- Horario de notificaciones (no enviar fuera de este rango)
    quiet_hours_start TIME,  -- ej: 22:00
    quiet_hours_end TIME,    -- ej: 08:00

    -- Días de la semana (no enviar en estos días)
    quiet_days JSONB,  -- ["saturday", "sunday"]

    -- Categorías silenciadas
    muted_categories JSONB,  -- ["system", "low_priority"]

    -- Templates específicos silenciados
    muted_templates JSONB,  -- [template_id_1, template_id_2, ...]

    -- Frecuencia máxima (para evitar spam)
    max_notifications_per_day INTEGER DEFAULT 20,
    min_interval_minutes INTEGER DEFAULT 30,  -- Mínimo intervalo entre notificaciones

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, company_id)
);

CREATE INDEX idx_user_notification_prefs_user ON user_notification_preferences(user_id);
CREATE INDEX idx_user_notification_prefs_enabled ON user_notification_preferences(user_id, notifications_enabled)
    WHERE notifications_enabled = true;


-- ============================================================================
-- 7. VIEWS ÚTILES
-- ============================================================================

-- Vista: Notificaciones pendientes listas para enviar (respetando preferencias de usuario)
CREATE OR REPLACE VIEW pending_notifications_ready AS
SELECT
    sn.id,
    sn.company_id,
    sn.notification_template_id,
    sn.entity_type,
    sn.entity_id,
    sn.recipients,
    sn.message_content,
    sn.scheduled_for,
    sn.send_attempts,
    nt.name as template_name,
    nt.priority,
    nt.category
FROM scheduled_notifications sn
JOIN notification_templates nt ON sn.notification_template_id = nt.id
WHERE sn.status = 'pending'
  AND sn.scheduled_for <= NOW()
  AND sn.send_attempts < 3  -- Máximo 3 intentos
ORDER BY nt.priority DESC, sn.scheduled_for ASC;


-- Vista: Estadísticas de notificaciones por empresa
CREATE OR REPLACE VIEW notification_stats_by_company AS
SELECT
    company_id,
    COUNT(*) as total_notifications,
    COUNT(*) FILTER (WHERE status = 'sent') as sent_count,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
    COUNT(*) FILTER (WHERE status = 'delivered') as delivered_count,
    COUNT(*) FILTER (WHERE status = 'read') as read_count,
    DATE_TRUNC('day', sent_at) as date
FROM notification_history
WHERE sent_at >= NOW() - INTERVAL '30 days'
GROUP BY company_id, DATE_TRUNC('day', sent_at);


-- ============================================================================
-- 8. FUNCIONES AUXILIARES
-- ============================================================================

-- Función: Actualizar timestamp de updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
CREATE TRIGGER update_notification_templates_updated_at
    BEFORE UPDATE ON notification_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_subscriptions_updated_at
    BEFORE UPDATE ON notification_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scheduled_notifications_updated_at
    BEFORE UPDATE ON scheduled_notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_event_triggers_updated_at
    BEFORE UPDATE ON notification_event_triggers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_notification_preferences_updated_at
    BEFORE UPDATE ON user_notification_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- 9. DATOS INICIALES - TEMPLATES PREDEFINIDOS
-- ============================================================================

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
);

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
);

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
);

-- Template: Evento vencido (mismo día)
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
);

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
);

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
);

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
);


-- ============================================================================
-- 10. COMENTARIOS Y DOCUMENTACIÓN
-- ============================================================================

COMMENT ON TABLE notification_templates IS 'Plantillas reutilizables de notificaciones con contenido y configuración de timing';
COMMENT ON TABLE notification_subscriptions IS 'Suscripciones de empresas a notificaciones específicas';
COMMENT ON TABLE scheduled_notifications IS 'Cola de notificaciones programadas para envío futuro (procesada por scheduler)';
COMMENT ON TABLE notification_history IS 'Historial completo de notificaciones enviadas para auditoría y analytics';
COMMENT ON TABLE notification_event_triggers IS 'Triggers automáticos que generan notificaciones basados en eventos del sistema';
COMMENT ON TABLE user_notification_preferences IS 'Preferencias individuales de notificaciones por usuario (horarios, categorías, etc.)';

COMMENT ON COLUMN notification_templates.timing_config IS 'Configuración JSON del timing: {"type": "relative", "offset_days": -1, "time": "09:00"} o {"type": "absolute", "time": "17:00"} o {"type": "immediate"}';
COMMENT ON COLUMN notification_templates.send_conditions IS 'Condiciones JSON para envío: {"event_status": ["pending"], "days_to_due": {"lte": 7}}';
COMMENT ON COLUMN scheduled_notifications.status IS 'Estados: pending, processing, sent, failed, cancelled, skipped';
COMMENT ON COLUMN scheduled_notifications.recipients IS 'Array JSON de destinatarios: [{"user_id": "uuid", "phone": "+56..."}]';
