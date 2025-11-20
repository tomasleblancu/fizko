-- Add accounting_state and accounting_date fields to purchase_documents
--
-- accounting_state: Tracks the SII estadoContab field (PENDIENTE, REGISTRO, NO_INCLUIR, RECLAMADO)
-- accounting_date: Date when the document transitioned from PENDIENTE to REGISTRO
--
-- NOTE: Index creation is in a separate migration (20251118000001) because
-- CREATE INDEX CONCURRENTLY cannot run inside a transaction block

-- Add columns only if they don't exist (idempotent)
DO $$
BEGIN
    -- Add accounting_state column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'purchase_documents'
        AND column_name = 'accounting_state'
    ) THEN
        ALTER TABLE purchase_documents ADD COLUMN accounting_state TEXT NULL;
    END IF;

    -- Add accounting_date column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'purchase_documents'
        AND column_name = 'accounting_date'
    ) THEN
        ALTER TABLE purchase_documents ADD COLUMN accounting_date DATE NULL;
    END IF;
END $$;

-- Add comments explaining the fields (these are idempotent)
COMMENT ON COLUMN purchase_documents.accounting_state IS 'SII accounting state: PENDIENTE (pending accounting) or REGISTRO (registered in accounting system)';
COMMENT ON COLUMN purchase_documents.accounting_date IS 'Date when accounting_state changed from PENDIENTE to REGISTRO';
