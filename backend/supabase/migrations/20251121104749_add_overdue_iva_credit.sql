-- Add overdue_iva_credit field to purchase_documents and sales_documents
-- This field stores detIVAFueraPlazo (IVA credit claimed outside the legal timeframe)

-- Add to purchase_documents
ALTER TABLE purchase_documents
ADD COLUMN IF NOT EXISTS overdue_iva_credit NUMERIC(15,2) DEFAULT 0;

-- Add to sales_documents
ALTER TABLE sales_documents
ADD COLUMN IF NOT EXISTS overdue_iva_credit NUMERIC(15,2) DEFAULT 0;

-- Add comments for documentation
COMMENT ON COLUMN purchase_documents.overdue_iva_credit IS 'IVA credit claimed outside legal timeframe (detIVAFueraPlazo from SII)';
COMMENT ON COLUMN sales_documents.overdue_iva_credit IS 'IVA credit claimed outside legal timeframe (detIVAFueraPlazo from SII)';
