-- ============================================================================
-- SISTEMA DE NOTIFICACIONES POR WHATSAPP
-- ============================================================================

-- 1. NOTIFICATION TEMPLATES
CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    message_template TEXT NOT NULL,
    timing_config JSONB NOT NULL DEFAULT '{"type": "immediate"}'::jsonb,
    priority VARCHAR(20) DEFAULT 'normal',
    can_repeat BOOLEAN DEFAULT false,
    max_repeats INTEGER DEFAULT 1,
    repeat_interval_hours INTEGER,
    send_conditions JSONB,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_templates_category ON notification_templates(category);
CREATE INDEX IF NOT EXISTS idx_notification_templates_entity_type ON notification_templates(entity_type);
CREATE INDEX IF NOT EXISTS idx_notification_templates_active ON notification_templates(is_active) WHERE is_active = true;

-- 2. NOTIFICATION SUBSCRIPTIONS
CREATE TABLE IF NOT EXISTS notification_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    notification_template_id UUID NOT NULL REFERENCES notification_templates(id) ON DELETE CASCADE,
    custom_timing_config JSONB,
    custom_message_template TEXT,
    is_enabled BOOLEAN DEFAULT true,
    channels JSONB DEFAULT '["whatsapp"]'::jsonb,
    filters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id, notification_template_id)
);

CREATE INDEX IF NOT EXISTS idx_notification_subscriptions_company ON notification_subscriptions(company_id);
CREATE INDEX IF NOT EXISTS idx_notification_subscriptions_template ON notification_subscriptions(notification_template_id);
CREATE INDEX IF NOT EXISTS idx_notification_subscriptions_enabled ON notification_subscriptions(company_id, is_enabled) WHERE is_enabled = true;