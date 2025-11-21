-- Add document_type_code column to purchase_documents and sales_documents
-- This stores the numeric SII document type code (33, 56, 61, 914, etc.)

-- Add to purchase_documents
ALTER TABLE purchase_documents
ADD COLUMN IF NOT EXISTS document_type_code TEXT;

-- Add to sales_documents
ALTER TABLE sales_documents
ADD COLUMN IF NOT EXISTS document_type_code TEXT;

-- Add comments
COMMENT ON COLUMN purchase_documents.document_type_code IS 'Código numérico del tipo de documento según SII (33=factura, 56=nota débito, 61=nota crédito, 914=DIN)';
COMMENT ON COLUMN sales_documents.document_type_code IS 'Código numérico del tipo de documento según SII (33=factura, 39=boleta, 56=nota débito, 61=nota crédito)';

-- Add indexes for efficient filtering by document type code
CREATE INDEX IF NOT EXISTS idx_purchase_documents_type_code
ON purchase_documents(company_id, document_type_code)
WHERE document_type_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sales_documents_type_code
ON sales_documents(company_id, document_type_code)
WHERE document_type_code IS NOT NULL;

-- Backfill existing purchase documents
UPDATE purchase_documents
SET document_type_code = CASE document_type
    WHEN 'factura_compra' THEN '33'
    WHEN 'factura_exenta_compra' THEN '34'
    WHEN 'boleta' THEN '39'
    WHEN 'liquidacion_factura' THEN '43'
    WHEN 'comprobante_pago' THEN '48'
    WHEN 'nota_debito_compra' THEN '56'
    WHEN 'nota_credito_compra' THEN '61'
    WHEN 'declaracion_ingreso' THEN '914'
    WHEN 'DIN' THEN '914'
    ELSE NULL
END
WHERE document_type_code IS NULL;

-- Backfill existing sales documents
UPDATE sales_documents
SET document_type_code = CASE document_type
    WHEN 'factura_venta' THEN '33'
    WHEN 'factura_exenta' THEN '34'
    WHEN 'boleta' THEN '39'
    WHEN 'boleta_exenta' THEN '41'
    WHEN 'liquidacion_factura' THEN '43'
    WHEN 'comprobante_pago' THEN '48'
    WHEN 'nota_debito_venta' THEN '56'
    WHEN 'nota_credito_venta' THEN '61'
    ELSE NULL
END
WHERE document_type_code IS NULL;
