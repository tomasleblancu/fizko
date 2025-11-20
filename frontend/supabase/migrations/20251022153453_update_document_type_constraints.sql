-- Update document type constraints to include all valid types

-- Drop existing constraint for purchase_documents
ALTER TABLE purchase_documents
DROP CONSTRAINT IF EXISTS purchase_documents_document_type_check;

-- Add updated constraint for purchase_documents with all valid types
ALTER TABLE purchase_documents
ADD CONSTRAINT purchase_documents_document_type_check
CHECK (document_type = ANY (ARRAY[
    'factura_compra'::text,
    'factura_exenta_compra'::text,
    'nota_credito_compra'::text,
    'nota_debito_compra'::text,
    'liquidacion_factura'::text
]));

-- Drop existing constraint for sales_documents
ALTER TABLE sales_documents
DROP CONSTRAINT IF EXISTS sales_documents_document_type_check;

-- Add updated constraint for sales_documents with all valid types
ALTER TABLE sales_documents
ADD CONSTRAINT sales_documents_document_type_check
CHECK (document_type = ANY (ARRAY[
    'factura_venta'::text,
    'boleta'::text,
    'boleta_exenta'::text,
    'nota_credito_venta'::text,
    'nota_debito_venta'::text,
    'factura_exenta'::text,
    'comprobante_pago'::text,
    'liquidacion_factura'::text
]));