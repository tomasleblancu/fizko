-- Migration: Add auto_assign_to_new_companies field to notification_templates
-- Created: 2025-10-31
-- Description: Adds a boolean field to control automatic assignment of notification templates to newly created companies

-- Add auto_assign_to_new_companies column
ALTER TABLE notification_templates
ADD COLUMN auto_assign_to_new_companies BOOLEAN NOT NULL DEFAULT false;

-- Add comment for documentation
COMMENT ON COLUMN notification_templates.auto_assign_to_new_companies IS
'When true, this notification template will be automatically assigned to all newly created companies via NotificationSubscription';

-- Create index for efficient querying of auto-assign templates
CREATE INDEX idx_notification_templates_auto_assign
ON notification_templates(auto_assign_to_new_companies)
WHERE auto_assign_to_new_companies = true AND is_active = true;
