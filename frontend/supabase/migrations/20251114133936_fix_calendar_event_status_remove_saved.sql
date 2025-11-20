-- Migration: Fix calendar event status - Remove 'saved', use 'pending' instead
-- Description: The 'saved' status was incorrectly added. The correct initial status is 'pending'.
-- Author: Claude
-- Date: 2025-11-14

-- Step 1: Update all existing events with 'saved' status to 'pending'
UPDATE calendar_events
SET status = 'pending'
WHERE status = 'saved';

-- Step 2: Alter default value for new events to use 'pending' instead of 'saved'
ALTER TABLE calendar_events
ALTER COLUMN status SET DEFAULT 'pending';

-- Note: We cannot directly remove a value from an enum in PostgreSQL without recreating it.
-- Since the 'saved' value is already in production, we'll leave it in the enum type definition
-- but no longer use it in the application. This is safer than recreating the entire enum
-- which could cause downtime.

-- Future cleanup (manual, when safe):
-- To completely remove 'saved' from the enum, you would need to:
-- 1. Create a new enum without 'saved'
-- 2. Alter the column to use the new enum
-- 3. Drop the old enum
-- This is only safe when 100% sure no code references 'saved' anymore.

COMMENT ON COLUMN calendar_events.status IS 'Current status: pending (initial), in_progress, completed, overdue, cancelled. Note: saved was deprecated in favor of pending.';
