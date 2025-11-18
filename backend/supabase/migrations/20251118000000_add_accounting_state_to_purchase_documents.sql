-- Add accounting_state and accounting_date fields to purchase_documents
--
-- accounting_state: Tracks the SII estadoContab field (PENDIENTE or REGISTRO)
-- accounting_date: Date when the document transitioned from PENDIENTE to REGISTRO

-- Add columns in a single ALTER TABLE statement for efficiency
ALTER TABLE purchase_documents
ADD COLUMN accounting_state TEXT NULL,
ADD COLUMN accounting_date DATE NULL;

-- Add comments explaining the fields
COMMENT ON COLUMN purchase_documents.accounting_state IS 'SII accounting state: PENDIENTE (pending accounting) or REGISTRO (registered in accounting system)';
COMMENT ON COLUMN purchase_documents.accounting_date IS 'Date when accounting_state changed from PENDIENTE to REGISTRO';

-- Create index CONCURRENTLY to avoid locking the table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_purchase_documents_accounting_state ON purchase_documents(company_id, accounting_state);
