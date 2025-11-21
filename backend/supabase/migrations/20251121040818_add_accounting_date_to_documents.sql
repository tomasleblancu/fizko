-- Add accounting_date column to purchase_documents and sales_documents
-- This field determines when the document is recognized for tax purposes

-- Add accounting_date to purchase_documents
ALTER TABLE purchase_documents
ADD COLUMN IF NOT EXISTS accounting_date DATE;

-- Add accounting_date to sales_documents
ALTER TABLE sales_documents
ADD COLUMN IF NOT EXISTS accounting_date DATE;

-- Create indexes for better query performance (will be used for tax calculations)
CREATE INDEX IF NOT EXISTS idx_purchase_documents_accounting_date
ON purchase_documents(accounting_date) WHERE accounting_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sales_documents_accounting_date
ON sales_documents(accounting_date) WHERE accounting_date IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN purchase_documents.accounting_date IS 'Date when the document is recognized for tax purposes. For DIN documents: issue_date. For others: reception_date.';
COMMENT ON COLUMN sales_documents.accounting_date IS 'Date when the document is recognized for tax purposes. Always equals issue_date for sales documents.';
