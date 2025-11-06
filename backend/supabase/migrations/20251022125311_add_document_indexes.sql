-- Add composite index on purchase_documents for faster upsert operations
CREATE INDEX IF NOT EXISTS idx_purchase_documents_company_folio
ON purchase_documents(company_id, folio);

-- Add composite index on sales_documents for faster upsert operations
CREATE INDEX IF NOT EXISTS idx_sales_documents_company_folio
ON sales_documents(company_id, folio);

-- Add index on purchase_documents issue_date for date range queries
CREATE INDEX IF NOT EXISTS idx_purchase_documents_issue_date
ON purchase_documents(issue_date DESC);

-- Add index on sales_documents issue_date for date range queries
CREATE INDEX IF NOT EXISTS idx_sales_documents_issue_date
ON sales_documents(issue_date DESC);

-- Add composite index for filtering documents by company and date range
CREATE INDEX IF NOT EXISTS idx_purchase_documents_company_date_range
ON purchase_documents(company_id, issue_date DESC);

CREATE INDEX IF NOT EXISTS idx_sales_documents_company_date_range
ON sales_documents(company_id, issue_date DESC);

-- Add index on document_type for filtering
CREATE INDEX IF NOT EXISTS idx_purchase_documents_type
ON purchase_documents(document_type);

CREATE INDEX IF NOT EXISTS idx_sales_documents_type
ON sales_documents(document_type);

-- Add composite index for company + type queries
CREATE INDEX IF NOT EXISTS idx_purchase_documents_company_type_date
ON purchase_documents(company_id, document_type, issue_date DESC);

CREATE INDEX IF NOT EXISTS idx_sales_documents_company_type_date
ON sales_documents(company_id, document_type, issue_date DESC);