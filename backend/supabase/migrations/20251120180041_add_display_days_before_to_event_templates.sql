-- Migration: Add display_days_before field to event_templates
-- Description: Adds a field to control how many days before due_date an event should be displayed to users
-- Date: 2025-11-20

-- Add display_days_before column to event_templates
-- This field defines how many days before the due_date the event should start showing to users
-- Default is 30 days, but can be customized per template (e.g., F29 might show 7 days before)
ALTER TABLE event_templates
ADD COLUMN display_days_before INTEGER NOT NULL DEFAULT 30;

-- Add constraint to ensure positive values
ALTER TABLE event_templates
ADD CONSTRAINT check_display_days_before_positive
CHECK (display_days_before > 0);

-- Add comment to document the field
COMMENT ON COLUMN event_templates.display_days_before IS 'Number of days before due_date when this event should be displayed to users';

-- Update existing templates with sensible defaults based on event type
-- F29 events: show 7 days before (more urgent)
UPDATE event_templates
SET display_days_before = 7
WHERE code LIKE 'f29%';

-- Annual events (F22): show 30 days before
UPDATE event_templates
SET display_days_before = 30
WHERE code LIKE 'f22%' OR category = 'impuesto_anual';

-- Previred: show 5 days before (monthly, urgent)
UPDATE event_templates
SET display_days_before = 5
WHERE code LIKE 'previred%';
