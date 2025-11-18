-- Add index for purchase_documents accounting_state field
--
-- This index improves query performance for filtering purchase documents by company and accounting state.
-- Common queries include:
-- - Finding all PENDIENTE documents for a company
-- - Finding all REGISTRO documents for accounting reports
-- - Detecting state transitions during sync operations
--
-- NOTE: This migration uses CREATE INDEX CONCURRENTLY which cannot run inside a transaction block.
-- It must be applied separately from the column creation migration.

-- Create index concurrently to avoid blocking table operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_purchase_documents_accounting_state
ON purchase_documents(company_id, accounting_state);

-- Add comment explaining the index purpose
COMMENT ON INDEX idx_purchase_documents_accounting_state IS 'Improves performance for queries filtering purchase documents by company and accounting state (PENDIENTE, REGISTRO, NO_INCLUIR, RECLAMADO)';
