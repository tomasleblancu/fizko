-- Migration: Add WhatsApp template integration fields to notification_templates
-- Purpose: Enable creation and management of real WhatsApp Business templates via Kapso

-- Add WhatsApp template integration fields
ALTER TABLE notification_templates
ADD COLUMN IF NOT EXISTS create_whatsapp_template BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS whatsapp_template_name VARCHAR(100) UNIQUE,
ADD COLUMN IF NOT EXISTS whatsapp_template_language VARCHAR(10) DEFAULT 'es',
ADD COLUMN IF NOT EXISTS whatsapp_template_category VARCHAR(20) DEFAULT 'UTILITY',
ADD COLUMN IF NOT EXISTS whatsapp_template_status VARCHAR(20),
ADD COLUMN IF NOT EXISTS whatsapp_template_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS whatsapp_header JSONB,
ADD COLUMN IF NOT EXISTS whatsapp_body JSONB,
ADD COLUMN IF NOT EXISTS whatsapp_footer JSONB,
ADD COLUMN IF NOT EXISTS whatsapp_buttons JSONB;

-- Add comments for documentation
COMMENT ON COLUMN notification_templates.create_whatsapp_template IS 'Flag to create a real WhatsApp Business template via Kapso';
COMMENT ON COLUMN notification_templates.whatsapp_template_name IS 'Name of the WhatsApp template (lowercase, underscores)';
COMMENT ON COLUMN notification_templates.whatsapp_template_language IS 'Language code (es, en_US, etc.)';
COMMENT ON COLUMN notification_templates.whatsapp_template_category IS 'Category: UTILITY, MARKETING, or AUTHENTICATION';
COMMENT ON COLUMN notification_templates.whatsapp_template_status IS 'Status: pending, approved, or rejected';
COMMENT ON COLUMN notification_templates.whatsapp_template_id IS 'Template ID returned by Meta';
COMMENT ON COLUMN notification_templates.whatsapp_header IS 'Header component (TEXT or MEDIA format)';
COMMENT ON COLUMN notification_templates.whatsapp_body IS 'Body component with variables';
COMMENT ON COLUMN notification_templates.whatsapp_footer IS 'Footer component (static text)';
COMMENT ON COLUMN notification_templates.whatsapp_buttons IS 'Buttons component (QUICK_REPLY, URL, PHONE_NUMBER)';

-- Create index on whatsapp_template_name for faster lookups
CREATE INDEX IF NOT EXISTS idx_notification_templates_whatsapp_name
ON notification_templates(whatsapp_template_name)
WHERE whatsapp_template_name IS NOT NULL;

-- Create index on whatsapp_template_status for filtering
CREATE INDEX IF NOT EXISTS idx_notification_templates_whatsapp_status
ON notification_templates(whatsapp_template_status)
WHERE whatsapp_template_status IS NOT NULL;

-- Create index for approved templates (most common query)
CREATE INDEX IF NOT EXISTS idx_notification_templates_approved
ON notification_templates(code, whatsapp_template_name)
WHERE create_whatsapp_template = TRUE AND whatsapp_template_status = 'approved';
