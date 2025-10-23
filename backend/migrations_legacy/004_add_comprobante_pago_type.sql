-- Migration: Add comprobante_pago to sales_documents allowed types
-- Description: Adds support for comprobante_pago (DTE code 48) in sales documents
-- Date: 2025-10-21

-- Drop the old constraint
ALTER TABLE sales_documents
DROP CONSTRAINT IF EXISTS sales_documents_document_type_check;

-- Add the new constraint with comprobante_pago included
ALTER TABLE sales_documents
ADD CONSTRAINT sales_documents_document_type_check
CHECK (document_type = ANY (ARRAY[
    'factura_venta'::text,
    'boleta'::text,
    'nota_credito_venta'::text,
    'nota_debito_venta'::text,
    'factura_exenta'::text,
    'comprobante_pago'::text
]));

-- Add comment
COMMENT ON CONSTRAINT sales_documents_document_type_check ON sales_documents IS
'Ensures document_type is one of the valid Chilean DTE types for sales';
