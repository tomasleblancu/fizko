-- =====================================================================
-- Subscription System
-- =====================================================================
-- This migration creates the complete subscription billing system:
-- - Subscription plans (pricing tiers)
-- - Company subscriptions
-- - Usage tracking per billing period
-- - Invoice/payment history
--
-- Author: AI Assistant
-- Date: 2025-11-06
-- =====================================================================

-- =====================================================================
-- Subscription Plans
-- =====================================================================
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Plan identification
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    tagname TEXT,
    tagline TEXT,
    description TEXT,

    -- Pricing
    price_monthly NUMERIC(10, 2) NOT NULL DEFAULT 0,
    price_yearly NUMERIC(10, 2) NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'CLP',

    -- Trial
    trial_days INTEGER NOT NULL DEFAULT 0,

    -- Features (JSONB for flexibility)
    features JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Display
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_public BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index on code for fast lookups
CREATE INDEX IF NOT EXISTS idx_subscription_plans_code ON subscription_plans(code);
CREATE INDEX IF NOT EXISTS idx_subscription_plans_active ON subscription_plans(is_active) WHERE is_active = true;

-- Comment on table
COMMENT ON TABLE subscription_plans IS 'Subscription plan definitions with pricing and feature limits';
COMMENT ON COLUMN subscription_plans.features IS 'JSONB with feature flags and limits: {max_monthly_transactions: 100, has_whatsapp: false, ...}';

-- =====================================================================
-- Subscriptions
-- =====================================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL UNIQUE REFERENCES companies(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),

    -- Status
    status TEXT NOT NULL DEFAULT 'trialing',

    -- Billing
    interval TEXT NOT NULL DEFAULT 'monthly',
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,

    -- Trial
    trial_start TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,

    -- Cancellation
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT false,
    canceled_at TIMESTAMPTZ,

    -- Payment provider integration
    payment_provider TEXT,
    external_subscription_id TEXT,
    payment_method_id TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT subscriptions_status_check CHECK (
        status IN ('trialing', 'active', 'past_due', 'canceled', 'incomplete')
    ),
    CONSTRAINT subscriptions_interval_check CHECK (
        interval IN ('monthly', 'yearly')
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_company_id ON subscriptions(company_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_id ON subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_period_end ON subscriptions(current_period_end);

-- Comment on table
COMMENT ON TABLE subscriptions IS 'Company subscriptions to billing plans (1:1 with companies)';
COMMENT ON COLUMN subscriptions.status IS 'Subscription status: trialing, active, past_due, canceled, incomplete';

-- =====================================================================
-- Subscription Usage Tracking
-- =====================================================================
CREATE TABLE IF NOT EXISTS subscription_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,

    -- Period
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,

    -- Usage counters
    monthly_transactions_count INTEGER NOT NULL DEFAULT 0,
    active_users_count INTEGER NOT NULL DEFAULT 0,
    api_calls_count INTEGER NOT NULL DEFAULT 0,
    whatsapp_messages_count INTEGER NOT NULL DEFAULT 0,

    -- Additional usage data (flexible)
    usage_data JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT usage_counters_non_negative CHECK (
        monthly_transactions_count >= 0 AND
        active_users_count >= 0 AND
        api_calls_count >= 0 AND
        whatsapp_messages_count >= 0
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subscription_usage_subscription_id ON subscription_usage(subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscription_usage_period ON subscription_usage(subscription_id, period_start);
CREATE INDEX IF NOT EXISTS idx_subscription_usage_period_range ON subscription_usage(period_start, period_end);

-- Comment on table
COMMENT ON TABLE subscription_usage IS 'Usage tracking per subscription billing period';

-- =====================================================================
-- Invoices
-- =====================================================================
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,

    -- Invoice details
    invoice_number TEXT UNIQUE NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'CLP',

    -- Status
    status TEXT NOT NULL DEFAULT 'draft',

    -- Dates
    invoice_date DATE NOT NULL,
    due_date DATE,
    paid_at TIMESTAMPTZ,

    -- Payment provider
    external_invoice_id TEXT,
    payment_intent_id TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT invoices_status_check CHECK (
        status IN ('draft', 'open', 'paid', 'void', 'uncollectible')
    ),
    CONSTRAINT invoices_amount_positive CHECK (amount >= 0)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_invoices_subscription_id ON invoices(subscription_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);

-- Comment on table
COMMENT ON TABLE invoices IS 'Invoice and payment records for subscriptions';

-- =====================================================================
-- Seed Default Plans
-- =====================================================================
INSERT INTO subscription_plans (code, name, tagname, tagline, description, price_monthly, price_yearly, trial_days, features, display_order) VALUES
(
    'basic',
    'Plan Básico',
    'Conecta',
    'Controla tu situación tributaria',
    'Perfecto para pequeños negocios y emprendedores',
    19990,
    199900,
    14,
    '{
        "max_monthly_transactions": 200,
        "max_users": 2,
        "has_whatsapp": true,
        "has_ai_assistant": true,
        "has_sii_sync": true,
        "has_advanced_reports": false,
        "has_api_access": false,
        "support_level": "email"
    }'::jsonb,
    1
),
(
    'pro',
    'Plan Profesional',
    'Cumple',
    'Controla y Cumple con tus obligaciones tributarias',
    'Para empresas en crecimiento con necesidades avanzadas',
    49990,
    499900,
    14,
    '{
        "max_monthly_transactions": null,
        "max_users": 5,
        "has_whatsapp": true,
        "has_ai_assistant": true,
        "has_sii_sync": true,
        "has_advanced_reports": true,
        "has_api_access": true,
        "support_level": "priority"
    }'::jsonb,
    2
)
ON CONFLICT (code) DO NOTHING;

-- =====================================================================
-- RLS Policies
-- =====================================================================

-- Enable RLS
ALTER TABLE subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- Subscription plans are public (read-only)
CREATE POLICY "Public plans are viewable by all users" ON subscription_plans
    FOR SELECT USING (is_public = true);

-- Subscriptions: users can only see their company's subscription
CREATE POLICY "Users can view their company subscription" ON subscriptions
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM sessions
            WHERE user_id = auth.uid() AND is_active = true
        )
    );

