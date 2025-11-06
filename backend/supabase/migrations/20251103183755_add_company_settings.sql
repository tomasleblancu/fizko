-- Migration: Add company_settings table
-- Description: General company business settings and configuration

-- Create company_settings table
CREATE TABLE IF NOT EXISTS company_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL UNIQUE REFERENCES companies(id) ON DELETE CASCADE,

    -- Business Operations Settings
    has_formal_employees BOOLEAN DEFAULT NULL,  -- ¿Tiene empleados con contrato formal?
    has_imports BOOLEAN DEFAULT NULL,           -- ¿Realiza importaciones?
    has_exports BOOLEAN DEFAULT NULL,           -- ¿Realiza exportaciones?
    has_lease_contracts BOOLEAN DEFAULT NULL,   -- ¿Tiene contratos de arriendo?

    -- Configuration tracking
    is_initial_setup_complete BOOLEAN DEFAULT FALSE NOT NULL,
    initial_setup_completed_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Index for performance
CREATE INDEX idx_company_settings_company_id ON company_settings(company_id);

-- Comment on table
COMMENT ON TABLE company_settings IS 'General company business settings and configuration';

-- Comments on columns
COMMENT ON COLUMN company_settings.has_formal_employees IS '¿Tiene empleados con contrato de trabajo formal?';
COMMENT ON COLUMN company_settings.has_imports IS '¿Realiza importaciones?';
COMMENT ON COLUMN company_settings.has_exports IS '¿Realiza exportaciones?';
COMMENT ON COLUMN company_settings.has_lease_contracts IS '¿Tiene contratos de arriendo?';
COMMENT ON COLUMN company_settings.is_initial_setup_complete IS 'Flag indicating if initial setup wizard has been completed';
COMMENT ON COLUMN company_settings.initial_setup_completed_at IS 'Timestamp when initial setup was completed';

-- Enable Row Level Security
ALTER TABLE company_settings ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can view settings for their active company
CREATE POLICY "Users can view their company settings"
    ON company_settings FOR SELECT
    USING (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

-- Users can insert settings for their active company
CREATE POLICY "Users can insert their company settings"
    ON company_settings FOR INSERT
    WITH CHECK (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

-- Users can update settings for their active company
CREATE POLICY "Users can update their company settings"
    ON company_settings FOR UPDATE
    USING (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

-- Trigger for updated_at timestamp
CREATE TRIGGER update_company_settings_updated_at
    BEFORE UPDATE ON company_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
