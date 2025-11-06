-- 3. SCHEDULED NOTIFICATIONS
CREATE TABLE IF NOT EXISTS scheduled_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    notification_template_id UUID NOT NULL REFERENCES notification_templates(id) ON DELETE CASCADE,
    entity_type VARCHAR(50),
    entity_id UUID,
    recipients JSONB NOT NULL,
    message_content TEXT NOT NULL,
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(30) DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE,
    send_attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    send_results JSONB,
    is_repeat BOOLEAN DEFAULT false,
    repeat_of UUID REFERENCES scheduled_notifications(id) ON DELETE SET NULL,
    repeat_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheduled_notifications_company ON scheduled_notifications(company_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_notifications_status ON scheduled_notifications(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_notifications_scheduled_for ON scheduled_notifications(scheduled_for) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_scheduled_notifications_entity ON scheduled_notifications(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_notifications_ready ON scheduled_notifications(status, scheduled_for) WHERE status = 'pending';