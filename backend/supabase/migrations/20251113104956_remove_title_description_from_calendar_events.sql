-- Remove redundant title and description columns from calendar_events
-- These fields should come from event_template instead

-- Drop the columns
ALTER TABLE calendar_events
DROP COLUMN IF EXISTS title,
DROP COLUMN IF EXISTS description;

-- Add comment to table explaining the relationship
COMMENT ON TABLE calendar_events IS 'Calendar event instances. Title and description come from event_template via event_template_id foreign key.';
