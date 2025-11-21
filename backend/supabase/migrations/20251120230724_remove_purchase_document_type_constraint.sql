-- Remove document_type check constraint to allow all document types
-- This allows DIN (declaracion_ingreso), boleta, comprobante_pago, and future types
-- The constraint was limiting to only 5 specific types, but we need to support
-- all document types that the SII API can return

ALTER TABLE purchase_documents
DROP CONSTRAINT IF EXISTS purchase_documents_document_type_check;
