-- Migration: Remove WhatsApp template creation fields
-- Keep only whatsapp_template_id for manually created templates

-- Drop columns related to WhatsApp template creation
ALTER TABLE notification_templates
  DROP COLUMN IF EXISTS create_whatsapp_template,
  DROP COLUMN IF EXISTS whatsapp_template_name,
  DROP COLUMN IF EXISTS whatsapp_template_language,
  DROP COLUMN IF EXISTS whatsapp_template_category,
  DROP COLUMN IF EXISTS whatsapp_template_status,
  DROP COLUMN IF EXISTS whatsapp_header,
  DROP COLUMN IF EXISTS whatsapp_body,
  DROP COLUMN IF EXISTS whatsapp_footer,
  DROP COLUMN IF EXISTS whatsapp_buttons;

-- Keep whatsapp_template_id and increase its size for Meta IDs
ALTER TABLE notification_templates
  ALTER COLUMN whatsapp_template_id TYPE VARCHAR(200);

-- Add comment
COMMENT ON COLUMN notification_templates.whatsapp_template_id IS 'WhatsApp template ID from Meta Business Manager (created manually)';
