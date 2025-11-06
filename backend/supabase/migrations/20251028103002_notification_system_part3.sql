-- 4. NOTIFICATION HISTORY
CREATE TABLE IF NOT EXISTS notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    notification_template_id UUID REFERENCES notification_templates(id) ON DELETE SET NULL,
    scheduled_notification_id UUID REFERENCES scheduled_notifications(id) ON DELETE SET NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    phone_number VARCHAR(20) NOT NULL,
    message_content TEXT NOT NULL,
    status VARCHAR(30) NOT NULL,
    whatsapp_conversation_id VARCHAR(100),
    whatsapp_message_id VARCHAR(100),
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    error_code VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_history_company ON notification_history(company_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_user ON notification_history(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_phone ON notification_history(phone_number);
CREATE INDEX IF NOT EXISTS idx_notification_history_status ON notification_history(status);
CREATE INDEX IF NOT EXISTS idx_notification_history_entity ON notification_history(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_sent_at ON notification_history(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_history_whatsapp_message ON notification_history(whatsapp_message_id) WHERE whatsapp_message_id IS NOT NULL;