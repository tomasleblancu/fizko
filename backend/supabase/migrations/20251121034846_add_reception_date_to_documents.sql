-- Add reception_date column to purchase_documents and sales_documents
-- This field corresponds to detFecRecepcion from SII API response

-- Add reception_date to purchase_documents
ALTER TABLE purchase_documents
ADD COLUMN IF NOT EXISTS reception_date DATE;

-- Add reception_date to sales_documents
ALTER TABLE sales_documents
ADD COLUMN IF NOT EXISTS reception_date DATE;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_purchase_documents_reception_date
ON purchase_documents(reception_date) WHERE reception_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sales_documents_reception_date
ON sales_documents(reception_date) WHERE reception_date IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN purchase_documents.reception_date IS 'Date when the document was received at SII (detFecRecepcion from SII API)';
COMMENT ON COLUMN sales_documents.reception_date IS 'Date when the document was received at SII (detFecRecepcion from SII API)';