-- Usage: same as subscriptions
CREATE POLICY "Users can view their subscription usage" ON subscription_usage
    FOR SELECT USING (
        subscription_id IN (
            SELECT id FROM subscriptions
            WHERE company_id IN (
                SELECT company_id FROM sessions
                WHERE user_id = auth.uid() AND is_active = true
            )
        )
    );

-- Invoices: same as subscriptions
CREATE POLICY "Users can view their invoices" ON invoices
    FOR SELECT USING (
        subscription_id IN (
            SELECT id FROM subscriptions
            WHERE company_id IN (
                SELECT company_id FROM sessions
                WHERE user_id = auth.uid() AND is_active = true
            )
        )
    );

-- Service role bypass (for backend operations)
CREATE POLICY "Service role can manage all subscription data" ON subscription_plans
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can manage all subscriptions" ON subscriptions
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can manage all usage" ON subscription_usage
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can manage all invoices" ON invoices
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- =====================================================================
-- Functions and Triggers
-- =====================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_subscription_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_subscription_plans_updated_at
    BEFORE UPDATE ON subscription_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_updated_at();

CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_updated_at();

CREATE TRIGGER update_subscription_usage_updated_at
    BEFORE UPDATE ON subscription_usage
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_updated_at();

CREATE TRIGGER update_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_updated_at();

-- =====================================================================
-- Helpful Views (Optional)
-- =====================================================================

-- View for active subscriptions with plan details
CREATE OR REPLACE VIEW active_subscriptions AS
SELECT
    s.id AS subscription_id,
    s.company_id,
    c.business_name AS company_name,
    s.status,
    s.current_period_end,
    sp.code AS plan_code,
    sp.name AS plan_name,
    sp.features,
    s.cancel_at_period_end
FROM subscriptions s
JOIN companies c ON c.id = s.company_id
JOIN subscription_plans sp ON sp.id = s.plan_id
WHERE s.status IN ('trialing', 'active');

COMMENT ON VIEW active_subscriptions IS 'Active subscriptions with company and plan details';

-- =====================================================================
-- Grant Permissions
-- =====================================================================

-- Grant SELECT on plans to authenticated users
GRANT SELECT ON subscription_plans TO authenticated;

-- Grant SELECT on subscriptions to authenticated users (RLS handles row-level access)
GRANT SELECT ON subscriptions TO authenticated;
GRANT SELECT ON subscription_usage TO authenticated;
GRANT SELECT ON invoices TO authenticated;

-- Grant ALL to service role (for backend operations)
GRANT ALL ON subscription_plans TO service_role;
GRANT ALL ON subscriptions TO service_role;
GRANT ALL ON subscription_usage TO service_role;
GRANT ALL ON invoices TO service_role;
GRANT SELECT ON active_subscriptions TO authenticated, service_role;
