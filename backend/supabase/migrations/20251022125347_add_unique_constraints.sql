-- Add unique constraint on purchase_documents (company_id, folio)
-- This allows efficient upsert operations
ALTER TABLE purchase_documents
ADD CONSTRAINT uq_purchase_documents_company_folio
UNIQUE (company_id, folio);

-- Add unique constraint on sales_documents (company_id, folio)
-- This allows efficient upsert operations
ALTER TABLE sales_documents
ADD CONSTRAINT uq_sales_documents_company_folio
UNIQUE (company_id, folio);