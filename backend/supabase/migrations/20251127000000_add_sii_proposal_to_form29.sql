-- Add sii_proposal field to form29 table
-- This field stores the raw JSON proposal from SII's get_declaracion_propuesta API

ALTER TABLE form29
ADD COLUMN IF NOT EXISTS sii_proposal JSONB;

COMMENT ON COLUMN form29.sii_proposal IS 'Propuesta de declaración F29 pre-calculada por el SII. Contiene códigos propuestos, condiciones del contribuyente, y códigos que requieren complementación manual.';

-- Add index for faster JSON queries
CREATE INDEX IF NOT EXISTS idx_form29_sii_proposal ON form29 USING GIN (sii_proposal);

-- Migration to add sii_proposal field to form29 table
-- This field stores the SII proposal data obtained from get_declaracion_propuesta API
