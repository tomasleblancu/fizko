-- =====================================================================
-- Add UF-Based Pricing System
-- =====================================================================
-- This migration adds:
-- 1. UF value tracking table (daily UF values from Banco Central)
-- 2. UF prices to subscription plans
-- 3. Function to get current UF value
-- 4. Function to convert UF to CLP
-- =====================================================================

-- =====================================================================
-- UF Value Tracking Table
-- =====================================================================
CREATE TABLE IF NOT EXISTS uf_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Date and value
    date DATE UNIQUE NOT NULL,
    value NUMERIC(10, 2) NOT NULL,

    -- Source tracking
    source TEXT DEFAULT 'manual',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uf_value_positive CHECK (value > 0)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_uf_values_date ON uf_values(date DESC);

-- Comment
COMMENT ON TABLE uf_values IS 'Daily UF (Unidad de Fomento) values from Banco Central de Chile';

-- =====================================================================
-- Add UF Prices to Subscription Plans
-- =====================================================================
ALTER TABLE subscription_plans
    ADD COLUMN IF NOT EXISTS price_monthly_uf NUMERIC(6, 2),
    ADD COLUMN IF NOT EXISTS price_yearly_uf NUMERIC(6, 2);

COMMENT ON COLUMN subscription_plans.price_monthly_uf IS 'Monthly price in UF (will be converted to CLP using current UF value)';
COMMENT ON COLUMN subscription_plans.price_yearly_uf IS 'Yearly price in UF (will be converted to CLP using current UF value)';

-- =====================================================================
-- Update Subscription Plans with UF Prices
-- =====================================================================
UPDATE subscription_plans
SET
    price_monthly_uf = 0.25,
    price_yearly_uf = 2.5,
    updated_at = now()
WHERE code = 'basic';

UPDATE subscription_plans
SET
    price_monthly_uf = 1.0,
    price_yearly_uf = 10.0,
    updated_at = now()
WHERE code = 'pro';

-- =====================================================================
-- Seed Current UF Value (Nov 2024)
-- =====================================================================
-- This should be updated regularly via API or manual entry
INSERT INTO uf_values (date, value, source)
VALUES
    (CURRENT_DATE, 37500.00, 'manual')
ON CONFLICT (date) DO UPDATE
    SET value = EXCLUDED.value,
        source = EXCLUDED.source,
        updated_at = now();

-- =====================================================================
-- Helper Functions
-- =====================================================================

-- Function to get current UF value
CREATE OR REPLACE FUNCTION get_current_uf_value()
RETURNS NUMERIC AS $$
DECLARE
    current_value NUMERIC;
BEGIN
    -- Get the most recent UF value
    SELECT value INTO current_value
    FROM uf_values
    ORDER BY date DESC
    LIMIT 1;

    -- If no value found, return a default (this should never happen in production)
    IF current_value IS NULL THEN
        RAISE WARNING 'No UF value found in database, using fallback value';
        RETURN 37500.00;
    END IF;

    RETURN current_value;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_current_uf_value IS 'Get the most recent UF value from uf_values table';

-- Function to convert UF to CLP
CREATE OR REPLACE FUNCTION uf_to_clp(uf_amount NUMERIC)
RETURNS NUMERIC AS $$
BEGIN
    RETURN ROUND(uf_amount * get_current_uf_value(), 0);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION uf_to_clp IS 'Convert UF amount to CLP using current UF value';

-- =====================================================================
-- View for Plans with Calculated CLP Prices
-- =====================================================================
CREATE OR REPLACE VIEW subscription_plans_with_clp AS
SELECT
    sp.id,
    sp.code,
    sp.name,
    sp.tagname,
    sp.tagline,
    sp.description,

    -- UF prices (source of truth)
    sp.price_monthly_uf,
    sp.price_yearly_uf,

    -- Calculated CLP prices (for display)
    uf_to_clp(sp.price_monthly_uf) AS price_monthly,
    uf_to_clp(sp.price_yearly_uf) AS price_yearly,

    -- Current UF value used for calculation
    get_current_uf_value() AS current_uf_value,

    sp.currency,
    sp.trial_days,
    sp.features,
    sp.display_order,
    sp.is_active,
    sp.is_public,
    sp.created_at,
    sp.updated_at
FROM subscription_plans sp
WHERE sp.price_monthly_uf IS NOT NULL;

COMMENT ON VIEW subscription_plans_with_clp IS 'Subscription plans with real-time CLP prices calculated from UF values';

-- =====================================================================
-- RLS Policies for UF Values
-- =====================================================================
ALTER TABLE uf_values ENABLE ROW LEVEL SECURITY;

-- UF values are public (read-only)
CREATE POLICY "UF values are viewable by all authenticated users" ON uf_values
    FOR SELECT USING (auth.role() = 'authenticated');

-- Only service role can insert/update UF values
CREATE POLICY "Service role can manage UF values" ON uf_values
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- =====================================================================
-- Grant Permissions
-- =====================================================================
GRANT SELECT ON uf_values TO authenticated;
GRANT ALL ON uf_values TO service_role;
GRANT SELECT ON subscription_plans_with_clp TO authenticated, service_role;

-- =====================================================================
-- Update Trigger for UF Values
-- =====================================================================
CREATE TRIGGER update_uf_values_updated_at
    BEFORE UPDATE ON uf_values
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_updated_at();
