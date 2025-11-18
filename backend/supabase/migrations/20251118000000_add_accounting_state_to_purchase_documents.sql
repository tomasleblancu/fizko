-- Add accounting_state and accounting_date fields to purchase_documents
--
-- accounting_state: Tracks the SII estadoContab field (PENDIENTE or REGISTRO)
-- accounting_date: Date when the document transitioned from PENDIENTE to REGISTRO

-- Add accounting_state column
ALTER TABLE purchase_documents
ADD COLUMN accounting_state TEXT NULL;

-- Add accounting_date column
ALTER TABLE purchase_documents
ADD COLUMN accounting_date DATE NULL;

-- Add comment explaining the fields
COMMENT ON COLUMN purchase_documents.accounting_state IS 'SII accounting state: PENDIENTE (pending accounting) or REGISTRO (registered in accounting system)';
COMMENT ON COLUMN purchase_documents.accounting_date IS 'Date when accounting_state changed from PENDIENTE to REGISTRO';

-- Create index for efficient filtering by accounting_state
CREATE INDEX idx_purchase_documents_accounting_state ON purchase_documents(company_id, accounting_state);
