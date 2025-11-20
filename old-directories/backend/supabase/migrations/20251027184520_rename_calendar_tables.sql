-- Rename tables to reflect correct architecture:
-- event_types → event_templates (global templates)
-- event_rules → company_events (company-template relationship)
-- calendar_events stays the same (concrete event instances)

-- Rename event_types to event_templates
ALTER TABLE event_types RENAME TO event_templates;

-- Rename event_rules to company_events
ALTER TABLE event_rules RENAME TO company_events;

-- Update foreign key references in calendar_events
ALTER TABLE calendar_events
  RENAME COLUMN event_rule_id TO company_event_id;

ALTER TABLE calendar_events
  RENAME COLUMN event_type_id TO event_template_id;

-- Update constraint names to match new table names
ALTER TABLE company_events
  RENAME CONSTRAINT event_rules_pkey TO company_events_pkey;

ALTER TABLE company_events
  RENAME CONSTRAINT event_rules_company_id_fkey TO company_events_company_id_fkey;

ALTER TABLE company_events
  RENAME CONSTRAINT event_rules_event_type_id_fkey TO company_events_event_template_id_fkey;

ALTER TABLE company_events
  RENAME CONSTRAINT unique_company_event_type TO unique_company_event_template;

ALTER TABLE company_events
  RENAME COLUMN event_type_id TO event_template_id;

-- Update calendar_events foreign key constraints
ALTER TABLE calendar_events
  DROP CONSTRAINT IF EXISTS calendar_events_event_rule_id_fkey;

ALTER TABLE calendar_events
  ADD CONSTRAINT calendar_events_company_event_id_fkey
  FOREIGN KEY (company_event_id) REFERENCES company_events(id) ON DELETE CASCADE;

ALTER TABLE calendar_events
  DROP CONSTRAINT IF EXISTS calendar_events_event_type_id_fkey;

ALTER TABLE calendar_events
  ADD CONSTRAINT calendar_events_event_template_id_fkey
  FOREIGN KEY (event_template_id) REFERENCES event_templates(id) ON DELETE CASCADE;

-- Update table comments to reflect architecture
COMMENT ON TABLE event_templates IS 'Global templates for tax events (F29, F22, etc.). One record per tax event type.';

COMMENT ON TABLE company_events IS 'Many-to-many relationship between companies and event_templates. Indicates which tax events apply to each company.';

COMMENT ON TABLE calendar_events IS 'Concrete instances of events with specific due dates. Contains status, notes, and company-specific data.';

-- Update column comments
COMMENT ON COLUMN company_events.event_template_id IS 'Reference to the global event template';
COMMENT ON COLUMN company_events.is_active IS 'Whether this event is currently active for the company';
COMMENT ON COLUMN company_events.custom_config IS 'Optional overrides for edge cases (usually empty)';

COMMENT ON COLUMN calendar_events.company_event_id IS 'Reference to the company-event relationship';
COMMENT ON COLUMN calendar_events.event_template_id IS 'Denormalized reference to event template for quick lookups';
COMMENT ON COLUMN calendar_events.status IS 'Current status: pending, completed, overdue';
