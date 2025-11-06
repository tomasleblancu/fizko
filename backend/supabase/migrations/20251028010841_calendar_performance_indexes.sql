-- Add performance indexes for calendar operations
-- These indexes optimize the activate/deactivate event endpoints

-- Index for looking up company_events by company_id and event_template_id
-- This is used in the WHERE clause: company_id = X AND event_template_id = Y
CREATE INDEX IF NOT EXISTS idx_company_events_company_template
ON company_events(company_id, event_template_id);

-- Index for looking up active company_events by company
-- This is used when fetching calendar configuration
CREATE INDEX IF NOT EXISTS idx_company_events_company_active
ON company_events(company_id, is_active)
WHERE is_active = true;

-- Index for calendar_events lookup by company_event and status
-- This is used when syncing calendar events
CREATE INDEX IF NOT EXISTS idx_calendar_events_company_event_status
ON calendar_events(company_event_id, status);

-- Index for calendar_events lookup by company_event and due_date
-- This is used when determining which event is "in_progress" (next to expire)
CREATE INDEX IF NOT EXISTS idx_calendar_events_company_event_due_date
ON calendar_events(company_event_id, due_date);
