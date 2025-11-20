-- =====================================================================
-- Add Reference Document Fields to Tax Documents
-- =====================================================================
-- Description: Adds fields to track referenced documents (e.g., credit notes referencing invoices)
-- Date: 2025-11-20
--
-- Use case: When a nota de crédito (tipo 61) references a factura (tipo 33),
-- we need to store detTipoDocRef and detFolioDocRef from SII data.
-- =====================================================================

-- Add reference document fields to purchase_documents
ALTER TABLE purchase_documents
ADD COLUMN IF NOT EXISTS reference_document_type TEXT,
ADD COLUMN IF NOT EXISTS reference_folio INTEGER;

-- Add reference document fields to sales_documents
ALTER TABLE sales_documents
ADD COLUMN IF NOT EXISTS reference_document_type TEXT,
ADD COLUMN IF NOT EXISTS reference_folio INTEGER;

-- Add comments for documentation
COMMENT ON COLUMN purchase_documents.reference_document_type IS 'Tipo de documento referenciado (detTipoDocRef del SII). Ejemplo: "33" para factura';
COMMENT ON COLUMN purchase_documents.reference_folio IS 'Folio del documento referenciado (detFolioDocRef del SII)';

COMMENT ON COLUMN sales_documents.reference_document_type IS 'Tipo de documento referenciado (detTipoDocRef del SII). Ejemplo: "33" para factura';
COMMENT ON COLUMN sales_documents.reference_folio IS 'Folio del documento referenciado (detFolioDocRef del SII)';

-- Create indexes for efficient lookups of referenced documents
CREATE INDEX IF NOT EXISTS ix_purchase_documents_reference
ON purchase_documents(company_id, reference_document_type, reference_folio)
WHERE reference_document_type IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_sales_documents_reference
ON sales_documents(company_id, reference_document_type, reference_folio)
WHERE reference_document_type IS NOT NULL;
