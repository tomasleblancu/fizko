-- Update unique constraint on purchase_documents to include sender_rut
-- Different suppliers can have the same folio number, so we need (company_id, folio, sender_rut)

-- Drop the old constraint
ALTER TABLE purchase_documents
DROP CONSTRAINT IF EXISTS uq_purchase_documents_company_folio;

-- Add new constraint including sender_rut
ALTER TABLE purchase_documents
ADD CONSTRAINT uq_purchase_documents_company_folio_sender
UNIQUE (company_id, folio, sender_rut);

-- Add comment
COMMENT ON CONSTRAINT uq_purchase_documents_company_folio_sender ON purchase_documents
IS 'Unique constraint on (company_id, folio, sender_rut) - different suppliers can have the same folio';
