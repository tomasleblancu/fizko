-- 5. NOTIFICATION EVENT TRIGGERS
CREATE TABLE IF NOT EXISTS notification_event_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    entity_type VARCHAR(50) NOT NULL,
    trigger_event VARCHAR(50) NOT NULL,
    trigger_conditions JSONB,
    notification_template_id UUID NOT NULL REFERENCES notification_templates(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_triggers_entity ON notification_event_triggers(entity_type);
CREATE INDEX IF NOT EXISTS idx_notification_triggers_active ON notification_event_triggers(is_active) WHERE is_active = true;

-- 6. USER NOTIFICATION PREFERENCES
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    notifications_enabled BOOLEAN DEFAULT true,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    quiet_days JSONB,
    muted_categories JSONB,
    muted_templates JSONB,
    max_notifications_per_day INTEGER DEFAULT 20,
    min_interval_minutes INTEGER DEFAULT 30,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_user_notification_prefs_user ON user_notification_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_notification_prefs_enabled ON user_notification_preferences(user_id, notifications_enabled) WHERE notifications_enabled = true;