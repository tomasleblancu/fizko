-- Migration: Simplify event_rules to be a simple many-to-many relationship
-- Remove redundant recurrence_config and notification_settings
-- Keep custom_config for edge cases where a company needs special handling

-- Drop columns that duplicate event_type configuration
ALTER TABLE event_rules DROP COLUMN IF EXISTS recurrence_config;
ALTER TABLE event_rules DROP COLUMN IF EXISTS notification_settings;

-- custom_config is kept for edge cases (initially empty)
-- It can be used for company-specific overrides like:
-- - Different notification days for this company
-- - Custom approval workflows
-- - Company-specific metadata

-- event_rules now only has:
-- - id (PK)
-- - company_id (FK to companies)
-- - event_type_id (FK to event_types)
-- - is_active (boolean) - whether this company uses this event
-- - custom_config (JSONB) - for edge case overrides (initially {})
-- - created_at, updated_at (timestamps)

-- Add unique constraint to prevent duplicate company-event_type combinations
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'unique_company_event_type'
    ) THEN
        ALTER TABLE event_rules
          ADD CONSTRAINT unique_company_event_type
          UNIQUE (company_id, event_type_id);
    END IF;
END $$;

-- Comment explaining the simplified model
COMMENT ON TABLE event_rules IS 'Many-to-many relationship between companies and event_types. Configuration comes from event_type.default_recurrence. custom_config for edge cases only.';
COMMENT ON COLUMN event_rules.custom_config IS 'Optional overrides for edge cases. Should be empty {} by default. Configuration comes from event_type.';
