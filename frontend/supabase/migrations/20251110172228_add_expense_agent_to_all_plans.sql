-- Add Expense Agent to all subscription plans
-- Migration to enable the Expense specialized agent across all plans.
--
-- The Expense agent is a specialized assistant for manual expense registration and tracking.
-- It provides:
-- - Manual expense registration with receipt upload
-- - OCR extraction from receipts (images and PDFs)
-- - Expense categorization and tracking
-- - IVA recuperable calculations
-- - Expense summaries and queries
--
-- Since expense tracking is a core business need for all Chilean businesses,
-- it should be available to all users regardless of their subscription plan.

-- ============================================================================
-- AGENT ACCESS CONFIGURATION
-- ============================================================================

-- Free Plan - Add expense agent
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{agents,expense}',
    'true'::jsonb
)
WHERE code = 'free';

-- Basic Plan (Conecta) - Add expense agent
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{agents,expense}',
    'true'::jsonb
)
WHERE code = 'basic';

-- Pro Plan (Impulsa) - Add expense agent
UPDATE subscription_plans
SET features = jsonb_set(
    features,
    '{agents,expense}',
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
--   - f29: ✅ (F29 visualization and guidance)
--   - expense: ✅ (manual expense registration and tracking) ⭐ NEW
--   - payroll: ❌ (requires Pro+)
--   - settings: ✅ (notification preferences)
--
-- Basic Plan (Conecta):
--   - general_knowledge: ✅
--   - tax_documents: ✅ (invoices, receipts, document search)
--   - f29: ✅ (F29 visualization and guidance)
--   - expense: ✅ (manual expense registration and tracking) ⭐ NEW
--   - payroll: ❌ (requires Pro+)
--   - settings: ✅
--
-- Pro Plan (Impulsa):
--   - general_knowledge: ✅
--   - tax_documents: ✅
--   - f29: ✅ (F29 visualization and guidance)
--   - expense: ✅ (manual expense registration and tracking) ⭐ NEW
--   - payroll: ✅ (employee management, labor law)
--   - settings: ✅
--
-- ============================================================================
-- EXPENSE AGENT vs TAX DOCUMENTS AGENT
-- ============================================================================
-- Key differences:
-- - Tax Documents Agent: Handles DTEs (electronic documents from SII)
--   - Facturas electrónicas, boletas, guías
--   - Automatically synced from SII
--   - Read-only data
--
-- - Expense Agent: Handles manual expenses
--   - Physical receipts (not DTEs)
--   - OCR extraction from uploaded images/PDFs
--   - User-created expenses
--   - Categories: transport, meals, office supplies, etc.
--
-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these queries to verify the migration:
--
-- 1. Check that expense agent is enabled in all plans:
--    SELECT code, name, features->'agents'->'expense' as expense_enabled
--    FROM subscription_plans
--    WHERE code IN ('free', 'basic', 'pro')
--    ORDER BY display_order;
--
-- Expected output:
--    code  | name     | expense_enabled
--    ------|----------|----------------
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
-- 3. Verify all 6 agents are properly configured:
--    SELECT
--      code,
--      name,
--      features->'agents'->'general_knowledge' as general_knowledge,
--      features->'agents'->'tax_documents' as tax_documents,
--      features->'agents'->'f29' as f29,
--      features->'agents'->'expense' as expense,
--      features->'agents'->'payroll' as payroll,
--      features->'agents'->'settings' as settings
--    FROM subscription_plans
--    WHERE code IN ('free', 'basic', 'pro')
--    ORDER BY display_order;
--
-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- To rollback this migration (remove expense agent from all plans):
--
-- UPDATE subscription_plans
-- SET features = features #- '{agents,expense}'
-- WHERE code IN ('free', 'basic', 'pro');
