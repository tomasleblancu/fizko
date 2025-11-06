-- Migration: Add extra_metadata column to notification_event_triggers
-- Created: 2025-10-30
-- Fixes: Missing column error when deleting notification templates

-- Add extra_metadata column to notification_event_triggers
ALTER TABLE notification_event_triggers
ADD COLUMN IF NOT EXISTS extra_metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Add comment to explain the column
COMMENT ON COLUMN notification_event_triggers.extra_metadata IS 'Additional metadata for the event trigger';
