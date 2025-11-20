-- Add F29 Agent to all subscription plans
-- Migration to enable the F29 specialized agent across all plans.
--
-- The F29 agent is a specialized assistant for Formulario 29 (Chilean monthly VAT declaration).
-- It provides visual widgets for F29 data, explanations of F29 codes, and guidance on tax declarations.
--
-- Since F29 visualization is a core feature and doesn't require access to historical document data,
-- it should be available to all users regardless of their subscription plan.

-- ============================================================================
-- AGENT ACCESS CONFIGURATION
-- ============================================================================

-- Free Plan - Add F29 agent
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{agents,f29}',
    'true'::jsonb
)
WHERE code = 'free';

-- Basic Plan (Conecta) - Add F29 agent
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{agents,f29}',
    'true'::jsonb
)
WHERE code = 'basic';

-- Pro Plan (Impulsa) - Add F29 agent
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{agents,f29}',
    'true'::jsonb
)
WHERE code = 'pro';

-- ============================================================================
-- UPDATED AGENT DISTRIBUTION
-- ============================================================================
-- After this migration, agents are distributed as follows:
--
-- Free Plan:
--   - general_knowledge: ✅ (conceptual questions, tax theory)
--   - tax_documents: ❌ (requires Basic+)
--   - f29: ✅ (F29 visualization and guidance) ⭐ NEW
--   - payroll: ❌ (requires Pro+)
--   - settings: ✅ (notification preferences)
--
-- Basic Plan (Conecta):
--   - general_knowledge: ✅
--   - tax_documents: ✅ (invoices, receipts, document search)
--   - f29: ✅ (F29 visualization and guidance) ⭐ NEW
--   - payroll: ❌ (requires Pro+)
--   - settings: ✅
--
-- Pro Plan (Impulsa):
--   - general_knowledge: ✅
--   - tax_documents: ✅
--   - f29: ✅ (F29 visualization and guidance) ⭐ NEW
--   - payroll: ✅ (employee management, labor law)
--   - settings: ✅

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these queries to verify the migration:
--
-- 1. Check that F29 agent is enabled in all plans:
--    SELECT code, name, features->'agents'->'f29' as f29_enabled
--    FROM subscription_plans
--    WHERE code IN ('free', 'basic', 'pro')
--    ORDER BY display_order;
--
-- Expected output:
--    code  | name     | f29_enabled
--    ------|----------|------------
--    free  | Gratis   | true
--    basic | Conecta  | true
--    pro   | Impulsa  | true
--
-- 2. Check full agent access by plan:
--    SELECT code, name, features->'agents' as agents_access
--    FROM subscription_plans
--    WHERE code IN ('free', 'basic', 'pro')
--    ORDER BY display_order;
--
-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- To rollback this migration (remove F29 agent from all plans):
--
-- UPDATE subscription_plans
-- SET features = features #- '{agents,f29}'
-- WHERE code IN ('free', 'basic', 'pro');
