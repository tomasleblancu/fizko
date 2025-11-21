-- Fix folio column to support large DIN folios (exceeds integer max)
-- DIN folios can be larger than 2,147,483,647 (integer max)
-- Example: 2400360734

-- Alter purchase_documents folio column to bigint
ALTER TABLE purchase_documents
ALTER COLUMN folio TYPE bigint;

-- Alter sales_documents folio column to bigint (preventive)
ALTER TABLE sales_documents
ALTER COLUMN folio TYPE bigint;

-- Also fix reference_folio in purchase_documents
ALTER TABLE purchase_documents
ALTER COLUMN reference_folio TYPE bigint;
