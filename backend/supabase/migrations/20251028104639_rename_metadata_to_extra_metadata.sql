-- Migration: Rename metadata columns to extra_metadata to avoid SQLAlchemy reserved name conflict
-- Created: 2025-10-28

-- Rename metadata column in notification_templates
ALTER TABLE notification_templates
RENAME COLUMN metadata TO extra_metadata;

-- Rename metadata column in scheduled_notifications
ALTER TABLE scheduled_notifications
RENAME COLUMN metadata TO extra_metadata;

-- Rename metadata column in notification_history
ALTER TABLE notification_history
RENAME COLUMN metadata TO extra_metadata;

-- Add comment to explain the naming
COMMENT ON COLUMN notification_templates.extra_metadata IS 'Additional metadata (renamed from metadata to avoid SQLAlchemy reserved name)';
COMMENT ON COLUMN scheduled_notifications.extra_metadata IS 'Additional metadata (renamed from metadata to avoid SQLAlchemy reserved name)';
COMMENT ON COLUMN notification_history.extra_metadata IS 'Additional metadata (renamed from metadata to avoid SQLAlchemy reserved name)';
