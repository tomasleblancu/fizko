-- Configure agent and tool access features for subscription plans
-- This migration adds the "agents" and "tools" keys to the features JSONB field
-- to enable subscription-based access control for AI agents and tools.

-- ============================================================================
-- AGENT ACCESS CONFIGURATION
-- ============================================================================
-- Agents available in each plan:
-- - general_knowledge: Conceptual questions, tax theory (ALL PLANS)
-- - tax_documents: Real document data, invoices, receipts (BASIC+)
-- - payroll: Employee management, labor law (PRO+)
-- - settings: Notification preferences, configuration (ALL PLANS)

-- Free Plan - Only General Knowledge + Settings
UPDATE subscription_plans
SET features = jsonb_set(
    COALESCE(features, '{}'::jsonb),
    '{agents}',
    '{
        "general_knowledge": true,
        "tax_documents": false,
        "payroll": false,
        "settings": true
    }'::jsonb
)
WHERE code = 'free';

-- Basic Plan (Conecta) - + Tax Documents
UPDATE subscription_plans
SET features = jsonb_set(
    COALESCE(features, '{}'::jsonb),
    '{agents}',
    '{
        "general_knowledge": true,
        "tax_documents": true,
        "payroll": false,
        "settings": true
    }'::jsonb
)
WHERE code = 'basic';

-- Pro Plan (Impulsa) - + Payroll
UPDATE subscription_plans
SET features = jsonb_set(
    COALESCE(features, '{}'::jsonb),
    '{agents}',
    '{
        "general_knowledge": true,
        "tax_documents": true,
        "payroll": true,
        "settings": true
    }'::jsonb
)
WHERE code = 'pro';

-- ============================================================================
-- TOOL ACCESS CONFIGURATION
-- ============================================================================
-- Individual tools can also be restricted by plan:
-- - get_documents: Search and list tax documents
-- - get_documents_summary: Monthly/yearly summaries
-- - get_f29_data: Detailed F29 form data (PRO+)
-- - get_people: List employees (PRO+)
-- - create_person: Register new employees (PRO+)
-- - update_person: Update employee information (PRO+)
-- - calculate_payroll: Automatic payroll calculations (ENTERPRISE)

-- Free Plan - No tools (agents are restricted)
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{tools}',
    '{
        "get_documents": false,
        "get_documents_summary": false,
        "get_f29_data": false,
        "get_people": false,
        "create_person": false,
        "update_person": false,
        "calculate_payroll": false
    }'::jsonb
)
WHERE code = 'free';

-- Basic Plan - Tax document tools only
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{tools}',
    '{
        "get_documents": true,
        "get_documents_summary": true,
        "get_f29_data": false,
        "get_people": false,
        "create_person": false,
        "update_person": false,
        "calculate_payroll": false
    }'::jsonb
)
WHERE code = 'basic';

-- Pro Plan - + F29 data + Payroll management (no automatic calculations)
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{tools}',
    '{
        "get_documents": true,
        "get_documents_summary": true,
        "get_f29_data": true,
        "get_people": true,
        "create_person": true,
        "update_person": true,
        "calculate_payroll": false
    }'::jsonb
)
WHERE code = 'pro';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these queries to verify the migration:
--
-- 1. Check agent access by plan:
--    SELECT code, name, features->'agents' as agents_access
--    FROM subscription_plans
--    ORDER BY display_order;
--
-- 2. Check tool access by plan:
--    SELECT code, name, features->'tools' as tools_access
--    FROM subscription_plans
--    ORDER BY display_order;
--
-- 3. Check full features for a specific plan:
--    SELECT code, name, features
--    FROM subscription_plans
--    WHERE code = 'pro';
--
-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- To rollback this migration (remove agent/tool features):
--
-- UPDATE subscription_plans
-- SET features = features - 'agents' - 'tools'
-- WHERE code IN ('free', 'basic', 'pro');
