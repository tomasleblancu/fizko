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